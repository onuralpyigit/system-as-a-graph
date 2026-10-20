# Backlog Plan (Releases / Epics / User Stories): System as a Graph (SaaG)

**Purpose:** This document (1) records a critical evaluation of the Software Development Plan (`SDP.tr.md` / `SDP.md`) with respect to CSCI/CSC/CSU traceability and logical consistency, and (2) derives a hierarchical backlog — **Releases → Epics → User Stories** — from the evaluated structure. Every story traces to SRS requirement IDs; every epic maps to exactly one SDP WBS deliverable; every release maps 1:1 to an SDP increment.

**Canonical ID decision (from evaluation Finding T1):** all traceability in this document uses the **SRS.md English IDs** — `MDG / SCG / FDM / ADM / SMM / DVE` (+ `FDM-INF.1`). See Appendix A for the bilingual mapping and the required cross-document renames.

---

## 0. Evaluation of the SDP (CSCI / CSC / CSU traceability and consistency)

### 0.1 What holds up

- **Arithmetic completeness.** The union of all WBS leaf requirement ranges covers every functional requirement exactly once: MDG 1–23, SCG 1–7, FDM 1–5, ADM {1,3,4,6}∪{2,5}, SMM 1–31 ∪ 32–37, DVE: {1–8, 9+19–20, 17–18+21–24, 11+13–15, 10+12+16, 25, 26–27, 28–49, 50–70, 71–78} = 1–78 with **no gaps and no overlaps**. 23+7+5+6+37+78 = 156 matches SRS Table 1.
- **Deliverable count.** Table 1 (1+1+1+2+2+10 = 17) matches the leaf count of the WBS tree.
- **Dependency-safe ordering.** Each DVE UI slice ships in the same increment as (or after) the backend slice it operates on; behavioral analysis (Inc 6) follows both data pipelines (Inc 4/5); installation evaluation (Inc 7) follows verification, analysis and concurrency (Inc 3/6/2). No backward dependency exists, except reporting (DVE.26), which is deliberately deferred to Inc 7 and acknowledged in the Inc 7 DoD ("Artım 3/6/7'den gelen raporlama testi").
- **Schedule arithmetic.** 8 strictly serial increments, 2+4+5+5+4+4+6+4 = 34 working weeks, back-to-back business-week boundaries from 2026-07-20 to 2027-03-12; Gantt bars, Table 3 and §3 text agree.

> **Re-baseline note (2026-10-20):** the SDP was re-baselined to **2026-07-06 → 2028-06-30** (104 business weeks): functional increments re-sized to 7–13 weeks (66 wk) plus three new closing increments — R8 Hardening (16 wk), R9 Pilot (14 wk), R10 Acceptance (8 wk). Requirement scope (157) and the deliverable/epic structure are unchanged; schedule findings above refer to the original 34-week baseline.
- **Increment ↔ CSC completion consistency.** "Tamamlanan CSC'ler" is recorded exactly in the increment that delivers a CSC's last slice (MDG→1, SCG→4, FDM/ADM/SMM→5, DVE→7).

