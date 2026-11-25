# ADR-0014: Field records: ingestion and storage

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, field recording mechanism owners, platform team |
| Kind | Decide |
| Traces | FDM.1–5; FDM-INF.1; ADM.2, 5; DVE.10, 12, 59–69; QA-04, QA-05, QA-07 |
| Resolves | DP-21 (EXT-IF-05 field data recording mechanism protocol); DP-29c, DP-30c (storage and entity schema of the Field Records Database) |
| Decide by | Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

FDM centrally stores and manages system data records and telemetry obtained via the target platforms' data recording mechanism as **System Field Records** (FDM.1):

* Operators (or automation scripts) upload field records in a controlled, traceable manner bound to `(project, platform, system_version)` and `record_source` (FDM.2–3).
* Operators list, search and select records by **project, platform, system version, record source, or upload time** (FDM.4, DVE.10, 12).
* Format incompatibility, integrity errors, or missing fields detected during upload are reported and recorded (FDM.5).
* ADM ingests selected System Field Records (`INT-IF-03`) to produce field-backed AED (ADM.2, 5) feeding DVE's health, resource, messaging, latency/loss, event, and architectural-drift analyses (DVE.59–69).
* Storage hardware disk sizing is governed by `FDM-INF.1` (DP-15, resolved in ADR-0020 §2).

Earlier SDP §5 drafts proposed VictoriaMetrics and discarding raw uploads after parsing. Nothing is implemented yet, and the target host is air-gapped without containers (ADR-0004).

## Decision Drivers

* Every AED dataset and drift/telemetry finding must remain traceable to the exact byte-for-byte uploaded field export (FDM.3, QA-04).
* Platform recorder export formats may evolve across projects/platforms, requiring pluggable parser adapters behind a clean port without altering storage or ADM contracts.
* Upload-time errors must give immediate operator feedback (FDM.5, `STD TC-TDM-01`) while large multi-hundred-MB archives parse without timing out HTTP requests.
* No time-series database daemon may be added to the offline host (QA-10), and all five FDM.4 filter criteria must be indexed in `dsm.db`.

## Considered Options

* Ingestion protocol (`EXT-IF-05`, `DP-21`): Multipart HTTPS archive/file upload (UI and `/api/v1/field-records`) with two-phase validation
* Ingestion protocol (`EXT-IF-05`, `DP-21`): Watched local drop directory only
* Ingestion protocol (`EXT-IF-05`, `DP-21`): Live streaming push agent from deployed platforms
* Storage (`DP-29c`, `DP-30c`): Retained immutable `raw/` export + unbucketed `normalized/` JSONL.gz streams on disk, indexed in SQLite `fdm_record`
* Storage (`DP-29c`, `DP-30c`): Dedicated time-series server (VictoriaMetrics / TimescaleDB)
* Storage (`DP-29c`, `DP-30c`): Parse into AED and discard raw uploads (earlier SDP §5)

## Decision Outcome

Chosen options: **multipart HTTPS export-file upload with synchronous envelope checks plus tracked normalization**, and **retained `raw/` + unbucketed `normalized/` files on `/var/lib/dsm/field_records/` catalogued in SQLite `fdm_record`**.

### 1. Ingestion and two-phase upload validation (`EXT-IF-05`, `DP-21`; FDM.2, 5)

* **Transport:**
  * Export files or archives (`.tar.gz`, `.zip`, `.jsonl.gz`, `.csv.gz`) from the platform recording mechanism are uploaded over HTTPS via the Operations Panel (`POST /api/fdm/records`, session + CSRF) or via CLI/automation (`POST /api/v1/field-records`, `Authorization: Bearer <token>` with `field_records:upload` scope, ADR-0019).
  * Maximum upload size is governed by `[fdm] max_upload_mb` in `dve.ini` (separate from smaller JSON Model Data uploads, default `2048 MB`, streamed to a temporary file on `/var/lib/dsm/field_records/.staging/` rather than buffered in RAM).
