# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-08  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 30s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---
## Database Footprint

TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.
Views (v_*) add no storage — they are computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `tb_mutation_log` | 3.38 GB | 289.3 MB | 3.67 GB |
| `tv_comment` | 756.0 MB | 285.6 MB | 1.64 GB |
| `tb_comment` | 294.6 MB | 82.2 MB | 376.9 MB |
| `tv_post` | 210.3 MB | 71.3 MB | 330.9 MB |
| `tb_post` | 133.6 MB | 20.0 MB | 153.6 MB |
| `tb_post_like` | 5.0 MB | 9.3 MB | 14.3 MB |
| `tv_user` | 8.2 MB | 5.8 MB | 14.0 MB |
| `tb_user` | 5.6 MB | 3.4 MB | 9.0 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |

**TV tables**: 1.98 GB  
**TB tables (normalized baseline)**: 4.21 GB  
**Storage amplification**: 1.47× (TV adds 1.98 GB on top of the normalized 4.21 GB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 1894 | 20.8 | 23.1 | 24.6 | 56,815 | 0.0% |
| async-graphql | Rust | Q1 | 7635 | 4.5 | 11.3 | 16.8 | 229,046 | 0.0% |
| go-gqlgen | Go | Q1 | 865 | 14.0 | 102.7 | 182.3 | 25,957 | 0.0% |
| graphql-yoga | Node.js | Q1 | 8743 | 4.5 | 6.4 | 8.9 | 262,293 | 0.0% |
| mercurius | Node.js | Q1 | 9500 | 4.0 | 6.8 | 9.0 | 285,015 | 0.0% |
| fraiseql-tv | Rust | Q1 | 8985 | 3.8 | 9.6 | 13.5 | 269,553 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 8618 | 2.9 | 14.3 | 27.1 | 258,552 | 0.0% |
| async-graphql | Rust | Q2 | 7239 | 4.5 | 12.7 | 21.0 | 217,173 | 0.0% |
| go-gqlgen | Go | Q2 | 7531 | 4.4 | 12.0 | 18.4 | 225,927 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9612 | 4.0 | 6.3 | 8.7 | 288,360 | 0.0% |
| mercurius | Node.js | Q2 | 9377 | 3.9 | 7.9 | 10.2 | 281,324 | 0.0% |
| fraiseql-tv | Rust | Q2 | 7190 | 4.4 | 13.6 | 23.0 | 215,697 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 8172 | 4.8 | 6.2 | 8.4 | 245,153 | 0.0% |
| async-graphql | Rust | Q2b | 8605 | 4.4 | 7.4 | 9.3 | 258,164 | 0.0% |
| go-gqlgen | Go | Q2b | 1937 | 14.7 | 54.8 | 68.7 | 58,101 | 0.0% |
| graphql-yoga | Node.js | Q2b | 4991 | 7.6 | 11.6 | 14.1 | 149,722 | 0.0% |
| mercurius | Node.js | Q2b | 5939 | 6.3 | 9.9 | 12.0 | 178,183 | 0.0% |
| fraiseql-tv | Rust | Q2b | 8508 | 4.2 | 9.4 | 12.6 | 255,249 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1150 | 19.4 | 114.4 | 142.6 | 34,489 | 0.0% |
| async-graphql | Rust | M1 | 2000 | 16.7 | 40.0 | 56.3 | 60,012 | 0.0% |
| go-gqlgen | Go | M1 | 1881 | 13.4 | 68.1 | 106.8 | 56,428 | 0.0% |
| graphql-yoga | Node.js | M1 | 2056 | 12.4 | 61.5 | 97.9 | 61,676 | 0.0% |
| mercurius | Node.js | M1 | 2123 | 11.8 | 60.5 | 94.5 | 63,704 | 0.0% |
| fraiseql-tv | Rust | M1 | 1270 | 24.2 | 78.1 | 148.9 | 38,099 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 10223 | 2.4 | 11.9 | 21.9 | 306,692 | 0.0% |
| async-graphql | Rust | F1 | 8228 | 4.2 | 10.3 | 15.5 | 246,836 | 0.0% |
| go-gqlgen | Go | F1 | 6736 | 4.7 | 14.4 | 23.9 | 202,067 | 0.0% |
| graphql-yoga | Node.js | F1 | 9699 | 3.9 | 7.2 | 9.5 | 290,982 | 0.0% |
| mercurius | Node.js | F1 | 9436 | 3.9 | 7.8 | 10.1 | 283,077 | 0.0% |
| fraiseql-tv | Rust | F1 | 9317 | 3.7 | 9.3 | 13.3 | 279,520 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 8901 | 4.3 | 7.5 | 10.6 | 267,037 | 0.0% |
| async-graphql | Rust | F2 | 8570 | 4.4 | 7.3 | 9.2 | 257,110 | 0.0% |
| go-gqlgen | Go | F2 | 1815 | 16.6 | 55.5 | 70.5 | 54,452 | 0.0% |
| graphql-yoga | Node.js | F2 | 5303 | 7.1 | 11.1 | 14.5 | 159,098 | 0.0% |
| mercurius | Node.js | F2 | 5785 | 6.4 | 10.5 | 13.5 | 173,545 | 0.0% |
| fraiseql-tv | Rust | F2 | 8427 | 4.3 | 9.2 | 12.3 | 252,818 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| async-graphql | Rust | T1 | 7775 | 4.9 | 7.5 | 9.3 | 233,241 | 0.0% |
| go-gqlgen | Go | T1 | 5219 | 6.1 | 17.1 | 24.2 | 156,559 | 0.0% |
| graphql-yoga | Node.js | T1 | 4348 | 8.7 | 13.0 | 16.8 | 130,434 | 0.0% |
| mercurius | Node.js | T1 | 4644 | 8.1 | 12.5 | 16.7 | 139,310 | 0.0% |
| fraiseql-tv | Rust | T1 | 3949 | 9.6 | 16.7 | 20.7 | 118,478 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 5090 | 7.6 | 12.4 | 14.7 | 152,690 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv | Rust | Q3 | 4727 | 8.1 | 12.4 | 15.2 | 141,801 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 3573 | 8.7 | 28.6 | 41.6 | 107,195 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 4539 | 6.6 | 23.0 | 35.3 | 136,182 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 8719 | 3.9 | 9.9 | 14.2 | 261,575 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1894 | 20.8 | 24.6 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| mercurius | Node.js | 9500 | 4.0 | 9.0 | 0.0% |
| graphql-yoga | Node.js | 8743 | 4.5 | 8.9 | 0.0% |
| async-graphql | Rust | 7635 | 4.5 | 16.8 | 0.0% |
| go-gqlgen | Go | 865 | 14.0 | 182.3 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 8985 | 3.8 | 13.5 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| mercurius | Node.js | graphql | 9500 | 4.0 | 9.0 |
| fraiseql-tv | Rust | graphql-precomputed | 8985 | 3.8 | 13.5 |
| graphql-yoga | Node.js | graphql | 8743 | 4.5 | 8.9 |
| async-graphql | Rust | graphql | 7635 | 4.5 | 16.8 |
| actix-web-rest | Rust | rest | 1894 | 20.8 | 24.6 |
| go-gqlgen | Go | graphql | 865 | 14.0 | 182.3 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| mercurius | Node.js | 403 | 8.9 | 103 | 51 | 122.6 |
| fraiseql-tv | Rust | — | — | 40 | 25 | 128.3 |
| graphql-yoga | Node.js | 403 | 8.7 | 98 | 51 | 119.0 |
| async-graphql | Rust | 693 | 4.5 | 12 | 13 | 134.4 |
| actix-web-rest | Rust | 667 | 4.0 | 12 | 9 | 68.7 |
| go-gqlgen | Go | 7,177 | 13.1 | 10 | 42 | 153.2 |

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 2,123 M/s: **~129,531 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.