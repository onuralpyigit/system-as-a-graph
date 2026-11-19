# ADR-0009: Model Data file format, and common validation and error records

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | MDG.1, 14–16, 18–23; SCG.4; FDM.5; ADM.5–6; SMM.2–3, 25–26, 37; DVE.5, 8, 14–15, 24; SDD §1 decision 5; QA-03, QA-04, QA-05 |
| Resolves | DP-29a, DP-30a (storage and entity schema of the Model Data file) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

MDG.23 requires MDG to "save it as a Model Data file", and SMM.2–3 require SMM to accept and validate it. DVE.5 lists the files per selection. SDD §1 decision 5 requires every acquisition path to validate input and record failures with one consistent set of attributes. The SRS repeats this in each CSC: MDG.16, 19–22; SMM.3, 25, 37; FDM.5; ADM.5–6.

As built (`1157784`):

* **File and path:** `FilesystemModelSetupDataStore` writes one JSON file per run, at `<workspace>/<project>/<platform>/<version>/<run_id>/<project>_<platform>_<version>.json`.
  * Path components are sanitised, and `Workspace.contains()` refuses paths outside the workspace.
  * The `run_id` is the dve task ID (`uuid4().hex`).
* **Sections:** `context`, `inventory`, `acquired_files`, `errors`, `generated_at`, `produced_by` and `graph`.
  * `graph` (`ModelSetupDataGraph`) has `metadata.scale`; the lists `nodes`, `networks`, `topics`, `messages`, `applications` and `libraries`; and `relationships.{runs_on, publishes_to, subscribes_to, sends, receives, uses, connects_to}`.
  * IDs are per-run positional (`N0`, `A0`, `L0`, `T0`, `M0`, `W0`) and not stable across runs.
* **Upload:** an externally produced file can be uploaded with `IModelSetupDataStore.add`. `check_payload` checks only its structure (`POST …/mdg-files`).
* **File gaps:**
  * no schema version and no published schema;
  * naive local timestamps;
  * application `priority` and `hotstandby` generated from a seed of the application name;
  * topic `frequency` and `criticality` derived from mocked QoS;
  * missing values written as `"NOT_FOUND"` or `-1`.
* **Errors:** `ErrorRecord` holds `status` (`ERROR` | `MISSING_DATA`), `reason`, `source_name`, `source_type`, one combined `project_platform` string, and naive `occurred_at`.
  * Port exceptions (`SourceRepoAccessError`, `SourceRepoAuthError`, `SourceRepoIntegrityError`, `ConfigManagementAccessError`) carry the category only in their class name.
  * Per-unit outcomes use `UnitStatus` (`ok`, `missing_data`, `error`, `not_acquired`).
  * `DataAcquisitionError` carries a record, but loses it when it crosses the pipe from an operation's child process: it comes back as `None` (`error_record.py:41-48`).

## Decision Drivers

* SMM must validate format, schema, integrity and mandatory fields (SMM.3), which needs a published schema.
* Old files must stay readable as the format evolves (DVE.5).
* A run's file is evidence for every result derived from it (QA-04), so it must be immutable and hash-identifiable. Placeholders must never be mistaken for facts (QA-03).
* The SRS distinguishes error kinds: missing data, access, authorization, format, integrity and missing field (MDG.16, 20; DVE.8). They must be filterable, the same in every CSC, and survive the child-process boundary.

## Considered Options

* File: JSON per run on the filesystem, made versioned and schema-validated (as built, extended) / relational rows / a graph-database import format
* Errors: a shared record type in `common/` with category and structured scope / keep the `mdg` record and copy it / per-CSC error models

## Decision Outcome

Chosen options: **a versioned, schema-validated JSON file per run (as built, extended)** and **a shared error-record type in `common/` (as built, extended)**. The file format works, is inspectable and downloadable, and the SRS calls it a *file*. The record pattern (record, raising error, per-item status) already works and only needs its gaps closed.

### 1. Model Data file

* **Location:** unchanged. The workspace root comes from host configuration outside the package (ADR-0004). The `run_id` is the producing operation's ID (ADR-0006, ADR-0007).
* **Schema:**
  * `"schema_version": "1.0"` at the top level, and `mdg/src/mdg/schemas/model-data-1.0.schema.json` shipped as package data.
  * MDG validates before saving, the upload path validates instead of only calling `check_payload`, and SMM validates again on input (SMM.3).
  * Validation uses `jsonschema` 4.17.x, which supports Python 3.7+ and whose dependencies (`attrs`, `pyrsistent`) publish cp39 manylinux2014 wheels. They are added to `mdg/wheelhouse/`.
