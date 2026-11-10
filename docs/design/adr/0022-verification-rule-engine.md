# ADR-0022: Verification rule engine and rule model

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering |
| Kind | Decide |
| Traces | DVE.18, 28–49, 72–77; QA-03, QA-11 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

R3 builds structural verification (DVE.28–49):

- topic QoS conformance;
- publisher/consumer matching;
- communication consistency;
- load balancing;
- core, OS and memory allocation;
- resource contention, cycles and structural integrity;
- architectural rules.

DVE.76 requires each control rule to have an identifier, evaluation heading, severity, weight, acceptance criterion and blocking status. DVE.18 requires each result to be classified as conforming or non-conforming. The rule *contents* are still open (CDR-01…08, governed by ADR-0023). The *engine* must be fixed now, so that rules can be added as the CDR closes them, without rework.

## Decision Drivers

* The same rule model must serve structural verification (R3) and installation evaluation (R7; DVE.72–77).
* Some checks are pattern queries (unmatched topics); others need algorithms (cycles, capacity sums, contention).
* Rule parameters (thresholds, allowed QoS combinations) change more often than rule logic, and they are owned by domain engineers (ADR-0023).
* Rules must be deterministic and read-only on the model (DVE.29, QA-03).
* Each rule must be testable in isolation with small fixture models (QA-11).

## Considered Options

* Rules as data only: each rule is a declarative Cypher query plus metadata
* Rules as code only: each rule is a Python class with hard-coded metadata
* Hybrid: rule metadata and parameters as data, check logic as registered Python check functions that may use Cypher or algorithms

## Decision Outcome

Chosen option: "Hybrid". Metadata and parameters belong to the catalog that domain engineers approve (ADR-0023). Check logic needs the full power of Python and graph algorithms, but it must stay small, reviewed and tested.

**Rule record (data, from the catalog):**

| Field | Meaning |
|---|---|
| `rule_id` | Stable identifier, e.g. `QOS-DUR-001` |
| `version` | Semantic version of this rule's definition |
| `heading` | Evaluation heading: one of the DVE.72–75 headings or a structural-verification family |
| `check` | Name of the registered check function |
| `params` | Parameters passed to the check (thresholds, allowed values) |
| `severity` | `informational` / `low` / `medium` / `high` / `critical` (DVE.21) |
| `weight` | Weight used by installation scoring (DVE.76, ADR-0027) |
| `acceptance_criterion` | Human-readable statement of what conforms |
| `blocking` | Whether a violation blocks installation (DVE.77) |
| `status` | `provisional` / `approved` (ADR-0023) |

**Check function (code):**

```python
@check("topic_has_publisher")
def topic_has_publisher(model: ModelReader, params: Mapping) -> Iterable[Violation]: ...
```

* `ModelReader` is SMM's read-only handle (ADR-0007, ADR-0016). It offers parameterized Cypher queries and `to_networkx(subgraph)` for algorithms.
* A check yields `Violation`s: the affected entity keys, evidence and an optional message. The engine turns them into findings (ADR-0024) by adding the rule metadata.
* A check must not write, call external systems, or read the clock or randomness.

**Engine:**

1. Load a *rule profile* (a set of rule IDs with parameter overrides, ADR-0023).
2. Run each rule's check against the instance.
3. Record one finding per violation.
4. Classify the operation result.

A rule whose check raises an exception yields an `error` finding for that rule; the other rules still run (DVE.24).

**Classification (DVE.18):** an operation is `non-conforming` if any finding comes from an approved rule with severity ≥ the profile's threshold (default `high`), or from an approved blocking rule. Otherwise it is `conforming`. Findings from `provisional` rules are reported but do not affect classification. Installation scoring adds weights per ADR-0027.

### Consequences

* Good, because CDR-01…08 closure becomes a catalog change (parameters or new rules), not an engine change.
* Good, because R3 and R7 share one engine and one finding model.
* Good, because each check is a pure function, testable with fixture graphs.
* Bad, because a new *kind* of check still needs code and a release.
* Bad, because checks that convert to NetworkX must keep subgraphs small to meet the time budgets of ADR-0036.

### Confirmation

* Every registered check has unit tests with a fixture model that must produce violations and one that must not (ADR-0041).
* A test runs the whole approved profile against the dev seed model and compares the result to a stored snapshot.

## Pros and Cons of the Options

### Rules as data only (Cypher)

* Good, because rules are fully editable without code.
* Bad, because cycle detection, capacity aggregation and contention analysis are awkward or impossible in the supported Cypher subset (ADR-0015), and the query text is untyped and hard to test.

### Rules as code only

* Good, because it is maximally expressive.
* Bad, because changing a threshold needs a code release, and severities and weights would be hidden in code, beyond review by the CDR Board.

### Hybrid

* Good, because it gives the right owner for each part.
* Bad, because there are two artifacts per rule (record + check) to keep consistent. The engine validates that every record's `check` exists at start-up.

## More Information

* [SRS §6.1.2, §6.1.4](../../requirements/SRS.md)
* Related: ADR-0014, ADR-0016, ADR-0023, ADR-0024, ADR-0027, ADR-0036
