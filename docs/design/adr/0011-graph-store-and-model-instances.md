# ADR-0011: Graph store and model instances

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Decide |
| Traces | SMM.1, 4, 26–31, 36; MDG.15; DVE.17, 19, 26, 28–58, 71–78; QA-02, QA-03, QA-04, QA-07, QA-10, QA-11 |
| Resolves | DP-29d, DP-29f (storage of the System Model and the Working Model) |
| Decide by | Wave A (2026-11-27); the engine choice is confirmed by the R3 spike |
| Supersedes | — |

## Context and Problem Statement

The System Model (ADR-0010) must be stored, queried by the verification rules (DVE.28–49), traversed by the behavioral analyses (DVE.53–58), and browsed and edited from the Operations Panel (DVE.17, 19–20). The SRS implies three kinds of model, which must coexist under concurrent users and pipeline operations (SMM.29–30):

1. **Baseline:** built from a Model Data file (SMM.4). It must never be altered by verification, analysis or data binding (DVE.29, 51; SMM.36).
2. **Working model:** derived from a baseline. The user edits nodes and relationships on it and runs verification (DVE.17).
3. **Candidate-evaluation model:** "a new, process-specific System Model" with candidate unit versions (SMM.31). MDG.15 already writes candidates into the Model Data inventory (`is_candidate`, a `candidates` list since `1157784`).

Nothing is implemented yet; SDP §5 names FalkorDB. Two constraints frame the choice:

* the target host is offline and has no container runtime, so a server must install natively on CentOS 7 or later (ADR-0004);
* the framework's `saag` engines need Python ≥ 3.10, so SMM implements derivation itself (ADR-0010 §7).

The expected scale is hundreds to a few thousand units, topics and messages. The deciding factors are therefore isolation, offline installability, query language and operating cost.

## Decision Drivers

* The engine and its Python driver must install offline, and the driver must have a CPython 3.9 wheel.
* Baselines are immutable by construction (QA-03). Creating, copying and deleting working and candidate models must be cheap (QA-02).
* Weights and `DEPENDS_ON` must equal the framework model's (ADR-0010); SMM's in-memory engine computes them.
* Rules need a declarative query language (ADR-0016). Development and tests must run without a server (QA-11).
* Working-model edits must be traceable (DVE.17, 26; QA-04), and pipeline evaluations isolated (DVE.78). Licensing must permit on-premises use.

## Considered Options

* Store: a native graph server (Neo4j Community 5 or FalkorDB) behind an SMM `IGraphStore` port, chosen by a spike / SMM's in-memory engine per operation / graph tables in SQLite / PostgreSQL + Apache AGE
* Instances: a separate graph instance per model / a delta overlay applied at query time / a full copy per operation

## Decision Outcome

Chosen options:

* **A native graph server behind an SMM `IGraphStore` port, chosen by a spike.** A server gives a shared, queryable model and Cypher, and the port keeps the engine replaceable.
* **A separate graph instance per model, with working models copied from their baseline.** To rule authors every instance is an ordinary graph, and the change log keeps edits traceable.

### 1. Port and engines

`IGraphStore` (`smm/src/smm/ports/graph_store.py`) keeps the operation names of the framework's `IGraphRepository`, but SMM implements it and imports nothing from `saag`:

| Operation | Purpose |
|---|---|
| `save_graph`, `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json`, `close` | Build and read one instance (framework names) |
| `save_derived` | Write the weights and `DEPENDS_ON` computed in memory, in one transaction |
| `create_instance`, `copy_instance`, `delete_instance`, `list_instances` | Instance lifecycle (§3) |
| `save_extensions` | Write the ADR-0010 extension labels and relationships |
| `apply_edit` | Apply one working-model edit command (§3) |
| `query` | Run a read-only, parameterized Cypher query (ADR-0016 `ModelReader`) |

* **Engines:**
  * the server adapter, `smm/src/smm/adapters/<engine>_graph_store.py`, in production;
  * SMM's in-memory engine (`smm/src/smm/graph/`, ADR-0010 §7), which computes weights and `DEPENDS_ON` and is the fake in tests.
* **Derivation:**
  1. SMM builds the structural view in memory from validated Model Data and derives there.
  2. It writes the instance with `save_graph`, `save_extensions` and `save_derived`.
  3. After an edit, it reads the structural view back, re-derives, and rewrites the derived view.
* **Keys:** the entity `name` per label. The run-local Model Data ID is kept as `source_id`. Uniqueness is on (`instance_id`, label, `name`), or (label, `name`) inside a named graph.
* **Access:** SMM owns the only adapter. Other CSCs use its façade (ADR-0003). Queries are parameterized.
* **Algorithms:** a rule that needs an algorithm loads the instance or a layer projection into networkx 3.2.1 inside the operation's child process, read-only.
* **Service:** the server listens on `localhost` only, starts before `dsm`, and its data directory is in the backups (ADR-0004).

### 2. Spike candidates

| | Neo4j Community 5 | FalkorDB |
|---|---|---|
| Install | Tarball plus a Java 17 runtime tarball; systemd service | Redis server plus the FalkorDB module (`.so`); must load on glibc 2.17, possibly built from source |
| Python driver | `neo4j` 5.x, pure Python, Python 3.7+ | `falkordb` over `redis-py` |
| Instances | One user database; indexed `instance_id` on every node and relationship | Native named graphs `model:<instance_id>` |
| Query language | Cypher, as the framework's Neo4j engine uses | openCypher subset |
| Licence | GPL-3.0 (Community) | SSPL v1 |

