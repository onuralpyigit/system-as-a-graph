# ADR-0011: Graph store and model instances

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, platform team |
| Kind | Decide |
| Traces | SMM.1, 4, 26–31, 36; MDG.15; DVE.17, 19, 26, 28–58, 71–78; QA-02, QA-03, QA-04, QA-07, QA-10, QA-11 |
| Resolves | DP-29d, DP-29f (storage of the System Model and the Working Model) |
| Decide by | Wave A2 (2026-12-18), including the R3 engine-confirmation spike |
| Supersedes | — |

## Context and Problem Statement

The System Model (ADR-0010) must be stored durably, queried in Cypher by verification rules (DVE.28–49), traversed by behavioral analyses (DVE.53–58), and browsed and edited interactively from the Operations Panel (DVE.17, 19–20, including undoable edits per UXD §4). Four instance roles coexist under concurrent users and CI pipelines (SMM.29–31):

1. **Baseline (`baseline`):** constructed from a validated Model Data file (SMM.4); strictly immutable after construction (DVE.29, 51; SMM.36).
2. **Working model (`working`):** copied from a baseline (or parent working model) so an operator can add/remove nodes and relationships, update attributes, undo edits, and run hypothetical verifications/analyses without breaking structural integrity (DVE.17).
3. **Candidate-evaluation model (`candidate`):** process-specific System Model combining candidate unit version(s) with target system units (SMM.31, MDG.15, DVE.71–78).
4. **Operation snapshot (`snapshot`):** short-lived read-only copy of a `working` model at a pinned revision created before spawning an operation (ADR-0006 §2).

Nothing is built yet. Earlier SDP §5 drafts named FalkorDB, whereas `SoftwareAsAGraph @ 0bbe06af` implements only `Neo4jRepository` and `MemoryRepository` (zero FalkorDB code exists in `saag`). The target host is air-gapped CentOS 7+ (`glibc 2.17`) with CPython 3.9 and no container runtime (ADR-0004), hosting up to `200` live model instances of ~5,000 units/topics and ~50,000 relationships each (ADR-0006, ADR-0020).

## Decision Drivers

* Both the graph server binary and its Python driver must install and run offline on CentOS 7 (`glibc 2.17`) + CPython 3.9.
* Instance copy, delete, and scoped queries must remain fast (< 5 s copy, < 2 s rule queries) even with **200 coexisting model instances** (~2.5M total nodes) loaded simultaneously (QA-02, QA-07).
* Baselines must be immutable by construction, working-model edits + `DEPENDS_ON` re-derivation must commit atomically and support `[Undo]` (SMM.29, DVE.17, UXD §4), and unit tests must run without a graph server (QA-11).
* Server licensing must be cleared for on-premises institutional deployment.

## Considered Options

* Graph store: Native Cypher graph server (Neo4j Community 5 default, or FalkorDB, confirmed by R3 spike) behind SMM's `IGraphStore` port
* Graph store: In-memory Python graph only (reloaded from JSON per request/operation)
* Graph store: Relational node/edge tables in SQLite
* Graph store: PostgreSQL with Apache AGE
* Instance model: Separate isolated graph instance per model (`baseline`, `working`, `candidate`, `snapshot`)
* Instance model: Read-time delta overlay on top of baselines
* Instance model: Ephemeral per-operation graph copies with no persistent working models

## Decision Outcome

Chosen options: **a native Cypher graph server behind SMM's `IGraphStore` port (Neo4j Community 5 as default, confirmed by the Wave A2 R3 spike)** and **a separate graph instance per model with atomic copy-on-create and logged undoable edits for working models**.

### 1. `IGraphStore` port and derivation pipeline

`IGraphStore` (`smm/src/smm/ports/graph_store.py`) adapts the 7-method `IGraphRepository(Protocol)` of `SoftwareAsAGraph @ 0bbe06af` into an explicit SMM ABC—replacing server-side `derive_dependencies()` with SMM's pure-Python derivation engine (`ADR-0010 §7`) plus atomic `save_derived`:

| Method | Purpose |
|---|---|
| `create_instance`, `copy_instance`, `delete_instance`, `list_instances` | Instance lifecycle across `baseline`, `working`, `candidate`, and `snapshot` |
| `save_graph`, `save_extensions`, `save_derived` | Write structural framework elements, SRS extension elements, and derived weights/`DEPENDS_ON` in a single store transaction |
| `apply_edit_and_derived` | Atomically apply a forward or inverse (`undo`) structural edit and replace derived weights/`DEPENDS_ON` in **one transaction** (preventing torn intermediate reads, SMM.29) |
| `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json`, `close` | Read operations matching `saag` `IGraphRepository` |
| `query` | Parameterized read-only Cypher execution scoped automatically to `instance_id` (backing ADR-0016 `ModelReader`) |

* **Implementations:** `smm/src/smm/adapters/<engine>_graph_store.py` in production, and `InMemoryGraphStore` (`smm/src/smm/graph/`) for fast server-free unit/rule tests (`ADR-0021`).
* **Network binding:** the graph server binds to `127.0.0.1` only, starts via `systemd` before `dsm.service`, and is accessed solely through `smm`'s façade (ADR-0003).

