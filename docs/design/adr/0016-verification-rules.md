# ADR-0016: Verification rules: engine, rule model and catalog

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering, middleware owners |
| Kind | Decide |
| Traces | DVE.18, 21–22, 24, 28–49, 59–70, 72–77; QA-03, QA-04, QA-11 |
| Resolves | DP-01…DP-08: the SRS rule sets deferred to the critical design phase, namely DVE.32–35 (topic QoS), DVE.39 (communication services in scope), DVE.40 (load balancing), DVE.41–43 (core allocation), DVE.44 (OS settings), DVE.45 (runtime memory allocation), DVE.49 (architectural rules) and DVE.18 (conformance classification), each through its catalog family (§2) |
| Decide by | Wave A2 (2026-12-18) for engine and catalog workflow; Wave B (2027-01-22) for `approved` status of DP-01…DP-08 catalog families |
| Supersedes | — |

## Context and Problem Statement

DVE executes deterministic rule checks across three release stages:

1. **R3 Structural Design Verification (`DVE.28–49`):** QoS Durability, Reliability, Lifespan and Transport Priority (`DVE.32–35`); unpublished/unconsumed topics and same-name content-definition conflicts (`DVE.36–38`); external-to-middleware communication consistency (`DVE.39`); console/processor load balancing (`DVE.40`); CPU core over-allocation, core conflicts and missing dedicated cores (`DVE.41–43`); OS settings (`DVE.44`); runtime memory allocation (`DVE.45`); resource contention (`DVE.46`); circular software-unit dependencies (`DVE.47`); disconnected/missing/invalid/unmatched relationships (`DVE.48`); and architectural pattern violations (`DVE.49`)—operating solely on the System Model without AED (`DVE.30`) and without mutating the model (`DVE.29`), while linking related findings by cause and effect (`DVE.22`).
2. **R6 Field Behavioral & Drift Checks (`DVE.59–70`, ADR-0017 §2):** health, CPU/RAM/storage/network thresholds, error/restart/timeout events, flow/latency/loss checks, and `drift_missing` / `drift_unexpected` / `drift_mismatch` rules over `ModelReader` + bound `AedReader`.
3. **R7 Installation Suitability Evaluation (`DVE.71–77`, ADR-0018):** scores rules grouped under the **four mandatory SRS headings** (`DVE.72–75`), where each rule carries `rule_id`, `evaluation_heading`, `severity`, `weight`, `acceptance_criterion`, and `blocking` (`DVE.76–77`).

The domain *contents* of eight rule families (`DP-01…DP-08`) are deferred to critical design. This ADR fixes the unified rule engine, check signature, cause-and-effect correlation model, error boundary, and Git-versioned YAML catalog governance.

## Decision Drivers

* One rule record and check signature must serve R3 structural checks (no AED), R6 field/drift checks (with AED), and R7 installation evaluation (`DVE.72–77`) without collisions between catalog file names and the four `DVE.72–75` evaluation headings!
* Checks need both declarative Cypher (`ModelReader`) and graph algorithms (`networkx 3.2.1`), plus deterministic cause-and-effect linking (`DVE.22`) and clean engine-error separation (`DVE.24`).
* Domain parameters and thresholds must live in human-readable YAML reviewed by domain owners, while allowing R3 development to run with `provisional` rules until `DP-01…DP-08` reach `approved` status at Wave B.
* `PyYAML` must be declared directly in `dve/setup.py` and vendored in `dve/wheelhouse/` (`PyYAML 6.0.2` `cp39` `manylinux2014_x86_64`, ADR-0004).

## Considered Options

* Engine model: Hybrid—declarative YAML rule metadata/parameters paired with registered pure-Python `@check` functions over `(ModelReader, params, Optional[AedReader])`
* Engine model: Pure Cypher strings stored in YAML only
* Engine model: Hardcoded Python rule classes with embedded thresholds
* Catalog storage & governance: Versioned YAML files in `dve/src/dve/rules/` approved via pull request (`provisional` → `approved`)
* Catalog storage & governance: Mutable database table edited at run time
* Catalog storage & governance: Separate ADR per rule parameter change

## Decision Outcome

Chosen options: **the hybrid rule engine (`YAML metadata + pure-Python @check functions`)** and **a Git-versioned YAML catalog in `dve/src/dve/rules/` governed by pull request**.

### 1. Rule record, check contract, cause-and-effect links and error handling

**Rule record schema (`dve/src/dve/schemas/rule-catalog-1.0.schema.json`):**

