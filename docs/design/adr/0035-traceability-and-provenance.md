# ADR-0035: Traceability, provenance and audit trail

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, security, quality assurance |
| Kind | Decide |
| Traces | MDG.1, 9, 14, 18, 22; SCG.5–6; FDM.2–3; ADM.1; SMM.5, 26, 35; DVE.16, 24–26, 78; QA-04 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

"Controlled, traceable" appears in almost every CSC's first requirement (MDG.1, ADM.1), and specific requirements name what to record:

* the Model Data file used for a model (SMM.26);
* the field-versus-synthetic source of Analytical Evaluation Data (SMM.35);
* scenario inputs (SCG.6, DVE.25);
* upload source and time (FDM.3);
* project, platform and system version everywhere.

As built:

* Model Data records `produced_by`, `generated_at` and per-file metadata.
* Run IDs are Celery task IDs.
* Timestamps are naive local time.
* Nothing links derived results back to their inputs beyond file paths.
* There is no audit trail of who did what.

## Decision Drivers

* Every result (finding, report, installation decision) must be traceable to the exact inputs, rules and tool version that produced it, and reproducible (QA-04).
* Security-relevant actions must be attributable to a user or automation client (QA-01).
* One mechanism for all CSCs, not one per artifact type.
* Records must be tamper-evident and append-only.

## Considered Options

* Ad-hoc metadata fields on each artifact (as built)
* An artifact registry with content hashes and a lineage graph, plus an audit log, in the relational store
* Full event sourcing of all state changes

## Decision Outcome

Chosen option: "An artifact registry with content hashes and a lineage graph, plus an audit log", in PostgreSQL (ADR-0008). It gives end-to-end lineage with one table design, and it does not restructure every CSC around events.

* **Artifacts:** every persisted output is registered when it is created, in a table `artifact` with:
  * `artifact_id` (UUID) and `kind`, one of `model_data_file`, `model_instance`, `synthetic_data_set`, `field_record`, `analytical_evaluation_data`, `report`;
  * `location` (path, graph name or table key) and `sha256` (content hash, for files and data sets);
  * `project`, `platform`, `system_version`;
  * `created_by` (user or automation-client identity), `created_at` (UTC), `producing_operation_id`;
  * `tool_version` (package version + git commit of the SaaG build);
  * `attributes` (JSONB, kind-specific, e.g. `source_kind: field | synthetic` for AED, SMM.35).
* **Lineage:** `artifact_input(artifact_id, input_artifact_id, role)` links each artifact to the artifacts it was derived from. For example:
  * Model Data file ← CMDB snapshot reference and clone commit hashes;
  * baseline model ← Model Data file;
  * AED ← field records or synthetic data set;
  * report ← operation.

  Operations (ADR-0024) record their input artifact IDs, rule catalog version and profile.
* **External inputs:** inputs that are not SaaG artifacts are recorded as attributes of the consuming artifact: the CMDB query time and selection, and the Git repository URL with tag and commit hash per unit (ADR-0010, ADR-0012). The SaaG artifacts are immutable (ADR-0013, ADR-0016).
* **Timestamps:** all timestamps are UTC, ISO 8601 with offset, from timezone-aware `datetime`.
* **Audit log:** `audit_event(at, actor, actor_kind, action, target, outcome, details)`. It is append-only, and the application role has `INSERT` and `SELECT` only, no `UPDATE` or `DELETE`. Events recorded:
  * login success and failure, logout;
  * API token create and revoke (ADR-0030);
  * data-source configuration create, change, delete and connect (ADR-0032);
  * operation start and cancel;
  * working-model edits (summary; detail is in the change log, ADR-0016);
  * rule profile selection for installation evaluation;
  * report export.
* **Retention:** per ADR-0040. Lineage rows outlive the artifacts they describe, so deleted artifacts remain explainable.

### Consequences

* Good, because any finding or decision can be traced:
  finding → operation → model instance + revision → Model Data file (hash) → commits and CMDB snapshot. It can then be re-run.
* Good, because one mechanism serves SMM.26, SMM.35, SCG.6, FDM.3 and DVE.26's "System Model used / AED used and its data source" report fields.
* Bad, because every producing code path must register its artifact. This is enforced by giving stores a single `save` path that registers.
* Bad, because the audit log grows without bound until retention (ADR-0040) applies.

### Confirmation

* An end-to-end test produces a Model Data file, builds a model and runs verification. It then walks the lineage from a finding back to the clone commit hashes.
* A database test asserts that the application role cannot update or delete `audit_event` rows.
* A test asserts that every timestamp written by `mdg` is timezone-aware.

## Pros and Cons of the Options

### Ad-hoc metadata (as built)

* Good, because it is simple.
* Bad, because there are no links between artifacts, no hashes, and no audit.

### Artifact registry + lineage + audit log

* Good, because it gives complete lineage and attribution with modest schema work.
* Bad, because of the registration discipline it requires.

### Event sourcing

* Good, because the complete history is implicit.
* Bad, because it means a large redesign of every CSC, which is out of proportion to the need.

## More Information

* Code: `mdg/src/mdg/domain/model_setup_data.py`, `acquired_file.py`, `workspace.py`
* Related: ADR-0008, ADR-0010, ADR-0012, ADR-0013, ADR-0016, ADR-0024, ADR-0030, ADR-0032, ADR-0040
