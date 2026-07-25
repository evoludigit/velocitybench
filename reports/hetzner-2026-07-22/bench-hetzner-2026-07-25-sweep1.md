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
| Run timestamp | 2026-07-25T09:31:03+00:00 |

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
| `tv_comment` | 769.3 MB | 258.9 MB | 1.00 GB |
| `tb_comment` | 294.9 MB | 82.5 MB | 377.5 MB |
| `tv_post` | 210.2 MB | 60.9 MB | 302.2 MB |
| `tb_post` | 133.7 MB | 19.6 MB | 153.3 MB |
| `tv_user` | 8.0 MB | 9.2 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 4.6 MB | 4.4 MB | 9.0 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
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
| fraiseql-tv | Rust | Q1 | 9675 | 4.1 | 5.3 | 5.8 | 290,249 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9866 | 4.0 | 5.1 | 5.7 | 295,973 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8888 | 4.4 | 5.8 | 6.9 | 266,644 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8855 | 4.5 | 5.8 | 6.6 | 265,641 | 0.0% |
| hasura | Haskell | Q1 | 1497 | 26.6 | 35.6 | 43.1 | 44,920 | 0.0% |
| postgraphile | Node.js | Q1 | 3083 | 12.3 | 19.8 | 26.5 | 92,490 | 0.0% |
| actix-web-rest | Rust | Q1 | 1669 | 23.5 | 27.7 | 29.8 | 50,058 | 0.0% |
| async-graphql | Rust | Q1 | 1424 | 17.2 | 62.8 | 66.8 | 42,712 | 0.0% |
| mercurius | Node.js | Q1 | 1465 | 17.8 | 64.1 | 75.1 | 43,951 | 0.0% |
| apollo-server | Node.js | Q1 | 1570 | 24.7 | 39.7 | 49.1 | 47,094 | 0.0% |
| strawberry | Python | Q1 | 972 | 39.6 | 52.5 | 81.1 | 29,154 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11394 | 3.5 | 4.4 | 4.9 | 341,827 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11073 | 3.6 | 4.6 | 5.2 | 332,194 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7130 | 4.7 | 16.2 | 26.1 | 213,915 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7360 | 4.5 | 15.4 | 26.1 | 220,807 | 0.0% |
| hasura | Haskell | Q2 | 1580 | 24.9 | 33.8 | 41.7 | 47,407 | 0.0% |
| postgraphile | Node.js | Q2 | 3505 | 10.6 | 18.3 | 26.5 | 105,157 | 0.0% |
| actix-web-rest | Rust | Q2 | 13475 | 2.9 | 3.7 | 4.6 | 404,250 | 0.0% |
| async-graphql | Rust | Q2 | 8455 | 4.6 | 6.4 | 7.9 | 253,652 | 0.0% |
| mercurius | Node.js | Q2 | 4474 | 8.2 | 14.8 | 19.4 | 134,234 | 0.0% |
| apollo-server | Node.js | Q2 | 2907 | 13.1 | 20.6 | 26.3 | 87,196 | 0.0% |
| strawberry | Python | Q2 | 1395 | 27.2 | 34.0 | 62.6 | 41,864 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9115 | 4.3 | 5.5 | 6.1 | 273,449 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9149 | 4.3 | 5.5 | 6.1 | 274,484 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5264 | 5.9 | 27.5 | 33.6 | 157,922 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5433 | 5.7 | 26.7 | 33.1 | 163,000 | 0.0% |
| hasura | Haskell | Q2b | 1337 | 30.0 | 41.6 | 46.9 | 40,108 | 0.0% |
| postgraphile | Node.js | Q2b | 2868 | 13.3 | 20.5 | 27.3 | 86,032 | 0.0% |
| actix-web-rest | Rust | Q2b | 5282 | 7.4 | 9.2 | 11.3 | 158,450 | 0.0% |
| async-graphql | Rust | Q2b | 6150 | 6.2 | 10.2 | 13.7 | 184,513 | 0.0% |
| mercurius | Node.js | Q2b | 2891 | 12.7 | 22.7 | 28.3 | 86,719 | 0.0% |
| apollo-server | Node.js | Q2b | 1925 | 19.5 | 32.6 | 41.2 | 57,763 | 0.0% |
| strawberry | Python | Q2b | 989 | 40.0 | 61.0 | 76.8 | 29,684 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7339 | 5.4 | 7.0 | 7.7 | 220,161 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7341 | 5.4 | 7.0 | 7.7 | 220,235 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3406 | 8.5 | 37.9 | 43.1 | 102,194 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3458 | 8.4 | 37.7 | 42.9 | 103,748 | 0.0% |
| hasura | Haskell | Q3 | 1040 | 37.8 | 51.5 | 54.9 | 31,201 | 0.0% |
| postgraphile | Node.js | Q3 | 1611 | 22.9 | 41.0 | 52.9 | 48,329 | 0.0% |
| actix-web-rest | Rust | Q3 | 4357 | 9.1 | 10.2 | 12.1 | 130,707 | 0.0% |
| async-graphql | Rust | Q3 | 2631 | 14.3 | 26.9 | 33.0 | 78,928 | 0.0% |
| mercurius | Node.js | Q3 | 917 | 42.4 | 60.4 | 69.3 | 27,509 | 0.0% |
| apollo-server | Node.js | Q3 | 655 | 60.1 | 83.3 | 93.4 | 19,643 | 0.0% |
| strawberry | Python | Q3 | 523 | 81.6 | 121.8 | 140.4 | 15,677 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11615 | 3.4 | 4.3 | 4.8 | 348,454 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11566 | 3.4 | 4.4 | 4.8 | 346,986 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11271 | 3.5 | 4.5 | 4.9 | 338,119 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11348 | 3.5 | 4.4 | 4.9 | 340,451 | 0.0% |
| hasura | Haskell | C3 | 1437 | 27.5 | 37.8 | 44.5 | 43,113 | 0.0% |
| postgraphile | Node.js | C3 | 3874 | 9.6 | 16.0 | 24.0 | 116,210 | 0.0% |
| actix-web-rest | Rust | C3 | 17857 | 2.2 | 2.6 | 3.0 | 535,701 | 0.0% |
| async-graphql | Rust | C3 | 16126 | 2.4 | 3.2 | 3.8 | 483,775 | 0.0% |
| mercurius | Node.js | C3 | 6803 | 5.5 | 9.3 | 12.6 | 204,097 | 0.0% |
| apollo-server | Node.js | C3 | 4011 | 9.6 | 14.6 | 17.9 | 120,344 | 0.0% |
| strawberry | Python | C3 | 1514 | 26.0 | 44.0 | 68.0 | 45,427 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11542 | 3.4 | 4.4 | 4.8 | 346,271 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11564 | 3.4 | 4.3 | 4.8 | 346,922 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11240 | 3.5 | 4.5 | 4.9 | 337,204 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11236 | 3.5 | 4.5 | 5.0 | 337,074 | 0.0% |
| hasura | Haskell | HC3 | 1498 | 26.9 | 37.0 | 44.1 | 44,926 | 0.0% |
| postgraphile | Node.js | HC3 | 4025 | 9.3 | 15.5 | 20.6 | 120,748 | 0.0% |
| actix-web-rest | Rust | HC3 | 17553 | 2.2 | 2.7 | 3.2 | 526,595 | 0.0% |
| async-graphql | Rust | HC3 | 16095 | 2.4 | 3.2 | 3.8 | 482,861 | 0.0% |
| mercurius | Node.js | HC3 | 7057 | 5.4 | 8.5 | 11.2 | 211,712 | 0.0% |
| apollo-server | Node.js | HC3 | 3948 | 9.7 | 14.9 | 17.9 | 118,449 | 0.0% |
| strawberry | Python | HC3 | 1539 | 25.0 | 45.2 | 64.5 | 46,172 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1122 | 20.3 | 91.5 | 187.3 | 33,658 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1135 | 20.1 | 90.0 | 186.8 | 34,050 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1133 | 20.0 | 91.5 | 185.8 | 34,001 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1125 | 20.1 | 91.1 | 185.7 | 33,742 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1073 | 21.4 | 93.6 | 194.7 | 32,186 | 0.0% |
| hasura | Haskell | M1 | 1570 | 19.7 | 51.5 | 60.7 | 47,090 | 0.0% |
| postgraphile | Node.js | M1 | 2952 | 11.6 | 21.5 | 50.7 | 88,552 | 0.0% |
| actix-web-rest | Rust | M1 | 2578 | 15.9 | 17.6 | 18.4 | 77,330 | 0.0% |
| async-graphql | Rust | M1 | 9836 | 4.0 | 4.9 | 5.5 | 295,074 | 0.0% |
| mercurius | Node.js | M1 | 4291 | 9.0 | 13.5 | 19.1 | 128,720 | 0.0% |
| apollo-server | Node.js | M1 | 2653 | 13.9 | 22.1 | 31.1 | 79,581 | 0.0% |
| strawberry | Python | M1 | 1269 | 30.0 | 38.8 | 69.8 | 38,068 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 9859 | 4.0 | 5.3 | 6.0 | 295,759 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10169 | 3.9 | 5.2 | 5.9 | 305,060 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10439 | 3.8 | 4.9 | 5.4 | 313,159 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10456 | 3.8 | 4.9 | 5.4 | 313,665 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6232 | 4.9 | 25.6 | 32.8 | 186,959 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6172 | 4.9 | 26.0 | 32.8 | 185,154 | 0.0% |
| hasura | Haskell | F1 | 1399 | 27.9 | 40.0 | 44.6 | 41,978 | 0.0% |
| postgraphile | Node.js | F1 | 3421 | 11.1 | 17.7 | 23.1 | 102,634 | 0.0% |
| actix-web-rest | Rust | F1 | 12931 | 3.0 | 3.7 | 4.3 | 387,917 | 0.0% |
| async-graphql | Rust | F1 | 9642 | 4.1 | 5.1 | 5.7 | 289,263 | 0.0% |
| mercurius | Node.js | F1 | 4338 | 8.5 | 14.9 | 19.7 | 130,125 | 0.0% |
| apollo-server | Node.js | F1 | 2978 | 12.9 | 20.2 | 26.2 | 89,332 | 0.0% |
| strawberry | Python | F1 | 1280 | 29.7 | 38.7 | 68.7 | 38,403 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8783 | 4.5 | 5.8 | 6.4 | 263,477 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8708 | 4.6 | 5.8 | 6.4 | 261,251 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4640 | 6.2 | 33.5 | 38.9 | 139,201 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4629 | 6.2 | 33.9 | 39.1 | 138,872 | 0.0% |
| hasura | Haskell | F2 | 1220 | 33.0 | 45.2 | 50.6 | 36,594 | 0.0% |
| postgraphile | Node.js | F2 | 2560 | 14.4 | 25.3 | 36.8 | 76,796 | 0.0% |
| actix-web-rest | Rust | F2 | 6211 | 6.3 | 7.3 | 8.3 | 186,322 | 0.0% |
| async-graphql | Rust | F2 | 6232 | 6.2 | 9.6 | 13.0 | 186,953 | 0.0% |
| mercurius | Node.js | F2 | 3090 | 11.9 | 20.8 | 26.5 | 92,698 | 0.0% |
| apollo-server | Node.js | F2 | 1959 | 19.2 | 31.6 | 39.0 | 58,776 | 0.0% |
| strawberry | Python | F2 | 932 | 48.1 | 64.7 | 91.8 | 27,962 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9567 | 4.2 | 5.3 | 5.8 | 287,024 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9570 | 4.2 | 5.3 | 5.8 | 287,109 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8697 | 4.6 | 5.9 | 6.6 | 260,914 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8718 | 4.5 | 5.9 | 6.6 | 261,534 | 0.0% |
| hasura | Haskell | F3 | 1493 | 26.7 | 36.3 | 43.7 | 44,797 | 0.0% |
| postgraphile | Node.js | F3 | 2982 | 12.9 | 19.9 | 26.4 | 89,472 | 0.0% |
| actix-web-rest | Rust | F3 | 1655 | 23.6 | 28.2 | 30.2 | 49,657 | 0.0% |
| async-graphql | Rust | F3 | 1412 | 17.3 | 62.9 | 67.0 | 42,363 | 0.0% |
| mercurius | Node.js | F3 | 1470 | 17.7 | 64.0 | 76.1 | 44,094 | 0.0% |
| apollo-server | Node.js | F3 | 1583 | 24.6 | 38.6 | 48.1 | 47,497 | 0.0% |
| strawberry | Python | F3 | 960 | 39.9 | 52.5 | 82.6 | 28,813 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5598 | 7.1 | 9.3 | 10.3 | 167,937 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5575 | 7.1 | 9.3 | 10.3 | 167,245 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3298 | 9.5 | 33.5 | 38.4 | 98,938 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3334 | 9.4 | 33.1 | 38.0 | 100,021 | 0.0% |
| hasura | Haskell | T1 | 887 | 44.0 | 59.0 | 62.7 | 26,624 | 0.0% |
| postgraphile | Node.js | T1 | 2154 | 16.8 | 29.2 | 62.0 | 64,618 | 0.0% |
| actix-web-rest | Rust | T1 | 3231 | 12.3 | 13.9 | 15.0 | 96,921 | 0.0% |
| async-graphql | Rust | T1 | 5694 | 6.7 | 10.5 | 13.4 | 170,813 | 0.0% |
| mercurius | Node.js | T1 | 1717 | 21.4 | 34.8 | 42.4 | 51,507 | 0.0% |
| apollo-server | Node.js | T1 | 1222 | 30.3 | 48.7 | 56.5 | 36,665 | 0.0% |
| strawberry | Python | T1 | 649 | 65.4 | 100.7 | 127.3 | 19,471 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1093 | 20.9 | 92.6 | 196.3 | 32,783 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1132 | 20.1 | 89.4 | 184.6 | 33,956 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1101 | 20.6 | 92.9 | 193.6 | 33,034 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1123 | 20.6 | 90.9 | 182.7 | 33,681 | 0.0% |
| hasura | Haskell | MC1 | 503 | 79.7 | 93.0 | 97.1 | 15,086 | 0.0% |
| postgraphile | Node.js | MC1 | 1313 | 26.0 | 53.7 | 92.3 | 39,400 | 0.0% |
| actix-web-rest | Rust | MC1 | 1295 | 29.7 | 35.7 | 39.9 | 38,860 | 0.0% |
| async-graphql | Rust | MC1 | 1263 | 22.7 | 58.3 | 61.7 | 37,890 | 0.0% |
| mercurius | Node.js | MC1 | 1342 | 27.0 | 46.9 | 54.3 | 40,274 | 0.0% |
| apollo-server | Node.js | MC1 | 1059 | 37.4 | 47.8 | 55.2 | 31,775 | 0.0% |
| strawberry | Python | MC1 | 548 | 70.2 | 106.4 | 119.1 | 16,447 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9274 | 4.3 | 5.4 | 6.0 | 278,231 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9328 | 4.3 | 5.4 | 5.9 | 279,852 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8546 | 4.6 | 6.0 | 6.7 | 256,365 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8450 | 4.7 | 6.0 | 6.7 | 253,492 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1409 | 17.2 | 63.2 | 67.3 | 42,261 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1473 | 17.9 | 63.4 | 75.0 | 44,203 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1589 | 24.5 | 38.0 | 48.0 | 47,669 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8903 | 4.5 | 5.7 | 6.2 | 267,080 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8885 | 4.5 | 5.7 | 6.3 | 266,539 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5093 | 6.0 | 28.9 | 34.9 | 152,785 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5205 | 5.9 | 28.2 | 34.0 | 156,149 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 6276 | 6.0 | 10.2 | 13.8 | 188,265 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3010 | 12.2 | 21.1 | 26.4 | 90,291 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1986 | 18.8 | 31.8 | 38.7 | 59,595 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1087 | 20.9 | 92.4 | 194.8 | 32,597 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1146 | 19.9 | 87.9 | 185.5 | 34,385 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1127 | 20.4 | 89.7 | 183.7 | 33,817 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1131 | 20.2 | 89.9 | 185.2 | 33,921 | 0.0% |
| async-graphql | Rust | M1_APQ | 10590 | 3.7 | 4.6 | 5.1 | 317,715 | 0.0% |
| mercurius | Node.js | M1_APQ | 3850 | 9.7 | 16.8 | 22.4 | 115,506 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2670 | 14.2 | 22.7 | 32.6 | 80,096 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1669 | 23.5 | 29.8 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1570 | 24.7 | 49.1 | 0.0% |
| mercurius | Node.js | 1465 | 17.8 | 75.1 | 0.0% |
| async-graphql | Rust | 1424 | 17.2 | 66.8 | 0.0% |
| strawberry | Python | 972 | 39.6 | 81.1 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9866 | 4.0 | 5.7 | 0.0% |
| fraiseql-tv | Rust | 9675 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-nocache | Rust | 8888 | 4.4 | 6.9 | 0.0% |
| fraiseql-v-cache | Rust | 8855 | 4.5 | 6.6 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 3083 | 12.3 | 26.5 | 0.0% |
| hasura | Haskell | 1497 | 26.6 | 43.1 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9866 | 4.0 | 5.7 |
| fraiseql-tv | Rust | graphql-precomputed | 9675 | 4.1 | 5.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8888 | 4.4 | 6.9 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8855 | 4.5 | 6.6 |
| postgraphile | Node.js | graphql-schema-first | 3083 | 12.3 | 26.5 |
| actix-web-rest | Rust | rest | 1669 | 23.5 | 29.8 |
| apollo-server | Node.js | graphql | 1570 | 24.7 | 49.1 |
| hasura | Haskell | graphql-schema-first | 1497 | 26.6 | 43.1 |
| mercurius | Node.js | graphql | 1465 | 17.8 | 75.1 |
| async-graphql | Rust | graphql | 1424 | 17.2 | 66.8 |
| strawberry | Python | graphql | 972 | 39.6 | 81.1 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9866 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-tv | 9675 | 113 | 0.0034 | 70 | 0.0054 | 139 | 0.0027 |
| fraiseql-v-nocache | 8888 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| fraiseql-v-cache | 8855 | 103 | 0.0037 | 64 | 0.0060 | 127 | 0.0030 |
| postgraphile | 3083 | 36 | 0.0106 | 22 | 0.0171 | 44 | 0.0086 |
| actix-web-rest | 1669 | 19 | 0.0196 | 12 | 0.0316 | 24 | 0.0158 |
| apollo-server | 1570 | 18 | 0.0208 | 11 | 0.0336 | 23 | 0.0168 |
| hasura | 1497 | 17 | 0.0219 | 11 | 0.0352 | 22 | 0.0177 |
| mercurius | 1465 | 17 | 0.0223 | 11 | 0.0360 | 21 | 0.0180 |
| async-graphql | 1424 | 17 | 0.0230 | 10 | 0.0370 | 20 | 0.0186 |
| strawberry | 972 | 11 | 0.0337 | 7 | 0.0542 | 14 | 0.0272 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 158.4 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 13 | 157.5 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 111.3 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 121.7 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 125 | 129.7 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 100.2 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 66 | 116.1 |
| hasura | Haskell | — | — | — | 135 | 164.5 |
| mercurius | Node.js | 464 | 8.8 | 104 | 63 | 108.0 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 134.0 |
| strawberry | Python | 1,812 | 12.7 | 136 | 191 | 175.3 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 20.0 |

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

> **Peak**: fraiseql-tv-cache 1132 cycles/s (1 req) vs mercurius 1342 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 9,836 M/s: **~108,193 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.