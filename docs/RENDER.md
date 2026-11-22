# Optional Render preview

Deployed November 22, 2026, Asia/Manila. This is an additional internet-accessible demo requested by the user. The course demonstration remains the existing WSL2 Docker Engine/Compose deployment. This preview bundles Nginx and FastAPI in one free web-service container, with PostgreSQL in a separate managed service; it does not establish the brief's independently deployed three-tier acceptance evidence or approval of Render under the FOSS tool policy.

## Live deployment

- URL: https://equiptrack-5r6t.onrender.com/
- Workspace: EquipTrack; free web service and free PostgreSQL, Singapore.
- Deployed application commit: `d6443048bcbde14a6d0cb563dc8a7d94e701da7e`, branch `codex/render-deployment`.
- Database expiry shown by Render: **December 22, 2026**.
- Eight public HTTPS checks passed: frontend and its script/logo/photo, database readiness, signed-out API rejection, and rejection of a login from an incorrect origin.
- Live browser custodian sign-in, dashboard, eight inventory items and authenticated page reload were verified. No borrowing/review/return transaction was submitted to the live cloud database during these checks. A separate-device internet test and complete live transaction cycle remain user acceptance checks.
- The first deployment failed because Render replaces `/tmp`; startup now creates Nginx temporary directories. The corrected image passed all 18 isolated HTTP checks with an empty runtime `/tmp` before the successful deployment. The isolated checks also passed after a restart; cloud restart persistence was not separately tested.

The laptop's existing data is preserved. The cloud demo starts with its own synthetic catalog and accounts. Passwords remain in Render's private Environment settings.

## Deployment

Use the existing private `zanybaz4-pixel/equiptrack` repository, branch `codex/render-deployment`, and root `render.yaml` as a Render Blueprint. Both resources explicitly use `plan: free`, in Singapore. Review the resource summary before deploying. A separate Hobby workspace can keep this deployment apart from other projects and their free database allowance. Do not replace, reset, or delete another project's database.

`Dockerfile.render` builds the current React interface and runs Nginx plus FastAPI as a non-root user. Render supplies public HTTPS; Nginx keeps the frontend and API on the same browser origin, preserving the existing Secure, HttpOnly, SameSite=Strict session cookie and CSRF checks. Use Render's generated public URL. For a custom domain, set `APP_ORIGIN` to the exact HTTPS origin.

The Blueprint creates a new database and generates separate runtime and demonstration passwords. Startup normalizes Render's PostgreSQL URL for the installed psycopg driver, creates the restricted `equiptrack_app` role, applies the existing Alembic migrations, and inserts missing synthetic catalog records and accounts. Repeated startup preserves existing equipment records and account password hashes. The API child process does not receive the migration-owner or provisioning passwords. No local database records or sign-in sessions are uploaded by this setup.

Demo emails are `custodian@example.invalid`, `student@example.invalid`, and `faculty@example.invalid`. Their passwords are the corresponding `DEMO_CUSTODIAN_PASSWORD`, `DEMO_STUDENT_PASSWORD`, and `DEMO_FACULTY_PASSWORD` values in the web service's private Render Environment settings. They are never printed in startup logs or committed to Git. Keep those values stable after provisioning. Redeploying with a different provisioning password does not change an existing account password.

The database's external IP allowlist is empty. Only Render's private network can connect. The running web service uses the restricted database role; migration operations use the separate owner connection only during startup. Automatic source deployment is disabled so that future pushes require a deliberate deployment.

## Free-plan limits

Render's free web service can sleep after 15 minutes without incoming requests. Its free PostgreSQL database expires 30 days after creation and is not durable long-term hosting. Record the actual expiry date from the database dashboard. Export a reviewed backup before expiry if the demo has records you need to keep. The existing local backup/restore scripts continue to apply to the laptop deployment; they are not Render backup automation.

## Verification boundary

Before first cloud deployment, the image built successfully and ran against a separate PostgreSQL 17 test database with a non-superuser migration owner and a 512 MB application limit. Nine deployment-configuration tests and 18 HTTP checks passed, including all three roles, eight catalog items, Secure/HttpOnly/SameSite cookie attributes, signed-out access rejection and CSRF rejection. These HTTP container checks are not browser HTTPS or Render deployment proof. A broader Windows test run was interrupted without a result; no full regression pass is claimed for this increment.

Before relying on this preview for a live assessment, complete the remaining acceptance checks above, including a borrower request, custodian review, return, and cloud persistence after restart. Deployment availability and authentication have been verified; the entire live business workflow is not claimed as tested.

## References

- [Render free-service limits](https://render.com/docs/free)
- [Docker deployment](https://render.com/docs/docker)
- [Blueprint specification](https://render.com/docs/blueprint-spec)
- [Default environment variables](https://render.com/docs/environment-variables)
- [PostgreSQL extensions](https://render.com/docs/postgresql-extensions)

The user-supplied MIS 215 PDF remains the primary academic reference; these sources describe the optional provider-specific preview.
