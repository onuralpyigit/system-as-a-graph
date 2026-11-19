# ADR-0016: Verification rules: engine, rule model and catalog

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering, middleware owners |
| Kind | Decide |
| Traces | DVE.18, 28–49, 72–77; QA-03, QA-04, QA-11 |
| Resolves | DP-01…DP-08: the SRS rule sets deferred to the critical design phase, namely DVE.32–35 (topic QoS), DVE.39 (communication services in scope), DVE.40 (load balancing), DVE.41–43 (core allocation), DVE.44 (OS settings), DVE.45 (runtime memory allocation), DVE.49 (architectural rules) and DVE.18 (conformance classification), each through its catalog family (§2) |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

R3 builds structural verification (DVE.28–49):

* topic QoS conformance;
* publisher and consumer matching;
* communication consistency;
* load balancing;
* core, OS and memory allocation;
* resource contention, cycles and structural integrity;
* architectural rules.

DVE.76 requires each control rule to have an identifier, evaluation heading, severity, weight, acceptance criterion and blocking status. DVE.18 requires each result to be classified as conforming or non-conforming. DVE.77 mentions an "evaluation profile", which implies selectable rule sets.

The rule *contents* are deferred to the critical design phase (DP-01…08). They are domain rules that engineers will refine for years, not architecture. What is architecture: the engine and rule model, where the content lives, how it is versioned and approved, and how it is tested. These must be fixed now, so rules can be added as their content is approved.

## Decision Drivers

* One rule model must serve structural verification (R3) and installation evaluation (R7, DVE.72–77).
* Some checks are pattern queries (unmatched topics). Others need algorithms (cycles, capacity sums, contention).
* Parameters change more often than logic and are owned by domain engineers, whose approval and review are needed.
* Rules must be deterministic and read-only (DVE.29, QA-03), testable with small fixtures (QA-11), and traceable to the exact definition that produced each finding (QA-04).
* R3 must start before every rule set is agreed, so provisional rules must be distinguishable.

## Considered Options

* Engine: hybrid, with metadata and parameters as data and check logic as registered Python functions / rules as Cypher data only / rules as code only
* Catalog: a versioned catalog in the repository, approved by pull request / rules in the database, editable at runtime / one ADR per rule family

## Decision Outcome

Chosen options: **the hybrid engine** and **a versioned catalog in the repository**. Metadata and parameters belong to a catalog that domain engineers approve. Check logic needs Python and graph algorithms, but stays small, reviewed and tested. The repository gives history, review, CI tests and exact reproducibility, since the catalog version is a git tag, at no extra tooling cost.

### 1. Engine and rule model

**Rule record (data):**

| Field | Meaning |
|---|---|
| `rule_id` | Stable identifier, e.g. `QOS-DUR-001` |
| `version` | Semantic version of this rule's definition |
| `heading` | One of the DVE.72–75 headings, or a structural-verification family |
| `check` | Name of the registered check function |
| `params` | Parameters passed to the check |
| `severity` | `informational` / `low` / `medium` / `high` / `critical` (DVE.21) |
| `weight` | Used by installation scoring (DVE.76, ADR-0018) |
| `acceptance_criterion` | Human-readable statement of what conforms |
| `blocking` | Whether a violation blocks installation (DVE.77) |
| `status` | `provisional` / `approved` (§2) |

**Check function (code):**

```python
@check("topic_has_publisher")
def topic_has_publisher(model: ModelReader, params: Mapping) -> Iterable[Violation]: ...
```

* **`ModelReader`** is SMM's read-only handle (ADR-0003, ADR-0011). It offers parameterized Cypher and `to_networkx(subgraph)` (networkx 3.2.1, the last release for Python 3.9).
  * It is engine-neutral. The `IGraphStore` adapter scopes every query to the reader's instance, so checks never mention `instance_id` or graph names.
  * Its in-memory implementation runs the same checks in tests without a server.
* **Checks** yield `Violation`s: affected entity keys, evidence and an optional message. The engine adds the rule metadata to make findings (ADR-0007). A check never writes, calls external systems, or reads the clock or randomness.
* **Engine run:**
  1. Load a rule profile (§2).
  2. Run each check against the instance.
  3. Record one finding per violation.
  4. Classify the result.

  A check that raises an exception yields an `error` finding for that rule, and the other rules still run (DVE.24). At start-up the engine validates that every record's `check` exists.
