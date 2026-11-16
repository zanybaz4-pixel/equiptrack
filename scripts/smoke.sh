#!/usr/bin/env bash
set -euo pipefail
base_url="${1:-https://localhost:8443}"
# curl uses the trust store or an explicit CURL_CA_BUNDLE.
page=$(curl --fail-with-body --silent --show-error "$base_url/")
if [[ "$page" != *"EquipTrack"* ]]; then
  printf 'The gateway did not return the EquipTrack frontend.\n' >&2
  exit 1
fi
curl --fail-with-body --silent --show-error "$base_url/api/health/live"
curl --fail-with-body --silent --show-error "$base_url/api/health/ready"
status=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "$base_url/api/equipment?limit=2")
if [[ "$status" != 401 ]]; then
  printf '\nExpected the unsigned catalog request to return 401; got %s.\n' "$status" >&2
  exit 1
fi
printf '\nFrontend, readiness and catalog access checks passed.\n'
