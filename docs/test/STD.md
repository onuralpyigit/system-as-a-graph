# Software Test Description (STD): System as a Graph (SaaG)

**Definition:** The System as a Graph (SaaG) Digital System Model is a static digital system model developed using an architectural digital twin approach, which models the structural and relational architecture of the system using a node-relationship representation, without actually running the system applications. In this model, system entities such as software units, middleware and communication services, processor/console units, topics, and messages are represented as nodes; the dependency, publishing, and consuming relationships between them are represented as relationships. The behavioral analysis dimension of the model is achieved not by running the components, but by overlaying Analytical Evaluation Data — derived from field records or the scenario generator — onto this model.

**Purpose:** This STD specifies the qualification test cases and procedures that verify the CSCI satisfies its design. Each test case corresponds one-to-one to a design element defined in SDD §3, exercises the SRS requirement(s) that design element traces to, and states an expected result. Test cases whose acceptance criteria depend on a rule set left open in the CDR state the mechanically verifiable behavior and note the open item; they do not invent thresholds the design has deliberately deferred.

**Table 1. STD Test Case Distribution**

| No | Component | Abbreviation | CSUs | Number of Test Cases |
|---|---|---|---|---|
| 1 | Model Setup Data Generation | SaaG-MSD | 1 | 5 |
| 2 | Scenario Generator | SaaG-SCG | 1 | 3 |
| 3 | Field Records Database | SaaG-FRD | 1 | 2 |
| 4 | Analytical Data Preparation | SaaG-ADP | 1 | 3 |
| 5 | Node-Relationship Based Core System Model | SaaG-CSM | 2 | 8 |
| 6 | Design Verification, Analysis and Evaluation | SaaG-VAE | 4 | 19 |
| **TOTAL** | | | **10** | **40** |

---

## 1. MSD — Model Setup Data Generation (SaaG-MSD)

**TC-MSD-01: Data Source Connector & Configuration Manager**
Traces to: MSD.2–8 / SDD §3.1.2

Procedure:
1. For each of the four external data source types (configuration management database, source code repository, package repository, network topology data source), define and save a source configuration (source type, source name, access method, connection address, credentials).
2. Verify each configuration is persisted and can be retrieved and edited.
3. For the network topology data source, select automatic acquisition and verify the system attempts retrieval from the configured external source.
4. For the network topology data source, select manual entry and enter network topology parameters directly.

Expected Result: All four data source types accept and persist configuration; both automatic and manual network topology acquisition methods are available and operate without error.

**TC-MSD-02: Configuration Data Acquisition**
Traces to: MSD.9–13, 16 / SDD §3.1.2

Procedure:
1. Select a project and acquire current project information from the configuration management database.
2. Select a platform under that project and acquire platform information.
3. Acquire system version information for the selected project/platform, and verify the currently effective version is marked among the returned versions.
4. Simulate a data deficiency, an access error, and a format incompatibility from the configuration management database, one at a time, and verify each condition marks the acquisition process with an error status.

Expected Result: Project/platform/version information is retrieved with the effective version marked; each injected fault condition results in an error-status acquisition process.

**TC-MSD-03: Software Unit Version Inventory Manager**
Traces to: MSD.14–15 / SDD §3.1.2

Procedure:
1. For a selected project/platform/version, record the Software Unit Version Inventory (software unit name and version).
2. Submit a candidate software unit version for installation evaluation.
3. Verify the candidate version is recorded alongside the other already-defined software unit versions in the selected system version, without displacing them.

Expected Result: The inventory correctly records baseline software unit versions and appends the candidate version without altering existing entries.

**TC-MSD-04: Source Repository Ingestion**
Traces to: MSD.17–20 / SDD §3.1.2

Procedure:
1. Trigger transfer of source code, installation scripts, and configuration files for the Software Unit Version Inventory's software units from the source code repository.
2. Verify file name, file path, package/version, and update timestamp are recorded per transferred file.
3. Remove a mandatory file from the source repository and re-run the transfer; verify the process reports "missing data" status.
4. Inject an access error, an authorization error, and an integrity error on obtained files, one at a time, and verify each is displayed and recorded.

Expected Result: Files transfer with correct metadata recorded; a missing mandatory file yields "missing data" status; access, authorization, and integrity errors are displayed and recorded.

