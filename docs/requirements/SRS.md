# Software Requirements Specification (SRS): System as a Graph (SaaG)

**Definition:** The System as a Graph (SaaG) Digital System Model is a static digital system model developed using an architectural digital twin approach, which models the structural and relational architecture of the system using a node-relationship representation, without actually running the system applications. In this model, system entities such as software units, middleware and communication services, processor/console units, topics, and messages are represented as nodes; the dependency, publishing, and consuming relationships between them are represented as relationships. The behavioral analysis dimension of the model is achieved not by running the components, but by overlaying Analytical Evaluation Data — derived from field records or the scenario generator — onto this model.

SaaG is the Computer Software Configuration Item (CSCI). This Software Requirements Specification (SRS) establishes a strictly one-to-one (1:1) mapping between Computer Software Components (CSCs) and Computer Software Units (CSUs), decomposing the system into six CSCs and six CSUs. Each functional requirement is scoped to exactly one CSU, and the infrastructure constraints governing the platform environment are formally incorporated.

**Purpose:** The primary purpose of the model is architectural verification. Within this scope, structural/circular dependencies, publisher/consumer matches, the conformance of topic quality-of-service (QoS) parameters, the capacity conformance of hardware present in the system (CPU core count, RAM size, network bandwidth, etc.), and design patterns that violate architectural rules are statically audited at the design stage. Architectural verification also covers the detection of deviations (architectural drift) between the architecture envisioned in the design and the runtime structure observed in field data. In addition to architectural verification, the model allows for hypothetical scenario analyses; without breaking structural integrity, the user can create experimental design constructs by adding/removing nodes/relationships or changing attributes. In these hypothetical scenarios, the propagation of situations such as an entity becoming inactive, an increase in message density, or a narrowing of bandwidth to dependent entities, and their effects on the architecture, are evaluated analytically. Furthermore, the model provides an automated evaluation mechanism for production deployment pipelines to verify candidate software unit suitability prior to target environment installation. Thus, the Digital System Model provides a repeatable verification environment aimed at predicting the architectural consequences of design decisions and changes before software units are installed in the target environment.

**Table 1. SRS Requirement Distribution**

| No | Component | Abbreviation | Number of CSUs | CSU ID | Number of Requirements |
|---|---|---|---|---|---|
| 1 | Model Setup Generator | SaaG-MSD | 1 | MSD | 23 |
| 2 | Scenario Generator | SaaG-SCG | 1 | SCG | 7 |
| 3 | Telemetry Data Manager | SaaG-FRD | 1 | FRD | 5 (+ 1 Infrastructure) |
| 4 | Analytical Data Manager | SaaG-ADP | 1 | ADP | 6 |
| 5 | Core System Model | SaaG-CSM | 1 | CSM | 37 |
| 6 | Design Verification Engine | SaaG-VAE | 1 | VAE | 78 |
| **TOTAL** | | | **6** | | **156 (+ 1 Infrastructure)** |

Per-CSC requirement distribution tables appear under each component's own section below. Every requirement in this document is traceable to its source baseline system capability requirement via §7.

---

## 1. Model Setup Generator (SaaG-MSD)

**Table 2. SaaG-MSD Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Model Setup Generator | MSD | 23 |
| **Subtotal** | | **23** |

### 1.1 MSD: Model Setup Generator

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
7. SCG shall prepare the produced synthetic data for transfer to the Analytical Data Manager component.

---

## 3. Telemetry Data Manager (SaaG-FRD)

**Table 4. SaaG-FRD Requirement Distribution**

| CSU / Element | Identifier | Type | Number of Requirements |
|---|---|---|---|
| Telemetry Data Manager | FRD | Functional | 5 |
| Storage Platform Environment | FRD-INF | Infrastructure | 1 |
| **Subtotal** | | | **6** |

### 3.1 FRD: Telemetry Data Manager

