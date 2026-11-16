# Privacy notice and review draft

Primary academic requirement: brief **R6, p. 11**. The final deliverable is a **2–3-page Data Privacy Compliance Note** covering data/purpose, lawful basis, access/control, retention/disposal, safeguards linked to R4, and data-subject access/correction. This Markdown draft is not a completed paginated note. The future login, account and request forms must show a short notice at the actual collection point; a general catalog privacy dialog alone does not establish that requirement.

## Present academic demonstration

EquipTrack currently uses a fictional organization and eight synthetic equipment assets. It seeds no personal accounts, identifiers or working passwords. Do not enter real personal information into test data, screenshots, purposes, remarks, logs or backups. The catalog UI provides an accessible privacy dialog.

Catalog searches are sent to the local FastAPI application. There are no analytics, third-party fonts or application tracking cookies. The native development server may log IP addresses/request paths; the supplied HTTPS gateway disables access logging to avoid recording search strings. The default interactive Swagger page loads vendor CDN assets, which can expose ordinary connection metadata to that CDN; use the local JSON spec or self-host Swagger for a completely offline/private demonstration.

Files under `.env`, `infra/certs`, `backups`, `.venv`, `node_modules` and test-results are local operational artifacts and excluded from version control as appropriate. Access-control, password-hashing and account-session protection are Phase 2 work; no claim of completed privacy compliance is made for this scaffold.

## Intended personal-data processing after review

Proposed future fields are name, school login email, role/student-or-faculty designation, account status, request dates/purpose, custody/condition records, and audit actor/action/time. These are for equipment access and accountability. Do not collect birth date, home address, government/student identifiers, health data, grades, photos or other information unnecessary for the five transactions.

Borrowers see only their own records; authorized custodians see operational records; public users must not see personal borrowing history. Audit details should allowlist status/condition changes and IDs, excluding passwords, tokens, request bodies and unnecessary free text. Password hashes are sensitive authentication data and are never returned through account APIs.

The [NPC's published Data Privacy Act text](https://privacy.gov.ph/DATA-PRIVACY-ACT/) states the general principles of transparency, legitimate purpose and proportionality. Its [school online-learning guidance](https://privacy.gov.ph/npc-phe-bulletin-no-17-update-on-the-data-privacy-best-practices-in-online-learning/) reinforces responsible handling of school-collected personal data. Those sources guide the review; they do not certify this application or prescribe an equipment-record retention period.

## Outstanding institution-specific decisions

For the academic note, specify and label the fictional scenario's modeled controller responsibilities, purposes, proposed retention/disposal and access/correction workflow, with a supported lawful-basis analysis and links to actual safeguards when built. Keep unknown institutional choices and unimplemented features explicit. No fictional DPO identity, real contact, established consent procedure or school-approved retention period is invented here. **The course project must stay synthetic even if real data is offered** (brief §3.3, p. 5); it is not a path to loading real records after informal approval.

Draft notice for that approved deployment must disclose the controller/contact, collected fields, purposes/lawful basis, recipients, storage and retention, safeguards, data-subject rights and request/complaint channels. Consent is not automatically assumed to be the correct basis for every school operation. Resolve this with the institution's privacy authority before collecting data.

Append-only auditing and personal-data erasure require a documented balance: restrict identifiers and retention, provide controlled lawful maintenance under an approved process, and preserve accountability where required. Do not promise unrestricted deletion while keeping identifiable immutable audits indefinitely. Backups need the same access, encryption and retention consideration as primary records.

This is a design/review draft grounded in published NPC material, not a legal opinion or a compliance certificate. Keep the demonstration synthetic until the missing institutional decisions and technical controls have been completed.
