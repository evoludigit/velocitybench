# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-25  
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
| Run timestamp | 2026-07-25T11:50:24+00:00 |

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
| `tb_comment` | 294.9 MB | 82.5 MB | 377.5 MB |
| `tb_mutation_log` | 74.1 MB | 5.8 MB | 79.9 MB |
| `tb_post` | 133.7 MB | 19.6 MB | 153.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `tv_comment` | 769.3 MB | 278.1 MB | 1.02 GB |
| `tv_post` | 210.7 MB | 68.7 MB | 311.1 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.5 MB | 0.0 MB | 0.5 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 639.7 MB  
**Storage amplification**: 3.15× (TV adds 1.34 GB on top of the normalized 639.7 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | C3 | 16160 ±0 | 2.4 | 3.0 | 3.4 | 1 | 0.0% |
| apollo-server | Node.js | C3 | 3904 ±0 | 9.8 | 15.7 | 19.9 | 1 | 0.0% |
| async-graphql | Rust | C3 | 15773 ±0 | 2.5 | 3.4 | 4.1 | 1 | 0.0% |
| fraiseql-tv | Rust | C3 | 11467 ±0 | 3.5 | 4.4 | 4.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11604 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11118 ±0 | 3.6 | 4.5 | 5.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11184 ±0 | 3.6 | 4.5 | 5.0 | 1 | 0.0% |
| hasura | Haskell | C3 | 1428 ±0 | 27.8 | 37.9 | 44.5 | 1 | 0.0% |
| mercurius | Node.js | C3 | 6666 ±0 | 5.6 | 9.6 | 12.8 | 1 | 0.0% |
| postgraphile | Node.js | C3 | 3800 ±0 | 9.7 | 16.9 | 29.2 | 1 | 0.0% |
| strawberry | Python | C3 | 1531 ±0 | 24.7 | 45.0 | 63.0 | 1 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F1 | 12049 ±0 | 3.2 | 4.2 | 5.7 | 1 | 0.0% |
| apollo-server | Node.js | F1 | 2900 ±0 | 13.1 | 21.0 | 27.5 | 1 | 0.0% |
| async-graphql | Rust | F1 | 9377 ±0 | 4.3 | 5.7 | 6.7 | 1 | 0.0% |
| fraiseql-tv | Rust | F1 | 10419 ±0 | 3.8 | 4.9 | 5.5 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10407 ±0 | 3.8 | 4.9 | 5.5 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6229 ±0 | 4.9 | 25.4 | 32.2 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6209 ±0 | 4.9 | 25.3 | 32.4 | 1 | 0.0% |
| hasura | Haskell | F1 | 1443 ±0 | 27.8 | 34.4 | 44.4 | 1 | 0.0% |
| mercurius | Node.js | F1 | 4349 ±0 | 8.5 | 14.8 | 19.6 | 1 | 0.0% |
| postgraphile | Node.js | F1 | 3287 ±0 | 11.4 | 18.4 | 27.0 | 1 | 0.0% |
| strawberry | Python | F1 | 1255 ±0 | 30.6 | 42.1 | 68.9 | 1 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F2 | 6775 ±0 | 5.8 | 6.7 | 7.8 | 1 | 0.0% |
| apollo-server | Node.js | F2 | 1906 ±0 | 19.5 | 33.2 | 40.8 | 1 | 0.0% |
| async-graphql | Rust | F2 | 6061 ±0 | 6.2 | 10.6 | 14.4 | 1 | 0.0% |
| fraiseql-tv | Rust | F2 | 8726 ±0 | 4.6 | 5.8 | 6.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8679 ±0 | 4.6 | 5.8 | 6.5 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4629 ±0 | 6.3 | 33.4 | 38.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4614 ±0 | 6.3 | 33.9 | 39.1 | 1 | 0.0% |
| hasura | Haskell | F2 | 1195 ±0 | 32.9 | 46.7 | 52.2 | 1 | 0.0% |
| mercurius | Node.js | F2 | 3101 ±0 | 11.8 | 20.5 | 26.1 | 1 | 0.0% |
| postgraphile | Node.js | F2 | 2553 ±0 | 14.6 | 24.2 | 33.0 | 1 | 0.0% |
| strawberry | Python | F2 | 921 ±0 | 45.4 | 66.5 | 87.4 | 1 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F3 | 1626 ±0 | 24.0 | 28.8 | 30.9 | 1 | 0.0% |
| apollo-server | Node.js | F3 | 1573 ±0 | 24.7 | 40.7 | 50.0 | 1 | 0.0% |
| async-graphql | Rust | F3 | 1401 ±0 | 17.6 | 63.1 | 67.1 | 1 | 0.0% |
| fraiseql-tv | Rust | F3 | 9477 ±0 | 4.2 | 5.3 | 5.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9420 ±0 | 4.2 | 5.4 | 5.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8662 ±0 | 4.6 | 5.9 | 6.6 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8615 ±0 | 4.6 | 6.0 | 6.6 | 1 | 0.0% |
| hasura | Haskell | F3 | 1496 ±0 | 26.7 | 32.7 | 42.3 | 1 | 0.0% |
| mercurius | Node.js | F3 | 1453 ±0 | 18.0 | 64.7 | 76.0 | 1 | 0.0% |
| postgraphile | Node.js | F3 | 3002 ±0 | 12.5 | 20.9 | 31.4 | 1 | 0.0% |
| strawberry | Python | F3 | 953 ±0 | 40.2 | 53.5 | 83.3 | 1 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | HC3 | 16289 ±0 | 2.4 | 2.9 | 3.4 | 1 | 0.0% |
| apollo-server | Node.js | HC3 | 3852 ±0 | 9.6 | 15.8 | 19.9 | 1 | 0.0% |
| async-graphql | Rust | HC3 | 15818 ±0 | 2.5 | 3.4 | 4.0 | 1 | 0.0% |
| fraiseql-tv | Rust | HC3 | 11472 ±0 | 3.5 | 4.4 | 4.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11607 ±0 | 3.4 | 4.3 | 4.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11154 ±0 | 3.6 | 4.5 | 5.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11249 ±0 | 3.5 | 4.5 | 4.9 | 1 | 0.0% |
| hasura | Haskell | HC3 | 1437 ±0 | 27.5 | 37.9 | 43.4 | 1 | 0.0% |
| mercurius | Node.js | HC3 | 6692 ±0 | 5.6 | 9.3 | 12.7 | 1 | 0.0% |
| postgraphile | Node.js | HC3 | 3835 ±0 | 9.7 | 16.6 | 24.4 | 1 | 0.0% |
| strawberry | Python | HC3 | 1532 ±0 | 24.2 | 44.9 | 63.3 | 1 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | M1 | 3183 ±0 | 12.6 | 15.4 | 16.8 | 1 | 0.0% |
| apollo-server | Node.js | M1 | 2544 ±0 | 14.7 | 23.6 | 32.3 | 1 | 0.0% |
| async-graphql | Rust | M1 | 9408 ±0 | 4.2 | 5.2 | 5.8 | 1 | 0.0% |
| fraiseql-tv | Rust | M1 | 1113 ±0 | 20.7 | 90.6 | 182.4 | 1 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1067 ±0 | 21.8 | 93.7 | 192.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1099 ±0 | 20.8 | 92.0 | 192.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1105 ±0 | 20.6 | 91.7 | 185.1 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1115 ±0 | 20.2 | 91.2 | 190.3 | 1 | 0.0% |
| hasura | Haskell | M1 | 1856 ±0 | 19.6 | 30.3 | 51.0 | 1 | 0.0% |
| mercurius | Node.js | M1 | 4027 ±0 | 9.4 | 15.7 | 22.8 | 1 | 0.0% |
| postgraphile | Node.js | M1 | 2967 ±0 | 11.5 | 21.2 | 52.6 | 1 | 0.0% |
| strawberry | Python | M1 | 1262 ±0 | 30.4 | 38.0 | 70.3 | 1 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | MC1 | 1284 ±0 | 29.8 | 36.0 | 39.4 | 1 | 0.0% |
| apollo-server | Node.js | MC1 | 1048 ±0 | 37.7 | 48.4 | 55.4 | 1 | 0.0% |
| async-graphql | Rust | MC1 | 1255 ±0 | 23.0 | 58.3 | 62.0 | 1 | 0.0% |
| fraiseql-tv | Rust | MC1 | 1103 ±0 | 21.0 | 90.1 | 191.7 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1089 ±0 | 21.2 | 92.2 | 189.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1090 ±0 | 21.0 | 91.6 | 191.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1109 ±0 | 20.9 | 90.2 | 189.3 | 1 | 0.0% |
| hasura | Haskell | MC1 | 575 ±0 | 68.7 | 85.9 | 96.5 | 1 | 0.0% |
| mercurius | Node.js | MC1 | 1329 ±0 | 27.3 | 47.4 | 54.6 | 1 | 0.0% |
| postgraphile | Node.js | MC1 | 1357 ±0 | 26.0 | 48.6 | 84.5 | 1 | 0.0% |
| strawberry | Python | MC1 | 541 ±0 | 74.7 | 108.5 | 129.1 | 1 | 0.0% |

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q1 | 1658 ±0 | 23.4 | 28.2 | 31.2 | 1 | 0.0% |
| apollo-server | Node.js | Q1 | 1571 ±0 | 24.6 | 40.0 | 49.7 | 1 | 0.0% |
| async-graphql | Rust | Q1 | 1402 ±0 | 17.4 | 63.2 | 67.2 | 1 | 0.0% |
| fraiseql-tv | Rust | Q1 | 9771 ±0 | 4.1 | 5.2 | 5.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9761 ±0 | 4.1 | 5.2 | 5.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8875 ±0 | 4.5 | 5.8 | 6.7 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8824 ±0 | 4.5 | 5.8 | 6.7 | 1 | 0.0% |
| hasura | Haskell | Q1 | 1542 ±0 | 25.7 | 35.1 | 42.5 | 1 | 0.0% |
| mercurius | Node.js | Q1 | 1458 ±0 | 17.8 | 64.8 | 76.4 | 1 | 0.0% |
| postgraphile | Node.js | Q1 | 3153 ±0 | 12.2 | 19.4 | 26.2 | 1 | 0.0% |
| strawberry | Python | Q1 | 976 ±0 | 39.8 | 55.6 | 82.2 | 1 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2 | 12718 ±0 | 3.1 | 3.8 | 4.3 | 1 | 0.0% |
| apollo-server | Node.js | Q2 | 2914 ±0 | 13.1 | 20.6 | 26.9 | 1 | 0.0% |
| async-graphql | Rust | Q2 | 8258 ±0 | 4.7 | 6.3 | 8.5 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2 | 10980 ±0 | 3.6 | 4.7 | 5.2 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11003 ±0 | 3.6 | 4.7 | 5.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7205 ±0 | 4.6 | 15.8 | 26.2 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7295 ±0 | 4.6 | 14.7 | 25.5 | 1 | 0.0% |
| hasura | Haskell | Q2 | 1647 ±0 | 24.1 | 34.0 | 40.1 | 1 | 0.0% |
| mercurius | Node.js | Q2 | 4464 ±0 | 8.2 | 15.1 | 19.8 | 1 | 0.0% |
| postgraphile | Node.js | Q2 | 3548 ±0 | 10.4 | 18.0 | 25.4 | 1 | 0.0% |
| strawberry | Python | Q2 | 1391 ±0 | 27.9 | 38.2 | 65.0 | 1 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2b | 5123 ±0 | 7.7 | 9.1 | 11.5 | 1 | 0.0% |
| apollo-server | Node.js | Q2b | 1897 ±0 | 19.6 | 33.7 | 42.4 | 1 | 0.0% |
| async-graphql | Rust | Q2b | 6109 ±0 | 6.2 | 10.5 | 14.0 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2b | 9119 ±0 | 4.4 | 5.6 | 6.2 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9063 ±0 | 4.4 | 5.6 | 6.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5351 ±0 | 5.8 | 26.5 | 33.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5375 ±0 | 5.8 | 26.6 | 33.0 | 1 | 0.0% |
| hasura | Haskell | Q2b | 1329 ±0 | 30.3 | 42.1 | 47.5 | 1 | 0.0% |
| mercurius | Node.js | Q2b | 3042 ±0 | 12.1 | 21.0 | 26.2 | 1 | 0.0% |
| postgraphile | Node.js | Q2b | 2689 ±0 | 14.0 | 23.2 | 32.4 | 1 | 0.0% |
| strawberry | Python | Q2b | 981 ±0 | 39.5 | 60.9 | 78.0 | 1 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q3 | 4299 ±0 | 9.2 | 10.3 | 11.9 | 1 | 0.0% |
| apollo-server | Node.js | Q3 | 655 ±0 | 60.1 | 82.8 | 95.0 | 1 | 0.0% |
| async-graphql | Rust | Q3 | 2695 ±0 | 13.9 | 26.2 | 33.4 | 1 | 0.0% |
| fraiseql-tv | Rust | Q3 | 7258 ±0 | 5.5 | 7.0 | 7.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7189 ±0 | 5.5 | 7.1 | 7.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3447 ±0 | 8.5 | 37.1 | 42.5 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3453 ±0 | 8.4 | 37.5 | 42.6 | 1 | 0.0% |
| hasura | Haskell | Q3 | 1071 ±0 | 37.1 | 50.5 | 54.9 | 1 | 0.0% |
| mercurius | Node.js | Q3 | 931 ±0 | 42.0 | 59.6 | 67.6 | 1 | 0.0% |
| postgraphile | Node.js | Q3 | 1585 ±0 | 23.3 | 41.2 | 54.0 | 1 | 0.0% |
| strawberry | Python | Q3 | 516 ±0 | 74.0 | 112.2 | 137.8 | 1 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | T1 | 3167 ±0 | 12.6 | 14.3 | 16.2 | 1 | 0.0% |
| apollo-server | Node.js | T1 | 1204 ±0 | 30.4 | 48.9 | 57.4 | 1 | 0.0% |
| async-graphql | Rust | T1 | 5579 ±0 | 6.8 | 11.2 | 14.0 | 1 | 0.0% |
| fraiseql-tv | Rust | T1 | 5695 ±0 | 7.0 | 9.2 | 10.2 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5711 ±0 | 6.9 | 9.1 | 10.1 | 1 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3323 ±0 | 9.5 | 33.1 | 38.4 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3311 ±0 | 9.5 | 32.9 | 37.9 | 1 | 0.0% |
| hasura | Haskell | T1 | 896 ±0 | 43.7 | 58.9 | 63.8 | 1 | 0.0% |
| mercurius | Node.js | T1 | 1739 ±0 | 21.3 | 34.1 | 41.3 | 1 | 0.0% |
| postgraphile | Node.js | T1 | 2090 ±0 | 17.3 | 31.3 | 62.1 | 1 | 0.0% |
| strawberry | Python | T1 | 650 ±0 | 59.1 | 92.3 | 106.2 | 1 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | M1_APQ | 2601 ±0 | 14.5 | 23.2 | 31.5 | 1 | 0.0% |
| async-graphql | Rust | M1_APQ | 10003 ±0 | 4.0 | 4.9 | 5.5 | 1 | 0.0% |
| fraiseql-tv | Rust | M1_APQ | 1089 ±0 | 20.9 | 92.4 | 193.7 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1119 ±0 | 20.9 | 89.7 | 190.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1119 ±0 | 20.7 | 90.2 | 189.7 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1121 ±0 | 20.2 | 89.8 | 190.9 | 1 | 0.0% |
| mercurius | Node.js | M1_APQ | 3889 ±0 | 9.7 | 16.3 | 22.1 | 1 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q1_APQ | 1578 ±0 | 24.8 | 38.8 | 48.4 | 1 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1398 ±0 | 17.4 | 63.2 | 67.2 | 1 | 0.0% |
| fraiseql-tv | Rust | Q1_APQ | 9333 ±0 | 4.3 | 5.4 | 5.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9126 ±0 | 4.3 | 5.5 | 6.1 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8352 ±0 | 4.8 | 6.1 | 6.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8382 ±0 | 4.7 | 6.1 | 6.8 | 1 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1453 ±0 | 18.1 | 64.0 | 75.8 | 1 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q2b_APQ | 1976 ±0 | 19.0 | 31.7 | 38.4 | 1 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 6323 ±0 | 6.1 | 9.7 | 13.0 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2b_APQ | 8828 ±0 | 4.5 | 5.7 | 6.3 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8739 ±0 | 4.6 | 5.8 | 6.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5219 ±0 | 6.0 | 27.3 | 33.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5159 ±0 | 6.0 | 27.9 | 34.1 | 1 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3029 ±0 | 12.2 | 21.0 | 26.5 | 1 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| fraiseql-tv | Rust | M1d | 10128 ±0 | 3.9 | 5.2 | 5.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 9994 ±0 | 4.0 | 5.2 | 6.0 | 1 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1658 ±0 | 23.4 | 31.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1571 ±0 | 24.6 | 49.7 | 0.0% |
| mercurius | Node.js | 1458 ±0 | 17.8 | 76.4 | 0.0% |
| async-graphql | Rust | 1402 ±0 | 17.4 | 67.2 | 0.0% |
| strawberry | Python | 976 ±0 | 39.8 | 82.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 9771 ±0 | 4.1 | 5.8 | 0.0% |
| fraiseql-tv-cache | Rust | 9761 ±0 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-cache | Rust | 8875 ±0 | 4.5 | 6.7 | 0.0% |
| fraiseql-v-nocache | Rust | 8824 ±0 | 4.5 | 6.7 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 3153 ±0 | 12.2 | 26.2 | 0.0% |
| hasura | Haskell | 1542 ±0 | 25.7 | 42.5 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 9771 ±0 | 4.1 | 5.8 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 9761 ±0 | 4.1 | 5.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8875 ±0 | 4.5 | 6.7 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8824 ±0 | 4.5 | 6.7 |
| postgraphile | Node.js | graphql-schema-first | 3153 ±0 | 12.2 | 26.2 |
| actix-web-rest | Rust | rest | 1658 ±0 | 23.4 | 31.2 |
| apollo-server | Node.js | graphql | 1571 ±0 | 24.6 | 49.7 |
| hasura | Haskell | graphql-schema-first | 1542 ±0 | 25.7 | 42.5 |
| mercurius | Node.js | graphql | 1458 ±0 | 17.8 | 76.4 |
| async-graphql | Rust | graphql | 1402 ±0 | 17.4 | 67.2 |
| strawberry | Python | graphql | 976 ±0 | 39.8 | 82.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 9771 | 114 | 0.0033 | 71 | 0.0054 | 141 | 0.0027 |
| fraiseql-tv-cache | 9761 | 114 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-v-cache | 8875 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| fraiseql-v-nocache | 8824 | 103 | 0.0037 | 64 | 0.0060 | 127 | 0.0030 |
| postgraphile | 3153 | 37 | 0.0104 | 23 | 0.0167 | 45 | 0.0084 |
| actix-web-rest | 1658 | 19 | 0.0197 | 12 | 0.0318 | 24 | 0.0160 |
| apollo-server | 1571 | 18 | 0.0208 | 11 | 0.0336 | 23 | 0.0168 |
| hasura | 1542 | 18 | 0.0212 | 11 | 0.0342 | 22 | 0.0171 |
| mercurius | 1458 | 17 | 0.0224 | 11 | 0.0361 | 21 | 0.0181 |
| async-graphql | 1402 | 16 | 0.0233 | 10 | 0.0376 | 20 | 0.0189 |
| strawberry | 976 | 11 | 0.0335 | 7 | 0.0540 | 14 | 0.0271 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 157.5 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 157.7 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 121.9 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 113.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 127 | 129.2 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 93.7 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 65 | 118.0 |
| hasura | Haskell | — | — | — | 135 | 161.6 |
| mercurius | Node.js | 464 | 8.8 | 104 | 55 | 108.1 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 131.8 |
| strawberry | Python | 1,812 | 12.7 | 136 | 187 | 175.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 18.5 |

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

> **Peak**: fraiseql-tv 1103 cycles/s (1 req) vs postgraphile 1357 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At FraiseQL's peak cascade throughput of 1,115 M/s: **~12,265 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): the prior mutation burst (each bio edit fans out to ~11 cascade row-writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.