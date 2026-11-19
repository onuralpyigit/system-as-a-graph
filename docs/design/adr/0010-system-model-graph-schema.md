# ADR-0010: System Model graph schema aligned with the Software-as-a-Graph model

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | SMM.1, 4–25; DVE.19, 28–49, 53–58; QA-03, QA-07 |
| Resolves | DP-30d, DP-30f (SDD §2.4 entity schema of the System Model, also used by the Working Model per ADR-0011) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SMM.4 requires the validated Model Data to become a node-relationship System Model. SMM.6–17 name the node types, SMM.18–23 name the relationship types, and SMM.24 requires CPU allocation, OS settings and runtime configuration as queryable attributes. SMM.5 and SMM.26 tie each model to a project, platform, system version and Model Data file. Every R3 verification rule (DVE.31–49) is written against this schema, and the R6 propagation analyses (DVE.53–58) traverse it, so it must be fixed first.

The Software-as-a-Graph (SaaG) research framework already defines a typed multigraph for publish-subscribe systems: [`docs/graph-model.md`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md) at commit `d1f8b424` (called **the framework model** below). It has six vertex types, six structural edge types, a derived `DEPENDS_ON` edge produced by seven rules, QoS-driven weights, and four layer projections. Its derived dependency graph is the one the JSS manuscript evaluates (§3.1–3.3).

MDG already emits the framework model's vocabulary. As of commit `1157784`, the Model Data `graph` section (ADR-0009) has:

* the entities `nodes`, `networks`, `applications`, `libraries`, `topics` and `messages`;
* the relationships `runs_on`, `publishes_to`, `subscribes_to`, `sends`, `receives`, `uses` and `connects_to`;
* the framework's ID scheme (`N0`, `A0`, `L0`, `T0`), plus `M0` for messages and `W0` for networks.

It has no SRS hierarchy, role, broker or communication-service nodes. The hierarchy is present only as the `system_hierarchy` attribute (CMDB columns `csms_name`, `css_name`, `csci_name`, `csc_name`), and the role only as the `role` attribute.

The framework's reference implementation (`saag` 1.0.0) requires networkx ≥ 3.4, numpy ≥ 2.1 and scipy ≥ 1.15, so it needs Python ≥ 3.10. The SaaG target host runs CPython 3.9 (ADR-0004), so SMM cannot import the framework at run time.

The question is: what are the System Model's node labels, relationship types, identity keys and attributes, and how does the model relate to the framework model's derived dependency view?

## Decision Drivers

* Every SRS node and relationship type must be representable and queryable by type (SMM.6–24, DVE.19).
* The analyses, metrics, test corpus and published results of the framework model should apply to the System Model without translation.
* Rules must address entities by keys that are stable across model instances (working and candidate models, ADR-0011) and across system versions (drift, DVE.66–68).
* Acquired facts, derived values and placeholders must stay distinguishable (QA-03, ADR-0009).
* Structural facts and derived analysis must stay separate, so editing or re-deriving one never corrupts the other (framework model §2.5).
* The schema must map onto a labeled property graph without depending on one engine's features (ADR-0011).

## Considered Options

* Framework-aligned typed property graph, extended with the SRS-only types, with a structural view and a derived dependency view
* SRS-named typed property graph (`CSU`, `ProcessingUnit`, `PUBLISHES`, `CONSUMES`, …) with a mapping table to the framework model
* Generic graph: one `Entity` label with a `type` property and one `RELATES` edge with a `kind` property

## Decision Outcome

Chosen option: "Framework-aligned typed property graph, extended with the SRS-only types, with a structural view and a derived dependency view", because it is the only option that serves both the SRS vocabulary and the framework's analyses unchanged. MDG already produces this vocabulary, and typed labels keep rules readable and indexable. Version scoping is per model instance (ADR-0011), not per element.

### 1. SRS to schema mapping

The framework model supplies the core pub-sub vocabulary. SRS concepts with no framework counterpart are added as **extension** labels and relationships.

**Table 1. SRS node types → labels**

| SRS | SRS term | Label | Source |
|---|---|---|---|
| SMM.6 | System | `System` | extension |
| SMM.7 | Software Segment | `SoftwareSegment` | extension |
| SMM.8 | CSCI | `CSCI` | extension |
| SMM.9 | CSC | `CSC` | extension |
| SMM.10 | CSU | `Application` (executable unit) or `Library` (shared unit) | framework |
| SMM.11 | Role | `Role` | extension |
| SMM.12 | Topic | `Topic` | framework |
| SMM.13 | Message | `Message` | extension |
| SMM.14 | Operator console and processor units | `Node` with `kind` = `operator_console` \| `processor` | framework |
| SMM.15 | Network components | `NetworkDevice` with `role` = `switch` \| `router` | framework |
| SMM.16 | Middleware services | `Broker` | framework |
| SMM.17 | Services of communication technologies | `CommunicationService` | extension |

