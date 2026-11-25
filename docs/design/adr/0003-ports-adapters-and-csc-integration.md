# ADR-0003: Ports and Adapters per CSC, and internal CSC integration

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | QA-11; MDG.2–5, 23; SCG.7; FDM.2, 4; ADM.2–4; SMM.2, 27–28, 33; DVE.2–3, 27; SDD §2.3 EXT-IF-01…07, INT-IF-01…05 |
| Resolves | DP-24…DP-28 (communication method/protocol of INT-IF-01…05) |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

SaaG integrates with seven external systems (SDD §2.3). In development and test most of them are unavailable or replaced by mocks: `dev/compose.yaml` runs MySQL and Gitea, and LDAP plus four of MDG's five source-data parser ports (`SystemRepoParser`, `AnsibleRepoParser`, `TypeSupportParser`, `MessageFileParser`) are mocks. Inside the CSCI, DVE must interact with MDG, SCG, ADM and SMM (DVE.2, plus FDM for field-record upload and selection, DVE.10, 12), and SDD §2.3 defines five internal interfaces whose "communication method/protocol" is deferred to the critical design phase:

| Interface | Handoff |
|---|---|
| INT-IF-01 | MDG → SMM, Model Data |
| INT-IF-02 | SCG → ADM, synthetic data |
| INT-IF-03 | FDM → ADM, field records |
| INT-IF-04 | ADM → SMM, Analytical Evaluation Data |
| INT-IF-05 | SMM → DVE, model and bound analytical data access |

`mdg/` and `dve/` are built as Ports and Adapters. `dve` calls `mdg` through its package façade (`mdg.produce_model_setup_data(...)`) inside a spawned child process (ADR-0006). The result is a JSON file on disk, resolved by `run_id`. This ADR records the hexagonal rules, documents current code deviations to clean up, and fixes the internal integration contracts so all six CSCs integrate uniformly.

## Decision Drivers

* Domain logic (validation, model construction, verification rules, propagation) must be testable in memory without external systems (QA-11).
* External systems are only partly specified (topology source, package repository, field data recording); replacing an adapter must never touch domain or service logic.
* SRS requirements require handed-off data to be *recorded* and *traceable* (MDG.23, SCG.5, FDM.3, ADM.1, SMM.26, 35); every handoff must leave a persisted, hash-identifiable artifact.
* All CSCs run in one process tree on one host (ADR-0004), and handoffs carry large payloads (models, telemetry and synthetic datasets).

## Considered Options

* Package structure: Ports and Adapters per CSC with injected fakes (as built)
* Package structure: Layered architecture without port inversion
* Package structure: Direct external-library calls inside use cases
* Internal integration: In-process façade calls passing persisted artifact references by ID
* Internal integration: Watched file-drop directories
* Internal integration: Local message broker / queue
* Internal integration: Internal HTTP microservices per CSC

## Decision Outcome

Chosen options: **Ports and Adapters per CSC with injected fakes (as built)** and **in-process façade calls passing persisted artifact references by ID**. The hexagonal layout is already working and isolates external-interface uncertainty behind small ABCs, while persisted artifact references satisfy every SRS traceability requirement without serialization or network overhead inside a single-host modular monolith.

### 1. Package structure

Rules for every CSC package `<csc>/src/<csc>/`:

| Directory | Contains | Allowed imports |
|---|---|---|
| `domain/` | Immutable value objects and entities (`@dataclass(frozen=True)`), domain errors | Python standard library and `common` only |
| `ports/` | Abstract interfaces `I<Name>` (`abc.ABC`) and port-specific exceptions | standard library, `common`, own `domain` |
| `services/` | Use cases, one class per use case, depending on ports only | standard library, `common`, own `domain` and `ports`, and peer `<csc>` top-level public façades/DTOs (following ADR-0004 §1 dependency direction) |
| `adapters/<area>/` | Concrete implementations `<Technology><Port>` (e.g. `GitSourceCodeRepository`, `MultiprocessingTaskRunner`) | standard library, `common`, own `domain`, `ports`, `config`, and third-party libraries |
| `__init__.py` | Public façade: re-exported DTOs/ports and factory functions wiring adapters to services; third-party adapter imports are lazy inside factory functions | everything in the package |

