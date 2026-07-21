# Software Requirements Specification (SRS): System as a Graph (SaaG)

**Definition:** This Software Requirements Specification (SRS) decomposes the six Computer Software Components (CSCs) specified in the SSS into ten Computer Software Units (CSUs). SaaG is the Computer Software Configuration Item (CSCI); each CSC below is decomposed into one or more CSUs, and each requirement is scoped to exactly one CSU. Every requirement in this document is traceable to its source System/Subsystem Specification (SSS) requirement via Appendix A.

## Table 1. SRS Requirement Distribution

| No | Component | Abbreviation | Number of CSUs | Number of Requirements |
|---|---|---|---|---|
| 1 | Model Setup Data Generation | SaaG-MSD | 1 | 23 |
| 2 | Scenario Generator | SaaG-SCG | 1 | 7 |
| 3 | Field Records Database | SaaG-FRD | 1 | 5 |
| 4 | Analytical Data Preparation | SaaG-ADP | 1 | 6 |
| 5 | Node-Relationship Based Core System Model | SaaG-CSM | 2 | 37 |
| 6 | Design Verification, Analysis and Evaluation | SaaG-VAE | 4 | 78 |
| **TOTAL** | | | **10** | **156** |

Per-CSC requirement distribution tables appear under each component's own section below.

**Purpose:** This SRS translates each SSS requirement into one or more CSU-level functional requirements suitable for design and implementation. Each requirement is scoped to a single CSU and is traceable to its source SSS requirement via Appendix A.

---

## 1. Model Setup Data Generation (SaaG-MSD)

**Table 2. SaaG-MSD Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Model Setup Data Generation | MSD | 23 |
| **Subtotal** | | **23** |

### 1.1 MSD: Model Setup Data Generation

1. MSD shall ensure that the Model Setup Data underlying the creation of the Digital System Model is produced in a controlled, traceable, verifiable manner and can be transferred to model construction processes.
2. MSD shall be able to access the system configuration management database as an external data source for Model Setup Data generation, and shall manage the data obtained from it in a controlled, traceable manner.
3. MSD shall be able to access the system software units and installation scripts source code repository as an external data source for Model Setup Data generation, and shall manage the data obtained from it in a controlled, traceable manner.
4. MSD shall be able to access the System Software Units Package Repository as an external data source for Model Setup Data generation, and shall manage the data obtained from it in a controlled, traceable manner.
5. MSD shall be able to access the System Network Topology Data Source as an external data source for Model Setup Data generation, and shall manage the data obtained from it in a controlled, traceable manner.
6. MSD shall be able to obtain the system network topology data automatically from an external data source (file, database, etc.) whose details will be determined during the critical design phase.
7. MSD shall be able to obtain the system network topology data through the user manually entering the network topology parameters.
8. MSD shall manage, for each data source, the source type, source name, access method, connection address, and the user information required for connection, as user-definable and savable configuration information.
9. MSD shall carry out data acquisition operations in association with project information, platform information, and system version number.
10. MSD shall be able to obtain current project information from the configuration management database.
11. MSD shall be able to obtain platform information belonging to the selected project from the configuration management database.
12. MSD shall be able to obtain system version information belonging to the selected project and platform from the configuration management database.
13. MSD shall mark the currently effective version information within the system version information obtained from the configuration management database.
14. MSD shall record, as the "Software Unit Version Inventory," the name and version information of the software units that will run in the system environment, according to the selected project, platform, and version information.
15. MSD shall update and record the Software Unit Version Inventory using the candidate version of the software unit being evaluated for installation into the target environment, together with the other software unit versions defined in the selected system version.
16. MSD shall mark the data acquisition process with an error status upon detecting deficiency, access error, or format incompatibility in the data obtained from the configuration management database.
17. MSD shall access and transfer into the system the source code, installation scripts, and configuration files of the software units within the scope of the Software Unit Version Inventory, via the source code repository.
18. MSD shall record the file name, file path, package/version information, and update timestamp for each file obtained from the source code repository.
19. MSD shall report the data acquisition process with a "missing data" status if any of the files that are mandatory to obtain from the source code repository — whose details will be determined during the critical design phase — are missing.
20. MSD shall display and record the relevant error in the event of an access, authorization, or integrity error occurring in files obtained from the source code repository.
21. MSD shall perform a mandatory-field-presence check, within the scope of model construction, for all source data received or manually entered.
22. MSD shall record, for each piece of data that fails the mandatory-field-presence check, the error reason, source name, source type, associated project/platform information, and error time.
23. MSD shall prepare the source data that passes the verification checks for transfer to the model construction process, and shall save it as a Model Setup Data file.

