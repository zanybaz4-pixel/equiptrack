# EquipTrack flow audit — November 24, 2026

Audited the custodian, student and faculty application, API, PostgreSQL rules,
password recovery, local networking and Render proxy configuration. All writes
used uniquely named disposable PostgreSQL databases and synthetic accounts.
Existing hosted records, account passwords and WSL demo data were preserved.

## Bugs reproduced and fixed

| Problem | Result after the fix | Verification |
| --- | --- | --- |
| A successful response with a truncated body or a timeout became `null`, causing workspace pages to crash. | Response-reading failures produce a retryable error; deliberate navigation cancellation remains canceled. | New tests failed before the fix; all 10 frontend API tests now pass. |
| Signing out on a custodian page and signing in as a borrower opened Access denied. | Explicit logout opens the sign-in route; successful sign-in opens the dashboard. | Actual local HTTPS browser: custodian overdue page → sign out → student dashboard. |
| Search accepted NUL characters that PostgreSQL rejects, producing 500. | Equipment and request search reject invalid text with 422 before querying. | Two contract regressions and both real HTTPS endpoints. |
| The local API had only internal Docker networks, preventing Gmail/Brevo HTTPS delivery. | A separate outbound network permits provider HTTPS without publishing API/database ports. | Disposable container: internal-only connection to Google port 443 failed; adding egress succeeded. Compose configuration checked. |
| Render login/reset limits used ingress proxy addresses, grouping different visitors together. | Render's Cloudflare visitor header determines quotas when supplied by trusted private peers. | Actual nginx reproduction failed before the fix. Separate visitors, burst rejection, forged XFF, untrusted CF headers and the shared recovery limit pass afterward. |
| The dashboard logo card clipped the department name at medium widths. | The logo and name wrap within the card as space changes. | Reproduced on the hosted dashboard; checked the repaired production bundle at medium, narrow and phone-width layouts. |

## Verification results

| Area | Evidence |
| --- | --- |
| Backend contracts, configuration, database constraints and integration workflows | **76 passed, zero skipped** against PostgreSQL 17.12, with separate restricted runtime and migration roles. |
| HTTPS endpoint workflow matrix | **69 checks passed** using curl, actual API processes and a fresh database. |
| Frontend response/error handling | **10 Node tests passed**. |
| Gmail signed relay source | **6 Node tests passed**, with mocked Google services; no email sent by these checks. |
| Hosted nginx configuration | Actual nginx checked login/recovery visitor isolation, 429 bursts, ignored forged XFF, ignored untrusted CF headers and reset/forgot shared quota. |
| Frontend | Production build passed; npm audit reported **zero known vulnerabilities**. |
| Python dependencies | `pip check` passed; this is dependency consistency, not a Python vulnerability scan. |
| Migration | Existing legacy category assignments survived migration 0003 → 0004; new category-free equipment remains supported. |

The HTTPS matrix covers student/faculty/custodian sign-in, secure session cookies,
sign-out/revocation, profile edits, catalog filtering and invalid input, account
creation/duplicates/deactivation, inventory creation/duplicates/editing, legacy
category API conflicts, request ownership/cancellation/rejection, concurrent
approvals, date reservations, concurrent release, active custody, damaged return,
completed-return history, removal from the awaiting-return queue and audit logs.
Database integration additionally covers serviceable and late returns, overdue
custody, retirement guards, role changes, CSRF and reset-token expiry/consumption.

Browser checks used the production bundle and real isolated HTTPS API. They
verified category-free inventory creation, student catalog visibility, actual
completed-return time/condition, the separate awaiting-return empty state,
single-line active Overdue equipment and switching account roles after logout.

## Deployment and limits of this audit

The source fixes target the existing `codex/render-deployment` branch and existing
Render service. No paid resources or database replacements are required. The
local Compose egress change takes effect on the next local API recreation; this
audit did not rebuild/recreate the existing WSL demo deployment.

Render proxy trust is deployment-specific: public service traffic passes through
Cloudflare, which supplies the visitor header. The nginx configuration trusts
private network peers, including other workspace services; those peers must remain
trusted. Direct public peers cannot select their quota with that header, and XFF
is not used. Revisit the private trust ranges if the ingress architecture changes.
See [Render ingress](https://render.com/articles/how-render-handles-ddos-attacks)
and [Cloudflare's header behavior](https://developers.cloudflare.com/fundamentals/reference/http-headers/).

Commands: `npm test` and `npm run build` in `frontend`,
`node --test tests/gmail-relay.test.cjs`, `pytest tests -q` in `backend` with
disposable test database URLs, and `python scripts/protocol-check.py` with
loopback HTTPS test-account configuration. On Windows with WSL Docker Engine,
`python scripts/check-render-limits.py` requires a built
`equiptrack-render:verification` image (`Dockerfile.render`). Temporary audit
outputs are in ignored `test-results/`, including
`branding-database-verification.json`, `full-flow-protocol.json` and
`mail-network-check.json`; these contain results rather than live credentials.

This audit does not claim every possible input or physical device is bug-free.
Hosted business records were not created/modified to repeat the isolated matrix.
The earlier owner-controlled Gmail inbox delivery, private password reset and
sign-in acceptance are documented in `GMAIL_DELIVERY.md`; they were not repeated
by this regression run. Google quotas and authorization expiry still apply.
