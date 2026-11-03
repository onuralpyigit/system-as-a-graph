# ADR-0010: External data-source adapters and connection configuration

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, configuration management owners |
| Kind | Reconcile |
| Traces | MDG.2–4, 8, 10–13, 17–20; DVE.7; QA-06 |
| Closes | CDR-17, CDR-18, CDR-19 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

MDG reads three external sources whose protocols are open in the CDR:

- the configuration management database (EXT-IF-01, CDR-17);
- the source code repository (EXT-IF-02, CDR-18);
- the software units package repository (EXT-IF-03, CDR-19).

As built:

* **CMDB:** `MysqlConfigManagementRepository` uses PyMySQL with hand-written SQL against the tables of the dev mock (`platform_pkg_version`, `platform_current_atm_version`, `csu_csms_relation`). SDP §5 instead specifies a "generic SQL adapter (SQLAlchemy)".
* **Source repository:** `GitSourceCodeRepository` runs the `git` CLI over HTTP(S). It makes a shallow clone of `<base_url>/<org>/<unit>.git` at the tag equal to the unit version, and lists versions with `git ls-remote --tags`. Credentials are embedded in the URL, and `http.sslVerify=false` is always set.
* **Package repository:** not implemented. SDP §5 specifies a "REST API (Artifactory/Nexus-style)".
* **Connection configuration:** `DataSourceConfig` (source type, name, access method, connection address, user information) satisfies the MDG.8 fields. The configurations are held only per session in memory and cannot be saved, although MDG.8 says they must be "savable".

## Decision Drivers

* The production CMDB engine and schema are not confirmed. Only the dev mock is known.
* Version selection must be reproducible: the same version must always yield the same files (MDG.17–18).
* The protocols must work in an on-premises network with internal certificate authorities.
* MDG.8 requires user-definable and savable per-source configuration.

## Considered Options

* CMDB: PyMySQL with fixed SQL (as built) / SQLAlchemy Core with the dialect taken from the connection URL (SDP §5)
* Source repository: `git` CLI shallow clone by tag (as built) / Git server REST API (archive download) / a Python Git library
* Package repository: HTTP REST client against a repository-manager API / filesystem mount

## Decision Outcome

Chosen options:

* **EXT-IF-01, CMDB (closes CDR-17):** SQL over the vendor's native protocol through **SQLAlchemy Core**, read-only. The DBMS dialect and driver come from the connection URL (`mysql+pymysql://…` for the dev mock). All queries stay in one adapter. The table and column names used are mapped in one place, so a different production schema changes only the mapping. This keeps the existing port and fixes the engine-lock-in risk at small cost.
* **EXT-IF-02, source repository (closes CDR-18):** **Git over HTTPS**, using the `git` CLI, with a shallow clone (`--depth 1`) of the tag that equals the unit version (as built). Changes from the as-built adapter:
  * TLS verification is on by default, with an optional CA bundle setting. `http.sslVerify=false` is removed.
  * Credentials are passed through `GIT_ASKPASS` or a credential helper, not in the URL (ADR-0032).
  * The commit hash of each clone is recorded for provenance (ADR-0035).
* **EXT-IF-03, package repository (closes CDR-19):** **HTTPS REST** with token authentication, behind an `IPackageRepository` port. The first adapter targets the repository manager actually in use; it is confirmed with its owners before R5, and a fake is used until then. The port returns package metadata (name, version, checksum) and downloads artifacts by version.
* **Connection configuration (MDG.8):** `DataSourceConfig` stays the domain type. Configurations are saved per user in the relational store (ADR-0008), with credentials encrypted (ADR-0032). The `dve.ini` sections provide only defaults. Each source is verified with one cheap call when it is connected, as built (DVE.7).

### Consequences

* Good, because a non-MySQL production CMDB needs only a new URL and a mapping, not a new adapter.
* Good, because source acquisition stays reproducible (tag → commit hash) and becomes secure by default.
* Bad, because there is a small rewrite of the CMDB adapter onto SQLAlchemy Core.
* Bad, because the package repository protocol stays provisional until its owners confirm the product.

### Confirmation

* Adapter contract tests (ADR-0041) run against the `dev/` MySQL and Gitea stack.
* A test asserts that no credential appears in any spawned process command line or in log output.

## Pros and Cons of the Options

### CMDB via PyMySQL (as built) / SQLAlchemy Core

* PyMySQL: Good, because it works today. Bad, because it is bound to MySQL, and the production CMDB engine is unconfirmed.
* SQLAlchemy Core: Good, because it is dialect-independent and still explicit SQL. Bad, because it adds a dependency layer.

### Source repository via `git` CLI / REST archive / Python library

* `git` CLI: Good, because it works with any Git server, it is built, and tags are exact. Bad, because it needs a subprocess and credential plumbing.
* REST archive: Good, because there is no `git` binary. Bad, because it is server-specific (Gitea, GitLab and Bitbucket differ).
* Python library: Good, because it runs in-process. Bad, because shallow-clone and auth support vary.

### Package repository via REST / filesystem mount

* REST: Good, because it is the standard interface of repository managers. Bad, because the product is still unconfirmed.
* Mount: Good, because it is simple. Bad, because it depends on infrastructure, and there are no checksums or metadata.

## More Information

* Code: `mdg/src/mdg/adapters/config_management/`, `mdg/src/mdg/adapters/source_code/git_source_code_repository.py`, `dve/src/dve/services/data_source_connections.py`
* Related: ADR-0003, ADR-0008, ADR-0032, ADR-0035
