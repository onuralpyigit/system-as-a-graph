# ADR-0008: MDG acquisition: data sources, network topology and source files

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, configuration management owners, system/network engineering, ansible repository owners |
| Kind | Ratify |
| Traces | MDG.2–13, 16–21; SCG.4; SMM.12–24; DVE.7, 32–35, 38–46; QA-01, QA-05, QA-06 |
| Resolves | DP-09 (MDG.6 topology source and method); DP-10 (MDG.19 mandatory file list); DP-17, DP-18, DP-19, DP-20 (protocols of EXT-IF-01 CMDB, EXT-IF-02 source repository, EXT-IF-03 package repository, EXT-IF-04 topology source) |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

MDG acquires data from four external sources (MDG.2–5): the configuration management database (EXT-IF-01), the source code repository (EXT-IF-02), the software units package repository (EXT-IF-03), and the network topology data source (EXT-IF-04). SDD §2.3 leaves all four protocols open (DP-17…DP-20), and the SRS defers the automatic topology acquisition method (MDG.6, DP-09) and mandatory source-repository file list (MDG.19, DP-10). MDG must also support manual topology entry (MDG.7), savable source configurations (MDG.8), CMDB deficiency/access/format error handling (MDG.16), source-file metadata and integrity checking (MDG.17–20), and extraction of the structural, QoS, resource and message-schema facts consumed by SMM, SCG and DVE.

**As built (`1157784`) and code-audit findings:**

* **CMDB (`MysqlConfigManagementRepository`):** PyMySQL 1.0.3, read-only parameterized `SELECT`s over `platform_pkg_version`, `platform_current_atm_version` and `csu_csms_relation` (`connect_timeout=5`, new connection per query). *Gaps:* maps `MySQLError` to `access`, omitting deficiency (`missing_data`) and row-format (`format`) errors (MDG.16); `list_unit_versions` lacks `DISTINCT`.
* **Source repository (`GitSourceCodeRepository`):** runs `git` CLI (`ls-remote --tags --refs` and `clone --depth 1 --branch <version>`, requires `git ≥ 2.14`, ADR-0004) with `DSM_GIT_USER`/`DSM_GIT_PASSWORD` env helper and `GIT_TERMINAL_PROMPT=0`. *Bugs & gaps:*
  * hardcodes `-c http.sslVerify=false` (`git_source_code_repository.py:126`);
  * deletes `.git` without recording `HEAD` commit hash or tagged commit timestamp;
  * `rpartition("/")` without `.rstrip("/")` (`line 56`) breaks repository base URLs ending with `/`;
  * `DataSourceService` joins `"<user>:<password>"` and splits on `:` (breaking usernames containing `:`), and `_redact` (`line 119`) does naive `text.replace(password, "***")` (turning `"dsm-src"` into `"***-src"` when the dev password is `"dsm"`), while auth error detection misses `"terminal prompts disabled"` / `"could not read Username"`;
  * `AcquiredFile` records only the located mandatory files rather than all acquired source, script and configuration files (MDG.17–18), and writes host-absolute workspace paths (`str(path)`) into the JSON output.
* **Package repository (`EXT-IF-03`):** not yet implemented (`SourceType` lacks a package adapter).
* **Topology (`EXT-IF-04`):** `IAnsibleRepoParser` and `ISystemRepoParser` are mocks; `dev/gitea/seed/` holds only READMEs for `ansible_repo` and `system_repo`, and missing/failed clone of `ansible_repo` aborts the run even if manual topology is desired (MDG.7).
* **Mandatory files & unit cloning:** `MandatoryFiles` checks for a `Makefile` with non-comment `include/Makefile_java.mk` plus `<unit_name>.xml`, **but** `ProduceModelSetupData` (`lines 172-177`) clones only units placed on a host by `system_repo` (skipping `common_lib`), and in `dev/gitea/seed/`, `common_lib_1.0.0` and `sensor_app_1.0.0` lack `Makefile`s (diverging from `FakeSourceCodeRepository`).
* **Parsers & optional build:** `SourceCodeParser` parses `<topic name=".." role="pub|sub|pubsub"/>` and Java `import` `uses`; `TypeSupportParser` and `MessageFileParser` are mocks. `GmakeBuildRunner` runs `gmake regenerate_code` (`300 s` timeout) when opted in, but discards `stderr` on non-zero exit and runs `gmake --version` without a timeout.

## Decision Drivers

