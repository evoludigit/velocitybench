#!/bin/bash
# Check that pg_tviews keeps tv_user / tv_post / tv_comment equal to the command
# tables through inserts, updates and deletes, on a database image.
#
# Usage: database/check-tview-writes.sh [IMAGE]   (default: velocitybench-postgres)
#        INIT_DIR=<checkout>/database ...   init scripts from another checkout
#                                           (the ones that match IMAGE's pg_tviews)
#
# Starts a throwaway container from IMAGE with the stack's own init scripts for
# the extensions and the CQRS schema, then runs each write as its own statement:
# pg_tviews 0.1.0-beta.11 kept the first change statement per entity and lost
# the INSERTs after it (pg_tviews #48), so a single statement proves nothing.
# Exits 1 when a tv_* table differs from its command table.
set -euo pipefail

image="${1:-velocitybench-postgres}"
here="${INIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
name="vb-tview-writes-$$"

cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$name" \
    -e POSTGRES_USER=benchmark -e POSTGRES_PASSWORD=check \
    -e POSTGRES_DB=velocitybench_benchmark -e TVIEW_PERSISTENCE=logged \
    -v "$here/01-extensions.sql:/docker-entrypoint-initdb.d/01-extensions.sql:ro" \
    -v "$here/01z-tview-persistence.sh:/docker-entrypoint-initdb.d/01z-tview-persistence.sh:ro" \
    -v "$here/fraiseql_cqrs_schema.sql:/docker-entrypoint-initdb.d/02-fraiseql-cqrs.sql:ro" \
    "$image" postgres -c shared_preload_libraries=pg_tviews >/dev/null

psql() { docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U benchmark -d velocitybench_benchmark -Atq "$@"; }

for _ in $(seq 1 60); do
    if docker exec "$name" pg_isready -h 127.0.0.1 -U benchmark >/dev/null 2>&1 \
        && psql -c "SELECT 1 FROM benchmark.tv_comment LIMIT 0" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

psql <<'SQL'
SET search_path TO benchmark, public;
INSERT INTO tb_user (identifier, email, username, full_name, bio)
    VALUES ('check-u1', 'check-u1@example.invalid', 'check-u1', 'Check One', 'b1');
INSERT INTO tb_user (identifier, email, username, full_name, bio)
    VALUES ('check-u2', 'check-u2@example.invalid', 'check-u2', 'Check Two', 'b2');
INSERT INTO tb_post (identifier, title, content, fk_author, published)
    SELECT 'check-p1', 't1', 'c1', pk_user, true FROM tb_user WHERE identifier = 'check-u1';
INSERT INTO tb_post (identifier, title, content, fk_author, published)
    SELECT 'check-p2', 't2', 'c2', pk_user, true FROM tb_user WHERE identifier = 'check-u2';
INSERT INTO tb_comment (fk_post, fk_author, content)
    SELECT pk_post, fk_author, 'k1' FROM tb_post WHERE identifier = 'check-p1';
INSERT INTO tb_comment (fk_post, fk_author, content)
    SELECT pk_post, fk_author, 'k2' FROM tb_post WHERE identifier = 'check-p2';
UPDATE tb_user SET bio = 'b1-changed' WHERE identifier = 'check-u1';
DELETE FROM tb_comment WHERE content = 'k2';
SQL

status=0
for t in user post comment; do
    tb=$(psql -c "SELECT count(*) FROM benchmark.tb_$t")
    tv=$(psql -c "SELECT count(*) FROM benchmark.tv_$t")
    if [ "$tb" = "$tv" ]; then
        echo "ok   tb_$t $tb, tv_$t $tv"
    else
        echo "FAIL tb_$t $tb, tv_$t $tv"
        status=1
    fi
done

bio=$(psql -c "SELECT data->'author'->>'bio' FROM benchmark.tv_comment WHERE data->>'content' = 'k1'")
if [ "$bio" = "b1-changed" ]; then
    echo "ok   the author's bio update reached tv_comment"
else
    echo "FAIL tv_comment's author bio is '$bio', expected 'b1-changed'"
    status=1
fi
exit "$status"
