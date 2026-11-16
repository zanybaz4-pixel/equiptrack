# Phase 4 integration verification

The [MIS 215 brief](MIS215_TermProject_Brief.pdf) remains the primary reference. Phase 4 connects its R2 protocol testing, R3 data integrity and R4 access controls to repeatable tests. The [current OpenAPI specification](openapi.json) was exported from the application and includes all 25 HTTP operations.

## Tested behavior

| Area | Evidence |
|---|---|
| Concurrent approvals and releases | Two distinct PostgreSQL application connections waited on the same equipment lock. One overlapping approval succeeded and the other returned 409. One release succeeded and the duplicate returned 409. The database contained one active loan and one audit event for each successful transition. |
| Period boundaries and custody | Adjacent periods could be approved. Equipment already out on loan blocked the next release. Tests checked that an active loan became overdue after its due instant, a late return cleared the overdue count, and release at the end of an approved period was rejected. |
| Return and history | A controlled audit insert failure returned 500 and rolled back the request, loan and equipment updates. A retry recorded damage and maintenance. A serviceable return restored availability, and later retirement preserved the loan history. |
| Ownership and sessions | Another borrower's reads and cancellation attempts returned 404. Borrowers could cancel their own pending requests and read their retained history. Tests rejected forged, expired and logged-out sessions, missing or cross-session CSRF tokens, and an unapproved Origin. Account deactivation and role changes revoked stored sessions. |
| Error handling | Malformed JSON returned 400. Invalid dates returned 422 without creating a request. A controlled database error returned a generic 500 with a matching request ID, and the application log and response excluded the synthetic note, cookie token, CSRF token, password and constraint name. |

The booking validator previously accepted Unix epoch timestamps written as strings. Both request creation and date-range availability now require extended ISO 8601 timestamps with `Z` or an explicit offset such as `+08:00`. The integration suite checks both endpoints and verifies that invalid requests leave no stored request.

## Reproduce the PostgreSQL tests

Run the existing pytest command from `backend/`. Set these environment variables to **disposable** PostgreSQL databases before running the full suite.

| Variable | Value |
|---|---|
| `TEST_DATABASE_URL` | Owner URL for an empty `equiptrack_test_*` database. The constraint suite applies migration DDL in transactions that roll back. |
| `TEST_API_DATABASE_URL` | Owner URL for a different `equiptrack_test_*` database with Alembic upgraded to head. The integrated API suite inserts unique synthetic fixtures and injects one temporary constraint to test rollback. |
| `TEST_API_RUNTIME_URL` | `equiptrack_app` URL for that same migrated API database. Create the restricted role before applying migrations so it receives the runtime grants. |

Run `python -m pytest -q`. The workflow suite uses real FastAPI routes and a PostgreSQL runtime connection pool. It controls only the lending clock for exact time-boundary cases. The login and session tests use the real clock. Without the database settings, the PostgreSQL cases skip.

## Recorded HTTPS protocol results

The final integration run on 2026-11-15 passed **41 pytest checks**, including all PostgreSQL cases. TestClient emitted one existing HTTPX deprecation warning. The frontend production build and Python dependency checks passed.

Run [protocol-check.py](../scripts/protocol-check.py) against a separately seeded, disposable HTTPS instance. Account and certificate setup are described in [PHASE2.md](PHASE2.md). The main curl matrix exercises both roles, all five transactions and the supported error paths. Supplemental probes check readiness with PostgreSQL stopped and liveness with an injected error in a separate process.

The [recorded results](phase4-curl-results.json) contain **67 matched outcomes**, with a successful and a failing request for each of the 25 OpenAPI operations. The main run used loopback Uvicorn HTTPS, PostgreSQL 17.12 for Windows and the restricted runtime role. Curl verified the certificate chain and hostname using a temporary CA. Schannel used best-effort revocation for that CA. Controlled tests used synthetic data only.

Phase 5 covers the required WSL2 Docker environment, Nginx TLS, successful restore, and access from a second device. Phase 6 covers measured load tests and the architecture comparison.