---

## 2. Scenario Generator (SaaG-SCG)

**Table 3. SaaG-SCG Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Scenario Generator | SCG | 7 |
| **Subtotal** | | **7** |

### 2.1 SCG: Scenario Generator

1. SCG shall be capable of producing synthetic data based on scenario inputs determined by the user, without requiring field records.
2. SCG shall serve as the data source for all system-wide simulation processes — whose details will be determined during the critical design phase — and shall produce the synthetic data to be used in simulation processes.
3. SCG shall enable the user to determine the scenario scope, scenario type, time interval, data density, and the data types to be produced, as required for scenario generation.
4. SCG shall be able to produce synthetic data in an equivalent structure conforming to the topic/message data schema, field naming, and value range constraints used by the software units, based on user inputs.
5. SCG shall record the produced synthetic data together with the scenario name, production time, associated project information, platform information, and system version number.
6. SCG shall record, in a traceable manner, the user inputs used in the production of the synthetic data.
7. SCG shall prepare the produced synthetic data for transfer to the Analytical Data Preparation component.

---

## 3. Field Records Database (SaaG-FRD)

**Table 4. SaaG-FRD Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Field Records Database | FRD | 5 |
| **Subtotal** | | **5** |

### 3.1 FRD: Field Records Database

1. FRD shall store and manage, in a centralized manner, the system data records and telemetry data obtained via the system data recording mechanism from the platforms on which the system is installed, as "System Field Records."
2. FRD shall enable the user to upload the telemetry and system data records obtained from the system field environment in a controlled, traceable manner, and shall record the uploaded records in association with the relevant project information, platform information, and system version number.
3. FRD shall record the uploaded System Field Records, in a traceable manner, together with the record source, upload time, and the associated project, platform, and system version information.
4. FRD shall enable the user to list, search, and select the existing System Field Records according to criteria such as project, platform, system version, record source, or upload time.
5. FRD shall report and record any format incompatibility, integrity error, or missing field conditions detected during upload.

*Note: SSS-FRD.6 (storage hardware disk capacity, details TBD at critical design) is an infrastructure constraint on the platform FRD runs on, and is not restated as a CSU-level functional requirement.*

---

## 4. Analytical Data Preparation (SaaG-ADP)

**Table 5. SaaG-ADP Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Analytical Data Preparation | ADP | 6 |
| **Subtotal** | | **6** |

### 4.1 ADP: Analytical Data Preparation

1. ADP shall ensure that the Analytical Evaluation Data — to be used in analysis, verification, and simulation processes — is prepared in a controlled, traceable, verifiable manner and can be transferred to the Core System Model.
2. ADP shall be able to obtain the System Field Records to be used in preparing the Analytical Evaluation Data from the Field Records Database.
3. ADP shall be able to obtain the synthetic data produced by the Scenario Generator as data required to create the Analytical Evaluation Data.
4. ADP shall process the System Field Records or the synthetic data supplied by the Scenario Generator, associate them appropriately, and produce the Analytical Evaluation Data — whose details will be determined during the critical design phase — which shall then be transmitted to the Core System Model.
5. ADP shall report and record the detection of format incompatibility or unreadable data in the System Field Records.
6. ADP shall report and record the detection of format incompatibility, unreadable data, or missing fields in the synthetic data supplied by the Scenario Generator.

---

## 5. Node-Relationship Based Core System Model (SaaG-CSM)

**Table 6. SaaG-CSM Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Model Manager | CSM-01 | 31 |
| Analytical Data Binder | CSM-02 | 6 |
| **Subtotal** | | **37** |

### 5.1 CSM-01: Model Manager

