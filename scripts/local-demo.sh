#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
unset DOCKER_CONTEXT
export DOCKER_HOST=unix:///var/run/docker.sock

state_dir="$HOME/.local/state/equiptrack"
install -d -m 700 "$state_dir"
exec 9>"$state_dir/local-demo.lock"
if ! flock -n 9; then
    printf 'EquipTrack is already running. Open https://localhost:8443\n'
    exit 0
fi

docker compose up -d --wait --wait-timeout 180
curl --noproxy '*' --fail --silent --show-error \
    --cacert infra/certs/equiptrack-rootCA.pem \
    https://localhost:8443/api/health/ready
printf '\nEquipTrack is ready at https://localhost:8443\nKeep this window open while using the system. Press Ctrl+C to end this session.\n'

# Keep a Windows-launched WSL session alive without a fixed preview timeout.
sleep infinity &
keeper=$!
trap 'kill "$keeper" 2>/dev/null || true; exit 0' INT TERM HUP
wait "$keeper"
