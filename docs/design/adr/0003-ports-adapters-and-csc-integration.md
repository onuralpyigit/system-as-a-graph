# ADR-0003: Ports and Adapters per CSC, and internal CSC integration

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | QA-11; MDG.2–5, 23; SCG.7; FDM.4; ADM.2–4; SMM.2, 27–28, 33; DVE.3, 27; SDD §2.3 EXT-IF-01…07, INT-IF-01…05 |
| Resolves | DP-24…DP-28 (communication method/protocol of INT-IF-01…05) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SaaG integrates with seven external systems (SDD §2.3). In development and test most of them are unavailable or replaced by mocks: `dev/compose.yaml` runs MySQL and Gitea, and LDAP and four of the six source-data parsers are mocks. Inside the CSCI, SDD §2.3 defines five internal interfaces and leaves their "communication method/protocol" to the critical design phase:

| Interface | Handoff |
|---|---|
| INT-IF-01 | MDG → SMM, Model Data |
| INT-IF-02 | SCG → ADM, synthetic data |
| INT-IF-03 | FDM → ADM, field records |
| INT-IF-04 | ADM → SMM, Analytical Evaluation Data |
| INT-IF-05 | SMM → DVE, model access |

`mdg/` and `dve/` are built as Ports and Adapters. `dve` calls `mdg` through its package façade (`mdg.produce_model_setup_data(...)`) inside a spawned child process (ADR-0006). The result is a JSON file on disk, resolved by `run_id`. This ADR records the pattern and the integration rules, so the four remaining CSCs follow them the same way.

## Decision Drivers

* Domain logic (validation, model construction, verification rules) must be testable without external systems (QA-11).
* External systems are only partly known (topology source, package repository, field data recording). Their adapters will change without the domain changing.
* SRS requirements say handed-off data is *recorded* and *traceable* (MDG.23, SCG.5, FDM.3, SMM.26, 35). A handoff must leave a persisted, identifiable artifact.
* All CSCs run in one process tree on one host (ADR-0004). Handoffs carry large payloads, such as whole models and data sets.

## Considered Options

* Structure: Ports and Adapters per CSC, with fakes selected by injection (as built) / layered architecture / direct integration
* Internal integration: in-process façade calls with persisted artifacts referenced by ID / file drop / message queue / internal HTTP

## Decision Outcome

Chosen options: **Ports and Adapters per CSC (as built)** and **in-process façade calls with persisted artifacts referenced by ID**. The structure is already implemented and tested, and it isolates the parts of the design still deferred. The SRS asks for recorded artifacts, not messaging: the handoff is the artifact, and the call only passes its identifier.

### 1. Package structure

Rules for every CSC package `<csc>/src/<csc>/`:

| Directory | Contains | May import |
|---|---|---|
| `domain/` | Immutable value objects and entities (`@dataclass(frozen=True)`), domain errors | standard library only |
| `ports/` | Abstract interfaces `I<Name>` (ABCs) and the port-specific exceptions | `domain` |
| `services/` | Use cases, one class per use case, depending on ports only | `domain`, `ports` |
| `adapters/<area>/` | Implementations `<Technology><Port>`, e.g. `GitSourceCodeRepository`, `MultiprocessingTaskRunner` | `domain`, `ports`, third-party libraries |
| `__init__.py` | The public façade: factory functions that wire adapters to services | everything in the package |

* **Fakes** live under `<csc>/tests/fakes/` as `Fake<Port>`, with a shared `seed.py`, and are selected in `conftest.py`. When a second CSC needs them, they move to an importable `<csc>.testing` module, which production code never imports. Today `dve/tests/fakes/` duplicates `mdg`'s config, source and seed fakes.
* **Mocks in production code** start their first docstring line with `Mock: …`, and must be replaced before the release that needs the real system. As of `1157784`:

  | Mock adapter | Replaced by |
  |---|---|
  | `dve/src/dve/adapters/ldap_directory_service.py` `LdapDirectoryService` | ADR-0019, before production use |
  | `mdg/src/mdg/adapters/source_data/system_repo_parser.py` `SystemRepoParser` | ADR-0008, before the R3 resource rules (DVE.40–46) |
  | `mdg/src/mdg/adapters/source_data/ansible_repo_parser.py` `AnsibleRepoParser` | ADR-0008 |
  | `mdg/src/mdg/adapters/source_data/type_support_parser.py` `TypeSupportParser` | ADR-0008, before the R3 QoS rules (DVE.32–35) |
  | `mdg/src/mdg/adapters/source_data/message_file_parser.py` `MessageFileParser` | ADR-0008 |