1. CSM-01 shall use the Model Setup Data to construct the structural and relational representation of the system in a node-relationship structure, making it usable in static analysis, verification, and simulation processes.
2. CSM-01 shall be able to accept, as input, the Model Setup Data produced by the Model Setup Data Generation component.
3. CSM-01 shall perform format, schema, integrity, and mandatory field checks on the Model Setup Data before the construction of the Core System Model.
4. CSM-01 shall convert the Model Setup Data that passes the checks into a node-relationship based Core System Model.
5. CSM-01 shall create the Core System Model in association with the relevant project, platform, and system version information.
6. CSM-01 shall represent System as a node in the node-relationship structure.
7. CSM-01 shall represent Software Segment as a node in the node-relationship structure.
8. CSM-01 shall represent Computer Software Configuration Item (CSCI) as a node in the node-relationship structure.
9. CSM-01 shall represent Computer Software Component (CSC) as a node in the node-relationship structure.
10. CSM-01 shall represent Computer Software Unit (CSU) as a node in the node-relationship structure.
11. CSM-01 shall represent Role as a node in the node-relationship structure.
12. CSM-01 shall represent Topic as a node in the node-relationship structure.
13. CSM-01 shall represent Message as a node in the node-relationship structure.
14. CSM-01 shall represent Operator Console and Processor Units as nodes in the node-relationship structure.
15. CSM-01 shall represent Network components as nodes in the node-relationship structure.
16. CSM-01 shall represent Middleware Services as nodes in the node-relationship structure.
17. CSM-01 shall represent Services belonging to Communication Technologies as nodes in the node-relationship structure.
18. CSM-01 shall represent "Running on Operator Console and Processor Units" as a relationship in the node-relationship structure.
19. CSM-01 shall represent "Using Middleware and Communication Services" as a relationship in the node-relationship structure.
20. CSM-01 shall represent "Publishing data" as a relationship in the node-relationship structure.
21. CSM-01 shall represent "Consuming data" as a relationship in the node-relationship structure.
22. CSM-01 shall represent "Being dependent on a library or software unit" as a relationship in the node-relationship structure.
23. CSM-01 shall represent "Assignment of a software unit to a role" as a relationship in the node-relationship structure.
24. CSM-01 shall represent the processor core allocation (CPU allocation), operating system settings, and runtime environment configurations (JVM, etc.) belonging to the system's software units as queryable attributes on the node-relationship structure.
25. CSM-01 shall report and record missing entity and invalid relationship errors detected during the construction of the Core System Model.
26. CSM-01 shall record the Model Setup Data file used for the created Core System Model, the model creation time, project information, platform information, system version number, and model status.
27. CSM-01 shall make the Core System Model available for use by the Design Verification, Analysis and Evaluation component.
28. CSM-01 shall enable the Design Verification, Analysis and Evaluation component to access the nodes, relationships, and the Analytical Evaluation Data associated with them.
29. CSM-01 shall handle read/write operations performed concurrently by multiple user sessions on the same Core System Model without compromising model integrity or the consistency of query results.
30. CSM-01 shall execute the operations in the production deployment pipeline and the analysis and simulation operations of a number of users — to be determined during the critical design phase — concurrently and independently of one another, preventing the operations from affecting each other.
31. CSM-01 shall create a new, process-specific Core System Model using the candidate version of the software unit being evaluated for installation into the target environment, together with the other software units in the target system version.

### 5.2 CSM-02: Analytical Data Binder

1. CSM-02 shall match the Analytical Evaluation Data with the relevant system entities and the connections between them in the Core System Model, making it usable in static analysis, verification, and simulation processes.
2. CSM-02 shall be able to accept, as input, the Analytical Evaluation Data produced by the Analytical Data Preparation component.
3. CSM-02 shall associate the Analytical Evaluation Data with the relevant project, platform, system version, and Core System Model; shall match the record, telemetry, and synthetic data found in the data with the relevant nodes and relationships; and shall bind it to the node-relationship structure.
4. CSM-02 shall preserve information on whether the Analytical Evaluation Data was produced using System Field Records or synthetic data supplied by the Scenario Generator.
5. CSM-02 shall bind the Analytical Evaluation Data to the model without altering the nodes and relationships in the Core System Model, and shall ensure that the Core System Model data and the Analytical Evaluation Data are managed in a manner that keeps them separable from one another.
6. CSM-02 shall report and record any node or relationship records for which no counterpart can be found in the Analytical Evaluation Data.

---

## 6. Design Verification, Analysis and Evaluation (SaaG-VAE)

**Table 7. SaaG-VAE Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Operations Panel | VAE-01 | 27 |
| Design Verifier | VAE-02 | 22 |
| Design Analyzer | VAE-03 | 21 |
| Design Evaluator | VAE-04 | 8 |
| **Subtotal** | | **78** |

### 6.1 VAE-01: Operations Panel

