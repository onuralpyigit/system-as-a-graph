# System as a Graph (SaaG)

**A static digital system model that represents a distributed publish–subscribe system's structural and relational architecture as a node-relationship graph — without ever running the target system.**

![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Status](https://img.shields.io/badge/status-in--development-orange)

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

Implementation has begun. The repository has the full documentation set, a scaffolded FastAPI backend ([`main.py`](main.py)), and a scaffolded Next.js frontend ([`web/`](web/)). Each CSU's internals — use cases, domain model, adapters — are still empty; only the folder structure is in place.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/requirements/SSS.md`](docs/requirements/SSS.md) | System/Subsystem Specification — the 112 CSCI-level requirements. |
| [`docs/requirements/SRS.md`](docs/requirements/SRS.md) | Software Requirements Specification — 156 CSU-scoped requirements derived from SSS. |
| [`docs/planning/SDP.md`](docs/planning/SDP.md) | Software Development Plan — WBS, 7-increment development schedule, and project structure. |
| [`docs/design/SDD.md`](docs/design/SDD.md) | Software Design Description — CSCI-wide design decisions, architecture, interfaces, database design, and CSU-level detailed design. |
| [`docs/design/UXD.md`](docs/design/UXD.md) | UI/UX Design Document — visual identity, layout, and interaction design for the VAE-01 Operations Panel. |
| [`docs/design/CDR.md`](docs/design/CDR.md) | Critical Design Review — open items register consolidating every design point left "to be determined during the critical design phase." |
| [`docs/test/STD.md`](docs/test/STD.md) | Software Test Description — qualification test cases and procedures mapped to SDD design elements and SRS requirements. |

The document set is fully traceable across documents.

## Repository layout

Every top-level backend directory maps to exactly one CSC and owns its own hexagonal boundary (`api/`, `use_cases/`, `model/`, `ports/`, `adapters/`). `web/` and `cli/` implement the VAE-01 user-facing applications. See [Table 4 in the SDP](docs/planning/SDP.md#4-project-structure) for the full directory mapping.

```
docs/            # SSS, SRS, SDP, SDD, UXD, CDR, STD
web/             # VAE-01: web application
cli/             # VAE-01: command-line application
msd/             # MSD: Model Setup Data Generation
scg/             # SCG: Scenario Generator
frd/             # FRD: Field Records Database
adp/             # ADP: Analytical Data Preparation
csm/             # CSM: Node-Relationship Based Core System Model (CSM-01 model_manager, CSM-02 data_binder)
vae/             # VAE: Design Verification, Analysis and Evaluation (VAE-02 design_verifier, VAE-03 design_analyzer, VAE-04 design_evaluator)
shared/          # contracts, types, errors, security shared across CSCs
tests/           # integration and acceptance tests
main.py          # FastAPI app aggregating each CSC's router
LICENSE          # Apache License 2.0
```

## Getting started

Run the API and web app in containers. The API is served at http://localhost:8000 and the web app at http://localhost:3000.

### Development

Hot reload, with source bind-mounted into the containers:

```bash
docker compose -f compose.dev.yaml up --build   # start
docker compose -f compose.dev.yaml down         # stop and remove
```

Testing and linting, against the running dev stack:

```bash
docker compose -f compose.dev.yaml exec api pytest
docker compose -f compose.dev.yaml exec api ruff check .
docker compose -f compose.dev.yaml exec web npm run lint
docker compose -f compose.dev.yaml exec web npm run test:e2e
```

### Production

Standalone builds, no bind mounts:

```bash
docker compose up --build   # start
docker compose down         # stop and remove
```

## License

Released under the Apache License 2.0 — see [`LICENSE`](LICENSE).
