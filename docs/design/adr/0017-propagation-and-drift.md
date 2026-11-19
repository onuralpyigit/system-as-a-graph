# ADR-0017: Behavioral propagation and drift detection

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | DVE.50–58, 59–70; SMM.28; QA-03, QA-07 |
| Resolves | — |
| Decide by | Wave D (2027-05-14) |
| Supersedes | — |

## Context and Problem Statement

R6 builds behavioral analysis on the System Model, without altering it (DVE.50–51).

* **From synthetic AED** (DVE.52–58):
  * evaluate the effect of an entity becoming inactive (DVE.54) and of load changes (DVE.55–56);
  * determine how fault, load, communication interruption or bandwidth narrowing **propagates** to dependent nodes, with the directly and indirectly affected elements and the **propagation path** (DVE.57);
  * name the entities with the highest resource use or most intensive messaging (DVE.58).
* **From field AED** (DVE.59–70):
  * analyse status, resources, events, flow, latency and loss (DVE.60–65, 69–70);
  * detect **architectural drift** between the Model Data and the runtime (DVE.66–68): entities present in the model but not observed, observed but not in the model, and present in both but incompatible.

ADR-0010 already defines the derived `DEPENDS_ON` view with weights, ADR-0013 defines simulation scenarios, and ADR-0012 defines AED and its key-based binding. This ADR fixes the algorithms.

## Decision Drivers

* Results must follow the framework model's dependency semantics, so they stay comparable with its published results (ADR-0010).
* Every affected element must come with an explainable path (DVE.57) and be recorded as a finding (ADR-0007).
* Drift must use the same identity keys as binding, so the two never disagree.
* The algorithms run in an operation's child process on one host, within ADR-0020's budgets, with pure Python 3.9.

## Considered Options

* Propagation: weighted traversal of `DEPENDS_ON` / dependency-matrix (DSM) analysis / re-running full simulation per change
* Drift matching: entity keys with an alias table / fingerprint similarity (attributes and neighbours) / manual mapping only

## Decision Outcome

Chosen options: **a weighted traversal of the derived `DEPENDS_ON` view** for propagation, and **matching by entity key with a reviewed alias table** for drift. The traversal reuses the framework's dependency semantics and weights directly and yields explicit paths. Key matching is deterministic and identical to AED binding.

### 1. Propagation (DVE.54–58)

* **Input:** a model instance and revision, a scenario's conditions (ADR-0013), and optionally bound AED (ADR-0012).
* **Algorithm:**
  1. Apply the conditions to an in-memory copy of the analysis view (SMM's engine, ADR-0010 §7).
  2. Re-derive the weights.
  3. From each *origin* element (the element the condition hits), walk `DEPENDS_ON` edges **in reverse**, from a dependency to its dependents, breadth first.
  4. An effect reaching element *v* along path *P* has strength *s(v) = s₀ · Π w(e)* over the edges *e* in *P*, where *s₀ = 1* for a hard fault or inactivity, and the relative change for load.
  5. Stop below the profile's `min_effect` (default 0.05) or at `max_depth` (default 10).
  6. Keep the strongest path per element.
* **Condition mapping:**
  * `inactive` and `fault` start at the element itself;
  * `density_increase` and `behaviour_change` start at the affected topics, through `app_to_app` and `app_to_broker` edges;
  * `bandwidth_narrowing` starts at the `NetworkDevice` or link, through `node_to_device` (rule 7) and `node_to_node`.
* **Output (DVE.57–58):**
  * one finding per affected element, with type `propagated_effect`, severity from the profile's strength bands, and the path as evidence;
  * a finding link from the origin to each affected element (DVE.22);
  * the top-N entities by resource use and messaging, from AED aggregates (DVE.58), as summary indicators in the operation result.
* **Algorithms library:** networkx 3.2.1 where needed (ADR-0016); the traversal itself is a plain BFS.

### 2. Field analyses and drift (DVE.59–70)

* **Field analyses (DVE.60–65, 69–70):** per-entity aggregates and thresholds over bound field AED, implemented as check functions in the rule engine (ADR-0016), with their thresholds in the rule catalog. Event analysis (DVE.69) groups `events` by entity and kind.
* **Drift (DVE.66–68):** compares the model's entity and relationship keys with those observed in field AED, after applying the alias table (ADR-0012):

  | Class | Rule | Finding type |
  |---|---|---|
  | Present in the model, not observed (DVE.66) | Model key with no observation in the record's time range | `drift_missing` |
  | Observed, not in the model (DVE.67) | Observed key with no model counterpart, which is the same set as SMM.37's unmatched records | `drift_unexpected` |
  | Incompatible (DVE.68) | Matched key whose observed attributes contradict the model, for example a publisher of a topic the model says it only consumes, or a node with a different core count | `drift_mismatch` |

  * Attribute comparisons are declared per label in the rule catalog, so new ones need no engine change.

### Consequences

* Good, because propagation uses exactly the framework's dependency semantics and weights, and every effect has a path.
* Good, because drift and binding share one identity scheme, so "unmatched" means the same thing everywhere.
* Good, because field thresholds live in the reviewed rule catalog (ADR-0016).
* Bad, because the product-of-weights model is a heuristic. It ranks effects but does not predict magnitudes such as latency in milliseconds.
* Bad, because renamed entities appear as missing plus unexpected until the alias table maps them.

### Confirmation

* A test on the framework model's worked example (ADR-0010 fixtures): an inactive library yields the expected dependent set and paths.
* Scenario tests per condition type on the dev seed model.
* A drift test with a field AED sample containing one missing, one unexpected and one mismatched entity yields exactly three drift findings of the right classes.
* A performance test runs propagation on the ADR-0020 reference model within its budget.

### Open points

* The strength bands that map effect strength to severity, and the default `min_effect` and `max_depth`, are confirmed with system engineering.
* The initial list of attribute comparisons for DVE.68 is agreed with the rule-catalog owners.

## Pros and Cons of the Options

* Weighted traversal (chosen): Good, because it is explainable, fast and consistent with the framework. Bad, because it is a ranking heuristic.
* Dependency matrix: Good, because it gives a compact overview. Bad, because it gives no per-path explanation, and it is quadratic in memory.
* Full re-simulation: Good, because it is the most realistic. Bad, because it needs an execution model, which the SRS excludes.
* Key matching with aliases (chosen): Good, because it is deterministic and reviewable. Bad, because aliases must be maintained.
* Fingerprint similarity: Good, because it finds renamed entities automatically. Bad, because it is probabilistic and can mis-match silently.
* Manual mapping only: Bad, because it does not scale.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `d1f8b424`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md), §6 (derivation rules), §7 (layers)
* [SRS §6.1.3](../../requirements/SRS.md)
* Related: ADR-0006, ADR-0007, ADR-0010, ADR-0011, ADR-0012, ADR-0013, ADR-0016, ADR-0020