1. VAE-01 shall enable the user to interact directly with the system components in support of design verification, static analysis, and evaluation operations performed by VAE-02, VAE-03, and VAE-04, and shall present the results of those operations to the user.
2. VAE-01 shall be able to interact with the Model Setup Data Generation, Scenario Generator, Analytical Data Preparation, and Core System Model components.
3. VAE-01 shall authenticate the username and password information of users wishing to access the system via a defined LDAP directory service, and shall allow only users who successfully authenticate to access the system within the scope of their authorizations.
4. VAE-01 shall enable the user to select the project, platform, and system version on which operations will be performed, and shall distinctly display the currently effective system version for the project and platform.
5. VAE-01 shall list, for the user, the Model Setup Data files belonging to the selected project, platform, and system version, and shall enable the user to select the file to be used.
6. VAE-01 shall enable the user to start the Model Setup Data production process and to monitor the status of the process as one of in progress, successful, or failed.
7. VAE-01 shall continuously and traceably display to the user the accessibility status of all data sources used.
8. VAE-01 shall display to the user the missing data, access, authorization, format, or integrity errors detected during Model Setup Data production.
9. VAE-01 shall enable the user to start the process of creating the Core System Model using the selected Model Setup Data, and to monitor the result of the operation as one of successful or failed.
10. VAE-01 shall enable the user to select System Field Records as the data source to be used for creating the Analytical Evaluation Data.
11. VAE-01 shall enable the user to select synthetic data supplied by the Scenario Generator as the data source to be used for creating the Analytical Evaluation Data.
12. VAE-01 shall enable the user to select the records to be used, in the case where System Field Records are to be used as the Analytical Evaluation Data source.
13. VAE-01 shall enable the user to determine the inputs relating to scenario scope, scenario type, time interval, data density, and the data types to be produced, in the case where synthetic data are to be used as the Analytical Evaluation Data source.
14. VAE-01 shall enable the user to start and track the synthetic data production process, and to view errors occurring during production.
15. VAE-01 shall enable the user to start and track the Analytical Evaluation Data production process, and to view errors occurring during production.
16. VAE-01 shall display to the user the project, platform, and system version information associated with the Analytical Evaluation Data bound to the Core System Model, and shall report the matching status of the record, telemetry, and synthetic data found in the data with the nodes and relationships.
17. VAE-01 shall enable the user to perform structural changes — such as adding/removing nodes, adding/removing relationships, and updating node/relationship attributes — on a working model derived from the Core System Model, without breaking its structural integrity, and shall enable design verification and analysis operations to be carried out on the updated working model.
18. VAE-01 shall classify design verification and analysis results as one of "conforming" or "non-conforming," according to rules/metrics to be determined during the critical design phase.
19. VAE-01 shall enable the user to search for a system entity or relationship on the node-relationship structure and to filter the results by type, project, platform, system version, or software unit information.
20. VAE-01 shall enable the user to perform visual zoom in, zoom out, pan, and node/relationship selection and attribute display operations on the node-relationship structure.
21. VAE-01 shall present to the user each finding detected in the analysis results together with at least the following information: finding identifier, finding type, finding description, affected system entity or relationship, related verification rule or acceptance criterion, data or evidence supporting the finding, and the severity level of the finding, expressed as one of informational, low, medium, high, or critical.
22. VAE-01 shall record and display to the user the cause-and-effect relationship between related findings detected within the scope of the same operation.
23. VAE-01 shall enable the user to sort and filter findings by operation type, evaluation result, finding type, severity level, project, platform, system version, or affected nodes.
24. VAE-01 shall record the error cause, the stage at which the operation was interrupted, and the error time occurring during a design verification, analysis, or simulation operation.
25. VAE-01 shall be able to record the scenario name, scenario inputs, data production time, and the associated project, platform, and system version information used in simulation operations.
26. VAE-01 shall generate a summary or detailed system report of design verification, analysis, and simulation results in an exportable file format whose details will be determined during the critical design phase, and shall ensure that the reports contain at least the following information: project information, platform information, system version information, the Core System Model used, the Analytical Evaluation Data used and its data source, operation identifier and operation type, operation start and end time, evaluation result, findings detected, affected nodes and relationships, severity levels, and additional information relating to the findings.
27. VAE-01 shall also accept analysis requests — made via user interfaces — through Build Automation Tools and a Command Line Interface (CLI); shall present status information on ongoing operations to users accessing the system and to automation clients (e.g., Jenkins); and shall ensure that analysis operations are carried out concurrently and independently of one another.

### 6.2 VAE-02: Design Verifier