### 0.2 Traceability findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| T1 | **Critical** | **Component-abbreviation collision across documents.** `TDM` means *Design Verification Engine* in SDP.tr (and SRS.tr) but *Telemetry Data Manager* (= FDM) in SDD/STD/CDR. Any citation "TDM.n" is ambiguous across the document set: SDP Inc 5's CDR list (CDR-15/-21/-26/-27) points at field-data interfaces, where `TDM` in SDD = FDM, while SDP's own "TDM.10, 12, 16" = DVE. | SDP.tr §2 Inc 5 ↔ SDD §2.3 EXT-IF-05 "TDM.2", INT-IF-03 "TDM → ADM" ↔ STD Table 1 "Telemetry Data Manager SaaG-TDM" |
| T2 | **Critical** | **CDR/STD forward traces cite non-existent requirement IDs.** CDR-09/-10 cite `SRS MSG.6/.19`, CDR-15 cites `SRS TDM-INF.1`, CDR-16 cites `SRS CSM.30`; SRS.md defines MDG.x, FDM-INF.1, SMM.30. Domain vocabulary is also silently renamed: "Model Data" (SRS) → "Model Setup Data" (SDD/STD), "System Model" → "Core System Model", "Model Data Generator" → "Model Setup Generator". | CDR.md §1.2–1.4 ↔ SRS.md §1, §3.2, §5.1; STD.md Table 1 |
| T3 | **Major** | **Repository diverges from SDP §4 and from every document.** Actual dirs: `mdg/`, `dve/`, `dev/`; SDP §4 specifies `msd/ scg/ frd/ adp/ csm/ vae/`; CSU IDs are MVU/SUR/SVY/AVY/SMY/TDM (tr) or MDG/SCG/FDM/ADM/SMM/DVE (en). Half-finished rename leaks into code (`mdg/tests/test_msd.py`). No document owns the CSC→directory mapping. | `ls` of repo root; SDP.tr §4 |
| T4 | **Major** | **Infrastructure requirement FDM-INF.1 is untracked in the WBS.** The SVY leaf cites "SVY.1–5" only; SDP Table 1 counts FDM as 1 deliverable and 6 total CSUs. The constraint is reachable only via prose (Inc 5 Design mentions CDR-15). SDP therefore delivers traceability for 156/157 SRS entries. | SDP.tr §1 tree line for SVY; SRS.md §3.2 |
| T5 | **Minor** | **Sloppy requirement citations in SDP §5:** bare component "TDM" used where a requirement ID is expected ("Refine … (TDM, TDM.3)"); redundant "TDM.28–78, TDM.78". Also DVE.2 ("interact with MDG, SCG, ADM, SMM") is counted as done in Increment 1 (slice 1–8), but full realization spans Inc 2–5 — slice coverage ≠ requirement satisfaction; it needs a "satisfied-in" date distinct from "covered-in". | SDP.tr Table 6; SRS.md DVE.2 vs. Inc 1 table |

### 0.3 Logical-consistency findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| L1 | **Major** | **WBS level semantics are mixed; "CSU" and "Deliverable" are conflated.** The SRS mandates a strict 1:1 CSC↔CSU mapping (6 CSC / 6 CSU). In the SDP WBS, a third-level leaf is a *CSU* under MVU/SCG/FDM but a *slice of the single CSU* under ADM/SMM/DVE. Table 2's column "Teslim Edilen CSU'lar" lists slices ("SMY (yapısal dilim)"), and §2 prose says increments deliver "CSC'nin kalan CSU'larını" — under the 1:1 model a CSU cannot be delivered piecemeal. Real traceability exists at requirement-ID level only; the CSU-level claim in the intro is therefore overstated. | SRS.md preamble vs. SDP.tr §1/§2 |
| L2 | **Major** | **SDP §5 pre-decides what the CDR register still leaves open.** Tech stack fixes graph DB / relational / TSDB (vs CDR-29/-30 *Open*), LDAP bind + JWT (CDR-22), REST/CLI protocol (CDR-23), PDF/JSON report format (CDR-13) — while the increments' DoDs require those same CDRs to be "resolved or deferred". Either the CDR register is stale or §5 is unsourced; the documents contradict each other. | SDP.tr Table 6 vs. CDR.md §1.4–1.6 |
| L3 | **Minor** | **Name drift for the same increment/component:** Inc 2 is "Yapısal Model İnşası" (§2/Table 2) but "Model Yöneticisi" (Table 3); Inc 3/6/7 are renamed to SDD engine element names ("Tasarım Doğrulayıcı / Analizcisi / Değerlendiricisi"); the DVE CSC is variously "Tasarım Doğrulama Motoru", "Doğrulama, Analiz, Değerlendirme", "CSC-6: Tasarım Doğrulama, Analiz ve Değerlendirme". | SDP.tr §2 vs §3 tables vs Gantt section titles |
| L4 | **Minor** | **Mixed duration units in the Gantt ("hf" weeks vs "g" days)** invites miscalculation; Increment 5 ends on 2027-01-01 (a public holiday). | SDP.tr Şekil 1 |
| L5 | **Risk (called out by the plan itself)** | **CDR closure is scheduled too late.** CDR-01–08 (all pass/fail rule sets) are gated inside Inc 3's DoD, forcing the six verifier engines to be built on "geçici kurallar" with promised rework; CDR-12 (AED format) is needed by both Inc 4 and Inc 5; CDR-29/-30 (storage/schema) gate the Inc 2 graph DB but close only within Inc 2. Decision items with stakeholder lead time should be pulled **at least one release ahead** of the increment that consumes them. | SDP.tr Inc 2/3/4 Design + DoDs |

### 0.4 Required corrections (feed into the backlog)