* **Fakes** live under `<csc>/tests/fakes/` as `Fake<Port>`, with a shared `seed.py`, injected via `conftest.py`. When a second CSC needs a producer's fakes (as `dve/tests/fakes/` currently duplicates `mdg/tests/fakes/{fake_config_management_repository.py,fake_source_code_repository.py,seed.py}` with behavioral drift), they move to `<csc>.testing`, which production code never imports.
* **Mocks in production code** start their first docstring line with `Mock: …`, and must be replaced before the release that consumes the real system:

  | Mock adapter (`1157784`) | Replaced under |
  |---|---|
  | `dve/src/dve/adapters/ldap_directory_service.py` (`LdapDirectoryService`) | ADR-0019, before production mode |
  | `mdg/src/mdg/adapters/source_data/system_repo_parser.py` (`SystemRepoParser`) | ADR-0008, before R3 resource/service rules (DVE.39–46) |
  | `mdg/src/mdg/adapters/source_data/ansible_repo_parser.py` (`AnsibleRepoParser`) | ADR-0008, before R3 capacity/load rules (DVE.40–46) |
  | `mdg/src/mdg/adapters/source_data/type_support_parser.py` (`TypeSupportParser`) | ADR-0008, before R3 QoS/conflict rules (DVE.32–35, 38) |
  | `mdg/src/mdg/adapters/source_data/message_file_parser.py` (`MessageFileParser`) | ADR-0008, before R3/R4 message & schema rules (SMM.13, SCG.4) |

* **Adapter selection:** `mdg/src/mdg/__init__.py:92-141` currently wires MySQL and Git unconditionally without reading `DataSourceConfig.access_method`, and imports `MysqlConfigManagementRepository` (`pymysql`) eagerly at module import time (`mdg/__init__.py:18`). Façade factories must lazily import concrete adapters and select them via a registry keyed by `DataSourceConfig.access_method` (or a `[…] backend =` `.ini` setting for non-source ports), raising a start-up configuration error on unknown values while still accepting caller-injected port instances for tests.
* **As-built structural cleanups (To build in R3):**
  * Move `dve/src/dve/adapters/*.py` into `<area>/` subpackages (`directory/`, `tasks/`) to match `mdg`.
  * Make `MysqlConfigManagementRepository` lazy in `mdg/__init__.py` so importing `mdg` domain types never requires `pymysql`.
  * Extract `MandatoryFiles` behind a domain/port specification rather than concrete-importing `mdg.adapters.source_code.mandatory_files` across sibling adapters, and route `ProduceModelSetupData` orchestration cleanly without cross-service coupling.
  * Deduplicate `dve/tests/fakes/` onto `mdg.testing`.

### 2. Internal integration (INT-IF-01…05 and orchestration seams)

* **Method:** a consumer invokes the producer CSC's top-level façade functions (`import <csc>`), never `<csc>.services.*` or `<csc>.adapters.*`. Long-running façade calls execute inside an operation's spawned child process (ADR-0006).
* **Payload:** the producer persists the output artifact first, registers it in `common_artifact` (ADR-0007), and returns an immutable `ArtifactRef(artifact_id, kind, location, sha256)`. The consumer loads and hash-verifies the artifact by reference.

  | Interface | Producer façade returns | Backing store |
  |---|---|---|
  | INT-IF-01 MDG → SMM | `ArtifactRef` (`model_data_file`) | Filesystem JSON (ADR-0009) |
  | INT-IF-02 SCG → ADM | `ArtifactRef` (`synthetic_data_set`) | Filesystem JSONL.gz (ADR-0013) |
  | INT-IF-03 FDM → ADM | Validated `record_id` list (`status = 'parsed'`) | Field records store + `fdm_record` (ADR-0014) |
  | INT-IF-04 ADM → SMM | `ArtifactRef` (`analytical_evaluation_data`) | Filesystem JSONL.gz + per-dataset `overlay.db` (ADR-0012) |
  | INT-IF-05 SMM → DVE | Read-only composite handle (`ModelReader` + optional bound `AedReader`) | Graph store (ADR-0011) + read-only `overlay.db` (ADR-0012) |