**TC-MSD-05: Data Validation & Model Setup Data Assembler**
Traces to: MSD.21–23 / SDD §3.1.2

Procedure:
1. Submit a full set of source data (received and manually entered) with all mandatory fields present, and verify it passes the mandatory-field-presence check.
2. Submit source data missing a mandatory field, and verify the failure records error reason, source name/type, project/platform association, and error time.
3. Verify that only the data passing verification is assembled into the Model Setup Data file and prepared for transfer via INT-IF-01.

Expected Result: Valid data assembles into a single Model Setup Data file; invalid data is excluded and its failure fully recorded with all four required attributes.

---

## 2. SCG — Scenario Generator (SaaG-SCG)

**TC-SCG-01: Scenario Input Manager**
Traces to: SCG.3, 6 / SDD §3.2.2

Procedure:
1. Enter scenario scope, scenario type, time interval, data density, and the data types to be produced.
2. Save the scenario inputs and verify they are traceably recorded and associated with the resulting data.

Expected Result: All five scenario input categories are captured and traceably recorded.

**TC-SCG-02: Synthetic Data Generator**
Traces to: SCG.2, 4 / SDD §3.2.2

Procedure:
1. Using the scenario inputs from TC-SCG-01, trigger synthetic data production.
2. Verify the produced data is structurally equivalent to the topic/message schema, field naming, and value-range constraints used by the actual software units.
3. Verify the synthetic data is usable as the data source for a system-wide simulation process.

Expected Result: Synthetic data conforms structurally to the real topic/message schema and is consumable by simulation processes.

**TC-SCG-03: Scenario Output Recorder**
Traces to: SCG.5, 7 / SDD §3.2.2

Procedure:
1. After synthetic data production, verify the output is recorded together with scenario name, production time, and project/platform/system-version association.
2. Verify the recorded output is prepared and available for transfer via INT-IF-02 to ADP.

Expected Result: Produced synthetic data is fully attributed and handed off to ADP without loss of scenario metadata.

---

## 3. FRD — Field Records Database (SaaG-FRD)

**TC-FRD-01: Record Upload Manager**
Traces to: FRD.2, 5 / SDD §3.3.2

Procedure:
1. Upload a valid telemetry/system data record associated with a project/platform/system-version, and verify it is accepted and recorded in a controlled, traceable manner.
2. Upload a record with an incompatible format, one with integrity errors, and one with missing fields, in three separate attempts, and verify each is detected and reported at upload time.

Expected Result: Valid uploads succeed and associate correctly; each malformed upload variant is detected and reported without being silently accepted.

**TC-FRD-02: Record Catalog Manager**
Traces to: FRD.3–4 / SDD §3.3.2

Procedure:
1. Verify each uploaded System Field Record is cataloged with source, upload time, and project/platform/version association.
2. List, search, and select existing records by project, platform, system version, record source, and upload time, in five separate queries.

Expected Result: Every uploaded record is cataloged with the required attributes and is retrievable through all five search criteria.

---

## 4. ADP — Analytical Data Preparation (SaaG-ADP)

**TC-ADP-01: Field Record Ingestion**
Traces to: ADP.2, 5 / SDD §3.4.2

Procedure:
1. Obtain System Field Records from FRD for Analytical Evaluation Data production.
2. Submit a field record with an incompatible format and one that is unreadable, and verify both are detected and reported.

Expected Result: Valid field records are ingested successfully; incompatible or unreadable records are detected and reported without halting the ingestion path.

**TC-ADP-02: Scenario Data Ingestion**
Traces to: ADP.3, 6 / SDD §3.4.2

Procedure:
1. Obtain synthetic data from SCG for Analytical Evaluation Data production.
2. Submit synthetic data with an incompatible format, data that is unreadable, and data with missing fields, in three separate attempts, and verify each condition is detected and reported.

Expected Result: Valid synthetic data is ingested successfully; each malformed variant is detected and reported.

**TC-ADP-03: Analytical Data Assembler**
Traces to: ADP.4 / SDD §3.4.2

Procedure:
1. Using ingested field records (TC-ADP-01), produce Analytical Evaluation Data and verify it is transmitted via INT-IF-04 to CSM-02.
2. Using ingested synthetic data (TC-ADP-02), independently produce Analytical Evaluation Data and verify the same handoff.
3. Verify the two runs never combine field-record and synthetic data within a single Analytical Evaluation Data set.

