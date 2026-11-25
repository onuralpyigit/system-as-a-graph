# ADR-0007: Records store: operations, findings, provenance and audit

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, security |
| Kind | Decide |
| Traces | MDG.1, 8–9, 14–15, 18–19, 22; SCG.5–6; FDM.2–3; ADM.1; SMM.5, 26, 35; DVE.6–7, 15–16, 18, 21–26, 58, 70, 77–78; QA-01, QA-04, QA-08, QA-10 |
| Resolves | DP-29b, DP-29g (storage of the Software Unit Version Inventory and of Findings, Operations & Reports); DP-30b, DP-30g (their entity schemas) |
| Decide by | Wave A2 (2026-12-18) |
| Supersedes | — |

## Context and Problem Statement

Several SDD §2.4 stores and cross-CSC workflows require durable, transactional, indexed structured records:

* the Software Unit Version Inventory (MDG.14–15; DP-29b, DP-30b);
* the Findings, Operations & Reports store (DVE.21–26, 77–78; DP-29g, DP-30g);
* saved data-source configurations (MDG.8) and traceable source-accessibility status (DVE.7);
* manual network-topology definitions/overrides (MDG.7);
* the model-instance registry, edit log and UI node-layout store (SMM.26, DVE.17, ADR-0011, ADR-0015);
* AED dataset catalog, binding records and entity aliases (SMM.34–37, ADR-0012);
* Field Records metadata catalog (FDM.3–4, ADR-0014);
* artifact provenance lineage and an append-only security/operations audit trail (QA-01, QA-04);
* user session epochs and hashed API tokens (ADR-0019).

As built (`1157784`), SaaG has no database of its own: inventories live only inside Model Data JSON files, task state/logs/credentials live in volatile API memory, timestamps are naive local `datetime.now()`, and there is no lineage or audit log. Earlier SDP §5 drafts proposed PostgreSQL, whereas the target host is offline and containerless (ADR-0004).

## Decision Drivers

* Records must be ACID-durable across `dsm` restarts with zero external database server administration on the air-gapped host (QA-04, QA-08, QA-10).
* Both the parent API process and `spawn` child processes (which start fresh Python interpreters) must resolve the same SQLite ≥ 3.24 engine cleanly on CentOS 7 (where system `libsqlite3` is 3.7.17).
* DVE.23's multi-criteria sorting (including true severity order) and filtering, `MDG.19`'s `"missing data"` process status, and `DVE.58/70`'s summary KPIs must map cleanly onto the schema.
* Single-writer WAL transactions on `dsm.db` must remain short (< 50 ms) so bulk analytical datasets never stall interactive sessions or operation logs.

## Considered Options

* Store engine: Embedded SQLite (≥ 3.24 via `common.db` with `pysqlite3-binary` fallback)
* Store engine: Native PostgreSQL or MySQL server (earlier SDP §5)
* Store engine: In-memory state plus ad-hoc JSON files on disk (as built)
* Findings & metadata layout: Normalized relational columns with JSON text for variable payloads
* Findings & metadata layout: Storing findings inside the graph database or as monolithic JSON blobs
* Provenance model: Explicit `common_artifact` registry, `common_artifact_input` lineage DAG and trigger-protected `common_audit_event` table
* Provenance model: Event-sourced command log across all CSCs

## Decision Outcome

Chosen options: **embedded SQLite (≥ 3.24 via `common.db`)**, **normalized relational records with JSON text for variable evidence/summaries**, and **a centralized artifact registry with lineage and an append-only audit log**.

### 1. Engine, `spawn`-safe driver resolution and isolation

