# ADR-0018: Installation evaluation: scoring, decision and reports

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, pipeline owners, system engineering |
| Kind | Decide |
| Traces | DVE.18, 21–26, 71–78; SMM.31; MDG.15; QA-04, QA-06 |
| Resolves | DP-13 (DVE.26 exportable report file format); DP-14 (DVE.76 conformance scoring method) |
| Decide by | Wave E (2027-08-13) |
| Supersedes | — |

## Context and Problem Statement

R7 evaluates whether one or more candidate software unit versions are suitable for installation into the target environment (`DVE.71`):

* **Candidate model:** SMM constructs an isolated `candidate` System Model combining the candidate unit version(s) with the target system version's baseline units (`MDG.15`, `SMM.31`, ADR-0011).
* **Four mandatory evaluation headings (`DVE.72–75`):**
  1. `structural_architectural` — structural and architectural conformance (`DVE.72`);
  2. `interface_topic_communication` — interface, topic, and communication conformance (`DVE.73`);
  3. `dependency_integration` — dependency and integration conformance (`DVE.74`);
  4. `resource_performance` — resource and performance sufficiency (`DVE.75`).
* **Scoring & override (`DVE.76–77`):** each rule carries `rule_id`, `evaluation_heading`, `severity`, `weight`, `acceptance_criterion`, and `blocking` (ADR-0016 §1); conformance categories and the scoring formula are deferred to critical design (`DP-14`). Any `critical` finding or violation of a `blocking: true` rule forces the installation result to `"non-conforming"` and instructs the deployment pipeline to stop, regardless of numeric score (`DVE.77`).
* **Multi-unit CI output (`DVE.78`):** evaluations for one or more software units run under independent `operation_id`s and return, per unit, **`score`, `score_class`, `blocking_findings`, and `installation_decision`**, plus an aggregate result, in a machine-processable format (delivered via ADR-0005 §3).
* **Exportable system reports (`DVE.26`, `DP-13`):** DVE generates summary and detailed reports across verification, analysis, simulation, and evaluation operations containing all mandatory provenance and finding fields.

## Decision Drivers

* Every score must be deterministically verifiable by hand from listed rule pass/fail outcomes and weights, without destabilizing when rules are added to another heading.
* Output field names must cleanly distinguish **`score_class`** (letter/quality band), **`conformance`** (`conforming` | `non-conforming`, `DVE.18, 77`), and **`decision`** (`allow` | `block` pipeline gate, `DVE.77–78`) so UI (`UXD Figure 10`), reports (`DVE.26`), and CI JSON (`DVE.78`) never conflate them!
* Report rendering must run 100% offline on CentOS 7 + CPython 3.9 with zero native C/Cairo/Pango dependencies (`ADR-0004`).

## Considered Options

* Scoring method (`DP-14`): Per-heading weighted pass ratio combined by profile heading weights, mandatory `score_class` bands, and unconditional `critical`/`blocking` override
* Scoring method (`DP-14`): Per-heading hard minimum thresholds only (no composite score)
* Scoring method (`DP-14`): Unbounded point deductions subtracted from 100 per finding
* Report formats (`DP-13`): Self-contained HTML (with `@media print` PDF support) + schema-validated JSON + findings CSV rendered by `dve`
* Report formats (`DP-13`): Server-side PDF rendering via WeasyPrint or ReportLab
* Report formats (`DP-13`): Machine-readable JSON export only

## Decision Outcome

Chosen options: **weighted pass ratio per `DVE.72–75` heading combined into a weighted overall score with mandatory `score_class` bands and an unconditional `critical`/`blocking` override**, and **self-contained HTML, JSON and CSV reports rendered by `dve` (with browser print-to-PDF)**.

### 1. Conformance scoring, classification and pipeline decision (`DVE.71–78`, `DP-14`)

* **Applicable rules:** all `status: approved` rules in the selected evaluation profile (ADR-0016 §2) whose `evaluation_heading` is one of the four `DVE.72–75` headings and whose scope applies to the candidate unit and its neighborhood on the `candidate` System Model (`provisional` rules execute for visibility but are excluded from scoring and blocking).
* **Rule outcome:** a rule $r$ with weight $w(r) > 0$ **passes** ($p(r) = 1$) if it produces zero findings on the candidate evaluation, and **fails** ($p(r) = 0$) if it produces one or more findings.
* **Heading score ($S_h \in [0, 100]$):** for each heading $h \in \{\text{DVE.72}, \text{DVE.73}, \text{DVE.74}, \text{DVE.75}\}$ with applicable rules $R_h \neq \emptyset$:
  $$S_h = 100 \times \frac{\sum_{r \in R_h} w(r)\cdot p(r)}{\sum_{r \in R_h} w(r)}$$
  *(Rounded to 2 decimal places; if $R_h = \emptyset$, $S_h = \text{null}$ / `"n/a"` and $h$ is excluded from the denominator below.)*