### 2. R3 spike candidates and CPython 3.9 / CentOS 7 constraints

| Dimension | Neo4j Community 5 (**Default**) | FalkorDB (Alternative) |
|---|---|---|
| Host installation on CentOS 7 (`glibc 2.17`) | Neo4j 5 tarball + Eclipse Temurin Java 17/21 tarball (`glibc 2.17` compatible; zero C compilation); dedicated `neo4j.service` | Requires building/packaging Redis 6.2+/7.x (CentOS 7 EPEL only ships Redis 3.2) **plus** compiling `falkordb.so` (C/Rust/GraphBLAS/OpenMP) against `glibc 2.17` |
| CPython 3.9 wheelhouse | `neo4j` `5.x` (`<6.0`, requires Python `>=3.8`, pure Python `py3-none-any`) + **`pytz`** (`py3-none-any`) | **Current `FalkorDB >= 1.1` requires Python `>= 3.10` (incompatible with CPython 3.9)**; restricted to legacy `FalkorDB == 1.0.x` + `redis >= 4.5` + `async-timeout >= 4.0.3` |
| Multi-instance isolation & indexing | Single `neo4j` database; **every node carries shared base label `:ModelElement` with `CREATE INDEX model_elem_inst FOR (n:ModelElement) ON (n.instance_id)`** plus per-label composite uniqueness `(instance_id, name)` | Native keyspace `model:<instance_id>`, `GRAPH.COPY`, `GRAPH.DELETE` |
| Cypher parity with `saag @ 0bbe06af` | Exact dialect used by `saag`'s `Neo4jRepository` | openCypher subset (lacks Neo4j 5 `CALL { … UNION … }` subqueries and composite constraint syntax) |
| Licence | GPLv3 (installed as an independent OS service process talked to over Bolt via Apache-2.0 `neo4j` Python driver—never linked into SaaG Python code) | SSPL v1 (requires explicit institutional legal clearance) |

* **Why `:ModelElement(instance_id)` is mandatory on Neo4j Community 5:** Neo4j 5 property indexes require a node label; label-less `MATCH (n {instance_id: $id})` performs a full database scan across all 200 instances (~2.5M nodes). Stamping `:ModelElement` on every node ensures `copy_instance`, `delete_instance`, and scoped `ModelReader` queries use an exact index seek in milliseconds.
* **Default if FalkorDB fails CPython 3.9 / `glibc 2.17` / SSPL checks:** **Neo4j Community 5**.

### 3. Model instance registry, atomic edits and Undo (SMM.26, 29–31; DVE.17)

| `kind` | Source | Mutability | Lifecycle |
|---|---|---|---|
| `baseline` | Validated Model Data file (SMM.4) | Immutable (`revision = 0`) | Retained per ADR-0004 §5 |
| `working` | Copy of a `baseline` or `working` instance | Mutable only via SMM's `apply_edit` / `undo_edit` | Per-user cap `5` (ADR-0006); deleted by owner or TTL |
| `candidate` | Candidate Model Data file (MDG.15, SMM.31) | Immutable (`revision = 0`) | Deleted automatically when its `installation_evaluation` finishes and findings are saved |
| `snapshot` | Pre-spawn copy of a `working` instance at `(instance_id, revision)` | Immutable | Deleted automatically when the reading operation finishes (swept at start-up on crash, ADR-0006 §1) |

* **SQLite registry (`smm_model_instance` in `dsm.db`, ADR-0007):**
  * `instance_id TEXT PK`, `kind`, `parent_instance_id NULL`, `parent_revision NULL`, `model_data_artifact_id`, `model_data_sha256`, `project`, `platform`, `system_version`, `created_by`, `created_at`, `status` (`creating` \| `ready` \| `failed` \| `deleting`), `revision INTEGER NOT NULL DEFAULT 0`.
* **Working-model commands and Undo (`DVE.17`, `UXD §4`):**
  * Commands: `add_node`, `remove_node(cascade: bool = False)`, `add_relationship`, `remove_relationship`, `update_attributes`.
  * By default, `remove_node(cascade=False)` rejects deleting a node that still has incident structural relationships (`409` / `invalid_relationship` `ErrorRecord`) so users never sever topology silently; when the UI confirms `cascade=True`, SMM captures the node and all incident structural relationships in the edit record's `inverse_command` before removing them.
  * Every edit executes under ADR-0006 §2's per-instance lock and optimistic `expected_revision` check:
    1. Load current $G_{\text{structural}}$, validate the command against `schema.py` (`ADR-0010`), compute `inverse_command`, and re-derive weights + `DEPENDS_ON` in memory;
    2. Commit the structural delta + replaced `DEPENDS_ON` edges in **one** `IGraphStore.apply_edit_and_derived` transaction;
    3. Append `smm_model_edit(instance_id, revision, action, forward_command_json, inverse_command_json, actor, at)` and bump `smm_model_instance.revision` in `dsm.db`.
  * **`undo_edit(instance_id, expected_revision)`:** reads the latest un-undone `smm_model_edit` row, applies `inverse_command_json` through the exact same atomic pipeline, increments `revision`, and records `action = 'undo'`—preserving an append-only audit trail while supporting multi-step `[Undo]` in the Operations Panel (ADR-0015).

