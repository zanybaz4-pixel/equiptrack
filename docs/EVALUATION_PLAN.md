# R7 evaluation plan

Primary reference: [MIS 215 Term Project Brief](MIS215_TermProject_Brief.pdf), R7 pp. 11–12. See the [six completed experiments](PHASE6.md).

## Part A: controlled performance experiments

Test only the student-controlled synthetic EquipTrack deployment. Use the selected FOSS k6 runner, trusted HTTPS, and the final authenticated API. Keep business data and configuration stable across comparable runs. Run on a dedicated disposable performance database, with enough synthetic accounts/assets to avoid measuring fixture shortages as normal throughput.

| Core transaction | Workload | Minimum concurrency matrix | Preconditions |
|---|---|---|---|
| T1 Equipment availability | Authenticated GET /api/equipment with fixed query/limit | 1, 10, 50 VUs | Seeded catalog, valid role/session, repeatable filters |
| T2 Borrowing request | Authenticated/CSRF-protected POST /api/requests; expect 201 | 1, 10, 50 VUs | Provision identities/items/valid periods; tag setup/cancellation separately |

These are **at least six separate measured runs**. The current read script has 30-second duration and one-second think time; keep those choices explicit and consistent when finalizing both scripts. VUs represent concurrent simulated users with think time, not a claim that every database operation starts at the exact same instant. Run warmup separately; repeat runs when needed to assess variability. Document any changed duration, cache state or workload distribution rather than silently comparing unequal tests.

For every run record:

- Timestamp, transaction, script/version, concurrency, duration, think time and completed request/sample count.
- Throughput in requests/second, mean and p95 response time in milliseconds, HTTP/transport error rate and check failure rate. Write metrics must exclude login/setup/cancel traffic using tags or dedicated metrics.
- Host CPU model/core count, physical RAM, host OS, WSL/Linux kernel, Engine/Compose versions, image versions/digests and database size.
- Actual WSL VM CPU/RAM limits and container CPU/memory allocations. If containers have no explicit limit, state that they share available WSL resources; do not invent allocations.
- Network path and load-generator placement. Co-located k6 may compete with the app for CPU/RAM; document that limitation.
- Raw k6 summary, relevant container/tier CPU and memory observations, safe application logs, and database connection/wait/slow-query evidence where available.

Do not report planned thresholds as measured performance. Do not disable TLS verification. Use actual measured degradation, resource saturation or query waits to identify a likely tier bottleneck; label an inference and alternative explanations. Throughput/latency alone do not prove which tier caused the result. Retain failed runs and explain exclusions. Do not point scripts at DepEd, university or other third-party systems.

`scripts/performance.sh` runs both authenticated k6 workloads against a new local database. Each cell uses a five-second warm-up and a 30-second timed scenario. The runner records samples and verifies write counts against database and audit rows. The 1, 10 and 50 user evidence is linked from [Phase 6](PHASE6.md).

## Part B: 3–5-page architectural comparison

Selected comparison alternative: a **two-tier design with a client connecting directly to the database** (permitted comparison option b). This is a conceptual analysis only; the implemented EquipTrack browser must continue to access FastAPI and never receive DB credentials or connect to PostgreSQL.

Use the student's own R7A results and course references. The brief requires an argued comparison; it does not require building or benchmarking the alternative. If the alternative is not measured, state that and avoid fabricated latency, cost or scaling numbers.

| Required dimension | EquipTrack evidence | Questions for the two-tier alternative |
|---|---|---|
| Architecture | Actual browser/gateway/API/DB diagram, ports, responsibilities and transaction trace | Where do rules run and how are clients deployed? What changes when API mediation is removed? |
| Performance | Measured T1/T2 mean/p95/throughput/error at 1/10/50, tier observations | Could removing an application hop help? What evidence limits that inference? How do connection counts and validation affect it? |
| Scalability | Contention, pool usage, resource limits and measured degradation | Can clients/DB connections be scaled and controlled centrally? Would lending contention remain? |
| Security | Server RBAC, ownership, secrets isolation and DB constraints when implemented | How would DB credentials, per-user privileges and tampered clients be handled? |
| Cost | Actual local resource/tool requirements; sourced assumptions only | What administration/deployment/network costs shift? No unsupported currency figures |
| Maintainability | Own modular services, migrations, API spec and repeatable containers | How would rule changes and client versions remain consistent? |

The R7B section of the Phase 6 report uses four pages to compare the designs and recommend the three-tier deployment for the fictional school. It distinguishes the measured prototype from the conceptual two-tier alternative.
