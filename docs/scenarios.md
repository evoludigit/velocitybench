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

### F1 / F2 — published filter (10 rows, F2 adds author nesting)

```graphql
# FraiseQL
{ posts(published: true, limit: 10) { id title } }

# Hasura
{ posts(where: {published: {_eq: true}}, limit: 10) { id title } }

# PostGraphile
{ allTbPosts(first: 10, condition: {published: true}) { nodes { id: rowId title } } }
```

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
| Classical (Hasura, PostGraphile, all resolver frameworks) | **2** | M1 mutation + serial Q1 re-fetch |

This definition is embedded in the runner's scenario table
(`_QUERY_LABELS["MC1"]`) and is generated into every report automatically.
