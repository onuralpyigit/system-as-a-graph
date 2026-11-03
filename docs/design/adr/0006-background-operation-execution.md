# ADR-0006: Background operation execution and status delivery

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Reconcile |
| Traces | DVE.6, 9, 14–15, 24, 27, 78; SMM.30; QA-02, QA-08 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

Model Data production, model construction, verification, simulation and installation evaluation all take longer than an HTTP request. Users and automation clients must start these operations, see their progress and outcome, cancel them, and run them concurrently (DVE.6, 27, 78; SMM.30).

SDP §5 specifies Procrastinate (a PostgreSQL-backed task queue), with SSE for the UI and REST polling for the CLI. The code is built differently:

- `dve/worker.py` runs a Celery 5.2 worker with Redis as broker and result backend.
- Progress is published as task `STARTED` metadata (`percent`, `phase`).
- Log lines go to a Redis list per run (`RedisProductionLog`).
- Cancellation is `revoke(terminate=True)`.
- The UI polls `GET /api/mdg/tasks/<id>?after=<line>`.
- Results are kept with `result_expires = None`, so they live in Redis until Redis is cleared.

## Decision Drivers

* Operation records must be durable and traceable (DVE.24–25, QA-04), not lost when a cache is flushed.
* Cancellation, progress reporting and concurrency limits per operation class are needed (QA-02, QA-08).
* The pipeline (installation evaluation) must not be starved by interactive simulations (DVE.27, 78).
* Fewer stateful services is better for an on-premises, single-team deployment (QA-10).

## Considered Options

* Celery + Redis (as built)
* Procrastinate on PostgreSQL (SDP §5)
* Celery with Redis as broker only, and durable operation state in the relational store

## Decision Outcome

Chosen option: "Celery with Redis as broker only, and durable operation state in the relational store". Celery is already integrated and tested, and it has mature routing, concurrency, retry and revocation. The weakness of the current setup is using Redis as the *system of record* for results and logs; this option moves that state to PostgreSQL (ADR-0008).

* **Execution:** Celery workers consume named queues per operation class: `pipeline` (installation evaluation, DVE.71–78), `interactive` (Model Data production, model build, verification), and `simulation` (behavioral analysis). Each queue has its own worker concurrency (ADR-0033).
* **Operation records:** the API creates an operation record (ADR-0024) before enqueuing and passes its `operation_id` to the task. The Celery task ID is stored as an attribute, not used as the identifier. The worker writes state transitions (`queued → running → succeeded | failed | cancelled`), progress (`percent`, `phase`), interruption stage and error (DVE.24), and log lines to the relational store.
* **Redis:** broker only. The result backend is disabled or short-lived. Losing Redis loses queued messages but no history; queued operations are re-enqueued from their records (ADR-0037).
* **Task payloads:** carry identifiers only (operation, data source, model instance IDs), never credentials (ADR-0032).
* **Status delivery:** REST polling with an incremental cursor (`GET /api/v1/operations/{id}?log_after=<n>`, as built) is the contract for both UI and CLI. SSE may be added later as an optimization for the UI, behind the same resource model.

### Consequences

* Good, because operation history survives Redis restarts and can be queried for findings, reports and audit (ADR-0035).
* Good, because separate queues let the CI gate keep its own capacity.
* Good, because the existing worker, progress and cancel code is kept.
* Bad, because Redis remains a service to operate (also needed if ADR-0015 chooses FalkorDB).
* Bad, because operation state is written in two places (Celery and the database). The database is authoritative, and the worker must update it reliably.
* Follow-up: replace `RedisProductionLog` with a relational adapter behind the existing `IProductionLog` port, and set `result_expires`.

### Confirmation

* Integration test: flush Redis after an operation completes; its status, progress and logs remain retrievable.
* Integration test: a long `simulation` operation does not delay a queued `pipeline` operation.

## Pros and Cons of the Options

### Celery + Redis (as built)

* Good, because it works today, with progress and cancellation.
* Bad, because history lives in Redis with no expiry and no durability guarantees. Operation identifiers are Celery internals.

### Procrastinate on PostgreSQL (SDP §5)

* Good, because jobs are enqueued in the same transaction as the operation record, and there is no Redis.
* Bad, because it is less mature. Progress, cancellation and queue routing would be re-implemented, and existing code rewritten.

### Celery broker-only + relational operation state

* Good, because it keeps proven execution and gives durable records.
* Bad, because there are two stores to keep consistent.

## More Information

* Code: `dve/src/dve/worker.py`, `dve/src/dve/adapters/celery_production_runner.py`, `dve/src/dve/adapters/redis_production_log.py`
* Related: ADR-0008, ADR-0024, ADR-0032, ADR-0033, ADR-0037
