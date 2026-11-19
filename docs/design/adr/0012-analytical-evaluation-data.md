# ADR-0012: Analytical Evaluation Data: format and binding

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | ADM.1–6; SCG.4–7; SMM.32–37; DVE.16, 52–70; QA-03, QA-04 |
| Resolves | DP-12 (ADM.4 Analytical Evaluation Data format and content); DP-29e, DP-30e (storage and entity schema of Analytical Evaluation Data) |
| Decide by | Wave B (2027-01-22) for §1 format; Wave C (2027-03-12) for §2 binding |
| Supersedes | — |

## Context and Problem Statement

The behavioral dimension of the System Model comes from overlaying **Analytical Evaluation Data (AED)** onto the structural model, not from running applications (SRS preamble). The relevant requirements are:

* **Production (ADM.1–4):** ADM produces AED from System Field Records (ADM.2) or from SCG's synthetic data (ADM.3). Its format and content are deferred to the critical design phase (ADM.4, DP-12).
* **Binding (SMM.32–37):**
  * SMM matches the AED to nodes and relationships;
  * it keeps whether the AED came from field records or synthetic data (SMM.35);
  * it never alters the System Model and keeps the two separable (SMM.36);
  * it reports records with no counterpart (SMM.37).
* **Consumers:** DVE shows the binding status (DVE.16). The behavioral analyses (DVE.53–70) read message flow, counts, volume, frequency, latency, loss, resource usage and events per entity.

Nothing is built yet. The constraints are those of ADR-0004 (offline host, CPython 3.9 wheels) and ADR-0007 (SQLite).

## Decision Drivers

* AED must be immutable, versioned and traceable to its inputs (ADM.1, QA-04), with its source kind kept (SMM.35).
* The System Model must stay unchanged and separable (SMM.36, QA-03).
* The analyses need per-entity, per-time-window aggregates far more often than raw events.
* No heavy compiled dependency for an offline host. The data volume of one data set is bounded by ADR-0020's budgets.

## Considered Options

* Format: a manifest plus gzip JSON Lines per record kind / Apache Parquet / rows in the SQLite store only
* Binding: a separate overlay in SQLite, keyed by entity key / properties written onto the graph instance / joined at query time from the data set files

## Decision Outcome

Chosen options: **a manifest plus gzip JSON Lines files** for the AED data set, and **a separate overlay in SQLite, keyed by the ADR-0010 entity key**, for binding. JSON Lines needs only the standard library and stays inspectable. Parquet would need a large `pyarrow` wheel. A SQLite overlay keeps the graph untouched (SMM.36) while giving the analyses indexed per-window queries.

### 1. AED data set format (ADM.4, DP-12)

* **Layout:** one directory per data set, registered as an artifact of kind `analytical_evaluation_data` (ADR-0007), under `/var/lib/dsm/workspace/aed/<project>/<platform>/<version>/<dataset_id>/`. It holds `manifest.json` and up to three gzip JSON Lines files: `entity_metrics.jsonl.gz`, `relation_metrics.jsonl.gz` and `events.jsonl.gz`.
* **`manifest.json`:**
  * `schema_version` (`"1.0"`);
  * `dataset_id` and `source_kind` (`field` | `synthetic`, SMM.35);
  * project, platform and system version;
  * `time_range` and `window_seconds`;
  * input artifact IDs: field record IDs, or the synthetic data set and its scenario;
  * the producing operation ID, and the SHA-256 of each data file.
* **Records.** Every record names its element by the ADR-0010 key, so matching needs no translation.

  | File | Record fields | Feeds |
  |---|---|---|
  | `entity_metrics` | `label`, `key`, `window_start`, `metric`, `value`, `unit` | Resource usage, health and status (DVE.60–62); topic activity (DVE.65) |
  | `relation_metrics` | `type`, `from`, `to`, `window_start`, `metric`, `value`, `unit` | Message flow, count, volume, frequency, latency, loss and success rate (DVE.53, 63–64) |
  | `events` | `label`, `key`, `at`, `kind` (`error` \| `warning` \| `restart` \| `timeout` \| `state`), `detail` | Event records (DVE.62, 69) |

  * Metric names come from a closed vocabulary in the schema, for example `cpu_percent`, `memory_mb`, `msg_count`, `bytes`, `freq_hz`, `latency_ms`, `loss_ratio` and `success_ratio`.
