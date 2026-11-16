#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
unset DOCKER_CONTEXT
export DOCKER_HOST=unix:///var/run/docker.sock

k6_image=grafana/k6:1.8.2@sha256:00fdcebafbc86cb0137d429529b1caa401a02e09025f02fc74866fa6e2b004d8
run_id="$(date -u +%Y%m%d%H%M%S)_$$"
project="equiptrack_perf_$run_id"
state=$(mktemp -d)
results="$PWD/test-results/performance/$run_id"
ca="$PWD/infra/certs/equiptrack-rootCA.pem"
origin=https://localhost:28443
mkdir -p "$results" "$state/fixture"
[[ -f "$ca" ]] || { echo 'Generate the local development certificate first.' >&2; exit 1; }

# Use an empty environment for Compose interpolation so the demo's shell variables
# and .env cannot override the isolated database or published address.
compose() {
    env -i PATH="$PATH" DOCKER_HOST="$DOCKER_HOST" docker compose --env-file "$state/compose.env" --project-name "$project" "$@"
}

finish() {
    compose stop >/dev/null 2>&1 || true
    rm -f -- "$state/fixture/sessions.json" "$state/compose.env"
    rmdir -- "$state/fixture" "$state" || true
}
trap finish EXIT

python3 - "$project" >"$state/compose.env" <<'PY'
import sys
from secrets import token_urlsafe

database = sys.argv[1]
owner_secret = token_urlsafe(24)
app_secret = token_urlsafe(24)
print(f"""POSTGRES_DB={database}
POSTGRES_USER=equiptrack_owner
POSTGRES_PASSWORD={owner_secret}
POSTGRES_APP_PASSWORD={app_secret}
DATABASE_URL=postgresql+psycopg://equiptrack_app:{app_secret}@db:5432/{database}
MIGRATION_DATABASE_URL=postgresql+psycopg://equiptrack_owner:{owner_secret}@db:5432/{database}
HTTPS_PORT=28443
BIND_ADDRESS=127.0.0.1
APP_ORIGIN=https://localhost:28443
APP_ENV=development""")
PY

sql() {
    compose exec -T db psql -XqAt -v ON_ERROR_STOP=1 -U equiptrack_owner -d "$project" -c "$1"
}

compose up --build -d --wait --wait-timeout 180
CURL_CA_BUNDLE="$ca" bash scripts/smoke.sh "$origin"
fixture_source=$(cat tests/performance/fixture.py)
compose run --rm --no-deps -T --user 0:0 -e "FIXTURE_ORIGIN=$origin" -v "$state/fixture:/fixture" seed python -c "$fixture_source" /fixture/sessions.json
test -s "$state/fixture/sessions.json"
mapfile -t containers < <(compose ps -q db api web edge)

{
    printf 'run_id=%s\nproject=%s\n' "$run_id" "$project"
    date -u
    lscpu
    free -b
    uname -r
    docker info --format 'Docker={{.ServerVersion}} OS={{.OperatingSystem}} CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}'
    docker compose version
    docker inspect --format '{{.Name}} {{.Image}} NanoCpus={{.HostConfig.NanoCpus}} MemoryBytes={{.HostConfig.Memory}}' "${containers[@]}"
    docker image inspect "$k6_image" --format '{{index .RepoDigests 0}}'
    docker run --rm "$k6_image" version
} >"$results/wsl-environment.txt"
sql "SELECT json_build_object('database_bytes',pg_database_size(current_database()),'assets',(SELECT count(*) FROM equipment_items),'borrowers',(SELECT count(*) FROM users),'max_connections',current_setting('max_connections'),'shared_buffers',current_setting('shared_buffers'),'track_io_timing',current_setting('track_io_timing'))" >"$results/database.json"

measure() {
    local mode=$1 vus=$2 duration=$3 output=$4
    docker run --rm --network host --user 0:0 --cap-drop ALL --security-opt no-new-privileges \
        -e SSL_CERT_FILE=/local-ca.pem -e "VUS=$vus" -e "DURATION=$duration" -e "WORKLOAD=$mode" \
        -v "$PWD/tests/performance:/workload:ro" -v "$ca:/local-ca.pem:ro" \
        -v "$state/fixture:/fixture:ro" -v "$output:/results" \
        "$k6_image" run --quiet --no-usage-report "/workload/$mode.js"
}

reset_trial_data() {
    # This database name was generated for this run and is passed explicitly to psql.
    sql 'TRUNCATE loan_records, borrowing_requests'
}

sample() {
    while true; do
        printf 'Sample %s\n' "$(date -u +%FT%TZ)"
        docker stats --no-stream --format '{{json .}}' "${containers[@]}"
        sql "SELECT json_build_object('sample_type','postgresql_connections','active',count(*) FILTER (WHERE state='active'),'lock_waits',count(*) FILTER (WHERE wait_event_type='Lock'),'io_waits',count(*) FILTER (WHERE wait_event_type='IO')) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()"
        sleep 1
    done
}

for mode in read write; do
    for vus in 1 10 50; do
        cell="$results/$mode-$vus"
        mkdir -p "$cell/warmup"
        echo "Running $mode at $vus virtual users"
        reset_trial_data
        measure "$mode" "$vus" 5s "$cell/warmup" >"$cell/warmup/k6.log" 2>&1
        reset_trial_data
        audit_before=$(sql "SELECT count(*) FROM audit_logs WHERE action='request.created'")
        [[ "$audit_before" =~ ^[0-9]+$ ]]
        date -u +%FT%TZ >"$cell/start-utc.txt"
        sample >"$cell/resources.txt" 2>&1 &
        sampler=$!
        status=0
        measure "$mode" "$vus" 30s "$cell" >"$cell/k6.log" 2>&1 || status=$?
        kill "$sampler" 2>/dev/null || true
        wait "$sampler" 2>/dev/null || true
        date -u +%FT%TZ >"$cell/end-utc.txt"
        sql "SELECT json_build_object('requests',(SELECT count(*) FROM borrowing_requests),'audit_creations',(SELECT count(*) FROM audit_logs WHERE action='request.created')-$audit_before,'database_bytes',pg_database_size(current_database()))" >"$cell/database.json"
        echo "k6 exit: $status"
        [[ "$status" -eq 0 ]] || exit "$status"
    done
done

printf 'Results saved to %s\n' "$results"
