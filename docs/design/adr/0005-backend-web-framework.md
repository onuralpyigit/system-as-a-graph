# ADR-0005: Backend web framework and API style

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Reconcile |
| Traces | DVE.1–2, 27, 78; QA-06, QA-11 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SDP §5 specifies FastAPI with REST/JSON. `dve/` is built on Flask 2.3 (`dve/src/dve/api.py`, about 320 lines, 15 API endpoints, synchronous, with hand-written body validation in `_json_body`). From R3 onwards, the API grows substantially: working-model editing, verification operations, findings queries, and in R7 the automation-client contract (DVE.27, 78), which must be machine-processable. The framework choice is cheapest to change now, while the API is small.

## Decision Drivers

* DVE.78 requires results "in a machine-processable format" for automation clients. A published, versioned API schema serves that directly (ADR-0028).
* Request validation must be consistent and must produce the error records of ADR-0034.
* Migration cost must stay small relative to R3's scope.
* The team is a Python team; both options are Python.

## Considered Options

* Flask 2.3 (as built), optionally with an OpenAPI extension (flask-smorest)
* FastAPI with Pydantic models (SDP §5)
* Django REST Framework

## Decision Outcome

Chosen option: "FastAPI with Pydantic models", because it gives three things from one set of type annotations: a generated OpenAPI schema, request and response validation, and typed client generation for the CLI. These are what DVE.27/78 and ADR-0028 need. The existing API is still small enough to port within R3.

* **API style:** REST with JSON bodies, resources under `/api/v1/`. Long-running work is started with `POST` and returns `202 Accepted` with an operation ID (ADR-0006, ADR-0024).
* **Errors:** a single error body `{ "error": { "code", "message", "details" } }`, mapped from domain errors.
* **Schema:** the OpenAPI document is generated at build time and committed, so API changes are visible in review.
* **Migration:** `api.py` and `test_api.py` are ported route by route in R3, before new endpoints are added. Session handling follows ADR-0030.

### Consequences

* Good, because API contract, validation and documentation come from the same source.
* Good, because async endpoints are available for status streaming if ADR-0006 adopts SSE later.
* Bad, because there is a one-time port of 15 endpoints and their tests.
* Bad, because the Flask session cookie mechanism used today has no direct FastAPI equivalent; ADR-0030 replaces it.
* Neutral, because Celery integration is framework-independent.

### Confirmation

* CI fails if the generated OpenAPI file differs from the committed one.
* The ported `test_api.py` passes against the FastAPI app via its test client.

## Pros and Cons of the Options

### Flask 2.3 (as built)

* Good, because it already works and has no migration cost.
* Bad, because validation is hand-written, and OpenAPI needs an extension and a parallel schema definition (marshmallow).

### FastAPI (SDP §5)

* Good, because it has a generated OpenAPI schema, Pydantic validation and async support.
* Bad, because of the migration effort and the session-handling rework.

### Django REST Framework

* Good, because it is a mature framework with an admin UI and ORM included.
* Bad, because it would be the largest migration, and its ORM overlaps with ADR-0008.

## More Information

* Code: `dve/src/dve/api.py`
* Related: ADR-0006, ADR-0024, ADR-0028, ADR-0030
