# EquipTrack final technical report
@cover
Bicol University • College of Science • Master in Information Systems

MIS 215 Client-Server Computing • Felix R. Penetrante

School Equipment Borrowing, Return, and Tracking System

Prepared by {{AUTHOR}}

{{COVER_DETAILS}}

{{STATUS}}

@contents

===
# 1 Introduction
## Organization and problem
Bicol Learning Academy is a fictional school in the Bicol Region. Its students and faculty need to check when shared classroom equipment is available, while an equipment custodian needs consistent records of approvals, handover and return. A projector can have an upcoming reservation, an open loan or a maintenance hold. A record that merely labels an item “available” cannot explain which dates it is available or who currently has custody.

Documentary grounding comes from two Philippine school-resource contexts. DepEd's Zambales Library Hub describes requests and staff inspection of returned supplementary learning resources under an agreed due date (Department of Education, Schools Division of Zambales, n.d.). The Schools Division of Valenzuela describes an asset issuance register and forms for borrowing, return and transfer (Department of Education, Schools Division of Valenzuela, n.d.). DepEd Order No. 001, s. 2023 supplies a wider property-accountability context (Department of Education, 2023). The short-term equipment slots, student eligibility, role boundaries and maintenance rule in EquipTrack are proposed policies for this scenario.

## Objectives
- Give student and faculty borrowers a date-aware catalog and a record of their own requests.
- Let a custodian approve requests, record custody transfers and document returned equipment condition.
- Keep competing reservations and active custody consistent in a shared database.
- Demonstrate authenticated HTTPS, repeatable local deployment and recovery from a backup.
- Evaluate one read and one write and use the measurements to compare the design with a two-tier alternative.

The technical scope is a synthetic academic demonstration. No school records were collected. Topic and protocol approval depend on the instructor.

===
# 2 Requirements analysis
## Actors and permissions
Student and faculty accounts use the same borrower role. A borrower can see the catalog, submit and cancel eligible requests, see their own history and edit their display name. A custodian uses the administrator role. The custodian reviews requests, records release and return, and maintains equipment, categories and synthetic user accounts. Server authorization governs each action. The role-specific menus guide each user to the corresponding tasks.

## Five core transactions
| Transaction | Actor | Successful outcome |
| T1 View availability | Borrower or custodian | Catalog reports availability for the selected period |
| T2 Submit a request | Borrower | A durable pending request identifies the borrower, item, period and purpose |
| T3 Decide a request | Custodian | Approval reserves the period or rejection records the decision |
| T4 Release an item | Custodian | An active loan records pickup time and condition |
| T5 Record a return | Custodian | Custody closes and equipment condition and service status are updated |

When a borrower submits a request, availability is checked again on the server. A pending request does not allocate the period. An approval locks the equipment and verifies the remaining rules before committing. The custody record and request status change together. A damaged return places the item in maintenance. Canceled, rejected and returned requests remain part of history.

## Quality requirements
The client communicates with a documented HTTPS API. PostgreSQL is the authority for equipment, users and records. The system keeps enough audit history to trace a decision and has a repeatable backup and recovery procedure. The interface uses Philippine time, works across narrow and wide layouts and presents recoverable validation or connection errors. The installation must be reproducible inside an approved runtime and reachable from a second networked device during defense.

===
# 3 Development methodology
## Incremental delivery
The equipment register was implemented as a small end-to-end slice before adding changes of state. This let the catalog establish the contract between browser, API and PostgreSQL. Adding user roles, requests and loans to the same slice kept database integrity checks and user interactions visible in each later increment.

| Phase | Delivered and verified |
| 1 Foundation | Requirements, architecture, initial schema and API-backed catalog |
| 2 Backend | Sessions, role checks, lifecycle routes, real PostgreSQL transaction checks |
| 3 Browser | Borrower and custodian workspaces, request history, laboratory browser walkthrough |
| 4 Integration | Route and response matrix, validation, concurrent requests and damaged returns |
| 5 Deployment | Ubuntu WSL2 Engine, HTTPS gateway, database recovery, second-device walkthrough in progress |
| 6 Evaluation | Isolated k6 workloads, performance interpretation and academic evidence package |

