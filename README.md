# EquipTrack: Equipment Borrowing and Return Tracking System for Bicol University College of Industrial Technology – Mechanical Technology Department

**Current increment: Phase 6.** The three-tier WSL2 deployment, backup recovery and six performance runs have been verified. [Phase 5](docs/PHASE5.md) records the status of the second-device rehearsal.

The primary academic reference is the MIS 215 Term Project Brief supplied by the course. See the [R1–R7 alignment and gaps](docs/BRIEF_ALIGNMENT.md). The [original EquipTrack request](docs/PROJECT_REQUEST.md) specifies the five core transactions.

The demonstration organization, **Bicol University College of Industrial Technology – Mechanical Technology Department in Legazpi City, Albay**. The current sources partly ground the scenario; specific lending practices still need evidence in the [Basis of the Scenario](docs/BASIS_OF_SCENARIO.md).

## Start here

- [Primary brief alignment and acceptance gaps](docs/BRIEF_ALIGNMENT.md)
- [Milestones, report formats and submission checklist](docs/SUBMISSION_CHECKLIST.md)
- [Performance and architectural comparison plan](docs/EVALUATION_PLAN.md)
- [Detailed six-phase plan and acceptance criteria](docs/IMPLEMENTATION_PLAN.md)
- [Requirements and proposed workflow](docs/REQUIREMENTS.md)
- [Three-tier architecture and transaction design](docs/ARCHITECTURE.md)
- [ERD and data dictionary](docs/DATABASE.md)
- [Phase 2 API contract and setup](docs/PHASE2.md)
- [Current OpenAPI specification](docs/openapi.json)
- [Installation, HTTPS, LAN, backup and restore](docs/INSTALLATION.md)
- [Optional Render internet preview](docs/RENDER.md)
- [Testing and performance evaluation](docs/TESTING.md)
- [Phase 3 walkthrough and browser verification](docs/PHASE3.md)
- [Phase 4 integration results and reproduction](docs/PHASE4.md)
- [Phase 5 deployment and recovery evidence](docs/PHASE5.md)
- [Phase 6 results and academic package](docs/PHASE6.md)
- [Raw k6 results and resource measurements](evidence/performance/)
- [Environment inspection and verification results](docs/STATUS.md)
- [Stack versions, licenses and policy gaps](docs/STACK_LICENSES.md)
- [Privacy review draft](docs/PRIVACY.md)
- [Sources and AI assistance disclosure](docs/SOURCES_AND_ACKNOWLEDGMENTS.md)

## Folder structure

```text
EQUIPTRACK/
├── backend/
│   ├── app/                 # FastAPI routes, config, ORM, catalog service, seed
│   ├── migrations/          # Alembic and immutable PostgreSQL schema revision
│   └── tests/               # HTTP contracts and opt-in PostgreSQL integration
├── frontend/
│   └── src/                 # React catalog, API client, responsive Tailwind/CSS
├── infra/
│   ├── nginx/               # HTTPS reverse proxy
│   ├── postgres/            # Separate runtime role initialization
│   └── certs/               # Ignored local certificates and keys
├── scripts/                 # Certificate generation, curl smoke, backup/restore
├── tests/performance/       # Phase 1 k6 read draft; authenticated workloads remain
├── docs/                    # Requirements, diagrams, decisions and evidence
├── backups/                 # Ignored local database dumps
├── test-results/            # Ignored local test/performance artifacts
├── .env.example
└── compose.yaml             # Separate presentation, application, and data tiers
```

## Run with the required infrastructure

For a fresh Ubuntu WSL2 setup with Docker Engine, Compose and mkcert, follow the [installation guide](docs/INSTALLATION.md). Then run these commands from the project root in **WSL Bash**:

```bash
test -f .env || cp .env.example .env
# If you just copied the example, replace both passwords and matching URL passwords.
bash scripts/dev-certs.sh
docker compose up --build -d --wait --wait-timeout 180
docker compose --profile tools run --rm seed
docker compose --profile tools run --rm seed python -m app.seed_accounts
CURL_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem" bash scripts/smoke.sh
```

Open **https://localhost:8443** and sign in as `student@example.invalid`, `faculty@example.invalid` or `custodian@example.invalid` with the password shown by the first provisioning run. Save generated passwords privately. Set `APP_ORIGIN` to the exact browser origin if you change the host or port. Interactive API docs are at **https://localhost:8443/api/docs**.

For the existing deployment on this laptop, see [how to resume and test it](docs/PHASE5.md#resume-on-this-laptop).

## Run the installed local checks (PowerShell)

```powershell
Set-Location C:\Users\bryan\Desktop\EQUIPTRACK\backend
..\.venv\Scripts\python.exe -m pytest -q
Set-Location ..\frontend
npm run build
```

The catalog never falls back to hardcoded browser records. When PostgreSQL is unavailable, it displays a retryable connection error. API tests with database doubles do not count as PostgreSQL or full-system acceptance. No load-test measurements have been fabricated.

For the live walkthrough, follow the [defense rehearsal guide](docs/DEFENSE.md).

## License

EquipTrack's original source code and documentation use the [MIT License](LICENSE). The course brief and third-party components retain their respective terms. The [stack and license inventory](docs/STACK_LICENSES.md) records the dependencies and their sources.