1. Declare SRS.md IDs canonical; rename SDD/STD/CDR (`MSG→MDG`, `TDM→FDM`, `CSM→SMM`, restore "Model Data"/"System Model" terms) — backlog work item R0-E0.2.
2. Introduce a formal fourth WBS tier **"Deliverable" (D-01…D-17)** below CSU; stop calling slices CSUs in Table 2. Deliverable IDs are used as Epic IDs below.
3. Add `FDM-INF.1` to the D-03 (FDM) scope.
4. Reconcile SDP §5 vs CDR-13/-22/-23/-29/-30 (mark resolved with the §5 decision as the rationale, or delete from §5).
5. Move CDR closure gates one release ahead (see §2 table "Decision lane").
6. Align repo dirs to canonical CSC IDs (`mdg/ scg/ fdm/ adm/ smm/ dve/ web/ cli/`) and fix `test_msd.py`.

---

## 1. Decomposition model

| Backlog tier | Maps to | Cardinality | ID scheme |
|---|---|---|---|
| **Release** | SDP increment (§2), incl. R0 skeleton + R8–R10 closing increments | 11 releases, strictly serial, dates from Table 3 | `R0…R10` |
| **Epic** | WBS deliverable (fixed by 0.4/2) or a decision-lane group | 19 deliverable epics (D-01…D-17, D-16 split a/b/c) + 1 foundation + 7 decision/closure + 1 reconciliation | `E<release>.<n>`, cites `D-01…D-17` |
| **User Story** | INVEST-sized cluster of 1–5 requirements, same interface/domain | 106 stories (95 traced in R0–R7 + 11 closeout in R8–R10) | `S<epic>-<nn>` |

- **Roles:** `Operator` (web panel user), `Automation Client` (Jenkins/CI via CLI), `Platform Team`, `CDR Board / Security`, `QA`.
- **Release DoD** = SDP §2 DoD: every story's requirements pass; cited CDRs Resolved/Deferred; packaging + demo green.
- **Coverage claim:** the 100 stories trace to all **156 functional + 1 infrastructure** requirements, each requirement owned by exactly one story (see §3 matrix).

### Deliverable register (D-01…D-17)

| ID | Deliverable (Epic scope) | CSU | Requirement IDs | Release |
|---|---|---|---|---|
| D-01 | Model Data Generation | MDG | MDG.1–23 | R1 |
| D-02 | Scenario Generator | SCG | SCG.1–7 | R4 |
| D-03 | Field Data Manager | FDM | FDM.1–5, **FDM-INF.1** | R5 |
| D-04 | Analytical Data Prep — Synthetic | ADM | ADM.1, 3, 4, 6 | R4 |
| D-05 | Analytical Data Prep — Field | ADM | ADM.2, 5 | R5 |
| D-06 | Structural Model Construction | SMM | SMM.1–31 | R2 |
| D-07 | Analytical Data Binding | SMM | SMM.32–37 | R5 |
| D-08 | Login & Model Data Setup (UI) | DVE | DVE.1–8 | R1 |
| D-09 | Model Build & View (UI) | DVE | DVE.9, 19–20 | R2 |
| D-10 | Model Editor & Findings (UI) | DVE | DVE.17–18, 21–24 | R3 |
| D-11 | Synthetic Data Config & Monitor (UI) | DVE | DVE.11, 13–15 | R4 |
| D-12 | Field Data Selection & Monitor (UI) | DVE | DVE.10, 12, 16 | R5 |
| D-13 | Simulation Scenario Recording (UI) | DVE | DVE.25 | R6 |
| D-14 | Reporting & CLI Automation | DVE | DVE.26–27 | R7 |
| D-15 | Structural Design Verification | DVE | DVE.28–49 | R3 |
| D-16 | Behavioral Simulation & Analysis | DVE | DVE.50–70 | R6 |
| D-17 | Installation Suitability Evaluation | DVE | DVE.71–78 | R7 |

---

## 2. Decision lane (CDR closure, pulled ≥1 release ahead)

| CDRs | Decision | Currently gated at | Close by |
|---|---|---|---|
| CDR-17–20, 22, 24 | EXT/INT protocols for R1 data sources, LDAP, MDG→SMM | R1 DoD | R0 |
| CDR-09, 10 | Topology acquisition source/method; mandatory file list | R1 DoD | R0 |
| CDR-29, 30, 16, 28 | Storage tech/schemas; concurrency limits; SMM→DVE read protocol | R2 DoD | R1 |
| CDR-01–08 | All verification rule sets & classification metrics | R3 DoD | R2 |
| CDR-11, 12, 25 | Simulation definition; **AED format (feeds R4+R5)**; SCG→ADM | R4 DoD | R3 |
| CDR-15, 21, 26, 27 | Telemetry capacity; field source protocol; handoffs | R5 DoD | R4 |
| CDR-13, 14, 23 | Report format; scoring; CLI/result format | R7 DoD | R6 |

