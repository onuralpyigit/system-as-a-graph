# ADR-0003: Decompose the CSCI into one package per CSC with façade handoffs

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-13 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Reconcile |
| Traces | QA-10, QA-11; MDG.23; SCG.7; FDM.4; ADM.2–4; SMM.2, 27–28, 33; DVE.27; SDD §2.2, §2.3 INT-IF-01…05; BACKLOG T3; SDP §4, §5 |
| Closes | CDR-24, CDR-25, CDR-26, CDR-27, CDR-28 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — (merges the three unaccepted drafts *Ports and Adapters per CSC*, *Deployable units and repository layout* and *Internal CSC integration style*, retired by the 2026-11-13 renumbering) |

## Context and Problem Statement

The SRS decomposes the CSCI into six CSCs. SDP §4 describes a repository with `msd/ scg/ frd/ adp/ csm/ vae/`; the repository actually has `mdg/` (a library) and `dve/` (a Flask API and UI over `mdg`), and SCG, FDM, ADM and SMM have no code. No document owns the CSC → directory mapping ([BACKLOG](../../planning/BACKLOG.md) finding T3), and CDR-24…28 leave the communication method of the five internal interfaces (SDD §2.3 INT-IF-01…05) open. SMM is built in R3, so both must be fixed before then. One question: how is the CSCI decomposed into code, and how do the parts hand data to each other?

## Decision Drivers

* One team, on-premises deployment with Docker Compose and no orchestration (SDP §5).
* The CSCs are sequential stages that exchange large artifacts (SDD §2.2), and the SRS requires the handed-off data to be *recorded*: MDG.23 ("save it as a Model Data file"), SCG.5, FDM.3, SMM.26, SMM.35.
* SRS traceability needs a visible one-to-one CSC → directory mapping (BACKLOG T3).
* Several external systems are only partly known (CDR-09, CDR-19, CDR-21). They must sit behind ports with fakes so that domain logic is testable without them (QA-11).
* `mdg/` and `dve/` already follow the pattern; deviating from it means rework.
* Concurrent operations must be isolated from one another (SMM.30). That is a runtime property, not a deployment one.

## Considered Options

Each option fixes the repository layout, the internal structure of a CSC and the handoff method at once.

* One Python distribution per CSC in one repository, Ports and Adapters inside each package, in-process calls through the public façade over persisted artifacts (as built)
* One deployable service per CSC with internal HTTP or broker APIs, layered code inside each service
* One Python distribution per CSC, layered code inside (controllers → services → repositories), file-drop handoff through a shared directory
* The SDP §4 repository layout with its directory names, layered

## Decision Outcome

Chosen option: "One distribution per CSC, Ports and Adapters, in-process façade handoffs", because the CSCs are sequential stages owned by one team. Separate services would add network contracts, deployment units and failure modes with no independent-scaling or ownership need, and the SRS asks for recorded artifacts, not for messaging. The pattern is already implemented and tested in `mdg/` and `dve/`.

**Repository layout.**

```
mdg/  scg/  fdm/  adm/  smm/  dve/   one Python distribution per CSC: <csc>/setup.py, <csc>/src/<csc>/, <csc>/tests/
dev/                                 development-only mock data sources (as today)
docs/
no web/                              ADR-0004 keeps the front end inside dve/src/dve/templates and static/
```

Only `mdg/` and `dve/` exist today. The image, the configuration and the environments are ADR-0034's to decide, and where cross-CSC types live is [ADR-0029](0029-validation-and-error-records.md)'s to decide.

**Required layers per package.** No other layout detail is fixed here.

| Directory | Contains | May import |
|---|---|---|
| `domain/` | Immutable value objects and entities (`@dataclass(frozen=True)`), domain errors | standard library only |
| `ports/` | Abstract interfaces named `I<Name>` (ABCs) and the port-specific exceptions | `domain` |
| `services/` | Use cases, one class per use case, depending on ports only | `domain`, `ports` |
| `adapters/` | Implementations of the ports, named `<Technology><Port>`, e.g. `GitSourceCodeRepository`, `LdapDirectoryService` | `domain`, `ports`, third-party libraries |
| `__init__.py` | The CSC's public façade: factory functions that wire adapters to services (e.g. `mdg.produce_model_setup_data`) | everything in its own package |

* How `adapters/` is subdivided, and where the web/UI layer is placed, are not decided here (ADR-0004 keeps the front end inside `dve`, ADR-0036 for adapter contract tests). `mdg` groups adapters by area and `dve` does not, and both keep an `.ini` loader at `config.py`; both forms conform.
* Fakes live under `<csc>/tests/fakes/` as `Fake<Port>`, with a shared `seed.py`. They implement the same port.
* A mock adapter that stands in for an unknown external system in production code (as `LdapDirectoryService` and `SystemRepoParser` do today) says so in its first docstring line (`Mock: …`). It must be replaced before the release that needs the real system.
* Other CSCs use a CSC only through its façade.

**Handoff.** A consumer calls the producer CSC's façade functions, never its `services/` or `adapters/`. The producer persists the artifact first and returns an artifact reference (ID, kind, location, content hash; [ADR-0030](0030-traceability-and-provenance.md)); the consumer loads the artifact by reference. Long-running calls run inside a background operation ([ADR-0004](0004-operations-panel-runtime-stack.md)).

