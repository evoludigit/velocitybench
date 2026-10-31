#!/bin/bash
# Select the persistence of pg_tviews-managed tv_* tables at cluster init.
#
# TVIEW_PERSISTENCE=logged   (default) — WAL-logged tables: crash-safe,
#                            replication-capable; the publishable benchmark profile,
#                            and pg_tviews' default.
# TVIEW_PERSISTENCE=unlogged — 2–3× write throughput, but truncated on crash
#                            recovery.
#
# pg_tviews takes persistence as a TVIEW option ({"logged": false}), not a
# setting. This records the options in velocitybench.tview_options for the
# database, which 02-fraiseql-cqrs.sql passes to each tviews.pg_tviews_create().
# ALTER DATABASE makes it apply to every later init script's session.
set -euo pipefail

mode="${TVIEW_PERSISTENCE:-logged}"
case "$mode" in
    logged)   options='{}' ;;
    unlogged) options='{"logged": false}' ;;
    *)
        echo "TVIEW_PERSISTENCE must be 'logged' or 'unlogged', got: $mode" >&2
        exit 1
        ;;
esac

echo "pg_tviews: creating tv_* tables as ${mode} (options ${options})"
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "ALTER DATABASE \"$POSTGRES_DB\" SET velocitybench.tview_options = '${options}';"
