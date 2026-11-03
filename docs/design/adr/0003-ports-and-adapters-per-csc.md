# ADR-0003: Ports and Adapters per CSC

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team |
| Kind | Ratify |
| Traces | QA-11; MDG.2–5; DVE.3, 27; SDD §2.3 EXT-IF-01…07; SDP §5 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SaaG integrates with seven external systems (SDD §2.3). In development and test, most of these are unavailable or replaced by mocks (`dev/compose.yaml` runs MySQL and Gitea; LDAP and the system repository parser are mocks). SDP §5 names "Ports and Adapters (Hexagonal), real adapters in production, fake adapters in development, DI-selected". `mdg/` and `dve/` are built that way. This ADR records the pattern and its rules so that the four remaining CSCs follow it the same way.

## Decision Drivers

* Domain logic (validation, model construction, verification rules) must be testable without external systems (QA-11).
* External systems are only partly known (CDR-09, CDR-19, CDR-21). Their adapters will change without the domain changing.
* The existing code already follows the pattern; deviating would mean rework.

## Considered Options

* Ports and Adapters per CSC, with fakes selected by dependency injection (as built)
* Classic layered architecture (controllers → services → repositories)
* Direct integration: services call external libraries directly

## Decision Outcome

Chosen option: "Ports and Adapters per CSC", because it is already implemented and tested in `mdg/` and `dve/`, and it isolates the parts of the design that the CDR still leaves open.

Rules for every CSC package `<csc>/src/<csc>/`:

| Directory | Contains | May import |
|---|---|---|
| `domain/` | Immutable value objects and entities (`@dataclass(frozen=True)`), domain errors | standard library only |
| `ports/` | Abstract interfaces named `I<Name>` (ABCs) and the port-specific exceptions | `domain` |
| `services/` | Use cases, one class per use case, depending on ports only | `domain`, `ports` |
| `adapters/<area>/` | Implementations named `<Technology><Port>`, e.g. `GitSourceCodeRepository`, `RedisProductionLog` | `domain`, `ports`, third-party libraries |
| `__init__.py` | The CSC's public façade: factory functions that wire adapters to services (e.g. `mdg.produce_model_setup_data`) | everything in the package |

* Fakes live under `<csc>/tests/fakes/` as `Fake<Port>`, with a shared `seed.py`. They implement the same port and are selected in `conftest.py`.
* A mock adapter that stands in for an unknown external system in production code (as `LdapDirectoryService` and `SystemRepoParser` do today) says so in its first docstring line (`Mock: …`). It must be replaced before the release that needs the real system.
* Other CSCs use a CSC only through its façade (ADR-0007).

### Consequences

* Good, because each external-system decision (ADR-0010, 0011, 0020, 0030) only replaces an adapter.
* Good, because the test suites run without Docker services.
* Bad, because there is extra indirection for simple CRUD paths.
* Bad, because fakes must be kept in step with ports. Today `dve/tests/fakes/` duplicates parts of `mdg/tests/fakes/`.

### Confirmation

* An `import-linter` contract per package in CI: `domain` imports nothing from the package; `services` does not import `adapters`.
* ADR-0041 sets adapter contract tests that run the same test cases against the fake and the real adapter.

## Pros and Cons of the Options

### Ports and Adapters (as built)

* Good, because external uncertainty is isolated and the design is testable.
* Bad, because there are more files and interfaces.

### Layered architecture

* Good, because it is familiar and simple.
* Bad, because repositories are usually bound to one persistence technology, and swapping in fakes needs mocking frameworks.

### Direct integration

* Good, because it has the least code.
* Bad, because tests need the real systems, and every CDR protocol decision touches the domain logic.

## More Information

* Code: `mdg/src/mdg/{domain,ports,services,adapters}`, `dve/src/dve/{domain,ports,services,adapters}`
* [SDP §5](../../planning/SDP.md), "External-integration architecture"
