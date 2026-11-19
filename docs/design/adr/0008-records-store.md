# ADR-0008: Records store: operations, findings, provenance and audit

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, security |
| Kind | Decide |
| Traces | MDG.1, 8–9, 14–15, 18, 22; SCG.5–6; FDM.2–3; ADM.1; SMM.5, 26, 35; DVE.6, 15–16, 18, 21–26, 77–78; QA-01, QA-04, QA-08, QA-10 |
| Resolves | DP-29b, DP-29g (storage of the Software Unit Version Inventory and of Findings, Operations & Reports); DP-30b, DP-30g (their entity schemas) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — (absorbs the former ADR-0008) |

## Context and Problem Statement

Several SDD §2.4 stores hold structured records that must be durable, queryable and filterable:

* the Software Unit Version Inventory;
* the Findings, Operations & Reports store;
* saved data-source configurations (MDG.8);
* the model-instance and artifact registries;
* sessions and API tokens.

The SRS also asks for detailed records:

* the content of every finding (DVE.21), with cause-and-effect links (DVE.22), sorting and filtering (DVE.23);
* the cause, stage and time of failed operations (DVE.24);
* scenario metadata (DVE.25) and the report content (DVE.26);
* independent operation IDs with per-unit results (DVE.78);
* "controlled, traceable" data throughout (MDG.1, SMM.26, 35, SCG.6, FDM.3).

As built (`1157784`), the code has no store of its own:

* The inventory is embedded in each Model Data JSON file.
* Task state, logs and credentials live in the API process's memory and are lost on restart (ADR-0006).
* Model Data records `produced_by`, `generated_at` and per-file metadata, but no hashes. `AcquiredFile.updated_at` is the scan time, and timestamps are naive local time.
* There is no lineage and no audit trail.
* MySQL appears only as the *external* CMDB mock in `dev/`.

SDP §5 names PostgreSQL, but the target host is offline and has no container runtime (ADR-0004).

## Decision Drivers

* Records must be durable, transactional, and survive a restart of `dsm` (QA-04, QA-08).
* No new server process on the offline host unless it is needed (QA-10). All writers are one process tree on one host.
* Every result must be traceable to the exact inputs, rules and tool version that produced it (QA-04). Security-relevant actions must be attributable (QA-01).
* Findings have a fixed core plus variable evidence (DVE.21). One record model serves every long-running activity.

## Considered Options

* Store: SQLite through Python's `sqlite3` / PostgreSQL installed natively (SDP §5) / MySQL / in memory and JSON files (as built)
* Findings: relational records with JSON text for variable parts / findings in the graph / one JSON document per operation
* Provenance: an artifact registry with hashes, lineage and an audit log / ad-hoc metadata (as built) / event sourcing

## Decision Outcome

Chosen options: **SQLite**, **relational operation and finding records with JSON text**, and **an artifact registry with lineage and an append-only audit log**. SQLite is an embedded library, not a server, so it needs no installation, service account or port, and one file is simple to back up (ADR-0004). DVE.23's multi-field filtering maps directly onto indexed columns. One registry design gives end-to-end lineage without restructuring every CSC around events.

### 1. Store

* **File:** `<data_dir>/dsm.db`, with `data_dir` outside the package (ADR-0004). It is owned by the service user with mode 0600.
* **Engine version:** SQLite ≥ 3.24 is required, for `INSERT … ON CONFLICT`. CentOS 7's system library is 3.7.17.
  * `dsm` checks `sqlite3.sqlite_version` at start-up and falls back to `pysqlite3`, from the `pysqlite3-binary` wheel in `dve/wheelhouse/`. That module bundles a recent SQLite; its manylinux tag is confirmed when the wheelhouse is built.
  * JSON is stored as `TEXT` and never queried with SQLite's JSON functions.
* **Connections:** one per thread or process, never shared across a fork or spawn. Each sets `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000` and `synchronous=NORMAL`. Writes are short transactions, and a child process writes only its own operation's rows.
* **Access:** repository ports per CSC (ADR-0003), plain SQL in the adapters, no ORM.
* **Migrations:**
  * numbered SQL scripts per CSC in `<csc>/src/<csc>/migrations/NNNN_<name>.sql`, applied at start-up;
  * recorded in `schema_migration(csc, number, applied_at)`, and stamped with `PRAGMA user_version`;
  * a failed migration rolls back and stops start-up.
