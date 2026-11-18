# ADR-0015: Graph storage technology behind the Software-as-a-Graph repository port

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-17 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Decide |
| Traces | SMM.1, 4, 27–31; DVE.17, 28–58; QA-02, QA-07, QA-11 |
| Closes | CDR-29 (part: System Model, Working Model) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

<!-- English is normative. Update 0015-graph-storage-technology.tr.md in the same pull request. -->

## Context and Problem Statement

The System Model (ADR-0014) must be stored, queried by the verification rules (DVE.28–49), traversed by the behavioral analyses (DVE.53–58), and instantiated many times: one baseline per Model Data file, plus working models and per-operation candidate models (ADR-0016; SMM.29–31). ADR-0016 and ADR-0033 assume that an instance is a named graph that can be copied cheaply. SDP §5 names FalkorDB. Nothing is implemented in SaaG yet.

ADR-0014 adopts the schema of the Software-as-a-Graph framework ([`docs/graph-model.md`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md) at `d1f8b424`, **the framework model**). The framework already has a storage layer for that schema:

* **Port:** `IGraphRepository` (`saag/core/ports/graph_repository.py`) with `save_graph`, `derive_dependencies`, `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json` and `close`.
* **Engines:** `Neo4jRepository` (Neo4j 5, plain Cypher, no APOC or GDS) and `MemoryRepository` (pure Python). A third, `SimulationGraph`, re-derives the same dependencies for simulation.
* **Parity:** `tests/test_repository_fidelity_parity.py` pins vertex weights, edge weights and path counts across the engines. `tests/test_simulation_dependency_derivation.py` pins the derived edge sets.
* **Scope:** one graph per database. `save_graph(clear=True)` replaces it, so the framework has no notion of model instances.

Expected scale: UXD §6 sets the visualization level-of-detail threshold at 1,000 nodes. A real system is expected to have hundreds to a few thousand units, topics and messages, which is within every candidate's capacity. The deciding factors are therefore instance isolation, parity with the framework model, query language and operations cost, not raw scale.

The question is: which engine stores and serves System Model instances, and how does it relate to the framework's repository port and engines?

## Decision Drivers

* Many isolated graph instances must be cheap to create, copy and delete (QA-02, ADR-0016, ADR-0033).
* Weights and derived `DEPENDS_ON` edges must equal the framework model's, so its analyses and published results apply (ADR-0014).
* Rules need a declarative query language (ADR-0022), plus graph algorithms in Python.
* Development and tests must run without a graph server, through fake adapters (QA-11, ADR-0003).
* Fit with the operated stack: Redis is already run (ADR-0006).
* Licensing must permit on-premises internal use.

## Considered Options

* FalkorDB behind the framework's repository port, with the framework's in-memory engine as derivation engine and test fake
* Neo4j through the framework's `Neo4jRepository`, as is
* The framework's `MemoryRepository` per operation, rebuilt from files, with no graph server
* PostgreSQL with the Apache AGE extension

## Decision Outcome

Chosen option: "FalkorDB behind the framework's repository port, with the framework's in-memory engine as derivation engine and test fake", subject to the spike in *Confirmation*. It is the only option that gives cheap named graphs (as ADR-0016 and ADR-0033 assume) while keeping the framework's contract and computing weights and dependencies with the framework's own code.

### 1. Port

SMM's graph-store port `IGraphStore` (`smm/ports/graph_store.py`) is the framework's `IGraphRepository`, extended for SaaG:

| Operation | Source | Purpose |
|---|---|---|
| `save_graph`, `derive_dependencies`, `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json`, `close` | framework, unchanged | Build, derive and read one instance |
| `create_instance`, `copy_instance`, `delete_instance`, `list_instances` | SaaG | Instance lifecycle (ADR-0016) |
| `save_extensions` | SaaG | Write the ADR-0014 extension labels and relationships |
| `apply_edit` | SaaG | Apply one working-model edit command (ADR-0016) |
| `query` | SaaG | Run a read-only, parameterized Cypher query (ADR-0022 `ModelReader`) |

Each adapter is bound to one instance when it is opened, in the same way that `Neo4jRepository` is bound to one database.

### 2. Engines

| Engine | Role |
|---|---|
| FalkorDB adapter (`smm/adapters/falkordb_graph_store.py`) | Production store. One named graph per instance, `model:<instance_id>`. |
| Framework `MemoryRepository` | Derivation engine inside the FalkorDB adapter, and the fake adapter for development and tests |

* **Derivation is computed, not re-implemented.** `derive_dependencies` on the FalkorDB adapter does three things:
  1. it reads the instance's structural view;
  2. it runs the framework's `MemoryRepository` phases 3, 4 and 5 over it (topic weights, the seven rules, edge-weight finalization);
  3. it writes the vertex weights and the `DEPENDS_ON` edges back in one transaction.

  SaaG therefore has no third copy of the derivation rules. Parity with the framework model holds by construction, and the framework's parity tests still check it.