1. VAE-02 shall perform design verification operations on the Core System Model.
2. VAE-02 shall perform design verification operations without altering the nodes and relationships in the Core System Model.
3. VAE-02 shall be able to perform analyses solely on the Core System Model without using Analytical Evaluation Data.
4. VAE-02 shall be able to perform, on the Core System Model, the analysis of structural dependencies, communication connections, and runtime environment relationships between system entities.
5. VAE-02 shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Durability parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
6. VAE-02 shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Reliability parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
7. VAE-02 shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Lifespan parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
8. VAE-02 shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Transport Priority parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
9. VAE-02 shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect a topic with no data publisher.
10. VAE-02 shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect a topic with no data consumer.
11. VAE-02 shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect topics defined with the same name having content definitions that differ from one another.
12. VAE-02 shall verify, on the Core System Model, the mutual consistency of source, destination, message, and communication direction information in external-to-middleware communications carried out via communication services to be determined during the critical design phase.
13. VAE-02 shall analyze, on the Core System Model, the conformance of the distribution of the system's software units across Operator Console and Processor Units to load balancing rules to be determined during the critical design phase.
14. VAE-02 shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect the total number of cores allocated on a Processor Unit exceeding the available core capacity.
15. VAE-02 shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect the same cores being allocated to multiple applications in a conflicting manner.
16. VAE-02 shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect applications required to run with high performance not having dedicated cores allocated to them.
17. VAE-02 shall audit, on the Core System Model, the conformance of the operating system settings running on processor/console units to rules to be determined during the critical design phase and to the processor core allocation made.
18. VAE-02 shall verify, on the Core System Model, the conformance of the memory allocation parameters in the runtime environment configurations of the system's software units to rules to be determined during the critical design phase.
19. VAE-02 shall detect, on the Core System Model, situations that could cause resource contention and bottlenecks arising from inconsistencies among processor core allocation, operating system settings, and runtime environment configurations.
20. VAE-02 shall detect circular dependencies between the system's software units on the Core System Model.
21. VAE-02 shall detect, on the Core System Model, disconnected, missing, invalid, or unmatched structural relationships between the nodes within the Core System Model.
22. VAE-02 shall detect, on the Core System Model, design patterns that violate architectural rules to be determined during the critical design phase.

### 6.3 VAE-03: Design Analyzer

1. VAE-03 shall perform static analysis operations on the Core System Model.
2. VAE-03 shall perform analysis operations without altering the nodes and relationships in the Core System Model.
3. VAE-03 shall be able to perform analyses using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
4. VAE-03 shall analyze the message flow direction, message count, data volume, and messaging frequency between nodes, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
5. VAE-03 shall be able to evaluate the effects on the Core System Model of a node or relationship becoming inactive, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
6. VAE-03 shall be able to perform design-time traffic analysis using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, and shall be able to evaluate, within the scope of the effects of load conditions created within the simulation on system entities and relationships, an increase in Topic/Message density.
7. VAE-03 shall be able to perform design-time traffic analysis using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, and shall be able to evaluate, within the scope of the effects of load conditions created within the simulation on system entities and relationships, a change in Topic/Message publishing or consumption behavior.
8. VAE-03 shall, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, determine the propagation of fault, load, communication interruption, or bandwidth-narrowing conditions created within the simulation onto dependent nodes, and shall detect the directly or indirectly affected nodes/relationships and the propagation path followed by the effect.
9. VAE-03 shall, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, determine the system entities with the highest resource usage or the most intensive messaging as a result of the simulation to be performed, and shall present these to the user as summary evaluation indicators.
10. VAE-03 shall be able to perform analyses using Analytical Evaluation Data produced from System Field Records.
11. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on operational and health status.
12. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on processor, memory, storage, and network usage values.
13. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on error, warning, restart, and timeout information.
14. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on message flow direction, message count, data volume, and messaging frequency.
15. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on communication latency, message loss, and successful transmission rates.
16. VAE-03 shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on topic publishing and consumption activities.
17. VAE-03 shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships present in the Model Setup Data but not observed in the runtime data.
18. VAE-03 shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships not present in the Model Setup Data but observed in the runtime data.
19. VAE-03 shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships showing incompatibility between the Model Setup Data and the runtime data.
20. VAE-03 shall analyze the event records associated with the nodes and relationships found in the Analytical Evaluation Data produced from System Field Records.
21. VAE-03 shall, using Analytical Evaluation Data produced from System Field Records, determine the system entities with the highest resource usage or the most intensive messaging as a result of the analysis, and shall present these to the user as summary evaluation indicators.