* Every adapter must work offline on CentOS 7+ (`CPython 3.9`, `git ≥ 2.14`) using standard library or already-vendored wheels (`PyMySQL`, `PyYAML`, ADR-0004).
* Acquisition must be cryptographically reproducible (tag → Git commit SHA + package SHA-256 + CMDB snapshot timestamp, MDG.1, 17–18, QA-04) and TLS-verified with internal CA bundles (QA-01).
* Manual (MDG.7) and automatic (MDG.6) topology paths must share one validation model and emit field names and units identical to the System Model schema (ADR-0010).
* Parsers must extract all structural entities, QoS parameters (including `Lifespan`, DVE.34), per-unit topic content hashes (DVE.38), external-to-middleware service flows (DVE.39), unit resource configs (SMM.24), and message field/range schemas (SCG.4).

## Considered Options

* CMDB (`EXT-IF-01`): PyMySQL read-only adapter (as built, extended)
* CMDB (`EXT-IF-01`): SQLAlchemy Core dialect layer (earlier SDP §5)
* Source repository (`EXT-IF-02`): `git` CLI shallow clone over HTTPS with CA verification (as built, hardened)
* Source repository (`EXT-IF-02`): Git server REST tarball API or Python Git library (`dulwich`/`pygit2`)
* Package repository (`EXT-IF-03`): HTTPS REST metadata & checksum adapter via `urllib.request`
* Package repository (`EXT-IF-03`): Shared filesystem mount
* Network topology (`EXT-IF-04`, `DP-09`): `SourceType.NETWORK_TOPOLOGY` supporting both `git_ansible` (Ansible YAML inventory/vars) and `manual` (`mdg_topology_override`)
* Network topology (`EXT-IF-04`, `DP-09`): Dedicated CMDB tables or manual entry only
* Source extraction: Static XML/YAML/Java/IDL parsing with resource-bounded opt-in `gmake` codegen

## Decision Outcome

Chosen options: **PyMySQL for EXT-IF-01**, **`git` CLI over TLS-verified HTTPS for EXT-IF-02**, **stdlib HTTPS REST (`IPackageRepository`) for EXT-IF-03**, **`SourceType.NETWORK_TOPOLOGY` (`git_ansible` YAML or `manual` SQLite store) for EXT-IF-04 / DP-09**, and **static source/config parsing with a resource-bounded opt-in `gmake` build**.

### 1. External data-source protocols and configuration (MDG.2–5, 8, 16; DP-17…DP-20)

* **EXT-IF-01, CMDB (`DP-17`):** MySQL protocol over TLS/TCP via `PyMySQL`, read-only parameterized SQL, reusing **one connection per acquisition run** (`connect_timeout=5`, `read_timeout=30`). Table/column names are isolated in one mapping dictionary inside `MysqlConfigManagementRepository`.
  * **Error mapping (`MDG.16`):** connection/SQL failures raise `ConfigManagementAccessError` (`category = access`); empty project/platform/version/inventory sets raise `ConfigManagementDeficiencyError` (`status = missing_data`, `category = missing_data`); null/malformed version or hierarchy columns raise `ConfigManagementFormatError` (`category = format`).
* **EXT-IF-02, Source Code Repository (`DP-18`):** Git smart-HTTP over **TLS-verified HTTPS** (`-c http.sslVerify=true`, with optional per-source `-c http.sslCAInfo=<ca_bundle_path>`; `sslVerify=false` is removed from production code).
  * Normalizes trailing `/` on base URLs before resolving `<base>/<unit_name>.git`; stores `username` and `secret` as separate fields on `DataSourceConfig` (retiring `":"`-concatenated `user_info`), uses credential-helper environment variables (`DSM_GIT_USER`, `DSM_GIT_PASSWORD`), detects HTTP `401`/`403` and `"terminal prompts disabled"` / `"could not read Username"` as `SourceRepoAuthError` (`category = authorization`), and redacts credentials via token-boundary/URL-userinfo regexes rather than naive substring replacement.
  * Before removing `.git`, records `commit_sha` (`git rev-parse HEAD`) and tagged commit UTC timestamp (`git show -s --format=%cI HEAD`) for provenance and `AcquiredFile.updated_at` (MDG.18).
