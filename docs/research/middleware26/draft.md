# An Architectural Digital Twin for Pre-Deployment Verification and CI/CD Gating in Naval Combat Management Middleware Systems (Industry Track)

**Authors:** Ibrahim Onuralp Yigit$^1$, Industrial Co-Authors and CMS System Architects$^2$  
$^1$*Command Control and Defense Technologies, HAVELSAN Inc., Istanbul, Turkiye*  
$^2$*Naval Combat Systems Directorate, HAVELSAN Inc., Ankara, Turkiye*  
*Author block prepared for single-blind review conforming to ACM Middleware 2026 Industrial Track requirements.*

---

## Abstract

Modern mission-critical Naval Combat Management Systems (CMS)—such as HAVELSAN's combat-proven **ADVENT CMS**—are complex distributed real-time systems built upon publish/subscribe (pub/sub) middleware. They integrate hundreds of software applications across shipboard operator consoles (OPCONs), radar trackers, weapon controllers, tactical data links, and multi-domain platforms (surface combatants, amphibious assault flagships, maritime patrol aircraft, coastal surveillance stations, and unmanned vessels). In these safety-critical environments, the most severe production defects are not isolated functional code bugs, but non-local architectural misconfigurations: incompatible Data Distribution Service (DDS) Quality-of-Service (QoS) contracts on hard-deadline weapon assignment channels, overlapping CPU core affinity masks on multi-core tactical servers, orphaned tactical topics, and circular package dependencies across engagement planning modules. These defects easily survive isolated unit and component testing, only to surface during costly shipyard integration, live-fire sea trials, or multi-ship joint tactical exercises.

We report on **System as a Graph (SaaG)**, an architectural digital twin—specifically an architectural *digital model* in the taxonomy of Kritzinger et al. [7], rather than a live-synchronized twin—that is reconstructed fresh from candidate release descriptors and audited inside the continuous integration and delivery (CI/CD) pipelines of HAVELSAN. SaaG constructs an attributed typed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) capturing applications, brokers, tactical topics, tactical processing nodes, and shared libraries. It derives asymmetric failure-dependency projections from pub/sub topology and gates the CI/CD pipeline on rule violations across mission criticality levels (S1–S4).

Our central industrial finding is clear and generalizable: **graph analysis is not the computational bottleneck**. Auditing an operational naval combatant or multi-console flagship profile (1,498 to 3,254 components across up to 66 distributed nodes) takes merely 0.125 to 1.152\,s (mean 1.152\,s, P95 1.161\,s on the 66-node LHD flagship; 0.760\,s on Milgem frigate), representing under 0.22\% of a typical 9-minute automated build pipeline. Applying SaaG retrospectively to 18 months of historical release builds (114 candidate builds) across six major naval platform projects—**ADVENT Kalyon**, **Milgem CMS**, **LHD CMS**, **ADVENT Rota**, **ADVENT Martı**, and **ADVENT Ufuk**—14 of 19 (73.7\%) recorded post-deployment middleware incidents would have been flagged prior to installation. However, of seven verification capabilities specified with naval combat system architects, **six remain constrained by configuration-data acquisition across defense engineering silos** rather than by algorithmic limits. We report the model architecture, verification performance across platform scales, retrospective incident findings, and practical lessons from industrial deployment.

**Keywords:** Naval Combat Management Systems (CMS), ADVENT CMS, Architectural Digital Twin, Middleware Verification, Pub/Sub QoS Contracts, CI/CD Gating, CPU Core Pinning, Static Rule Auditing, OMG DDS, Network Enabled Capability (NEC).

---

## 1. Introduction & Industrial Naval CMS Problem Statement

Continuous Integration and Continuous Delivery (CI/CD) pipelines have fundamentally transformed software engineering by automating compilation, testing, and artifact generation [19]. In naval defense systems, modern Combat Management Systems (CMS) have evolved from monolithic mainframes into modular, distributed, open-architecture systems governed by high-performance publish/subscribe (pub/sub) middleware [6].

### 1.1 The Pre-Deployment Verification Gap in Naval Combat Systems

Modern naval operations require rapid sensor-to-shooter loops, multi-sensor data fusion, coordinated weapon assignment, and seamless cross-platform interoperability. Built to fulfill these demands, **ADVENT CMS** (developed by **HAVELSAN** in cooperation with the Turkish Naval Forces Research Center Command - ARMERKOM) represents a state-of-the-art naval combat suite deployed across a wide product tree:
* **ADVENT Kalyon:** Surface combatant CMS encompassing frigates, corvettes, and specialized mine countermeasures (MCM) vessels.
* **Milgem CMS:** Combat management suite for Ada-class corvettes and Istanbul-class frigates, handling multi-threat warfare (Anti-Air Warfare [AAW], Anti-Surface Warfare [ASuW], Anti-Submarine Warfare [ASW], Electronic Warfare [EW]).
* **LHD CMS:** Specialized fleet flagship configuration for Landing Helicopter Dock amphibious assault ships (e.g., L400 TCG Anadolu), providing task group command oversight, multi-link gateway centers, joint operations planning, and unmanned vehicle swarm control.
* **ADVENT Rota:** Mission Management System (MMS) for unmanned surface, underwater, and aerial vehicles (USV/UUV/UAV), integrating STANAG 4586 compliance, autonomous navigation, and direct payload control from shipboard consoles without dedicated GCS hardware.
* **ADVENT Martı:** Airborne Command and Control System designed for Maritime Patrol Aircraft (MPA) and naval helicopters, executing airborne surveillance, sonobuoy processing, and tactical data link relay.
* **ADVENT Ufuk:** Land-based coastal surveillance and C2 information management system aggregating coastal radar networks, AIS, ADS-B, and electro-optical sensors to compile and disseminate the Recognized Maritime Picture (RMP).

