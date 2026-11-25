# ADR-0012: Analytical Evaluation Data: format and binding

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | ADM.1–6; SCG.4–7; SMM.32–37; DVE.15–16, 52–70; QA-03, QA-04 |
| Resolves | DP-12 (ADM.4 Analytical Evaluation Data format and content), by §1; DP-29e, DP-30e (storage and entity schema of Analytical Evaluation Data), by §2 |
| Decide by | Wave B (2027-01-22) for §1 format; Wave C (2027-03-12) for §2 binding |
| Supersedes | — |

## Context and Problem Statement

The behavioral analysis dimension of the System Model is achieved by overlaying **Analytical Evaluation Data (AED)** onto the structural graph rather than executing target applications (SRS preamble):

* **Production (ADM.1–6):** ADM prepares controlled, traceable, verifiable AED from *either* System Field Records (ADM.2) *or* synthetic data supplied by SCG (ADM.3)—never mixing the two in one dataset—and reports format/readability/missing-field errors (ADM.5–6). Its format and content are deferred to critical design (ADM.4, DP-12).
* **Binding (SMM.32–37):** SMM associates AED with `(project, platform, system_version)` and a System Model instance, matches record/telemetry/synthetic data to nodes **and relationships** (SMM.34), preserves `field` vs. `synthetic` provenance (SMM.35), binds **without altering System Model nodes or relationships** while keeping the two separable (SMM.36), and reports unmatched records (SMM.37).
* **Downstream consumers (DVE.15–16, 52–70):** DVE tracks AED production (DVE.15), displays scope and matching status (DVE.16), evaluates synthetic flow/load/propagation/top-N indicators (DVE.52–58), analyzes field health, CPU/RAM/storage/network usage, errors/warnings/restarts/timeouts, message flow/volume/frequency, latency/loss/success rate, pub/sub activity, node **and relationship** events, top-N indicators (DVE.59–65, 69–70), and compares Model Data entities/relationships/attributes against observed runtime data for architectural drift (DVE.66–68).

Nothing is implemented yet. Offline CPython 3.9 wheel constraints (ADR-0004) and SQLite single-writer contention limits on `dsm.db` (ADR-0007) govern the design.

## Decision Drivers

* AED datasets must be immutable, hash-verified artifacts enforcing strict single-source provenance (`field` XOR `synthetic`, ADM.1–4, SMM.35, QA-04).
* Binding must never mutate the graph store (SMM.36, QA-03) and must **never bulk-insert millions of metric rows into central `dsm.db`**, which would stall user sessions and operation logs under SQLite's single-writer lock (ADR-0007).
* The AED schema must represent node **and relationship** events (DVE.69), directed edge flow (DVE.53, 63), observed runtime entities/relationships/attributes for drift mismatch detection (DVE.66–68), and synthetic field-value summaries (SCG.4).
* Zero heavy native columnar dependencies (`pyarrow`) to compile or vendor offline.

## Considered Options

* Dataset format (§1): Directory with `manifest.json` plus gzip JSON Lines (`.jsonl.gz`) files validated by JSON Schema
* Dataset format (§1): Apache Parquet files (`pyarrow`)
* Dataset format (§1): Relational SQLite tables only (no portable file set)
* Binding & query storage (§2): Per-dataset immutable SQLite `overlay.db` file opened read-only, with lightweight binding/alias metadata in `dsm.db`
* Binding & query storage (§2): Bulk-loading `smm_aed_metric` rows into central `dsm.db`
* Binding & query storage (§2): Writing properties directly onto graph-server nodes/edges
* Binding & query storage (§2): Re-scanning `.jsonl.gz` files on every analysis query

## Decision Outcome

Chosen options: **a `manifest.json` plus gzip JSON Lines (`.jsonl.gz`) dataset directory** (§1) and **an immutable per-dataset SQLite `overlay.db` file opened read-only by `AedReader`, paired with lightweight catalog/binding/alias rows in `dsm.db`** (§2).

### 1. AED dataset format and content (`ADM.4`, `DP-12` — Wave B)

* **Artifact layout:** `/var/lib/dsm/workspace/aed/<project>/<platform>/<version>/<dataset_id>/`, registered in `common_artifact` (`kind = 'analytical_evaluation_data'`, ADR-0007), containing `manifest.json` and up to five `.jsonl.gz` streams:
  1. `entity_metrics.jsonl.gz`
  2. `relation_metrics.jsonl.gz`
  3. `events.jsonl.gz`
  4. `observed_topology.jsonl.gz` *(populated for `field` AED to support DVE.66–68 drift; optional for `synthetic`)*
  5. `field_samples.jsonl.gz` *(populated for `synthetic` AED to verify SCG.4 field naming and value-range constraints; optional for `field`)*
