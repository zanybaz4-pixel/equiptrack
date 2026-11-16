# Primary reference and requirement alignment

The matrix below records the baseline at the time of brief review. See [PHASE2.md](PHASE2.md) for the current implementation and actual verification against R2–R4.

Primary academic reference: [MIS 215 Term Project Brief](MIS215_TermProject_Brief.pdf), Bicol University, College of Science, IT Department, Master in Information Systems. All **22 pages** were reviewed on 2026-11-13. Page references below are the PDF's printed page numbers. The supplied PDF is preserved unchanged.

SHA-256: `f98b356add78c3a0e1212bd7b4819c63426bf090c1a02c12d613e5fcfe033d37`.

`BRIEF_EXTRACTED.txt` is a searchable reading aid extracted from that file. The PDF remains authoritative if extraction order or table layout is ambiguous; key requirement/policy tables were also visually reviewed.

## How the sources apply

The user designated the brief as the primary project reference. It defines academic requirements and acceptance evidence. The user's EquipTrack request supplies the equipment domain, exact five transactions, selected technologies and incremental workflow. Compatible stricter choices remain: exactly five transactions, PostgreSQL, React/Vite/Tailwind, FastAPI/SQLAlchemy, k6, Docker Engine inside WSL2 and locally trusted certificates.

The brief allows 3–5 transactions and alternative stacks/deployment options; it does not require replacing those user selections. REST is **proposed Option A** under R2. Do not claim FIC approval of the topic or protocol; neither has been provided. The brief says a protocol change after approval requires FIC agreement (p. 7).

Instructions addressed to students about submission, contacting the FIC, installations, licensing or account credentials are requirements to plan and satisfy within the user's authorized scope. They are not independent authorization to contact anyone, submit to BU-LMS, publish a repository, change system software or expose a service. No such action was performed during this reference review.

## R1–R7 acceptance matrix

| Requirement / pages | Brief minimum | EquipTrack decision and evidence | Current gap / completion criterion |
|---|---|---|---|
| Scope, pp. 4–7 | Real/realistic Bicol organization; documented processes; synthetic only; 3–5 core actions with read and write; login/logout, two roles, admin accounts supporting | Fictional Bicol Learning Academy; five named transactions in REQUIREMENTS.md; [scenario basis](BASIS_OF_SCENARIO.md) | Detailed rule grounding and FIC proposal approval pending; lending/auth not implemented |
| R1, p. 7 | Browser client, separate application and database processes/containers; no direct client DB; diagram with every component/link port/protocol | React/static Nginx → FastAPI → PostgreSQL; labeled diagram and Compose in ARCHITECTURE.md | Actual container/network execution pending |
| R2 Option A, p. 8 | At least 8 endpoints; GET/POST/PUT-or-PATCH/DELETE; URI/body/response/status/auth spec; consistent errors; 200/201/400/401/403-or-404/500; success/failure for each endpoint using curl/HTTPie/Bruno with recorded results | Nine planned business method/path combinations; own handlers/services; OpenAPI + API.md; curl chosen | Current five GET routes are only a scaffold; 400 not implemented; pytest and the existing positive smoke script do not satisfy the recorded per-endpoint curl matrix |
| R3, p. 10 | Relational DB; at least 3 related tables, ERD/dictionary; authoritative server DB; explain any local storage; backup and demonstrated restore | Six business tables, migration and seed, DATABASE.md, in-memory React state and Secure session cookie. PostgreSQL restore verified in [Phase 5](PHASE5.md). | Include the restore result and cookie/storage decisions in the submission. |
| R4, p. 10 | All browser traffic HTTPS; bcrypt/Argon2; sessions/tokens; server RBAC for 2+ roles; client/server validation; ORM/parameters; ignored env secrets + example | HTTPS config, env example, safe queries/errors; Argon2id/cookie+CSRF plan | HTTP local preview is development evidence only; hashing/auth/RBAC and real HTTPS acceptance pending |
| R5, pp. 10–11 | Reproducible container/VM startup with one command after listed setup; Windows: Engine in WSL2 or base VirtualBox Linux VM; second-device LAN demo | WSL2 Engine startup, localhost HTTPS and restart persistence verified in [Phase 5](PHASE5.md). | Trusted HTTPS demonstration on a second LAN device. |
| R6, p. 11 | 2–3-page Data Privacy Compliance Note: data/purposes, lawful basis, access/control, retention/disposal, R4 safeguards, access/correction; short notice where personal data is collected; synthetic only | PRIVACY.md is a design draft; final required format tracked in SUBMISSION_CHECKLIST.md | Final-length note not authored/validated; login/account/request-form notices and subject access/correction not yet implemented; no real data may be introduced |
| R7A, pp. 11–12 | Owned deployment only; read + write at 1/10/50; throughput/mean/p95/error each run; host CPU/RAM and allocated resources; evidence-backed degradation/bottleneck analysis | [Six completed k6 measurements](PHASE6.md) for authenticated T1 availability and T2 create request, with raw and resource summaries | Review interpretation and discuss co-located test generator during defense |
| R7B, p. 12 | 3–5 pages comparing one permitted alternative on architecture/performance/scalability/security/cost/maintainability, using own R7A evidence + course references | Four-page comparison with a two-tier alternative in section 11 of the final report | Review the argument against the assigned course references |

