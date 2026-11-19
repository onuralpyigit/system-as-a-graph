# ADR-0014: Field records: ingestion and storage

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, field recording mechanism owners, platform team |
| Kind | Decide |
| Traces | FDM.1–5; FDM-INF.1; ADM.2, 5; DVE.10, 12, 59–65, 69; QA-04, QA-05, QA-07 |
| Resolves | DP-21 (EXT-IF-05 field data recording mechanism protocol); DP-29c, DP-30c (storage and entity schema of the Field Records Database) |
| Decide by | Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

FDM stores and manages, centrally, the data records and telemetry obtained from installed platforms through the system data recording mechanism, as **System Field Records** (FDM.1). The other requirements:

* The user uploads records in a controlled, traceable way, associated with project, platform and system version (FDM.2–3).
* The user lists, searches and selects records (FDM.4), and upload errors are reported (FDM.5).
* ADM reads the records to produce Analytical Evaluation Data (ADM.2, 5).
* The storage disk capacity is deferred (FDM-INF.1, ADR-0020).

The protocol of EXT-IF-05 (DP-21) and the storage of the Field Records Database (DP-29c, DP-30c) are deferred design points. SDP §5 proposed VictoriaMetrics and discarding raw uploads after parsing. Nothing is built yet. The target host is offline, without a container runtime, and uses SQLite (ADR-0004, ADR-0007).

## Decision Drivers

* Uploads must be traceable and reproducible (FDM.3, QA-04). AED built from a record must be explainable later.
* The export format of the recording mechanism is not yet known, so the parser must be replaceable.
* There is no new server on the offline host, and the storage must be sizeable in advance (FDM-INF.1).
* Search by project, platform, version, source and upload time must be fast (FDM.4).

## Considered Options

* Protocol: export files uploaded over HTTPS (browser or API) / a watched drop folder / a push API called by the recording mechanism
* Storage: raw files retained plus a normalized copy and an SQLite catalog / a time-series server (VictoriaMetrics, TimescaleDB) / parse and discard the raw files (SDP §5)

## Decision Outcome

Chosen options: **export files uploaded over HTTPS**, and **raw files retained, with a normalized copy and an SQLite catalog**. Uploading files works with any recording mechanism that can export, and needs no change on the platforms. Keeping the raw file makes every derived result traceable to its original evidence, and the SQLite catalog serves FDM.4 without a new server.

### 1. Ingestion (EXT-IF-05, FDM.2, 5)

* **Protocol:**
  * The recording mechanism's export files (one archive or file per recording) are uploaded over HTTPS to `dve`.
  * They come from the Operations Panel as a multipart upload (DVE.10, 12), or from an automation client on `/api/v1/field-records` with an API token (ADR-0019).
  * The upload size limit is configured (`max_upload_mb`, as built for Model Data).
  * A drop-folder import may be added later behind the same service.
* **Metadata:** each upload names project, platform, system version and record source (the platform or recorder identity). The upload time and the user are added by the server (FDM.3).
* **Parsing:**
  * An `IFieldRecordParser` port with one adapter per export format turns a raw file into normalized records.
  * The normalized records are entity metrics, relation metrics and events keyed by the runtime entity names, in the ADR-0012 record shapes.
  * A fake parser is used until the real format is confirmed.
* **Validation (FDM.5):** format, integrity (archive checksum and readability) and mandatory fields, in the order and with the error records of ADR-0009. A failed upload is kept with status `rejected` and its error records, so the user sees why.
* **Processing:** parsing runs as an `interactive` operation (ADR-0006), not inside the request.

### 2. Storage (FDM.1, 4; DP-29c, DP-30c)

* **Files:**
  * stored under `/var/lib/dsm/field_records/<project>/<platform>/<version>/<record_id>/`;
  * `raw/`: the uploaded file, unchanged, with its SHA-256;
  * `normalized/`: gzip JSON Lines (`entity_metrics`, `relation_metrics`, `events`), written once.

  Both are registered as artifacts of kind `field_record` (ADR-0007).
* **Catalog:** an `fdm_record` table in SQLite (ADR-0007):

  | Column | Notes |
  |---|---|
  | `record_id` | `uuid4().hex` |
  | `project`, `platform`, `system_version` | FDM.2–3 |
  | `source` | Platform or recorder identity |
  | `uploaded_at`, `uploaded_by` | UTC; user or token identity |
  | `original_name`, `size_bytes`, `sha256` | Of the raw file |
  | `format`, `parser_version` | Which adapter parsed it |
  | `time_range_start`, `time_range_end` | Covered recording time |
  | `status` | `received`, `parsed`, `rejected` |
  | `operation_id` | The parsing operation |

  Indexes cover (project, platform, system_version, uploaded_at) and (source), which serve FDM.4's list, search and select.
* **Selection for ADM (ADM.2):** the user selects records (DVE.12), and FDM's façade returns their IDs (INT-IF-03, ADR-0003). ADM reads the normalized files.
* **Retention and sizing:** retention follows ADR-0004 §5. Disk sizing follows ADR-0020's formula (FDM-INF.1).
* **To build:** the `fdm/` package skeleton (ADR-0004), the parser port, fake and first adapter, the upload and list API, and the screens (DVE.10, 12).

### Consequences

* Good, because every upload is kept byte for byte, hashed and attributed, so AED and findings stay explainable.
* Good, because no server is added, and the parser for an unknown format stays replaceable.
* Good, because the normalized copy lets ADM read records without re-parsing.
* Bad, because keeping raw files roughly doubles the storage compared with discarding them. ADR-0020's sizing accounts for it.
* Bad, because there is no time-series query engine, so ad-hoc telemetry queries go through ADM and AED rather than directly against the records.

### Confirmation

* An upload test with a valid, a malformed and a truncated sample: statuses, error records and catalog rows are correct.
* A test re-parses a stored raw file and gets a normalized copy with the same hashes.
* A listing test filters by each FDM.4 criterion.

### Open points

* The export format, or formats, of the system data recording mechanism and their fields are confirmed with its owners. The first parser adapter depends on this.
* Whether automated push from platforms is needed later, which would make EXT-IF-05 an API call rather than a file upload.

## Pros and Cons of the Options

* HTTPS file upload (chosen): Good, because it works with any exporting recorder and needs no change on the platforms. Bad, because uploads are manual or scripted.
* Drop folder: Good, because it is simple for batch transfer. Bad, because of partial-file races and weaker attribution.
* Push API: Good, because it is automatic. Bad, because it needs changes in the recording mechanism and network access from the platforms.
* Raw + normalized + SQLite catalog (chosen): Good, because it is traceable, serverless and searchable. Bad, because of the storage overhead.
* Time-series server: Good, because it has rich telemetry queries. Bad, because it is a new server to install and operate offline.
* Parse and discard: Good, because it is the smallest footprint. Bad, because the original evidence is lost, and a parser bug cannot be corrected by re-parsing.

## More Information

* [SRS §3, §4.1](../../requirements/SRS.md), [SDP §5](../../planning/SDP.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0009, ADR-0012, ADR-0019, ADR-0020
