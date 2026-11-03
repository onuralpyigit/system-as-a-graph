# ADR-0033: Concurrency control and operation limits

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, pipeline owners |
| Kind | Decide |
| Traces | SMM.29–31; DVE.17, 27, 78; QA-02, QA-07 |
| Closes | CDR-16 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SMM.29 requires concurrent read and write by multiple sessions on the same System Model without loss of integrity or result consistency. SMM.30 requires pipeline operations and the analysis or simulation operations of "a number of users — to be determined during the critical design phase" to run concurrently and independently (CDR-16). DVE.78 requires parallel installation evaluations.

ADR-0016 already isolates baselines (immutable), working models (one owner) and candidate models (one operation). Two questions remain: how concurrent writes to one working model are handled, and what the capacity limits are.

## Decision Drivers

* The results of an operation must not change because of a concurrent edit (SMM.29).
* CI pipeline evaluations must keep their capacity under interactive load (DVE.27, 78).
* The limits must be explicit and configurable, so that the hardware can be sized for them (ADR-0036).

## Considered Options

* Write control: pessimistic locks per working model / optimistic concurrency with revision numbers / last write wins
* Capacity: a single shared worker pool / per-class queues and worker pools with configured limits

## Decision Outcome

Chosen options: **optimistic concurrency with revision numbers** for working-model writes, and **per-class queues with configured limits** for operations.

* **Reads are snapshot-consistent:**
  * Verification and analysis operations read a fixed `(instance_id, revision)` (ADR-0016, ADR-0024).
  * Before an operation starts on a working model, SMM takes a copy of it at the current revision (`GRAPH.COPY`, ADR-0015). The operation runs on that copy.
  * Later edits therefore never change a running operation's input.
* **Writes are optimistic:**
  * Each working-model edit command carries `expected_revision`.
  * SMM applies it only if it matches the current revision, then increments the revision. Otherwise it returns `409 Conflict` with the current revision, and the UI reloads and re-applies.
  * Edits to one instance are serialized by a short per-instance lock, held only while the command is applied.
* **Baselines and candidates:** they have no writers after construction, so they need no locking.
* **Queues and limits (closes CDR-16):** operations go to Celery queues (ADR-0006) with separate worker pools. The initial configured values are listed below. They must be confirmed by the CDR Board and pipeline owners before this ADR is accepted.

  | Class | Queue | Initial concurrent operations | Notes |
  |---|---|---|---|
  | Installation evaluation (pipeline) | `pipeline` | 4 | Reserved; never shared with other classes |
  | Model Data production, model construction, verification | `interactive` | 4 | |
  | Simulation and field analysis | `simulation` | 2 | Long-running, CPU-heavy |

  | Other limit | Initial value |
  |---|---|
  | Concurrent signed-in interactive users | 20 |
  | Working models per user | 5 |
  | Total live model instances (all kinds) | 200 |

  Requests beyond a queue's capacity wait in the queue with status `queued`. Requests beyond an instance limit are rejected with a clear error.

### Consequences

* Good, because running operations are reproducible regardless of concurrent edits.
* Good, because the pipeline has guaranteed capacity, which removes the risk of CI waiting behind simulations.
* Good, because the limits are explicit numbers that ADR-0036 can size hardware against.
* Bad, because a snapshot copy is made per operation on working models (cheap per ADR-0015, but not free).
* Bad, because simultaneous edits by two tabs or users on one working model get conflicts. Working models have one owner (ADR-0016), so this should be rare.

### Confirmation

* Concurrency test: while a verification runs on a working model, an edit commits. The verification result matches a run on the pre-edit revision.
* Conflict test: two edits with the same `expected_revision`. One succeeds and one gets `409`.
* Load test (R8): the configured limits are held, and pipeline latency stays within the ADR-0036 budget under full interactive and simulation load.

## Pros and Cons of the Options

### Pessimistic locks

* Good, because there are no conflicts to handle.
* Bad, because long-held locks block users, and a lost client leaves the lock stale.

### Optimistic revisions

* Good, because it never blocks, and conflicts are explicit.
* Bad, because the UI must handle `409` responses.

### Last write wins

* Good, because it is trivial.
* Bad, because edits are silently lost, which violates SMM.29.

### Single shared pool vs per-class pools

* Shared: Good, because it gives maximal utilization. Bad, because the pipeline can be starved.
* Per-class: Good, because capacity is guaranteed. Bad, because some capacity may sit idle.

## More Information

* [CDR-16](../CDR.md)
* Related: ADR-0006, ADR-0015, ADR-0016, ADR-0024, ADR-0036