1. FRD shall store and manage, in a centralized manner, the system data records and telemetry data obtained via the system data recording mechanism from the platforms on which the system is installed, as "System Field Records."
2. FRD shall enable the user to upload the telemetry and system data records obtained from the system field environment in a controlled, traceable manner, and shall record the uploaded records in association with the relevant project information, platform information, and system version number.
3. FRD shall record the uploaded System Field Records, in a traceable manner, together with the record source, upload time, and the associated project, platform, and system version information.
4. FRD shall enable the user to list, search, and select the existing System Field Records according to criteria such as project, platform, system version, record source, or upload time.
5. FRD shall report and record any format incompatibility, integrity error, or missing field conditions detected during upload.

### 3.2 Infrastructure and Platform Constraints

1. **FRD-INF.1:** FRD shall operate on storage hardware with a disk capacity whose sizing and specifications will be determined during the critical design phase.

---

## 4. Analytical Data Manager (SaaG-ADP)

**Table 5. SaaG-ADP Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Analytical Data Manager | ADP | 6 |
| **Subtotal** | | **6** |

### 4.1 ADP: Analytical Data Manager

1. ADP shall ensure that the Analytical Evaluation Data — to be used in analysis, verification, and simulation processes — is prepared in a controlled, traceable, verifiable manner and can be transferred to the Core System Model.
2. ADP shall be able to obtain the System Field Records to be used in preparing the Analytical Evaluation Data from the Telemetry Data Manager.
3. ADP shall be able to obtain the synthetic data produced by the Scenario Generator as data required to create the Analytical Evaluation Data.
4. ADP shall process the System Field Records or the synthetic data supplied by the Scenario Generator, associate them appropriately, and produce the Analytical Evaluation Data — whose details will be determined during the critical design phase — which shall then be transmitted to the Core System Model.
5. ADP shall report and record the detection of format incompatibility or unreadable data in the System Field Records.
6. ADP shall report and record the detection of format incompatibility, unreadable data, or missing fields in the synthetic data supplied by the Scenario Generator.

---

## 5. Core System Model (SaaG-CSM)

**Table 6. SaaG-CSM Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Core System Model | CSM | 37 |
| **Subtotal** | | **37** |

### 5.1 CSM: Core System Model

#### 5.1.1 Structural Graph Construction and Management

1. CSM shall use the Model Setup Data to construct the structural and relational representation of the system in a node-relationship structure, making it usable in static analysis, verification, and simulation processes.
2. CSM shall be able to accept, as input, the Model Setup Data produced by the Model Setup Generator component.
3. CSM shall perform format, schema, integrity, and mandatory field checks on the Model Setup Data before the construction of the Core System Model.
4. CSM shall convert the Model Setup Data that passes the checks into a node-relationship based Core System Model.
5. CSM shall create the Core System Model in association with the relevant project, platform, and system version information.
6. CSM shall represent System as a node in the node-relationship structure.
7. CSM shall represent Software Segment as a node in the node-relationship structure.
8. CSM shall represent Computer Software Configuration Item (CSCI) as a node in the node-relationship structure.
9. CSM shall represent Computer Software Component (CSC) as a node in the node-relationship structure.
10. CSM shall represent Computer Software Unit (CSU) as a node in the node-relationship structure.
11. CSM shall represent Role as a node in the node-relationship structure.
12. CSM shall represent Topic as a node in the node-relationship structure.
13. CSM shall represent Message as a node in the node-relationship structure.
14. CSM shall represent Operator Console and Processor Units as nodes in the node-relationship structure.
15. CSM shall represent Network components as nodes in the node-relationship structure.
16. CSM shall represent Middleware Services as nodes in the node-relationship structure.
17. CSM shall represent Services belonging to Communication Technologies as nodes in the node-relationship structure.
18. CSM shall represent "Running on Operator Console and Processor Units" as a relationship in the node-relationship structure.
19. CSM shall represent "Using Middleware and Communication Services" as a relationship in the node-relationship structure.
20. CSM shall represent "Publishing data" as a relationship in the node-relationship structure.
21. CSM shall represent "Consuming data" as a relationship in the node-relationship structure.
22. CSM shall represent "Being dependent on a library or software unit" as a relationship in the node-relationship structure.
23. CSM shall represent "Assignment of a software unit to a role" as a relationship in the node-relationship structure.
24. CSM shall represent the processor core allocation (CPU allocation), operating system settings, and runtime environment configurations (JVM, etc.) belonging to the system's software units as queryable attributes on the node-relationship structure.
25. CSM shall report and record missing entity and invalid relationship errors detected during the construction of the Core System Model.
26. CSM shall record the Model Setup Data file used for the created Core System Model, the model creation time, project information, platform information, system version number, and model status.
27. CSM shall make the Core System Model available for use by the Design Verification Engine component.
28. CSM shall enable the Design Verification Engine component to access the nodes, relationships, and the Analytical Evaluation Data associated with them.
29. CSM shall handle read/write operations performed concurrently by multiple user sessions on the same Core System Model without compromising model integrity or the consistency of query results.
30. CSM shall execute the operations in the production deployment pipeline and the analysis and simulation operations of a number of users — to be determined during the critical design phase — concurrently and independently of one another, preventing the operations from affecting each other.
31. CSM shall create a new, process-specific Core System Model using the candidate version of the software unit being evaluated for installation into the target environment, together with the other software units in the target system version.

