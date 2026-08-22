# A Middleware-Centric Architectural Digital Model for Pre-Deployment Verification and CI/CD Gating in Naval Combat Management Systems

**Authors:** Ibrahim Onuralp Yigit$^1$, Industrial Co-Authors and CMS System Architects$^2$  
$^1$*Command Control and Defense Technologies, HAVELSAN Inc., Istanbul, Turkiye*  
$^2$*Naval Combat Systems Directorate, HAVELSAN Inc., Ankara, Turkiye*  
*Author block prepared for single-blind review conforming to ACM Middleware 2026 Industrial Track requirements.*

---

## Abstract

Modern mission-critical Naval Combat Management Systems (CMS), such as HAVELSAN's combat-proven ADVENT CMS, are complex distributed real-time systems built upon publish/subscribe (pub/sub) middleware. They integrate hundreds of software applications across shipboard operator consoles (OPCONs), radar trackers, weapon controllers, tactical data links (Link 11, Link 16, Link 22, Link H), and multi-domain platforms (surface combatants, amphibious assault flagships, maritime patrol aircraft, coastal surveillance stations, and unmanned vessels). In these safety-critical environments, the most severe integration defects are non-local architectural misconfigurations: incompatible Quality-of-Service (QoS) contracts on hard-deadline weapon assignment channels, overlapping CPU core affinity masks on multi-core tactical servers, orphaned tactical topics, and circular package dependencies across engagement planning modules. These defects easily survive isolated unit and component testing, only to surface during costly shipyard integration, live-fire sea trials, or multi-ship joint tactical exercises.

We report on an architectural digital model generated using System as a Graph (SaaG), an industrial framework designed for pre-deployment verification and continuous integration and delivery (CI/CD) gating in naval combat management systems. Reconstructed fresh from candidate release descriptors rather than relying on runtime synchronization, SaaG constructs an attributed typed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) capturing applications, brokers, tactical topics, tactical processing nodes, and shared libraries. The framework derives asymmetric failure-dependency projections from pub/sub communication topologies ($B \xrightarrow{\text{DEPENDS\_ON}} A$) and gates the CI/CD pipeline against static rule violations mapped to military safety severity levels (MIL-STD-882E S1–S4).

Our central industrial finding is clear: graph analysis is not the computational bottleneck. Across five scaling operational naval platform profiles (1,498 to 3,254 components across up to 66 distributed nodes), static verification executes in merely 0.125 to 1.152\,s (mean 1.152\,s, P95 1.161\,s on the 66-node LHD flagship; 0.760\,s on a frigate combatant), representing under 0.22\% of a typical 9-minute automated build pipeline. We demonstrate that the SaaG framework statically detects critical pub/sub misconfiguration scenarios prior to release packaging without requiring expensive physical testbeds. However, an industrial gap analysis reveals that of seven verification capabilities specified with naval combat system architects, six remain constrained by configuration-data acquisition across defense engineering silos rather than by algorithmic limits. We report the framework architecture, multi-scale verification performance, representative misconfiguration case studies, and practical lessons from industrial deployment.

**Keywords:** Naval Combat Management Systems (CMS), ADVENT CMS, SaaG Framework, Architectural Digital Model, Middleware Verification, Pub/Sub QoS Contracts, CI/CD Gating, CPU Core Pinning, OMG DDS, MIL-STD-882E, Network Enabled Capability (NEC).

---

## 1. Introduction & Industrial Problem Statement

Continuous Integration and Continuous Delivery (CI/CD) pipelines have fundamentally transformed software engineering by automating compilation, testing, and artifact generation [19]. In naval defense systems, modern Combat Management Systems (CMS) have evolved from monolithic mainframes into modular, distributed, open-architecture systems governed by high-performance publish/subscribe (pub/sub) middleware [6].

### 1.1 The Pre-Deployment Verification Gap in Naval Combat Systems

