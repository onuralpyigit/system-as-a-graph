# System as a Graph (SaaG)

**A static digital system model that represents a distributed publish–subscribe system's structural and relational architecture as a node-relationship graph — without ever running the target system.**

![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Status](https://img.shields.io/badge/status-documentation--only-orange)

---

## Overview

SaaG models a target system's architecture as a typed graph: software units, middleware and communication services, processor/console units, topics, and messages become nodes; dependency, publishing, and consuming relationships between them become edges. Behavioral analysis is added not by executing components, but by overlaying **Analytical Evaluation Data** — derived from field records or from a scenario generator — onto this structural graph.

The model's primary purpose is architectural verification at design time: structural/circular dependencies, publisher–consumer matching, topic QoS conformance, hardware capacity conformance, and design patterns that violate architectural rules are all statically audited before any software unit is installed in the target environment. It also detects **architectural drift** between the designed structure and what is observed in the field, and supports hypothetical scenario analysis — evaluating how an entity going down, a spike in message density, or a bandwidth reduction would propagate through the architecture — without altering the structural model itself.

## Capability areas

Per the SRS, SaaG is organized into six Computer Software Components (CSCs) and ten Computer Software Units (CSUs):

| CSC | CSU | Abbreviation | Requirements |
|---|---|---|---|
| Model Setup Data Generation | MSD | MSD | 23 |
| Scenario Generator | SCG | SCG | 7 |
| Field Records Database | FRD | FRD | 5 |
| Analytical Data Preparation | ADP | ADP | 6 |
| Node-Relationship Based Core System Model | CSM-01, CSM-02 | CSM | 37 |
| Design Verification, Analysis and Evaluation | VAE-01, VAE-02, VAE-03, VAE-04 | VAE | 78 |
| **Total** | | | **156** |

## Current status

This repository currently contains the **structured documentation set** for SaaG. No implementation exists yet — there is no application code, CLI, API, or UI.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/requirements/SSS.md`](docs/requirements/SSS.md) | System/Subsystem Specification — the 112 CSCI-level requirements. |
| [`docs/requirements/SRS.md`](docs/requirements/SRS.md) | Software Requirements Specification — 156 CSU-scoped requirements derived from SSS. |
| [`docs/planning/SDP.md`](docs/planning/SDP.md) | Software Development Plan — WBS, 10-increment development schedule, and project structure. |
| [`docs/design/SDD.md`](docs/design/SDD.md) | Software Design Description — CSCI-wide design decisions, architecture, interfaces, database design, and CSU-level detailed design. |
| [`docs/design/UXD.md`](docs/design/UXD.md) | UI/UX Design Document — visual identity, layout, and interaction design for the VAE-01 Operations Panel. |
| [`docs/design/CDR.md`](docs/design/CDR.md) | Critical Design Review — open items register consolidating every design point left "to be determined during the critical design phase." |
| [`docs/test/STD.md`](docs/test/STD.md) | Software Test Description — qualification test cases and procedures mapped to SDD design elements and SRS requirements. |

The document set is fully traceable across documents.

## Repository layout

```
docs/
  requirements/  # SSS and SRS
  planning/      # SDP
  design/        # SDD, UXD, and CDR
  test/          # STD
LICENSE
```

## License

Released under the Apache License 2.0 — see [`LICENSE`](LICENSE).