| Field | Meaning |
|---|---|
| `rule_id` | Stable identifier, e.g. `QOS-LIFE-001`, `CPU-ALLOC-002`, `DRIFT-001` |
| `version` | Semantic version of this rule's definition (`"1.0.0"`) |
| `family` | Catalog file / domain family (e.g. `qos`, `cpu_allocation`, `drift`; §2) |
| **`evaluation_heading`** | **Separated from `family`:** one of the four canonical `DVE.72–75` headings (`structural_architectural`, `interface_topic_communication`, `dependency_integration`, `resource_performance`), or `null` for rules excluded from installation evaluation—ensuring every structural/interface/dependency/resource rule participates cleanly in R7 scoring (ADR-0018)! |
| `requires_aed` | `false` for pure structural rules (`DVE.30`); `true` for AED-backed behavioral/resource/drift rules |
| `check` | Registered Python `@check` function name |
| `params` | Validated parameter mapping passed to the check |
| `severity` | `informational` \| `low` \| `medium` \| `high` \| `critical` (DVE.21) |
| `weight` | Positive float used by ADR-0018 installation scoring (DVE.76) |
| `acceptance_criterion` | Human-readable conformance statement (DVE.21, 76) |
| `blocking` | `bool` — whether a violation forces `block` / `non-conforming` in installation evaluation (DVE.76–77) |
| `causes_from` | Optional list of `{upstream_rule_id, match_on: 'same_entity' \| 'topic_publisher' \| 'hosting_node', link_kind}` rules for automatic cause-and-effect linking (`DVE.22`) |
| `status` | `provisional` \| `approved` (§2) |

**Unified check signature (`dve/src/dve/rules/registry.py`):**

```python
@check("topic_qos_lifespan_conformance")
def topic_qos_lifespan_conformance(
    model: ModelReader,
    params: Mapping[str, Any],
    aed: Optional[AedReader] = None,
) -> Iterable[Violation]: ...
```

* **`ModelReader` and `AedReader`:** read-only handles from SMM (`INT-IF-05`, ADR-0003, ADR-0011, ADR-0012). On structural runs (`DVE.30`), `aed` is `None` and rules with `requires_aed: true` are skipped cleanly. `ModelReader` offers instance-scoped parameterized Cypher and `to_networkx(subgraph)` (`networkx==3.2.1`), backed by `InMemoryGraphStore` in unit tests.
* **Determinism & purity (`DVE.29, QA-03`):** checks never mutate the model, never call network/filesystem I/O, and never read wall-clock time or unseeded randomness.
* **Cause-and-effect finding links (`DVE.22`):**
  * Each `Violation` carries `affected` (`[{element_kind, label_or_type, key}]`), `evidence` (dict), optional `correlation_keys` (e.g. `topic:/telemetry/imu` or `node:proc_1`), and optional explicit `caused_by_keys`.
  * After all checks in an operation finish, the engine resolves both explicit `caused_by_keys` and declarative `causes_from` patterns (for example: `DVE.36` unpublished topic → starved subscriber warnings; `DVE.44` non-isolated OS cores + `DVE.41/42` conflicting core allocation → `DVE.46` resource contention) and writes rows into `dve_finding_link` (`ADR-0007`).
* **Check exception handling (`DVE.24`):**
  * If a check function raises an unexpected Python exception, **it does NOT emit a fake target-system finding** (since `dve_finding.severity` has only `informational..critical`). Instead, the engine records a structured `ErrorRecord` (`status = 'error'`, `category = 'internal'`, `stage = 'rule:<rule_id>'`, `ADR-0009`) on the operation (`DVE.24`), sets `common_operation.outcome_status = 'error'`, and continues executing the remaining rules so one faulty check does not blind the rest of the run.
* **Conformance classification (`DVE.18`):**
  * Across `structural_verification`, `simulation_analysis`, and `field_analysis`, an operation's `conformance` (`common_operation.conformance`, ADR-0007) is `non-conforming` if at least one finding comes from an `approved` rule (or propagation band in `classification.yaml`) with `severity_rank` at or above the profile's `min_nonconforming_severity` (default `high`) or `blocking: true`; otherwise `conforming` (when `outcome_status != 'error'`).
  * Findings from `provisional` rules are persisted and displayed in the UI (`[Provisional]` badge) so domain engineers can review them during R3, but never flip `conformance` or R7 scores.

### 2. Catalog layout, profiles and governance (`DP-01…DP-08`)