### 6.4 VAE-04: Design Evaluator

1. VAE-04 shall perform evaluation operations on the Core System Model, in the form of installation suitability evaluation for candidate software units.
2. VAE-04 shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of structural and architectural conformance.
3. VAE-04 shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of interface, topic, and communication conformance.
4. VAE-04 shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of dependency and integration conformance.
5. VAE-04 shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of resource and performance sufficiency.
6. VAE-04 shall define each control rule used in the installation suitability evaluation with a rule identifier, evaluation heading, severity level, weight value, acceptance criterion, and blocking status, and shall classify and score the conformance categories and scoring method belonging to the rule results in a manner whose details will be determined during the critical design phase.
7. VAE-04 shall, upon detecting a finding with a critical severity level or a violation of a control rule defined as blocking in the evaluation profile, determine the installation result for the target environment as "non-conforming" independently of the overall conformance score, and shall transmit the decision information preventing the continuation of the production deployment pipeline to the automation client.
8. VAE-04 shall execute installation suitability evaluations initiated for one or more software units within the scope of the production deployment pipeline using independent operation identifiers from one another, and shall present, for each software unit, a separate conformance score, score class, blocking findings, and installation decision, as well as the aggregate operation result, in a machine-processable format to the automation client.

---

## Appendix A: Traceability Matrix

Relationship key: **Direct** = one SSS requirement reworded to one CSU-scoped SRS requirement, unchanged in substance. **Split** = one SSS requirement's enumerated items each stated as a separate SRS requirement. **Joint** = one SSS requirement (a component charter, or a requirement whose scope spans multiple CSUs) realized by a distinct SRS requirement in each contributing CSU.

### SaaG-MSD

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| MSD.1 | MSD | SSS-MSD.1 | Direct (charter) |
| MSD.2 | MSD | SSS-MSD.2 | Split |
| MSD.3 | MSD | SSS-MSD.2 | Split |
| MSD.4 | MSD | SSS-MSD.2 | Split |
| MSD.5 | MSD | SSS-MSD.2 | Split |
| MSD.6 | MSD | SSS-MSD.3 | Split |
| MSD.7 | MSD | SSS-MSD.3 | Split |
| MSD.8 | MSD | SSS-MSD.4 | Direct |
| MSD.9 | MSD | SSS-MSD.5 | Direct |
| MSD.10 | MSD | SSS-MSD.6 | Direct |
| MSD.11 | MSD | SSS-MSD.7 | Direct |
| MSD.12 | MSD | SSS-MSD.8 | Direct |
| MSD.13 | MSD | SSS-MSD.9 | Direct |
| MSD.14 | MSD | SSS-MSD.10 | Direct |
| MSD.15 | MSD | SSS-MSD.11 | Direct |
| MSD.16 | MSD | SSS-MSD.12 | Direct |
| MSD.17 | MSD | SSS-MSD.13 | Direct |
| MSD.18 | MSD | SSS-MSD.14 | Direct |
| MSD.19 | MSD | SSS-MSD.15 | Direct |
| MSD.20 | MSD | SSS-MSD.16 | Direct |
| MSD.21 | MSD | SSS-MSD.17 | Direct |
| MSD.22 | MSD | SSS-MSD.18 | Direct |
| MSD.23 | MSD | SSS-MSD.19 | Direct |

### SaaG-SCG

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| SCG.1 | SCG | SSS-SCG.1 | Direct (charter) |
| SCG.2 | SCG | SSS-SCG.2 | Direct |
| SCG.3 | SCG | SSS-SCG.3 | Direct |
| SCG.4 | SCG | SSS-SCG.4 | Direct |
| SCG.5 | SCG | SSS-SCG.5 | Direct |
| SCG.6 | SCG | SSS-SCG.6 | Direct |
| SCG.7 | SCG | SSS-SCG.7 | Direct |

### SaaG-FRD

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| FRD.1 | FRD | SSS-FRD.1 | Direct (charter) |
| FRD.2 | FRD | SSS-FRD.2 | Direct |
| FRD.3 | FRD | SSS-FRD.3 | Direct |
| FRD.4 | FRD | SSS-FRD.4 | Direct |
| FRD.5 | FRD | SSS-FRD.5 | Direct |
| — | — | SSS-FRD.6 | Infrastructure (no CSU) |

