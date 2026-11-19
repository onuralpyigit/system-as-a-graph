# ADR-0030: Security: authentication, sessions, authorization and secrets

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-19 |
| Deciders | CDR Board |
| Consulted | Development team, security, directory administrators, platform team |
| Kind | Reconcile |
| Traces | DVE.3, 7, 27, 77–78; MDG.8; QA-01, QA-10 |
| Resolves | DP-22 (EXT-IF-06 LDAP directory service protocol) |
| Decide by | Wave A (2026-11-27); §3 authorization by Wave B (2027-01-22) |
| Supersedes | — (absorbs the planned ADR-0030 and the former ADR-0030) |

## Context and Problem Statement

DVE.3 requires authentication against a defined LDAP directory service, with access limited to each user's authorizations. DVE.27 adds automation clients (Jenkins, CLI). MDG.8 requires data-source configurations, including user information, to be savable. SDD §2.3 leaves the LDAP protocol (EXT-IF-06) open. SDP §5 specifies LDAP direct bind, stateless JWT sessions, and environment variables (`.env`) for secrets.

As built (`1157784`):

* **Directory:** `LdapDirectoryService` is a mock. It accepts `admin`/`admin` and `operator`/`operator` and returns a `Role` (`ADMIN`, `OPERATOR`).
* **Session:** Flask's signed cookie (itsdangerous), holding `username`, `role` and `conn_token`.
  * `session.permanent = True`, with `session_lifetime` = 86,400 s.
  * `SameSite=Lax`; `HttpOnly` by Flask default; `Secure` not set.
* **CSRF:** Flask-WTF `CSRFProtect`, with the `X-CSRFToken` header from `GET /api/csrf-token`.
* **Authorization:** only `login_required`. The role is stored but never checked. Automation clients have no authentication.
* **Secret key:** in the packaged `dve.ini` (`secret_key = dev-insecure-change-me`), with no override.
* **Data-source credentials:**
  * held per session in memory (`DataSourceService._sessions`, keyed by `conn_token`), joined as `"<user>:<password>"`, lost on restart, and not savable;
  * passed to operations as spawn arguments, with no broker;
  * kept out of the `git` command line by the environment credential helper, with errors redacted (ADR-0010).
* **Browser storage:** only the last usernames are kept in `localStorage`.

## Decision Drivers

* Logout and role changes must take effect promptly. Browser sessions must resist XSS token theft and CSRF.
* Automation clients need long-lived, revocable, scoped credentials.
* There is one backend process on one host (ADR-0004), with an SQLite store (ADR-0008). No vault exists on the offline host.
* No credential may appear in plain text in logs, process arguments, records or the repository (QA-01), and rotation must not need code changes.
* The tested session and CSRF code should be kept if it can meet these drivers.

## Considered Options

* Sessions: the hardened Flask signed cookie with server-side revocation (as built, extended) / stateless JWT (SDP §5) / opaque server-side sessions
* Automation: SaaG-issued API tokens / a shared service account with LDAP bind
* Application secrets: host files outside the package / the packaged `.ini` (as built) / environment variables (SDP §5)
* Data-source credentials: encrypted in SQLite, with session memory for unsaved connections / memory only (as built) / plain text / an external vault

## Decision Outcome

Chosen options:

* **LDAP search-and-bind** through `ldap3`;
* **the hardened Flask signed cookie with epoch revocation** in SQLite;
* **SaaG API tokens** for automation clients;
* **secret files outside the package**;
* **AES-256-GCM-encrypted saved credentials**.

This keeps the tested cookie and CSRF code and adds what it lacks: immediate logout everywhere, roles that change without waiting for expiry, and savable credentials, with no new service.

### 1. Authentication (EXT-IF-06) and sessions

* **LDAP:**
  * LDAPv3 over LDAPS (636) or StartTLS (389), with certificates verified against a configured CA bundle.
  * The library is `ldap3`, pure Python, added to `dve/wheelhouse/`.
  * Flow:
    1. A service account binds and searches the user by `uid` or `sAMAccountName` under a base DN.
    2. SaaG binds as that DN with the given password.
    3. SaaG reads the groups for §3.
  * The password is never stored or logged.
  * `[directory] backend = ldap | mock` selects the adapter (ADR-0003). `mock` is refused in production mode (ADR-0004).
* **Browser sessions:**
  * The cookie holds only `username`, `epoch`, `issued_at`, `last_seen` and `conn_token`; the role leaves it.
  * A `dve_user(username, epoch, roles, roles_checked_at)` row is read on every request. A mismatched epoch is rejected, and roles come from the row.
  * Logout increments `epoch`, invalidating every cookie of that user; an administrator can do the same. Roles are refreshed from LDAP at login, and when `roles_checked_at` is older than 15 minutes.
  * Flags: `HttpOnly`, `SameSite=Lax` (as built), and `Secure` in production mode.
  * Timeouts: 12 h absolute, replacing the 24 h lifetime, and 30 min idle, refreshed at most once a minute. Both are configurable.
  * CSRF stays as built.
