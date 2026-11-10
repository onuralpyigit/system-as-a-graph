# ADR-0013: Model Data file format and versioning

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | MDG.1, 14–15, 18, 22–23; SMM.2–3, 26; DVE.5; QA-03, QA-04 |
| Closes | CDR-29 (part: Model Data file), CDR-30 (part: Model Data file) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

MDG.23 requires MDG to "save it as a Model Data file", and SMM.2–3 require SMM to accept and validate that file. DVE.5 lists Model Data files per selection.

As built, `FilesystemModelSetupDataStore` writes one JSON file per run:

```
<workspace>/<project>/<platform>/<version>/<run_id>/<project>_<platform>_<version>.json
```

It has top-level sections `context`, `inventory`, `acquired_files`, `errors`, `generated_at`, `produced_by` and `graph`. The `graph` section has `metadata.scale`, `nodes`, `topics`, `applications`, `libraries`, and `relationships.{runs_on, publishes_to, subscribes_to, uses}`. The `run_id` is the Celery task ID.

The file has no schema version and no published schema. Timestamps are naive local time. Some application attributes (`priority`, `hotstandby`) are filled from a seeded random generator as placeholders.

## Decision Drivers

* SMM must validate the file's format, schema, integrity and mandatory fields (SMM.3), which requires a published schema.
* Files must stay readable as the format evolves (DVE.5 lists old runs).
* A run's file is evidence for every result derived from it (QA-04), so it must be immutable and hash-identifiable.
* Placeholder values must never be mistaken for acquired facts (QA-03).

## Considered Options

* JSON file per run on the filesystem (as built), made versioned and schema-validated
* Store Model Data as rows in the relational store
* Write directly in a graph-database import format

## Decision Outcome

Chosen option: "JSON file per run on the filesystem, made versioned and schema-validated", because the format works, is human-inspectable and downloadable (the existing `/download` endpoint), and SRS explicitly calls it a *file*.

* **Location:** unchanged. The workspace root comes from configuration (ADR-0039) and is a persistent volume in deployment.
* **Naming:** the `run_id` becomes the operation ID of the producing operation (ADR-0024). The file name is unchanged.
* **Schema:** add `"schema_version": "1.0"` at the top level, and a JSON Schema at `mdg/schemas/model-data-1.0.schema.json`. MDG validates the file before saving it, and SMM validates it again on input (SMM.3). Section names are renamed to the canonical vocabulary in schema 1.0 (ADR-0002).
* **Evolution:** minor versions only add optional fields. A major version change ships a reader for the previous major version, so listing (DVE.5) and model construction keep working for existing files.
* **Immutability and integrity:**
  * the file is written once, to a temporary name, and then atomically renamed;
  * its SHA-256 is recorded in the artifact registry (ADR-0035);
  * SMM verifies the hash before construction.
* **Timestamps:** ISO 8601 in UTC with offset.
* **Placeholders:** values that were not acquired are written as `null` and listed in a `placeholders` array with their JSON path and reason. Examples are today's random `priority`/`hotstandby` and mocked QoS. The `"NOT_FOUND"` sentinel string is retired. Graph construction (ADR-0014) does not turn placeholders into facts.
* **Provenance block:** `produced_by`, the producing operation ID, the tool version, and the clone commit hash per unit (ADR-0035).

### Consequences

* Good, because SMM gets a contract it can validate, and old files stay readable.
* Good, because results can be traced back to a byte-identical input.
* Bad, because existing files from before schema 1.0 have no version field. A reader treats them as `0.x` (best effort, read-only).
* Bad, because the random placeholder logic in `ModelSetupDataGraph` must be removed.

### Confirmation

* A unit test validates the output of `produce_model_setup_data` against the JSON Schema.
* A test asserts that no `"NOT_FOUND"` strings and no random values appear in the output.

## Pros and Cons of the Options

### JSON file per run (as built, versioned)

* Good, because it is simple, inspectable, downloadable, and matches the SRS wording.
* Bad, because there are no queries across runs. Listing reads each file's header, which is acceptable at the expected run counts.

### Relational rows

* Good, because it is queryable.
* Bad, because the graph-shaped payload would be split across many tables, losing the single-file evidence.

### Graph-DB import format

* Good, because it loads quickly.
* Bad, because it binds MDG to the storage choice of ADR-0015, and it is not human-readable.

## More Information

* Code: `mdg/src/mdg/domain/model_setup_data.py`, `model_setup_data_graph.py`, `workspace.py`, `adapters/model_setup_data/`
* Related: ADR-0002, ADR-0014, ADR-0024, ADR-0035
