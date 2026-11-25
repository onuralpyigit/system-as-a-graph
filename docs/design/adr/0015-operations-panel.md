# ADR-0015: Operations Panel: frontend, graph view and browser support

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, UX |
| Kind | Ratify |
| Traces | DVE.1, 4–27, 57–58, 70; QA-07, QA-10, QA-12; UXD §1–7 |
| Resolves | — |
| Decide by | Wave A1 (2026-12-04) |
| Supersedes | — |

## Context and Problem Statement

Earlier UXD and SDP §5 drafts assumed Next.js 14, React 18, Refine, shadcn/ui, Tailwind, TanStack Query/Table, and React Flow. Commit `1157784` implemented the Operations Panel directly inside `dve/`:

* **Single Flask-served page:** `dve/src/dve/templates/index.html` (692 lines) renders stage views (`boot`, `login`, `sources`, `select`, `files`, `units`, `run`, `model`, `graph`) plus `#modal`.
* **Zero-build vanilla JS:** `static/app.js` (2,537 lines, ES5-compatible IIFE) and `static/graph.js` (2,766 lines, `window.DsmHierarchyGraph`), loaded after vendored **AntV G6 5.1.1** (`static/vendor/g6.min.js`, ~1.38 MB, MIT `g6.LICENSE`).
* **Self-hosted assets:** `static/app.css` (3,541 lines), Barlow 400 and Orbitron 600 fonts (OFL), Lucide icon subset v1.43.0 (ISC), and pre-blurred background images (avoiding `backdrop-filter` for Firefox 90 compatibility).
* **As-built gaps identified during code and SRS audit:**
  * `graph.js` currently renders only the CSMS software hierarchy tree and hardware switch/cabinet diagram from raw Model Data JSON—it does not yet render `Topic`, `Message`, `Role`, `Broker`, or `CommunicationService` nodes, selectable relationships with Inspector attributes (`DVE.20`), or **relationship search** (`DVE.19`).
  * `index.html:688` omits a G6 version comment, `#run-progress` (`index.html:373-380`) lacks `aria-label` (required by `axe-core` rule `aria-progressbar-name`), and `fonts.css` / SVGs / `bg.jpeg` / `g6.min.js` contain comment, XML-namespace and EXIF URLs that a naive grep for `http` would flag.
  * The UI currently tracks only the single `task_id` it started locally, missing live status display of CLI/Jenkins-submitted ongoing operations (`DVE.27`).
  * Working Model editing (`DVE.17`) must reconcile canvas gestures with `UXD §4`'s requirement that edits be explicit, validated, and undoable (`[Undo]`), without writing layout coordinates onto immutable baseline graph nodes (`DVE.29`).

## Decision Drivers

* Every asset must be served offline from `dve`'s wheel with zero Node.js/npm build toolchain to vendor offline (QA-10).
* The UI must run cleanly on workstation browsers down to Firefox 90 (`Firefox 91 ESR` reference test target) and meet WCAG 2.1 AA (QA-12, UXD §6–7).
* Graph views must scale past 1,000 elements via server-side scoping while supporting entity **and relationship** search, multi-criteria filtering (DVE.19), attribute inspection (DVE.20), explicit undoable Working Model edits (DVE.17), and finding/propagation overlays (DVE.22, 57).

## Considered Options

* Frontend architecture: Flask-served vanilla-JS page with modular `static/views/*.js` files and vendored libraries, zero build step (as built, extended)
* Frontend architecture: React + Vite SPA bundled into static assets
* Frontend architecture: Next.js 14 SSR/App Router (earlier SDP §5 / UXD)
* Graph visualization: Vendored AntV G6 5.1.1 behind a single `window.Dsm` graph adapter (as built, extended)
* Graph visualization: React Flow / Cytoscape.js / Sigma.js
* Browser & accessibility baseline: Firefox 90+ floor (`Firefox 91 ESR` test reference) and WCAG 2.1 AA

## Decision Outcome

Chosen options: **the Flask-served zero-build vanilla-JS page modularized per view**, **vendored AntV G6 5.1.1 with server-side view scoping**, and **the Firefox 90+ / WCAG 2.1 AA baseline**.

### 1. Frontend architecture and live operations strip

