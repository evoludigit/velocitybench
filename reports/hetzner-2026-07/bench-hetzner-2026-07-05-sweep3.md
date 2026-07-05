# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-05  
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
| Kernel | 6.8.0-117-generic |
| PostgreSQL | 17.10 (Debian 17.10-1.pgdg13+1) |
| Load generator | k6-v2.0.0 |
| Target host | 10.7.0.2 |
| `tv_*` persistence | logged (WAL-durable — publishable profile) |
| `tv_*` trigger scope | FraiseQL frameworks only — classical stacks mutate a vanilla tb_user (they never deploy pg_tviews) |
| Dataset | MEDIUM — 10 000 users · 50 000 posts · 200 000 comments |
| Concurrency | 40 workers |
| Measurement / warmup / cooldown | 30s / 10s / 5s |
| Passes | 1 |
| Run timestamp | 2026-07-05T04:27:19+00:00 |

### Framework Versions

| Framework | Version |
|-----------|---------|
| fraiseql-tv | 2.10.0 |
| fraiseql-tv-audit | 2.10.0 |
| fraiseql-tv-cache | 2.10.0 |
| fraiseql-v-cache | 2.10.0 |
| fraiseql-v-nocache | 2.10.0 |
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
| `tv_comment` | 701.1 MB | 322.3 MB | 1.62 GB |
| `tb_comment` | 294.7 MB | 82.2 MB | 377.0 MB |
| `tv_post` | 201.0 MB | 72.2 MB | 321.8 MB |
| `tb_post` | 133.6 MB | 19.7 MB | 153.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_mutation_log` | 7.4 MB | 0.6 MB | 8.0 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 567.2 MB  
**Storage amplification**: 4.52× (TV adds 1.95 GB on top of the normalized 567.2 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 8182 | 4.7 | 6.9 | 7.6 | 245,469 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 8415 | 4.6 | 6.6 | 7.3 | 252,447 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8005 | 4.9 | 7.0 | 7.9 | 240,144 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7945 | 4.9 | 7.0 | 8.0 | 238,364 | 0.0% |
| hasura | Haskell | Q1 | 1491 | 27.6 | 35.9 | 44.8 | 44,743 | 0.0% |
| postgraphile | Node.js | Q1 | 2814 | 13.2 | 23.4 | 35.8 | 84,435 | 0.0% |
| actix-web-rest | Rust | Q1 | 1628 | 23.9 | 28.6 | 31.2 | 48,854 | 0.0% |
| async-graphql | Rust | Q1 | 1404 | 17.2 | 63.7 | 68.0 | 42,135 | 0.0% |
| mercurius | Node.js | Q1 | 1473 | 17.8 | 64.3 | 74.6 | 44,204 | 0.0% |
| apollo-server | Node.js | Q1 | 1575 | 24.7 | 38.1 | 47.2 | 47,248 | 0.0% |
| strawberry | Python | Q1 | 991 | 38.9 | 51.0 | 76.4 | 29,721 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 9298 | 4.2 | 5.9 | 6.5 | 278,942 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 9800 | 4.0 | 5.7 | 6.3 | 293,988 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7058 | 4.8 | 11.8 | 25.4 | 211,729 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7051 | 4.8 | 11.8 | 26.6 | 211,524 | 0.0% |
| hasura | Haskell | Q2 | 1600 | 25.5 | 30.9 | 40.7 | 48,011 | 0.0% |
| postgraphile | Node.js | Q2 | 3471 | 10.7 | 18.4 | 29.3 | 104,127 | 0.0% |
| actix-web-rest | Rust | Q2 | 11585 | 3.4 | 4.4 | 5.2 | 347,546 | 0.0% |
| async-graphql | Rust | Q2 | 6040 | 6.1 | 11.5 | 15.2 | 181,203 | 0.0% |
| mercurius | Node.js | Q2 | 4720 | 8.0 | 13.0 | 17.1 | 141,586 | 0.0% |
| apollo-server | Node.js | Q2 | 2992 | 12.6 | 21.0 | 26.9 | 89,761 | 0.0% |
| strawberry | Python | Q2 | 1424 | 26.8 | 34.5 | 59.1 | 42,707 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 7906 | 4.9 | 7.0 | 7.8 | 237,167 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 8056 | 4.9 | 6.8 | 7.6 | 241,680 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5061 | 6.3 | 26.4 | 34.2 | 151,837 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5069 | 6.3 | 25.5 | 33.8 | 152,076 | 0.0% |
| hasura | Haskell | Q2b | 1233 | 31.7 | 44.6 | 49.6 | 36,994 | 0.0% |
| postgraphile | Node.js | Q2b | 2603 | 14.3 | 25.0 | 38.0 | 78,080 | 0.0% |
| actix-web-rest | Rust | Q2b | 4929 | 7.8 | 10.6 | 13.0 | 147,875 | 0.0% |
| async-graphql | Rust | Q2b | 5587 | 6.6 | 12.0 | 15.3 | 167,601 | 0.0% |
| mercurius | Node.js | Q2b | 2927 | 12.4 | 22.8 | 28.7 | 87,804 | 0.0% |
| apollo-server | Node.js | Q2b | 1930 | 19.2 | 33.7 | 41.9 | 57,904 | 0.0% |
| strawberry | Python | Q2b | 1030 | 40.7 | 55.7 | 74.6 | 30,891 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 4080 | 8.4 | 24.8 | 33.8 | 122,412 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 4156 | 8.2 | 24.2 | 33.5 | 124,665 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1511 | 16.9 | 65.4 | 79.8 | 45,321 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1512 | 16.9 | 65.8 | 80.6 | 45,372 | 0.0% |
| hasura | Haskell | Q3 | 1029 | 38.8 | 51.9 | 56.3 | 30,873 | 0.0% |
| postgraphile | Node.js | Q3 | 1450 | 24.7 | 49.9 | 67.3 | 43,504 | 0.0% |
| async-graphql | Rust | Q3 | 2241 | 17.0 | 32.0 | 38.9 | 67,237 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 9857 | 4.0 | 5.5 | 6.1 | 295,701 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 10078 | 3.9 | 5.4 | 6.0 | 302,345 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 9588 | 4.1 | 5.7 | 6.2 | 287,625 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 9534 | 4.1 | 5.7 | 6.3 | 286,034 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 9888 | 3.9 | 5.5 | 6.1 | 296,626 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 9909 | 4.0 | 5.5 | 6.1 | 297,273 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 9634 | 4.1 | 5.7 | 6.2 | 289,035 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 9674 | 4.0 | 5.6 | 6.2 | 290,221 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 99 | 203.4 | 1306.2 | 2476.0 | 2,963 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 108 | 218.8 | 1140.7 | 2054.2 | 3,238 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 100 | 197.8 | 1300.9 | 2709.3 | 3,003 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 102 | 199.5 | 1289.7 | 2615.3 | 3,064 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 99 | 183.8 | 1578.1 | 3015.8 | 2,980 | 0.0% |
| hasura | Haskell | M1 | 1553 | 22.3 | 49.6 | 58.9 | 46,597 | 0.0% |
| postgraphile | Node.js | M1 | 2909 | 11.7 | 22.3 | 49.6 | 87,264 | 0.0% |
| actix-web-rest | Rust | M1 | 2465 | 15.8 | 18.6 | 20.9 | 73,961 | 0.0% |
| async-graphql | Rust | M1 | 8320 | 4.7 | 6.4 | 7.0 | 249,597 | 0.0% |
| mercurius | Node.js | M1 | 3954 | 9.5 | 15.5 | 21.0 | 118,623 | 0.0% |
| apollo-server | Node.js | M1 | 2512 | 14.6 | 24.1 | 33.8 | 75,364 | 0.0% |
| strawberry | Python | M1 | 1322 | 29.0 | 36.0 | 60.6 | 39,661 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 8642 | 4.6 | 6.4 | 7.2 | 259,258 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 9022 | 4.3 | 6.1 | 6.8 | 270,651 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 9234 | 4.2 | 6.0 | 6.7 | 277,018 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 5819 | 5.4 | 23.7 | 32.9 | 174,574 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 5745 | 5.4 | 26.0 | 34.2 | 172,357 | 0.0% |
| hasura | Haskell | F1 | 1332 | 29.4 | 40.0 | 46.0 | 39,975 | 0.0% |
| postgraphile | Node.js | F1 | 3171 | 11.6 | 20.6 | 32.2 | 95,140 | 0.0% |
| actix-web-rest | Rust | F1 | 11328 | 3.4 | 4.5 | 5.2 | 339,840 | 0.0% |
| async-graphql | Rust | F1 | 6291 | 6.0 | 10.3 | 13.7 | 188,723 | 0.0% |
| mercurius | Node.js | F1 | 4251 | 8.5 | 15.9 | 21.2 | 127,517 | 0.0% |
| apollo-server | Node.js | F1 | 2838 | 13.3 | 22.1 | 28.9 | 85,133 | 0.0% |
| strawberry | Python | F1 | 1309 | 29.3 | 37.9 | 60.3 | 39,274 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 7350 | 5.3 | 7.4 | 8.2 | 220,508 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 7513 | 5.2 | 7.2 | 8.0 | 225,377 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4308 | 6.8 | 34.3 | 40.5 | 129,229 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4294 | 6.8 | 34.9 | 40.8 | 128,819 | 0.0% |
| hasura | Haskell | F2 | 1084 | 36.0 | 48.9 | 54.5 | 32,522 | 0.0% |
| postgraphile | Node.js | F2 | 2340 | 15.5 | 29.1 | 42.8 | 70,210 | 0.0% |
| actix-web-rest | Rust | F2 | 4913 | 8.0 | 9.7 | 11.4 | 147,403 | 0.0% |
| async-graphql | Rust | F2 | 5339 | 7.0 | 12.5 | 15.8 | 160,179 | 0.0% |
| mercurius | Node.js | F2 | 3372 | 11.2 | 17.4 | 22.5 | 101,175 | 0.0% |
| apollo-server | Node.js | F2 | 1868 | 19.5 | 35.4 | 45.0 | 56,049 | 0.0% |
| strawberry | Python | F2 | 963 | 40.3 | 64.6 | 75.9 | 28,878 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 7779 | 5.0 | 7.0 | 7.7 | 233,382 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 8187 | 4.8 | 6.7 | 7.4 | 245,596 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7677 | 5.1 | 7.2 | 8.1 | 230,318 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 7737 | 5.0 | 7.2 | 8.1 | 232,104 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4857 | 7.9 | 12.0 | 13.7 | 145,715 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4861 | 7.9 | 12.0 | 13.8 | 145,826 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2490 | 11.5 | 44.6 | 50.9 | 74,706 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2498 | 11.2 | 45.3 | 51.9 | 74,951 | 0.0% |
| hasura | Haskell | T1 | 897 | 43.0 | 59.4 | 66.9 | 26,918 | 0.0% |
| postgraphile | Node.js | T1 | 2122 | 16.9 | 31.2 | 66.3 | 63,652 | 0.0% |
| actix-web-rest | Rust | T1 | 47 | 859.1 | 953.7 | 989.9 | 1,419 | 0.0% |
| async-graphql | Rust | T1 | 4856 | 8.0 | 12.4 | 14.7 | 145,695 | 0.0% |
| mercurius | Node.js | T1 | 1643 | 22.3 | 37.3 | 44.2 | 49,280 | 0.0% |
| apollo-server | Node.js | T1 | 1186 | 31.0 | 50.0 | 58.6 | 35,570 | 0.0% |
| strawberry | Python | T1 | 669 | 57.6 | 88.7 | 99.8 | 20,061 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 102 | 198.3 | 1314.1 | 2511.6 | 3,055 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 102 | 210.4 | 1319.8 | 2482.5 | 3,069 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 103 | 195.0 | 1238.0 | 2394.3 | 3,098 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 99 | 195.4 | 1337.7 | 3143.0 | 2,973 | 0.0% |
| hasura | Haskell | MC1 | 486 | 81.9 | 95.9 | 99.8 | 14,580 | 0.0% |
| postgraphile | Node.js | MC1 | 1283 | 26.3 | 54.6 | 93.7 | 38,479 | 0.0% |
| async-graphql | Rust | MC1 | 1241 | 23.4 | 58.6 | 62.4 | 37,236 | 0.0% |
| mercurius | Node.js | MC1 | 1319 | 27.3 | 47.5 | 55.4 | 39,559 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 7947 | 4.9 | 6.9 | 7.6 | 238,422 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 7760 | 5.0 | 7.1 | 7.8 | 232,805 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 7238 | 5.4 | 7.6 | 8.5 | 217,149 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 7370 | 5.3 | 7.5 | 8.4 | 221,102 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 7903 | 4.9 | 6.9 | 7.7 | 237,084 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 7600 | 5.1 | 7.2 | 7.9 | 228,005 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 4849 | 6.5 | 27.4 | 35.5 | 145,473 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4876 | 6.7 | 25.5 | 34.2 | 146,272 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 105 | 193.3 | 1213.8 | 2127.1 | 3,162 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 103 | 228.7 | 1147.7 | 2022.9 | 3,087 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 103 | 200.2 | 1202.3 | 2513.2 | 3,103 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 100 | 187.3 | 1503.4 | 2732.0 | 2,995 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1628 | 23.9 | 31.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1575 | 24.7 | 47.2 | 0.0% |
| mercurius | Node.js | 1473 | 17.8 | 74.6 | 0.0% |
| async-graphql | Rust | 1404 | 17.2 | 68.0 | 0.0% |
| strawberry | Python | 991 | 38.9 | 76.4 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 8415 | 4.6 | 7.3 | 0.0% |
| fraiseql-tv | Rust | 8182 | 4.7 | 7.6 | 0.0% |
| fraiseql-v-nocache | Rust | 8005 | 4.9 | 7.9 | 0.0% |
| fraiseql-v-cache | Rust | 7945 | 4.9 | 8.0 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2814 | 13.2 | 35.8 | 0.0% |
| hasura | Haskell | 1491 | 27.6 | 44.8 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 8415 | 4.6 | 7.3 |
| fraiseql-tv | Rust | graphql-precomputed | 8182 | 4.7 | 7.6 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8005 | 4.9 | 7.9 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7945 | 4.9 | 8.0 |
| postgraphile | Node.js | graphql-schema-first | 2814 | 13.2 | 35.8 |
| actix-web-rest | Rust | rest | 1628 | 23.9 | 31.2 |
| apollo-server | Node.js | graphql | 1575 | 24.7 | 47.2 |
| hasura | Haskell | graphql-schema-first | 1491 | 27.6 | 44.8 |
| mercurius | Node.js | graphql | 1473 | 17.8 | 74.6 |
| async-graphql | Rust | graphql | 1404 | 17.2 | 68.0 |
| strawberry | Python | graphql | 991 | 38.9 | 76.4 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 8415 | 98 | 0.0039 | 61 | 0.0063 | 121 | 0.0031 |
| fraiseql-tv | 8182 | 95 | 0.0040 | 59 | 0.0064 | 118 | 0.0032 |
| fraiseql-v-nocache | 8005 | 93 | 0.0041 | 58 | 0.0066 | 115 | 0.0033 |
| fraiseql-v-cache | 7945 | 92 | 0.0041 | 57 | 0.0066 | 114 | 0.0033 |
| postgraphile | 2814 | 33 | 0.0116 | 20 | 0.0187 | 41 | 0.0094 |
| actix-web-rest | 1628 | 19 | 0.0201 | 12 | 0.0324 | 23 | 0.0162 |
| apollo-server | 1575 | 18 | 0.0208 | 11 | 0.0335 | 23 | 0.0168 |
| hasura | 1491 | 17 | 0.0219 | 11 | 0.0353 | 21 | 0.0177 |
| mercurius | 1473 | 17 | 0.0222 | 11 | 0.0358 | 21 | 0.0179 |
| async-graphql | 1404 | 16 | 0.0233 | 10 | 0.0375 | 20 | 0.0188 |
| strawberry | 991 | 12 | 0.0330 | 7 | 0.0532 | 14 | 0.0267 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 11 | 139.9 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 13 | 137.5 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 12 | 93.2 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 105.6 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 130 | 118.5 |
| actix-web-rest | Rust | 681 | 4.0 | 12 | 5 | 84.8 |
| apollo-server | Node.js | 744 | 7.5 | 120 | 54 | 119.1 |
| hasura | Haskell | — | — | — | 134 | 146.3 |
| mercurius | Node.js | 444 | 9.2 | 104 | 55 | 97.6 |
| async-graphql | Rust | 693 | 4.5 | 12 | 10 | 123.7 |
| strawberry | Python | 1,771 | 12.6 | 136 | 174 | 168.7 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.8 |

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

> **Peak**: fraiseql-tv-cache 102 cycles/s (1 req) vs mercurius 1319 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 8,320 M/s: **~507,513 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.5M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.