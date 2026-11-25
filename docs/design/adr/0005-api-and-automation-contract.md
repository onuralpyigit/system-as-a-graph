# ADR-0005: Backend API and automation-client contract

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, pipeline owners |
| Kind | Ratify |
| Traces | DVE.1–2, 27, 77–78; QA-06, QA-11 |
| Resolves | DP-23 (EXT-IF-07 build automation / CLI protocol and result format), by §3 |
| Decide by | Wave A1 (2026-12-04); §3 automation contract by Wave E (2027-08-13) |
| Supersedes | — |

## Context and Problem Statement

Earlier SDP §5 drafts specified FastAPI with Pydantic. `dve/` is built on **Flask 2.3.2 with Flask-WTF 1.2.2**. `dve/src/dve/api.py` has 395 lines and 18 routes inside a single `create_app()` factory, backed by 45 API test functions (63 parametrized test items in `dve/tests/test_api.py`).

From R3 onwards the API expands to serve working-model editing, structural verification, synthetic/field workflows, behavioral analysis, findings filtering and report export. DVE.27 requires accepting analysis requests via Build Automation Tools and a CLI—presenting live status of ongoing operations to both interactive users and automation clients—and DVE.77–78 require per-unit and aggregate installation-suitability evaluations in a machine-processable format (EXT-IF-07, DP-23). All dependencies must install offline as CPython 3.9 wheels (ADR-0004).

## Decision Drivers

* Automation clients and CLI users need a versioned HTTP contract, documented schemas, and deterministic exit semantics (DVE.27, 77–78).
* Request validation must handle boolean/numeric zero values accurately and emit the shared `ErrorRecord` structure of ADR-0009.
* Keeping the working Flask + CSRF + session stack avoids rewriting 18 routes and 63 API tests for zero functional gain.
* Child-process task execution (ADR-0006) requires a **single-process, multi-threaded** production WSGI server so one parent process owns the child process table while serving 20 concurrent polling users without blocking.

## Considered Options

* Framework: Flask 2.3 with Flask-WTF and `waitress` WSGI server (as built, extended)
* Framework: FastAPI with Pydantic and Uvicorn (earlier SDP §5)
* Framework: Django REST Framework
* Automation contract (§3, open): Versioned REST `/api/v1/` with Bearer tokens plus `dsm` Click CLI subcommands

## Decision Outcome

Chosen option for the framework: **Flask 2.3 with Flask-WTF and `waitress` as the single-process multi-threaded production WSGI server**. It preserves the tested UI, session and CSRF plumbing, stays 100% pure Python in the wheelhouse, and satisfies single-parent ownership of ADR-0006's child processes.

### 1. As built (`1157784` + `f820ccb`)

* App factory `create_app(runtime=None)` in `dve/src/dve/api.py`; `Runtime` (`dve/src/dve/__init__.py`) injects port adapters or test fakes.
* `GET /` serves the single-page Operations Panel (ADR-0015); `/api/...` routes return JSON.
* CSRF: `GET /api/csrf-token` issues a token sent in `X-CSRFToken`; failures return `403` with `{"error": …, "csrf": true}`.
* Asynchronous tasks start with `202` (`POST /api/mdg/run`) and are polled via `GET /api/mdg/tasks/<id>?after=N` (ADR-0006).
* Commit `f820ccb` pinned `Werkzeug>=2.3.7,<3.1` (`werkzeug-2.3.8` in `dve/wheelhouse/`) because Flask 2.3.2's test client reads `werkzeug.__version__`, removed in Werkzeug 3.1.
* **As-built `api.py` defects identified for cleanup (§2):**
  * `_json_body` (`api.py:77-85`) calls `request.get_json(silent=True, force=True)` (ignoring `Content-Type`) and checks `if not body.get(field)`, falsely rejecting valid `0`, `False`, and `[]` values as missing fields.
  * The `413` handler (`api.py:131-133`) formats `config().api.max_upload_mb` rather than reading `app.config["MAX_CONTENT_LENGTH"]`.
  * Local filesystem routes (`GET/POST …/mdg-files`, `…/model`, `…/download`, `api.py:279-326`) carry an unnecessary `@config_db_required` decorator even though they touch only `model_setup_data_store`.
  * `serve()` (`api.py:387`) calls Werkzeug's single-threaded development `app.run()`, and `DataSourceService._sessions` (`data_source_service.py:25`) is an unlocked `dict` that is not thread-safe under multi-threaded WSGI execution.

### 2. Rules for growth (Wave A1)

* **Blueprints:** split `api.py` by bounded area (`auth`, `sources`, `model_data`, `operations`, `models`, `verification`, `analysis`, `field_records`, `findings`, `reports`, `health`), each wired to `Runtime` inside `create_app()`. Fix the unnecessary `@config_db_required` guard on local artifact routes and synchronize `DataSourceService._sessions` with a `threading.RLock`.
* **Versioning and live visibility (DVE.27):**
  * `/api/v1/` hosts versioned endpoints shared by the UI, CLI, and CI automation, starting in Wave A1 with `/api/v1/operations` (including `GET /api/v1/operations?state=queued,running` so UI users and CLI clients both see all ongoing operations, DVE.27) and `/api/v1/health` (ADR-0020), and growing with each release wave.
  * `/api/v1/` accepts either an authenticated browser session (+ CSRF on mutating verbs) or an `Authorization: Bearer <token>` header (exempt from CSRF, ADR-0019). UI-only convenience routes may remain unversioned under `/api/` as aliases over the same services.