* **Same-origin asset serving:** `dve` serves `/` and `/static/*` from package data, keeping session cookies strictly first-party (ADR-0019).
* **Incremental modularization (zero build step):**
  * `static/core.js` centralizes CSRF-aware `fetch` (`X-CSRFToken`), background polling (`X-Background-Poll: 1` so 1 Hz polls do not reset the 30-min idle session timeout, ADR-0019 §1), `localStorage` (`dsm:state:<username>`, never storing secrets/tokens), focus-trapped modals, and `ErrorRecord` banners.
  * New R3–R7 stage screens live in `static/views/<stage>.js` (`working-model.js`, `verification.js`, `scenarios.js`, `field-records.js`, `analysis.js`, `evaluations.js`, `reports.js`), registered on `window.Dsm` via ordered `<script>` tags with explicit version comments in `index.html`.
* **Ongoing operations strip (`DVE.27`, `TC-DVE-07`):** a persistent top-bar operations drawer polls `GET /api/v1/operations?state=queued,running` (scoped to the active project/platform or all authorized projects) so interactive users see live status and progress of both UI-initiated and CLI/Jenkins-initiated operations.
* **Charts (`DVE.58, 70`):** vendor Apache ECharts (`echarts.min.js` + `echarts.LICENSE`, Apache-2.0) under `static/vendor/` when R6 summary KPI indicators and resource/messaging distributions are added.

### 2. Graph view, search/filtering, and Working Model editor (`DVE.17, 19–20, 22, 57`)

* **Single G6 boundary:** only `graph.js` (and `static/views/graph-*.js`) calls AntV G6 APIs, exposing a clean façade on `window.Dsm`.
* **Complete 12-label & relationship rendering (`DVE.20`):**
  * Extends `graph.js` beyond Model Data files to render SMM model instances across four switchable lens modes: *Hierarchy & Roles* (`System`..`CSU`, `Role`), *Messaging & Middleware* (`Application`, `Library`, `Topic`, `Message`, `Broker`, `CommunicationService` with `PUBLISHES_TO`, `SUBSCRIBES_TO`, `ROUTES`, `USES_SERVICE`, `TRANSFERS`, `CARRIES`, `SENDS`, `RECEIVES`), *Hardware & Network* (`Node`, `NetworkDevice`, `RUNS_ON`, `CONNECTS_TO`), and *Derived Dependencies* (`DEPENDS_ON` by ADR-0010 layer projection).
  * Clicking **either a node or a relationship** opens the right-hand Inspector drawer displaying all acquired/derived attributes, `weight`, `origin`, `placeholder_reasons` (replacing `"NOT_FOUND"`, ADR-0009), and bound AED metrics/events (`DVE.16, 20`).
* **Entity & relationship search and 5-dimension filtering (`DVE.19`, `TC-DVE-05`):**
  * Server-side `GET /api/v1/models/<instance_id>/elements?q=…&kind=node|relationship|all&type=…&software_unit=…` searches **both entities and relationships** (`name`, `type`, `from->to`, interface/topic names), where `type=CSU` matches `Application ∪ Library` (ADR-0010 §1).
  * Filtering by `project`, `platform`, and `system_version` operates in the top-bar model selector (`GET /api/v1/models?project=…&platform=…&system_version=…`), scoping or switching the active model instance while preserving the search query across versions.
  * Views cap rendered canvas elements at `1,000` (UXD §6), collapsing larger neighborhoods into expandable cluster badges and switching from rich HTML cards to lightweight canvas shapes above threshold.
