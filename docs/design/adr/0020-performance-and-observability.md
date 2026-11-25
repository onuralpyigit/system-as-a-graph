# ADR-0020: Performance, capacity and observability

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, platform team, system engineering |
| Kind | Decide |
| Traces | FDM-INF.1; SMM.29–30; DVE.6–7, 14–15, 23, 27, 78; UXD §6; QA-07, QA-08, QA-09 |
| Resolves | DP-15 (FDM-INF.1 storage hardware disk capacity) |
| Decide by | Wave C (2027-03-12) |
| Supersedes | — |

## Context and Problem Statement

Multiple ADRs rely on concrete performance, memory, and disk budgets:

* ADR-0006 fixes concurrency caps (`4 pipeline + 4 interactive + 2 simulation = 10` worker processes, `20` active users, `200` live graph instances);
* ADR-0007 requires SQLite WAL contention verification on `dsm.db`;
* ADR-0011's spike requires graph write, copy and query latency thresholds across 200 instances;
* ADR-0012, ADR-0013 and ADR-0014 require storage sizing across Model Data, SCG, Field Records, and AED `overlay.db` files;
* **SRS `FDM-INF.1` (`DP-15`)** requires determining the **storage hardware disk capacity sizing and specifications** during critical design; and
* SDP Increment 8 requires capacity verification and runtime observability on a containerless offline host (`ADR-0004`).

As built (`1157784`), `dve/src/dve/config.py` configures basic standard-library console logging (`dve` and `mdg` at `log_level`, root at `WARNING`), with no log files, health probes, or operational metrics.

## Decision Drivers

* Every latency and capacity target must be concrete and mechanically testable in R3/R8 qualification suites—and `FDM-INF.1` (`DP-15`) needs both a site sizing formula **and** a concrete minimum hardware specification so `SRS FDM-INF.1` closes unambiguously at Wave C!
* RAM and disk budgets must account for all 10 concurrent worker processes, 200 coexisting graph instances, `raw + normalized` field records (`2.0×`), and AED `.jsonl.gz + overlay.db` artifacts.
* Observability must add zero extra server daemons offline (QA-10) while correlating logs by `operation_id` and protecting sensitive endpoints cleanly (QA-01, QA-09).

## Considered Options

* Performance targets: Explicit latency/throughput budgets across all 10 operation types against a synthetic reference model and reference host
* Performance targets: HTTP endpoint p95 budgets only
* Performance targets: Unbounded best-effort execution
* Observability: Structured JSON log files (`RotatingFileHandler`), authenticated/localhost health & source-status endpoints, and optional Prometheus text exposition
* Observability: Bundled Prometheus + Grafana / VictoriaMetrics stack
* Observability: Unstructured stdout logs only

## Decision Outcome

Chosen options: **explicit latency budgets across all operation classes on a stated reference model and reference host (with a concrete 4 TB NVMe/SSD baseline + sizing formula for `FDM-INF.1`)**, and **structured JSON log files plus tiered health and metrics endpoints**.

### 1. Reference model and latency budgets (`QA-07`)

* **Synthetic reference model:** `5,000` `Application`/`Library` CSUs, `5,000` `Topic`s, `2,000` `Message`s, `500` `Node`s, `50` `NetworkDevice`s/`Broker`s, and `50,000` structural relationships, with `200` coexisting model instances loaded in the graph server (matching ADR-0011 §2).
* **Latency budgets on the reference host (§2) under full ADR-0006 concurrent load (`4 pipeline + 4 interactive + 2 simulation`, `20` signed-in users):**

  | Operation / API class | Target budget |
  |---|---|
  | `model_data_production` (local parse & validation, excluding external Git network transfer) | `≤ 120 s` |
  | `model_construction` (SMM validation, Python `0bbe06af` derivation, and graph-store write) | `≤ 30 s` |
  | Working-model `copy_instance` or `delete_instance` (with 200 instances loaded) | `≤ 5 s` |
  | Working-model single `apply_edit` / `undo_edit` (including re-derivation) | `≤ 2 s` |
  | `field_record_ingestion` (`IFieldRecordParser` normalization, per `1 GB` archive) | `≤ 90 s` |
  | `synthetic_data_production` (`SCG`, `3,600` windows across `5,000` topics + `field_samples`) | `≤ 45 s` |
  | `aed_production` (`ADM` windowing, validation, and `overlay.db` build, per `1M` metric rows) | `≤ 60 s` |
  | `aed_binding` (`SMM.bind` key/alias matching & `SMM.37` counts) | `≤ 10 s` |
  | `structural_verification` (full R3 profile) | `≤ 60 s` |
  | `simulation_analysis` (dual-graph propagation + KPIs, one scenario) | `≤ 30 s` |
  | `field_analysis` (field health/traffic rules + `DVE.66–68` drift) | `≤ 60 s` |
  | `installation_evaluation` (per candidate unit, end-to-end) | `≤ 120 s` |
  | `report` export (`HTML`, `JSON`, or `CSV` up to `10,000` findings) | `≤ 5 s` |
  | Metadata list & operation status API calls (`p95`) | `≤ 500 ms` |
  | `dve_finding` filtered/sorted page of `100` rows (`p95`, DVE.23) | `≤ 1 s` |
  | Scoped graph view payload (`≤ 1,000` elements, `p95`) & canvas pan/zoom | `≤ 1 s` API; `60 fps` canvas (UXD §6) |

