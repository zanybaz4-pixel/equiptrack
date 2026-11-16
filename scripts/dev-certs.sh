#!/usr/bin/env bash
# Generates development certificates only; it does NOT modify a trust store.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v mkcert >/dev/null || { echo 'mkcert is missing. See docs/INSTALLATION.md.' >&2; exit 1; }
if [[ -f infra/certs/equiptrack.pem || -f infra/certs/equiptrack-key.pem ]]; then
  echo 'Certificate files already exist. Review them before replacing them.' >&2
  exit 1
fi
umask 077
mkcert -cert-file infra/certs/equiptrack.pem -key-file infra/certs/equiptrack-key.pem \
  localhost 127.0.0.1 ::1 "$@"
echo 'Certificates created. Each client must trust the development CA separately.'