* **Overall conformance score ($S \in [0, 100]$):** let $H^+ = \{h : R_h \neq \emptyset\}$ and $c_h > 0$ be the profile's heading coefficients (default $c_h = 0.25$ equal weighting across all four headings):
  $$S = \frac{\sum_{h \in H^+} c_h \cdot S_h}{\sum_{h \in H^+} c_h}$$
* **Mandatory four-part evaluation outcome (`DVE.18, 76–78`, harmonizing `UXD Figure 10`):**

  | Field | Values & Rule |
  |---|---|
  | `score` | Numeric $S \in [0.00, 100.00]$ (plus `heading_scores` map for `DVE.72–75`) |
  | `score_class` | Mandatory quality band from `S` (default profile bands: **`A`** (`Good`, $S \ge 90$), **`B`** (`Satisfactory`, $80 \le S < 90$), **`C`** (`Marginal`, $60 \le S < 80$), **`D`** (`Insufficient`, $S < 60$)) — satisfies `DVE.78`'s explicit *score class* requirement |
  | `conformance` | `non-conforming` if $S < \text{threshold}$ (default `80.0`) **OR** `blocking_findings` is non-empty; otherwise `conforming` (`DVE.18, 77`) |
  | `decision` | `allow` when `conformance == 'conforming'` (and `outcome_status != 'error'`); **`block`** when `conformance == 'non-conforming'` or an engine/acquisition error occurred (`DVE.77–78`) |

* **Unconditional blocking override (`DVE.77`):** every finding with `severity == 'critical'` or `blocking == true` is collected into `blocking_findings`. Even if $S = 99.0$ (`score_class = 'A'`), any non-empty `blocking_findings` forces `conformance = 'non-conforming'` and `decision = 'block'`.
* **Multi-unit batch execution and aggregation (`DVE.78`):**
  * Submitting $K \ge 1$ candidate software units creates one non-process parent batch `common_operation` row and $K$ independent child `installation_evaluation` operations on the `pipeline` queue (`parent_operation_id`, ADR-0006 §3, ADR-0007 §2), each building and evaluating its own isolated `candidate` model instance so unit faults are attributed cleanly without cross-unit contamination (plus an optional combined-batch integration check when $K > 1$).
  * The parent operation's `result_summary` aggregates all per-unit results: aggregate `score = min_k(S_k)` (worst-case candidate score), aggregate `score_class` from that minimum score, `conformance = 'non-conforming'` if any unit is `non-conforming`, and **`decision = 'block'` if any unit's decision is `block`**.

### 2. Exportable system reports (`DVE.26`, `DP-13`)

* **Supported export formats (rendered offline by `dve`):**
  1. **Self-contained HTML (`.html`):** rendered via `Jinja2` (`3.1.6`, already in `dve/wheelhouse/`) from `dve/src/dve/templates/reports/{summary,detailed}.html.j2` with embedded CSS, inline SVG score/severity badges, zero external URLs, and dedicated `@media print` page-break/header styles so workstation browsers (*Print → Save as PDF*) produce clean archival PDFs without native server libraries.
  2. **Structured JSON (`.json`):** validated against `dve/src/dve/schemas/report-1.0.schema.json`, sharing the exact evaluation/finding payload structure returned to `/api/v1/` automation clients (ADR-0005 §3).
  3. **Findings CSV (`.csv`):** RFC 4180 UTF-8 CSV via Python's `csv` module for spreadsheet auditing and institutional review boards.