### 2. Reference host, RAM partitioning, and `FDM-INF.1` storage specification (`DP-15`)

* **Compute & RAM baseline:** `x86_64`, **≥ 12 physical CPU cores** (`10` reserved across ADR-0006 worker queues + `2` for OS, `waitress` API, and graph server), **≥ 32 GB ECC RAM** partitioned to prevent OOM under peak load:
  * Native graph server (Neo4j JVM heap `6 GB` + off-heap pagecache `6 GB`): `≤ 12 GB`;
  * `dsm` parent API + up to `10` concurrent Python child processes (`≤ 1.2 GB` `RLIMIT_AS` soft target per worker): `≤ 14 GB`;
  * OS kernel, filesystem cache and SQLite WAL/read-only `overlay.db` mappings: `6 GB`.
* **Storage hardware specification & capacity formula (`SRS FDM-INF.1`, `DP-15`):**
  * **Hardware tier:** local **enterprise NVMe or SAS/SATA SSD** (network NFS/SMB mounts are forbidden for `dsm.db` WAL and Neo4j stores), providing **≥ 20,000 random 4 KB read/write IOPS** and **≥ 500 MB/s sustained sequential throughput**, formatted as `xfs` or `ext4` (`noatime`).
  * **Capacity sizing formula:**
    $$D_{\text{required}} = 1.30 \times (F + W + G + S + L + B)$$

    | Term | Formula | Design-basis reference inputs ($d = 90\text{ days}$) | Reference subtotal |
    |---|---|---|---|
    | $F$ | $2.0 \times r \times d$ (`raw/` + `normalized/`, ADR-0014) | $r = 10\text{ GB/day}$ raw field uploads × $90\text{ d}$ × $2.0$ | `1,800 GB` |
    | $W$ | $(w_{\text{mdg}} + w_{\text{scg}} + w_{\text{aed}}) \times d$ (Model Data + SCG + AED `.jsonl.gz` & `overlay.db` + reports) | $4\text{ GB/day}$ combined workspace artifacts × $90\text{ d}$ | `360 GB` |
    | $G$ | $N_{\text{inst}} \times s_{\text{inst}}$ (up to `200` live graph instances + transaction logs, ADR-0011) | $200 \times 0.4\text{ GB}$ | `80 GB` |
    | $S$ | Central `dsm.db` + WAL (`common_operation`, `dve_finding`, `common_audit_event`) | $90\text{ d}$ of operations/findings | `20 GB` |
    | $L$ | Rotated structured JSON logs (`/var/log/dsm/`) | `20` × `100 MB` capped archives | `2 GB` |
    | $B$ | Local staging snapshot of $0.5 \times (F + W + G + S)$ prior to off-host transfer (ADR-0004 §5) | Rolling local backup staging | `800 GB` |
    | **Total ($1.30\times$)** | Includes `30%` filesystem/compaction headroom | $1.30 \times 3,062\text{ GB} \approx 3,981\text{ GB}$ | **≥ 4.0 TB usable SSD** |

  * **Normative `FDM-INF.1` requirement:** the production host provides **at least `4.0 TB` usable local NVMe/enterprise SSD** on `/var/lib/dsm` for the reference workload ($r \le 10\text{ GB/day}, d \le 90\text{ days}$), scaled linearly by $D_{\text{required}}$ where institutional $r$ or $d$ (ADR-0004 §5) is higher. `deploy/install.sh` verifies free disk space on `/var/lib/dsm` against `[storage] min_required_gb` at install time.

### 3. Structured logging, health probes and metrics (`QA-08, QA-09`)