* **Naming:** one table prefix per owning CSC (`mdg_`, `smm_`, `fdm_`, `dve_`, …), plus `common_` for operations, artifacts and audit. Short names are used below.
* **IDs and times:** IDs are `uuid4().hex`. Timestamps are ISO 8601 UTC with offset, from timezone-aware `datetime`.
* **Placed here:**
  * the inventory, also kept in the Model Data file;
  * data-source configurations, encrypted (ADR-0030);
  * the operation, finding and report records (§2);
  * the model-instance registry and edit log (ADR-0015);
  * the provenance and audit records (§3);
  * sessions and API tokens (ADR-0030).
* **Not here:** the System Model graph (ADR-0015), Model Data files (ADR-0013), and bulk telemetry (ADR-0020).
* **Inventory schema (DP-30b),** mirroring `SoftwareUnitVersion` and `CandidateUnitVersion` (MDG.14–15):

  ```sql
  CREATE TABLE mdg_inventory_unit (
    operation_id   TEXT NOT NULL,   -- the producing Model Data run
    project        TEXT NOT NULL,
    platform       TEXT NOT NULL,
    system_version TEXT NOT NULL,
    unit_name      TEXT NOT NULL,
    version        TEXT NOT NULL,
    is_candidate   INTEGER NOT NULL CHECK (is_candidate IN (0, 1)),
    PRIMARY KEY (operation_id, unit_name)
  );
  CREATE INDEX mdg_inventory_unit_sel ON mdg_inventory_unit (project, platform, system_version);
  ```

### 2. Operation and finding records (DP-30g)

**`operation`**

