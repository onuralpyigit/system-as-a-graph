# Software Design Description (SDD): System as a Graph (SaaG)

**Definition:** The System as a Graph (SaaG) Digital System Model is a static digital system model developed using an architectural digital twin approach, which models the structural and relational architecture of the system using a node-relationship representation, without actually running the system applications. In this model, system entities such as software units, middleware and communication services, processor/console units, topics, and messages are represented as nodes; the dependency, publishing, and consuming relationships between them are represented as relationships. The behavioral analysis dimension of the model is achieved not by running the components, but by overlaying Analytical Evaluation Data — derived from field records or the scenario generator — onto this model.

**Purpose:** This SDD describes the design that satisfies the SRS, specifying the CSCI-wide design decisions (§1), the CSCI's architectural decomposition, concept of execution, interface design, and database design (§2), the detailed design of each CSC down to CSU level (§3), and the traceability of every SRS requirement to the design element that satisfies it (§4). It introduces no CSUs beyond the 10 already defined in the SRS and SDP — each CSU is instead decomposed internally into design elements.

---

## 1. CSCI-Wide Design Decisions

1. **Static digital twin, no execution**: The CSCI never executes the target system's actual software units; it constructs and analyzes a node-relationship representation of the system's architecture (SRS §1.1 MSD.1, §5.1 CSM-01.1).
2. **Separable structural and behavioral layers**: The structural graph (Core System Model, built from Model Setup Data) and the behavioral overlay (Analytical Evaluation Data, built from field records or synthetic data) are constructed independently by different CSUs and bound together by CSM-02 without either altering the other, so they remain separable at all times (SRS §5.2 CSM-02.5).
3. **Concurrency-safe shared model access**: Multiple user sessions, and multiple concurrent production-pipeline/analysis/simulation operations, read and write the same Core System Model without compromising model integrity or result consistency (SRS §5.1 CSM-01.29–30).
4. **Non-destructive experimentation**: Structural "what-if" changes (adding/removing nodes or relationships, altering attributes) are performed only on a working model derived from the Core System Model, never on the Core System Model itself (SRS §6.1 VAE-01.17).
5. **Common validation-and-error-recording pattern**: Every data-acquisition path in the CSCI (configuration data, source repository files, field records, synthetic data, Model Setup Data) performs format/integrity/mandatory-field checks and records failures with a consistent set of attributes (source, reason, time), rather than each CSC inventing its own error model (SRS §1.1 MSD.16, 20, 22; §3.1 FRD.5; §4.1 ADP.5–6).

---

## 2. CSCI Architectural Design

### 2.1 CSCI Components

The SaaG CSCI is decomposed into 6 Computer Software Components (CSCs) and 10 Computer Software Units (CSUs), identical to the decomposition already fixed in the SRS:

| CSC | Abbreviation | CSUs | SRS Reference | SDD Reference |
|---|---|---|---|---|
| Model Setup Data Generation | SaaG-MSD | MSD | §1.1 | §3.1.1 |
| Scenario Generator | SaaG-SCG | SCG | §2.1 | §3.2.1 |
| Field Records Database | SaaG-FRD | FRD | §3.1 | §3.3.1 |
| Analytical Data Preparation | SaaG-ADP | ADP | §4.1 | §3.4.1 |
| Node-Relationship Based Core System Model | SaaG-CSM | CSM-01, CSM-02 | §5.1, §5.2 | §3.5.1, §3.5.2 |
| Design Verification, Analysis and Evaluation | SaaG-VAE | VAE-01, VAE-02, VAE-03, VAE-04 | §6.1–§6.4 | §3.6.1–§3.6.4 |

### 2.2 Concept of Execution