### Consequences

* Good, because rules and UI views share Cypher over isolated instances, `:ModelElement(instance_id)` prevents Neo4j full-graph scans at 200 instances, and atomic `apply_edit_and_derived` + `undo_edit` satisfy SMM.29 and DVE.17 cleanly.
* Good, because pure-Python derivation and `InMemoryGraphStore` keep `smm` and `dve` unit suites fast and server-independent.
* Bad, because bundling and operating a native graph server + JVM tarball is the heaviest infrastructure component on the offline host.
* Bad, because Neo4j Community isolation relies on `Neo4jGraphStore` injecting `:ModelElement {instance_id: $id}` into every query; `ModelReader` encapsulates this so rule authors never write raw unscoped queries.

### Confirmation

The Wave A2 spike on a network-disconnected CentOS-7-compatible VM (`glibc 2.17`, CPython 3.9) verifies before acceptance:

1. **Offline install & reboot survival:** `deploy/` script installs the server and `cp39` driver wheels (`neo4j` + `pytz`, or `FalkorDB 1.0.x` + `redis` + `async-timeout`) with `--no-index` and survives reboot under `systemd`.
2. **Parity:** ADR-0010 `0bbe06af` worked example round-trips with identical weights and `DEPENDS_ON` edges.
3. **200-instance scale & `:ModelElement` index verification:** with **200 coexisting instances** loaded (including the 5,000-App / 5,000-Topic / 50,000-edge reference model), `EXPLAIN` confirms zero `AllNodesScan`, initial write finishes in `< 30 s`, `copy_instance` in `< 5 s`, `delete_instance` in `< 5 s`, and pub/sub + cycle + `get_layer_data("app")` queries in `< 2 s`.
4. **Isolation, immutability & Undo:** concurrent edits on two working instances never cross-bleed; writes to `baseline`/`candidate`/`snapshot` fail; `apply_edit` followed by `undo_edit` reproduces the exact pre-edit structural and `DEPENDS_ON` graph.
5. **Licence clearance:** written sign-off recorded in the spike PR (GPLv3 separate-process boundary for Neo4j Community, or SSPL v1 review if FalkorDB).

## Pros and Cons of the Options

### Native Cypher graph server behind `IGraphStore` (chosen)

* Good, because it provides shared concurrent read access, expressive Cypher pattern matching for ADR-0016 rules, and engine replaceability behind `IGraphStore`.
* Bad, because it adds an offline daemon (and JVM for Neo4j) to install, monitor and back up.

### In-memory Python graph only

* Good, because zero server processes are installed on the host.
* Bad, because there is no shared persistent graph for interactive UI exploration/editing (DVE.17, 19–20) and no declarative Cypher engine for rules.

### Relational node/edge tables in SQLite

* Good, because storage stays inside Embedded SQLite.
* Bad, because multi-hop structural/pattern rules become verbose recursive SQL CTEs and contend with `dsm.db` operational writes (retained only as emergency revisit fallback).

### PostgreSQL with Apache AGE

* Good, because relational and openCypher data live in one server.
* Bad, because SaaG does not deploy PostgreSQL (ADR-0007) and compiling AGE for CentOS 7 offline is high-maintenance.

### Separate graph instance per model (chosen)

* Good, because every baseline, working, candidate and snapshot model is a normal self-contained graph—keeping rule Cypher queries simple and pipeline runs strictly isolated.
* Bad, because storage scales linearly with active working models (bounded by the 5-per-user / 200-total caps and TTL cleanup).

### Read-time delta overlay on top of baselines

* Good, because working models store only diffs.
* Bad, because every Cypher rule and `DEPENDS_ON` traversal would have to merge node/edge tombstones and attribute overrides at query time.

### Ephemeral per-operation graph copies only

* Good, because no persistent working models consume disk.
* Bad, because interactive iterative editing and `[Undo]` in the Operations Panel (DVE.17) require persistent working models across sessions.

## More Information

* Framework model: [`software-as-a-graph/docs/graph-model.md` @ `0bbe06af`](https://github.com/onuralpyigit/software-as-a-graph/blob/0bbe06afa12be228e343895322716b8cbd085535/docs/graph-model.md), `saag/core/ports/graph_repository.py`, `saag/infrastructure/neo4j_repo.py`
* [SDP §5](../../planning/SDP.md), [UXD §4, §6](../UXD.md)
* Related: ADR-0003, ADR-0004, ADR-0006, ADR-0007, ADR-0010, ADR-0012, ADR-0015, ADR-0016, ADR-0020, ADR-0021
* Revisit if neither server passes offline CentOS 7 installation or institutional licensing (fallback: dedicated per-instance SQLite graph files loaded into `smm`'s in-memory engine for traversals).
