# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-07  
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
| Kernel | 6.8.0-124-generic |
| PostgreSQL | 17.10 (Debian 17.10-1.pgdg13+1) |
| Load generator | k6-v2.0.0 |
| Target host | 10.7.0.2 |
| `tv_*` persistence | logged (WAL-durable — publishable profile) |
| `tv_*` trigger scope | FraiseQL frameworks only — classical stacks mutate a vanilla tb_user (they never deploy pg_tviews) |
| Dataset | MEDIUM — 10 000 users · 50 000 posts · 200 000 comments |
| Concurrency | 40 workers |
| Measurement / warmup / cooldown | 30s / 10s / 5s |
| Passes | 3 |
| Run timestamp | 2026-07-07T10:06:53+00:00 |

### Framework Versions

| Framework | Version |
|-----------|---------|
| fraiseql-tv | 2.11.0 |
| fraiseql-tv-audit | 2.11.0 |
| fraiseql-tv-cache | 2.11.0 |
| fraiseql-v-cache | 2.11.0 |
| fraiseql-v-nocache | 2.11.0 |
| hasura | v2.49.3-ce |
| postgraphile | 5.0.3 |
| strawberry | 1.0.0 |

## Reading These Numbers

- **Same-run rule**: every number below comes from one sequential sweep on one host. Compare rows within this report only — never across reports or hardware.
- **Q1 honesty note**: Q1 is a flat 20-row SELECT — the scenario where a schema-to-API engine has the least to offer over a hand-tuned endpoint, and FraiseQL's position there is mid-pack. The architectural gap appears in nested reads (Q2b, Q3), mutations (M1), and consistency cycles (MC1).
- **Errors disqualify**: a row with a non-zero error count is reported but not comparable; publishable tables require 0% errors.

---
## Database Footprint

TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.
Views (v_*) add no storage — they are computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tb_comment` | 294.7 MB | 81.5 MB | 376.4 MB |
| `tb_mutation_log` | 6.6 MB | 0.6 MB | 7.2 MB |
| `tb_post` | 133.8 MB | 19.8 MB | 153.7 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.6 MB | 6.8 MB |
| `tv_comment` | 693.0 MB | 322.3 MB | 1.62 GB |
| `tv_post` | 200.8 MB | 72.2 MB | 322.2 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 566.1 MB  
**Storage amplification**: 4.53× (TV adds 1.95 GB on top of the normalized 566.1 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | C3 | 11122 ±0 | 3.5 | 4.2 | 5.0 | 1 | 0.0% |
| apollo-server | Node.js | C3 | 2493 ±0 | 15.3 | 23.8 | 30.4 | 1 | 0.0% |
| async-graphql | Rust | C3 | 10723 ±0 | 3.6 | 5.3 | 5.9 | 1 | 0.0% |
| fraiseql-tv | Rust | C3 | 7566 ±0 | 5.2 | 7.2 | 7.9 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 7628 ±0 | 5.1 | 7.1 | 7.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7480 ±0 | 5.2 | 7.2 | 7.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7489 ±0 | 5.2 | 7.2 | 8.0 | 1 | 0.0% |
| hasura | Haskell | C3 | 975 ±0 | 41.1 | 51.9 | 57.0 | 1 | 0.0% |
| mercurius | Node.js | C3 | 3936 ±0 | 9.5 | 16.0 | 21.3 | 1 | 0.0% |
| postgraphile | Node.js | C3 | 2477 ±0 | 15.2 | 23.9 | 37.8 | 1 | 0.0% |
| strawberry | Python | C3 | 1337 ±0 | 29.1 | 37.9 | 60.4 | 1 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F1 | 8841 ±0 | 4.4 | 5.3 | 6.2 | 1 | 0.0% |
| apollo-server | Node.js | F1 | 2028 ±0 | 18.9 | 29.0 | 36.8 | 1 | 0.0% |
| async-graphql | Rust | F1 | 6010 ±0 | 6.3 | 9.6 | 11.2 | 1 | 0.0% |
| fraiseql-tv | Rust | F1 | 7045 ±0 | 5.6 | 7.8 | 8.7 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 6999 ±0 | 5.6 | 7.8 | 8.6 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4670 ±0 | 6.6 | 30.6 | 37.2 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4716 ±0 | 6.5 | 30.4 | 37.1 | 1 | 0.0% |
| hasura | Haskell | F1 | 982 ±0 | 40.2 | 51.7 | 56.7 | 1 | 0.0% |
| mercurius | Node.js | F1 | 2730 ±0 | 13.6 | 23.6 | 31.3 | 1 | 0.0% |
| postgraphile | Node.js | F1 | 2082 ±0 | 18.0 | 29.2 | 45.6 | 1 | 0.0% |
| strawberry | Python | F1 | 1110 ±0 | 33.8 | 46.5 | 68.3 | 1 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F2 | 3642 ±0 | 10.6 | 13.6 | 16.3 | 1 | 0.0% |
| apollo-server | Node.js | F2 | 1452 ±0 | 25.8 | 43.2 | 54.0 | 1 | 0.0% |
| async-graphql | Rust | F2 | 3966 ±0 | 9.5 | 16.6 | 20.2 | 1 | 0.0% |
| fraiseql-tv | Rust | F2 | 6031 ±0 | 6.5 | 9.0 | 10.0 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 6042 ±0 | 6.5 | 9.0 | 10.1 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 3592 ±0 | 8.2 | 37.8 | 43.2 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 3551 ±0 | 8.2 | 38.5 | 44.4 | 1 | 0.0% |
| hasura | Haskell | F2 | 891 ±0 | 46.1 | 57.4 | 63.9 | 1 | 0.0% |
| mercurius | Node.js | F2 | 2062 ±0 | 17.8 | 32.1 | 40.6 | 1 | 0.0% |
| postgraphile | Node.js | F2 | 1762 ±0 | 21.2 | 34.7 | 49.5 | 1 | 0.0% |
| strawberry | Python | F2 | 837 ±0 | 45.8 | 70.2 | 81.4 | 1 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | F3 | 1304 ±0 | 30.2 | 36.0 | 39.1 | 1 | 0.0% |
| apollo-server | Node.js | F3 | 1306 ±0 | 30.3 | 43.3 | 49.3 | 1 | 0.0% |
| async-graphql | Rust | F3 | 1160 ±0 | 22.4 | 68.0 | 73.0 | 1 | 0.0% |
| fraiseql-tv | Rust | F3 | 6485 ±0 | 6.0 | 8.4 | 9.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 6518 ±0 | 6.0 | 8.4 | 9.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6348 ±0 | 6.2 | 8.6 | 9.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6182 ±0 | 6.3 | 8.8 | 9.9 | 1 | 0.0% |
| hasura | Haskell | F3 | 1061 ±0 | 37.4 | 47.0 | 53.3 | 1 | 0.0% |
| mercurius | Node.js | F3 | 1236 ±0 | 22.2 | 71.7 | 80.8 | 1 | 0.0% |
| postgraphile | Node.js | F3 | 1977 ±0 | 19.0 | 31.4 | 50.2 | 1 | 0.0% |
| strawberry | Python | F3 | 836 ±0 | 46.0 | 63.1 | 80.6 | 1 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | HC3 | 11059 ±0 | 3.6 | 4.1 | 4.7 | 1 | 0.0% |
| apollo-server | Node.js | HC3 | 2345 ±0 | 16.4 | 25.0 | 31.0 | 1 | 0.0% |
| async-graphql | Rust | HC3 | 10667 ±0 | 3.6 | 5.3 | 6.1 | 1 | 0.0% |
| fraiseql-tv | Rust | HC3 | 7666 ±0 | 5.1 | 7.1 | 7.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 7629 ±0 | 5.1 | 7.1 | 7.9 | 1 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7412 ±0 | 5.3 | 7.3 | 8.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 7526 ±0 | 5.2 | 7.2 | 7.9 | 1 | 0.0% |
| hasura | Haskell | HC3 | 981 ±0 | 41.0 | 51.1 | 56.0 | 1 | 0.0% |
| mercurius | Node.js | HC3 | 4040 ±0 | 9.3 | 15.8 | 20.6 | 1 | 0.0% |
| postgraphile | Node.js | HC3 | 2516 ±0 | 15.1 | 23.3 | 37.8 | 1 | 0.0% |
| strawberry | Python | HC3 | 1327 ±0 | 30.1 | 41.5 | 63.3 | 1 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | M1 | 1658 ±0 | 24.8 | 27.5 | 29.0 | 1 | 0.0% |
| apollo-server | Node.js | M1 | 1676 ±0 | 22.0 | 35.6 | 51.1 | 1 | 0.0% |
| async-graphql | Rust | M1 | 6480 ±0 | 6.2 | 7.8 | 8.6 | 1 | 0.0% |
| fraiseql-tv | Rust | M1 | 89 ±0 | 223.0 | 1563.6 | 3348.7 | 1 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 91 ±0 | 191.8 | 1601.2 | 3745.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 91 ±0 | 225.2 | 1481.0 | 3470.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 91 ±0 | 192.2 | 1600.2 | 4072.7 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 91 ±0 | 190.0 | 1702.0 | 3608.2 | 1 | 0.0% |
| hasura | Haskell | M1 | 677 ±0 | 60.4 | 72.4 | 80.9 | 1 | 0.0% |
| mercurius | Node.js | M1 | 2546 ±0 | 14.4 | 24.5 | 34.4 | 1 | 0.0% |
| postgraphile | Node.js | M1 | 2076 ±0 | 17.1 | 31.1 | 69.8 | 1 | 0.0% |
| strawberry | Python | M1 | 1108 ±0 | 34.0 | 50.2 | 67.1 | 1 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | MC1 | 955 ±0 | 40.6 | 48.6 | 53.6 | 1 | 0.0% |
| apollo-server | Node.js | MC1 | 791 ±0 | 48.1 | 62.6 | 79.9 | 1 | 0.0% |
| async-graphql | Rust | MC1 | 1025 ±0 | 29.2 | 63.5 | 67.5 | 1 | 0.0% |
| fraiseql-tv | Rust | MC1 | 89 ±0 | 223.5 | 1568.3 | 3591.2 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 92 ±0 | 216.1 | 1483.1 | 3503.6 | 1 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 93 ±0 | 193.6 | 1687.3 | 4110.1 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 92 ±0 | 190.9 | 1608.4 | 3712.8 | 1 | 0.0% |
| hasura | Haskell | MC1 | 405 ±0 | 98.7 | 111.9 | 116.8 | 1 | 0.0% |
| mercurius | Node.js | MC1 | 1083 ±0 | 34.3 | 53.1 | 63.0 | 1 | 0.0% |
| postgraphile | Node.js | MC1 | 947 ±0 | 38.0 | 69.2 | 107.6 | 1 | 0.0% |
| strawberry | Python | MC1 | 480 ±0 | 80.7 | 111.9 | 131.7 | 1 | 0.0% |

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q1 | 1339 ±0 | 29.2 | 34.7 | 38.2 | 1 | 0.0% |
| apollo-server | Node.js | Q1 | 1297 ±0 | 30.3 | 43.6 | 52.7 | 1 | 0.0% |
| async-graphql | Rust | Q1 | 1146 ±0 | 22.6 | 68.4 | 73.2 | 1 | 0.0% |
| fraiseql-tv | Rust | Q1 | 6550 ±0 | 6.0 | 8.4 | 9.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 6588 ±0 | 5.9 | 8.3 | 9.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 6451 ±0 | 6.1 | 8.6 | 9.8 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 6317 ±0 | 6.2 | 8.7 | 9.8 | 1 | 0.0% |
| hasura | Haskell | Q1 | 1060 ±0 | 37.5 | 47.2 | 53.9 | 1 | 0.0% |
| mercurius | Node.js | Q1 | 1233 ±0 | 22.1 | 72.2 | 81.7 | 1 | 0.0% |
| postgraphile | Node.js | Q1 | 2099 ±0 | 18.2 | 28.3 | 39.4 | 1 | 0.0% |
| strawberry | Python | Q1 | 856 ±0 | 45.1 | 63.1 | 80.2 | 1 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2 | 8959 ±0 | 4.4 | 5.3 | 6.0 | 1 | 0.0% |
| apollo-server | Node.js | Q2 | 2060 ±0 | 18.6 | 29.0 | 37.9 | 1 | 0.0% |
| async-graphql | Rust | Q2 | 6224 ±0 | 6.0 | 9.6 | 10.8 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2 | 7271 ±0 | 5.4 | 7.5 | 8.4 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7338 ±0 | 5.3 | 7.5 | 8.3 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5667 ±0 | 6.0 | 18.2 | 28.1 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5552 ±0 | 6.1 | 20.3 | 30.0 | 1 | 0.0% |
| hasura | Haskell | Q2 | 1130 ±0 | 35.6 | 43.8 | 51.3 | 1 | 0.0% |
| mercurius | Node.js | Q2 | 2850 ±0 | 13.1 | 22.9 | 30.3 | 1 | 0.0% |
| postgraphile | Node.js | Q2 | 2203 ±0 | 17.2 | 27.2 | 40.7 | 1 | 0.0% |
| strawberry | Python | Q2 | 1256 ±0 | 30.7 | 36.2 | 58.5 | 1 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q2b | 4325 ±0 | 9.0 | 10.9 | 12.1 | 1 | 0.0% |
| apollo-server | Node.js | Q2b | 1483 ±0 | 25.5 | 41.6 | 51.5 | 1 | 0.0% |
| async-graphql | Rust | Q2b | 4122 ±0 | 9.0 | 16.2 | 20.2 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2b | 6259 ±0 | 6.3 | 8.7 | 9.7 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 6288 ±0 | 6.2 | 8.7 | 9.7 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4126 ±0 | 7.5 | 31.3 | 37.9 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4097 ±0 | 7.6 | 31.4 | 38.4 | 1 | 0.0% |
| hasura | Haskell | Q2b | 908 ±0 | 43.6 | 55.4 | 59.3 | 1 | 0.0% |
| mercurius | Node.js | Q2b | 2196 ±0 | 16.8 | 28.7 | 37.2 | 1 | 0.0% |
| postgraphile | Node.js | Q2b | 1953 ±0 | 19.6 | 29.5 | 42.7 | 1 | 0.0% |
| strawberry | Python | Q2b | 853 ±0 | 42.8 | 66.5 | 92.5 | 1 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | Q3 | 3281 ±0 | 11.9 | 14.1 | 15.1 | 1 | 0.0% |
| apollo-server | Node.js | Q3 | 501 ±0 | 78.2 | 112.5 | 127.7 | 1 | 0.0% |
| async-graphql | Rust | Q3 | 1421 ±0 | 27.3 | 50.8 | 61.9 | 1 | 0.0% |
| fraiseql-tv | Rust | Q3 | 3207 ±0 | 10.2 | 32.5 | 39.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 3176 ±0 | 10.2 | 34.1 | 40.7 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1303 ±0 | 19.9 | 72.6 | 90.4 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1302 ±0 | 19.8 | 73.3 | 92.0 | 1 | 0.0% |
| hasura | Haskell | Q3 | 820 ±0 | 49.3 | 61.7 | 66.2 | 1 | 0.0% |
| mercurius | Node.js | Q3 | 665 ±0 | 58.8 | 85.4 | 97.3 | 1 | 0.0% |
| postgraphile | Node.js | Q3 | 1177 ±0 | 31.4 | 57.4 | 74.8 | 1 | 0.0% |
| strawberry | Python | Q3 | 476 ±0 | 79.1 | 119.8 | 152.3 | 1 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| actix-web-rest | Rust | T1 | 2568 ±0 | 15.4 | 17.3 | 19.3 | 1 | 0.0% |
| apollo-server | Node.js | T1 | 918 ±0 | 41.6 | 63.6 | 73.0 | 1 | 0.0% |
| async-graphql | Rust | T1 | 3606 ±0 | 10.5 | 17.6 | 22.5 | 1 | 0.0% |
| fraiseql-tv | Rust | T1 | 4040 ±0 | 9.5 | 14.4 | 16.5 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 3876 ±0 | 10.0 | 14.7 | 16.6 | 1 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2114 ±0 | 13.3 | 48.5 | 56.7 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2114 ±0 | 13.4 | 48.8 | 57.5 | 1 | 0.0% |
| hasura | Haskell | T1 | 656 ±0 | 60.9 | 75.7 | 81.0 | 1 | 0.0% |
| mercurius | Node.js | T1 | 1214 ±0 | 31.0 | 49.1 | 57.2 | 1 | 0.0% |
| postgraphile | Node.js | T1 | 1658 ±0 | 22.2 | 38.0 | 73.1 | 1 | 0.0% |
| strawberry | Python | T1 | 570 ±0 | 68.0 | 97.0 | 113.0 | 1 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | M1_APQ | 1730 ±0 | 21.4 | 34.9 | 50.8 | 1 | 0.0% |
| async-graphql | Rust | M1_APQ | 6760 ±0 | 5.8 | 7.6 | 8.3 | 1 | 0.0% |
| fraiseql-tv | Rust | M1_APQ | 88 ±0 | 228.7 | 1479.8 | 3323.3 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 92 ±0 | 214.3 | 1538.4 | 2856.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 93 ±0 | 206.3 | 1510.1 | 2893.0 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 93 ±0 | 192.3 | 1716.8 | 3955.0 | 1 | 0.0% |
| mercurius | Node.js | M1_APQ | 2502 ±0 | 14.6 | 24.9 | 36.8 | 1 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q1_APQ | 1289 ±0 | 30.8 | 43.3 | 50.3 | 1 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1149 ±0 | 22.5 | 68.8 | 73.7 | 1 | 0.0% |
| fraiseql-tv | Rust | Q1_APQ | 6194 ±0 | 6.3 | 8.9 | 9.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6263 ±0 | 6.2 | 8.8 | 9.8 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 6036 ±0 | 6.5 | 9.1 | 10.4 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6084 ±0 | 6.5 | 9.0 | 10.1 | 1 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1234 ±0 | 22.3 | 71.5 | 81.1 | 1 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| apollo-server | Node.js | Q2b_APQ | 1503 ±0 | 25.1 | 40.8 | 51.2 | 1 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 3966 ±0 | 9.4 | 16.7 | 20.4 | 1 | 0.0% |
| fraiseql-tv | Rust | Q2b_APQ | 6099 ±0 | 6.4 | 8.9 | 9.8 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 5879 ±0 | 6.7 | 9.2 | 10.2 | 1 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4013 ±0 | 7.8 | 32.2 | 38.5 | 1 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 3958 ±0 | 7.8 | 33.2 | 39.6 | 1 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2162 ±0 | 17.2 | 29.7 | 38.3 | 1 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | Median RPS (±σ) | p50 ms | p95 ms | p99 ms | Passes | Errors |
|-----------|----------|-------|----------------:|-------:|-------:|-------:|-------:|--------|
| fraiseql-tv | Rust | M1d | 6783 ±0 | 5.8 | 8.0 | 9.1 | 1 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 6697 ±0 | 5.9 | 8.2 | 9.3 | 1 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1339 ±0 | 29.2 | 38.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1297 ±0 | 30.3 | 52.7 | 0.0% |
| mercurius | Node.js | 1233 ±0 | 22.1 | 81.7 | 0.0% |
| async-graphql | Rust | 1146 ±0 | 22.6 | 73.2 | 0.0% |
| strawberry | Python | 856 ±0 | 45.1 | 80.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 6588 ±0 | 5.9 | 9.3 | 0.0% |
| fraiseql-tv | Rust | 6550 ±0 | 6.0 | 9.4 | 0.0% |
| fraiseql-v-cache | Rust | 6451 ±0 | 6.1 | 9.8 | 0.0% |
| fraiseql-v-nocache | Rust | 6317 ±0 | 6.2 | 9.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2099 ±0 | 18.2 | 39.4 | 0.0% |
| hasura | Haskell | 1060 ±0 | 37.5 | 53.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 6588 ±0 | 5.9 | 9.3 |
| fraiseql-tv | Rust | graphql-precomputed | 6550 ±0 | 6.0 | 9.4 |
| fraiseql-v-cache | Rust | graphql-precomputed | 6451 ±0 | 6.1 | 9.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 6317 ±0 | 6.2 | 9.8 |
| postgraphile | Node.js | graphql-schema-first | 2099 ±0 | 18.2 | 39.4 |
| actix-web-rest | Rust | rest | 1339 ±0 | 29.2 | 38.2 |
| apollo-server | Node.js | graphql | 1297 ±0 | 30.3 | 52.7 |
| mercurius | Node.js | graphql | 1233 ±0 | 22.1 | 81.7 |
| async-graphql | Rust | graphql | 1146 ±0 | 22.6 | 73.2 |
| hasura | Haskell | graphql-schema-first | 1060 ±0 | 37.5 | 53.9 |
| strawberry | Python | graphql | 856 ±0 | 45.1 | 80.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 6588 | 77 | 0.0050 | 48 | 0.0080 | 95 | 0.0040 |
| fraiseql-tv | 6550 | 76 | 0.0050 | 47 | 0.0080 | 94 | 0.0040 |
| fraiseql-v-cache | 6451 | 75 | 0.0051 | 47 | 0.0082 | 93 | 0.0041 |
| fraiseql-v-nocache | 6317 | 73 | 0.0052 | 46 | 0.0083 | 91 | 0.0042 |
| postgraphile | 2099 | 24 | 0.0156 | 15 | 0.0251 | 30 | 0.0126 |
| actix-web-rest | 1339 | 16 | 0.0244 | 10 | 0.0393 | 19 | 0.0197 |
| apollo-server | 1297 | 15 | 0.0252 | 9 | 0.0406 | 19 | 0.0204 |
| mercurius | 1233 | 14 | 0.0265 | 9 | 0.0427 | 18 | 0.0214 |
| async-graphql | 1146 | 13 | 0.0285 | 8 | 0.0460 | 16 | 0.0231 |
| hasura | 1060 | 12 | 0.0309 | 8 | 0.0497 | 15 | 0.0249 |
| strawberry | 856 | 10 | 0.0382 | 6 | 0.0615 | 12 | 0.0309 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 134.5 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 134.3 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 103.4 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 11 | 89.9 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 127 | 116.6 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 92.4 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 65 | 108.2 |
| mercurius | Node.js | 464 | 8.8 | 104 | 56 | 99.4 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 119.6 |
| hasura | Haskell | — | — | — | 133 | 153.2 |
| strawberry | Python | 1,812 | 12.7 | 136 | 189 | 161.8 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.5 |

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

> **Peak**: fraiseql-tv-cache 92 cycles/s (1 req) vs mercurius 1083 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 6,480 M/s: **~395,253 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.