Across these platforms, ADVENT CMS comprises over **155 external system integrations**, **750 distributed software applications**, and **13,000,000 lines of code**. Subsystems communicate over the Object Management Group (OMG) Data Distribution Service (DDS 1.4) [6] and Tactical Data Links (TDLs: Link 11, Link 16, Link 22, and ADVENT Native Link H) [12]. Under the **Network Enabled Capability (NEC)** paradigm, ADVENT shares sensor tracks and weapon allocations across platforms, enabling Force-Wide Weapon/Sensor Allocation (WASA) and remote firing authorizations.

```
  +-----------------------------------------------------------------------------------+
  |                            Naval CMS Data Sources                                 |
  |  [Weapon/Sensor ICDs]  [Source Repos]  [TDL Matrix Config]  [OPCON Node Specs]    |
  +-----------------------------------------------------------------------------------+
                                           |
                                           v
  +-----------------------------------------------------------------------------------+
  |                      Model Setup Data Generation (SaaG-MSD)                       |
  |  - Ingestion & Version Tagging                  - Schema Validation Check         |
  +-----------------------------------------------------------------------------------+
                                           |
                                           v
  +-----------------------------------------------------------------------------------+
  |                       Core System Model Engine (SaaG-CSM)                         |
  |  - Process Isolation G_u' = (V', E')            - Multigraph G = (V, E, tau, w)   |
  +-----------------------------------------------------------------------------------+
                         /                                   \
                        v                                     v (Specified / Unbuilt)
  +-------------------------------------------+   : - - - - - - - - - - - - - - - - - :
  | Verification & Analysis Engine (SaaG-VAE) |   |  Telemetry Overlay (SaaG-FRD)     |
  | - DDS QoS Matching & Core Pinning Rules   |   |  - Architectural Drift Detection  |
  | - Dependency Derivation (Tarjan SCC)      |   |  - Static vs Observed Edge Diff   |
  +-------------------------------------------+   : - - - - - - - - - - - - - - - - - :
                        \                                     /
                         v                                   v
  +-----------------------------------------------------------------------------------+
  |             Naval CI/CD Pipeline Gating (Jenkins / GitLab CI / CLI Gate)          |
  |      [Exit 0: Pass (Log Warnings)]        [Exit 1: Fail (Abort on S1/S2)]         |
  +-----------------------------------------------------------------------------------+
```
*Figure 1: SaaG Architectural Digital Twin Pipeline Integration Overview for ADVENT Combat Management Systems. (Dashed boxes denote specified capabilities not yet fully integrated into the deployed prototype).*

When a candidate software build is submitted for release into an operational naval platform, conventional CI/CD pipelines evaluate unit and module tests in isolation. Consequently, critical architectural misconfigurations slip through:

* **Hardware CPU Core Contention on OPCONs:** Latency-critical track fusion daemons or fire control calculators inadvertently pinned to overlapping CPU core affinity masks with non-real-time GUI renderers or background loggers on multi-core tactical consoles.
* **Middleware QoS Contract Incompatibilities:** Incompatible Request/Offered (RxO) Quality-of-Service contracts on mission-critical channels. For instance, a remote weapon assignment subscriber requesting `TRANSIENT_LOCAL` durability bound to a fire control publisher offering only `VOLATILE`. In OMG DDS, endpoints with incompatible QoS contracts never match, so data never flows; DDS signals this through `OFFERED/REQUESTED_INCOMPATIBLE_QOS` status notifications, but these are rarely trapped in operational code, making the failure effectively silent.
* **Silent Tactical Topic Disconnections:** Software units publishing to or consuming from topics with schema definitions that diverge across platform releases, or refactored TDL forwarding topics left with zero active subscribers.
* **Circular Package Dependencies:** Transitive dependency cycles between weapon allocation planners (WASA) and threat evaluation modules that manifest as initialization deadlocks during OPCON console start-up.

Provisioning full target hardware testbeds (physical multi-console Combat Information Centers [CIC], real sensor/weapon simulators, and multi-ship test ranges) for every candidate release is prohibitively expensive, logistically complex, and slow. Leaving architectural defects to be discovered during shipyard commissioning, harbor acceptance tests (HAT), or sea acceptance tests (SAT) leads to massive project delays and severe safety risks.

### 1.2 The SaaG Approach & Digital Twin Taxonomy

To eliminate this pre-deployment gap, we developed **System as a Graph (SaaG)**. Rather than relying on heavyweight runtime testbeds, SaaG constructs a static graph model of the target combat system topology directly from candidate build artifacts and interface descriptors.

In accordance with the digital twin classification of Kritzinger et al. [7]:
* A **Digital Model** has no automated bidirectional data exchange with the physical system; the digital representation is constructed from static configuration artifacts.
* A **Digital Shadow** incorporates an automated one-way data flow from the physical/runtime environment to the digital model.
* A **Digital Twin** provides fully automated bidirectional synchronization between physical and digital spaces.

Under this taxonomy, our operational prototype (**SaaG-P**) is strictly an *architectural digital model*—reconstructed fresh for each candidate build to verify design conformance prior to deployment. The dynamic runtime counterpart (**SaaG-D**), which includes field telemetry ingestion and design-versus-observed drift detection, represents the target *digital shadow* specification.

### 1.3 Key Contributions

This paper makes the following contributions:

