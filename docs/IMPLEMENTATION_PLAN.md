# Implementation plan

Backend, browser and integration verification are recorded in [PHASE2.md](PHASE2.md), [PHASE3.md](PHASE3.md) and [PHASE4.md](PHASE4.md).

## Scope and sequencing

The user requested an incremental project and, for the first increment, environment inspection, a detailed plan, recommended structure, architecture, database schema, and an initial scaffold. This increment provides those artifacts plus a functional read-only API/catalog slice. It does not claim the six-phase system is finished.

The supplied MIS 215 Term Project Brief (external course material) is now the primary academic reference. [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) defines the required milestones and report formats. Retain the user's compatible stricter selections, including exactly five transactions. Propose **Option A: REST over HTTPS**; FIC approval is not yet recorded. Do not introduce Supabase, Firebase, PostgREST, Hasura or other database-generated application tiers, cloud databases, or a proprietary runtime substitute.

## Phase 1 — planning and architecture (this increment)

Deliverables: environment report; requirements with five named core transactions; fictional organization and source/assumption register; three-tier and ER diagrams; six-table schema, keys and concurrency constraints; data dictionary; endpoint plan; phase acceptance matrix; React/Vite/Tailwind and FastAPI/SQLAlchemy scaffold; initial migration and synthetic catalog seed; Nginx/Compose definitions; installation and test instructions; license inventory and AI disclosure.

Validation: import/compile backend, run HTTP-contract tests, build frontend, validate Compose without printing secrets, produce OpenAPI from actual routes. PostgreSQL migration execution, container startup, HTTPS trust and second-device checks require the missing infrastructure. A blocked runtime check must be reported separately from passed local checks.

## Phase 2 — backend development

1. Create Argon2id password hashing, explicit synthetic-user provisioning, normalized email login, generic invalid-credential responses and disabled-user rejection. Add rate limiting suitable for LAN use. Never seed a universal admin password.
2. Implement signed short-lived authentication in Secure/HttpOnly/SameSite cookies, CSRF tokens and Origin verification for mutations. Load the current role and active status from the database on every authenticated request; do not trust browser claims. Define logout invalidation and session/key rotation. Add any necessary session table as a reviewed schema change, documenting why it extends the six-table baseline.
3. Implement reusable borrower/admin dependencies, ownership checks, profile routes and user activation/role changes. Protect catalog routes before broadening network access. Reject self-deactivation and removal of the last active admin in a serialized service operation.
4. Implement availability for a requested time interval, request create/list/detail/owner-cancel, admin decision, release and return. Use one SQL transaction for state changes and audit insertion, deterministic equipment → request lock ordering, and database constraints as the final concurrency guard. Translate conflicts into safe HTTP 409 responses.
5. Implement inventory management with soft retirement, category management, paginated admin/borrower queries, derived active/late/returned-late fields and dashboard aggregates. Broaden runtime privileges only as needed; preserve append-only audits and role separation.
6. Export real OpenAPI and executable examples; cover successful and failing calls for every route, ownership, role checks, CSRF, authentication, invalid states, dates, and uniqueness conflicts. Meet R2's status-code minimum, including a meaningful 400 malformed-JSON response, while keeping documented 422 schema validation and the consistent error envelope. Current code still uses 422; the 400 distinction is planned.

Exit criteria: all required endpoint methods exist; every required route has success and failure tests; real PostgreSQL concurrency tests prove only one winner for overlapping approvals and simultaneous release; no API leaks account/password information; return rolls back completely if audit/condition updates fail.

## Phase 3 — frontend development

Build login and role-aware layouts; borrower dashboard, equipment catalog/detail, request form, my requests/history and profile; admin dashboard, inventory editor, requests/decision detail, release/return screens, active and overdue views, user management and searchable history. Supporting admin views may share reusable tables and a request detail panel. Pages are views over the same five transactions, not extra transactions.

Connect all counts, rows, badges and mutations to authenticated API responses. Add form validation, inline API errors, loading/empty/retry states, confirmation of meaningful mutations, timezone-aware datetime controls, keyboard focus handling and mobile navigation. Hide forbidden controls for usability while retaining server authorization.

Exit criteria: both roles can finish their authorized flow against the real backend; browser reload preserves server state; unauthorized deep links fail safely; keyboard-only use, 360px viewport and reduced-motion settings work. No fake metrics or hardcoded production records.

## Phase 4 — integration and consistency

Use disposable PostgreSQL databases and independent connections for races. Exercise request → approval → release → return, rejection, owner cancellation, conflicting requests, invalid/missing credentials, inactive accounts, maintenance, late return and damaged return. Test transaction rollback, audit event counts, interval boundaries and UTC/Asia-Manila conversion. Compare database rows before/after each mutation; inspect logs for secrets.

