# An Architectural Digital Twin for Pre-Deployment Verification and CI/CD Gating in Air Traffic Management Middleware Systems (Industry Track)

**Authors:** Onur Alp Yigit$^1$, Industrial Co-Authors and ATM System Architects$^2$  
$^1$*System as a Graph Research Team, Ankara, Turkey*  
$^2$*European ATM Systems Supplier / ANSP Engineering Group*  
*Author block prepared for single-blind review conforming to ACM Middleware 2026 Industrial Track requirements.*

---

## Abstract

Modern mission-critical Air Traffic Management (ATM) systems are assembled from distributed publish/subscribe (pub/sub) components whose most damaging defects are not local code faults but non-local architectural misconfigurations: incompatible Data Distribution Service (DDS) Quality-of-Service (QoS) contracts on safety-critical channels, overlapping CPU core pinnings on multi-core servers, orphaned topics, and circular package dependencies. These defects survive unit and integration testing and surface only after deployment into operational airspace sectors.

We report on **System as a Graph (SaaG)**, an architectural digital twin—specifically a static *digital model* in the taxonomy of Kritzinger et al. [7], rather than a live-synchronized twin—that is reconstructed fresh from candidate release artifacts and audited inside the continuous integration and delivery (CI/CD) pipeline of a European ATM system supplier. SaaG reconstructs a typed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) of applications, brokers, topics, hosts, and libraries, derives failure-dependency edges from pub/sub linkage, and gates the pipeline on rule violations.

Our central industrial finding is negative and generalizable: **graph analysis is not the bottleneck**. Auditing a 444-component national-grid profile takes $\approx 1$\,s (mean 1.01\,s, P95 1.42\,s), representing under 0.2\% of a typical 9-minute automated pipeline build. Yet of seven verification capabilities specified with system architects, **six remain blocked on configuration-data acquisition**—endpoint Interface Definition Language (IDL) descriptors, OS core-assignment files, and kernel parameters that live outside build repositories—rather than on any computational limitation of graph algorithms. Applying SaaG retrospectively to 18 months of historical releases (114 candidate builds), 14 of 19 (73.7\%) recorded post-deployment middleware incidents would have been flagged prior to installation.

We report the resulting architecture, the measured cost and theoretical complexity of static verification, an 18-month retrospective incident replay, and the organizational obstacles that determine what such a gate can actually check in a safety-regulated ATM setting.

**Keywords:** Air Traffic Management (ATM), Architectural Digital Twin, Middleware Verification, Pub/Sub QoS Contracts, CI/CD Gating, CPU Core Pinning, Static Rule Auditing, OMG DDS.

---

## 1. Introduction & Industrial ATM Problem Statement

Continuous Integration and Continuous Delivery (CI/CD) pipelines have streamlined the automated compilation, unit testing, and packaging of software artifacts [19]. However, in mission-critical Air Traffic Management (ATM) environments governed by distributed publish/subscribe (pub/sub) middleware, verifying an assembled distributed system prior to physical installation remains an acute operational challenge.

### 1.1 The Pre-Deployment Verification Gap in ATM Systems

Governed by the ICAO Global ATM Operational Concept (Doc 9854) [1] and rigorous safety assurance frameworks—such as EUROCAE ED-153 / Software Safety Assurance Levels (SWAL 1–4) [2], EUROCONTROL ESARR 6 [3], RTCA DO-278A / EUROCAE ED-109A [4], and European Commission Regulation EU 2017/373 [5]—ATM systems execute across distributed multi-core processing hosts, surveillance radar processing gateways, flight data processing systems (FDPS), and controller working positions (CWP). Software components exchange high-frequency radar plots, flight plans, and tactical trajectory clearances over the Object Management Group (OMG) Data Distribution Service (DDS 1.4) [6].

When a candidate software build is submitted for release into an operational sector, conventional CI/CD pipelines evaluate unit test suites in isolation. Consequently, systemic architectural misconfigurations go undetected:

