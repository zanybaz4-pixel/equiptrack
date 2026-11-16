# Phase 6 evaluation and academic package

The MIS 215 brief's R7A performance matrix ran on November 16, 2026, Philippine time. Each trial used its own authenticated synthetic traffic through HTTPS on an isolated Ubuntu WSL2 Compose stack. See the [structured results](phase6-performance.json) and [workload design](EVALUATION_PLAN.md).

| Transaction | Virtual users | Requests | Requests/sec | Mean ms | p95 ms | HTTP errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Read availability | 1 | 30 | 0.90 | 7.89 | 8.83 | 0% |
| Read availability | 10 | 300 | 8.99 | 11.90 | 21.35 | 0% |
| Read availability | 50 | 1,500 | 44.25 | 23.10 | 140.62 | 0% |
| Submit request | 1 | 30 | 0.90 | 9.57 | 10.63 | 0% |
| Submit request | 10 | 300 | 8.91 | 20.60 | 41.59 | 0% |
| Submit request | 50 | 1,483 | 43.70 | 28.68 | 134.90 | 0% |

Write tail latency grew at 10 users and both workloads showed their largest p95 increase at 50. FastAPI used more sampled CPU than PostgreSQL or Nginx in both 50-user runs. No lock or I/O waits appeared in the PostgreSQL samples. The application tier is the first candidate for profiling. Short waits and host scheduling can be missed by spot samples. The 50-user write trial committed 1,483 requests and an equal number of creation events.

Windows reported an AMD Ryzen 5 5600X, 6 physical cores, 12 logical processors and 31.93 GiB of physical RAM. WSL exposed 12 logical CPUs and 15.58 GiB of RAM. The containers shared those resources. k6 ran on the same WSL host and used a one-second pause after each request. The results are for this synthetic load, fixture size and network path.

## Reproduce

Run `bash scripts/performance.sh` from the repository in Ubuntu WSL2 after generating the local CA and leaf certificate. The isolated runner uses port 28443 and a new database, creates synthetic borrowers, warms up each cell and measures each load for 30 seconds. Results are saved under `test-results/performance`. The first two setup attempts ended before collecting timing samples. The final run used a private fixture mount and preserved the append-only audit log.

## Academic review

The final report contains the four-page R7B comparison and the two-page privacy note. The package also includes a proposal, a protocol overview with the full OpenAPI file, an evaluation handout and a [defense rehearsal guide](DEFENSE.md). Cover names and filenames use Brinces. Review the course details and references against what the instructor provided.

The optional defense overlay matched a real HTTPS 201 response, the Nginx server log's request identifier, and a matching PostgreSQL request audit row. The test ran on the isolated verification stack. See the [recorded trace](phase6-trace.json).

The submission checklist tracks student decisions and defense evidence. Rehearsal and recording depend on the live second device. The source archive is a local submission copy.