#### 5.1.2 Analytical Data Binding

32. CSM shall match the Analytical Evaluation Data with the relevant system entities and the connections between them in the Core System Model, making it usable in static analysis, verification, and simulation processes.
33. CSM shall be able to accept, as input, the Analytical Evaluation Data produced by the Analytical Data Manager component.
34. CSM shall associate the Analytical Evaluation Data with the relevant project, platform, system version, and Core System Model; shall match the record, telemetry, and synthetic data found in the data with the relevant nodes and relationships; and shall bind it to the node-relationship structure.
35. CSM shall preserve information on whether the Analytical Evaluation Data was produced using System Field Records or synthetic data supplied by the Scenario Generator.
36. CSM shall bind the Analytical Evaluation Data to the model without altering the nodes and relationships in the Core System Model, and shall ensure that the Core System Model data and the Analytical Evaluation Data are managed in a manner that keeps them separable from one another.
37. CSM shall report and record any node or relationship records for which no counterpart can be found in the Analytical Evaluation Data.

---

## 6. Design Verification Engine (SaaG-VAE)

**Table 7. SaaG-VAE Requirement Distribution**

| CSU | CSU ID | Number of Requirements |
|---|---|---|
| Design Verification Engine | VAE | 78 |
| **Subtotal** | | **78** |

### 6.1 VAE: Design Verification Engine

#### 6.1.1 Operations and Visualization