Expected Result: Analytical Evaluation Data is correctly assembled and handed off for both upstream sources, and the two sources are never mixed in one production run. Analytical Evaluation Data format/content details are pending resolution of CDR-12; this test case verifies successful assembly and handoff, not the internal schema.

---

## 5. Node-Relationship Based Core System Model (SaaG-CSM)

### 5.1 CSM-01: Model Manager

**TC-CSM01-01: Model Construction Engine**
Traces to: CSM-01.2–5, 25–26 / SDD §3.5.1.2

Procedure:
1. Submit a valid Model Setup Data file (TC-MSD-05) via INT-IF-01, and verify format, schema, integrity, and mandatory-field checks run before model construction.
2. Verify the checked data converts into a node-relationship Core System Model associated with the correct project/platform/system version.
3. Submit a Model Setup Data file with a missing entity and one with an invalid relationship, in two separate attempts, and verify each is reported as an error.
4. Verify the Model Setup Data file used, creation time, and model status are recorded against the created model.

Expected Result: A valid Model Setup Data file produces a correctly-associated Core System Model with full construction metadata recorded; missing-entity and invalid-relationship conditions are detected and reported.

**TC-CSM01-02: Node-Relationship Schema Manager**
Traces to: CSM-01.6–24 / SDD §3.5.1.2

Procedure:
1. Verify the Core System Model can represent each of the 12 node types: System, Software Segment, CSCI, CSC, CSU, Role, Topic, Message, Operator Console/Processor Units, Network components, Middleware Services, Communication Technology services.
2. Verify the model can represent each of the 6 relationship types: runs-on, uses-middleware/communication-service, publishes, consumes, depends-on, assigned-to-role.
3. Verify CPU allocation, OS settings, and runtime environment configuration are exposed as queryable attributes on relevant nodes.

Expected Result: All 12 node types, all 6 relationship types, and the three attribute categories are representable and queryable in the Core System Model.

**TC-CSM01-03: Model Access Provider**
Traces to: CSM-01.27–28 / SDD §3.5.1.2

Procedure:
1. From a VAE component, request read access to the Core System Model via INT-IF-05.
2. Request read access to the nodes, relationships, and their bound Analytical Evaluation Data.

Expected Result: VAE can read the Core System Model and its bound Analytical Evaluation Data via INT-IF-05, without write access.

**TC-CSM01-04: Concurrency & Session Manager**
Traces to: CSM-01.29–30 / SDD §3.5.1.2

Procedure:
1. Open two concurrent user sessions against the same Core System Model and perform simultaneous read/write operations from each; verify model integrity and query-result consistency are preserved.
2. Concurrently trigger a production-pipeline operation and a user analysis/simulation operation against the same model, and verify both execute independently without affecting each other's results.

Expected Result: Concurrent multi-session read/write and concurrent pipeline/analysis operations complete without integrity loss or cross-interference. The specific concurrent user/operation count is pending resolution of CDR-16; this test case verifies correctness under concurrency, not a specific load target.

**TC-CSM01-05: Candidate Evaluation Model Builder**
Traces to: CSM-01.31 / SDD §3.5.1.2

Procedure:
1. Submit a candidate software unit version for installation evaluation, and verify a new, process-specific Core System Model is created combining the candidate with the other software units of the target system version.
2. Run two candidate evaluations concurrently and verify each produces an isolated model unaffected by the other.

Expected Result: Each candidate evaluation produces its own isolated Core System Model; concurrent evaluations do not interfere with one another.

### 5.2 CSM-02: Analytical Data Binder

**TC-CSM02-01: Analytical Data Ingestion**
Traces to: CSM-02.2 / SDD §3.5.2.2

Procedure:
1. Submit Analytical Evaluation Data produced by ADP (TC-ADP-03) via INT-IF-04, and verify CSM-02 accepts it as input for binding.

Expected Result: Analytical Evaluation Data from ADP is accepted via INT-IF-04.

**TC-CSM02-02: Node/Relationship Matcher & Binder**
Traces to: CSM-02.1, 3–5 / SDD §3.5.2.2

