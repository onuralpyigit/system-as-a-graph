# ADR-0015: Operations Panel: frontend, graph view and browser support

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, UX |
| Kind | Ratify |
| Traces | DVE.1, 4–27, 57; QA-07, QA-10, QA-12; UXD §1–7 |
| Resolves | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The UXD and SDP §5 assumed the following:

* Next.js 14 with React 18;
* Refine, shadcn/ui, Tailwind and TanStack Query/Table;
* React Flow for the graph and Recharts/ECharts for charts;
* a Firefox 90+ floor (UXD §6) and WCAG AA (UXD §7).

Commit `1157784` built the Operations Panel differently:

* **One page.** `dve/src/dve/templates/index.html` (about 690 lines) holds the stage views: boot, login, sources, select, files, units, run, model and graph, plus a modal.
* **Vanilla JavaScript, no build step.** `static/app.js` (about 2,540 lines, one ES5-style IIFE) and `static/graph.js` (about 2,770 lines, exposed as `window.DsmHierarchyGraph`). Scripts load in the order G6, `graph.js`, `app.js`.
* **Graph:** AntV G6 5.1.1, vendored as `static/vendor/g6.min.js` (about 1.4 MB, MIT, with `g6.LICENSE`). It draws two views:
  * Software view: a tree CSMS › CSS › CSCI › CSC › CSU from `system_hierarchy`, with a relation card per CSU. HTML nodes (`type: "html"`) are placed by a custom `DsmTreeLayout`, registered as `dsm-tree`.
  * Hardware view: networks as switches with bus lines, and nodes in cabinets, from `networks`, `nodes` and `connects_to`.
  * Interaction: drag-canvas, zoom-canvas and scroll-canvas, collapse and expand, hover highlight, tooltips, and a search panel that finds, opens, centres and highlights an entity (DVE.19).
  * The view reads one whole Model Data file (`GET …/mdg-files/<run_id>/model`) and treats the `"NOT_FOUND"` sentinel as missing.
* **Assets:** `app.css` holds the styles. Barlow 400 and Orbitron 600 (OFL) and a Lucide icon subset v1.43.0 (ISC) are self-hosted; nothing loads from a CDN.
* **State:** UI position is kept per user in `localStorage`. Requests go through one helper with CSRF token and retry (ADR-0005).
* **Firefox 90 floor, already met:**
  * an `Object.hasOwn` polyfill for G6;
  * no `backdrop-filter` (pre-blurred images instead);
  * static font weights;
  * scrollbar styling within Firefox 90.
* **ARIA in use:**
  * `role="alert"` and `role="status"` messages;
  * `aria-live="polite"` on the run console;
  * `role="progressbar"`, a `role="dialog"` modal and a `role="listbox"` for search results;
  * labels on icon-only buttons.

From R3 the panel needs these:

* the working-model editor (DVE.17);
* findings tables with sorting and filtering (DVE.21–23);
* overlays for cause and effect and for propagation (DVE.22, 57);
* charts (DVE.58, 70);
* screens for synthetic data, field records, simulations, reports and evaluations (DVE.10–16, 25–27).

The target host is offline (ADR-0004), so `dve` must serve every asset itself.

## Decision Drivers

* The page must work offline and in the oldest workstation browsers expected, Firefox 90 (QA-10, QA-12).
* The existing page covers DVE.1–9 and 19–20 and is tested through the API.
* A Node.js toolchain would be a second ecosystem to vendor offline for development and CI.
* Models may exceed 1,000 elements (UXD §6), and the canvas is not accessible by itself.

## Considered Options

* Frontend: Flask-served page in vanilla JS with vendored libraries, no build step (as built) / React SPA with Vite / Next.js + Refine + shadcn/ui (SDP, UXD)
* Graph library: AntV G6 5 (as built) / React Flow / Cytoscape.js / Sigma.js
* Browser baseline: Firefox 90 and WCAG 2.1 AA (as built, UXD) / evergreen only / a transpiled build

## Decision Outcome

Chosen options: **the Flask-served vanilla-JS page (as built)**, **AntV G6 5 with server-side view scoping (as built)**, and **a Firefox 90 floor with WCAG 2.1 AA (as built)**. They work offline with no build step and no Node.js, and they already deliver the first screens and the graph view. The rules below keep the page maintainable as screens are added.

### 1. Frontend rules

* **Serving:** `dve` serves the page at `/` and every asset from `dve/src/dve/static/` as package data, at the API's origin. Cookies stay first-party (ADR-0019).
* **No build step:** the browser runs the files as committed. There is no transpiler, bundler or package manager.
* **Vendored libraries:** `static/vendor/<name>.min.js` with `<name>.LICENSE` beside it, and the version in an `index.html` comment. A new library needs a line in *More Information*.
* **Module split:**
  * New screens go in `static/views/<stage>.js`, one per stage, each registering on a single `window.Dsm` namespace.
  * They load after `static/core.js`, which holds the request helper with CSRF retry, polling, `localStorage` access and common error display.
  * `app.js` is split along these lines as screens are touched, not in one rewrite. Plain `<script>` tags keep the load order explicit.
