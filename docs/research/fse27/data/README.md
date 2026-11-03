# Result templates for the FSE 2027 revision

Each CSV feeds one table or paragraph of [`../paper.tex`](../paper.tex); the paper marks the slot
`TODO(data)`. The protocol for producing each file is [`../experiment-protocol.md`](../experiment-protocol.md).

Rules (the same ones the Middleware '26 industry draft used):

1. **No number without an `n`, a window and a provenance** (`generated` or `industrial`).
2. **Every category must correspond to a check that actually ran.** A known miss is a result, not a
   blank row.
3. **Record confounders and disagreements** (oracle vs. SaaG-P, architect vs. architect).
4. **Anonymize once, at collection time**, and record it in `clearance.md`.

| File | Feeds |
|---|---|
| `rq1_mutants.csv` | §5.2, Table 5 |
| `rq1_oracle.csv` | §5.2, oracle paragraph |
| `rq2_baseline_findings.csv` | §5.3, Table 6 |
| `rq2_delta_gating.csv` | §5.3 |
| `rq2_diagnostic_outcomes.csv` | §5.3, §6 |
| `rq3_replay.csv` | §5.4, Table 7 |
| `rq4_latency.csv` | §5.5, Table 8 |
| `sens_weights.csv` | §5.6 |
| `lessons_effort.csv` | §6, Table 9 |
| `clearance.md` | §5.1, Data Availability |

## Configuration under test (fill before running — protocol §0)

- SaaG-P build / commit: TODO(data)
- Environment: TODO(data)
- Rules as implemented: TODO(data)
- D1 (full DDS RxO set): TODO(data) done / not possible because …
- D2 (severity procedure): TODO(data)
