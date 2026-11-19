# ADR-0004: Deployment, repository layout, configuration and environments

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Ratify |
| Traces | QA-03, QA-10, QA-11; FDM.1–2; FDM-INF.1; SMM.30; DVE.27; BACKLOG T3; SDP §4–5 |
| Resolves | — |
| Decide by | Wave A (2026-11-27); §5 retention and backup by Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

The SRS decomposes the CSCI into six CSCs. SDP §4 described a repository with `msd/ scg/ frd/ adp/ csm/ vae/` and SDP §5 a Docker Compose deployment. BACKLOG finding T3 noted that no document owns the CSC → directory mapping.

Commit `1157784` settled the deployment model:

* It removed every Docker dependency from the product: the `docker` package, the Redis container started by `dsm`, and the Celery worker.
* It added offline **wheelhouses** per distribution (`mdg/wheelhouse/`, `dve/wheelhouse/`). Each holds pinned wheels for CPython 3.9 on x86_64 with glibc ≥ 2.17 (CentOS 7 or later), installed with `pip install --no-index --find-links=…`, `mdg` first.
* `dsm` (`dve/src/dve/__main__.py`) is the only command. It starts the API, whose child processes run the operations (ADR-0006).
* Configuration comes from `.ini` files packaged inside the distributions: `mdg/src/mdg/mdg.ini` and `dve/src/dve/dve.ini`. They are loaded with `configparser` and cannot be overridden.
* The relative `workspace` path in `mdg.ini` resolves inside the installed package (`WorkspaceConfig.root()`), so produced files land under `site-packages/`.
* Both `setup.py` files declare `python_requires=">=3.8"`, but the wheelhouses hold cp39 wheels only.
* Docker remains only in `dev/compose.yaml` (MySQL 9.7.2 and Gitea 1.27.3 mocks) on developer machines.

Every other ADR depends on what the target host can run. This one states it.

## Decision Drivers

* The target host has no internet access and no container runtime.
* The host's baseline is CentOS 7 or later, so glibc 2.17 and old system libraries apply (for example SQLite 3.7.17, ADR-0007).
* Upgrading the product must never overwrite configuration, secrets or data.
* CSCs exchange large artifacts and run in strict sequence (SDD §2.2). SRS traceability needs a visible one-to-one CSC → code mapping.
* Developers need realistic external systems without access to production ones.

## Considered Options

* Deployment: offline install of pinned CPython 3.9 wheels into a virtual environment, one process tree (as built) / container image with `api` and `worker` / Docker Compose (SDP §5) / a self-contained bundle with its own interpreter
* Decomposition: modular monolith, one distribution per CSC (as built) / service per CSC / the SDP §4 layout

## Decision Outcome

Chosen options: **a modular monolith installed offline from pinned CPython 3.9 wheels and run as one process tree (as built)**. The CSCs are sequential stages owned by one team, and the target host has no container runtime. Separate services or images would add network contracts and failure modes without any scaling or ownership need.

### 1. Repository layout

```
mdg/  scg/  fdm/  adm/  smm/  dve/   one Python distribution per CSC: setup.py, src/<csc>/, tests/, wheelhouse/
common/                              shared kernel: error records, provenance types (ADR-0009, ADR-0007); no business logic
dev/                                 development-only mock data sources (Docker Compose, developer machines only)
deploy/                              install scripts, host configuration templates, service unit
docs/
```

* The Operations Panel stays inside `dve/src/dve/{templates,static}` (ADR-0015); there is no `web/` build.
* **Dependency direction:** `dve` → `smm`, `adm`, `mdg`, `scg`, `fdm`; `adm` → `scg`, `fdm`; `smm` → `mdg`, `adm`; every package may use `common`. No cycles.
* **Process model:** `dsm` starts the API process. Each background operation runs in a spawned child process of it (ADR-0006). The host's service manager supervises the tree.
* **To build:**
  * Create the `scg/ fdm/ adm/ smm/ common/` skeletons when their release starts.
  * Move `ErrorRecord` and the provenance types into `common/` when a second CSC needs them.
  * Remove the empty, untracked SDP §4 leftovers in local checkouts (`msd/ frd/ adp/ csm/ vae/ web/`).

### 2. Runtime and packaging

* **Runtime:** CPython 3.9, x86_64, glibc ≥ 2.17. `python_requires` becomes `">=3.9,<3.10"` in every `setup.py` until the wheelhouses are rebuilt for a newer interpreter.
* **Dependencies:** any new dependency must exist as a `cp39` or `abi3` wheel for `manylinux2014_x86_64` (or older), or be pure Python. This is why ADR-0010 ports the framework's rules instead of importing `saag`, which needs Python ≥ 3.10.
* **Wheelhouses:** each distribution keeps its `wheelhouse/` with a README giving the exact `pip download` command that regenerates it (as built). Distributions install in dependency order. A release is a tarball of the repository at a tag, including the wheelhouses.

### 3. Install layout and configuration

`deploy/install.sh` creates:

