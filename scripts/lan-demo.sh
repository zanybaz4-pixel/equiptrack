#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
unset DOCKER_CONTEXT
export DOCKER_HOST=unix:///var/run/docker.sock

lan_address="${1:?Pass the Windows LAN address}"
duration="${2:-infinity}"
if [[ "$duration" != infinity && ! "$duration" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Use a duration in whole seconds or infinity.\n' >&2
    exit 1
fi

state_dir="$HOME/.local/state/equiptrack"
install -d -m 700 "$state_dir"
exec 9>"$state_dir/lan-demo.lock"
if ! flock -n 9; then
    printf 'A LAN demo session is already open. Try https://%s:8443 on your other device.\n' "$lan_address"
    exit 0
fi

wsl_address=$(ip -4 -o address show dev eth0 scope global | awk '{split($4, address, "/"); print address[1]; exit}')
[[ "$wsl_address" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]
openssl x509 -in infra/certs/equiptrack.pem -checkip "$lan_address" -noout

restore_loopback() {
    docker compose up -d --wait --wait-timeout 90 api edge >/dev/null
}
trap restore_loopback EXIT
trap 'exit 0' INT TERM HUP

origin="https://$lan_address:8443"
BIND_ADDRESS="$wsl_address" APP_ORIGIN="$origin" docker compose up -d --wait --wait-timeout 90 api edge
curl --noproxy '*' --fail --silent --show-error --cacert infra/certs/equiptrack-rootCA.pem --resolve "$lan_address:8443:$wsl_address" "$origin/api/health/ready"
printf '\nWSL address: %s\nOpen %s from another device on the same private network.\nKeep this window open. Press Ctrl+C to end this demo session.\n' "$wsl_address" "$origin"

sleep "$duration" &
timer=$!
trap 'kill "$timer" 2>/dev/null || true; exit 0' INT TERM HUP
wait "$timer"
