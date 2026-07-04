#!/bin/bash
# Select the persistence of pg_tviews-managed tv_* tables at cluster init.
#
# TVIEW_PERSISTENCE=logged   (default) — WAL-logged tables: crash-safe,
#                            replication-capable; the publishable benchmark profile.
# TVIEW_PERSISTENCE=unlogged — pg_tviews' compiled default: 2–3× write
#                            throughput, but truncated on crash recovery.
#
# Runs after 01-extensions.sql (extension registers the GUC) and before
# 02-fraiseql-cqrs.sql (pg_tviews_create() reads it). ALTER DATABASE makes the
# setting apply to every later init script's session and all runtime sessions,
# so tviews created later (e.g. by conversion helpers) inherit the same mode.
set -euo pipefail

mode="${TVIEW_PERSISTENCE:-logged}"
case "$mode" in
    logged)   unlogged=false ;;
    unlogged) unlogged=true ;;
    *)
        echo "TVIEW_PERSISTENCE must be 'logged' or 'unlogged', got: $mode" >&2
        exit 1
        ;;
esac

echo "pg_tviews: creating tv_* tables as ${mode} (pg_tviews.unlogged_by_default=${unlogged})"
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "ALTER DATABASE \"$POSTGRES_DB\" SET pg_tviews.unlogged_by_default = ${unlogged};"
