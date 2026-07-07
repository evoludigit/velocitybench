# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-07  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
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
| Passes | 1 |
| Run timestamp | 2026-07-07T07:29:18+00:00 |

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
| `tv_comment` | 692.0 MB | 290.2 MB | 1.58 GB |
| `tb_comment` | 294.7 MB | 81.5 MB | 376.4 MB |
| `tv_post` | 200.4 MB | 62.6 MB | 311.7 MB |
| `tb_post` | 133.8 MB | 19.8 MB | 153.7 MB |
| `tv_user` | 8.0 MB | 9.3 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 4.6 MB | 4.4 MB | 9.1 MB |
| `tb_user_follows` | 2.1 MB | 4.6 MB | 6.8 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.0 MB | 0.0 MB | 0.1 MB |
| `tvd_user` | 0.0 MB | 0.0 MB | 0.0 MB |
| `tb_mutation_log` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.90 GB  
**TB tables (normalized baseline)**: 560.3 MB  
**Storage amplification**: 4.47× (TV adds 1.90 GB on top of the normalized 560.3 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 6559 | 5.9 | 8.4 | 9.4 | 196,783 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 6549 | 6.0 | 8.4 | 9.4 | 196,479 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 6441 | 6.1 | 8.6 | 10.0 | 193,235 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 5965 | 6.5 | 9.4 | 11.2 | 178,946 | 0.0% |
| hasura | Haskell | Q1 | 1066 | 37.4 | 47.1 | 53.3 | 31,967 | 0.0% |
| postgraphile | Node.js | Q1 | 2101 | 18.2 | 28.3 | 42.1 | 63,043 | 0.0% |
| actix-web-rest | Rust | Q1 | 1315 | 29.4 | 36.2 | 39.7 | 39,454 | 0.0% |
| async-graphql | Rust | Q1 | 1168 | 22.6 | 67.0 | 71.8 | 35,052 | 0.0% |
| mercurius | Node.js | Q1 | 1231 | 21.8 | 72.3 | 82.0 | 36,939 | 0.0% |
| apollo-server | Node.js | Q1 | 1295 | 30.2 | 44.8 | 57.6 | 38,863 | 0.0% |
| strawberry | Python | Q1 | 855 | 45.5 | 63.8 | 83.6 | 25,645 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 7202 | 5.4 | 7.6 | 8.5 | 216,048 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7362 | 5.3 | 7.5 | 8.3 | 220,862 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5628 | 6.0 | 20.4 | 29.5 | 168,825 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5394 | 6.3 | 20.5 | 29.3 | 161,828 | 0.0% |
| hasura | Haskell | Q2 | 1122 | 35.3 | 44.7 | 50.6 | 33,657 | 0.0% |
| postgraphile | Node.js | Q2 | 2407 | 15.7 | 24.5 | 38.0 | 72,215 | 0.0% |
| actix-web-rest | Rust | Q2 | 9152 | 4.3 | 5.1 | 5.5 | 274,548 | 0.0% |
| async-graphql | Rust | Q2 | 5878 | 6.7 | 9.7 | 10.8 | 176,341 | 0.0% |
| mercurius | Node.js | Q2 | 2870 | 12.9 | 22.4 | 29.6 | 86,094 | 0.0% |
| apollo-server | Node.js | Q2 | 1974 | 19.3 | 30.6 | 41.5 | 59,234 | 0.0% |
| strawberry | Python | Q2 | 1123 | 32.6 | 53.0 | 79.9 | 33,679 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 6176 | 6.3 | 8.9 | 10.0 | 185,276 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 6348 | 6.1 | 8.7 | 9.7 | 190,451 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4061 | 7.5 | 33.4 | 39.2 | 121,827 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4080 | 7.5 | 32.9 | 39.0 | 122,392 | 0.0% |
| hasura | Haskell | Q2b | 921 | 43.3 | 55.4 | 59.2 | 27,638 | 0.0% |
| postgraphile | Node.js | Q2b | 1884 | 20.1 | 32.1 | 48.0 | 56,513 | 0.0% |
| actix-web-rest | Rust | Q2b | 4259 | 9.2 | 11.2 | 13.9 | 127,779 | 0.0% |
| async-graphql | Rust | Q2b | 3775 | 10.1 | 17.3 | 21.2 | 113,242 | 0.0% |
| mercurius | Node.js | Q2b | 2229 | 16.5 | 29.1 | 37.8 | 66,858 | 0.0% |
| apollo-server | Node.js | Q2b | 1469 | 25.5 | 42.9 | 54.4 | 44,065 | 0.0% |
| strawberry | Python | Q2b | 842 | 44.5 | 69.5 | 90.4 | 25,275 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 4616 | 8.4 | 12.3 | 14.7 | 138,471 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 3147 | 10.1 | 35.8 | 42.0 | 94,399 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1286 | 20.1 | 73.4 | 92.3 | 38,588 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1290 | 20.0 | 73.5 | 92.4 | 38,714 | 0.0% |
| hasura | Haskell | Q3 | 809 | 49.4 | 62.3 | 67.3 | 24,274 | 0.0% |
| postgraphile | Node.js | Q3 | 1178 | 31.3 | 57.4 | 74.7 | 35,349 | 0.0% |
| actix-web-rest | Rust | Q3 | 3293 | 11.9 | 14.3 | 15.7 | 98,795 | 0.0% |
| async-graphql | Rust | Q3 | 1236 | 32.0 | 54.9 | 64.4 | 37,080 | 0.0% |
| mercurius | Node.js | Q3 | 704 | 55.2 | 81.9 | 95.0 | 21,132 | 0.0% |
| apollo-server | Node.js | Q3 | 502 | 78.6 | 111.7 | 125.8 | 15,052 | 0.0% |
| strawberry | Python | Q3 | 465 | 79.8 | 116.1 | 145.0 | 13,957 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 7741 | 5.1 | 7.0 | 7.8 | 232,224 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 7713 | 5.1 | 7.0 | 7.8 | 231,390 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7441 | 5.3 | 7.2 | 7.9 | 223,232 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7356 | 5.3 | 7.4 | 8.2 | 220,688 | 0.0% |
| hasura | Haskell | C3 | 975 | 40.8 | 50.9 | 56.1 | 29,246 | 0.0% |
| postgraphile | Node.js | C3 | 2581 | 14.8 | 22.5 | 32.2 | 77,425 | 0.0% |
| actix-web-rest | Rust | C3 | 11172 | 3.5 | 4.1 | 4.6 | 335,165 | 0.0% |
| async-graphql | Rust | C3 | 9997 | 4.0 | 5.5 | 6.3 | 299,897 | 0.0% |
| mercurius | Node.js | C3 | 4062 | 9.3 | 15.0 | 19.6 | 121,847 | 0.0% |
| apollo-server | Node.js | C3 | 2552 | 14.9 | 23.3 | 29.3 | 76,563 | 0.0% |
| strawberry | Python | C3 | 1325 | 29.3 | 39.5 | 58.1 | 39,739 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 7864 | 5.0 | 6.9 | 7.7 | 235,930 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 7664 | 5.1 | 7.0 | 7.8 | 229,919 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 7543 | 5.2 | 7.2 | 8.0 | 226,280 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7391 | 5.3 | 7.4 | 8.2 | 221,732 | 0.0% |
| hasura | Haskell | HC3 | 954 | 41.4 | 52.1 | 56.6 | 28,610 | 0.0% |
| postgraphile | Node.js | HC3 | 2588 | 14.6 | 22.7 | 36.3 | 77,639 | 0.0% |
| actix-web-rest | Rust | HC3 | 11066 | 3.6 | 4.2 | 4.7 | 331,989 | 0.0% |
| async-graphql | Rust | HC3 | 10248 | 3.9 | 5.3 | 6.0 | 307,435 | 0.0% |
| mercurius | Node.js | HC3 | 4131 | 9.2 | 14.5 | 18.7 | 123,918 | 0.0% |
| apollo-server | Node.js | HC3 | 2542 | 15.0 | 23.4 | 29.8 | 76,265 | 0.0% |
| strawberry | Python | HC3 | 1344 | 29.0 | 47.5 | 60.0 | 40,313 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 32 | 48.4 | 12788.7 | 29978.6 | 970 | 5.1% |
| fraiseql-tv-cache | Rust | M1 | 95 | 231.0 | 1388.3 | 2409.0 | 2,842 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 91 | 220.9 | 1506.5 | 3088.0 | 2,732 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 93 | 211.5 | 1572.0 | 3170.2 | 2,789 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 91 | 224.0 | 1419.5 | 2886.6 | 2,717 | 0.0% |
| hasura | Haskell | M1 | 1129 | 26.8 | 63.8 | 73.7 | 33,869 | 0.0% |
| postgraphile | Node.js | M1 | 2170 | 16.1 | 29.1 | 70.1 | 65,085 | 0.0% |
| actix-web-rest | Rust | M1 | 1588 | 25.5 | 30.9 | 34.4 | 47,627 | 0.0% |
| async-graphql | Rust | M1 | 5873 | 6.7 | 8.6 | 9.4 | 176,199 | 0.0% |
| mercurius | Node.js | M1 | 2520 | 14.3 | 25.1 | 36.6 | 75,603 | 0.0% |
| apollo-server | Node.js | M1 | 1719 | 21.3 | 34.1 | 50.6 | 51,566 | 0.0% |
| strawberry | Python | M1 | 1162 | 33.2 | 39.4 | 64.8 | 34,870 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 42 | 2.9 | 10035.4 | 13239.5 | 1,248 | 2.7% |
| fraiseql-tv-cache | Rust | M1d | 6776 | 5.8 | 8.2 | 9.4 | 203,295 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 7089 | 5.5 | 7.7 | 8.6 | 212,682 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 7106 | 5.5 | 7.7 | 8.6 | 213,181 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4737 | 6.6 | 29.7 | 36.7 | 142,103 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4662 | 6.5 | 31.5 | 37.9 | 139,863 | 0.0% |
| hasura | Haskell | F1 | 1057 | 38.6 | 49.3 | 56.2 | 31,705 | 0.0% |
| postgraphile | Node.js | F1 | 2338 | 16.3 | 24.4 | 39.6 | 70,148 | 0.0% |
| actix-web-rest | Rust | F1 | 8969 | 4.4 | 5.3 | 5.9 | 269,064 | 0.0% |
| async-graphql | Rust | F1 | 5630 | 7.0 | 10.1 | 11.6 | 168,909 | 0.0% |
| mercurius | Node.js | F1 | 2746 | 13.5 | 23.6 | 31.3 | 82,383 | 0.0% |
| apollo-server | Node.js | F1 | 2075 | 18.5 | 28.0 | 36.6 | 62,236 | 0.0% |
| strawberry | Python | F1 | 1111 | 33.3 | 51.3 | 76.6 | 33,318 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 6250 | 6.3 | 8.8 | 9.9 | 187,491 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 6252 | 6.2 | 8.8 | 10.0 | 187,554 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 3573 | 8.2 | 38.1 | 43.9 | 107,190 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 3564 | 8.2 | 38.2 | 43.9 | 106,916 | 0.0% |
| hasura | Haskell | F2 | 933 | 41.2 | 54.8 | 62.9 | 27,989 | 0.0% |
| postgraphile | Node.js | F2 | 1723 | 21.4 | 36.8 | 56.5 | 51,701 | 0.0% |
| actix-web-rest | Rust | F2 | 3813 | 10.3 | 12.2 | 13.2 | 114,376 | 0.0% |
| async-graphql | Rust | F2 | 3718 | 10.2 | 17.7 | 21.9 | 111,532 | 0.0% |
| mercurius | Node.js | F2 | 2116 | 17.5 | 30.2 | 38.3 | 63,472 | 0.0% |
| apollo-server | Node.js | F2 | 1462 | 25.6 | 42.9 | 54.4 | 43,869 | 0.0% |
| strawberry | Python | F2 | 836 | 45.5 | 71.4 | 77.9 | 25,080 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 6591 | 5.9 | 8.3 | 9.3 | 197,739 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 6497 | 6.0 | 8.4 | 9.4 | 194,915 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6248 | 6.3 | 8.8 | 9.9 | 187,455 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6332 | 6.2 | 8.6 | 9.7 | 189,956 | 0.0% |
| hasura | Haskell | F3 | 1074 | 37.0 | 47.2 | 52.9 | 32,214 | 0.0% |
| postgraphile | Node.js | F3 | 2017 | 18.9 | 30.0 | 42.4 | 60,524 | 0.0% |
| actix-web-rest | Rust | F3 | 1319 | 29.7 | 35.4 | 38.4 | 39,562 | 0.0% |
| async-graphql | Rust | F3 | 1169 | 22.7 | 66.9 | 71.4 | 35,058 | 0.0% |
| mercurius | Node.js | F3 | 1241 | 21.8 | 71.9 | 82.2 | 37,224 | 0.0% |
| apollo-server | Node.js | F3 | 1300 | 30.4 | 43.9 | 53.5 | 39,012 | 0.0% |
| strawberry | Python | F3 | 850 | 45.4 | 63.3 | 85.9 | 25,503 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 3973 | 9.7 | 14.5 | 16.5 | 119,196 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4041 | 9.5 | 14.3 | 16.4 | 121,220 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2111 | 13.4 | 48.8 | 57.7 | 63,333 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2108 | 13.4 | 49.0 | 57.9 | 63,241 | 0.0% |
| hasura | Haskell | T1 | 653 | 61.2 | 75.4 | 79.7 | 19,585 | 0.0% |
| postgraphile | Node.js | T1 | 1587 | 23.3 | 38.4 | 76.2 | 47,601 | 0.0% |
| actix-web-rest | Rust | T1 | 2578 | 15.3 | 17.3 | 18.5 | 77,339 | 0.0% |
| async-graphql | Rust | T1 | 3543 | 10.9 | 17.3 | 21.3 | 106,298 | 0.0% |
| mercurius | Node.js | T1 | 1211 | 31.1 | 50.0 | 58.9 | 36,342 | 0.0% |
| apollo-server | Node.js | T1 | 917 | 41.4 | 63.2 | 72.4 | 27,516 | 0.0% |
| strawberry | Python | T1 | 590 | 65.1 | 94.1 | 107.1 | 17,710 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 32 | 55.5 | 13521.9 | 27488.4 | 959 | 4.9% |
| fraiseql-tv-cache | Rust | MC1 | 92 | 245.7 | 1469.5 | 2955.6 | 2,760 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 91 | 234.2 | 1423.0 | 2800.1 | 2,724 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 93 | 225.5 | 1409.3 | 2928.5 | 2,778 | 0.0% |
| hasura | Haskell | MC1 | 403 | 99.2 | 111.8 | 116.3 | 12,098 | 0.0% |
| postgraphile | Node.js | MC1 | 1000 | 34.6 | 65.0 | 112.0 | 29,991 | 0.0% |
| actix-web-rest | Rust | MC1 | 967 | 40.4 | 47.9 | 53.2 | 29,010 | 0.0% |
| async-graphql | Rust | MC1 | 1030 | 29.5 | 63.6 | 67.7 | 30,915 | 0.0% |
| mercurius | Node.js | MC1 | 1072 | 34.2 | 53.2 | 64.5 | 32,173 | 0.0% |
| apollo-server | Node.js | MC1 | 795 | 47.2 | 64.6 | 80.8 | 23,851 | 0.0% |
| strawberry | Python | MC1 | 491 | 80.7 | 115.7 | 133.1 | 14,720 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 6257 | 6.2 | 8.7 | 9.6 | 187,707 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6049 | 6.4 | 9.1 | 10.0 | 181,466 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 5967 | 6.5 | 9.3 | 10.5 | 179,018 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 5957 | 6.6 | 9.2 | 10.3 | 178,700 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1148 | 22.7 | 68.3 | 73.1 | 34,428 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1238 | 22.1 | 71.4 | 81.0 | 37,136 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1303 | 30.2 | 44.4 | 54.9 | 39,088 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 6084 | 6.4 | 9.1 | 10.1 | 182,535 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 6039 | 6.4 | 9.2 | 10.2 | 181,174 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 3931 | 7.8 | 32.7 | 39.2 | 117,921 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 3940 | 7.7 | 34.0 | 40.3 | 118,191 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 3669 | 10.3 | 18.4 | 22.6 | 110,067 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2200 | 16.8 | 28.7 | 37.3 | 65,985 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1529 | 24.7 | 40.3 | 49.2 | 45,868 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 32 | 54.9 | 12123.8 | 30001.5 | 971 | 5.2% |
| fraiseql-tv-cache | Rust | M1_APQ | 90 | 237.3 | 1404.2 | 3551.0 | 2,705 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 88 | 240.4 | 1511.6 | 3082.3 | 2,638 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 93 | 230.7 | 1380.7 | 2605.0 | 2,795 | 0.0% |
| async-graphql | Rust | M1_APQ | 6437 | 6.1 | 7.7 | 8.8 | 193,112 | 0.0% |
| mercurius | Node.js | M1_APQ | 2492 | 14.6 | 24.5 | 34.8 | 74,752 | 0.0% |
| apollo-server | Node.js | M1_APQ | 1792 | 20.9 | 31.9 | 44.1 | 53,769 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1315 | 29.4 | 39.7 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1295 | 30.2 | 57.6 | 0.0% |
| mercurius | Node.js | 1231 | 21.8 | 82.0 | 0.0% |
| async-graphql | Rust | 1168 | 22.6 | 71.8 | 0.0% |
| strawberry | Python | 855 | 45.5 | 83.6 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 6559 | 5.9 | 9.4 | 0.0% |
| fraiseql-tv-cache | Rust | 6549 | 6.0 | 9.4 | 0.0% |
| fraiseql-v-nocache | Rust | 6441 | 6.1 | 10.0 | 0.0% |
| fraiseql-v-cache | Rust | 5965 | 6.5 | 11.2 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2101 | 18.2 | 42.1 | 0.0% |
| hasura | Haskell | 1066 | 37.4 | 53.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 6559 | 5.9 | 9.4 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 6549 | 6.0 | 9.4 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 6441 | 6.1 | 10.0 |
| fraiseql-v-cache | Rust | graphql-precomputed | 5965 | 6.5 | 11.2 |
| postgraphile | Node.js | graphql-schema-first | 2101 | 18.2 | 42.1 |
| actix-web-rest | Rust | rest | 1315 | 29.4 | 39.7 |
| apollo-server | Node.js | graphql | 1295 | 30.2 | 57.6 |
| mercurius | Node.js | graphql | 1231 | 21.8 | 82.0 |
| async-graphql | Rust | graphql | 1168 | 22.6 | 71.8 |
| hasura | Haskell | graphql-schema-first | 1066 | 37.4 | 53.3 |
| strawberry | Python | graphql | 855 | 45.5 | 83.6 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 6559 | 76 | 0.0050 | 47 | 0.0080 | 94 | 0.0040 |
| fraiseql-tv-cache | 6549 | 76 | 0.0050 | 47 | 0.0080 | 94 | 0.0040 |
| fraiseql-v-nocache | 6441 | 75 | 0.0051 | 47 | 0.0082 | 93 | 0.0041 |
| fraiseql-v-cache | 5965 | 69 | 0.0055 | 43 | 0.0088 | 86 | 0.0044 |
| postgraphile | 2101 | 24 | 0.0156 | 15 | 0.0251 | 30 | 0.0126 |
| actix-web-rest | 1315 | 15 | 0.0249 | 9 | 0.0401 | 19 | 0.0201 |
| apollo-server | 1295 | 15 | 0.0253 | 9 | 0.0407 | 19 | 0.0204 |
| mercurius | 1231 | 14 | 0.0266 | 9 | 0.0428 | 18 | 0.0215 |
| async-graphql | 1168 | 14 | 0.0280 | 8 | 0.0451 | 17 | 0.0226 |
| hasura | 1066 | 12 | 0.0307 | 8 | 0.0495 | 15 | 0.0248 |
| strawberry | 855 | 10 | 0.0383 | 6 | 0.0616 | 12 | 0.0309 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 11 | 116.2 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 132.8 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 13 | 91.3 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 104.0 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 129 | 115.4 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 92.1 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 64 | 106.9 |
| mercurius | Node.js | 464 | 8.8 | 104 | 55 | 98.3 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 115.6 |
| hasura | Haskell | — | — | — | 134 | 153.2 |
| strawberry | Python | 1,812 | 12.7 | 136 | 180 | 161.8 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.6 |

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

> **Peak**: fraiseql-tv-cache 92 cycles/s (1 req) vs mercurius 1072 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 5,873 M/s: **~358,271 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.