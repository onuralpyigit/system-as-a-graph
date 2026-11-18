# ADR-0004: Operations Panel runtime stack: web framework, task execution, persistence and front end

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-13 |
| Deciders | CDR Board |
| Consulted | Development team, UX, platform team |
| Kind | Reconcile |
| Traces | DVE.1–27, 78; MDG.8, 14–15; SMM.26, 30; QA-02, 04, 06, 07, 08, 11, 12; UXD §1–7 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — (merges the three unaccepted drafts *Backend web framework and API style*, *Background operation execution and status delivery* and *Frontend application architecture*, and withdraws *Relational store for metadata, operations and findings* without a replacement decision; all four were retired by the 2026-11-13 renumbering) |

## Context and Problem Statement

Four drafts decided the Operations Panel's runtime stack: the web framework, how long-running operations run and report, where records are persisted, and how the front end is built. They were written from SDP §5 and the UXD, and described FastAPI, Celery + Redis, PostgreSQL and Next.js; two of them justified their choice by what was "as built". None of it was built. The claimed Celery worker, Redis result backend, `RedisProductionLog` and single 1,950-line UI script do not exist anywhere in the tree, so this record is rewritten from the code instead of edited.

What the code does today, at `d74ad05`:

| Topic | As built | Evidence |
|---|---|---|
| Web framework | Flask 2.3.2 + Flask-WTF, 18 routes in 395 lines, hand-written body validation | `dve/setup.py`, `dve/src/dve/api.py:77-85, 121-378` |
| Sessions | Flask signed cookie (`Lax`), `GET /api/csrf-token`, per-session data-source guards | `api.py:124-127, 143-155, 215-219` |
| Task execution | one API process, one spawned child per task, FIFO queue, `concurrency = max(1, cpu_count)`, cancel by `terminate()` | `dve/src/dve/adapters/multiprocessing_task_runner.py:155-256` |
| Task state and log | `TaskStatus` in the runner's own dict, `InMemoryTaskLog` capped at 5,000 lines, both gone when the API process exits | `dve/src/dve/domain/task_status.py:10`, `adapters/in_memory_task_log.py:12-37`, `api.py:381-387` |
| Status delivery | `POST /api/mdg/run` answers `202` + `task_id`; `GET /api/mdg/tasks/<id>?after=<line>` polls status and log | `api.py:348, 361-376` |
| Persistence | Model Setup Data files on the filesystem, task state and data-source credentials in memory; no ORM, no migrations, no store server | `dve/src/dve/__init__.py:51-59`; no import of Celery, Redis, SQLAlchemy or Alembic in `dve/`, `mdg/`, `dev/` |
| Front end | one Jinja template with 8 views; `app.js` 2,537, `graph.js` 2,766, `app.css` 3,541 lines; AntV G6 vendored at 1.38 MB; self-hosted fonts | `dve/src/dve/templates/index.html:154-513`, `dve/src/dve/static/` |
| Tooling | no CI, no container image, no `deploy/`, no OpenAPI document | repository root |

## Decision Drivers

* DVE.27 and DVE.78 need a contract an automation client can rely on; that is a published contract, not a framework.
* Request and acquisition errors must reach one error-record shape ([ADR-0029](0029-validation-and-error-records.md)).
* Operation records must be durable and traceable (DVE.24–25, QA-04), which the code does not do today.
* Cancellation, progress and concurrency limits are needed per operation class (DVE.6, 9, 14–15; QA-02, QA-08; [ADR-0028](0028-concurrency-control.md)).
* QA-10: an on-premises, single-team deployment gains from every service not operated.
* The UI grows from the eight views it has to the ten screens the UXD names, with a graph editor, virtualized tables and charts (UXD §4, §6).
* The change is cheapest now: the API is 18 routes and R3 builds on whatever this record fixes.

## Considered Options

* **Framework:** Flask 2.3 + Flask-WTF (as built) · FastAPI with Pydantic (SDP §5) · Django REST Framework
* **Task execution:** multiprocessing with an in-memory log (as built) · Celery + Redis (the retired draft) · Procrastinate on PostgreSQL (SDP §5)
* **Persistence:** files + memory (as built) · PostgreSQL (SDP §5) · MySQL/MariaDB (the engine already in `dev/compose.yaml`)
* **Front end:** Jinja + hand-written JS + vendored G6 (as built) · React SPA built with Vite (the retired draft) · Next.js 14 + Refine + shadcn/ui (SDP §5, UXD)

## Decision Outcome

### Web framework and API style

Chosen option: "Flask 2.3 + Flask-WTF (as built)", because the framework already carries the three layers the API depends on — signed-cookie sessions, CSRF token issuance and per-session data-source guards — and R3 grows the API rather than the framework's job.

