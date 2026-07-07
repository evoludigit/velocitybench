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
| Run timestamp | 2026-07-07T15:09:13+00:00 |

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
| `tv_comment` | 693.1 MB | 322.4 MB | 1.62 GB |
| `tb_comment` | 294.7 MB | 81.5 MB | 376.4 MB |
| `tv_post` | 200.8 MB | 72.2 MB | 322.3 MB |
| `tb_post` | 133.8 MB | 19.8 MB | 153.7 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_mutation_log` | 9.8 MB | 0.8 MB | 10.6 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.6 MB | 6.8 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 569.6 MB  
**Storage amplification**: 4.51× (TV adds 1.95 GB on top of the normalized 569.6 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 6550 | 6.0 | 8.3 | 9.3 | 196,492 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 6677 | 5.8 | 8.2 | 9.2 | 200,304 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 6317 | 6.2 | 8.7 | 10.0 | 189,521 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 6504 | 6.0 | 8.4 | 9.8 | 195,115 | 0.0% |
| hasura | Haskell | Q1 | 1083 | 37.4 | 46.7 | 53.9 | 32,500 | 0.0% |
| postgraphile | Node.js | Q1 | 2115 | 18.1 | 27.8 | 39.4 | 63,440 | 0.0% |
| actix-web-rest | Rust | Q1 | 1387 | 28.1 | 34.1 | 37.8 | 41,598 | 0.0% |
| async-graphql | Rust | Q1 | 1207 | 21.7 | 66.0 | 71.0 | 36,216 | 0.0% |
| mercurius | Node.js | Q1 | 1262 | 21.4 | 70.8 | 79.7 | 37,849 | 0.0% |
| apollo-server | Node.js | Q1 | 1297 | 30.4 | 44.1 | 53.1 | 38,922 | 0.0% |
| strawberry | Python | Q1 | 883 | 44.8 | 63.3 | 80.2 | 26,478 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 7271 | 5.4 | 7.5 | 8.4 | 218,117 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7378 | 5.3 | 7.4 | 8.3 | 221,329 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5446 | 6.1 | 21.5 | 30.7 | 163,377 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5737 | 6.1 | 16.4 | 26.9 | 172,103 | 0.0% |
| hasura | Haskell | Q2 | 1123 | 35.6 | 43.8 | 51.3 | 33,696 | 0.0% |
| postgraphile | Node.js | Q2 | 2346 | 16.0 | 25.4 | 42.5 | 70,376 | 0.0% |
| actix-web-rest | Rust | Q2 | 9210 | 4.3 | 5.0 | 5.7 | 276,304 | 0.0% |
| async-graphql | Rust | Q2 | 5977 | 6.6 | 9.5 | 10.5 | 179,307 | 0.0% |
| mercurius | Node.js | Q2 | 2850 | 12.9 | 23.3 | 31.2 | 85,511 | 0.0% |
| apollo-server | Node.js | Q2 | 2021 | 18.8 | 29.9 | 39.9 | 60,621 | 0.0% |
| strawberry | Python | Q2 | 1262 | 30.6 | 36.2 | 57.1 | 37,873 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 6259 | 6.3 | 8.7 | 9.7 | 187,784 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 6340 | 6.1 | 8.7 | 9.7 | 190,199 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4045 | 7.5 | 33.7 | 39.5 | 121,343 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4147 | 7.5 | 31.3 | 37.5 | 124,414 | 0.0% |
| hasura | Haskell | Q2b | 906 | 43.9 | 56.3 | 61.1 | 27,176 | 0.0% |
| postgraphile | Node.js | Q2b | 1999 | 19.1 | 29.0 | 42.7 | 59,958 | 0.0% |
| actix-web-rest | Rust | Q2b | 4419 | 8.8 | 10.5 | 11.6 | 132,582 | 0.0% |
| async-graphql | Rust | Q2b | 3446 | 11.0 | 20.1 | 24.6 | 103,372 | 0.0% |
| mercurius | Node.js | Q2b | 2269 | 16.6 | 26.9 | 35.3 | 68,084 | 0.0% |
| apollo-server | Node.js | Q2b | 1513 | 25.0 | 40.4 | 50.9 | 45,382 | 0.0% |
| strawberry | Python | Q2b | 905 | 42.8 | 58.5 | 72.7 | 27,164 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 3247 | 10.1 | 32.5 | 39.7 | 97,401 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 3223 | 10.2 | 32.7 | 39.8 | 96,687 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1280 | 20.0 | 74.1 | 92.2 | 38,397 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1303 | 19.5 | 73.8 | 93.7 | 39,102 | 0.0% |
| hasura | Haskell | Q3 | 796 | 50.0 | 63.3 | 66.9 | 23,886 | 0.0% |
| postgraphile | Node.js | Q3 | 1208 | 30.6 | 56.0 | 73.1 | 36,227 | 0.0% |
| actix-web-rest | Rust | Q3 | 3337 | 11.8 | 13.9 | 15.0 | 100,124 | 0.0% |
| async-graphql | Rust | Q3 | 1314 | 29.9 | 52.4 | 62.0 | 39,415 | 0.0% |
| mercurius | Node.js | Q3 | 665 | 58.9 | 84.9 | 97.3 | 19,940 | 0.0% |
| apollo-server | Node.js | Q3 | 501 | 78.2 | 112.5 | 127.7 | 15,034 | 0.0% |
| strawberry | Python | Q3 | 485 | 79.1 | 140.4 | 156.6 | 14,562 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 7496 | 5.2 | 7.2 | 8.0 | 224,883 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 7528 | 5.2 | 7.2 | 8.0 | 225,834 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7540 | 5.2 | 7.2 | 7.9 | 226,195 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7629 | 5.2 | 7.0 | 7.7 | 228,860 | 0.0% |
| hasura | Haskell | C3 | 989 | 41.0 | 51.2 | 57.0 | 29,667 | 0.0% |
| postgraphile | Node.js | C3 | 2508 | 15.1 | 23.4 | 34.9 | 75,239 | 0.0% |
| actix-web-rest | Rust | C3 | 11214 | 3.5 | 4.0 | 4.3 | 336,411 | 0.0% |
| async-graphql | Rust | C3 | 10366 | 3.8 | 5.3 | 5.9 | 310,974 | 0.0% |
| mercurius | Node.js | C3 | 4082 | 9.0 | 15.4 | 21.8 | 122,450 | 0.0% |
| apollo-server | Node.js | C3 | 2619 | 14.7 | 21.9 | 27.8 | 78,564 | 0.0% |
| strawberry | Python | C3 | 1338 | 29.1 | 37.8 | 58.1 | 40,135 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 7749 | 5.0 | 7.0 | 7.8 | 232,459 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 7629 | 5.1 | 7.1 | 7.9 | 228,868 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 7558 | 5.2 | 7.2 | 7.9 | 226,744 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7637 | 5.2 | 7.0 | 7.7 | 229,099 | 0.0% |
| hasura | Haskell | HC3 | 957 | 41.6 | 51.4 | 56.0 | 28,713 | 0.0% |
| postgraphile | Node.js | HC3 | 2538 | 15.1 | 22.6 | 31.8 | 76,147 | 0.0% |
| actix-web-rest | Rust | HC3 | 11175 | 3.5 | 4.1 | 4.8 | 335,254 | 0.0% |
| async-graphql | Rust | HC3 | 10404 | 3.8 | 5.3 | 5.9 | 312,117 | 0.0% |
| mercurius | Node.js | HC3 | 4058 | 9.1 | 15.8 | 21.4 | 121,732 | 0.0% |
| apollo-server | Node.js | HC3 | 2580 | 15.0 | 22.1 | 27.5 | 77,387 | 0.0% |
| strawberry | Python | HC3 | 1338 | 28.8 | 37.2 | 58.0 | 40,147 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 89 | 216.2 | 1563.6 | 3982.4 | 2,657 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 92 | 266.6 | 1405.0 | 2721.9 | 2,760 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 90 | 198.4 | 1702.0 | 3608.2 | 2,706 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 91 | 192.2 | 1600.2 | 5147.0 | 2,741 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 89 | 248.0 | 1520.1 | 3195.6 | 2,672 | 0.0% |
| hasura | Haskell | M1 | 677 | 60.4 | 74.0 | 82.9 | 20,300 | 0.0% |
| postgraphile | Node.js | M1 | 2222 | 15.4 | 28.9 | 66.7 | 66,671 | 0.0% |
| actix-web-rest | Rust | M1 | 1838 | 21.8 | 26.6 | 28.2 | 55,129 | 0.0% |
| async-graphql | Rust | M1 | 6051 | 6.6 | 8.1 | 8.8 | 181,541 | 0.0% |
| mercurius | Node.js | M1 | 2546 | 14.4 | 24.5 | 37.9 | 76,391 | 0.0% |
| apollo-server | Node.js | M1 | 1782 | 20.8 | 32.7 | 47.8 | 53,466 | 0.0% |
| strawberry | Python | M1 | 1137 | 33.8 | 43.9 | 66.8 | 34,120 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 6690 | 5.9 | 8.1 | 9.2 | 200,707 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 6675 | 5.9 | 8.2 | 9.3 | 200,240 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 7045 | 5.6 | 7.8 | 8.7 | 211,349 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 6961 | 5.6 | 7.9 | 8.7 | 208,840 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4609 | 6.6 | 31.6 | 37.9 | 138,256 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4733 | 6.6 | 28.8 | 35.6 | 141,985 | 0.0% |
| hasura | Haskell | F1 | 982 | 40.2 | 51.2 | 56.7 | 29,452 | 0.0% |
| postgraphile | Node.js | F1 | 2203 | 17.1 | 26.5 | 44.7 | 66,086 | 0.0% |
| actix-web-rest | Rust | F1 | 8804 | 4.5 | 5.2 | 5.8 | 264,114 | 0.0% |
| async-graphql | Rust | F1 | 5924 | 6.7 | 9.6 | 10.7 | 177,716 | 0.0% |
| mercurius | Node.js | F1 | 2764 | 13.4 | 23.6 | 31.3 | 82,934 | 0.0% |
| apollo-server | Node.js | F1 | 2074 | 18.5 | 28.2 | 36.7 | 62,210 | 0.0% |
| strawberry | Python | F1 | 1139 | 33.8 | 40.6 | 66.4 | 34,182 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 6031 | 6.5 | 9.0 | 10.0 | 180,919 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 5991 | 6.5 | 9.1 | 10.1 | 179,727 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 3488 | 8.3 | 38.7 | 44.5 | 104,632 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 3594 | 8.1 | 37.8 | 43.2 | 107,824 | 0.0% |
| hasura | Haskell | F2 | 891 | 46.1 | 57.4 | 63.9 | 26,733 | 0.0% |
| postgraphile | Node.js | F2 | 1805 | 20.7 | 33.7 | 49.5 | 54,158 | 0.0% |
| actix-web-rest | Rust | F2 | 3712 | 10.6 | 12.6 | 16.3 | 111,371 | 0.0% |
| async-graphql | Rust | F2 | 4019 | 9.7 | 14.4 | 16.7 | 120,579 | 0.0% |
| mercurius | Node.js | F2 | 2070 | 17.5 | 32.1 | 40.6 | 62,107 | 0.0% |
| apollo-server | Node.js | F2 | 1505 | 25.2 | 40.9 | 49.8 | 45,139 | 0.0% |
| strawberry | Python | F2 | 850 | 45.5 | 70.2 | 81.4 | 25,501 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 6527 | 6.0 | 8.4 | 9.4 | 195,803 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 6361 | 6.2 | 8.6 | 9.5 | 190,837 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6105 | 6.4 | 9.0 | 10.1 | 183,160 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6363 | 6.2 | 8.5 | 9.5 | 190,887 | 0.0% |
| hasura | Haskell | F3 | 1126 | 36.8 | 43.5 | 52.3 | 33,789 | 0.0% |
| postgraphile | Node.js | F3 | 2028 | 18.6 | 29.8 | 47.1 | 60,839 | 0.0% |
| actix-web-rest | Rust | F3 | 1318 | 29.4 | 36.0 | 39.1 | 39,535 | 0.0% |
| async-graphql | Rust | F3 | 1213 | 21.5 | 66.0 | 70.7 | 36,402 | 0.0% |
| mercurius | Node.js | F3 | 1286 | 21.3 | 70.1 | 79.7 | 38,591 | 0.0% |
| apollo-server | Node.js | F3 | 1332 | 29.7 | 41.3 | 46.3 | 39,952 | 0.0% |
| strawberry | Python | F3 | 873 | 44.6 | 59.9 | 77.2 | 26,199 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 3926 | 9.9 | 14.6 | 16.5 | 117,793 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 3872 | 10.0 | 14.8 | 16.7 | 116,158 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2114 | 13.4 | 48.5 | 56.0 | 63,422 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2160 | 13.1 | 47.8 | 56.3 | 64,807 | 0.0% |
| hasura | Haskell | T1 | 641 | 62.0 | 77.2 | 84.0 | 19,229 | 0.0% |
| postgraphile | Node.js | T1 | 1658 | 22.2 | 35.8 | 73.1 | 49,755 | 0.0% |
| actix-web-rest | Rust | T1 | 2567 | 15.4 | 17.6 | 19.5 | 77,009 | 0.0% |
| async-graphql | Rust | T1 | 3606 | 10.5 | 17.6 | 22.5 | 108,179 | 0.0% |
| mercurius | Node.js | T1 | 1226 | 29.8 | 49.3 | 59.0 | 36,778 | 0.0% |
| apollo-server | Node.js | T1 | 922 | 39.9 | 63.6 | 73.0 | 27,671 | 0.0% |
| strawberry | Python | T1 | 598 | 65.0 | 92.6 | 101.7 | 17,927 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 88 | 206.7 | 1602.3 | 5247.3 | 2,637 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 95 | 270.2 | 1237.8 | 2205.1 | 2,843 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 92 | 223.6 | 1404.9 | 2887.4 | 2,771 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 91 | 193.6 | 1777.6 | 4593.2 | 2,721 | 0.0% |
| hasura | Haskell | MC1 | 405 | 98.7 | 111.7 | 116.8 | 12,151 | 0.0% |
| postgraphile | Node.js | MC1 | 1006 | 34.6 | 64.4 | 107.3 | 30,185 | 0.0% |
| actix-web-rest | Rust | MC1 | 991 | 39.0 | 46.5 | 51.9 | 29,728 | 0.0% |
| async-graphql | Rust | MC1 | 1073 | 28.6 | 61.6 | 65.5 | 32,183 | 0.0% |
| mercurius | Node.js | MC1 | 1152 | 32.9 | 48.4 | 57.6 | 34,559 | 0.0% |
| apollo-server | Node.js | MC1 | 812 | 46.8 | 59.6 | 71.7 | 24,364 | 0.0% |
| strawberry | Python | MC1 | 500 | 77.9 | 104.3 | 114.3 | 15,002 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 6301 | 6.2 | 8.6 | 9.6 | 189,032 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6263 | 6.2 | 8.8 | 9.8 | 187,893 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6085 | 6.5 | 8.8 | 9.9 | 182,538 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 6036 | 6.5 | 8.9 | 9.9 | 181,069 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1201 | 21.6 | 66.4 | 71.2 | 36,027 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1287 | 21.4 | 69.8 | 80.0 | 38,605 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1332 | 29.9 | 41.3 | 46.1 | 39,961 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 6099 | 6.4 | 8.9 | 9.8 | 182,960 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 5879 | 6.7 | 9.2 | 10.1 | 176,384 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 3974 | 7.7 | 33.3 | 39.6 | 119,207 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4028 | 7.7 | 32.2 | 38.5 | 120,827 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 3861 | 9.7 | 17.4 | 22.0 | 115,827 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2175 | 17.0 | 29.7 | 38.3 | 65,247 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1489 | 25.4 | 41.6 | 51.3 | 44,671 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 88 | 207.5 | 1610.2 | 4099.2 | 2,654 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 92 | 251.4 | 1377.0 | 2856.8 | 2,751 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 93 | 196.4 | 1797.9 | 3472.4 | 2,800 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 95 | 251.9 | 1286.8 | 2813.8 | 2,850 | 0.0% |
| async-graphql | Rust | M1_APQ | 6187 | 6.4 | 8.0 | 8.6 | 185,600 | 0.0% |
| mercurius | Node.js | M1_APQ | 2631 | 14.1 | 22.8 | 33.3 | 78,921 | 0.0% |
| apollo-server | Node.js | M1_APQ | 1730 | 21.4 | 34.9 | 50.8 | 51,886 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1387 | 28.1 | 37.8 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1297 | 30.4 | 53.1 | 0.0% |
| mercurius | Node.js | 1262 | 21.4 | 79.7 | 0.0% |
| async-graphql | Rust | 1207 | 21.7 | 71.0 | 0.0% |
| strawberry | Python | 883 | 44.8 | 80.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 6677 | 5.8 | 9.2 | 0.0% |
| fraiseql-tv | Rust | 6550 | 6.0 | 9.3 | 0.0% |
| fraiseql-v-cache | Rust | 6504 | 6.0 | 9.8 | 0.0% |
| fraiseql-v-nocache | Rust | 6317 | 6.2 | 10.0 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2115 | 18.1 | 39.4 | 0.0% |
| hasura | Haskell | 1083 | 37.4 | 53.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 6677 | 5.8 | 9.2 |
| fraiseql-tv | Rust | graphql-precomputed | 6550 | 6.0 | 9.3 |
| fraiseql-v-cache | Rust | graphql-precomputed | 6504 | 6.0 | 9.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 6317 | 6.2 | 10.0 |
| postgraphile | Node.js | graphql-schema-first | 2115 | 18.1 | 39.4 |
| actix-web-rest | Rust | rest | 1387 | 28.1 | 37.8 |
| apollo-server | Node.js | graphql | 1297 | 30.4 | 53.1 |
| mercurius | Node.js | graphql | 1262 | 21.4 | 79.7 |
| async-graphql | Rust | graphql | 1207 | 21.7 | 71.0 |
| hasura | Haskell | graphql-schema-first | 1083 | 37.4 | 53.9 |
| strawberry | Python | graphql | 883 | 44.8 | 80.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 6677 | 78 | 0.0049 | 48 | 0.0079 | 96 | 0.0040 |
| fraiseql-tv | 6550 | 76 | 0.0050 | 47 | 0.0080 | 94 | 0.0040 |
| fraiseql-v-cache | 6504 | 76 | 0.0050 | 47 | 0.0081 | 94 | 0.0041 |
| fraiseql-v-nocache | 6317 | 73 | 0.0052 | 46 | 0.0083 | 91 | 0.0042 |
| postgraphile | 2115 | 25 | 0.0155 | 15 | 0.0249 | 30 | 0.0125 |
| actix-web-rest | 1387 | 16 | 0.0236 | 10 | 0.0380 | 20 | 0.0191 |
| apollo-server | 1297 | 15 | 0.0252 | 9 | 0.0406 | 19 | 0.0204 |
| mercurius | 1262 | 15 | 0.0259 | 9 | 0.0418 | 18 | 0.0210 |
| async-graphql | 1207 | 14 | 0.0271 | 9 | 0.0437 | 17 | 0.0219 |
| hasura | 1083 | 13 | 0.0302 | 8 | 0.0486 | 16 | 0.0244 |
| strawberry | 883 | 10 | 0.0371 | 6 | 0.0597 | 13 | 0.0300 |

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
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 135.2 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 13 | 105.0 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 11 | 89.8 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 132 | 117.3 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 6 | 94.1 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 66 | 108.2 |
| mercurius | Node.js | 464 | 8.8 | 104 | 61 | 100.0 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 115.4 |
| hasura | Haskell | — | — | — | 134 | 152.6 |
| strawberry | Python | 1,812 | 12.7 | 136 | 191 | 163.1 |
| fraiseql-tv-audit | Rust | — | — | 43 | 9 | 2.5 |

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

> **Peak**: fraiseql-tv-cache 95 cycles/s (1 req) vs mercurius 1152 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 6,051 M/s: **~369,133 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.