# ADR-0006: Operations: execution, concurrency and reliability

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, pipeline owners |
| Kind | Ratify |
| Traces | DVE.6–7, 9, 14–15, 17, 24, 27, 78; SMM.29–31; QA-02, QA-07, QA-08 |
| Resolves | DP-16 (SRS SMM.30 concurrent user/operation count) |
| Decide by | Wave A (2026-11-27); §4 retries and source health by Wave B (2027-01-22) |
| Supersedes | — (absorbs the former ADR-0006 and the planned ADR-0006) |

## Context and Problem Statement

Model Data production, model construction, verification, simulation and installation evaluation all take longer than an HTTP request. The requirements on them are:

* Users and automation clients must start them, see progress and outcome, and cancel them (DVE.6, 14–15, 27).
* They must run concurrently and independently (SMM.30, DVE.78), for "a number of users" left to the critical design phase (DP-16).
* Concurrent sessions must read and write a model without losing integrity (SMM.29).
* Interruptions must be recorded with their stage (DVE.24).

SDP §5 specifies Procrastinate, a PostgreSQL-backed queue. The first implementation used Celery 5.2 with Redis. Commit `1157784` removed Celery, Redis and Docker, because the target host is offline and has no container runtime (ADR-0004), and replaced them with spawned child processes.

## Decision Drivers

* No extra server to install and operate on the offline host (QA-10).
* Cancellation, progress, and concurrency limits per operation class (QA-02, QA-08).
* A long simulation must not starve an evaluation started by the pipeline (DVE.27, 78).
* Running operations must give reproducible results under concurrent edits (SMM.29).
* Operation records must survive a restart of `dsm` (DVE.24–25, QA-04).

## Considered Options

* Execution: spawned child process per operation behind an `ITaskRunner` port (as built) / Celery with Redis / Procrastinate on PostgreSQL (SDP §5)
* Write control: optimistic revisions / pessimistic locks / last write wins
* Capacity: one shared limit (as built) / per-class queues with configured limits

## Decision Outcome

Chosen options: **a spawned child process per operation (as built)**, **optimistic revisions for working-model writes**, and **per-class queues with configured limits**. The runner uses only the standard library and isolates each operation in its own process, so a crash, a memory spike or a cancellation affects only that operation. Durability comes from SQLite records (ADR-0008), not from a broker.

### 1. Execution

**As built (`1157784`):**

* **Ports:**
  * `ITaskRunner.submit(target, *args) -> task_id`, plus `status` and `cancel` (`dve/src/dve/ports/task_runner.py`);
  * `ITaskLog.append` and `lines_since` (`ports/task_log.py`).
* **`MultiprocessingTaskRunner`** (`dve/src/dve/adapters/multiprocessing_task_runner.py`):
  * One `spawn` child per task, a daemon of the API process. Task IDs are `uuid4().hex`.
  * The child sends `log`, `progress`, `done` and `failed` events through a one-way `Pipe`. A watcher thread in the parent applies them.
  * At most `os.cpu_count()` tasks run at once. Further tasks wait in a FIFO as `PENDING`.
  * Cancel sends SIGTERM through `terminate()`. The child raises `Cancelled` and is recorded as `REVOKED`.
  * A child that exits without reporting is recorded as `FAILURE` ("task process exited with code N").
* **States:** `PENDING`, `STARTED`, `SUCCESS`, `FAILURE` and `REVOKED`, with `started_at` and `finished_at`. Progress is `percent` and `phase`, through mdg's `ProgressCallback`.
* **Logs:** `InMemoryTaskLog` keeps up to 5,000 lines per task. Only `dve` and `mdg` records at INFO or above are forwarded.
* **Status delivery:** the UI polls `GET /api/mdg/tasks/<id>?after=<n>` every second (`RUN_POLL_MS = 1000`) and stops after 5 consecutive failures.
* **Gap:** state and logs are lost when `dsm` restarts.

**To build:**

* **Durable records:** the API creates an `operation` row (ADR-0008) before `submit` and uses the operation ID as the task ID. The watcher thread writes state, progress, failure and log lines to SQLite. `InMemoryTaskLog` is replaced behind `ITaskLog`.
* **Restart recovery:** at start-up, every operation left `queued` or `running` becomes `failed`, with stage `interrupted` and the last recorded phase (DVE.24). On SIGTERM, the parent first marks running operations `cancelled` with stage `shutdown`.
* **Arguments:** picklable values only (ADR-0003), passed at spawn time and never through a broker. Credentials of unsaved connections may be passed this way, but never logged or recorded (ADR-0030).
* **Status contract:** REST polling with an incremental cursor for UI and CLI: `GET /api/v1/operations/{id}?log_after=<n>` (ADR-0005). `/api/mdg/tasks/...` becomes an alias over the same records.