1. **MSD** acquires and validates data from the configuration management database, source code repository, package repository, and network topology source, and assembles it into a Model Setup Data file.
2. **CSM-01** ingests the Model Setup Data file and constructs the Core System Model (nodes and relationships).
3. In parallel, **SCG** produces synthetic data from user-defined scenarios, and **FRD** stores System Field Records uploaded from the field.
4. **ADP** consumes either the System Field Records (from FRD) or the synthetic data (from SCG) — never both for the same run — and produces Analytical Evaluation Data.
5. **CSM-02** binds the Analytical Evaluation Data to the relevant nodes and relationships of the Core System Model, preserving which upstream source (field or synthetic) produced it.
6. **VAE** is the sole component through which users and automation clients (CLI/build tools) interact with the model: **VAE-01** drives the MSD/CSM/ADP production processes and presents results; **VAE-02** performs read-only rule-based verification against the Core System Model; **VAE-03** performs read-only simulation and observational analysis using Analytical Evaluation Data; **VAE-04** evaluates installation suitability of candidate software units for the production deployment pipeline.

This sequencing matches the incremental build order already established in SDP §2.

**Figure 1. CSCI Concept of Execution**

```mermaid
flowchart TD
    A["1. MSD acquires &amp; validates<br/>external data"] --> B["2. CSM-01 constructs<br/>Core System Model"]
    B --> C{"3. Parallel acquisition"}
    C --> D["SCG produces<br/>synthetic data"]
    C --> E["FRD stores<br/>System Field Records"]
    D --> F["4. ADP produces<br/>Analytical Evaluation Data"]
    E --> F
    F --> G["5. CSM-02 binds AED<br/>to Core System Model"]
    B --> G
    G --> H["6. VAE-01 drives production<br/>&amp; presents results"]
    H --> I["VAE-02<br/>Design Verifier"]
    H --> J["VAE-03<br/>Design Analyzer"]
    H --> K["VAE-04<br/>Design Evaluator"]
```

### 2.3 Interface Design

SaaG has 12 interfaces: 7 external interfaces connecting the CSCI to systems outside its boundary, and 5 internal interfaces connecting its CSUs to one another.

**Table 1. External Interfaces**

| ID | Interface | Direction | CSU | SRS Reference |
|---|---|---|---|---|
| EXT-IF-01 | Configuration Management Database | Bidirectional (query/response) | MSD | MSD.2, 9–13, 16 |
| EXT-IF-02 | Source Code Repository | Inbound | MSD | MSD.3, 17–20 |
| EXT-IF-03 | Software Units Package Repository | Inbound | MSD | MSD.4 |
| EXT-IF-04 | Network Topology Data Source | Inbound (automatic or manual) | MSD | MSD.5–7 |
| EXT-IF-05 | System Field Data Recording Mechanism | Inbound (upload) | FRD | FRD.2 |
| EXT-IF-06 | LDAP Directory Service | Bidirectional | VAE-01 | VAE-01.3 |
| EXT-IF-07 | Build Automation Tools / CLI | Bidirectional | VAE-01 | VAE-01.27 |

**Table 2. Internal Interfaces**

| ID | Interface | Direction | SRS Reference |
|---|---|---|---|
| INT-IF-01 | Model Setup Data Handoff | MSD → CSM-01 | MSD.23 / CSM-01.2 |
| INT-IF-02 | Synthetic Data Handoff | SCG → ADP | SCG.7 / ADP.3 |
| INT-IF-03 | Field Records Handoff | FRD → ADP | FRD.4 / ADP.2 |
| INT-IF-04 | Analytical Evaluation Data Handoff | ADP → CSM-02 | ADP.4 / CSM-02.2 |
| INT-IF-05 | Core System Model Access (read-only) | CSM → VAE | CSM-01.27–28 / VAE-02.3, VAE-03.10 |

**Figure 2. External and Internal Interface Topology**

```mermaid
flowchart LR
    subgraph EXT["External Systems"]
        CMDB["Configuration Management<br/>Database"]
        REPO["Source Code<br/>Repository"]
        PKG["Software Units<br/>Package Repository"]
        NTS["Network Topology<br/>Data Source"]
        FDR["System Field Data<br/>Recording Mechanism"]
        LDAP["LDAP Directory<br/>Service"]
        BAT["Build Automation<br/>Tools / CLI"]
    end
    subgraph CSCI["SaaG CSCI"]
        MSD["MSD"]
        SCG["SCG"]
        FRD["FRD"]
        ADP["ADP"]
        CSM01["CSM-01"]
        CSM02["CSM-02"]
        VAE01["VAE-01"]
    end
    CMDB <-->|"EXT-IF-01"| MSD
    REPO -->|"EXT-IF-02"| MSD
    PKG -->|"EXT-IF-03"| MSD
    NTS -->|"EXT-IF-04"| MSD
    FDR -->|"EXT-IF-05"| FRD
    LDAP <-->|"EXT-IF-06"| VAE01
    BAT <-->|"EXT-IF-07"| VAE01
    MSD -->|"INT-IF-01"| CSM01
    SCG -->|"INT-IF-02"| ADP
    FRD -->|"INT-IF-03"| ADP
    ADP -->|"INT-IF-04"| CSM02
    CSM01 -->|"Core System Model"| CSM02
    CSM02 -->|"INT-IF-05"| VAE01
```

