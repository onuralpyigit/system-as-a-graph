# ADR-0010: System Model graph schema aligned with the Software-as-a-Graph model

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | SMM.1, 4–25; SCG.4; DVE.19–20, 28–49, 53–58; QA-03, QA-07 |
| Resolves | DP-30d, DP-30f (SDD §2.4 entity schema of the System Model, also used by the Working Model per ADR-0011) |
| Decide by | Wave A2 (2026-12-18) |
| Supersedes | — |

## Context and Problem Statement

SMM.4 requires converting validated Model Data into a node-relationship **System Model**:

* **Nodes (SMM.6–17):** System, Software Segment, CSCI, CSC, CSU, Role, Topic, Message, Operator Console and Processor Units, Network components, Middleware Services, and Services of Communication Technologies.
* **Relationships (SMM.18–23):** Running on console/processor units, Using middleware and communication services, Publishing data, Consuming data, Being dependent on a library **or software unit**, and Assignment of a software unit to a role.
* **Attributes & Lifecycle (SMM.5, 24–26):** CPU core allocation, OS settings and runtime environment configurations as queryable attributes (SMM.24); missing-entity and invalid-relationship error reporting (SMM.25); project/platform/version provenance (SMM.5, 26).
* **Downstream consumers:** Every R3 structural rule (DVE.28–49—including Lifespan QoS `DVE.34`, same-name topic content conflicts `DVE.38`, external-to-middleware communication consistency `DVE.39`, CPU/OS/memory contention `DVE.41–46`, unit cycles `DVE.47`, and disconnected/unmatched elements `DVE.48`), SCG field-constrained synthetic generation (`SCG.4`), and R6 propagation/drift analyses (`DVE.53–70`) query this schema directly.

