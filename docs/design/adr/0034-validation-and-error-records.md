# ADR-0034: Common validation and error-record pattern

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | MDG.16, 19–22; SCG.4; SMM.3, 25, 37; FDM.5; ADM.5–6; DVE.8, 14–15, 24; SDD §1 decision 5; QA-05 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SDD §1 decision 5 requires every data-acquisition path to validate its input and record failures with a consistent set of attributes. The SRS repeats the need in each CSC: MDG.16, 19–22; SMM.3, 25, 37; FDM.5; ADM.5–6.

As built in `mdg`:

* `ErrorRecord` holds `status` (`ERROR` | `MISSING_DATA`), `reason`, `source_name`, `source_type`, `project_platform` (one combined string) and `occurred_at` (naive local time).
* `DataAcquisitionError` carries a record. Across a process boundary it is rebuilt from its message, and the record is lost.
* Port-specific exceptions carry the error category in their class name: `SourceRepoAccessError`, `SourceRepoAuthError`, `SourceRepoIntegrityError` and `ConfigManagementAccessError`. The record only keeps it in the free-text `reason`.
* Per-unit outcomes use `UnitStatus` (`ok`, `missing_data`, `error`, `not_acquired`).

The other five CSCs will need the same pattern, and DVE must display and filter these records (DVE.8, 24).

## Decision Drivers

* The SRS distinguishes the error kinds: missing data, access, authorization, format, integrity and missing field (MDG.16, 20; DVE.8). They must be filterable, not buried in text.
* One record type across all CSCs, so DVE displays all of them the same way.
* Records must survive the worker boundary (ADR-0006).
* Timestamps must be comparable across hosts (QA-04).

## Considered Options

* Keep the `mdg` error record as is, and copy it into each CSC
* A shared error-record type in `common/`, extended with a category and structured scope
* Per-CSC error models

## Decision Outcome

Chosen option: "A shared error-record type in `common/`, extended with a category and structured scope". This ratifies the as-built pattern (record + raising error + per-item status) and fixes its gaps.

* **Type** (`common/errors.py`, ADR-0004):

  | Field | Notes |
  |---|---|
  | `status` | `error` / `missing_data` (as built), plus `warning` for non-blocking anomalies (e.g. an unmatched AED record, SMM.37) |
  | `category` | `access`, `authorization`, `integrity`, `format`, `schema`, `missing_field`, `missing_data`, `invalid_relationship`, `internal` |
  | `reason` | Human-readable text |
  | `source_name`, `source_type` | As built |
  | `stage` | The processing stage (e.g. `acquire_context`, `clone`, `parse`, `validate`, `construct`, `bind`) (DVE.24) |
  | `project`, `platform`, `system_version` | Separate fields, replacing the combined `project_platform` |
  | `subject` | Optional: unit name, file path, record ID or entity key the error concerns |
  | `operation_id` | The operation it belongs to (ADR-0024) |
  | `occurred_at` | UTC, ISO 8601 with offset |

* **Raising:** each port exception maps to one `category`. Adapters raise port exceptions, and services convert them into records. A service that must stop raises `DataAcquisitionError(record)`. The record is serialized as JSON in the task's failure and stored on the operation (ADR-0024), so it survives the process boundary.
* **Validation order** for every ingestion (MDG Model Data, SMM input, FDM upload, ADM inputs):
  1. readability and format;
  2. schema;
  3. integrity (hashes, references);
  4. mandatory-field presence.

  All failures of one item are collected before the item is rejected, so a user sees every problem at once.
* **Per-item status:** a per-item outcome enum like `UnitStatus` (`ok`, `missing_data`, `error`, `not_acquired`) is kept for batch inputs (units, records). The operation result summarizes it.
* **Storage:** records are persisted with their operation in PostgreSQL. They are also embedded in the artifact they concern when the SRS asks for it, e.g. the Model Data `errors` section (ADR-0013).

### Consequences

* Good, because DVE can filter every CSC's errors by category, stage and scope (DVE.8, 23–24).
* Good, because records no longer lose structure crossing into the worker.
* Bad, because `mdg`'s `ErrorRecord` changes shape. The Model Data schema 1.0 (ADR-0013) adopts the new fields, and old files are read with a converter.

### Confirmation

* A test of every adapter in `mdg` asserts the `category` produced for each port exception.
* A round-trip test: a record raised in a Celery task is retrieved intact from the operation's `failure`.
* Lint: no CSC defines its own error-record type (an `import-linter` rule checks that records are imported from `common`).

## Pros and Cons of the Options

### Keep as is and copy

* Good, because there is no change.
* Bad, because there are copies, the category stays text-only, and the record is lost across processes.

### Shared, extended type

* Good, because there is one model, it is filterable, and it is durable.
* Bad, because of the migration of `mdg` and the Model Data schema.

### Per-CSC models

* Good, because each CSC is free to fit its own needs.
* Bad, because it contradicts SDD §1 decision 5, and DVE would need one renderer per CSC.

## More Information

* Code: `mdg/src/mdg/domain/error_record.py`, `mdg/src/mdg/domain/model_setup_data.py` (`UnitStatus`), `mdg/src/mdg/ports/*.py`
* Related: ADR-0004, ADR-0006, ADR-0013, ADR-0024, ADR-0035
