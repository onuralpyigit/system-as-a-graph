# Experiment protocol — FSE 2027 Industry revision of the SaaG paper

Both Middleware '26 reviewers rejected the paper for the same reason: it measured how long the gate
takes, not whether it catches defects. This protocol specifies the evidence the revision needs. The
prototype is internal, so the team runs these experiments on the internal SaaG-P build and fills the
templates in [`data/`](data/). The paper ([`paper.tex`](paper.tex)) already carries a `TODO(data)` slot
for each number; nothing goes into the paper that is not a row in `data/`.

Deadline: **23 Jan 2027 AoE**. Suggested freeze for results: **8 Jan 2027**, which leaves two weeks
for writing.

| RQ | Question | Template(s) | Paper |
|---|---|---|---|
| RQ1 | Does the gate detect injected misconfigurations and accept valid ones? | `rq1_mutants.csv`, `rq1_oracle.csv` | §5.2, Table 5 |
| RQ2 | What does the gate report on a real fielded baseline, and are those findings real? | `rq2_baseline_findings.csv`, `rq2_delta_gating.csv`, `rq2_diagnostic_outcomes.csv` | §5.3, Table 6 |
| RQ3 | Would the gate have caught defects that historically escaped to integration or sea trials? | `rq3_replay.csv` | §5.4, Table 7 |
| RQ4 | What does the gate cost in the pipeline? | `rq4_latency.csv` (existing numbers) | §5.5, Table 8 |
| S | How sensitive are severities and gate decisions to the uncalibrated weights? | `sens_weights.csv` | §5.6 |
| L | What did building the data pipeline cost, and where did it stall? | `lessons_effort.csv`, `clearance.md` | §6, Table 9 |

---

## 0. Freeze the configuration under test

Before any run, record in `data/README.md`:

- SaaG-P commit / build id, Python and NetworkX versions, machine (the latency runs used Ubuntu 22.04,
  AMD EPYC 7763, 32 GB, Python 3.11, NetworkX 3.2).