The acceptance checks start with decisive boundaries. A database double establishes an HTTP shape. Tests against PostgreSQL establish constraints and transaction behavior. A browser workflow establishes the observable UI outcome. The live LAN walkthrough establishes reachability from another device. Each covers an independently relevant failure mode, and its evidence is recorded with the environment in which it ran.

The most consequential implementation refinement was moving decisions about conflicts and custody into the application transaction backed by PostgreSQL constraints. Frontend availability is useful for selection. It can become stale while another person approves an overlapping request. The transaction rechecks the conditions after obtaining the equipment lock and persists the corresponding audit entry for successful state changes.

===
# 4 System architecture
@architecture

The presentation tier is the React application served by an internal web server. The visible HTTPS entry point is Nginx. Nginx serves the application via the presentation network and forwards /api calls across the application network to FastAPI. The API and database share a separate data network. No database or application port is published to the LAN.

FastAPI verifies the caller and request data before selecting a catalog read or a lending transaction. SQLAlchemy maps the relational model and sends parameterized SQL to PostgreSQL. The database applies referential integrity, unique active custody and exclusion rules for approved and released reservation periods. Migrations run with an owner role. The API connects with a restricted role, and the browser receives only the API representation.

For an approval, the browser sends a JSON decision to the gateway. FastAPI authenticates the session and role, locks the affected equipment, checks overlapping reservations and writes the decision and the audit entry in one transaction. The response comes back through the same gateway. A second client can request the resulting state from the shared server.

The gateway retains the request host and forwarded HTTPS scheme so URL redirects retain the externally visible port. If PostgreSQL stops, liveness stays available while readiness signals that the service cannot use its database. This allows an operator to distinguish an application process failure from a data-tier dependency failure.

===
# 5 Communication protocol
## Option A REST over HTTPS
The API sends JSON under /api. GET reads resources. POST creates requests and performs explicitly named lifecycle transitions. PATCH corrects fields such as a display name. PUT replaces selected catalog records. DELETE is used for the documented category removal operation. The complete contracts, path parameters, body shapes and response codes appear in the supplied OpenAPI file. The companion protocol document contains a method and path index and a demonstration sequence.

| Operation | Successful exchange |
| Sign in | POST /api/auth/login returns user summary, CSRF value and a Secure session cookie |
| Check availability | GET /api/equipment with borrow_at, due_at and limit returns an item page |
| Request equipment | POST /api/requests with item ID, period and purpose returns 201 and a pending request |
| Decide and hand over | A custodian issues the documented decision and release requests for the request ID |
| Record a return | The custodian posts condition and optional remarks and receives the updated resource |

The API uses timestamps with an offset. The browser translates them to Philippine time for display and input. Authenticated mutations send the same-origin header and session-derived CSRF value. A request identifier is returned in headers to help correlate diagnostics without exposing passwords or session values in logs.

Errors use a JSON envelope. Malformed bodies yield 400, missing credentials 401, disallowed access 403, unavailable resources 404, conflicting state 409 and validation failures 422 when the input has the wrong shape or constraints. A PostgreSQL outage yields a readiness 503. A request from an unauthorized role or owner cannot acquire access by guessing another borrower’s resource identifier.

===
# 6 Data design and storage
@erd

The borrower and equipment foreign keys connect each request to the people and inventory it concerns. The loan table records release and return actors and time. The distinct request and loan entities preserve the difference between allocation and physical custody. An audit event carries the action, actor, entity type and ID, and structured details. The actor is a foreign key. The heterogeneous entity ID supports events on more than one type of record.