* **INT-IF-05 (`SMM → DVE`, SMM.27–28):** DVE obtains a read-only `ModelHandle(model: ModelReader, aed: Optional[AedReader])` bound to a specific `(instance_id, revision)` (and optional `binding_id`). All structural mutations go through SMM's working-model command façade (`apply_edit`, `undo_edit`, ADR-0011), never through `ModelReader`.
* **Model schema feed to SCG (`DVE → SCG`, SCG.4, DVE.17):** SDD §2.3 has no direct `SMM → SCG` interface, yet SCG needs nominal topic/message rates and field/value-range schemas from either a baseline or an edited Working Model (DVE.17), and `scg` does not import `mdg` or `smm` (ADR-0004 §1). DVE extracts a picklable, read-only `ModelSchemaSnapshot` DTO (defined in `common`) via `SMM`'s `ModelReader(instance_id, revision)` and passes it into `scg.produce_synthetic_data(...)`.
* **Errors and child-process boundary:**
  * Façade functions raise domain exceptions carrying a structured `ErrorRecord` (`common/errors.py`, ADR-0009).
  * Spawn arguments must be picklable (`ArtifactRef`, identifiers, frozen dataclasses or `to_dict()` dicts), and return values are plain dicts (`ProductionResult.to_dict()`).
  * **As-built bug to fix:** `MultiprocessingTaskRunner.run_task` (`dve/src/dve/adapters/multiprocessing_task_runner.py:135-136`) currently catches `Exception as exc` and sends `("failed", str(exc))` over the pipe, discarding `DataAcquisitionError.record` (and `DataAcquisitionError` itself lacked `__reduce__`). Both the pipe protocol (`("failed", error_record_dict)`) and `DataAcquisitionError.__reduce__` are fixed together (ADR-0006, ADR-0009).
* **Progress:** long-running façade functions accept `progress: Callable[[int, str], None]`, matching `mdg.produce_model_setup_data`.

### Consequences

* Good, because external-system changes replace a single adapter class while fast unit/service suites run in memory with zero external services.
* Good, because internal handoffs need no network protocol or broker while leaving a hash-verified, auditable artifact at every stage.
* Bad, because ports and fakes add boilerplate that must stay synchronized via adapter contract tests.
* Bad, because architectural boundaries rely on Python import discipline enforced in CI (`import-linter`).

### Confirmation

* `import-linter` (`<=2.0` on CPython 3.9, ADR-0021) enforces per-package contracts: `domain` imports only stdlib/`common`, `services` never imports `adapters`, and cross-CSC imports target only `<csc>` top-level façades or `common` along ADR-0004's acyclic graph.
* Adapter contract tests (`<csc>/tests/contract/`, ADR-0021) execute identical behavioral assertions against `Fake<Port>` and the real adapter.
* Every `INT-IF-01…05` façade handoff has an integration test verifying artifact hash validation and structured `ErrorRecord` propagation across a spawned child process.

## Pros and Cons of the Options

### Ports and Adapters per CSC with injected fakes (chosen)

* Good, because external uncertainty is isolated behind small ABCs and domain/service logic is fast to test without Docker or network access.
* Neutral, because `common` holds shared cross-CSC value objects (`ErrorRecord`, `ArtifactRef`, `ModelSchemaSnapshot`).
* Bad, because it introduces extra interface files and requires contract tests to keep fakes honest.

### Layered architecture without port inversion

* Good, because it has fewer abstractions and is familiar.
* Bad, because services bind directly to concrete data-access classes, requiring monkeypatching in tests.

### Direct external-library calls inside use cases

* Good, because it has the smallest initial line count.
* Bad, because business rules cannot be tested without live MySQL, Git, LDAP and graph servers.

### In-process façade calls passing persisted artifact references (chosen)

* Good, because it matches the single-host modular monolith (ADR-0004) and satisfies SRS artifact-recording and provenance requirements directly.
* Bad, because CSCs share one Python runtime version (CPython 3.9).

### Watched file-drop directories

* Good, because producers and consumers are loosely coupled on disk.
* Bad, because it introduces polling latency, partial-write races and untyped error propagation.

### Local message broker / queue

* Good, because it decouples execution timing.
* Bad, because large graph/telemetry payloads do not belong on a broker and no broker is allowed on the offline host (ADR-0004, ADR-0006).

### Internal HTTP microservices per CSC

* Good, because each CSC could deploy or scale independently.
* Bad, because it adds six local network services, auth/TLS plumbing and serialization overhead with no scaling need.

## More Information

* Code: `mdg/src/mdg/{domain,ports,services,adapters}`, `mdg/src/mdg/__init__.py`, `dve/src/dve/{domain,ports,services,adapters}`, `dve/src/dve/__init__.py`, `dve/src/dve/adapters/multiprocessing_task_runner.py`
* [SDD §2.3](../SDD.md), [SDP §4–5](../../planning/SDP.md)
* Related: ADR-0002, ADR-0004, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0011, ADR-0012, ADR-0013, ADR-0014, ADR-0019, ADR-0021
* Revisit if any CSC must be deployed onto a separate physical host or written in a non-Python runtime, which would promote its `INT-IF-*` façade boundary to an explicit RPC/HTTP adapter.
