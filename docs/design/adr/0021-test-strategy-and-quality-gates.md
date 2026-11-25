# ADR-0021: Test strategy and quality gates

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, QA |
| Kind | Ratify |
| Traces | QA-11; STD; ADR-0003 |
| Resolves | — |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

The [STD](../../test/STD.md) defines 40 qualification test cases (one per SDD §3 design element) covering all 157 SRS requirements. Beneath qualification testing, SaaG needs a uniform automated test pyramid across all six CSC packages and `common/`, plus strict CI quality gates that run offline on CPython 3.9.

**As built (`1157784` + `f820ccb`) and audit findings:**

* **Per-package `pytest` suites:** `mdg/pytest.ini` and `dve/pytest.ini` set `pythonpath = src tests` and `testpaths = tests` (`mdg`: **132** collected tests; `dve`: **111** collected tests, including 63 parametrized items in `test_api.py`). Commit `f820ccb` pinned `Werkzeug>=2.3.7,<3.1` (`werkzeug-2.3.8` in `dve/wheelhouse/`) after Werkzeug 3.1.9 broke Flask 2.3.2's test client.
* **Seed divergence between fakes and `dev/`:** `mdg/tests/fakes/fake_source_code_repository.py` gives `sensor_app` a valid `Makefile` and no Java file, whereas `dev/gitea/seed/sensor_app_1.0.0/` and `common_lib_1.0.0/` lack `Makefile`s, and `dev/mysql/init.sql` defines version `0.9.0` without matching `*_0.9.0` Git seed directories—which would break adapter contract parity unless unified (`ADR-0008 §3`). Also `dve/tests/fakes/` duplicates three `mdg` fake modules (`ADR-0003 §1`).
* **Offline test-runner & browser gotchas on CPython 3.9:**
  * `pytest` and `import-linter` are not in runtime wheelhouses, and **`import-linter >= 2.1` dropped Python 3.9** (must pin `import-linter <= 2.0` with `grimp <= 3.1` for CPython 3.9 CI).
  * Mozilla never issued an ESR on major version 90—the ESR release covering the Firefox 90+ engine floor is **`Firefox 91 ESR`** (`ADR-0015 §3`). Moreover, Playwright's Firefox driver (`juggler`) drives only Playwright's custom-patched Firefox build rather than stock Mozilla ESR binaries, requiring clear separation between Playwright regression gates and stock `Firefox 91 ESR` WebDriver (`geckodriver`) verification.

## Decision Drivers

* Fast unit, domain, service, rule and API tests must run in seconds with zero Docker services and zero network access (QA-11, ADR-0003).
* CI gates must install strictly from local CPython 3.9 wheelhouses (`pip install --no-index`) so wheel mismatches (such as the Werkzeug 3.1 break or `manylinux_2_28` tags) are caught immediately (ADR-0004).
* Fake adapters and `dev/` containers must share one canonical seed definition so adapter contract tests prove real/fake behavioral equivalence.
* Database migrations, WAL concurrency (ADR-0007), `saag @ 0bbe06af` derivation parity (ADR-0010), browser accessibility (`Firefox 91 ESR`, ADR-0015), and ADR/roadmap trace invariants (ADR-0001) must all be gated mechanically.

## Considered Options

* Per-package `pytest` suites with injected fakes (as built), extended with contract, SQLite migration/WAL, rule-fixture, `saag` parity, browser, wheelhouse and offline-install gates
* Single monolithic repository-root `pytest` suite importing all packages together
* End-to-end tests against the `dev/` Docker Compose stack only

## Decision Outcome

Chosen option: **per-package `pytest` suites with injected fakes (as built), extended with adapter contract, database migration/WAL, rule-fixture, graph-parity, browser (`Firefox 91 ESR` + Playwright), wheelhouse/doc-lint, and offline-install gates**.

### 1. Test pyramid and execution levels

| Level | Location | Runtime dependencies | Gate trigger |
|---|---|---|---|
| Unit & service | `common/tests/` and `<csc>/tests/{domain,services,adapters}` using `<csc>.testing` fakes | CPython 3.9 + offline wheelhouses only | Every commit / PR |
| API & OpenAPI contract | `dve/tests/test_api.py` (`create_app()` over fakes + OpenAPI URL-map & response-schema check, ADR-0005) | CPython 3.9 + offline wheelhouses only | Every commit / PR |
| SQLite migration & WAL concurrency | `common/tests/test_migrations.py` & `test_wal_concurrency.py` (fresh + upgrade SQL migrations, `pysqlite3` fallback in `spawn` workers, 10-worker concurrent write test, ADR-0007) | CPython 3.9 + `pysqlite3-binary` | Every commit / PR |
| Rule fixtures | `dve/tests/rules/` (positive & negative fixture graphs per rule + `causes_from` link checks, ADR-0016) | CPython 3.9 + `InMemoryGraphStore` | Every change to `dve/` or `smm/` |
| Framework graph parity | `smm/tests/fixtures/framework_0bbe06af/` (`w(T0)=0.5938`, `w(L0)=0.6555`, `app_to_lib=0.6231`, Rules 1–7) + 200-instance isolation against the ADR-0011 graph server | CPython 3.9 (+ graph server for integration part) | Every change to `smm/` |
| Adapter contract | `<csc>/tests/contract/` running one shared test mixin against both `Fake<Port>` and the real adapter (`dev/` MySQL 9.7.2, Gitea 1.27.3, OpenLDAP, mock Package REST) over unified seed data | `dev/compose.yaml` (developer/CI host) | Every adapter/seed change; nightly |
| Browser & WCAG 2.1 AA | Playwright (bundled Firefox + vendored `axe-core`) on every UI change, plus Selenium WebDriver (`geckodriver`) smoke & ES/CSS compatibility gate against stock **Firefox 91 ESR** and current Firefox ESR (ADR-0015) | CI browser runner (never installed on target host) | Every change to `templates/` or `static/`; nightly |
| Offline install & capacity | `deploy/install.sh` on a network-disconnected CentOS-7-compatible VM (`glibc 2.17`), plus R8 reference-model load suite (ADR-0004, ADR-0020) | Offline CentOS 7 VM | Every release tag (and R8 DoD) |
| Qualification | 40 [STD](../../test/STD.md) test cases (`TC-MDG-*`..`TC-DVE-*`) | Test environment | Each release DoD |