---

## 3. Releases, Epics, Stories

Size: S ≤ 2 days, M ≤ 4 days, L ≤ 8 days (one increment = 3–6 weeks). "Traces" = SRS.md requirement IDs; each requirement appears exactly once overall.

### R0 — Project Skeleton (2026-07-06 → 2026-07-17, 2 wk)
**Goal:** repo + shared infrastructure + docs skeleton. **Demo:** clean checkout builds, lints, boots Compose stack; docs placeholders present.

| Epic | Scope | Traces |
|---|---|---|
| E0.1 Foundation (no SRS trace) | SDP Inc 0 | — |
| E0.2 Naming reconciliation (fix T1–T3, L3) | canonical IDs, CDR/SDD/STD renames, dir alignment | fixes 0.4/1,6 |

| Story | Title | Size |
|---|---|---|
| S0.1-01 | As a developer, I get the repo skeleton (hexagonal layout per CSC, `web/`, `cli/`, `shared/`) so every later story lands in a fixed place | M |
| S0.1-02 | As a developer, I get `shared/` contracts/types/errors/security scaffolding so CSCs share one error and security model | M |
| S0.1-03 | As a platform team, I get a Docker Compose base stack with placeholder services and an env/secrets template | M |
| S0.1-04 | As a QA, I get CI (build, lint, unit-test gates) and the `docs/` skeleton | S |
| S0.2-01 | As a maintainer, I get SRS.md IDs applied everywhere (SDD/STD/CDR renames, repo dirs `mdg/ scg/ fdm/ adm/ smm/ dve/`, `test_msd.py` fix) so all cross-document traces resolve | L |
| S0.2-02 | As the CDR board, I get the decision-log workflow + pre-scheduled decision lane (§2) | S |

### R1 — Model Data Generation (2026-07-20 → 2026-09-04, 7 wk) — completes SaaG-MDG
**Demo (SDP Inc 1):** LDAP login → pick project/platform/version → configure 4 sources → run MVU production → validated Model Data file.

| Epic | Deliverable | Traces |
|---|---|---|
| E1.1 Model Data Generator backend | D-01 | MDG.1–23 |
| E1.2 Login & Model Data Setup (web) | D-08 | DVE.1–8 |
| E1.3 Decision gate: CDR-09/10, 17–20, 22, 24 | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S1.1-01 | As an operator, I define/save per-source config (type, name, access method, address, credentials) | MDG.8 | M |
| S1.1-02 | As an operator, I acquire project/platform/version from the CMDB with the effective version marked and faults marked error-status | MDG.2, 9–13, 16 | L |
| S1.1-03 | As an operator, I pull sources/scripts/config files from the source repo with per-file metadata, missing-file and access/auth/integrity error states | MDG.3, 17–20 | L |
| S1.1-04 | As an operator, I pull package metadata from the Software Units Package Repository | MDG.4 | M |
| S1.1-05 | As an operator, I obtain network topology automatically or by manual entry | MDG.5–7 | M |
| S1.1-06 | As an operator, I record the Software Unit Version Inventory and append a candidate version for evaluation | MDG.14–15 | M |
| S1.1-07 | As the system, I validate mandatory fields, record failures with full attribution, and assemble the Model Data file for handoff | MDG.1, 21–23 | L |
| S1.2-01 | As an operator, I authenticate via LDAP and get a JWT session scoped to my authorization | DVE.1–3 | M |
| S1.2-02 | As an operator, I select project/platform/version and see the effective version distinctly marked | DVE.4 | S |
| S1.2-03 | As an operator, I list and select Model Data files for the selected scope | DVE.5 | S |
| S1.2-04 | As an operator, I start Model Data production and watch in-progress/success/failure status | DVE.6 | M |
| S1.2-05 | As an operator, I see continuous accessibility status of all data sources | DVE.7 | M |
| S1.2-06 | As an operator, I see missing-data/access/auth/format/integrity errors from production | DVE.8 | S |
| S1.3-01 | Decision: EXT-IF-01…04/06 + INT-IF-01 protocols; topology method; mandatory file list (CDR pulled from R0) | — | M |

