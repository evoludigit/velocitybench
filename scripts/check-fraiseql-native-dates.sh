#!/bin/bash
# Check that each running FraiseQL service sorts posts and comments by createdAt on
# a column, not on the document.
#
# Usage: scripts/check-fraiseql-native-dates.sh [SERVICE...]
#        (default: fraiseql-tv-nocache fraiseql-v-nocache; COMPOSE_PROJECT_NAME as for the stack)
#
# The compiler records createdAt in a query's native_columns only when compile
# --database finds the created_at column on the query's relation (entrypoint.sh).
# Without it, orderBy createdAt casts each document's value, which no index serves.
# Exits 1 when a service's compiled schema lacks the mapping.
set -euo pipefail

services=("$@")
[ ${#services[@]} -gt 0 ] || services=(fraiseql-tv-nocache fraiseql-v-nocache)

status=0
for service in "${services[@]}"; do
    schema="$(docker compose --profile '*' exec -T "$service" cat /app/schema.compiled.json)"
    for query in posts comments; do
        pg_type="$(jq -r --arg q "$query" \
            '.queries[] | select(.name == $q) | .native_columns.createdAt.pg_type // "none"' <<<"$schema")"
        case "$pg_type" in
            timestamptz|"timestamp with time zone")
                echo "ok   $service $query: createdAt is the column ($pg_type)" ;;
            *)
                echo "FAIL $service $query: createdAt is read out of the document (native column: $pg_type)"
                status=1 ;;
        esac
    done
done
exit "$status"
