# ADR-0005: Backend API and automation-client contract

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, pipeline owners |
| Kind | Ratify |
| Traces | DVE.1–2, 27, 77–78; QA-06, QA-11 |
| Resolves | DP-23 (EXT-IF-07 build automation / CLI protocol and result format), by §3 |
| Decide by | Wave A (2026-11-27); §3 automation contract by Wave E (2027-08-13) |
| Supersedes | — (absorbs the planned ADR-0005) |

## Context and Problem Statement

SDP §5 specifies FastAPI with REST/JSON. `dve/` is built on **Flask 2.3.2 with Flask-WTF 1.2.2**. `dve/src/dve/api.py` has about 395 lines and 18 routes in one `create_app()` factory, with these traits:

* hand-written body validation (`_json_body`);
* CSRF protection (`CSRFProtect`);
* an upload size limit (`MAX_CONTENT_LENGTH` from `max_upload_mb`);
* errors returned as `{"error": "<message>"}`.

From R3 the API grows substantially: working-model editing, verification and findings queries. In R7 it must serve automation clients such as Jenkins (DVE.27, 77–78). They submit installation evaluations for one or more units and receive, per unit, a score, class, blocking findings and decision, plus an aggregate result, "in a machine-processable format". The protocol of EXT-IF-07 is a deferred design point (DP-23). Every dependency must ship as a cp39 wheel (ADR-0004).

## Decision Drivers

* Automation clients need a documented, versioned contract and stable exit semantics (DVE.77–78).
* Request validation must be consistent and must produce the error records of ADR-0013.
* The existing code and its 45 API tests work, so a port must buy something the SRS needs.
* Operations run in child processes owned by the API process (ADR-0006), so production must keep a single API process.

## Considered Options

* Framework: Flask 2.3 with Flask-WTF (as built) / FastAPI with Pydantic (SDP §5) / Django REST Framework
* Automation contract (open, §3): REST `/api/v1/` with API tokens plus a `dsm` CLI subcommand / CLI-only / result as JSON Schema / exit codes per decision

## Decision Outcome

Chosen option for the framework: **Flask 2.3 with Flask-WTF (as built)**. It already serves the UI and the Model Data workflow and is tested. A documented contract and a validation helper give automation clients what DVE.27/78 need, without porting 18 routes and rebuilding sessions and CSRF.

### 1. As built (`1157784`)

* App factory `create_app(runtime=None)`, with every route as a closure. The `Runtime` dataclass (`dve/src/dve/__init__.py`) injects the adapters, and tests pass their own.
* JSON for every `/api/...` route; `GET /` renders the single page (ADR-0009).
* CSRF: the token from `GET /api/csrf-token` is sent as `X-CSRFToken`. A failure returns 403 with `{"error": …, "csrf": true}`.
* Long-running work is started with `POST` and returns `202` with a task ID (`POST /api/mdg/run`). Status comes from `GET /api/mdg/tasks/<id>?after=N` (ADR-0006).
* `serve()` runs Werkzeug's development server (`app.run()`).
* Werkzeug is pinned to `>=2.3.7,<3.1` (2.3.8 in `dve/wheelhouse/`), because Flask 2.3.2's test client fails on Werkzeug 3.1 (ADR-0041).

### 2. Rules for growth

* **Blueprints:** one per area, for example `auth`, `sources`, `model_data`, `operations`, `models`, `findings`, `reports` and `automation`. Each is registered in `create_app()` and takes its adapters from the `Runtime`.
* **Versioning:** routes for automation clients live under `/api/v1/` and are authenticated by API token (ADR-0030). UI routes may stay unversioned; they change together with the page.
* **Errors:** `{"error": "<message>", "code": "<stable_code>", "details": {…}}`. This keeps the as-built `error` key. `code` comes from the error record category (ADR-0013) or the HTTP case, such as `csrf`, `not_found` or `payload_too_large`.
* **Validation:** one helper, grown from `_json_body`, validates a body against a small declarative schema (required keys, types, enums). A failure maps to a 400 with an error record. No validation framework is added.
* **Contract document:** `docs/api/openapi.yaml`, written by hand for `/api/v1/`. A contract test walks the Flask URL map and fails if a route and the document disagree.
* **Production server:** **waitress**, a pure-Python multi-threaded WSGI server, replaces `app.run()`. It keeps one process, so the task runner and its children stay owned by one parent. Pre-forking servers such as gunicorn are not used, because each worker would have its own task table.

### 3. Automation-client contract (open, decide by Wave E)

* **Question:** what do the API, CLI, result schema and exit codes look like for CI pipelines (DVE.27, 77–78; DP-23)?
* **Direction:**
  * REST under `/api/v1/` with API tokens (ADR-0030).
  * A `dsm` CLI subcommand built with click, which is already in the wheelhouse, that submits, polls and prints the result.
  * One operation per unit with an aggregate parent (ADR-0008, `parent_operation_id`).
* **To decide:**
  * the result JSON Schema: per-unit score, class, blocking findings and decision, plus the aggregate;
  * the exit codes per decision;
  * whether the CLI also runs without the server.
* **Inputs:** ADR-0027 (scoring and decision), ADR-0006 (polling contract), ADR-0008 (operation records).

### Consequences

* Good, because there is no port, and the existing tests and UI keep working.
* Good, because all dependencies stay pure Python or are already cp39 wheels.
* Bad, because the OpenAPI document is maintained by hand. The contract test catches missing routes, not body changes, so §3 adds example-based tests for the automation responses.
* Bad, because there is no async request handling. Status is delivered by polling, so none is needed.

### Confirmation

* `dve/tests/test_api.py` passes against `create_app()` for every blueprint.
* The OpenAPI contract test runs in CI.
* A start-up test checks that `serve()` uses waitress and refuses the development server in production mode (ADR-0004).

## Pros and Cons of the Options

* Flask with Flask-WTF (as built): Good, because it already works offline, with CSRF, sessions and tests. Bad, because validation and the contract need conventions rather than coming from type annotations.
* FastAPI (SDP §5): Good, because it generates the OpenAPI schema and validation from annotations. Bad, because of the port of 18 routes and the session and CSRF rework, and because pydantic-core is a compiled dependency to vendor offline.
* Django REST Framework: Good, because it is mature. Bad, because it is the largest migration, and its ORM overlaps with ADR-0008.

## More Information

* Code: `dve/src/dve/api.py`, `dve/src/dve/__init__.py`, `dve/tests/test_api.py`, `dve/tests/conftest.py`, `dve/setup.py`
* Related: ADR-0004, ADR-0006, ADR-0008, ADR-0009, ADR-0013, ADR-0027, ADR-0030, ADR-0041
