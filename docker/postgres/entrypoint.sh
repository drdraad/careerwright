#!/usr/bin/env bash
# PostgreSQL's start, as root, before the image's own entrypoint (ADR 0004, amendment
# 2026-11-01). On a Linux host a Compose file secret keeps its owner-only host permissions,
# which the postgres user cannot read. This copies each secret given to the container into the
# in-memory private directory, read-only for the postgres user alone, then hands over to the
# image's entrypoint, which drops to that user. No value is printed or passed as an argument.
set -euo pipefail

private=/run/careerwright/private
if [ "$(id -u)" != 0 ]; then
    echo "entrypoint.sh must start as root to give postgres its secrets" >&2
    exit 1
fi
if ! grep -q " $private tmpfs " /proc/mounts; then
    echo "$private is not a tmpfs mount; the copies must stay in memory" >&2
    exit 1
fi

chmod 0700 "$private"
rm -rf "$private/secrets"
install -d -m 0700 -o postgres -g postgres "$private/secrets"
for secret in /run/secrets/*; do
    install -m 0400 -o postgres -g postgres "$secret" "$private/secrets/${secret##*/}"
done
chmod 0500 "$private/secrets"
chown postgres:postgres "$private"
chmod 0500 "$private"

exec docker-entrypoint.sh "$@"