* **`manifest.json` (`adm/src/adm/schemas/aed-1.0.schema.json`, validated via `jsonschema==4.17.3`):**
  * `schema_version`: `"1.0"`, `dataset_id`, `producing_operation_id`, `created_at` (UTC);
  * `project`, `platform`, `system_version`;
  * `source` (**enforced `oneOf` — strict non-mixing per ADM.2–4**):
    * `{ "source_kind": "field", "field_record_ids": ["…"] }` (at least one `parsed` `fdm_record`), **or**
    * `{ "source_kind": "synthetic", "synthetic_dataset_id": "…", "scenario_name": "…", "seed": 12345 }`;
  * `time_range`: `{start, end}` (UTC ISO 8601) and `window_seconds` (default `1` s for `synthetic`, `10` s for `field`, configurable per run);
  * `files`: map of filename → `{sha256, record_count, size_bytes}`.
* **Stream record schemas** (all keys follow ADR-0010 `(label, name)` and `(type, from, to)`):

  | Stream | Record fields | SRS coverage |
  |---|---|---|
  | `entity_metrics` | `label`, `key`, `window_start`, `metric`, `value`, `unit` | Health/status (`health_state`, `availability_ratio`, DVE.60); resources (`cpu_percent`, `memory_mb`, `storage_mb`, `storage_percent`, `net_rx_mbps`, `net_tx_mbps`, DVE.58, 61, 70); pub/sub activity (`pub_active`, `sub_active`, `pub_msg_count`, `sub_msg_count`, DVE.65) |
  | `relation_metrics` | `type`, `from`, `to`, **`direction`** (`forward` \| `reverse`), `window_start`, `metric`, `value`, `unit` | Flow direction, count, volume, frequency (`msg_count`, `bytes`, `freq_hz`, DVE.53, 58, 63, 70); delivery quality (`latency_ms`, `latency_p95_ms`, `loss_ratio`, `success_ratio`, DVE.64) |
  | `events` | **`element_kind`** (`node` \| `relationship`), **`label_or_type`**, **`key`** (`name` or `from->to`), `at`, `kind` (`error` \| `warning` \| `restart` \| `timeout` \| `state`), `code`, `detail` | Node **and relationship** event & fault analysis (**DVE.62, 69**; SMM.34) |
  | `observed_topology` | `element_kind` (`node` \| `relationship`), `label_or_type`, `key` (`name` or `from->to`), `first_seen`, `last_seen`, `observed_attributes` (JSON: e.g. `cpu_cores`, `os_type`, `version`, `qos_reliability`, `qos_durability`, `qos_lifespan_ms`, `host`) | Runtime entity, relationship, and attribute-incompatibility drift (**DVE.66–68**) |
  | `field_samples` | `label` (`Topic` \| `Message`), `key`, `window_start`, `field_name`, `field_type`, `min_val`, `max_val`, `mean_val`, `sample_count`, `unit` | Conformance to unit topic/message field naming and value ranges (**SCG.4**) |

* **Aggregation ownership & error reporting (ADM.5–6):** `FDM` retains raw observation timestamps in `normalized/` (ADR-0014); `ADM` merges selected records, buckets metrics into `window_seconds`, validates every record in ADR-0009's 4-step order, and emits `ErrorRecord`s (`format`, `schema`, `integrity`, `missing_field`) on malformed inputs.

### 2. Per-dataset read-only SQLite overlay and binding (`SMM.32–37`; `DP-29e`, `DP-30e` — Wave C)

* **Zero-contention `<dataset_dir>/overlay.db`:**
  * When ADM finalizes a dataset (or on first `SMM.bind`), an immutable SQLite database `<dataset_dir>/overlay.db` (`journal_mode=OFF`, `synchronous=FULL` during one-time build, then `chmod 0400` and hashed) is materialized alongside the `.jsonl.gz` files containing indexed `aed_metric`, `aed_event`, `aed_observed`, and `aed_field_sample` tables.
  * `SMM`'s `AedReader` opens `file:<path>/overlay.db?mode=ro&immutable=1` read-only. **Zero bulk metric/event rows are ever inserted into central `dsm.db`**, completely eliminating write-lock contention with sessions, logs and operations (ADR-0007).
* **Lightweight metadata & alias tables in `dsm.db` (`smm_` prefix, ADR-0007):**
  * `smm_aed_dataset(dataset_id PK, source_kind, project, platform, system_version, schema_version, window_seconds, artifact_id, overlay_sha256, created_at)`;
  * `smm_aed_alias(project, platform, system_version, element_kind, label_or_type, observed_key, model_key, updated_by, updated_at, PRIMARY KEY (project, platform, system_version, element_kind, label_or_type, observed_key))` — version-scoped, type-safe alias mapping shared by binding and drift (ADR-0017);
  * `smm_aed_binding(binding_id PK, instance_id, revision, dataset_id, source_kind, matched_node_count, matched_rel_count, unmatched_aed_count, uncovered_model_count, breakdown_json, bound_by, bound_at)`.
