# PostGraphile

PostGraphile is a schema-to-API engine: it generates a GraphQL API directly
from the PostgreSQL schema. In VelocityBench it represents the Node.js entry
in the "compiled/generated GraphQL" category alongside Hasura and FraiseQL.

## Version

**PostGraphile v5** (Grafast executor), pinned in `package.json` /
`package-lock.json` and gated by `tests/benchmark/test_postgraphile_version.py`.
Runs the stock **amber preset** — no custom plugins or inflection
(`src/graphile.config.ts`).

## Ports & endpoints

| What | URL |
|------|-----|
| GraphQL | `POST http://localhost:4014/graphql` (compose maps 4014 → container 4000) |
| Health (reports `version` for the run JSON) | `GET http://localhost:4014/health` |

## Benchmark documents

v5 amber naming: collections are `allTbUsers` / `allTbPosts` / `allTbComments`,
relations `tbUserByFkAuthor` / `tbCommentsByFkPost`, single-row lookup
`tbPostByRowId`. The uuid `id` column surfaces as `rowId` (the `id` field is
the Relay node ID), so benchmark documents alias `id: rowId` to return the
uuid like every other framework:

```graphql
# Q1
{ allTbUsers(first: 20) { nodes { id: rowId username fullName } } }

# F1 — published filter
{ allTbPosts(first: 10, condition: {published: true}) { nodes { id: rowId title } } }
```

The canonical documents live in `tests/benchmark/bench_sequential.py`
(`_PG_*` constants).

## Running

```bash
# Benchmark (canonical path — k6, full scenario row set)
make bench-one FRAMEWORK=postgraphile

# Local development (postgres via root docker-compose exposes host port 5434)
npm install && npm run build
DB_HOST=localhost DB_PORT=5434 DB_PASSWORD=benchmark123 npm start

# Smoke tests (same env)
DB_HOST=localhost DB_PORT=5434 DB_PASSWORD=benchmark123 npm test
```

## Notes

- Configuration lives entirely in `src/graphile.config.ts` — the server never
  writes smart-tag `COMMENT`s or any other DDL into the shared database.
- Type checking runs in `npm run build` (tsc, node16 resolution); jest runs
  transpile-only because ts-jest mis-resolves grafserv's exports-map subpaths.