Execute and record at least one success and one failure case for **every endpoint using curl**, as required by R2 Option A (brief p. 8), including supporting endpoints. Keep commands, status/response and expected-versus-actual outcomes with sanitized synthetic fixtures. Pytest augments this protocol evidence; the present happy-path smoke script does not replace it.

Exit criteria: one active loan per item under contention, no conflicting approved intervals, no unauthorized data leakage or mutation, durable history after cancellation/retirement, correctly derived overdue status, and reproducible evidence. HTTP tests with doubles do not satisfy this phase.

## Phase 5 — deployment

With explicit permission for system changes, prepare an Ubuntu WSL2 distribution, Docker Engine and Compose plugin, mkcert and trusted local CA. Build the separate tiers, migrate, seed synthetic demonstration accounts/equipment, verify HTTPS, backups and restore into a new database. Configure supervised LAN access and Windows/WSL networking only after authentication is ready.

Record engine/Compose/image versions and digests, certificate SANs/trust results, host and second-device evidence. Database/API ports remain private. Do not run volume deletion, overwrite a database, change firewall rules or install trust anchors automatically.

Exit criteria: clean startup, healthy tiers, trusted HTTPS from two devices, safe backup and tested restore, restart persistence, no plaintext secrets in frontend/build/logs and no proprietary runtime dependency.

## Phase 6 — evaluation and academic package

Finalize requirements traceability, architecture, ERD/dictionary, OpenAPI, install/deploy guide, security/privacy review, source register, demonstration sequence and AI disclosure. Finish authenticated k6 read/write workloads; run separate 1, 10, 50 VU experiments with controlled synthetic fixtures and trustworthy TLS. Store host CPU/RAM, actual VM/container allocations, configuration, duration, hardware, versions, raw summaries and errors; report throughput, mean, p95 and failure rate for each run and evidence for degradation/likely bottleneck. Do not infer performance from unit tests.

Complete **R7 Part B: a 3–5-page argued comparison** with a two-tier alternative on architecture, performance, scalability, security, cost and maintainability, using own R7A measurements and course references. This is conceptual comparison, not permission to connect the actual browser to the DB. Follow [EVALUATION_PLAN.md](EVALUATION_PLAN.md); do not invent alternative benchmarks.

Prepare the 3–5-page proposal, 20–30-page final report (A4, 1-inch margins, 11/12-point font), 2–3-page privacy note, APA 7 references, required appendices, repository ZIP/link, chosen OSI project LICENSE and synthetic test-account instructions. Exact formats/exclusions and section order are in SUBMISSION_CHECKLIST.md. Practice the 15-minute second-device defense and devtools/log/DB request trace; produce a backup screen recording. Topic/protocol approval, student identity, license choice and exact BU-LMS dates remain unprovided.

Exit criteria: complete reproducible evidence for all requirements, instructor reconciliation against the brief/FOSS policy, and student review sufficient to explain locks, constraints, TLS, authorization and all five transactions.

## Traceability

| Requirement | Owning artifact or phase | Current state |
|---|---|---|
| Five core transactions | REQUIREMENTS.md; Phase 2 services | Availability slice implemented; other four designed |
| Two roles, ownership, secure login | Phase 2; SECURITY decisions in ARCHITECTURE.md | Planned; no login UI or mutation route pretends to work |
| PostgreSQL relational design | DATABASE.md; migration 0001 | DDL written, not yet run on PostgreSQL |
| At least eight documented endpoints, four verbs | API.md; Phase 2 | Five GET paths implemented; POST/PATCH/PUT/DELETE planned |
| Responsive API-backed UI | frontend/src | Read-only catalog slice; full role views Phase 3 |
| Containers, Nginx, trusted HTTPS, LAN | compose.yaml; INSTALLATION.md | Configured in files, runtime checks pending |
| Automated tests and recorded per-endpoint curl success/failure | backend/tests; TESTING.md | Scaffold contracts run locally; PostgreSQL/curl acceptance pending |
| k6 1/10/50 read + write | tests/performance; Phase 6 | Read workload provided; authenticated write workload pending |
| Backup and restore | scripts/backup.sh, restore.sh | Scripts provided; restore drill pending |
| R7B 3–5-page comparison and resource/bottleneck evidence | EVALUATION_PLAN.md | Added to plan; no measured results or completed comparison |
| Licensing and 2–3-page privacy note / collection-point notice | STACK_LICENSES.md; PRIVACY.md | Brief reviewed; complete tool/license audit and final privacy evidence pending |
| Proposal/report/repository/defense formats | SUBMISSION_CHECKLIST.md | Requirements mapped; final academic artifacts not yet produced |
| Sources and disclosure | SOURCES_AND_ACKNOWLEDGMENTS.md | Source/assumption distinctions documented |