* **Database file:** `/var/lib/dsm/data/dsm.db` (mode `0600`, owned by service user `dsm`, ADR-0004).
* **Shared connector (`common/src/common/db.py`) and CentOS 7 fallback:**
  * SQLite ≥ 3.24 is required (for `INSERT … ON CONFLICT` upserts and deterministic query planning). CentOS 7 ships system SQLite `3.7.17`.
  * Because `MultiprocessingTaskRunner` uses `spawn` (ADR-0006), child processes do not inherit `sys.modules` from `dsm`. Therefore `common.db`—imported by every CSC adapter—checks `sqlite3.sqlite_version_info >= (3, 24, 0)` on import and transparently imports `pysqlite3 as sqlite3` when the system library is older.
  * `pysqlite3-binary` (pinned to a `cp39` `manylinux_2_17_x86_64` / `manylinux2014_x86_64` build such as `0.5.4.post2`, never `manylinux_2_28`) lives in **`common/wheelhouse/`** so standalone `mdg`, `smm`, `fdm`, `adm` and `dve` processes all have it.
  * JSON payloads are stored as `TEXT` validated in Python; SQLite JSON SQL functions are not relied upon.
* **Connection pragmas & write discipline:** one connection per thread/process, never shared across `spawn`. Every connection executes `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; PRAGMA synchronous=NORMAL;`. Transactions are kept short (< 50 ms). **Bulk AED time-windowed metric/event rows do NOT live in `dsm.db`**—they live in immutable per-dataset `<dataset_dir>/overlay.db` files opened read-only (ADR-0012 §2), preventing single-writer lock contention on `dsm.db`.
* **Migrations:** numbered SQL scripts per package (`<pkg>/src/<pkg>/migrations/NNNN_<name>.sql`, starting with `common`), tracked in `common_schema_migration(package, version, applied_at)` at `dsm` start-up inside an exclusive transaction; any failure rolls back and aborts start-up.
* **Conventions:** table names carry their owning package prefix (`common_`, `mdg_`, `scg_`, `fdm_`, `adm_`, `smm_`, `dve_`). Primary IDs are `uuid4().hex` (except integer sequences noted below), and all timestamps are timezone-aware ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).

### 2. Core schemas (DP-30b, DP-30g, and cross-ADR metadata tables)

**Software Unit Version Inventory (`mdg_inventory_unit`, DP-30b; MDG.14–15):**
Persisted from deduplicated CMDB unit rows **before** `ProduceModelSetupData` filters out internal `system_repo` / `ansible_repo` entries so the recorded inventory is complete:

```sql
CREATE TABLE mdg_inventory_unit (
  operation_id   TEXT NOT NULL REFERENCES common_operation(operation_id),
  project        TEXT NOT NULL,
  platform       TEXT NOT NULL,
  system_version TEXT NOT NULL,
  unit_name      TEXT NOT NULL,
  version        TEXT NOT NULL,
  unit_kind      TEXT NOT NULL DEFAULT 'application' CHECK (unit_kind IN ('application', 'library', 'system', 'topology')),
  is_candidate   INTEGER NOT NULL CHECK (is_candidate IN (0, 1)),
  PRIMARY KEY (operation_id, unit_name)
);
CREATE INDEX mdg_inventory_unit_sel ON mdg_inventory_unit (project, platform, system_version);
```

**Operations (`common_operation`, DP-30g; DVE.6, 9, 14–16, 18, 24–25, 27, 58, 70, 78; MDG.19):**

