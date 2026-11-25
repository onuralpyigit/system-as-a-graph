# ADR-0009: Model Data file format, and common validation and error records

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | MDG.1, 14–16, 18–23; SCG.4; FDM.5; ADM.5–6; SMM.2–3, 25–26, 37; DVE.5, 8, 14–15, 24; SDD §1 decision 5; QA-03, QA-04, QA-05 |
| Resolves | DP-29a, DP-30a (storage and entity schema of the Model Data file) |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

MDG.23 requires MDG to prepare verified source data and save it as a **Model Data file**, while SMM.2–3 require SMM to ingest and validate format, schema, integrity and mandatory fields before constructing the System Model. DVE.5 lists Model Data files per `(project, platform, system_version)` selection. Across the CSCI, SDD §1 decision 5 and SRS MDG.16, 19–22; FDM.5; ADM.5–6; SMM.3, 25, 37; DVE.8, 24 require one consistent validation and structured error-recording model.

**As built (`1157784`) and code-audit findings:**

* **Filesystem layout:** `FilesystemModelSetupDataStore` writes `<workspace>/<project>/<platform>/<version>/<run_id>/<project>_<platform>_<version>.json`.
  * **Security/containment bug:** `Workspace._name(component)` (`workspace.py:40-41`) runs `re.sub(r"[^A-Za-z0-9._-]", "_", component)`, which leaves `".."` intact (`_name("..") == ".."`), and while `add()` and `resolve()` check `Workspace.contains()`, **`save()` (`filesystem_model_setup_data_store.py:29-37`) and `ProduceModelSetupData.execute()` (`produce_model_setup_data.py:137`) never call `Workspace.contains()`**.
* **Validation & exclusion bugs:**
  * **`MDG.23` violation (`produce_model_setup_data.py:200`):** `CheckMandatoryFields` records `ErrorRecord`s for invalid items, **but `ProduceModelSetupData` still passes the failed items into `ModelSetupDataGraph.build()` and saves them into `graph`!**
  * `CheckMandatoryFields` (`check_mandatory_fields.py:30-41`) checks only 8 raw fields for `None`/`""`, ignoring `"NOT_FOUND"`, `-1`, `Topic.size`, and `Node`/`Network` attributes.
  * `ModelSetupDataGraph.build()` (`model_setup_data_graph.py:47-50`) populates `lib_ids` only from `Application → Library` `USES`, silently dropping transitive `Library → Library` targets, generates fake `priority`/`hotstandby` from `random.Random(name)`, derives topic `frequency`/`criticality` from mocked QoS, deduplicates `topics` by name (discarding conflicting unit definitions needed by `DVE.38` and per-endpoint QoS needed by `DVE.32–35`), and emits `"NOT_FOUND"` / `-1` sentinels.
* **Error records:** `ErrorRecord` (`error_record.py:15-28`) uses uppercase `ERROR | MISSING_DATA`, combines `project_platform` into one string, uses naive timestamps, tags missing Git units in `ProduceModelSetupData._missing` with `source_type = "config_mgmt_db"`, and loses `self.record` across child-process pipes (`ADR-0003`).

## Decision Drivers

* SMM.3 requires a formal, machine-checkable schema, cryptographic integrity check, and explicit placeholder tracking so unknown values are never mistaken for architectural facts (QA-03, QA-04).
* MDG.23 requires source items failing mandatory-field checks to be excluded from the constructed `graph` payload while keeping their `ErrorRecord`s in `errors`.
* Model Data 1.0 must carry all extracted fields needed by ADR-0010 (`qos_lifespan_ms`, per-endpoint `declared_type_hash`/`declared_qos`, `brokers`, `communication_services`, `transfers`, unit `cpu_allocation`/`os_settings`/`runtime_config`, and `field_schema` for `SCG.4`).
* Error records must cover every SRS error category (`SMM.25` missing entity vs. invalid relationship, `SMM.37` unmatched record, `MDG.16/20` access/auth/format/integrity/missing data) and survive child-process IPC intact.

## Considered Options

* Model Data storage & format: Versioned, schema-validated JSON file per run on the filesystem with SHA-256 registration (as built, extended)
* Model Data storage & format: Normalized relational tables in SQLite without a file
* Model Data storage & format: Engine-specific graph dump format
* Error model: Shared `ErrorRecord` type in `common/errors.py` with structured category, stage and scope
* Error model: Copying the legacy `mdg` `ErrorRecord` unchanged
* Error model: Separate error classes/schemas per CSC

## Decision Outcome

Chosen options: **a versioned, JSON-Schema-validated JSON file per run on the filesystem (as built, extended)** and **one shared `ErrorRecord` type in `common/errors.py`**.

### 1. Model Data file (`DP-29a`, `DP-30a`; MDG.1, 14–15, 18–23; SMM.2–3)