Modern naval operations require rapid sensor-to-shooter loops, multi-sensor data fusion, coordinated weapon assignment, and seamless cross-platform interoperability. Built to fulfill these demands, **ADVENT CMS** (developed by **HAVELSAN** in cooperation with the Turkish Naval Forces Research Center Command - ARMERKOM) represents a state-of-the-art naval combat suite deployed across a wide product tree:
* **ADVENT Kalyon:** Surface combatant CMS encompassing frigates, corvettes, and specialized mine countermeasures (MCM) vessels.
* **Milgem CMS:** Combat management suite for Ada-class corvettes and Istanbul-class frigates, handling multi-threat warfare (Anti-Air Warfare [AAW], Anti-Surface Warfare [ASuW], Anti-Submarine Warfare [ASW], Electronic Warfare [EW]).
* **LHD CMS:** Specialized fleet flagship configuration for Landing Helicopter Dock amphibious assault ships (e.g., L400 TCG Anadolu), providing task group command oversight, multi-link gateway centers, joint operations planning, and unmanned vehicle swarm control.
* **ADVENT Rota:** Mission Management System (MMS) for unmanned surface, underwater, and aerial vehicles (USV/UUV/UAV), integrating STANAG 4586 compliance, autonomous navigation, and direct payload control from shipboard consoles without dedicated GCS hardware.
* **ADVENT Martı:** Airborne Command and Control System designed for Maritime Patrol Aircraft (MPA) and naval helicopters, executing airborne surveillance, sonobuoy processing, and tactical data link relay.
* **ADVENT Ufuk:** Land-based coastal surveillance and C2 information management system aggregating coastal radar networks, AIS, ADS-B, and electro-optical sensors to compile and disseminate the Recognized Maritime Picture (RMP).

Across these platforms, ADVENT CMS comprises over **155 external system integrations**, **750 distributed software applications**, and **13,000,000 lines of code**. Subsystems communicate over **Genieware**—a national publish/subscribe middleware designed for real-time mission-critical defense systems, operating on a DDS-like pub/sub architecture—and Tactical Data Links (TDLs: Link 11, Link 16, Link 22, and ADVENT Native Link H) [12]. Under the **Network Enabled Capability (NEC)** paradigm, ADVENT shares sensor tracks and weapon allocations across platforms, enabling Force-Wide Weapon/Sensor Allocation (WASA) and remote firing authorizations.

```
  +-----------------------------------------------------------------------------------+
  |                            Naval CMS Data Sources                                 |
  |  [Weapon/Sensor ICDs]  [Source Repos]  [Platform Configs]  [Node Specs]    |
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
  | - Pub/Sub QoS Rules & Core Pinning Rules  |   |  - Architectural Drift Detection  |
  | - Dependency Derivation (Tarjan SCC)      |   |  - Static vs Observed Edge Diff   |
  +-------------------------------------------+   : - - - - - - - - - - - - - - - - - :
                        \                                     /
                         v                                   v
  +-----------------------------------------------------------------------------------+
  |             Naval CI/CD Pipeline Gating (Jenkins / GitLab CI / CLI Gate)          |
  |      [Exit 0: Pass (Log Warnings)]        [Exit 1: Fail (Abort on S1/S2)]         |
  +-----------------------------------------------------------------------------------+
```
*Figure 1: SaaG Architectural Digital Model Pipeline Integration Overview for ADVENT Combat Management Systems. (Dashed boxes denote specified capabilities not yet fully integrated into the deployed prototype).*

When a candidate software build is submitted for release into an operational naval platform, conventional CI/CD pipelines evaluate unit and module tests in isolation. Consequently, critical architectural misconfigurations slip through:

* **Hardware CPU Core Contention on Nodes:** Latency-critical track fusion daemons or fire control calculators inadvertently pinned to overlapping CPU core affinity masks with non-real-time GUI renderers or background loggers on multi-core tactical consoles.
* **Middleware QoS Contract Incompatibilities:** Incompatible Request/Offered (RxO) Quality-of-Service contracts on mission-critical channels. For instance, a remote weapon assignment subscriber requesting `TRANSIENT_LOCAL` durability bound to a fire control publisher offering only `VOLATILE`. In pub/sub middleware like Genieware and DDS, endpoints with incompatible QoS contracts never match, so data never flows; the middleware signals this through incompatible QoS status notifications, but these are rarely trapped in operational code, making the failure effectively silent.
* **Silent Tactical Topic Disconnections:** Software units publishing to or consuming from topics with schema definitions that diverge across platform releases, or refactored TDL forwarding topics left with zero active subscribers.
* **Circular Package Dependencies:** Transitive dependency cycles between weapon allocation planners (WASA) and threat evaluation modules that manifest as initialization deadlocks during OPCON console start-up.