Every data-acquisition interface reports its own deficiency/access/format/integrity errors back through itself, consistent with the CSCI-wide validation pattern (§1, decision 5). The communication method and protocol for every interface listed above, and the choice between automatic and manual acquisition for EXT-IF-04, are to be determined during the critical design phase (tracked in `CDR.md`, group 1.4).

### 2.4 Database Design

SaaG persists 7 data stores:

**Table 3. Data Stores**

| Store | Description | Owning CSU | SRS Reference |
|---|---|---|---|
| Model Setup Data file | Validated source data assembled for model construction | MSD | MSD.23 |
| Software Unit Version Inventory | Software unit name/version per project, platform, version | MSD | MSD.14–15 |
| Field Records Database | Uploaded System Field Records and telemetry | FRD | FRD.1–4 |
| Core System Model | Node-relationship structural graph | CSM-01 | CSM-01.4–5 |
| Analytical Evaluation Data | Behavioral overlay bound to the Core System Model | CSM-02 | CSM-02.3 |
| Working Model | Non-destructive structural sandbox derived from the Core System Model | VAE-01 | VAE-01.17 |
| Findings, Operations & Reports | Verification/analysis/evaluation findings, operation records, and generated reports | VAE-01 | VAE-01.21–26 |

Database-wide design decisions: (1) every store is keyed by project/platform/system-version; (2) the Core System Model and Analytical Evaluation Data are separable stores joined only through CSM-02's binding, per §1 decision 2; (3) Analytical Evaluation Data and the Findings/Operations/Reports store both preserve upstream-source provenance (field record vs. synthetic); (4) ingestion-oriented stores (Model Setup Data file, Field Records Database) share the common validation-status attribute set from §1 decision 5. Physical storage technology per store, and the detailed entity schemas and attribute definitions for all 7 stores, are to be determined during the critical design phase (tracked in `CDR.md`, group 1.5).

---

## 3. CSCI Detailed Design

### 3.1 MSD — Model Setup Data Generation (SaaG-MSD)

#### 3.1.1 CSC-wide design decisions

All external data acquisition funnels through a common validation and error-recording path (mandatory-field checks, missing-data status, access/authorization/integrity error handling) before a single Model Setup Data file is assembled (MSD.1).

#### 3.1.2 CSU detailed design

**Data Source Connector & Configuration Manager** — manages controlled, traceable access to the four external data sources (configuration management database, source code repository, package repository, network topology data source), including user-definable per-source configuration (source type, name, access method, connection address, credentials) and the two supported methods of network topology acquisition (automatic or manual entry). Traces to MSD.2–8.

**Configuration Data Acquisition** — retrieves current project, platform, and system version information from the configuration management database; marks the effective version; marks the acquisition process with an error status on deficiency, access error, or format incompatibility. Traces to MSD.9–13, 16.

**Software Unit Version Inventory Manager** — records and updates the Software Unit Version Inventory (software unit name/version per project, platform, version), including insertion of a candidate software unit version alongside the other defined versions. Traces to MSD.14–15.

**Source Repository Ingestion** — transfers source code, installation scripts, and configuration files for the software units in scope from the source code repository; records file name, path, package/version, and update timestamp per file; reports missing-data status for mandatory files that cannot be obtained; reports access/authorization/integrity errors. Traces to MSD.17–20.

**Data Validation & Model Setup Data Assembler** — performs a mandatory-field-presence check across all received/manually-entered source data; records error reason, source name/type, project/platform association, and error time for each failure; assembles the data that passes verification into the Model Setup Data file handed off via INT-IF-01. Traces to MSD.21–23.

