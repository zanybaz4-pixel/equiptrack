# Sources, assumptions and assistance

## Interface assets updated November 21 2026

The user supplied the Bicol University seal for the interface redesign. The local PNG has a transparent background prepared with OpenAI image editing. The sign-in page and dashboard use a Bicol University campus-building photograph from [I Love Music](https://madroniolovelee.blogspot.com/), downloaded from [the campus image](https://3.bp.blogspot.com/-1XwqP5yhnWk/UIi1hCGaWHI/AAAAAAAAAC0/nMjwXj64v64/s1600/DSC09429.jpg). The image is stored locally and displayed with CSS cropping and color overlays. The photograph is credited here in the project documentation. These visual assets retain their owners' rights.

Reviewed 2026-11-13. The supplied [MIS 215 Term Project Brief](MIS215_TermProject_Brief.pdf) is the **primary academic reference**, including its §6 FOSS/framework policy. All 22 pages were read; BRIEF_ALIGNMENT.md maps requirements and gaps. No school interview, site visit, instructor approval or real Bicol school policy was supplied. External process and technical sources below support only their specific claims; they do not override the brief.

Phase 6 also used the [DepEd Zambales Library Hub borrowing and return procedure](https://zambales.deped.gov.ph/citizens-charter/borrowing-and-returning-lr-from-lh.html) as a documented analogue for due dates and return inspection. The benchmarking scripts use [Grafana k6's documented metrics](https://grafana.com/docs/k6/latest/using-k6/metrics/reference/) and the pinned [k6 OSS release](https://github.com/grafana/k6/releases/tag/v1.8.2). Codex assisted with the experiment, result interpretation and drafting the PDF review copies.

The brief's §12.2 requires disclosure of AI tools and purposes and the ability to explain submitted work; its §6.1 exempts the laptop OS/code editor and permits Git hosting. This is not a blanket exemption for proprietary build, test or deployment services. Keep a complete actual-tool inventory and verify the specific use against the brief before academic submission.

## Organizational workflow evidence

| Source | Supports | Does not establish |
|---|---|---|
| [DepEd SDO Valenzuela ASSETS](https://sites.google.com/deped.gov.ph/assetmanagement/s/assets) | A published DepEd property unit describes issued-equipment tracking and borrowing/returning/transfer forms | Bicol Learning Academy exists; students may borrow; our exact approval/reservation rules |
| [DepEd Order 001 s. 2023](https://www.deped.gov.ph/wp-content/uploads/2023/01/DO_s2023_001.pdf) | Documented equipment/property accountability forms and assigned administrative roles | A mandate for this application's specific two-role UI or five-state service process |

The application is a proposed academic design informed by these practices. Pending-request cancellation, half-open intervals, release timing, damage handling and the exact role matrix derive from the user's project requirements and explicit design assumptions in REQUIREMENTS.md, not an invented established school policy. No real school or DepEd endorsement is claimed.

## Technical and deployment sources

- [PostgreSQL constraints](https://www.postgresql.org/docs/17/ddl-constraints.html) and [range/exclusion types](https://www.postgresql.org/docs/17/rangetypes.html): relational integrity and reservation overlap protection.
- [FastAPI official source/documentation](https://github.com/fastapi/fastapi): framework and OpenAPI support. Business services are written for this project; no database-generated application tier is used.
- [Docker Engine Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/) and [Docker Desktop license](https://docs.docker.com/subscription-billing/desktop-license/): distinguish the FOSS Engine target from detected Desktop tooling. No installation commands were executed.
- [mkcert official project](https://github.com/FiloSottile/mkcert): local development certificates and caution around the root CA private key.
- [NPC Data Privacy Act](https://privacy.gov.ph/DATA-PRIVACY-ACT/) and [school guidance](https://privacy.gov.ph/npc-phe-bulletin-no-17-update-on-the-data-privacy-best-practices-in-online-learning/): principles for the review draft, not a legal compliance determination.
- Version/license metadata was queried from `https://pypi.org/pypi/PACKAGE/json` and `https://registry.npmjs.org/PACKAGE/latest`, then selected versions were installed and recorded. Specific versions and links appear in STACK_LICENSES.md, requirements files, package lock and dependency-inventory.json.

Primary sources support the associated design choices within their stated scope. No passages or code from a school system were copied. The synthetic school/asset descriptions and original project code were generated for this academic scaffold. Lucide supplies open-source vector interface icons. The November 21 redesign includes the image assets credited above and locally hosted DM Sans fonts from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/dmsans), distributed under the SIL Open Font License; the license is included in `frontend/public/fonts/OFL.txt`.

## AI-assisted contribution disclosure draft

> This project used OpenAI Codex to assist with requirements analysis, architecture and schema design, initial React/FastAPI code, migration and infrastructure scripts, synthetic equipment data, test cases, debugging, documentation and source/license research. The student is responsible for reviewing, understanding, adapting and validating the work, checking the MIS 215 brief and permitted-tool policy, verifying cited sources, and accurately presenting actual test and deployment results. This disclosure describes assistance and does not claim the student independently authored all generated material.

Adjust to the instructor's required format and record student changes. Codex is a disclosed assistance tool, not a FOSS runtime dependency. Docker Desktop was detected as existing software; it was not installed or used to certify the required deployment. No subagents, real school records, cloud service deployment, external messaging, or system-level installations were used for this increment.

## Defense review prompts

Be able to explain why approval differs from release, why pending does not reserve, how a partial unique index differs from an interval exclusion constraint, why application row locks are still needed, how damage affects availability, why overdue is derived, where role/ownership checks belong, why the browser cannot hold database credentials, and why mocks/builds do not establish PostgreSQL or LAN acceptance. Trace one future mutation from HTTPS request through authorization, locked service transaction, constraint check, audit insert and commit/rollback.