## Policy, deliverables and rubric

| Brief section / pages | Required treatment | Current response / gap |
|---|---|---|
| §6.1, pp. 12–13 | Every system/build/deploy/test component OSI-licensed; laptop OS and code editor exempt; Git-hosting services allowed; Docker Desktop/Postman/ngrok and listed non-OSI DBs disallowed | STACK_LICENSES.md records the deployed Engine, Compose and mkcert. Phase 5 verification ran with Engine in WSL2. | Audit all final tools and bundled native dependencies for submission. |
| §6.2, pp. 13–14 | Own transaction handlers/business rules; framework plumbing allowed; generated OpenAPI allowed if R2 is met; generated application/API tiers disallowed | Own Python routes/catalog query; future validation/authorization/transitions in services. No Supabase/PostgREST/Hasura/Strapi/Directus/PocketBase/Spring Data REST generated tier. UI/OpenAPI does not replace business code |
| §7–8, pp. 15–16 | Proposal 3–5 pages plus excluded front/back matter; 5–7-minute presentation; Week 14 end-to-end slice + draft protocol; work-plan timeline | [Submission checklist](SUBMISSION_CHECKLIST.md) maps all sections/milestones. Relative timing only; exact BU-LMS dates are unknown |
| §9.1, pp. 16–17 | Final report 20–30 pages excluding appendices, A4, 1-inch margins, 11/12 pt, 14 ordered sections and appendices; APA 7 | Phase 6 review copy has 20 body pages, one cover and three appendices |
| §9.2, p. 17 | Repository source/setup/spec/seed/backup/restore/load scripts/env example; README synthetic test credentials; own OSI-approved LICENSE | Local source archive, MIT License and reproducible synthetic account provisioning prepared. The repository link is pending. |
| §10, p. 17 | 15-minute live defense + ~10-minute questions; all core transactions from second device; devtools→logs→DB trace; backup recording | Rehearsal sequence/timings included in checklist; no recording or successful second-device trace claimed |
| §11, pp. 18–20 | C1 15, C2 20, C3 30, C4 15, C5 10, C6 10 | Evidence prioritized by R1–R7; no self-assigned score or completed compliance claim |
| §12–13, pp. 21–22 | Individual work; sources and AI purposes acknowledged; explain code; PDF naming; Git link + ZIP; self-check | Sources/disclosure draft retained; student review and final formatting/submission still required |

## Immediate corrections and priorities

1. The brief/FOSS policy is now available; the old absence was only the initial workspace state.
2. Exactly five transactions remain within the brief's 3–5 range. Authentication/accounts are supporting functions.
3. Add meaningful **HTTP 400** coverage to Phase 2, for malformed JSON, while retaining documented 422 for well-formed schema-invalid input. Current code still returns 422 for FastAPI validation; do not claim this gap is fixed by documentation.
4. Record curl success and failure evidence **for every final endpoint**, including supporting routes. Existing pytest results and happy-path smoke checks are useful but insufficient for R2.
5. Complete the source basis before presenting detailed lending assumptions as realistic organizational practices. The existing references support custody tracking broadly, not every proposed timing/reservation policy.
6. Add R7B, host/resource evidence, mandatory report lengths, project LICENSE, synthetic demo credentials and defense recording to the acceptance checklist.

This review changes requirements/planning documentation only. It does not implement the remaining services, install tools, change published API behavior, or turn prior local checks into R1–R7 completion evidence.
