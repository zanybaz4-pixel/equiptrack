# Phase 1 status and verification

See [PHASE2.md](PHASE2.md) for backend verification, [PHASE3.md](PHASE3.md) for browser workflows, [PHASE4.md](PHASE4.md) for integration results and [PHASE5.md](PHASE5.md) for the deployed stack and recovery results. The rest of this file records the Phase 1 baseline.

Date: **2026-11-13 (Asia/Manila)**. Scope: the requested initial inspection, implementation plan, architecture, database design and scaffold. This is not acceptance of the complete system.

## Primary-reference update

The user subsequently supplied `docs/MIS215_TermProject_Brief.pdf` and designated it the primary reference. All 22 pages were read and key requirement/policy tables visually reviewed. The phase records refer to a separate alignment document and course brief. Those materials were absent from the supplied archive.

Updated planning adds recorded curl success/failure for every endpoint, required HTTP 400 coverage, client-storage decisions, host/resource and bottleneck evidence, the 3–5-page architectural comparison, required privacy/report formats, project LICENSE and synthetic-account/defense artifacts. Exactly five transactions and the selected stack remain compatible with the brief. Docker Desktop is expressly rejected, while the host OS/code editor exemption and WSL2 Engine acceptance are now confirmed. Broader scenario grounding remains incomplete; BASIS_OF_SCENARIO.md records the gaps.

This follow-up changed documentation only: no application/API behavior, dependencies or environment settings changed, and no new runtime results were claimed. Source hash, page references, relative document links and the revised table/checklist structure were checked. Prior test/build results remain dated scaffold evidence below; no tests were rerun merely for these documentation edits.

## Environment inspection

The workspace was empty, with no existing code, applicable AGENTS.md, MIS 215 term-project brief or FOSS policy found. The supplied project request was read and copied into PROJECT_REQUEST.md. No historical MyDugo/RED project files were used.

| Item | Observed result |
|---|---|
| Python | 3.14.6; project-local .venv created |
| Node / npm | 24.21.0 / 11.19.0 |
| Git | 2.56.1.windows.1; no repository initialized |
| curl | 8.22.0, Schannel |
| Docker CLI / Compose | 29.9.2 / 5.6.1 from existing Docker Desktop install |
| Docker daemon | Unavailable; desktop-linux named pipe absent |
| WSL | Version 2 default; only docker-desktop registered, stopped |
| Ubuntu development distribution | Not registered |
| psql / mkcert / k6 | Not found on PATH |
| Initial Python app/test dependencies | Missing; subsequently installed only in project .venv |

Sandbox DNS prevented initial registry queries; approved network access retrieved publisher metadata and installed local packages. Initial WSL read access was denied by the sandbox; approved read-only inspection established the WSL result above. No system-level install, service startup, trust-store change, firewall change, database reset, deployment or destructive operation was performed.

## Created and implemented

- Detailed six-phase plan, requirements/role matrix, source/assumption register and acceptance traceability.
- Mermaid three-tier architecture and ERD, six-table dictionary, immutable initial Alembic SQL migration, idempotent synthetic catalog seed.
- Database definitions for ordered booking dates, nonoverlapping approved/released reservations, one active loan per item, request/equipment consistency, return-field integrity, damaged-item service restrictions and append-only audit DML. These definitions have not yet executed against PostgreSQL.
- Five working FastAPI GET route contracts: liveness, schema readiness, categories, paginated/filtered catalog, equipment detail. Safe JSON errors and request IDs; no SQL/credential leakage in tested errors.
- React/Vite/Tailwind catalog using actual API fetches, search/filter/pagination, detail dialog, responsive navigation, privacy/guide, loading/empty/error states and bounded fetch timeout. No hardcoded frontend equipment fallback or simulated loan actions.
- Compose separation, read-only runtime database role, owner-only migration/seed services, Nginx TLS configuration, certificate-generation/curl-smoke and conservative backup/restore scripts.
- Version/license inventory, local dependency locks, initial OpenAPI export, privacy review draft, academic sources and AI-assistance disclosure.

## Checks actually executed

| Check | Result | What it proves / limits |
|---|---|---|
| Final backend pytest | **25 passed, 7 skipped, 1 warning** | HTTP contracts pass with database doubles; PostgreSQL tests skipped because TEST_DATABASE_URL absent |
| Backend compile/import | Passed | Python syntax/import and actual route/OpenAPI generation |
| pip check | Passed | No installed Python dependency conflicts |
| Frontend production build | Passed, Vite 8.3.8 | Bundles React/Tailwind; not full business-flow acceptance |
| Compose config --quiet | Passed with .env.example | Configuration validation only; no daemon/image build required |
| Actual local liveness HTTP request | 200 | Native loopback API responds |
| Actual catalog request with missing database | API/browser showed safe database-unavailable 503 | Failure path only; no database success inferred |
| Browser desktop 1366×900 | Shell/guide/catalog error checked | Real page rendering; catalog cards not backed by a running DB during this check |
| Browser mobile 390×844 | Menu open/close, privacy dialog, layout and hidden-nav accessibility checked | Manual targeted check, not comprehensive accessibility certification |
| Temporary viewport/processes | Viewport reset; owned preview/stalled test processes stopped | Preview is not a deployed or continuously running service |

The first sandboxed TestClient run stalled before results; a run outside that Windows restriction completed, including the final rerun after the error-header change. The dependency stack emits one Starlette deprecation warning for HTTPX-backed TestClient (suggesting httpx2). It is not a test failure; review the supported test-client migration during Phase 2 rather than suppressing the warning. Source formatting completed for JS/JSX/CSS/HTML/JSON; Prettier has no inferred Nginx parser, so the manually formatted Nginx file was left intact.

## Not yet implemented / verified

Authentication, Argon2id, session/CSRF/rate limiting, server RBAC, account/inventory mutation services, request creation/cancellation/approval, release/return, dashboard/history/overdue APIs and their complete role-specific screens are future phases. Nine business endpoint contracts are designed, but only the Phase 1 GET slice exists; the at-least-eight endpoint/four-verb requirement is not yet satisfied by running code.

PostgreSQL migration/seed execution, exclusion/unique/audit constraint execution, true simultaneous-connection races, all-five-transaction end-to-end acceptance, container builds/startup, trusted HTTPS, second-device LAN access and backup/restore drill are **unverified**. There is no SQLite substitute. The k6 read workload is supplied but unrun; the authenticated write workload is pending the write/auth API. No throughput, mean/p95 latency or error-rate measurements were produced.

Version/license metadata and official source checks are recorded. The supplied brief/FOSS policy has now been reviewed, but full actual-tool and container/native-library license verification, target Linux runtime execution, project LICENSE selection and FIC topic/protocol approval remain incomplete. The prior Desktop-distributed Compose configuration check must be repeated with the accepted WSL2 Engine/Compose tooling. Image digests, bundled notices and advisory scans remain for deployment review. The privacy document is a review draft, not the required completed 2–3-page note, and no real-school policy, consent, retention period or legal compliance certificate is asserted.

## Next implementation phase

**Phase 2: backend authentication, authorization and lending services.** Follow IMPLEMENTATION_PLAN.md. Real PostgreSQL is needed to prove its transaction and concurrency guarantees. Ubuntu WSL2 + Docker Engine/Compose + mkcert setup is an identified prerequisite for container acceptance; system-level changes require the user's permission and have not been made. Keep the current scaffold local and synthetic.