* **Two-phase validation (`FDM.5`, `TC-TDM-01`):**
  1. **Phase A — Synchronous upload check (in-request):** validates mandatory multipart metadata (`project`, `platform`, `system_version`, `source`, optional client `expected_sha256` and `format`), non-empty byte stream, `SHA-256` match, and container/archive header readability. Missing metadata or corrupt headers immediately record an `ErrorRecord` (`missing_field`, `integrity`, or `format`, ADR-0009), insert a `rejected` `fdm_record` audit row if bytes arrived, and return HTTP `400`/`422` directly to the uploader.
  2. **Phase B — Asynchronous content normalization (`field_record_ingestion` on `interactive` queue, ADR-0006, ADR-0007):** moves the verified raw file into `raw/`, returns `202 Accepted` with `{record_id, operation_id}` (which the UI upload dialog polls inline to completion), and runs `IFieldRecordParser` to validate record-level schemas and mandatory fields. Any content error marks `fdm_record.status = 'rejected'`, attaches all `ErrorRecord`s to the operation and record, and keeps the raw file for inspection (until purged or deleted).
* **Pluggable `IFieldRecordParser` port:**
  * Ships with a **canonical SaaG JSONL/CSV archive adapter** (`saag-field-v1`, usable immediately by any platform export script and by qualification tests) plus a format registry keyed by `format` header/manifest so platform-specific binary/CSV recorder adapters plug in cleanly per project.
  * Emits **unbucketed** normalized `.jsonl.gz` streams (`entity_observations.jsonl.gz`, `relation_observations.jsonl.gz`, `events.jsonl.gz` covering both nodes and relationships for `DVE.69`, and `observed_topology.jsonl.gz` capturing runtime entities, edges and static attributes for `DVE.66–68`), preserving original observation timestamps so `ADM` can aggregate to any requested `window_seconds` (ADR-0012 §1).

### 2. Physical storage and catalog schema (`DP-29c`, `DP-30c`; FDM.1, 3–4)

* **Filesystem layout (`/var/lib/dsm/field_records/`, provisioned by `deploy/install.sh` per ADR-0004 §3):**
  * `<project>/<platform>/<version>/<record_id>/raw/<original_name>` — immutable raw upload, registered in `common_artifact` with **`kind = 'field_record_raw'`** (`ADR-0007 §3`);
  * `<project>/<platform>/<version>/<record_id>/normalized/*.jsonl.gz` — immutable normalized streams, registered in `common_artifact` with **`kind = 'field_record_normalized'`** linked to `field_record_raw` via `common_artifact_input`.
* **SQLite catalog (`fdm_record` in `dsm.db`, ADR-0007):**

  | Column | Type & Notes |
  |---|---|
  | `record_id` | `TEXT PRIMARY KEY` (`uuid4().hex`) |
  | `project`, `platform`, `system_version` | `TEXT NOT NULL` (FDM.2–3) |
  | `source` | `TEXT NOT NULL` — platform tail/hull ID or recorder instance name (FDM.3) |
  | `uploaded_at`, `uploaded_by` | `TEXT NOT NULL` — UTC ISO 8601; username or token identity |
  | `original_name`, `size_bytes`, `sha256` | `TEXT`, `INTEGER`, `TEXT` — raw file metadata |
  | `raw_artifact_id`, `normalized_artifact_id` | `TEXT REFERENCES common_artifact(artifact_id)` (`normalized_artifact_id` `NULL` until `parsed`) |
  | `format`, `parser_version` | `TEXT NOT NULL`, `TEXT NOT NULL` |
  | `recording_start`, `recording_end` | `TEXT NULL` (UTC range observed inside the recording) |
  | `status` | `TEXT NOT NULL CHECK (status IN ('received', 'parsed', 'rejected'))` |
  | `error_count` | `INTEGER NOT NULL DEFAULT 0` |
  | `operation_id` | `TEXT NOT NULL REFERENCES common_operation(operation_id)` (`type = 'field_record_ingestion'`) |

  * **Indexes (`FDM.4`, `TC-TDM-02`):** `(project, platform, system_version, uploaded_at DESC)`, standalone `(uploaded_at DESC)`, `(source, uploaded_at DESC)`, and `(platform, system_version)` so single-criterion and multi-criterion searches execute via index scans.
