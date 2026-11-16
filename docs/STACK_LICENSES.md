# Stack and license review

Review date: **2026-11-13**. Exact direct package versions below were verified against PyPI/npm publisher metadata, installed locally and checked by imports/builds. `frontend/package-lock.json` records resolved npm versions/integrities and license metadata. `backend/requirements-dev.lock.txt` snapshots the installed Windows Python test environment; primary runtime requirements are in `requirements.txt`. `dependency-inventory.json` records transitive metadata, including optional npm packages for other platforms.

**Primary policy: [MIS 215 Term Project Brief](MIS215_TermProject_Brief.pdf), §6.1–6.2, pp. 12–14.** Every system component and build, deploy and test tool must be OSI-licensed. The laptop OS and code editor are exempt, and Git hosting services are allowed. Accepted examples include React, FastAPI, PostgreSQL, Nginx, Engine, Compose, OpenAPI, curl and k6. EquipTrack uses a root [MIT License](../LICENSE), listed as an example in §9.2.

| Component | Name and Version | License | Reason for Choosing It |
|---|---|---|---|
| React / React DOM | React / React DOM: 19.3.1 | MIT — [source](https://github.com/facebook/react/blob/main/LICENSE) | Reusable browser components and state for both school roles; user-selected client framework. |
| Vite | Vite: 8.3.8 | MIT — [source](https://github.com/vitejs/vite/blob/main/LICENSE) | Local development server and production bundling for the user-selected React client. |
| React Vite plugin | React Vite plugin: 6.3.0 | MIT — [publisher metadata](https://www.npmjs.com/package/@vitejs/plugin-react) | JSX compilation and React development integration. |
| Tailwind CSS / Vite integration | Tailwind CSS / Vite integration: 4.3.5 | MIT — [source](https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE) | Responsive styling while retaining project-specific layout and components. |
| Lucide React | Lucide React: 1.72.0 | ISC package metadata — [publisher](https://www.npmjs.com/package/lucide-react); review icon notices too | Consistent local vector UI icons without external image hosting. |
| Python | Python: Host 3.14.6; image family 3.13-slim | PSF-2.0 — [license](https://docs.python.org/3/license.html) | User-selected application language; clear service and transaction logic. |
| FastAPI | FastAPI: 0.162.5 | MIT — [source](https://github.com/fastapi/fastapi) | Explicit Python route handlers, input schemas and OpenAPI plumbing; business rules remain project code. |
| Uvicorn | Uvicorn: 0.54.0 | BSD-3-Clause — [publisher metadata](https://pypi.org/project/uvicorn/0.54.0/) | ASGI process serving the independently deployed application tier. |
| SQLAlchemy | SQLAlchemy: 2.1.8 | MIT — [publisher metadata](https://pypi.org/project/SQLAlchemy/2.1.8/) | Parameterized ORM queries and controlled sessions/transactions. |
| psycopg / psycopg-binary | psycopg / psycopg-binary: 3.3.9 | LGPL-3.0-only — [publisher metadata](https://pypi.org/project/psycopg/3.3.9/) | PostgreSQL driver for SQLAlchemy and real database constraints. |
| Alembic | Alembic: 1.20.1 | MIT — [publisher metadata](https://pypi.org/project/alembic/1.20.1/) | Reviewed versioned schema migrations without automatic application generation. |
| pydantic-settings | pydantic-settings: 2.16.3 | MIT — [publisher metadata](https://pypi.org/project/pydantic-settings/2.16.3/) | Typed environment-based configuration and secret loading. |
| PostgreSQL | PostgreSQL: 17.12-alpine image selection | PostgreSQL License — [official](https://www.postgresql.org/about/licence/) | User-selected relational authority; exclusion constraints, foreign keys and transactional locking. |
| Nginx | Nginx: 1.28-alpine image family | BSD-2-Clause — [source license](https://nginx.org/LICENSE) | TLS termination, static delivery and same-origin reverse proxy. |
| Node.js / npm | Node.js / npm: Host 24.21.0 / 11.19.0; build image family 24-alpine | MIT and bundled notices — [Node source](https://github.com/nodejs/node/blob/main/LICENSE), [npm](https://github.com/npm/cli/blob/latest/LICENSE) | Build tooling for React/Vite; no Node application-tier replacement. |
| pytest | pytest: 9.2.0 | MIT — [publisher](https://pypi.org/project/pytest/9.2.0/) | Automated Python logic/API/integrity checks, additional to required curl evidence. |
| HTTPX | HTTPX: 0.28.1 | BSD-3-Clause — [publisher](https://pypi.org/project/httpx/0.28.1/) | HTTP contract test transport; review current TestClient deprecation during Phase 2. |
| Prettier | Prettier: 3.6.2 | MIT — [publisher](https://www.npmjs.com/package/prettier/v/3.6.2) | Source readability; temporary formatting use, not a runtime component. |
| Docker Engine / CLI | 29.9.3 inside Ubuntu 24.04 LTS on WSL2 | Apache-2.0 — [official](https://docs.docker.com/engine/install/) | Built and ran the separate deployment tiers. |
| Compose plugin | 5.7.1 inside Ubuntu | Apache-2.0 — [source](https://github.com/docker/compose/blob/main/LICENSE) | Starts and configures the tiers, networks and PostgreSQL volume. |
| mkcert | 1.4.4 inside Ubuntu | BSD-3-Clause — [source](https://github.com/FiloSottile/mkcert/blob/master/LICENSE) | Issued development TLS certificates for localhost and the laptop's LAN IP. |
| k6 OSS | 1.8.2, pinned image digest in scripts/performance.sh | AGPL-3.0 — [source](https://github.com/grafana/k6/blob/master/LICENSE.md) | Ran the six read and write performance experiments. |
| Git | Git: 2.56.1.windows.1 | GPL-2.0 — [source](https://github.com/git/git/blob/master/COPYING) | Required repository version control; final repo/link/ZIP still pending. |
| curl | curl: Windows curl.exe available; version recorded in STATUS when checked | curl license — [official](https://curl.se/docs/copyright.html) | Brief-accepted protocol tool for recorded success/failure evidence per endpoint. |
| Argon2id implementation | argon2-cffi 25.1.0 | MIT ([release metadata](https://pypi.org/project/argon2-cffi/25.1.0/)) | Brief-accepted password hashing. Binding and dependency metadata are listed in dependency-inventory.json. |

The brief explicitly rejects Docker Desktop (p. 13). The Phase 5 deployment configuration and runtime checks used Engine and Compose inside Ubuntu WSL2, as permitted by R5. Codex use is disclosed under §12.2.

Container base tags do not provide digest-level reproducibility; Python/Node/Alpine/Debian/Nginx image contents and all transitive/native licenses need an image inventory after the first approved build. Pin reviewed patch tags/digests and scan current advisories before final evaluation. No vulnerability-free claim is made. The checked-in Python snapshot is evidence of this host run; generate Linux locks after testing the selected Python container. Do not assume a Windows dependency resolution proves Linux compatibility.

Regenerate package metadata with `.venv/Scripts/python.exe scripts/dependency-inventory.py` in PowerShell. Review any missing/ambiguous license entry manually and preserve notices in the academic distribution. Check the resulting inventory against the supplied brief and OSI license list; resolve genuine ambiguities with the FIC before submission without claiming approval that was not provided.

## Ready-made framework features used (§6.2)

| Feature | Reliance and responsibility |
|---|---|
| FastAPI routing, parsing and OpenAPI | Framework plumbing. We define endpoints/response models and must check every R2 field/status/error; generated docs do not generate lending rules |
| Pydantic / settings | Typed parsing, constraints and environment configuration. The API returns 400 for malformed JSON and 422 for invalid fields. |
| SQLAlchemy / psycopg | ORM, parameter binding, connections and sessions. Our catalog query is implemented; lending state/ownership/locking services remain to be written |
| Alembic | Migration runner. The six-table DDL, exclusion/partial constraints and audit trigger are explicit project schema code |
| React / Vite / Tailwind / Lucide | Rendering, build/style tooling and icons. Catalog/API/error/navigation logic and school UI are project components |
| Argon2 and sessions | Argon2-cffi provides the password hash algorithm. EquipTrack implements session persistence, CSRF, role authorization and the transaction handlers. |

There is no built-in admin or generic CRUD scaffold implementing our core transactions, and no database-to-application generator. `STATUS.md` records which tools actually ran; `dependency-inventory.json` captures the prior host dependency versions. Target Linux/image versions, bundled libpq/OpenSSL notices, optional packages and any additional tools need final OSI/notice review. These requirements are not fully satisfied by a top-level license table alone.