---

### 3.2 SCG — Scenario Generator (SaaG-SCG)

#### 3.2.1 CSC-wide design decisions

Synthetic data generation is fully decoupled from field data collection; scenario inputs and the data they produced are recorded together so any synthetic data set is traceable back to the exact inputs that generated it (SCG.1, 6).

#### 3.2.2 CSU detailed design

**Scenario Input Manager** — captures and traceably records user-defined scenario inputs: scenario scope, scenario type, time interval, data density, and data types to be produced. Traces to SCG.3, 6.

**Synthetic Data Generator** — serves as the data source for system-wide simulation processes; produces synthetic data structurally equivalent to the topic/message schema, field naming, and value-range constraints used by the actual software units. Traces to SCG.2, 4.

**Scenario Output Recorder** — records produced synthetic data together with scenario name, production time, and project/platform/system-version association; prepares the data for transfer via INT-IF-02. Traces to SCG.5, 7.

---

### 3.3 FRD — Field Records Database (SaaG-FRD)

#### 3.3.1 CSC-wide design decisions

System Field Records are stored centrally and indexed for retrieval by project, platform, system version, record source, and upload time; upload-time validation prevents malformed records from entering the store (FRD.1). Storage hardware disk capacity is an environment/infrastructure requirement (SSS-FRD.6) whose sizing will be determined during the critical design phase; it is not modeled as a CSU-level design element.

#### 3.3.2 CSU detailed design

**Record Upload Manager** — accepts user uploads of telemetry and system data records in a controlled, traceable manner, associated with project/platform/system-version; detects and reports format incompatibility, integrity errors, or missing fields at upload time. Traces to FRD.2, 5.

**Record Catalog Manager** — records each uploaded System Field Record with its source, upload time, and project/platform/version association; supports listing, search, and selection of existing records by project, platform, system version, record source, or upload time. Traces to FRD.3–4.

---

### 3.4 ADP — Analytical Data Preparation (SaaG-ADP)

#### 3.4.1 CSC-wide design decisions

Analytical Evaluation Data is produced from exactly one of two upstream sources — System Field Records (via FRD, INT-IF-03) or synthetic data (via SCG, INT-IF-02) — through parallel, independently-validated ingestion paths that converge on a single assembly step (ADP.1).

#### 3.4.2 CSU detailed design

**Field Record Ingestion** — obtains System Field Records from FRD for Analytical Evaluation Data production; detects and reports format incompatibility or unreadable data. Traces to ADP.2, 5.

**Scenario Data Ingestion** — obtains synthetic data from SCG for Analytical Evaluation Data production; detects and reports format incompatibility, unreadable data, or missing fields. Traces to ADP.3, 6.

**Analytical Data Assembler** — processes and appropriately associates the ingested System Field Records or synthetic data, and produces the Analytical Evaluation Data transmitted via INT-IF-04. Traces to ADP.4.

---

### 3.5 Node-Relationship Based Core System Model (SaaG-CSM)

#### 3.5.1 CSM-01: Model Manager

##### 3.5.1.1 CSU-wide design decisions

The Core System Model is built once from validated Model Setup Data and then shared read/write across concurrent sessions and pipeline operations without compromising integrity (CSM-01.1, 29–30).

##### 3.5.1.2 Design elements

**Model Construction Engine** — accepts the Model Setup Data produced by MSD via INT-IF-01; performs format/schema/integrity/mandatory-field checks; converts validated data into a node-relationship Core System Model associated with project/platform/system version; reports missing-entity and invalid-relationship errors; records the Model Setup Data file used, creation time, and model status. Traces to CSM-01.2–5, 25–26.

**Node-Relationship Schema Manager** — defines and maintains the 12 node types (System, Software Segment, CSCI, CSC, CSU, Role, Topic, Message, Operator Console/Processor Units, Network components, Middleware Services, Communication Technology services) and 6 relationship types (runs-on, uses-middleware/communication-service, publishes, consumes, depends-on, assigned-to-role); exposes CPU allocation, OS settings, and runtime environment configuration as queryable node attributes. Traces to CSM-01.6–24.