*(DVE.2 "interact with MDG/SCG/ADM/SMM" is marked partially satisfied here; satisfied-in = R5 — finding T5.)*

### R2 — Structural Model Construction (2026-09-07 → 2026-11-06, 9 wk)
**Demo (SDP Inc 2):** build model from the R1 Model Data file; navigate the graph under concurrent multi-session access.

| Epic | Deliverable | Traces |
|---|---|---|
| E2.1 Structural Model Construction | D-06 | SMM.1–31 |
| E2.2 Model Build & View (web) | D-09 | DVE.9, 19–20 |
| E2.3 Decision gate: CDR-29/30, 16, 28 (+ CDR-01–08 start) | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S2.1-01 | As the system, I accept and validate (format/schema/integrity/mandatory) the Model Data input | SMM.1–3 | M |
| S2.1-02 | As the system, I convert validated data into the node-relationship System Model bound to project/platform/version | SMM.4–5 | L |
| S2.1-03 | As the system, I represent System/Software Segment/CSCI/CSC/CSU/Role nodes | SMM.6–11 | M |
| S2.1-04 | As the system, I represent Topic/Message/Console/Processor/Network/Middleware/CommTech nodes | SMM.12–17 | M |
| S2.1-05 | As the system, I represent running-on / using-services / publishing / consuming / dependency / role-assignment relationships | SMM.18–23 | M |
| S2.1-06 | As the system, I expose CPU/OS/runtime settings as queryable attributes | SMM.24 | M |
| S2.1-07 | As an operator, I get build-time missing-entity/invalid-relationship errors and full model metadata (file, time, scope, status) recorded | SMM.25–26 | S |
| S2.1-08 | As DVE, I read nodes/relationships/bound data via the agreed read-only protocol | SMM.27–28 | L |
| S2.1-09 | As the system, I keep integrity/consistency under concurrent multi-session read/write | SMM.29 | L |
| S2.1-10 | As the pipeline, I get process-specific isolated model copies (incl. candidate-version copy) executed concurrently and independently | SMM.30–31 | L |
| S2.2-01 | As an operator, I start model build and see success/failure result | DVE.9 | S |
| S2.2-02 | As an operator, I search entities/relationships and filter by type/project/platform/version/unit | DVE.19 | M |
| S2.2-03 | As an operator, I zoom/pan/select and view node & relationship attributes | DVE.20 | M |
| S2.3-01 | Decision: storage tech + 7-store schemas, concurrency counts, SMM→DVE protocol (from R1) | — | L |
| S2.3-02 | Decision: verification rule sets CDR-01–08 (for R3) | — | L |

### R3 — Structural Design Verification (2026-11-09 → 2027-01-22, 11 wk)
**Demo (SDP Inc 3):** edit a sandbox working model, run the six check engines, inspect classified findings.

| Epic | Deliverable | Traces |
|---|---|---|
| E3.1 Verification engines | D-15 | DVE.28–49 |
| E3.2 Working-model editor & findings (web) | D-10 | DVE.17–18, 21–24 |
| E3.3 Decision gate: CDR-11/12/25 (for R4/R5) | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S3.1-01 | As the system, I run verification operations on the model without altering it | DVE.28–29 | M |
| S3.1-02 | As the system, I run model-only analyses with no Analytical Evaluation Data | DVE.30–31 | M |
| S3.1-03 | As an architect, I detect topic QoS (Durability/Reliability/Lifespan/Transport-Priority) non-conformances per CDR-01 rules | DVE.32–35 | L |
| S3.1-04 | As an architect, I detect publisher/consumer mismatches: no publisher, no consumer, same-name different-content topics | DVE.36–38 | M |
| S3.1-05 | As an architect, I verify external↔middleware source/destination/message/direction consistency | DVE.39 | M |
| S3.1-06 | As an architect, I detect load-balancing, core-allocation (over-commit/conflict/dedicated-core), OS-settings and runtime-memory non-conformances and contention/bottlenecks | DVE.40–46 | L |
| S3.1-07 | As an architect, I detect circular dependencies, broken/missing/unmatched relationships, and architectural-rule pattern violations | DVE.47–49 | M |
| S3.2-01 | As an operator, I edit a derived working model in a sandbox (add/remove nodes/relationships, update attributes) without breaking integrity or touching the real model | DVE.17 | L |
| S3.2-02 | As the system, I classify results conforming/non-conforming per CDR-08 metrics | DVE.18 | M |
| S3.2-03 | As an operator, I see each finding with id, type, description, affected entity, rule/criterion, evidence, severity | DVE.21 | M |
| S3.2-04 | As an operator, I see cause-effect links between related findings of one operation | DVE.22 | M |
| S3.2-05 | As an operator, I sort/filter findings by operation, result, type, severity, scope, affected node | DVE.23 | M |
| S3.2-06 | As the system, I record error cause/stage/time for any interrupted operation | DVE.24 | S |

