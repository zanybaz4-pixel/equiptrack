# Testing and performance

## Backend and frontend

From the repository root in Bash, use Python 3.14 and a Node version supported by `frontend/package.json`:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
(cd backend && python -m pytest -q)
(cd frontend && npm ci && npm run build)
node --test tests/gmail-relay.test.cjs
docker compose --env-file .env.example config --quiet
```

For PostgreSQL integration checks, set `TEST_DATABASE_URL` to an owner connection URL for an empty, disposable PostgreSQL database named `equiptrack_test_*`. The role must be able to create the schema and `btree_gist` extension. Run pytest again from `backend/`. Tests that require PostgreSQL are skipped when the URL is absent.

After startup and seeding, run `CURL_CA_BUNDLE="$(mkcert -CAROOT)/rootCA.pem" bash scripts/smoke.sh`. The [defense walkthrough](DEFENSE.md) covers the browser workflow. The [Phase 5 results](PHASE5.md) describe the recorded protocol and recovery runs.

## k6 workloads

Run from the repository root in the Linux/WSL Docker Engine environment. Set up the local certificate first using `bash scripts/dev-certs.sh`. If the certificates predate the current script, copy the public CA using `cp "$(mkcert -CAROOT)/rootCA.pem" infra/certs/equiptrack-rootCA.pem`.

```bash
bash scripts/performance.sh
```

The runner uses a separate Compose project and an HTTPS gateway on port 28443. It provisions synthetic fixtures and runs the authenticated catalog read and request creation workloads with 1, 10 and 50 virtual users. It writes summaries and resource samples under `test-results/performance/`. [Evaluation plan](EVALUATION_PLAN.md) · [Recorded results](PHASE6.md)
