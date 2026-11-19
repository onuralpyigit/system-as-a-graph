# ADR-0010: MDG acquisition: data sources, network topology and source files

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, configuration management owners, system/network engineering, ansible repository owners |
| Kind | Ratify |
| Traces | MDG.2–13, 17–21; SMM.12–15, 18, 20–22, 24; DVE.7, 32–35, 40–46; QA-01, QA-05, QA-06 |
| Resolves | DP-09 (MDG.6 topology source and method); DP-10 (MDG.19 mandatory file list); DP-17, DP-18, DP-19, DP-20 (protocols of EXT-IF-01 CMDB, EXT-IF-02 source repository, EXT-IF-03 package repository, EXT-IF-04 topology source) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — (absorbs the former ADR-0010) |

## Context and Problem Statement

MDG reads the configuration management database, the source code repository, the package repository and the network topology source (MDG.2–5). SDD §2.3 leaves each one's protocol open. The SRS also defers the automatic topology source (MDG.6) and the mandatory file list (MDG.19).

As built (`1157784`):

* **CMDB:** `MysqlConfigManagementRepository` uses PyMySQL 1.0.3 with parameterised, read-only `SELECT`s. It reads the tables `platform_pkg_version`, `platform_current_atm_version` and `csu_csms_relation`.
  * Each query opens a new connection (`connect_timeout=5`).
  * `pymysql.MySQLError` maps to `ConfigManagementAccessError`.
  * The address format is `<host>:<port>/<database>`.
* **Source repository:** `GitSourceCodeRepository` runs the `git` CLI.
  * Units are shallow-cloned with `--depth 1 --branch <version>`; the tag equals the version. Versions are listed with `ls-remote --tags --refs`.
  * Credentials stay out of the URL and the command line. An inline helper reads `DSM_GIT_USER` and `DSM_GIT_PASSWORD` from the subprocess environment. `GIT_TERMINAL_PROMPT=0` is set, and errors are redacted.
  * `-c http.sslVerify=false` is always set (`git_source_code_repository.py:126`).
  * `.git` is deleted after cloning, so no commit hash is kept.
* **Package repository:** not built. "Packages" are CMDB `pkg_name`/`pkg_version` rows, fetched from Git by tag.
* **Topology:**
  * The **ansible repository** (`mdg.ini` `[workspace] ansible_repo`) is a CMDB unit cloned by tag. `IAnsibleRepoParser` turns it into `Node`, `Network` and `ConnectsTo` (with device, dev_raw and bandwidth in Gb/s).
  * The **system repository** gives `runs_on`, roles and criticality through `ISystemRepoParser`.
  * Both parsers are mocks, and the dev seed repositories hold only a README.
  * A missing or failed clone of either repository fails the run.
* **Mandatory files:** `MandatoryFiles` requires, per software unit, a `Makefile` whose non-comment text contains an include pattern (`include/Makefile_java.mk`), plus `<unit_name>.xml`.
  * The rule does not apply to the system and ansible repositories.
  * Only units that an application places on a node are cloned (`produce_model_setup_data.py:172-177`), so library units such as `common_lib` are not.
* **Parsing:** `SourceCodeParser` is the only real parser.
  * It reads topics from the manifest (`<topic name=".." role="pub|sub|pubsub"/>`, skipping configured dummy names).
  * It reads library `uses` from Java imports under a configured prefix and suffix.
  * `TypeSupportParser` (QoS) and `MessageFileParser` (messages) are mocks.
* **Optional build:** `[build] run_regenerate_code`, off by default. `GmakeBuildRunner` runs `gmake regenerate_code` in the Makefile directory with a 300 s timeout. A failing build is logged; a missing `gmake` fails the run.
* **Configuration:** `DataSourceConfig` (source type, name, access method, connection address, user information) lives per session in memory (`DataSourceService`) and cannot be saved.

## Decision Drivers

* The CMDB is MySQL in every environment known so far. Each extra library is one more wheel to vendor offline (ADR-0004).
* Acquisition must be reproducible (MDG.17–18) and versioned with the system version (MDG.9), including topology.
* The protocols must work with internal certificate authorities. MDG.8 requires savable configurations.
* Running repository code on the SaaG host is a risk, and the host has no container runtime to sandbox it.
* Manual topology entry (MDG.7) and automatic acquisition must be validated the same way (MDG.21). The resource rules need numeric capacity (DVE.40–46), but the as-built `hw` field is free text such as `x86-64/8c`.

## Considered Options

