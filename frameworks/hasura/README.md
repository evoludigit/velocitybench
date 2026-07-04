# Hasura GraphQL Engine

Hasura is a schema-to-API engine: it generates a GraphQL API directly from the
PostgreSQL schema. In VelocityBench it represents the incumbent in the
"compiled/generated GraphQL" category alongside PostGraphile and FraiseQL.

## Version

Pinned in **one place**: the `image:` tag in the root `docker-compose.yml`
(`hasura/graphql-engine:v2.49.3-ce.cli-migrations-v3`).

- `v2.49.x` — latest stable v2 line. Hasura v3 (DDN) is not benchmarkable as a
  plain self-hosted container (it requires the hosted control plane for schema
  builds), so the campaign benchmarks the latest v2 Community Edition. This
  choice is documented in the report methodology.
- `-ce` — pure Community Edition build.
- `.cli-migrations-v3` — applies `metadata/` non-interactively at container
  start, **before** the server accepts traffic. A fresh clone reproduces the
  exact Hasura config with `docker compose up hasura`.

`tests/benchmark/test_hasura_wiring.py` gates all of the above.

## Ports & endpoints

| What | URL |
|------|-----|
| GraphQL | `POST http://localhost:4000/v1/graphql` |
| Health (strict: fails on inconsistent metadata) | `GET http://localhost:4000/healthz?strict=true` |
| Version | `GET http://localhost:4000/v1/version` |

## Benchmark configuration

Hasura benchmarks the classical normalized path: `tb_user` / `tb_post` /
`tb_comment` with JOIN-backed relationships (no `tv_*` JSONB tables — those are
FraiseQL's architecture, not Hasura's).

Metadata (`metadata/databases/default/tables/tables.yaml`) renames root fields
and columns to the cross-framework GraphQL shape so the standard benchmark
documents apply verbatim:

- root fields: `users`, `posts`, `comments`, `updateUser`
- columns: `full_name` → `fullName`, `created_at` → `createdAt`, `updated_at` → `updatedAt`
- relationships: `posts.author`, `posts.comments`, `comments.author`, `comments.post`, `users.posts`

Only filter arguments and the mutation shape stay Hasura-native:

```graphql
# F1 — published filter
{ posts(where: {published: {_eq: true}}, limit: 10) { id title } }

# M1 — mutation (public role has an update permission on tb_user.bio only)
mutation {
  updateUser(where: {id: {_eq: "<uuid>"}}, _set: {bio: "bench"}) {
    returning { id bio }
  }
}
```

Requests are sent **unauthenticated** and resolve to the `public` role
(`HASURA_GRAPHQL_UNAUTHORIZED_ROLE=public`) with row-unrestricted select
permissions — the standard public-API setup. Console, dev mode, and per-request
HTTP logging are disabled so the benchmark measures the engine, not the logger.

## Running

```bash
# Benchmark (canonical path — k6, full scenario row set)
make bench-one FRAMEWORK=hasura

# Just start it
docker compose up -d hasura
```

## Changing the config

Edit the files under `metadata/` and restart the container — the
cli-migrations entrypoint re-applies them idempotently. No console clicking;
console is disabled in the benchmark profile.
