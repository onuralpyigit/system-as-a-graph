# ADR-0002: Canonical component identifiers and domain vocabulary

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | All SRS requirements (citation form); BACKLOG findings T1, T2, T3, L3 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The same components and artifacts have different names across the document set and the code ([BACKLOG Appendix A](../../planning/BACKLOG.md)):

- SRS.md uses `MDG / SCG / FDM / ADM / SMM / DVE`.
- SRS.tr and SDP.tr use `MVU / SUR / SVY / AVY / SMY / TDM`.
- SDD, STD and CDR use `MSG / SCG / TDM / ADM / CSM / DVE`.

`TDM` therefore means the Design Verification Engine in Turkish documents but the Telemetry Data Manager (= FDM) in the SDD. CDR items cite requirement IDs that do not exist (`MSG.6`, `CSM.30`). The artifacts are renamed too: "Model Data" becomes "Model Setup Data", and "System Model" becomes "Core System Model". The code follows the SDD vocabulary (`ModelSetupData`, `model_setup_data_store`, `test_msd.py`). Its docstrings also cite an older requirement numbering ("SRS DSM-MDG req 19"). Without one canonical scheme, no trace in the SRS → SDD → STD → code chain can be resolved reliably.

## Decision Drivers

* Every requirement citation must resolve to exactly one SRS requirement.
* The Turkish and English documents must cite the same IDs.
* Renaming must be cheap enough to finish before R3 adds verification code that cites DVE requirements heavily.

## Considered Options

* SRS.md IDs and terms everywhere (BACKLOG decision T1)
* Keep the per-document names and add a mapping table
* SDD vocabulary everywhere (`MSG`, `TDM`, `CSM`, "Model Setup Data", "Core System Model")

## Decision Outcome

Chosen option: "SRS.md IDs and terms everywhere", because the SRS is the contractual baseline, and it is the only scheme without the `TDM` collision.

1. **Component IDs:** `MDG`, `SCG`, `FDM`, `ADM`, `SMM`, `DVE` in every language. The infrastructure constraint is `FDM-INF.1`. The Turkish documents use the Turkish component *names* (e.g. "Model Veri Üreteci") with the canonical IDs. The Turkish abbreviations are retired.
2. **Requirement citations:** `<ID>.<n>` as numbered in SRS.md, e.g. `MDG.19`, `DVE.27`. Ranges are written `DVE.32–35`.
3. **Artifact terms:** "Model Data" (file: "Model Data file"), "System Model", "Analytical Evaluation Data", "System Field Records", "Software Unit Version Inventory", exactly as in the SRS. "Model Setup Data" and "Core System Model" are retired.
4. **Code:**
   * Package directories are `mdg/ scg/ fdm/ adm/ smm/ dve/` (ADR-0004).
   * Public identifiers move from `model_setup_data` / `ModelSetupData` to `model_data` / `ModelData` in one refactor during R3.
   * Docstrings cite requirements as `MDG.n`.

### Consequences

* Good, because every trace becomes resolvable, and the CDR-to-requirement links can be checked mechanically.
* Good, because new R3 code starts with the right vocabulary.
* Bad, because the SDD, STD and CDR need a rename pass (BACKLOG story S0.2-01). The code refactor touches the `mdg` public API and the `dve` imports of it.
* Bad, because the existing Model Data JSON files carry the old naming in field names. ADR-0013 handles their versioning.
* Follow-up: BACKLOG S0.2-01 (document renames); a code refactor story in R3; update CDR "Source" cells.

### Confirmation

* A CI check greps `docs/` and `*/src/` for the retired forms. The pattern is `\b(MSG|TDM|CSM|MVU|SUR|SVY|AVY|SMY)\.\d`, plus "Model Setup Data" and "Core System Model". It fails on any match outside `SRS.tr.md` and `SDP.tr.md` until those are migrated.
* Pull-request review checks the citation form.

## Pros and Cons of the Options

### SRS.md IDs and terms everywhere

* Good, because there is a single source of truth, and it is already used by BACKLOG and the ADR roadmap.
* Bad, because there is a one-time rename across documents and code.

### Per-document names plus a mapping table

* Good, because nothing has to be renamed.
* Bad, because `TDM` stays ambiguous, and every reader must translate every citation.

### SDD vocabulary everywhere

* Good, because the code already uses it.
* Bad, because it contradicts the SRS, which is the contractual document, and it keeps the `TDM` homonym in Turkish.

## More Information

* [BACKLOG §0.2 and Appendix A](../../planning/BACKLOG.md)
* [ADR Roadmap](../ADR-ROADMAP.md)