Procedure:
1. Bind the ingested Analytical Evaluation Data to the Core System Model built in TC-CSM01-01, associating it with the correct project/platform/system version/model.
2. Verify record, telemetry, and synthetic data entries are matched to their corresponding nodes and relationships.
3. Verify the upstream source (field vs. synthetic) is preserved on the bound data.
4. Verify the Core System Model's own nodes and relationships are unchanged after binding, i.e. the structural and behavioral layers remain separable.

Expected Result: Analytical Evaluation Data is correctly matched and bound with provenance preserved, and the Core System Model itself is left unaltered.

**TC-CSM02-03: Unmatched Record Reporter**
Traces to: CSM-02.6 / SDD §3.5.2.2

Procedure:
1. Bind Analytical Evaluation Data containing at least one record with no corresponding node/relationship in the Core System Model, and verify the unmatched record is reported.

Expected Result: Every node or relationship record lacking an Analytical Evaluation Data counterpart is reported.

---

## 6. Design Verification, Analysis and Evaluation (SaaG-VAE)

### 6.1 VAE-01: Operations Panel

**TC-VAE01-01: Session & Authentication Manager**
Traces to: VAE-01.3–4 / SDD §3.6.1.2

Procedure:
1. Authenticate with valid LDAP credentials and verify access is granted within the user's authorizations.
2. Authenticate with invalid credentials and verify access is denied.
3. Select a project/platform/system version and verify the currently effective version is distinctly displayed.

Expected Result: Only successfully-authenticated users gain access within their authorization scope; the effective version is clearly indicated after selection.

**TC-VAE01-02: Model Setup Data Workflow Manager**
Traces to: VAE-01.5–9 / SDD §3.6.1.2

Procedure:
1. List Model Setup Data files for a selected project/platform/version and select one.
2. Start Model Setup Data production and monitor status through in-progress, successful, and (via an injected fault) failed outcomes.
3. Verify data-source accessibility status is continuously displayed.
4. Inject a missing-data, access, authorization, format, and integrity error, one at a time, and verify each is displayed to the user.
5. Start Core System Model creation from the selected Model Setup Data file and monitor the successful/failed result.

Expected Result: The full Model Setup Data production and Core System Model creation workflow is monitorable end-to-end, with data-source status and all five error categories visible to the user.

**TC-VAE01-03: Analytical Data Workflow Manager**
Traces to: VAE-01.10–16 / SDD §3.6.1.2

Procedure:
1. Select System Field Records as the Analytical Evaluation Data source and select specific records.
2. Select synthetic data (SCG) as the source instead, and enter scenario scope/type/interval/density/data-types inputs.
3. Start and track synthetic data production, viewing any errors.
4. Start and track Analytical Evaluation Data production from each source, viewing any errors.
5. Verify the resulting project/platform/system-version association and the CSM-02 matching/binding status are displayed.

Expected Result: Both Analytical Evaluation Data source paths (field records, synthetic) are selectable, trackable end-to-end with error visibility, and their binding status is displayed.

**TC-VAE01-04: Working Model Editor**
Traces to: VAE-01.17 / SDD §3.6.1.2

Procedure:
1. Derive a working model from the Core System Model.
2. Add a node, remove a relationship, and update a node attribute on the working model, and verify the Core System Model itself remains unchanged.
3. Run a VAE-02 verification operation against the updated working model instead of the Core System Model.

Expected Result: Structural edits apply only to the working model, preserve its structural integrity, and are usable as the input to downstream verification/analysis operations.

**TC-VAE01-05: Model Visualization & Navigation UI**
Traces to: VAE-01.19–20 / SDD §3.6.1.2

Procedure:
1. Search for a system entity/relationship on the node-relationship structure.
2. Filter results by type, project, platform, system version, and software unit, in five separate filters.
3. Perform zoom in, zoom out, pan, node/relationship selection, and attribute display operations.

Expected Result: Search, all five filter dimensions, and all visual navigation operations function correctly against the displayed model.

**TC-VAE01-06: Findings & Reporting Manager**
Traces to: VAE-01.18, 21–26 / SDD §3.6.1.2

Procedure:
1. Run a verification/analysis operation and verify each finding is classified as conforming or non-conforming.
2. Verify each finding is presented with identifier, type, description, affected entity/relationship, related rule/acceptance criterion, supporting evidence, and severity (informational/low/medium/high/critical).
3. Verify cause-and-effect relationships between findings from the same operation are recorded and displayed.
4. Sort and filter findings by operation type, evaluation result, finding type, severity, project, platform, system version, and affected nodes.
5. Interrupt an operation mid-run and verify error cause, interruption stage, and error time are recorded.
6. Run a simulation and verify scenario name, inputs, production time, and project/platform/version are recorded.
7. Generate a summary report and a detailed report and verify each contains all fields listed in VAE-01.26.