| Entity | Principal data and integrity |
| users | Unique email, hash, role, borrower type and active flag |
| auth_sessions | Token digest, user reference and expiry |
| equipment_categories | Unique category name |
| equipment_items | Unique asset code, category, condition and service status |
| borrowing_requests | Borrower, item, period, purpose, decision and status |
| loan_records | Unique request, active custody, release and return details |
| audit_logs | Actor and succinct record of a committed action |

The controlled status and condition vocabularies prevent unexpected values. The period constraint requires the due time to follow the borrowing time. The exclusion rule on half-open periods permits adjacent reservations. The active-loan rule enforces one open custody record per item. PostgreSQL rejects data that would violate those invariants even when requests arrive concurrently.

===
# 6 Data storage and recovery
## Client and server storage
The React client loads its business data from the API and keeps viewed data and CSRF state in memory. Reloading fetches current data. The browser cookie holds an opaque credential under HTTPS; PostgreSQL stores its digest with an expiry. The database remains the authoritative record across browsers. The interface does not use browser storage as an offline equipment register.

## Backup and demonstrated restore
The backup command uses PostgreSQL's custom-format dump and preserves schema and grants. It excludes active session rows. A temporary file is completed before the archive is published. The restore command validates the archive and restores into a fresh named database. A repeated attempt to use the same target name is rejected. The original database can remain available while an operator checks the restored copy.

| Observed recovery evidence | Result |
| Schema | Alembic revision 0002_sessions |
| Business records | 4 users, 9 equipment items, 5 categories, 3 requests and 1 loan |
| Audit and damage | 14 audit events and one damaged-return record |
| Sessions | 2 in source and 0 in restored database |
| Restored access | API worked with the restricted application role |
| Persistence | Database restart preserved the source snapshot |

The exercise also checked the active-loan and reservation constraints and the audit trigger. The stored archive matched the recorded SHA-256 digest. Infrastructure credentials remain deployment-specific. A restored application requires the correct role grants and new sign-ins. The measured artifact is the Phase 5 recovery drill, performed in a separate synthetic environment.

===
# 7 Security design
| R4 control | Implementation and evidence |
| HTTPS | Nginx terminates TLS. The local mkcert chain was verified with an explicit CA bundle |
| Password protection | Argon2id hashes are stored. Provisioning creates random synthetic credentials |
| Authentication | Opaque HttpOnly, Secure, SameSite cookies and expiring server-side session digests |
| Authorization | FastAPI checks role, account activity and ownership at protected routes |
| Input validation | Client date and field checks support entry. Pydantic and domain rules decide on the server |
| SQL safety | SQLAlchemy and bound parameters. Separate owner and runtime database roles |
| Secret handling | Deployment values live in ignored environment files. The example contains placeholders |

Mutating routes also compare the request origin and verify a session-derived CSRF header. Login throttling bounds repeated attempts at the gateway, and Argon2 work is limited inside the API. Logout revokes the session. An inactive account cannot create a valid session. Borrowers cannot decide, release or return equipment through the custodian routes.

Catalog and request searches avoid logging arbitrary query strings at the gateway. Diagnostics use request IDs and structured, limited metadata. An inspection found none of the five generated demo and database passwords in the deployed frontend or captured logs. The check was scoped to those known values and artifacts.

The local CA creates trust for this demonstration. The private CA key stays in Ubuntu. The Android test uses only the public certificate. A real deployment would require institution-managed trust, patching, access reviews and an approved incident-handling process.

===
# 8 Deployment
## Runtime and preparation
Ubuntu 24.04 LTS on WSL2 hosts Docker Engine 29.9.3 and Compose 5.7.1. The program uses Nginx 1.28, FastAPI and PostgreSQL 17.12 in separate services. mkcert 1.4.4 generated a development certificate for localhost and the observed laptop LAN address. The installations and image digests are recorded in PHASE5.md.

After preparing distinct database role passwords in the environment file and issuing the development certificate, `docker compose up --build -d --wait --wait-timeout 180` builds, migrates and starts the system. The migration job completes before the API becomes available. The seed is explicit and creates synthetic records. Separate runtime and migration credentials keep owner privileges out of the API container.

