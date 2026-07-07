# VelocityBench

GraphQL & REST framework performance benchmarks — 8 languages, reproducible methodology, real PostgreSQL data.

> **Latest run**: March 2026 · sequential isolation · 40 workers · 30s per framework · dataset: 10 000 users / 50 000 posts / 200 000 comments

---

## Results

Full tables: [reports/bench-sequential-2026-03-04.md](reports/bench-sequential-2026-03-04.md)

The **Author** column is the language the developer writes in; the **Runtime** column is
what actually executes requests. For most frameworks these are the same. FraiseQL is the
exception: schemas are authored in Python, compiled ahead of time, and served by a
standalone Rust binary — **no Python runs per request**. See
[FraiseQL variants](#fraiseql-variants) for what `-v` means.

### Q1 — `users(limit: 20) { id username fullName }`

| Framework | Author | Runtime | Type | RPS | p50 | p99 | Errors |
|-----------|--------|---------|------|----:|----:|----:|--------|
| actix-web-rest | Rust | Rust | REST | 12 588 | 2.0 ms | 17.2 ms | 0% |
| spring-boot | Java | JVM | REST | 9 150 | 3.3 ms | 17.4 ms | 0% |
| mercurius | Node.js | Node.js | GraphQL | 9 008 | 4.0 ms | 10.7 ms | 0% |
| async-graphql | Rust | Rust | GraphQL | 7 905 | 4.7 ms | 12.1 ms | 0% |
| graphql-go | Go | Go | GraphQL | 7 576 | 4.3 ms | 19.3 ms | 0% |
| express-rest | Node.js | Node.js | REST | 7 513 | 3.8 ms | 7.7 ms | 0% |
| **fraiseql-v** | **Python** | **Rust** | GraphQL | 6 513 | 5.6 ms | 13.8 ms | 0% |
| go-gqlgen | Go | Go | GraphQL | 6 442 | 4.3 ms | 30.1 ms | 0% |
| play-graphql | Scala | JVM | GraphQL | 6 182 | 5.0 ms | 26.9 ms | 0% |
| ruby-rails | Ruby | Ruby | REST | 5 642 | 5.5 ms | 26.8 ms | 0% |
| gin-rest | Go | Go | REST | 5 586 | 4.5 ms | 37.2 ms | 0% |

### Q2b — `posts(limit: 10) { id title author { username fullName } }` (nested join)

| Framework | Author | Runtime | Type | RPS | p50 | p99 | Errors |
|-----------|--------|---------|------|----:|----:|----:|--------|
| actix-web-rest | Rust | Rust | REST | 11 019 | 2.4 ms | 19.1 ms | 0% |
| mercurius | Node.js | Node.js | GraphQL | 8 252 | 4.5 ms | 11.6 ms | 0% |
| express-rest | Node.js | Node.js | REST | 7 573 | 4.3 ms | 11.5 ms | 0% |
| play-graphql | Scala | JVM | GraphQL | 7 421 | 4.6 ms | 16.6 ms | 0% |
| graphql-go | Go | Go | GraphQL | 7 323 | 4.5 ms | 18.1 ms | 0% |
| gin-rest | Go | Go | REST | 6 818 | 4.3 ms | 23.8 ms | 0% |
| graphql-yoga | Node.js | Node.js | GraphQL | 6 437 | 5.6 ms | 10.8 ms | 0% |
| csharp-dotnet | C# | .NET | REST | 6 386 | 5.2 ms | 15.6 ms | 0% |
| go-gqlgen | Go | Go | GraphQL | 6 271 | 5.0 ms | 24.6 ms | 0% |
| spring-boot | Java | JVM | REST | 5 265 | 6.0 ms | 27.9 ms | 0% |
| async-graphql | Rust | Rust | GraphQL | 4 229 | 8.2 ms | 25.3 ms | 0% |

> Read FraiseQL's position honestly: `fraiseql-v` is **competitive mid-pack throughput from
> a compiled-from-schema engine with zero hand-written resolvers** — not the fastest raw
> server here. The architectural story (Python ergonomics, Rust runtime, no N+1 by
> construction) is the point, not a top-of-table RPS number.

---

## FraiseQL variants

FraiseQL appears under more than one row because the same Rust binary serves two read-side
strategies. Both author in Python and run in Rust; they differ only in how the read model
is stored:

| Variant | Read model | Trades |
|---------|-----------|--------|
| **`fraiseql-v`** | `v_*` views — JSONB composed on the fly per request | No storage multiplier, no write amplification; pays the composition cost at read time |
| **`fraiseql-tv`** | `tv_*` tables — JSONB pre-materialized via incremental refresh ([pg_tviews](../fraiseql/)) | Faster reads; spends storage + write-time refresh to buy them |

This is a **tradeoff, not a strict upgrade** — `tv-` is not universally faster (materialization
overhead and TOAST effects can erase the win on write-heavy or wide-row workloads). The
headline tables above show the conservative `-v` baseline on purpose. Per-variant numbers
(including `-tv`, `-tv-audit`, and `-nocache` configurations) are in the dated runs under
[`reports/`](reports/).