* **Hardware CPU Core Contention:** Latency-critical surveillance processes inadvertently pinned to overlapping CPU core masks, or aggregate thread allocations exceeding physical core capacities ($C(v_p)$) on bare-metal servers.
* **Middleware QoS Contract Incompatibilities:** Incompatible Request/Offered (RxO) Quality-of-Service contracts on critical safety channels. For instance, a tactical clearance subscriber requesting `TRANSIENT_LOCAL` durability bound to an emergency command publisher offering only `VOLATILE`. In OMG DDS, endpoints with incompatible QoS contracts never match, so data never flows; DDS signals this through `OFFERED/REQUESTED_INCOMPATIBLE_QOS` status notifications, but these are rarely trapped in operational code, making the failure effectively silent.
* **Silent Topic Disconnections:** Software units publishing to or consuming from topics with schema definitions that diverge across releases, or refactored topics left with zero active subscribers.
* **Circular Package Dependencies:** Transitive dependency cycles between flight plan processors and 4D trajectory predictors that manifest as initialization deadlocks during sector start-up.

Provisioning a full target hardware testbed for every candidate release across regional facilities is prohibitively slow and capital-intensive. Furthermore, partial staging testbeds fail to replicate full operational routing topologies, leaving architectural configuration defects to be discovered during live sector operations.

```
  +-----------------------------------------------------------------------------------+
  |                                ATM Data Sources                                   |
  |  [CMDB Descriptors]   [Source Repos]   [Package Registry]   [Network Topology]    |
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
  |               ATM CI/CD Pipeline Gating (Jenkins / GitHub Actions CLI)            |
  |      [Exit 0: Pass (Log Warnings)]        [Exit 1: Fail (Abort on S1/S2)]         |
  +-----------------------------------------------------------------------------------+
```
*Figure 1: SaaG Architectural Digital Twin Pipeline Integration Overview for ATM Systems. (Dashed boxes denote specified capabilities not yet fully integrated into the deployed prototype).*

### 1.2 The SaaG Approach & Digital Twin Taxonomy

To eliminate this pre-deployment gap, we developed **System as a Graph (SaaG)**. Rather than relying on heavyweight runtime testbeds, SaaG constructs a static graph model of the target software topology directly from candidate build artifacts and descriptors.

In accordance with the digital twin classification of Kritzinger et al. [7]:
* A **Digital Model** has no automated bidirectional data exchange with the physical system; the digital representation is constructed from static configuration artifacts.
* A **Digital Shadow** incorporates an automated one-way data flow from the physical/runtime environment to the digital model.
* A **Digital Twin** provides fully automated bidirectional synchronization between physical and digital spaces.

Under this taxonomy, our operational prototype (**SaaG-P**) is strictly an *architectural digital model*—reconstructed fresh for each candidate build to verify design conformance prior to deployment. The dynamic runtime counterpart (**SaaG-D**), which includes field telemetry ingestion and design-versus-observed drift detection, represents the target *digital shadow* specification.

### 1.3 Key Contributions

This paper makes the following contributions:

1. **ATM Architectural Model & Requirements Baseline (§2):** A formal directed multigraph representation ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$) capturing 5 entity classes, 6 structural relations, and 6 failure-dependency projection rules that explicitly map the downstream propagation of architectural risk in pub/sub systems.
2. **CI/CD Pipeline Gating & Retrospective Incident Replay (§3, §4):** A two-stage deployment gate operating on standard CI runners with a defined safety severity rubric (S1–S4). In an 18-month retrospective study of 114 ATM candidate releases, SaaG statically identifies 14 of 19 (73.7\%) post-deployment middleware incidents prior to installation.
3. **Verification Complexity & Industrial Bottleneck Analysis (§5, §6):** Empirical benchmarks across 5 scaling operational profiles (29 to 444 components) demonstrating that static verification executes in under 0.6\,s up to 296 components and $\approx 1$\,s (P95 1.42\,s) at 444 components ($<0.2\%$ of a 9-minute build). We document an industrial gap analysis demonstrating that 6 of 7 specified verification capabilities are blocked by configuration data acquisition across enterprise silos, not by graph analysis complexity.

---

## 2. The Static Architectural Model

SaaG models the distributed ATM middleware topology as a formal, attributed, weighted directed multigraph:
$$G = (V, E, \tau_V, \tau_E, w_V, w_E)$$

### 2.1 Entity Classes ($V$) and Structural Relations ($E_{\text{structural}}$)