1. VAE shall enable the user to interact directly with the system components in support of design verification, static analysis, and evaluation operations, and shall present the results of those operations to the user.
2. VAE shall be able to interact with the Model Setup Generator, Scenario Generator, Analytical Data Manager, and Core System Model components.
3. VAE shall authenticate the username and password information of users wishing to access the system via a defined LDAP directory service, and shall allow only users who successfully authenticate to access the system within the scope of their authorizations.
4. VAE shall enable the user to select the project, platform, and system version on which operations will be performed, and shall distinctly display the currently effective system version for the project and platform.
5. VAE shall list, for the user, the Model Setup Data files belonging to the selected project, platform, and system version, and shall enable the user to select the file to be used.
6. VAE shall enable the user to start the Model Setup Data production process and to monitor the status of the process as one of in progress, successful, or failed.
7. VAE shall continuously and traceably display to the user the accessibility status of all data sources used.
8. VAE shall display to the user the missing data, access, authorization, format, or integrity errors detected during Model Setup Data production.
9. VAE shall enable the user to start the process of creating the Core System Model using the selected Model Setup Data, and to monitor the result of the operation as one of successful or failed.
10. VAE shall enable the user to select System Field Records as the data source to be used for creating the Analytical Evaluation Data.
11. VAE shall enable the user to select synthetic data supplied by the Scenario Generator as the data source to be used for creating the Analytical Evaluation Data.
12. VAE shall enable the user to select the records to be used, in the case where System Field Records are to be used as the Analytical Evaluation Data source.
13. VAE shall enable the user to determine the inputs relating to scenario scope, scenario type, time interval, data density, and the data types to be produced, in the case where synthetic data are to be used as the Analytical Evaluation Data source.
14. VAE shall enable the user to start and track the synthetic data production process, and to view errors occurring during production.
15. VAE shall enable the user to start and track the Analytical Evaluation Data production process, and to view errors occurring during production.
16. VAE shall display to the user the project, platform, and system version information associated with the Analytical Evaluation Data bound to the Core System Model, and shall report the matching status of the record, telemetry, and synthetic data found in the data with the nodes and relationships.
17. VAE shall enable the user to perform structural changes — such as adding/removing nodes, adding/removing relationships, and updating node/relationship attributes — on a working model derived from the Core System Model, without breaking its structural integrity, and shall enable design verification and analysis operations to be carried out on the updated working model.
18. VAE shall classify design verification and analysis results as one of "conforming" or "non-conforming," according to rules/metrics to be determined during the critical design phase.
19. VAE shall enable the user to search for a system entity or relationship on the node-relationship structure and to filter the results by type, project, platform, system version, or software unit information.
20. VAE shall enable the user to perform visual zoom in, zoom out, pan, and node/relationship selection and attribute display operations on the node-relationship structure.
21. VAE shall present to the user each finding detected in the analysis results together with at least the following information: finding identifier, finding type, finding description, affected system entity or relationship, related verification rule or acceptance criterion, data or evidence supporting the finding, and the severity level of the finding, expressed as one of informational, low, medium, high, or critical.
22. VAE shall record and display to the user the cause-and-effect relationship between related findings detected within the scope of the same operation.
23. VAE shall enable the user to sort and filter findings by operation type, evaluation result, finding type, severity level, project, platform, system version, or affected nodes.
24. VAE shall record the error cause, the stage at which the operation was interrupted, and the error time occurring during a design verification, analysis, or simulation operation.
25. VAE shall be able to record the scenario name, scenario inputs, data production time, and the associated project, platform, and system version information used in simulation operations.
26. VAE shall generate a summary or detailed system report of design verification, analysis, and simulation results in an exportable file format whose details will be determined during the critical design phase, and shall ensure that the reports contain at least the following information: project information, platform information, system version information, the Core System Model used, the Analytical Evaluation Data used and its data source, operation identifier and operation type, operation start and end time, evaluation result, findings detected, affected nodes and relationships, severity levels, and additional information relating to the findings.
27. VAE shall also accept analysis requests — made via user interfaces — through Build Automation Tools and a Command Line Interface (CLI); shall present status information on ongoing operations to users accessing the system and to automation clients (e.g., Jenkins); and shall ensure that analysis operations are carried out concurrently and independently of one another.

#### 6.1.2 Structural Design Verification