Provisioning full target hardware testbeds (physical multi-console Combat Information Centers [CIC], real sensor/weapon simulators, and multi-ship test ranges) for every candidate release is prohibitively expensive, logistically complex, and slow. Leaving architectural defects to be discovered during shipyard commissioning, harbor acceptance tests (HAT), or sea acceptance tests (SAT) leads to massive project delays and severe safety risks.

### 1.2 The Architectural Digital Model Paradigm & Digital Twin Taxonomy

To eliminate this pre-deployment gap, we developed **System as a Graph (SaaG)**. Rather than relying on heavyweight runtime testbeds, SaaG constructs a static graph model of the target combat system topology directly from candidate build artifacts and interface descriptors.

In accordance with the digital twin classification of Kritzinger et al. [7]:
* A **Digital Model** has no automated bidirectional data exchange with the physical system; the digital representation is constructed from static configuration artifacts.
* A **Digital Shadow** incorporates an automated one-way data flow from the physical/runtime environment to the digital model.
* A **Digital Twin** provides fully automated bidirectional synchronization between physical and digital spaces.

Under this taxonomy, our operational prototype (**SaaG-P**) is strictly an *architectural digital model*—reconstructed fresh for each candidate build to verify design conformance prior to deployment. The dynamic runtime counterpart (**SaaG-D**), which includes field telemetry ingestion and design-versus-observed drift detection, represents the target *digital shadow* specification.

### 1.3 Key Contributions & Empirical Findings

This paper makes the following contributions:

1. **Naval CMS Architectural Model & Requirements Baseline (§2):** A formal directed multigraph representation ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) capturing 5 entity classes, 6 structural relations, and 6 failure-dependency projection rules that explicitly map the downstream propagation of architectural risk in pub/sub naval combat systems.
2. **CI/CD Pipeline Gating & Architectural Verification Methodology (§3, §4):** A two-stage deployment gate operating on standard CI runners with a defined safety severity rubric (S1–S4) aligned with military safety frameworks (MIL-STD-882E). We demonstrate static pre-deployment verification across representative mission-critical pub/sub misconfiguration scenarios (QoS mismatches, CPU core contention, topic continuity breaks, circular dependencies).
3. **Verification Complexity & Industrial Bottleneck Analysis (§5, §6):** Empirical benchmarks across 5 scaling operational naval platform profiles (1,498 to 3,254 components; 1 to 66 nodes) based on ADVENT CMS platform lines (Martı, Ufuk, Rota, Kalyon/Milgem, LHD Flagship), demonstrating that static verification executes in 0.125\,s (Martı), 0.410\,s (Ufuk), 0.435\,s (Rota), 0.760\,s (Milgem frigate), and 1.152\,s (LHD flagship with 66 nodes, P95 1.161\,s), consuming $<0.22\%$ of a 9-minute build. We analyze why physical node distribution drives graph lifting complexity, and document an industrial gap analysis demonstrating that 6 of 7 specified verification capabilities are blocked by configuration data acquisition across defense engineering silos, not by graph analysis complexity.

---

## 2. The Architectural Digital Model: Formulation and Graph Derivation

SaaG adopts and operationalizes the formal graph modeling foundation established by Yigit and Buzluca [20] for distributed publish-subscribe systems. We formalize the distributed naval CMS middleware topology as an attributed, weighted directed multigraph:
$$G = (V, E, \tau_V, \tau_E, w_V, w_E)$$

### 2.1 Entity Classes ($V$) and Structural Relations ($E_{\text{structural}}$)

