# ADR-0006: Operations: execution, concurrency and reliability

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, pipeline owners |
| Kind | Ratify |
| Traces | DVE.6–7, 9, 14–15, 17, 24, 27, 78; SMM.29–31; QA-02, QA-07, QA-08 |
| Resolves | DP-16 (SRS SMM.30 concurrent user/operation count) |
| Decide by | Wave A1 (2026-12-04); §4 retries and source health by Wave B (2027-01-22) |
| Supersedes | — |

## Context and Problem Statement

Model Data production, model construction, field-record parsing, synthetic data generation, AED preparation/binding, verification, behavioral analysis and installation evaluation all outlive an HTTP request:

* Interactive users and automation clients must start, monitor and cancel operations (DVE.6, 9, 14–15, 27).
* Production-pipeline and multi-user analysis/simulation operations must run concurrently and independently without interfering with one another, up to a concurrency target determined in critical design (SMM.30, DVE.78; DP-16).
* Multiple concurrent user sessions must read and edit a System Model without corrupting integrity or query consistency (SMM.29).
* Interrupted or failed operations must record the error cause, interrupted stage and timestamp (DVE.24).
* Accessibility status of configured data sources must be displayed continuously and traceably (DVE.7).

Earlier SDP §5 drafts proposed Procrastinate on PostgreSQL, and an early prototype used Celery + Redis. Commit `1157784` removed Celery, Redis and Docker to fit the containerless offline host (ADR-0004), replacing them with `MultiprocessingTaskRunner`.

## Decision Drivers

* Zero external queue/broker daemons to install and operate offline (QA-10).
* Process-level memory and crash isolation per operation, with clean process-group cancellation (QA-02, QA-08).
* Guaranteed capacity for CI deployment-pipeline evaluations even when heavy simulations are queued (DVE.27, 78).
* Snapshot-consistent reads and race-free working-model edits across parent threads and spawned children (SMM.29).
* Durable operation, stage-interruption and log records across restarts of `dsm` (DVE.24–25, QA-04).

## Considered Options

* Execution: Spawned child process per operation behind `ITaskRunner`, persisted in SQLite (as built, extended)
* Execution: Celery worker with Redis broker
* Execution: Procrastinate on PostgreSQL (earlier SDP §5)
* Write concurrency: Optimistic revision checks with pre-spawn snapshot isolation
* Write concurrency: Pessimistic session locks
* Write concurrency: Last write wins
* Capacity management: Per-class FIFO queues with reserved limits
* Capacity management: Single shared concurrency pool (as built)

## Decision Outcome

Chosen options: **a spawned child process per operation persisted in SQLite**, **optimistic revision checks with pre-spawn snapshot isolation**, and **per-class FIFO queues with reserved limits**. Standard-library `spawn` isolates memory spikes and crashes per operation with zero extra services, while SQLite persistence (ADR-0007) and class queues provide durability and pipeline isolation.

### 1. Execution lifecycle

**As built (`1157784`):**

* `ITaskRunner` (`dve/src/dve/ports/task_runner.py`) and `ITaskLog` (`ports/task_log.py`) backed by `MultiprocessingTaskRunner` (`adapters/multiprocessing_task_runner.py`) and `InMemoryTaskLog`.
* One `spawn` daemon child process per task (`uuid4().hex`), sending `log`, `progress`, `done`, and `failed` tuples over a simplex `Pipe` to a parent watcher thread; capped at `os.cpu_count()` with a single FIFO `deque`.
* UI polls `GET /api/mdg/tasks/<id>?after=<n>` every `1000 ms` (`RUN_POLL_MS`), stopping after 5 consecutive transport errors.
* **As-built defects and gaps identified during code audit (fixed in R3):**
  1. State and logs live only in RAM and vanish on `dsm` restart; `_tasks` and `_lines` never evict finished entries.
  2. `status(unknown_id)` (`multiprocessing_task_runner.py:182`) returns `200 PENDING` instead of `404`, and `cancel(unknown_id)` (`line 195`) inserts a permanent phantom `REVOKED` entry into `_tasks` (unbounded memory leak).
  3. `run_task` (`line 135`) converts exceptions to `str(exc)`, losing `ErrorRecord`, and `cancel()` (`line 134, 199`) marks `REVOKED` without recording the interrupted `stage` (`progress_phase`), cause or timestamp required by DVE.24.
  4. `terminate()` kills only the direct child Python process; `git` and `gmake` subprocesses are not placed in their own process group (`start_new_session=True`), risking orphaned grandchildren on cancel.
  5. Any signed-in user knowing a `task_id` can cancel another user's task (`api.py:374`).

