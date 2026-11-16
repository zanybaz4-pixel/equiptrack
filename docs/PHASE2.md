# Phase 2 backend and verification

For the current browser workflows, see [PHASE3.md](PHASE3.md). This page records Phase 2 evidence.

The MIS 215 brief remains the primary academic reference. The Phase 2 API implements all five EquipTrack transactions over REST. Account, inventory, dashboard and audit operations support those transactions. All provisioning and verification in this phase use synthetic records.

## Start and sign in

Follow the HTTPS setup in [README.md](../README.md). Migration `0002_sessions` adds the authentication table and grants writes to the restricted application role. After running the catalog seed, explicitly provision accounts:

```bash
docker compose --profile tools run --rm seed python -m app.seed_accounts
```

The first run generates distinct passwords for the demonstration custodian, student and faculty accounts. Keep the generated passwords privately. Re-running preserves existing accounts and passwords. The browser supports sign-in, sign-out and catalog browsing. The dedicated borrowing and administration screens are scheduled for Phase 3.

Use the exact HTTPS browser origin as `APP_ORIGIN`. Send `Origin` on login and authenticated writes. Login sets the `__Host-equiptrack` cookie and returns a CSRF token. Send the cookie and `X-CSRF-Token` on authenticated writes. The token is also returned by `GET /api/auth/me` for an existing session. The browser stores it in memory. Read requests use the session cookie. The API enforces current account status, role and ownership.

## Route reference

The paths below are relative to `/api`. [OpenAPI](openapi-phase2.json) describes the actual input and output shapes. Body-bearing endpoints accept JSON. A malformed body returns 400. Schema validation returns 422. Missing or expired sessions return 401. Authorization failures return 403, with 404 for requests outside a borrower's scope. State conflicts return 409. Database connection failures return 503. Errors use `{error:{code,message,request_id}}`.

| Method and path | Access | Result |
|---|---|---|
| GET /health/live | Public | Process liveness |
| GET /health/ready | Public | Schema connectivity |
| POST /auth/login | Trusted Origin | Cookie, current user and CSRF token |
| GET /auth/me | Signed in | Current user and CSRF token |
| POST /auth/logout | Signed in | Revokes the session and clears the cookie |
| GET /categories | Signed in | Category list |
| GET /equipment | Signed in | Paginated catalog with filters and optional booking period |
| GET /equipment/{equipment_id} | Signed in | Item details and availability |
| GET /requests | Signed in | Visible requests with status, search and custody filters |
| POST /requests | Borrower | Creates a pending request |
| GET /requests/{request_id} | Owner or custodian | Request detail and custody history |
| DELETE /requests/{request_id} | Owner | Cancels a pending request and retains it in history |
| PATCH /requests/{request_id}/decision | Custodian | Approves or rejects a pending request |
| POST /requests/{request_id}/release | Custodian | Records custody within the approved period |
| PUT /requests/{request_id}/return | Custodian | Records return and updates condition and service status |
| GET /profile | Signed in | Current account |
| PATCH /profile | Signed in | Corrects the account display name |
| GET /users | Custodian | Paginated account list |
| POST /users | Custodian | Provisions an account |
| PUT /users/{user_id} | Custodian | Updates name, role and activation status |
| POST /categories | Custodian | Adds a category |
| POST /equipment | Custodian | Adds an inventory item |
| PUT /equipment/{equipment_id} | Custodian | Updates an inventory item |
| GET /dashboard | Signed in | Visible requests by status and overdue count |
| GET /audit-logs | Custodian | Paginated audit history with optional entity filter |

List endpoints that return arrays accept offset and limit as shown in OpenAPI. Catalog availability supports a current snapshot or paired `borrow_at` and `due_at` timestamps with offsets. An open overdue loan blocks new bookings until return, including future dates queried while the item is overdue. Adjacent reservations remain valid. The release operation checks actual custody again.

## Implementation details

- Argon2id hashes passwords through [argon2-cffi](https://pypi.org/project/argon2-cffi/25.1.0/). The database stores a SHA-256 digest of each random session token and its user ID and eight-hour expiry in `auth_sessions`. Account deactivation or role changes revoke stored sessions. The application bounds simultaneous password checks. The Nginx configuration includes per-IP login throttling.
- Reservation changes lock the equipment item first, then the request. The exclusion constraint prevents overlapping approved reservations, while a partial unique index limits each item to one active loan. A damaged return marks the item for maintenance. Request, loan, equipment and audit writes commit together.
- Six business tables remain in place. `auth_sessions` is a supporting table with a token digest primary key, user foreign key, expiry timestamp and expiry/user indexes. Runtime grants permit only the needed table operations. The audit trigger prevents mutation of existing audit rows.

## Verification

The test environment ran a temporary, loopback-only PostgreSQL 17.12 instance from the official portable Windows archive. Both migrations ran. The API used a restricted database role. Curl used Uvicorn HTTPS with a temporary CA passed through `--cacert`. Schannel used best-effort revocation for that local CA, with chain and hostname checks enabled.

- **33 pytest checks passed**, including real PostgreSQL exclusions, loan uniqueness, damaged-item restrictions, overdue and late return behavior, and full rollback when the return audit insert fails. TestClient emitted one HTTPX deprecation warning.
- **62 curl cases passed** in the main matrix. Two overlapping approvals produced 200 and 409, while two concurrent releases produced 201 and 409. The matrix checked role and ownership failures, CSRF, malformed JSON, session revocation at logout, and maintenance after damaged return.
- The readiness endpoint returned 503 after the temporary PostgreSQL process stopped. Liveness remained 200. A separate controlled fault in the liveness handler exercised HTTP 500 over HTTPS.
- The 65 recorded outcomes include at least one successful and one failing request for every one of the 25 OpenAPI operations.
- The frontend production build, Python compilation, dependency checks and Compose structure validation passed.

See [recorded curl outcomes](phase2-curl-results.json). To repeat the main matrix on a fresh synthetic deployment, set `PROTOCOL_TEST_ORIGIN` to the loopback HTTPS origin and `PROTOCOL_TEST_ACCOUNTS` to a JSON object with `student`, `faculty` and `admin` entries containing generated email/password pairs. Run `python scripts/protocol-check.py > test-results/phase2-curl.json`. If needed, supply the local CA path through `PROTOCOL_TEST_CA`. The script changes synthetic data, including returning one item as damaged. Use a fresh test database for a new run. Status results omit credentials, cookies, CSRF values and response bodies.

The Windows test proves database and API behavior. WSL2 Docker Engine startup, Nginx TLS and rate-limit verification, second-device access, and browser workflow verification remain open. The full browser workflow, account and request collection-point notices, k6 runs, architectural comparison and academic submission artifacts are later phases.
