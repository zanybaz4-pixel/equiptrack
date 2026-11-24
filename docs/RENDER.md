# Optional Render preview

Deployed November 22, 2026, Asia/Manila. This is an additional internet-accessible demo requested by the user. The course demonstration remains the existing WSL2 Docker Engine/Compose deployment. This preview bundles Nginx and FastAPI in one free web-service container, with PostgreSQL in a separate managed service; it does not establish the brief's independently deployed three-tier acceptance evidence or approval of Render under the FOSS tool policy.

## Live deployment

November 25 directory import: the owner requested all 174 transcribed Tool Room
Directory rows in Equipment Inventory, available for admin review. New entries
use Good / Serviceable. Shared rack codes are stored separately from unique
internal item codes. A one-time migration preserves any matched item IDs and
custody history, and stable directory keys prevent duplicate imports. Unclear
handwriting is noted; the blank Welding Apron location is `Not recorded`.
Pre-deployment verification passed 79 backend checks with disposable PostgreSQL,
69 HTTPS workflow checks, 10 frontend API tests, six relay tests and the production
build. Migration verification checked all 174 rows, an existing active loan and
condition, and an unchanged item count after repeated upgrade.

- URL: https://equiptrack-5r6t.onrender.com/
- Workspace: EquipTrack; free web service and free PostgreSQL, Singapore.
- Deployed application commit: `d6443048bcbde14a6d0cb563dc8a7d94e701da7e`, branch `codex/render-deployment`.
- Database expiry shown by Render: **December 22, 2026**.
- Eight public HTTPS checks passed: frontend and its script/logo/photo, database readiness, signed-out API rejection, and rejection of a login from an incorrect origin.
- Live browser custodian sign-in, dashboard, eight inventory items and authenticated page reload were verified. No borrowing/review/return transaction was submitted to the live cloud database during these checks. A separate-device internet test and complete live transaction cycle remain user acceptance checks.
- The first deployment failed because Render replaces `/tmp`; startup now creates Nginx temporary directories. The corrected image passed all 18 isolated HTTP checks with an empty runtime `/tmp` before the successful deployment. The isolated checks also passed after a restart; cloud restart persistence was not separately tested.

The laptop's existing data is preserved. The cloud demo starts with its own synthetic catalog and accounts. Passwords remain in Render's private Environment settings.

## Account email addresses

Password recovery setup and verification are documented in [PASSWORD_RECOVERY.md](PASSWORD_RECOVERY.md). The owner's signed Gmail relay is configured, and real inbox delivery, password reset and subsequent sign-in were verified on November 24, 2026.

At the user's request on November 24, 2026, account creation accepts Gmail and other valid email addresses. The previous `@example.invalid` restriction was in the account form; the API already validates and normalizes general email addresses. Existing demo accounts remain unchanged. The email identifies an EquipTrack account: this does not implement Google sign-in, email verification, or email delivery. Choose a separate EquipTrack password of at least 12 characters.

This user-requested extension permits personal sign-in emails in the cloud preview. The brief's synthetic-data requirement still applies to academic test records and submitted evidence; use the seeded fictional accounts for that demonstration.

## Deployment

The November 24 department interface uses the owner-supplied Mechanical Technology Department logo, maroon and gold branding, and the department name throughout sign-in, recovery and the workspace. The old seal and campus photo are removed. Categories are absent from custodian, student and faculty screens. Migration `0004_optional_equipment_category` permits new equipment without a category while preserving existing data and legacy API compatibility. The build and 50 contract/configuration checks passed; 16 isolated PostgreSQL workflow checks passed, including category-free creation, catalog visibility, editing and preservation of existing category assignments. Local browser checks covered all roles and narrow-screen layout. The expiry test fixture uses the API clock because the isolated WSL database was measured approximately 22 seconds ahead of the Windows API host; application session behavior was unchanged.

Use the existing private `zanybaz4-pixel/equiptrack` repository, branch `codex/render-deployment`, and root `render.yaml` as a Render Blueprint. Both resources explicitly use `plan: free`, in Singapore. Review the resource summary before deploying. A separate Hobby workspace can keep this deployment apart from other projects and their free database allowance. Do not replace, reset, or delete another project's database.

`Dockerfile.render` builds the current React interface and runs Nginx plus FastAPI as a non-root user. Render supplies public HTTPS; Nginx keeps the frontend and API on the same browser origin, preserving the existing Secure, HttpOnly, SameSite=Strict session cookie and CSRF checks. Use Render's generated public URL. For a custom domain, set `APP_ORIGIN` to the exact HTTPS origin.

The Blueprint creates a new database and generates separate runtime and demonstration passwords. Startup normalizes Render's PostgreSQL URL for the installed psycopg driver, creates the restricted `equiptrack_app` role, applies the existing Alembic migrations, and inserts missing synthetic catalog records and accounts. Repeated startup preserves existing equipment records and account password hashes. The API child process does not receive the migration-owner or provisioning passwords. No local database records or sign-in sessions are uploaded by this setup.