### R4 — Synthetic Data Pipeline (2027-01-25 → 2027-03-12, 7 wk) — completes SaaG-SCG
**Demo (SDP Inc 4):** define scenario inputs → produce traceable synthetic data → prepare AED → monitor production.

| Epic | Deliverable | Traces |
|---|---|---|
| E4.1 Scenario Generator | D-02 | SCG.1–7 |
| E4.2 ADM synthetic prep | D-04 | ADM.1, 3, 4, 6 |
| E4.3 Synthetic data UI | D-11 | DVE.11, 13–15 |
| E4.4 Decision gate: CDR-15/21/26/27 (for R5) | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S4.1-01 | As an operator, I define scope, type, time interval, density, data types | SCG.3 | M |
| S4.1-02 | As the system, I produce schema-conformant synthetic data without field records | SCG.1, 4 | L |
| S4.1-03 | As the system, I record synthetic data with scenario name/time/scope and traceable inputs | SCG.5–6 | M |
| S4.1-04 | As the system, I feed the defined simulation processes (contract per CDR-11) | SCG.2 | S |
| S4.1-05 | As ADM, I receive synthetic data per the INT-IF-02 handoff | SCG.7 | M |
| S4.2-01 | As ADM, I ingest synthetic data from SCG | ADM.3 | M |
| S4.2-02 | As the system, I prepare controlled, traceable Analytical Evaluation Data per the CDR-12 format and transfer it toward the model | ADM.1, 4 | L |
| S4.2-03 | As an operator, I get format/unreadable/missing-field errors on synthetic inputs | ADM.6 | S |
| S4.3-01 | As an operator, I choose synthetic data as the AED source | DVE.11 | S |
| S4.3-02 | As an operator, I enter scenario inputs in the panel | DVE.13 | S |
| S4.3-03 | As an operator, I start/track synthetic-data and AED production with error visibility | DVE.14–15 | M |

### R5 — Field Data Pipeline (2027-03-15 → 2027-05-14, 9 wk) — completes SaaG-FDM, SaaG-ADM, SaaG-SMM
**Demo (SDP Inc 5):** bind synthetic AED without touching model; upload field records; bind field AED independently.

| Epic | Deliverable | Traces |
|---|---|---|
| E5.1 Field Data Manager | D-03 | FDM.1–5, FDM-INF.1 |
| E5.2 ADM field prep | D-05 | ADM.2, 5 |
| E5.3 Analytical Data Binding | D-07 | SMM.32–37 |
| E5.4 Field data UI | D-12 | DVE.10, 12, 16 |
| E5.5 Decision gate: CDR-13/14/23 (start for R6/R7) | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S5.1-01 | As the system, I centrally store and manage System Field Records from the recording mechanism | FDM.1 | M |
| S5.1-02 | As an operator, I upload telemetry/records with controlled traceability bound to project/platform/version | FDM.2 | M |
| S5.1-03 | As the system, I record provenance (source, upload time, scope) per record | FDM.3 | S |
| S5.1-04 | As an operator, I list/search/select records by project, platform, version, source, upload time | FDM.4 | M |
| S5.1-05 | As an operator, I get format/integrity/missing-field errors on upload | FDM.5 | S |
| S5.1-06 | As the platform team, I provision disk sizing per the CDR-15 decision and the infra constraint | FDM-INF.1 | S |
| S5.2-01 | As ADM, I obtain System Field Records from FDM | ADM.2 | M |
| S5.2-02 | As an operator, I get format/unreadable errors on field records | ADM.5 | S |
| S5.3-01 | As the system, I accept AED and match records/telemetry/synthetic data to nodes and relationships, bound to scope | SMM.32–34 | L |
| S5.3-02 | As the system, I preserve synthetic-vs-field provenance of bound data | SMM.35 | S |
| S5.3-03 | As the system, I bind without altering nodes/relationships and keep the layers separable | SMM.36 | L |
| S5.3-04 | As an operator, I get reports of AED records with no model counterpart | SMM.37 | M |
| S5.4-01 | As an operator, I choose System Field Records as the AED source | DVE.10 | S |
| S5.4-02 | As an operator, I select which records to use | DVE.12 | S |
| S5.4-03 | As an operator, I see bound-data scope and matching status per node/relationship | DVE.16 | M |