28. VAE shall perform design verification operations on the Core System Model.
29. VAE shall perform design verification operations without altering the nodes and relationships in the Core System Model.
30. VAE shall be able to perform analyses solely on the Core System Model without using Analytical Evaluation Data.
31. VAE shall be able to perform, on the Core System Model, the analysis of structural dependencies, communication connections, and runtime environment relationships between system entities.
32. VAE shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Durability parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
33. VAE shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Reliability parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
34. VAE shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Lifespan parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
35. VAE shall verify, on the Core System Model, the conformance of topic data transmission quality-of-service Transport Priority parameters to rules to be determined during the critical design phase, and shall detect incompatibilities.
36. VAE shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect a topic with no data publisher.
37. VAE shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect a topic with no data consumer.
38. VAE shall verify topic data publisher and data consumer matches on the Core System Model, and shall detect topics defined with the same name having content definitions that differ from one another.
39. VAE shall verify, on the Core System Model, the mutual consistency of source, destination, message, and communication direction information in external-to-middleware communications carried out via communication services to be determined during the critical design phase.
40. VAE shall analyze, on the Core System Model, the conformance of the distribution of the system's software units across Operator Console and Processor Units to load balancing rules to be determined during the critical design phase.
41. VAE shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect the total number of cores allocated on a Processor Unit exceeding the available core capacity.
42. VAE shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect the same cores being allocated to multiple applications in a conflicting manner.
43. VAE shall verify, on the Core System Model, the conformance of the processor core allocation made to the system's software units to rules to be determined during the critical design phase, and shall detect applications required to run with high performance not having dedicated cores allocated to them.
44. VAE shall audit, on the Core System Model, the conformance of the operating system settings running on processor/console units to rules to be determined during the critical design phase and to the processor core allocation made.
45. VAE shall verify, on the Core System Model, the conformance of the memory allocation parameters in the runtime environment configurations of the system's software units to rules to be determined during the critical design phase.
46. VAE shall detect, on the Core System Model, situations that could cause resource contention and bottlenecks arising from inconsistencies among processor core allocation, operating system settings, and runtime environment configurations.
47. VAE shall detect circular dependencies between the system's software units on the Core System Model.
48. VAE shall detect, on the Core System Model, disconnected, missing, invalid, or unmatched structural relationships between the nodes within the Core System Model.
49. VAE shall detect, on the Core System Model, design patterns that violate architectural rules to be determined during the critical design phase.

#### 6.1.3 Behavioral Simulation and Analysis

50. VAE shall perform static analysis operations on the Core System Model.
51. VAE shall perform analysis operations without altering the nodes and relationships in the Core System Model.
52. VAE shall be able to perform analyses using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
53. VAE shall analyze the message flow direction, message count, data volume, and messaging frequency between nodes, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
54. VAE shall be able to evaluate the effects on the Core System Model of a node or relationship becoming inactive, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator.
55. VAE shall be able to perform design-time traffic analysis using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, and shall be able to evaluate, within the scope of the effects of load conditions created within the simulation on system entities and relationships, an increase in Topic/Message density.
56. VAE shall be able to perform design-time traffic analysis using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, and shall be able to evaluate, within the scope of the effects of load conditions created within the simulation on system entities and relationships, a change in Topic/Message publishing or consumption behavior.
57. VAE shall, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, determine the propagation of fault, load, communication interruption, or bandwidth-narrowing conditions created within the simulation onto dependent nodes, and shall detect the directly or indirectly affected nodes/relationships and the propagation path followed by the effect.
58. VAE shall, using Analytical Evaluation Data produced from synthetic data supplied by the Scenario Generator, determine the system entities with the highest resource usage or the most intensive messaging as a result of the simulation to be performed, and shall present these to the user as summary evaluation indicators.
59. VAE shall be able to perform analyses using Analytical Evaluation Data produced from System Field Records.
60. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on operational and health status.
61. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on processor, memory, storage, and network usage values.
62. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on error, warning, restart, and timeout information.
63. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on message flow direction, message count, data volume, and messaging frequency.
64. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on communication latency, message loss, and successful transmission rates.
65. VAE shall be able to perform analyses on the Core System Model, using Analytical Evaluation Data produced from System Field Records, on topic publishing and consumption activities.
66. VAE shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships present in the Model Setup Data but not observed in the runtime data.
67. VAE shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships not present in the Model Setup Data but observed in the runtime data.
68. VAE shall compare the nodes and relationships in the Model Setup Data with the runtime system entities and relationships observed in the Analytical Evaluation Data produced from System Field Records, and shall detect system entities and relationships showing incompatibility between the Model Setup Data and the runtime data.
69. VAE shall analyze the event records associated with the nodes and relationships found in the Analytical Evaluation Data produced from System Field Records.
70. VAE shall, using Analytical Evaluation Data produced from System Field Records, determine the system entities with the highest resource usage or the most intensive messaging as a result of the analysis, and shall present these to the user as summary evaluation indicators.

