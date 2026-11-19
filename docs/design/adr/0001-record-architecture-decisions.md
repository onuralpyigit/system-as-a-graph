# ADR-0001: Record architecture decisions with MADR

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | BACKLOG S0.2-02 (decision-log workflow); BACKLOG findings L2, L5 |
| Resolves | — |
| Decide by | — |
| Supersedes | — |

## Context and Problem Statement

SaaG has no decision log. The SRS and SDD defer 30 design points "to the critical design phase". A separate CDR register used to list them, but all were `Open`, and a register row records neither the options weighed nor the reasons for a choice. Meanwhile, [SDP §5](../../planning/SDP.md) fixes a technology stack that those deferred points still leave open ([BACKLOG](../../planning/BACKLOG.md) finding L2). The code in `mdg/` and `dve/` was built on a partly different stack (Flask instead of FastAPI, spawned child processes instead of Procrastinate, offline wheelhouses for CPython 3.9 instead of Docker Compose; see commit `1157784`). The project needs one place where each significant decision is reasoned, approved and linked to the requirements and deferred design points it settles.

## Decision Drivers

* A decision must be traceable to SRS requirement IDs and to the deferred design points it resolves.
* The reasons and rejected options must survive staff changes and later reviews.
* Decisions must be reviewed with the same pull-request flow as code and documents.
* The project documents are kept in English and Turkish (SRS, SDP).
* The process must be light enough to close the overdue BACKLOG decision lane items quickly (L5).

## Considered Options

* MADR records in the repository (`docs/design/adr/`)
* Nygard-style records in the repository
* Extending the CDR register with a "decision" column only
* A wiki outside the repository

## Decision Outcome

Chosen option: "MADR records in the repository", because MADR's *Decision Drivers*, *Considered Options* and *Pros and Cons* sections match how deferred design points have to be resolved: by comparing alternatives against requirements. Keeping the records in the repository keeps them versioned and reviewed alongside the SRS, SDD and code.

The process is:

1. **Location and naming.** `docs/design/adr/NNNN-kebab-case-title.md`, using [template.md](template.md). The [ADR Roadmap](../ADR-ROADMAP.md) reserves numbers. A number is never reused.
2. **Language.** ADRs and the ADR Roadmap are written in English only; there are no Turkish translations. They use the canonical SRS.md IDs `MDG / SCG / FDM / ADM / SMM / DVE` (BACKLOG Appendix A).
3. **SaaG fields.** In addition to the MADR sections, every ADR states `Kind`, `Traces`, `Resolves` and `Decide by` in its header table. `Resolves` names the deferred design points the ADR settles, by their SRS or SDD source (for example "SRS MDG.19 mandatory file list").
4. **Lifecycle.** `Planned` (roadmap only) → `Proposed` (file in an open pull request) → `Accepted` or `Rejected`. Later it may become `Deprecated` or `Superseded by ADR-NNNN`. A roadmap entry dropped before acceptance is removed from the catalog, and numbers stay gapless. An accepted ADR is not edited in substance; a change of decision is a new ADR that supersedes it.
5. **Approval.** The CDR Board accepts or rejects a proposed ADR by approving its pull request.
6. **ADRs are the only register of deferred design points.** Every point the SRS or SDD defers "to the critical design phase" is listed in [ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr) against the ADR that resolves it. There is no separate CDR register. A point is resolved when its ADR is `Accepted`; it is deferred when its ADR is re-planned to a later wave with a recorded reason. The pull request that accepts an ADR replaces the "to be determined during the critical design phase" wording in the SRS or SDD with a link to the ADR, and updates the ADR's status in the roadmap.
7. **SDP §5 as options.** Technology choices in SDP §5 are candidate options. Where the code differs from them, a *Reconcile* ADR weighs both, and SDP §5 or the code is aligned afterwards.

### Consequences

* Good, because every deferred design point gets an owner, a deadline (roadmap wave) and a recorded rationale, in one place.
* Good, because the contradiction between SDP §5 and the still-open design points (L2) gets a defined resolution path.
* Good, because decisions are reviewed and versioned with the documents and code they affect.
* Bad, because accepting an ADR requires touching several documents (ADR, roadmap, SRS or SDD) in one pull request.

### Confirmation

* Each release DoD includes a roadmap check: every ADR scheduled for the wave due at that release is `Accepted` or `Rejected`, or it is re-planned with a reason ([ADR Roadmap §7](../ADR-ROADMAP.md#7-maintaining-this-roadmap)).
* Pull-request review checks that an accepted ADR's `Resolves` points no longer carry "to be determined during the critical design phase" wording in the SRS or SDD.

## Pros and Cons of the Options

### MADR records in the repository

* Good, because the structure makes alternatives and drivers explicit, which fits the resolution of deferred design points.
* Good, because it is plain Markdown, reviewed in pull requests, and readable without tools.
* Bad, because it is longer to write than the Nygard format.

### Nygard-style records in the repository

* Good, because it is short (Context, Decision, Consequences).
* Bad, because rejected options and their trade-offs are often lost, and they are exactly what the CDR Board needs to review.

### Extending the CDR register only

* Good, because there is no new document type.
* Bad, because a table row cannot hold context, options and consequences. The register would still contradict SDP §5 without explaining why.
* Bad, because the register and the ADRs would have to be kept in step, so the same decision is maintained in two places. The register was retired on 2026-11-19 for this reason.

### A wiki outside the repository

* Good, because it is easy to edit.
* Bad, because it is not versioned or reviewed with the code and documents, and links to requirement IDs drift.

## More Information

* [ADR Roadmap](../ADR-ROADMAP.md): the catalog of planned ADRs, the decision waves and the coverage matrices.
* [ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr): the deferred design points and the ADR that resolves each one.
* Amended 2026-11-19: the separate CDR register (`docs/design/CDR.md`) was retired. Its 30 items are now tracked only through ADRs (step 6), and the `Closes` header field is renamed `Resolves`.
* Amended 2026-11-19: ADRs are kept in English only (step 2). The Turkish `.tr.md` ADR files, `template.tr.md` and the Turkish roadmap (`ADR-ROADMAP.tr.md`) were removed.
* Amended 2026-11-19: the catalog was consolidated by theme and renumbered gaplessly as ADR-0001…ADR-0021; numbers of ADRs removed before acceptance are not kept.
* MADR: <https://adr.github.io/madr/>
