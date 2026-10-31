#!/bin/sh
# Compile the schema against the database this server reads, then serve it.
#
# FraiseQL finds a query's native columns (an argument named for a column of its
# relation, such as posts(createdAt:) for tv_post.created_at) only when it
# compiles with --database. Compiling at image build time, with no database,
# would serve a schema that sorts and filters those fields in the document, so
# the image ships the compiler and compiles here, as a deployment would. Any
# compile error (drift included) stops the container before it serves.
set -eu

cd /app/compile
fraiseql-cli compile schema.json --output /app/schema.compiled.json --database "$DATABASE_URL"

# Which schema this run measures: its digest, and the native columns compile found.
echo "compiled schema sha256 $(sha256sum /app/schema.compiled.json | cut -d' ' -f1)"
jq -r '.queries[] | select((.native_columns // {}) != {})
       | "native_columns \(.name): \(.native_columns | to_entries
           | map("\(.key)=\(.value.pg_type)") | join(","))"' /app/schema.compiled.json

cd /app
exec fraiseql-server "$@"