**Target execution contract (To build):**

* **Durable SQLite backing:** before spawning, the API inserts a `common_operation` row (ADR-0007) and uses `operation_id` as the task ID. Unknown IDs return `404`. The watcher thread persists state transitions, `progress_percent`, `progress_phase`, structured `ErrorRecord` dicts, and `operation_log` rows (`0`-based `seq`, preserving `?after=-1` cursor compatibility with `app.js`).
* **Complete interruption recording (DVE.24):** every non-success exit—uncaught exception, unexpected child exit code, user/API `cancel()`, `SIGTERM` (`stage = shutdown`), and start-up recovery of orphaned `queued`/`running` rows (`stage = interrupted`)—records an `ErrorRecord` containing the failure/cancellation cause, the exact active `progress_phase` at interruption, and the UTC timestamp.
* **Process-group cleanup:** external tools (`git`, `gmake`) run with `start_new_session=True`, and the child's `SIGTERM` handler kills any active subprocess group (`os.killpg`) before raising `Cancelled`.
* **Start-up orphan sweep:** alongside marking stale `queued`/`running` rows `failed (interrupted)`, start-up deletes any orphaned `candidate` or temporary working-snapshot graph instances left in the graph store (ADR-0011) so crashed runs never leak against the live-instance cap (§3).

### 2. Concurrency control and isolation (SMM.29)

* **Race-free snapshot reads:**
  * Operations against an immutable `baseline` or `candidate` instance read `(instance_id, revision = 0)` directly.
  * When an operation is submitted against a mutable `working` model, **the API process acquires that instance's in-process `threading.RLock`, copies the working model at its committed `revision` into a read-only `snapshot` instance (ADR-0011), and releases the lock before spawning the child process.** The child never copies a working model concurrently with an in-flight edit, preventing torn reads. The temporary snapshot is deleted when the operation finishes.
* **Atomic optimistic writes:**
  * Working-model edits (`apply_edit`, `undo_edit`, ADR-0011) execute in the API process under the per-instance `threading.RLock`.
  * Each request supplies `expected_revision`; SMM atomically checks and bumps `revision` in `smm_model_instance` (`UPDATE smm_model_instance SET revision = revision + 1 WHERE instance_id = ? AND revision = ?`), returning `409 Conflict` with the current revision on mismatch, and commits the structural mutation plus re-derived `DEPENDS_ON` edges in one graph-store transaction before releasing the lock.

### 3. Per-class queues, non-deadlocking coordinators and limits (SMM.30, DP-16)

Every `common_operation.type` (ADR-0007) maps to one of three isolated FIFO queues configured in `[operations]` of `dve.ini` (sized for the 10+ core reference host of ADR-0020):

| Runner queue | Assigned `operation.type` values | Max concurrent child processes | Notes |
|---|---|---|---|
| `pipeline` | Per-unit `installation_evaluation` | `4` | Reserved exclusively for CI/CD pipeline runs; never starved by interactive or simulation work |
| `interactive` | `model_data_production`, `model_construction`, `field_record_ingestion`, `aed_production`, `aed_binding`, `structural_verification` | `4` | Short-to-medium operator workflows |
| `simulation` | `synthetic_data_production`, `simulation_analysis`, `field_analysis` | `2` | CPU- and memory-intensive analytical runs |

* **Non-deadlocking multi-unit evaluations (DVE.78):** when an automation request submits $N$ candidate units in one batch, the parent batch `operation` row is a **non-process coordinator record** in SQLite (`executor_ref = NULL`). Only the per-unit child `installation_evaluation` operations occupy `pipeline` worker slots (and each unit worker invokes `mdg` and `smm` in-process inside its own child rather than enqueueing nested tasks). Thus four concurrent multi-unit CI pipelines can never deadlock waiting for child slots on the same queue.
* **Session and model caps:**

  | Resource limit | Initial value | Enforcement |
  |---|---|---|
  | Concurrent active interactive user sessions | `20` | SQLite active-session count; excess logins or requests beyond queue limits receive `429` (`rate_limited`) |
  | Working models per user | `5` | `smm_model_instance` count (`kind = 'working'`); `429` with `ErrorRecord` |
  | Total live graph instances (baselines + working + active candidates/snapshots) | `200` | `smm_model_instance` count; `429` with `ErrorRecord` |