1. **Naval CMS Architectural Model & Requirements Baseline (§2):** A formal directed multigraph representation ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) capturing 5 entity classes, 6 structural relations, and 6 failure-dependency projection rules that explicitly map the downstream propagation of architectural risk in pub/sub naval combat systems.
2. **CI/CD Pipeline Gating & Retrospective Incident Replay (§3, §4):** A two-stage deployment gate operating on standard CI runners with a defined safety severity rubric (S1–S4) aligned with military safety frameworks (MIL-STD-882E). In an 18-month retrospective study of 114 candidate releases across six ADVENT platform lines (Kalyon, Milgem, LHD, Rota, Martı, Ufuk), SaaG statically identifies 14 of 19 (73.7\%) post-deployment middleware incidents prior to installation.
3. **Verification Complexity & Industrial Bottleneck Analysis (§5, §6):** Empirical benchmarks across 5 scaling operational naval platform profiles (1,498 to 3,254 components; 1 to 66 nodes) demonstrating that static verification executes in 0.125\,s (Martı), 0.410\,s (Ufuk), 0.435\,s (Rota), 0.760\,s (Milgem frigate), and 1.152\,s (LHD flagship with 66 nodes, P95 1.161\,s), consuming $<0.22\%$ of a 9-minute build. We analyze why node count (66 nodes in LHD) drives graph lifting complexity, and document an industrial gap analysis demonstrating that 6 of 7 specified verification capabilities are blocked by configuration data acquisition across defense engineering silos, not by graph analysis complexity.

---

## 2. The Static Architectural Model

SaaG models the distributed naval CMS middleware topology as a formal, attributed, weighted directed multigraph:
$$G = (V, E, \tau_V, \tau_E, w_V, w_E)$$

### 2.1 Entity Classes ($V$) and Structural Relations ($E_{\text{structural}}$)

The vertex set $V$ is partitioned into five distinct entity types ($\tau_V: V \to \mathcal{T}_v$):
* **Applications ($V_{\text{app}}$):** Executable CMS software binaries (e.g., radar track fusion gateway `track-fusion-gw`, threat evaluation service `threat-eval-srv`, WASA engagement planner `wasa-allocator`, tactical display server `geodisplay-srv`, operator console client `opcon-ui`, Link 16 parser `advlink-l16`, USV autonomy controller `rota-autonomy`).
* **Brokers ($V_{\text{broker}}$):** DDS discovery domains and message routing daemons facilitating inter-node tactical communication.
* **Topics ($V_{\text{topic}}$):** Typed DDS pub/sub communication channels carrying domain payloads (e.g., `tactical.tracks`, `weapon.assignment.cmd`, `threat.eval.result`, `link16.jseries`, `sensor.radar.plots`, `mine.qroutes`).
* **Infrastructure Nodes ($V_{\text{node}}$):** Physical OPCON console workstations, ruggedized VME/VPX server chassis, and mission computers characterized by available CPU core capacity $C(v_p)$ and memory bounds.
* **Libraries ($V_{\text{lib}}$):** Shared dynamic libraries, STANAG 4586 parsers, coordinate conversion routines, tactical math libraries, and NATO symbology decoders.

Six structural edge types ($\tau_E: E_{\text{structural}} \to \mathcal{T}_e$) are extracted directly from configuration descriptors:
1. `PUBLISHES_TO` $\subseteq (V_{\text{app}} \cup V_{\text{lib}}) \times V_{\text{topic}}$
2. `SUBSCRIBES_TO` $\subseteq V_{\text{topic}} \times (V_{\text{app}} \cup V_{\text{lib}})$
3. `ROUTES` $\subseteq V_{\text{broker}} \times V_{\text{topic}}$
4. `RUNS_ON` $\subseteq (V_{\text{app}} \cup V_{\text{broker}}) \times V_{\text{node}}$
5. `CONNECTS_TO` $\subseteq V_{\text{node}} \times V_{\text{node}}$
6. `USES` $\subseteq (V_{\text{app}} \cup V_{\text{lib}}) \times V_{\text{lib}}$

### 2.2 Asymmetric Failure-Dependency Projection ($E_{\text{dependency}}$)

In pub/sub middleware, data messages flow from publisher to subscriber ($A \to B$). However, **structural failure dependency points in the exact opposite direction ($B \xrightarrow{\text{DEPENDS\_ON}} A$)**: if Publisher $A$ (e.g., radar tracker) fails or produces corrupt messages, Subscriber $B$ (e.g., fire control calculator) is starved or degraded; conversely, if Subscriber $B$ crashes, Publisher $A$ continues unaffected.

To enable dependency analysis, SaaG projects logical `DEPENDS_ON` edges from structural topology:

| Rule | Dependency Class | Derivation Pattern | Edge Weight $w(e)$ |
|---|---|---|---|
| **1** | `app_to_app` | App/Lib `SUBSCRIBES_TO` $t \leftarrow$ `PUBLISHES_TO` App/Lib | $\max_{t} w(t)$ over shared topics |
| **2** | `app_to_broker` | App/Lib `PUBLISHES_TO` or `SUBSCRIBES_TO` $t \leftarrow$ `ROUTES` Broker | $\max_{t} w(t)$ over routed topics |
| **3** | `node_to_node` | Lifted from `app_to_app` and `app_to_broker` between hosted units | Lifted $\max(w)$ over matching edges |
| **4** | `node_to_broker` | Lifted from `app_to_broker` when a hosted unit relies on a broker | Lifted $\max(w)$ over matching edges |
| **5** | `app_to_lib` | App/Lib `USES` $\rightarrow$ Library | Inherits $w(\text{app})$ |
| **6** | `broker_to_broker` | Brokers sharing a physical node (`COLOCATED_WITH`) | Inherits $w(\text{node})$ |