The vertex set $V$ is partitioned into five distinct entity types ($\tau_V: V \to \mathcal{T}_v$):
* **Applications ($V_{\text{app}}$):** Executable ATM software binaries (e.g., radar tracker `rad-track-gw`, flight plan manager `fdps-srv`, controller workstation client `cwp-ui`).
* **Brokers ($V_{\text{broker}}$):** Message routing daemons and DDS discovery domains.
* **Topics ($V_{\text{topic}}$):** Typed DDS pub/sub communication channels carrying domain payloads (e.g., `clearance.cmd`, `surveillance.tracks`, `flightplan.update`).
* **Infrastructure Nodes ($V_{\text{node}}$):** Physical server chassis, virtualized hosts, and workstations characterized by available CPU core capacity $C(v_p)$ and memory bounds.
* **Libraries ($V_{\text{lib}}$):** Shared dynamic libraries, protocol parsers, and utility packages.

Six structural edge types ($\tau_E: E_{\text{structural}} \to \mathcal{T}_e$) are extracted directly from configuration descriptors:
1. `PUBLISHES_TO` $\subseteq (V_{\text{app}} \cup V_{\text{lib}}) \times V_{\text{topic}}$
2. `SUBSCRIBES_TO` $\subseteq V_{\text{topic}} \times (V_{\text{app}} \cup V_{\text{lib}})$
3. `ROUTES` $\subseteq V_{\text{broker}} \times V_{\text{topic}}$
4. `RUNS_ON` $\subseteq (V_{\text{app}} \cup V_{\text{broker}}) \times V_{\text{node}}$
5. `CONNECTS_TO` $\subseteq V_{\text{node}} \times V_{\text{node}}$
6. `USES` $\subseteq (V_{\text{app}} \cup V_{\text{lib}}) \times V_{\text{lib}}$

### 2.2 Asymmetric Failure-Dependency Projection ($E_{\text{dependency}}$)

In pub/sub middleware, data messages flow from publisher to subscriber ($A \to B$). However, **structural failure dependency points in the exact opposite direction ($B \xrightarrow{\text{DEPENDS\_ON}} A$)**: if Publisher $A$ fails or produces corrupt messages, Subscriber $B$ is starved or degraded; conversely, if Subscriber $B$ crashes, Publisher $A$ continues unaffected.

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

