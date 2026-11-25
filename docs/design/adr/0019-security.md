# ADR-0019: Security: authentication, sessions, authorization and secrets

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-25 |
| Deciders | CDR Board |
| Consulted | Development team, security, directory administrators, platform team |
| Kind | Reconcile |
| Traces | DVE.3, 7, 27, 77–78; MDG.8; QA-01, QA-10 |
| Resolves | DP-22 (EXT-IF-06 LDAP directory service protocol) |
| Decide by | Wave A1 (2026-12-04); §3 authorization by Wave B (2027-01-22) |
| Supersedes | — |

## Context and Problem Statement

DVE.3 requires authenticating users via a defined LDAP directory service (EXT-IF-06, DP-22) and restricting system access to each user's authorizations. DVE.27, 77–78 require authenticating non-interactive CI/automation and CLI requests. MDG.8 requires savable data-source configurations including connection user credentials. Earlier SDP §5 drafts proposed LDAP direct bind, stateless JWT browser tokens, and `.env` environment variables.

**As built (`1157784`) and security-audit findings:**

* **Directory:** `LdapDirectoryService` (`dve/src/dve/adapters/ldap_directory_service.py`) is a mock accepting `admin`/`admin` and `operator`/`operator`.
* **Session & CSRF:** Flask `itsdangerous` signed cookie (`session.permanent = True`, `86400 s` lifetime, `HttpOnly`, `SameSite=Lax`, `Secure` unset) paired with `Flask-WTF` `CSRFProtect` (`X-CSRFToken`). `role` is stored in the cookie and never checked (`login_required` only).
* **Critical session-fixation & credential-bleed bug (`dve/src/dve/api.py:179-191`):** `POST /api/login` overwrites `session["username"]` and `session["role"]` **without calling `session.clear()` or closing `session.get("conn_token")` in `DataSourceService`!** If User A connects CMDB and Git and User B subsequently signs in on the same browser/client without a prior logout, **User B inherits User A's `conn_token` and executes operations using User A's database and Git credentials** (`dve/tests/test_api.py:398-401` currently relies on this bug).
* **Secrets & credentials:** `secret_key = dev-insecure-change-me` is packaged inside `dve.ini` with no host override; unsaved data-source credentials live indefinitely in an unlocked `DataSourceService._sessions` dict as `"<user>:<password>"` (exposed in `DataSourceConfig.__repr__` and `to_dict()`), and cannot be saved across restarts (`MDG.8` unmet).
* **Browser `localStorage`:** `app.js` stores `dve.last-username`, `dve.last-db-username`, `dve.last-repo-username`, and per-user UI navigation state `dsm:state:<username>` (`selection`, `active_task`, `last_run`, `view`, `model_file`, `graph_mode`, `candidates`—no passwords or tokens).

## Decision Drivers

* Re-login must rotate session state cleanly (zero cross-user `conn_token` bleed), and logout or LDAP role revocation must take effect immediately (QA-01).
* Browser sessions must resist XSS token exfiltration (`HttpOnly`) and CSRF, without 1 Hz background task polling keeping idle sessions alive forever.
* CI/CD pipelines and CLI scripts need long-lived, scoped, revocable credentials independent of human LDAP passwords (`DVE.27, 77–78`).
* Secrets and saved `MDG.8` credentials must live outside Python packages on the Vault-less offline host (ADR-0004) with offline key-rotation support.

## Considered Options

* Browser sessions: Hardened Flask signed cookie (`HttpOnly`, `SameSite=Lax`, `Secure`) backed by SQLite `epoch` revocation and non-extending background polls (reconciling as-built cookies with server revocation)
* Browser sessions: Stateless JWT in `localStorage` or cookies (earlier SDP §5)
* Browser sessions: Full opaque server-side session store replacing Flask sessions
* Automation auth: Scoped SHA-256-hashed SaaG Bearer API tokens on `/api/v1/`
* Automation auth: Shared LDAP service user credentials passed on every CI call
* Application secrets: Mode-`0600` host files (`/etc/dsm/secret_key`, `/etc/dsm/data_key` keyring)
* Application secrets: Packaged `.ini` (as built) or process environment variables (earlier SDP §5)
* Saved `MDG.8` credentials: AES-256-GCM encrypted `common_data_source` rows in `dsm.db`
* Saved `MDG.8` credentials: Volatile memory only (as built) or external HashiCorp Vault

## Decision Outcome

Chosen options (reconciling the tested Flask cookie/CSRF code with enterprise LDAP, revocation and secret externalization):
* **LDAPv3 search-and-bind** over LDAPS/StartTLS via `ldap3` (+ `pyasn1`);
* **hardened Flask signed cookie with session reset on login and SQLite `epoch` revocation**;
* **scoped SHA-256-hashed Bearer API tokens** for CLI and CI clients;
* **mode-`0600` host secret/keyring files** outside `/opt/dsm/venv`; and
* **AES-256-GCM encrypted `common_data_source` rows** in `dsm.db`.

