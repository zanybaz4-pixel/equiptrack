# EquipTrack term project proposal
@cover
Bicol University • College of Science • Master in Information Systems

MIS 215 Client-Server Computing • Felix R. Penetrante

School Equipment Borrowing, Return, and Tracking System

Prepared by {{AUTHOR}}

{{COVER_DETAILS}}

{{STATUS}}

===
# 1 Organization profile
Bicol Learning Academy is a fictional school in the Bicol Region. Students and teachers need shared classroom equipment at specific times. The custodian records who has an item, its expected return, and whether it needs maintenance. The project models the equipment-lending register as a service available to those two groups.

## 2 Problem statement
When borrowers ask for equipment and the custodian records custody in separate steps, a list of current items can hide a future reservation or an overdue loan. A shared database associates each request and handover with an item and its borrowing interval. The single source of truth can serve a phone and a staff computer at the same time. Borrowers depend on the school network and service availability, and the school must protect and back up the register.

## 3 Objectives
The general objective is to build, deploy and evaluate a three-tier equipment-lending system for a synthetic school.

- Show date-aware availability and give borrowers access to their own request and loan history.
- Preserve the approval, release and return history for the custodian.
- Protect access and consistency through HTTPS, server role rules and database constraints.
- Prove recovery and measure one read and one write at the concurrency levels specified in the brief.

## 4 Scope and limitations
The five transactions are checking availability, submitting a request, deciding a request, releasing an item and recording its return. Students and faculty are borrowers. A custodian is the administrative role. The demo uses fictional accounts and equipment. Integration with school identity, payments, notifications and inter-school inventory falls outside this project.

===
# 5 Proposed architecture
@architecture

The React presentation tier uses HTTPS to reach the Nginx gateway. FastAPI is the application tier, reachable at port 8000 on the internal network. Only FastAPI and authorized migration or recovery services use the PostgreSQL tier at port 5432. The gateway is published on port 8443 during the demonstration.

## 6 Protocol option
Option A uses a documented REST API with JSON over HTTPS. A catalog read can be retried. A request creates a record and returns its ID and state. The decision, release and return routes make transitions explicit. The workflow does not require persistent connections.

## 7 Stack and license selections
| Component | Name and version | License | Reason |
| Presentation | React 19.3.1 | MIT | Role-based browser views |
| Application | FastAPI 0.162.5 | MIT | Explicit routes and OpenAPI |
| Database | PostgreSQL 17.12 | PostgreSQL License | Transactions and constraints |
| Gateway | Nginx 1.28 | BSD-2-Clause | HTTPS and reverse proxy |
| Deployment | Engine 29.9.3, Compose 5.7.1 | Apache-2.0 | Repeatable Ubuntu WSL2 services |
| Evaluation | k6 OSS 1.8.2 | AGPL-3.0 | Reproducible concurrency tests |

The selected ready-made features are UI rendering, routing, schema validation, ORM parameter binding and container orchestration. The five transaction handlers and their equipment rules are implemented in this project.

===
# 8 Basis of the scenario
The DepEd Schools Division of Zambales (n.d.) publishes a borrowing and return procedure for a Library Hub. It identifies school borrowers, staff checks, agreed return times and inspection of returned materials. This establishes an analogue for issuing, tracking and receiving shared learning resources. The materials and actual participants differ from this equipment project.

The DepEd Schools Division of Valenzuela (n.d.) describes tracking issued property and offers forms used in borrowing, returning and transferring assets. DepEd Order No. 001, s. 2023 establishes property-accountability procedures in a public education setting. These sources support documenting transfer and return. EquipTrack proposes borrower self-service, custodian approval and maintenance routing as part of its fictional design.

## 9 Initial privacy plan
Model the minimum fields for login, ownership, lending and custody. Use entirely synthetic accounts during build, evaluation and defense. Supply a notice at data-entry points. Use HTTPS, secure password hashes, least-privilege access and a protected audit trail. A real school would review applicable lawful bases, storage periods and how users can exercise rights before collecting any personal data.

## 10 Work plan
| Milestone | Planned activity and evidence |
| Topic and protocol approval | Review the fictional organization, five transactions and Option A with the instructor |
| After midterms | Present the proposal and the trace from organizational need to design |
| Week 14 | Show catalog availability through the browser, API and PostgreSQL and bring the protocol draft |
| Before final submission | Integrate the lifecycle, complete deployment and recovery, measure the system and document the design |
| Defense | Rehearse all five transactions from a second device and prepare a supporting recording |

The schedule follows the term brief. The instructor announces exact dates through BU-LMS.

===
# References
@references
