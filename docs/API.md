# REST API contract

This file preserves the Phase 1 design and API snapshot. Use [openapi.json](openapi.json) for the current API contract and [PHASE4.md](PHASE4.md) for its verification.

Base URL after HTTPS setup: `https://localhost:8443/api`. JSON requests/responses. Actual implemented OpenAPI is served at `/api/openapi.json`; Swagger UI is `/api/docs`. The checked-in `openapi-phase1.json` is an export from the application, not a promise that planned routes exist.

Primary protocol reference: brief **R2 Option A**, p. 8. The final API must cover all five transactions with at least eight endpoints and GET/POST/PUT-or-PATCH/DELETE, record curl success/failure per endpoint, and use 200, 201, 400, 401, 403 or 404, and 500 appropriately. The current scaffold is not yet R2-complete.

## Implemented in Phase 1

These development routes currently read synthetic catalog data without login. Authentication and role protection are Phase 2 prerequisites before broader deployment.

| Method/path | Input | 200 response | Documented failures |
|---|---|---|---|
| GET /health/live | none | status, service, phase; no database check | Generic unexpected 500 |
| GET /health/ready | none | status ready, database postgresql | 503 unavailable/unmigrated database |
| GET /categories | none | Array of id, name, description | 503 database failure |
| GET /equipment | q <=120 chars; category_id >0; availability enum; offset 0..100000; limit 1..100 | items, total, offset, limit | 422 invalid filters; 503 database failure |
| GET /equipment/{id} | positive integer item ID | One equipment object | 404 unknown; 422 invalid ID; 503 database failure |

Equipment shape:

```json
{
  "id": 1,
  "asset_code": "ET-PJ-001",
  "name": "Classroom projector",
  "description": "HD projector with HDMI cable and carry case.",
  "location": "Resource Center · Shelf A",
  "category_id": 1,
  "category": "Presentation",
  "condition": "good",
  "availability": "available"
}
```

Availability enum: available, reserved, on_loan, maintenance, retired. A current snapshot is not a future reservation guarantee. Page results sort by name then ID. Empty results return HTTP 200 and an empty items array. No raw ORM user/loan objects are serialized.

## Planned Phase 2 business endpoints — not yet implemented

All authenticated routes require a valid server-checked active user. Borrower paths filter ownership in SQL; fetching another user's request returns 404 to avoid disclosing its existence. Admin-only routes return 403 for borrowers. No request body may choose a borrower or acting administrator ID.

| Transaction | Method/path | Role | Body / query | Success | Key failures |
|---|---|---|---|---|---|
| T1 | GET /equipment | both | optional borrow_at + due_at together, search/filter/pagination | 200 page with period availability | 401, 422 invalid period |
| T1 | GET /equipment/{id} | both | positive ID, optional period | 200 equipment detail | 401, 404, 422 |
| T2 | GET /requests | both | status, q, date range, offset, limit | 200 own/all page | 401, 422 |
| T2 | POST /requests | borrower | equipment_id, borrow_at, due_at, purpose | 201 pending request + Location | 401, 403, 404, 409 conflict/unserviceable, 422 invalid/past dates |
| T2 | GET /requests/{id} | owner/admin | ID | 200 request + safe loan/status fields | 401, 404 |
| T2 | DELETE /requests/{id} | owner borrower | no body | 200 retained request, status canceled | 401, 404 nonowner, 409 no longer pending |
| T3 | PATCH /requests/{id}/decision | admin | decision approved/rejected, remarks optional | 200 decided request | 401, 403, 404, 409 state/overlap, 422 |
| T4 | POST /requests/{id}/release | admin | condition good/fair | 201 loan record | 401, 403, 404, 409 state/active loan/serviceability/time, 422 |
| T5 | PUT /requests/{id}/return | admin | condition good/fair/damaged, remarks optional | 200 returned loan + equipment status | 401, 403, 404, 409 not released/already returned, 422 |

This plan supplies nine business paths/method combinations spanning GET, POST, PATCH, PUT and DELETE. Supporting functions below are not extra core transactions. Do not count Phase 1 health routes toward completion of lending requirements.

Create request example (future contract; choose future dates relative to the demonstration):

```json
{
  "equipment_id": 1,
  "borrow_at": "2030-01-15T09:00:00+08:00",
  "due_at": "2030-01-15T12:00:00+08:00",
  "purpose": "Synthetic classroom presentation"
}
```

Decision body: `{"decision":"approved","remarks":"Synthetic approval"}`. Release body: `{"condition":"good"}`. Return body: `{"condition":"damaged","remarks":"Synthetic inspection finding"}`. Server supplies decision/release/return times; callers cannot falsify those timestamps.

Planned request output: id, equipment summary, safe borrower summary when admin, borrow_at/due_at, purpose, status, created_at, decision actor/time/remarks, canceled_at, optional loan, is_overdue, was_returned_late. List responses use items/total/offset/limit. Return response includes updated service_status so damaged availability is explicit.

## Planned supporting endpoints

POST `/auth/login`, POST `/auth/logout`, GET `/auth/me`, GET `/auth/csrf`; GET/PATCH `/profile`; GET `/dashboard`; POST/PATCH `/equipment`; GET/POST/PATCH `/users`; GET `/audit-logs`. Final user/inventory identifiers and schemas must be reflected in implemented OpenAPI and tested. There is no self-registration or default admin password.

Login will use JSON email/password over HTTPS and set Secure, HttpOnly, SameSite cookies. State-changing requests will require a session-bound CSRF token header and trusted same-origin request. Disabled accounts/expired sessions return 401. Roles and ownership are checked from current server-side state. Password hashes, cookies and credentials never appear in response JSON. Support endpoints must also have both successful and failing tests.

## Consistent errors

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid request parameters. Check the API schema.",
    "request_id": "server-generated-uuid"
  }
}
```

Implemented codes include validation_error (422), not_found (404), method_not_allowed (405), database_unavailable (503), internal_error (500). Phase 2 will add unauthenticated (401), forbidden (403) and conflict-specific codes (409). No SQL, connection URL, submitted passwords or stack traces in API errors. Authorization and integrity errors must roll back mutations, including audit insertion.

**Required Phase 2 correction:** malformed JSON will return 400 `bad_request` in the same envelope; well-formed JSON/query/path values that fail schema validation retain documented 422. FastAPI currently routes request-validation errors to 422, so the 400 branch remains unimplemented and unverified. Update handlers, all affected OpenAPI responses and recorded curl tests together; do not merely relabel existing test results. 500 tests must induce a controlled fault in a test environment, not break the live demonstration database.

DELETE is authorized cancellation, not a database delete. PUT return is designed as a single transition; a duplicate call returns a documented 409 without further mutation rather than creating a second return. Verify that convention in client retry behavior and tests.
