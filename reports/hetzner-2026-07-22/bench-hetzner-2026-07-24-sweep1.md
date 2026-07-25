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
| Run timestamp | 2026-07-24T16:22:42+00:00 |

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
| `tv_comment` | 768.4 MB | 258.5 MB | 1.00 GB |
| `tb_comment` | 294.4 MB | 81.9 MB | 376.4 MB |
| `tv_post` | 210.2 MB | 61.2 MB | 302.3 MB |
| `tb_post` | 133.6 MB | 20.4 MB | 154.1 MB |
| `tv_user` | 8.0 MB | 9.3 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tb_user` | 4.6 MB | 4.4 MB | 9.0 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.0 MB | 0.0 MB | 0.1 MB |
| `tvd_user` | 0.0 MB | 0.0 MB | 0.0 MB |
| `tb_mutation_log` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.32 GB  
**TB tables (normalized baseline)**: 560.9 MB  
**Storage amplification**: 3.40× (TV adds 1.32 GB on top of the normalized 560.9 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9872 | 4.0 | 5.1 | 5.7 | 296,146 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9899 | 4.0 | 5.1 | 5.7 | 296,971 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8863 | 4.4 | 5.9 | 7.0 | 265,887 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8812 | 4.5 | 5.9 | 6.8 | 264,351 | 0.0% |
| hasura | Haskell | Q1 | 3637 | 10.6 | 17.2 | 19.6 | 109,096 | 0.0% |
| postgraphile | Node.js | Q1 | 3307 | 11.7 | 17.5 | 22.0 | 99,222 | 0.0% |
| actix-web-rest | Rust | Q1 | 1689 | 23.2 | 27.4 | 29.2 | 50,659 | 0.0% |
| async-graphql | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1 | 1458 | 17.8 | 64.9 | 77.6 | 43,729 | 0.0% |
| apollo-server | Node.js | Q1 | 1548 | 24.5 | 42.2 | 53.8 | 46,438 | 0.0% |
| strawberry | Python | Q1 | 986 | 39.0 | 51.8 | 78.5 | 29,575 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11602 | 3.4 | 4.3 | 4.8 | 348,073 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11185 | 3.5 | 4.6 | 5.1 | 335,552 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7370 | 4.5 | 15.8 | 25.7 | 221,115 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7360 | 4.5 | 16.2 | 25.8 | 220,799 | 0.0% |
| hasura | Haskell | Q2 | 3845 | 10.1 | 14.7 | 18.6 | 115,340 | 0.0% |
| postgraphile | Node.js | Q2 | 3953 | 9.7 | 14.8 | 19.2 | 118,587 | 0.0% |
| actix-web-rest | Rust | Q2 | 13471 | 2.9 | 3.4 | 3.8 | 404,126 | 0.0% |
| async-graphql | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2 | 4881 | 7.9 | 12.0 | 14.8 | 146,423 | 0.0% |
| apollo-server | Node.js | Q2 | 3123 | 12.5 | 18.4 | 21.4 | 93,689 | 0.0% |
| strawberry | Python | Q2 | 1402 | 27.9 | 38.0 | 63.8 | 42,045 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9226 | 4.3 | 5.5 | 6.1 | 276,777 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9239 | 4.3 | 5.5 | 6.1 | 277,178 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5354 | 5.8 | 27.3 | 33.2 | 160,623 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5241 | 5.8 | 28.5 | 34.3 | 157,221 | 0.0% |
| hasura | Haskell | Q2b | 3163 | 12.0 | 19.7 | 21.7 | 94,904 | 0.0% |
| postgraphile | Node.js | Q2b | 2848 | 13.7 | 19.6 | 24.3 | 85,447 | 0.0% |
| actix-web-rest | Rust | Q2b | 4898 | 8.1 | 9.1 | 9.7 | 146,930 | 0.0% |
| async-graphql | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b | 3488 | 11.0 | 16.4 | 20.0 | 104,628 | 0.0% |
| apollo-server | Node.js | Q2b | 2178 | 17.7 | 27.2 | 32.2 | 65,346 | 0.0% |
| strawberry | Python | Q2b | 1000 | 41.1 | 59.4 | 83.3 | 29,987 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7272 | 5.5 | 7.1 | 7.8 | 218,173 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7236 | 5.5 | 7.1 | 7.8 | 217,087 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3409 | 8.6 | 37.4 | 42.6 | 102,267 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3410 | 8.6 | 37.4 | 42.5 | 102,293 | 0.0% |
| hasura | Haskell | Q3 | 2615 | 14.7 | 22.4 | 25.4 | 78,438 | 0.0% |
| postgraphile | Node.js | Q3 | 1852 | 20.8 | 32.0 | 37.4 | 55,564 | 0.0% |
| actix-web-rest | Rust | Q3 | 4324 | 9.2 | 10.2 | 10.9 | 129,719 | 0.0% |
| async-graphql | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q3 | 1042 | 38.2 | 49.5 | 52.7 | 31,246 | 0.0% |
| apollo-server | Node.js | Q3 | 780 | 50.8 | 64.9 | 69.6 | 23,387 | 0.0% |
| strawberry | Python | Q3 | 533 | 83.0 | 128.4 | 144.1 | 15,994 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11645 | 3.4 | 4.3 | 4.8 | 349,343 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11623 | 3.4 | 4.4 | 4.8 | 348,690 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11288 | 3.5 | 4.5 | 4.9 | 338,625 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11045 | 3.6 | 4.6 | 5.0 | 331,357 | 0.0% |
| hasura | Haskell | C3 | 3474 | 11.1 | 17.6 | 20.0 | 104,206 | 0.0% |
| postgraphile | Node.js | C3 | 4217 | 9.1 | 13.6 | 18.2 | 126,524 | 0.0% |
| actix-web-rest | Rust | C3 | 17858 | 2.2 | 2.6 | 2.9 | 535,752 | 0.0% |
| async-graphql | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | C3 | 7315 | 5.2 | 8.1 | 10.8 | 219,450 | 0.0% |
| apollo-server | Node.js | C3 | 4217 | 9.2 | 13.6 | 16.3 | 126,506 | 0.0% |
| strawberry | Python | C3 | 1560 | 24.4 | 36.2 | 63.6 | 46,803 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11697 | 3.4 | 4.3 | 4.8 | 350,922 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11683 | 3.4 | 4.3 | 4.8 | 350,480 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11190 | 3.6 | 4.5 | 5.0 | 335,699 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11152 | 3.6 | 4.5 | 5.0 | 334,549 | 0.0% |
| hasura | Haskell | HC3 | 3456 | 11.0 | 18.1 | 20.5 | 103,673 | 0.0% |
| postgraphile | Node.js | HC3 | 4250 | 9.1 | 13.4 | 16.9 | 127,503 | 0.0% |
| actix-web-rest | Rust | HC3 | 17850 | 2.2 | 2.6 | 2.9 | 535,515 | 0.0% |
| async-graphql | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | HC3 | 7368 | 5.2 | 8.1 | 10.8 | 221,054 | 0.0% |
| apollo-server | Node.js | HC3 | 4224 | 9.2 | 13.6 | 16.6 | 126,711 | 0.0% |
| strawberry | Python | HC3 | 1578 | 23.6 | 35.8 | 58.6 | 47,329 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1105 | 20.2 | 94.0 | 197.2 | 33,152 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1116 | 20.4 | 89.9 | 189.9 | 33,482 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1121 | 20.3 | 91.1 | 182.9 | 33,628 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1116 | 20.7 | 91.1 | 182.0 | 33,466 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1062 | 21.4 | 94.6 | 195.0 | 31,870 | 0.0% |
| hasura | Haskell | M1 | 1961 | 19.3 | 26.7 | 30.8 | 58,822 | 0.0% |
| postgraphile | Node.js | M1 | 3498 | 10.7 | 16.5 | 21.7 | 104,927 | 0.0% |
| actix-web-rest | Rust | M1 | 5216 | 7.6 | 8.5 | 10.4 | 156,470 | 0.0% |
| async-graphql | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1 | 4457 | 8.6 | 12.2 | 16.4 | 133,708 | 0.0% |
| apollo-server | Node.js | M1 | 2807 | 13.4 | 19.2 | 24.3 | 84,218 | 0.0% |
| strawberry | Python | M1 | 1315 | 29.2 | 36.1 | 65.9 | 39,445 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 9907 | 4.0 | 5.3 | 5.9 | 297,201 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10075 | 4.0 | 5.2 | 5.8 | 302,254 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10337 | 3.8 | 5.0 | 5.5 | 310,103 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10518 | 3.8 | 4.9 | 5.4 | 315,549 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6797 | 4.7 | 19.8 | 28.8 | 203,918 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6819 | 4.7 | 20.0 | 28.4 | 204,584 | 0.0% |
| hasura | Haskell | F1 | 3489 | 11.0 | 17.3 | 20.1 | 104,656 | 0.0% |
| postgraphile | Node.js | F1 | 3679 | 10.5 | 15.7 | 20.1 | 110,365 | 0.0% |
| actix-web-rest | Rust | F1 | 13009 | 3.0 | 3.7 | 4.0 | 390,263 | 0.0% |
| async-graphql | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F1 | 4720 | 8.1 | 12.3 | 15.0 | 141,594 | 0.0% |
| apollo-server | Node.js | F1 | 3052 | 12.8 | 18.8 | 21.7 | 91,552 | 0.0% |
| strawberry | Python | F1 | 1276 | 29.9 | 37.5 | 68.7 | 38,274 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8716 | 4.6 | 5.8 | 6.4 | 261,493 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8787 | 4.5 | 5.8 | 6.3 | 263,620 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 5200 | 5.9 | 28.3 | 34.2 | 155,994 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 5196 | 5.9 | 28.2 | 34.3 | 155,895 | 0.0% |
| hasura | Haskell | F2 | 2877 | 13.3 | 20.5 | 22.7 | 86,309 | 0.0% |
| postgraphile | Node.js | F2 | 2806 | 13.6 | 21.1 | 26.7 | 84,167 | 0.0% |
| actix-web-rest | Rust | F2 | 4776 | 8.3 | 9.3 | 9.9 | 143,278 | 0.0% |
| async-graphql | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F2 | 3406 | 11.2 | 16.7 | 20.2 | 102,172 | 0.0% |
| apollo-server | Node.js | F2 | 2114 | 18.3 | 27.6 | 33.2 | 63,409 | 0.0% |
| strawberry | Python | F2 | 951 | 40.5 | 68.1 | 81.0 | 28,519 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9520 | 4.2 | 5.3 | 5.9 | 285,608 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9683 | 4.1 | 5.2 | 5.7 | 290,490 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8677 | 4.6 | 5.9 | 6.6 | 260,318 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8689 | 4.6 | 5.9 | 6.6 | 260,683 | 0.0% |
| hasura | Haskell | F3 | 3573 | 10.8 | 16.2 | 19.1 | 107,194 | 0.0% |
| postgraphile | Node.js | F3 | 3354 | 11.6 | 17.1 | 21.2 | 100,623 | 0.0% |
| actix-web-rest | Rust | F3 | 1623 | 24.2 | 28.3 | 30.2 | 48,689 | 0.0% |
| async-graphql | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F3 | 1467 | 17.7 | 64.3 | 75.3 | 44,007 | 0.0% |
| apollo-server | Node.js | F3 | 1575 | 24.6 | 39.8 | 49.4 | 47,248 | 0.0% |
| strawberry | Python | F3 | 976 | 39.5 | 53.2 | 83.9 | 29,270 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5653 | 7.0 | 9.2 | 10.2 | 169,583 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5645 | 7.0 | 9.2 | 10.2 | 169,358 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3431 | 9.2 | 32.3 | 37.3 | 102,928 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3416 | 9.3 | 31.9 | 36.7 | 102,484 | 0.0% |
| hasura | Haskell | T1 | 2153 | 17.5 | 26.0 | 28.5 | 64,595 | 0.0% |
| postgraphile | Node.js | T1 | 2511 | 15.3 | 22.7 | 29.4 | 75,327 | 0.0% |
| actix-web-rest | Rust | T1 | 3232 | 12.3 | 13.8 | 14.4 | 96,954 | 0.0% |
| async-graphql | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | T1 | 2023 | 18.8 | 25.7 | 29.3 | 60,699 | 0.0% |
| apollo-server | Node.js | T1 | 1432 | 26.7 | 35.7 | 40.1 | 42,954 | 0.0% |
| strawberry | Python | T1 | 665 | 60.3 | 83.1 | 114.8 | 19,947 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1096 | 20.9 | 92.8 | 188.0 | 32,894 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1100 | 20.7 | 91.5 | 196.1 | 33,012 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1107 | 20.4 | 92.2 | 196.3 | 33,224 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1109 | 20.9 | 90.5 | 189.8 | 33,256 | 0.0% |
| hasura | Haskell | MC1 | 1211 | 32.2 | 40.2 | 44.8 | 36,323 | 0.0% |
| postgraphile | Node.js | MC1 | 1560 | 24.0 | 35.8 | 44.7 | 46,793 | 0.0% |
| actix-web-rest | Rust | MC1 | 1358 | 28.7 | 33.3 | 35.9 | 40,727 | 0.0% |
| async-graphql | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | MC1 | 1347 | 26.8 | 47.4 | 54.3 | 40,407 | 0.0% |
| apollo-server | Node.js | MC1 | 1056 | 37.6 | 48.2 | 54.9 | 31,692 | 0.0% |
| strawberry | Python | MC1 | 567 | 68.0 | 102.2 | 112.8 | 17,004 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9326 | 4.3 | 5.4 | 5.9 | 279,786 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9214 | 4.3 | 5.4 | 6.0 | 276,420 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8382 | 4.7 | 6.1 | 6.8 | 251,456 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8398 | 4.7 | 6.1 | 6.7 | 251,936 | 0.0% |
| async-graphql | Rust | Q1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1_APQ | 1461 | 18.0 | 64.3 | 76.8 | 43,820 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1572 | 24.7 | 39.4 | 50.2 | 47,155 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8770 | 4.5 | 5.8 | 6.4 | 263,087 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8909 | 4.5 | 5.7 | 6.3 | 267,269 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5166 | 6.0 | 27.9 | 34.2 | 154,965 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5143 | 6.0 | 28.0 | 34.1 | 154,285 | 0.0% |
| async-graphql | Rust | Q2b_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b_APQ | 3418 | 11.2 | 16.8 | 20.3 | 102,541 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 2213 | 17.4 | 26.6 | 31.6 | 66,390 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1118 | 20.6 | 90.6 | 186.6 | 33,550 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1136 | 20.3 | 88.8 | 184.5 | 34,094 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1119 | 20.2 | 91.1 | 187.3 | 33,574 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1102 | 20.6 | 90.9 | 198.3 | 33,045 | 0.0% |
| async-graphql | Rust | M1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1_APQ | 4414 | 8.7 | 12.3 | 16.5 | 132,426 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2879 | 13.1 | 18.6 | 23.3 | 86,376 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1689 | 23.2 | 29.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1548 | 24.5 | 53.8 | 0.0% |
| mercurius | Node.js | 1458 | 17.8 | 77.6 | 0.0% |
| strawberry | Python | 986 | 39.0 | 78.5 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9899 | 4.0 | 5.7 | 0.0% |
| fraiseql-tv | Rust | 9872 | 4.0 | 5.7 | 0.0% |
| fraiseql-v-nocache | Rust | 8863 | 4.4 | 7.0 | 0.0% |
| fraiseql-v-cache | Rust | 8812 | 4.5 | 6.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 3637 | 10.6 | 19.6 | 0.0% |
| postgraphile | Node.js | 3307 | 11.7 | 22.0 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9899 | 4.0 | 5.7 |
| fraiseql-tv | Rust | graphql-precomputed | 9872 | 4.0 | 5.7 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8863 | 4.4 | 7.0 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8812 | 4.5 | 6.8 |
| hasura | Haskell | graphql-schema-first | 3637 | 10.6 | 19.6 |
| postgraphile | Node.js | graphql-schema-first | 3307 | 11.7 | 22.0 |
| actix-web-rest | Rust | rest | 1689 | 23.2 | 29.2 |
| apollo-server | Node.js | graphql | 1548 | 24.5 | 53.8 |
| mercurius | Node.js | graphql | 1458 | 17.8 | 77.6 |
| strawberry | Python | graphql | 986 | 39.0 | 78.5 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9899 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-tv | 9872 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-v-nocache | 8863 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| fraiseql-v-cache | 8812 | 102 | 0.0037 | 64 | 0.0060 | 127 | 0.0030 |
| hasura | 3637 | 42 | 0.0090 | 26 | 0.0145 | 52 | 0.0073 |
| postgraphile | 3307 | 38 | 0.0099 | 24 | 0.0159 | 48 | 0.0080 |
| actix-web-rest | 1689 | 20 | 0.0194 | 12 | 0.0312 | 24 | 0.0157 |
| apollo-server | 1548 | 18 | 0.0211 | 11 | 0.0340 | 22 | 0.0171 |
| mercurius | 1458 | 17 | 0.0224 | 11 | 0.0362 | 21 | 0.0181 |
| strawberry | 986 | 11 | 0.0332 | 7 | 0.0535 | 14 | 0.0268 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 158.6 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 11 | 157.8 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 115.1 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 124.1 |
| hasura | Haskell | — | — | — | 130 | 162.3 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 125 | 118.9 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 100.2 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 72 | 111.3 |
| mercurius | Node.js | 464 | 8.8 | 104 | 57 | 104.6 |
| strawberry | Python | 1,812 | 12.7 | 136 | 181 | 176.5 |
| fraiseql-tv-audit | Rust | — | — | 43 | 11 | 19.7 |

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

> **Peak**: fraiseql-tv-cache 1100 cycles/s (1 req) vs postgraphile 1560 cycles/s (2 req) — 0.7× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 5,216 M/s: **~57,372 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.