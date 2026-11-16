# Phase 3 borrower and custodian workspaces

EquipTrack uses the MIS 215 brief as the primary academic reference. The browser connects to the FastAPI routes for all five core transactions. Date entry and display use Philippine time. The catalog checks availability for the selected dates, and the backend checks again when a request is submitted or approved.

## Run the demonstration

Follow the deployment and synthetic account setup in [README.md](../README.md). Sign in as a synthetic borrower to find equipment, open its details, choose a time range, and submit a request. The **My requests** view includes pending requests and cancellation. **Borrowing history** defaults to returned items and can filter other statuses. **My profile** supports display name correction.

Sign out and sign in as the synthetic custodian. Use **Review requests** to approve or reject a pending request. Use **Release equipment** when the approved period begins. Record its pickup condition. Find released requests in **Active loans** and **Record returns**. A damaged return updates the item's service status to maintenance. **Overdue equipment** lists active loans past their due time.

Custodians can manage inventory, categories and synthetic accounts, search transaction history and inspect the audit trail. The frontend hides custodian routes from borrowers and handles unauthorized deep links. The backend enforces roles and ownership. Request reads expose the borrower's display name to the custodian. Borrower reads omit the name value and remain scoped to the current account. The running API serves the current schema at `/api/openapi.json`.

## Verification on 2026-11-15

- A signed-in borrower searched the catalog, checked a date range, submitted a request and reloaded the browser with the request still visible. A direct link to user management displayed Access denied.
- The custodian saw the borrower's name, approved the request, released the item and recorded a damaged return. PostgreSQL showed a returned request, the recorded damage, maintenance status and four request audit events. The borrower subsequently saw the return details in their borrowing history and the maintenance status in the catalog.
- Separate synthetic requests exercised reversed-date validation, keyboard dismissal of the cancellation dialog, borrower cancellation, custodian rejection with remarks, and search and status filters. A seeded open loan with a past due date appeared in the overdue queue.
- Browser checks also covered profile updates across reload, equipment and category creation, inventory edits, account creation and deactivation, active loans, audit history and sign-out.
- At 360 CSS pixels, the catalog and navigation fit without horizontal page scrolling. Keyboard activation moved focus to the new page heading, and reduced-motion emulation matched the preference.
- The production frontend build passed. The backend test suite passed 33 checks with PostgreSQL, with one existing TestClient deprecation warning.

Browser verification used Vite on localhost and a disposable PostgreSQL 17.12 database with the restricted runtime role. Phase 2 separately exercised HTTPS at the API. Container startup, Nginx TLS, backup and restore, and a second device on the LAN remain to be verified.
