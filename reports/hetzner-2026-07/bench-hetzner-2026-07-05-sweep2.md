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
| Run timestamp | 2026-07-05T02:27:08+00:00 |

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
| `tv_comment` | 700.9 MB | 322.2 MB | 1.62 GB |
| `tb_comment` | 294.7 MB | 82.2 MB | 377.0 MB |
| `tv_post` | 200.9 MB | 72.2 MB | 321.6 MB |
| `tb_post` | 133.6 MB | 19.7 MB | 153.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `tb_mutation_log` | 3.7 MB | 0.3 MB | 4.1 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 563.3 MB  
**Storage amplification**: 4.54× (TV adds 1.95 GB on top of the normalized 563.3 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 8448 | 4.6 | 6.6 | 7.3 | 253,439 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 8413 | 4.6 | 6.6 | 7.3 | 252,400 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8044 | 4.8 | 6.9 | 7.9 | 241,335 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7926 | 4.9 | 7.0 | 8.1 | 237,776 | 0.0% |
| hasura | Haskell | Q1 | 1385 | 28.6 | 36.5 | 44.1 | 41,559 | 0.0% |
| postgraphile | Node.js | Q1 | 2871 | 12.8 | 23.0 | 36.9 | 86,141 | 0.0% |
| actix-web-rest | Rust | Q1 | 1647 | 23.8 | 27.8 | 30.1 | 49,411 | 0.0% |
| async-graphql | Rust | Q1 | 1409 | 17.3 | 63.5 | 67.5 | 42,277 | 0.0% |
| mercurius | Node.js | Q1 | 1489 | 17.7 | 63.4 | 74.1 | 44,680 | 0.0% |
| apollo-server | Node.js | Q1 | 1579 | 24.9 | 36.3 | 44.5 | 47,360 | 0.0% |
| strawberry | Python | Q1 | 989 | 39.1 | 54.8 | 76.4 | 29,663 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 9565 | 4.1 | 5.7 | 6.4 | 286,957 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 9567 | 4.1 | 5.8 | 6.5 | 287,010 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7133 | 4.9 | 9.5 | 24.9 | 213,989 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7057 | 5.0 | 9.4 | 25.5 | 211,705 | 0.0% |
| hasura | Haskell | Q2 | 1457 | 27.1 | 32.9 | 42.9 | 43,702 | 0.0% |
| postgraphile | Node.js | Q2 | 3343 | 10.9 | 20.1 | 31.8 | 100,296 | 0.0% |
| actix-web-rest | Rust | Q2 | 11352 | 3.4 | 4.6 | 5.6 | 340,560 | 0.0% |
| async-graphql | Rust | Q2 | 5431 | 6.8 | 13.0 | 16.5 | 162,941 | 0.0% |
| mercurius | Node.js | Q2 | 4051 | 8.6 | 17.9 | 23.8 | 121,536 | 0.0% |
| apollo-server | Node.js | Q2 | 2982 | 12.7 | 21.0 | 26.3 | 89,463 | 0.0% |
| strawberry | Python | Q2 | 1423 | 27.0 | 34.2 | 56.6 | 42,691 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 8133 | 4.8 | 6.8 | 7.5 | 244,000 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 8139 | 4.8 | 6.8 | 7.6 | 244,159 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5116 | 6.2 | 26.2 | 34.1 | 153,473 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5106 | 6.2 | 26.8 | 34.7 | 153,182 | 0.0% |
| hasura | Haskell | Q2b | 1216 | 32.5 | 44.5 | 49.4 | 36,481 | 0.0% |
| postgraphile | Node.js | Q2b | 2616 | 14.1 | 25.6 | 38.2 | 78,494 | 0.0% |
| actix-web-rest | Rust | Q2b | 4734 | 8.0 | 11.7 | 14.2 | 142,028 | 0.0% |
| async-graphql | Rust | Q2b | 5198 | 7.2 | 12.8 | 16.6 | 155,944 | 0.0% |
| mercurius | Node.js | Q2b | 2968 | 12.3 | 22.6 | 28.1 | 89,032 | 0.0% |
| apollo-server | Node.js | Q2b | 1891 | 19.5 | 34.6 | 44.9 | 56,738 | 0.0% |
| strawberry | Python | Q2b | 1034 | 40.7 | 56.2 | 73.7 | 31,021 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 4148 | 8.1 | 26.1 | 34.3 | 124,436 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 4158 | 8.2 | 25.4 | 33.7 | 124,737 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1518 | 16.7 | 65.1 | 79.8 | 45,530 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1511 | 16.9 | 65.4 | 80.0 | 45,329 | 0.0% |
| hasura | Haskell | Q3 | 986 | 39.9 | 53.3 | 57.6 | 29,573 | 0.0% |
| postgraphile | Node.js | Q3 | 1487 | 23.8 | 49.7 | 68.9 | 44,607 | 0.0% |
| async-graphql | Rust | Q3 | 2141 | 17.7 | 34.1 | 41.1 | 64,218 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 10135 | 3.8 | 5.5 | 6.1 | 304,042 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 10101 | 3.9 | 5.4 | 6.0 | 303,016 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 9751 | 4.0 | 5.6 | 6.2 | 292,518 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 9740 | 4.0 | 5.6 | 6.2 | 292,197 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 9905 | 4.0 | 5.5 | 6.1 | 297,156 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 10041 | 3.9 | 5.5 | 6.1 | 301,216 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 9710 | 4.0 | 5.6 | 6.1 | 291,286 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 9682 | 4.0 | 5.6 | 6.2 | 290,451 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 96 | 206.5 | 1375.7 | 3652.0 | 2,877 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 101 | 208.3 | 1296.7 | 2458.9 | 3,034 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 98 | 183.8 | 1591.9 | 3989.9 | 2,947 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 102 | 179.4 | 1411.2 | 2483.9 | 3,054 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 99 | 175.8 | 1483.4 | 3197.8 | 2,969 | 0.0% |
| hasura | Haskell | M1 | 1515 | 22.4 | 53.6 | 64.6 | 45,447 | 0.0% |
| postgraphile | Node.js | M1 | 2901 | 11.4 | 22.7 | 64.2 | 87,035 | 0.0% |
| actix-web-rest | Rust | M1 | 2476 | 15.7 | 18.6 | 22.8 | 74,267 | 0.0% |
| async-graphql | Rust | M1 | 7878 | 5.0 | 6.7 | 7.3 | 236,355 | 0.0% |
| mercurius | Node.js | M1 | 3868 | 9.4 | 16.5 | 24.8 | 116,054 | 0.0% |
| apollo-server | Node.js | M1 | 2454 | 15.1 | 26.0 | 35.6 | 73,611 | 0.0% |
| strawberry | Python | M1 | 1329 | 28.9 | 35.4 | 61.4 | 39,871 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 8552 | 4.6 | 6.4 | 7.4 | 256,564 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 9175 | 4.2 | 6.0 | 6.7 | 275,246 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 9081 | 4.3 | 6.0 | 6.7 | 272,430 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 5858 | 5.3 | 25.4 | 33.8 | 175,746 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 5784 | 5.5 | 23.4 | 33.8 | 173,535 | 0.0% |
| hasura | Haskell | F1 | 1299 | 30.2 | 40.7 | 45.9 | 38,970 | 0.0% |
| postgraphile | Node.js | F1 | 3140 | 11.8 | 19.9 | 33.3 | 94,205 | 0.0% |
| actix-web-rest | Rust | F1 | 10799 | 3.6 | 4.7 | 5.9 | 323,965 | 0.0% |
| async-graphql | Rust | F1 | 6713 | 5.8 | 8.7 | 10.0 | 201,377 | 0.0% |
| mercurius | Node.js | F1 | 4466 | 8.3 | 14.6 | 18.9 | 133,968 | 0.0% |
| apollo-server | Node.js | F1 | 2929 | 12.9 | 21.6 | 27.9 | 87,872 | 0.0% |
| strawberry | Python | F1 | 1319 | 29.0 | 38.2 | 60.2 | 39,562 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 7730 | 5.0 | 7.1 | 7.9 | 231,903 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 7739 | 5.0 | 7.1 | 7.9 | 232,177 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4320 | 6.8 | 34.7 | 40.6 | 129,594 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4347 | 6.7 | 34.5 | 40.3 | 130,405 | 0.0% |
| hasura | Haskell | F2 | 1102 | 35.5 | 48.6 | 52.2 | 33,072 | 0.0% |
| postgraphile | Node.js | F2 | 2427 | 15.0 | 27.5 | 40.6 | 72,817 | 0.0% |
| actix-web-rest | Rust | F2 | 4636 | 8.3 | 11.6 | 13.7 | 139,068 | 0.0% |
| async-graphql | Rust | F2 | 5245 | 7.1 | 12.6 | 15.9 | 157,340 | 0.0% |
| mercurius | Node.js | F2 | 3158 | 11.6 | 20.4 | 25.7 | 94,744 | 0.0% |
| apollo-server | Node.js | F2 | 1898 | 19.3 | 34.7 | 43.3 | 56,928 | 0.0% |
| strawberry | Python | F2 | 971 | 40.1 | 63.9 | 70.8 | 29,129 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 8149 | 4.8 | 6.7 | 7.5 | 244,482 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 8311 | 4.7 | 6.6 | 7.3 | 249,333 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7891 | 4.9 | 7.0 | 7.9 | 236,722 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 7750 | 5.0 | 7.1 | 8.0 | 232,487 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4965 | 7.7 | 11.7 | 13.5 | 148,940 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4939 | 7.8 | 11.8 | 13.5 | 148,173 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2529 | 11.3 | 44.3 | 50.9 | 75,866 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2522 | 11.2 | 44.8 | 51.1 | 75,645 | 0.0% |
| hasura | Haskell | T1 | 795 | 50.8 | 66.0 | 72.1 | 23,841 | 0.0% |
| postgraphile | Node.js | T1 | 2166 | 16.5 | 30.8 | 62.3 | 64,995 | 0.0% |
| actix-web-rest | Rust | T1 | 49 | 823.8 | 912.5 | 971.4 | 1,467 | 0.0% |
| async-graphql | Rust | T1 | 5111 | 7.6 | 11.5 | 14.0 | 153,319 | 0.0% |
| mercurius | Node.js | T1 | 1673 | 21.8 | 36.6 | 44.0 | 50,200 | 0.0% |
| apollo-server | Node.js | T1 | 1181 | 31.0 | 51.3 | 60.6 | 35,423 | 0.0% |
| strawberry | Python | T1 | 671 | 65.8 | 84.8 | 115.6 | 20,136 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 103 | 206.4 | 1243.9 | 2584.0 | 3,077 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 103 | 209.3 | 1206.2 | 2445.5 | 3,101 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 98 | 183.2 | 1480.9 | 3618.6 | 2,950 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 100 | 196.9 | 1452.8 | 2982.8 | 2,991 | 0.0% |
| hasura | Haskell | MC1 | 476 | 83.8 | 98.3 | 104.4 | 14,284 | 0.0% |
| postgraphile | Node.js | MC1 | 1286 | 26.2 | 58.7 | 94.6 | 38,566 | 0.0% |
| async-graphql | Rust | MC1 | 1250 | 23.5 | 57.9 | 61.7 | 37,486 | 0.0% |
| mercurius | Node.js | MC1 | 1322 | 27.1 | 46.9 | 55.5 | 39,652 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 7944 | 4.9 | 6.9 | 7.6 | 238,334 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 7964 | 4.9 | 6.8 | 7.5 | 238,908 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 7567 | 5.2 | 7.2 | 8.1 | 227,005 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 7279 | 5.4 | 7.5 | 8.3 | 218,383 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 7959 | 4.9 | 6.9 | 7.7 | 238,775 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 7790 | 5.0 | 7.0 | 7.7 | 233,686 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 4917 | 6.4 | 27.1 | 35.1 | 147,521 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4914 | 6.5 | 26.5 | 34.2 | 147,423 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 103 | 202.8 | 1327.3 | 2623.9 | 3,084 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 103 | 212.0 | 1259.8 | 2250.2 | 3,101 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 101 | 195.0 | 1409.7 | 2961.7 | 3,035 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 102 | 189.2 | 1468.9 | 2777.4 | 3,057 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1647 | 23.8 | 30.1 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1579 | 24.9 | 44.5 | 0.0% |
| mercurius | Node.js | 1489 | 17.7 | 74.1 | 0.0% |
| async-graphql | Rust | 1409 | 17.3 | 67.5 | 0.0% |
| strawberry | Python | 989 | 39.1 | 76.4 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 8448 | 4.6 | 7.3 | 0.0% |
| fraiseql-tv-cache | Rust | 8413 | 4.6 | 7.3 | 0.0% |
| fraiseql-v-nocache | Rust | 8044 | 4.8 | 7.9 | 0.0% |
| fraiseql-v-cache | Rust | 7926 | 4.9 | 8.1 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2871 | 12.8 | 36.9 | 0.0% |
| hasura | Haskell | 1385 | 28.6 | 44.1 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 8448 | 4.6 | 7.3 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 8413 | 4.6 | 7.3 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8044 | 4.8 | 7.9 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7926 | 4.9 | 8.1 |
| postgraphile | Node.js | graphql-schema-first | 2871 | 12.8 | 36.9 |
| actix-web-rest | Rust | rest | 1647 | 23.8 | 30.1 |
| apollo-server | Node.js | graphql | 1579 | 24.9 | 44.5 |
| mercurius | Node.js | graphql | 1489 | 17.7 | 74.1 |
| async-graphql | Rust | graphql | 1409 | 17.3 | 67.5 |
| hasura | Haskell | graphql-schema-first | 1385 | 28.6 | 44.1 |
| strawberry | Python | graphql | 989 | 39.1 | 76.4 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 8448 | 98 | 0.0039 | 61 | 0.0062 | 122 | 0.0031 |
| fraiseql-tv-cache | 8413 | 98 | 0.0039 | 61 | 0.0063 | 121 | 0.0031 |
| fraiseql-v-nocache | 8044 | 94 | 0.0041 | 58 | 0.0066 | 116 | 0.0033 |
| fraiseql-v-cache | 7926 | 92 | 0.0041 | 57 | 0.0066 | 114 | 0.0033 |
| postgraphile | 2871 | 33 | 0.0114 | 21 | 0.0184 | 41 | 0.0092 |
| actix-web-rest | 1647 | 19 | 0.0199 | 12 | 0.0320 | 24 | 0.0161 |
| apollo-server | 1579 | 18 | 0.0207 | 11 | 0.0334 | 23 | 0.0167 |
| mercurius | 1489 | 17 | 0.0220 | 11 | 0.0354 | 21 | 0.0178 |
| async-graphql | 1409 | 16 | 0.0232 | 10 | 0.0374 | 20 | 0.0188 |
| hasura | 1385 | 16 | 0.0236 | 10 | 0.0380 | 20 | 0.0191 |
| strawberry | 989 | 11 | 0.0331 | 7 | 0.0533 | 14 | 0.0267 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 137.0 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 139.7 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 12 | 93.5 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 105.9 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 122 | 119.1 |
| actix-web-rest | Rust | 681 | 4.0 | 12 | 5 | 84.0 |
| apollo-server | Node.js | 744 | 7.5 | 120 | 57 | 120.0 |
| mercurius | Node.js | 444 | 9.2 | 104 | 49 | 99.2 |
| async-graphql | Rust | 693 | 4.5 | 12 | 10 | 123.9 |
| hasura | Haskell | — | — | — | 133 | 142.3 |
| strawberry | Python | 1,771 | 12.6 | 136 | 184 | 166.9 |
| fraiseql-tv-audit | Rust | — | — | 43 | 9 | 2.6 |

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

> **Peak**: fraiseql-tv-cache 103 cycles/s (1 req) vs mercurius 1322 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 7,878 M/s: **~480,588 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.5M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.