## Network demonstration
The local test published only HTTPS on port 8443. Under WSL2 NAT, the approved Windows listener forwarded TCP 8443 on the Private Ethernet interface to the WSL-side gateway. The rule is restricted to the local subnet. A certificate-verified readiness check and the frontend page loaded from the laptop on the LAN address. The user reported opening the site on Android. The request progression is recorded with the evidence available in PHASE5.md.

When Ubuntu stopped, the LAN address timed out. Restarting the lab stack and keeping the WSL test session open recovered it. For defense, start the stack in advance, check the WSL address and Windows listener, and verify the same network and certificate trust on the second device. Keep database and API ports on the internal networks.

===
# 9 Testing
## Functional and integration coverage
The application has automated checks for authentication, role denial, loading failures, availability, borrower ownership, state transitions and transactional integrity against PostgreSQL. The browser walkthrough covered request persistence, custodian approval and pickup, damaged return and history display. Reversed dates, cancellation, rejected requests and overdue loans were also exercised. The integration suite recorded 41 passing tests. Full-browser and database tests have separate evidence because they probe different boundaries.

## Recorded protocol coverage
The Phase 4 matrix recorded 67 outcomes from the HTTP protocol suite. The Phase 5 isolated deployment recorded 64 checks through Nginx over HTTPS. The suites overlap and the counts should not be added together. The matrix includes successful and deliberately rejected requests for the documented API, including syntax errors, authorization and concurrent conflict cases. See the raw JSON results and the specification shipped with the source.

| Representative test | Expected and observed behavior |
| Missing credentials | Catalog returns 401 |
| Borrower uses a custodian path | Server returns 403 |
| Overlapping approval race | One approval succeeds and the other receives a conflict |
| Malformed JSON | The API sends HTTP 400 and a structured error |
| Damaged return | Loan closes and item moves to maintenance |
| Database interruption | Liveness stays 200 and readiness returns 503 |

The Phase 5 test also exercised a redirect through HTTPS and confirmed the host port survives the redirect. The recovery drill checked the restored data and grants. A separate defense rehearsal matched the identifier in a real HTTPS 201 response to the Nginx log and the corresponding database and audit rows. The defense overlay logs a fixed creation route, method, status and request identifier. The trace evidence and commands accompany the source.

===
# 10 Performance experiment design
## Workloads and controls
The read trial calls GET /api/equipment with a fixed borrowing interval and 12-item limit. It checks both HTTP 200 and the returned item count. The write trial sends POST /api/requests, with a legitimate session, origin and CSRF header, for each virtual user's assigned equipment. It checks HTTP 201 and the created request's state and asset identity. The purpose text and equipment are synthetic. Each user is assigned a distinct account and item, so the write trials estimate independent submissions. They do not simulate a rush to reserve the same projector.

Each of the two workloads ran at 1, 10 and 50 constant virtual users. Each cell uses a five-second warm-up, followed by a separate 30-second measurement. Each user starts the next iteration after one second of think time and its previous response. Borrowing and loan rows from the warm-up and the previous cell are cleared only in the isolated performance database. The audit table remains append-only. Committed requests and new audit events are counted separately after each cell. Login setup and warm-up traffic are excluded from the measured data.

## Test environment
@environment

k6 shares the WSL host with the application. Its traffic enters Nginx through the host's loopback port 28443 with the local CA bundle and then follows the API and PostgreSQL path. The experiment therefore measures the local container path with TLS, without Android Wi-Fi delay or browser rendering. Latency is the request sending, waiting and response-receiving interval recorded by k6. HTTPS verification remains enabled. This lab setup is owned by the project and isolated from the demonstration database.

===
# 10 Performance results and interpretation
@results

Throughput is the k6 transaction counter divided by the recorded run duration, including its graceful finish. Average and p95 use k6 request duration, in milliseconds. The error rate is the proportion of attempts that did not produce the expected HTTP status. The raw records separately preserve response body check results. Two initial starts were excluded before any timing samples were taken. The fixture handoff and an attempted reset of the protected audit table were corrected before the measured series.

