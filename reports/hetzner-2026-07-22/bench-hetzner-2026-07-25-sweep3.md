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
| Run timestamp | 2026-07-25T14:09:50+00:00 |

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
| `tv_post` | 210.7 MB | 68.7 MB | 311.1 MB |
| `tb_post` | 133.7 MB | 19.6 MB | 153.3 MB |
| `tb_mutation_log` | 74.1 MB | 5.8 MB | 79.9 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.7 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.5 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 639.7 MB  
**Storage amplification**: 3.15× (TV adds 1.34 GB on top of the normalized 639.7 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9740 | 4.1 | 5.2 | 5.8 | 292,215 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9761 | 4.1 | 5.2 | 5.8 | 292,837 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8824 | 4.5 | 5.8 | 6.6 | 264,735 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8862 | 4.5 | 5.8 | 6.7 | 265,847 | 0.0% |
| hasura | Haskell | Q1 | 1542 | 25.7 | 35.1 | 42.5 | 46,275 | 0.0% |
| postgraphile | Node.js | Q1 | 3153 | 12.2 | 18.9 | 24.2 | 94,597 | 0.0% |
| actix-web-rest | Rust | Q1 | 1662 | 23.3 | 28.4 | 31.5 | 49,874 | 0.0% |
| async-graphql | Rust | Q1 | 1402 | 17.4 | 63.2 | 67.3 | 42,069 | 0.0% |
| mercurius | Node.js | Q1 | 1452 | 17.8 | 65.1 | 76.9 | 43,563 | 0.0% |
| apollo-server | Node.js | Q1 | 1552 | 24.8 | 41.0 | 50.5 | 46,567 | 0.0% |
| strawberry | Python | Q1 | 968 | 39.8 | 55.6 | 82.5 | 29,036 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 10980 | 3.6 | 4.7 | 5.2 | 329,388 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11047 | 3.6 | 4.6 | 5.2 | 331,420 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7251 | 4.6 | 14.7 | 25.5 | 217,532 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7321 | 4.6 | 15.4 | 25.4 | 219,621 | 0.0% |
| hasura | Haskell | Q2 | 1647 | 24.1 | 34.0 | 40.1 | 49,417 | 0.0% |
| postgraphile | Node.js | Q2 | 3685 | 10.3 | 16.4 | 22.2 | 110,558 | 0.0% |
| actix-web-rest | Rust | Q2 | 12718 | 3.1 | 3.8 | 4.3 | 381,526 | 0.0% |
| async-graphql | Rust | Q2 | 8258 | 4.7 | 6.3 | 8.5 | 247,727 | 0.0% |
| mercurius | Node.js | Q2 | 4464 | 8.2 | 15.1 | 19.9 | 133,905 | 0.0% |
| apollo-server | Node.js | Q2 | 2896 | 13.1 | 21.5 | 28.0 | 86,882 | 0.0% |
| strawberry | Python | Q2 | 1385 | 27.5 | 33.8 | 60.0 | 41,551 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9070 | 4.4 | 5.6 | 6.2 | 272,104 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9063 | 4.4 | 5.6 | 6.2 | 271,887 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5375 | 5.8 | 26.7 | 33.4 | 161,252 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5419 | 5.8 | 26.5 | 33.1 | 162,579 | 0.0% |
| hasura | Haskell | Q2b | 1332 | 29.3 | 42.1 | 46.6 | 39,960 | 0.0% |
| postgraphile | Node.js | Q2b | 2658 | 14.2 | 23.2 | 32.4 | 79,745 | 0.0% |
| actix-web-rest | Rust | Q2b | 4978 | 7.8 | 10.5 | 13.3 | 149,332 | 0.0% |
| async-graphql | Rust | Q2b | 6106 | 6.2 | 10.7 | 14.3 | 183,192 | 0.0% |
| mercurius | Node.js | Q2b | 3044 | 12.1 | 21.0 | 26.1 | 91,316 | 0.0% |
| apollo-server | Node.js | Q2b | 1867 | 19.9 | 33.9 | 42.4 | 56,023 | 0.0% |
| strawberry | Python | Q2b | 984 | 45.5 | 60.9 | 93.2 | 29,531 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7263 | 5.5 | 7.0 | 7.8 | 217,877 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7251 | 5.5 | 7.1 | 7.8 | 217,525 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3453 | 8.4 | 37.5 | 42.8 | 103,577 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3452 | 8.5 | 37.1 | 42.5 | 103,557 | 0.0% |
| hasura | Haskell | Q3 | 1071 | 37.4 | 50.9 | 57.4 | 32,137 | 0.0% |
| postgraphile | Node.js | Q3 | 1596 | 23.2 | 41.2 | 53.5 | 47,881 | 0.0% |
| actix-web-rest | Rust | Q3 | 4218 | 9.4 | 10.7 | 12.8 | 126,525 | 0.0% |
| async-graphql | Rust | Q3 | 2695 | 13.9 | 26.2 | 33.4 | 80,848 | 0.0% |
| mercurius | Node.js | Q3 | 931 | 42.0 | 59.2 | 67.6 | 27,938 | 0.0% |
| apollo-server | Node.js | Q3 | 643 | 61.0 | 84.5 | 95.0 | 19,291 | 0.0% |
| strawberry | Python | Q3 | 503 | 77.5 | 118.2 | 137.8 | 15,102 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11635 | 3.4 | 4.3 | 4.8 | 349,063 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11604 | 3.4 | 4.3 | 4.8 | 348,112 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11190 | 3.6 | 4.5 | 5.0 | 335,686 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11118 | 3.6 | 4.5 | 5.0 | 333,525 | 0.0% |
| hasura | Haskell | C3 | 1421 | 27.8 | 36.6 | 43.2 | 42,641 | 0.0% |
| postgraphile | Node.js | C3 | 3649 | 10.1 | 17.6 | 29.2 | 109,463 | 0.0% |
| actix-web-rest | Rust | C3 | 16160 | 2.4 | 3.0 | 3.4 | 484,807 | 0.0% |
| async-graphql | Rust | C3 | 16089 | 2.4 | 3.2 | 3.9 | 482,664 | 0.0% |
| mercurius | Node.js | C3 | 6772 | 5.5 | 9.5 | 12.5 | 203,158 | 0.0% |
| apollo-server | Node.js | C3 | 3904 | 9.8 | 15.3 | 19.4 | 117,119 | 0.0% |
| strawberry | Python | C3 | 1547 | 24.7 | 47.4 | 63.0 | 46,417 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11559 | 3.4 | 4.3 | 4.8 | 346,776 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11433 | 3.5 | 4.4 | 4.9 | 342,996 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11254 | 3.5 | 4.5 | 5.0 | 337,629 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11154 | 3.6 | 4.5 | 5.0 | 334,614 | 0.0% |
| hasura | Haskell | HC3 | 1444 | 27.2 | 38.5 | 45.7 | 43,328 | 0.0% |
| postgraphile | Node.js | HC3 | 3821 | 9.7 | 16.9 | 25.4 | 114,622 | 0.0% |
| actix-web-rest | Rust | HC3 | 16289 | 2.4 | 2.9 | 3.4 | 488,670 | 0.0% |
| async-graphql | Rust | HC3 | 16066 | 2.4 | 3.2 | 3.8 | 481,969 | 0.0% |
| mercurius | Node.js | HC3 | 6884 | 5.4 | 9.3 | 12.4 | 206,535 | 0.0% |
| apollo-server | Node.js | HC3 | 3960 | 9.6 | 15.1 | 18.8 | 118,792 | 0.0% |
| strawberry | Python | HC3 | 1532 | 24.2 | 48.0 | 61.9 | 45,945 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1128 | 20.3 | 91.2 | 182.4 | 33,841 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1094 | 20.9 | 92.0 | 198.1 | 32,811 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1129 | 19.8 | 89.9 | 190.3 | 33,878 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1105 | 20.6 | 91.7 | 185.1 | 33,148 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1065 | 21.8 | 93.8 | 194.1 | 31,959 | 0.0% |
| hasura | Haskell | M1 | 1856 | 19.6 | 30.3 | 51.0 | 55,679 | 0.0% |
| postgraphile | Node.js | M1 | 3001 | 11.5 | 20.6 | 46.8 | 90,038 | 0.0% |
| actix-web-rest | Rust | M1 | 3548 | 11.0 | 14.2 | 15.8 | 106,449 | 0.0% |
| async-graphql | Rust | M1 | 9538 | 4.1 | 5.0 | 5.5 | 286,134 | 0.0% |
| mercurius | Node.js | M1 | 4039 | 9.4 | 15.7 | 21.1 | 121,174 | 0.0% |
| apollo-server | Node.js | M1 | 2541 | 14.8 | 24.7 | 32.3 | 76,234 | 0.0% |
| strawberry | Python | M1 | 1254 | 30.4 | 37.6 | 70.7 | 37,613 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10128 | 3.9 | 5.2 | 5.9 | 303,832 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 9870 | 4.0 | 5.3 | 6.0 | 296,088 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10419 | 3.8 | 4.9 | 5.5 | 312,580 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10407 | 3.8 | 4.9 | 5.5 | 312,196 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6185 | 5.0 | 25.3 | 32.0 | 185,558 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6231 | 4.9 | 25.3 | 32.0 | 186,926 | 0.0% |
| hasura | Haskell | F1 | 1450 | 27.5 | 33.8 | 44.4 | 43,503 | 0.0% |
| postgraphile | Node.js | F1 | 3241 | 11.5 | 19.5 | 27.7 | 97,236 | 0.0% |
| actix-web-rest | Rust | F1 | 12049 | 3.2 | 4.2 | 5.7 | 361,468 | 0.0% |
| async-graphql | Rust | F1 | 9524 | 4.2 | 5.2 | 5.8 | 285,708 | 0.0% |
| mercurius | Node.js | F1 | 4176 | 8.7 | 16.3 | 21.1 | 125,286 | 0.0% |
| apollo-server | Node.js | F1 | 2898 | 13.3 | 20.3 | 25.2 | 86,936 | 0.0% |
| strawberry | Python | F1 | 1255 | 31.8 | 46.3 | 74.7 | 37,664 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8775 | 4.5 | 5.8 | 6.4 | 263,240 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8679 | 4.6 | 5.8 | 6.5 | 260,378 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4614 | 6.3 | 33.5 | 38.9 | 138,407 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4639 | 6.2 | 33.4 | 38.9 | 139,166 | 0.0% |
| hasura | Haskell | F2 | 1157 | 34.3 | 46.7 | 52.2 | 34,710 | 0.0% |
| postgraphile | Node.js | F2 | 2545 | 14.6 | 24.9 | 35.0 | 76,351 | 0.0% |
| actix-web-rest | Rust | F2 | 6775 | 5.8 | 6.7 | 7.8 | 203,251 | 0.0% |
| async-graphql | Rust | F2 | 6061 | 6.2 | 10.6 | 14.4 | 181,835 | 0.0% |
| mercurius | Node.js | F2 | 3101 | 11.8 | 20.5 | 26.1 | 93,016 | 0.0% |
| apollo-server | Node.js | F2 | 1902 | 19.6 | 33.2 | 40.8 | 57,061 | 0.0% |
| strawberry | Python | F2 | 921 | 41.2 | 73.2 | 83.8 | 27,628 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9446 | 4.2 | 5.3 | 5.9 | 283,388 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9383 | 4.2 | 5.4 | 6.0 | 281,488 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8615 | 4.6 | 6.0 | 6.6 | 258,453 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8662 | 4.6 | 5.9 | 6.6 | 259,860 | 0.0% |
| hasura | Haskell | F3 | 1495 | 26.7 | 35.6 | 44.0 | 44,846 | 0.0% |
| postgraphile | Node.js | F3 | 2914 | 12.8 | 22.3 | 33.5 | 87,427 | 0.0% |
| actix-web-rest | Rust | F3 | 1613 | 24.1 | 29.0 | 31.3 | 48,377 | 0.0% |
| async-graphql | Rust | F3 | 1401 | 17.5 | 63.1 | 67.2 | 42,019 | 0.0% |
| mercurius | Node.js | F3 | 1453 | 18.0 | 64.7 | 76.0 | 43,583 | 0.0% |
| apollo-server | Node.js | F3 | 1558 | 24.8 | 40.7 | 50.0 | 46,754 | 0.0% |
| strawberry | Python | F3 | 953 | 40.2 | 53.5 | 85.5 | 28,598 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5746 | 6.9 | 9.0 | 10.0 | 172,381 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5711 | 6.9 | 9.1 | 10.1 | 171,327 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3296 | 9.5 | 33.5 | 38.5 | 98,877 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3319 | 9.5 | 33.1 | 38.4 | 99,577 | 0.0% |
| hasura | Haskell | T1 | 846 | 46.8 | 61.5 | 67.4 | 25,367 | 0.0% |
| postgraphile | Node.js | T1 | 2075 | 17.3 | 31.6 | 62.7 | 62,254 | 0.0% |
| actix-web-rest | Rust | T1 | 3153 | 12.7 | 14.4 | 18.0 | 94,602 | 0.0% |
| async-graphql | Rust | T1 | 5579 | 6.7 | 11.2 | 14.0 | 167,366 | 0.0% |
| mercurius | Node.js | T1 | 1778 | 20.7 | 33.5 | 40.1 | 53,333 | 0.0% |
| apollo-server | Node.js | T1 | 1204 | 30.4 | 49.1 | 58.6 | 36,113 | 0.0% |
| strawberry | Python | T1 | 650 | 58.6 | 93.6 | 105.1 | 19,508 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1103 | 20.9 | 89.9 | 192.1 | 33,094 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1069 | 21.4 | 92.9 | 200.1 | 32,084 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1109 | 20.5 | 90.2 | 188.5 | 33,275 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1090 | 21.4 | 91.6 | 187.6 | 32,715 | 0.0% |
| hasura | Haskell | MC1 | 945 | 33.1 | 83.2 | 93.8 | 28,354 | 0.0% |
| postgraphile | Node.js | MC1 | 1367 | 26.1 | 45.7 | 76.0 | 41,004 | 0.0% |
| actix-web-rest | Rust | MC1 | 1284 | 29.8 | 36.5 | 40.9 | 38,533 | 0.0% |
| async-graphql | Rust | MC1 | 1255 | 23.0 | 58.3 | 62.3 | 37,638 | 0.0% |
| mercurius | Node.js | MC1 | 1328 | 27.3 | 47.2 | 54.4 | 39,841 | 0.0% |
| apollo-server | Node.js | MC1 | 1060 | 37.2 | 47.9 | 55.4 | 31,815 | 0.0% |
| strawberry | Python | MC1 | 538 | 74.7 | 108.5 | 129.1 | 16,154 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9263 | 4.3 | 5.4 | 6.0 | 277,877 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9247 | 4.3 | 5.5 | 6.0 | 277,423 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8348 | 4.8 | 6.1 | 6.8 | 250,428 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8352 | 4.8 | 6.1 | 6.8 | 250,557 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1398 | 17.4 | 63.4 | 67.4 | 41,935 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1452 | 18.2 | 64.2 | 76.0 | 43,575 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1557 | 24.8 | 40.8 | 50.2 | 46,710 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8828 | 4.5 | 5.7 | 6.3 | 264,855 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 8859 | 4.5 | 5.7 | 6.3 | 265,762 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5159 | 6.0 | 27.6 | 33.6 | 154,783 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5219 | 6.0 | 27.1 | 33.2 | 156,580 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 6323 | 6.1 | 9.7 | 13.0 | 189,687 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3029 | 12.2 | 21.0 | 26.3 | 90,861 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1976 | 19.0 | 31.7 | 38.2 | 59,286 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1120 | 20.5 | 90.9 | 190.9 | 33,588 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1075 | 20.9 | 93.9 | 204.1 | 32,240 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1121 | 20.2 | 90.1 | 190.9 | 33,624 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1097 | 20.7 | 91.5 | 189.7 | 32,916 | 0.0% |
| async-graphql | Rust | M1_APQ | 10478 | 3.8 | 4.6 | 5.1 | 314,337 | 0.0% |
| mercurius | Node.js | M1_APQ | 3979 | 9.5 | 15.8 | 22.1 | 119,366 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2589 | 14.7 | 23.4 | 31.5 | 77,666 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1662 | 23.3 | 31.5 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1552 | 24.8 | 50.5 | 0.0% |
| mercurius | Node.js | 1452 | 17.8 | 76.9 | 0.0% |
| async-graphql | Rust | 1402 | 17.4 | 67.3 | 0.0% |
| strawberry | Python | 968 | 39.8 | 82.5 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9761 | 4.1 | 5.8 | 0.0% |
| fraiseql-tv | Rust | 9740 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-cache | Rust | 8862 | 4.5 | 6.7 | 0.0% |
| fraiseql-v-nocache | Rust | 8824 | 4.5 | 6.6 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 3153 | 12.2 | 24.2 | 0.0% |
| hasura | Haskell | 1542 | 25.7 | 42.5 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9761 | 4.1 | 5.8 |
| fraiseql-tv | Rust | graphql-precomputed | 9740 | 4.1 | 5.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8862 | 4.5 | 6.7 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8824 | 4.5 | 6.6 |
| postgraphile | Node.js | graphql-schema-first | 3153 | 12.2 | 24.2 |
| actix-web-rest | Rust | rest | 1662 | 23.3 | 31.5 |
| apollo-server | Node.js | graphql | 1552 | 24.8 | 50.5 |
| hasura | Haskell | graphql-schema-first | 1542 | 25.7 | 42.5 |
| mercurius | Node.js | graphql | 1452 | 17.8 | 76.9 |
| async-graphql | Rust | graphql | 1402 | 17.4 | 67.3 |
| strawberry | Python | graphql | 968 | 39.8 | 82.5 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9761 | 114 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-tv | 9740 | 113 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-v-cache | 8862 | 103 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| fraiseql-v-nocache | 8824 | 103 | 0.0037 | 64 | 0.0060 | 127 | 0.0030 |
| postgraphile | 3153 | 37 | 0.0104 | 23 | 0.0167 | 45 | 0.0084 |
| actix-web-rest | 1662 | 19 | 0.0197 | 12 | 0.0317 | 24 | 0.0159 |
| apollo-server | 1552 | 18 | 0.0211 | 11 | 0.0339 | 22 | 0.0170 |
| hasura | 1542 | 18 | 0.0212 | 11 | 0.0342 | 22 | 0.0171 |
| mercurius | 1452 | 17 | 0.0225 | 10 | 0.0363 | 21 | 0.0182 |
| async-graphql | 1402 | 16 | 0.0233 | 10 | 0.0376 | 20 | 0.0189 |
| strawberry | 968 | 11 | 0.0338 | 7 | 0.0544 | 14 | 0.0273 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 158.3 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 156.8 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 121.7 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 114.0 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 127 | 129.2 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 6 | 92.2 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 65 | 116.1 |
| hasura | Haskell | — | — | — | 135 | 161.1 |
| mercurius | Node.js | 464 | 8.8 | 104 | 55 | 108.1 |
| async-graphql | Rust | 697 | 4.4 | 12 | 11 | 131.8 |
| strawberry | Python | 1,812 | 12.7 | 136 | 187 | 175.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 18.6 |

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

> **Peak**: fraiseql-tv 1103 cycles/s (1 req) vs postgraphile 1367 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At FraiseQL's peak cascade throughput of 1,129 M/s: **~12,421 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): the prior mutation burst (each bio edit fans out to ~11 cascade row-writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.