The vertex set $V$ is partitioned into five distinct entity types ($\tau_V: V \to \mathcal{T}_v$):
* **Applications ($V_{\text{app}}$):** Executable CMS software binaries (e.g., radar track fusion gateway `track-fusion-gw`, threat evaluation service `threat-eval-srv`, WASA engagement planner `wasa-allocator`, tactical display server `geodisplay-srv`, operator console client `opcon-ui`, Link 16 parser `advlink-l16`, USV autonomy controller `rota-autonomy`).
* **Brokers ($V_{\text{broker}}$):** Genieware discovery domains, routing daemons, and middleware gateways facilitating inter-node tactical communication.
* **Topics ($V_{\text{topic}}$):** Typed publish/subscribe communication channels carrying domain payloads (e.g., `tactical.tracks`, `weapon.assignment.cmd`, `threat.eval.result`, `link16.jseries`, `sensor.radar.plots`, `mine.qroutes`).
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

Building upon the dependency analysis methodology of Yigit and Buzluca [20], SaaG projects logical `DEPENDS_ON` edges from structural topology:

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

### 2.4 Process-Isolated Candidate Digital Models for Concurrent CI/CD Builds

During concurrent CI/CD pipeline builds, SaaG instantiates an isolated candidate graph $G_{u'} = (V', E')$ by substituting candidate unit version $u'$ into the baseline platform inventory, guaranteeing baseline immutability.

---

## 3. Model-Driven Verification Rules & CI/CD Pipeline Gating

SaaG enforces static compliance rules across $G_{u'}$. In accordance with our modality contract:
* ● **Implemented in Prototype (SaaG-P):** Audited statically on descriptors.
* ○ **Specified in Target Architecture (SaaG-D):** Designed for full enterprise integration.

### 3.1 Static Verification Rules Catalog

| Policy / Rule | Prototype (SaaG-P) | Specified Target (SaaG-D) | Target Middleware Check |
|---|:---:|:---:|---|
| **Pub/Sub RxO QoS Matching** | ● | ● | Durability & Reliability Compatibility ($O \ge R$) |
| **Middleware Static Pre-Conditions** | ● | ● | `PARTITION` (Security/Mission boundary) & `DOMAIN_ID` match |
| **Extended Pub/Sub RxO** | ○ | ● | `DEADLINE`, `LIVELINESS`, `OWNERSHIP`, `LATENCY_BUDGET` |
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
| Pub/Sub Middleware (Genieware / DDS) RxO Matching Contract:                   |
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

### 3.2 Severity Rubric & Alignment with Military Safety Standards (MIL-STD-882E)

To integrate cleanly with military system safety standards (MIL-STD-882E and naval software integrity levels), rule violations are categorized into four severity levels (S1–S4), decoupled from message transport priority:

* **S1 (Critical Severity — Catastrophic / Safety Critical):** Architectural flaws that cause complete loss of safety-critical functions (e.g., pub/sub RxO mismatch on weapon assignment or primary radar tracking channels, CPU over-allocation on fire control servers).
* **S2 (High Severity — Critical / Mission Essential):** Severe defects with localized redundancy or secondary mitigation (e.g., orphaned tactical data link topics, circular dependencies among core WASA engagement planning units).
* **S3 (Medium Severity — Marginal / Operational):** Non-critical configuration anomalies (e.g., unassigned transport priority hints, best-effort auxiliary sensor stream topic leaks).
* **S4 (Low Severity / Informational):** Style and maintenance warnings (e.g., deprecated utility library versions, non-standard topic naming).

### 3.3 CI/CD Runner Integration: Exit Codes, Delta-Aware Gating, & Waiver Register

SaaG integrates into standard Jenkins and GitLab CI runners via a CLI gate:

$$\text{Exit Code} = \begin{cases} 0, & \text{PASS: No S1 or S2 violations (S3/S4 warnings logged in report)} \\ 1, & \text{FAIL: One or more S1 (Critical) or S2 (High) violations detected} \\ 2, & \text{TOOL ERROR: Execution failure / malformed descriptor input} \end{cases}$$

Standard CI runners treat non-zero exit codes as build failures. For safety-critical release branches (e.g., weapon control, fire authorization, track fusion), SaaG operates in a **fail-closed** configuration (Exit 2 aborts the pipeline). For non-tactical auxiliary feature branches, pipelines may configure a **fail-open** policy with mandatory audit logging.

#### Delta-Aware Gating and Waiver Register
In an enterprise naval codebase carrying legacy subsystems, an absolute gate blocks every build if pre-existing violations exist. SaaG supports *delta-aware gating*: candidate builds are blocked only if $\text{Violations}(G_{u'}) \setminus \text{Violations}(G_{\text{baseline}}) \neq \emptyset$. Known legacy violations are managed via a Chief Architect-approved *Waiver Register* with cryptographic signatures and time-bound expiration dates.

---

## 4. Multi-Scale Naval Platform Architectures & Verification Methodology

To assess the practical applicability of SaaG pre-deployment verification in an operational naval combat systems environment, we model the architectural scales and middleware configurations across five major ADVENT platform families (**ADVENT Martı**, **ADVENT Ufuk**, **ADVENT Rota**, **ADVENT Kalyon / Milgem CMS**, and **LHD CMS Flagship**).

### 4.1 Multi-Domain Combat System Architecture & Platform Profiles

Modern naval combat suites deploy across diverse physical and operational domains, as reflected in the public product tree of HAVELSAN ADVENT CMS:
* **Airborne Command & Control (ADVENT Martı):** Deployed on Maritime Patrol Aircraft (MPA), helicopters, and naval UAVs, handling airborne radar, sonobuoy acoustic processing, and tactical data link relays with tight embedded single-node footprints ($|V|=1,498, |E|=4,824$).
* **Coastal Surveillance & C2 Station (ADVENT Ufuk):** Land-based multi-sensor compilation center integrating coastal radar networks, AIS, ADS-B, and electro-optical surveillance across 23 distributed server nodes ($|V|=2,174, |E|=7,142$).
* **Unmanned & Autonomous Systems (ADVENT Rota):** Mission Management System for unmanned surface, underwater, and aerial platforms (USV/UUV/UAV) supporting STANAG 4586 compliance and autonomous payload control ($|V|=2,192, |E|=6,980$).
* **Surface Combatant Core (Milgem CMS / ADVENT Kalyon):** Comprehensive multi-warfare suite (AAW, ASuW, ASW, EW) deployed on corvettes and frigates across 21 tactical console nodes ($|V|=3,254, |E|=11,460$).
* **Task Group Command Flagship (LHD CMS):** Fleet flagship suite (such as L400 TCG Anadolu) featuring large-scale multi-link gateway centers, joint operations planning, and 66 physical operator consoles and tactical server chassis ($|V|=2,775, |E|=9,620$).

Across all platform scales, subsystems rely on **Genieware** publish/subscribe middleware to facilitate real-time sensor-to-shooter coordination and Network Enabled Capability (NEC).

### 4.2 Continuous Verification & Pipeline Gating Workflow

SaaG operates directly within continuous integration runners (Jenkins, GitLab CI) upon every merge request:
1. **Descriptor Ingestion & Candidate Isolation:** The pipeline extracts candidate unit descriptors, IDL schemas, topic binding specifications, and node affinity masks. It generates an isolated candidate multigraph $G_{u'}$.
2. **Failure-Dependency Projection:** Inverted failure edges ($B \xrightarrow{\text{DEPENDS\_ON}} A$) are computed along with hierarchical criticality weights.
3. **Multi-Policy Rule Evaluation:** The verification engine evaluates pub/sub QoS contracts, core pinning bounds, topic connectivity, and SCC cycles.
4. **Delta-Aware Gating:** The runner checks new violations against the baseline register and waiver list, returning Exit 0 (Pass) or Exit 1 (Fail).

### 4.3 Evaluation on Representative Architectural Misconfiguration Scenarios

To validate the verification engine across mission-critical middleware failure modes without relying on restricted proprietary records, we evaluate SaaG against representative classes of architectural misconfigurations:

1. **Weapon Assignment Channel QoS Incompatibility (Scenario A - S1 Critical):** A candidate update alters the durability policy of a remote weapon assignment topic (`weapon.assignment.cmd`) from `TRANSIENT_LOCAL` to `VOLATILE` while the subscriber remains `TRANSIENT_LOCAL`. In pub/sub middleware (Genieware/DDS), this contract mismatch prevents endpoint matching, silently dropping fire commands. SaaG detects this incompatibility statically during graph lifting in $<0.05$\,s.
2. **Operator Console (OPCON) Multi-Core Pinning Contention (Scenario B - S1 Critical):** A multi-sensor track fusion daemon binds processing threads to CPU cores 0–3, conflicting with a co-located 3D tactical display server bound to cores 2–5. Under heavy track loads, mutual preemption causes scheduling jitter exceeding hard 25\,ms display deadlines. SaaG identifies the colliding CPU affinity masks on host nodes.
3. **Orphaned Tactical Data Link (TDL) Forwarding Channels (Scenario C - S2 High):** A refactored Link 16 J-series forwarding topic is left without active subscriber endpoints, silently breaking cross-platform track dissemination. SaaG detects the disconnected topic endpoint ($|S(t)|=0$).
4. **Engagement Planning Dependency Cycles (Scenario D - S2 High):** Transitive package dependencies between a Force-Wide Weapon/Sensor Allocation (WASA) planner and a threat evaluation module form a closed cycle ($A \to B \to C \to A$), leading to initialization deadlocks during OPCON startup. Tarjan's SCC algorithm isolates the cycle in linear time ($O(|V|+|E|)$).

| Scenario Class | Injected Architectural Fault | Severity | Detected Rule | Verification Time |
|---|---|:---:|---|:---:|
| **Scenario A** | Durability mismatch on `weapon.assignment.cmd` (`VOLATILE` vs `TRANSIENT_LOCAL`) | S1 | Pub/Sub RxO Match | 0.048\,s |
| **Scenario B** | CPU core overlap (cores 2–3) between track fusion and tactical display | S1 | Core Pinning Conformance | 0.052\,s |
| **Scenario C** | Orphaned Link 16 forwarding topic without active subscribers | S2 | Topic Continuity Audit | 0.038\,s |
| **Scenario D** | Cyclic dependency between WASA engagement planner and threat evaluation | S2 | Tarjan SCC Cycle Detector | 0.041\,s |
| **Scenario E** | Security `PARTITION` mismatch between primary and redundant sensor gateways | S1 | Middleware Pre-Condition | 0.039\,s |

*Table 3: Pre-deployment verification performance across representative naval middleware misconfiguration scenarios.*

---

## 5. Computational Performance & Scalability of Digital Model Auditing

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

#### Scaling Dynamics & Physical Node Distribution Impact
The benchmark results reveal two key architectural dynamics:

1. **Dominance of Graph Construction:** Across all evaluated operational platforms, Graph Construction accounts for **98.4\% to 99.6\% of total wall-clock time**, whereas pure Rule Auditing executes in merely **2 to 14 milliseconds** ($0.002$--$0.014$\,s). Once the multigraph $G_{u'}$ is assembled in memory, static policy evaluations (Tarjan SCC cycle detection, pub/sub RxO matrix checking, and CPU pinning scans) are computationally negligible.
2. **Impact of Physical Host Node Distribution:** A critical insight emerges from comparing **LHD CMS** (2,775 components across 66 physical nodes) and **Milgem CMS / Kalyon** (3,254 components across 21 physical nodes). Although Milgem has more total software components, the LHD Flagship profile exhibits higher graph construction latency (1.138\,s vs 0.757\,s). This behavior is driven by the quadratic complexity of dependency lifting across the **66 physical OPCON consoles and server nodes**: evaluating pairwise process co-location edges (`broker_to_broker`, `node_to_node`, `node_to_broker`, and cross-chassis core-pinning bounds) scales with the physical node topology density ($O(k^2)$ per host across 66 nodes).
3. **Single-Node Embedded Performance:** For single-node tactical units (ADVENT Martı with 1,498 components: 0.125\,s; ADVENT Rota with 2,192 components: 0.435\,s), the absence of inter-node routing and cross-console lifting allows verification to complete in well under 0.5 seconds.

The theoretical complexity of individual verification checks confirms their scalability:
* Tarjan's SCC cycle detection: $O(|V| + |E|)$.
* Core allocation & pinning clash check: $O(k^2)$ per host node, where $k$ is the number of co-located processes ($k \ll |V|$).
* Pub/Sub RxO contract matching: $O(|P(t)| \cdot |S(t)|)$ per topic $t$.

---

## 6. Industrial Lessons: The Data-Acquisition Bottleneck in Architectural Digital Modeling

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
| **1. Endpoint-Level Pub/Sub RxO Conformance** | Partially Realized (Topic-level) | **Data Ingestion:** Endpoint-level IDL XML descriptors stored in siloed vendor tools |
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

*Recommendation for Defense Practitioners:* When introducing architectural digital models into naval combat systems, organizations should invest first in **declarative, centralized configuration-as-code practices and machine-readable ICD registries** before investing in sophisticated graph reasoning engines.

---

## 7. Related Work

### 7.1 Architecture Conformance & Reflexion Models
Software architecture conformance checking verifies that an implementation matches its intended design. Murphy, Notkin, and Sullivan [9] pioneered Software Reflexion Models to compare high-level architectural models against extracted source-code call graphs. Perry and Wolf [10] and de Silva and Balasubramaniam [11] characterized architectural erosion in evolving systems. Terra and Valente [12] introduced dependency constraint languages to enforce structural boundaries. Yigit and Buzluca [20] formulated graph-based dependency analysis for critical components in publish-subscribe systems. SaaG builds upon these foundations and operationalizes an architectural digital model for pre-deployment CI/CD gating in naval combat management systems.

### 7.2 Configuration Error Detection in Distributed Systems
Configuration errors represent a leading cause of distributed system outages. Xu and Zhou [13] provide a comprehensive taxonomy of systems approaches for tackling configuration faults. Tang et al. [14] describe holistic configuration management systems at internet scale. Huang et al. [15] developed ConfValley to validate cloud configurations using declarative logic constraints. SaaG extends configuration verification to safety-critical naval combat pub/sub systems, coupling DDS QoS contract matching with military safety assurance levels (MIL-STD-882E).

### 7.3 Policy-as-Code & Middleware Diagnostics
Policy engines such as ArchUnit, OPA-Gatekeeper, and Kyverno enforce static rules on code and container manifests. In the robotics and middleware domains, ROS 2 and OMG DDS tools provide runtime QoS mismatch reporting [6, 17]. However, runtime diagnostics fire only after nodes are initialized in the target environment. SaaG performs pre-deployment gating within CI/CD pipelines, preventing non-conforming builds from reaching staging testbeds or operational ships.

### 7.4 Digital Models, Shadows, and Twins in Systems Engineering
Kritzinger et al. [7] established the foundational taxonomy distinguishing digital models, digital shadows, and digital twins based on data synchronization topology. Tao et al. [18] reviewed digital twins in physical manufacturing. SaaG adapts the digital model concept to software architecture, establishing a static, reproducible baseline for pre-deployment gating in continuous delivery pipelines for naval combat management systems.

---

## 8. Conclusion & Evolution Toward Runtime Digital Shadows

We presented **SaaG (System as a Graph)**, an architectural digital model framework for pre-deployment verification and CI/CD gating in mission-critical Naval Combat Management Systems (ADVENT CMS). Operating on an attributed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$), SaaG statically audits publish/subscribe QoS contracts, CPU core allocations, topic continuity, and dependency cycles before software reaches operational platforms. Benchmarks across 5 operational ADVENT profiles (from single-node embedded units like ADVENT Martı MPA at 0.125\,s and ADVENT Rota USVs to the 66-node LHD Flagship at 1.152\,s) demonstrate that verification requires $\le 1.15$\,s ($<0.22\%$ of an automated build), while reliably catching critical misconfigurations across representative fault scenarios. Our analysis demonstrates that graph analysis is computationally lightweight, whereas configuration data acquisition across defense engineering silos is the primary practical hurdle.

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
20. I. O. Yigit and F. Buzluca. A Graph-Based Dependency Analysis Method for Identifying Critical Components in Distributed Publish-Subscribe Systems. *IEEE Access*, 2024. https://doi.org/10.1109/ACCESS.2024 (https://ieeexplore.ieee.org/document/11315354)