{{FINDINGS}}

{{RESOURCE_FINDINGS}}

A single run per cell is sufficient for the required matrix and limits confidence in the exact ordering of nearby values. The loopback placement avoids variable wireless delay and may introduce contention with the test generator. Repeat runs, persistent arrival rates, a separate load generator and a hot-item workload would answer different questions about production capacity. The read and write throughput values reflect the specified pacing, including the one-second pause, so they cannot be treated as maximum throughput.

===
# 11 Comparison architecture
@alternative

The alternative for Bicol Learning Academy is a native or managed desktop client that connects directly to PostgreSQL on the school network. The client can issue parameterized SQL and receive rows without an HTTP application service. A careful version would put reservation and custody operations into centrally maintained database routines and grant each authenticated role only the required operations.

EquipTrack puts the presentation and transaction decisions on separate tiers. React displays date-aware results and guides users. FastAPI evaluates caller, role, ownership, period and state, and opens a transaction through a small pool of database connections. The database remains responsible for integrity constraints and durable storage. The term project brief treats a direct database client as a comparison model and requires the delivered implementation to retain three tiers (Penetrante, n.d.).

The two-tier design might suit a single custodian or a small fleet of centrally managed computers. That context would make desktop releases and native database connectivity manageable. EquipTrack includes borrowers using phones or shared devices, and its second-device demonstration already relies on an ordinary browser. A browser-based workflow lets a school update the interface and business rules centrally and serves the same API contract across platforms.

The comparison holds the entity model and lending rules constant where possible. It attributes differences to the location of the application rules, the network path and the operational responsibilities. There is no measured two-tier prototype in this evaluation.

===
# 11 Comparison performance and scalability
{{COMPARISON_DATA}}

A native database client can avoid HTTP and JSON serialization. It can reduce end-to-end latency when the database procedure bundles all checks and the client maintains a safe connection. When the desktop program sends several SQL round trips over the LAN, the saved HTTP hop can be offset by the additional database round trips. The local p95 values in this experiment cannot estimate the net effect. The benchmark includes authenticated API handling and database work under TLS on a single Windows host.

Pooling changes how growth reaches the data tier. A three-tier service can reuse connections across browser sessions and limit concurrent database work at one chokepoint. A naïve two-tier client can keep a connection for each desktop instance. Each additional instance then competes for PostgreSQL processes and memory. A database proxy or restrictive stored procedures could reduce this burden, with added infrastructure or design work.

For simultaneous requests on the same item, both architectures need a rule that serializes conflicting state changes and a database constraint that remains correct at commit. More clients or more API replicas would leave a hot item subject to its own capacity and row-lock behavior. EquipTrack's independent-item workload leaves that scenario open. The functional concurrency check supplies correctness evidence for overlapping approvals, separate from the timing experiment.

The school should use an application tier and measure the patterns that matter for its scale. Daily browsing and independent requests benefit from a shared service. If borrowers repeatedly choose a few popular devices, testing the lock path is more informative than increasing the number of idle sessions.

===
# 11 Comparison security and cost
## Security responsibilities
EquipTrack gives each borrower a web session and exposes a documented set of operations. The app role reaches PostgreSQL on an internal network. It cannot migrate or drop the schema. Ownership and access rules are enforced through centralized dependencies and protected query paths. The loan and reservation constraints protect consistency at the database boundary.

A direct-database alternative can implement strong controls with TLS, per-user privileges, row-level security and stored procedures. It must also provision and revoke credentials across clients and expose a PostgreSQL endpoint to that client network. The implementation would need to demonstrate that a user who edits the desktop program or connects with a general SQL tool receives only the access intended for the role. Direct access increases the importance of the minimum DB privilege design and database-facing support work.