| Column | Type & Notes |
|---|---|
| `operation_id` | `TEXT PRIMARY KEY` — generated before spawn (or `NULL`-executor coordinator for multi-unit batches, ADR-0006) |
| `parent_operation_id` | `TEXT NULL REFERENCES common_operation(operation_id)` — links per-unit evaluations to their batch parent (DVE.78) |
| `type` | `TEXT NOT NULL` — one of the **10** canonical types: `model_data_production`, `model_construction`, `field_record_ingestion`, `synthetic_data_production`, `aed_production`, `aed_binding`, `structural_verification`, `simulation_analysis`, `field_analysis`, `installation_evaluation` |
| `queue_class` | `TEXT NOT NULL` — `pipeline` \| `interactive` \| `simulation` (ADR-0006 §3) |
| `project`, `platform`, `system_version` | `TEXT NOT NULL` — scope selection (DVE.4) |
| `requested_by`, `client_kind` | `TEXT NOT NULL` — username or token name; `ui` \| `cli` \| `automation` |
| `inputs` | `TEXT NOT NULL` (JSON) — `instance_id`, `revision`, `aed_dataset_id`, `binding_id`, `catalog_version`, `profile`, scenario inputs (DVE.25), candidate unit(s) |
| `state` | `TEXT NOT NULL` — `queued` \| `running` \| `succeeded` \| `failed` \| `cancelled` |
| `outcome_status` | `TEXT NULL` — `ok` \| `missing_data` \| `warning` \| `error`; explicitly represents `MDG.19`'s `"missing data"` acquisition process outcome even when partial artifacts are recorded |
| `conformance` | `TEXT NULL` — `conforming` \| `non-conforming` (DVE.18, 77) |
| `result_summary` | `TEXT NULL` (JSON) — per-operation summary payload: unit counts (`MDG`), matched/unmatched counts (`SMM.37`), top-N resource/messaging indicators (`DVE.58, 70`), or `score`, `score_class`, `heading_scores`, `blocking_finding_ids`, and `decision` (`allow` \| `block`, `DVE.78`, ADR-0018) |
| `progress_percent`, `progress_phase` | `INTEGER NOT NULL DEFAULT 0`, `TEXT NULL` |
| `failure` | `TEXT NULL` (JSON) — `ErrorRecord` dict including interrupted `stage` (`progress_phase`, `interrupted`, or `shutdown`, DVE.24) |
| `queued_at`, `started_at`, `ended_at` | `TEXT` (UTC ISO 8601) |
| `executor_ref` | `INTEGER NULL` — OS PID while running (`NULL` for batch coordinator rows) |

* **`common_operation_log`:** `(operation_id TEXT, seq INTEGER, at TEXT, level TEXT, message TEXT, PRIMARY KEY (operation_id, seq))`, `0`-based `seq`.

**Findings and reports (`dve_finding`, `dve_finding_link`, `dve_finding_affected`, `dve_report`, DP-30g; DVE.21–23, 26):**

| Table | Key Columns & Purpose |
|---|---|
| `dve_finding` | `finding_id TEXT PRIMARY KEY` (displayed as `<op_short>-<seq>`), `operation_id`, `rule_id`, `rule_version`, `evaluation_heading` (`DVE.72–75` or `NULL`), `finding_type`, `severity` (`informational`..`critical`), **`severity_rank INTEGER NOT NULL CHECK (severity_rank BETWEEN 0 AND 4)`** (enables true severity SQL `ORDER BY`, DVE.23), `description`, `affected` (JSON), `acceptance_criterion`, `blocking` (`0`\|`1`), `evidence` (JSON) |
| `dve_finding_link` | `(operation_id, cause_finding_id, effect_finding_id, link_kind, PRIMARY KEY (cause_finding_id, effect_finding_id))` — cause-and-effect chains within an operation (DVE.22) |
| `dve_finding_affected` | `(finding_id, element_kind, label_or_type, key, PRIMARY KEY (finding_id, element_kind, label_or_type, key))` — indexed side table for DVE.23 filtering by affected node/relationship |
| `dve_report` | `(report_id TEXT PRIMARY KEY, operation_id TEXT, report_kind TEXT CHECK (report_kind IN ('summary', 'detailed')), format TEXT CHECK (format IN ('html', 'json', 'csv')), artifact_id TEXT REFERENCES common_artifact(artifact_id), created_by TEXT, created_at TEXT)` (DVE.26, ADR-0018) |

* **Indexes:** `dve_finding(operation_id, severity_rank DESC)`, `dve_finding(rule_id)`, `dve_finding(finding_type)`, `dve_finding_affected(element_kind, label_or_type, key)`, `common_operation(project, platform, system_version, type, queued_at DESC)`, `common_operation(state, queue_class)`.

