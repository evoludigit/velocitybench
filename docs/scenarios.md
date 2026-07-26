# Benchmark Scenarios — Per-Engine GraphQL Documents

This is the methodology appendix for the schema-to-API comparison
(FraiseQL / Hasura / PostGraphile). **Canonical source:** the constants in
`tests/benchmark/bench_sequential.py`; equivalence is machine-enforced by
`tests/benchmark/scenario_parity.py`, which runs as a mandatory pre-sweep
gate — a sweep aborts if any (engine, scenario) pair stops returning the same
entity count and field set as the FraiseQL reference.

**Parity means equivalent work** — same rows, same joins, same fields — not
byte-identical JSON. Engine-native naming differences (root fields, filter
syntax, connection wrappers) are normalized before comparison:

| Engine | Naming notes |
|--------|--------------|
| FraiseQL | Cross-framework shape natively (`users`, `posts`, `comments`; camelCase) |
| Hasura v2 CE | Metadata renames root fields + columns to the cross-framework shape; filters stay `where:` boolean expressions |
| PostGraphile v5 (amber) | Relay-style: `allTbUsers { nodes { … } }`, relations `tbUserByFkAuthor`; uuid column aliased `id: rowId` (the bare `id` field is the Relay node ID) |

## Read scenarios

### Q1 — flat user list (20 rows: id, username, fullName)

```graphql
# FraiseQL / Hasura (identical document)
{ users(limit: 20) { id username fullName } }

# PostGraphile
{ allTbUsers(first: 20) { nodes { id: rowId username fullName } } }
```

### Q2 — flat post list (10 rows: id, title)

```graphql
# FraiseQL / Hasura
{ posts(limit: 10) { id title } }

# PostGraphile
{ allTbPosts(first: 10) { nodes { id: rowId title } } }
```

### Q2b — posts + author (1-level nesting)

```graphql
# FraiseQL / Hasura
{ posts(limit: 10) { id title author { username fullName } } }

# PostGraphile
{ allTbPosts(first: 10) { nodes { id: rowId title tbUserByFkAuthor { username fullName } } } }
```

### Q3 — comments + author + post (2-level nesting, 20 rows)

```graphql
# FraiseQL / Hasura
{ comments(limit: 20) { id content author { username } post { title } } }

# PostGraphile
{ allTbComments(first: 20) { nodes { id: rowId content
    tbUserByFkAuthor { username } tbPostByFkPost { title } } } }
```

### C3 / HC3 — single-entity lookup (1 row; C3 rotates 20 UUIDs, HC3 a 5-UUID hot pool)

C3 measures cache-miss single-row traffic (every request a different UUID from
the discovered pool); HC3 the same lookup with only 5 fixed UUIDs, so a cache
saturates after 5 misses. UUIDs are discovered at runtime, so these are
rendered-per-UUID documents (or rotating REST URLs), not static documents —
they are therefore outside the static-document parity audit; equivalence is
by construction (same unique-index lookup, same field set).

```graphql
# FraiseQL — variables-driven
query GetUser($id: ID!) { user(id: $id) { id username fullName } }

# Classical resolver frameworks (one rendered document per UUID, rotated)
{ user(id: "<uuid>") { id username fullName } }

# Hasura — no *_by_pk root is addressable by the benchmark uuid (the pk is
# the serial pk_user), so the lookup goes through `where` on the unique
# uuid column — same unique-index work
{ users(where: {id: {_eq: "<uuid>"}}) { id username fullName } }

# PostGraphile
{ user: tbUserByRowId(rowId: "<uuid>") { id: rowId username fullName } }
```

REST: `GET /users/<uuid>`, URL rotated across the same pool.

### F1 / F2 — published filter (10 rows, F2 adds author nesting)

```graphql
# FraiseQL
{ posts(published: true, limit: 10) { id title } }

# Hasura
{ posts(where: {published: {_eq: true}}, limit: 10) { id title } }

# PostGraphile
{ allTbPosts(first: 10, condition: {published: true}) { nodes { id: rowId title } } }
```

### F3 — ORDER BY baseline (20 rows)

Currently the orderBy-free baseline — the same 20-row/3-field list as Q1
(`users(limit: 20) { id username fullName }`; PostGraphile:
`allTbUsers(first: 20) { nodes { id: rowId username fullName } }`; REST:
`GET /users?limit=20`). The cell exists so the grid is complete and the
future `orderBy` variant is a one-constant change per engine; until then F3
numbers duplicate Q1 by design.

### T1 — full blog page load (fixed post id: post + author + 10 comments with authors)

```graphql
# FraiseQL — multi-root, two concurrent SQL queries (v2 pipeline)
query GetPostAndComments($id: ID!) {
  post(id: $id) { id title content author { username fullName bio } }
  comments(postId: $id, limit: 10) { id content author { username } }
}

# Hasura — single-post lookup via where (pk is the serial pk_post; the
# benchmark id is a uuid column, so *_by_pk is not addressable by it)
{ posts(where: {id: {_eq: "<post-uuid>"}}) { id title content
    author { username fullName bio }
    comments(limit: 10) { id content author { username } } } }

# PostGraphile
{ tbPostByRowId(rowId: "<post-uuid>") { id: rowId title content
    tbUserByFkAuthor { username fullName bio }
    tbCommentsByFkPost(first: 10) { nodes { id: rowId content
      tbUserByFkAuthor { username } } } } }
```