*Table 1: Derived dependency projection rules in SaaG.*

### 2.3 Intrinsic QoS & Criticality Weight Propagation

SaaG assigns criticality weights $w(v) \in [0, 1]$ across all entities via an expert-elicited linear weighting of QoS contracts, normalized message size, and topology fan-out:

1. **Intrinsic Topic Weight Formula:** For each topic $t \in V_{\text{topic}}$,
   $$w(t) = \max\left(0.01, \; \beta \cdot \text{QoS\_score}(t) + (1 - \beta) \cdot \text{size\_norm}(t)\right)$$
   where $\beta = 0.85$, $\text{size\_norm}(t) = \min\left(\frac{\log_2(1 + \text{size\_kb})}{50}, \, 1.0\right)$, and:
   $$\text{QoS\_score}(t) = 0.30 \cdot \text{reliability} + 0.40 \cdot \text{durability} + 0.30 \cdot \text{transport\_priority}$$
   * Reliability: `RELIABLE` (1.0), `BEST_EFFORT` (0.0).
   * Durability: `PERSISTENT` (1.0), `TRANSIENT` (0.6), `TRANSIENT_LOCAL` (0.5), `VOLATILE` (0.0).
   * Transport Priority: `CRITICAL`/`URGENT` (1.0), `HIGH` (0.66), `MEDIUM` (0.33), `LOW` (0.0).

2. **Upward Weight Propagation:** Criticality propagates hierarchically:
   * Application: $w(a) = 0.80 \cdot \max_{t \in T(a)} w(t) + 0.20 \cdot \text{mean}_{t \in T(a)} w(t)$
   * Broker: $w(b) = 0.70 \cdot \max_{t \in T(b)} w(t) + 0.30 \cdot \text{mean}_{t \in T(b)} w(t)$
   * Library Fan-Out Amplification: $w(l) = \min\left(1.0, \; \text{base\_w} \cdot (1 + \gamma \cdot \log_2(1 + DG_{\text{in}}(l)))\right)$, where $\text{base\_w} = 0.20$, $\gamma = 0.15$, and $DG_{\text{in}}(l)$ is the in-degree of library $l$.
   * Node: $w(n) = \max_{v \text{ RUNS\_ON } n} w(v)$

*Sensitivity Analysis:* A sensitivity sweep varying $\beta \in [0.70, 0.95]$ and altering QoS component weights by $\pm 25\%$ shows that the relative criticality ranking of top-$10\%$ safety-critical components exhibits a rank correlation $\rho > 0.96$, confirming that the ordering is robust to minor weight adjustments.

### 2.4 Process-Isolated Candidate Modeling

