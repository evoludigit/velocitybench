# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-24  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation × 3 passes — pass 1 canonical order, passes 2–3 randomised; RPS = median ± σ across passes  
**Concurrency**: 40 workers  
**Measurement**: 30s per scenario  
**Warmup**: 10s per scenario  
**Cooldown**: 5s between frameworks  

---

## Methodology

| | |
|---|---|
| Host CPU | AMD EPYC-Genoa Processor |
| Kernel | 6.8.0-117-generic |
| PostgreSQL | 17.10 (Debian 17.10-1.pgdg13+1) |
| Load generator | k6-v2.0.0 |
| Target host | 10.7.0.2 |
| `tv_*` persistence | logged (WAL-durable — publishable profile) |
| `tv_*` trigger scope | FraiseQL frameworks only — classical stacks mutate a vanilla tb_user (they never deploy pg_tviews) |
| Dataset | MEDIUM — 10 000 users · 50 000 posts · 200 000 comments |
| Concurrency | 40 workers |
| Measurement / warmup / cooldown | 30s / 10s / 5s |
| Passes | 3 |
| Run timestamp | 2026-07-24T18:30:56+00:00 |

### Framework Versions

| Framework | Version |
|-----------|---------|
| fraiseql-tv | 2.14.0 |
| fraiseql-tv-audit | 2.14.0 |
| fraiseql-tv-cache | 2.14.0 |
| fraiseql-v-cache | 2.14.0 |
| fraiseql-v-nocache | 2.14.0 |
| hasura | v2.49.3-ce |
| postgraphile | 5.0.3 |
| strawberry | 1.0.0 |

## Reading These Numbers

- **Same-run rule**: every number below comes from one sequential sweep on one host. Compare rows within this report only — never across reports or hardware.
- **Q1 honesty note**: Q1 is a flat 20-row SELECT — the scenario where a schema-to-API engine has the least to offer over a hand-tuned endpoint, and FraiseQL's position there is mid-pack. The architectural gap appears in nested reads (Q2b, Q3), mutations (M1), and consistency cycles (MC1).
- **Errors disqualify**: a row with a non-zero error count is reported but not comparable; publishable tables require 0% errors.

---
## Database Footprint

