# ADR-0016: Model instances: baseline, working and candidate-evaluation models

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Decide |
| Traces | SMM.26, 29–31, 36; DVE.17, 28–30, 50–51, 71–78; MDG.15; QA-02, QA-03, QA-04 |
| Closes | CDR-29 (part: Working Model) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The SRS implies three kinds of System Model:

1. **Baseline model:** built from a Model Data file (SMM.4). It must never be altered by verification or analysis (DVE.29, 51) or by data binding (SMM.36).
2. **Working model:** "derived from the System Model", on which the user adds and removes nodes and relationships and runs verification (DVE.17).
3. **Candidate-evaluation model:** "a new, process-specific System Model" combining a candidate software unit version with the target system version (SMM.31). MDG.15 already produces a Model Data file with the candidate in the inventory (`is_candidate`).

These must coexist under concurrent users and pipeline operations without interfering (SMM.29–30).

## Decision Drivers

* Baselines are immutable by construction, not by convention (QA-03).
* Creating and discarding a working or candidate model must be cheap (QA-02).
* Working-model edits must be traceable and reportable (DVE.17, DVE.26, QA-04).
* Candidate evaluations from the pipeline run in parallel and independently (DVE.78).

## Considered Options

* A separate named graph per instance, with working models copied from their baseline
* A delta overlay: working models stored as a change set applied at query time over the baseline
* A full copy per operation: every verification run copies the baseline

## Decision Outcome

Chosen option: "A separate named graph per instance, with working models copied from their baseline". Each instance is an ordinary graph that rules query without special logic. Copying is cheap in the chosen store (ADR-0015, `GRAPH.COPY`). The edit history is still kept as a change log for traceability.

| Kind | Created from | Mutability | Owner | Lifetime |
|---|---|---|---|---|
| `baseline` | A Model Data file (SMM.4) | Immutable after construction | System | Retained per ADR-0040 |
| `working` | Copy of a baseline (or of another working model) | Edited through SMM's working-model API only | One user | Until deleted by the owner, or expired (ADR-0040) |
| `candidate` | Its own Model Data file produced with a candidate (MDG.15) | Immutable after construction | One operation | Deleted when its evaluation operation ends, after findings are persisted |

* **Registry:** each instance is a row in the relational store (ADR-0008), in a table with:
  * `instance_id`, `kind`, `parent_instance_id`;
  * `model_data_ref` and its hash;
  * project, platform and system version;
  * `created_by`, `created_at`, `status`, `revision`.

  The graph name is `model:<instance_id>`.
* **Immutability:** SMM's façade exposes write operations only for `working` instances. Verification and analysis receive a read-only handle (ADR-0007).
* **Edits (DVE.17):** each edit is a command (add/remove node, add/remove relationship, set attribute) that:
  1. is validated against the schema and structural integrity rules (ADR-0014);
  2. is applied to the working graph;
  3. is appended to the instance's change log with user and time;
  4. increments `revision`.

  Concurrency follows ADR-0033.
* **Operations reference instances:** every verification or analysis operation records `instance_id` and `revision` (ADR-0024), so results are reproducible.
* **Analytical data:** bound as a separable layer per ADR-0017. It is never written into a baseline's graph.

### Consequences

* Good, because rules need no awareness of overlays. Every instance is a plain graph.
* Good, because pipeline evaluations are fully isolated, one graph per operation.
* Good, because the change log gives an exact, reportable diff of each working model.
* Bad, because storage grows with the number of working models. It is bounded by expiry (ADR-0040) and the instance limits of ADR-0033.
* Bad, because a working model does not follow later baseline updates. Rebasing would replay the change log onto a new baseline, and it is not in scope now.

### Confirmation

* A test asserts that any write through SMM's API to a `baseline` or `candidate` instance fails.
* A test asserts that replaying a working model's change log on its parent baseline reproduces the working graph.
* A pipeline test runs two candidate evaluations in parallel and checks that neither sees the other's nodes.

## Pros and Cons of the Options

### Named graph per instance

* Good, because it is simple to query, isolation is strong, and it uses a native store primitive.
* Bad, because of storage per instance.

### Delta overlay

* Good, because it has minimal storage and keeps baseline updates visible.
* Bad, because every rule query must merge the overlay, which is complex and error-prone. Cypher has no native overlay semantics.

### Full copy per operation

* Good, because it gives maximum isolation.
* Bad, because it copies even when nothing changed, and working-model edits would be lost between operations.

## More Information

* Related: ADR-0007, ADR-0014, ADR-0015, ADR-0017, ADR-0024, ADR-0033, ADR-0040
