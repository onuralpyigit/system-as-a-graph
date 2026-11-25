# ADR-0017: Behavioral propagation and drift detection

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | DVE.50–70; SMM.28, 37; QA-03, QA-07 |
| Resolves | — |
| Decide by | Wave D (2027-05-14) |
| Supersedes | — |

## Context and Problem Statement

R6 implements non-destructive behavioral analysis over the System Model (`DVE.50–51`):

* **Synthetic simulation analyses (`DVE.52–58`):** analyze message flow direction, count, volume and frequency (`DVE.53`); evaluate node **or relationship** inactivity (`DVE.54`), topic/message density increases (`DVE.55`), and pub/sub behavior changes (`DVE.56`); trace propagation of **fault, load, communication interruption, or bandwidth narrowing** onto directly and indirectly dependent elements with explicit **propagation paths** (`DVE.57`); and compute top resource-consuming and most messaging-intensive entities (`DVE.58`).
* **Field-record analyses & architectural drift (`DVE.59–70`):** analyze operational/health status (`DVE.60`), CPU/RAM/storage/network usage (`DVE.61`), error/warning/restart/timeout events (`DVE.62`), message flow (`DVE.63`), latency/loss/success rates (`DVE.64`), topic pub/sub activity (`DVE.65`), node **and relationship** event records (`DVE.69`), and top-N resource/messaging entities (`DVE.70`); plus compare Model Data nodes/relationships against observed runtime data to detect **missing (`DVE.66`), unexpected (`DVE.67`), and attribute-incompatible (`DVE.68`)** elements.

ADR-0010 fixes the structural and `DEPENDS_ON` graph views, ADR-0012 fixes the AED streams (`observed_topology`, `relation_metrics` direction, node+edge `events`), ADR-0013 fixes dual-snapshot ($G_{\text{pre}}, G_{\text{post}}$) scenarios, and ADR-0016 fixes the `@check(model, params, aed)` rule engine. This ADR specifies the exact propagation and drift algorithms so no structural or cross-layer dependency blind spots exist.

## Decision Drivers

* Propagation must handle node removal/inactivity (`DVE.54`), `Node` → hosted `Application`/`Broker` lifting (`RUNS_ON`), `Topic`/`Message`/relationship origins (`DVE.54–56`), and non-articulation `CONNECTS_TO` mesh-link congestion (`DVE.57`) without missing affected dependents!
* Every affected element must record an explicit, human-inspectable path (`DVE.57`) and cause-and-effect `dve_finding_link` (`DVE.22`).
* Drift detection (`DVE.66–68`) must use the exact same entity/relationship identity keys and `smm_aed_alias` table as `SMM.bind` (`ADR-0012 §2`).
* All algorithms must execute in pure Python 3.9 (+ `networkx 3.2.1`) within ADR-0020's latency budgets.

## Considered Options

* Propagation algorithm: Dual-graph ($G_{\text{pre}}, G_{\text{post}}$) redundancy-aware reverse traversal over `DEPENDS_ON` + `RUNS_ON` with link-congestion seeding
* Propagation algorithm: Naive post-removal `DEPENDS_ON`-only BFS (misses severed origins and hosted `RUNS_ON` apps)
* Propagation algorithm: Dense Design Structure Matrix (DSM) transitive closure
* Drift matching: Deterministic `(label_or_type, key)` matching with version-scoped `smm_aed_alias` and catalog-driven attribute comparators
* Drift matching: Heuristic graph-fingerprint / neighborhood similarity matching

## Decision Outcome

Chosen options: **dual-graph ($G_{\text{pre}}, G_{\text{post}}$) redundancy-aware reverse traversal over `DEPENDS_ON` and incoming `RUNS_ON` with structural/link-congestion seeding**, and **deterministic key matching with `smm_aed_alias` plus catalog-declared attribute comparators**.

### 1. Multi-layer behavioral propagation (`DVE.53–58`)

Given $G_{\text{pre}}$ (baseline/working state before scenario perturbations), $G_{\text{post}}$ (state after applying ADR-0013 §1 perturbations and re-deriving loads/weights/`DEPENDS_ON`), and bound synthetic `AedReader`:

1. **Seed computation ($s_0 \in (0, 1]$) on $G_{\text{pre}}$ vs. $G_{\text{post}}$:**
   * **Why $G_{\text{pre}}$ is traversed:** when `inactive` (`DVE.54`) or `communication_interruption` (`DVE.57`) removes a node or edge in $G_{\text{post}}$, its `DEPENDS_ON` edges disappear from $G_{\text{post}}$. Seeding from the loss between $G_{\text{pre}}$ and $G_{\text{post}}$ and walking **$G_{\text{pre}}$** ensures severed dependents are always reached while respecting redundancy (`hotstandby` publishers, redundant switches/links) that survives in $G_{\text{post}}$!
   * **Origin seeding rules by element & condition kind:**
     * *Node `inactive` / `fault` (`Application`, `Broker`, `CommunicationService`, `Node`, `NetworkDevice`):* $s_0(u) = 1.0$ on the failed/removed node $u$. For a subscriber depending on topic $t$, if redundant active publishers of $t$ remain in $G_{\text{post}}$, the first hop attenuates by the fraction of lost publisher capacity; if zero publishers remain, full starvation ($1.0 \cdot w(e)$) propagates.
     * *Structural relationship `inactive` / `communication_interruption` (`DVE.54, 57`):* deactivating `u -[:PUBLISHES_TO]-> t`, `b -[:ROUTES]-> t`, or `cs -[:TRANSFERS]-> m` seeds affected subscribers/consumers of `t`/`m` according to lost publisher/route coverage between $G_{\text{pre}}$ and $G_{\text{post}}$; deactivating `a -[:RUNS_ON]-> n` seeds `a` ($s_0 = 1.0$ unless a `hotstandby` replica remains on another `Node`).
     * *`Topic` / `Message` `density_increase` & `behaviour_change` (`DVE.55–56`):* `Topic` and `Message` have no `DEPENDS_ON` edges of their own; the seed step transitions across structural `SUBSCRIBES_TO`, `PUBLISHES_TO`, `ROUTES`, `CARRIES`, `SENDS`, `RECEIVES`, and `TRANSFERS` to the directly connected `Application`, `Library`, `Broker`, and `CommunicationService` nodes with $s_0 = \min(1.0, |\Delta \text{rate}| / \text{rate}_{\text{pre}})$, and recomputes link/host utilization.
     * *`load` (`DVE.57`):* seeds overloaded `Application`s or `Node`s with $s_0 = \min(1.0, \max(0, \text{util}_{\text{post}} - \text{threshold}) / (1 - \text{threshold}))$.
     * *`bandwidth_narrowing` & link congestion (`DVE.57`):* recomputes offered traffic (`bytes × freq_hz` from synthetic AED / Phase 5c) across surviving shortest `CONNECTS_TO` paths in $G_{\text{post}}$ (covering **both** articulation `NetworkDevice`s from Rule 7 **and** non-articulation host-mesh or dual-switch links!). Every saturated link (`utilization = load_mbps / capacity_mbps > 1.0`) seeds its endpoint `Node`s/`NetworkDevice`s with $s_0 = \min(1.0, (\text{utilization} - 1.0) / \text{utilization})$.
2. **Cross-layer reverse traversal (`DEPENDS_ON` + `RUNS_ON`):**
   * From each seeded element $u$, run a priority-queue best-first search (Dijkstra in $-\log w$, bounded by `max_depth = 10` and `min_effect = 0.05` from `propagation.yaml`) over **two reverse transition types** on $G_{\text{pre}}$:
     * **Reverse `DEPENDS_ON`:** `dependency ← dependent` with factor $w(e)$ (`app_to_app`, `app_to_lib`, `app_to_broker`, `node_to_node`, `node_to_broker`, `broker_to_broker`, `node_to_device`);
     * **Reverse `RUNS_ON` (host-to-guest lift):** `Node ← Application | Broker | CommunicationService` with factor $1.0$—ensuring that a failed, overloaded, or network-congested `Node` immediately propagates to every software unit and broker hosted on it, and from there along `app_to_app` / `app_to_broker` to remote dependents!
   * Path strength along $P = (u_0, e_1, u_1, \dots, e_k, v)$ is $s(v) = s_0(u_0) \cdot \prod_{i=1}^{k} w(e_i)$; the strongest simple path $P^*(v)$ (and hop classification: `direct` for $k=1$, `indirect` for $k>1$) is retained per affected element $v$.
3. **Findings, links and KPIs (`DVE.57–58`):**
   * Emits one `dve_finding` (`finding_type = 'propagated_effect'`) per affected element with `P*(v)` and `s(v)` in `evidence`, mapped to severity via `propagation.yaml` bands (defaults: `critical ≥ 0.70`, `high ≥ 0.40`, `medium ≥ 0.20`, `low ≥ 0.05`), plus `dve_finding_link` rows from the origin finding to each downstream finding (`DVE.22`).
   * Computes top-$N$ (default $N = 10$) entities by peak/mean CPU, memory, network bandwidth, message count, and data volume from `AedReader` (`DVE.58`) into `common_operation.result_summary`.

### 2. Field behavioral checks and architectural drift (`DVE.59–70`)