T1 is a fixed-id lookup, so the parity gate also checks exact values
(id/title/content) and that all engines return the same comment count for
that post.

## Mutation scenarios (excluded from the shape audit — workflow-defined)

### M1 — single-field update (rotating real writes)

Every M1 request is a **real write**: the load rotates 20 user UUIDs × 10 bio
values, cycle-paired so consecutive visits to the same user always send a
different value. Two failure modes this design prevents (both found live on
2026-07-04):

- a **constant value** hits no-op short circuits (e.g. FraiseQL's
  `fn_update_user` skips unchanged bios) and silently measures reads;
- a **single UUID** serializes all workers on one row's lock and measures the
  database, not the framework.

A per-framework **write-effect probe** runs before measurement (two writes,
then a direct DB check); a framework whose mutation doesn't actually write
aborts the sweep.

```graphql
# FraiseQL — variables-driven (executor reads args from the variables map)
mutation UpdateUser($id: ID!, $bio: String) { updateUser(id: $id, bio: $bio) { … } }

# Hasura (one of 200 rotating rendered documents)
mutation { updateUser(where: {id: {_eq: "<uuid>"}}, _set: {bio: "bio-3"})
  { returning { id bio } } }

# PostGraphile v5 (rotating likewise)
mutation { updateTbUserByRowId(input: {rowId: "<uuid>", tbUserPatch: {bio: "bio-3"}})
  { tbUser { id: rowId bio } } }
```

**pg_tviews trigger scoping.** The `tb_user` tview triggers fire only while a
FraiseQL framework is under test: FraiseQL deploys pg_tviews, so its mutation
numbers include that maintenance cost. Classical stacks never deploy pg_tviews
— during their runs the triggers are disabled (their M1 hits a vanilla table),
then re-enabled with drifted `tv_user` rows resynced before the next FraiseQL
framework. The run JSON records `tview_trigger_scope: fraiseql-only`.

### MC1 — mutation-to-consistent-state cycle (deliberately asymmetric)

MC1 is a **workflow benchmark, not raw server speed**: it measures the client
round trips needed to reach consistent state after a write.

| Engine family | Requests per cycle | Definition |
|---------------|-------------------:|------------|
| FraiseQL | **1** | mutation response carries the cascade (all affected entities) |
| Classical GraphQL (Hasura, PostGraphile, all resolver frameworks) | **2** | M1 mutation + serial Q1 re-fetch |
| REST (actix-web-rest) | **2** | `PUT /users/{id}` + serial `GET /users?limit=20` re-fetch |

This definition is embedded in the runner's scenario table
(`_QUERY_LABELS["MC1"]`) and is generated into every report automatically.
The mutation half rotates url/body pairs exactly like M1 (real writes).

## Scenario coverage & exclusions — publishable subset (2026-07)

Machine truth is the `FRAMEWORKS` dict in `tests/benchmark/bench_sequential.py`;
this matrix documents it so no gap is ever implicit. ✅ = wired; a dash means
**excluded by design** with the reason listed below. The APQ trio is
Q1_APQ + Q2b_APQ + M1_APQ.

| Framework | Q1 Q2 Q2b Q3 | C3 HC3 | F1 F2 F3 | M1 | T1 | MC1 | APQ trio |
|-----------|:---:|:---:|:---:|:--:|:--:|:---:|:---:|
| fraiseql-tv | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-tv-cache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-v-nocache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-v-cache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fraiseql-tv-audit | — (2) | — (2) | — (2) | ✅ | — (2) | — (2) | — (2) |
| hasura | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — (4) |
| postgraphile | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — (5) |
| actix-web-rest | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — (6) |
| async-graphql | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| mercurius | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| apollo-server | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| strawberry | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — (7) |

**Exclusion reasons (all by design):**

2. **fraiseql-tv-audit** — audit-overhead appendix row: measures M1 only, to
   isolate the cost of audit logging on the mutation path. Deliberately not a
   full-grid framework; do not expand.
4. **APQ on Hasura** — Hasura CE v2 has no automatic-persisted-query
   handshake (its allow-lists and query caching are different mechanisms /
   Enterprise features). Hand-rolling APQ would benchmark custom code.
5. **APQ on PostGraphile** — v5 first-party persisted operations are a
   build-time allowlist, not the register-on-first-use sha256 handshake the
   APQ scenarios measure.
6. **APQ on actix-web-rest** — APQ is a GraphQL wire-protocol optimization
   (persisting a query document by hash); REST requests carry no document,
   so the scenario is not applicable.
7. **APQ on Strawberry** — Strawberry GraphQL ships no first-party APQ
   extension (verified against the installed `strawberry/extensions`
   inventory); third-party or hand-rolled implementations would not
   benchmark the framework.

APQ on async-graphql uses the built-in `ApolloPersistedQueries` extension
(first-party, `apollo_persisted_queries` cargo feature); on mercurius the
core `persistedQueryDefaults.automatic()` provider; on apollo-server the
protocol is native and on by default. All other cells in the table are
measured on every sweep.
