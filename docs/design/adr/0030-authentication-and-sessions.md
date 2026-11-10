# ADR-0030: Authentication and session management

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, security, directory service administrators |
| Kind | Reconcile |
| Traces | DVE.3, 27, 77–78; QA-01 |
| Closes | CDR-22 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

DVE.3 requires authentication against a defined LDAP directory service, with access limited to each user's authorizations. DVE.27 adds automation clients (Jenkins, CLI). CDR-22 leaves the LDAP protocol open. SDP §5 specifies an LDAP direct bind with stateless JWT sessions.

As built:

* `LdapDirectoryService` is a mock that accepts two fixed users (`admin`, `operator`) and returns a `Role`.
* The session is Flask's default signed cookie. It holds `username`, `role` and a connection token; the lifetime is `session_lifetime` (24 h) and the secret key comes from `dve.ini` (dev default `dev-insecure-change-me`).
* There is no automation-client authentication.

## Decision Drivers

* Logout and role changes must take effect immediately (QA-01).
* Browser sessions must resist XSS token theft and CSRF.
* Automation clients cannot do an interactive login and need long-lived, revocable, scoped credentials.
* There is one backend (ADR-0004), so stateless tokens do not need to be verified elsewhere.

## Considered Options

* Sessions: a Flask signed cookie (as built) / stateless JWT (SDP §5) / an opaque session ID with a server-side session store
* Automation: a shared service account with LDAP bind / personal or service API tokens issued by SaaG

## Decision Outcome

Chosen options: **LDAP search-and-bind**, **opaque server-side sessions** for browsers, and **SaaG-issued API tokens** for automation clients. Server-side sessions can be revoked at once, and the session store already exists (PostgreSQL, ADR-0008). JWT's main advantage, verification without shared state, brings no benefit with a single backend, and it makes revocation harder.

* **LDAP protocol (closes CDR-22):**
  * LDAPv3 over LDAPS (port 636), or StartTLS on 389. Certificates are verified against the configured CA bundle. The `ldap3` library is used.
  * Flow:
    1. A configured service account binds and searches the user by `uid`/`sAMAccountName` under a base DN.
    2. SaaG binds as the found DN with the given password.
    3. SaaG reads group memberships for authorization (ADR-0031).
  * The password is never stored or logged.
* **Browser sessions:**
  * The session ID is a random 256-bit value in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie. The session row (user, roles, created, last seen, expiry) lives in PostgreSQL.
  * Idle timeout is 30 minutes and absolute timeout is 12 hours. Both are configurable.
  * Logout deletes the row.
  * State-changing requests also require a CSRF header token.
* **Automation clients:**
  * A user with the right role (ADR-0031) creates API tokens with a name, scopes (e.g. `evaluation:run`) and expiry.
  * Only a hash of the token is stored. The client sends `Authorization: Bearer <token>`.
  * Tokens can be revoked in the UI. Their use is recorded in the audit trail (ADR-0035).
* **Mock:** the fixed-user mock stays only as a test fake under `tests/fakes/` (ADR-0003). The development stack gets an OpenLDAP container in `dev/compose.yaml`.

### Consequences

* Good, because revocation is immediate for both sessions and tokens, and the browser never holds a bearer token.
* Good, because CI pipelines get scoped, revocable credentials without sharing a person's password.
* Bad, because each request needs a session lookup, a cheap indexed read.
* Bad, because the LDAP service account needs provisioning by directory administrators, and its secret must be managed (ADR-0032).

### Confirmation

* Integration tests against the dev OpenLDAP cover valid login, wrong password, unknown user, and TLS failure.
* Tests show that logout and token revocation invalidate the credential on the next request.
* A security test asserts the cookie flags and that the CSRF check rejects requests without the header.

## Pros and Cons of the Options

### Flask signed cookie (as built)

* Good, because it needs no server state.
* Bad, because it cannot be revoked before expiry (logout only clears the browser copy). The role is frozen in the cookie for 24 h, and its integrity depends on a secret currently stored in an ini file.

### Stateless JWT (SDP §5)

* Good, because it can be verified without shared state, and it works for the CLI too.
* Bad, because revocation needs a deny list, which brings back state. Tokens kept in browser storage are exposed to XSS.

### Opaque server-side sessions + API tokens

* Good, because it is revocable, follows standard browser practice, and gives automation clients separate credentials.
* Bad, because it needs a session store, which already exists.

## More Information

* Code: `dve/src/dve/adapters/ldap_directory_service.py` (mock), `dve/src/dve/api.py`
* Related: ADR-0005, ADR-0008, ADR-0028, ADR-0031, ADR-0032, ADR-0035
