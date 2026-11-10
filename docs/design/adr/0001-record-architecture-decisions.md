# ADR-0001: Record architecture decisions with MADR

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | BACKLOG S0.2-02 (decision-log workflow); BACKLOG findings L2, L5 |
| Closes | — |
| Decide by | — |
| Supersedes | — |

## Context and Problem Statement

SaaG has no decision log. The SRS and SDD defer 30 design points "to the critical design phase", and the [CDR register](../CDR.md) lists them, but all are `Open`, and the register records neither the options weighed nor the reasons for a choice. Meanwhile, [SDP §5](../../planning/SDP.md) fixes a technology stack that the CDR still lists as open ([BACKLOG](../../planning/BACKLOG.md) finding L2). The code in `mdg/` and `dve/` was built on a partly different stack (Flask, Celery + Redis instead of FastAPI, Procrastinate). The project needs one place where each significant decision is reasoned, approved and linked to the requirements and CDR items it settles.

## Decision Drivers

* A decision must be traceable to SRS requirement IDs and to the CDR items it closes.
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

Chosen option: "MADR records in the repository", because MADR's *Decision Drivers*, *Considered Options* and *Pros and Cons* sections match how CDR items have to be closed: by comparing alternatives against requirements. Keeping the records in the repository keeps them versioned and reviewed alongside the SRS, SDD and code.

The process is:

1. **Location and naming.** `docs/design/adr/NNNN-kebab-case-title.md`, using [template.md](template.md). The [ADR Roadmap](../ADR-ROADMAP.md) reserves numbers. A number is never reused.
2. **Languages.** English is normative. A Turkish translation `NNNN-kebab-case-title.tr.md` (from [template.tr.md](template.tr.md)) is added or updated in the same pull request. Both languages use the canonical SRS.md IDs `MDG / SCG / FDM / ADM / SMM / DVE` (BACKLOG Appendix A).
3. **SaaG fields.** In addition to the MADR sections, every ADR states `Kind`, `Traces`, `Closes` and `Decide by` in its header table.
4. **Lifecycle.** `Planned` (roadmap only) → `Proposed` (file in an open pull request) → `Accepted` or `Rejected`. Later it may become `Deprecated` or `Superseded by ADR-NNNN`. A roadmap entry dropped before it is proposed becomes `Withdrawn`. An accepted ADR is not edited in substance; a change of decision is a new ADR that supersedes it.
5. **Approval.** The CDR Board accepts or rejects a proposed ADR by approving its pull request.
6. **Closing CDR items.** The pull request that accepts an ADR also sets each CDR item in its `Closes` field to `Resolved` with a link to the ADR. It replaces the "to be determined during the critical design phase" wording in the SRS or SDD, and updates the ADR's status in the roadmap.
7. **SDP §5 as options.** Technology choices in SDP §5 are candidate options. Where the code differs from them, a *Reconcile* ADR weighs both, and SDP §5 or the code is aligned afterwards.

### Consequences

* Good, because every CDR item gets an owner, a deadline (roadmap wave) and a recorded rationale.
* Good, because the SDP §5 / CDR contradiction (L2) gets a defined resolution path.
* Good, because decisions are reviewed and versioned with the documents and code they affect.
* Bad, because each decision needs an English and a Turkish file, which doubles the writing and review effort.
* Bad, because accepting an ADR requires touching several documents (ADR, roadmap, CDR, SRS or SDD) in one pull request.

### Confirmation

* Each release DoD includes a roadmap check: every ADR scheduled for the wave due at that release is `Accepted`, `Rejected` or `Withdrawn`, or it is re-planned with a reason ([ADR Roadmap §7](../ADR-ROADMAP.md#7-maintaining-this-roadmap)).
* Pull-request review checks that an accepted ADR's `Closes` items are `Resolved` in CDR.md, and that the `.tr.md` file exists.

## Pros and Cons of the Options

### MADR records in the repository

* Good, because the structure makes alternatives and drivers explicit, which fits CDR closure.
* Good, because it is plain Markdown, reviewed in pull requests, and readable without tools.
* Bad, because it is longer to write than the Nygard format.

### Nygard-style records in the repository

* Good, because it is short (Context, Decision, Consequences).
* Bad, because rejected options and their trade-offs are often lost, and they are exactly what the CDR Board needs to review.

### Extending the CDR register only

* Good, because there is no new document type.
* Bad, because a table row cannot hold context, options and consequences. The register would still contradict SDP §5 without explaining why.

### A wiki outside the repository

* Good, because it is easy to edit.
* Bad, because it is not versioned or reviewed with the code and documents, and links to requirement IDs drift.

## More Information

* [ADR Roadmap](../ADR-ROADMAP.md): the catalog of planned ADRs, the decision waves and the coverage matrices.
* [CDR register](../CDR.md): the open items closed by ADRs.
* MADR: <https://adr.github.io/madr/>