* **Section names:** `graph` keeps the framework names MDG emits today, because they are the System Model vocabulary (ADR-0010). Later sections take ADR-0010 names too: hierarchy, roles, brokers, communication services and node capacity. The ADR-0002 terms apply to code and documents, not to these names.
* **Evolution:** minor versions only add optional fields. A major version ships a reader for the previous one. Files from before 1.0 are read as `0.x`, best effort and read-only.
* **Integrity:** the file is written once to a temporary name and atomically renamed. Its SHA-256 goes to the artifact registry (ADR-0007), and SMM verifies it before construction.
* **Timestamps:** UTC, ISO 8601 with offset.
* **Placeholders:** values not acquired are written as `null` and listed in a `placeholders` array with JSON path and reason.
  * Examples: the seeded `priority`/`hotstandby`, mocked QoS and the frequency derived from it, and node capacity not yet in the ansible repository (ADR-0008).
  * The `"NOT_FOUND"` and `-1` sentinels are retired, and graph construction never turns placeholders into facts.
* **Provenance block:** `produced_by`, the operation ID, the tool version, and the clone commit hash per unit (ADR-0008).

### 2. Common validation and error records

* **Type**, in `common/errors.py` (ADR-0004):

  | Field | Notes |
  |---|---|
  | `status` | `error` / `missing_data` (as built), plus `warning` for non-blocking anomalies, e.g. an unmatched AED record (SMM.37) |
  | `category` | `access`, `authorization`, `integrity`, `format`, `schema`, `missing_field`, `missing_data`, `invalid_relationship`, `internal` |
  | `reason` | Human-readable text |
  | `source_name`, `source_type` | As built |
  | `stage` | Processing stage, e.g. `acquire_context`, `clone`, `parse`, `validate`, `construct`, `bind` (DVE.24) |
  | `project`, `platform`, `system_version` | Separate fields, replacing `project_platform` |
  | `subject` | Optional: unit name, file path, record ID or entity key |
  | `operation_id` | The owning operation (ADR-0007) |
  | `occurred_at` | UTC, ISO 8601 with offset |

* **Raising:**
  * Each port exception maps to one `category`. Adapters raise port exceptions, and services convert them into records.
  * A service that must stop raises `DataAcquisitionError(record)`.
  * The child sends the record as a plain dict in its `failed` event, and the API process stores it on the operation.
  * `DataAcquisitionError` gets a `__reduce__` that pickles the record.
* **Validation order** for every ingestion (MDG output, SMM input, FDM upload, ADM inputs):
  1. readability and format;
  2. schema;
  3. integrity (hashes, references);
  4. mandatory fields.

  All failures of one item are collected before it is rejected.
* **Per-item status:** an enum like `UnitStatus` is kept for batch inputs, and the operation result summarizes it.
* **Storage:** records are persisted with their operation in SQLite (ADR-0007), and embedded in the artifact they concern where the SRS asks, as in the Model Data `errors` section.

### Consequences

* Good, because SMM gets a contract it can validate, old files stay readable, and results trace back to a byte-identical input.
* Good, because DVE can filter every CSC's errors by category, stage and scope (DVE.8, 23–24), and records keep their structure across processes.
* Bad, because the seeded placeholder logic in `ModelSetupDataGraph` must go, and `graph.js` must read `placeholders` instead of `"NOT_FOUND"` (ADR-0015).
* Bad, because `ErrorRecord` changes shape. Schema 1.0 adopts the new fields, with a converter for old files.
* Bad, because `jsonschema` and its dependencies add wheels to the offline wheelhouse.

### Confirmation

* `produce_model_setup_data` output validates against the JSON Schema, and contains no `"NOT_FOUND"`, no `-1` and no generated values.
* The upload route rejects a file that fails the schema, with a `schema` error record.
* Every `mdg` adapter test asserts the `category` produced for each port exception.
* A record raised in a child process is retrieved intact from the operation's `failure`, and a pickled `DataAcquisitionError` keeps its record.
* An `import-linter` rule checks that error records are imported from `common`.

## Pros and Cons of the Options

* JSON file per run (as built, versioned): Good, because it is simple, inspectable, downloadable, and matches the SRS wording. Bad, because there are no queries across runs; listing reads each file's header.
* Relational rows: Bad, because the graph-shaped payload would be split across many tables, losing the single-file evidence.
* Graph-DB import format: Bad, because it binds MDG to ADR-0011's choice and is not human-readable.
* Shared, extended error type: Good, because there is one filterable, durable model. Bad, because `mdg` and the schema must migrate.
* Copying the current record: Bad, because the category stays text-only and the record is lost across processes.
* Per-CSC models: Bad, because they contradict SDD §1 decision 5, and DVE would need one renderer per CSC.

## More Information

* Code: `mdg/src/mdg/domain/model_setup_data.py`, `mdg/src/mdg/domain/model_setup_data_graph.py`, `mdg/src/mdg/domain/workspace.py`, `mdg/src/mdg/domain/error_record.py`, `mdg/src/mdg/adapters/model_setup_data/`, `mdg/src/mdg/ports/`
* Related: ADR-0002, ADR-0004, ADR-0006, ADR-0007, ADR-0015, ADR-0008, ADR-0010, ADR-0011