* **Structured JSON file logs (`/var/log/dsm/dsm.log`):**
  * Configured once in `dsm` (`configure_logging`), writing one UTF-8 JSON line per event (`ts` UTC ISO 8601, `level`, `logger`, `msg`, `operation_id`, `user`, `req_id`) passed through ADR-0019's secret-redaction filter.
  * Rotated via `RotatingFileHandler(maxBytes=100 * 1024 * 1024, backupCount=20)` (`2.0 GB` hard disk ceiling, sized for ≥ 30 days of normal operation without unbounded growth). Per-operation user-visible logs stay in `common_operation_log` (`ADR-0007`).
* **Tiered health & source-accessibility endpoints (reconciling `systemd` probes with ADR-0019 security):**
  * `GET /api/v1/health`: returns `200 {"status": "ok"}` or `503 {"status": "degraded"}` unauthenticated so `systemd`/local watchdogs can probe liveness; detailed component diagnostics (`sqlite_ok`, `graph_store_ok`, `free_disk_gb`, `queue_depths`) are included **only** when called from `127.0.0.1` or with an authenticated session / Bearer token.
  * `GET /api/v1/health/sources` (`DVE.7`): **requires an authenticated session or Bearer token**; returns current reachability, last probe latency, and recent `common_source_health` status history for each configured data source without exposing connection passwords.
* **Optional scrape metrics (`GET /api/v1/metrics`):** restricted to `127.0.0.1` or Bearer token (`operations:read`); emits Prometheus text-exposition counters and histograms (`dsm_operations_total`, `dsm_operation_duration_seconds`, `dsm_queue_depth`, `dsm_http_request_duration_seconds`) computed in memory using stdlib counters—zero metrics daemon installed on the host.

### Consequences

* Good, because `FDM-INF.1` (`DP-15`) gets both a concrete **4.0 TB NVMe/SSD (`20k IOPS`, `500 MB/s`)** specification and a transparent linear formula for larger sites, and all 10 operation types have testable latency targets.
* Good, because tiered auth on `/api/v1/health`, `/api/v1/health/sources`, and `/api/v1/metrics` supports `systemd` probes without leaking internal source names to unauthenticated network callers.
* Bad, because operators do not get a bundled Grafana dashboard UI out of the box (metrics are scraped if an institutional monitor exists).

### Confirmation

* R8 capacity & soak suite generates the 5,000-unit / 50,000-edge reference model across 200 instances and verifies every §1 latency budget and the 32 GB RAM ceiling under full `4 + 4 + 2` concurrent worker load.
* Observability tests verify: every log line emitted inside a child operation carries its `operation_id` with secrets redacted; stopping the graph server flips `/api/v1/health` to `503`; and unauthenticated non-localhost calls to `/api/v1/health/sources` and `/api/v1/metrics` return `401`.

## Pros and Cons of the Options

### Per-operation-class budgets + concrete 4 TB SSD baseline & formula (chosen)

* Good, because procurement gets a concrete SSD specification (`FDM-INF.1`) while R8 qualification gets unambiguous pass/fail latency gates across every CSC workflow.
* Bad, because initial R3/R4 numbers are engineering baselines refined empirically during R8 soak tests.

### HTTP endpoint p95 budgets only

* Good, because API response times are easy to measure.
* Bad, because background operations (`MDG`, `SMM`, `SCG`, `FDM`, `ADM`, `DVE`) dominate user wait time and CI pipeline duration.

### Unbounded best-effort execution

* Good, because no synthetic benchmark generator is needed.
* Bad, because `FDM-INF.1` remains unresolved and R8 has no objective acceptance criteria.

### Structured JSON logs + tiered health & text metrics endpoints (chosen)

* Good, because it requires zero extra daemons or wheels offline while giving `operation_id` correlation, `systemd` supervision, and optional Prometheus scraping.
* Bad, because visual time-series dashboards require external scraping tools.

### Bundled Prometheus / VictoriaMetrics + Grafana stack

* Good, because rich operator dashboards ship locally.
* Bad, because installing, securing and upgrading two extra server daemons offline violates QA-10.

### Unstructured stdout logs only

* Good, because zero logging code is added.
* Bad, because `systemd` gets no dependency health signal and multi-process logs cannot be filtered reliably by `operation_id`.

## More Information

* [SRS FDM-INF.1, SMM.30, DVE.7, 23, 27, 78](../../requirements/SRS.md), [UXD §6](../UXD.md), [SDP Increment 8](../../planning/SDP.md)
* Code: `dve/src/dve/config.py`, `dve/src/dve/dve.ini`
* Related: ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0011, ADR-0012, ADR-0013, ADR-0014, ADR-0015, ADR-0019
* Revisit if real institutional models exceed `10,000` software units / `200,000` relationships or raw field ingestion exceeds `50 GB/day`, adjusting the host RAM/SSD tier accordingly.