* **EXT-IF-03, Software Units Package Repository (`DP-19`, MDG.4):** HTTPS REST over TLS via Python's `urllib.request` (`ssl.create_default_context(cafile=…)`), behind `IPackageRepository`:
  * **Contract:** `GET <connection_address>/api/v1/packages/<unit_name>/<version>` with `Authorization: Bearer <token>` or HTTP Basic auth from `DataSourceConfig`, returning JSON `{name, version, artifact_name, sha256, size_bytes, published_at, unit_kind}` (compatible with Nexus/Artifactory/Gitea package endpoints via adapter path templates).
  * **Role in acquisition:** cross-checks that every inventory unit version exists in the package repository, records package metadata and `sha256` into Model Data `packages` (ADR-0009), and flags missing packages (`missing_data`) or checksum/version mismatches (`SourceRepoIntegrityError`, `category = integrity`). Shipped with `HttpPackageRepository` and `FakePackageRepository` (and seeded mock endpoint in `dev/`).
* **EXT-IF-04, Network Topology Data Source (`DP-20`, MDG.5–7):** configured independently as `SourceType.NETWORK_TOPOLOGY` in `common_data_source` (never piggybacking silently on `EXT-IF-02`'s config), with `access_method` selecting between:
  * `git_ansible` (automatic, **DP-09**, MDG.6): clones the configured topology Git repository at the system version tag over HTTPS using `NETWORK_TOPOLOGY`'s own address and credentials;
  * `manual` (MDG.7): reads the operator-entered topology JSON stored in `mdg_topology_override` (`dsm.db`, ADR-0007) for `(project, platform, system_version)` and **skips cloning `ansible_repo` entirely**. An operator may also apply a `manual` override on top of `git_ansible`; both record `origin = manual` in provenance without writing back to Git.
* **Savable configurations (MDG.8):** persisted in `common_data_source` (`dsm.db`, ADR-0007) with `scope` (`user`, `project`, or `system` so CI API tokens resolve project/system sources cleanly, ADR-0019 §2–3) and AES-256-GCM encrypted secrets. Connecting a source runs a lightweight reachability probe (`SELECT 1`, `git ls-remote`, `HEAD /api/v1/packages`, DVE.7).

### 2. Network topology YAML schema and ADR-0010 alignment (MDG.5–7; DP-09)

`AnsibleRepoParser` parses YAML via `yaml.safe_load` (`PyYAML`, zero Jinja execution; unexpanded `{{ … }}` templates become `null` + `placeholders` entries per ADR-0009) from `inventory.yml` (or `hosts.yml`), `group_vars/<group>.yml`, and `host_vars/<host>.yml`, emitting canonical ADR-0010 field names and units directly:

| Ansible YAML key (`host_vars` / `group_vars`) | Emitted Model Data / ADR-0010 field | Used by |
|---|---|---|
| `saag_kind` (`operator_console` \| `processor`) | `Node.kind` | SMM.14; DVE.40 |
| `saag_cores` (int), `saag_ram_gb` (float) | `Node.cpu_cores`, `Node.memory_gb` | SMM.14; DVE.41–46 |
| `saag_os_type`, `saag_ip_address` | `Node.os_type`, `Node.ip_address` | SMM.14 |
| `saag_os_settings` (mapping: `isolated_cores`, `rt_throttling`, `swappiness`, `hugepages`, `limits`) | `Node.os_settings` | SMM.24; DVE.44, 46 |
| `saag_hw`, `saag_mw`, `saag_gpu`, `saag_display` | `Node.hw`, `mw`, `gpu`, `display` (+ inventory group → `Node.group`) | ADR-0015 hardware cabinet view |
| `saag_network_devices`: list of `{name, role: switch \| router}` | `NetworkDevice` (`name`, `role`) | SMM.15; Rule 7 |
| `saag_interfaces`: list of `{device, dev_raw, peer_device, peer_interface, bandwidth_gbps}` | `CONNECTS_TO` (`from_interface = device`, `to_interface = peer_interface`, `dev_raw`, **`capacity_mbps = bandwidth_gbps × 1000`**) | SMM.15, 18; DVE.40, 57 |

* Missing topology files yield `missing_data`; invalid YAML/types yield `format` `ErrorRecord`s; hosts referenced by `system_repo` without `host_vars` are retained with `placeholders` entries so resource rules flag incomplete capacity explicitly.

### 3. Mandatory files, unit classification and source extraction (MDG.17–21; DP-10)

* **Cloning all inventory units & classifying `Application` vs. `Library` (MDG.14, 17):**
  * MDG clones **every** software unit in the Software Unit Version Inventory (not only host-placed units).
  * A unit is classified as `Application` if `system_repo` places it on at least one `Node` (`runs_on`) or CMDB/package metadata marks `unit_kind = application`; otherwise, if it is a shared dependency (`unit_kind = library` or referenced via `uses`), it is classified as `Library`.
* **Mandatory source-repository file set (MDG.19, DP-10):**

  | Unit kind | Mandatory files | Missing-file outcome |
  |---|---|---|
  | `Application` | 1. A `Makefile` under the unit whose non-comment text matches `[mandatory_files] makefile_include_patterns` (e.g. `include/Makefile_java.mk`)<br/>2. `<unit_name>.xml` unit manifest | Unit status `missing_data`, `ErrorRecord(status='missing_data', category='missing_data')`, and overall operation `outcome_status = 'missing_data'` (MDG.19, ADR-0007) |
  | `Library` | At least one build/descriptor file: matching `Makefile` **or** `<unit_name>.xml` (allowing header/shared libraries without a pub/sub manifest and manifest-backed libraries like `common_lib`) | Same `missing_data` recording |
  | `system_repo`, `ansible_repo` | Validated by `SystemRepoParser` / `AnsibleRepoParser` (§2) rather than `MandatoryFiles` | Reported per §2 |

  * `dev/gitea/seed/` and `FakeSourceCodeRepository` are aligned to one shared seed layout (`common_lib_1.0.0` valid library, `nav_app_1.0.0` valid application, plus dedicated negative-test tags/units for `TC-MSG-04`).
* **Integrity checking and file recording (MDG.18, 20):**
  * `SourceRepoIntegrityError` (`category = integrity`) is raised on non-zero `git` checkout/object verification, unreadable/corrupt UTF-8 or malformed XML/YAML syntax in unit descriptors, or mismatch against `IPackageRepository`'s source/package digest.
  * `AcquiredFile` records **every** acquired source file, installation script (`.sh`, `.service`, Ansible deploy tasks) and configuration file (`.xml`, `.yaml`, `.properties`, `.conf`) within the unit—with **repo-relative** `file_path`, `unit_name`, `version`, `commit_sha`, and tagged commit UTC `updated_at` (MDG.17–18).
* **Static parsers replacing the remaining mocks:**
  1. **`SystemRepoParser`:** parses deployment descriptors in `system_repo` to extract:
     * `System → SoftwareSegment → CSCI → CSC` hierarchy (supplementing CMDB `csu_csms_relation`), `Role` definitions and `ASSIGNED_TO` edges (SMM.6–11, 23);
     * `RUNS_ON` placements and per-unit `cpu_allocation` (`cores_requested`, `pinned_cores`, `dedicated`, `high_performance`), unit `os_settings`, and `runtime_config` (`memory_max_mb`, JVM/process flags) (SMM.18, 24; DVE.40–46);
     * `Broker` instances (`type`, `version`, `max_connections`, `RUNS_ON`, `ROUTES`) and `CommunicationService` instances (`technology`, `version`, `RUNS_ON`, `USES_SERVICE`, and external-to-middleware `TRANSFERS` `{direction, source, destination, message_or_topic}`) (SMM.16–17, 19; DVE.39).
  2. **`SourceCodeParser`:** parses `<unit_name>.xml` (`publishes_to`, `subscribes_to`, `sends`, `receives`, direct unit/library `uses`, SMM.20–22) and Java/C++ import statements.
  3. **`TypeSupportParser`:** parses DDS/middleware QoS & IDL/XML type definitions to extract **Durability, Reliability, Lifespan (`qos_lifespan_ms`), Transport Priority**, Deadline and History Depth (DVE.32–35), plus a canonical structural **`declared_type_hash`** and `declared_size` per `(unit, topic)` endpoint so `DVE.38` detects same-named topics with differing content definitions across units!
  4. **`MessageFileParser`:** parses message/topic payload definitions (`.idl`, `.xsd`, `.xml`, `.json`) to extract `message_id`, `size_bytes`, `frequency`, `fields_hash`, and **`field_schema`** (`[{name, type, min, max, unit}]`) required by `SCG.4` synthetic data generation.
* **Bounded opt-in build (`GmakeBuildRunner`):** off by default (`run_regenerate_code = false`). When enabled, runs in a new session (`start_new_session=True`), scrubbed environment (`PATH`, `HOME`, `LANG` only—never `DSM_*`), `300 s` timeout (`10 s` on `gmake --version`), `resource.setrlimit` caps (`RLIMIT_CPU`, `RLIMIT_AS`, `RLIMIT_FSIZE`), and logs exit code plus redacted `stderr` tail into `common_operation_log`.

### Consequences

* Good, because all four external interfaces (`DP-17…20`), automatic/manual topology (`DP-09`), and mandatory files (`DP-10`) are concretely specified with offline-ready stdlib/`PyMySQL`/`PyYAML` adapters.
* Good, because emitted field names, units (`capacity_mbps`), `qos_lifespan_ms`, per-endpoint `declared_type_hash`, `CommunicationService` flows, and `field_schema` feed ADR-0010, ADR-0013 and ADR-0016 with zero translation gaps.
* Bad, because `system_repo` and `ansible_repo` maintainers must populate the documented YAML/XML descriptors (missing attributes degrade gracefully to `placeholders` rather than silent fake numbers).
* Bad, because opt-in `gmake` still runs build recipes on the host under `rlimit` bounds rather than a container sandbox.

### Confirmation

* Unit and adapter contract tests (`mdg/tests/contract/`, ADR-0021) against `dev/` MySQL, Gitea and mock Package REST verify: TLS CA enforcement (zero `sslVerify=false`), trailing-slash URLs, `:` in usernames, boundary-safe redaction, CMDB deficiency/format/access categories (`MDG.16`), `manual` vs `git_ansible` topology modes (`MDG.6–7`), `Library` + `Application` cloning and `AcquiredFile` repo-relative paths (`MDG.17–19`), `SourceRepoIntegrityError` (`MDG.20`), and `GmakeBuildRunner` env scrubbing + `rlimit`s.

## Pros and Cons of the Options

### PyMySQL read-only adapter (chosen)

* Good, because it is pure Python, already in `mdg/wheelhouse/`, and keeps SQL explicit.
* Bad, because non-MySQL CMDBs require adding a new `IConfigManagementRepository` adapter.

### SQLAlchemy Core (earlier SDP §5)

* Good, because dialects swap more easily.
* Bad, because vendoring SQLAlchemy and greenlet wheels adds weight for an unplanned database change.

### `git` CLI shallow clone over TLS-verified HTTPS (chosen)

* Good, because it works against any Git server with exact tag resolution and shallow bandwidth.
* Bad, because it requires `git ≥ 2.14` on the target host and subprocess credential-helper care.

### Git server REST archive or Python Git library

* Good, because no `git` subprocess is spawned.
* Bad, because archive URLs are vendor-specific (Gitea vs GitLab vs Bitbucket) and `pygit2` requires native `libgit2` wheels on CentOS 7.

### HTTPS REST `IPackageRepository` via stdlib (chosen)

* Good, because it verifies unit versions and SHA-256 digests with zero third-party wheels.
* Bad, because repository path templates must match the institution's artifact manager.

### Shared filesystem mount for packages

* Good, because file reads are local.
* Bad, because network mounts break host isolation and carry no standard metadata/checksum API.

### `NETWORK_TOPOLOGY` supporting `git_ansible` YAML and `manual` SQLite store (chosen)

* Good, because it satisfies both MDG.6 (versioned deployer-maintained Ansible vars) and MDG.7 (standalone or override manual entry) behind one validation model.
* Bad, because Ansible inventories using dynamic plugins or unexpanded Jinja expressions yield `placeholders` that require manual override.

### Dedicated CMDB tables or manual entry only

* Good, because no YAML parser is needed.
* Bad, because the institutional CMDB has no NIC/switch tables, and manual-only violates MDG.6.

### Static parsing with resource-bounded opt-in `gmake` (chosen)

* Good, because default runs are fast, deterministic and execute zero untrusted code.
* Bad, because units relying on build-generated IDL/XML must either check generated descriptors into Git or enable the host `gmake` option.

## More Information

* Code: `mdg/src/mdg/adapters/config_management/mysql_config_management_repository.py`, `mdg/src/mdg/adapters/source_code/`, `mdg/src/mdg/adapters/source_data/`, `mdg/src/mdg/services/produce_model_setup_data.py`, `dve/src/dve/services/data_source_service.py`
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0009, ADR-0010, ADR-0013, ADR-0016, ADR-0019, ADR-0021
* Revisit if the institutional CMDB migrates off MySQL, or if container/namespace sandboxing (`bwrap`) becomes available on the target host for `gmake`.