**Model Access Provider** — makes the Core System Model, and the Analytical Evaluation Data bound to it, available for read access via INT-IF-05. Traces to CSM-01.27–28.

**Concurrency & Session Manager** — handles concurrent read/write operations from multiple user sessions on the same Core System Model without compromising integrity or query-result consistency; executes production-pipeline operations and user analysis/simulation operations concurrently and independently of one another. Traces to CSM-01.29–30.

**Candidate Evaluation Model Builder** — creates a new, process-specific Core System Model combining a candidate software unit version under evaluation with the other software units of the target system version, isolated from other concurrent evaluations. Traces to CSM-01.31.

#### 3.5.2 CSM-02: Analytical Data Binder

##### 3.5.2.1 CSU-wide design decisions

The structural graph (Core System Model) and the behavioral overlay (Analytical Evaluation Data) are bound as separable layers (CSM-02.5), with upstream-source provenance preserved (CSM-02.4).

##### 3.5.2.2 Design elements

**Analytical Data Ingestion** — accepts Analytical Evaluation Data produced by ADP via INT-IF-04. Traces to CSM-02.2.

**Node/Relationship Matcher & Binder** — associates the Analytical Evaluation Data with the relevant project/platform/system version/model; matches record, telemetry, and synthetic data to the corresponding nodes and relationships; preserves provenance (field vs. synthetic); binds without altering the Core System Model, keeping the two layers separable. Traces to CSM-02.1, 3–5.

**Unmatched Record Reporter** — reports node or relationship records for which no counterpart can be found in the Analytical Evaluation Data. Traces to CSM-02.6.

---

### 3.6 Design Verification, Analysis and Evaluation (SaaG-VAE)

#### 3.6.1 VAE-01: Operations Panel

##### 3.6.1.1 CSU-wide design decisions

VAE-01 is the sole interaction surface between users/automation clients and the rest of the CSCI; it drives MSD/CSM/ADP production and presents VAE-02/03/04 results without performing verification or analysis itself (VAE-01.1–2).

##### 3.6.1.2 Design elements

**Session & Authentication Manager** — authenticates users against a defined LDAP directory service (EXT-IF-06) and restricts access to their authorizations; lets the user select the working project/platform/system version and see the currently effective version. Traces to VAE-01.3–4.

**Model Setup Data Workflow Manager** — lists Model Setup Data files for the selected project/platform/version and lets the user pick one; starts and monitors the Model Setup Data production process (in progress/successful/failed) and the Core System Model creation process; continuously displays data-source accessibility status; displays missing-data/access/authorization/format/integrity errors from MSD. Traces to VAE-01.5–9.

**Analytical Data Workflow Manager** — lets the user choose the Analytical Evaluation Data source (System Field Records or SCG synthetic data), select field records or specify scenario inputs accordingly, start/track synthetic- and Analytical-Evaluation-Data production and view errors, and displays the resulting binding/matching status from CSM-02. Traces to VAE-01.10–16.

**Working Model Editor** — derives a working model from the Core System Model and lets the user add/remove nodes and relationships and update attributes without breaking structural integrity, enabling VAE-02/VAE-03 operations on the updated working model instead of the Core System Model directly. Traces to VAE-01.17.

**Model Visualization & Navigation UI** — lets the user search the node-relationship structure, filter by type/project/platform/system-version/software-unit, and perform zoom/pan/selection/attribute-display operations. Traces to VAE-01.19–20.

**Findings & Reporting Manager** — classifies verification/analysis results as conforming/non-conforming; presents each finding with identifier, type, description, affected entity/relationship, related rule/acceptance criterion, supporting evidence, and severity; records cause-and-effect relationships between findings from the same operation; supports sort/filter of findings; records error cause/interruption stage/time for interrupted operations; records simulation scenario metadata; generates exportable summary/detailed reports. Traces to VAE-01.18, 21–26.

**Automation Interface (CLI/Build Tools)** — accepts analysis requests from Build Automation Tools and a Command Line Interface via EXT-IF-07; presents ongoing-operation status to both interactive users and automation clients; ensures requested operations run concurrently and independently of one another. Traces to VAE-01.27.