* **Bidirectional unmatched reporting (`SMM.37`, `DVE.16`):**
  * `SMM.bind(instance_id, revision, dataset_id)` resolves observed keys through `smm_aed_alias` against `ModelReader(instance_id, revision)` and records **both** directions:
    1. **AED records with no model counterpart (`unmatched_aed_count`):** each distinct unmatched AED element key emits a `warning` `ErrorRecord` (`category = 'unmatched_record'`, `subject = '<label_or_type>:<key>'`), feeding `DVE.16` and `DVE.67` (`drift_unexpected`);
    2. **Model nodes/relationships with no AED counterpart (`uncovered_model_count`):** recorded in `smm_aed_binding.breakdown_json` (by `record` / `telemetry` / `synthetic` stream kind for `DVE.16`) and as `warning` `ErrorRecord`s (`category = 'unmatched_record'`), directly satisfying `SRS SMM.37` and `STD TC-CSM-08` (`TC-SMM-08`)!
* **Strict separation (`SMM.36`):** binding writes zero bytes to the graph server. One dataset can bind concurrently to a baseline, multiple working models, and candidate models.

### Consequences

* Good, because `.jsonl.gz` files remain portable, streamable standard-library artifacts while read-only `overlay.db` gives millisecond indexed queries with zero `dsm.db` lock contention.
* Good, because relationship events (`DVE.69`), directed edge flows (`DVE.53, 63`), observed runtime attributes (`DVE.66–68`), synthetic field ranges (`SCG.4`), and bidirectional unmatched counts (`SMM.37`) are all first-class.
* Bad, because `overlay.db` duplicates the compressed `.jsonl.gz` streams on disk (~1.4–1.8× dataset size, budgeted in ADR-0020 §2); `.jsonl.gz` remains the authoritative archival source from which `overlay.db` can always be regenerated.

### Confirmation

* Schema test validates both a `field` and a `synthetic` AED 1.0 dataset, and confirms `aed-1.0.schema.json` rejects any manifest mixing `field_record_ids` and `synthetic_dataset_id` (`ADM.2–4`, `TC-ADM-03`).
* Binding test binds an AED dataset containing node events, relationship events (`DVE.69`), an extra runtime entity, and a model node without telemetry: verifies both `unmatched_aed_count` and `uncovered_model_count` (`SMM.37`), confirms zero mutations on the graph instance (`SMM.36`), and verifies zero writes to `dsm.db` metric tables during concurrent load.
* Round-trip test deletes and rebuilds `overlay.db` from `.jsonl.gz` and asserts identical `AedReader` query results.

## Pros and Cons of the Options

### `manifest.json` plus `.jsonl.gz` streams (chosen for §1)

* Good, because it requires only Python's standard library (`gzip`, `json`) plus `jsonschema`, is line-streamable, and is human-inspectable.
* Bad, because text JSON is larger on disk than binary columnar encodings.

### Apache Parquet (`pyarrow`)

* Good, because columnar compression and scan speed are high.
* Bad, because `pyarrow` is a large C++ wheel bundle to maintain across air-gapped CentOS 7 (`glibc 2.17`) CPython 3.9 environments.

### Relational SQLite rows only (no JSONL files)

* Good, because no `overlay.db` materialization step is needed.
* Bad, because binary SQLite pages are opaque to diff/inspect and fragile as a cross-version archival interchange format.

### Per-dataset read-only `overlay.db` + `dsm.db` metadata (chosen for §2)

* Good, because it keeps the System Model untouched (`SMM.36`), eliminates single-writer lock contention on `dsm.db`, and makes deleting a dataset's index a single file unlink.
* Bad, because each dataset stores both `.jsonl.gz` and `overlay.db`.

### Bulk-loading metrics into central `dsm.db`

* Good, because only one SQLite file exists.
* Bad, because multi-million-row `INSERT` transactions block concurrent user logins, session checks and task logs on `dsm.db`.

### Writing AED properties onto graph-server nodes and edges

* Good, because Cypher queries see structural and behavioral properties together.
* Bad, because it directly violates SMM.36 (*"without altering the nodes and relationships in the System Model"*).

### Query-time scanning of `.jsonl.gz` files without an index

* Good, because zero index disk space is used.
* Bad, because repeated per-entity/per-window queries during R6 rules decompress the entire dataset repeatedly.

## More Information

* [SRS §4.1, §5.1.2, §6.1.3](../../requirements/SRS.md), [STD TC-ADM-03, TC-CSM-08](../../test/STD.md)
* Related: ADR-0003, ADR-0004, ADR-0007, ADR-0009, ADR-0010, ADR-0011, ADR-0013, ADR-0014, ADR-0016, ADR-0017, ADR-0020
* Revisit if single-dataset `overlay.db` sizes exceed 10 GB on the target host, in which case DuckDB (`cp39` wheel check permitting) or partitioned window files may be evaluated.