* **Adapter selection:** today the façades wire one adapter per port by hand (`mdg/src/mdg/__init__.py:92-141`). MySQL and Git are always chosen, and `DataSourceConfig.access_method` is never read. New façade factories select the adapter from `access_method`, or from a `[…] backend =` ini key for ports that are not data sources, through a registry dictionary in the façade. An unknown value is a start-up configuration error. Callers may still pass their own port instances, which is how tests inject fakes.

### 2. Internal integration (INT-IF-01…05)

* **Method:** a consumer calls the producer CSC's façade functions, never its internal modules. Long-running calls run inside an operation's child process (ADR-0006).
* **Payload:** the producer persists the artifact first and returns an artifact reference: ID, kind, location and content hash (ADR-0007). The consumer loads the artifact by reference.

  | Interface | Producer call returns | Artifact store |
  |---|---|---|
  | INT-IF-01 MDG → SMM | Model Data file reference | Filesystem (ADR-0009) |
  | INT-IF-02 SCG → ADM | Synthetic data set reference | ADR-0012 |
  | INT-IF-03 FDM → ADM | Field record selection (record IDs) | ADR-0014 |
  | INT-IF-04 ADM → SMM | Analytical Evaluation Data reference | ADR-0012 |
  | INT-IF-05 SMM → DVE | Read-only model instance handle | Graph store (ADR-0011) |

* **INT-IF-05:** DVE gets a model access object from SMM's façade. It only exposes queries and is bound to one model instance. Writes go through SMM's working-model API (ADR-0011), never through the handle.
* **Errors:** façade functions raise domain errors carrying an error record (ADR-0009).
* **Process boundary:**
  * Arguments are picklable: identifiers, plain dataclasses and `to_dict()` forms.
  * Results are plain dicts, as built: `ProductionResult.to_dict()`.
  * Exceptions must survive pickling with their error record. Today `DataAcquisitionError` loses it (ADR-0009).
* **Progress:** long-running façade functions accept a `progress(percent, phase)` callback, as `mdg.produce_model_setup_data` does.

**As built:** INT-IF-01 works as above, with two gaps. The reference is the tuple (project, platform, version, `run_id`), not an artifact ID, and there is no content hash yet. The other four interfaces are not built.

**To build:** SMM's façade takes a Model Data reference and verifies its hash before construction (SMM.2–3). The SCG, ADM and FDM façades follow the table, from R4.

### Consequences

* Good, because each external-system decision only replaces an adapter, and the fast test suites run without the `dev/` services.
* Good, because there is no network protocol or wire format inside the CSCI, and every handoff is a persisted, hashable artifact.
* Bad, because there is extra indirection for simple paths, and fakes must be kept in step with ports.
* Bad, because CSC boundaries depend on import discipline, enforced in CI.

### Confirmation

* `import-linter` contracts per package: `domain` imports nothing from the package, `services` does not import `adapters`, and consumers import only `<csc>`, never `<csc>.services` or `<csc>.adapters`.
* Adapter contract tests run the same cases against the fake and the real adapter (ADR-0021).
* Each façade function has a contract test with a fake producer artifact.

## Pros and Cons of the Options

### Structure

* Ports and Adapters (as built): Good, because external uncertainty is isolated and the design is testable. Bad, because there are more files and interfaces.
* Layered: Good, because it is familiar. Bad, because repositories bind to one technology, and swapping in fakes needs mocking.
* Direct integration: Good, because it has the least code. Bad, because tests need the real systems.

### Internal integration

* Façade calls with persisted artifacts: Good, because it is the simplest option and matches the SRS recording requirements. Bad, because it couples CSCs to a shared runtime.
* File drop: Good, because it gives loose coupling. Bad, because of polling and partial-file races, and no typed contract.
* Message queue: Good, because it is decoupled. Bad, because large payloads don't belong on a broker, and there is no broker on the host.
* Internal HTTP: Good, because it is ready for a service split. Bad, because it adds network failure modes for no current benefit.

## More Information

* Code: `mdg/src/mdg/{domain,ports,services,adapters}`, `mdg/src/mdg/__init__.py`, `dve/src/dve/{domain,ports,services,adapters}`, `dve/src/dve/__init__.py`
* [SDD §2.3](../SDD.md), [SDP §5](../../planning/SDP.md)
* Related: ADR-0004, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0011, ADR-0012, ADR-0014, ADR-0019, ADR-0021
