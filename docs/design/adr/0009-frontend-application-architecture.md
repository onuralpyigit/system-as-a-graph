# ADR-0009: Frontend application architecture

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, UX |
| Kind | Reconcile |
| Traces | DVE.1, 4–27; QA-07, QA-12; UXD §1–7 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

The Operations Panel is built today as one Flask template (`templates/index.html`) and a single 1,950-line vanilla JavaScript file (`static/app.js`). It covers login, data-source connection, selection and Model Data production. Starting in R3, the UI needs much more:

- an interactive graph editor (DVE.17, 19–20);
- virtualized findings tables (DVE.21–23);
- charts (DVE.58, 70);
- many more screens.

The UXD and SDP §5 assume Next.js 14 with React 18, Refine, shadcn/ui, Tailwind, TanStack Query/Table, React Flow and Recharts/ECharts. UXD §6 sets route-level code splitting and performance budgets, and UXD §7 sets accessibility rules.

## Decision Drivers

* The UI scope from R3 onwards: a graph editor, data tables, charts, about 15 screens (UXD §4).
* UXD §6 budgets (route chunking, table virtualization, 60 fps canvas) and UXD §7 accessibility.
* On-premises deployment: fewer runtime services is better (QA-10).
* The component ecosystem needed (graph canvas, tables, charts) is React-centred.

## Considered Options

* Keep server-rendered templates with vanilla JavaScript (as built)
* Next.js with Refine and shadcn/ui (SDP §5, UXD)
* A React single-page application built with Vite, served as static files by the backend, using the UXD component libraries

## Decision Outcome

Chosen option: "A React single-page application built with Vite". It keeps every UXD library choice (shadcn/ui on Radix, Tailwind, TanStack Query/Table, React Flow, Recharts/ECharts), so UXD remains valid. It is also built to static assets, so production runs no Node.js server. An internal tool behind a login gains nothing from Next.js server-side rendering.

* **Location:** `web/` (ADR-0004), TypeScript, React 18, React Router with lazy routes. This meets the UXD §6 "one route chunk per screen group" rule.
* **Data layer:** TanStack Query against the REST API (ADR-0005). The typed API client is generated from the committed OpenAPI document.
* **Admin/CRUD scaffolding:** Refine is optional. It is adopted only if it shortens the CRUD screens without constraining the custom graph and findings views.
* **Serving:** the API container serves the built `web/dist` at `/`, so it is the same origin as the API. Cookies stay first-party (ADR-0030).
* **Migration:** the existing four views (login, sources, selection, production) are rebuilt in R3. `app.js` is removed when parity is reached.
* UXD references to Next.js-specific features are updated:
  * `next/font` → self-hosted `@fontsource` files;
  * route segments → lazy routes.

### Consequences

* Good, because the UXD design and library choices carry over unchanged, apart from the framework shell.
* Good, because there is one fewer production runtime than with Next.js, and static assets are cacheable.
* Bad, because the existing vanilla UI is rewritten, and a Node toolchain is needed in CI and development (not in production).
* Bad, because there is no SSR. The first paint depends on the JS bundle, which UXD §6 budgets.

### Confirmation

* A CI build produces `web/dist`. A bundle-size check enforces the per-route budget.
* Playwright smoke tests (ADR-0041) run against the API container serving the bundle.
* Automated accessibility checks (axe) run on each route (ADR-0042).

## Pros and Cons of the Options

### Templates + vanilla JavaScript (as built)

* Good, because it needs no build toolchain and already works.
* Bad, because a graph editor, virtualized tables and charts without a component framework would mean re-implementing what the libraries provide. A single 1,950-line file is already hard to maintain.

### Next.js + Refine (SDP, UXD)

* Good, because it matches the documents exactly, and it has file-based routing.
* Bad, because it needs a Node.js server in production for its default mode. A static export gives up most Next.js features, which leaves a Vite SPA with extra constraints.

### React SPA with Vite

* Good, because it keeps the UXD libraries, needs no server runtime, and has a simple build.
* Bad, because routing and layout conventions must be set by the team.

## More Information

* [UXD](../UXD.md), [SDP §5](../../planning/SDP.md)
* Code: `dve/src/dve/templates/index.html`, `dve/src/dve/static/app.js`
* Related: ADR-0005, ADR-0025, ADR-0030, ADR-0042
