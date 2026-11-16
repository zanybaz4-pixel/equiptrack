# Requirements specification

Primary academic reference: [MIS 215 Term Project Brief](MIS215_TermProject_Brief.pdf), especially scope pp. 4–7 and R1–R7 pp. 7–12. [BRIEF_ALIGNMENT.md](BRIEF_ALIGNMENT.md) tracks minimums and gaps. The brief permits 3–5 core transactions; EquipTrack retains the user's exact five. REST/HTTPS is proposed **Option A**, with no FIC approval yet claimed.

## Organization and evidence

**Bicol Learning Academy** is an invented school in the Bicol Region, Philippines. The name, rooms, asset codes and records in this repository are synthetic. It is not a claim about an existing school. Student/faculty borrower access and the reservation rules below are project design assumptions requiring stakeholder approval.

DepEd SDO Valenzuela's published [ASSETS description](https://sites.google.com/deped.gov.ph/assetmanagement/s/assets) documents tracking issuance and supporting borrowing, returning and transfer through forms. This supports the general need for custody tracking; it is not a Bicol school policy or a mandate for EquipTrack's exact state machine. DepEd's [2023 delegation order](https://www.deped.gov.ph/wp-content/uploads/2023/01/DO_s2023_001.pdf) documents roles and accountability forms; it does not prescribe our student borrowing rules. See the source register for the limits of these references.

## Exactly five core business transactions

| ID | Transaction | Actor | Input → outcome | Rules and failures |
|---|---|---|---|---|
| T1 | Equipment availability | Borrower/admin | Search/category/period → equipment and availability | Unique item/asset; distinguish service state, reservation and actual loan; empty result is 200 |
| T2 | Borrowing request | Borrower | Equipment, borrow/due instants, purpose → pending request; owner DELETE → canceled | Active account, dates ordered and not in past at submit, serviceable asset, no known interval conflict; pending does not reserve; ownership required |
| T3 | Request approval | Admin | Approve/reject, optional remarks → decision + actor/time | Pending only; lock and recheck availability; overlapping approved/released reservations rejected; no silent expiry |
| T4 | Equipment release | Admin | Approved request + inspected condition → active loan | At/after borrow time and before due time; no active loan; no damaged/maintenance/retired release; server timestamp |
| T5 | Equipment return | Admin | Released request + return condition/remarks → returned loan and request | Server timestamp; no duplicate return; update current condition; damaged → maintenance; audit and changes atomic |

Authentication, dashboards, profiles, category/inventory/account administration, derived overdue lists and audit/history views are supporting functions.

## Proposed rules requiring review

- Each request covers one individually tracked equipment item; multiple items require separate requests. No quantity pool, fines, external notifications or procurement/disposal workflow in scope.
- API uses explicit timezone offsets and stores `timestamptz`; UI displays Asia/Manila. A due instant is precise, not an ambiguous end-of-day date. Requested periods are half-open `[borrow_at, due_at)`; adjacent reservations may meet exactly at a boundary.
- Pending requests may coexist; they do not hold an item. Approval allocates the interval. Availability checked at submission is advisory and is checked again under lock at approval/release.
- Active loans block immediate release even after the planned return instant. An approved future reservation does not promise physical availability if an earlier loan is late. Staff must resolve such conflicts; the system must not falsify a return.
- Approval is not release. Release is allowed only within the approved interval. Uncollected approvals remain in history; no automatic new state or expiry job is invented. An expired approval cannot be released; a new request is required.
- Only owners cancel pending requests; approved/released/returned/rejected requests cannot be canceled using DELETE. Retain history and cancellation time. Future administrative override needs a separately reviewed policy.
- `is_overdue = returned_at IS NULL AND now > due_at` for an existing released loan. Unreleased requests are not overdue loans. `was_returned_late = returned_at > due_at` is a separate historical field. Do not store an overdue flag that goes stale.
- Returned damaged items enter maintenance; admins may restore serviceability only after documenting inspection via inventory administration and audit. A fair item can remain serviceable. No fictional penalties or repair deadlines are asserted.
- Accounts deactivate and items retire; do not hard-delete referenced transaction records. Restrict audit contents to actor/action/entity/time and safe state changes; exclude passwords, tokens and free-text purposes from audit details.

## Roles and visibility

| Function | Borrower | Admin |
|---|---|---|
| Catalog and detail | Read | Read |
| Submit request | Own | No borrower impersonation |
| List/detail history | Own only | All, paginated/filterable |
| Cancel pending | Own only | No implicit owner bypass |
| Decide/release/return | Forbidden | Authorized and state-validated |
| Inventory/accounts/audits/dashboard | Forbidden except own profile | Authorized |

The Phase 1 synthetic catalog is temporarily readable without authentication and the runtime database role is read-only. Before exposing the system to a real LAN audience, implement authentication and protect the catalog. Current public-read development routes are not final authorization acceptance.

## Nonfunctional requirements

Three independently deployed tiers, JSON REST over trusted HTTPS, OSI-licensed components/tools under brief §6.1, no generated application tier, no frontend credentials, consistent safe errors, parameterized queries, transactional audit records, restoreable backups, accessible/responsive UI and reproducible tests. The laptop OS and code editor are exempt, and Git hosting is allowed; Docker Desktop and Postman are explicitly disallowed. No production SLA or response-time result is invented. k6 acceptance thresholds are provisional experiment settings, subject to measured baseline and instructor review.

R2 additionally requires recorded curl success/failure per endpoint and appropriate 200/201/400/401/403-or-404/500 usage. R7 requires host CPU/RAM and allocated-resource evidence plus a 3–5-page architectural comparison using measured read/write results. R6 requires a 2–3-page privacy note and notice at collection points. See BRIEF_ALIGNMENT.md for the full acceptance matrix, SUBMISSION_CHECKLIST.md for artifact formats and BASIS_OF_SCENARIO.md for remaining process-evidence gaps. These are requirements, not claims of completed implementation.
