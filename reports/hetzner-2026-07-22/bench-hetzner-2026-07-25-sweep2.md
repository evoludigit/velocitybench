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
| Run timestamp | 2026-07-25T11:50:24+00:00 |

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
| `tv_post` | 210.5 MB | 68.7 MB | 311.0 MB |
| `tb_post` | 133.7 MB | 19.6 MB | 153.3 MB |
| `tb_mutation_log` | 37.2 MB | 2.9 MB | 40.2 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.5 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 599.9 MB  
**Storage amplification**: 3.29× (TV adds 1.34 GB on top of the normalized 599.9 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9771 | 4.1 | 5.2 | 5.7 | 293,143 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9677 | 4.1 | 5.2 | 5.8 | 290,319 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8760 | 4.5 | 5.9 | 6.7 | 262,809 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8951 | 4.4 | 5.8 | 6.7 | 268,539 | 0.0% |
| hasura | Haskell | Q1 | 1674 | 23.6 | 30.6 | 40.3 | 50,219 | 0.0% |
| postgraphile | Node.js | Q1 | 3067 | 12.4 | 19.9 | 26.9 | 91,997 | 0.0% |
| actix-web-rest | Rust | Q1 | 1658 | 23.4 | 28.2 | 31.2 | 49,732 | 0.0% |
| async-graphql | Rust | Q1 | 1411 | 17.4 | 62.9 | 67.2 | 42,317 | 0.0% |
| mercurius | Node.js | Q1 | 1463 | 17.6 | 64.8 | 76.0 | 43,894 | 0.0% |
| apollo-server | Node.js | Q1 | 1583 | 24.6 | 38.7 | 47.9 | 47,491 | 0.0% |
| strawberry | Python | Q1 | 976 | 39.8 | 57.3 | 82.2 | 29,281 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11203 | 3.5 | 4.6 | 5.1 | 336,086 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11003 | 3.6 | 4.7 | 5.2 | 330,097 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7321 | 4.6 | 14.0 | 24.4 | 219,627 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7151 | 4.6 | 16.8 | 26.6 | 214,523 | 0.0% |
| hasura | Haskell | Q2 | 1777 | 23.2 | 28.3 | 38.7 | 53,319 | 0.0% |
| postgraphile | Node.js | Q2 | 3534 | 10.5 | 18.3 | 25.4 | 106,035 | 0.0% |
| actix-web-rest | Rust | Q2 | 13820 | 2.8 | 3.5 | 4.2 | 414,598 | 0.0% |
| async-graphql | Rust | Q2 | 8027 | 4.9 | 6.9 | 9.2 | 240,802 | 0.0% |
| mercurius | Node.js | Q2 | 4634 | 8.1 | 13.5 | 17.9 | 139,011 | 0.0% |
| apollo-server | Node.js | Q2 | 2914 | 13.1 | 20.6 | 26.9 | 87,405 | 0.0% |
| strawberry | Python | Q2 | 1391 | 28.5 | 40.5 | 67.0 | 41,721 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9187 | 4.3 | 5.5 | 6.1 | 275,614 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9117 | 4.4 | 5.5 | 6.1 | 273,523 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5372 | 5.9 | 25.7 | 32.5 | 161,164 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5341 | 5.8 | 27.0 | 33.0 | 160,244 | 0.0% |
| hasura | Haskell | Q2b | 1309 | 30.3 | 43.2 | 47.8 | 39,275 | 0.0% |
| postgraphile | Node.js | Q2b | 2689 | 14.0 | 23.6 | 32.5 | 80,678 | 0.0% |
| actix-web-rest | Rust | Q2b | 5379 | 7.3 | 8.6 | 11.2 | 161,384 | 0.0% |
| async-graphql | Rust | Q2b | 6109 | 6.2 | 10.5 | 14.0 | 183,259 | 0.0% |
| mercurius | Node.js | Q2b | 3024 | 12.2 | 21.1 | 26.2 | 90,706 | 0.0% |
| apollo-server | Node.js | Q2b | 1897 | 19.6 | 33.7 | 42.8 | 56,909 | 0.0% |
| strawberry | Python | Q2b | 972 | 39.5 | 57.1 | 78.0 | 29,147 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7236 | 5.5 | 7.1 | 7.9 | 217,094 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7069 | 5.6 | 7.2 | 8.0 | 212,064 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3385 | 8.6 | 37.6 | 42.6 | 101,537 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3447 | 8.5 | 37.2 | 42.8 | 103,419 | 0.0% |
| hasura | Haskell | Q3 | 1069 | 37.1 | 50.5 | 54.9 | 32,070 | 0.0% |
| postgraphile | Node.js | Q3 | 1582 | 23.4 | 40.8 | 54.5 | 47,456 | 0.0% |
| actix-web-rest | Rust | Q3 | 4351 | 9.1 | 10.3 | 11.9 | 130,519 | 0.0% |
| async-graphql | Rust | Q3 | 2749 | 13.7 | 25.2 | 32.1 | 82,457 | 0.0% |
| mercurius | Node.js | Q3 | 932 | 41.9 | 59.6 | 67.0 | 27,964 | 0.0% |
| apollo-server | Node.js | Q3 | 656 | 59.9 | 82.5 | 92.4 | 19,687 | 0.0% |
| strawberry | Python | Q3 | 518 | 74.0 | 112.1 | 128.3 | 15,531 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11411 | 3.5 | 4.4 | 4.8 | 342,317 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11587 | 3.4 | 4.4 | 4.8 | 347,616 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11158 | 3.6 | 4.5 | 5.0 | 334,737 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11307 | 3.5 | 4.5 | 4.9 | 339,217 | 0.0% |
| hasura | Haskell | C3 | 1428 | 27.9 | 37.9 | 44.5 | 42,825 | 0.0% |
| postgraphile | Node.js | C3 | 4064 | 9.3 | 15.0 | 19.9 | 121,915 | 0.0% |
| actix-web-rest | Rust | C3 | 18313 | 2.1 | 2.5 | 3.0 | 549,403 | 0.0% |
| async-graphql | Rust | C3 | 15773 | 2.5 | 3.4 | 4.1 | 473,179 | 0.0% |
| mercurius | Node.js | C3 | 6521 | 5.6 | 10.2 | 13.7 | 195,625 | 0.0% |
| apollo-server | Node.js | C3 | 3909 | 9.7 | 15.7 | 19.9 | 117,259 | 0.0% |
| strawberry | Python | C3 | 1531 | 24.2 | 44.9 | 61.3 | 45,944 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11472 | 3.5 | 4.4 | 4.8 | 344,147 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11607 | 3.4 | 4.3 | 4.8 | 348,196 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11249 | 3.5 | 4.5 | 4.9 | 337,480 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11208 | 3.6 | 4.5 | 4.9 | 336,242 | 0.0% |
| hasura | Haskell | HC3 | 1437 | 27.6 | 37.9 | 43.4 | 43,117 | 0.0% |
| postgraphile | Node.js | HC3 | 3835 | 9.8 | 16.3 | 23.4 | 115,048 | 0.0% |
| actix-web-rest | Rust | HC3 | 18076 | 2.1 | 2.5 | 3.0 | 542,276 | 0.0% |
| async-graphql | Rust | HC3 | 15563 | 2.6 | 3.4 | 4.2 | 466,892 | 0.0% |
| mercurius | Node.js | HC3 | 6692 | 5.6 | 9.3 | 12.7 | 200,771 | 0.0% |
| apollo-server | Node.js | HC3 | 3823 | 9.9 | 15.8 | 19.9 | 114,700 | 0.0% |
| strawberry | Python | HC3 | 1532 | 24.2 | 44.9 | 63.3 | 45,952 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1107 | 20.7 | 90.6 | 192.9 | 33,197 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1099 | 20.8 | 90.7 | 192.3 | 32,971 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1110 | 20.2 | 91.2 | 194.6 | 33,310 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1147 | 19.9 | 89.8 | 183.1 | 34,411 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1075 | 21.7 | 93.6 | 192.8 | 32,240 | 0.0% |
| hasura | Haskell | M1 | 1588 | 20.1 | 51.0 | 58.3 | 47,628 | 0.0% |
| postgraphile | Node.js | M1 | 2930 | 11.5 | 22.1 | 56.9 | 87,912 | 0.0% |
| actix-web-rest | Rust | M1 | 3183 | 12.6 | 15.4 | 16.8 | 95,482 | 0.0% |
| async-graphql | Rust | M1 | 9408 | 4.2 | 5.1 | 5.8 | 282,225 | 0.0% |
| mercurius | Node.js | M1 | 4027 | 9.4 | 15.5 | 22.8 | 120,797 | 0.0% |
| apollo-server | Node.js | M1 | 2557 | 14.7 | 22.8 | 31.5 | 76,720 | 0.0% |
| strawberry | Python | M1 | 1262 | 30.2 | 38.0 | 70.3 | 37,864 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10096 | 3.9 | 5.2 | 6.0 | 302,873 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10172 | 3.9 | 5.2 | 5.8 | 305,168 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10517 | 3.8 | 4.8 | 5.4 | 315,503 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10206 | 3.9 | 5.0 | 5.6 | 306,171 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6209 | 4.9 | 25.3 | 32.4 | 186,264 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6160 | 5.0 | 25.7 | 32.4 | 184,788 | 0.0% |
| hasura | Haskell | F1 | 1443 | 27.8 | 34.4 | 44.3 | 43,287 | 0.0% |
| postgraphile | Node.js | F1 | 3287 | 11.4 | 18.4 | 27.0 | 98,605 | 0.0% |
| actix-web-rest | Rust | F1 | 13342 | 2.9 | 3.5 | 4.2 | 400,266 | 0.0% |
| async-graphql | Rust | F1 | 9377 | 4.3 | 5.7 | 6.7 | 281,315 | 0.0% |
| mercurius | Node.js | F1 | 4387 | 8.4 | 14.8 | 19.4 | 131,606 | 0.0% |
| apollo-server | Node.js | F1 | 2900 | 13.1 | 21.0 | 27.5 | 86,989 | 0.0% |
| strawberry | Python | F1 | 1268 | 30.1 | 40.1 | 68.9 | 38,039 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8561 | 4.6 | 5.9 | 6.5 | 256,843 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8528 | 4.7 | 5.9 | 6.6 | 255,847 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4563 | 6.3 | 33.9 | 39.2 | 136,895 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4596 | 6.3 | 33.9 | 39.2 | 137,870 | 0.0% |
| hasura | Haskell | F2 | 1402 | 27.5 | 38.6 | 47.0 | 42,057 | 0.0% |
| postgraphile | Node.js | F2 | 2553 | 14.7 | 24.2 | 33.0 | 76,579 | 0.0% |
| actix-web-rest | Rust | F2 | 7027 | 5.6 | 6.4 | 7.0 | 210,816 | 0.0% |
| async-graphql | Rust | F2 | 5915 | 6.4 | 11.0 | 14.6 | 177,438 | 0.0% |
| mercurius | Node.js | F2 | 3230 | 11.4 | 19.0 | 24.7 | 96,912 | 0.0% |
| apollo-server | Node.js | F2 | 1950 | 19.1 | 32.3 | 40.1 | 58,495 | 0.0% |
| strawberry | Python | F2 | 915 | 45.4 | 66.5 | 88.5 | 27,462 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9486 | 4.2 | 5.3 | 5.9 | 284,592 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9426 | 4.2 | 5.4 | 5.9 | 282,793 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8576 | 4.6 | 6.0 | 6.6 | 257,281 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8683 | 4.6 | 5.9 | 6.6 | 260,503 | 0.0% |
| hasura | Haskell | F3 | 1496 | 26.7 | 32.6 | 42.3 | 44,889 | 0.0% |
| postgraphile | Node.js | F3 | 3029 | 12.4 | 20.7 | 31.4 | 90,877 | 0.0% |
| actix-web-rest | Rust | F3 | 1655 | 23.7 | 28.0 | 30.0 | 49,646 | 0.0% |
| async-graphql | Rust | F3 | 1412 | 17.5 | 62.5 | 66.4 | 42,357 | 0.0% |
| mercurius | Node.js | F3 | 1450 | 18.0 | 64.7 | 76.8 | 43,509 | 0.0% |
| apollo-server | Node.js | F3 | 1581 | 24.7 | 37.8 | 47.6 | 47,434 | 0.0% |
| strawberry | Python | F3 | 952 | 40.3 | 52.7 | 83.4 | 28,562 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5602 | 7.1 | 9.3 | 10.2 | 168,066 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5640 | 7.0 | 9.2 | 10.3 | 169,191 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3311 | 9.5 | 32.9 | 37.7 | 99,331 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3323 | 9.4 | 33.7 | 38.4 | 99,683 | 0.0% |
| hasura | Haskell | T1 | 896 | 43.7 | 58.9 | 63.8 | 26,875 | 0.0% |
| postgraphile | Node.js | T1 | 2090 | 17.5 | 29.2 | 62.1 | 62,700 | 0.0% |
| actix-web-rest | Rust | T1 | 3238 | 12.2 | 13.8 | 14.6 | 97,137 | 0.0% |
| async-graphql | Rust | T1 | 5596 | 6.8 | 10.7 | 13.6 | 167,893 | 0.0% |
| mercurius | Node.js | T1 | 1717 | 21.5 | 34.6 | 41.8 | 51,517 | 0.0% |
| apollo-server | Node.js | T1 | 1254 | 29.7 | 46.3 | 55.4 | 37,630 | 0.0% |
| strawberry | Python | T1 | 646 | 59.1 | 92.3 | 109.1 | 19,383 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1074 | 21.7 | 91.3 | 191.7 | 32,218 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1089 | 21.0 | 92.2 | 189.3 | 32,679 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1114 | 20.9 | 89.4 | 190.4 | 33,423 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1114 | 20.6 | 91.1 | 191.0 | 33,434 | 0.0% |
| hasura | Haskell | MC1 | 575 | 68.7 | 85.9 | 96.4 | 17,257 | 0.0% |
| postgraphile | Node.js | MC1 | 1357 | 25.6 | 49.8 | 84.5 | 40,716 | 0.0% |
| actix-web-rest | Rust | MC1 | 1299 | 29.7 | 35.5 | 39.4 | 38,978 | 0.0% |
| async-graphql | Rust | MC1 | 1262 | 23.0 | 57.9 | 61.3 | 37,861 | 0.0% |
| mercurius | Node.js | MC1 | 1330 | 27.2 | 47.7 | 54.6 | 39,886 | 0.0% |
| apollo-server | Node.js | MC1 | 1048 | 37.7 | 48.7 | 58.5 | 31,445 | 0.0% |
| strawberry | Python | MC1 | 541 | 70.9 | 108.1 | 119.2 | 16,232 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9333 | 4.3 | 5.4 | 5.9 | 279,997 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9088 | 4.4 | 5.5 | 6.1 | 272,625 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8382 | 4.7 | 6.1 | 6.8 | 251,458 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8471 | 4.7 | 6.0 | 6.8 | 254,140 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1404 | 17.3 | 63.2 | 67.1 | 42,111 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1464 | 17.9 | 63.9 | 75.3 | 43,918 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1592 | 24.7 | 36.2 | 44.4 | 47,775 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8932 | 4.5 | 5.7 | 6.2 | 267,969 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8739 | 4.6 | 5.8 | 6.3 | 262,173 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5158 | 6.0 | 28.3 | 34.3 | 154,736 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5219 | 5.9 | 28.0 | 34.1 | 156,574 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 6263 | 6.1 | 10.0 | 13.5 | 187,881 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2977 | 12.3 | 21.6 | 26.8 | 89,300 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1969 | 19.1 | 31.7 | 38.4 | 59,070 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1089 | 21.0 | 92.6 | 193.7 | 32,660 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1119 | 20.9 | 89.3 | 181.6 | 33,583 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1117 | 20.3 | 89.8 | 194.9 | 33,521 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1129 | 20.5 | 89.4 | 190.1 | 33,883 | 0.0% |
| async-graphql | Rust | M1_APQ | 10003 | 4.0 | 4.9 | 5.5 | 300,100 | 0.0% |
| mercurius | Node.js | M1_APQ | 3874 | 9.7 | 16.7 | 22.7 | 116,213 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2601 | 14.5 | 23.2 | 31.6 | 78,037 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1658 | 23.4 | 31.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1583 | 24.6 | 47.9 | 0.0% |
| mercurius | Node.js | 1463 | 17.6 | 76.0 | 0.0% |
| async-graphql | Rust | 1411 | 17.4 | 67.2 | 0.0% |
| strawberry | Python | 976 | 39.8 | 82.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 9771 | 4.1 | 5.7 | 0.0% |
| fraiseql-tv-cache | Rust | 9677 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-cache | Rust | 8951 | 4.4 | 6.7 | 0.0% |
| fraiseql-v-nocache | Rust | 8760 | 4.5 | 6.7 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 3067 | 12.4 | 26.9 | 0.0% |
| hasura | Haskell | 1674 | 23.6 | 40.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 9771 | 4.1 | 5.7 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 9677 | 4.1 | 5.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8951 | 4.4 | 6.7 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8760 | 4.5 | 6.7 |
| postgraphile | Node.js | graphql-schema-first | 3067 | 12.4 | 26.9 |
| hasura | Haskell | graphql-schema-first | 1674 | 23.6 | 40.3 |
| actix-web-rest | Rust | rest | 1658 | 23.4 | 31.2 |
| apollo-server | Node.js | graphql | 1583 | 24.6 | 47.9 |
| mercurius | Node.js | graphql | 1463 | 17.6 | 76.0 |
| async-graphql | Rust | graphql | 1411 | 17.4 | 67.2 |
| strawberry | Python | graphql | 976 | 39.8 | 82.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 9771 | 114 | 0.0033 | 71 | 0.0054 | 141 | 0.0027 |
| fraiseql-tv-cache | 9677 | 113 | 0.0034 | 70 | 0.0054 | 139 | 0.0027 |
| fraiseql-v-cache | 8951 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| fraiseql-v-nocache | 8760 | 102 | 0.0037 | 63 | 0.0060 | 126 | 0.0030 |
| postgraphile | 3067 | 36 | 0.0107 | 22 | 0.0172 | 44 | 0.0086 |
| hasura | 1674 | 19 | 0.0195 | 12 | 0.0315 | 24 | 0.0158 |
| actix-web-rest | 1658 | 19 | 0.0197 | 12 | 0.0318 | 24 | 0.0160 |
| apollo-server | 1583 | 18 | 0.0207 | 11 | 0.0333 | 23 | 0.0167 |
| mercurius | 1463 | 17 | 0.0224 | 11 | 0.0360 | 21 | 0.0181 |
| async-graphql | 1411 | 16 | 0.0232 | 10 | 0.0374 | 20 | 0.0187 |
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
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 158.1 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 11 | 157.7 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 121.9 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 11 | 113.4 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 126 | 128.4 |
| hasura | Haskell | — | — | — | 134 | 161.6 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 103.9 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 64 | 118.0 |
| mercurius | Node.js | 464 | 8.8 | 104 | 57 | 107.8 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 133.4 |
| strawberry | Python | 1,812 | 12.7 | 136 | 189 | 174.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 11 | 18.5 |

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

> **Peak**: fraiseql-tv-cache 1089 cycles/s (1 req) vs postgraphile 1357 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 9,408 M/s: **~103,482 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.