* **Classification (DVE.18):** an operation is `non-conforming` if any finding comes from an approved rule with severity at or above the profile's threshold (default `high`), or from an approved blocking rule. Findings from provisional rules are reported but do not classify. Installation scoring adds weights (ADR-0018).

### 2. Catalog and governance

* **Location:** `dve/src/dve/rules/`, shipped as package data so the installed wheel carries the catalog (ADR-0004). There is one YAML file per family, loaded with PyYAML `safe_load` (6.0, already in `mdg/wheelhouse/`):

  | File | Rule family | Resolves |
  |---|---|---|
  | `qos.yaml` | Topic QoS (DVE.32–35) | DP-01 |
  | `communication.yaml` | External-to-middleware communication services in scope (DVE.39) | DP-02 |
  | `load_balancing.yaml` | Distribution across processing units (DVE.40) | DP-03 |
  | `cpu_allocation.yaml` | Core allocation (DVE.41–43) | DP-04 |
  | `os_settings.yaml` | OS settings (DVE.44) | DP-05 |
  | `memory.yaml` | Runtime memory allocation (DVE.45) | DP-06 |
  | `architecture.yaml` | Architectural rules (DVE.49) | DP-07 |
  | `structural.yaml` | Pub/sub matching, cycles, integrity (DVE.36–38, 46–48) | — |
  | `classification.yaml` | Conformance classification thresholds (DVE.18) | DP-08 |

* **Profiles:** `dve/src/dve/rules/profiles/<name>.yaml` selects rule IDs and overrides parameters, and can be scoped to a project or platform. `default.yaml` applies when none is named. Each installation-evaluation request names its profile (DVE.77).
* **Versioning:** each rule has its own `version`, and the catalog is versioned by the tag of the release that ships it. Every operation records the catalog version and profile (ADR-0007).
* **Approval:**
  * A rule enters as `provisional`, merged with development-team review.
  * Setting `status: approved` needs the CDR Board's domain owner for that family, recorded in the pull request.
* **Testing:** every rule ships with fixture models that must and must not trigger it, in `dve/tests/rules/fixtures/` (not shipped).
* **Runtime changes:** none. Users choose profiles at runtime but cannot edit rules.
* **Resolving DP-01…08:** a family is resolved when its file has at least one `approved` rule covering every requirement in its range. That pull request replaces the "to be determined" wording in the SRS with a link to the file and catalog version. Until then, the family is open in [ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr), and R3 runs with provisional rules.

### Consequences

* Good, because settling rule contents is a catalog change, not an engine change, under domain-expert control and without ADR churn.
* Good, because R3 and R7 share one engine and finding model, and every finding is reproducible from (catalog version, profile, instance revision).
* Good, because each check is a pure function, testable with fixture graphs.
* Bad, because a new *kind* of check, or a new threshold, needs a release. That is accepted, because traceability is worth more than edit speed.
* Bad, because checks must keep networkx subgraphs small for ADR-0020's budgets. Until the engine is chosen, their Cypher must stay within what both ADR-0011 candidates support.
* Bad, because domain owners review YAML in pull requests, so the format must stay readable and documented.

### Confirmation

* Every registered check has fixture tests that must and must not produce violations (ADR-0021).
* The whole approved profile runs against the dev seed model and is compared with a stored snapshot.
* A CI schema check validates every rule file against the rule record and every profile against the catalog.
* CI fails if an `approved` rule changes without a `version` bump.

## Pros and Cons of the Options

* Hybrid engine (chosen): Good, because each part has the right owner. Bad, because each rule has two artifacts, record and check, to keep consistent.
* Cypher data only: Good, because rules are editable without code. Bad, because cycles, capacity aggregation and contention are awkward in Cypher, and query text is untyped and hard to test.
* Code only: Good, because it is maximally expressive. Bad, because thresholds need releases, and severities and weights hide in code, beyond CDR Board review.
* Catalog in the repository (chosen): Good, because it has history, review, CI and reproducibility. Bad, because changes are release-bound.
* Database rules editable at runtime: Good, because changes are immediate. Bad, because changes are unreviewed and results hard to reproduce.
* ADR per family: Bad, because rule content is not architecture, and every threshold change would supersede an ADR.

## More Information

* [SRS §6.1.2, §6.1.4](../../requirements/SRS.md), [ADR Roadmap §6.1](../ADR-ROADMAP.md#61-deferred-design-points--adr)
* Related: ADR-0003, ADR-0004, ADR-0007, ADR-0010, ADR-0011, ADR-0018, ADR-0020, ADR-0021