* **Kept:** `create_app`, `_json_body`, the `login_required` and `connected()` decorators and the CSRF and 413 handlers stay; there is no port, no parallel schema definition and no session rework.
* **The current surface is the v1 baseline:** no version prefix, `/api/mdg/*` under the resource that owns the task, `202` + `{"task_id": ...}`, states `PENDING/STARTED/SUCCESS/FAILURE/REVOKED`, and `{"error": "message"}` plus a `csrf` flag on refusals.
* **Deferred to the automation-client contract (ADR-0023, Wave E, closes CDR-23):** the `/api/v1` prefix, the nested `{"error": {code, message, details}}` body, the machine-readable result schema and the exit codes (DVE.27, 78). A version prefix is cheap to add once and expensive to add twice, so it is decided with the client that consumes it.
* **Validation:** bodies keep their hand-written checks until [ADR-0029](0029-validation-and-error-records.md) lands, when they produce the shared error record instead of a message string.

### Background operation execution

Chosen option: "multiprocessing with an in-memory task log (as built)", because the runner, the log and the polling contract work, are tested, and already sit behind ports (`ITaskRunner`, `ITaskLog`) that let another executor replace them without touching the domain or the API. Celery + Redis would be a new integration and a new stateful service, not the low-cost option the retired draft claimed.

* **Adapters of record:** `MultiprocessingTaskRunner` (spawn, one child per task, `log`/`progress`/`done`/`failed` events over a pipe) and `InMemoryTaskLog`; the polling contract is unchanged.
* **Gaps accepted with this decision:** a restart discards operation history, results and logs; a log that reaches 5,000 lines stops collecting; one concurrency bound covers every operation class; there is no priority, retry, checkpoint or worker on another process or host.
* **Revisit triggers, stated as conditions:** operation records must survive a restart or be queried for findings, reports and audit ([ADR-0019](0019-findings-and-operation-records.md), DVE.24–25, QA-04); a second process or host must run tasks; one operation class must be shielded from another's capacity (DVE.27, 78, [ADR-0028](0028-concurrency-control.md)); a run longer than the log cap must stay retrievable. Each trigger is answered by a new adapter behind the same ports, not by a rewrite.
* **Not here:** retries, idempotency and interruption stages (ADR-0032), and worker-pool sizing ([ADR-0028](0028-concurrency-control.md)).
* **Open gap this record exposes:** the task payload carries `user_info = "user:password"` into the child process (`data_source_service.py:41`, `task_service.py:68-69`). [ADR-0027](0027-secrets-and-credentials.md) requires payloads to carry identifiers only and must close this before any credential is persisted.

### Persistence

**No relational store is decided here, and the implementation as it stands needs none.** Model Setup Data goes to the filesystem, task state and credentials live in memory, and the directory service is a mock.

* **Requirements on any future store:** durable and transactional (QA-04); findings filtered and sorted on many fields (DVE.23); reproducible, versioned migrations; room for server-side sessions ([ADR-0025](0025-authentication-and-sessions.md)), operation records and findings ([ADR-0019](0019-findings-and-operation-records.md)), the model-instance registry ([ADR-0011](0011-model-instances.md)) and artifact and provenance rows ([ADR-0030](0030-traceability-and-provenance.md)); one engine serving every CSC.
* **What creates the need:** R3 findings and reports (DVE.21–26), operation history and audit (DVE.24–25), saved per-user data-source configurations (MDG.8) and instance registries (SMM.29–31). None of these exists today.
* **No ADR number is reserved for the store.** The record is written when the need arrives. ADRs that assume persistence say so as an open assumption: ADR-0005, ADR-0010, ADR-0011, ADR-0019, ADR-0025, ADR-0029, ADR-0030.

### Front end

Chosen option: "Jinja template + hand-written ES5 scripts + vendored AntV G6 (as built)", because the panel already ships eight views and both model pictures on that stack, and a build step plus a Node runtime would have to earn back work that is already written and reviewed.

* **No build step:** `dve/src/dve/static/` is served as it is, and there is no Node toolchain in development, CI or production.
* **Rules that keep it maintainable:** one JS module per view instead of a second `app.js`; a vendored library is a pinned minified build with its license file in `static/vendor/`; fonts stay self-hosted; the Firefox 90 floor (ADR-0037) is held with shims such as `graph.js:11-22`, not with a transpiler.
* **Revisit triggers:** the first findings table that must virtualize (UXD §6 budgets 200+ rows), the first WCAG AA control the hand-written markup fails, or a component that cannot be vendored. Any of the three opens its own record.
* **Consequence for the UXD:** its component table (§5) and budgets (§6) name Next.js, React Flow, Refine, shadcn, TanStack and `next/font`. This record does not edit those documents; the list is under More Information.

### Consequences

* Good, because there is no migration: the API, the runner and the UI reviewed this week are the ones this record endorses.
* Good, because the runtime stays one Python process and one filesystem, which keeps QA-10 true and adds no service to back up.
* Good, because execution and persistence keep their ports, so a queue or a store can be adopted later without touching the domain layer.
* Good, because a *Reconcile* record that matches the code is what tells the next reader what is real.
* Bad, because the findings tables, charts and the model editor will be hand-built against UXD rules with no component library behind them.
* Bad, because accessibility (ADR-0037) and the UXD §6 budgets have no automated check, and there is no CI to run one in until ADR-0036.
* Bad, because operation history is not durable and a restart discards the log a user is reading (DVE.24–25, QA-04).
* Bad, because the automation contract arrives only with ADR-0023 in R7, and every path added before it becomes part of the v1 baseline.
* Neutral, because `dve` keeps a flat `adapters/` while `mdg` groups by area; [ADR-0003](0003-code-architecture-per-csc.md) accepts both forms.