- The exact rule set that runs, **as implemented** (e.g. "RxO durability + reliability + PARTITION,
  evaluated per topic, not per endpoint pair"). The paper's rules table is written from this list.
- **Decision D1 — extend RxO to the full DDS request/offered set?** The DDS spec makes DEADLINE,
  LATENCY_BUDGET, LIVELINESS, OWNERSHIP and DESTINATION_ORDER request/offered as well. Reviewer B
  flagged their absence. If the descriptors carry these fields, add the comparisons (each is a few
  lines: offered deadline period ≤ requested; offered latency budget ≤ requested; offered liveliness
  kind ≥ requested and lease ≤ requested; ownership kinds equal; offered destination order ≥
  requested) and run the extended rule in RQ1. If the descriptors do not carry them, say so; the
  paper then states the omission once, as a limitation tied to the data gap. Record which.
- **Decision D2 — severity assignment.** Write down the exact procedure that maps a violation to
  S1–S4 (which channel/host attributes, which weight thresholds, any manual table of safety-critical
  channels). §3.3 of the paper is rewritten from this; §5.6 perturbs it.

## 1. RQ1 — Detection effectiveness by controlled fault injection

**Subjects.** The five generated platform profiles already used for latency (Maritime Surveillance
Aircraft, Coastal Surveillance, Unmanned Surface Vehicle, Amphibious Ship, Corvette), × the same 5
generator seeds = 25 baselines.

**Step 1.1 — clean baselines.** Run the gate on each unmutated baseline. A generated baseline should
be violation-free by construction; any finding here is either a generator artifact or a false
positive. Record every finding; fix the generator if it is the generator, and report the rest as
false positives. (Baselines that intentionally carry legacy violations are for RQ2's delta-gating
experiment, not here.)

**Step 1.2 — mutation operators.** Apply exactly one mutation per mutant to a clean baseline. Draw
the mutation site uniformly from eligible sites, stratified so that at least a third of sites lie on
channels the severity table marks safety-critical. Target **n = 40 mutants per operator per profile**
(8 per seed): 200 per operator, which gives a Wilson 95% CI half-width of at most ~7 points at
recall 0.5 and ~2 points at recall 0.98.

Faulty mutants — each has a known expected outcome:

| Op | Fault injected | Expected rule | Expected outcome on SaaG-P |
|---|---|---|---|
| M1 | Writer durability lowered below a reader's request (e.g. VOLATILE vs TRANSIENT_LOCAL) | RxO | detect |
| M2 | Writer reliability BEST_EFFORT vs a RELIABLE reader | RxO | detect |
| M3 | Redundant publisher moved to a different PARTITION than its readers | RxO (PARTITION) | detect |
| M4 | Offered DEADLINE period longer than requested | RxO (extended) | detect if D1 done, else **known miss** |
| M5 | Offered LIVELINESS kind weaker / lease longer than requested | RxO (extended) | detect if D1 done, else **known miss** |
| M6 | Last subscriber of a topic removed | Topic continuity | detect |
| M7 | Last publisher of a topic removed | Topic continuity | detect |
| M8 | One dependency edge added that closes a cycle (vary cycle length 2, 3, 5+) | Tarjan SCC | detect |
| M9 | Sum of requested cores on a host raised above its capacity | Core allocation | detect |
| M10 | Two latency-critical units given overlapping core masks, total within capacity | Core non-overlap | **known miss** (capacity-only check) |
| M11 | Topic carries a different message type/schema at publisher vs subscriber, same topic name | Schema match | **known miss** (name-level check) |
| M12 | On a topic with ≥2 writers, only one writer's QoS is lowered | RxO | measures **topic- vs endpoint-level** gap — record whether flagged and whether the flagged pair is the right one |

Benign mutants — the correct outcome is *no new violation* (exit 0). These measure false positives:

| Op | Change | Why it must pass |
|---|---|---|
| B1 | Writer QoS raised (VOLATILE→TRANSIENT_LOCAL, BEST_EFFORT→RELIABLE) | Offered ≥ requested still holds |
| B2 | Reader QoS lowered | Same |
| B3 | A new subscriber with compatible QoS added to an existing topic | No orphan, no mismatch |
| B4 | Consistent rename of a topic in every descriptor | Topology unchanged |
| B5 | Descriptor entries reordered / whitespace changed | Pure serialization change |
| B6 | A unit moved to another host with spare core capacity | Within capacity |
| B7 | An edge added that does not close a cycle | DAG preserved |

**Step 1.3 — scoring.** For each mutant record: rules fired, whether the fired violation is located at
the mutated element (a finding elsewhere is a false positive even if the mutant is faulty), the
severity assigned, and the exit code. Per operator compute:

- recall = located detections / faulty mutants;
- false-positive rate on B1–B7 and on clean baselines;
- precision over all findings (located true findings / all findings);
- gate-decision accuracy: exit 1 when the expected severity is S1/S2, exit 0 otherwise;
- severity agreement with the expected severity (the protocol's table above plus D2).

Report Wilson 95% intervals. Do not average across operators in the headline; give a per-operator
table and one pooled line for "implemented rules only".

**Step 1.4 — independent oracle for QoS operators (M1–M5, M12, B1–B2).** Ground truth for these is
"the DDS middleware refuses to match the pair". Check it on the middleware itself rather than on our
own reading of the spec: instantiate the mutated reader/writer pair (not the whole profile) in the
program's middleware, or in an open DDS such as Cyclone DDS, and read
`OFFERED_INCOMPATIBLE_QOS` / `REQUESTED_INCOMPATIBLE_QOS` and whether `SUBSCRIPTION_MATCHED` fires.
A sample of **50 mutants per operator** is enough. The open SaaG research code shows the
corpus→DDS QoS mapping and the status polling
(`SoftwareAsAGraph/saag/testbed/dds.py`, `saag/simulation/runtime/dds_status.py`). Record
agreement between SaaG-P's verdict and the middleware's in `rq1_oracle.csv`. Disagreements are
results, not noise: report them.

## 2. RQ2 — Gate on one real, anonymized baseline

**Subject.** One fielded platform baseline, anonymized per `clearance.md` (referred to as
"Platform R" in the paper). Use the same descriptor curation path the prototype uses today
(hand-curated JSON), and log the curation effort for §6 while doing it.

**Step 2.1 — absolute audit.** Run the gate with no baseline subtraction. For every finding record
rule, severity, and an **architect triage verdict**: `TP-fix` (real, fixed or scheduled), `TP-debt`
(real, accepted → waiver register), `FP-model` (wrong because the model/rule is wrong),
`FP-data` (wrong because a descriptor was wrong or stale), `unknown`. Two architects triage
independently on a sample of ≥30 findings (or all, if fewer) — report Cohen's κ — and resolve
disagreements together. Record triage minutes per finding.

**Step 2.2 — delta-aware gating.** Take the last *k* (≥ 20) merged change sets of that baseline, or
as many as cleared. For each, run (a) absolute gating and (b) delta-aware gating against the previous
baseline + waiver register. Record how many would have been blocked under each, and for the ones
delta-aware gating blocks, whether the block was justified.

**Step 2.3 — diagnostic mode.** On the same baseline, record what diagnostic mode surfaced (SCCs and
their size, orphan topics, unreferenced libraries, highest-weight brokers/topics) and **what the team
actually did** with each item (refactored, ticket opened, rejected as harmless). Reviewer A asked for
achieved outcomes; this table is that answer. Only list outcomes that happened.

## 3. RQ3 — Historical defect replay

**Subjects.** *k* anonymized architectural defects (target k ≥ 8) that were found during integration,
harbor acceptance (HAT) or sea acceptance (SAT), or in the field, from the program's defect records.
Include defects the gate is *not* designed for as well, so the result is not cherry-picked: select by
a rule written down before looking at the gate's output (e.g. "every defect in the tracker tagged
middleware/configuration between dates X and Y").

**Steps.** For each: reconstruct the pre-fix descriptors, run the gate, record flagged / not flagged,
the rule and severity, and — when not flagged — why (capability not implemented, data not in
descriptors, outside scope). Where cleared, record the phase found and the effort/delay the defect
cost (days, or a bucket like <1 d, 1–5 d, >5 d).

## 4. RQ4 — Cost

The latency numbers in the Middleware submission stay (Table 6 there; `rq4_latency.csv` here). Add:

- gate latency on Platform R (same 500-run / 20-warm-up method, or fewer runs with *n* stated);
- the *n* and the window behind "a typical pipeline takes ~30 min".

## 5. Sensitivity of severities and gate decisions to weights

Perturb each of α_app, α_broker, β and the QoS factor values (RELIABLE, PERSISTENT/TRANSIENT_LOCAL,
CRITICAL/HIGH) by −20 %, −10 %, +10 %, +20 % one at a time, and also 200 random joint perturbations
(uniform ±20 %). On the RQ1 mutant set and on Platform R, report:

- fraction of findings whose severity label changes;
- fraction of gate decisions (exit code) that flip;
- Kendall τ between baseline and perturbed triage order of findings.

If severity is assigned from a channel table rather than from the weights (D2), say so — then the
weights only order triage and the gate decision is insensitive by construction, which is a result
worth one sentence.

## 6. Lessons — data acquisition effort

Fill `lessons_effort.csv` from project records, not recollection where records exist. Wanted:

- number of distinct configuration sources and formats feeding one baseline (Git repos, XML QoS
  profiles, C++ pragmas, startup scripts, ICD documents, CMDB, shipyard archives);
- fields per entity type that had to be reconciled by hand, and how many conflicts were found;
- person-weeks spent curating the descriptors for Platform R;
- lead time to obtain access / release approval for each source (days);
- descriptor errors discovered during curation (these are defects found by the act of modeling —
  report them; they are evidence too);
- organizational obstacles: who owns which source, which approvals were needed, which were refused.