#### 6.1.4 Installation Suitability Evaluation

71. VAE shall perform evaluation operations on the Core System Model, in the form of installation suitability evaluation for candidate software units.
72. VAE shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of structural and architectural conformance.
73. VAE shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of interface, topic, and communication conformance.
74. VAE shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of dependency and integration conformance.
75. VAE shall analyze the suitability of a software unit for installation into the target environment under the evaluation heading of resource and performance sufficiency.
76. VAE shall define each control rule used in the installation suitability evaluation with a rule identifier, evaluation heading, severity level, weight value, acceptance criterion, and blocking status, and shall classify and score the conformance categories and scoring method belonging to the rule results in a manner whose details will be determined during the critical design phase.
77. VAE shall, upon detecting a finding with a critical severity level or a violation of a control rule defined as blocking in the evaluation profile, determine the installation result for the target environment as "non-conforming" independently of the overall conformance score, and shall transmit the decision information preventing the continuation of the production deployment pipeline to the automation client.
78. VAE shall execute installation suitability evaluations initiated for one or more software units within the scope of the production deployment pipeline using independent operation identifiers from one another, and shall present, for each software unit, a separate conformance score, score class, blocking findings, and installation decision, as well as the aggregate operation result, in a machine-processable format to the automation client.

---

## 7. System Capability Allocation and Requirements Traceability

This section establishes the bidirectional traceability and allocation between baseline system capability requirements (CSCI/CSC level) and Computer Software Unit (CSU) functional requirements.

**Relationship key:**
- **Direct**: A baseline system capability requirement allocated directly to a single CSU functional requirement without decomposition.
- **Split**: A compound system capability requirement decomposed into multiple atomic, independently testable CSU functional requirements.
- **Joint**: A system-wide charter or cross-cutting capability requirement realized through coordinated functional requirements across multiple contributing CSUs.
- **Infrastructure**: A non-functional or physical platform constraint allocated to the runtime infrastructure environment.

### SaaG-MSD

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
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

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
|---|---|---|---|
| SCG.1 | SCG | SSS-SCG.1 | Direct (charter) |
| SCG.2 | SCG | SSS-SCG.2 | Direct |
| SCG.3 | SCG | SSS-SCG.3 | Direct |
| SCG.4 | SCG | SSS-SCG.4 | Direct |
| SCG.5 | SCG | SSS-SCG.5 | Direct |
| SCG.6 | SCG | SSS-SCG.6 | Direct |
| SCG.7 | SCG | SSS-SCG.7 | Direct |

### SaaG-FRD

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
|---|---|---|---|
| FRD.1 | FRD | SSS-FRD.1 | Direct (charter) |
| FRD.2 | FRD | SSS-FRD.2 | Direct |
| FRD.3 | FRD | SSS-FRD.3 | Direct |
| FRD.4 | FRD | SSS-FRD.4 | Direct |
| FRD.5 | FRD | SSS-FRD.5 | Direct |
| FRD-INF.1 | FRD-INF | SSS-FRD.6 | Infrastructure (platform storage) |

### SaaG-ADP

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
|---|---|---|---|
| ADP.1 | ADP | SSS-ADP.1 | Direct (charter) |
| ADP.2 | ADP | SSS-ADP.2 | Direct |
| ADP.3 | ADP | SSS-ADP.3 | Direct |
| ADP.4 | ADP | SSS-ADP.4 | Direct |
| ADP.5 | ADP | SSS-ADP.5 | Direct |
| ADP.6 | ADP | SSS-ADP.6 | Direct |