* **Selection guard for ADM (`FDM.4`, `DVE.12`, `ADM.2`):** all statuses (`received`, `parsed`, `rejected`) are visible in FDM's management list with their diagnostics, **but only `status = 'parsed'` records are selectable** for `INT-IF-03` handoff to `ADM` (`adm.produce_aed` also re-verifies `status = 'parsed'` and `normalized_artifact_id` SHA-256).

### Consequences

* Good, because retaining both `raw/` and unbucketed `normalized/` files gives full auditability, allows re-parsing if a recorder adapter is updated, and lets ADM re-window the same field recording at different `window_seconds` resolutions without re-parsing raw exports.
* Good, because two-phase validation gives instant HTTP error feedback on bad uploads while keeping multi-hundred-MB parsing off WSGI worker threads.
* Bad, because storing `raw/` plus `normalized/` requires ~`2.0×` raw upload disk space (explicitly accounted for in ADR-0020 §2's `F = r × d × 2.0` sizing formula).

### Confirmation

* Upload tests (`TC-TDM-01` / `TC-FDM-01`) verify: valid `saag-field-v1` archive reaches `status = 'parsed'` with distinct `field_record_raw` and `field_record_normalized` artifacts; corrupt gzip/SHA-256 mismatch fails synchronously in Phase A with `integrity` `ErrorRecord`; missing required telemetry column fails in Phase B with `status = 'rejected'` and `missing_field` `ErrorRecord`, and cannot be passed to `ADM`.
* Catalog filter tests (`TC-TDM-02` / `TC-FDM-02`) query `fdm_record` independently by `project`, `platform`, `system_version`, `source`, and `uploaded_at` range.
* Reproducibility test re-runs `IFieldRecordParser` on `raw/` and verifies identical `normalized/` digests.

## Pros and Cons of the Options

### Multipart HTTPS upload with two-phase validation (chosen)

* Good, because it works across air-gapped transfer media without modifying deployed target platforms and supports both browser UI and scripted CLI uploads.
* Bad, because operators or transfer scripts initiate uploads explicitly rather than streaming live.

### Watched drop directory only

* Good, because bulk `scp`/`rsync` copies need no HTTP client.
* Bad, because partial-copy races, missing uploader identity (`uploaded_by`), and asynchronous error feedback complicate FDM.2–3 and FDM.5 (may still be added later as a thin wrapper calling the same service).

### Live push API from target platforms

* Good, because ingestion is real-time.
* Bad, because deployed tactical/industrial platforms are typically network-isolated from the design-verification host and cannot be modified by SaaG.

### Retained `raw/` + unbucketed `normalized/` files + SQLite `fdm_record` (chosen)

* Good, because it is serverless offline, preserves forensic raw evidence, supports flexible ADM windowing, and indexes all FDM.4 search fields in SQLite.
* Bad, because disk usage is ~`2.0×` raw upload volume.

### Time-series database server (VictoriaMetrics / TimescaleDB)

* Good, because ad-hoc PromQL/SQL time-series slices are built in.
* Bad, because it introduces an extra server binary to deploy, secure and back up offline and cannot store arbitrary relationship events or observed static topology cleanly.

### Parse and discard raw uploads (earlier SDP §5)

* Good, because disk footprint is smaller.
* Bad, because deleting raw exports destroys original field evidence (QA-04) and prevents re-parsing if a parser adapter defect is discovered.

## More Information

* [SRS §3.1, §3.2, §4.1, §6.1.3](../../requirements/SRS.md), [STD TC-TDM-01..02](../../test/STD.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0009, ADR-0012, ADR-0019, ADR-0020
* Revisit if direct automated telemetry streaming from lab integration rigs is added in a future increment (adding an ingest endpoint feeding the same `fdm` service).