A CSU is split into `Application` and `Library` because the framework weights them differently (§4) and because SMM.22 names libraries explicitly. Both carry the CSU's hierarchy through `CONTAINS`.

**Table 2. SRS relationship types → relationship types**

| SRS | SRS term | Relationship type |
|---|---|---|
| SMM.18 | Running on operator console and processor units | `RUNS_ON` |
| SMM.19 | Using middleware and communication services | `USES_SERVICE` (declared), and derived `DEPENDS_ON {app_to_broker}` (via `ROUTES`) |
| SMM.20 | Publishing data | `PUBLISHES_TO` |
| SMM.21 | Consuming data | `SUBSCRIBES_TO` |
| SMM.22 | Being dependent on a library or software unit | `USES` (declared), and derived `DEPENDS_ON {app_to_lib, app_to_app}` |
| SMM.23 | Assignment of a software unit to a role | `ASSIGNED_TO` |

### 2. Node labels

Every node has `name` as its key (see §6), `source_id` (the Model Data `id`, if any), `origin` and `weight`. Attribute names follow the framework model §5.1.

**Table 3. Node labels**

| Label | Source | Core attributes |
|---|---|---|
| `Application` | framework | `version`, `app_type`, `criticality` (`HIGH` \| `MEDIUM` \| `LOW`), `hotstandby`, `is_candidate`, `cm_*` code metrics; `cpu_allocation`, `runtime_config` (SMM.24) |
| `Library` | framework | `version`, `cm_*` code metrics |
| `Topic` | framework | `size` (bytes), `frequency` (Hz), `qos_reliability`, `qos_durability`, `qos_transport_priority`, `qos_deadline_ms`, `qos_history_depth`, `type_definition_hash`; `subscriber_count`, `publisher_count` (derived) |
| `Broker` | framework | `type`, `version`, `max_connections` |
| `Node` | framework | `kind`, `cpu_cores`, `memory_gb`, `os_type`, `ip_address`; `os_settings` (SMM.24) |
| `NetworkDevice` | framework | `role` |
| `System`, `SoftwareSegment`, `CSCI`, `CSC` | extension | `description` |
| `Role` | extension | `description` |
| `Message` | extension | `size_bytes`, `fields_hash` |
| `CommunicationService` | extension | `technology`, `version` |
| `Model` | SaaG | one per model instance; see §6 |

### 3. Relationship types

