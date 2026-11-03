# ADR-0011: Network topology acquisition

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, system/network engineering |
| Kind | Decide |
| Traces | MDG.5–7, 21; SMM.14–15, 18; DVE.40–46 |
| Closes | CDR-09, CDR-20 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

MDG.6 requires network topology data to be obtained automatically "from an external data source (file, database, etc.) whose details will be determined during the critical design phase" (CDR-09). MDG.7 additionally requires manual entry. CDR-20 leaves the protocol of EXT-IF-04 open. Topology feeds the processor/console and network nodes of the System Model (SMM.14–15, 18) and the resource rules (DVE.40–46).

Today no topology source is implemented. The application-to-processor-unit relation (`runs_on`) comes from a mocked system repository parser (`SystemRepoParser`), which reads the system repository that MDG already clones per system version.

## Decision Drivers

* Topology must be versioned with the system version, so that a model of version N always uses version N's topology (MDG.9).
* No authoritative network-management system has been identified as a SaaG data source.
* Manual entry (MDG.7) and automatic acquisition must produce the same data, so they can be validated the same way (MDG.21).
* Capacity attributes (cores, RAM, bandwidth) are needed for the resource rules.

## Considered Options

* A topology file in the system repository, in a SaaG-defined schema, acquired with the system repository clone
* A query against the configuration management database
* An export from a network-management system
* Manual entry only

## Decision Outcome

Chosen option: "A topology file in the system repository, in a SaaG-defined schema". The system repository is already cloned per system version by tag (ADR-0010, ADR-0012), so topology is versioned exactly like the software it hosts. No new external interface or credential is needed.

* **Format:** `topology.yaml` at a configured path in the system repository, validated against a JSON Schema owned by MDG (`mdg/schemas/topology.schema.json`). Its sections:
  * `processing_units`: name, kind (`operator_console` | `processor`), cores, RAM, OS profile reference;
  * `network_components`: name, kind, bandwidth;
  * `links`: unit ↔ network component, bandwidth;
  * `schema_version`.
* **EXT-IF-04 protocol (closes CDR-20):** Git over HTTPS, through the same adapter and credentials as EXT-IF-02. It is read from the system repository clone already made by MDG.
* **Automatic acquisition (closes CDR-09):** MDG reads the file during Model Data production. If the file is absent, the run is marked `missing_data` for topology (MDG.19). If it fails schema validation, a format error is recorded (ADR-0034).
* **Manual entry (MDG.7):** the UI edits the same schema and saves it as a topology override attached to the run. The override is recorded as manual in the run's provenance (ADR-0035). It is never written back to the system repository.
* **Other sources later:** an adapter for a CMDB table or network-management export may be added behind an `ITopologySource` port. It must produce the same schema.

### Consequences

* Good, because topology is reproducible per system version and needs no new integration.
* Good, because a single schema serves the automatic path, the manual path and validation.
* Bad, because system engineering must maintain `topology.yaml` in the system repository, which is a process change.
* Bad, because the mocked `SystemRepoParser` must be replaced with a real parser that also reads `runs_on` from the system repository (ADR-0012).

### Confirmation

* The `dev/gitea` seed's `system_repo_1.0.0` gains a sample `topology.yaml`. The MDG tests cover the valid, missing and invalid cases.
* The schema file is versioned, and Model Data records the `schema_version` used (ADR-0013).

## Pros and Cons of the Options

### Topology file in the system repository

* Good, because it is versioned with the system and has no new interface or credentials.
* Bad, because it depends on engineers keeping the file current.

### CMDB query

* Good, because it may already hold hardware data.
* Bad, because the CMDB schema is unconfirmed, and it is not known to hold network data.

### Network-management export

* Good, because it may be authoritative for the live network.
* Bad, because none has been identified. It describes the *deployed* network, not the *designed* one for a given system version.

### Manual entry only

* Good, because it is trivial to implement.
* Bad, because it fails MDG.6, and it is error-prone and not reproducible.

## More Information

* Code: `mdg/src/mdg/adapters/source_data/system_repo_parser.py` (mock)
* Related: ADR-0010, ADR-0012, ADR-0013, ADR-0014, ADR-0034
