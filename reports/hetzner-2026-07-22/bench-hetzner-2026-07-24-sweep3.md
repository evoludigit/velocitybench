# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-24  
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
| Run timestamp | 2026-07-24T20:39:15+00:00 |

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
| `tv_comment` | 768.4 MB | 278.2 MB | 1.02 GB |
| `tb_comment` | 294.4 MB | 81.9 MB | 376.4 MB |
| `tv_post` | 210.6 MB | 68.7 MB | 310.9 MB |
| `tb_post` | 133.6 MB | 20.4 MB | 154.1 MB |
| `tb_mutation_log` | 73.2 MB | 5.7 MB | 79.0 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.4 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 638.6 MB  
**Storage amplification**: 3.15× (TV adds 1.34 GB on top of the normalized 638.6 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9760 | 4.1 | 5.2 | 5.8 | 292,789 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9873 | 4.0 | 5.1 | 5.7 | 296,183 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8866 | 4.4 | 5.9 | 7.0 | 265,982 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8833 | 4.5 | 5.8 | 6.6 | 264,999 | 0.0% |
| hasura | Haskell | Q1 | 3636 | 10.6 | 17.2 | 19.5 | 109,089 | 0.0% |
| postgraphile | Node.js | Q1 | 3419 | 11.3 | 17.2 | 21.6 | 102,582 | 0.0% |
| actix-web-rest | Rust | Q1 | 1675 | 23.4 | 27.3 | 29.4 | 50,250 | 0.0% |
| async-graphql | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1 | 1450 | 18.0 | 65.0 | 77.0 | 43,498 | 0.0% |
| apollo-server | Node.js | Q1 | 1566 | 24.5 | 41.7 | 51.2 | 46,990 | 0.0% |
| strawberry | Python | Q1 | 990 | 39.0 | 49.9 | 76.8 | 29,707 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11100 | 3.6 | 4.6 | 5.2 | 333,014 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11263 | 3.5 | 4.5 | 5.1 | 337,876 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7426 | 4.5 | 15.6 | 25.8 | 222,794 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7410 | 4.5 | 16.4 | 25.8 | 222,306 | 0.0% |
| hasura | Haskell | Q2 | 3886 | 9.9 | 15.5 | 18.9 | 116,576 | 0.0% |
| postgraphile | Node.js | Q2 | 3865 | 10.0 | 15.1 | 19.4 | 115,958 | 0.0% |
| actix-web-rest | Rust | Q2 | 14069 | 2.8 | 3.3 | 3.7 | 422,059 | 0.0% |
| async-graphql | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2 | 4875 | 7.9 | 12.0 | 14.8 | 146,242 | 0.0% |
| apollo-server | Node.js | Q2 | 3162 | 12.3 | 18.2 | 21.3 | 94,868 | 0.0% |
| strawberry | Python | Q2 | 1401 | 27.5 | 32.3 | 61.8 | 42,028 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9233 | 4.3 | 5.5 | 6.1 | 276,991 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9296 | 4.3 | 5.5 | 6.1 | 278,870 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5304 | 5.8 | 27.4 | 33.6 | 159,126 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5322 | 5.8 | 27.1 | 33.5 | 159,669 | 0.0% |
| hasura | Haskell | Q2b | 3190 | 12.0 | 19.0 | 21.1 | 95,714 | 0.0% |
| postgraphile | Node.js | Q2b | 2982 | 12.9 | 19.1 | 24.1 | 89,452 | 0.0% |
| actix-web-rest | Rust | Q2b | 4944 | 8.1 | 9.0 | 9.5 | 148,320 | 0.0% |
| async-graphql | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b | 3486 | 11.0 | 16.4 | 19.9 | 104,595 | 0.0% |
| apollo-server | Node.js | Q2b | 2194 | 17.6 | 26.8 | 31.8 | 65,825 | 0.0% |
| strawberry | Python | Q2b | 1009 | 38.1 | 66.6 | 75.5 | 30,281 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7258 | 5.5 | 7.0 | 7.8 | 217,731 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7366 | 5.4 | 6.9 | 7.6 | 220,986 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3412 | 8.5 | 37.6 | 43.1 | 102,364 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3399 | 8.6 | 37.7 | 43.1 | 101,979 | 0.0% |
| hasura | Haskell | Q3 | 2621 | 14.7 | 22.0 | 23.9 | 78,619 | 0.0% |
| postgraphile | Node.js | Q3 | 1751 | 22.1 | 33.3 | 39.2 | 52,530 | 0.0% |
| actix-web-rest | Rust | Q3 | 4301 | 9.3 | 10.3 | 11.0 | 129,027 | 0.0% |
| async-graphql | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q3 | 1033 | 38.6 | 50.0 | 53.3 | 30,978 | 0.0% |
| apollo-server | Node.js | Q3 | 784 | 50.6 | 64.6 | 69.1 | 23,518 | 0.0% |
| strawberry | Python | Q3 | 530 | 81.5 | 124.6 | 141.4 | 15,896 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11697 | 3.4 | 4.3 | 4.8 | 350,901 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11725 | 3.4 | 4.3 | 4.8 | 351,743 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11293 | 3.5 | 4.5 | 4.9 | 338,803 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11235 | 3.5 | 4.5 | 4.9 | 337,062 | 0.0% |
| hasura | Haskell | C3 | 3465 | 11.1 | 17.6 | 20.4 | 103,948 | 0.0% |
| postgraphile | Node.js | C3 | 4062 | 9.5 | 14.1 | 18.3 | 121,860 | 0.0% |
| actix-web-rest | Rust | C3 | 18619 | 2.1 | 2.5 | 2.7 | 558,583 | 0.0% |
| async-graphql | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | C3 | 7314 | 5.2 | 8.1 | 10.8 | 219,433 | 0.0% |
| apollo-server | Node.js | C3 | 4112 | 9.4 | 13.9 | 16.8 | 123,348 | 0.0% |
| strawberry | Python | C3 | 1575 | 23.6 | 37.3 | 61.4 | 47,261 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11593 | 3.4 | 4.3 | 4.8 | 347,804 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11660 | 3.4 | 4.3 | 4.8 | 349,787 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11350 | 3.5 | 4.4 | 4.9 | 340,511 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11302 | 3.5 | 4.5 | 4.9 | 339,058 | 0.0% |
| hasura | Haskell | HC3 | 3485 | 11.0 | 17.4 | 19.6 | 104,544 | 0.0% |
| postgraphile | Node.js | HC3 | 4215 | 9.1 | 13.6 | 17.7 | 126,437 | 0.0% |
| actix-web-rest | Rust | HC3 | 18495 | 2.1 | 2.5 | 2.9 | 554,861 | 0.0% |
| async-graphql | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | HC3 | 7218 | 5.3 | 8.2 | 10.8 | 216,530 | 0.0% |
| apollo-server | Node.js | HC3 | 4261 | 9.0 | 13.7 | 16.5 | 127,820 | 0.0% |
| strawberry | Python | HC3 | 1569 | 10.2 | 48.0 | 78.6 | 47,074 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1117 | 20.3 | 92.5 | 187.2 | 33,522 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1077 | 21.2 | 94.2 | 193.2 | 32,298 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1123 | 20.2 | 90.6 | 194.0 | 33,699 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1111 | 20.8 | 90.5 | 188.3 | 33,341 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1061 | 21.6 | 95.1 | 194.8 | 31,826 | 0.0% |
| hasura | Haskell | M1 | 1958 | 19.3 | 26.8 | 31.6 | 58,735 | 0.0% |
| postgraphile | Node.js | M1 | 3503 | 10.6 | 16.5 | 21.6 | 105,086 | 0.0% |
| actix-web-rest | Rust | M1 | 5291 | 7.5 | 8.3 | 10.5 | 158,735 | 0.0% |
| async-graphql | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1 | 4364 | 8.8 | 12.4 | 16.6 | 130,930 | 0.0% |
| apollo-server | Node.js | M1 | 2750 | 13.8 | 19.6 | 24.4 | 82,490 | 0.0% |
| strawberry | Python | M1 | 1316 | 29.0 | 39.0 | 70.3 | 39,486 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10016 | 4.0 | 5.3 | 5.9 | 300,490 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10213 | 3.9 | 5.2 | 5.8 | 306,403 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10575 | 3.8 | 4.8 | 5.4 | 317,242 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10557 | 3.8 | 4.8 | 5.4 | 316,711 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6901 | 4.7 | 18.6 | 27.9 | 207,033 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6725 | 4.7 | 21.9 | 30.0 | 201,751 | 0.0% |
| hasura | Haskell | F1 | 3462 | 11.0 | 17.9 | 20.3 | 103,850 | 0.0% |
| postgraphile | Node.js | F1 | 3781 | 10.1 | 15.6 | 20.4 | 113,417 | 0.0% |
| actix-web-rest | Rust | F1 | 13308 | 2.9 | 3.5 | 3.8 | 399,227 | 0.0% |
| async-graphql | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F1 | 4759 | 8.1 | 12.2 | 14.9 | 142,779 | 0.0% |
| apollo-server | Node.js | F1 | 3102 | 12.5 | 18.6 | 21.7 | 93,063 | 0.0% |
| strawberry | Python | F1 | 1270 | 30.1 | 36.3 | 68.4 | 38,097 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8852 | 4.5 | 5.7 | 6.3 | 265,559 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8831 | 4.5 | 5.7 | 6.3 | 264,926 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 5184 | 6.0 | 27.9 | 34.2 | 155,506 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 5174 | 5.9 | 28.4 | 34.5 | 155,215 | 0.0% |
| hasura | Haskell | F2 | 2882 | 13.3 | 20.7 | 22.6 | 86,462 | 0.0% |
| postgraphile | Node.js | F2 | 2826 | 13.6 | 20.6 | 25.9 | 84,772 | 0.0% |
| actix-web-rest | Rust | F2 | 4776 | 8.3 | 9.4 | 9.9 | 143,282 | 0.0% |
| async-graphql | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F2 | 3392 | 11.3 | 16.8 | 20.3 | 101,751 | 0.0% |
| apollo-server | Node.js | F2 | 2237 | 17.2 | 26.6 | 31.7 | 67,107 | 0.0% |
| strawberry | Python | F2 | 941 | 40.6 | 72.9 | 81.1 | 28,233 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9468 | 4.2 | 5.3 | 5.9 | 284,032 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9476 | 4.2 | 5.3 | 5.9 | 284,287 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8477 | 4.7 | 6.0 | 6.7 | 254,301 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8723 | 4.6 | 5.9 | 6.5 | 261,679 | 0.0% |
| hasura | Haskell | F3 | 3609 | 10.7 | 16.9 | 19.7 | 108,273 | 0.0% |
| postgraphile | Node.js | F3 | 3374 | 11.4 | 17.5 | 22.4 | 101,207 | 0.0% |
| actix-web-rest | Rust | F3 | 1616 | 24.3 | 28.4 | 30.2 | 48,472 | 0.0% |
| async-graphql | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F3 | 1461 | 17.8 | 64.5 | 76.8 | 43,829 | 0.0% |
| apollo-server | Node.js | F3 | 1568 | 24.6 | 40.6 | 50.1 | 47,037 | 0.0% |
| strawberry | Python | F3 | 969 | 17.4 | 81.2 | 112.1 | 29,082 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5801 | 6.8 | 8.9 | 9.9 | 174,028 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5810 | 6.8 | 8.9 | 9.9 | 174,307 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3346 | 9.4 | 32.8 | 38.1 | 100,386 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3337 | 9.3 | 33.8 | 38.7 | 100,106 | 0.0% |
| hasura | Haskell | T1 | 2161 | 17.7 | 26.7 | 30.6 | 64,823 | 0.0% |
| postgraphile | Node.js | T1 | 2459 | 15.6 | 23.7 | 30.5 | 73,771 | 0.0% |
| actix-web-rest | Rust | T1 | 3302 | 12.0 | 13.4 | 14.1 | 99,053 | 0.0% |
| async-graphql | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | T1 | 1972 | 19.4 | 26.3 | 30.1 | 59,173 | 0.0% |
| apollo-server | Node.js | T1 | 1461 | 26.2 | 35.1 | 39.7 | 43,823 | 0.0% |
| strawberry | Python | T1 | 668 | 60.7 | 84.9 | 112.9 | 20,027 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1085 | 21.0 | 92.8 | 196.0 | 32,545 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1085 | 20.9 | 92.9 | 198.6 | 32,556 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1106 | 20.5 | 92.3 | 189.3 | 33,184 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1090 | 20.7 | 92.7 | 197.5 | 32,708 | 0.0% |
| hasura | Haskell | MC1 | 1200 | 32.2 | 41.0 | 48.1 | 36,011 | 0.0% |
| postgraphile | Node.js | MC1 | 1431 | 26.3 | 38.7 | 49.8 | 42,927 | 0.0% |
| actix-web-rest | Rust | MC1 | 1353 | 28.9 | 33.2 | 35.7 | 40,601 | 0.0% |
| async-graphql | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | MC1 | 1341 | 27.3 | 46.7 | 53.9 | 40,231 | 0.0% |
| apollo-server | Node.js | MC1 | 1073 | 36.9 | 47.8 | 54.8 | 32,176 | 0.0% |
| strawberry | Python | MC1 | 563 | 85.4 | 136.1 | 149.0 | 16,890 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9393 | 4.2 | 5.4 | 5.9 | 281,797 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9206 | 4.3 | 5.5 | 6.0 | 276,173 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8372 | 4.7 | 6.1 | 6.8 | 251,146 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8465 | 4.7 | 6.0 | 6.7 | 253,947 | 0.0% |
| async-graphql | Rust | Q1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1_APQ | 1458 | 18.2 | 63.8 | 75.0 | 43,733 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1578 | 24.5 | 40.0 | 50.2 | 47,331 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9012 | 4.4 | 5.6 | 6.1 | 270,358 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9028 | 4.4 | 5.6 | 6.2 | 270,853 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5091 | 6.0 | 28.4 | 34.6 | 152,743 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5116 | 5.9 | 29.0 | 35.1 | 153,494 | 0.0% |
| async-graphql | Rust | Q2b_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b_APQ | 3391 | 11.3 | 16.9 | 20.5 | 101,731 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 2245 | 17.1 | 26.5 | 31.7 | 67,337 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1100 | 21.1 | 91.3 | 181.8 | 33,006 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1100 | 20.6 | 92.3 | 191.8 | 32,994 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1098 | 20.2 | 93.3 | 198.3 | 32,935 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1103 | 20.4 | 91.8 | 194.5 | 33,102 | 0.0% |
| async-graphql | Rust | M1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1_APQ | 4328 | 8.9 | 12.5 | 16.3 | 129,850 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2750 | 13.8 | 19.5 | 24.3 | 82,493 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1675 | 23.4 | 29.4 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1566 | 24.5 | 51.2 | 0.0% |
| mercurius | Node.js | 1450 | 18.0 | 77.0 | 0.0% |
| strawberry | Python | 990 | 39.0 | 76.8 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9873 | 4.0 | 5.7 | 0.0% |
| fraiseql-tv | Rust | 9760 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-nocache | Rust | 8866 | 4.4 | 7.0 | 0.0% |
| fraiseql-v-cache | Rust | 8833 | 4.5 | 6.6 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 3636 | 10.6 | 19.5 | 0.0% |
| postgraphile | Node.js | 3419 | 11.3 | 21.6 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9873 | 4.0 | 5.7 |
| fraiseql-tv | Rust | graphql-precomputed | 9760 | 4.1 | 5.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8866 | 4.4 | 7.0 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8833 | 4.5 | 6.6 |
| hasura | Haskell | graphql-schema-first | 3636 | 10.6 | 19.5 |
| postgraphile | Node.js | graphql-schema-first | 3419 | 11.3 | 21.6 |
| actix-web-rest | Rust | rest | 1675 | 23.4 | 29.4 |
| apollo-server | Node.js | graphql | 1566 | 24.5 | 51.2 |
| mercurius | Node.js | graphql | 1450 | 18.0 | 77.0 |
| strawberry | Python | graphql | 990 | 39.0 | 76.8 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9873 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-tv | 9760 | 113 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-v-nocache | 8866 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| fraiseql-v-cache | 8833 | 103 | 0.0037 | 64 | 0.0060 | 127 | 0.0030 |
| hasura | 3636 | 42 | 0.0090 | 26 | 0.0145 | 52 | 0.0073 |
| postgraphile | 3419 | 40 | 0.0096 | 25 | 0.0154 | 49 | 0.0077 |
| actix-web-rest | 1675 | 19 | 0.0195 | 12 | 0.0315 | 24 | 0.0158 |
| apollo-server | 1566 | 18 | 0.0209 | 11 | 0.0336 | 23 | 0.0169 |
| mercurius | 1450 | 17 | 0.0226 | 10 | 0.0363 | 21 | 0.0182 |
| strawberry | 990 | 12 | 0.0330 | 7 | 0.0532 | 14 | 0.0267 |

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
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 114.4 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 123.4 |
| hasura | Haskell | — | — | — | 133 | 161.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 124 | 118.9 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 6 | 105.0 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 72 | 111.2 |
| mercurius | Node.js | 464 | 8.8 | 104 | 56 | 105.7 |
| strawberry | Python | 1,812 | 12.7 | 136 | 181 | 175.3 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 18.1 |

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

> **Peak**: fraiseql-tv-cache 1085 cycles/s (1 req) vs postgraphile 1431 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 5,291 M/s: **~58,202 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.