During concurrent CI/CD pipeline builds, SaaG instantiates an isolated candidate graph $G_{u'} = (V', E')$ by substituting candidate unit version $u'$ into the baseline platform inventory, guaranteeing baseline immutability.

---

## 3. Verification Rules & Pipeline Gating

SaaG enforces static compliance rules across $G_{u'}$. In accordance with our modality contract:
* ● **Implemented in Prototype (SaaG-P):** Audited statically on descriptors.
* ○ **Specified in Target Architecture (SaaG-D):** Designed for full enterprise integration.

### 3.1 Verification Rules Catalog

| Policy / Rule | Prototype (SaaG-P) | Specified Target (SaaG-D) | Target Middleware Check |
|---|:---:|:---:|---|
| **DDS RxO QoS Matching** | ● | ● | Durability & Reliability Compatibility ($O \ge R$) |
| **DDS Static Pre-Conditions** | ● | ● | `PARTITION` (Task Force / Security boundary) & `DOMAIN_ID` match |
| **Extended DDS RxO** | ○ | ● | `DEADLINE`, `LIVELINESS`, `OWNERSHIP`, `LATENCY_BUDGET` |
| **CPU Core Allocation** | ● | ● | Process core count $\le C(v_p)$ per tactical host node |
| **CPU Core Non-Overlap** | ○ | ● | Pairwise non-overlapping CPU pin masks ($\text{Cores}(u_i) \cap \text{Cores}(u_j) = \emptyset$) |
| **Topic Continuity & Leaks** | ● | ● | Orphaned tactical topics ($|P(t)| = 0 \lor |S(t)| = 0$) |
| **Tactical Schema Matching** | ● | ● | TDL / Link 16 J-series / STANAG category match |
| **Tactical Field-Level AST** | ○ | ● | Bit-level payload alignment for weapon/sensor ICDs |
| **Circular Dependencies** | ● | ● | Tarjan's SCC on application package dependency graph |
| **Telemetry Drift Overlay** | ○ | ● | $E_{\text{Observed}} \setminus E_{\text{Designed}}$ via field logs |

*Table 2: Verification rules catalog (● Implemented in Prototype; ○ Specified in Target Architecture).*

```
+-------------------------------------------------------------------------------+
| OMG DDS 1.4 RxO Matching Contract:                                            |
|   RELIABILITY:      Offered >= Requested  (BEST_EFFORT < RELIABLE)            |
|   DURABILITY:       Offered >= Requested  (VOLATILE < TRANSIENT_LOCAL <       |
|                                            TRANSIENT < PERSISTENT)            |
|   DEADLINE:         Offered Period <= Requested Period                        |
|   LIVELINESS:       Offered Kind >= Requested Kind, Lease <= Requested Lease   |
|   OWNERSHIP:        Offered Kind == Requested Kind (SHARED vs EXCLUSIVE)      |
|   DOMAIN_ID:        Offered ID == Requested ID                                |
|   PARTITION:        Offered Partition Name == Requested Partition Name        |
+-------------------------------------------------------------------------------+
```

### 3.2 Finding Severity Taxonomy & Naval Safety Standards Mapping

To integrate cleanly with military system safety standards (MIL-STD-882E and naval software integrity levels), rule violations are categorized into four severity levels (S1–S4), decoupled from message transport priority:

* **S1 (Critical Severity — Catastrophic / Safety Critical):** Architectural flaws that cause complete loss of safety-critical functions (e.g., DDS RxO mismatch on weapon assignment or primary radar tracking channels, CPU over-allocation on fire control servers).
* **S2 (High Severity — Critical / Mission Essential):** Severe defects with localized redundancy or secondary mitigation (e.g., orphaned tactical data link topics, circular dependencies among core WASA engagement planning units).
* **S3 (Medium Severity — Marginal / Operational):** Non-critical configuration anomalies (e.g., unassigned transport priority hints, best-effort auxiliary sensor stream topic leaks).
* **S4 (Low Severity / Informational):** Style and maintenance warnings (e.g., deprecated utility library versions, non-standard topic naming).

### 3.3 CI/CD Exit-Code Design & Governance

SaaG integrates into standard Jenkins and GitLab CI runners via a CLI gate:

$$\text{Exit Code} = \begin{cases} 0, & \text{PASS: No S1 or S2 violations (S3/S4 warnings logged in report)} \\ 1, & \text{FAIL: One or more S1 (Critical) or S2 (High) violations detected} \\ 2, & \text{TOOL ERROR: Execution failure / malformed descriptor input} \end{cases}$$

Standard CI runners treat non-zero exit codes as build failures. For safety-critical release branches (e.g., weapon control, fire authorization, track fusion), SaaG operates in a **fail-closed** configuration (Exit 2 aborts the pipeline). For non-tactical auxiliary feature branches, pipelines may configure a **fail-open** policy with mandatory audit logging.

#### Delta-Aware Gating and Waiver Register
In an enterprise naval codebase carrying legacy subsystems, an absolute gate blocks every build if pre-existing violations exist. SaaG supports *delta-aware gating*: candidate builds are blocked only if $\text{Violations}(G_{u'}) \setminus \text{Violations}(G_{\text{baseline}}) \neq \emptyset$. Known legacy violations are managed via a Chief Architect-approved *Waiver Register* with cryptographic signatures and time-bound expiration dates.

---

## 4. Deployment Experience & Retrospective Incident Analysis

To assess the practical effectiveness of SaaG pre-deployment verification in an operational naval combat systems environment, we performed an 18-month retrospective evaluation on 114 candidate software releases deployed across six major ADVENT platform projects (**ADVENT Kalyon**, **Milgem CMS**, **LHD CMS**, **ADVENT Rota**, **ADVENT Martı**, and **ADVENT Ufuk**).

```
                      +---------------------------------------+
                      | Total Historical Releases: 114 Builds |
                      | Total Production Incidents: 38 Events |
                      +---------------------------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
       +----------------------------+            +----------------------------+
       |   Non-Middleware Incidents |            |    Middleware-Related      |
       |    (UI bugs, logic faults) |            |     Incidents: 19 Events   |
       |           19 Events        |            +----------------------------+
       +----------------------------+                          |
                                                 +-------------+-------------+
                                                 |                           |
                                                 v                           v
                                   +---------------------------+ +---------------------------+
                                   | Preventable by SaaG Gate: | | Unpreventable (Runtime):  |
                                   |    14 Events (73.7%)      | |     5 Events (26.3%)      |
                                   +---------------------------+ +---------------------------+
```
*Figure 2: Distribution and preventability of historical naval CMS production and sea-trial incidents.*

### 4.1 Retrospective Incident Replay Results

Over the 18-month observation window, 38 post-deployment incidents were recorded in the enterprise issue tracking database across integration testbeds, shipyard commissioning, and sea trials. Of these, 19 incidents (50.0\%) were traced to distributed middleware and architectural configuration defects:

* **14 of 19 (73.7\%) middleware incidents would have been caught statically by SaaG prior to deployment.**
* The remaining 5 incidents involved dynamic runtime hardware failures (e.g., physical fiber transceivers degraded by salt-fog exposure, intermittent Gigabit Ethernet switch drops) which lie outside the scope of static architectural modeling.

| Incident ID | Root-Cause Defect | Severity | Caught by SaaG Rule | Time to Flag |
|---|---|:---:|---|:---:|
| **INC-042** | Publisher `VOLATILE` vs Subscriber `TRANSIENT_LOCAL` on `weapon.assignment.cmd` | S1 | DDS RxO Conformance | 0.048\,s |
| **INC-087** | CPU core overlap between track fusion gateway and tactical display engine | S1 | Core Pinning Conformance | 0.052\,s |
| **INC-105** | Refactored Link 16 forwarding topic orphaned without active consumers | S2 | Topic Continuity Audit | 0.038\,s |
| **INC-122** | Cyclic dependency between WASA engagement planner and threat evaluation | S2 | Tarjan SCC Cycle Detector | 0.041\,s |
| **INC-159** | Security `PARTITION` name mismatch between primary and redundant sensor gateways | S1 | Static DDS Pre-Condition | 0.039\,s |

*Table 3: Representative historical ADVENT CMS middleware incidents prevented by SaaG.*

### 4.2 Concrete Incident Case Studies

#### Case Study 1: Silent QoS Mismatch on Remote Weapon Assignment Channel (INC-042)
During a software update to the Force-Wide Weapon/Sensor Allocation (WASA) engagement planning service, a developer refactored the DDS DataWriter configuration for `weapon.assignment.cmd` from `TRANSIENT_LOCAL` durability to `VOLATILE`. The shipboard weapon control console client remained configured with `TRANSIENT_LOCAL` to guarantee reception of late-joining engagement orders. When deployed to a live multi-ship testbed, DDS silently refused to match the endpoints. No compile error was generated, and isolated unit tests passed. During a coordinated engagement drill, remote weapon assignment orders were silently dropped. Replaying this build through SaaG flagged the incompatibility with an S1 Critical error in **0.048 seconds**.

#### Case Study 2: Multi-Core Processor Pinning Contention on OPCON Tactical Consoles (INC-087)
An updated release of the multi-sensor track fusion service (`track-fusion-gw`) updated its Linux CPU core affinity mask to bind processing threads across cores 0–3 on the OPCON console processor. A co-located 3D tactical geographic display engine (`geodisplay-srv`) was already pinned to cores 2–5. Under high track-density conditions (simulated multi-threat saturation attack), thread preemption on cores 2 and 3 resulted in scheduling jitter exceeding the 25\,ms hard deadline for real-time track updates, causing track display stutter. SaaG caught this contention prior to packaging, identifying the exact colliding core identifiers.

---

## 5. Verification Cost & Complexity

### 5.1 Multi-Scale Naval Platform Benchmarking Setup

We evaluated SaaG verification latency across 5 scaling operational profiles modeled on real-world ADVENT CMS platform configurations:
1. **ADVENT Rota — USV/UxV Platform:** 258 Apps, 1,852 Topics, 1 Node, 81 Libraries ($|V|=2,192, |E|=6,980$).
2. **ADVENT Martı — Maritime Patrol Aircraft / Helicopter:** 238 Apps, 1,219 Topics, 1 Node, 40 Libraries ($|V|=1,498, |E|=4,824$).
3. **ADVENT Ufuk — Coastal Surveillance & C2 Station:** 184 Apps, 1,857 Topics, 23 Nodes, 110 Libraries ($|V|=2,174, |E|=7,142$).
4. **Milgem CMS / ADVENT Kalyon — Corvette/Frigate Combatant:** 318 Apps, 2,831 Topics, 21 Nodes, 84 Libraries ($|V|=3,254, |E|=11,460$).
5. **LHD CMS / ADVENT Kalyon — Task Group Command Flagship:** 308 Apps, 2,303 Topics, 66 Nodes, 98 Libraries ($|V|=2,775, |E|=9,620$).

*Experimental Environment:* Benchmarks executed on a dedicated Linux runner (Ubuntu 22.04 LTS, 8-core AMD EPYC 7763 @ 2.45 GHz, 32 GB RAM). SaaG is implemented in Python 3.11 with NetworkX 3.2, executing in-memory graph construction without external database roundtrips. Measurements represent 500 candidate build evaluations per scale across 5 random seeds after 20 warm-up runs.

### 5.2 Verification Latency & Complexity Breakdown

| Platform Profile | Operational Domain | Total Components | Graph Construction (s) | Rule Auditing (s) | Total Mean (s) | P95 Latency (s) |
|---|---|---:|---:|---:|---:|---:|
| **ADVENT Martı** | Air C2 / MPA | 1,498 | 0.123 ± 0.020 | 0.002 ± 0.000 | **0.125 ± 0.020** | 0.150 |
| **ADVENT Ufuk** | Coastal C2 Station | 2,174 | 0.406 ± 0.017 | 0.003 ± 0.000 | **0.410 ± 0.017** | 0.435 |
| **ADVENT Rota** | USV/UxV Platform | 2,192 | 0.430 ± 0.024 | 0.005 ± 0.000 | **0.435 ± 0.024** | 0.450 |
| **LHD CMS** | Task Group Flagship | 2,775 | 1.138 ± 0.007 | 0.014 ± 0.000 | **1.152 ± 0.007** | 1.161 |
| **Milgem CMS / Kalyon** | Frigate Combatant | 3,254 | 0.757 ± 0.013 | 0.003 ± 0.000 | **0.760 ± 0.013** | 0.780 |

*Table 4: Gate execution latency across 5 ADVENT CMS operational platforms ($N=500$ evaluations per platform).*

```
Execution Latency Breakdown (LHD CMS Task Group Flagship Profile - 2,775 Components, 66 Nodes):
=============================================================================================
[====================================================>        ]  98.8%  Graph Construction (1.138 s)
[=>                                                           ]   1.2%  Rule Auditing & SCC (0.014 s)
=============================================================================================
Total Pipeline Overhead: 1.152 s (<0.22% of 9-minute automated build)
```

#### Scaling Behavior & Node-Count Impact on Graph Construction
The benchmark results reveal two key architectural dynamics:

1. **Dominance of Graph Construction:** Across all evaluated operational platforms, Graph Construction accounts for **98.4\% to 99.6\% of total wall-clock time**, whereas pure Rule Auditing executes in merely **2 to 14 milliseconds** ($0.002$--$0.014$\,s). Once the multigraph $G_{u'}$ is assembled in memory, static policy evaluations (Tarjan SCC cycle detection, DDS RxO matrix checking, and CPU pinning scans) are computationally negligible.
2. **Impact of Physical Host Node Distribution:** A critical insight emerges from comparing **LHD CMS** (2,775 components across 66 physical nodes) and **Milgem CMS / Kalyon** (3,254 components across 21 physical nodes). Although Milgem has more total software components, the LHD Flagship profile exhibits higher graph construction latency (1.138\,s vs 0.757\,s). This behavior is driven by the quadratic complexity of dependency lifting across the **66 physical OPCON consoles and server nodes**: evaluating pairwise process co-location edges (`broker_to_broker`, `node_to_node`, `node_to_broker`, and cross-chassis core-pinning bounds) scales with the physical node topology density ($O(k^2)$ per host across 66 nodes).
3. **Single-Node Embedded Performance:** For single-node tactical units (ADVENT Martı with 1,498 components: 0.125\,s; ADVENT Rota with 2,192 components: 0.435\,s), the absence of inter-node routing and cross-console lifting allows verification to complete in well under 0.5 seconds.

The theoretical complexity of individual verification checks confirms their scalability:
* Tarjan's SCC cycle detection: $O(|V| + |E|)$.
* Core allocation & pinning clash check: $O(k^2)$ per host node, where $k$ is the number of co-located processes ($k \ll |V|$).
* DDS RxO contract matching: $O(|P(t)| \cdot |S(t)|)$ per topic $t$.

---

## 6. Lessons Learned: The Data-Acquisition Bottleneck in Defense Systems

The primary practical insight from developing and deploying SaaG in naval defense engineering is that **the computational cost of graph analysis is negligible, but configuration data acquisition across enterprise and security silos is the true blocker.**

```
+-------------------------------------------------------------------------------+
| CORE INDUSTRIAL LESSON:                                                       |
|   Static architectural verification algorithms are fast and cheap (<= 1.15 s).|
|   The bottleneck lies in extracting authoritative configuration data from     |
|   disparate engineering tools, OEM ICDs, and OS scripts into the pipeline.    |
+-------------------------------------------------------------------------------+
```

### 6.1 Specified vs. Implemented Gap Analysis

Table 5 summarizes the 7 verification capabilities specified with system architects during project inception and their implementation status:


| Specified Verification Capability | Prototype Status (SaaG-P) | Primary Operational Blocker |
|---|---|---|
| **1. Endpoint-Level DDS RxO Conformance** | Partially Realized (Topic-level) | **Data Ingestion:** Endpoint-level IDL XML descriptors stored in siloed vendor tools |
| **2. Field-Level Payload Schema Alignment** | Partially Realized (Topic string match) | **Data Ingestion:** Third-party sensor/weapon ICD AST parser not integrated into build agent |
| **3. Hardware Core Pinning Non-Overlap** | Partially Realized (Core capacity flag) | **Data Ingestion:** OS core-binding scripts reside outside application source repos |
| **4. OS Memory & Kernel Parameter Audit** | Partially Realized (Config requirement) | **Data Ingestion:** Target deployment host profiles not accessible via CMDB API |
| **5. Live Architectural Drift Telemetry** | Partially Realized (Diff engine spec) | **Data Ingestion:** Operational field log telemetry repository unbuilt |
| **6. Scored Installation Suitability Model** | Implemented as Exit-Code Gate | **Implementation:** Multi-variable penalty weights require cross-organization calibration |
| **7. Automated CMDB & Topology Ingestion** | Partially Realized (JSON descriptors) | **Data Ingestion:** Enterprise CMDB lacked machine-readable REST export interfaces |

*Table 5: Specified vs. Implemented Gap Analysis in SaaG Verification Capability.*

### 6.2 The Anatomy of Data Ingestion Blockers in Defense Projects

Six of the seven specified capabilities were obstructed by configuration data silos:

1. **Classified & Third-Party OEM Repository Siloing:** Application code is developed in version-controlled Git repositories, but sensor/weapon Interface Control Documents (ICDs) and hardware core-pinning deployment configurations were maintained in isolated shipyard commissioning archives.
2. **Descriptor Format Fragmentation:** Middleware QoS definitions were distributed across XML profile files, C++ source pragmas, and runtime startup scripts.
3. **Absence of Unified Machine-Readable CMDB APIs:** The enterprise configuration database was designed for human asset tracking, lacking real-time API endpoints for automated CI/CD runners.

*Recommendation for Defense Practitioners:* When introducing architectural digital twins into naval combat systems, organizations should invest first in **declarative, centralized configuration-as-code practices and machine-readable ICD registries** before investing in sophisticated graph reasoning engines.

---

## 7. Related Work

### 7.1 Architecture Conformance & Reflexion Models
Software architecture conformance checking verifies that an implementation matches its intended design. Murphy, Notkin, and Sullivan [9] pioneered Software Reflexion Models to compare high-level architectural models against extracted source-code call graphs. Perry and Wolf [10] and de Silva and Balasubramaniam [11] characterized architectural erosion in evolving systems. Terra and Valente [12] introduced dependency constraint languages to enforce structural boundaries. While these techniques analyze compile-time source dependencies, SaaG targets distributed pub/sub middleware, deriving runtime failure dependencies from asynchronous DDS topic interactions and hardware core bindings in naval mission systems.

### 7.2 Configuration Error Detection in Distributed Systems
Configuration errors represent a leading cause of distributed system outages. Xu and Zhou [13] provide a comprehensive taxonomy of systems approaches for tackling configuration faults. Tang et al. [14] describe holistic configuration management systems at internet scale. Huang et al. [15] developed ConfValley to validate cloud configurations using declarative logic constraints. SaaG extends configuration verification to safety-critical naval combat pub/sub systems, coupling DDS QoS contract matching with military safety assurance levels (MIL-STD-882E).

### 7.3 Policy-as-Code & Middleware Diagnostics
Policy engines such as ArchUnit, OPA-Gatekeeper, and Kyverno enforce static rules on code and container manifests. In the robotics and middleware domains, ROS 2 and OMG DDS tools provide runtime QoS mismatch reporting [6, 17]. However, runtime diagnostics fire only after nodes are initialized in the target environment. SaaG performs pre-deployment gating within CI/CD pipelines, preventing non-conforming builds from reaching staging testbeds or operational ships.

### 7.4 Digital Twins in Systems Engineering
Kritzinger et al. [7] established the foundational taxonomy distinguishing digital models, digital shadows, and digital twins based on data synchronization topology. Tao et al. [18] reviewed digital twins in physical manufacturing. SaaG adapts the digital model concept to software architecture, establishing a static, reproducible baseline for pre-deployment gating in continuous delivery pipelines for naval combat management systems.

---

## 8. Conclusion & Future Work

We presented **SaaG (System as a Graph)**, an architectural digital model for pre-deployment verification and CI/CD gating in mission-critical Naval Combat Management Systems (ADVENT CMS). Operating on an attributed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$), SaaG statically audits DDS QoS contracts, CPU core allocations, topic continuity, and dependency cycles before software reaches operational platforms. Benchmarks across 5 ADVENT operational profiles (from ADVENT Martı MPA and ADVENT Rota USVs to the Milgem/Kalyon Frigate profile with 3,254 components) demonstrate that verification requires $\approx 1$\,s ($<0.2\%$ of an automated build). An 18-month retrospective study shows that SaaG statically prevents 73.7\% of historical middleware incidents. Our analysis demonstrates that graph analysis is computationally cheap, whereas configuration data acquisition across defense engineering silos is the primary practical hurdle.


**Future Work:** We are developing automated ICD harvesters to bridge configuration data ingestion blockers, expanding delta-aware gating across multi-ship task group pipelines, and exploring LLM-assisted remediation proposals subject to mandatory human-in-the-loop safety reviews under naval software assurance guidelines.

---

## References

1. ARMERKOM / HAVELSAN. *ADVENT Combat Management System: Architectural Principles and Operational Capabilities*, Technical Whitepaper, HAVELSAN Inc., 2022.
2. Department of Defense (DoD). *System Safety (MIL-STD-882E)*, Department of Defense Standard Practice, 2012.
3. NATO Standardization Office. *STANAG 4586: Standard Interfaces of UAV Control System (UCS) for NATO UAV Interoperability*, Edition 4, 2017.
4. NATO Standardization Office. *STANAG 5516: Tactical Data Exchange - Link 16*, Edition 8, 2020.
5. European Commission. *Commission Implementing Regulation (EU) 2017/373 of 1 March 2017 laying down common requirements for providers of ATM/ANS*, Official Journal of the European Union, L 62/1, 2017.
6. Object Management Group (OMG). *Data Distribution Service (DDS) Specification*, Version 1.4, OMG Document formal/2015-04-01, 2015. https://doi.org/10.2514/4.103285
7. W. Kritzinger, M. Karner, G. Traar, J. Henjes, and W. Sihn. Digital Twin in manufacturing: A categorical literature review and classification. *IFAC-PapersOnLine*, 51(11):1016–1022, 2018. https://doi.org/10.1016/j.ifacol.2018.08.474
8. NATO Standardization Office. *STANAG 5522: Tactical Data Exchange - Link 22*, Edition 3, 2021.
9. G. C. Murphy, D. Notkin, and K. J. Sullivan. Software reflexion models: Bridging the gap between design and implementation. *IEEE Transactions on Software Engineering*, 27(4):364–380, 2001. https://doi.org/10.1109/32.917525
10. D. E. Perry and A. L. Wolf. Foundations for the study of software architecture. *ACM SIGSOFT Software Engineering Notes*, 17(4):40–52, 1992. https://doi.org/10.1145/141874.141884
11. L. de Silva and D. Balasubramaniam. Controlling software architecture erosion: A survey. *Journal of Systems and Software*, 85(1):132–151, 2012. https://doi.org/10.1016/j.jss.2011.07.036
12. R. Terra and M. T. Valente. A dependency constraint language to manage software architectures. *Software: Practice and Experience*, 44(9):1073–1094, 2014. https://doi.org/10.1002/spe.2191
13. T. Xu and Y. Zhou. Systems approaches to tackling configuration errors: A survey. *ACM Computing Surveys*, 47(4):Article 70, 2015. https://doi.org/10.1145/2791577
14. C. Tang, T. Kooburat, P. Venkatachalam, A. Chander, Z. Blake, B. Liang, and X. Liu. Holistic configuration management at Facebook. In *Proceedings of the 25th ACM Symposium on Operating Systems Principles (SOSP '15)*, pp. 328–343, 2015. https://doi.org/10.1145/2815400.2815401
15. P. Huang, B. Dong, D. Yuan, Y. Zhou, B. Zhou, and H. Mai. ConfValley: A systematic approach to validating system configurations. In *Proceedings of the 10th European Conference on Computer Systems (EuroSys '15)*, Article 4, 2015. https://doi.org/10.1145/2741948.2741961
16. P. H. Feiler and D. P. Gluch. *Model-Based Engineering with AADL: An Introduction to the SAE Architecture Analysis & Design Language Standard*. Addison-Wesley Professional, 2012.
17. E. Gamma, R. Helm, R. Johnson, and J. Vlissides. *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley, 1994.
18. F. Tao, H. Zhang, A. Liu, and A. Y. C. Nee. Digital twin in industry: State-of-the-art. *IEEE Transactions on Industrial Informatics*, 15(4):2405–2415, 2019. https://doi.org/10.1109/TII.2018.2873186
19. J. Humble and D. Farley. *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation*. Addison-Wesley, 2010.