* CMDB: PyMySQL in one adapter (as built) / SQLAlchemy Core (SDP §5)
* Source repository: `git` CLI shallow clone by tag (as built) / Git server REST archive / a Python Git library
* Package repository: HTTPS REST / filesystem mount
* Topology: the ansible repository over Git (as built, parser mocked) / a `topology.yaml` in the system repository / a CMDB query / manual entry only
* Extraction: static parsing with an opt-in host build (as built) / always build / build in a container

## Decision Outcome

Chosen options: **PyMySQL**, **the `git` CLI over HTTPS**, **HTTPS REST through the standard library for packages**, **the ansible repository for topology**, and **static parsing with a constrained opt-in host build**, all as built or extending what is built.

### 1. Data sources and connection configuration

* **EXT-IF-01, CMDB:** the MySQL protocol through PyMySQL, read-only. Every table and column name lives in one place in the adapter, so a different schema changes only that mapping. A non-MySQL CMDB would need a new adapter behind `IConfigManagementRepository`.
* **EXT-IF-02, source repository:** Git over HTTPS with the `git` CLI, shallow clone by tag, and the environment-based credential helper.
* **EXT-IF-03, package repository:** HTTPS REST behind a new `IPackageRepository` port. It returns metadata (name, version, checksum) and downloads by version, using `urllib.request` with a token. The product is confirmed with its owners before R5, with a fake until then.
* **Configuration (MDG.8):** `DataSourceConfig` stays the domain type, and `access_method` selects the adapter (ADR-0003).
  * Configurations are saved per user in SQLite (ADR-0008), with credentials encrypted (ADR-0030).
  * `dve.ini` gives only defaults.
  * Each source is verified with one cheap call when it is connected (DVE.7).
* **To build:**
  * TLS verification on, with a per-source `ca_bundle` (`-c http.sslCAInfo=<path>`); remove `sslVerify=false`.
  * Record `git rev-parse HEAD` before deleting `.git`, on every `AcquiredFile` and in the Model Data provenance (ADR-0013, ADR-0008).
  * One CMDB connection per run.
  * The package adapter, and saved configurations with a write-only secret field.

### 2. Network topology (MDG.5–7, EXT-IF-04)

* **Source:** the ansible repository, cloned per system version over Git, through the EXT-IF-02 adapter and credentials. It is versioned with the system and maintained by its deployers, so no new interface or file is needed.
* **Format:** the standard Ansible YAML layout, parsed with PyYAML, which is pinned but unused today. The parser reads:
  * the inventory file (`inventory.yml` or `hosts.yml`, path configurable), whose groups give `Node.group`;
  * `host_vars/<host>.yml` and `group_vars/<group>.yml`.

  It reads nothing else and evaluates no Jinja. A templated value becomes a placeholder (ADR-0013).
* **SaaG keys** in host or group variables. The names must be confirmed with the ansible repository owners; this point is open.

  | Key | Model field | Used by |
  |---|---|---|
  | `saag_hw`, `saag_os`, `saag_mw`, `saag_gpu`, `saag_display` | `Node.hw`, `os`, `mw`, `gpu`, `display` (as built) | SMM.14 |
  | `saag_kind` (`operator_console` \| `processor`) | `Node.kind` (new) | SMM.14 |
  | `saag_cores`, `saag_ram_gb` | `Node.cores`, `Node.ram_gb` (new, numeric) | DVE.41–46 |
  | `saag_interfaces`: list of `{device, dev_raw, network, bandwidth_gbps}` | `ConnectsTo`, `Network` (as built) | SMM.15, 18; DVE.40 |

* **Validation:**
  * A missing file gives `missing_data` (MDG.19), and a malformed file gives a `format` error record (ADR-0013).
  * A host without capacity keys is kept and listed as a placeholder, so the rules report it instead of guessing.
  * Nodes named only by the system repository are kept as placeholders.
* **Manual entry (MDG.7):** the UI edits the same fields and saves them as an override attached to the run in SQLite. The override is recorded as manual (ADR-0008) and never written back to the repository.
* **To build:**
  * a real `AnsibleRepoParser`, with seed files (valid, missing and invalid hosts) in `dev/gitea/seed/ansible_repo_1.0.0/`;
  * numeric `cores`, `ram_gb` and `kind` on `Node`, carried into Model Data (ADR-0013, ADR-0014);
  * the override API and screen.

### 3. Mandatory files and extraction (MDG.17–21)

* **Mandatory set (DP-10):** per software unit. A missing file marks the unit `missing_data` with an error record (ADR-0013).

  | File | Rule |
  |---|---|
  | `Makefile` | Any `Makefile` under the unit whose non-comment content includes one of `[mandatory_files] makefile_include_patterns` |
  | `<unit_name>.xml` | The topic manifest declaring published and consumed topics |

  * The system and ansible repositories have no mandatory files; topology gaps are reported by §2.
  * Installation scripts and configuration files are acquired when present and recorded per MDG.18, but are not mandatory.
  * Changing the set is a change to this ADR.