The **Software-as-a-Graph (`saag`)** research framework in the companion workspace defines a formal typed property multigraph for publish-subscribe systems: [`docs/graph-model.md` @ `0bbe06af`](https://github.com/onuralpyigit/software-as-a-graph/blob/0bbe06afa12be228e343895322716b8cbd085535/docs/graph-model.md) (commit `0bbe06afa12be228e343895322716b8cbd085535`, called **the framework model** below). It specifies six core vertex types, six structural edge types, seven `DEPENDS_ON` derivation rules, AHP QoS-driven weights (including the non-saturating library fanout lift introduced in `d1419ae7`), and four layer projections.

Although `saag`'s `pyproject.toml` lists `requires-python = ">=3.9"`, its pinned scientific dependencies (`networkx>=3.4`, `numpy>=2.1`, `scipy>=1.15`, `scikit-learn>=1.5`) require Python ≥ 3.10 on PyPI, so the CPython 3.9 target host (ADR-0004) cannot import `saag` at run time. Meanwhile, `mdg` (`1157784`) already emits the core framework collections (`nodes`, `networks`, `applications`, `libraries`, `topics`, `messages`), lacking the SRS extension types and attributes.

## Decision Drivers

* Every SRS node type, relationship type and attribute (`SMM.6–24`)—and every structural/behavioral condition in `DVE.28–58` and `SCG.4`—must be first-class and queryable in Cypher without opaque string parsing.
* Framework weights, `DEPENDS_ON` derivation rules and layer projections must match `SoftwareAsAGraph @ 0bbe06af` bit-for-bit so published methodology, corpus scenarios and worked examples transfer directly.
* Entity keys must be deterministic and stable across baseline, working and candidate instances (ADR-0011) and across versions (drift, DVE.66–68), without CSCI/CSC naming collisions.
* Acquired facts, derived analytical edges/weights, and placeholders (ADR-0009) must remain strictly distinguishable (QA-03).

## Considered Options

* Framework-aligned typed property graph (`saag @ 0bbe06af`), extended with SRS types and verification attributes, split into structural and derived dependency views
* Pure SRS-named property graph (`CSU`, `ProcessingUnit`, `PUBLISHES`, `CONSUMES`, …) with an external translation adapter for framework analyses
* Generic single-label graph (`:Entity {type}` / `:RELATES {kind}`)

## Decision Outcome

Chosen option: **Framework-aligned typed property graph (`saag @ 0bbe06af`) extended with the SRS-specific node/relationship types and verification attributes, maintaining separable structural ($G_{\text{structural}}$) and derived dependency ($G_{\text{analysis}}$) views**, ported cleanly to pure Python 3.9 in `smm`.

### 1. SRS-to-schema mapping

**Table 1. SRS node types → graph labels**

| SRS | SRS term | Graph label(s) | Provenance |
|---|---|---|---|
| SMM.6 | System | `System` | SRS extension |
| SMM.7 | Software Segment | `SoftwareSegment` | SRS extension |
| SMM.8 | CSCI | `CSCI` | SRS extension |
| SMM.9 | CSC | `CSC` | SRS extension |
| SMM.10 | CSU | `Application` (executable unit) or `Library` (shared unit) | framework (`CSU` UI/search filter matches `Application ∪ Library`, DVE.19) |
| SMM.11 | Role | `Role` | SRS extension |
| SMM.12 | Topic | `Topic` | framework + SRS QoS extensions |
| SMM.13 | Message | `Message` | SRS extension (aligned with `mdg`) |
| SMM.14 | Operator Console and Processor Units | `Node` (`kind` = `operator_console` \| `processor`) | framework + SRS extensions |
| SMM.15 | Network components | `NetworkDevice` (`role` = `switch` \| `router`) | framework |
| SMM.16 | Middleware Services | `Broker` | framework + SRS extensions |
| SMM.17 | Services of Communication Technologies | `CommunicationService` | SRS extension |

*(In Neo4j Community 5, every node additionally carries the storage-scoping base label `:ModelElement` indexed on `instance_id`; see ADR-0011 §2.)*

**Table 2. SRS relationship types → structural & derived relationships**

| SRS | SRS term | Structural relationship (`G_structural`) | Derived view (`G_analysis`) |
|---|---|---|---|
| SMM.18 | Running on Operator Console and Processor Units | `RUNS_ON` (`Application \| Broker \| CommunicationService → Node`) | Lifts into Rules 3, 4, 6 |
| SMM.19 | Using Middleware and Communication Services | `USES_SERVICE` (`Application \| Library → Broker \| CommunicationService`) + `ROUTES` (`Broker → Topic`) + `TRANSFERS` (`CommunicationService → Message \| Topic`) | Rule 2 (`app_to_broker`), Rule 4 (`node_to_broker`) |
| SMM.20 | Publishing data | `PUBLISHES_TO` (`Application \| Library → Topic`) + `SENDS` (`Application \| Library → Message`) | Rule 1 (`app_to_app`), Rule 2 (`app_to_broker`) |
| SMM.21 | Consuming data | `SUBSCRIBES_TO` (`Application \| Library → Topic`) + `RECEIVES` (`Application \| Library → Message`) | Rule 1 (`app_to_app`), Rule 2 (`app_to_broker`) |
| SMM.22 | Being dependent on a library or software unit | `USES` (`Application \| Library → Application \| Library`) | Rule 5 (`app_to_lib`) and Rule 1 (`app_to_app` for direct `App → App` `USES` and 1–3 hop `Library` chains) |
| SMM.23 | Assignment of a software unit to a role | `ASSIGNED_TO` (`Application \| Library → Role`) | — |

### 2. Node labels and queryable attributes (SMM.6–17, 24; DVE.32–46; SCG.4)

Every node carries `name` (its natural key within its label and instance, §6), `source_id` (positional Model Data ID if any), `origin` (`acquired` \| `edited`), and—for framework labels—`weight` and `weight_basis` (`complete` \| `partial`).

**Table 3. Node labels and core attributes**

| Label | Core attributes (framework attributes + SaaG SRS extensions) |
|---|---|
| `Application` | `version`, `app_type`, `criticality` (`HIGH` \| `MEDIUM` \| `LOW`, mapped via `saag` `canonical_criticality`), `hotstandby` (`bool`), `cm_*` code metrics *(framework)*; `is_candidate` (`bool`, SMM.31), **queryable scalar resource properties** `cpu_cores_requested` (`float`), `cpu_pinned_cores` (`int[]`), `cpu_dedicated` (`bool`), `high_performance` (`bool`, DVE.43), `memory_max_mb` (`int`, DVE.45), plus full JSON-Schema-validated `cpu_allocation`, `os_settings`, and `runtime_config` documents (SMM.24, DVE.41–46) |
| `Library` | `version`, `cm_*` code metrics *(framework)*; `is_candidate` (`bool`, MDG.15 / SMM.31) |
| `Topic` | `size` (bytes), `topic_frequency` (Hz, aliased from `frequency`, default `1.0` Hz marked `partial`), `topic_criticality`, `qos_reliability`, `qos_durability`, `qos_transport_priority`, `qos_deadline_ms`, `qos_history_depth`, `subscriber_count`, `publisher_count` *(framework)*; **`qos_lifespan_ms`** (`int`, **DVE.34**), `type_definition_hash`, `definition_conflict` (`bool`, **DVE.38**), and `field_schema` (JSON array `[{name, type, min, max, unit}]`, **SCG.4**) |
| `Broker` | `type`, `max_connections`, `host` *(framework)*; `version` *(extension)* |
| `Node` | `kind` (`operator_console` \| `processor`), `cpu_cores` (`int`), `memory_gb` (`float`), `os_type`, `ip_address`, `link_load_mbps`, `max_link_utilization` *(framework)*; `os_settings` (JSON + promoted scalars `isolated_cores`, `rt_throttling`, SMM.24 / DVE.44), plus UI cabinet attributes `group`, `hw`, `mw`, `gpu`, `display` (ADR-0008, ADR-0015) |
| `NetworkDevice` | `role` (`switch` \| `router`), `link_load_mbps`, `max_link_utilization` *(framework)* |
| `System`, `SoftwareSegment`, `CSCI`, `CSC` | `display_name`, `description` (`name` is hierarchically qualified for `SoftwareSegment`, `CSCI`, `CSC`, §6) |
| `Role` | `description` |
| `Message` | `message_id`, `size_bytes`, `frequency` (Hz, DVE.55–56), `fields_hash`, `field_schema` (`[{name, type, min, max, unit}]`, SCG.4) |
| `CommunicationService` | `technology` (e.g. `TCP`, `UDP`, `gRPC`, `REST`, `DDS-Bridge`, `Serial`), `version`, `protocol_family` |
| `Model` | Singleton per instance: `project`, `platform`, `system_version`, `model_data_artifact_id`, `model_data_sha256`, `created_at`, `status`, `weighting_profile` (SMM.5, 26) |

### 3. Structural and derived relationships

**Table 4. Structural relationships ($G_{\text{structural}}$)**

| Type | Allowed `From → To` | Attributes |
|---|---|---|
| `PUBLISHES_TO` | `Application \| Library → Topic` | `weight = w(Topic)`, `qos_reliability`, `qos_durability`, `qos_transport_priority` *(framework)*; **`declared_qos_lifespan_ms`**, **`declared_type_hash`**, **`declared_size`** (preserves per-publisher definitions so **DVE.32–35** RxO mismatches and **DVE.38** same-name content conflicts are directly queryable!) |
| `SUBSCRIBES_TO` | `Application \| Library → Topic` | Same attributes as `PUBLISHES_TO` (`declared_*` captures subscriber expectations for **DVE.32–35, 38**) |
| `ROUTES` | `Broker → Topic` | `weight = w(Topic)`, `qos_reliability`, `qos_durability`, `qos_transport_priority` |
| `RUNS_ON` | `Application \| Broker \| CommunicationService → Node` | — |
| `USES` | `Application \| Library → Application \| Library` | `dependency_kind` (`library` \| `unit`, satisfying **SMM.22** and **DVE.47** unit cycles) |
| `CONNECTS_TO` | `Node \| NetworkDevice — Node \| NetworkDevice` | `from_interface`, `to_interface`, `capacity_mbps` (`bandwidth_gbps × 1000`), `load_mbps`, `utilization` (stored once, traversed undirected per framework §5.2) |
| `CONTAINS` | `System → SoftwareSegment → CSCI → CSC → Application \| Library` | — |
| `ASSIGNED_TO` | `Application \| Library → Role` | — |
| `CARRIES` | `Topic → Message` | — |
| `USES_SERVICE` | `Application \| Library → Broker \| CommunicationService` | `direction` (`send` \| `receive` \| `bidirectional`), `source_endpoint`, `destination_endpoint`, `protocol` (**SMM.19, DVE.39**) |
| `TRANSFERS` | `CommunicationService → Message \| Topic` | `direction` (`external_to_mw` \| `mw_to_external` \| `bidirectional`), `source`, `destination` (enables **DVE.39** mutual-consistency verification across `Application ↔ CommunicationService ↔ Message/Topic ↔ Broker`) |
| `SENDS` | `Application \| Library → Message` | — |
| `RECEIVES` | `Application \| Library → Message` | — |

**Derived dependency view ($G_{\text{analysis}}$):** contains only `DEPENDS_ON` (`dependent → dependency`, opposite to data flow), carrying `dependency_type`, `weight`, `path_count`, and `origin = 'derived'`. Rules 1–7 match `SoftwareAsAGraph @ 0bbe06af` (`saag/infrastructure/neo4j_repo.py` and `memory_repo.py`):

**Table 5. Dependency derivation rules (`saag @ 0bbe06af` §6.1 + SMM.22 direct unit `USES`)**

| Rule | `dependency_type` | Exact derivation pattern | Edge weight & `path_count` |
|---|---|---|---|
| 1 | `app_to_app` | Union over distinct shared `Topic`s of: (a) direct `(sub:Application\|Library)-[:SUBSCRIBES_TO]->(t)<-[:PUBLISHES_TO]-(pub:Application\|Library)` (`sub <> pub`), (b) `(app:Application)-[:USES*1..3]->(lib:Library)-[:SUBSCRIBES_TO]->(t)<-[:PUBLISHES_TO]-(pub)`, and (c) `(sub)-[:SUBSCRIBES_TO]->(t)<-[:PUBLISHES_TO]-(lib:Library)<-[:USES*1..3]-(app:Application)`, **plus** direct declared `(a:Application)-[:USES]->(b:Application)` (`SMM.22`) | Topic-mediated: probabilistic union $1 - \prod_{t}(1 - w(t))$ over distinct topics $t$, `path_count = \|{t}\|`; direct `App → App` `USES` combined via $1 - (1 - w_{\text{topics}})(1 - \text{HM}(w(a), w(b)))$ |
| 2 | `app_to_broker` | Union over distinct `Topic`s of direct `(c:Application\|Library)-[:PUBLISHES_TO\|SUBSCRIBES_TO]->(t)<-[:ROUTES]-(b:Broker)` and `(app:Application)-[:USES*1..3]->(lib:Library)-[:PUBLISHES_TO\|SUBSCRIBES_TO]->(t)<-[:ROUTES]-(b:Broker)` | Probabilistic union $1 - \prod_{t}(1 - w(t))$, `path_count = \|{t}\|` |
| 3 | `node_to_node` | `Node B → Node A` (`B <> A`) when a component on `B` has **`DEPENDS_ON` (`app_to_app` OR `app_to_broker`)** to a component on `A` (evaluating all `RUNS_ON` hosts for `hotstandby` units) | Worst-case lift $\max w(d)$, `path_count = count(d)` |
| 4 | `node_to_broker` | `Node n → Broker b` when an `Application` hosted on `n` has `DEPENDS_ON {app_to_broker}` to `b` (including same-node brokers) | Worst-case lift $\max w(d)$, `path_count = count(d)` |
| 5 | `app_to_lib` | `(c:Application\|Library)-[:USES]->(lib:Library)` | Harmonic mean $\frac{2\cdot w(c)\cdot w(\text{lib})}{w(c) + w(\text{lib})}$, `path_count = 1` |
| 6 | `broker_to_broker` | Bidirectional between two distinct `Broker`s co-hosted via `RUNS_ON` on one or more shared `Node`s | $\max_{n \in \text{shared}} w(n)$, `path_count = \|\text{shared}\|` |
| 7 | `node_to_device` | `Node B → NetworkDevice d` when `B` and `A` (`B -[:DEPENDS_ON {node_to_node}]-> A`) lie in the same connected `CONNECTS_TO` island initially and removing `d` separates `B` from `A` | Worst-case lift $\max w(B \to A)$, `path_count` = carried `node_to_node` pairs |

### 4. Weights (`saag-graph-model@0bbe06af`)

Every framework node and topic-carrying structural edge carries `weight` $\in [0.01, 1.0]$, matching `SoftwareAsAGraph @ 0bbe06af` (§5.3–5.4, §6.3):

* **Topic:** $w(t) = \text{clamp}_{[0.01, 1.0]}\!\left(0.75\cdot\text{QoS}(t) + 0.15\cdot\text{SizeNorm}(t) + 0.10\cdot\text{FreqNorm}(t)\right)$, with AHP QoS weights `0.24` (reliability), `0.62` (durability), and `0.14` (transport priority) over raw `size` and `topic_frequency`.
* **Application and Broker:** power mean ($p = 3$) of incident `Topic` weights; an `Application` with no direct `Topic` takes the maximum weight of the `Library` / `Application` targets it `USES` (or `0.01` floor).
* **Library (saturating fanout lift from `d1419ae7` / `0bbe06af`):** let $\text{base\_w}$ be the maximum weight across the library's own `Topic`s and its direct `USES` consumers, and $\text{DG}_{\text{in}}$ be its direct `USES` consumer count:
  $$w(\text{lib}) = \text{clamp}_{[0.01, 1.0]}\!\left(1 - (1 - \text{base\_w})\cdot(1 + \text{DG}_{\text{in}})^{-0.15}\right)$$
* **Node:** maximum weight of hosted `Application`s and `Broker`s. **NetworkDevice:** maximum weight of `Node`s depending on it via Rule 7.
* **Static link-load baseline:** SMM also ports `saag`'s Phase 5c `_calculate_network_load` (`load_mbps`, `utilization` on `CONNECTS_TO`, `max_link_utilization` on `Node`/`NetworkDevice`) so R3/R6 bandwidth rules have nominal link utilization ready.
* **Extension labels (`System`, `SoftwareSegment`, `CSCI`, `CSC`, `Role`, `Message`, `CommunicationService`):** `weight` is omitted (`null`).

### 5. Layer projections

Analyses use the four projections of `saag @ 0bbe06af` §7 unchanged: `app` (`Application`, `Library`; `app_to_app`, `app_to_lib`), `infra` (`Node`, `NetworkDevice`; `node_to_node`, `node_to_device`), `mw` (`Application`, `Broker`, `Node` with `Broker`s scored; `app_to_broker`, `node_to_broker`, `broker_to_broker`), and `system` (all six framework labels and all seven rules). Verification rules in ADR-0016 query the full graph (including all SRS extension labels and relationships).

### 6. Identity, placeholders and construction error boundary (SMM.25 vs. DVE.48)

* **Identity keys:** `(label, name)` is unique within a model instance. To prevent name collisions across subsystems, `SoftwareSegment`, `CSCI`, and `CSC` use slash-qualified hierarchical keys (`<system>/<segment>`, `<system>/<segment>/<csci>`, `<system>/<segment>/<csci>/<csc>`) with short names in `display_name`. All other labels use their canonical system-unique `name`.
* **Placeholders:** fields listed in Model Data `placeholders` (ADR-0009) are omitted (`null`) and listed in `placeholder_reasons` on the element; weights computed using framework defaults carry `weight_basis = 'partial'`.
* **Construction error boundary (`SMM.25` vs. `DVE.48`):**
  * During `SMM` construction, if a relationship references a non-existent endpoint key (`category = missing_entity`) or an endpoint label pair disallowed by Table 4 (`category = invalid_relationship`), SMM records an `ErrorRecord` (SMM.25, ADR-0009) and skips creating that malformed edge **without aborting valid nodes and edges** (unless critical schema validation in SMM.3 fails).
  * Structurally valid nodes with zero incident edges (isolated/disconnected nodes), topics without publishers or subscribers (`DVE.36–37`), conflicting topic definitions (`DVE.38`), and incomplete communication bridges (`DVE.39, 48`) **are constructed into the System Model** so DVE's structural verification rules (`DVE.36–48`, `TC-DVE-08`) can inspect and report them as findings!

### 7. Implementation and lifecycle in SMM

* SMM implements `schema.py`, weight calculation (§4), Phase 5c link load, and Rules 1–7 (§3) in pure Python 3.9 under `smm/src/smm/graph/` (using `networkx==3.2.1` only where graph algorithms require it), with parity fixtures copied from `SoftwareAsAGraph @ 0bbe06af` into `smm/tests/fixtures/framework_0bbe06af/`.
* Working models mutate only $G_{\text{structural}}$; SMM recomputes weights and $G_{\text{analysis}}$ (`DEPENDS_ON`) atomically on every edit (ADR-0006 §2, ADR-0011 §3). AED is bound externally via ADR-0012 and never mutates either view.

### Consequences

* Good, because all 12 SRS node types, all 6 SRS relationship families, `DVE.34` Lifespan, `DVE.38` topic conflicts, `DVE.39` service consistency, `SMM.22` unit-to-unit `USES`, `SMM.24` scalar+JSON resource configs, and `SCG.4` field schemas have exact, Cypher-queryable homes.
* Good, because upgrading to `saag @ 0bbe06af` fixes the earlier library-weight clamping and Rule 1–4 multi-host/path-union parity bugs before R3 code is written.
* Bad, because maintaining two vocabularies (SRS terms vs. framework labels) requires Tables 1–2 as the normative lookup in SDD §2.4 and §3.5.
* Bad, because re-implementing derivation in Python 3.9 requires parity fixture tests to prevent drift from `SoftwareAsAGraph`.

### Confirmation

* `smm/src/smm/graph/schema.py` declares all labels, relationship endpoint pairs and attribute schemas; construction tests exercise every Table 3 label and Table 4 relationship, plus `missing_entity` and `invalid_relationship` reporting (`SMM.25`).
* Parity gate on CPython 3.9 reproduces `SoftwareAsAGraph @ 0bbe06af` §9 worked example exactly: **$w(T0) = 0.5938$, $w(L0) = 0.6555$, `app_to_lib` $= 0.6231$**, and all five derived edges (`A1→A0`, `A0→B0`, `A1→B0`, `A0→L0`, `A1→L0`), plus multi-host `hotstandby` and `USES*1..3` union cases.
* Verification-readiness test constructs a fixture containing a Lifespan mismatch (`DVE.34`), a same-name topic hash conflict (`DVE.38`), an inconsistent `CommunicationService` `TRANSFERS` flow (`DVE.39`), and an `Application → Application` `USES` cycle (`DVE.47`), confirming each is queryable on the graph.

## Pros and Cons of the Options

### Framework-aligned typed property graph (`saag @ 0bbe06af`) with SRS extensions (chosen)

* Good, because it preserves exact compatibility with `SoftwareAsAGraph` weights, layers and published benchmarks while covering 100% of SRS `SMM.6–24` and `DVE.28–58`.
* Neutral, because SRS terminology maps through Tables 1–2.
* Bad, because adding new vertex/edge types later requires a schema migration.

### Pure SRS-named property graph with translation layer

* Good, because Cypher labels match English SRS nouns verbatim.
* Bad, because every `saag` metric, layer projection and `mdg` serializer requires bidirectional translation, and `DEPENDS_ON` weights still have to be defined from scratch.

### Generic single-label graph (`:Entity` / `:RELATES`)

* Good, because arbitrary types require no label changes.
* Bad, because property-filtered traversals lose label-index selectivity and static schema safety.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `0bbe06af`](https://github.com/onuralpyigit/software-as-a-graph/blob/0bbe06afa12be228e343895322716b8cbd085535/docs/graph-model.md), §4–§7 and §9; `saag/infrastructure/neo4j_repo.py` and `memory_repo.py`
* [SRS §5.1.1, §6.1.2, §6.1.3](../../requirements/SRS.md)
* Code: `mdg/src/mdg/domain/model_setup_data_graph.py`, `mdg/src/mdg/domain/source_data.py`
* Related: ADR-0002, ADR-0007, ADR-0008, ADR-0009, ADR-0011, ADR-0012, ADR-0013, ADR-0015, ADR-0016, ADR-0017, ADR-0020, ADR-0021
* Revisit if `SoftwareAsAGraph` introduces a major v2 graph metamodel or if a future verification rule requires hyperedges or temporal structural versioning inside a single model instance.
