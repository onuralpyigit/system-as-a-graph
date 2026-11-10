# ADR-0014: System Model graph schema

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | SMM.4–25; DVE.19, 28–49; QA-03 |
| Closes | CDR-30 (part: System Model) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SMM.6–17 name the node types, SMM.18–23 name the relationship types, and SMM.24 requires CPU allocation, OS settings and runtime configuration as queryable attributes. SMM.5 requires each model to be associated with project, platform and system version.

The Model Data graph section (ADR-0013) has only part of this vocabulary: `nodes` (processor units), `applications`, `libraries`, `topics`, and the relationships `runs_on`, `publishes_to`, `subscribes_to` and `uses`. Every verification rule in R3 (DVE.31–49) is written against the schema, so the schema must be fixed first.

## Decision Drivers

* Every SRS node and relationship type must be representable and queryable by type (SMM.6–24, DVE.19).
* Rules must be able to address entities by stable keys across model instances (working and candidate models, ADR-0016) and across versions (drift, DVE.66–68).
* Attribute provenance (acquired, derived or placeholder) must be visible to rules (QA-03).
* The schema should map directly onto a labeled property graph (ADR-0015) without coupling to one engine's features.

## Considered Options

* A labeled property graph with one label per SRS node type and one relationship type per SRS relationship
* A generic graph: a single `Entity` label with a `type` property, and a single `RELATES` edge with a `kind` property
* A version-stamped single graph: all versions in one graph, with version properties on every element

## Decision Outcome

Chosen option: "A labeled property graph with one label per SRS node type and one relationship type per SRS relationship". Typed labels make rules readable and indexable, and they map 1:1 to the SRS. Version scoping is handled per model instance (ADR-0016), not per element.

**Node labels (SMM.6–17):**

| Label | SRS | Key (unique within a model instance) | Core attributes |
|---|---|---|---|
| `System` | SMM.6 | `name` | — |
| `SoftwareSegment` | SMM.7 | `name` | — |
| `CSCI` | SMM.8 | `name` | — |
| `CSC` | SMM.9 | `name` | — |
| `CSU` | SMM.10 | `name` | `version`, `criticality`, `is_candidate`, `cpu_allocation`, `runtime_config` (SMM.24) |
| `Role` | SMM.11 | `name` | — |
| `Topic` | SMM.12 | `name` | `qos_durability`, `qos_reliability`, `qos_lifespan`, `qos_transport_priority`, `type_definition_hash` |
| `Message` | SMM.13 | `name` | `size_bytes`, `fields_hash` |
| `ProcessingUnit` | SMM.14 | `name` | `kind` (`operator_console` / `processor`), `cores`, `ram_mb`, `os_settings` (SMM.24) |
| `NetworkComponent` | SMM.15 | `name` | `kind`, `bandwidth_mbps` |
| `MiddlewareService` | SMM.16 | `name` | `version` |
| `CommunicationService` | SMM.17 | `name` | `technology` |

Libraries in the Model Data (`libraries`) are `CSU` nodes with `kind = "library"`. That matches SMM.22 ("dependent on a library or software unit").

**Relationship types (SMM.18–23), plus containment:**

| Type | From → To | SRS |
|---|---|---|
| `RUNS_ON` | CSU → ProcessingUnit | SMM.18 |
| `USES_SERVICE` | CSU → MiddlewareService / CommunicationService | SMM.19 |
| `PUBLISHES` | CSU → Topic | SMM.20 |
| `CONSUMES` | CSU → Topic | SMM.21 (Model Data `subscribes_to`) |
| `DEPENDS_ON` | CSU → CSU | SMM.22 (Model Data `uses`) |
| `ASSIGNED_TO` | CSU → Role | SMM.23 |
| `CONTAINS` | System → SoftwareSegment → CSCI → CSC → CSU | hierarchy implied by SMM.6–10 |
| `CARRIES` | Topic → Message | SMM.12–13 |
| `CONNECTED_TO` | ProcessingUnit → NetworkComponent | topology (ADR-0011) |

**Attribute conventions:**

* Scalar attributes are flat properties. Structured settings (`cpu_allocation`, `os_settings`, `runtime_config`) are JSON-encoded properties with a schema per attribute, so rules can parse them.
* Every node and relationship carries `origin`: `acquired` (from Model Data), `derived` (computed by SMM), or `edited` (working model, ADR-0016). A value listed in the Model Data `placeholders` (ADR-0013) is stored as absent, with `placeholder_reasons`. Rules treat it as unknown, never as a value.
* Identity: `(label, key)` is unique within a model instance and stable across instances and versions. Drift detection and working-model diffs match on it.
* Model-level metadata (project, platform, system version, Model Data file reference and hash, creation time, status; SMM.5, 26) lives on one `Model` node per instance and in the instance registry (ADR-0016). It is not repeated on every element.

**Construction errors:** a relationship whose endpoint is missing is not created. It is reported as an invalid-relationship error (SMM.25, ADR-0034).

### Consequences

* Good, because rules are written against SRS vocabulary (`MATCH (c:CSU)-[:PUBLISHES]->(t:Topic)`), and each SRS item has an obvious home.
* Good, because stable keys support working-model diffs, candidate comparison and drift.
* Bad, because adding a node type requires a schema change (and this ADR is superseded). This is intentional.
* Bad, because the Model Data graph section must gain the missing sections (hierarchy, roles, messages, services, topology). Until it does, those labels are empty.

### Confirmation

* The schema is declared once in code (`smm/schema.py`). Model construction rejects labels and types not declared there.
* A construction test uses a Model Data fixture that covers every label and relationship type.

## Pros and Cons of the Options

### Typed labeled property graph

* Good, because it is readable, indexable and maps 1:1 to the SRS.
* Bad, because it has a rigid vocabulary.

### Generic single label

* Good, because new types need no schema change.
* Bad, because every query filters on a property, which is slower and harder to read. Type errors are not caught.

### Version-stamped single graph

* Good, because there is one graph to manage.
* Bad, because every query needs a version filter, and isolating working and candidate models becomes error-prone.

## More Information

* [SRS §5.1.1](../../requirements/SRS.md)
* Code: `mdg/src/mdg/domain/model_setup_data_graph.py`
* Related: ADR-0011, ADR-0013, ADR-0015, ADR-0016, ADR-0022
