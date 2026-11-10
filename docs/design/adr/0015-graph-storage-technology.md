# ADR-0015: Graph storage technology

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Decide |
| Traces | SMM.1, 4, 27–31; DVE.17, 28–58; QA-02, QA-07 |
| Closes | CDR-29 (part: System Model, Working Model) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The System Model (ADR-0014) must be stored, queried by the verification rules (DVE.28–49), traversed by the behavioral analyses (DVE.53–58), and instantiated many times: one baseline per Model Data file, plus working models and per-operation candidate models (ADR-0016; SMM.29–31). SDP §5 names FalkorDB. Nothing is implemented yet.

Expected scale: UXD §6 sets the visualization level-of-detail threshold at 1,000 nodes. The dev seed has a handful of units. A real system is expected to have hundreds to a few thousand CSUs, topics and messages, which is well within any candidate's capacity. The deciding factors are therefore instance isolation, query language and operations cost, not raw scale.

## Decision Drivers

* Cheap creation and deletion of many isolated graph instances (QA-02).
* A declarative query language for the rules (ADR-0022), plus access to graph algorithms (cycles, reachability).
* Fit with the existing stack: Redis is already operated (ADR-0006).
* Licensing that permits on-premises internal use.

## Considered Options

* FalkorDB (SDP §5): a property graph with Cypher, as a Redis module, with many named graphs per server
* Neo4j Community Edition
* An in-process NetworkX graph, persisted as files
* PostgreSQL with the Apache AGE extension

## Decision Outcome

Chosen option: "FalkorDB", subject to the spike in *Confirmation*. Each model instance is one named graph (a Redis key). Instances are created with `GRAPH.COPY` and dropped with `GRAPH.DELETE`, which fits ADR-0016's instance model directly. Cypher (openCypher subset) suits declarative rules, and FalkorDB is served over the Redis protocol, which the team already operates.

* **Deployment:** a dedicated FalkorDB container with AOF persistence. It is separate from the Celery broker Redis, because the two have different persistence and eviction settings.
* **Access:** SMM owns the only adapter (`smm/adapters/falkordb_*`) behind an `IGraphStore` port. Other CSCs use SMM's façade (ADR-0007). Queries use parameters, never string-built Cypher.
* **Algorithms:** rules that need algorithms not expressible in Cypher may load the instance's subgraph into NetworkX inside the worker (ADR-0022). This is read-only, and the in-memory copy is discarded after the operation.
* **Fallback:** if the spike fails, the next candidate is PostgreSQL + AGE (named graphs, the same database as ADR-0008), then NetworkX with files.

### Consequences

* Good, because per-instance isolation is native and cheap, and there is no tenant filter in every query.
* Good, because Cypher rules are portable to other openCypher engines if this decision is superseded.
* Bad, because FalkorDB is licensed under SSPL v1. It is permitted for internal on-premises use, but it must be cleared with the project's licensing authority before acceptance.
* Bad, because it is a younger product than Neo4j, with a smaller Cypher feature set (e.g. limited procedures).
* Bad, because there is one more stateful service to back up (ADR-0040).

### Confirmation

A spike in R3 must pass the following before this ADR is accepted:

1. Load a synthetic model of 5,000 CSUs, 5,000 topics and 50,000 relationships in under 30 s.
2. `GRAPH.COPY` of that model in under 5 s.
3. Pub/sub-match and cycle-detection queries return in under 2 s.
4. Licensing is cleared.

The results are recorded in this ADR's *More Information*.

## Pros and Cons of the Options

### FalkorDB

* Good, because it has cheap named graphs and Cypher, it runs on the Redis protocol, and it is fast.
* Bad, because of the SSPL licence, product maturity, and a Cypher subset.

### Neo4j Community

* Good, because it is the most mature, with full Cypher and APOC/GDS (Community-licensed subsets).
* Bad, because Community Edition supports a single user database. Isolating many instances would need label- or property-based tenancy in every query. It is also GPLv3, and the server is heavyweight.

### NetworkX in process

* Good, because it is pure Python, has every algorithm, has no new service, and is trivial to copy.
* Bad, because it has no query language, each worker holds whole models in memory, persistence is serialization only, and access from UI queries is not shared.

### PostgreSQL + Apache AGE

* Good, because it reuses PostgreSQL (ADR-0008) and has named graphs and Cypher.
* Bad, because the extension is less mature, there is no copy-graph primitive, and query performance on traversals is weaker.

## More Information

* [SDP §5](../../planning/SDP.md), [UXD §6](../UXD.md)
* Related: ADR-0006, ADR-0014, ADR-0016, ADR-0022, ADR-0033, ADR-0040