### SaaG-ADP

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| ADP.1 | ADP | SSS-ADP.1 | Direct (charter) |
| ADP.2 | ADP | SSS-ADP.2 | Direct |
| ADP.3 | ADP | SSS-ADP.3 | Direct |
| ADP.4 | ADP | SSS-ADP.4 | Direct |
| ADP.5 | ADP | SSS-ADP.5 | Direct |
| ADP.6 | ADP | SSS-ADP.6 | Direct |

### SaaG-CSM

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| CSM-01.1 | CSM-01 | SSS-CSM.1 | Joint |
| CSM-01.2 | CSM-01 | SSS-CSM.2 | Direct |
| CSM-01.3 | CSM-01 | SSS-CSM.3 | Direct |
| CSM-01.4 | CSM-01 | SSS-CSM.4 | Direct |
| CSM-01.5 | CSM-01 | SSS-CSM.5 | Direct |
| CSM-01.6 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.7 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.8 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.9 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.10 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.11 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.12 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.13 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.14 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.15 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.16 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.17 | CSM-01 | SSS-CSM.6 | Split |
| CSM-01.18 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.19 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.20 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.21 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.22 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.23 | CSM-01 | SSS-CSM.7 | Split |
| CSM-01.24 | CSM-01 | SSS-CSM.8 | Direct |
| CSM-01.25 | CSM-01 | SSS-CSM.9 | Direct |
| CSM-01.26 | CSM-01 | SSS-CSM.15 | Direct |
| CSM-01.27 | CSM-01 | SSS-CSM.16 | Direct |
| CSM-01.28 | CSM-01 | SSS-CSM.17 | Direct |
| CSM-01.29 | CSM-01 | SSS-CSM.18 | Direct |
| CSM-01.30 | CSM-01 | SSS-CSM.19 | Direct |
| CSM-01.31 | CSM-01 | SSS-CSM.20 | Direct |
| CSM-02.1 | CSM-02 | SSS-CSM.1 | Joint |
| CSM-02.2 | CSM-02 | SSS-CSM.10 | Direct |
| CSM-02.3 | CSM-02 | SSS-CSM.11 | Direct |
| CSM-02.4 | CSM-02 | SSS-CSM.12 | Direct |
| CSM-02.5 | CSM-02 | SSS-CSM.13 | Direct |
| CSM-02.6 | CSM-02 | SSS-CSM.14 | Direct |

### SaaG-VAE

