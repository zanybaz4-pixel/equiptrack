# PROJECT: EQUIPTRACK
## School Equipment Borrowing, Return, and Tracking System

You are my senior full-stack software engineer, software architect, and development assistant.

We are going to develop a complete, functional, secure, and professionally designed web-based system called **EquipTrack**.

The system will manage school equipment borrowing, approval, release, return, and availability tracking.

This is an academic project for MIS 215: Client-Server Computing.

Follow the attached MIS215 Term Project Brief if it is available in the workspace. The requirements below summarize the essential technical constraints.

Your goal is to help me build, understand, test, deploy, and document the system step by step.

## 1. PROJECT OVERVIEW

System Name: EquipTrack

Project Title: School Equipment Borrowing, Return, and Tracking System

Purpose:

Develop a centralized web application that helps a school manage equipment lending, track borrowing transactions, prevent double-booking, monitor overdue items, and maintain accurate equipment records.

Assume a realistic fictional school in the Bicol Region until a real school is approved.

The organizational workflow must be supported by documented practices or other verifiable sources. Do not invent organizational policies and present them as established facts.

Use synthetic data only.

## 2. TECHNOLOGY STACK

Frontend:
- React
- Vite
- Tailwind CSS
- Responsive HTML and JavaScript

Backend:
- Python
- FastAPI
- SQLAlchemy
- REST API with JSON

Database:
- PostgreSQL

Infrastructure:
- Nginx
- Docker Engine inside WSL2
- Docker Compose
- HTTPS using locally trusted development certificates

Testing:
- pytest
- curl
- k6

Use only software components and development tools permitted by the MIS 215 FOSS policy.

Verify the applicable open-source licenses and versions.

Do not use Supabase, Firebase, PostgREST, Hasura, or tools that automatically generate the application tier from the database.

Business rules must be implemented in our own application code.

## 3. USER ROLES

Implement two main roles.

BORROWER (STUDENT/FACULTY)

A borrower can:
- Log in securely.
- View available equipment.
- Search or filter equipment.
- Submit borrowing requests.
- Cancel their own pending requests.
- View their borrowing history.
- Monitor request status.
- View expected return dates.
- See whether borrowed equipment is overdue.

EQUIPMENT CUSTODIAN / ADMIN

An administrator can:
- Log in securely.
- View the administrative dashboard.
- Manage equipment inventory.
- Manage user accounts.
- Review borrowing requests.
- Approve or reject requests.
- Record equipment releases.
- Record equipment returns.
- Record equipment condition.
- View active borrowing records.
- Monitor overdue equipment.
- Search and filter transaction history.

Implement server-side role-based access control.

## 4. FIVE CORE TRANSACTIONS

Implement exactly these five core business transactions.

TRANSACTION 1: EQUIPMENT AVAILABILITY

Users search and retrieve available equipment from the database.

Display equipment name, asset code, category, condition, and availability status.

TRANSACTION 2: BORROWING REQUEST

Borrowers submit a request specifying equipment, intended borrowing date, expected return date, and purpose.

Allow pending requests to be canceled by their owners.

Validate availability and borrowing dates.

TRANSACTION 3: REQUEST APPROVAL

Administrators review pending requests and approve or reject them.

Prevent conflicting reservations.

Record the administrator's decision and optional remarks.

TRANSACTION 4: EQUIPMENT RELEASE

Administrators release equipment for approved requests.

Record the actual release time and equipment condition.

Prevent simultaneous active loans for the same equipment.

TRANSACTION 5: EQUIPMENT RETURN

Administrators record returned equipment.

Record return date, actual equipment condition, and remarks.

Restore availability when appropriate.

If the equipment is damaged, mark it for maintenance rather than immediately making it available.

Automatically calculate overdue status based on the expected return date and actual return status.

Treat dashboards, authentication, and account administration as supporting functions, not additional core transactions.

## 5. DATABASE DESIGN

Use a relational PostgreSQL database.

Start with these proposed tables:

- users
- equipment_categories
- equipment_items
- borrowing_requests
- loan_records
- audit_logs

Design proper primary keys, foreign keys, relationships, indexes, and constraints.

Every individual equipment item must have a unique asset code.

Ensure no equipment item can have two active loans simultaneously.

Enforce important business rules using database transactions and appropriate locking or constraints.

Create the ERD and data dictionary.

Provide schema migrations, synthetic seed data, database backup scripts, and restore scripts.

## 6. REST API REQUIREMENTS

Use REST API over HTTPS.

Implement at least eight documented endpoints covering all five core transactions.

Use at least these HTTP methods:

GET, POST, PATCH or PUT, and DELETE.

Suggested routes include:

GET /api/equipment

GET /api/equipment/{id}

GET /api/requests

POST /api/requests

GET /api/requests/{id}

