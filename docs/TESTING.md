# Testing and evaluation

The current integration suite and HTTPS results are in [PHASE4.md](PHASE4.md). The Phase 1 checks below explain the original scaffold baseline.

Primary reference: brief R2 Option A p. 8 and R7 pp. 11–12. [EVALUATION_PLAN.md](EVALUATION_PLAN.md) covers the required environment measurements, six minimum read/write runs, bottleneck interpretation and 3–5-page architectural comparison.

## What the initial tests prove

`backend/tests/test_api.py` uses FastAPI TestClient and explicit SQLAlchemy session doubles. It verifies HTTP response contracts, pagination envelopes, validation, missing resources, safe database failures, unknown routes/methods, safe unexpected errors, parameter binding and implemented OpenAPI. It does not prove PostgreSQL storage, database permissions, concurrency or completed authentication.

`backend/tests/test_postgres.py` is opt-in and uses actual PostgreSQL with the initial DDL in a rolled-back transaction. It covers conflicting/adjacent reservations, date-order rejection, duplicate active-loan rejection, damaged-state integrity, append-only audit and continued unavailability of an overdue active loan. It requires an existing new/empty `equiptrack_test_*` database. The fixture refuses another database name or an existing public schema with tables. It never substitutes SQLite. These are integrity tests, not simultaneous-connection races or complete application-flow tests.

Run from backend:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
```

To run real integration tests after provisioning a disposable empty PostgreSQL test database, set `TEST_DATABASE_URL` to its owner connection URL in the current shell, then run the same command. The database account must be able to create the btree_gist extension and schema objects. Do not use application, production or restored school data. Seven skipped integration checks are an unmet verification item, not a pass.

Frontend: `npm ci` then `npm run build`. This verifies bundling, not interaction or accessibility. Compose: `docker compose --env-file .env.example config --quiet` validates structure without connecting to a daemon. HTTPS smoke: `bash scripts/smoke.sh` only after trusted TLS/database startup. The smoke script uses curl with certificate verification enabled.

## Required later success/failure matrix

For **every final endpoint**, execute at least one successful and one failing request using curl, recording command, expected/actual status and JSON result. Include authenticated/supporting routes as well as the business API. Use synthetic fixtures and redact cookie/token values in published evidence. The existing smoke script has positive requests only and no per-endpoint recorded matrix; pytest does not replace this R2 evidence. Add a 400 malformed-JSON case, retained 422 schema-invalid cases, and the required 200/201/401/403-or-404/500 coverage as the final API is implemented.

| Area | Positive | Negative / race |
|---|---|---|
| Login/session | Correct synthetic password; logout invalidation | Wrong password, inactive account, expired/forged token, throttling, CSRF |
| Catalog/detail | Search/category/status/period, pagination, empty results | Invalid parameters, unknown ID, missing login, injection-like search |
| Request create | Serviceable item, future valid interval | Past/inverted/missing offset dates, damaged/retired/unavailable, role misuse |
| Request list/detail | Own rows; admin all rows | Cross-user ID/list leakage, invalid filters |
| Owner cancellation | Pending → canceled, retained history + audit | Nonowner, released/approved request, repeated cancel |
| Decision | Pending → approved/rejected, actor/time | Borrower role, stale state, overlapping approvals on two connections |
| Release | Approved valid time → one loan | Early/expired/not approved, active late loan, damaged, concurrent release |
| Return | Released → returned, available if serviceable | Duplicate/not released, damaged → maintenance, rollback on audit failure |
| Overdue | Late active vs returned-late distinction | Exact due boundary, unreleased expired request, timezone errors |
| Inventory/accounts | Authorized create/update/retire/deactivate | Borrower writes, duplicate asset/email, referenced hard delete, last-admin loss |
| Recovery/deployment | Restart persistence; safe restore; trusted second device | Untrusted/mismatched cert, private DB exposure, incomplete dump |

For races, synchronize two independent transactions before the critical change, then assert one winner and the expected safe conflict. Query final rows and audit counts. A sequential duplicate insert test does not establish race behavior. Any business mutation and audit must either both commit or both roll back.

## k6 experiments

`tests/performance/read.js` measures authenticated catalog availability. `tests/performance/write.js` measures authenticated request creation with the CSRF check. Use the same five-second warm-up, 30-second scenario and one-second think time at 1, 10 and 50 virtual users.

With Docker Engine running in Ubuntu WSL2 and the local CA generated, run:

```bash
bash scripts/performance.sh
```

The runner creates a new database and distinct project, validates the local certificate and stages the synthetic sessions before measuring either transaction. The summaries report transaction count and rate, mean and p95 response times, HTTP errors and validation errors. Separate resource samples and confirmed write counts accompany each run. See the [recorded results](PHASE6.md).

## Evidence and demonstration

Record actual commands, exit status, dependency versions and exact limitations in STATUS.md. Preserve raw test summaries under ignored test-results and sanitize any selected academic evidence. A complete demonstration must show all five transactions with two roles, a forbidden action, a conflicting approval/release, late borrowing and a damaged return, then verify database/audit state and restore recovery. No such complete-system result is claimed in Phase 1.