* **Filesystem location & path-traversal hardening:** `<workspace>/<project>/<platform>/<version>/<run_id>/<project>_<platform>_<version>.json`, where `workspace` is under `/var/lib/dsm/workspace/` (ADR-0004) and `run_id` is the producing `operation_id` (ADR-0007).
  * `Workspace._name()` explicitly rejects `.` and `..` path segments, and **every** path builder (`run_dir`, `save`, `add`, `resolve`) enforces `Workspace.contains()` before touching disk.
  * Files are written to `<name>.json.tmp`, `fsync`ed, atomically renamed, hashed (`SHA-256`), and registered in `common_artifact` (`kind = 'model_data_file'`, ADR-0007). SMM verifies both the `SHA-256` digest and `model-data-1.0.schema.json` before construction (SMM.3).
* **Schema validation (`jsonschema`):**
  * Pin `jsonschema==4.17.3` (`<4.18`, keeping pure-Python `attrs` and `cp39` `manylinux2014_x86_64` `pyrsistent` in `common/wheelhouse/` so `mdg`, `smm`, `scg`, `fdm` and `adm` share one offline validator).
  * Published at `mdg/src/mdg/schemas/model-data-1.0.schema.json`; validated on `MDG` save, `POST …/mdg-files` upload, and `SMM` ingest.
* **Top-level structure of `model-data-1.0.schema.json`:**
  * `schema_version`: `"1.0"`;
  * `status`: `"ok" | "missing_data" | "error"` — explicitly records the overall acquisition outcome (`MDG.19`, mirrored in `common_operation.outcome_status`). When a unit is missing mandatory files (`MDG.19`) or fails mandatory-field checks (`MDG.21`), **that invalid item/unit is excluded from `graph` (`MDG.23`)**, its errors are recorded in `errors`, and a `missing_data` file may still be saved for inspection while SMM refuses silent baseline promotion without operator override;
  * `provenance`: `{operation_id, produced_by, generated_at (UTC ISO 8601), tool_version, cmdb_source_id, cmdb_queried_at, git_source_id, package_source_id, topology_source_id, topology_mode, unit_commits: {unit_name: commit_sha}}` (`MDG.1`);
  * `context`: `{project, platform, system_version, is_effective_version}`;
  * `inventory`: full `SoftwareUnitVersion` list including `unit_kind` (`application | library`) and `is_candidate` (`MDG.14–15`);
  * `packages`: per-unit `{name, version, artifact_name, sha256, size_bytes}` (`MDG.4`, ADR-0008);
  * `acquired_files`: repo-relative `file_path`, `file_name`, `unit_name`, `version`, `commit_sha`, UTC `updated_at` (`MDG.18`);
  * `placeholders`: array of `{json_pointer, entity_key, reason}` replacing `"NOT_FOUND"`, `-1`, and seeded random `priority`/`hotstandby` values (`QA-03`);
  * `errors`: array of serialized `ErrorRecord` objects (§2);
  * `graph`: aligned 1-to-1 with ADR-0010's structural model:
    * **Collections:** `hierarchy` (`systems`, `segments`, `cscis`, `cscs`), `roles`, `nodes` (`cpu_cores`, `memory_gb`, `kind`, `os_type`, `ip_address`, `os_settings`, plus UI fields `group, hw, mw, gpu, display`), `network_devices` (`name`, `role`), `brokers` (`name`, `type`, `version`, `max_connections`), `communication_services` (`name`, `technology`, `version`), `applications` (including `cpu_allocation`, `os_settings`, `runtime_config`, `is_candidate`), `libraries` (including transitive `Library → Library` dependencies and `is_candidate`), `topics` (including `qos_durability`, `qos_reliability`, **`qos_lifespan_ms`**, `qos_transport_priority`, `qos_deadline_ms`, `qos_history_depth`, `field_schema`, `definition_conflict`), and `messages` (`message_id`, `size_bytes`, `frequency`, `fields_hash`, `field_schema`);
    * **Relationships:** `contains`, `assigned_to`, `runs_on`, `uses` (`Application | Library → Application | Library`, `SMM.22`), `publishes_to` and `subscribes_to` (**carrying per-endpoint `declared_type_hash`, `declared_size`, and `declared_qos` for `DVE.32–35, 38`**), `routes`, `uses_service` (`{direction, protocol, source_endpoint, destination_endpoint}`), `transfers` (`CommunicationService → Message | Topic`, `{direction, source, destination}`, `DVE.39`), `carries`, `sends`, `receives`, and `connects_to` (`from_interface`, `to_interface`, `capacity_mbps`).
* **Backward compatibility:** minor `1.x` versions add optional fields only; pre-1.0 files lacking `schema_version` are loaded through a read-only `0.x` adapter (translating uppercase `ERROR`/`MISSING_DATA`, `networks` → `network_devices`, and `"NOT_FOUND"`/`-1` → `placeholders`).

### 2. Common validation and error records (`common/src/common/errors.py`)