### 2. Offline CPython 3.9 CI gates and test wheelhouse

* **`dev/wheelhouse-test/`:** holds pinned CPython 3.9 (`manylinux2014_x86_64` / `py3-none-any`) wheels for developer and offline-VM test execution—specifically `pytest` (`8.3.x`, `<8.4` with `pluggy`, `iniconfig`, `packaging`, `exceptiongroup`, `tomli`) and **`import-linter<=2.0` (`grimp<=3.1`)** because `import-linter >= 2.1` requires Python ≥ 3.10. Nothing in `dev/wheelhouse-test/` is installed onto production `/opt/dsm/venv/`.
* **Mandatory fast gates on every pull request:**
  1. Install runtime distributions from `*/wheelhouse/` + test runners from `dev/wheelhouse-test/` using `pip install --no-index` on CPython 3.9, and pass all unit, service, API, rule-fixture, `0bbe06af` in-memory parity, and SQLite migration/WAL suites;
  2. Wheelhouse tag audit (rejecting `manylinux_2_28` or Python `>=3.10`-only wheels, ADR-0004 §2);
  3. `import-linter` hexagonal and cross-CSC dependency contracts (ADR-0003, ADR-0004);
  4. Canonical identifier & citation grep (ADR-0002);
  5. Static external-URL check on `templates/` and `static/` (ADR-0015);
  6. ADR & [ADR Roadmap](../ADR-ROADMAP.md) consistency check (gapless numbering, header `Status`/`Kind`/`Wave`/`Traces` parity with Tables 2–6, and zero residual `"to be determined during the critical design phase"` strings for accepted `DP-*` items, ADR-0001).
* **Seed unification (To build in R3):** align `dev/mysql/init.sql` and `dev/gitea/seed/` with `mdg.testing.seed` (moving shared fakes from `dve/tests/fakes/` to `mdg.testing` per ADR-0003 §1) so positive `1.0.0` runs and negative missing-file/version cases behave identically across unit and contract suites.

### Consequences

* Good, because fast per-package suites run offline in seconds on the exact production wheels, catching packaging breaks (`Werkzeug 3.1`, `manylinux_2_28`, `import-linter 2.1`) before merge.
* Good, because separating Playwright regression checks from stock `Firefox 91 ESR` `geckodriver` checks avoids Playwright's `juggler` ESR limitation while genuinely testing the Firefox 90+ floor.
* Bad, because CI must maintain `dev/wheelhouse-test/`, Docker services for contract gates, and archived `Firefox 91 ESR` binaries.

### Confirmation

* CI pipeline configuration executes all six fast gates on CPython 3.9 with `--no-index`, plus adapter contract and browser (`Firefox 91 ESR` + current ESR + `axe-core`) jobs.
* Every bug fix in `mdg/`, `dve/` and future CSCs includes a regression test that fails prior to the fix.

## Pros and Cons of the Options

### Per-package `pytest` with fakes, extended with multi-tier gates (chosen)

* Good, because package boundaries stay crisp, unit feedback takes seconds without Docker, and contract/browser/install gates verify real external seams where mocks fall short.
* Bad, because CI orchestrates multiple test stages and `dev/wheelhouse-test/`.

### Single repository-wide `pytest` suite

* Good, because one `pytest` invocation runs everything.
* Bad, because `sys.path` and third-party wheel isolation between CSC packages blur, masking undeclared cross-package dependencies.

### End-to-end tests against `dev/` Docker stack only

* Good, because real MySQL/Gitea/LDAP containers run every time.
* Bad, because suites are slow, cannot run on containerless air-gapped hosts, and localize domain/rule failures poorly.

## More Information

* Code: `mdg/pytest.ini`, `dve/pytest.ini`, `mdg/tests/`, `dve/tests/`, `dve/tests/conftest.py`, `dve/setup.py`, `dev/compose.yaml`
* [STD](../../test/STD.md)
* Related: ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0007, ADR-0010, ADR-0011, ADR-0015, ADR-0016
* Revisit if the minimum supported workstation browser floor advances from Firefox 90/91 ESR to a newer ESR baseline, retiring the archival `Firefox 91 ESR` WebDriver job.
