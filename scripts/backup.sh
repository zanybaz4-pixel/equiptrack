#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
staging_dir=$(mktemp -d backups/.equiptrack-XXXXXXX)
trap 'rm -f -- "$staging_dir/archive.dump"; rmdir -- "$staging_dir"' EXIT
backup_path="backups/equiptrack-$(date -u +%Y%m%dT%H%M%SZ)-${staging_dir##*.equiptrack-}.dump"

# Keep application grants and schema, but omit login sessions.
docker compose exec -T db sh -ceu '
  exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --exclude-table-data=public.auth_sessions
' > "$staging_dir/archive.dump"
mv -n -- "$staging_dir/archive.dump" "$backup_path"
if [[ -e "$staging_dir/archive.dump" ]]; then
  echo "Backup path already exists: $backup_path" >&2
  exit 1
fi
echo "Backup saved: $backup_path"
