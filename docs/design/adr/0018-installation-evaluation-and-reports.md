# ADR-0018: Installation evaluation: scoring, decision and reports

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, pipeline owners, system engineering |
| Kind | Decide |
| Traces | DVE.18, 21–26, 71–78; SMM.31; MDG.15; QA-04, QA-06 |
| Resolves | DP-13 (DVE.26 exportable report file format); DP-14 (DVE.76 conformance scoring method) |
| Decide by | Wave E (2027-08-13) |
| Supersedes | — |

## Context and Problem Statement

R7 evaluates whether candidate software units may be installed in the target environment (DVE.71):

* **Model:** a process-specific System Model is built with the candidate versions (SMM.31, MDG.15; ADR-0011).
* **Headings:** suitability is analysed under four headings:
  * structural and architectural conformance (DVE.72);
  * interface, topic and communication conformance (DVE.73);
  * dependency and integration conformance (DVE.74);
  * resource and performance sufficiency (DVE.75).
* **Rules:** each control rule has an identifier, heading, severity, weight, acceptance criterion and blocking status. The conformance categories and the scoring method are deferred (DVE.76, DP-14).
* **Blocking:** a critical finding or a violated blocking rule makes the result "non-conforming" regardless of the score, and the pipeline is told to stop (DVE.77).
* **Per unit:** several units are evaluated with independent operation IDs. Each gets its own score, score class, blocking findings and decision, plus an aggregate result, machine-processable (DVE.78).

Separately, DVE.26 requires summary and detailed **reports** of verification, analysis and simulation results in an exportable format, which is deferred (DP-13). It lists their mandatory content.

ADR-0016 fixes the rule record (including `weight` and `blocking`), and ADR-0007 the operation and finding records. ADR-0005 §3 covers the automation contract that carries the result.

## Decision Drivers

* The score must be explainable from the rule results, and stable when rules are added under another heading.
* Blocking must override any score (DVE.77).
* The CI result must be machine-processable and identical to what the UI and the report show (DVE.78).
* Report generation must work on the offline host with the wheels already vendored (ADR-0004).

## Considered Options

* Scoring: weighted pass ratio per heading, then a weighted mean / per-heading minimums / severity-penalty points
* Reports: HTML + JSON + CSV rendered by `dve`, with PDF printed from the browser / server-side PDF (WeasyPrint or ReportLab) / JSON only

## Decision Outcome

Chosen options: **a weighted pass ratio per heading combined by a weighted mean, with a threshold class and a blocking override**, and **HTML, JSON and CSV reports rendered by `dve`, with PDF printed from the browser**. The pass ratio is directly explainable from the rule results. Jinja2, already a Flask dependency in the wheelhouse, renders HTML with no new library, while a server-side PDF engine would need native libraries the offline host may lack.

### 1. Scoring and decision (DVE.71–78, DP-14)

* **Applicable rules:** the rules of the evaluation profile (ADR-0016) whose heading is one of DVE.72–75 and whose check applies to the candidate's elements.
* **Heading score:** *S_h = 100 × Σ w(r) for passed rules r ÷ Σ w(r) for applicable rules r*. A heading with no applicable rules is reported as `n/a` and left out of the overall score.
* **Overall score:** *S = Σ_h c_h · S_h ÷ Σ_h c_h* over the headings with a score. The heading coefficients *c_h* come from the profile and default to equal weights.
* **Classes (DVE.76, DVE.18):** `conforming` if *S* is at or above the profile's `threshold`, otherwise `non-conforming`. The default threshold is 80. A profile may define named bands for display, such as `A ≥ 90`, `B ≥ 80` and `C < 80`, but the decision depends only on the threshold.
* **Blocking override (DVE.77):** if any finding has severity `critical`, or comes from a rule with `blocking: true`, the class is `non-conforming` and the decision is `block`, whatever *S* is. The blocking findings are listed in the result.
* **Decision:** `allow` when conforming and nothing blocks, otherwise `block`.
* **Per unit and aggregate (DVE.78):**
  * One `installation_evaluation` operation per candidate unit, each a child of one parent operation (ADR-0007 `parent_operation_id`).
  * Each child records its heading scores, overall score, class, blocking findings and decision.
  * The parent's decision is `block` if any child blocks.
* **Provisional rules** are reported but excluded from scores and decisions (ADR-0016).

### 2. Reports (DVE.26, DP-13)

* **Formats:**
  * **HTML**, rendered with Jinja2 templates in `dve/src/dve/templates/reports/`, self-contained (inline CSS, no external requests), with print styles, so the browser's *Print to PDF* produces the PDF;
  * **JSON**, following a published schema (`docs/api/report-1.0.schema.json`). It is the same data the automation contract returns (ADR-0005 §3);
  * **CSV** of the findings table, for spreadsheets.
* **Kinds:** a *summary* report (headline results, scores, counts by severity, blocking findings) and a *detailed* report (every finding with all DVE.21 fields, cause-and-effect links, affected elements and evidence).
* **Mandatory content (DVE.26):**
  * project, platform and system version;
  * the System Model used (instance, revision, Model Data hash);
  * the AED used and its source kind;
  * operation ID and type, and start and end time;
  * the result, findings, affected nodes and relationships, severities and additional information.

  All of these come from the ADR-0007 records. Nothing is stored only in the report.
* **Storage:** a generated report is registered as an artifact of kind `report` (ADR-0007), and its export is audited.
* **Server-side PDF** is out of scope until an offline-installable renderer is chosen in a new ADR.

### Consequences

* Good, because every score can be recomputed by hand from the listed rule results and weights.
* Good, because the UI, the reports and the CI result are generated from the same records, so they cannot disagree.
* Good, because reports need no new dependency and work offline.
* Bad, because a weighted mean can hide one weak heading. The per-heading scores are always shown, and a profile can make important rules blocking.
* Bad, because PDF output depends on the user's browser print, so its layout is controlled only through print CSS.

### Confirmation

* A scoring test on fixed rule results checks heading scores, the overall score, the class, and that a single blocking or critical finding forces `block`.
* A multi-unit test checks independent child operations and the aggregate decision.
* A report test renders summary and detailed reports for a sample operation and checks that every DVE.26 field is present in the HTML, JSON and CSV. The JSON validates against its schema.

### Open points

* The default threshold, the heading coefficients and the display bands are confirmed with the pipeline owners and the CDR Board.
* Whether a server-side PDF is required for formal records, which would need a renderer decision.

## Pros and Cons of the Options

* Weighted pass ratio (chosen): Good, because it is explainable and stable under rule additions. Bad, because it can average away a weak heading, which the per-heading display and blocking rules mitigate.
* Per-heading minimums: Good, because no heading can be ignored. Bad, because there are more parameters, and results are harder to rank.
* Severity-penalty points: Good, because they are intuitive. Bad, because the result depends on the number of rules, so it is unstable as the catalog grows.
* HTML + JSON + CSV (chosen): Good, because they work offline and need no new dependency. Bad, because PDF depends on browser printing.
* Server-side PDF: Good, because the output is controlled. Bad, because WeasyPrint needs native libraries (Pango, Cairo), and ReportLab means hand-built layouts.
* JSON only: Bad, because it is not readable as a report.

## More Information

* [SRS §6.1.1, §6.1.4](../../requirements/SRS.md)
* Related: ADR-0005, ADR-0006, ADR-0007, ADR-0011, ADR-0016, ADR-0019