* **Canonical `ErrorRecord` fields:**

  | Field | Type & Values |
  |---|---|
  | `status` | `error` \| `missing_data` \| `warning` (lowercase in 1.0; `0.x` converter maps legacy `ERROR`/`MISSING_DATA`) |
  | `category` | `access` \| `authorization` \| `integrity` \| `format` \| `schema` \| `missing_field` \| `missing_data` \| **`missing_entity`** \| `invalid_relationship` \| **`unmatched_record`** \| `internal` |
  | `reason` | Human-readable diagnostic message (secrets redacted) |
  | `source_name`, `source_type` | Accurate origin identifier and source kind (fixing `ProduceModelSetupData._missing` and `AcquireProjectContext._record` mislabeling) |
  | `stage` | Pipeline phase: `acquire_context`, `acquire_packages`, `clone`, `build`, `parse`, `validate`, `construct`, `ingest_field`, `generate_synthetic`, `produce_aed`, `bind`, `rule:<id>`, `interrupted`, `shutdown` (DVE.24) |
  | `project`, `platform`, `system_version` | Separate strings (replacing combined `project_platform`) |
  | `subject` | Optional entity key, unit name, repo-relative file path, or record ID |
  | `operation_id` | Owning `common_operation.operation_id` |
  | `occurred_at` | Timezone-aware UTC ISO 8601 timestamp |

* **IPC-safe propagation:** `DomainOperationError` (and `DataAcquisitionError`) implements `__reduce__` returning `(cls, (self.record,))`, and `MultiprocessingTaskRunner` serializes `record.to_dict()` directly over the child pipe (ADR-0003, ADR-0006).
* **Standard four-step validation order** across MDG, SMM, SCG, FDM and ADM:
  1. readability and container/syntax format (`format`);
  2. JSON/YAML/XML schema conformance (`schema`);
  3. cryptographic hashes and cross-entity referential checks (`integrity`, `missing_entity`, `invalid_relationship`);
  4. mandatory domain field presence (`missing_field`, `missing_data`).
  All validation errors on an input batch are collected before rejecting invalid items.

### Consequences

* Good, because SMM, SCG and DVE receive a strictly validated, hash-verified JSON 1.0 contract with zero fake random attributes or `"NOT_FOUND"` sentinels.
* Good, because `missing_entity`, `invalid_relationship`, and `unmatched_record` map 1-to-1 to SMM.25 and SMM.37, and records survive child-process boundaries intact.
* Bad, because `ModelSetupDataGraph.build()` and `graph.js` (`"NOT_FOUND"` handling, ADR-0015) require a coordinated R3 update alongside the `0.x` compatibility reader.

### Confirmation

* Schema test validates `produce_model_data` output against `model-data-1.0.schema.json` and asserts zero `"NOT_FOUND"`, `-1`, or random-seeded values.
* Exclusion test (`MDG.23`, `TC-MSG-05`): injecting a record with a missing mandatory field records an `ErrorRecord` in `errors` and **excludes** that item from `graph`.
* Security test verifies `Workspace` rejects `".."` in `save()`, `add()`, and `resolve()`.
* IPC test raises `DataAcquisitionError(record)` inside a spawned child process and verifies the exact `ErrorRecord` fields in `common_operation.failure`.

## Pros and Cons of the Options

### Versioned, schema-validated JSON file per run on the filesystem (chosen)

* Good, because it matches the SRS "Model Data file" requirement literally, is human-inspectable, downloadable, and trivially hash-verifiable.
* Bad, because cross-run metadata queries require indexing summary attributes in `dsm.db` (`common_artifact`, ADR-0007).

### Normalized relational rows in SQLite without a file

* Good, because SQL queries can inspect elements across runs directly.
* Bad, because shredding nested graph payloads across dozens of tables complicates export/upload (`DVE.5`) and weakens single-file cryptographic evidence.

### Engine-specific graph dump format

* Good, because bulk graph loading can be faster.
* Bad, because it couples MDG to ADR-0011's graph server and breaks human readability and schema validation.

### Shared `ErrorRecord` in `common/errors.py` (chosen)

* Good, because one error schema, UI renderer, and SQLite representation serves every CSC (`SDD §1 decision 5`).
* Bad, because existing `mdg` error call sites and tests must migrate to separated `project`/`platform`/`system_version` and lowercase `status`.

### Copying the legacy `mdg` `ErrorRecord` unchanged

* Good, because `mdg` needs no refactor.
* Bad, because `category` is missing, `project_platform` is concatenated, and `self.record` is lost across `spawn` pipes.

### Separate error models per CSC

* Good, because each CSC tailors its own fields freely.
* Bad, because it violates SDD §1 decision 5 and forces DVE to maintain six error mappers.

## More Information

* Code: `mdg/src/mdg/domain/model_setup_data.py`, `mdg/src/mdg/domain/model_setup_data_graph.py`, `mdg/src/mdg/domain/workspace.py`, `mdg/src/mdg/domain/error_record.py`, `mdg/src/mdg/services/produce_model_setup_data.py`, `mdg/src/mdg/services/check_mandatory_fields.py`
* Related: ADR-0002, ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0008, ADR-0010, ADR-0011, ADR-0012, ADR-0015
* Revisit if single Model Data JSON files exceed 200 MB uncompressed, in which case transparent `.json.gz` compression may be added in schema version `1.1`.