* **Data:** the page reads only JSON from `/api/...`. Large lists are paged and sorted on the server (DVE.23), so no virtualized-table library is needed.
* **Charts:** a vendored ECharts build (Apache 2.0), when charts are needed (DVE.58, 70).
* **State:** only UI position and convenience values go in `localStorage`, keyed per user. Passwords and tokens never do.
* **UXD:** its layouts, flows, budgets (§6) and accessibility rules (§7) apply. Its library names are superseded by this ADR.

### 2. Graph view

* **Pinning:** G6 stays vendored at a fixed version. An upgrade replaces `g6.min.js` and `g6.LICENSE` and passes the browser tests on Firefox 90.
* **One adapter:** only `graph.js` and future `static/views/graph-*.js` touch the G6 API. Other screens use the `window.Dsm` graph object, so a later library change stays local.
* **To build, once SMM exists (ADR-0010, ADR-0011):**
  * **Scoping:** the API serves *views* of a model instance. These are an overview aggregated by processing unit or CSC, an N-hop neighbourhood, and a search and filter subset (DVE.19: type, project, platform, system version, software unit).
    * A view is capped at the UXD §6 threshold of 1,000 elements. Larger results come back aggregated with counts.
    * Above the threshold, nodes draw as simple shapes instead of HTML cards.
  * **Editing (DVE.17):** canvas edits call SMM's working-model commands with `expected_revision` (ADR-0006, ADR-0011). They apply optimistically, and a `409` reloads the view. Node positions are saved with the instance. G6's `click-select`, `drag-element` and `create-edge` behaviours are the starting point.
  * **Overlays:** findings (DVE.22) and propagation paths (DVE.57) drawn as G6 element states.
  * **Placeholders:** when ADR-0009 retires `"NOT_FOUND"`, `graph.js` reads the `placeholders` list instead.
  * **Fallback:** a WebGL renderer for a read-only overview, if ADR-0020's measurements require it. That needs a new ADR.

### 3. Browser and accessibility baseline

* **Supported:** Firefox 90 or later; Firefox 91 ESR is the reference. The current ESR is also tested. Chromium of the same era or later is expected to work but is not tested.
* **Language and CSS:** only what Firefox 90 supports. So classes, `const`/`let`, arrow functions and `async`/`await` are allowed. Anything newer needs a feature check or a polyfill in the file that needs it, as `graph.js` does for `Object.hasOwn`. In CSS, `:has()`, container queries, `backdrop-filter` and nesting are not used.
* **WCAG 2.1 AA:**
  * contrast as in UXD §2;
  * every control keyboard-operable with visible focus;
  * status changes announced through live regions;
  * dialogs trap and restore focus.
  * Every graph view has a keyboard-operable list or search that selects the same elements as the canvas.
* **States:** every data view shows the UXD §7 empty, loading and error states. Errors show the record's source, reason and time (ADR-0009).

### Consequences

* Good, because the page installs with the Python wheel, runs offline, and keeps its current screens and tests.
* Good, because the graph view already meets DVE.19–20 for Model Data files, and server-side scoping keeps payloads small as models grow.
* Bad, because there is no component library, so dialogs, menus and tables are written in-house and must meet UXD §7 by hand. There is no type checking either.
* Bad, because G6's documentation and community are mostly in Chinese, and its bundle is large.
* Bad, because the parallel keyboard list is required, since canvas content is not reachable by assistive technology.

### Confirmation

* Browser tests (ADR-0021) load every stage view in Firefox 91 ESR and the current ESR, against `dsm` with fake adapters.
* A performance test pans and zooms a 1,000-element view against UXD §6. An API test asserts that no view exceeds the cap.
* An axe-core check, vendored for tests only, runs on each stage view and fails on WCAG A or AA violations.
* A keyboard-only test walks login, sources, selection, a production run and graph search, and checks that list selection highlights the canvas element.
* A CI check fails if `index.html` or any static file references an external URL.

## Pros and Cons of the Options

* Vanilla page (as built): Good, because it needs no toolchain, works offline and exists. Bad, because large screens need in-house components and discipline.
* React SPA with Vite: Good, because it keeps the UXD libraries. Bad, because it needs Node.js and a vendored npm cache offline, and a rewrite.
* Next.js: Bad, because it needs a Node.js server in production.
* G6 (as built): Good, because it is one vendored file, with a canvas renderer, HTML nodes, custom layouts and editing behaviours. Bad, because of its size and its mostly non-English community.
* React Flow: Bad, because it requires React and a build step.
* Cytoscape.js: Bad, because it would replace a working integration, and custom HTML nodes need extensions.
* Sigma.js: Bad, because it has minimal editing support.
* Evergreen-only: Bad, because users on old ESR builds would be locked out. A transpiled build would need the toolchain avoided above.

## More Information

* Code: `dve/src/dve/templates/index.html`, `dve/src/dve/static/app.js`, `dve/src/dve/static/graph.js`, `dve/src/dve/static/app.css`, `dve/src/dve/static/fonts/fonts.css`, `dve/src/dve/static/vendor/g6.min.js`
* Vendored: AntV G6 5.1.1 (MIT); Barlow 400 and Orbitron 600 (OFL); Lucide icon subset v1.43.0 (ISC)
* [UXD](../UXD.md), [SDP §5](../../planning/SDP.md)
* Related: ADR-0005, ADR-0006, ADR-0009, ADR-0010, ADR-0011, ADR-0019, ADR-0020, ADR-0021
