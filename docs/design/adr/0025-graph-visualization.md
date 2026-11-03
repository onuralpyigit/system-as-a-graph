# ADR-0025: Graph visualization and large-model rendering

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, UX |
| Kind | Decide |
| Traces | DVE.17, 19–20, 22, 57; QA-07, QA-12; UXD §4–7 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

DVE.19–20 require search, filter, zoom, pan, selection and attribute display on the node-relationship structure. DVE.17 requires editing a working model on it. UXD §6 sets 60 fps pan and zoom, with full detail below 1,000 nodes and simplified rendering above. UXD and SDP §5 name React Flow.

Nothing is implemented: the current UI has no graph view. ADR-0009 selects a React SPA.

## Decision Drivers

* Editing interactions (DVE.17) are as important as viewing.
* Models may exceed 1,000 elements; the view must stay responsive (QA-07).
* Custom node rendering is needed: severity badges, status colours (UXD §2.2), and keyboard access (UXD §7).
* The library must fit React (ADR-0009).

## Considered Options

* React Flow, with server-side scoping and an automatic layout library
* Cytoscape.js (canvas renderer, built-in layouts)
* Sigma.js (WebGL renderer for very large graphs)

## Decision Outcome

Chosen option: "React Flow, with server-side scoping and an automatic layout library". It has first-class editing (connect, drag, delete, selection), its nodes are React components (custom badges, focus handling, accessibility), and it is already the UXD design basis. The scale limit of DOM-rendered nodes is handled by never sending the whole large graph to the browser.

* **Scoping:** the API serves *views*, not whole models:
  * an overview aggregated by processing unit or CSC, with expandable groups;
  * a neighbourhood of N hops around a selected entity;
  * a filtered subset from search (DVE.19).

  The server caps a view at the UXD §6 detail threshold of 1,000 elements. Larger results are returned aggregated, with counts.
* **Layout:** ELK (`elkjs`) runs in a Web Worker, so the main thread stays free. Node positions of working models are saved with the instance, so edits don't reshuffle the layout.
* **Editing:** canvas edits call SMM's working-model commands (ADR-0016). They are applied optimistically and reconciled with the server response (UXD §6).
* **Overlays:** findings (DVE.22 cause/effect chains) and propagation paths (DVE.57) are drawn as highlighted edge and node styles on the current view.
* **Fallback:** if the ADR-0036 performance budget measurement shows aggregated overviews are insufficient, a read-only Sigma.js overview may be added. That needs a new ADR.

### Consequences

* Good, because editing, custom node UI and keyboard access come with the library, and UXD stays valid.
* Good, because server-side scoping also keeps payloads and memory small.
* Bad, because overview aggregation and neighbourhood queries are extra server work in SMM.
* Bad, because a user cannot see every node of a very large model at once; they work through aggregation instead.

### Confirmation

* A Playwright performance test pans and zooms a 1,000-element view and checks the frame rate against UXD §6.
* An API test asserts that no view response exceeds the element cap.

## Pros and Cons of the Options

### React Flow + scoping

* Good, because it has the best editing experience, React-native nodes, and matches UXD.
* Bad, because DOM nodes limit the size of a single view.

### Cytoscape.js

* Good, because it renders on canvas, handles about 10k elements, and has many layouts and algorithms.
* Bad, because editing needs extensions, custom node content is limited, and canvas accessibility is weaker.

### Sigma.js

* Good, because WebGL handles very large graphs.
* Bad, because it has minimal editing support and the most custom work for interaction.

## More Information

* [UXD §4–7](../UXD.md)
* Related: ADR-0009, ADR-0014, ADR-0016, ADR-0036, ADR-0042