### R6 — Behavioral Design Analysis (2027-05-17 → 2027-08-13, 13 wk)
**Demo (SDP Inc 6):** static analysis over synthetic and field AED; drift detection; scenario metadata recorded.

| Epic | Deliverable | Traces |
|---|---|---|
| E6.1 Synthetic analysis engines | D-16a | DVE.50–58 |
| E6.2 Field analysis engines | D-16b | DVE.59–65, 69–70 |
| E6.3 Drift detection | D-16c | DVE.66–68 |
| E6.4 Scenario recording (web) | D-13 | DVE.25 |
| E6.5 Decision gate: CDR-13/14/23 closure; verify CDR-28/29/30 carried | — | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S6.1-01 | As the system, I run static analysis without altering model nodes/relationships | DVE.50–51 | M |
| S6.1-02 | As an analyst, I analyze synthetic message flow direction/count/volume/frequency and node/relationship inactivity effects | DVE.52–54 | L |
| S6.1-03 | As an analyst, I run traffic analysis for topic/message density increase and publish/consume behavior changes | DVE.55–56 | L |
| S6.1-04 | As an analyst, I trace fault/load/bandwidth propagation paths and affected nodes/relationships | DVE.57 | L |
| S6.1-05 | As an analyst, I see top-resource/most-messaging summary indicators from simulation | DVE.58 | M |
| S6.2-01 | As an analyst, I analyze field-based operational/health status and CPU/memory/storage/network usage | DVE.59–61 | L |
| S6.2-02 | As an analyst, I analyze field error/warning/restart/timeout records | DVE.62 | M |
| S6.2-03 | As an analyst, I analyze field message flow, publish/consume activity, latency/loss/success rates | DVE.63–65 | L |
| S6.2-04 | As an analyst, I analyze bound event records and see field-based top-usage indicators | DVE.69–70 | M |
| S6.3-01 | As an analyst, I detect architectural drift: model-only, runtime-only, and mismatched entities/relationships | DVE.66–68 | L |
| S6.4-01 | As the system, I record simulation scenario name/inputs/production time/scope with results | DVE.25 | M |

### R7 — Installation Suitability Evaluation (2027-08-16 → 2027-10-08, 8 wk) — completes SaaG-DVE
**Demo (SDP Inc 7):** Jenkins calls CLI → per-unit scored, concurrency-safe evaluation with blocking-decision and machine-readable results → consolidated report.

| Epic | Deliverable | Traces |
|---|---|---|
| E7.1 Installation Suitability Evaluation | D-17 | DVE.71–78 |
| E7.2 Reporting & CLI | D-14 | DVE.26–27 |
| E7.3 Release closure (full-stack acceptance) | — | regression of R1–R6 |

| Story | Title | Traces | Size |
|---|---|---|---|
| S7.1-01 | As the system, I run installation-suitability evaluations on the model with a rule model (rule id, heading, severity, weight, acceptance criterion, blocking status) scored per CDR-14 | DVE.71, 76 | L |
| S7.1-02 | As the system, I score structural/architectural conformance of a candidate unit | DVE.72 | M |
| S7.1-03 | As the system, I score interface/topic/communication conformance | DVE.73 | M |
| S7.1-04 | As the system, I score dependency/integration conformance | DVE.74 | M |
| S7.1-05 | As the system, I score resource/performance sufficiency | DVE.75 | M |
| S7.1-06 | As the pipeline, I receive a "non-conforming" blocking decision on critical findings, independent of total score | DVE.77 | M |
| S7.1-07 | As an automation client, I run multi-candidate evaluations concurrently with independent operation ids and machine-processable per-unit + aggregate results | DVE.78 | L |
| S7.2-01 | As an automation client, I start/query evaluations via CLI/build-tool integration with status streaming and concurrent independence | DVE.27 | L |
| S7.2-02 | As an operator, I export summary/detailed reports (per CDR-13 format) covering all verification/analysis/evaluation results with mandatory content | DVE.26 | L |
| S7.3-01 | As QA, I run the full-stack acceptance demo across all six CSCs | — | L |

### R8 — Integration Hardening & Capacity Verification (2027-10-11 → 2028-01-28, 16 wk)
**Goal:** full-stack stabilization at CDR-15/16 targets. No new requirement traces. **Demo:** 72-hour soak under concurrent multi-session load.

