# ADR-0021: Test strategy and quality gates

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, QA |
| Kind | Ratify |
| Traces | QA-11; STD; ADR-0003 |
| Resolves | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The STD defines qualification test cases per SDD design element. Below that level, the project needs a common way to test each CSC, its adapters, rules and UI, and a set of gates that every change must pass. SDP §5 names pytest and Playwright.

As built (`1157784`):

* **Layout:** each package has its own pytest suite. `mdg/pytest.ini` and `dve/pytest.ini` both set `pythonpath = src tests` and `testpaths = tests`. Tests are grouped as `tests/adapters/`, `tests/domain/` and `tests/services/`, plus top-level façade, config and API tests.
* **Fakes:** in `tests/fakes/` (ADR-0003). They include `FakeConfigManagementRepository`, `FakeSourceCodeRepository`, recording parser fakes, `FakeTaskRunner` and `scripted_task`. A `seed.py` mirrors the `dev/` seed: project `skywatch`, platform `nftw`, version `1.0.0`.
* **External tools are never needed.** `subprocess.run` (for `git` and `gmake`) and `pymysql` are monkeypatched. `dve/tests/conftest.py` builds the app with `create_app(runtime)` over the fakes and mdg's real filesystem store in a temporary workspace, and uses a test client that follows the UI's CSRF token-and-retry behaviour.
* **The real task runner is tested.** `MultiprocessingTaskRunner` runs through spawned processes for success, failure, crash, concurrency, cancel and signal handling.
* **Results on 2026-11-19, Python 3.11 in a scratch environment:**
  * `mdg`: 132 tests pass.
  * `dve`: with the Werkzeug 3.1.9 then shipped in `dve/wheelhouse/`, 28 tests failed and 35 errored, because Flask 2.3.2's test client reads `werkzeug.__version__`, which Werkzeug 3.1 removed. After the pin below, all 111 tests pass.
* There is no CI configuration in the repository, and no browser test.

## Decision Drivers

* Domain logic, adapters and rules must be testable without the external systems (QA-11, ADR-0003).
* Tests must run in the offline target environment: CPython 3.9 with the wheelhouses (ADR-0004).
* The real external systems differ from the fakes, so each adapter also needs a test against something real.
* UI regressions must be caught in the oldest supported browser (ADR-0015).

## Considered Options

* Per-package pytest with fakes (as built), extended with contract, rule, parity, browser and install gates
* A single repository-wide test suite
* End-to-end tests only, against the `dev/` stack

## Decision Outcome

Chosen option: "Per-package pytest with fakes (as built), extended with contract, rule, parity, browser and install gates".

**Test levels:**

| Level | Where | Needs | Gate |
|---|---|---|---|
| Unit and service | `<csc>/tests/{domain,services,adapters}` with fakes | Python only | Every change |
| API | `dve/tests/test_api.py` through `create_app()` | Python only | Every change |
| Adapter contract | `<csc>/tests/contract/`: the same cases against the fake and the real adapter | The `dev/` Docker stack (MySQL, Gitea, OpenLDAP) | Every change to an adapter; nightly |
| Rule fixtures | `dve/tests/rules/fixtures/`: models that must and must not trigger each rule (ADR-0016) | Python only | Every change to a rule or the engine |
| Graph parity | `smm/tests/fixtures/framework_d1f8b424/` (ADR-0010), plus the isolation tests of ADR-0011 against the chosen graph server | The graph server for the second part | Every change to SMM |
| Browser | Playwright against `dsm` running with fake adapters, in Firefox 90 ESR and the current Firefox ESR (ADR-0015) | Firefox builds | Every change to `static/` or `templates/`; nightly |
| Install | `deploy/install.sh` on a CentOS-7-compatible host without network (ADR-0004) | That host or VM | Every release |
| Qualification | STD test cases | Test environment | Each release DoD |

**Gates for every change:**

* the unit, service and API suites pass on CPython 3.9, with dependencies installed from the wheelhouses only (`pip install --no-index`), not from PyPI;
* the `import-linter` contracts of ADR-0003 and ADR-0004 pass;
* the citation grep of ADR-0002 passes;
* the OpenAPI contract test of ADR-0005 passes;
* the external-URL check of ADR-0015 passes.

**Rules:**

* Fakes are kept next to their port's consumers until a second CSC needs them; then they move to an importable `<csc>.testing` module (ADR-0003).
* A bug fix comes with a test that fails without it.
* Tests never call real production systems and never need internet access.
* Browser tests may use Playwright from the development machine's toolchain; nothing from it is installed on the target host.

**Werkzeug pin (done 2026-11-19):** `dve/setup.py` requires `Werkzeug>=2.3.7,<3.1`. `dve/wheelhouse/` carries `werkzeug-2.3.8-py3-none-any.whl` in place of 3.1.9, and its README's `pip download` command includes the pin. Lifting the pin means moving to a Flask release that supports Werkzeug 3.1, together with that Flask upgrade.

### Consequences

* Good, because the fast suites stay independent of Docker and of the network, as built.
* Good, because the gate runs with the same wheels as production, which would have caught the Werkzeug mismatch.
* Bad, because contract and browser tests need the `dev/` stack and Firefox builds in CI, and are slower.
* Bad, because there is no CI service yet; one must be chosen and set up (it is not part of the product).

### Confirmation

* The CI configuration runs every gate listed above, and the release DoD (SDP §2) cites this ADR.
* The `dve` suite passes on CPython 3.9 with packages installed only from the wheelhouse.

## Pros and Cons of the Options

### Per-package pytest with fakes, extended (as built)

* Good, because it is fast, already exists, and matches the package boundaries.
* Bad, because several suites and environments must be orchestrated.

### Single repository-wide suite

* Good, because there is one command.
* Bad, because it blurs package boundaries and makes every package's tests depend on every other's dependencies.

### End-to-end only

* Good, because it exercises real behaviour.
* Bad, because it is slow, needs the Docker stack for every change, and gives poor fault localisation.

## More Information

* Code: `mdg/pytest.ini`, `dve/pytest.ini`, `mdg/tests/`, `dve/tests/`, `dve/tests/conftest.py`, `dve/setup.py`, `dve/wheelhouse/`
* [STD](../../test/STD.md)
* Related: ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0015, ADR-0010, ADR-0011, ADR-0016