The **structural view** (the framework's $G_{\text{structural}}$) holds the relationships built from Model Data and edited in working models.

**Table 4. Structural relationships**

| Type | From → To | Source | Attributes |
|---|---|---|---|
| `PUBLISHES_TO` | Application \| Library → Topic | framework | `weight` = w(Topic) |
| `SUBSCRIBES_TO` | Application \| Library → Topic | framework | `weight` = w(Topic) |
| `ROUTES` | Broker → Topic | framework | `weight` = w(Topic) |
| `RUNS_ON` | Application \| Broker → Node | framework | — |
| `USES` | Application \| Library → Library | framework | — |
| `CONNECTS_TO` | Node \| NetworkDevice — Node \| NetworkDevice (undirected) | framework | `from_interface`, `to_interface`, `capacity_mbps` |
| `CONTAINS` | System → SoftwareSegment → CSCI → CSC → Application \| Library | extension | — |
| `ASSIGNED_TO` | Application → Role | extension | — |
| `CARRIES` | Topic → Message | extension | — |
| `USES_SERVICE` | Application → Broker \| CommunicationService | extension | — |
| `SENDS` | Application → Message | extension | — (from Model Data `sends`) |
| `RECEIVES` | Application → Message | extension | — (from Model Data `receives`) |

`CONNECTS_TO` is stored once, in the direction the source lists it, and read as undirected (framework model §5.2). Its topology comes from ADR-0008.

The **derived dependency view** (the framework's $G_{\text{analysis}}$) holds only `DEPENDS_ON`. It points from the **dependent** to the **dependency**, which is opposite to the data flow. Each edge carries `dependency_type`, `weight`, `path_count` and `origin = derived`.

**Table 5. Dependency derivation rules (framework model §6.1)**

| Rule | `dependency_type` | Derived from | Edge weight |
|---|---|---|---|
| 1 | `app_to_app` | subscriber → publisher of a shared Topic, following `USES` chains up to 3 hops | probabilistic union $1-\prod(1-w(t))$ |
| 2 | `app_to_broker` | Application → Broker that `ROUTES` a Topic it publishes or subscribes to | probabilistic union |
| 3 | `node_to_node` | Node B → Node A when an Application on B depends on one on A | worst-case lift $\max w$ |
| 4 | `node_to_broker` | Node → Broker used by an Application it hosts | worst-case lift |
| 5 | `app_to_lib` | `USES` | harmonic mean of w(Application) and w(Library) |
| 6 | `broker_to_broker` | two Brokers that run on the same Node (both directions) | max weight of the shared Nodes |
| 7 | `node_to_device` | Node B → NetworkDevice d when d separates B from a Node it depends on | worst-case lift |

The rules are adopted as written in the framework model, which is their normative definition. SaaG does not redefine them. Extension relationships do not create `DEPENDS_ON` edges.

### 4. Weights

Every node and relationship carries `weight` in $[0.01, 1.0]$, computed as in the framework model §5.3–5.4 and §6.3:

* **Topic:** $w(t) = 0.75\cdot\text{QoS}(t) + 0.15\cdot\text{SizeNorm}(t) + 0.10\cdot\text{FreqNorm}(t)$, clamped. QoS uses the AHP weights 0.24 (reliability), 0.62 (durability) and 0.14 (transport priority).
* **Application and Broker:** power mean ($p = 3$) of the weights of their Topics. An Application with no direct Topic takes the maximum weight of the Libraries it uses.
* **Library:** the maximum of its Topic and consumer weights, scaled by $1 + 0.15\cdot\log_2(1 + \text{consumers})$.
* **Node:** the maximum weight of what runs on it. **NetworkDevice:** the maximum weight of the Nodes that depend on it (Rule 7).
* **Extension labels:** `weight` is absent. They are not part of the weighted analysis.

The constants above form the **weighting profile** `saag-graph-model@d1f8b424`. The `Model` node records the profile it was built with. Changing a constant creates a new profile, not a new schema.

### 5. Layer projections

Analyses run on the four projections of the framework model §7, unchanged:

| Layer | Nodes | `dependency_type` |
|---|---|---|
| `app` | Application, Library | `app_to_app`, `app_to_lib` |
| `infra` | Node, NetworkDevice | `node_to_node`, `node_to_device` |
| `mw` | Application, Broker, Node (only Brokers are scored) | `app_to_broker`, `node_to_broker`, `broker_to_broker` |
| `system` | all framework labels | all seven |

Extension labels are not part of any projection. Verification rules can still query them on the full graph.

### 6. Conventions

* **Identity:** `(label, name)` is unique within a model instance and stable across instances and versions. Drift detection, working-model diffs and finding references (ADR-0007) match on it. The Model Data `id` (`A0`, `T3`, …) is stored as `source_id` only, because MDG assigns it by sorting names within one run, so it changes between runs.
* **Provenance:** every node and relationship carries `origin`: `acquired` (from Model Data), `derived` (computed by SMM: weights, counts and every `DEPENDS_ON`), or `edited` (working model, ADR-0011).
* **Placeholders:** a value listed in the Model Data `placeholders` (ADR-0009) is stored as absent, with `placeholder_reasons`. Rules treat it as unknown. A weight computed from an absent value or a framework default (for example the 1 Hz default frequency) is still stored, with `weight_basis = partial`. Otherwise `weight_basis = complete`.
* **Structured attributes:** `cpu_allocation`, `os_settings` and `runtime_config` (SMM.24) are JSON-encoded properties, each with its own JSON Schema, so rules can parse them.
* **Model metadata:** project, platform, system version, Model Data file reference and SHA-256, creation time, status and weighting profile (SMM.5, 26) live on the `Model` node and in the instance registry (ADR-0011). They are not repeated on every element.
* **Construction errors:** a relationship whose endpoint is missing, or whose endpoint labels are not allowed by Table 4, is not created. It is reported as an invalid-relationship error (SMM.25, ADR-0009).

### 7. Implementation in SMM

* SMM implements this schema, the weights (§4) and the seven derivation rules (§3) itself, in pure Python that runs on CPython 3.9, in `smm/src/smm/graph/`. It does not import the `saag` package at run time. If it needs graph algorithms, it uses networkx 3.2.1, the last release that supports Python 3.9.
* The framework model at `d1f8b424` stays the normative definition. The port is held to it by parity fixtures copied into `smm/tests/fixtures/framework_d1f8b424/`: the §9 worked example, plus any framework test scenario used to check derivation. Adopting a newer framework revision means refreshing the fixtures and the weighting profile in one pull request.
* The in-memory implementation is also the derivation engine that ADR-0011's graph-store adapter writes from, and the fake used in tests.

### 8. Lifecycle

1. SMM builds the structural view from validated Model Data (the framework's Import stage).
2. SMM computes the weights and derives the dependency view (the framework's Pre-Analysis stage).
3. Working models edit only the structural view. The dependency view and the weights are recomputed after each edit and are never edited directly.
4. Analytical Evaluation Data is bound alongside, never inside, either view (ADR-0012).

### Consequences

* Good, because the framework's metrics, prediction and simulation pipelines, its scenario corpus and its published results apply to SaaG models without translation.
* Good, because every SRS type has a home (Tables 1–2), and rules read naturally: `MATCH (a:Application)-[:PUBLISHES_TO]->(t:Topic)`.
* Good, because the dependency view directly supports the propagation analyses (DVE.53–58), and the weights let rules rank by criticality.
* Good, because stable keys support working-model diffs, candidate comparison and drift.
* Bad, because there are two vocabularies (SRS terms and framework labels). Tables 1–2 are the single mapping, and the SDD uses them.
* Bad, because SaaG depends on a framework revision. A later framework schema change is adopted only through a new ADR or a new weighting profile.
* Bad, because the derivation rules and weights are re-implemented rather than imported. The parity fixtures are the only guard against divergence.
* Bad, because the Model Data must gain sections for hierarchy, roles, brokers, communication services and node capacity. Until then, `CONTAINS` is built from the `system_hierarchy` attribute (`csms_name` → `System`, `css_name` → `SoftwareSegment`, `csci_name` → `CSCI`, `csc_name` → `CSC`), `ASSIGNED_TO` from the `role` attribute, Model Data `networks` become `NetworkDevice` with `role = switch`, and `Broker` and `CommunicationService` stay empty.
* Bad, because derivation adds construction cost on large models. Budgets are set in ADR-0020.
* Follow-up: update SDD §2.4 (System Model store) and §3.5 to cite this ADR; on acceptance, replace the "to be determined during the critical design phase" wording for the System Model schema in SDD §2.4 with a link to this ADR.

### Confirmation

* The schema is declared once in code (`smm/src/smm/graph/schema.py`): labels, relationship types, allowed endpoint labels and attribute schemas. Construction rejects anything not declared there.
* A construction test uses a Model Data fixture that covers every label and relationship type.
* A parity test reproduces the framework model's worked example (§9) from the copied fixtures: $w(T0) = 0.5938$, $w(L0) = 0.7350$, `app_to_lib` weight 0.6569, and exactly its five derived edges. It runs on Python 3.9.
* A construction test builds a model from a Model Data file produced from the `dev/` seed, including `messages`, `networks`, `sends`, `receives` and `connects_to`.
* A test asserts that every `DEPENDS_ON` has `origin = derived` and that no extension relationship produces one.

## Pros and Cons of the Options

### Framework-aligned typed property graph with SRS extensions (chosen)

* Good, because it matches MDG's output and the framework's analyses, and it covers the SRS through extensions.
* Good, because the structural/derived split keeps facts and analysis separable.
* Neutral, because SRS terms must be looked up in the mapping tables.
* Bad, because it has a rigid vocabulary: a new type needs a schema change.

### SRS-named typed property graph with mapping

* Good, because labels match the SRS word for word.
* Bad, because every framework analysis needs a translation layer, and MDG's output needs renaming.
* Bad, because it has no defined dependency view or weights, so DVE.53–58 would need another decision.

### Generic single label

* Good, because new types need no schema change.
* Bad, because every query filters on a property, which is slower and harder to read, and type errors are not caught.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `d1f8b424`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md), §4 (formal definition), §5 (weights), §6 (derivation rules), §7 (layers), §9 (worked example)
* [SRS §5.1.1](../../requirements/SRS.md)
* Code: `mdg/src/mdg/domain/model_setup_data_graph.py`, `mdg/src/mdg/domain/source_data.py`; framework `pyproject.toml` (Python and dependency floors)
* Related: ADR-0002, ADR-0008, ADR-0009, ADR-0011, ADR-0012, ADR-0016, ADR-0007, ADR-0017, ADR-0020
* Revisit if the framework model changes its vertex or edge types, or if a verification rule needs a type that Tables 3–4 lack.