| Epic | Scope | Traces |
|---|---|---|
| E8.1 Full-stack hardening (no SRS trace) | SDP Inc 8 | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S8.1-01 | As QA, I pass the complete STD regression suite on the full stack | — | L |
| S8.1-02 | As the platform team, I pass load/capacity tests at the CDR-15/16 targets | — | L |
| S8.1-03 | As the security owner, I pass the LDAP/JWT/authorization-matrix audit | — | M |
| S8.1-04 | As ops, I run a 72-hour soak plus approved defect burn-down | — | L |

### R9 — Pilot Operations, Training & Documentation (2028-01-31 → 2028-05-05, 14 wk)
**Goal:** institutional pilot without team support; enablement complete. No new requirement traces. **Demo:** pilot operators run end-to-end flows unassisted.

| Epic | Scope | Traces |
|---|---|---|
| E9.1 Pilot & enablement (no SRS trace) | SDP Inc 9 | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S9.1-01 | As a pilot operator, I run the full workflow suite unassisted | — | L |
| S9.1-02 | As UX, I burn down pilot feedback with full regression on each change | — | L |
| S9.1-03 | As the team, we publish user manual, runbooks, and training materials | — | M |
| S9.1-04 | As an operator, I validate CDR-13 report output on real institutional data | — | M |

### R10 — Acceptance & Production Handover (2028-05-08 → 2028-06-30, 8 wk) — accepts the CSCI
**Goal:** formal CSCI acceptance and production handover; document baseline frozen. **Demo:** acceptance run of all six CSCs (per-increment demos re-performed).

| Epic | Scope | Traces |
|---|---|---|
| E10.1 Acceptance & handover (no SRS trace) | SDP Inc 10 | — |

| Story | Title | Traces | Size |
|---|---|---|---|
| S10.1-01 | As the acceptance board, I see the six-CSC acceptance run pass | — | L |
| S10.1-02 | As the CDR board, I close every register item (Resolved/Deferred) and freeze the document baseline | — | M |
| S10.1-03 | As ops, I receive the production handover with a rollback drill and closeout report | — | M |

---

## 4. Requirement → Release matrix (coverage proof)

| CSU | Range | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
|---|---|---|---|---|---|---|---|---|
| MDG | 1–23 | ●1–23 | | | | | | |
| SCG | 1–7 | | | | ●1–7 | | | |
| FDM | 1–5, INF | | | | | ●1–5, INF.1 | | |
| ADM | 1–6 | | | | ●1,3,4,6 | ●2,5 | | |
| SMM | 1–37 | | ●1–31 | | | ●32–37 | | |
| DVE | 1–78 | ●1–8 | ●9,19–20 | ●17–18,21–24,28–49 | ●11,13–15 | ●10,12,16 | ●25,50–70 | ●26–27,71–78 |

**Totals:** 157/157 requirements (156 functional + FDM-INF.1), each owned by exactly one story. 11 releases · 31 epics (19 deliverable epics covering D-01…D-17 with D-16 split a/b/c, 7 decision/closure, 1 foundation, 1 reconciliation, 3 closing-release) · 106 stories (95 traced + 11 closeout). All traced stories land in R0–R7; closing increments R8–R10 add hardening, pilot, and acceptance work without new requirement traces.

---

## Appendix A — Canonical naming map (decision from finding T1)

| Canonical (SRS.md) | SRS.tr / SDP.tr | SDD/STD/CDR (current) | Repo dir (current) | Action |
|---|---|---|---|---|
| MDG — Model Data Generator | MVU | "MSG — Model Setup Generator" | `mdg/` | rename SDD/STD/CDR → MDG; keep `mdg/` |
| SCG — Scenario Generator | SUR | SCG | (missing) | create `scg/` |
| FDM — Field Data Manager | SVY | "TDM — Telemetry Data Manager" | (missing) | rename → FDM; **eliminate the TDM homonym** |
| ADM — Analytical Data Manager | AVY | ADM | (missing) | create `adm/` |
| SMM — System Model Manager | SMY | "CSM — Core System Model" | (missing) | rename → SMM; restore "System Model" term |
| DVE — Design Verification Engine | TDM | DVE | `dve/` | keep `dve/`; SDP.tr "TDM" stays as TR-only alias |
| Artifacts | Model Data file / System Model | "Model Setup Data" / "Core System Model" | — | restore SRS terms |