* **Report kinds and mandatory `DVE.26` content:**
  * Both `summary` (executive metadata, heading/overall scores, counts by severity/heading, top KPIs, blocking findings) and `detailed` (full finding catalog with all `DVE.21` fields, `DVE.22` `cause ↔ effect` links, affected nodes/relationships, and supporting evidence) include **every mandatory `DVE.26` attribute**:
    * `project`, `platform`, `system_version`;
    * System Model used (`instance_id`, `kind`, `revision`, `model_data_artifact_id`, `model_data_sha256`, working-model edit count if `working`);
    * Analytical Evaluation Data used (`dataset_id`, `source_kind`: `field` | `synthetic` | `none`, input `field_record_ids` or `scenario_name`/`seed`);
    * `operation_id` (and child `operation_id`s for multi-unit runs), `operation_type`, UTC `started_at` and `ended_at`;
    * `conformance` / evaluation result (`score`, `score_class`, `decision`), findings detected, affected nodes and relationships, severity levels, and rule/evidence details.
* **Persistence & audit:** generated report files are stored under `/var/lib/dsm/workspace/reports/<project>/<platform>/<version>/<report_id>.<ext>`, registered in `common_artifact` (`kind = 'report'`), indexed in `dve_report` (`dsm.db`, ADR-0007 §2), and logged in `common_audit_event`.
* **Document alignment follow-up:** on acceptance, update `UXD §4` (Figure 10/11) and `SDP §2 Increment 7` from `PDF/JSON` to `HTML (print-to-PDF), JSON, CSV`.

### Consequences

* Good, because `score`, `score_class`, `conformance`, and `decision` satisfy `DVE.18`, `DVE.76–78`, and `UXD Figure 10` with zero field-name ambiguity across UI, reports and Jenkins pipelines.
* Good, because HTML + JSON + CSV require zero new wheels beyond `Jinja2` and Python's standard library.
* Bad, because weighted heading averages can mask a lower non-blocking heading score if other headings score 100—mitigated by always displaying all four `S_h` scores and marking critical rules `blocking: true`.

### Confirmation

* Scoring unit tests (`TC-DVE-17`) verify exact `S_h`, `S`, `score_class`, `conformance`, and `decision` across edge cases: empty heading (`n/a`), `S = 95` overridden to `non-conforming`/`block` by a single `critical` or `blocking: true` finding, and `provisional` rule exclusion.
* Multi-unit evaluation test (`DVE.78`, `TC-DVE-19`) submits two candidate units (one passing, one failing a blocking rule), verifying distinct child `operation_id`s, per-unit payloads, and aggregate `decision = 'block'`.
* Report test (`TC-DVE-06`) renders `summary` and `detailed` reports in HTML, JSON and CSV, asserting every `DVE.26` field and `report-1.0.schema.json` validity.

## Pros and Cons of the Options

### Weighted pass ratio per heading + `score_class` + blocking override (chosen)

* Good, because scores stay bounded in $[0, 100]$ regardless of catalog size, remain hand-verifiable, and enforce `DVE.77` hard stops cleanly.
* Bad, because non-blocking failures in a high-rule-count heading carry smaller per-rule percentage drops unless weighted higher.

### Per-heading minimums only

* Good, because weak headings cannot average out.
* Bad, because `DVE.78` explicitly requires a numeric conformance score and score class per unit.

### Unbounded severity-penalty deductions from 100

* Good, because every individual finding deducts points.
* Bad, because large models or growing rule catalogs clamp scores to `0`, making scores incomparable across system versions.

### Self-contained HTML (print-to-PDF) + JSON + CSV (chosen)

* Good, because it runs 100% offline using stdlib + `Jinja2` with zero native C dependencies while serving humans, spreadsheets, and CI pipelines.
* Bad, because generating a `.pdf` binary requires the user's browser *Print to PDF* action.

### Server-side PDF (WeasyPrint / ReportLab)

* Good, because the backend emits `.pdf` bytes directly.
* Bad, because WeasyPrint depends on system `libpango`/`libcairo`/`gdk-pixbuf` (fragile on CentOS 7 `glibc 2.17`), and ReportLab requires maintaining a second imperative layout codebase separate from HTML.

### JSON export only

* Good, because implementation is minimal.
* Bad, because formal review boards and `DVE.26` require human-readable summary and detailed system reports.

## More Information

* [SRS §6.1.1, §6.1.4](../../requirements/SRS.md), [STD TC-DVE-06, 17..19](../../test/STD.md), [UXD §4](../UXD.md)
* Related: ADR-0005, ADR-0006, ADR-0007, ADR-0011, ADR-0016, ADR-0019
* Revisit if formal qualification boards mandate unattended server-side `.pdf` generation without a browser (evaluating pure-Python `fpdf2` wheel packaging).