### 1. LDAP authentication (`EXT-IF-06`, `DP-22`), sessions and API tokens

* **LDAPv3 search-and-bind (`ldap3`):**
  * Protocol: LDAPv3 over **LDAPS (`636`)** or **StartTLS (`389`)**, verifying server certificates against the configured CA bundle (`ca_bundle_path`; requires CPython 3.9 linked against OpenSSL ≥ 1.1.1, ADR-0004 §2).
  * Wheelhouse: vendor pure-Python **`ldap3` (`2.9.1`) AND its transitive dependency `pyasn1` (`>=0.4.6`)** into `dve/wheelhouse/`.
  * Flow: (1) service bind DN searches user entry by `uid` / `sAMAccountName` under `base_dn` (`connect_timeout = 5 s`, `receive_timeout = 5 s`); (2) user DN bind verifies the supplied password (never stored or logged); (3) group memberships (`memberOf` / ` groupOfNames`) are read and mapped to SaaG roles (§3).
  * `[directory] backend = ldap | mock` selects the adapter (`ADR-0003`); `mock` is refused at start-up in `production` mode (`ADR-0004 §3`), and `dev/compose.yaml` adds an OpenLDAP seed container for contract tests.
* **Hardened browser sessions & session-fixation fix:**
  * **Mandatory login reset:** `POST /api/login` **always** closes any prior `session.get("conn_token")` in `DataSourceService`, calls `session.clear()`, generates a fresh `conn_token`, and writes `{username, epoch, issued_at, last_activity_at, conn_token}` (`dve/tests/test_api.py:398-401` is updated to reconnect sources explicitly after user switch).
  * **Server-side epoch & role lookup:** every authenticated request reads `dve_user(username PK, epoch INTEGER, roles_json TEXT, roles_checked_at TEXT, disabled INTEGER)` in `dsm.db` (`ADR-0007`). Role claims are never trusted from the cookie. Logout (or admin revocation) increments `epoch`, invalidating all cookies of that user immediately.
  * **Non-blocking group refresh & idle timeout:** if `roles_checked_at` is older than `15 min`, group refresh runs with a tight `2 s` timeout (falling back to cached roles with a warning if LDAP is transiently slow rather than stalling active requests). Interactive requests update `last_activity_at` (at most once per `60 s`) against a `30 min` idle timeout and `12 h` absolute timeout; **background 1 Hz polling requests carrying `X-Background-Poll: 1` (`ADR-0015 §1`) verify session validity without advancing `last_activity_at`** so unattended tabs still time out after `30 min`. Unsaved entries in `DataSourceService._sessions` carry the same TTL and are swept automatically.
  * Cookie flags: `HttpOnly=True`, `SameSite="Lax"`, and `Secure=True` in `production` mode; CSRF stays enforced via `Flask-WTF` on all cookie-authenticated mutating requests.
* **Automation & CLI Bearer tokens (`DVE.27, 77–78`):**
  * Stored in `dve_api_token(token_id PK, name, token_sha256 UNIQUE, owner_user, scopes_json, project_scope NULL, created_at, expires_at, last_used_at NULL, revoked_at NULL)`.
  * Raw token (`32` random bytes prefixed `dsm_tok_`) is displayed once on creation; only its `SHA-256` digest is stored.
  * Scopes cover all `/api/v1/` automation needs: `evaluation:run`, `verification:run`, `analysis:run`, `operations:read`, `operations:cancel`, `field_records:upload`, `reports:read`. Bearer-token requests are accepted only on `/api/v1/`, are exempt from browser CSRF, and log token `name`/`token_id` in `common_audit_event`.

### 2. Host secrets, encrypted `MDG.8` credentials and key rotation

* **Host secret files (`/etc/dsm/`, mode `0600`, owned by `dsm`, ADR-0004 §3):**
  * `/etc/dsm/secret_key`: 32 random bytes signing Flask cookies.
  * `/etc/dsm/data_key`: multi-line keyring file (`<key_id>:<base64_32_byte_key>` per line; **first line is the active encryption key**, subsequent lines are retired keys retained for decryption during rotation).
  * `DSM_SECRET_KEY` and `DSM_DATA_KEY` environment overrides are permitted in `development` mode only and stripped from every child/subprocess environment (`ADR-0006`, `ADR-0008`).
* **Saved data-source configurations (`MDG.8`, `common_data_source` in `dsm.db`):**
  * Passwords/tokens are encrypted using **AES-256-GCM** (`cryptography.hazmat.primitives.ciphers.aead.AESGCM` with a fresh 96-bit random nonce prepended to ciphertext and `(source_id, source_type, connection_address)` bound as AEAD `associated_data` so ciphertexts cannot be transplanted onto attacker-controlled URLs!).
  * `cryptography` (`43.0.3`, statically linking OpenSSL 3.x) + `cffi` + `pycparser` are placed in **`common/wheelhouse/`** (`ADR-0004`).
  * **Offline key rotation:** `dsm rotate-data-key` prepends a new `<key_id>:<key>` to `/etc/dsm/data_key` and re-encrypts all `common_data_source` rows inside a SQLite transaction, allowing old keys to be pruned safely.
  * API responses omit secrets (`has_secret: true`); child operations receive `source_id` and decrypt inside the worker at connect time. Unsaved session-only configs mask secrets in `DataSourceConfig.__repr__` and log redaction filters (`dve`, `mdg`, `common`).

