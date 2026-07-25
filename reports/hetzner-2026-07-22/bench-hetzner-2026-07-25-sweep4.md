# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-25  
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
| Run timestamp | 2026-07-25T16:29:13+00:00 |

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
| `tv_comment` | 769.3 MB | 278.1 MB | 1.02 GB |
| `tb_comment` | 294.9 MB | 82.5 MB | 377.5 MB |
| `tv_post` | 210.9 MB | 68.7 MB | 311.3 MB |
| `tb_post` | 133.7 MB | 19.6 MB | 153.3 MB |
| `tb_mutation_log` | 110.3 MB | 8.6 MB | 119.0 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.5 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 678.7 MB  
**Storage amplification**: 3.02× (TV adds 1.34 GB on top of the normalized 678.7 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9783 | 4.1 | 5.2 | 5.8 | 293,476 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9835 | 4.0 | 5.2 | 5.8 | 295,037 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8954 | 4.4 | 5.8 | 6.9 | 268,619 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8875 | 4.5 | 5.9 | 6.8 | 266,254 | 0.0% |
| hasura | Haskell | Q1 | 1463 | 27.0 | 36.0 | 42.6 | 43,890 | 0.0% |
| postgraphile | Node.js | Q1 | 3237 | 11.7 | 19.4 | 26.2 | 97,119 | 0.0% |
| actix-web-rest | Rust | Q1 | 1656 | 23.6 | 28.1 | 30.3 | 49,667 | 0.0% |
| async-graphql | Rust | Q1 | 1390 | 17.6 | 63.2 | 67.2 | 41,703 | 0.0% |
| mercurius | Node.js | Q1 | 1458 | 17.8 | 64.6 | 76.4 | 43,749 | 0.0% |
| apollo-server | Node.js | Q1 | 1571 | 24.6 | 40.0 | 49.7 | 47,119 | 0.0% |
| strawberry | Python | Q1 | 976 | 39.4 | 52.1 | 78.9 | 29,286 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 10958 | 3.6 | 4.7 | 5.2 | 328,753 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 10976 | 3.6 | 4.7 | 5.2 | 329,291 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7295 | 4.5 | 16.0 | 26.5 | 218,862 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7205 | 4.6 | 15.8 | 26.2 | 216,156 | 0.0% |
| hasura | Haskell | Q2 | 1623 | 24.7 | 35.1 | 43.1 | 48,702 | 0.0% |
| postgraphile | Node.js | Q2 | 3548 | 10.4 | 18.0 | 27.4 | 106,435 | 0.0% |
| actix-web-rest | Rust | Q2 | 12219 | 3.1 | 4.2 | 5.8 | 366,573 | 0.0% |
| async-graphql | Rust | Q2 | 8837 | 4.5 | 6.3 | 7.2 | 265,109 | 0.0% |
| mercurius | Node.js | Q2 | 4379 | 8.4 | 15.3 | 19.8 | 131,373 | 0.0% |
| apollo-server | Node.js | Q2 | 3016 | 12.7 | 19.8 | 25.2 | 90,465 | 0.0% |
| strawberry | Python | Q2 | 1398 | 27.9 | 38.2 | 65.0 | 41,951 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9119 | 4.4 | 5.6 | 6.2 | 273,578 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9044 | 4.4 | 5.6 | 6.2 | 271,324 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5436 | 5.8 | 26.6 | 33.0 | 163,068 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5351 | 5.8 | 26.3 | 32.9 | 160,531 | 0.0% |
| hasura | Haskell | Q2b | 1329 | 30.4 | 41.2 | 47.5 | 39,871 | 0.0% |
| postgraphile | Node.js | Q2b | 2750 | 13.7 | 22.5 | 30.9 | 82,514 | 0.0% |
| actix-web-rest | Rust | Q2b | 5123 | 7.7 | 9.1 | 11.5 | 153,691 | 0.0% |
| async-graphql | Rust | Q2b | 6115 | 6.2 | 10.2 | 13.5 | 183,454 | 0.0% |
| mercurius | Node.js | Q2b | 3042 | 12.1 | 20.9 | 26.8 | 91,252 | 0.0% |
| apollo-server | Node.js | Q2b | 1934 | 19.5 | 32.2 | 39.5 | 58,024 | 0.0% |
| strawberry | Python | Q2b | 981 | 39.4 | 62.3 | 77.3 | 29,416 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7258 | 5.5 | 7.0 | 7.8 | 217,726 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7189 | 5.5 | 7.1 | 7.9 | 215,680 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3458 | 8.4 | 37.4 | 42.6 | 103,738 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3443 | 8.6 | 36.6 | 41.9 | 103,280 | 0.0% |
| hasura | Haskell | Q3 | 1163 | 33.3 | 49.1 | 54.1 | 34,879 | 0.0% |
| postgraphile | Node.js | Q3 | 1585 | 23.3 | 41.9 | 54.0 | 47,548 | 0.0% |
| actix-web-rest | Rust | Q3 | 4299 | 9.2 | 10.2 | 11.0 | 128,978 | 0.0% |
| async-graphql | Rust | Q3 | 2461 | 15.1 | 29.4 | 36.5 | 73,842 | 0.0% |
| mercurius | Node.js | Q3 | 904 | 43.2 | 62.0 | 70.7 | 27,112 | 0.0% |
| apollo-server | Node.js | Q3 | 655 | 60.1 | 82.8 | 95.4 | 19,648 | 0.0% |
| strawberry | Python | Q3 | 516 | 73.8 | 112.2 | 138.5 | 15,484 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11467 | 3.5 | 4.4 | 4.8 | 343,998 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11732 | 3.4 | 4.3 | 4.8 | 351,962 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11184 | 3.6 | 4.5 | 4.9 | 335,519 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11103 | 3.6 | 4.5 | 5.0 | 333,096 | 0.0% |
| hasura | Haskell | C3 | 1439 | 27.6 | 39.3 | 44.5 | 43,171 | 0.0% |
| postgraphile | Node.js | C3 | 3800 | 9.7 | 16.9 | 29.2 | 113,985 | 0.0% |
| actix-web-rest | Rust | C3 | 16151 | 2.4 | 3.0 | 3.8 | 484,518 | 0.0% |
| async-graphql | Rust | C3 | 15639 | 2.5 | 3.5 | 4.1 | 469,165 | 0.0% |
| mercurius | Node.js | C3 | 6666 | 5.6 | 9.6 | 12.8 | 199,991 | 0.0% |
| apollo-server | Node.js | C3 | 3730 | 10.1 | 16.9 | 21.4 | 111,899 | 0.0% |
| strawberry | Python | C3 | 1531 | 25.4 | 44.0 | 66.0 | 45,932 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11422 | 3.5 | 4.4 | 4.9 | 342,668 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11613 | 3.4 | 4.3 | 4.8 | 348,386 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11241 | 3.5 | 4.5 | 4.9 | 337,235 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11149 | 3.6 | 4.5 | 5.0 | 334,482 | 0.0% |
| hasura | Haskell | HC3 | 1429 | 27.5 | 37.1 | 43.1 | 42,882 | 0.0% |
| postgraphile | Node.js | HC3 | 3896 | 9.5 | 16.6 | 24.4 | 116,886 | 0.0% |
| actix-web-rest | Rust | HC3 | 16112 | 2.4 | 3.0 | 3.7 | 483,365 | 0.0% |
| async-graphql | Rust | HC3 | 15818 | 2.5 | 3.4 | 4.0 | 474,548 | 0.0% |
| mercurius | Node.js | HC3 | 6100 | 5.9 | 11.4 | 15.5 | 182,995 | 0.0% |
| apollo-server | Node.js | HC3 | 3852 | 9.6 | 16.9 | 21.8 | 115,557 | 0.0% |
| strawberry | Python | HC3 | 1526 | 24.8 | 42.2 | 66.3 | 45,773 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1113 | 20.7 | 90.1 | 181.1 | 33,400 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1100 | 20.6 | 92.4 | 190.6 | 32,986 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1115 | 20.7 | 91.7 | 188.9 | 33,451 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1097 | 20.7 | 91.9 | 193.9 | 32,898 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1067 | 21.9 | 93.7 | 190.5 | 32,014 | 0.0% |
| hasura | Haskell | M1 | 1912 | 19.6 | 27.9 | 34.9 | 57,358 | 0.0% |
| postgraphile | Node.js | M1 | 2967 | 11.4 | 21.2 | 52.6 | 89,016 | 0.0% |
| actix-web-rest | Rust | M1 | 2821 | 14.3 | 17.3 | 18.1 | 84,623 | 0.0% |
| async-graphql | Rust | M1 | 9293 | 4.3 | 5.2 | 5.8 | 278,796 | 0.0% |
| mercurius | Node.js | M1 | 3976 | 9.5 | 16.1 | 22.8 | 119,279 | 0.0% |
| apollo-server | Node.js | M1 | 2544 | 14.6 | 23.6 | 33.4 | 76,306 | 0.0% |
| strawberry | Python | M1 | 1268 | 30.5 | 41.7 | 69.0 | 38,045 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10179 | 3.9 | 5.2 | 5.8 | 305,375 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 9994 | 4.0 | 5.2 | 6.0 | 299,834 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10367 | 3.8 | 4.9 | 5.5 | 311,013 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10485 | 3.8 | 4.9 | 5.5 | 314,541 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6286 | 4.8 | 25.9 | 32.8 | 188,565 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6229 | 4.9 | 25.4 | 32.2 | 186,873 | 0.0% |
| hasura | Haskell | F1 | 1404 | 27.8 | 40.0 | 44.9 | 42,134 | 0.0% |
| postgraphile | Node.js | F1 | 3405 | 11.0 | 18.0 | 24.6 | 102,154 | 0.0% |
| actix-web-rest | Rust | F1 | 11995 | 3.2 | 4.3 | 6.1 | 359,851 | 0.0% |
| async-graphql | Rust | F1 | 9369 | 4.3 | 5.7 | 7.1 | 281,062 | 0.0% |
| mercurius | Node.js | F1 | 4349 | 8.5 | 14.8 | 19.6 | 130,462 | 0.0% |
| apollo-server | Node.js | F1 | 2913 | 13.0 | 21.1 | 27.8 | 87,385 | 0.0% |
| strawberry | Python | F1 | 1255 | 30.6 | 42.1 | 68.6 | 37,661 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8726 | 4.6 | 5.8 | 6.4 | 261,771 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8739 | 4.6 | 5.8 | 6.3 | 262,169 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4638 | 6.2 | 34.1 | 39.5 | 139,134 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4629 | 6.3 | 33.0 | 38.4 | 138,858 | 0.0% |
| hasura | Haskell | F2 | 1195 | 32.9 | 47.5 | 53.0 | 35,842 | 0.0% |
| postgraphile | Node.js | F2 | 2622 | 14.3 | 23.4 | 32.1 | 78,663 | 0.0% |
| actix-web-rest | Rust | F2 | 6543 | 6.0 | 7.1 | 8.0 | 196,298 | 0.0% |
| async-graphql | Rust | F2 | 6176 | 6.2 | 9.8 | 13.1 | 185,277 | 0.0% |
| mercurius | Node.js | F2 | 3099 | 11.8 | 20.6 | 26.2 | 92,959 | 0.0% |
| apollo-server | Node.js | F2 | 1906 | 19.5 | 33.3 | 42.0 | 57,167 | 0.0% |
| strawberry | Python | F2 | 931 | 48.4 | 62.0 | 87.4 | 27,935 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9477 | 4.2 | 5.3 | 5.9 | 284,312 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9420 | 4.2 | 5.4 | 5.9 | 282,600 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8706 | 4.6 | 5.9 | 6.5 | 261,174 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8574 | 4.6 | 6.0 | 6.6 | 257,234 | 0.0% |
| hasura | Haskell | F3 | 1504 | 26.2 | 32.7 | 42.1 | 45,134 | 0.0% |
| postgraphile | Node.js | F3 | 3002 | 12.5 | 20.9 | 30.7 | 90,058 | 0.0% |
| actix-web-rest | Rust | F3 | 1626 | 24.0 | 28.8 | 30.9 | 48,779 | 0.0% |
| async-graphql | Rust | F3 | 1400 | 17.6 | 63.1 | 67.1 | 42,004 | 0.0% |
| mercurius | Node.js | F3 | 1466 | 17.9 | 64.0 | 74.8 | 43,983 | 0.0% |
| apollo-server | Node.js | F3 | 1573 | 24.4 | 40.8 | 50.5 | 47,180 | 0.0% |
| strawberry | Python | F3 | 961 | 40.0 | 53.8 | 80.7 | 28,836 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5695 | 7.0 | 9.2 | 10.2 | 170,854 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5748 | 6.9 | 9.0 | 10.0 | 172,449 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3346 | 9.4 | 32.9 | 37.9 | 100,369 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3337 | 9.5 | 32.6 | 37.6 | 100,105 | 0.0% |
| hasura | Haskell | T1 | 930 | 42.4 | 57.1 | 62.4 | 27,906 | 0.0% |
| postgraphile | Node.js | T1 | 2118 | 16.9 | 31.3 | 61.5 | 63,550 | 0.0% |
| actix-web-rest | Rust | T1 | 3167 | 12.6 | 14.3 | 16.2 | 95,012 | 0.0% |
| async-graphql | Rust | T1 | 4883 | 7.5 | 13.3 | 16.0 | 146,485 | 0.0% |
| mercurius | Node.js | T1 | 1739 | 21.3 | 34.1 | 41.3 | 52,158 | 0.0% |
| apollo-server | Node.js | T1 | 1196 | 30.9 | 48.9 | 57.4 | 35,895 | 0.0% |
| strawberry | Python | T1 | 653 | 59.9 | 88.2 | 106.2 | 19,593 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1105 | 21.0 | 90.1 | 187.5 | 33,144 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1102 | 21.2 | 90.5 | 187.5 | 33,050 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1099 | 21.0 | 92.3 | 189.3 | 32,979 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1070 | 21.0 | 92.5 | 202.1 | 32,101 | 0.0% |
| hasura | Haskell | MC1 | 516 | 77.3 | 93.1 | 97.5 | 15,493 | 0.0% |
| postgraphile | Node.js | MC1 | 1338 | 26.0 | 48.6 | 90.0 | 40,141 | 0.0% |
| actix-web-rest | Rust | MC1 | 1278 | 30.2 | 36.0 | 39.3 | 38,328 | 0.0% |
| async-graphql | Rust | MC1 | 1250 | 23.0 | 58.6 | 62.0 | 37,500 | 0.0% |
| mercurius | Node.js | MC1 | 1329 | 27.4 | 47.4 | 54.7 | 39,858 | 0.0% |
| apollo-server | Node.js | MC1 | 1047 | 37.8 | 48.4 | 55.2 | 31,410 | 0.0% |
| strawberry | Python | MC1 | 548 | 89.1 | 134.6 | 150.2 | 16,438 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9385 | 4.2 | 5.3 | 5.9 | 281,537 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9126 | 4.3 | 5.5 | 6.1 | 273,771 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8450 | 4.7 | 6.1 | 6.9 | 253,505 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8258 | 4.8 | 6.2 | 6.9 | 247,738 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1398 | 17.5 | 63.2 | 67.2 | 41,945 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1453 | 18.1 | 64.0 | 75.8 | 43,579 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1578 | 24.8 | 38.8 | 48.4 | 47,327 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8821 | 4.5 | 5.7 | 6.3 | 264,632 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8727 | 4.6 | 5.8 | 6.4 | 261,801 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5188 | 5.9 | 27.9 | 34.1 | 155,627 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5122 | 6.1 | 27.3 | 33.8 | 153,664 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 6325 | 6.0 | 9.7 | 12.9 | 189,745 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3058 | 12.0 | 21.0 | 26.5 | 91,728 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1988 | 18.8 | 31.8 | 41.1 | 59,627 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1086 | 20.9 | 92.4 | 197.2 | 32,579 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1124 | 20.3 | 89.7 | 190.2 | 33,705 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1124 | 20.5 | 89.3 | 187.8 | 33,707 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1119 | 20.8 | 90.2 | 182.2 | 33,578 | 0.0% |
| async-graphql | Rust | M1_APQ | 9974 | 4.0 | 4.9 | 5.5 | 299,230 | 0.0% |
| mercurius | Node.js | M1_APQ | 3889 | 9.8 | 16.3 | 22.1 | 116,668 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2667 | 14.1 | 22.9 | 31.3 | 79,998 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1656 | 23.6 | 30.3 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1571 | 24.6 | 49.7 | 0.0% |
| mercurius | Node.js | 1458 | 17.8 | 76.4 | 0.0% |
| async-graphql | Rust | 1390 | 17.6 | 67.2 | 0.0% |
| strawberry | Python | 976 | 39.4 | 78.9 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9835 | 4.0 | 5.8 | 0.0% |
| fraiseql-tv | Rust | 9783 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-nocache | Rust | 8954 | 4.4 | 6.9 | 0.0% |
| fraiseql-v-cache | Rust | 8875 | 4.5 | 6.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 3237 | 11.7 | 26.2 | 0.0% |
| hasura | Haskell | 1463 | 27.0 | 42.6 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9835 | 4.0 | 5.8 |
| fraiseql-tv | Rust | graphql-precomputed | 9783 | 4.1 | 5.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8954 | 4.4 | 6.9 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8875 | 4.5 | 6.8 |
| postgraphile | Node.js | graphql-schema-first | 3237 | 11.7 | 26.2 |
| actix-web-rest | Rust | rest | 1656 | 23.6 | 30.3 |
| apollo-server | Node.js | graphql | 1571 | 24.6 | 49.7 |
| hasura | Haskell | graphql-schema-first | 1463 | 27.0 | 42.6 |
| mercurius | Node.js | graphql | 1458 | 17.8 | 76.4 |
| async-graphql | Rust | graphql | 1390 | 17.6 | 67.2 |
| strawberry | Python | graphql | 976 | 39.4 | 78.9 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9835 | 114 | 0.0033 | 71 | 0.0054 | 142 | 0.0027 |
| fraiseql-tv | 9783 | 114 | 0.0033 | 71 | 0.0054 | 141 | 0.0027 |
| fraiseql-v-nocache | 8954 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| fraiseql-v-cache | 8875 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| postgraphile | 3237 | 38 | 0.0101 | 23 | 0.0163 | 47 | 0.0082 |
| actix-web-rest | 1656 | 19 | 0.0198 | 12 | 0.0318 | 24 | 0.0160 |
| apollo-server | 1571 | 18 | 0.0208 | 11 | 0.0336 | 23 | 0.0168 |
| hasura | 1463 | 17 | 0.0224 | 11 | 0.0360 | 21 | 0.0181 |
| mercurius | 1458 | 17 | 0.0224 | 11 | 0.0361 | 21 | 0.0181 |
| async-graphql | 1390 | 16 | 0.0235 | 10 | 0.0379 | 20 | 0.0190 |
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
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 13 | 157.6 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 157.5 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 112.3 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 13 | 122.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 130 | 132.1 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 93.7 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 66 | 118.5 |
| hasura | Haskell | — | — | — | 135 | 166.1 |
| mercurius | Node.js | 464 | 8.8 | 104 | 55 | 108.7 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 131.1 |
| strawberry | Python | 1,812 | 12.7 | 136 | 181 | 176.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 18.4 |

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

> **Peak**: fraiseql-tv 1105 cycles/s (1 req) vs postgraphile 1338 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

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