### 4. Source health monitoring and retry policy (open, decide by Wave B)

* **Question:** how are continuous data-source accessibility tracking (DVE.7) and transient-fault retries/idempotency (DVE.6, 14–15; QA-08) parameterized?
* **Mandatory constraint for DVE.7:** SRS DVE.7 requires *continuously and traceably* displaying the accessibility status of all configured data sources—fail-fast during runs alone is insufficient. Wave B will fix the background/on-demand probe interval, timeout, `common_source_health` retention in SQLite (ADR-0007), and UI status-indicator states, alongside per-class idempotency keys (`Idempotency-Key` header) and bounded transient network retry rules for `EXT-IF-01…04`.

### Consequences

* Good, because zero queue/broker servers are added offline, pipeline slots cannot be starved by simulations, and multi-unit CI batches cannot self-deadlock.
* Good, because pre-spawn snapshot copying under the instance lock guarantees strict snapshot isolation under concurrent working-model edits.
* Bad, because throughput is bounded by one host (~1 s `spawn` overhead per operation and temporary graph snapshot cost on working-model runs).
* Bad, because an OS reboot or `dsm` crash aborts in-flight child processes as `failed (interrupted)` rather than resuming mid-run.

### Confirmation

* `dve/tests/adapters/test_multiprocessing_task_runner.py` plus new tests verify: `404` on unknown `task_id` `status`/`cancel` (zero memory leak), grandchild process-group cleanup on `cancel()`, and preserved `stage`/`ErrorRecord` on exception, crash, cancel, `SIGTERM`, and start-up recovery.
* Queue isolation test: 4 running/queued `simulation` tasks never delay a newly submitted `pipeline` task, and 4 simultaneous multi-unit `pipeline` batches complete without deadlock.
* Concurrency test: editing a working model concurrently with a running verification yields identical verification findings to the pre-edit revision, while conflicting `expected_revision` edits return `409`.

## Pros and Cons of the Options

### Spawned child process per operation with SQLite persistence (chosen)

* Good, because it uses Python's standard library, isolates memory/crashes per operation, and needs no broker service offline.
* Bad, because it is single-host only and incurs process-spawn overhead.

### Celery worker with Redis broker

* Good, because distributed queues and retry primitives are built in.
* Bad, because operating Redis and separate worker daemons offline adds deployment complexity removed in `1157784`.

### Procrastinate on PostgreSQL (earlier SDP §5)

* Good, because task queueing shares ACID transactions with relational records.
* Bad, because SaaG uses embedded SQLite rather than a PostgreSQL server (ADR-0007).

### Optimistic revisions with pre-spawn snapshot isolation (chosen)

* Good, because readers and writers never block each other over human think-time and snapshots cannot read half-written edits.
* Bad, because concurrent editors on the same working model must handle `409 Conflict`, and working-model runs temporarily copy the instance.

### Pessimistic session locks

* Good, because edits never conflict once locked.
* Bad, because abandoned browser tabs stall collaborators and require lock-stealing timeouts.

### Last write wins

* Good, because it needs no revision plumbing.
* Bad, because silent lost updates and mid-query mutations violate SMM.29.

### Per-class FIFO queues with reserved limits (chosen)

* Good, because CI deployment evaluations have guaranteed concurrency regardless of interactive/simulation load.
* Bad, because idle `pipeline` slots are not lent to `simulation` jobs.

### Single shared concurrency pool (as built)

* Good, because all CPU cores are pooled dynamically.
* Bad, because 10 long simulations starve CI pipeline evaluations, violating SMM.30 and DVE.27/78 responsiveness.

## More Information

* Code: `dve/src/dve/adapters/multiprocessing_task_runner.py`, `dve/src/dve/adapters/in_memory_task_log.py`, `dve/src/dve/services/task_service.py`, `dve/src/dve/domain/task_status.py`
* [SRS SMM.29–30, DVE.6–7, 24, 27, 78](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0005, ADR-0007, ADR-0009, ADR-0011, ADR-0018, ADR-0019, ADR-0020
* Revisit if R8 load testing shows single-host process spawning cannot meet ADR-0020 throughput budgets, requiring multi-host worker distribution.