### 3. Role-based authorization and shared source access (open, decide by Wave B)

* **Question:** how do LDAP groups map to SaaG roles and per-project permissions across interactive users and CI API tokens (`DVE.3`, `MDG.8`, `DVE.78`)?
* **Scope to settle in Wave B:**
  1. Role permission matrix (building on `ADMIN`, `ARCHITECT` / `OPERATOR`, `VIEWER`, `AUTOMATION`) governing: managing `system`/`project`-scoped `common_data_source` entries (`MDG.8`), uploading field records (`FDM.2`), creating/editing Working Models (`DVE.17`), cancelling operations (`ADR-0006`), approving/selecting evaluation profiles (`DVE.77`), and minting API tokens;
  2. LDAP group DN → role mapping configuration in `/etc/dsm/dve.ini`;
  3. Rules allowing CI Bearer tokens (`evaluation:run`) to use `project`- or `system`-scoped `common_data_source` entries without impersonating an interactive user.

### Consequences

* Good, because fixing login session reset eliminates cross-user credential bleed immediately, epoch checks make logout/revocation instant, and AEAD `associated_data` prevents credential-redirect attacks.
* Good, because `X-Background-Poll: 1` preserves genuine 30-min idle session expiry despite 1 Hz UI polling, and `/etc/dsm/data_key` keyring format makes key rotation concrete offline.
* Bad, because every authenticated request performs one primary-key SQLite lookup on `dve_user` (sub-millisecond under WAL).

### Confirmation

* Regression & security test (`dve/tests/test_api.py`): User A connects CMDB/Git, User B calls `POST /api/login` on the same client—asserts User A's `conn_token` is closed and User B has zero connected sources.
* Contract tests against `dev/` OpenLDAP: valid search-and-bind, wrong password, unknown user, expired/bumped `epoch`, idle timeout advancing only on interactive calls (not `X-Background-Poll: 1`), and Bearer token scope enforcement on `/api/v1/`.
* Crypto & rotation tests: verify AES-256-GCM round-trip, AEAD failure when `connection_address` is tampered, `dsm rotate-data-key` re-encryption, zero secrets in `GET` responses, `repr()`, `common_operation.inputs`, or logs, and `production` start-up refusal on `mock` directory or insecure key permissions.

## Pros and Cons of the Options

### Hardened Flask signed cookie with SQLite `epoch` revocation (chosen)

* Good, because it preserves `HttpOnly` + `Flask-WTF` CSRF protection while adding instant server-side logout/role revocation via one tiny table.
* Bad, because a stolen cookie remains usable from another IP until idle timeout or `epoch` bump.

### Stateless JWT (earlier SDP §5)

* Good, because signature verification needs no database read.
* Bad, because immediate logout/role revocation reintroduces a server-side blocklist anyway, and storing JWTs in `localStorage` exposes sessions to XSS.

### Full opaque server-side session store

* Good, because zero session metadata sits in the cookie.
* Bad, because it replaces tested Flask session plumbing for negligible gain once `role` and `epoch` live in `dve_user`.

### Scoped SHA-256-hashed Bearer API tokens (chosen)

* Good, because Jenkins pipelines get least-privilege, revocable credentials without storing human LDAP passwords.
* Bad, because token lifecycle UI and CLI commands must be built.

### Shared LDAP service account in CI

* Good, because no token table is needed.
* Bad, because rotating a shared password breaks every pipeline at once and offers no per-pipeline scope or audit attribution.

### Mode-`0600` host keyring files + AES-256-GCM in SQLite (chosen)

* Good, because upgrades of `/opt/dsm/venv` never touch secrets, subprocess environments stay clean, and `MDG.8` credentials persist safely with key rotation.
* Bad, because losing `/etc/dsm/data_key` without a custodial backup (`ADR-0004 §5`) renders saved data-source passwords unrecoverable.

### Packaged `.ini` or environment variables / external Vault

* Good, because `.env` is simple in containers and Vault centralizes rotation.
* Bad, because packaged `.ini` leaks secrets inside wheels, environment variables leak into child environments unless scrubbed everywhere, and no Vault server exists on the air-gapped host.

## More Information

* Code: `dve/src/dve/api.py`, `dve/src/dve/adapters/ldap_directory_service.py`, `dve/src/dve/services/data_source_service.py`, `dve/src/dve/config.py`, `mdg/src/mdg/domain/data_source.py`
* Related: ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0014, ADR-0015, ADR-0020
* Revisit if institutional SSO (SAML 2.0 / OIDC) replaces direct LDAPv3, or if an on-premises HSM / PKCS#11 provider becomes available for wrapping `data_key`.
