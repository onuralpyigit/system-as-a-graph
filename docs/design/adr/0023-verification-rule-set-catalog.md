# ADR-0023: Verification rule-set catalog and governance

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, system engineering, middleware owners |
| Kind | Decide |
| Traces | DVE.18, 32–49, 76–77; QA-04, QA-11 |
| Closes | CDR-01, CDR-02, CDR-03, CDR-04, CDR-05, CDR-06, CDR-07, CDR-08 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

CDR-01…08 leave the *content* of the verification rules open: QoS rules, communication services in scope, load balancing, core allocation, OS settings, memory allocation, architectural rules, and classification metrics. These are domain rules that engineers will refine for years. They are not architecture decisions. Writing each rule set as an ADR would turn every threshold change into an ADR.

What *is* an architecture decision is where rule content lives, how it is versioned, who approves it, and how it is tested. ADR-0022 fixes the rule record format. DVE.77 also mentions an "evaluation profile", which implies selectable rule sets.

## Decision Drivers

* Every finding must be traceable to the exact rule definition that produced it (QA-04).
* Rule changes need domain-expert approval and review.
* R3 must start before every rule set is agreed. Provisional rules must be distinguishable from approved ones.
* Different projects or platforms may need different thresholds (DVE.77 "evaluation profile").

## Considered Options

* A versioned rules catalog in the repository, approved by pull request
* Rules in the database, editable at runtime through an admin UI
* One ADR per rule family

## Decision Outcome

Chosen option: "A versioned rules catalog in the repository, approved by pull request", because it gives a full history, review, testing in CI, and exact reproducibility (catalog version = git tag) at no extra tooling cost.

* **Location:** `dve/rules/` with one YAML file per family:

  | File | Rule family | Closes |
  |---|---|---|
  | `qos.yaml` | Topic QoS (DVE.32–35) | CDR-01 |
  | `communication.yaml` | External-to-middleware communication services in scope (DVE.39) | CDR-02 |
  | `load_balancing.yaml` | Distribution across processing units (DVE.40) | CDR-03 |
  | `cpu_allocation.yaml` | Core allocation (DVE.41–43) | CDR-04 |
  | `os_settings.yaml` | OS settings (DVE.44) | CDR-05 |
  | `memory.yaml` | Runtime memory allocation (DVE.45) | CDR-06 |
  | `architecture.yaml` | Architectural rules (DVE.49) | CDR-07 |
  | `structural.yaml` | Pub/sub matching, cycles, integrity (DVE.36–38, 46–48) | — |
  | `classification.yaml` | Conformance classification thresholds (DVE.18) | CDR-08 |

* **Profiles:** `dve/rules/profiles/<name>.yaml` selects rule IDs and overrides parameters. A profile can be scoped to a project or platform. `default.yaml` is used when none is selected. Each installation-evaluation request names its profile (DVE.77).
* **Versioning:**
  * Each rule has its own `version`.
  * The catalog as a whole is versioned by the repository tag of the release that ships it.
  * Every operation records the catalog version and profile used (ADR-0024).
* **Approval:**
  * A rule enters as `provisional`. It can be merged with development-team review, and it is reported but does not affect classification (ADR-0022).
  * Setting `status: approved` needs approval from the CDR Board's designated domain owner for that family, recorded in the pull request.
* **Testing:** every rule ships with fixture models that must and must not trigger it (`dve/rules/fixtures/`). CI runs them.
* **Runtime changes:** none. Users choose profiles at runtime, but they cannot edit rules. A new threshold needs a catalog change and a release.
* **CDR closure:** CDR-01…08 are each set to `Resolved` when their family file contains at least one `approved` rule covering every requirement in the CDR item's source range. The CDR entry links to the file and the catalog version. Until then, the item stays `Open`, and R3 runs with provisional rules.

### Consequences

* Good, because rule content can evolve under domain-expert control without ADR churn.
* Good, because every finding is reproducible from (catalog version, profile, model instance revision).
* Bad, because changing a threshold needs a release. That is accepted: the traceability is worth more than the edit speed.
* Bad, because domain owners must review YAML in pull requests, so the format must stay readable and documented.

### Confirmation

* A CI schema check validates every rule file against the rule record (ADR-0022) and every profile against the catalog.
* The fixture tests pass for every rule.
* A CI check fails if an `approved` rule changes without a `version` bump.

## Pros and Cons of the Options

### Versioned catalog in the repository

* Good, because it has history, review, CI and reproducibility.
* Bad, because changes are release-bound.

### Database rules editable at runtime

* Good, because changes are immediate.
* Bad, because changes are unreviewed and history needs extra auditing. Results become hard to reproduce, and there is no fixture testing.

### ADR per rule family

* Good, because it uses the same process as other decisions.
* Bad, because rule content is not architecture, and every threshold change would be an ADR supersession.

## More Information

* [CDR §1.1](../CDR.md)
* Related: ADR-0022, ADR-0024, ADR-0027, ADR-0041