* **Default if the spike is inconclusive: Neo4j Community.** It is the more mature product, its install needs no compiled module, and the framework already uses its Cypher dialect.
* **Scoping with Neo4j:** the adapter adds the `instance_id` scope to every query. Rule authors and `ModelReader` callers never write it (ADR-0016).

### 3. Model instances

| Kind | Created from | Mutability | Owner | Lifetime |
|---|---|---|---|---|
| `baseline` | A Model Data file (SMM.4) | Immutable after construction | System | Retained per ADR-0004 §5 |
| `working` | Copy of a baseline or another working model | Edited through SMM's working-model API only | One user | Until deleted, or expired (ADR-0004 §5) |
| `candidate` | Its own Model Data file with candidates (MDG.15) | Immutable after construction | One operation | Deleted when its evaluation ends, after findings are persisted |

* **Isolation mechanism:**

  | Engine | Instance | Copy | Delete |
  |---|---|---|---|
  | FalkorDB | Named graph `model:<instance_id>` | `GRAPH.COPY` | `GRAPH.DELETE` |
  | Neo4j Community | Indexed `instance_id` on every element | `MATCH … CREATE` in batches, in one transaction | `MATCH (n {instance_id: $id}) DETACH DELETE n`, in batches |
  | In-memory engine (tests) | One Python object | Deep copy | Drop the reference |

* **Registry:** a `model_instance` table in SQLite (ADR-0007) with these columns:
  * `instance_id` (`uuid4().hex`), `kind`, `parent_instance_id`;
  * `model_data_ref` and its hash;
  * project, platform and system version;
  * `created_by`, `created_at`, `status`, `revision`.
* **Immutability:** SMM's façade exposes writes only for `working` instances. Verification and analysis get a read-only handle (ADR-0003).
* **Edits (DVE.17):** each edit is a command: add or remove a node, add or remove a relationship, or set an attribute. A command:
  1. is validated against the schema and structural integrity rules (ADR-0010);
  2. is applied to the working graph;
  3. is appended to `model_edit(instance_id, revision, command JSON, user, at)`;
  4. increments `revision`.

  Concurrency follows ADR-0006 §2.
* **Reproducibility:** every operation records `instance_id` and `revision` (ADR-0007).
* **Analytical data:** bound as a separable layer (ADR-0012), never written into a baseline.

### Consequences

* Good, because the Operations Panel and the rules share one queryable model in Cypher.
* Good, because derivation and tests do not depend on the server, so the engine choice stays reversible.
* Good, because rules need no overlay logic, pipeline evaluations are isolated, and the change log gives an exact, reportable diff of each working model.
* Bad, because a server must be installed and patched offline, which is the largest operating cost in the CSCI.
* Bad, because with Neo4j Community, isolation depends on the adapter's `instance_id` scope rather than a native primitive. A missing filter would mix instances.
* Bad, because every write round-trips the instance through Python memory, and storage grows with working models, bounded by expiry and ADR-0006's limits.
* Bad, because working models do not follow later baseline updates. Rebasing would replay the change log, and it is not in scope.
* Follow-up: on acceptance, replace the "to be determined" storage wording in SDD §2.4 with a link to this ADR.

### Confirmation

A spike in R3, on a CentOS-7-compatible host without network access, records these for each candidate before acceptance:

1. **Offline install:** the server installs from copied files with a `deploy/` script, runs under the service manager, and survives a reboot.
2. **Driver:** the Python driver installs from a cp39 wheelhouse.
3. **Parity:** a model built from the ADR-0010 worked-example fixture and read back has the same weights and `DEPENDS_ON` as the in-memory engine.
4. **Load:** 5,000 Applications, 5,000 Topics and 50,000 relationships are written in under 30 s.
5. **Copy:** copying that instance takes under 5 s.
6. **Queries:** the pub/sub-match and cycle queries, and `get_layer_data("app")`, return in under 2 s.
7. **Isolation:** two instances edited concurrently never see each other's elements.
8. **Licensing:** the licence is cleared.

After the spike, CI runs the parity and isolation tests against the chosen adapter. Also:

* writing to a `baseline` or `candidate` instance through SMM fails;
* replaying a working model's change log on its parent reproduces it;
* two parallel candidate evaluations never see each other's nodes.

## Pros and Cons of the Options

* Native graph server (chosen): Good, because it gives a shared model, Cypher and a replaceable engine. Bad, because of the offline operating cost and, for Neo4j Community, scoping by property.
* In-memory engine only: Good, because it needs no service. Bad, because it has no query language, instances exist only during an operation, and the panel cannot query a shared model (DVE.17, 19).
* Graph tables in SQLite: Good, because it needs no new service. Bad, because traversals become slow recursive SQL, and the rules lose Cypher.
* PostgreSQL + AGE: Bad, because it needs a server ADR-0007 does not adopt, and the extension is less mature.
* Separate instance per model (chosen): Good, because it is simple to query and isolation is strong. Bad, because of storage per instance.
* Delta overlay: Good, because storage is minimal. Bad, because every rule query must merge the overlay, and Cypher has no overlay semantics.
* Full copy per operation: Bad, because it copies even when nothing changed, and edits would be lost between operations.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `d1f8b424`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md), §6.4 (implementation parity); framework `pyproject.toml` (Python ≥ 3.10 dependency floors)
* [SDP §5](../../planning/SDP.md), [UXD §6](../UXD.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0010, ADR-0012, ADR-0016, ADR-0020
* Revisit if neither candidate installs offline (fallback: graph tables in SQLite, with the in-memory engine for traversals), or if the licence review rejects the chosen engine.
