# ADR-0004: Deployable units and repository layout

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Reconcile |
| Traces | QA-10, QA-11; SMM.30; DVE.27; BACKLOG T3; SDP §4 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The SRS decomposes the CSCI into six CSCs. SDP §4 describes a repository with `msd/ scg/ frd/ adp/ csm/ vae/`. The repository actually has `mdg/` (a library), `dve/` (Flask API + Celery worker + UI over `mdg`) and `dev/` (mock data sources). BACKLOG finding T3 notes that no document owns the CSC → directory mapping. Before SCG, FDM, ADM and SMM get code, the project must decide two things. Is each CSC its own deployable service, or is the CSCI one deployable? Where does each CSC live in the repository?

## Decision Drivers

* Single-team, on-premises deployment with Docker Compose and no orchestration (SDP §5).
* CSCs exchange large artifacts (Model Data, System Model, Analytical Evaluation Data) and run in strict sequence (SDD §2.2).
* SRS traceability needs a visible one-to-one CSC → code mapping.
* Concurrent operations must be isolated from one another (SMM.30). That is a runtime property, not a deployment one.

## Considered Options

* Modular monolith: one Python distribution per CSC in one repository, deployed together as one image with two process types (API and worker)
* Service per CSC: six deployable services with network APIs
* The SDP §4 layout with its directory names

## Decision Outcome

Chosen option: "Modular monolith", because the CSCs are sequential stages owned by one team. Separate services would add network contracts, deployment units and failure modes without any independent scaling or ownership need.

* **Repository layout:**

  ```
  mdg/  scg/  fdm/  adm/  smm/  dve/   one Python distribution per CSC: <csc>/setup.py, <csc>/src/<csc>/, <csc>/tests/
  web/                                 Operations Panel front end, if ADR-0009 selects a separate front-end build
  dev/                                 development-only mock data sources
  deploy/                              production Compose files and configuration templates (ADR-0039)
  docs/
  ```

  A shared kernel for cross-cutting types (error records, ADR-0034; provenance, ADR-0035) lives in a seventh distribution, `common/`. It contains no business logic.
* **Dependency direction:** `dve` → `smm`, `adm`, `mdg`, `scg`, `fdm`; `adm` → `scg`, `fdm`; `smm` → `mdg` (Model Data types), `adm` (AED types). No cycles.
* **Process types:** one container image runs as `api` (HTTP) or `worker` (background operations, ADR-0006). Workers can be scaled by replica count. Isolation between operations comes from ADR-0016 and ADR-0033, not from separate services.
* SDP §4 is updated to this layout.

### Consequences

* Good, because CSC boundaries stay visible and testable (per-package import contracts) while deployment stays a single image.
* Good, because handoffs are in-process calls (ADR-0007), with no serialization overhead between stages.
* Bad, because all CSCs share one release cadence and one dependency set. A heavy dependency in one CSC is installed everywhere.
* Bad, because the boundaries are enforced by tooling and review rather than by the network.
* Follow-up: create the `scg/ fdm/ adm/ smm/ common/` skeletons and update SDP §4.

### Confirmation

* An `import-linter` "layers" contract across distributions enforces the dependency direction above.
* The Compose file defines only `api`, `worker` and backing stores.

## Pros and Cons of the Options

### Modular monolith

* Good, because it is simple to deploy and debug, and it matches the existing `mdg` + `dve` structure.
* Bad, because it scales only as a whole (mitigated by scaling the worker).

### Service per CSC

* Good, because there are hard boundaries and independent deployment.
* Bad, because there are six services, their APIs and their versioning for one team. The SRS requires none of this.

### SDP §4 layout

* Good, because it is already written down.
* Bad, because its names (`msd`, `frd`, `adp`, `csm`, `vae`) contradict the canonical IDs (ADR-0002).

## More Information

* [BACKLOG finding T3 and Appendix A](../../planning/BACKLOG.md)
* Related: ADR-0003, ADR-0006, ADR-0007, ADR-0039
