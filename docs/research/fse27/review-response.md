# Middleware '26 Industry #71 → FSE 2027 Industry: response to reviews

Middleware '26 Industry rejected the earlier version (two Weak Rejects). This file maps every point
in Reviews A and B to the change in [`paper.tex`](paper.tex). FSE reviewers will not see it; it is
our checklist. Status: **text done** = the change is written; **needs data** = the text and table
are in place, but the numbers come from [`experiment-protocol.md`](experiment-protocol.md).

## The shared core objection

Both reviewers said the paper shows the gate is cheap, not that it catches anything. Reviewer A:
"does not establish verification effectiveness", and suggested controlled fault injection. Reviewer
B: "zero detection evidence … more of a position paper".

| Change | Where | Status |
|---|---|---|
| RQ1–RQ4 stated in the introduction; the paper is now organized around them | §1 | text done |
| Fault injection: 12 faulty + 7 benign operators, 200 mutants each, Wilson CIs, located-detection scoring, gate-decision accuracy, severity agreement | §4.2, Tables 4–5 | needs data (`rq1_mutants.csv`) |
| Independent oracle for QoS operators: the middleware's own incompatible-QoS status and matching | §4.2 | needs data (`rq1_oracle.csv`) |
| Fielded baseline (Platform R), two-architect triage with κ, TP/FP classes, delta vs. absolute gating replay | §4.3, §5.3, Table 6 | needs data (`rq2_*.csv`) |
| Historical defect replay with a selection rule fixed before running the gate | §4.4, §5.4, Table 7 | needs data (`rq3_replay.csv`) |
| Old Table 5 ("illustrative scenarios", no measurements) removed; its scenarios became operators M1, M3, M6, M8, M10 | §4.2 | text done |

## Review A

| Point | Change | Where | Status |
|---|---|---|---|
| Dense, too many domain terms and acronyms | Dropped Link 11/22, NEC, STANAG 4586, CIC, WASA, VME/VPX. Each remaining term (CMS, DDS, QoS, RxO, ICD, HAT/SAT) is defined where it first appears. Plain-language list of the four fault classes in §1 | §1, §2 | text done |
| Needs a worked example: configuration → graph → result | New Figure 1 and §2.3: descriptor → structural graph → DEPENDS_ON → S1 RxO violation → exit 1 | §2.3, Fig. 1 | text done |
| A one-paragraph DDS primer was missing | §2.1 explains request/offered matching and why the failure is silent | §2.1 | text done |
| Unclear what is new beyond [8] | Table 2 splits inherited vs. new; contribution 1 points to it | §1, §3.1, Table 2 | text done, **confirm** (`TODOcheck`) |
| Criticality weights and severity rubric: contribution not shown | Weights now have one stated role (triage order within a severity); sensitivity analysis measures their effect on severity, gate decisions and triage order | §3.1, §3.3, §5.6 | needs data (`sens_weights.csv`), **confirm D2** |
| Intended vs. implemented blurred | Rules table lists only implemented rules, stated at their real granularity; specified-only capabilities appear only in the gap table, now with a "measured consequence" column fed by M10–M12 and RQ3 | §3.2, Table 3, Table 10 | text done; numbers need data |
| Fault injection on generated configurations would still give evidence | Done: RQ1 | §4.2, §5.2 | needs data |
| Data-access barriers are the most valuable part, but need concrete evidence of effort, obstacles and consequences | §6 rewritten: three kinds of silo, effort table (sources, formats, lead times, conflicts, person-weeks), defects found by curation, organizational obstacles, recommendations tied to the numbers | §6, Table 9 | needs data (`lessons_effort.csv`) |
| Refactoring and defect-prevention benefits have no achieved outcomes | Diagnostic-mode outcomes on Platform R (only actions actually taken); RQ3 gives defect-prevention evidence | §5.3, §5.4 | needs data (`rq2_diagnostic_outcomes.csv`, `rq3_replay.csv`) |

## Review B

| Point | Change | Where | Status |
|---|---|---|---|
| No TP/FP rates or defects caught | RQ1 (TP/FP per operator), RQ2 (precision on a real baseline), RQ3 (historical catches) | §5 | needs data |
| Latencies come from generated topologies on one machine | Kept and labeled generated; Platform R latency added; 30-min pipeline figure gets its n and window | §5.5, Table 8 | needs data (`rq4_latency.csv`) |
| Weights uncalibrated, no sensitivity analysis | §5.6 sensitivity (±10/20 % one-at-a-time + 200 joint perturbations) | §5.6 | needs data |
| QoS score omits DEADLINE, LATENCY_BUDGET, LIVELINESS | The QoS *score* formula is gone from the paper (it only ordered triage). The RxO *rule* is the real issue: protocol decision D1 extends it to the full DDS RxO set if descriptors carry those fields; operators M4/M5 measure it either way | §3.2, Table 4 | **decide D1** |
| Abstract dramatizes S1 cases only partly covered | Abstract now names only implemented checks; its S1 example (durability RxO mismatch) is implemented and measured by M1 | Abstract | text done |
| No artifact or reproducibility statement | Data Availability section; `clearance.md` records what can be released (aim: generator parameters, mutation catalog, synthetic profiles and mutants) | end of paper | needs clearance |
| Heavy formalism not exercised by any result | Removed the topic-weight equation, the per-entity weight table, the QoS factor footnote, and the library/node weight formulas. Kept only what a result uses: entity/edge types and the DEPENDS_ON rules (used by the cycle rule and diagnostic mode) | §3.1 | text done |
| Minor: brackets in title suffix | Title has no track suffix (FSE does not ask for one) and was shortened | title | text done |

## Also changed

- Related work: added ROSDiscover (closest prior work — static recovery of ROS run-time architecture
  and rule checking), HAROS, PCheck, ctest, AADL, ArchUnit and OPA Gatekeeper with real citations;
  positioned SaaG against ROSDiscover explicitly.
- Threats to validity is now its own section.
- Template switched to FSE's `sigconf,screen` with the companion-proceedings booktitle;
  bibliography style ACM-Reference-Format.
- Earlier phrasing implied more than was built ("digital model … operational prototype",
  "6 of 7 blocked" as the headline result). The headline is now measured effectiveness; the data
  bottleneck is the lesson.

## Before submission

1. Fill every `data/*.csv` and `clearance.md`; replace each `\TODOdata{}` and `\tbd` in `paper.tex`
   (`make todo` lists them).
2. Resolve every `\TODOcheck{}`: D1, D2, how the per-topic RxO comparison aggregates, the Table 2
   split against the RASSE'25 paper, and the CCS concept ids.
3. Remove the three marker macros, rebuild, confirm ≤ 10 pages of body plus ≤ 2 of references
   (`make pages`).
4. Decide on single vs. double anonymous (FSE Industry allows either; the industrial context argues
   for keeping names).