* **Validation:**
  * The data set is validated against a published JSON Schema, `adm/src/adm/schemas/aed-1.0.schema.json`, with `jsonschema` (ADR-0009), before it is registered.
  * ADM reports unreadable or malformed inputs as error records (ADM.5–6, ADR-0009).
* **Evolution and integrity:** minor versions only add fields or metric names. A data set is immutable once registered.

### 2. Binding to the System Model (SMM.32–37)

* **Overlay tables** in the SQLite store (ADR-0007), with the `smm_` prefix:
  * `aed_dataset(dataset_id, source_kind, project, platform, system_version, schema_version, artifact_id)`;
  * `aed_metric(dataset_id, element_kind, label_or_type, key, window_start, metric, value)`, with `element_kind` = `node` | `relationship`, loaded from the files when bound;
  * `aed_event(dataset_id, label, key, at, kind, detail)`;
  * `aed_binding(binding_id, instance_id, revision, dataset_id, matched_count, unmatched_count, bound_at)`.
* **Matching:**
  * by (label, `name`) for nodes and (type, from, to) for relationships;
  * an optional `aed_alias(dataset_id, observed_key, model_key)` table, filled from a reviewed mapping file, covers runtime names that differ from model names.
* **Unmatched (SMM.37):** every record with no counterpart is recorded as a `warning` error record with category `invalid_relationship` or `missing_data` and the record key as `subject`. DVE.16 shows matched and unmatched counts from `aed_binding`.
* **Separation (SMM.36):** binding never writes to the graph store. A binding names an instance and revision. Analyses read the graph through `ModelReader` and the AED through an `AedReader` port, both read-only.
* **To build:** the ADM façade `produce_aed(...)`; SMM's `bind(instance_id, dataset_id)`; the `AedReader` port with an SQLite adapter and an in-memory fake.

### Consequences

* Good, because AED is inspectable, hashable and needs no new dependency beyond `jsonschema`.
* Good, because the System Model stays untouched, and one data set can be bound to several instances, for example a baseline and a working model.
* Good, because per-window aggregates keep both synthetic and field data small enough for SQLite.
* Bad, because loading a data set into SQLite duplicates it. The files stay authoritative, and the overlay rows can be rebuilt from them.
* Bad, because raw per-message traces are not kept in AED. Analyses that need them must read the field records (ADR-0014).

### Confirmation

* A schema test validates a synthetic and a field-derived sample data set.
* A binding test binds a sample to the dev seed model, checks the matched and unmatched counts, and asserts that the graph instance is unchanged.
* A round-trip test rebuilds the overlay rows from the files and gets identical query results.

### Open points

* The closed metric vocabulary is confirmed with system engineering against the field recording mechanism's actual measurements (ADR-0014).
* The default `window_seconds` (proposed: 1 s for synthetic data, 10 s for field data) is confirmed against ADR-0020's budgets.

## Pros and Cons of the Options

* Manifest + gzip JSON Lines (chosen): Good, because it uses only the standard library, is streamable and inspectable. Bad, because it is larger and slower than a columnar format.
* Parquet: Good, because it is compact and fast for analytics. Bad, because it needs `pyarrow`, a heavy compiled wheel to vendor offline.
* SQLite rows only: Good, because it is directly queryable. Bad, because a data set is no longer a single hashable file artifact.
* Overlay in SQLite (chosen): Good, because it is separable and indexed. Bad, because data is copied from the files.
* Graph properties: Bad, because they alter the System Model (SMM.36).
* Query-time joins from files: Good, because nothing is duplicated. Bad, because every analysis re-scans the files.

## More Information

* [SRS §4.1, §5.1.2, §6.1.3](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0007, ADR-0009, ADR-0010, ADR-0011, ADR-0013, ADR-0014, ADR-0017, ADR-0020
