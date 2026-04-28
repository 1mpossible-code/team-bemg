# Requirements for Security System

## Features Needed

- Different users have different permissions
- Do we need group permissions? (Maybe later.)
- We should be fine-grained about access... someone might be able, e.g., to update a record but not delete it.
- We must be able to easily add different types of security checks as required, e.g.,
    - login
    - auth key
    - dual factor
    - biometrics
    - IP address
- If there is no security record for some feature, it is open to all.

## Design

- Security data should be in our DB.
- First cut: let's use CRUD.
- Having a dictionary of bools to specify checks needed will permit easily adding more later.

## Current Implementation

### Modules

- `security/models.py` — `SecProtocol` and `ActionChecks` value objects. `ActionChecks` supports `login`, `valid_users`, `allowed_roles`, `api_key` / `valid_api_keys`, `pass_phrase`, and `codes`. New checks can be added here without touching call sites.
- `security/manager.py` — in-memory registry of protocols, plus `is_permitted(...)` which decodes the `Authorization: Bearer <jwt>` header via `server.auth.authenticate_request` and runs the checks for the given feature/action.
- `security/decorators.py` — `@require_protocol(feature, action)` for Flask routes. Reads the `Authorization` header, calls the manager, stashes the decision on `flask.g.security_result`, and either passes through, audit-logs, or returns 403 depending on env flags.
- `security/security.py` — legacy-format seed records (`temp_recs`) and the `read()` bootstrap that loads them into the manager. This is what the app calls at startup.

### Features with protocols today

| Feature     | READ           | CREATE                        | UPDATE                        | DELETE                        |
|-------------|----------------|-------------------------------|-------------------------------|-------------------------------|
| `people`    | open           | login + `ejc369@nyu.edu` only | open                          | open                          |
| `countries` | open           | login + role `admin`          | login + role `admin`          | login + role `admin`          |

`countries` write actions are wired in `server/countries_endpoints.py` via `@require_protocol(...)` on `CountriesList.post`, `Country.put`, and `Country.delete`. Read endpoints are intentionally left open so unauthenticated browsing keeps working. Other features (states, cities) currently have no protocol record, which means they are open to all per the rule above.

### Rollout / enforcement flags

Both default to off, so adding a new protocol record does not change live behavior until an operator opts in.

| Env var                  | Default | Effect                                                                                              |
|--------------------------|---------|-----------------------------------------------------------------------------------------------------|
| `SECURITY_ENFORCEMENT`   | `false` | When `true`, the decorator returns HTTP 403 for any denied request.                                 |
| `SECURITY_AUDIT_ONLY`    | `false` | When `true` (with enforcement on), denied requests still pass through but are logged at INFO level. |

Audit-only mode is the recommended way to roll a new protocol out: turn enforcement on with audit-only, watch the logs (e.g. through `/dev/logs`) for unexpected denials, then drop audit-only.

### Auth tokens

`server/auth.py` issues HS256 JWTs with `sub` (user id) and `role` claims. Allowed roles are `admin` and `user`. The `JWT_SECRET` env var controls signing; the default `dev-jwt-secret` is for local use only.

### Adding a security protocol to a new feature

1. **Register the feature** by adding an entry to `temp_recs` in `security/security.py`, e.g.:

   ```python
   STATES = 'states'

   temp_recs = {
       ...,
       STATES: {
           CREATE: {CHECKS: {LOGIN: True, ALLOWED_ROLES: [ROLE_ADMIN]}},
           UPDATE: {CHECKS: {LOGIN: True, ALLOWED_ROLES: [ROLE_ADMIN]}},
           DELETE: {CHECKS: {LOGIN: True, ALLOWED_ROLES: [ROLE_ADMIN]}},
       },
   }
   ```

2. **Decorate the route** in the matching endpoint module:

   ```python
   from security import require_protocol

   @require_protocol("states", "create")
   @states_ns.expect(state_create_model)
   def post(self):
       ...
   ```

   `@require_protocol` should be the outermost decorator so a 403 short-circuits before `@marshal_with` runs.

3. **Add a test** that flips `SECURITY_ENFORCEMENT=true` (see `server/tests/test_countries_security.py` as a template) covering: no token → 403, wrong role → 403, admin token → 2xx, and the relevant GET still 200.

No app-code changes are required beyond those three steps — `create_app()` already calls `security.security.read()` at startup, so the new entry is loaded automatically.