**Cross-CSC supporting tables in `dsm.db`:**

| Table | Owning ADR | Columns |
|---|---|---|
| `common_data_source` | ADR-0008, ADR-0019 (MDG.8) | `source_id TEXT PK, owner_user TEXT NULL, scope TEXT ('user'\|'project'\|'system'), project TEXT NULL, source_type TEXT, source_name TEXT, access_method TEXT, connection_address TEXT, username TEXT NULL, encrypted_secret BLOB NULL, key_id TEXT NULL, ca_bundle_path TEXT NULL, updated_at TEXT` |
| `common_source_health` | ADR-0006 §4, ADR-0020 (DVE.7) | `source_id TEXT REFERENCES common_data_source(source_id), checked_at TEXT, reachable INTEGER (0\|1), latency_ms INTEGER NULL, error_code TEXT NULL, message TEXT NULL` (indexed on `source_id, checked_at DESC`) |
| `mdg_topology_override` | ADR-0008 §2 (MDG.7) | `override_id TEXT PK, project TEXT, platform TEXT, system_version TEXT, mode TEXT ('manual'\|'override'), payload_json TEXT, updated_by TEXT, updated_at TEXT, UNIQUE (project, platform, system_version)` |
| `smm_model_instance`, `smm_model_edit` | ADR-0011 §3 | Model registry (`status` in `creating\|ready\|failed\|deleting`, `revision INTEGER`) and append-only Working Model edit/undo log |
| `smm_instance_layout` | ADR-0015 §2 | `(instance_id TEXT, revision INTEGER, view_kind TEXT, positions_json TEXT, updated_at TEXT, PRIMARY KEY (instance_id, view_kind))` — keeps UI node coordinates out of immutable graph elements |
| `smm_aed_dataset`, `smm_aed_binding`, `smm_aed_alias` | ADR-0012 §2 | Metadata pointers to per-dataset `overlay.db`, match/unmatched counts, and `(project, platform, system_version, element_kind, label_or_type, observed_key)` aliases |
| `fdm_record` | ADR-0014 §2 | System Field Records catalog (indexed on `(project, platform, system_version, uploaded_at)` and standalone `(uploaded_at)` and `(source)`) |
| `dve_user`, `dve_api_token` | ADR-0019 §1 | Session epoch/role cache and SHA-256 hashed scoped API tokens |

### 3. Provenance lineage and append-only audit log

* **`common_artifact`:** registers every persisted output atomically on creation:
  * `artifact_id TEXT PK`, `kind` in `('model_data_file', 'model_instance', 'synthetic_data_set', 'field_record_raw', 'field_record_normalized', 'analytical_evaluation_data', 'report')`;
  * `location` (workspace-relative path or graph `instance_id`), `sha256` (`NOT NULL` for file artifacts);
  * `project`, `platform`, `system_version`, `created_by`, `created_at`, `producing_operation_id`, `tool_version`, `attributes` (JSON).
* **`common_artifact_input`:** `(artifact_id, input_artifact_id, role, PRIMARY KEY (artifact_id, input_artifact_id, role))`, forming an immutable provenance DAG from reports and findings back to AED, field/synthetic sets, model instances, Model Data files, Git commit hashes and CMDB snapshot timestamps.
* **`common_audit_event`:** `(event_id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, actor TEXT NOT NULL, actor_kind TEXT NOT NULL, action TEXT NOT NULL, target TEXT NULL, outcome TEXT NOT NULL, details TEXT NULL)`.
  * Enforced append-only via `BEFORE UPDATE` and `BEFORE DELETE` SQLite triggers (`SELECT RAISE(ABORT, 'common_audit_event is append-only')`).
  * Records login/logout, token creation/revocation, data-source CRUD/connects, manual topology edits, operation start/cancel, working-model edits/undos, profile changes, and report exports.

