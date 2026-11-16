#!/usr/bin/env bash
# Restore only into a new, separately named database. Never overwrite the source.
set -euo pipefail
cd "$(dirname "$0")/.."
backup_path="${1:?Usage: bash scripts/restore.sh backups/file.dump equiptrack_restore_NAME}"
restore_database="${2:?Provide a NEW database named equiptrack_restore_NAME}"
[[ -f "$backup_path" ]] || { echo 'Backup file not found.' >&2; exit 1; }
[[ "$restore_database" =~ ^equiptrack_restore_[a-zA-Z0-9_]+$ ]] || { echo 'Target must start with equiptrack_restore_ and contain only letters, digits, underscores.' >&2; exit 1; }
[[ ${#restore_database} -le 63 ]] || { echo 'Target database name cannot exceed 63 bytes.' >&2; exit 1; }

restore_command=$(cat <<'SH'
target=$1
umask 077
staging_dir=$(mktemp -d)
trap 'rm -f "$staging_dir/archive.dump" "$staging_dir/archive.list" "$staging_dir/restore.list"; rmdir "$staging_dir"' EXIT
cat > "$staging_dir/archive.dump"
pg_restore --list "$staging_dir/archive.dump" > "$staging_dir/archive.list"
# Older archives may contain session rows. Keep that table empty after recovery.
awk '!($4 == "TABLE" && $5 == "DATA" && $6 == "public" && $7 == "auth_sessions")' "$staging_dir/archive.list" > "$staging_dir/restore.list"
createdb -U "$POSTGRES_USER" --template=template0 "$target"
pg_restore -U "$POSTGRES_USER" --dbname="$target" --no-owner --exit-on-error --single-transaction --use-list="$staging_dir/restore.list" "$staging_dir/archive.dump"
SH
)
docker compose exec -T db sh -ceu "$restore_command" sh "$restore_database" < "$backup_path"
echo "Restored into $restore_database. Verify application access and sign in again before any cutover."