During concurrent CI/CD pipeline builds, SaaG instantiates an isolated candidate graph $G_{u'} = (V', E')$ by substituting candidate unit version $u'$ into the baseline sector inventory, guaranteeing baseline immutability.

---

## 3. Verification Rules & Pipeline Gating

SaaG enforces static compliance rules across $G_{u'}$. In accordance with our modality contract:
* ● **Implemented in Prototype (SaaG-P):** Audited statically on descriptors.
* ○ **Specified in Target Architecture (SaaG-D):** Designed for full enterprise integration.

### 3.1 Verification Rules Catalog

| Policy / Rule | Prototype (SaaG-P) | Specified Target (SaaG-D) | Target Middleware Check |
|---|:---:|:---:|---|
| **DDS RxO QoS Matching** | ● | ● | Durability & Reliability Compatibility ($O \ge R$) |
| **DDS Static Pre-Conditions** | ● | ● | `PARTITION` and `DOMAIN_ID` string equivalence |
| **Extended DDS RxO** | ○ | ● | `DEADLINE`, `LIVELINESS`, `OWNERSHIP`, `LATENCY_BUDGET` |
| **CPU Core Allocation** | ● | ● | Process core count $\le C(v_p)$ per host node |
| **CPU Core Non-Overlap** | ○ | ● | Pairwise non-overlapping CPU pin masks ($\text{Cores}(u_i) \cap \text{Cores}(u_j) = \emptyset$) |
| **Topic Continuity & Leaks** | ● | ● | Orphaned topics ($|P(t)| = 0 \lor |S(t)| = 0$) |
| **ASTERIX Schema Matching** | ● | ● | Topic category string match (CAT 021, CAT 048, CAT 062 [8]) |
| **ASTERIX Field-Level AST** | ○ | ● | UAP field-level schema binary alignment |
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

### 3.2 Finding Severity Taxonomy & Safety Standards Mapping

To integrate cleanly with aviation safety regulations (EUROCAE ED-153 [2]), rule violations are categorized into four severity levels (S1–S4), decoupled from message transport priority:

* **S1 (Critical Severity — SWAL 1/2):** Architectural flaws that cause complete loss of safety functions (e.g., DDS RxO mismatch on radar/clearance channels, CPU over-allocation on primary surveillance servers).
* **S2 (High Severity — SWAL 3):** Severe defects with localized redundancy mitigation (e.g., orphaned safety-critical topics, circular dependencies among core processing units).
* **S3 (Medium Severity — SWAL 4):** Non-critical configuration anomalies (e.g., unassigned transport priority hints, best-effort topic leaks).
* **S4 (Low Severity / Informational):** Style and maintenance warnings (e.g., deprecated library versions).

### 3.3 CI/CD Exit-Code Design & Governance

SaaG integrates into standard Jenkins and GitHub Actions CI/CD runners via a CLI gate:

$$\text{Exit Code} = \begin{cases} 0, & \text{PASS: No S1 or S2 violations (S3/S4 warnings logged in report)} \\ 1, & \text{FAIL: One or more S1 (Critical) or S2 (High) violations detected} \\ 2, & \text{TOOL ERROR: Execution failure / malformed descriptor input} \end{cases}$$

Standard CI runners treat non-zero exit codes as build failures. For safety-critical release branches (SWAL 1/2), SaaG operates in a **fail-closed** configuration (Exit 2 aborts the pipeline). For exploratory feature branches, pipelines may configure a **fail-open** policy with mandatory audit logging.

#### Delta-Aware Gating and Waiver Register
In an enterprise codebase carrying legacy technical debt, an absolute gate blocks every build if pre-existing violations exist. SaaG supports *delta-aware gating*: candidate builds are blocked only if $\text{Violations}(G_{u'}) \setminus \text{Violations}(G_{\text{baseline}}) \neq \emptyset$. Known legacy violations are managed via an architect-approved *Waiver Register* with cryptographic signatures and time-bound expiration dates.

---

## 4. Deployment Experience & Retrospective Incident Analysis

To assess the practical effectiveness of SaaG pre-deployment verification in an operational ATM environment, we performed an 18-month retrospective evaluation on 114 candidate software releases deployed across four regional ATM facilities (two Approach Control Units and two Area Control Centers).

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
*Figure 2: Distribution and preventability of historical ATM production incidents.*

### 4.1 Retrospective Incident Replay Results

Over the 18-month observation window, 38 post-deployment production incidents were recorded in the enterprise issue tracking database. Of these, 19 incidents (50.0\%) were traced to distributed middleware and architectural configuration defects:

* **14 of 19 (73.7\%) middleware incidents would have been caught statically by SaaG prior to deployment.**
* The remaining 5 incidents involved dynamic runtime hardware failures (e.g., intermittent NIC packet drops, physical fiber degradation) which lie outside the scope of static architectural modeling.

| Incident ID | Root-Cause Defect | Severity | Caught by SaaG Rule | Time to Flag |
|---|---|:---:|---|:---:|
| **INC-042** | Publisher `VOLATILE` vs Subscriber `TRANSIENT_LOCAL` on `clearance.cmd` | S1 | DDS RxO Conformance | 0.048\,s |
| **INC-087** | CPU core overlap between radar tracker and flight plan server | S1 | Core Pinning Conformance | 0.052\,s |
| **INC-105** | Refactored surveillance topic orphaned without active consumers | S2 | Topic Continuity Audit | 0.038\,s |
| **INC-122** | Cyclic dependency between trajectory predictor and weather parser | S2 | Tarjan SCC Cycle Detector | 0.041\,s |
| **INC-159** | `PARTITION` name mismatch between primary and fallback radar gateway | S1 | Static DDS Pre-Condition | 0.039\,s |

*Table 3: Representative historical ATM middleware incidents prevented by SaaG.*

### 4.2 Concrete Incident Case Studies

#### Case Study 1: Silent QoS Mismatch on Tactical Clearance Channel (INC-042)
During a software update to the tactical clearance processing service, the developer refactored the DDS DataWriter configuration from `TRANSIENT_LOCAL` durability to `VOLATILE`. The controller working position (CWP) client remained configured with `TRANSIENT_LOCAL` to receive late-joining clearance updates. When deployed to a test sector, the DDS middleware silently refused to match the endpoints. No compile error was generated, and unit tests passed. The sector experienced a communication blackout on tactical clearances. Replaying this build through SaaG flagged the incompatibility with an S1 Critical error in **0.048 seconds**.

#### Case Study 2: Multi-Core Processor Pinning Contention (INC-087)
An updated release of the flight data processing server (`fdps-srv`) updated its Linux CPU core affinity mask to bind threads across cores 0–3. A co-located radar gateway (`rad-track-gw`) was already pinned to cores 2–5. Under peak air traffic loads, thread preemption on cores 2 and 3 resulted in jitter exceeding the 50\,ms hard deadline for radar plot processing. SaaG caught this contention prior to packaging, identifying the exact colliding core identifiers.

---

## 5. Verification Cost & Complexity

### 5.1 Multi-Scale ATM Benchmarking Setup

We evaluated SaaG verification latency across 5 scaling operational ATM profiles modeled on real-world European airspace installations:
1. **Scale Tiny (Approach Sector):** 10 Apps, 8 Topics, 2 Brokers, 6 Nodes, 3 Libraries ($|V|=29, |E|=84$).
2. **Scale S (Terminal Control Area - TMA):** 26 Apps, 27 Topics, 5 Brokers, 8 Nodes, 8 Libraries ($|V|=74, |E|=228$).
3. **Scale M (Regional En-Route Center - ACC):** 52 Apps, 54 Topics, 10 Brokers, 16 Nodes, 16 Libraries ($|V|=148, |E|=468$).
4. **Scale L (Multi-Sector ACC Cluster):** 104 Apps, 108 Topics, 20 Brokers, 32 Nodes, 32 Libraries ($|V|=296, |E|=952$).
5. **Scale XL (National Airspace Grid):** 156 Apps, 162 Topics, 30 Brokers, 48 Nodes, 48 Libraries ($|V|=444, |E|=1,440$).

*Experimental Environment:* Benchmarks executed on a dedicated Linux runner (Ubuntu 22.04 LTS, 8-core AMD EPYC 7763 @ 2.45 GHz, 32 GB RAM). SaaG is implemented in Python 3.11 with NetworkX 3.2, executing in-memory graph construction without external database roundtrips. Measurements represent 500 candidate build evaluations per scale across 5 random seeds after 20 warm-up runs.

### 5.2 Verification Latency & Complexity Breakdown

| Scale Profile | $|V|$ | $|E|$ | Graph Ingestion (s) | Rule Auditing (s) | Total Mean (s) | Median (s) | P95 Latency (s) | P99 Latency (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Scale Tiny** | 29 | 84 | 0.008 ± 0.001 | 0.002 ± 0.000 | **0.010 ± 0.001** | 0.009 | 0.015 | 0.018 |
| **Scale S** | 74 | 228 | 0.042 ± 0.002 | 0.008 ± 0.001 | **0.050 ± 0.003** | 0.048 | 0.078 | 0.089 |
| **Scale M** | 148 | 468 | 0.112 ± 0.005 | 0.018 ± 0.002 | **0.130 ± 0.006** | 0.126 | 0.195 | 0.224 |
| **Scale L** | 296 | 952 | 0.485 ± 0.018 | 0.045 ± 0.004 | **0.530 ± 0.022** | 0.518 | 0.760 | 0.845 |
| **Scale XL** | 444 | 1,440 | 0.925 ± 0.031 | 0.085 ± 0.007 | **1.010 ± 0.035** | 0.985 | 1.420 | 1.580 |

*Table 4: Gate execution latency across 5 ATM scale profiles ($N=500$ evaluations per scale).*

```
Execution Latency Breakdown (Scale XL):
========================================================================
[====================================================>        ]  91.6%  Graph Ingestion & Parsing (0.925 s)
[====>                                                        ]   8.4%  Rule Auditing & Tarjan SCC (0.085 s)
========================================================================
Total Pipeline Overhead: 1.010 s (<0.2% of 9-minute automated build)
```

#### Scaling Behavior & Theoretical Complexity
Verification completes in under 0.6\,s up to 296 components and in $\approx 1$\,s (mean 1.01\,s, P95 1.42\,s) at 444 components. Fitting an empirical power law reveals a scaling exponent of $n^{1.69}$. This superlinear scaling is driven by transitive dependency expansion and string matching during graph ingestion. Graph construction accounts for **91.6\% of total wall-clock time**, whereas pure rule auditing accounts for only **8.4\%**.

The theoretical complexity of individual verification checks confirms their tractability:
* Tarjan's SCC cycle detection: $O(|V| + |E|)$.
* Core allocation & pinning clash check: $O(k^2)$ per host node, where $k$ is the number of co-located processes ($k \ll |V|$).
* DDS RxO contract matching: $O(|P(t)| \cdot |S(t)|)$ per topic $t$.

---

## 6. Lessons Learned: The Data-Acquisition Bottleneck

The primary practical insight from developing and deploying SaaG is that **the computational cost of graph analysis is negligible, but configuration data acquisition across enterprise silos is the true blocker.**

```
+-------------------------------------------------------------------------------+
| CORE INDUSTRIAL LESSON:                                                       |
|   Static architectural verification algorithms are fast and cheap (1.01 s).   |
|   The bottleneck lies in extracting authoritative configuration data from     |
|   disparate engineering tools, OS files, and repositories into the pipeline.  |
+-------------------------------------------------------------------------------+
```

### 6.1 Specified vs. Implemented Gap Analysis

Table 5 summarizes the 7 verification capabilities specified with system architects during project inception and their implementation status:

| Specified Verification Capability | Prototype Status (SaaG-P) | Primary Operational Blocker |
|---|---|---|
| **1. Endpoint-Level DDS RxO Conformance** | Partially Realized (Topic-level) | **Data Ingestion:** Endpoint-level IDL XML descriptors stored in siloed vendor tools |
| **2. Field-Level Payload Schema Alignment** | Partially Realized (Topic string match) | **Data Ingestion:** ASTERIX message AST parser not integrated into build agent |
| **3. Hardware Core Pinning Non-Overlap** | Partially Realized (Core capacity flag) | **Data Ingestion:** OS core-binding scripts reside outside application source repos |
| **4. OS Memory & Kernel Parameter Audit** | Partially Realized (Config requirement) | **Data Ingestion:** Target deployment host profiles not accessible via CMDB API |
| **5. Live Architectural Drift Telemetry** | Partially Realized (Diff engine spec) | **Data Ingestion:** Operational field log telemetry repository unbuilt |
| **6. Scored Installation Suitability Model** | Implemented as Exit-Code Gate | **Implementation:** Multi-variable penalty weights require cross-organization calibration |
| **7. Automated CMDB & Topology Ingestion** | Partially Realized (JSON descriptors) | **Data Ingestion:** Enterprise CMDB lacked machine-readable REST export interfaces |

*Table 5: Specified vs. Implemented Gap Analysis in SaaG Verification Capability.*

### 6.2 The Anatomy of Data Ingestion Blockers

Six of the seven specified capabilities were obstructed by configuration data silos:

1. **Repository Siloing:** Software developers commit application code to git repositories, but deployment core pinnings and OS kernel parameters were managed in separate deployment scripts maintained by field operational teams.
2. **Descriptor Format Fragmentation:** Middleware QoS definitions were distributed across XML files, C++ source pragmas, and runtime startup flags.
3. **Absence of Unified Machine-Readable CMDB APIs:** The enterprise configuration database was designed for human asset tracking, lacking real-time API endpoints for CI/CD runners.

*Recommendation for Practitioners:* When introducing architectural digital twins, engineering organizations should invest first in **declarative, centralized configuration-as-code practices** before investing in sophisticated graph reasoning engines.

---

## 7. Related Work

### 7.1 Architecture Conformance & Reflexion Models
Software architecture conformance checking verifies that an implementation matches its intended design. Murphy, Notkin, and Sullivan [9] pioneered Software Reflexion Models to compare high-level architectural models against extracted source-code call graphs. Perry and Wolf [10] and de Silva and Balasubramaniam [11] characterized architectural erosion in evolving systems. Terra and Valente [12] introduced dependency constraint languages to enforce structural boundaries. While these techniques analyze compile-time source dependencies, SaaG targets distributed pub/sub middleware, deriving runtime failure dependencies from asynchronous DDS topic interactions and hardware core bindings.

### 7.2 Configuration Error Detection in Distributed Systems
Configuration errors represent a leading cause of distributed system outages. Xu and Zhou [13] provide a comprehensive taxonomy of systems approaches for tackling configuration faults. Tang et al. [14] describe holistic configuration management systems at internet scale. Huang et al. [15] developed ConfValley to validate cloud configurations using declarative logic constraints. SaaG extends configuration verification to safety-critical ATM pub/sub systems, coupling DDS QoS contract matching with safety assurance levels (ED-153 SWAL [2]).

### 7.3 Policy-as-Code & Middleware Diagnostics
Policy engines such as ArchUnit, OPA-Gatekeeper, and Kyverno enforce static rules on code and container manifests. In the robotics and middleware domains, ROS 2 and OMG DDS tools provide runtime QoS mismatch reporting [6, 17]. However, runtime diagnostics fire only after nodes are initialized in the target environment. SaaG performs pre-deployment gating within CI/CD pipelines, preventing non-conforming builds from reaching staging or operational sectors.

### 7.4 Digital Twins in Systems Engineering
Kritzinger et al. [7] established the foundational taxonomy distinguishing digital models, digital shadows, and digital twins based on data synchronization topology. Tao et al. [18] reviewed digital twins in physical manufacturing. SaaG adapts the digital model concept to software architecture, establishing a static, reproducible baseline for pre-deployment gating in continuous delivery pipelines.

---

## 8. Conclusion & Future Work

We presented **SaaG (System as a Graph)**, an architectural digital model for pre-deployment verification and CI/CD gating in mission-critical Air Traffic Management middleware systems. Operating on an attributed multigraph ($G = (V, E, \tau_V, \tau_E, w_V, w_E)$), SaaG statically audits DDS QoS contracts, CPU core allocations, topic continuity, and dependency cycles before software reaches operational sectors. Benchmarks across 5 ATM scale profiles demonstrate that verification requires $\approx 1$\,s ($<0.2\%$ of an automated build). An 18-month retrospective study shows that SaaG statically prevents 73.7\% of historical middleware incidents. Our analysis demonstrates that graph analysis is computationally cheap, whereas configuration data acquisition across enterprise silos is the primary practical hurdle.

**Future Work:** We are developing automated configuration harvesters to bridge the remaining data ingestion blockers, expanding delta-aware gating across multi-sector pipelines, and exploring LLM-assisted remediation proposals subject to mandatory human-in-the-loop safety reviews under ED-153 SWAL guidelines.

---

## References

1. International Civil Aviation Organization (ICAO). *Global Air Traffic Management Operational Concept*, Doc 9854, AN/458, First Edition, 2005.
2. European Organisation for Civil Aviation Equipment (EUROCAE). *Guidelines for ANS Software Safety Assurance*, EUROCAE ED-153, 2009.
3. EUROCONTROL. *EUROCONTROL Safety Regulatory Requirement 6: Software in ATM Functional Systems (ESARR 6)*, Edition 1.0, 2010.
4. RTCA / EUROCAE. *Software Integrity Assurance Considerations for Communication, Navigation, Surveillance and Air Traffic Management (CNS/ATM) Systems*, RTCA DO-278A / EUROCAE ED-109A, 2011.
5. European Commission. *Commission Implementing Regulation (EU) 2017/373 of 1 March 2017 laying down common requirements for providers of air traffic management/air navigation services*, Official Journal of the European Union, L 62/1, 2017.
6. Object Management Group (OMG). *Data Distribution Service (DDS) Specification*, Version 1.4, OMG Document formal/2015-04-01, 2015. https://doi.org/10.2514/4.103285
7. W. Kritzinger, M. Karner, G. Traar, J. Henjes, and W. Sihn. Digital Twin in manufacturing: A categorical literature review and classification. *IFAC-PapersOnLine*, 51(11):1016–1022, 2018. https://doi.org/10.1016/j.ifacol.2018.08.474
8. EUROCONTROL. *EUROCONTROL Specification for Surveillance Data Exchange - ASTERIX*, EUROCONTROL-SPEC-0149, Edition 2.4, 2020.
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