## Cost and operational effort
The measured EquipTrack stack runs on one existing laptop without a paid hosting dependency. A school deployment still needs an operator, a machine or hosting service, network support, backups, recovery tests and security maintenance. The extra service tier adds container and API maintenance. The presentation can be updated once for everyone with a browser.

A small two-tier deployment could use fewer shared server processes. Desktop setup, application updates, local troubleshooting and database connectivity support would be spread across managed computers. Procedures and database access policies also need a release process. The school would need to price staff time, device coverage and maintenance against measured use. The local lab evaluation did not measure electricity, staff effort or hosting expense, so there is no currency estimate.

===
# 11 Comparison maintainability and decision
## Maintaining a shared workflow
EquipTrack centralizes domain rules in the API and schema. The OpenAPI description and recorded protocol checks give the browser a stable contract when the database evolves. For example, changing when a custodian can approve or release a request typically involves one deployment plus the client help text. Existing users receive the browser version on refresh.

In a direct-database design, moving rules into stored procedures can centralize policy but makes the database schema and procedure signatures part of the client contract. The school then needs an explicit plan for older clients, compatible procedure changes and credential rotations. Database-native procedures can be clear and reliable for a small controlled fleet. A school that supports phones has more client variants and a broader distribution problem.

The practical choice for the fictional school is the implemented three-tier system. It supports the intended devices, keeps the database reachable only inside the application network and makes a shared queue and custody rules available across client sessions. The timed tests establish the behavior of a small, co-located prototype under the studied read and write traffic. They suggest where further measurements and tuning would have value. The result does not establish a universal performance advantage for the three-tier pattern.

A next evaluation would repeat tests from a separate client machine, use a larger catalog with historical data, and compare independent submissions with simultaneous attempts for a common asset. Only a controlled alternative prototype could quantify the performance impact of replacing FastAPI with direct database calls.

===
# 12 Data privacy compliance note
## Collection and purpose
EquipTrack uses synthetic data for the course project. A real school application would collect the minimum identifiers needed to manage accountability for borrowed equipment. Republic Act No. 10173 and the National Privacy Commission’s implementing rules provide the framework for transparency, purpose limitation, proportionality and data-subject rights.

| Field group | Why the application uses it |
| Account name, login email and role | Authenticate the user, identify the borrower and apply permissions |
| Borrower type | Distinguish student and faculty demonstration profiles |
| Request details and time slot | Explain an equipment request, resolve a schedule and record custody |
| Release and return details | Document the handover and preserve servicing history |
| Session and audit records | Protect authentication and trace an authorized decision |

The request purpose field should describe the equipment use. The notice at the account and data-entry screens explains the demonstration and discourages putting anyone else's identifying or sensitive information in free text. Staff should communicate how a production system handles names and optional remarks before any collection. The labels in the demonstration correspond to invented people and assets.

## Lawful basis
The course project models how a school might administer loans without using identifiable student records. For any later deployment, the school as personal information controller would document a lawful basis for each purpose under section 12 of the Act. Section 13 requires separate analysis where education-related or other sensitive personal information is involved. A school privacy officer would confirm the relevant authority or other lawful condition, the necessity of each field, and any special considerations for minors. The project has no institutional policy or processing authority to assert.

===
# 12 Privacy access rights and retention
## Access and security measures
Borrowers can see and correct their display name in **My profile** and see their own request history. They cannot read another borrower's loan records. Custodians can see the account and loan details needed for approval and custody. The server makes these decisions from the current session and request ownership. PostgreSQL access is reserved for the application and authorized operators. Authenticated HTTPS, Argon2id, secure cookies, restricted roles and secret handling implement the R4 safeguards summarized in section 7.

A real school would identify its accountable privacy contact in the collection notice, verify the requester's identity and provide a process for access, correction and other data-subject requests. The self-service name change handles one narrow correction. Corrections to lending history require review so associated custody and audit data remain intelligible. The operator should document why access is needed, review it when duties change and record any disclosure.

