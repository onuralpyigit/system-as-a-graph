# ADR-0004: Deployment, repository layout, configuration and environments

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Ratify |
| Traces | QA-03, QA-10, QA-11; FDM.1–2; FDM-INF.1; SMM.30; DVE.27; BACKLOG T3; SDP §4–5 |
| Resolves | — |
| Decide by | Wave A1 (2026-12-04); §5 retention and backup by Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

The SRS decomposes the CSCI into six CSCs. SDP §4 originally described a repository with `msd/ scg/ frd/ adp/ csm/ vae/` and SDP §5 a Docker Compose deployment. BACKLOG finding T3 noted that no document owned the CSC → directory mapping.

Commits `1157784` and `f820ccb` established the offline deployment model:

* Every runtime Docker, Redis and Celery dependency was removed from the product.
* Offline **wheelhouses** were added per distribution (`mdg/wheelhouse/`, `dve/wheelhouse/`), holding pinned wheels for CPython 3.9 on x86_64 (`glibc ≥ 2.17`, CentOS 7+), installed via `pip install --no-index --find-links=…`.
* `dsm` (`dve/src/dve/__main__.py`) is the single entry-point command, starting the API process whose spawned children execute background operations (ADR-0006).
* Docker remains solely in `dev/compose.yaml` (MySQL 9.7.2 and Gitea 1.27.3 mocks) on developer workstations.
* **As-built gaps identified during code audit:**
  * `.ini` files (`mdg/src/mdg/mdg.ini`, `dve/src/dve/dve.ini`) are packaged inside `site-packages/`, cached with `@lru_cache(maxsize=1)` (`dve/src/dve/config.py:75`, `mdg/src/mdg/__init__.py:86`), and cannot be overridden by host files.
  * Relative `workspace` in `mdg.ini` resolves inside `site-packages/` (`WorkspaceConfig.root()`).
  * Both `setup.py` files still declare `python_requires=">=3.8"` even though vendored wheels (`cffi`, `markupsafe`, `wtforms`, `blinker`, `importlib_metadata`, `zipp`) require Python `>=3.9`.
  * Both `mdg/wheelhouse/README.md:19` and `dve/wheelhouse/README.md:22` pass `--platform manylinux_2_28_x86_64` (allowing `glibc 2.28` wheels that fail on CentOS 7's `glibc 2.17`), and `mdg/wheelhouse/README.md` fails to download `PyYAML==6.0` because `PyYAML 6.0` only published `manylinux1`/`manylinux2010` tags.
  * `dve/src/dve/__main__.py:18-27` traps `SIGTERM` and calls `sys.exit(0)` immediately without draining or recording running child operations.
  * Local checkouts may still contain untracked SDP §4 leftover directories (`msd/`, `scg/`, `frd/`, `adp/`, `csm/`, `vae/`, `web/`) with cached `.pyc` or `node_modules/` artifacts.

Every other ADR depends on what the target host can run. This ADR fixes the runtime, host prerequisites, layout and configuration contract.

## Decision Drivers

* The target host has no internet access and no container runtime.
* The host baseline is CentOS 7 or later (`x86_64`, `glibc ≥ 2.17`), where stock OS packages are old (e.g. system SQLite 3.7.17, stock `git` 1.8.3.1, system OpenSSL 1.0.2k).
* Upgrading the product must never overwrite host configuration, secrets, models or field records.
* CSCs exchange large artifacts sequentially (SDD §2.2) and need a clear 1-to-1 CSC → package layout for SRS traceability.
* Developers need reproducible local mocks without access to institutional production systems.

## Considered Options

* Deployment: Offline install of pinned CPython 3.9 wheels into a host virtual environment, one `dsm` process tree (as built)
* Deployment: Container image with `api` and `worker` containers
* Deployment: Multi-container Docker Compose stack (earlier SDP §5)
* Deployment: Relocatable bundle shipping a custom-compiled Python interpreter
* Decomposition: Modular monolith with one Python distribution per CSC plus `common/` (as built, extended)
* Decomposition: Separate network service per CSC

## Decision Outcome

Chosen options: **offline installation of pinned CPython 3.9 wheels into a host virtual environment running as one `dsm` process tree (as built)** and **a modular monolith with one Python distribution per CSC plus `common/`**. The CSCs are sequential pipeline stages maintained by one team, and the target host has no container runtime.

### 1. Repository layout

```text
common/                              shared kernel: errors, db connector, artifact/schema DTOs; wheelhouse/
mdg/  scg/  fdm/  adm/  smm/  dve/   one Python distribution per CSC: setup.py, src/<csc>/, tests/, wheelhouse/
dev/                                 developer-only mock stack (compose.yaml) and offline test-runner wheelhouse
deploy/                              offline install.sh, host .ini templates, systemd unit, backup/restore scripts
docs/
```

* The Operations Panel stays inside `dve/src/dve/{templates,static}` (ADR-0015); there is no `web/` Node.js build.
* **Dependency direction (acyclic):** `dve` → `smm`, `adm`, `mdg`, `scg`, `fdm`; `adm` → `scg`, `fdm`; `smm` → `mdg`, `adm`; every CSC package depends on `common`. Note `scg` does not import `mdg` or `smm` (DVE passes a `common` `ModelSchemaSnapshot` DTO into `scg`, ADR-0003, ADR-0013).
* **Process model:** `dsm` starts the single `waitress` WSGI API process (ADR-0005). Background operations run as spawned child processes of `dsm` (ADR-0006), supervised as one process group under `systemd`.
* **To build:**
  * Create `common/` first in R3 (holding `ErrorRecord`, `ArtifactRef`, `common.db` SQLite connector, and shared wheels: `cryptography`, `cffi`, `pycparser`, `jsonschema==4.17.3`, `attrs`, `pyrsistent`, `pysqlite3-binary`), then `smm/` in R3, `scg/` and `adm/` in R4, and `fdm/` in R5.
  * Clean up untracked legacy directories (`msd/ frd/ adp/ csm/ vae/ web/` and legacy `scg/` artifacts) in `.gitignore` / developer checkouts.

### 2. Runtime, host prerequisites and packaging

* **Target OS & CPU:** Linux `x86_64`, `glibc ≥ 2.17` (CentOS 7 / RHEL 7 or later).
* **Host prerequisite floors (verified by `deploy/install.sh`):**
  * **CPython 3.9 (`>=3.9,<3.10`)** compiled against **OpenSSL ≥ 1.1.1** so Python's `ssl` module supports TLS 1.2/1.3 for HTTPS Git/package repositories and LDAPS/StartTLS (ADR-0008, ADR-0019). Every `setup.py` sets `python_requires=">=3.9,<3.10"`.
  * **`git ≥ 2.14`** on `PATH` (for example via `rh-git227` / vendor RPM on CentOS 7), because stock CentOS 7 `git 1.8.3.1` lacks `GIT_TERMINAL_PROMPT=0` (Git 2.3), `ls-remote --refs` (Git 2.8/2.14), and `-c credential.helper=` reset (Git 2.9) used by `GitSourceCodeRepository` (ADR-0008).
  * **`gmake` (GNU Make ≥ 3.82)** only when operators enable `[build] run_regenerate_code = true` (ADR-0008).
  * **Native graph server prerequisite** selected by the ADR-0011 R3 spike (default: Neo4j Community 5 tarball + Eclipse Temurin Java 17/21 tarball on `localhost`).
* **Wheelhouse compatibility rules:**
  * Every binary wheel must carry a `cp39` or `abi3` tag compatible with `glibc ≤ 2.17`: `manylinux1_x86_64`, `manylinux2010_x86_64`, or `manylinux2014_x86_64` (`manylinux_2_17_x86_64`), or `py3-none-any`.
  * **`--platform manylinux_2_28_x86_64` is forbidden** in wheelhouse `pip download` commands and removed from `mdg/wheelhouse/README.md` and `dve/wheelhouse/README.md`; `PyYAML` is either bumped to `6.0.2` (`manylinux2014_x86_64`) or downloaded with `--platform manylinux2010_x86_64` included alongside `manylinux2014_x86_64`.
  * Release artifacts are versioned tarballs containing the source distributions, per-package `wheelhouse/` directories, and `deploy/`. Installation runs `pip install --no-index --find-links=…` in dependency order (`common` → leaf CSCs → `dve`).

### 3. Install layout and configuration

`deploy/install.sh` provisions:

| Path | Contents | Owner, mode |
|---|---|---|
| `/opt/dsm/venv/` | Virtual environment with `common` and all CSC distributions | `root:root`, `0755` (read-only to service user) |
| `/etc/dsm/mdg.ini`, `/etc/dsm/dve.ini` | Host configuration overrides (extended per CSC only when a CSC adds host-tunable settings; otherwise centralized in `dve.ini`) | `root:dsm`, `0640` |
| `/etc/dsm/secret_key`, `/etc/dsm/data_key` | Session signing key and AES-256-GCM keyring file (ADR-0019) | `dsm:dsm`, `0600` |
| `/var/lib/dsm/workspace/` | Model Data runs/clones (ADR-0009), SCG datasets (ADR-0013), AED datasets & `overlay.db` files (ADR-0012) | `dsm:dsm`, `0700` |
| `/var/lib/dsm/field_records/` | Raw and normalized System Field Records (ADR-0014) | `dsm:dsm`, `0700` |
| `/var/lib/dsm/data/` | Central SQLite database `dsm.db` and WAL files (ADR-0007) | `dsm:dsm`, `0700` |
| `/var/log/dsm/` | Structured JSON application logs (ADR-0020) | `dsm:dsm`, `0750` |

* **Override mechanics:** packaged `.ini` files hold safe development defaults. Config loaders read packaged defaults first, then overlay `/etc/dsm/<pkg>.ini` (or `$DSM_CONFIG/<pkg>.ini`), exposing a `reload_config()` / explicit `Config` injection rather than an un-clearable global `@lru_cache`. Effective configuration is logged once at start-up with secret paths/values redacted.
* **Relative paths** in host `.ini` files resolve against `/var/lib/dsm`, never inside `site-packages/`.
* **Production guard (`[runtime] mode = development | production`):** in `production` mode, start-up aborts if any of the following hold:
  * missing, world/group-readable, or default development secret keys (ADR-0019);
  * `[directory] backend = mock` (ADR-0019);
  * Werkzeug's development server instead of `waitress` (ADR-0005);
  * `workspace`, `field_records`, or `data` resolving inside `/opt/dsm/venv/`;
  * `sqlite3` / `pysqlite3` version `< 3.24` (ADR-0007) or `git` version `< 2.14`.
* **Graceful shutdown:** `deploy/dsm.service` runs `dsm` as unprivileged user `dsm` (`Restart=on-failure`). On `SIGTERM`, `dsm` stops accepting new tasks, marks in-flight operations `cancelled` with `stage = shutdown` in `dsm.db`, terminates child process groups, and only then exits (replacing the immediate `sys.exit(0)` in `dve/__main__.py`).

### 4. Environments

| Environment | Where | External systems |
|---|---|---|
| Development | Developer workstation | `dev/compose.yaml`: MySQL 9.7.2, Gitea 1.27.3, plus OpenLDAP (ADR-0019). Docker is used here only. |
| Test | Offline CentOS-7-compatible VM (`glibc 2.17`, CPython 3.9, `dev/wheelhouse-test/`) | `dev/` mocks on a companion host or institutional staging instances |
| Production | Air-gapped target host | Institutional CMDB, Git/package repositories, field-record exports, and LDAP |

### 5. Retention, backup and recovery (open, decide by Wave C)

* **Question:** how long are baseline/working models, Model Data files, synthetic datasets, field records, AED overlays, findings and reports retained, and how are all stateful stores backed up and restored consistently (FDM.1–2; QA-03, QA-10)?
* **Coordinated scope required:** a valid backup and restore procedure must cover **four** data locations atomically (or in a defined quiesced order) so cross-store references never dangle:
  1. `/var/lib/dsm/data/dsm.db` (via SQLite online backup API, ADR-0007);
  2. `/var/lib/dsm/workspace/` (`Model Data`, `SCG`, `AED` + `overlay.db`);
  3. `/var/lib/dsm/field_records/` (`raw/` and `normalized/`);
  4. the native graph server's data directory / dump (ADR-0011);
  plus separate custodial backup of `/etc/dsm/data_key` (ADR-0019), without which encrypted data-source credentials in `dsm.db` cannot be decrypted.
* **Options to weigh in Wave C:** per-artifact retention windows and working-model TTLs (feeding ADR-0020's disk formula), online vs. maintenance-window graph snapshots, and automated restore verification drills.

### Consequences

* Good, because installation requires only the host OS prerequisites and the release tarball—no internet and no container daemon.
* Good, because configuration, keys and all mutable stores live under `/etc/dsm` and `/var/lib/dsm`, making `/opt/dsm/venv` stateless and replaceable on upgrade.
* Bad, because CPython 3.9 reached upstream EOL in October 2025; OS-vendor security patches apply, and migrating to a newer Python minor version requires rebuilding every wheelhouse under a future ADR.
* Bad, because every third-party wheel must be vetted for `manylinux2014_x86_64` (`glibc ≤ 2.17`) compatibility.

### Confirmation

* `deploy/install.sh` completes on a network-disconnected CentOS-7-compatible VM, checks `git`, OpenSSL, SQLite and disk prerequisites, and passes `systemctl start dsm`.
* A CI wheel-audit check verifies that every `.whl` in `*/wheelhouse/` is `py3-none-any` or `manylinux{1,2010,2014}_x86_64` / `manylinux_2_17_x86_64` (rejecting `manylinux_2_28`), and that each wheelhouse `README.md` command reproduces the exact committed wheel set.
* `import-linter` verifies the acyclic CSC dependency graph of §1.
* Start-up tests verify every `production`-mode refusal rule in §3.

## Pros and Cons of the Options

### Offline wheelhouse install into one `dsm` process tree (chosen)

* Good, because it works on air-gapped CentOS 7+ hosts with zero container runtime and matches commit `1157784`.
* Bad, because wheelhouse `manylinux` tags and host CLI floors (`git`, OpenSSL) must be curated explicitly.

### Container image or Docker Compose stack (earlier SDP §5)

* Good, because OS userland (`git`, SQLite, OpenSSL, Python) is bundled predictably inside the image.
* Bad, because the target production host forbids container runtimes.

### Self-contained bundle with a custom Python interpreter

* Good, because it decouples SaaG from the host's Python 3.9 build.
* Bad, because shipping and security-patching a custom CPython + OpenSSL build offline shifts OS maintenance onto the SaaG team.

### Modular monolith, one distribution per CSC plus `common/` (chosen)

* Good, because SRS 1-to-1 CSC boundaries remain explicit and testable while deployment stays a single virtual environment and process tree.
* Bad, because package boundaries must be policed via `import-linter` rather than process isolation.

### Separate network service per CSC

* Good, because process boundaries enforce isolation automatically.
* Bad, because six services multiply systemd units, ports, auth and failure modes on a single host for no throughput gain.

## More Information

* Code: `mdg/setup.py`, `dve/setup.py`, `mdg/wheelhouse/README.md`, `dve/wheelhouse/README.md`, `mdg/src/mdg/config.py`, `dve/src/dve/config.py`, `dve/src/dve/__main__.py`, `dev/compose.yaml`
* Related: ADR-0002, ADR-0003, ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0010, ADR-0011, ADR-0014, ADR-0019, ADR-0020, ADR-0021
* Revisit if the target host upgrades its Python baseline to 3.11/3.12, if a container runtime becomes permitted in production, or if multi-host horizontal scaling is required.