| SRS Req ID | CSU | Source SSS Req | Relationship |
|---|---|---|---|
| VAE-01.1 | VAE-01 | SSS-VAE.1 | Joint |
| VAE-01.2 | VAE-01 | SSS-VAE.2 | Direct |
| VAE-01.3 | VAE-01 | SSS-VAE.3 | Direct |
| VAE-01.4 | VAE-01 | SSS-VAE.4 | Direct |
| VAE-01.5 | VAE-01 | SSS-VAE.5 | Direct |
| VAE-01.6 | VAE-01 | SSS-VAE.6 | Direct |
| VAE-01.7 | VAE-01 | SSS-VAE.7 | Direct |
| VAE-01.8 | VAE-01 | SSS-VAE.8 | Direct |
| VAE-01.9 | VAE-01 | SSS-VAE.9 | Direct |
| VAE-01.10 | VAE-01 | SSS-VAE.10 | Split |
| VAE-01.11 | VAE-01 | SSS-VAE.10 | Split |
| VAE-01.12 | VAE-01 | SSS-VAE.11 | Direct |
| VAE-01.13 | VAE-01 | SSS-VAE.12 | Direct |
| VAE-01.14 | VAE-01 | SSS-VAE.13 | Direct |
| VAE-01.15 | VAE-01 | SSS-VAE.14 | Direct |
| VAE-01.16 | VAE-01 | SSS-VAE.16 | Direct |
| VAE-01.17 | VAE-01 | SSS-VAE.17 | Direct |
| VAE-01.18 | VAE-01 | SSS-VAE.42 | Direct |
| VAE-01.19 | VAE-01 | SSS-VAE.43 | Split |
| VAE-01.20 | VAE-01 | SSS-VAE.43 | Split |
| VAE-01.21 | VAE-01 | SSS-VAE.44 | Direct |
| VAE-01.22 | VAE-01 | SSS-VAE.45 | Direct |
| VAE-01.23 | VAE-01 | SSS-VAE.46 | Direct |
| VAE-01.24 | VAE-01 | SSS-VAE.47 | Direct |
| VAE-01.25 | VAE-01 | SSS-VAE.48 | Direct |
| VAE-01.26 | VAE-01 | SSS-VAE.49 | Direct |
| VAE-01.27 | VAE-01 | SSS-VAE.50 | Direct |
| VAE-02.1 | VAE-02 | SSS-VAE.1 | Joint |
| VAE-02.2 | VAE-02 | SSS-VAE.15 | Joint |
| VAE-02.3 | VAE-02 | SSS-VAE.18 | Direct |
| VAE-02.4 | VAE-02 | SSS-VAE.19 | Direct |
| VAE-02.5 | VAE-02 | SSS-VAE.20 | Split |
| VAE-02.6 | VAE-02 | SSS-VAE.20 | Split |
| VAE-02.7 | VAE-02 | SSS-VAE.20 | Split |
| VAE-02.8 | VAE-02 | SSS-VAE.20 | Split |
| VAE-02.9 | VAE-02 | SSS-VAE.21 | Split |
| VAE-02.10 | VAE-02 | SSS-VAE.21 | Split |
| VAE-02.11 | VAE-02 | SSS-VAE.21 | Split |
| VAE-02.12 | VAE-02 | SSS-VAE.22 | Direct |
| VAE-02.13 | VAE-02 | SSS-VAE.23 | Direct |
| VAE-02.14 | VAE-02 | SSS-VAE.24 | Split |
| VAE-02.15 | VAE-02 | SSS-VAE.24 | Split |
| VAE-02.16 | VAE-02 | SSS-VAE.24 | Split |
| VAE-02.17 | VAE-02 | SSS-VAE.25 | Direct |
| VAE-02.18 | VAE-02 | SSS-VAE.26 | Direct |
| VAE-02.19 | VAE-02 | SSS-VAE.27 | Direct |
| VAE-02.20 | VAE-02 | SSS-VAE.28 | Direct |
| VAE-02.21 | VAE-02 | SSS-VAE.29 | Direct |
| VAE-02.22 | VAE-02 | SSS-VAE.30 | Direct |
| VAE-03.1 | VAE-03 | SSS-VAE.1 | Joint |
| VAE-03.2 | VAE-03 | SSS-VAE.15 | Joint |
| VAE-03.3 | VAE-03 | SSS-VAE.31 | Direct |
| VAE-03.4 | VAE-03 | SSS-VAE.32 | Direct |
| VAE-03.5 | VAE-03 | SSS-VAE.33 | Direct |
| VAE-03.6 | VAE-03 | SSS-VAE.34 | Split |
| VAE-03.7 | VAE-03 | SSS-VAE.34 | Split |
| VAE-03.8 | VAE-03 | SSS-VAE.35 | Direct |
| VAE-03.9 | VAE-03 | SSS-VAE.36 | Direct |
| VAE-03.10 | VAE-03 | SSS-VAE.37 | Direct |
| VAE-03.11 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.12 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.13 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.14 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.15 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.16 | VAE-03 | SSS-VAE.38 | Split |
| VAE-03.17 | VAE-03 | SSS-VAE.39 | Split |
| VAE-03.18 | VAE-03 | SSS-VAE.39 | Split |
| VAE-03.19 | VAE-03 | SSS-VAE.39 | Split |
| VAE-03.20 | VAE-03 | SSS-VAE.40 | Direct |
| VAE-03.21 | VAE-03 | SSS-VAE.41 | Direct |
| VAE-04.1 | VAE-04 | SSS-VAE.1 | Joint |
| VAE-04.2 | VAE-04 | SSS-VAE.51 | Split |
| VAE-04.3 | VAE-04 | SSS-VAE.51 | Split |
| VAE-04.4 | VAE-04 | SSS-VAE.51 | Split |
| VAE-04.5 | VAE-04 | SSS-VAE.51 | Split |
| VAE-04.6 | VAE-04 | SSS-VAE.52 | Direct |
| VAE-04.7 | VAE-04 | SSS-VAE.53 | Direct |
| VAE-04.8 | VAE-04 | SSS-VAE.54 | Direct |

**Coverage check:** all 112 SSS requirements appear at least once above (111 as functional CSU requirements, 1 — SSS-FRD.6 — as a noted infrastructure constraint). Total SRS requirements: **156**.