| Path | Contents | Owner, mode |
|---|---|---|
| `/opt/dsm/venv/` | Virtual environment with the distributions | root, read-only for the service user |
| `/etc/dsm/dve.ini`, `/etc/dsm/mdg.ini` | Host configuration overriding the packaged defaults | root, readable by the service user |
| `/etc/dsm/secret_key`, `/etc/dsm/data_key` | Secrets (ADR-0019) | service user, 0600 |
| `/var/lib/dsm/workspace/` | Model Data runs and clones (ADR-0009) | service user, 0700 |
| `/var/lib/dsm/data/` | SQLite database (ADR-0007) | service user, 0700 |
| `/var/log/dsm/` | Log files (ADR-0020) | service user |

* **Graph server:** the one chosen by the ADR-0011 spike is installed beside it by its own script in `deploy/`.
* **Override order:** packaged `.ini` files keep development defaults. A host file overrides them key by key, at `/etc/dsm/<pkg>.ini` or in the directory named by `DSM_CONFIG`. The merged result is logged at start-up without secret values.
* **Relative paths** in host files resolve against `/var/lib/dsm`, never against the package directory.
* **Production flag:** `[runtime] mode = development | production`. In production mode, start-up refuses each of these:
  * development secrets (ADR-0019);
  * the mock directory backend (ADR-0019);
  * the Werkzeug development server (ADR-0005);
  * a workspace or data directory inside the package.
* **Service:** `deploy/dsm.service` runs `dsm` as a dedicated unprivileged user, with `Restart=on-failure`. SIGTERM stops the API and its children; ADR-0006 records the interrupted operations.

### 4. Environments

| Environment | Where | External systems |
|---|---|---|
| Development | Developer machine | `dev/compose.yaml`: MySQL 9.7.2, Gitea 1.27.3, plus OpenLDAP (ADR-0019). Docker is allowed here only. |
| Test | A CentOS-7-compatible host or VM without internet | The `dev/` mocks, or test instances of the real systems |
| Production | The offline target host | The real CMDB, repositories and LDAP |

### 5. Retention, backup and recovery (open, decide by Wave C)

* **Question:** how long are models, records, findings and reports retained, and how are they backed up and restored (FDM.1–2; QA-03, QA-10)?
* **Options to weigh:**
  * retention per store;
  * the SQLite online-backup API (ADR-0007) plus file copies of the workspace and the graph-server data (ADR-0011);
  * restore drills.
* **Constraints already set:**
  * the data-encryption key must be backed up separately, or saved credentials are lost (ADR-0019);
  * working-model expiry bounds graph storage (ADR-0011).

### Consequences

* Good, because installation needs only Python 3.9 and the release tarball, with no container runtime and no internet.
* Good, because configuration, secrets and data live outside the package, so an upgrade replaces only the virtual environment.
* Good, because CSC boundaries stay visible and testable while deployment stays one install.
* Bad, because Python 3.9 is past its upstream end of life (October 2025). Interpreter security fixes must come from the host's vendor. A move to a newer interpreter is a new decision that rebuilds every wheelhouse.
* Bad, because every dependency is vendored and patched by hand, and the old system libraries force fallbacks such as ADR-0007's bundled SQLite.
* Bad, because the CSCI scales only within one host, and all CSCs share one release cadence.

### Confirmation

* An `import-linter` "layers" contract across distributions enforces the dependency direction.
* A CI job does the following on a CentOS-7-compatible environment without network access:
  1. runs `deploy/install.sh` from the release tarball;
  2. starts `dsm` in production mode with test secrets;
  3. calls `GET /api/session`.
* Tests assert that production mode refuses a workspace inside the package directory, and that the wheelhouse README commands regenerate the committed wheel set.

## Pros and Cons of the Options

* Offline wheel install, one process tree (as built): Good, because it is simple, documented and needs nothing beyond Python 3.9. Bad, because it is tied to the host's interpreter and system libraries, and it scales only up.
* Container image or Docker Compose (SDP §5): Good, because images fix the runtime. Bad, because the target host has no container runtime.
* Self-contained bundle with its own interpreter: Good, because it would allow newer dependencies such as `saag`. Bad, because the project would build and patch an interpreter. Revisit if Python 3.9 blocks a needed dependency.
* Service per CSC: Good, because of hard boundaries. Bad, because there are six services and APIs for one team, which the SRS does not require.
* SDP §4 layout: Bad, because its names contradict the canonical IDs (ADR-0002).

## More Information

* Code: `mdg/setup.py`, `dve/setup.py`, `mdg/wheelhouse/README.md`, `dve/wheelhouse/README.md`, `mdg/src/mdg/config.py`, `dve/src/dve/config.py`, `dve/src/dve/__main__.py`, `dev/compose.yaml`
* [BACKLOG finding T3 and Appendix A](../../planning/BACKLOG.md)
* Related: ADR-0002, ADR-0003, ADR-0005, ADR-0006, ADR-0007, ADR-0015, ADR-0010, ADR-0011, ADR-0019, ADR-0020
* Revisit if the target host gains a container runtime, if the CSCI must run on more than one host, or if Python 3.9 blocks a required dependency.