## Proposed retention and disposal
Demo accounts, TLS trust files, temporary sessions and loan copies are practical teaching artifacts. Keep the synthetic run outputs for the academic assessment and remove ephemeral credentials when the lab no longer needs them. Live sessions expire and are omitted from portable database backups. The restore exercise explicitly checked that they were absent.

For a real school, the proposed schedule would retain open lending records during the loan and closed records through the school's applicable accountability and dispute period. Backup copies would follow a documented rotation, with expiry and approved disposal. The custodian and privacy officer would determine actual periods, approved holds and disposal steps before launch. The demonstration does not implement a production retention schedule. Removing a working copy alone does not purge retained backups.

===
# 13 Conclusions limitations and future work
EquipTrack demonstrates a shared, authenticated borrowing workflow through a browser, API and database. The API and database jointly handle lifecycle rules and conflicting approvals. The recovery exercise restored the schema, records and restricted access in a fresh PostgreSQL database. A user's Android access and the project's request progression are documented with the available live evidence.

The evaluation compares 1, 10 and 50 constant users over the tested HTTPS path. Its reservoir of synthetic users and items supports a controlled workload. The laptop's shared WSL resources, independent write items, modest dataset and short runs limit extrapolation. A production assessment would include more tenants or larger borrower populations only after a documented need, a retention policy and organizational authorization exist.

Client-server deployment helps the school keep one authoritative inventory and allows borrowers and custodians to work from different devices. It introduces a dependency on the network, the server and certificate trust. The Android session exposed a practical example when WSL stopped and the address timed out. Planned maintenance, a monitored deployment and a documented recovery process are needed when the service becomes operationally important.

Course acceptance still depends on the instructor, the student's review and the live defense. Capture the five transaction steps and the same-request trace through browser, API and database. Source code reuse and AI-assisted work must be accurately acknowledged. The school case remains synthetic, with published evidence supporting analogous practices and explicit design assumptions for its lending rules.

===
# 14 References
@references

===
# Appendix A Stack and license inventory
@licenses

===
# Appendix B Setup and reproduction
1. Start Ubuntu in WSL2 with its installed Docker Engine and Compose plugin.
2. Copy the environment example and set two distinct random database role passwords with corresponding URLs.
3. Generate the development certificate, covering the exact address to be used. Establish client-side trust in the public development CA.
4. Run the Compose startup command from the project directory, then run the synthetic seed and demo account provisioning once.
5. Use the gateway's HTTPS address, check OpenAPI and verify readiness before starting the walkthrough.
6. Run the backup script and restore into a fresh database for the recovery demonstration.
7. Run scripts/performance.sh from Ubuntu after setup. The script uses a uniquely named database and loopback port 28443, runs the six experiment cells and writes raw results below test-results/performance.

The source includes the Compose topology, startup guide, migrations and synthetic fixtures. The companion protocol specification contains the endpoint index and specimen exchanges. The ZIP intentionally omits generated passwords, certificate keys, backups and local build folders.

The dependency inventory and lock files record the selected versions. Third-party features used include React rendering, FastAPI routing and schema validation, SQLAlchemy parameterization and persistence, PostgreSQL constraints and recovery utilities, and Nginx serving and proxying. The original EquipTrack code uses the MIT License, one of the examples in the MIS 215 brief. See STACK_LICENSES.md for source links and the version inventory.

===
# Appendix C Acknowledgment of tools and sources
OpenAI Codex assisted with requirements analysis, design, application and infrastructure code, test scripts, troubleshooting, source research, performance analysis and drafting. Published DepEd sources ground the fictional workflow. Exact technology versions and license sources are captured in the stack inventory and lock files. The student must review, understand and be ready to explain the generated and adapted work during the defense.

The runtime evidence was gathered with Docker Engine and Compose inside Ubuntu WSL2, mkcert, Nginx, curl, PostgreSQL tools, and Grafana k6 OSS. The project used local synthetic accounts and equipment. The report and benchmark do not assert external deployment, institutional approval or benchmarking of the comparison architecture.