* **Keys:** SMM calls `save_graph` with `id` set to the ADR-0014 key (the entity `name`). The run-local Model Data id goes to `source_id`. FalkorDB enforces a unique `id` per label.
* **Framework dependency:** SaaG uses the framework package `saag` pinned to the commit ADR-0014 names, as a library. SMM imports only `saag.core` and `saag.infrastructure.memory_repo`.

### 3. FalkorDB deployment and access

* **Container:** a dedicated FalkorDB container with AOF persistence. It is separate from the Celery broker Redis, because the two need different persistence and eviction settings.
* **Instances:** created with `GRAPH.COPY` (working models and operation snapshots, ADR-0016 and ADR-0033) or built from Model Data (baseline and candidate models), and dropped with `GRAPH.DELETE`.
* **Access:** SMM owns the only adapter. Other CSCs use SMM's façade (ADR-0007). Queries are parameterized, never built by string concatenation.
* **Algorithms:** a rule that needs an algorithm not expressible in Cypher loads the instance, or one of its layer projections (`get_layer_data`), into NetworkX inside the worker (ADR-0022). The copy is read-only and is discarded after the operation.
* **Fallback:** if the spike fails, the next candidate is the framework's `Neo4jRepository` with one Neo4j database per instance, which needs Neo4j Enterprise. After that comes PostgreSQL with AGE.

### Consequences

* Good, because per-instance isolation is native and cheap, and no query needs an instance filter.
* Good, because weights and dependencies are computed by the framework's own code, so SaaG results stay comparable with the framework's.
* Good, because development and tests run without a server, on the same engine the framework tests.
* Good, because Cypher rules stay portable to other openCypher engines, including the framework's Neo4j engine.
* Bad, because the derivation round-trip moves each instance's structural view through Python memory. This is acceptable at the expected scale and is measured in the spike.
* Bad, because FalkorDB is licensed under SSPL v1, and the framework under GPL-3.0-or-later. Both are expected to permit internal on-premises use, but both must be cleared with the project's licensing authority before acceptance.
* Bad, because FalkorDB is a younger product than Neo4j, with an openCypher subset.
* Bad, because there is one more stateful service to back up (ADR-0040).
* Follow-up: update the graph-storage row in SDP §5 to cite this ADR, and set CDR-29's System Model and Working Model parts to `Resolved` on acceptance.

### Confirmation

A spike in R3 must pass the following before this ADR is accepted:

1. **Parity:** the framework's parity suite (`test_repository_fidelity_parity.py`, `test_simulation_dependency_derivation.py`) passes with the FalkorDB adapter added as an engine, including the worked example of framework model §9.
2. **Load:** a synthetic model of 5,000 Applications, 5,000 Topics and 50,000 relationships is built and derived in under 30 s.
3. **Copy:** `GRAPH.COPY` of that model takes under 5 s.
4. **Queries:** the pub/sub-match and cycle-detection queries, and `get_layer_data("app")`, return in under 2 s.
5. **Licensing:** FalkorDB and the framework package are cleared.

The results are recorded in this ADR's *More Information*. After that, a CI job runs the parity suite against the FalkorDB adapter on every change to SMM or to the pinned framework version.

## Pros and Cons of the Options

### FalkorDB behind the framework port (chosen)

* Good, because it has cheap named graphs and Cypher, it runs on the Redis protocol, and it reuses the framework's contract and derivation code.
* Neutral, because derivation runs in Python rather than in the database.
* Bad, because of the SSPL licence, product maturity, and an openCypher subset.

### Neo4j through the framework's `Neo4jRepository`

* Good, because the adapter exists, is parity-tested, and runs the framework's Cypher unchanged.
* Bad, because Neo4j Community has one user database. Isolating many instances would need Neo4j Enterprise (licence cost), one server per instance, or an instance filter in every query, and the framework's queries have no such filter.
* Bad, because there is no graph-copy primitive, so ADR-0016 and ADR-0033 would have to rebuild instead of copy.

### Framework `MemoryRepository` per operation, no server

* Good, because it is the framework's own engine, needs no new service, and is trivial to copy.
* Bad, because it has no query language, so ADR-0022's Cypher queries are lost, and each worker holds whole models in memory.
* Bad, because instances exist only while an operation runs, so the Operations Panel cannot query a shared model (DVE.17, DVE.19).

### PostgreSQL + Apache AGE

* Good, because it reuses PostgreSQL (ADR-0008) and has named graphs and Cypher.
* Bad, because the extension is less mature, it has no copy-graph primitive, and traversal performance is weaker.

## More Information

* Framework: [`saag/core/ports/graph_repository.py`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/saag/core/ports/graph_repository.py), `saag/infrastructure/memory_repo.py`, `saag/infrastructure/neo4j_repo.py`, and framework model §6.4 (implementation parity)
* [SDP §5](../../planning/SDP.md), [UXD §6](../UXD.md)
* Related: ADR-0003, ADR-0006, ADR-0007, ADR-0014, ADR-0016, ADR-0022, ADR-0033, ADR-0036, ADR-0040
* Revisit if the spike fails, if the licence review rejects FalkorDB or the framework package, or if the framework adds an instance-aware engine.