### Confirmation

* Each package's suite passes on its own with no broker, queue or database service running: `python -m pytest` in `mdg/` and in `dve/`. One session cannot run both: each suite imports its own top-level `fakes` package and they share test module basenames, so `python -m pytest dve/tests mdg/tests` fails during collection.
* A search for `celery|redis|sqlalchemy|alembic` over `dve/src` and `mdg/src` returns nothing.
* Every route `api.py` serves is listed in its module docstring, and `dve.ini` has no queue or broker section.
* `static/vendor/` holds one pinned G6 build with its license, and `static/fonts/` holds every family the CSS names.
* `dve/src/dve/static/` gains no second file that serves more than one view.
* Any CI-based gate is deferred to ADR-0036, which introduces CI.

## Pros and Cons of the Options

| Topic | Option | Good | Bad |
|---|---|---|---|
| Framework | Flask 2.3 + Flask-WTF (as built) | Works today with sessions, CSRF and per-session sources already wired | Validation is hand-written and no OpenAPI document is generated |
| Framework | FastAPI with Pydantic (SDP §5) | One set of annotations gives schema, validation and async endpoints | Ports 18 routes and their tests and reworks the session layer for a schema document |
| Framework | Django REST Framework | Mature framework with admin and ORM included | Largest migration, and its ORM pre-empts the store this record leaves open |
| Execution | Multiprocessing + in-memory log (as built) | Proven in this codebase, tested, and already behind `ITaskRunner`/`ITaskLog` | History dies with the process and one bound serves all operation classes |
| Execution | Celery + Redis (retired draft) | Mature routing, retries and revocation, and progress meta comes free | No service exists to keep or integrate: both would be new, and history would sit in Redis |
| Execution | Procrastinate on PostgreSQL (SDP §5) | Jobs enqueue in the same transaction as the operation record; no broker | Needs the store this record defers, and progress, cancel and routing would be re-implemented |
| Persistence | Files + memory (as built) | Nothing to operate, migrate or back up, and no need goes unmet today | No queries, constraints or transactions; records cannot be filtered (DVE.23) |
| Persistence | PostgreSQL (SDP §5) | JSONB for evidence, indexed core fields, and the ADR-0010 AGE fallback | A stateful service, a migration history and a backup duty with no consumer yet |
| Persistence | MySQL/MariaDB | One engine across dev and production, already run in `dev/` | Weaker JSON support, and it blurs the line against the external CMDB mock |
| Front end | Jinja + hand-written JS + vendored G6 (as built) | Ships today, no build step, no Node runtime, graph canvas already working | Tables, charts and editor will be hand-built; budgets and accessibility are hand-enforced |
| Front end | React SPA built with Vite (retired draft) | Component ecosystem for tables, charts and forms; typed generated client | Discards ~8,800 shipped lines and the G6 canvas and needs a toolchain in a repo with no CI |
| Front end | Next.js 14 + Refine + shadcn/ui (SDP §5, UXD) | Matches the UXD and SDP exactly, with file-based routing | Needs a Node server in production for an internal tool behind a login |

## More Information

* Follow-ups this record leaves open, deliberately outside the ADR set: `docs/planning/SDP.md:584, 589, 592-596, 605, 616` (FastAPI, PostgreSQL, Next.js, React Flow, Recharts, Refine, TanStack, Procrastinate, Playwright) and `docs/design/UXD.md:68, 77, 83, 127, 221, 246, 379-387, 399-407` (Next.js shell and route chunks, Geist through `next/font`, Refine, shadcn, TanStack, React Flow).
* Why the retired drafts' "as built" columns were wrong: `dve/worker.py`, `celery_production_runner.py` and `redis_production_log.py` are not in the tree; `app.js` is 2,537 lines and `graph.js` adds 2,766 more; SaaG owns no relational store.
* Code: `dve/src/dve/api.py`, `dve/src/dve/adapters/multiprocessing_task_runner.py`, `dve/src/dve/adapters/in_memory_task_log.py`, `dve/src/dve/services/task_service.py`, `dve/src/dve/static/graph.js`.
* Revisit condition: reopened when any trigger named above fires, or when SDP §5 and the UXD are corrected and still disagree with this record.
* Related: [ADR-0003](0003-code-architecture-per-csc.md), [ADR-0011](0011-model-instances.md), [ADR-0019](0019-findings-and-operation-records.md), [ADR-0025](0025-authentication-and-sessions.md), [ADR-0027](0027-secrets-and-credentials.md), [ADR-0028](0028-concurrency-control.md), [ADR-0029](0029-validation-and-error-records.md), [ADR-0030](0030-traceability-and-provenance.md), ADR-0023, ADR-0032, ADR-0034, ADR-0036, ADR-0037.