Demo emails are `custodian@example.invalid`, `student@example.invalid`, and `faculty@example.invalid`. Their passwords are the corresponding `DEMO_CUSTODIAN_PASSWORD`, `DEMO_STUDENT_PASSWORD`, and `DEMO_FACULTY_PASSWORD` values in the web service's private Render Environment settings. They are never printed in startup logs or committed to Git. Keep those values stable after provisioning. Redeploying with a different provisioning password does not change an existing account password.

The database's external IP allowlist is empty. Only Render's private network can connect. The running web service uses the restricted database role; migration operations use the separate owner connection only during startup. Automatic source deployment is disabled so that future pushes require a deliberate deployment.

## Free-plan limits

Return records update, November 24, 2026: Record returns opens Completed returns by default, querying returned requests without the active-custody filter. Its table shows the actual returned time and condition, along with the borrower and status. Awaiting return separately queries open loans and retains access to recording their return. Both views share equipment search and reset pagination when switching. No historical loans or audit records are changed. Local browser verification reproduced the old empty list despite a completed fixture, then verified the completed record and the separate awaiting-return empty state after the fix.

Student reservation guidance, November 24, 2026: the borrowing form checks the selected dates automatically, keeps submission disabled until availability is confirmed, and explains reservations with a link to choose another item. Date changes clear previous submission errors. A reservation created during submission refreshes availability and retains the student's form entries. Custodian approval also checks the request's dates before enabling approval and provides a route to review existing requests when unavailable. Existing reservation and custody rules remain enforced by the API and PostgreSQL. Local browser checks verified reserved dates, available-date submission, and a simulated reservation race; isolated PostgreSQL tests verified concurrent approvals and custody behavior.

Render's free web service can sleep after 15 minutes without incoming requests. Its free PostgreSQL database expires 30 days after creation and is not durable long-term hosting. Record the actual expiry date from the database dashboard. Export a reviewed backup before expiry if the demo has records you need to keep. The existing local backup/restore scripts continue to apply to the laptop deployment; they are not Render backup automation.

## Verification boundary

Button and header update, November 25, 2026: the top-bar breadcrumb is removed
at the owner's request. Buttons across sign-in, recovery, forms, dialogs,
inventory, request actions, pagination, return-view selectors and navigation
controls share raised maroon/ivory surfaces, solid lower edges, soft shadows
and pressed states. Destructive controls retain a red treatment. Keyboard focus,
disabled states, reduced-motion and forced-color preferences remain supported.
Local browser review covered inventory, Add equipment/Cancel/Close, return-view
selectors, sign-in, recovery and keyboard focus. Ten frontend tests and the
production build passed; the change does not modify equipment or loan records.

Search update, November 25, 2026: catalog/inventory and request searches accept
equipment names, shared rack codes and location codes (case insensitive, with
literal wildcard handling). Labels and examples identify all three supported
values. Availability/status filters still apply; catalog empty results explain
that All statuses can reveal available items. The reported `MT03.01` failure was
reproduced before the fix. Verification passed 81 backend checks with disposable
PostgreSQL, 69 HTTPS workflow checks, 10 frontend API tests and the production
build, including equipment-name and location-code regression coverage.

The broader November 24 audit is documented in [FLOW_AUDIT_2026-11-24.md](FLOW_AUDIT_2026-11-24.md): 76 backend checks with actual PostgreSQL, 69 isolated HTTPS workflow checks, 10 frontend API regressions and six signed-relay checks passed. It fixes response-body failure handling, account-switch navigation, invalid search characters, local mail egress and Render visitor quotas. Public Render traffic uses Cloudflare's visitor header only from trusted private peers; other private workspace services must remain trusted. This audit preserves existing hosted and local demo records.

Before first cloud deployment, the image built successfully and ran against a separate PostgreSQL 17 test database with a non-superuser migration owner and a 512 MB application limit. Nine deployment-configuration tests and 18 HTTP checks passed, including all three roles, eight catalog items, Secure/HttpOnly/SameSite cookie attributes, signed-out access rejection and CSRF rejection. These HTTP container checks are not browser HTTPS or Render deployment proof. A broader Windows test run was interrupted without a result; no full regression pass is claimed for this increment.

Before relying on this preview for a live assessment, complete the remaining acceptance checks above, including a borrower request, custodian review, return, and cloud persistence after restart. Deployment availability and authentication have been verified; the entire live business workflow is not claimed as tested.

## References

- [Render free-service limits](https://render.com/docs/free)
- [Docker deployment](https://render.com/docs/docker)
- [Blueprint specification](https://render.com/docs/blueprint-spec)
- [Default environment variables](https://render.com/docs/environment-variables)
- [PostgreSQL extensions](https://render.com/docs/postgresql-extensions)

The user-supplied MIS 215 PDF remains the primary academic reference; these sources describe the optional provider-specific preview.