TV tables (pre-computed JSONB) trade storage for read speed by materializing a lean summary embed at write time (post.author = {id, username, full_name, bio}; comment.author = {id, username}; comment.post = {id, title}). Views (v_*) add no storage — computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tb_comment` | 294.4 MB | 81.9 MB | 376.4 MB |
| `tb_mutation_log` | 73.2 MB | 5.7 MB | 79.0 MB |
| `tb_post` | 133.6 MB | 20.4 MB | 154.1 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.7 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `tv_comment` | 768.4 MB | 278.2 MB | 1.02 GB |
| `tv_post` | 210.6 MB | 68.7 MB | 310.9 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.4 MB | 0.0 MB | 0.5 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 638.5 MB  
**Storage amplification**: 3.15× (TV adds 1.34 GB on top of the normalized 638.5 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | C3 | 18275 ±0 | 2.2 | 2.5 | 2.8 | 1 | 0.0% |
| apollo-server | Node.js | C3 | 4203 ±0 | 9.2 | 13.7 | 16.5 | 1 | 0.0% |
| async-graphql | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | C3 | 11611 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11723 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11235 ±0 | 3.5 | 4.5 | 4.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11315 ±0 | 3.5 | 4.5 | 4.9 | 1 | 0.0% |
| hasura | Haskell | C3 | 3473 ±0 | 11.1 | 17.6 | 20.1 | 1 | 0.0% |
| mercurius | Node.js | C3 | 7408 ±0 | 5.1 | 8.0 | 10.7 | 1 | 0.0% |
| postgraphile | Node.js | C3 | 4332 ±0 | 8.9 | 13.3 | 17.6 | 1 | 0.0% |
| strawberry | Python | C3 | 1588 ±0 | 23.6 | 37.2 | 58.7 | 1 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F1 | 13308 ±0 | 3.0 | 3.5 | 3.8 | 1 | 0.0% |
| apollo-server | Node.js | F1 | 3102 ±0 | 12.6 | 18.6 | 21.7 | 1 | 0.0% |
| async-graphql | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | F1 | 10575 ±0 | 3.8 | 4.8 | 5.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10557 ±0 | 3.8 | 4.8 | 5.4 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6773 ±0 | 4.7 | 19.9 | 29.3 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6929 ±0 | 4.7 | 19.1 | 28.7 | 1 | 0.0% |
| hasura | Haskell | F1 | 3502 ±0 | 11.0 | 17.4 | 20.0 | 1 | 0.0% |
| mercurius | Node.js | F1 | 4695 ±0 | 8.2 | 12.3 | 15.1 | 1 | 0.0% |
| postgraphile | Node.js | F1 | 3731 ±0 | 10.3 | 15.6 | 20.4 | 1 | 0.0% |
| strawberry | Python | F1 | 1285 ±0 | 30.1 | 36.5 | 68.5 | 1 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F2 | 4728 ±0 | 8.4 | 9.4 | 9.9 | 1 | 0.0% |
| apollo-server | Node.js | F2 | 2202 ±0 | 17.5 | 26.7 | 31.7 | 1 | 0.0% |
| async-graphql | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | F2 | 8856 ±0 | 4.5 | 5.7 | 6.3 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8881 ±0 | 4.5 | 5.7 | 6.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 5186 ±0 | 5.9 | 28.4 | 34.3 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 5194 ±0 | 5.9 | 28.3 | 34.6 | 1 | 0.0% |
| hasura | Haskell | F2 | 2882 ±0 | 13.3 | 20.5 | 22.7 | 1 | 0.0% |
| mercurius | Node.js | F2 | 3392 ±0 | 11.3 | 16.8 | 20.3 | 1 | 0.0% |
| postgraphile | Node.js | F2 | 2826 ±0 | 13.5 | 20.6 | 25.9 | 1 | 0.0% |
| strawberry | Python | F2 | 941 ±0 | 40.9 | 71.8 | 81.1 | 1 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F3 | 1610 ±0 | 24.4 | 28.5 | 31.1 | 1 | 0.0% |
| apollo-server | Node.js | F3 | 1568 ±0 | 24.6 | 40.6 | 50.1 | 1 | 0.0% |
| async-graphql | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | F3 | 9495 ±0 | 4.2 | 5.3 | 5.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9483 ±0 | 4.2 | 5.3 | 5.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8723 ±0 | 4.6 | 5.9 | 6.5 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8729 ±0 | 4.5 | 5.8 | 6.5 | 1 | 0.0% |
| hasura | Haskell | F3 | 3633 ±0 | 10.6 | 16.7 | 19.7 | 1 | 0.0% |
| mercurius | Node.js | F3 | 1452 ±0 | 17.9 | 64.5 | 76.8 | 1 | 0.0% |
| postgraphile | Node.js | F3 | 3374 ±0 | 11.4 | 17.5 | 22.1 | 1 | 0.0% |
| strawberry | Python | F3 | 979 ±0 | 38.9 | 72.3 | 104.3 | 1 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | HC3 | 18366 ±0 | 2.1 | 2.5 | 2.9 | 1 | 0.0% |
| apollo-server | Node.js | HC3 | 4261 ±0 | 9.0 | 13.6 | 16.5 | 1 | 0.0% |
| async-graphql | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | HC3 | 11640 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11655 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11313 ±0 | 3.5 | 4.5 | 4.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11338 ±0 | 3.5 | 4.4 | 4.9 | 1 | 0.0% |
| hasura | Haskell | HC3 | 3485 ±0 | 11.0 | 17.3 | 20.0 | 1 | 0.0% |
| mercurius | Node.js | HC3 | 7293 ±0 | 5.2 | 8.1 | 10.8 | 1 | 0.0% |
| postgraphile | Node.js | HC3 | 4380 ±0 | 8.8 | 13.1 | 17.2 | 1 | 0.0% |
| strawberry | Python | HC3 | 1615 ±0 | 22.9 | 35.6 | 56.1 | 1 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | M1 | 5210 ±0 | 7.6 | 8.4 | 10.4 | 1 | 0.0% |
| apollo-server | Node.js | M1 | 2769 ±0 | 13.6 | 19.5 | 24.4 | 1 | 0.0% |
| async-graphql | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | M1 | 1117 ±0 | 20.0 | 90.9 | 190.1 | 1 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1068 ±0 | 21.5 | 94.0 | 194.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1114 ±0 | 20.4 | 93.0 | 189.4 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1111 ±0 | 20.5 | 92.1 | 191.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1118 ±0 | 20.2 | 92.2 | 194.0 | 1 | 0.0% |
| hasura | Haskell | M1 | 1964 ±0 | 19.2 | 26.8 | 31.5 | 1 | 0.0% |
| mercurius | Node.js | M1 | 4422 ±0 | 8.7 | 12.3 | 16.6 | 1 | 0.0% |
| postgraphile | Node.js | M1 | 3503 ±0 | 10.6 | 16.5 | 21.7 | 1 | 0.0% |
| strawberry | Python | M1 | 1316 ±0 | 29.1 | 36.6 | 65.2 | 1 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | MC1 | 1353 ±0 | 28.9 | 33.2 | 35.7 | 1 | 0.0% |
| apollo-server | Node.js | MC1 | 1063 ±0 | 37.3 | 47.8 | 54.8 | 1 | 0.0% |
| async-graphql | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | MC1 | 1111 ±0 | 20.8 | 91.8 | 188.5 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1097 ±0 | 20.7 | 91.5 | 198.6 | 1 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1094 ±0 | 20.8 | 92.7 | 197.5 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1106 ±0 | 20.6 | 92.3 | 190.9 | 1 | 0.0% |
| hasura | Haskell | MC1 | 1215 ±0 | 32.1 | 40.2 | 44.2 | 1 | 0.0% |
| mercurius | Node.js | MC1 | 1341 ±0 | 27.1 | 47.1 | 53.9 | 1 | 0.0% |
| postgraphile | Node.js | MC1 | 1539 ±0 | 24.6 | 36.8 | 46.3 | 1 | 0.0% |
| strawberry | Python | MC1 | 566 ±0 | 74.5 | 127.8 | 140.8 | 1 | 0.0% |

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q1 | 1675 ±0 | 23.4 | 27.3 | 29.4 | 1 | 0.0% |
| apollo-server | Node.js | Q1 | 1566 ±0 | 24.6 | 41.0 | 50.9 | 1 | 0.0% |
| async-graphql | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q1 | 9760 ±0 | 4.1 | 5.2 | 5.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9871 ±0 | 4.0 | 5.2 | 5.7 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8943 ±0 | 4.4 | 5.8 | 6.6 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8924 ±0 | 4.4 | 5.8 | 7.0 | 1 | 0.0% |
| hasura | Haskell | Q1 | 3636 ±0 | 10.6 | 17.1 | 19.5 | 1 | 0.0% |
| mercurius | Node.js | Q1 | 1450 ±0 | 17.9 | 65.2 | 77.0 | 1 | 0.0% |
| postgraphile | Node.js | Q1 | 3419 ±0 | 11.3 | 17.2 | 21.6 | 1 | 0.0% |
| strawberry | Python | Q1 | 996 ±0 | 39.0 | 50.2 | 76.8 | 1 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2 | 14046 ±0 | 2.8 | 3.3 | 3.7 | 1 | 0.0% |
| apollo-server | Node.js | Q2 | 3129 ±0 | 12.5 | 18.3 | 21.3 | 1 | 0.0% |
| async-graphql | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q2 | 11110 ±0 | 3.6 | 4.6 | 5.2 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11197 ±0 | 3.5 | 4.5 | 5.1 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7455 ±0 | 4.4 | 16.1 | 25.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7492 ±0 | 4.5 | 14.8 | 25.1 | 1 | 0.0% |
| hasura | Haskell | Q2 | 3886 ±0 | 9.9 | 15.5 | 18.9 | 1 | 0.0% |
| mercurius | Node.js | Q2 | 4875 ±0 | 7.9 | 11.9 | 14.8 | 1 | 0.0% |
| postgraphile | Node.js | Q2 | 3962 ±0 | 9.7 | 14.8 | 19.1 | 1 | 0.0% |
| strawberry | Python | Q2 | 1401 ±0 | 27.5 | 32.4 | 60.2 | 1 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2b | 4872 ±0 | 8.2 | 9.2 | 9.7 | 1 | 0.0% |
| apollo-server | Node.js | Q2b | 2194 ±0 | 17.6 | 26.8 | 31.8 | 1 | 0.0% |
| async-graphql | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q2b | 9233 ±0 | 4.3 | 5.5 | 6.1 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9323 ±0 | 4.3 | 5.4 | 6.0 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5353 ±0 | 5.8 | 27.1 | 33.5 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5364 ±0 | 5.7 | 27.5 | 33.6 | 1 | 0.0% |
| hasura | Haskell | Q2b | 3197 ±0 | 11.9 | 19.0 | 21.1 | 1 | 0.0% |
| mercurius | Node.js | Q2b | 3470 ±0 | 11.0 | 16.4 | 20.0 | 1 | 0.0% |
| postgraphile | Node.js | Q2b | 2967 ±0 | 13.1 | 19.0 | 23.4 | 1 | 0.0% |
| strawberry | Python | Q2b | 1009 ±0 | 38.1 | 64.5 | 71.7 | 1 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q3 | 4301 ±0 | 9.2 | 10.3 | 11.0 | 1 | 0.0% |
| apollo-server | Node.js | Q3 | 782 ±0 | 50.8 | 65.1 | 69.6 | 1 | 0.0% |
| async-graphql | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q3 | 7258 ±0 | 5.5 | 7.0 | 7.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7265 ±0 | 5.5 | 7.0 | 7.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3411 ±0 | 8.5 | 37.7 | 42.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3424 ±0 | 8.5 | 37.6 | 42.9 | 1 | 0.0% |
| hasura | Haskell | Q3 | 2615 ±0 | 14.7 | 22.1 | 23.9 | 1 | 0.0% |
| mercurius | Node.js | Q3 | 1034 ±0 | 38.5 | 49.8 | 52.8 | 1 | 0.0% |
| postgraphile | Node.js | Q3 | 1824 ±0 | 21.1 | 32.4 | 37.9 | 1 | 0.0% |
| strawberry | Python | Q3 | 539 ±0 | 71.1 | 109.1 | 116.1 | 1 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | T1 | 3293 ±0 | 12.1 | 13.4 | 14.2 | 1 | 0.0% |
| apollo-server | Node.js | T1 | 1440 ±0 | 26.5 | 35.4 | 39.7 | 1 | 0.0% |
| async-graphql | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | T1 | 5810 ±0 | 6.8 | 8.9 | 9.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5810 ±0 | 6.8 | 8.9 | 9.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3359 ±0 | 9.4 | 32.9 | 38.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3408 ±0 | 9.2 | 32.6 | 37.5 | 1 | 0.0% |
| hasura | Haskell | T1 | 2166 ±0 | 17.4 | 25.7 | 28.2 | 1 | 0.0% |
| mercurius | Node.js | T1 | 2000 ±0 | 19.0 | 26.0 | 29.8 | 1 | 0.0% |
| postgraphile | Node.js | T1 | 2468 ±0 | 15.5 | 23.7 | 30.1 | 1 | 0.0% |
| strawberry | Python | T1 | 668 ±0 | 57.8 | 90.4 | 101.9 | 1 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | M1_APQ | 2801 ±0 | 13.5 | 19.4 | 24.2 | 1 | 0.0% |
| async-graphql | Rust | M1_APQ | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | M1_APQ | 1105 ±0 | 20.5 | 91.3 | 181.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1107 ±0 | 20.6 | 91.3 | 197.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1103 ±0 | 20.7 | 91.8 | 190.6 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1102 ±0 | 20.7 | 91.9 | 195.1 | 1 | 0.0% |
| mercurius | Node.js | M1_APQ | 4377 ±0 | 8.8 | 12.3 | 16.3 | 1 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q1_APQ | 1576 ±0 | 24.7 | 39.4 | 49.0 | 1 | 0.0% |
| async-graphql | Rust | Q1_APQ | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q1_APQ | 9393 ±0 | 4.2 | 5.3 | 5.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9335 ±0 | 4.3 | 5.4 | 6.0 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8430 ±0 | 4.7 | 6.0 | 6.7 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8459 ±0 | 4.7 | 6.0 | 6.8 | 1 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1458 ±0 | 18.2 | 64.0 | 75.0 | 1 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q2b_APQ | 2190 ±0 | 17.6 | 26.7 | 31.8 | 1 | 0.0% |
| async-graphql | Rust | Q2b_APQ | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q2b_APQ | 9142 ±0 | 4.4 | 5.5 | 6.1 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9073 ±0 | 4.4 | 5.5 | 6.1 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5149 ±0 | 6.0 | 28.3 | 34.3 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5196 ±0 | 5.9 | 28.1 | 34.3 | 1 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3424 ±0 | 11.2 | 16.9 | 20.5 | 1 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| fraiseql-tv | Rust | M1d | 10155 ±0 | 3.9 | 5.2 | 5.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10213 ±0 | 3.9 | 5.2 | 5.8 | 1 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1675 ±0 | 23.4 | 29.4 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1566 ±0 | 24.6 | 50.9 | 0.0% |
| mercurius | Node.js | 1450 ±0 | 17.9 | 77.0 | 0.0% |
| strawberry | Python | 996 ±0 | 39.0 | 76.8 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9871 ±0 | 4.0 | 5.7 | 0.0% |
| fraiseql-tv | Rust | 9760 ±0 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-cache | Rust | 8943 ±0 | 4.4 | 6.6 | 0.0% |
| fraiseql-v-nocache | Rust | 8924 ±0 | 4.4 | 7.0 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 3636 ±0 | 10.6 | 19.5 | 0.0% |
| postgraphile | Node.js | 3419 ±0 | 11.3 | 21.6 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9871 ±0 | 4.0 | 5.7 |
| fraiseql-tv | Rust | graphql-precomputed | 9760 ±0 | 4.1 | 5.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8943 ±0 | 4.4 | 6.6 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8924 ±0 | 4.4 | 7.0 |
| hasura | Haskell | graphql-schema-first | 3636 ±0 | 10.6 | 19.5 |
| postgraphile | Node.js | graphql-schema-first | 3419 ±0 | 11.3 | 21.6 |
| actix-web-rest | Rust | rest | 1675 ±0 | 23.4 | 29.4 |
| apollo-server | Node.js | graphql | 1566 ±0 | 24.6 | 50.9 |
| mercurius | Node.js | graphql | 1450 ±0 | 17.9 | 77.0 |
| strawberry | Python | graphql | 996 ±0 | 39.0 | 76.8 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9871 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-tv | 9760 | 113 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-v-cache | 8943 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| fraiseql-v-nocache | 8924 | 104 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| hasura | 3636 | 42 | 0.0090 | 26 | 0.0145 | 52 | 0.0073 |
| postgraphile | 3419 | 40 | 0.0096 | 25 | 0.0154 | 49 | 0.0077 |
| actix-web-rest | 1675 | 19 | 0.0195 | 12 | 0.0315 | 24 | 0.0158 |
| apollo-server | 1566 | 18 | 0.0209 | 11 | 0.0336 | 23 | 0.0169 |
| mercurius | 1450 | 17 | 0.0226 | 10 | 0.0363 | 21 | 0.0182 |
| strawberry | 996 | 12 | 0.0329 | 7 | 0.0529 | 14 | 0.0266 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 159.4 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 159.4 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 124.1 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 115.0 |
| hasura | Haskell | — | — | — | 133 | 161.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 125 | 118.9 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 6 | 105.0 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 67 | 111.2 |
| mercurius | Node.js | 464 | 8.8 | 104 | 57 | 105.5 |
| strawberry | Python | 1,812 | 12.7 | 136 | 180 | 175.3 |
| fraiseql-tv-audit | Rust | — | — | 43 | 11 | 20.1 |

---

## MC1 — Cascade Advantage

**Requests per cycle** (what a client must issue to reach fully consistent state after a mutation):

| Framework type | Requests/cycle | What is sent |
|----------------|---------------|--------------|
| FraiseQL | **1** | M1 mutation — `cascade` field in response contains all affected entities |
| Classical GraphQL | **2** | M1 mutation (1) + Q1 list re-fetch (2) |

RPS above = **cycles/second** (mutation-to-consistent-state cycles, not raw requests).  
At equal cycles/second, FraiseQL issues 2× fewer HTTP round trips and returns ~0 stale entities.  
Classical frameworks must fire follow-up queries to invalidate stale cache entries.

> **Peak**: fraiseql-tv 1111 cycles/s (1 req) vs postgraphile 1539 cycles/s (2 req) — 0.7× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 5,210 M/s: **~57,308 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.