# ADR-0002: Canonical component identifiers and domain vocabulary

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | All SRS requirements (citation form); BACKLOG findings T1, T2, T3, L3 |
| Resolves | — |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

The same components and artifacts have different names across the document set and the code ([BACKLOG Appendix A](../../planning/BACKLOG.md)):

* SRS.md uses `MDG / SCG / FDM / ADM / SMM / DVE`.
* SRS.tr and SDP.tr use `MVU / SUR / SVY / AVY / SMY / TDM`.
* SDD, STD and the retired CDR register used `MSG / SCG / TDM / ADM / CSM / DVE` (including `SaaG-MSG`, `SaaG-TDM`, `SaaG-CSM` and test IDs `TC-MSG-*`, `TC-TDM-*`, `TC-CSM-*`).

`TDM` therefore means the Design Verification Engine in Turkish documents but the Telemetry Data Manager (= FDM) in the SDD. The artifacts were renamed too: "Model Data" became "Model Setup Data", and "System Model" became "Core System Model".

As built (`1157784`), the code follows the SDD artifact vocabulary (`ModelSetupData`, `model_setup_data_store`, `mdg/tests/test_mdg.py`, `mdg/tests/domain/test_model_setup_data.py`, and UI labels in `dve/src/dve/templates/index.html` and `dve/src/dve/static/app.js`). Docstrings, HTML comments and JS comments cite an older numbering in several forms—`SRS DSM-MDG req N`, `SRS DSM-DVE req N`, `SRS DSM-SMM req N`, unprefixed `DSM-SMM req 6-7` and `DSM-DVE req 5`, dotted sub-numbers (`req 2.1`, `req 2.2`), `(SRS DSM-DVE)` without a number, and bare `(req N)` in both `dve/src/dve/static/*.js` and `dve/src/dve/templates/index.html`. None of those numbers match SRS.md. Without one canonical scheme, no trace in the SRS → SDD → STD → code chain can be resolved reliably.

## Decision Drivers

* Every requirement citation must resolve to exactly one SRS requirement.
* The Turkish and English documents must cite the same IDs without homonym collisions.
* Renaming must finish before R3 adds verification code that cites `DVE` and `SMM` requirements heavily.
* Operational command, service and directory names already wired into deployment scripts (`dsm`) should not suffer gratuitous churn.

## Considered Options

* SRS.md IDs and terms everywhere (BACKLOG decision T1)
* Per-document names plus a mapping table
* SDD vocabulary everywhere (`MSG`, `TDM`, `CSM`, "Model Setup Data", "Core System Model")

## Decision Outcome

Chosen option: "SRS.md IDs and terms everywhere", because the SRS is the contractual baseline, and it is the only scheme without the `TDM` collision.

1. **Component IDs:** `MDG`, `SCG`, `FDM`, `ADM`, `SMM`, `DVE` in every language. The infrastructure constraint is `FDM-INF.1`. The Turkish documents use the Turkish component *names* (e.g. "Model Veri Üreteci") paired with the canonical English IDs (`MDG`). All retired component abbreviations (`MSG`, `TDM`, `CSM`, `MVU`, `SUR`, `SVY`, `AVY`, `SMY`) are removed from SDD, STD, UXD, BACKLOG and Turkish documents (`TC-MSG-*` → `TC-MDG-*`, `TC-TDM-*` → `TC-FDM-*`, `TC-CSM-*` → `TC-SMM-*`).
2. **Requirement citations:** `<ID>.<n>` as numbered in SRS.md, e.g. `MDG.19`, `DVE.27`. Ranges are written `DVE.32–35`.
3. **Artifact terms:** "Model Data" (file: "Model Data file"), "System Model", "Analytical Evaluation Data", "System Field Records", "Software Unit Version Inventory", exactly as in the SRS, in documents, code and UI labels. "Model Setup Data" and "Core System Model" are retired.
4. **Retained product/runtime prefix (`dsm`):** `dsm` ("Digital System Model", from the SRS title) is intentionally retained as the console executable (`dsm`), systemd unit (`dsm.service`), host directory prefix (`/opt/dsm`, `/etc/dsm`, `/var/lib/dsm`, `/var/log/dsm`), SQLite file (`dsm.db`), environment variable prefix (`DSM_*`), and frontend namespace (`window.Dsm`, `dsm:state:*`), because it names the whole CSCI product rather than a single CSC.
5. **Code refactor (R3):**
   * Package directories are `mdg/ scg/ fdm/ adm/ smm/ dve/` plus `common/` (ADR-0004).
   * Public identifiers and modules move from `model_setup_data` / `ModelSetupData` to `model_data` / `ModelData` in one coordinated refactor across `mdg` and `dve`.
   * Docstrings, HTML comments and JS comments replace all `DSM-*` and `(req N)` citations with canonical `MDG.n`, `SMM.n`, `DVE.n` IDs using a reviewed mapping table from the legacy numbering to SRS.md (the legacy numbers are not a constant offset).

### Consequences

* Good, because every trace becomes mechanically resolvable across SRS, SDD, STD, ADRs and code.
* Good, because new R3 code starts with the canonical vocabulary while keeping `dsm` operational paths stable.
* Bad, because SDD, STD, UXD and BACKLOG remnants need a coordinated rename pass (BACKLOG story S0.2-01), and the code refactor touches `mdg`'s public API, `dve` imports and UI text.
* Bad, because pre-1.0 Model Data JSON files on disk use legacy field/type names; ADR-0009's `0.x` reader handles backward compatibility.

### Confirmation

* A CI check greps `docs/`, `*/src/` and `*/tests/` for retired component and artifact forms: `\b(MSG|TDM|CSM|MVU|SUR|SVY|AVY|SMY)\.\d`, `\b(SaaG|TC)-(MSG|TDM|CSM)\b`, `\bDSM-(MDG|SMM|DVE)\b`, `\(req\s+\d`, `"Model Setup Data"`, and `"Core System Model"`. It fails on any match outside historical ADR context paragraphs (such as this ADR's problem statement) once S0.2-01 and the R3 code rename land.
* Pull-request review verifies canonical requirement citations on all touched files.

## Pros and Cons of the Options

### SRS.md IDs and terms everywhere

* Good, because there is a single contractual source of truth, already used by the SRS, SDP, BACKLOG and ADR Roadmap.
* Good, because it eliminates the `TDM` homonym across English and Turkish documents.
* Bad, because it requires a one-time rename across SDD, STD, UXD and the `mdg`/`dve` codebase.

### Per-document names plus a mapping table

* Good, because existing files do not have to be renamed.
* Bad, because `TDM` stays ambiguous, and every reader and CI script must translate every citation.

### SDD vocabulary everywhere

* Good, because parts of the `1157784` codebase already used `ModelSetupData`.
* Bad, because it contradicts the contractual SRS and leaves the Turkish `TDM` homonym unresolved.

## More Information

* [BACKLOG §0.2 and Appendix A](../../planning/BACKLOG.md)
* [ADR Roadmap](../ADR-ROADMAP.md)
* Code: `mdg/src/mdg/domain/model_setup_data.py`, `mdg/src/mdg/ports/model_setup_data_store.py`, `dve/src/dve/templates/index.html`, `dve/src/dve/static/app.js`
* Revisit only if a future contractual amendment to the SRS renames a CSC or splits an existing CSU.
