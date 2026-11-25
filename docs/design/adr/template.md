# ADR-NNNN: {Short title of the problem and the chosen solution}

| Field | Value |
|---|---|
| Status | {Proposed \| Accepted \| Accepted (<clause> Proposed) \| Rejected \| Deprecated \| Superseded by [ADR-NNNN](NNNN-title.md)} |
| Date | {YYYY-MM-DD of the last status change} |
| Deciders | CDR Board{, other people who took part in the decision} |
| Consulted | {people or teams whose opinion was sought} |
| Kind | {Ratify \| Reconcile \| Decide} (see [ADR Roadmap §2](../ADR-ROADMAP.md#2-conventions)) |
| Traces | {SRS requirement IDs, e.g. SMM.29–31; quality attributes, e.g. QA-02} |
| Resolves | {deferred design points this ADR settles, by SRS/SDD source, e.g. "SMM.30 concurrent user/operation count" (see [ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr)), or —} |
| Decide by | {Wave and date from [ADR Roadmap §5](../ADR-ROADMAP.md#5-decision-schedule)} |
| Supersedes | {[ADR-NNNN](NNNN-title.md) or —} |

<!-- ADRs are written in English only. Use canonical SRS.md IDs (MDG, SCG, FDM, ADM, SMM, DVE). -->

## Context and Problem Statement

{Describe the context and the problem in two or three sentences, or as a question. Cite the SRS requirements, SDD sections and deferred design points ("to be determined during the critical design phase") that create the need for this decision.}

## Decision Drivers

* {Driver 1, e.g. a requirement (DVE.27) or quality attribute (QA-06)}
* {Driver 2, e.g. a constraint (on-premises deployment, existing code in `dve/`)}
* {…}

## Considered Options

* {Option 1, e.g. "as built"}
* {Option 2, e.g. "SDP §5"}
* {Option 3}

## Decision Outcome

Chosen option: "{Option N}", because {justification: which drivers it satisfies, which knock-out criterion it meets, or why it is better than the others}.

### Consequences

* Good, because {positive consequence, e.g. a requirement now satisfiable, simpler deployment}
* Bad, because {negative consequence, e.g. migration work, a new dependency to operate}
* {Follow-up work: SDD sections to update, SRS/SDD "to be determined" wording to replace with a link to this ADR, backlog stories affected}

### Confirmation

{How compliance with this decision is checked: an STD test case, an automated test or CI check, an architecture fitness function, or a review checklist item.}

## Pros and Cons of the Options

### {Option 1}

{Example, description or link to more information}

* Good, because {argument}
* Neutral, because {argument}
* Bad, because {argument}

### {Option 2}

{…}

## More Information

{Links to related ADRs, SRS requirements, SDD sections, code paths, prototypes or measurements. State any condition under which this decision should be revisited.}
