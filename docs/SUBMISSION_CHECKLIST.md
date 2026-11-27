# Academic deliverables and acceptance checklist

Primary reference: MIS 215 Term Project Brief (external course material), §§7–13, pp. 15–22. These are planned deliverables, not claims of submission or approval. Exact dates must come from BU-LMS/FIC announcements; none were supplied. No submission, calendar scheduling, external contact or publication is authorized by this checklist alone.

## Milestones and relative work plan

| Milestone | Brief timing | Required evidence | EquipTrack preparation |
|---|---|---|---|
| M1, 15 points | One week after Midterm Examination | 3–5-page proposal and 5–7-minute presentation | Finalize scenario sources, scope, Option A, architecture/license table and relative plan; obtain FIC topic/protocol approval |
| M2, feedback only | Week 14 | One core transaction live through all 3 tiers and draft protocol specification | Use T1 as the first complete slice; requires real PostgreSQL, not mocked API results |
| M3, 75 points | One week before Final Examination | Repo, report, protocol, privacy note, evaluation | Finish phases 2–6 and evidence below |
| M4, 10 points | One week before Final Examination | 15-minute defense, then questions | All five transactions from a second device, request trace, findings, backup recording |

Sequence after approval: backend/auth → role UI → transaction/concurrency testing → required runtime/HTTPS/LAN and restore → measured evaluation and comparison → final report/rehearsal. Reach a real T1 slice by Week 14. This dependency sequence is not yet a dated Gantt chart; map it to actual announced exam/deadline dates when available.

## Proposal (§8, pp. 15–16)

Body is **3–5 pages**, excluding title page, references and appendices. Preserve this order:

1. Organization Profile: clearly fictional Bicol school, users and location context.
2. Problem Statement: process evidence, problem, need for shared network data, and at least one client-server limitation.
3. Objectives: general objective and 3–5 specific objectives.
4. Scope and Limitations: five core transactions, roles and exclusions.
5. Proposed Architecture: all components, tiers, ports and protocols.
6. Protocol Option: propose Option A and justify REST for this workflow.
7. Stack and License Table: Component; Name and Version; License; Reason for Choosing It; identify ready-made features used.
8. Basis of the Scenario: required for the fictional organization; trace actual practices to sources.
9. Initial Privacy Plan: expected modeled data and purposes, synthetic only.
10. Work Plan: timeline/Gantt from approval to final submission including Week 14.

Include title-page project/student/course/term/date details, APA 7 references and permission-letter appendix only if a real-organization case requires one. Student name/term and exact dates must not be invented. Current Markdown documents are inputs to a proposal, not the final 3–5-page artifact.

## Final Technical Report (§9.1, pp. 16–17)

**20–30 pages excluding appendices; A4, 1-inch margins, 11- or 12-point font.** Ordered sections:

1. Introduction.
2. Requirements Analysis.
3. Development Methodology, with chosen SDLC, rationale and actual phase outcomes.
4. System Architecture (R1).
5. Communication Protocol Specification (R2), full or with full appendix.
6. Data Design and Storage Plan (R3), including client storage and demonstrated backup/restore.
7. Security Design (R4), mapped to implemented controls.
8. Deployment (R5), with reproducibility and network evidence.
9. Testing (R2), functional and recorded protocol results.
10. Performance Evaluation (R7A).
11. Architectural Comparison (R7B), **3–5 pages** covering the six required dimensions and own measurements.
12. Data Privacy Compliance Note (R6), **2–3 pages** covering all six required topics.
13. Conclusions, Limitations and Future Work, including observed advantages/limits of client-server computing.
14. References, APA 7.

Appendices: Stack and License Table, setup guide and Acknowledgment of Tools and Sources, plus supporting protocol/test/evaluation evidence as needed. Do not count incomplete requirements as fulfilled just because they appear in the report.

## Repository and submission package (§9.2 and §12)

- [ ] Git repository link and ZIP copy; no secrets, private certificate keys, dumps or unnecessary build artifacts.
- [x] Clearly named source folders for frontend/backend/infra and setup README scaffold.
- [x] Compose configuration, schema/migration, synthetic catalog seed, backup/restore scripts and env example supplied.
- [x] Demonstrated startup after prerequisites with one Compose command.
- [x] README explains how to generate and retrieve the synthetic accounts locally.
- [x] OpenAPI captures the current routes and protocol contract.
- [x] Recorded curl success and failure coverage in the protocol results.
- [x] Read and write load scripts, all six minimum runs, raw summaries and tier observations.
- [x] Demonstrated backup and restore.
- [x] Root [MIT License](../LICENSE), one of the examples in section 9.2.
- [ ] Full reused-code/library/tool and AI-use acknowledgment, with license notices retained.
- [x] Review PDFs named `MIS215_TP_Brinces_<Deliverable>.pdf`.
- [ ] APA 7 references checked, including source provenance and date/author details rather than guessed dates.

## Defense rehearsal (§10)

| Segment | Time | Required demonstration |
|---|---|---|
| Organization/problem | 2 minutes | Scenario evidence and shared-data need |
| Architecture/protocol | 3 minutes | Three tiers, ports/protocols, proposed/approved Option A |
| Live transactions | 6 minutes | All five through trusted HTTPS from second device |
| Live request trace | 2 minutes | Same request in browser devtools, server log/request ID and DB query |
| Evaluation | 2 minutes | Measured R7A findings and justified R7B comparison |
| Questions | About 10 minutes | Explain own code, rules, framework plumbing and limitations |

Prepare a short backup screen recording; it supplements rather than replaces the expected live demo. Final self-check also includes synthetic-only data, privacy notice at collection, server RBAC, ignored secrets, own transaction handlers, successful restore and complete attribution. Rehearsal, recording and final submission remain pending.