* **Package location:** `dve/src/dve/rules/`, validated at start-up and in CI against `rule-catalog-1.0.schema.json` using `PyYAML` `safe_load` (`PyYAML>=6.0` added to `dve/setup.py` and `dve/wheelhouse/`):

  | Catalog YAML file | Scope & SRS trace | Resolves | Target wave |
  |---|---|---|---|
  | `qos.yaml` | Topic Durability, Reliability, **Lifespan**, Transport Priority (`DVE.32–35`) | DP-01 | Wave B (`approved`) |
  | `communication.yaml` | External-to-middleware `CommunicationService` `USES_SERVICE`/`TRANSFERS` consistency (`DVE.39`) | DP-02 | Wave B (`approved`) |
  | `load_balancing.yaml` | CSU distribution across console/processor `Node`s (`DVE.40`) | DP-03 | Wave B (`approved`) |
  | `cpu_allocation.yaml` | Core capacity overflow, core conflicts, high-performance dedicated cores (`DVE.41–43`) | DP-04 | Wave B (`approved`) |
  | `os_settings.yaml` | Host/unit OS settings & core-allocation alignment (`DVE.44`) | DP-05 | Wave B (`approved`) |
  | `memory.yaml` | Runtime memory allocation limits vs. `Node.memory_gb` (`DVE.45`) | DP-06 | Wave B (`approved`) |
  | `architecture.yaml` | Forbidden layer/CSC dependencies and design-pattern violations (`DVE.49`) | DP-07 | Wave B (`approved`) |
  | `classification.yaml` | `conforming` / `non-conforming` severity & propagation thresholds (`DVE.18`) | DP-08 | Wave B (`approved`) |
  | `structural.yaml` | Unpublished/unconsumed topics, same-name `declared_type_hash` conflicts, resource contention, `USES`/pub-sub cycles, disconnected/unmatched elements (`DVE.36–38, 46–48`) | — (SRS-defined) | Wave A2 / R3 |
  | `propagation.yaml`, `field_health.yaml`, `field_traffic.yaml`, `drift.yaml` | R6 simulation propagation bands (`DVE.54–58`), field health/resource/event/latency thresholds (`DVE.60–65, 69–70`), and `DVE.66–68` drift attribute rules (ADR-0017) | — | Wave D / R6 |

* **Evaluation profiles (`dve/src/dve/rules/profiles/<name>.yaml`, `DVE.77`):** select active `rule_id`s, parameter overrides, heading weights (ADR-0018), and classification thresholds per project/platform (`default.yaml` when unspecified).
* **Approval & `DP-01…DP-08` closure:**
  * Rules land in R3 as `status: provisional` with positive and negative fixture graphs under `dve/tests/rules/fixtures/`.
  * Promoting a family to `status: approved` (gated at **Wave B, 2027-01-22**) requires pull-request approval from the CDR Board's domain owner for that family; that PR replaces the "to be determined during the critical design phase" wording in `SRS.md` with a link to the catalog file and tag ([ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr)).

### Consequences

* Good, because separating `family` from `evaluation_heading` and passing `Optional[AedReader]` lets one rule engine power R3 structural verification, R6 field/drift analysis, and R7 installation evaluation seamlessly.
* Good, because `dve_finding_link` correlation (`DVE.22`) and clean `ErrorRecord` separation on check exceptions (`DVE.24`) prevent schema mismatches.
* Bad, because threshold changes require a Git commit and package tag rather than ad-hoc runtime edits—accepted deliberately to preserve cryptographic reproducibility (QA-04).

### Confirmation

* Start-up & CI schema gate validates every YAML file in `dve/src/dve/rules/`, verifies every `check` name is registered, and rejects any `approved` rule lacking both positive and negative fixture tests.
* Engine unit tests verify: `requires_aed: true` skipping on structural runs (`DVE.30`); `causes_from` generating `dve_finding_link` rows (`DVE.22`); check exceptions recording an `internal` `ErrorRecord` (`stage = 'rule:<id>'`) while remaining checks complete (`DVE.24`); and `provisional` findings excluded from `conformance` flipping.

## Pros and Cons of the Options

### Hybrid engine (`YAML metadata + pure-Python @check functions`) (chosen)

* Good, because domain engineers review thresholds/weights in YAML while complex algorithms (Tarjan SCC cycles, CPU pinning set intersections, bandwidth contention) are written and unit-tested in Python.
* Bad, because introducing a brand-new check algorithm requires a Python code release.

### Pure Cypher strings stored in YAML only

* Good, because rules live 100% in data files.
* Bad, because set-packing CPU core checks, AED `overlay.db` joins, and portable Neo4j/in-memory execution cannot be expressed cleanly in engine-neutral Cypher alone.

### Hardcoded Python rule classes only

* Good, because everything is in one language.
* Bad, because domain owners must review Python code for simple QoS or memory threshold updates.

### Versioned YAML catalog in Git approved by pull request (chosen)

* Good, because Git provides immutable version tags, line-by-line review attribution, and CI fixture enforcement for free.
* Bad, because changing a threshold in an air-gapped deployment ships a new release tarball (or profile file).

### Mutable rules stored in SQLite and edited in the UI

* Good, because operators can tweak rules on the fly.
* Bad, because unreviewed live edits undermine qualification reproducibility and CDR Board governance.

### One ADR per rule parameter change

* Good, because every parameter has MADR prose.
* Bad, because hundreds of domain thresholds would flood the ADR catalog with non-architectural noise (ADR-0001).

## More Information

* [SRS §6.1.1, §6.1.2, §6.1.3, §6.1.4](../../requirements/SRS.md), [STD TC-DVE-06, 08..13, 17](../../test/STD.md)
* Related: ADR-0001, ADR-0003, ADR-0007, ADR-0008, ADR-0009, ADR-0010, ADR-0011, ADR-0012, ADR-0017, ADR-0018, ADR-0021
* Revisit if institutional operators later need signed external rule-pack tarballs loaded from `/etc/dsm/rules.d/` without rebuilding the `dve` Python wheel.
