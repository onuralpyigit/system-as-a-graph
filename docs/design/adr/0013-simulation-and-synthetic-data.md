# ADR-0013: Simulation semantics and synthetic data generation

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | SCG.1–7; ADM.3, 6; DVE.11, 13–15, 17, 25, 50–58; QA-04 |
| Resolves | DP-11 (SCG.2 system-wide simulation processes that SCG's synthetic data feeds) |
| Decide by | Wave B (2027-01-22) |
| Supersedes | — |

## Context and Problem Statement

SCG produces synthetic data from user-specified scenario inputs without requiring field records (SCG.1), serving as the data source for all system-wide simulation processes whose details are deferred to critical design (SCG.2, DP-11):

* Users configure **scenario scope, scenario type, time interval, data density, and data types to be produced** (SCG.3, DVE.13).
* Produced synthetic data must conform to the **topic/message data schema, field naming, and value-range constraints** used by the software units (SCG.4).
* SCG records scenario name, production time, project/platform/version, and exact user inputs (SCG.5–6), and hands the dataset off to ADM (SCG.7, ADM.3, 6).
* Users must also be able to run scenarios and simulations on an edited **Working Model** (DVE.17), evaluating message flow (DVE.53), node/relationship inactivity (DVE.54), topic/message density increases (DVE.55), pub/sub behavior changes (DVE.56), propagation of **fault, load, communication interruption, and bandwidth narrowing** (DVE.57), and top resource/messaging entities (DVE.58), recording scenario metadata on the simulation operation (DVE.25).

The SRS defines SaaG as a static digital twin ("not by running the components"). This ADR defines what "simulation" means architecturally and how SCG satisfies `SCG.4` and `DVE.17` reproducibly.

## Decision Drivers

* Target applications are never executed; simulation operates analytically over the System Model graph and synthetic AED overlays.
* Synthetic generation must read schemas and nominal rates from a `ModelSchemaSnapshot` of the selected **baseline or Working Model `(instance_id, revision)`** (supporting DVE.17 while respecting ADR-0004's acyclic package boundary so `scg` never imports `mdg` or `smm`).
* SCG must satisfy `SCG.4` literally—generating schema-validated, value-range-bounded payload field summaries alongside traffic/resource window aggregates.
* Pre- and post-condition model states ($G_{\text{pre}}$ and $G_{\text{post}}$) must both be preserved during `simulation_analysis` so removing an inactive node/edge never erases the incoming `DEPENDS_ON` edges needed by ADR-0017's reverse propagation walk!

## Considered Options

* Simulation semantics: Dual-snapshot ($G_{\text{pre}}, G_{\text{post}}$) analytical load & dependency propagation over the System Model
* Simulation semantics: Discrete-event packet/queue simulation (`simpy`)
* Simulation semantics: Recorded field-trace replay
* Synthetic data granularity: Seeded per-window traffic/resource aggregates plus schema-constrained `field_samples` (`SCG.4`)
* Synthetic data granularity: Per-message full synthetic packet traces

## Decision Outcome

Chosen options: **dual-snapshot ($G_{\text{pre}}, G_{\text{post}}$) analytical load and dependency propagation** for simulation semantics, and **seeded per-window aggregates paired with `field_schema`-constrained `field_samples`** for synthetic data generation.

### 1. System-wide simulation processes (`SCG.2`, `DP-11`; `DVE.25, 50–58`)

A *system-wide simulation process* is a DVE operation of type `simulation_analysis` (`simulation` queue, ADR-0006, ADR-0007) consuming a System Model `(instance_id, revision)` (baseline or pre-spawn Working Model snapshot, DVE.17), a scenario document (§2), and the synthetic AED prepared by ADM from SCG's output:

1. **Load $G_{\text{pre}}$:** load the structural and derived graph ($G_{\text{pre}}$) into SMM's in-memory engine inside the child process—never mutating the stored graph instance (DVE.51).
2. **Construct $G_{\text{post}}$ under scenario conditions:** clone $G_{\text{pre}}$ in memory, apply the scenario's perturbation(s), recompute topic/link loads, and re-derive weights and `DEPENDS_ON` on $G_{\text{post}}$:

   | `scenario_type` | Perturbation applied on $G_{\text{post}}$ and synthetic load | SRS |
   |---|---|---|
   | `nominal` | Baseline topology and nominal topic/message rates | DVE.53 |
   | `inactive` | Remove scoped nodes and/or structural relationships (`PUBLISHES_TO`, `SUBSCRIBES_TO`, `ROUTES`, `RUNS_ON`, `CONNECTS_TO`, `USES`) in $G_{\text{post}}$ | DVE.54 |
   | `density_increase` | Multiply scoped `Topic` / `Message` frequency and/or payload size by `density` factor (> 1.0) | DVE.55 |
   | `behaviour_change` | Add, remove, or re-rate `PUBLISHES_TO` / `SUBSCRIBES_TO` / `SENDS` / `RECEIVES` edges on scoped units/topics/messages | DVE.56 |
   | `fault` | Mark scoped `Application`, `Broker`, `CommunicationService`, or `Node` failed (zero output capacity / error state over fault window) | DVE.57 |
   | `load` | Inject CPU, memory, or message-processing load spike on scoped `Application`s or `Node`s | DVE.57 |
   | `communication_interruption` | Sever scoped `CONNECTS_TO` links, `NetworkDevice`s, `Broker` `ROUTES`, or `CommunicationService` `TRANSFERS` over interruption window | DVE.57 |
   | `bandwidth_narrowing` | Reduce `CONNECTS_TO.capacity_mbps` on scoped network links/devices by configured ratio | DVE.57 |

   *(Compound scenarios may combine multiple condition blocks in one run.)*
3. **Evaluate propagation & KPIs (ADR-0017):** compare $G_{\text{pre}}$ and $G_{\text{post}}$ with the bound synthetic AED to trace direct/indirect affected elements and propagation paths (`DVE.57`), evaluate flow/density/inactivity (`DVE.53–56`), and compute top-N resource and messaging entities (`DVE.58`) into `common_operation.result_summary`.
4. **Persist provenance (`DVE.25`):** record scenario name, full scenario inputs, synthetic data production timestamp, `instance_id`/`revision`, `aed_dataset_id`, `conformance` (`DVE.18`), and findings (`dve_finding`, `dve_finding_link`) in `dsm.db` (ADR-0007).

### 2. Scenario schema and `SCG.4`-conformant synthetic generation (`SCG.1, 3–7`)

* **Model input (`DVE.17`, `ADR-0003`):** DVE extracts a read-only `ModelSchemaSnapshot` DTO (`common`) from `SMM`'s `ModelReader(instance_id, revision)` containing scoped nodes, structural edges, nominal `size`/`frequency`/capacities, `placeholders`, and every `Topic`/`Message` `field_schema` (`[{name, type, min, max, unit}]`, ADR-0008, ADR-0010), and passes it to `scg.produce_synthetic_data(snapshot, scenario)`. Editing a Working Model and immediately generating synthetic data therefore reflects the Working Model's edits accurately.
* **Scenario schema (`scg/src/scg/schemas/scenario-1.0.schema.json`):**
  * `schema_version`: `"1.0"`, `name`, `description`;
  * `scope`: target entity/relationship keys, CSCI/CSC filters, or `"system"` (`SCG.3`);
  * `scenario_type` and `conditions` (§1 table);
  * `time_range` (`duration_seconds` or UTC `{start, end}`), `window_seconds` (default `1`), `density` multiplier, and `data_types` subset (`entity_metrics`, `relation_metrics`, `events`, `field_samples`, `SCG.3, DVE.13`);
  * `seed` (`int`, auto-generated and recorded if omitted for 100% bit-level reproducibility) and optional distribution overrides (defaults: Poisson for message counts, truncated normal for sizes/latencies/CPU/RAM).
* **Schema & value-range conformance (`SCG.4`):**
  1. **Per-window traffic & resource streams:** using `random.Random(seed)`, SCG generates `entity_metrics`, `relation_metrics` (with `direction`), and fault/timeout `events` consistent with publisher/subscriber topology and scenario perturbations. Placeholder nominal rates (`ADR-0009`) fall back to documented profile defaults (`1.0 Hz`, `256 B`) and emit a provenance note.
  2. **Payload field-naming & range synthesis (`field_samples.jsonl.gz`):** for every `Topic` and `Message` in scope with a `field_schema`, SCG draws field-level values per window using the exact declared `field_name` and `field_type` (`int`, `float`, `bool`, `enum`), **strictly clipped to `[min, max]`**, and writes `min_val`, `max_val`, `mean_val`, `sample_count`, and `unit` into `field_samples.jsonl.gz`. Any schema constraint violation in user overrides fails pre-flight validation with a `schema` `ErrorRecord`.
* **Storage & handoff (`SCG.5–7`, `ADM.3, 6`):**
  * Written to `/var/lib/dsm/workspace/scg/<project>/<platform>/<version>/<scg_dataset_id>/`, hashed (`SHA-256`), and registered in `common_artifact` (`kind = 'synthetic_data_set'`, storing `scenario_name`, `seed`, `produced_at`, and full `scenario` JSON in `attributes`, SCG.5–6).
  * `scg.produce_synthetic_data` returns `ArtifactRef` (`INT-IF-02`, ADR-0003). `ADM` (`adm.produce_aed`) validates readability, `aed-1.0.schema.json` conformance, value-range invariants, and mandatory fields (`ADM.6`), builds `<aed_dir>/overlay.db` (ADR-0012 §2), and registers the immutable `analytical_evaluation_data` artifact (`source_kind = 'synthetic'`).

### Consequences

* Good, because simulation stays faithful to the static-twin paradigm while preserving both $G_{\text{pre}}$ and $G_{\text{post}}$ so `inactive` and `communication_interruption` propagation works without edge-deletion blind spots.
* Good, because reading `ModelSchemaSnapshot` from `ModelReader` enables seamless hypothetical scenario runs on Working Models (`DVE.17`), and `field_samples.jsonl.gz` directly satisfies `SCG.4` and `STD TC-SCG-02`.
* Bad, because sub-window microsecond burst/queueing dynamics are approximated analytically per window rather than simulated packet-by-packet.

### Confirmation

* Determinism test runs `produce_synthetic_data` twice with the same `seed` and `ModelSchemaSnapshot`, asserting byte-identical `.jsonl.gz` SHA-256 hashes.
* `SCG.4` test (`TC-SCG-02`) verifies that every generated `field_samples` record matches the unit's `Topic`/`Message` field names, types, and `[min, max]` bounds, and that ADM (`ADM.6`) rejects tampered out-of-range synthetic files.
* Working-model simulation test (`DVE.17`) adds a topic subscriber on a Working Model, generates synthetic data, and confirms flow and propagation include the newly edited subscriber.
* Scenario coverage test (`TC-DVE-14`) exercises all eight `scenario_type` values (`nominal`, `inactive`, `density_increase`, `behaviour_change`, `fault`, `load`, `communication_interruption`, `bandwidth_narrowing`).

## Pros and Cons of the Options

### Dual-snapshot ($G_{\text{pre}}, G_{\text{post}}$) analytical propagation (chosen)

* Good, because it is fast, deterministic, stdlib-only, works on edited Working Models, and preserves pre-removal dependencies for accurate impact paths.
* Bad, because transient sub-window queue buildup is not modeled.

### Discrete-event simulation (`simpy`)

* Good, because queue depths and micro-burst latencies can be modeled explicitly.
* Bad, because it requires per-unit service-time distributions that static source repos do not contain, runs orders of magnitude slower, and blurs the SRS static-twin boundary (kept open as an optional future engine ADR if needed).

### Trace replay

* Good, because traffic patterns come from real runs.
* Bad, because requiring field traces violates SCG.1 (*"without requiring field records"*).

### Seeded per-window aggregates plus `field_samples` (chosen)

* Good, because dataset sizes stay bounded (megabytes, not tens of gigabytes) while satisfying `SCG.4` field-naming and value-range verification.
* Bad, because individual synthetic packet payloads are summarized per window rather than stored message-by-message.

### Per-message synthetic traces

* Good, because every individual message instance is materialized.
* Bad, because a 1-hour scenario across 5,000 topics at 100 Hz generates $1.8 \times 10^9$ records, blowing single-host storage and time budgets (ADR-0020).

## More Information

* [SRS §2.1, §4.1, §6.1.3](../../requirements/SRS.md), [STD TC-SCG-01..03, TC-DVE-14](../../test/STD.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0010, ADR-0011, ADR-0012, ADR-0017, ADR-0020
* Revisit if system engineering later requires sub-millisecond queueing-network delay predictions (`simpy` 4.1.1 pure-Python discrete-event extension).