* **Field checks (`DVE.60–65, 69–70`):** executed as ADR-0016 `@check(model, params, aed)` functions configured by `field_health.yaml` and `field_traffic.yaml` over bound `field` `overlay.db` (`entity_metrics`, directed `relation_metrics`, and node+relationship `events`), writing top-$N$ field resource/messaging KPIs (`DVE.70`) into `common_operation.result_summary`.
* **Architectural drift detection (`DVE.66–68`, `drift.yaml`):** compares the System Model's nodes and structural relationships (`ModelReader`) against `aed_observed` (`observed_topology.jsonl.gz` in `overlay.db`, ADR-0012 §1) after resolving `smm_aed_alias` (`ADR-0012 §2`):

  | SRS | Drift class | Comparison over `(element_kind, label_or_type, key)` | `finding_type` |
  |---|---|---|---|
  | DVE.66 | Present in Model Data / System Model, not observed in runtime field data | Model node or structural relationship within expected runtime scope (`Application`, `Broker`, `CommunicationService`, `Node`, `Topic`, `PUBLISHES_TO`, `SUBSCRIBES_TO`, `RUNS_ON`, `CONNECTS_TO`, `TRANSFERS`) absent from `aed_observed` | `drift_missing` |
  | DVE.67 | Not present in Model Data / System Model, observed in runtime field data | Observed runtime node or relationship in `aed_observed` (after alias resolution) with no counterpart in `ModelReader` (identical key set to `SMM.37` `unmatched_aed_count`) | `drift_unexpected` |
  | DVE.68 | Present in both, showing incompatibility between model and runtime data | Matched node or relationship whose `aed_observed.observed_attributes` contradict model attributes per comparators declared in `drift.yaml` (e.g. `Node.cpu_cores` or `os_type`, `Application.version` or hosting `RUNS_ON` `Node`, `Topic` QoS parameters, or direction reversal where a subscriber-only unit publishes at runtime) | `drift_mismatch` |

### Consequences

* Good, because dual-graph ($G_{\text{pre}}, G_{\text{post}}$) seeding + `RUNS_ON` host lifting + `CONNECTS_TO` path congestion closes all structural-removal, host-to-app, topic-origin and mesh-network blind spots in `DVE.54–57`.
* Good, because `observed_topology` and `smm_aed_alias` make `DVE.66–68` deterministic across both nodes and relationships and consistent with `SMM.37`.
* Bad, because multiplicative weight attenuation $s_0 \cdot \prod w(e)$ is an analytical impact-ranking index $\in [0, 1]$ rather than a physical millisecond latency predictor.

### Confirmation

* Worked-example & redundancy tests: deactivating `L0` or single publisher `A0` propagates to `A1` with expected `s(A1)` and path; deactivating one replica of a dual-node `hotstandby` publisher attenuates rather than reporting total starvation.
* Cross-layer test: injecting `fault` on `Node N0` or `bandwidth_narrowing` on a direct `Node ↔ Node` `CONNECTS_TO` link propagates across `RUNS_ON` to hosted `Application`s and downstream remote subscribers (`TC-DVE-14`).
* Drift test (`TC-DVE-16`): running `field_analysis` against a sample `observed_topology` with one missing node/edge, one unexpected node/edge, and one mismatched `cpu_cores`/QoS attribute produces exact `drift_missing`, `drift_unexpected`, and `drift_mismatch` findings.

## Pros and Cons of the Options

### Dual-graph ($G_{\text{pre}}, G_{\text{post}}$) reverse traversal over `DEPENDS_ON` + `RUNS_ON` (chosen)

* Good, because it preserves severed edges for traversal, accounts for surviving redundancy in $G_{\text{post}}$, lifts infrastructure faults to hosted software units, and outputs explicit paths (`DVE.57`).
* Bad, because maintaining two in-memory copies during an operation roughly doubles child-process graph RAM (~tens of MB at 50k edges, well within ADR-0020 budgets).

### Naive post-removal `DEPENDS_ON`-only BFS

* Good, because only one graph copy is held.
* Bad, because removing an inactive origin deletes its incoming `DEPENDS_ON` edges (yielding zero affected nodes!) and `Node` faults never reach hosted `Application`s.

### Dense Design Structure Matrix (DSM) transitive closure

* Good, because matrix multiplication is compact.
* Bad, because $O(V^2)$ memory at $V > 12,000$ is wasteful on sparse graphs and loses individual multi-hop explanation paths.

### Deterministic key matching with `smm_aed_alias` and catalog comparators (chosen)

* Good, because every drift finding is 100% explainable, reproducible, and consistent with `SMM.bind`.
* Bad, because legitimately renamed runtime processes must be listed in `smm_aed_alias` once per version.

### Heuristic neighborhood/fingerprint similarity matching

* Good, because renamed nodes might match without an alias entry.
* Bad, because false-positive fuzzy matches silently mask genuine `DVE.66/67` architectural drift.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `0bbe06af`](https://github.com/onuralpyigit/software-as-a-graph/blob/0bbe06afa12be228e343895322716b8cbd085535/docs/graph-model.md), §6–§7
* [SRS §6.1.3](../../requirements/SRS.md), [STD TC-DVE-14..16](../../test/STD.md)
* Related: ADR-0006, ADR-0007, ADR-0010, ADR-0011, ADR-0012, ADR-0013, ADR-0016, ADR-0020
* Revisit if R6/R9 pilot feedback requires probabilistic Monte Carlo availability simulation alongside deterministic path-strength ranking.