#### 3.6.2 VAE-02: Design Verifier

##### 3.6.2.1 CSU-wide design decisions

VAE-02 performs only read-only, rule-based structural verification against the Core System Model, optionally without any Analytical Evaluation Data at all (VAE-02.1–3).

##### 3.6.2.2 Design elements

**Structural & Dependency Analysis Engine** — analyzes structural dependencies, communication connections, and runtime-environment relationships between system entities; detects resource-contention/bottleneck conditions, circular dependencies, and disconnected/missing/invalid/unmatched structural relationships. Traces to VAE-02.4, 19–21.

**Topic QoS Verification Engine** — verifies topic data transmission quality-of-service conformance for Durability, Reliability, Lifespan, and Transport Priority parameters. Traces to VAE-02.5–8.

**Publisher/Consumer Matcher** — verifies topic data publisher/consumer matches, detecting topics with no publisher, no consumer, or conflicting same-name content definitions. Traces to VAE-02.9–11.

**Communication Consistency Verifier** — verifies the mutual consistency of source, destination, message, and communication direction information in external-to-middleware communications. Traces to VAE-02.12.

**Resource Allocation Verifier** — analyzes software-unit load-balancing distribution across processor/console units; verifies processor core allocation, operating system settings, and runtime environment memory allocation conformance. Traces to VAE-02.13–18.

**Architectural Rule Verifier** — detects design patterns that violate architectural rules. Traces to VAE-02.22.

#### 3.6.3 VAE-03: Design Analyzer

##### 3.6.3.1 CSU-wide design decisions

VAE-03 performs only read-only analysis using Analytical Evaluation Data, drawn from either the synthetic-data path or the field-record path (VAE-03.1–3).

##### 3.6.3.2 Design elements

**Simulation Analysis Engine** — analyzes, using synthetic-sourced Analytical Evaluation Data, message flow/count/volume/frequency; the effect of a node/relationship becoming inactive; design-time traffic analysis under increased topic/message density or changed publish/consume behavior; propagation of fault/load/communication-interruption/bandwidth-narrowing conditions to dependent nodes; and highest-resource-usage/most-intensive-messaging entities. Traces to VAE-03.4–9.

**Field Data Analysis Engine** — analyzes, using field-record-sourced Analytical Evaluation Data, operational/health status; processor/memory/storage/network usage; error/warning/restart/timeout information; message flow/volume/frequency; communication latency/message loss/successful-transmission rates; topic publish/consume activity; event records; and highest-resource-usage/most-intensive-messaging entities. Traces to VAE-03.10–16, 20–21.

**Architectural Drift Detector** — compares the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in field-record-sourced Analytical Evaluation Data, detecting entities/relationships present-but-not-observed, observed-but-not-present, or incompatible between the two. Traces to VAE-03.17–19.

#### 3.6.4 VAE-04: Design Evaluator

##### 3.6.4.1 CSU-wide design decisions

VAE-04 evaluates installation suitability for candidate software units as part of the production deployment pipeline; a critical or blocking finding always forces a non-conforming result regardless of overall score (VAE-04.1, 7).

##### 3.6.4.2 Design elements

**Installation Suitability Evaluator** — analyzes a software unit's suitability for target-environment installation across structural/architectural conformance, interface/topic/communication conformance, dependency/integration conformance, and resource/performance sufficiency; scores conformance per control rule (rule identifier, evaluation heading, severity, weight, acceptance criterion, blocking status). Traces to VAE-04.2–6.

**Blocking Decision Engine** — forces a "non-conforming" installation result whenever a critical-severity finding or a blocking-rule violation occurs, regardless of overall conformance score, and transmits the pipeline-blocking decision to the automation client. Traces to VAE-04.7.

**Concurrent Evaluation Orchestrator** — runs installation evaluations for one or more software units under independent operation identifiers, reporting a separate score/class/blocking-findings/decision per unit plus an aggregate result, in machine-processable format. Traces to VAE-04.8.

---

## 4. Requirements Traceability

