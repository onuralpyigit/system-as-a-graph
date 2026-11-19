# ADR-0020: Performance, capacity and observability

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, system engineering |
| Kind | Decide |
| Traces | FDM-INF.1; SMM.29–30; DVE.6–7, 14–15, 23, 27, 78; UXD §6; QA-07, QA-08, QA-09 |
| Resolves | DP-15 (FDM-INF.1 storage hardware disk capacity) |
| Decide by | Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

Several ADRs defer their numbers here:

* ADR-0006 needs a host size for its per-class limits;
* ADR-0007 needs a check on SQLite write contention;
* ADR-0011's spike needs load thresholds;
* ADR-0015's graph view needs the UI budget;
* ADR-0012 and ADR-0014 need data-volume and disk sizing.

FDM-INF.1 defers the disk capacity of the field-record storage (DP-15). SDP Increment 8 asks for capacity verification and runtime observability.

As built (`1157784`), logging uses the standard library. The `dve` and `mdg` loggers are raised to `log_level` from `dve.ini`, and the root logger stays at WARNING (`dve/src/dve/config.py`). There is no health endpoint and no metrics. Everything runs on one offline host (ADR-0004).

## Decision Drivers

* Budgets must be explicit numbers that tests can check and hardware can be sized against.
* The host is sized once, offline, so the disk formula must include every store.
* Observability must not add a server to the offline host (QA-10), yet failures must be diagnosable per operation (QA-08, QA-09).

## Considered Options

* Budgets: per operation class against a reference model / per endpoint only / no explicit budgets
* Observability: structured log files plus a health endpoint / a metrics stack (Prometheus or VictoriaMetrics plus dashboards) / plain log files only

## Decision Outcome

Chosen options: **budgets per operation class against a stated reference model**, and **structured log files plus a health endpoint**. All numbers below are **initial values, to be confirmed by the CDR Board** and re-measured in R8.

### 1. Reference model and budgets

* **Reference model:** 5,000 Applications, 5,000 Topics, 2,000 Messages, 500 Nodes and 50,000 relationships, generated synthetically for tests. This is the same scale as ADR-0011's spike.
* **Budgets on the reference host (§2):**

  | Operation | Budget |
  |---|---|
  | Model Data production (excluding network clone time) | ≤ 120 s |
  | Model construction, including derivation and store write | ≤ 30 s |
  | Working-model copy | ≤ 5 s |
  | Full structural verification profile | ≤ 60 s |
  | Propagation analysis, one scenario | ≤ 30 s |
  | Installation evaluation, one unit | ≤ 120 s |
  | List and status API calls (p95) | ≤ 500 ms |
  | Findings page of 100 rows with filters (p95, DVE.23) | ≤ 1 s |
  | Graph view response, ≤ 1,000 elements | ≤ 1 s |
  | UI pan and zoom; route time-to-interactive | UXD §6 (60 fps; < 1 s) |

* **Concurrency:** the budgets hold with ADR-0006's initial limits running together (4 pipeline, 4 interactive, 2 simulation) and 20 signed-in users.

### 2. Host sizing and disk capacity (FDM-INF.1, DP-15)

* **Reference host:** x86_64, at least 10 cores (the sum of ADR-0006's class limits), 32 GB RAM, local SSD.
* **Disk:**

  *D = F + W + G + S + L + B*

  | Term | Meaning | Initial estimate |
  |---|---|---|
  | *F* | Field records = *r* × *d* × 1.5 | *r* = raw volume per day, *d* = retention days; 1.5 covers the normalized copy (ADR-0014) |
  | *W* | Workspace: Model Data runs and clones | runs per day × average run size × retention days |
  | *G* | Graph server data | live instances (≤ 200, ADR-0006) × instance size |
  | *S* | SQLite records | findings and operation logs × retention |
  | *L* | Logs | 30 days of rotated logs |
  | *B* | Backups | one full copy of *F + W + G + S* (ADR-0004 §5) |

  The result is multiplied by 1.3 for headroom. The values of *r*, *d* and the run rate come from the field-recording owners and the pipeline owners. The installer checks free space against the configured *D*.

### 3. Observability

* **Logs:**
  * standard-library logging to `/var/log/dsm/dsm.log`, one JSON object per line: time (UTC), level, logger, message, `operation_id`, `user`;
  * rotated by size with `RotatingFileHandler`, keeping 30 days;
  * the root logger is configured once in `dsm`, extending the as-built `configure_logging`;
  * the secret-redaction filter applies (ADR-0019).
* **Per-operation logs** stay in `operation_log` (ADR-0007) for the UI. The file log is for operators.
* **Health:** `GET /api/v1/health` returns 200 or 503 with component states: SQLite readable and writable, the graph server reachable, free disk above a threshold, and the task runner's queue lengths. `GET /api/v1/health/sources` checks the configured data sources (DVE.7). Both are suitable for the service manager or a monitoring system.
* **Metrics:** an optional `GET /api/v1/metrics` in plain-text exposition format gives operation counts and durations by class, queue lengths and request latencies. No metrics server is installed; an existing monitoring system may scrape it.

### Consequences

* Good, because every budget is a number a test can check, and hardware is sized from one formula.
* Good, because there is no new server, and logs carry the operation ID for correlation with records.
* Bad, because the initial numbers are estimates until R8 measures them, and they may change.
* Bad, because there are no dashboards out of the box. The metrics endpoint only helps where a monitoring system exists.

### Confirmation

* A performance suite (R8) generates the reference model and checks each budget, also under the concurrent load of §1.
* A test asserts that every log line written during an operation carries its `operation_id`.
* A health test stops each dependency (SQLite file permissions, graph server) and expects 503 with the failing component named.

### Open points

* The raw field-record volume per day and the retention period, from the recording-mechanism owners.
* Confirmation of the reference model scale against the largest real system.

## Pros and Cons of the Options

* Budgets per operation class (chosen): Good, because they are testable and tied to the work users do. Bad, because they need a reference model and host.
* Endpoint budgets only: Bad, because long operations, which matter most, are not covered.
* No budgets: Bad, because there is nothing to size hardware or accept R8 against.
* Structured logs + health (chosen): Good, because there is no new server and failures stay diagnosable. Bad, because there are no dashboards.
* Metrics stack: Good, because it gives dashboards and alerting. Bad, because of the servers to install and operate offline.
* Plain log files only: Bad, because there is no health signal for the service manager, and correlation is weak.

## More Information

* [UXD §6](../UXD.md), [SDP Increment 8](../../planning/SDP.md)
* Code: `dve/src/dve/config.py` (`configure_logging`), `dve/src/dve/dve.ini`
* Related: ADR-0004, ADR-0006, ADR-0007, ADR-0015, ADR-0011, ADR-0012, ADR-0014, ADR-0019