### SaaG-CSM

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
|---|---|---|---|
| CSM.1 | CSM | SSS-CSM.1 | Joint |
| CSM.2 | CSM | SSS-CSM.2 | Direct |
| CSM.3 | CSM | SSS-CSM.3 | Direct |
| CSM.4 | CSM | SSS-CSM.4 | Direct |
| CSM.5 | CSM | SSS-CSM.5 | Direct |
| CSM.6 | CSM | SSS-CSM.6 | Split |
| CSM.7 | CSM | SSS-CSM.6 | Split |
| CSM.8 | CSM | SSS-CSM.6 | Split |
| CSM.9 | CSM | SSS-CSM.6 | Split |
| CSM.10 | CSM | SSS-CSM.6 | Split |
| CSM.11 | CSM | SSS-CSM.6 | Split |
| CSM.12 | CSM | SSS-CSM.6 | Split |
| CSM.13 | CSM | SSS-CSM.6 | Split |
| CSM.14 | CSM | SSS-CSM.6 | Split |
| CSM.15 | CSM | SSS-CSM.6 | Split |
| CSM.16 | CSM | SSS-CSM.6 | Split |
| CSM.17 | CSM | SSS-CSM.6 | Split |
| CSM.18 | CSM | SSS-CSM.7 | Split |
| CSM.19 | CSM | SSS-CSM.7 | Split |
| CSM.20 | CSM | SSS-CSM.7 | Split |
| CSM.21 | CSM | SSS-CSM.7 | Split |
| CSM.22 | CSM | SSS-CSM.7 | Split |
| CSM.23 | CSM | SSS-CSM.7 | Split |
| CSM.24 | CSM | SSS-CSM.8 | Direct |
| CSM.25 | CSM | SSS-CSM.9 | Direct |
| CSM.26 | CSM | SSS-CSM.15 | Direct |
| CSM.27 | CSM | SSS-CSM.16 | Direct |
| CSM.28 | CSM | SSS-CSM.17 | Direct |
| CSM.29 | CSM | SSS-CSM.18 | Direct |
| CSM.30 | CSM | SSS-CSM.19 | Direct |
| CSM.31 | CSM | SSS-CSM.20 | Direct |
| CSM.32 | CSM | SSS-CSM.1 | Joint |
| CSM.33 | CSM | SSS-CSM.10 | Direct |
| CSM.34 | CSM | SSS-CSM.11 | Direct |
| CSM.35 | CSM | SSS-CSM.12 | Direct |
| CSM.36 | CSM | SSS-CSM.13 | Direct |
| CSM.37 | CSM | SSS-CSM.14 | Direct |

### SaaG-VAE