* **Error envelope:** `{"error": "<message>", "code": "<stable_code>", "details": {…}}`, retaining the top-level `error` string for backward compatibility while mapping `code` and `details` directly from `common.errors.ErrorRecord` (ADR-0009) or HTTP transport cases (`csrf`, `not_found`, `conflict`, `rate_limited`, `payload_too_large` derived from `app.config["MAX_CONTENT_LENGTH"]`).
* **Request validation:** replace `_json_body` with a strict declarative validator requiring `application/json` (except multipart uploads), checking key presence (`key not in body or body[key] is None`) separately from non-empty string rules, validating types/enums, and returning `400` with a `schema` or `missing_field` `ErrorRecord`.
* **OpenAPI contract (`docs/api/openapi.yaml`):** maintained alongside `/api/v1/` routes starting in Wave A1. A CI contract test inspects Flask's `app.url_map` and fails if any `/api/v1/` route or HTTP method is undocumented or stale.
* **Production WSGI server (`waitress`):** vendor `waitress==3.0.2` (pure Python, zero extra dependencies) into `dve/wheelhouse/`. `serve()` runs `waitress.serve(app, host=…, port=…, threads=cfg.api.threads)` with `threads = 16` by default (overriding waitress's default of `4` so 20 concurrent users polling at 1 Hz plus uploads never exhaust worker threads), while keeping a single parent OS process for `MultiprocessingTaskRunner`. Pre-forking servers (`gunicorn`, `uwsgi`) are forbidden because forked workers would split child-process supervision.

### 3. Automation-client and CLI contract (open, decide by Wave E)

* **Question:** what are the exact CLI subcommands, request/response JSON Schemas, and process exit codes for Build Automation Tools and CLI users across **verification, behavioral analysis, and installation evaluation** (DVE.27, 77–78; EXT-IF-07, DP-23)?
* **Fixed architectural constraints:**
  * Transport is HTTPS REST under `/api/v1/` authenticated by scoped API tokens (ADR-0019).
  * `dsm` gains `click` subcommands (`click 8.1.8` is already in `dve/wheelhouse/`): e.g. `dsm verify`, `dsm analyze`, `dsm evaluate`, `dsm operations status/list/cancel`—submitting requests to `/api/v1/`, polling with `--wait`, streaming logs, and printing JSON or human-readable summaries (DVE.27).
  * Multi-unit installation evaluation (DVE.78) creates one non-process parent `operation` row and one independent child `installation_evaluation` `operation_id` per candidate software unit (ADR-0006, ADR-0007).
* **To settle in Wave E:**
  * Exact JSON Schema (`docs/api/evaluation-result-1.0.schema.json`) carrying per-unit `operation_id`, `score`, `score_class`, `conformance`, `blocking_findings`, and `decision` (`allow` | `block`), plus the aggregate result (aligned with ADR-0018);
  * Exact CLI exit-code mapping (`0` = conforming/`allow`, `2` = non-conforming/`block`, `3` = execution/operational error, `4` = authentication/validation error);
  * Poll interval/backoff defaults and CI pipeline timeout handling (Jenkinsfile reference snippet).

### Consequences

* Good, because the existing 18 routes, UI integration and 63 API tests keep working without a framework migration.
* Good, because `waitress` and `click` are pure Python, keeping CentOS 7 offline packaging trivial.
* Bad, because `docs/api/openapi.yaml` is maintained by hand rather than generated from Pydantic models, requiring route-map and response-schema contract tests in CI.
* Bad, because synchronous WSGI threads hold a thread per in-flight request; keeping long work in child processes (ADR-0006) and configuring `threads = 16` bounds thread occupancy to short DB/graph reads.

### Confirmation

* `dve/tests/test_api.py` passes across all blueprints, including falsy JSON values (`0`, `False`, `[]`), `Content-Type` enforcement, accurate `413` limits, and concurrent `DataSourceService` access.
* The OpenAPI route-coverage test passes in CI from Wave A1 onwards.
* Start-up test verifies `serve()` invokes `waitress` with configured `threads` and rejects Werkzeug's dev server in `production` mode (ADR-0004).

## Pros and Cons of the Options

### Flask 2.3 with Flask-WTF and `waitress` (chosen)

* Good, because it is already built, tested, pure Python in `dve/wheelhouse/`, and runs in a single parent process compatible with `MultiprocessingTaskRunner`.
* Bad, because request validation and OpenAPI schemas require explicit conventions and contract tests rather than automatic type-annotation generation.

### FastAPI with Pydantic and Uvicorn (earlier SDP §5)

* Good, because OpenAPI schemas and request validation are generated automatically from type annotations.
* Bad, because porting 18 routes, reworking Flask cookie sessions and CSRF, and vendoring compiled Rust `pydantic-core` wheels for CPython 3.9/`glibc 2.17` adds risk and maintenance cost without unlocking new SRS capability.

### Django REST Framework

* Good, because batteries-included auth, admin and serializers are mature.
* Bad, because it is the heaviest migration and its ORM conflicts with ADR-0003/0007's plain-SQL repository ports.

## More Information

* Code: `dve/src/dve/api.py`, `dve/src/dve/__init__.py`, `dve/src/dve/services/data_source_service.py`, `dve/tests/test_api.py`, `dve/setup.py`
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0009, ADR-0015, ADR-0018, ADR-0019, ADR-0020, ADR-0021
* Revisit if streaming server-sent events / WebSockets become mandatory beyond 1 Hz REST polling, or when upgrading Flask requires lifting the `Werkzeug<3.1` pin.