* **Extraction:** static parsing, with settings in `mdg.ini` `[source_parser]`. Parsers are ports with fakes (ADR-0003).
* **Opt-in build:** off by default. When an operator enables it, `gmake regenerate_code` runs on the host:
  * as the unprivileged service user;
  * inside the run's own clone;
  * with an environment reduced to `PATH`, `HOME` and `LANG`, so no `DSM_GIT_*` or other secret is inherited;
  * with the 300 s timeout and `resource.setrlimit` limits on CPU time and address space, set in `preexec_fn`;
  * with the exit code and stderr tail written to the run log.
* **Per-file record (MDG.18):** name, path, package/version and update time, plus the commit hash. The update time becomes the commit time once the hash is recorded.
* **To build:**
  * Replace `TypeSupportParser` with a parser of the units' topic type definitions, giving Durability, Reliability, Lifespan and Transport Priority, before the R3 QoS rules (DVE.32–35). Until then its values are placeholders.
  * Replace `MessageFileParser` (SMM.13, 20–21) and `SystemRepoParser`.
  * Clone every inventory unit, including libraries, which are exempt from the manifest rule (MDG.17).
  * Parse CPU allocation, OS settings and runtime configuration into unit attributes (SMM.24, DVE.41–46). The source files are agreed with the owners and recorded here.
  * Add the build constraints above to `GmakeBuildRunner`.

### Consequences

* Good, because every external source has a small, offline-friendly adapter, and acquisition is reproducible (tag → commit hash) and secure by default once TLS is on.
* Good, because topology comes from a repository that is already acquired, and one set of fields serves the automatic path, the manual path and validation.
* Good, because the MDG.19 file list is settled with a rule already implemented and tested.
* Bad, because a non-MySQL CMDB would need a second adapter, and the package protocol is provisional.
* Bad, because the ansible owners must add the `saag_*` keys, and Ansible layouts vary.
* Bad, because the opt-in build still runs repository code on the host, bounded but not sandboxed. A unit whose topics need generated code is parsed incompletely while it is off.

### Confirmation

* Existing tests in `mdg/tests/adapters/` cover:
  * address parsing and error mapping;
  * tag clone arguments and version ordering;
  * no password on a `git` command line or in error text;
  * mandatory files, including the comment-only include case.
* Adapter contract tests (ADR-0041) run the same cases against the `dev/` MySQL and Gitea stack.
* New tests:
  * `git` arguments never contain `sslVerify=false` outside a test override;
  * the topology parser handles the valid, missing and invalid seeds and never calls Ansible or Jinja;
  * `GmakeBuildRunner` passes a reduced environment and sets resource limits.

## Pros and Cons of the Options

* PyMySQL (as built): Good, because it is pure Python and already in the wheelhouse. Bad, because it is bound to MySQL. SQLAlchemy Core is dialect-independent but a large dependency for an engine change that is not planned.
* `git` CLI (as built): Good, because it works with any server and tags are exact. Bad, because it needs subprocess and credential plumbing. A REST archive is server-specific, and Python Git libraries vary in shallow-clone and auth support.
* Package REST: Good, because it is the standard interface of repository managers. A filesystem mount has no checksums or metadata.
* Ansible repository: Good, because it is versioned, already cloned, and maintained by the deployers. Bad, because the owners must maintain the SaaG keys.
  * A `topology.yaml` would duplicate what the ansible repository holds.
  * The CMDB holds no network data.
  * Manual entry alone fails MDG.6.
* Static parsing with an opt-in host build (as built): Good, because it is deterministic and fast. Bad, because the opt-in runs on the host.
  * Always building needs the full toolchain and runs repository code every time.
  * A container build needs a runtime the host lacks.

## More Information

* Code:
  * `mdg/src/mdg/adapters/config_management/mysql_config_management_repository.py`
  * `mdg/src/mdg/adapters/source_code/` (`git_source_code_repository.py`, `mandatory_files.py`, `gmake_build_runner.py`)
  * `mdg/src/mdg/adapters/source_data/`
  * `mdg/src/mdg/domain/source_data.py`
  * `mdg/src/mdg/services/produce_model_setup_data.py`
  * `mdg/src/mdg/mdg.ini`
  * `dve/src/dve/services/data_source_service.py`
* Related: ADR-0003, ADR-0004, ADR-0008, ADR-0013, ADR-0014, ADR-0030, ADR-0041
* Revisit if the production CMDB is not MySQL-compatible.
