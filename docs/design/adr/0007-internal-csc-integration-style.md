# ADR-0007: Internal CSC integration style

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Decide |
| Traces | MDG.23; SCG.7; FDM.4; ADM.2–4; SMM.2, 27–28, 33; SDD §2.3 INT-IF-01…05 |
| Closes | CDR-24, CDR-25, CDR-26, CDR-27, CDR-28 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SDD §2.3 defines five internal interfaces:

| Interface | Handoff |
|---|---|
| INT-IF-01 | MDG → SMM, Model Data |
| INT-IF-02 | SCG → ADM, synthetic data |
| INT-IF-03 | FDM → ADM, field records |
| INT-IF-04 | ADM → SMM, Analytical Evaluation Data |
| INT-IF-05 | SMM → DVE, model access |

CDR-24…28 leave their "communication method/protocol" open. Today `dve` calls `mdg` through its package API (`mdg.produce_model_setup_data(...)`) inside a Celery task, and the result is a file on disk. ADR-0004 makes the CSCI one deployable with one package per CSC. The handoff method has to be decided before SMM is built.

## Decision Drivers

* Several SRS requirements say the handed-off data is *recorded* and *traceable*: MDG.23 ("save it as a Model Data file"), SCG.5, FDM.3, SMM.26 and SMM.35. A handoff must therefore leave a persisted, identifiable artifact.
* Every component runs in the same deployable (ADR-0004).
* Handoffs carry large payloads: whole models and data sets.
* The interfaces must stay replaceable and testable with fakes (ADR-0003).

## Considered Options

* In-process calls through each CSC's public façade, with persisted artifacts referenced by ID
* File drop: a producer writes to a shared directory, and a consumer polls it
* Message queue: CSCs publish and consume events through the broker
* Internal HTTP APIs between CSCs

## Decision Outcome

Chosen option: "In-process calls through each CSC's public façade, with persisted artifacts referenced by ID", because all CSCs run in the same process image. The SRS asks for recorded artifacts, not for messaging. The handoff is the artifact; the call only passes its identifier.

* **Method:** a consumer calls the producer CSC's façade functions (`<csc>/__init__.py`), never its internal modules. Calls run inside a worker task (ADR-0006) when they are long-running.
* **Payload:** the producer persists the artifact first and returns an artifact reference (ID, kind, location, content hash; ADR-0035). The consumer loads the artifact by reference.

| Interface | Producer call returns | Artifact store |
|---|---|---|
| INT-IF-01 MDG → SMM | Model Data file reference | Filesystem (ADR-0013) |
| INT-IF-02 SCG → ADM | Synthetic data set reference | Per ADR-0019 |
| INT-IF-03 FDM → ADM | Field record selection (record IDs) | Per ADR-0021 |
| INT-IF-04 ADM → SMM | Analytical Evaluation Data reference | Per ADR-0019 |
| INT-IF-05 SMM → DVE | Read-only model instance handle | Graph store (ADR-0015, 0016) |

* **INT-IF-05 access:** DVE gets a model access object from SMM's façade. The object only exposes queries and is bound to one model instance. Writes go through SMM's working-model API (ADR-0016), never through the handle.
* **Errors:** façade functions raise domain errors carrying an error record (ADR-0034).

### Consequences

* Good, because there is no network protocol, serialization layer or versioned wire format inside the CSCI.
* Good, because every handoff is a persisted, hashable artifact, which satisfies the traceability requirements directly.
* Bad, because splitting a CSC into a separate service later would need a new interface; ADR-0004 rules this out for now.
* Bad, because CSC boundaries depend on import discipline (enforced in CI, ADR-0003/0004).

### Confirmation

* `import-linter`: consumers import only `<csc>` (the façade), not `<csc>.services` or `<csc>.adapters`.
* Each façade function has a contract test with a fake producer artifact.

## Pros and Cons of the Options

### In-process façade calls with persisted artifacts

* Good, because it is the simplest option, and it matches the deployable and the SRS recording requirements.
* Bad, because it couples CSCs to a shared runtime.

### File drop

* Good, because it gives loose coupling.
* Bad, because of polling and partial-file races, and no typed contract.

### Message queue

* Good, because it is asynchronous and decoupled.
* Bad, because large payloads don't belong on the broker, and the stages are already sequenced by the operations of ADR-0006.

### Internal HTTP

* Good, because it is ready for a later service split.
* Bad, because it would add network failure modes inside one deployable for no current benefit.

## More Information

* [SDD §2.3](../SDD.md), [CDR §1.4](../CDR.md)
* Related: ADR-0003, ADR-0004, ADR-0013, ADR-0016, ADR-0019, ADR-0035