| SRS Req ID | CSU | Baseline System Req ID | Relationship |
|---|---|---|---|
| VAE.1 | VAE | SSS-VAE.1 | Joint |
| VAE.2 | VAE | SSS-VAE.2 | Direct |
| VAE.3 | VAE | SSS-VAE.3 | Direct |
| VAE.4 | VAE | SSS-VAE.4 | Direct |
| VAE.5 | VAE | SSS-VAE.5 | Direct |
| VAE.6 | VAE | SSS-VAE.6 | Direct |
| VAE.7 | VAE | SSS-VAE.7 | Direct |
| VAE.8 | VAE | SSS-VAE.8 | Direct |
| VAE.9 | VAE | SSS-VAE.9 | Direct |
| VAE.10 | VAE | SSS-VAE.10 | Split |
| VAE.11 | VAE | SSS-VAE.10 | Split |
| VAE.12 | VAE | SSS-VAE.11 | Direct |
| VAE.13 | VAE | SSS-VAE.12 | Direct |
| VAE.14 | VAE | SSS-VAE.13 | Direct |
| VAE.15 | VAE | SSS-VAE.14 | Direct |
| VAE.16 | VAE | SSS-VAE.16 | Direct |
| VAE.17 | VAE | SSS-VAE.17 | Direct |
| VAE.18 | VAE | SSS-VAE.42 | Direct |
| VAE.19 | VAE | SSS-VAE.43 | Split |
| VAE.20 | VAE | SSS-VAE.43 | Split |
| VAE.21 | VAE | SSS-VAE.44 | Direct |
| VAE.22 | VAE | SSS-VAE.45 | Direct |
| VAE.23 | VAE | SSS-VAE.46 | Direct |
| VAE.24 | VAE | SSS-VAE.47 | Direct |
| VAE.25 | VAE | SSS-VAE.48 | Direct |
| VAE.26 | VAE | SSS-VAE.49 | Direct |
| VAE.27 | VAE | SSS-VAE.50 | Direct |
| VAE.28 | VAE | SSS-VAE.1 | Joint |
| VAE.29 | VAE | SSS-VAE.15 | Joint |
| VAE.30 | VAE | SSS-VAE.18 | Direct |
| VAE.31 | VAE | SSS-VAE.19 | Direct |
| VAE.32 | VAE | SSS-VAE.20 | Split |
| VAE.33 | VAE | SSS-VAE.20 | Split |
| VAE.34 | VAE | SSS-VAE.20 | Split |
| VAE.35 | VAE | SSS-VAE.20 | Split |
| VAE.36 | VAE | SSS-VAE.21 | Split |
| VAE.37 | VAE | SSS-VAE.21 | Split |
| VAE.38 | VAE | SSS-VAE.21 | Split |
| VAE.39 | VAE | SSS-VAE.22 | Direct |
| VAE.40 | VAE | SSS-VAE.23 | Direct |
| VAE.41 | VAE | SSS-VAE.24 | Split |
| VAE.42 | VAE | SSS-VAE.24 | Split |
| VAE.43 | VAE | SSS-VAE.24 | Split |
| VAE.44 | VAE | SSS-VAE.25 | Direct |
| VAE.45 | VAE | SSS-VAE.26 | Direct |
| VAE.46 | VAE | SSS-VAE.27 | Direct |
| VAE.47 | VAE | SSS-VAE.28 | Direct |
| VAE.48 | VAE | SSS-VAE.29 | Direct |
| VAE.49 | VAE | SSS-VAE.30 | Direct |
| VAE.50 | VAE | SSS-VAE.1 | Joint |
| VAE.51 | VAE | SSS-VAE.15 | Joint |
| VAE.52 | VAE | SSS-VAE.31 | Direct |
| VAE.53 | VAE | SSS-VAE.32 | Direct |
| VAE.54 | VAE | SSS-VAE.33 | Direct |
| VAE.55 | VAE | SSS-VAE.34 | Split |
| VAE.56 | VAE | SSS-VAE.34 | Split |
| VAE.57 | VAE | SSS-VAE.35 | Direct |
| VAE.58 | VAE | SSS-VAE.36 | Direct |
| VAE.59 | VAE | SSS-VAE.37 | Direct |
| VAE.60 | VAE | SSS-VAE.38 | Split |
| VAE.61 | VAE | SSS-VAE.38 | Split |
| VAE.62 | VAE | SSS-VAE.38 | Split |
| VAE.63 | VAE | SSS-VAE.38 | Split |
| VAE.64 | VAE | SSS-VAE.38 | Split |
| VAE.65 | VAE | SSS-VAE.38 | Split |
| VAE.66 | VAE | SSS-VAE.39 | Split |
| VAE.67 | VAE | SSS-VAE.39 | Split |
| VAE.68 | VAE | SSS-VAE.39 | Split |
| VAE.69 | VAE | SSS-VAE.40 | Direct |
| VAE.70 | VAE | SSS-VAE.41 | Direct |
| VAE.71 | VAE | SSS-VAE.1 | Joint |
| VAE.72 | VAE | SSS-VAE.51 | Split |
| VAE.73 | VAE | SSS-VAE.51 | Split |
| VAE.74 | VAE | SSS-VAE.51 | Split |
| VAE.75 | VAE | SSS-VAE.51 | Split |
| VAE.76 | VAE | SSS-VAE.52 | Direct |
| VAE.77 | VAE | SSS-VAE.53 | Direct |
| VAE.78 | VAE | SSS-VAE.54 | Direct |

**Coverage check:** all 112 baseline system capabilities appear at least once above (111 realized as functional CSU requirements, 1 — SSS-FRD.6 / FRD-INF.1 — realized as a platform infrastructure constraint). Total SRS functional requirements: **156**; infrastructure constraints: **1**; total managed requirements: **157**.
