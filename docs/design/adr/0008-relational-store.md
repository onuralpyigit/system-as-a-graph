# ADR-0008: Relational store for metadata, operations and findings

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Reconcile |
| Traces | MDG.8, 14–15; DVE.21–26, 78; SMM.26; QA-04, QA-08 |
| Closes | CDR-29 (part: Software Unit Version Inventory; Findings, Operations & Reports) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

Several stores in SDD §2.4 hold structured records that must be durable, queryable and filterable:

- the Software Unit Version Inventory;
- the Findings, Operations & Reports store;
- data-source configurations (MDG.8);
- model-instance and artifact registries (ADR-0016, ADR-0035).

DVE.23 needs sorting and filtering of findings by many fields. SDP §5 names PostgreSQL. The code has no relational store of its own. The inventory is embedded in the Model Data JSON, and operation state and logs are in Redis (ADR-0006). MySQL appears only as the *external* configuration management database mock in `dev/`.

## Decision Drivers

* Records must be durable and transactional (QA-04, QA-08).
* Findings have a fixed core plus variable evidence (DVE.21), so the store should handle semi-structured columns.
* The schema must be versioned and migrated reproducibly.
* Operations effort: one well-known database engine in an on-premises Compose deployment.

## Considered Options

* PostgreSQL (SDP §5)
* MySQL/MariaDB (the same engine as the dev CMDB mock)
* No relational store: keep records in Redis and JSON files (as built)

## Decision Outcome

Chosen option: "PostgreSQL", because JSONB columns hold finding evidence and operation parameters next to indexed core fields. It also has strong transactional semantics, and it can host other needs later (e.g. time-series extensions under ADR-0021) without a second engine.

* **Version:** PostgreSQL 16, run as a Compose service with a persistent volume.
* **Access:** SQLAlchemy 2 (Core plus ORM where useful) behind repository ports (ADR-0003). Migrations with Alembic, one migration history per CSC schema.
* **Schemas:** one PostgreSQL schema per owning CSC (`mdg`, `fdm`, `dve`, …), plus `common` for operations, artifacts and audit (ADR-0024, ADR-0035).
* **Stores placed here:**
  * the Software Unit Version Inventory (also kept inside the Model Data file for self-containment);
  * data-source configurations (credentials encrypted, ADR-0032);
  * operations, findings and report metadata (ADR-0024);
  * model-instance registry (ADR-0016);
  * artifact and provenance registry (ADR-0035).
* **Not here:** the System Model graph (ADR-0015), Model Data files (ADR-0013), and bulk telemetry (ADR-0021).
* The dev CMDB mock stays MySQL, because it imitates an external system; it is not SaaG's store.

### Consequences

* Good, because findings filtering (DVE.23), operation history and reports have a durable, indexed home.
* Good, because one engine serves records of every CSC.
* Bad, because there is a new stateful service to back up (ADR-0040) and migrations to maintain.
* Bad, because the inventory exists both in the database and in the Model Data file. The file is the frozen copy for one run; the database copy is for querying.

### Confirmation

* `alembic upgrade head` runs in CI against a PostgreSQL service container, and repository adapters are tested against it.
* The findings list endpoint meets the ADR-0036 latency budget at the target findings volume.

## Pros and Cons of the Options

### PostgreSQL

* Good, because of JSONB, rich indexing, transactional DDL, and a broad on-prem track record.
* Bad, because it is another service, compared with the current file-and-Redis setup.

### MySQL/MariaDB

* Good, because the team already runs it in `dev/`.
* Bad, because its JSON support is weaker and has no JSONB-style indexing. Reusing the engine also blurs the line between the external CMDB and SaaG's own data.

### Redis and JSON files (as built)

* Good, because nothing new is needed.
* Bad, because there are no queries, constraints or transactions, and durability depends on Redis persistence settings.

## More Information

* [SDD §2.4](../SDD.md), [CDR-29](../CDR.md)
* Related: ADR-0006, ADR-0016, ADR-0024, ADR-0032, ADR-0035, ADR-0040