Expected Result: Findings are classified, fully attributed, sortable/filterable, and cause-and-effect linked; interruption and simulation metadata are recorded; both report types contain all required fields. Conforming/non-conforming classification rules (CDR-08) and the exportable report file format (CDR-13) are pending resolution; this test case verifies presence and structure of the required data, not specific thresholds or file format.

**TC-VAE01-07: Automation Interface (CLI/Build Tools)**
Traces to: VAE-01.27 / SDD §3.6.1.2

Procedure:
1. Submit an analysis request from the CLI and, separately, from a Build Automation Tool client via EXT-IF-07.
2. Verify ongoing-operation status is visible to both an interactive user and the automation client.
3. Submit two analysis requests concurrently and verify they execute independently without interfering with each other.

Expected Result: Both automation entry points can submit requests and observe status; concurrent requests do not interfere with one another.

### 6.2 VAE-02: Design Verifier

**TC-VAE02-01: Structural & Dependency Analysis Engine**
Traces to: VAE-02.4, 19–21 / SDD §3.6.2.2

Procedure:
1. Run structural dependency, communication-connection, and runtime-environment relationship analysis on a Core System Model.
2. Introduce a resource-contention condition and a circular dependency into a test model, and verify both are detected.
3. Introduce a disconnected, a missing, an invalid, and an unmatched structural relationship, in four separate cases, and verify each is detected.

Expected Result: All analyzed relationship types are examined, and all six injected fault conditions are correctly detected.

**TC-VAE02-02: Topic QoS Verification Engine**
Traces to: VAE-02.5–8 / SDD §3.6.2.2

Procedure:
1. Configure topics with Durability, Reliability, Lifespan, and Transport Priority QoS parameters, including at least one non-conformant value per parameter.
2. Run QoS verification and verify each of the four parameters is checked and incompatibilities detected.

Expected Result: All four QoS parameters are verified and non-conformant values flagged. Conformance rules for each parameter are pending resolution of CDR-01; this test case verifies that verification runs and reports against whatever rule set is configured, not specific pass/fail thresholds.

**TC-VAE02-03: Publisher/Consumer Matcher**
Traces to: VAE-02.9–11 / SDD §3.6.2.2

Procedure:
1. Define a topic with no publisher and verify it is detected.
2. Define a topic with no consumer and verify it is detected.
3. Define two same-named topics with differing content definitions and verify the conflict is detected.

Expected Result: All three publisher/consumer mismatch conditions are detected.

**TC-VAE02-04: Communication Consistency Verifier**
Traces to: VAE-02.12 / SDD §3.6.2.2

Procedure:
1. Configure an external-to-middleware communication with consistent source, destination, message, and direction information, and verify it passes.
2. Configure the same communication with one inconsistent attribute (e.g. mismatched direction), and verify it is flagged.

Expected Result: Consistent communications pass; inconsistent ones are flagged. Which communication services are in scope is pending resolution of CDR-02; this test case exercises the verification mechanism against the currently configured service set.

**TC-VAE02-05: Resource Allocation Verifier**
Traces to: VAE-02.13–18 / SDD §3.6.2.2

Procedure:
1. Analyze software-unit load-balancing distribution across processor/console units.
2. Configure core allocation exceeding available capacity, and verify detection.
3. Configure the same cores allocated to conflicting applications, and verify detection.
4. Configure a high-performance application without dedicated cores, and verify detection.
5. Audit OS settings against the core allocation.
6. Configure a non-conformant runtime environment memory allocation, and verify detection.

Expected Result: Load-balancing distribution is analyzed and all core-allocation, OS-settings, and memory-allocation conditions are correctly detected. Load-balancing, core-allocation, OS-settings, and memory-allocation conformance rules are pending resolution of CDR-03, CDR-04, CDR-05, and CDR-06; this test case verifies detection mechanics against whatever rule set is configured.

**TC-VAE02-06: Architectural Rule Verifier**
Traces to: VAE-02.22 / SDD §3.6.2.2