DELETE /api/requests/{id}

PATCH /api/requests/{id}/decision

POST /api/requests/{id}/release

PUT /api/requests/{id}/return

DELETE on a pending request must perform an authorized cancellation or documented soft deletion, preserving transaction history.

Include separate authentication and account-management routes.

Use appropriate HTTP status codes and one consistent JSON error structure.

Document endpoint paths, request bodies, responses, authentication, and possible errors in OpenAPI.

Implement automated success and failure tests for every required endpoint.

## 7. USER INTERFACE DESIGN

Create a beautiful, modern school-management interface.

Design direction:

Professional, modern, minimalist, and responsive.

Use:
- Clean typography
- Navy blue and white as primary colors
- Smooth transitions
- Rounded cards
- Clear icons
- Interactive tables
- Status badges
- Responsive sidebar navigation
- Mobile-friendly layouts
- Loading indicators
- Helpful validation messages

BORROWER INTERFACE

Pages:
- Login
- Dashboard
- Equipment Catalog
- Equipment Details
- Borrowing Request Form
- My Requests
- Borrowing History
- Profile

ADMINISTRATOR INTERFACE

Pages:
- Admin Dashboard
- Equipment Inventory
- Borrowing Requests
- Equipment Release
- Equipment Returns
- Active Borrowings
- Overdue Equipment
- User Management
- Transaction History

All information should come from the backend API.

Do not create a frontend that only displays hardcoded data.

## 8. SECURITY

Implement:
- Password hashing using Argon2 or bcrypt
- Secure authentication
- Server-side authorization
- Role-based access control
- HTTPS
- Input validation
- Parameterized database queries or ORM
- Environment-based secrets
- A .env.example file
- Safe error handling
- Privacy notice
- Audit logging for equipment transactions

Never expose database credentials to the frontend.

Use fictional student, faculty, and administrator records for demonstrations.

## 9. DEPLOYMENT

Keep the three tiers separate.

The application must run in containers or virtual machines.

Create a Docker Compose configuration that starts the necessary services.

Use Docker Engine inside WSL2 for Windows development.

Configure HTTPS through Nginx.

Ensure the application can be accessed from another device on the same local network, not only from localhost.

Document the complete installation and startup process.

Do not install system-level tools or make destructive environment changes without asking permission.

## 10. TESTING AND EVALUATION

Create automated tests for the main business logic and API.

Include tests for:
- Successful borrowing requests
- Unavailable equipment
- Invalid borrowing dates
- Unauthorized actions
- Approval and rejection
- Duplicate or conflicting loans
- Equipment release
- Equipment return
- Damaged equipment
- Overdue transactions

Use k6 to test one read transaction and one write transaction at concurrency levels of 1, 10, and 50 users.

Prepare scripts to capture throughput, average response time, 95th percentile response time, and error rates.

Do not fabricate performance measurements.

## 11. ACADEMIC DOCUMENTATION

Help prepare:
- Requirements specification
- Three-tier architecture diagram
- ERD
- Data dictionary
- REST API specification
- Installation instructions
- Testing documentation
- Deployment documentation
- Performance test scripts
- Stack and License Table
- Privacy compliance documentation
- Acknowledgment of Tools and Sources

Explain the code and major architectural decisions so I can review them and defend my work.

Clearly identify AI-assisted contributions for academic disclosure.

## 12. DEVELOPMENT INSTRUCTIONS

Develop incrementally.

PHASE 1: Project Planning and Architecture

Analyze requirements, define the five core transactions, create the architecture and database design, and establish the project structure.

PHASE 2: Backend Development

Create the database models, authentication, role permissions, application services, business rules, and API endpoints.

PHASE 3: Frontend Development

Create the borrower and administrator interfaces and connect them to the actual backend.

PHASE 4: Integration and Testing

Test every core transaction end to end, fix defects, and ensure database consistency.

PHASE 5: Deployment

Configure containers, HTTPS, backup/restore procedures, and second-device network access.

PHASE 6: Evaluation and Documentation

Prepare performance tests, diagrams, documentation, and demonstration instructions.

IMPORTANT RULES:

Do not generate a mockup-only project.

Create real working frontend and backend components.

Do not silently replace required functionality with placeholder code.

Inspect the existing workspace before creating or modifying files.

Keep code modular, organized, readable, and documented.

Run available tests after implementing each phase.

Report any missing dependencies, unresolved errors, and incomplete requirements.

Do not falsely claim successful tests or completed features.

Do not perform destructive changes without approval.

Keep the application aligned with the MIS 215 project requirements.

START NOW.

First, inspect my development environment and current workspace.

Then create a detailed implementation plan, recommended folder structure, three-tier architecture, database schema, and initial project scaffold.

Explain what you created, show me how to run it, and identify the next implementation phase.