* **Automation clients (DVE.27, 77–78):**
  * A user with the right role creates named tokens with scopes (e.g. `evaluation:run`) and an expiry.
  * A token is 32 random bytes, shown once, and only its SHA-256 is stored, in `dve_api_token`.
  * Clients send `Authorization: Bearer <token>`. Token requests are exempt from CSRF and accepted only on `/api/v1/` (ADR-0005).
  * Revocation is in the UI. Token use is audited (ADR-0008).
* **Development:** `dev/compose.yaml` gains an OpenLDAP container with seed users and groups. The mock stays for tests and quick local runs.

### 2. Secrets and credentials

* **Application secrets:**
  * The packaged `dve.ini` keeps development defaults only.
  * `/etc/dsm/dve.ini` (or the directory in `DSM_CONFIG`) holds paths only: `secret_key_file = /etc/dsm/secret_key` and `data_key_file = /etc/dsm/data_key`.
  * The secret files are owned by the service user with mode 0600, created by the install script with `secrets.token_bytes(32)`, and never committed.
  * In development, `DSM_SECRET_KEY` and `DSM_DATA_KEY` may supply the values. The task runner removes them from every child process and subprocess environment.
  * In production mode, start-up refuses a missing secret, a secret file readable by others, or the development secret key.
* **Saved data-source configurations (MDG.8):**
  * Each is a `dve_data_source` row (ADR-0008, ADR-0010).
  * Its password or token is encrypted with AES-256-GCM (`cryptography`'s `AESGCM`; 43.0.3 is already in `mdg/wheelhouse/`). Each row stores a key ID, so the key can be rotated by re-encrypting.
  * Configurations belong to their creator, and sharing follows §3.
* **Unsaved connections:** kept per session in memory, as built.
* **Use:**
  * API responses never contain the secret field.
  * For a saved configuration, operation arguments carry `data_source_id` only, and the child decrypts at the moment of use.
  * An unsaved connection's value may still be a spawn argument, but never goes into records, logs or `repr()`. `DataSourceConfig.__repr__` masks `user_info`.
* **Git and logging:**
  * The credential helper stays as built, and TLS verification is turned on (ADR-0010).
  * A log filter on the `dve` and `mdg` loggers redacts secret fields and URL user-info.

### 3. Authorization (open, decide by Wave B)

* **Question:** how are DVE.3's "authorizations" defined and enforced per operation?
* **Options to weigh:**
  * roles mapped from LDAP groups;
  * per-project permissions;
  * a single role.
* **Constraints already set:**
  * roles are read from the `dve_user` row (§1);
  * the as-built `ADMIN` and `OPERATOR` values are the starting vocabulary;
  * API-token scopes and the sharing of saved configurations depend on this decision.

### Consequences

* Good, because the tested session and CSRF code is kept, and logout and role changes take effect on the next request.
* Good, because CI pipelines get scoped, revocable credentials without sharing a person's password.
* Good, because MDG.8 is met, saved connections survive restarts, and secrets live outside the package, so upgrades cannot overwrite or expose them.
* Bad, because each request reads one indexed SQLite row, and the cookie is a bearer credential until its epoch is bumped (limited by the flags and timeouts).
* Bad, because the LDAP service account must be provisioned, and losing the data-encryption key loses saved credentials. Its backup belongs to ADR-0004 §5.
* Bad, because anyone with the service user's rights can read the key files. That is inherent without a vault, and mitigated by host hardening.

### Confirmation

* Integration tests against the dev OpenLDAP: valid login, wrong password, unknown user, TLS failure.
* Logout and token revocation invalidate the credential on the next request, including a copy of the cookie saved before logout.
* Production start-up fails with `[directory] backend = mock`, with the development secret key, or with a world-readable key file.
* The existing CSRF tests and the `mdg` tests that keep passwords out of `git` arguments keep passing.
* An operation started from a saved configuration has no password in its spawn arguments or its `operation` row.
* `GET` on a configuration never returns the secret, and `repr(DataSourceConfig(...))` never contains it.

## Pros and Cons of the Options

* Hardened signed cookie with epoch revocation (chosen): Good, because it keeps tested code, and revocation needs one row per user. Bad, because the cookie is a bearer credential until revoked.
* Stateless JWT: Good, because it is verifiable without state. Bad, because revocation brings back state, and browser-held tokens are exposed to XSS.
* Opaque server-side sessions: Good, because every session is revocable. Bad, because it replaces working code for little gain on a single host.
* Host secret files (chosen): Good, because they are outside the package, with tight permissions. The packaged `.ini` ships inside the wheel, and environment variables are inherited by `git` and `gmake` unless scrubbed.
* Encrypted credentials in SQLite (chosen): Good, because they are savable with no new service. Bad, because of key management. Memory only violates MDG.8. A vault would be a new critical service offline.

## More Information

* Code: `dve/src/dve/adapters/ldap_directory_service.py` (mock), `dve/src/dve/ports/directory_service.py`, `dve/src/dve/api.py`, `dve/src/dve/services/data_source_service.py`, `dve/src/dve/services/task_service.py`, `dve/src/dve/dve.ini`, `dve/src/dve/config.py`
* Related: ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0008, ADR-0010