### Consequences

* Good, because SQLite needs zero daemon administration offline, `common.db` works identically in parent and `spawn` child processes on CentOS 7, and keeping bulk AED metrics in per-dataset `overlay.db` files keeps `dsm.db` writes fast and contention-free.
* Good, because `outcome_status`, `conformance`, `result_summary`, and `severity_rank` satisfy MDG.19, DVE.18, DVE.21–26, DVE.58/70, and DVE.78 directly in SQL.
* Bad, because `dsm.db` is single-host only and duplicates inventory summary rows alongside the authoritative Model Data JSON file.

### Confirmation

* Migration gate runs all CSC SQL migrations from scratch and from the prior schema on CPython 3.9 (`common.db` tested both with stdlib `sqlite3` and forced `pysqlite3` fallback, including inside `spawn` subprocesses).
* Concurrency test runs 10 child processes (4 `pipeline`, 4 `interactive`, 2 `simulation`) streaming logs and findings while 20 simulated user threads read `dve_user` and `dve_finding`, asserting zero `OperationalError: database is locked` failures.
* SQL tests verify `severity_rank` sort order, `common_audit_event` `UPDATE`/`DELETE` trigger rejection, and complete end-to-end lineage traversal from a finding to Git commit hashes and CMDB query timestamp.

## Pros and Cons of the Options

### Embedded SQLite via `common.db` with `pysqlite3-binary` fallback (chosen)

* Good, because it requires no server process, backs up atomically via the SQLite online-backup API, and handles multi-field SQL filtering/sorting cleanly.
* Bad, because it permits one writer at a time on one host (mitigated by WAL, < 50 ms transactions, and externalized read-only AED `overlay.db` files).

### Native PostgreSQL or MySQL server (earlier SDP §5)

* Good, because row-level MVCC supports high multi-host write concurrency.
* Bad, because provisioning, patching, securing and backing up an extra RDBMS daemon offline violates QA-10 for single-host workloads.

### In-memory state and ad-hoc JSON files (as built)

* Good, because it needs zero SQL migrations.
* Bad, because restarts lose task history and interruption records (violating DVE.24 and QA-04), and cross-run filtering (DVE.23) requires full directory scans.

### Normalized relational columns with JSON text for variable evidence (chosen)

* Good, because indexed columns serve DVE.23/FDM.4 queries directly while JSON `evidence` and `result_summary` vary cleanly per rule and operation type.
* Bad, because `dve_finding_affected` duplicates entity keys alongside `dve_finding.affected` JSON.

### Findings stored inside the graph or as per-operation JSON files

* Good, because findings sit next to graph nodes or need one file write.
* Bad, because deleting a candidate/working graph instance would destroy its historical findings, and Cypher/file scans are poor for cross-operation tabular paging.

### Artifact registry, lineage table and append-only audit log (chosen)

* Good, because every CSC registers outputs through one simple helper while achieving full cryptographic lineage.
* Bad, because every producing service must remember to call the registration façade.

### Event sourcing across all CSCs

* Good, because audit history is intrinsic.
* Bad, because rebuilding projections for every CSC is disproportionate complexity for a pipeline-oriented static twin.

## More Information

* Code: `mdg/src/mdg/domain/inventory.py`, `mdg/src/mdg/domain/model_setup_data.py`, `mdg/src/mdg/domain/acquired_file.py`, `dve/src/dve/domain/task_status.py`, `dve/src/dve/ports/task_log.py`
* [SDD §2.4](../SDD.md), [SRS §1.1, §5.1, §6.1](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0008, ADR-0009, ADR-0011, ADR-0012, ADR-0014, ADR-0015, ADR-0016, ADR-0018, ADR-0019, ADR-0020
* Revisit if SaaG must scale across multiple active hosts or if R8 load tests demonstrate `dsm.db` write-lock p95 wait times above 100 ms.