Procedure:
1. Construct a model containing a known architectural-rule-violating design pattern.
2. Run architectural rule verification and verify the violation is detected.

Expected Result: The configured architectural-rule violation is detected. Architectural rules are pending resolution of CDR-07; this test case verifies detection against whatever rule set is configured.

### 6.3 VAE-03: Design Analyzer

**TC-VAE03-01: Simulation Analysis Engine**
Traces to: VAE-03.4–9 / SDD §3.6.3.2

Procedure:
1. Using synthetic-sourced Analytical Evaluation Data, analyze message flow direction, count, volume, and frequency between nodes.
2. Deactivate a node/relationship in simulation and verify the effect on the model is evaluated.
3. Increase Topic/Message density in the scenario and verify the traffic-analysis effect is evaluated.
4. Change publish/consume behavior in the scenario and verify the effect is evaluated.
5. Inject a fault, a load, a communication-interruption, and a bandwidth-narrowing condition, in four separate runs, and verify propagation to dependent nodes, affected nodes/relationships, and propagation path are all determined.
6. Verify the highest-resource-usage/most-intensive-messaging entities are presented as summary indicators.

Expected Result: All listed simulation analyses run correctly against synthetic-sourced data and produce the specified outputs.

**TC-VAE03-02: Field Data Analysis Engine**
Traces to: VAE-03.10–16, 20–21 / SDD §3.6.3.2

Procedure:
1. Using field-record-sourced Analytical Evaluation Data, analyze operational/health status.
2. Analyze processor/memory/storage/network usage values.
3. Analyze error/warning/restart/timeout information.
4. Analyze message flow direction, count, volume, and frequency.
5. Analyze communication latency, message loss, and successful-transmission rates.
6. Analyze topic publish/consume activity.
7. Analyze event records associated with nodes/relationships.
8. Verify the highest-resource-usage/most-intensive-messaging entities are presented as summary indicators.

Expected Result: All listed field-data analyses run correctly and produce the specified outputs.

**TC-VAE03-03: Architectural Drift Detector**
Traces to: VAE-03.17–19 / SDD §3.6.3.2

Procedure:
1. Compare Model Setup Data nodes/relationships against field-record-sourced runtime observations.
2. Construct a case where an entity is present in the Model Setup Data but not observed at runtime, and verify detection.
3. Construct a case where an entity is observed at runtime but not present in the Model Setup Data, and verify detection.
4. Construct a case where an entity is present in both but incompatible between them, and verify detection.

Expected Result: All three drift categories are correctly detected.

### 6.4 VAE-04: Design Evaluator

**TC-VAE04-01: Installation Suitability Evaluator**
Traces to: VAE-04.2–6 / SDD §3.6.4.2

Procedure:
1. Submit a candidate software unit for installation suitability evaluation.
2. Verify it is analyzed under all four evaluation headings: structural/architectural conformance, interface/topic/communication conformance, dependency/integration conformance, resource/performance sufficiency.
3. Verify each control rule result carries a rule identifier, evaluation heading, severity, weight, acceptance criterion, and blocking status.
4. Verify a conformance score is produced from the scored rule results.

Expected Result: All four evaluation headings are assessed with fully-attributed rule results and an overall conformance score. Scoring method details are pending resolution of CDR-14; this test case verifies that scoring is produced and rule attribution is complete, not a specific scoring formula.

**TC-VAE04-02: Blocking Decision Engine**
Traces to: VAE-04.7 / SDD §3.6.4.2

Procedure:
1. Construct an evaluation with a critical-severity finding but a high overall conformance score, and verify the installation result is forced to "non-conforming."
2. Construct an evaluation with a violated blocking-rule but no critical finding, and verify the same forced "non-conforming" outcome.
3. Verify the blocking decision is transmitted to the automation client.

Expected Result: A critical finding or blocking-rule violation always forces "non-conforming" regardless of score, and the decision reaches the automation client.

**TC-VAE04-03: Concurrent Evaluation Orchestrator**
Traces to: VAE-04.8 / SDD §3.6.4.2

Procedure:
1. Submit installation suitability evaluations for three software units concurrently, each under an independent operation identifier.
2. Verify each unit receives a separate score, score class, blocking findings, and installation decision.
3. Verify an aggregate result across all three is produced.
4. Verify all results are delivered to the automation client in machine-processable format.

