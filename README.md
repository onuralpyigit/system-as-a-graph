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
| [`docs/requirements/SRS.md`](docs/requirements/SRS.md) | Software Requirements Specification — unified system and software requirements (156 CSU-scoped functional requirements, 1 platform infrastructure constraint, and system capability allocation). Available in English ([`SRS.md`](docs/requirements/SRS.md)) and Turkish ([`SRS.tr.md`](docs/requirements/SRS.tr.md)). |
| [`docs/planning/SDP.md`](docs/planning/SDP.md) | Software Development Plan — WBS, 7-increment development schedule, and project structure. |
| [`docs/design/SDD.md`](docs/design/SDD.md) | Software Design Description — CSCI-wide design decisions, architecture, interfaces, database design, and CSU-level detailed design. |
| [`docs/design/UXD.md`](docs/design/UXD.md) | UI/UX Design Document — visual identity, layout, and interaction design for the VAE-01 Operations Panel. |
| [`docs/design/CDR.md`](docs/design/CDR.md) | Critical Design Review — open items register consolidating every design point left "to be determined during the critical design phase." |
| [`docs/test/STD.md`](docs/test/STD.md) | Software Test Description — qualification test cases and procedures mapped to SDD design elements and SRS requirements. |

The document set is fully traceable across documents.

## Repository layout

Every top-level backend directory maps to exactly one CSC and owns its own hexagonal boundary (`api/`, `use_cases/`, `model/`, `ports/`, `adapters/`). `web/` and `cli/` implement the VAE-01 user-facing applications. See [Table 4 in the SDP](docs/planning/SDP.md#4-project-structure) for the full directory mapping.

```
docs/            # SRS, SDP, SDD, UXD, CDR, STD
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

The API runs on http://localhost:8000 and the web app on http://localhost:3000, whether run locally or via Docker.

### Backend (Python 3.11+)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install .
uvicorn main:app --reload
```

Run tests and linting:

```bash
pytest
ruff check .
```

### Web app (Next.js)

```bash
cd web
npm install
npm run dev
```

Run end-to-end tests and linting:

```bash
npx playwright install --with-deps chromium # one-time browser download
npm run test:e2e
npm run lint
```

### Docker

Run the API and web app in containers, without installing Python or Node locally.

**Development** — hot reload, with source bind-mounted into the containers:

```bash
docker compose -f compose.dev.yml up --build
```

**Production** — standalone builds, no bind mounts:

```bash
docker compose up --build
```

Stop and remove containers:

```bash
docker compose -f compose.dev.yml down    # dev
docker compose down                       # prod
```

## License

Released under the Apache License 2.0 — see [`LICENSE`](LICENSE).