| Column | Notes |
|---|---|
| `operation_id` | Generated by the API before submission and used as the task ID (ADR-0006); exposed to users and automation clients (DVE.78) |
| `parent_operation_id` | Set for the per-unit sub-operations of a multi-unit evaluation (DVE.78) |
| `type` | `model_data_production`, `model_construction`, `synthetic_data_production`, `aed_production`, `structural_verification`, `simulation_analysis`, `field_analysis`, `installation_evaluation` |
| `project`, `platform`, `system_version` | Selection (DVE.4) |
| `requested_by`, `client_kind` | User or automation-client identity; `ui` / `cli` / `automation` |
| `inputs` | JSON: model instance and revision, AED reference, rule catalog version and profile, scenario inputs (DVE.25), parameters |
| `state` | `queued`, `running`, `succeeded`, `failed`, `cancelled`. These map one to one to the as-built `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `REVOKED` |
| `progress_percent`, `progress_phase` | From the `progress(percent, phase)` callback |
| `result` | `conforming` / `non-conforming` / null (DVE.18); for evaluations also score, class and decision (ADR-0027) |
| `failure` | JSON error record (ADR-0013) plus `stage` (DVE.24): a pipeline phase, `interrupted` or `shutdown` (ADR-0006) |
| `queued_at`, `started_at`, `ended_at` | UTC |
| `executor_ref` | Child process ID while running |

**`finding`** (DVE.21)

| Column | Notes |
|---|---|
| `finding_id` | Displayed as `<operation short id>-<sequence>` |
| `operation_id` | Owning operation |
| `rule_id`, `rule_version` | Related verification rule (ADR-0022) |
| `finding_type` | For example `qos_mismatch`, `unpublished_topic`, `cycle`, `capacity_exceeded`, `drift_missing` |
| `severity` | `informational`, `low`, `medium`, `high`, `critical` |
| `description` | Text |
| `affected` | JSON array of entity references `{label, key}` and relationship references `{type, from, to}` (ADR-0014) |
| `acceptance_criterion`, `blocking` | Copied from the rule at execution time |
| `evidence` | JSON with supporting data |

* **`finding_link`** (DVE.22): `(cause_finding_id, effect_finding_id, kind)`, within one operation.
* **`finding_affected`** (the DVE.23 "affected nodes" filter): `(finding_id, element_kind, label_or_type, key)`, one row per affected entity or relationship. `element_kind` is `node` or `relationship`, and `key` is the ADR-0014 name or `from->to`.
* **`operation_log`:** `(operation_id, seq, at, level, message)`. It replaces `InMemoryTaskLog` behind `ITaskLog`, and the `?after=` / `log_after` cursor is `seq`.
* **Reports (DVE.26):** generated on demand from these tables (ADR-0027). The report metadata is stored; the file is registered as an artifact (§3).
* **Indexes:**
  * `finding(operation_id, severity)`, `finding(rule_id)`, `finding(finding_type)`;
  * `finding_affected(label_or_type, key)`;
  * `operation(project, platform, system_version, type, queued_at)`;
  * `operation_log(operation_id, seq)`.

### 3. Provenance and audit

* **`artifact`:** every persisted output is registered when it is created. Columns:
  * `artifact_id` and `kind`, one of `model_data_file`, `model_instance`, `synthetic_data_set`, `field_record`, `analytical_evaluation_data`, `report`;
  * `location` (path, graph name or table key) and `sha256`;
  * `project`, `platform`, `system_version`;
  * `created_by`, `created_at`, `producing_operation_id`;
  * `tool_version` (package version plus git commit);
  * `attributes` (JSON; for example `source_kind: field | synthetic` for AED, SMM.35).
* **Lineage:** `artifact_input(artifact_id, input_artifact_id, role)`. For example:
  * Model Data file ← CMDB selection and clone commit hashes;
  * baseline model ← Model Data file;
  * AED ← field records or synthetic data;
  * report ← operation.

  Operations record their input artifact IDs, rule catalog version and profile. Non-SaaG inputs (the CMDB query time and selection, the repository URL, tag and commit) are attributes of the consuming artifact (ADR-0010).
* **`audit_event`:** `(at, actor, actor_kind, action, target, outcome, details)`, append-only.
  * SQLite has no roles, so triggers abort any `UPDATE` or `DELETE`: `CREATE TRIGGER … BEFORE UPDATE ON common_audit_event BEGIN SELECT RAISE(ABORT, 'append-only'); END`.
  * Events recorded:
    * login success and failure, and logout;
    * API token create and revoke;
    * data-source configuration changes and connects;
    * operation start and cancel;
    * working-model edits (summary only);
    * rule profile selection;
    * report export.
* **Registration discipline:** stores have one `save` path that also registers the artifact. Lineage rows outlive the artifacts they describe. Retention follows ADR-0004 §5.

### Consequences

* Good, because nothing new is installed on the offline host, and backup is one online-backup call.
* Good, because DVE.21–26 are met by construction: findings filtering is plain SQL, and the same records feed the UI, the reports and the CI result.
* Good, because any finding can be traced back and re-run: finding → operation → model instance and revision → Model Data file and hash → commits and CMDB selection.
* Bad, because there is one writer at a time. WAL and short transactions keep this acceptable at the ADR-0006 concurrency, and ADR-0036 checks it under load.
* Bad, because the store cannot be shared by a second host, and the inventory exists both here and in the Model Data file.
* Bad, because `affected` is written twice (JSON and side table), and every producing path must register its artifact.

### Confirmation

* Every CSC's migrations run in CI on a fresh database and on a copy of the previous release's, using the oldest supported SQLite library.
* A concurrency test runs the maximum number of operations writing logs at once, with no `database is locked` error.
* A test asserts that every finding has every non-null DVE.21 field.
* An end-to-end test walks the lineage from a finding back to the clone commit hashes.
* A database test asserts that `UPDATE` and `DELETE` on `audit_event` fail, and a test asserts that every timestamp `mdg` writes is timezone-aware.
* The findings list endpoint meets the ADR-0036 latency budget.

## Pros and Cons of the Options

* SQLite: Good, because it is embedded, needs no administration, and is in the standard library. Bad, because it allows a single writer on a single host, and CentOS 7's library is too old (handled by the fallback).
* PostgreSQL or MySQL: Good, because they allow many concurrent writers. Bad, because each is a server to install, patch, secure and back up offline. MySQL would also blur the line with the external CMDB.
* In memory and JSON files (as built): Bad, because records are lost on restart, which fails DVE.24 and QA-04.
* Findings in the graph: Bad, because they would be lost when instances are deleted, and paging in Cypher is weaker. A JSON document per operation would mean scanning documents to filter.
* Event sourcing: Good, because history is implicit. Bad, because it means a redesign of every CSC, out of proportion to the need.

## More Information

* Code: `mdg/src/mdg/domain/inventory.py`, `mdg/src/mdg/domain/model_setup_data.py`, `mdg/src/mdg/domain/acquired_file.py`, `dve/src/dve/domain/task_status.py`, `dve/src/dve/ports/task_log.py`, `dve/src/dve/adapters/in_memory_task_log.py`
* [SDD §2.4](../SDD.md), [SRS §6.1.1](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0010, ADR-0013, ADR-0014, ADR-0015, ADR-0022, ADR-0027, ADR-0030, ADR-0036
* Revisit if the CSCI must run on more than one host, or if ADR-0036's load test shows write contention.
