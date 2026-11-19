# ADR-0013: Simulation semantics and synthetic data generation

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | SCG.1–7; ADM.3, 6; DVE.11, 13–15, 25, 50–58; QA-04 |
| Resolves | DP-11 (SCG.2 system-wide simulation processes that SCG's synthetic data feeds) |
| Decide by | Wave B (2027-01-22) |
| Supersedes | — |

## Context and Problem Statement

SCG produces synthetic data from user-defined scenario inputs, without field records (SCG.1). It "shall serve as the data source for all system-wide simulation processes — whose details will be determined during the critical design phase" (SCG.2, DP-11). The other requirements:

* The user sets scope, scenario type, time interval, data density and data types (SCG.3, DVE.13).
* Synthetic data must conform to the topic and message schemas, field naming and value ranges of the software units (SCG.4).
* SCG records the scenario name, time and project context (SCG.5) and the inputs used (SCG.6), and hands the data to ADM (SCG.7).

DVE then analyses message flow (DVE.53) and evaluates these effects with AED produced from that synthetic data:

* an entity becoming inactive (DVE.54);
* an increase in density, and changes in publishing or consuming behaviour (DVE.55–56);
* the propagation of fault, load, interruption and bandwidth narrowing (DVE.57);
* the top entities by resource use or messaging (DVE.58).

The SRS defines the twin as static: behaviour comes from overlaying data, "not by running the components". The question is what "simulation" means concretely and how synthetic data is produced reproducibly.

## Decision Drivers

* The model is never executed. Simulation must work on the graph and on data overlays.
* Results must be reproducible from recorded inputs (SCG.5–6, DVE.25, QA-04).
* Synthetic data must fit ADR-0012's AED format and the units' schemas (SCG.4).
* Data volume must stay within ADR-0020's budgets on one host, with only the standard library and wheels already vendored.

## Considered Options

* Semantics: analytical propagation over the derived dependency view with a load model / discrete-event simulation of message traffic / trace replay
* Generation: seeded statistical aggregates per time window / per-message synthetic traces

## Decision Outcome

Chosen options:

* **Analytical propagation over the derived dependency view, driven by a load model**, for simulation semantics.
* **Seeded statistical aggregates per time window** for synthetic data.

Both are consistent with the SRS definition of a static twin. Both need only the standard library and the graph model of ADR-0010, and both are exactly reproducible from a seed. Discrete-event simulation stays possible later as an additional scenario engine.

### 1. Simulation semantics (SCG.2, DP-11)

A *simulation process* is a DVE operation of type `simulation_analysis` (ADR-0007). It runs in four steps:

1. It takes a model instance and revision (ADR-0011), a scenario (§2) and the synthetic AED produced for that scenario.
2. It applies the scenario's **conditions** to a copy of the analysis view:

   | Scenario type | Condition applied | SRS |
   |---|---|---|
   | `nominal` | None; baseline load from the synthetic data | DVE.53 |
   | `density_increase` | Topic and message frequency and size scaled by a factor | DVE.55 |
   | `behaviour_change` | Publishers or subscribers added, removed or rescheduled for selected topics | DVE.56 |
   | `inactive` | Selected nodes or relationships removed | DVE.54 |
   | `bandwidth_narrowing` | `CONNECTS_TO` capacity reduced | DVE.57 |
   | `fault` / `interruption` | Selected entities or links marked failed for a time interval | DVE.57 |

3. It re-derives the weights and `DEPENDS_ON` with SMM's in-memory engine (ADR-0010), and computes propagation and summary indicators as defined in ADR-0017.
4. It records findings, the scenario name, the inputs and the data production time (DVE.25, ADR-0007).

Simulation never changes the baseline or the working model. Conditions are applied to an in-memory copy inside the operation's child process (ADR-0006).

### 2. Scenarios and synthetic data (SCG.1, 3–7)

* **Scenario definition:** a JSON document validated against `scg/src/scg/schemas/scenario-1.0.schema.json`. It holds:
  * `name`, `scope` (selected nodes, units or topics), `type` (§1 table) and condition parameters;
  * `time_range`, `window_seconds`, `density` (a multiplier on the nominal rates) and `data_types` (which AED files and metrics to produce);
  * `seed`, which is generated and recorded when not given.
* **Nominal rates:** taken from the Model Data. These are topic and message `size` and `frequency`, the publisher and subscriber sets, and node capacity. Values listed as placeholders (ADR-0009) are reported as such, and the profile's default is used instead.
* **Generation:**
  * Per window and per entity or relation, SCG draws counts, volumes and frequencies from distributions around the nominal rates, using `random.Random(seed)`.
  * Values are clipped to the value ranges and units of the topic and message schema (SCG.4).
  * Output is an AED-input data set in the ADR-0012 format with `source_kind = synthetic`, registered as an artifact of kind `synthetic_data_set` (ADR-0007).
* **Recording (SCG.5–6):** the scenario name, production time, project, platform and version, the full scenario document and the seed are stored in the artifact's attributes and in the operation's `inputs`.
* **Handoff (SCG.7):** SCG's façade returns the data set reference. ADM converts it to AED (ADM.3, 6) through ADR-0003's in-process call.
* **To build:** the `scg/` package skeleton (ADR-0004), the scenario schema, the generator, and the DVE screens for scenario input and monitoring (DVE.11, 13–15).

### Consequences

* Good, because "simulation" is defined in terms the SRS and the graph model already support, with no execution and no new engine.
* Good, because every simulation is reproducible bit for bit from the scenario document and its seed.
* Good, because per-window aggregates keep data sets small.
* Bad, because effects that depend on message timing, such as queueing delays and bursts within a window, are not modelled. A discrete-event engine would be a new ADR.
* Bad, because the quality of the results depends on the nominal rates in the Model Data. Placeholders weaken them, and they are reported.

### Confirmation

* A reproducibility test runs the same scenario twice with one seed, and the data set hashes are identical.
* A conformance test checks that every generated value respects the schema's value ranges (SCG.4).
* A scenario test per type, on the dev seed model, shows the expected affected entities (for example, `inactive` on a publisher makes its subscribers' topics unpublished).

### Open points

* Default distributions per metric (proposed: Poisson for counts, normal clipped at zero for sizes) are confirmed with system engineering.
* A later scenario engine based on discrete-event simulation (`simpy` 4.1.1 is pure Python) would be decided in a new ADR.

## Pros and Cons of the Options

* Analytical propagation (chosen): Good, because it is static, fast, reproducible and needs no new engine. Bad, because there are no intra-window timing effects.
* Discrete-event simulation: Good, because it models timing and queues. Bad, because it effectively simulates execution, needs a traffic model per unit, and is slower.
* Trace replay: Good, because it is realistic. Bad, because it needs field records, which contradicts SCG.1.
* Per-window aggregates (chosen): Good, because they are compact and match ADR-0012. Bad, because there are no per-message details.
* Per-message traces: Good, because they are detailed. Bad, because the volume grows with rate × duration and exceeds the single-host budgets.

## More Information

* [SRS §2.1, §6.1.3](../../requirements/SRS.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0009, ADR-0010, ADR-0011, ADR-0012, ADR-0017, ADR-0020