| SRS Req ID Range | Design Element |
|---|---|
| MSD.1 | §3.1.1 MSD (CSC-wide) |
| MSD.2–8 | §3.1.2 Data Source Connector & Configuration Manager |
| MSD.9–13, 16 | §3.1.2 Configuration Data Acquisition |
| MSD.14–15 | §3.1.2 Software Unit Version Inventory Manager |
| MSD.17–20 | §3.1.2 Source Repository Ingestion |
| MSD.21–23 | §3.1.2 Data Validation & Model Setup Data Assembler |
| SCG.1, 6 | §3.2.1–2 SCG (CSC-wide) / Scenario Input Manager |
| SCG.3 | §3.2.2 Scenario Input Manager |
| SCG.2, 4 | §3.2.2 Synthetic Data Generator |
| SCG.5, 7 | §3.2.2 Scenario Output Recorder |
| FRD.1 | §3.3.1 FRD (CSC-wide) |
| FRD.2, 5 | §3.3.2 Record Upload Manager |
| FRD.3–4 | §3.3.2 Record Catalog Manager |
| ADP.1 | §3.4.1 ADP (CSC-wide) |
| ADP.2, 5 | §3.4.2 Field Record Ingestion |
| ADP.3, 6 | §3.4.2 Scenario Data Ingestion |
| ADP.4 | §3.4.2 Analytical Data Assembler |
| CSM-01.1 | §3.5.1.1 CSM-01 (CSU-wide) |
| CSM-01.2–5, 25–26 | §3.5.1.2 Model Construction Engine |
| CSM-01.6–24 | §3.5.1.2 Node-Relationship Schema Manager |
| CSM-01.27–28 | §3.5.1.2 Model Access Provider |
| CSM-01.29–30 | §3.5.1.2 Concurrency & Session Manager |
| CSM-01.31 | §3.5.1.2 Candidate Evaluation Model Builder |
| CSM-02.1, 3–5 | §3.5.2.2 Node/Relationship Matcher & Binder |
| CSM-02.2 | §3.5.2.2 Analytical Data Ingestion |
| CSM-02.6 | §3.5.2.2 Unmatched Record Reporter |
| VAE-01.1–2 | §3.6.1.1 VAE-01 (CSU-wide) |
| VAE-01.3–4 | §3.6.1.2 Session & Authentication Manager |
| VAE-01.5–9 | §3.6.1.2 Model Setup Data Workflow Manager |
| VAE-01.10–16 | §3.6.1.2 Analytical Data Workflow Manager |
| VAE-01.17 | §3.6.1.2 Working Model Editor |
| VAE-01.19–20 | §3.6.1.2 Model Visualization & Navigation UI |
| VAE-01.18, 21–26 | §3.6.1.2 Findings & Reporting Manager |
| VAE-01.27 | §3.6.1.2 Automation Interface (CLI/Build Tools) |
| VAE-02.1–3 | §3.6.2.1 VAE-02 (CSU-wide) |
| VAE-02.4, 19–21 | §3.6.2.2 Structural & Dependency Analysis Engine |
| VAE-02.5–8 | §3.6.2.2 Topic QoS Verification Engine |
| VAE-02.9–11 | §3.6.2.2 Publisher/Consumer Matcher |
| VAE-02.12 | §3.6.2.2 Communication Consistency Verifier |
| VAE-02.13–18 | §3.6.2.2 Resource Allocation Verifier |
| VAE-02.22 | §3.6.2.2 Architectural Rule Verifier |
| VAE-03.1–3 | §3.6.3.1 VAE-03 (CSU-wide) |
| VAE-03.4–9 | §3.6.3.2 Simulation Analysis Engine |
| VAE-03.10–16, 20–21 | §3.6.3.2 Field Data Analysis Engine |
| VAE-03.17–19 | §3.6.3.2 Architectural Drift Detector |
| VAE-04.1, 7 | §3.6.4.1 VAE-04 (CSU-wide) / Blocking Decision Engine |
| VAE-04.2–6 | §3.6.4.2 Installation Suitability Evaluator |
| VAE-04.8 | §3.6.4.2 Concurrent Evaluation Orchestrator |

**Coverage check:** all 156 SRS requirements appear at least once above, across all 10 CSUs. Every design element in §3 traces back to at least one SRS requirement, and every SRS requirement maps to exactly one design element.
