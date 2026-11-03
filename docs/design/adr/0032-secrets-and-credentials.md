# ADR-0032: Secrets and data-source credential protection

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, security, platform team |
| Kind | Reconcile |
| Traces | MDG.8; DVE.3, 7; QA-01, QA-10 |
| Closes | — |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

SaaG holds two kinds of secret:

1. **Application secrets:** the session or cookie key, database passwords, the LDAP service account (ADR-0030), and the encryption key below.
2. **Data-source credentials:** the CMDB, source repository and package repository user information, which MDG.8 requires to be user-definable and *savable*.

As built:

* The Flask secret key is in `dve.ini` with a development default.
* Data-source credentials are kept per session in the API process's memory (`DataSourceConnections`). They are lost on restart and cannot be saved, which contradicts MDG.8. A second API process would not see them.
* Data-source credentials are sent to the worker inside the Celery task payload (`DataSourceConfig.user_info = "user:password"`). They pass through Redis in plain text.
* The Git adapter embeds the password in the clone URL, which is visible in the process list, and disables TLS verification (`http.sslVerify=false`).
* SDP §5 specifies environment variables (`.env`).

## Decision Drivers

* MDG.8: configurations, including user information, are savable.
* No credential may appear in plain text in message brokers, logs, process arguments or the repository (QA-01).
* On-premises deployment with Docker Compose. There is no existing secrets vault in the known environment.
* Rotation must be possible without code changes.

## Considered Options

* Application secrets: in `.ini` files (as built) / environment variables (SDP §5) / Docker secrets files mounted into containers
* Data-source credentials: per-session memory (as built) / saved in plain text / saved encrypted in the relational store / an external vault

## Decision Outcome

Chosen options: **Docker secrets files for application secrets**, with environment variables as a fallback for development. **Data-source credentials are saved encrypted in the relational store and referenced by ID everywhere else.**

* **Application secrets:**
  * Read from files under `/run/secrets/` (Compose `secrets:`), or from environment variables named `SAAG_*` in development.
  * They are never committed. The `.ini` files keep only non-secret settings (ADR-0039).
  * At start-up, the API refuses to run in production mode with a missing secret or a known development default.
* **Data-source credentials:**
  * A saved data-source configuration (ADR-0010) is a row in PostgreSQL. The password or token is encrypted with AES-256-GCM (`cryptography`'s `AESGCM`), using a data-encryption key loaded from a secret file.
  * The ciphertext row stores a key ID, so the key can be rotated by re-encrypting.
  * Configurations belong to their creating user. Shared configurations are an authorization decision (ADR-0031).
* **Use:**
  * API responses never contain the secret field; it is write-only.
  * Task payloads carry `data_source_id` only (ADR-0006). The worker decrypts at the moment of use and keeps the plain value in memory for the duration of the call.
* **Git:** credentials are supplied via `GIT_ASKPASS` (a helper that reads them from the worker's memory or environment for that one subprocess), not in the URL. TLS verification is on, with an optional CA bundle path (ADR-0010).
* **Logging:** a log filter redacts the values of known secret fields and URL user-info. The tests check that it does.

### Consequences

* Good, because MDG.8 "savable" is satisfied, and connections survive restarts and multiple API processes.
* Good, because Redis, logs and process arguments no longer carry credentials.
* Bad, because there is key management: losing the data-encryption key makes saved credentials unrecoverable (users must re-enter them). The key's backup belongs to ADR-0040.
* Bad, because a compromised worker host can still read secrets in use. That is inherent; mitigated by host hardening.

### Confirmation

* A test asserts that the Celery message for a production task contains no `user_info` or password.
* A test runs a clone and asserts that the password is absent from the `git` process arguments.
* A test asserts that `GET` on a data-source configuration never returns the secret.
* Production start-up fails with the development secret key (test).

## Pros and Cons of the Options

### Application secrets in `.ini` / environment / secrets files

* `.ini`: Good, because it is simple. Bad, because it is committed or copied in plain text, and the dev default can reach production.
* Environment: Good, because it is the 12-factor standard. Bad, because it is visible to `docker inspect` and to child processes.
* Secrets files: Good, because they are not in the image or env, and Compose supports them natively. Bad, because there is slightly more deployment configuration.

### Data-source credentials in memory / plain / encrypted / vault

* Memory: Good, because nothing is persisted. Bad, because it violates MDG.8, breaks on restart, and leaks via the task payload.
* Plain: Bad, because it is unacceptable.
* Encrypted in PostgreSQL: Good, because it is savable and has no new service. Bad, because of key management.
* Vault: Good, because it is the strongest option. Bad, because there is no existing vault in the environment, and it would be a new critical service.

## More Information

* Code: `dve/src/dve/services/data_source_connections.py`, `dve/src/dve/worker.py`, `mdg/src/mdg/adapters/source_code/git_source_code_repository.py`, `dve/src/dve/dve.ini`
* Related: ADR-0006, ADR-0008, ADR-0010, ADR-0030, ADR-0031, ADR-0039, ADR-0040