### 2. Concurrency control (SMM.29)

* **Reads are snapshot-consistent:**
  * Verification and analysis read a fixed `(instance_id, revision)` (ADR-0015).
  * Before an operation starts on a working model, SMM copies it at the current revision into a short-lived instance, and the operation runs on that copy.
* **Writes are optimistic:**
  * Each edit carries `expected_revision`, and SMM applies it only if that matches. Otherwise it returns `409 Conflict` with the current revision.
  * The check is one SQLite statement on the instance registry: `UPDATE model_instance SET revision = revision + 1 WHERE instance_id = ? AND revision = ?`. It holds across the API process and its children.
  * Edits to one instance are applied by the API process under a per-instance `threading.Lock`. A single host and API process make a distributed lock unnecessary.
* **Baselines and candidates** have no writers after construction, so they need no locks.

### 3. Queues and limits (SMM.30, DP-16)

The runner keeps one FIFO and one limit per operation class, set in `[operations]` of `dve.ini`. If the sum of the class limits exceeds the CPU count, start-up logs a warning. The values below need at least 10 cores (ADR-0036), and the CDR Board and pipeline owners must confirm them before acceptance.

| Class | Runner queue | Initial concurrent operations | Notes |
|---|---|---|---|
| Installation evaluation (pipeline) | `pipeline` | 4 | Reserved; never shared |
| Model Data production, model construction, verification | `interactive` | 4 | |
| Simulation and field analysis | `simulation` | 2 | Long-running, CPU-heavy |

| Other limit | Initial value |
|---|---|
| Concurrent signed-in interactive users | 20 |
| Working models per user | 5 |
| Total live model instances | 200 |

* Requests beyond a queue's capacity wait as `queued`.
* Requests beyond a user or instance limit get `429` with an error record. The counts come from SQLite (ADR-0008, ADR-0030).
* **To build:** the per-class queues, the `[operations]` section, the counters, and SMM's revision check.

### 4. Reliability (open, decide by Wave B)

* **Question:** how are retries, idempotency and data-source health handled, beyond the restart recovery of §1 (DVE.6–7, 14–15, 24; QA-08)?
* **Options to weigh:**
  * retries with idempotency keys per operation class;
  * checkpoint and resume of long pipelines;
  * fail-fast with the recorded stage (current behaviour);
  * periodic health checks of connected data sources (DVE.7).

### Consequences

* Good, because there is no broker or queue server to install, secure or back up.
* Good, because each operation has its own address space, and pipeline capacity is reserved.
* Good, because running operations are reproducible regardless of concurrent edits, and conflicts are explicit.
* Bad, because the runner and its limits are bounded by one host. Scaling out needs a queue and a new decision (ADR-0036).
* Bad, because spawning costs about a second per operation, and a snapshot copy is made per operation on working models.
* Bad, because the parent process is a single point of failure for running operations, which are recorded as interrupted rather than resumed.

### Confirmation

* Existing tests in `dve/tests/adapters/test_multiprocessing_task_runner.py` cover success, failure, crash, concurrency, pending cancel, SIGTERM and log filtering.
* Restart test: an operation running at restart is reported `failed` with stage `interrupted`, and its earlier log lines are still retrievable.
* A long `simulation` operation does not delay a queued `pipeline` operation.
* While a verification runs on a working model, an edit commits, and the result matches a run on the pre-edit revision.
* Two edits with the same `expected_revision`: one succeeds and one gets `409`.
* Load test (R8): the limits hold, and pipeline latency stays within the ADR-0036 budget under full load.

## Pros and Cons of the Options

* Child process per operation (as built): Good, because it uses only the standard library and is tested. Bad, because durability needs its own persistence, and it does not scale beyond one host.
* Celery with Redis: Good, because it has mature routing and retries. Bad, because Redis and the worker are extra services on an offline host, which is why they were removed in `1157784`.
* Procrastinate on PostgreSQL: Good, because enqueueing and records share a transaction. Bad, because it needs a PostgreSQL server, which ADR-0008 does not adopt.
* Optimistic revisions: Good, because they never block. Bad, because the UI must handle `409`. Pessimistic locks block users and go stale. Last write wins silently loses edits, which violates SMM.29.
* Per-class limits: Good, because pipeline capacity is guaranteed. Bad, because some capacity may sit idle. A shared limit risks starving the pipeline.

## More Information

* Code: `dve/src/dve/adapters/multiprocessing_task_runner.py`, `dve/src/dve/adapters/in_memory_task_log.py`, `dve/src/dve/services/task_service.py`, `dve/src/dve/domain/task_status.py`
* [SRS SMM.30](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0005, ADR-0008, ADR-0015, ADR-0030, ADR-0036