| Interface | Producer call returns | Artifact store |
|---|---|---|
| INT-IF-01 MDG → SMM | Model Data file reference | Filesystem ([ADR-0008](0008-model-data-file-format.md)) |
| INT-IF-02 SCG → ADM | Synthetic data set reference | Per ADR-0014 |
| INT-IF-03 FDM → ADM | Field record selection (record IDs) | Per ADR-0016 |
| INT-IF-04 ADM → SMM | Analytical Evaluation Data reference | Per ADR-0014 |
| INT-IF-05 SMM → DVE | Read-only model instance handle | Graph store ([ADR-0010](0010-graph-storage-technology.md), [ADR-0011](0011-model-instances.md)) |

* **INT-IF-05 access:** DVE gets a model access object from SMM's façade. The object only exposes queries and is bound to one model instance. Writes go through SMM's working-model API ([ADR-0011](0011-model-instances.md)), never through the handle.
* **Errors:** façade functions raise domain errors carrying an error record ([ADR-0029](0029-validation-and-error-records.md)).

**Dependency direction.** `dve` → `smm`, `adm`, `mdg`, `scg`, `fdm`; `adm` → `scg`, `fdm`; `smm` → `mdg` (Model Data types), `adm` (Analytical Evaluation Data types). No cycles.

**Process types are not decided here.** As built, `dve` runs one API process that spawns one child process per task and keeps task status in its own memory (`dve/src/dve/__init__.py` `runtime()`, `dve/src/dve/adapters/multiprocessing_task_runner.py`, `InMemoryTaskLog`), and there is no container image and no `deploy/` directory. Task execution and status delivery are decided by [ADR-0004](0004-operations-panel-runtime-stack.md); the image and the configuration are ADR-0034's.

### Consequences

* Good, because CSC boundaries stay visible one-to-one for SRS traceability, and deployment stays simple.
* Good, because there is no network protocol, serialization layer or versioned wire format inside the CSCI.
* Good, because every handoff is a persisted, hashable artifact, which satisfies MDG.23, SCG.5, FDM.3, SMM.26 and SMM.35 directly.
* Good, because each external-system decision (ADR-0005, 0006, 0015, 0025) only replaces one adapter, and the test suites already run without Docker services.
* Bad, because the boundaries are enforced by tooling and review rather than by the network.
* Bad, because all CSCs share one release cadence and one dependency set; a heavy dependency in one CSC is installed everywhere.
* Bad, because fakes must be kept in step with ports. Today `dve/tests/fakes/` keeps its own reduced copies of the `ISourceCodeRepository` and `IConfigManagementRepository` fakes and of `seed.py`, rather than importing `mdg`'s.
* Bad, because splitting a CSC into a separate service later would need a new interface.
* Follow-up: update SDP §4 to this layout; create the `scg/ fdm/ adm/ smm/` skeletons; ADR-0029 decides where the shared error record lives; [ADR-0004](0004-operations-panel-runtime-stack.md) keeps the multiprocessing task runner.

### Confirmation

* An `import-linter` *layers* contract per package enforces the import column of the table above.
* An `import-linter` *forbidden contract* per package: another CSC may import `<csc>` (the façade), not `<csc>.services` or `<csc>.adapters`.
* Each façade function has a contract test with a fake producer artifact; the same test cases run against the fake and the real adapter (ADR-0036).
* Review checklist: a new CSC directory uses one of the six canonical names, and a handoff returns a reference rather than an object graph.
* The repository has no CI configuration yet, so these are gates to add under ADR-0036, not checks that pass today.

## Pros and Cons of the Options

### One distribution per CSC, Ports and Adapters, façade handoffs (as built)

* Good, because external uncertainty is isolated behind ports and the design is testable without the external systems.
* Good, because it matches the code that exists, so no rework.
* Good, because it is the simplest option for a sequential pipeline in one deployable, and the recorded artifact satisfies the traceability requirements.
* Bad, because there are more files and interfaces than a layered design needs, and extra indirection on simple paths.
* Bad, because it couples the CSCs to a shared runtime, and all of them share one dependency set and release cadence.

### Service per CSC

* Good, because boundaries are hard, deployment is independent, and the internal interfaces become visible network contracts.
* Bad, because it is six services, six APIs and six versioning problems for one team, with Docker Compose and no orchestration.
* Bad, because large artifacts would cross a network boundary inside one CSCI for no requirement that asks for it.

### Packages with layered code and file-drop handoff

* Good, because it has the fewest interfaces, and a shared directory decouples producer from consumer in time.
* Bad, because repositories are usually bound to one persistence technology, so fakes need mocking frameworks instead of port implementations.
* Bad, because a dropped file gives no typed contract, and partial-file and polling races appear exactly where payloads are largest.

### SDP §4 layout

* Good, because it is already written down in an approved document.
* Bad, because its names (`msd`, `frd`, `adp`, `csm`, `vae`) contradict the canonical component identifiers (ADR-0002), so the CSC → directory mapping the SRS needs would still not exist.
* Bad, because it fixes a layout the code does not have, leaving the mapping unowned, which is BACKLOG finding T3.

## More Information

* Code: `mdg/src/mdg/{domain,ports,services,adapters}`, `mdg/src/mdg/__init__.py` (the façade), `dve/src/dve/__init__.py` (runtime wiring), `dve/src/dve/adapters/`
* [ADR Roadmap](../ADR-ROADMAP.md), [CDR register](../CDR.md) §1.4, [SDD §2.3](../SDD.md)
* Related: ADR-0002 (component identifiers), ADR-0004, ADR-0008, ADR-0011, ADR-0029, ADR-0030, ADR-0034, ADR-0036
* Absorbs three drafts that were `Proposed` but never accepted — *Ports and Adapters per CSC*, *Deployable units and repository layout* and *Internal CSC integration style*. They have no numbers of their own: the 2026-11-13 renumbering reissued those slots.
* Revisit this decision if a CSC must be deployed, scaled or released independently of the others.