Expected Result: Concurrent multi-unit evaluation produces correctly-isolated per-unit results plus an aggregate, all machine-processable.

---

## 7. Requirements Traceability

| Test Case | Design Element | SRS Req ID Range |
|---|---|---|
| TC-MSD-01 | Data Source Connector & Configuration Manager | MSD.2–8 |
| TC-MSD-02 | Configuration Data Acquisition | MSD.9–13, 16 |
| TC-MSD-03 | Software Unit Version Inventory Manager | MSD.14–15 |
| TC-MSD-04 | Source Repository Ingestion | MSD.17–20 |
| TC-MSD-05 | Data Validation & Model Setup Data Assembler | MSD.21–23 |
| TC-SCG-01 | Scenario Input Manager | SCG.3, 6 |
| TC-SCG-02 | Synthetic Data Generator | SCG.2, 4 |
| TC-SCG-03 | Scenario Output Recorder | SCG.5, 7 |
| TC-FRD-01 | Record Upload Manager | FRD.2, 5 |
| TC-FRD-02 | Record Catalog Manager | FRD.3–4 |
| TC-ADP-01 | Field Record Ingestion | ADP.2, 5 |
| TC-ADP-02 | Scenario Data Ingestion | ADP.3, 6 |
| TC-ADP-03 | Analytical Data Assembler | ADP.4 |
| TC-CSM01-01 | Model Construction Engine | CSM-01.2–5, 25–26 |
| TC-CSM01-02 | Node-Relationship Schema Manager | CSM-01.6–24 |
| TC-CSM01-03 | Model Access Provider | CSM-01.27–28 |
| TC-CSM01-04 | Concurrency & Session Manager | CSM-01.29–30 |
| TC-CSM01-05 | Candidate Evaluation Model Builder | CSM-01.31 |
| TC-CSM02-01 | Analytical Data Ingestion | CSM-02.2 |
| TC-CSM02-02 | Node/Relationship Matcher & Binder | CSM-02.1, 3–5 |
| TC-CSM02-03 | Unmatched Record Reporter | CSM-02.6 |
| TC-VAE01-01 | Session & Authentication Manager | VAE-01.3–4 |
| TC-VAE01-02 | Model Setup Data Workflow Manager | VAE-01.5–9 |
| TC-VAE01-03 | Analytical Data Workflow Manager | VAE-01.10–16 |
| TC-VAE01-04 | Working Model Editor | VAE-01.17 |
| TC-VAE01-05 | Model Visualization & Navigation UI | VAE-01.19–20 |
| TC-VAE01-06 | Findings & Reporting Manager | VAE-01.18, 21–26 |
| TC-VAE01-07 | Automation Interface (CLI/Build Tools) | VAE-01.27 |
| TC-VAE02-01 | Structural & Dependency Analysis Engine | VAE-02.4, 19–21 |
| TC-VAE02-02 | Topic QoS Verification Engine | VAE-02.5–8 |
| TC-VAE02-03 | Publisher/Consumer Matcher | VAE-02.9–11 |
| TC-VAE02-04 | Communication Consistency Verifier | VAE-02.12 |
| TC-VAE02-05 | Resource Allocation Verifier | VAE-02.13–18 |
| TC-VAE02-06 | Architectural Rule Verifier | VAE-02.22 |
| TC-VAE03-01 | Simulation Analysis Engine | VAE-03.4–9 |
| TC-VAE03-02 | Field Data Analysis Engine | VAE-03.10–16, 20–21 |
| TC-VAE03-03 | Architectural Drift Detector | VAE-03.17–19 |
| TC-VAE04-01 | Installation Suitability Evaluator | VAE-04.2–6 |
| TC-VAE04-02 | Blocking Decision Engine | VAE-04.7 |
| TC-VAE04-03 | Concurrent Evaluation Orchestrator | VAE-04.8 |

**Coverage check:** all 40 SDD §3 design elements have exactly one test case above, and all 156 SRS requirements are covered through their owning design element, consistent with SDD §4. Test cases TC-ADP-03, TC-CSM01-04, TC-VAE01-06, TC-VAE02-02, TC-VAE02-04, TC-VAE02-05, TC-VAE02-06, and TC-VAE04-01 carry acceptance criteria pending CDR-01 through CDR-08, CDR-12, CDR-14, and CDR-16 resolution (see the CDR).