* **Explicit, undoable Working Model editing (`DVE.17`, reconciling `UXD §4`):**
  * Baselines and candidate instances open strictly read-only (`DVE.29`).
  * On a `working` instance, **accidental drags never mutate model semantics**: node dragging updates only visual coordinates saved in SQLite `smm_instance_layout(instance_id, view_kind, positions_json)` (`ADR-0007`, leaving graph store data untouched).
  * Structural edits—adding/removing nodes, adding/removing relationships (via Inspector form or confirmed `create-edge` dialog), and editing attributes—submit explicit commands with `expected_revision` to SMM (`ADR-0006 §2`, `ADR-0011 §3`). A toolbar `[Undo]` button invokes `POST /api/v1/models/<id>/undo` (`ADR-0011`'s `undo_edit`), and HTTP `409 Conflict` prompts a clean view refresh.
* **Analytical overlays (`DVE.22, 57`):** selecting a finding highlights its `cause ↔ effect` chain (`dve_finding_link`) on the canvas; selecting a `simulation_analysis` result animates/highlights the `DEPENDS_ON` + `RUNS_ON` propagation path and strength bands (`ADR-0017`).

### 3. Browser and accessibility baseline (`QA-12`, `UXD §6–7`)

* **Browser floor:** Firefox 90+ (`Firefox 91 ESR` and current Firefox ESR are the automated test targets, ADR-0021). JS and CSS stay within Firefox 90 native support (`Object.hasOwn` polyfilled in `graph.js`; no CSS `:has()`, nesting, container queries, or `backdrop-filter`).
* **WCAG 2.1 AA compliance:**
  * Add `aria-label` on `#run-progress` (`index.html:373`) so `axe-core` passes cleanly;
  * Maintain keyboard operability, visible focus rings, modal focus trap/restore, `aria-live` regions, and a synchronized **keyboard-navigable entity/relationship table** beside every G6 canvas so screen-reader and keyboard-only users can search, select and inspect every node and relationship without using a pointer.

### Consequences

* Good, because the UI ships inside `dve`'s wheel with zero Node.js build dependencies, preserves ~6,000 lines of working UI/graph code, and reconciles `DVE.17` editing + `[Undo]` cleanly with `UXD §4`.
* Good, because `smm_instance_layout` keeps visual coordinates out of immutable graph elements (`DVE.29`).
* Bad, because custom tables, forms and accessible dialogs are maintained in vanilla JS without static TypeScript checking.

### Confirmation

* Browser gates (ADR-0021) verify every stage view against `dsm` + fakes in `Firefox 91 ESR` and current Firefox ESR, running vendored `axe-core` with zero WCAG 2.1 A/AA violations.
* Graph API & UI tests (`TC-DVE-05`) verify entity **and relationship** search, all five `DVE.19` filter dimensions, `1,000`-element view capping, Working Model edit + `[Undo]`, and live visibility of CLI-started operations in the top-bar strip (`TC-DVE-07`).
* Offline-asset CI check parses HTML (`src`, `href`), CSS (`url(...)` after stripping comments), and JS network calls to ensure zero external HTTP(S) requests (ignoring code comments, XML `xmlns` URIs, image EXIF metadata, and inert strings).

## Pros and Cons of the Options

### Flask-served modular vanilla JS with zero build step (chosen)

* Good, because it runs offline out of the box, needs zero npm/Node.js vendoring, and builds directly on the existing 6,000-line UI.
* Bad, because UI state and ARIA discipline rely on conventions and automated `axe-core`/browser tests rather than React components.

### React + Vite SPA

* Good, because component composition and TypeScript typing scale cleanly for complex forms.
* Bad, because vendoring hundreds of npm packages offline and rewriting the working UI delays R3 delivery.

### Next.js 14 SSR (earlier SDP §5 / UXD)

* Good, because routing and data fetching are integrated.
* Bad, because running a Node.js server in production violates ADR-0004's single-Python-process-tree constraint.

### Vendored AntV G6 5.1.1 behind one adapter (chosen)

* Good, because it is already integrated as a single file with custom tree/cabinet layouts, HTML cards and canvas zoom/pan.
* Bad, because bundle size (~1.38 MB) is sizeable and upstream docs are partly Chinese-first.

### React Flow / Cytoscape.js / Sigma.js

* Good, because English documentation is broader.
* Bad, because React Flow requires React, Sigma.js lacks rich card/edge editing, and Cytoscape.js would discard 2,766 lines of working `graph.js` integration.

## More Information

* Code: `dve/src/dve/templates/index.html`, `dve/src/dve/static/app.js`, `dve/src/dve/static/graph.js`, `dve/src/dve/static/app.css`, `dve/src/dve/static/fonts/fonts.css`, `dve/src/dve/static/vendor/g6.min.js`
* Vendored: AntV G6 5.1.1 (MIT); Barlow 400 & Orbitron 600 (OFL); Lucide subset v1.43.0 (ISC); ECharts 5.x (Apache-2.0, R6)
* [UXD §1–7](../UXD.md)
* Related: ADR-0002, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0009, ADR-0010, ADR-0011, ADR-0017, ADR-0019, ADR-0020, ADR-0021
* Revisit if ADR-0020 benchmarks show 1,000-element canvas views dropping below UXD §6's frame-rate target on workstation GPUs (evaluating G6's WebGL renderer).
