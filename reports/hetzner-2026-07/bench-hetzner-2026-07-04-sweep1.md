# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-04  
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
| Run timestamp | 2026-07-05T00:28:06+00:00 |

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
| `tv_comment` | 700.5 MB | 291.9 MB | 1.58 GB |
| `tb_comment` | 294.7 MB | 82.2 MB | 377.0 MB |
| `tv_post` | 200.7 MB | 62.2 MB | 311.1 MB |
| `tb_post` | 133.6 MB | 19.7 MB | 153.3 MB |
| `tv_user` | 8.0 MB | 9.2 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 4.6 MB | 4.4 MB | 9.1 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.0 MB | 0.0 MB | 0.1 MB |
| `tvd_user` | 0.0 MB | 0.0 MB | 0.0 MB |
| `tb_mutation_log` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.90 GB  
**TB tables (normalized baseline)**: 560.5 MB  
**Storage amplification**: 4.47× (TV adds 1.90 GB on top of the normalized 560.5 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 8542 | 4.6 | 6.5 | 7.3 | 256,248 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 8242 | 4.7 | 6.7 | 7.4 | 247,261 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 7927 | 4.9 | 7.0 | 8.0 | 237,824 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7886 | 4.9 | 7.1 | 8.2 | 236,587 | 0.0% |
| hasura | Haskell | Q1 | 1624 | 26.8 | 32.6 | 43.8 | 48,712 | 0.0% |
| postgraphile | Node.js | Q1 | 2926 | 12.6 | 22.8 | 32.9 | 87,787 | 0.0% |
| actix-web-rest | Rust | Q1 | 1651 | 23.8 | 27.8 | 30.0 | 49,519 | 0.0% |
| async-graphql | Rust | Q1 | 1413 | 17.2 | 63.6 | 67.8 | 42,384 | 0.0% |
| mercurius | Node.js | Q1 | 1486 | 17.9 | 63.8 | 74.7 | 44,581 | 0.0% |
| apollo-server | Node.js | Q1 | 1581 | 24.6 | 38.6 | 48.3 | 47,439 | 0.0% |
| strawberry | Python | Q1 | 1000 | 38.5 | 51.0 | 73.7 | 29,988 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 9965 | 3.9 | 5.6 | 6.2 | 298,945 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 9508 | 4.1 | 5.8 | 6.4 | 285,232 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 6990 | 4.9 | 12.3 | 25.3 | 209,708 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 6968 | 4.9 | 10.9 | 25.7 | 209,036 | 0.0% |
| hasura | Haskell | Q2 | 1491 | 26.3 | 38.3 | 43.8 | 44,719 | 0.0% |
| postgraphile | Node.js | Q2 | 3169 | 11.5 | 21.1 | 35.2 | 95,062 | 0.0% |
| actix-web-rest | Rust | Q2 | 11475 | 3.4 | 4.4 | 5.3 | 344,242 | 0.0% |
| async-graphql | Rust | Q2 | 6212 | 6.1 | 10.0 | 13.7 | 186,365 | 0.0% |
| mercurius | Node.js | Q2 | 4643 | 8.0 | 14.0 | 18.1 | 139,299 | 0.0% |
| apollo-server | Node.js | Q2 | 2907 | 13.0 | 21.6 | 27.8 | 87,218 | 0.0% |
| strawberry | Python | Q2 | 1446 | 28.5 | 39.6 | 61.8 | 43,384 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 8360 | 4.6 | 6.7 | 7.4 | 250,790 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 7851 | 5.0 | 7.0 | 7.8 | 235,525 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5022 | 6.4 | 26.3 | 34.4 | 150,674 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5002 | 6.3 | 27.0 | 34.4 | 150,071 | 0.0% |
| hasura | Haskell | Q2b | 1234 | 31.8 | 44.7 | 48.9 | 37,019 | 0.0% |
| postgraphile | Node.js | Q2b | 2537 | 14.6 | 24.9 | 40.3 | 76,112 | 0.0% |
| actix-web-rest | Rust | Q2b | 4769 | 8.0 | 11.4 | 13.6 | 143,063 | 0.0% |
| async-graphql | Rust | Q2b | 5544 | 6.6 | 12.0 | 15.1 | 166,318 | 0.0% |
| mercurius | Node.js | Q2b | 2988 | 12.1 | 22.5 | 28.2 | 89,631 | 0.0% |
| apollo-server | Node.js | Q2b | 1956 | 19.0 | 32.8 | 42.1 | 58,669 | 0.0% |
| strawberry | Python | Q2b | 1030 | 43.7 | 54.1 | 81.2 | 30,888 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 5861 | 6.6 | 9.5 | 10.7 | 175,820 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 4173 | 8.1 | 25.7 | 34.3 | 125,196 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1500 | 16.8 | 66.0 | 81.5 | 44,991 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1472 | 17.5 | 66.4 | 81.8 | 44,148 | 0.0% |
| hasura | Haskell | Q3 | 966 | 40.6 | 54.0 | 57.4 | 28,989 | 0.0% |
| postgraphile | Node.js | Q3 | 1469 | 24.2 | 50.7 | 67.8 | 44,057 | 0.0% |
| async-graphql | Rust | Q3 | 2251 | 16.6 | 32.9 | 39.7 | 67,538 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 9738 | 4.0 | 5.6 | 6.2 | 292,152 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 10042 | 3.9 | 5.5 | 6.1 | 301,265 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 9683 | 4.0 | 5.6 | 6.2 | 290,484 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 9533 | 4.1 | 5.7 | 6.4 | 285,995 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 9848 | 4.0 | 5.6 | 6.2 | 295,444 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 10092 | 3.9 | 5.5 | 6.1 | 302,749 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 9731 | 4.0 | 5.6 | 6.2 | 291,921 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 9472 | 4.1 | 5.7 | 6.3 | 284,157 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 32 | 41.3 | 12372.5 | 30002.0 | 960 | 5.3% |
| fraiseql-tv-cache | Rust | M1 | 98 | 204.5 | 1415.0 | 3241.3 | 2,934 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 97 | 200.1 | 1514.4 | 2997.0 | 2,922 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 96 | 207.5 | 1470.3 | 3732.4 | 2,877 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 102 | 196.6 | 1397.8 | 2770.1 | 3,046 | 0.0% |
| hasura | Haskell | M1 | 1494 | 22.5 | 52.0 | 62.8 | 44,816 | 0.0% |
| postgraphile | Node.js | M1 | 2929 | 11.5 | 22.0 | 53.6 | 87,882 | 0.0% |
| actix-web-rest | Rust | M1 | 2362 | 16.3 | 19.5 | 31.6 | 70,855 | 0.0% |
| async-graphql | Rust | M1 | 8534 | 4.6 | 6.1 | 6.7 | 256,030 | 0.0% |
| mercurius | Node.js | M1 | 3746 | 9.7 | 17.4 | 24.4 | 112,380 | 0.0% |
| apollo-server | Node.js | M1 | 2520 | 14.6 | 23.9 | 34.2 | 75,611 | 0.0% |
| strawberry | Python | M1 | 1330 | 28.9 | 36.4 | 59.1 | 39,912 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 44 | 2.1 | 10004.8 | 13031.3 | 1,305 | 2.7% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 8872 | 4.4 | 6.2 | 6.9 | 266,154 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 8856 | 4.4 | 6.2 | 6.9 | 265,678 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 5774 | 5.3 | 26.1 | 34.1 | 173,214 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 5759 | 5.4 | 24.8 | 33.6 | 172,778 | 0.0% |
| hasura | Haskell | F1 | 1325 | 29.6 | 39.2 | 46.4 | 39,746 | 0.0% |
| postgraphile | Node.js | F1 | 3038 | 12.1 | 21.7 | 35.2 | 91,149 | 0.0% |
| actix-web-rest | Rust | F1 | 10756 | 3.6 | 4.7 | 5.8 | 322,668 | 0.0% |
| async-graphql | Rust | F1 | 6589 | 5.9 | 8.6 | 11.4 | 197,674 | 0.0% |
| mercurius | Node.js | F1 | 4222 | 8.6 | 16.3 | 21.2 | 126,652 | 0.0% |
| apollo-server | Node.js | F1 | 2872 | 13.1 | 21.7 | 28.7 | 86,153 | 0.0% |
| strawberry | Python | F1 | 1315 | 29.1 | 38.9 | 60.8 | 39,448 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 7539 | 5.2 | 7.3 | 8.1 | 226,164 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 7625 | 5.1 | 7.2 | 8.1 | 228,752 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4208 | 7.0 | 33.7 | 41.0 | 126,225 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4296 | 6.9 | 33.9 | 39.9 | 128,869 | 0.0% |
| hasura | Haskell | F2 | 1103 | 35.4 | 49.3 | 53.8 | 33,085 | 0.0% |
| postgraphile | Node.js | F2 | 2405 | 15.2 | 27.1 | 42.5 | 72,148 | 0.0% |
| actix-web-rest | Rust | F2 | 4809 | 8.1 | 10.3 | 13.0 | 144,256 | 0.0% |
| async-graphql | Rust | F2 | 5325 | 6.9 | 12.7 | 16.3 | 159,764 | 0.0% |
| mercurius | Node.js | F2 | 2750 | 13.2 | 24.5 | 30.5 | 82,513 | 0.0% |
| apollo-server | Node.js | F2 | 1874 | 19.6 | 35.2 | 44.3 | 56,224 | 0.0% |
| strawberry | Python | F2 | 962 | 40.0 | 67.1 | 74.0 | 28,854 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 8266 | 4.7 | 6.7 | 7.4 | 247,974 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 7955 | 4.9 | 6.8 | 7.5 | 238,662 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7479 | 5.2 | 7.3 | 8.2 | 224,368 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 7663 | 5.1 | 7.2 | 8.1 | 229,895 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4858 | 7.9 | 12.0 | 13.7 | 145,725 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4799 | 8.0 | 12.1 | 13.8 | 143,981 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2438 | 12.0 | 44.6 | 51.3 | 73,142 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2524 | 11.2 | 44.6 | 51.1 | 75,717 | 0.0% |
| hasura | Haskell | T1 | 814 | 48.5 | 65.2 | 71.0 | 24,419 | 0.0% |
| postgraphile | Node.js | T1 | 2078 | 17.4 | 31.4 | 59.3 | 62,328 | 0.0% |
| actix-web-rest | Rust | T1 | 47 | 867.1 | 957.4 | 1035.5 | 1,405 | 0.0% |
| async-graphql | Rust | T1 | 4332 | 9.0 | 14.4 | 16.8 | 129,962 | 0.0% |
| mercurius | Node.js | T1 | 1637 | 22.2 | 37.8 | 44.8 | 49,111 | 0.0% |
| apollo-server | Node.js | T1 | 1186 | 30.8 | 51.7 | 59.9 | 35,588 | 0.0% |
| strawberry | Python | T1 | 679 | 64.0 | 87.0 | 112.8 | 20,383 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 32 | 49.1 | 13296.1 | 29987.7 | 964 | 5.0% |
| fraiseql-tv-cache | Rust | MC1 | 96 | 204.6 | 1386.8 | 3938.1 | 2,881 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 97 | 203.5 | 1448.1 | 3101.5 | 2,899 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 102 | 213.4 | 1191.7 | 2599.5 | 3,060 | 0.0% |
| hasura | Haskell | MC1 | 477 | 83.5 | 96.7 | 101.3 | 14,319 | 0.0% |
| postgraphile | Node.js | MC1 | 1269 | 26.5 | 61.1 | 97.2 | 38,072 | 0.0% |
| async-graphql | Rust | MC1 | 1260 | 23.1 | 58.3 | 62.0 | 37,786 | 0.0% |
| mercurius | Node.js | MC1 | 1352 | 26.6 | 46.4 | 53.7 | 40,550 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 7688 | 5.1 | 7.1 | 7.9 | 230,630 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 7759 | 5.1 | 7.0 | 7.7 | 232,769 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 7005 | 5.6 | 7.8 | 8.6 | 210,163 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 7298 | 5.3 | 7.6 | 8.4 | 218,925 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 7399 | 5.3 | 7.4 | 8.2 | 221,981 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 7574 | 5.2 | 7.2 | 8.0 | 227,211 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 4596 | 6.8 | 29.3 | 37.4 | 137,873 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4890 | 6.6 | 26.7 | 34.7 | 146,709 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 32 | 48.2 | 12799.1 | 30001.6 | 948 | 5.1% |
| fraiseql-tv-cache | Rust | M1_APQ | 98 | 201.0 | 1364.1 | 3358.2 | 2,939 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 99 | 195.7 | 1468.0 | 3454.5 | 2,976 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 112 | 210.2 | 1078.3 | 1902.9 | 3,364 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1651 | 23.8 | 30.0 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1581 | 24.6 | 48.3 | 0.0% |
| mercurius | Node.js | 1486 | 17.9 | 74.7 | 0.0% |
| async-graphql | Rust | 1413 | 17.2 | 67.8 | 0.0% |
| strawberry | Python | 1000 | 38.5 | 73.7 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 8542 | 4.6 | 7.3 | 0.0% |
| fraiseql-tv-cache | Rust | 8242 | 4.7 | 7.4 | 0.0% |
| fraiseql-v-nocache | Rust | 7927 | 4.9 | 8.0 | 0.0% |
| fraiseql-v-cache | Rust | 7886 | 4.9 | 8.2 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2926 | 12.6 | 32.9 | 0.0% |
| hasura | Haskell | 1624 | 26.8 | 43.8 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 8542 | 4.6 | 7.3 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 8242 | 4.7 | 7.4 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 7927 | 4.9 | 8.0 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7886 | 4.9 | 8.2 |
| postgraphile | Node.js | graphql-schema-first | 2926 | 12.6 | 32.9 |
| actix-web-rest | Rust | rest | 1651 | 23.8 | 30.0 |
| hasura | Haskell | graphql-schema-first | 1624 | 26.8 | 43.8 |
| apollo-server | Node.js | graphql | 1581 | 24.6 | 48.3 |
| mercurius | Node.js | graphql | 1486 | 17.9 | 74.7 |
| async-graphql | Rust | graphql | 1413 | 17.2 | 67.8 |
| strawberry | Python | graphql | 1000 | 38.5 | 73.7 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 8542 | 99 | 0.0038 | 62 | 0.0062 | 123 | 0.0031 |
| fraiseql-tv-cache | 8242 | 96 | 0.0040 | 60 | 0.0064 | 119 | 0.0032 |
| fraiseql-v-nocache | 7927 | 92 | 0.0041 | 57 | 0.0066 | 114 | 0.0033 |
| fraiseql-v-cache | 7886 | 92 | 0.0041 | 57 | 0.0067 | 113 | 0.0034 |
| postgraphile | 2926 | 34 | 0.0112 | 21 | 0.0180 | 42 | 0.0090 |
| actix-web-rest | 1651 | 19 | 0.0198 | 12 | 0.0319 | 24 | 0.0160 |
| hasura | 1624 | 19 | 0.0202 | 12 | 0.0325 | 23 | 0.0163 |
| apollo-server | 1581 | 18 | 0.0207 | 11 | 0.0333 | 23 | 0.0167 |
| mercurius | 1486 | 17 | 0.0220 | 11 | 0.0355 | 21 | 0.0178 |
| async-graphql | 1413 | 16 | 0.0232 | 10 | 0.0373 | 20 | 0.0187 |
| strawberry | 1000 | 12 | 0.0327 | 7 | 0.0527 | 14 | 0.0265 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 118.4 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 138.9 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 12 | 93.2 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 107.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 122 | 116.5 |
| actix-web-rest | Rust | 681 | 4.0 | 12 | 6 | 82.4 |
| hasura | Haskell | — | — | — | 133 | 144.7 |
| apollo-server | Node.js | 744 | 7.5 | 120 | 56 | 119.1 |
| mercurius | Node.js | 444 | 9.2 | 104 | 51 | 98.9 |
| async-graphql | Rust | 693 | 4.5 | 12 | 10 | 124.8 |
| strawberry | Python | 1,771 | 12.6 | 136 | 180 | 167.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.9 |

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

> **Peak**: fraiseql-tv-cache 96 cycles/s (1 req) vs mercurius 1352 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 8,534 M/s: **~520,594 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.5M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.