# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-09-27  
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
| Kernel | 6.8.0-138-generic |
| PostgreSQL | 17.11 (Debian 17.11-1.pgdg13+2) |
| Load generator | k6-v2.3.0 |
| Target host | 10.7.0.2 |
| `tv_*` persistence | logged (WAL-durable — publishable profile) |
| `tv_*` trigger scope | FraiseQL frameworks only — classical stacks mutate a vanilla tb_user (they never deploy pg_tviews) |
| Dataset | MEDIUM — 10 000 users · 50 000 posts · 200 000 comments |
| Concurrency | 40 workers |
| Measurement / warmup / cooldown | 30s / 10s / 5s |
| Passes | 1 |
| Run timestamp | 2026-09-27T10:24:26+00:00 |

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
| `tb_comment` | 294.4 MB | 82.4 MB | 376.8 MB |
| `tv_post` | 210.2 MB | 60.6 MB | 301.7 MB |
| `tb_post` | 133.6 MB | 19.6 MB | 153.2 MB |
| `tv_user` | 8.0 MB | 9.2 MB | 17.2 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tb_user` | 4.6 MB | 4.4 MB | 9.0 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `tb_mutation_log` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.31 GB  
**TB tables (normalized baseline)**: 560.3 MB  
**Storage amplification**: 3.40× (TV adds 1.31 GB on top of the normalized 560.3 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 7807 | 5.1 | 7.1 | 7.9 | 234,204 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 8008 | 4.8 | 7.1 | 7.9 | 240,230 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 7685 | 5.0 | 7.5 | 8.4 | 230,541 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 6968 | 5.5 | 8.3 | 9.4 | 209,043 | 0.0% |
| hasura | Haskell | Q1 | 2861 | 13.6 | 20.5 | 23.9 | 85,819 | 0.0% |
| postgraphile | Node.js | Q1 | 2949 | 13.0 | 20.3 | 25.6 | 88,465 | 0.0% |
| actix-web-rest | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q1 | 1248 | 20.6 | 65.7 | 70.3 | 37,442 | 0.0% |
| mercurius | Node.js | Q1 | 1331 | 19.8 | 70.0 | 81.2 | 39,932 | 0.0% |
| apollo-server | Node.js | Q1 | 1416 | 27.8 | 40.2 | 47.9 | 42,492 | 0.0% |
| strawberry | Python | Q1 | 861 | 44.7 | 60.8 | 91.5 | 25,821 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 8928 | 4.4 | 6.2 | 6.9 | 267,845 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 9022 | 4.3 | 6.2 | 7.0 | 270,663 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7028 | 5.0 | 9.1 | 25.0 | 210,827 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 6558 | 5.3 | 10.0 | 27.1 | 196,746 | 0.0% |
| hasura | Haskell | Q2 | 3071 | 12.7 | 15.5 | 22.4 | 92,128 | 0.0% |
| postgraphile | Node.js | Q2 | 3054 | 12.6 | 18.9 | 24.7 | 91,625 | 0.0% |
| actix-web-rest | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q2 | 4416 | 8.8 | 13.5 | 15.4 | 132,465 | 0.0% |
| mercurius | Node.js | Q2 | 4304 | 8.9 | 13.8 | 17.9 | 129,113 | 0.0% |
| apollo-server | Node.js | Q2 | 2923 | 13.2 | 20.2 | 24.2 | 87,688 | 0.0% |
| strawberry | Python | Q2 | 1277 | 29.7 | 36.9 | 75.6 | 38,305 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 7608 | 5.1 | 7.5 | 8.3 | 228,250 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 7600 | 5.1 | 7.4 | 8.2 | 228,007 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5268 | 6.2 | 23.2 | 32.4 | 158,043 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4892 | 6.8 | 24.7 | 33.6 | 146,770 | 0.0% |
| hasura | Haskell | Q2b | 2483 | 15.5 | 24.0 | 26.6 | 74,504 | 0.0% |
| postgraphile | Node.js | Q2b | 2536 | 15.3 | 22.3 | 28.1 | 76,070 | 0.0% |
| actix-web-rest | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q2b | 4538 | 8.0 | 15.1 | 17.5 | 136,128 | 0.0% |
| mercurius | Node.js | Q2b | 3105 | 12.1 | 18.8 | 24.0 | 93,152 | 0.0% |
| apollo-server | Node.js | Q2b | 1965 | 19.5 | 30.7 | 37.2 | 58,947 | 0.0% |
| strawberry | Python | Q2b | 911 | 48.9 | 65.3 | 104.6 | 27,317 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 5873 | 6.6 | 9.9 | 11.1 | 176,201 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 5864 | 6.6 | 9.9 | 11.1 | 175,930 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3362 | 9.4 | 34.7 | 41.7 | 100,870 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3200 | 9.9 | 35.8 | 42.7 | 95,989 | 0.0% |
| hasura | Haskell | Q3 | 1992 | 19.5 | 28.2 | 30.8 | 59,751 | 0.0% |
| postgraphile | Node.js | Q3 | 1482 | 26.1 | 39.9 | 47.1 | 44,460 | 0.0% |
| actix-web-rest | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q3 | 2111 | 17.4 | 33.8 | 40.4 | 63,342 | 0.0% |
| mercurius | Node.js | Q3 | 875 | 45.4 | 60.1 | 64.9 | 26,243 | 0.0% |
| apollo-server | Node.js | Q3 | 632 | 62.9 | 81.7 | 88.6 | 18,961 | 0.0% |
| strawberry | Python | Q3 | 473 | 83.6 | 129.5 | 163.5 | 14,184 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 9163 | 4.3 | 6.1 | 6.7 | 274,877 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 9316 | 4.2 | 6.0 | 6.7 | 279,470 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 9180 | 4.2 | 6.1 | 6.8 | 275,413 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 8580 | 4.5 | 6.5 | 7.2 | 257,413 | 0.0% |
| hasura | Haskell | C3 | 2693 | 14.5 | 21.7 | 25.4 | 80,777 | 0.0% |
| postgraphile | Node.js | C3 | 3695 | 10.4 | 15.6 | 20.7 | 110,858 | 0.0% |
| actix-web-rest | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | C3 | 11881 | 3.1 | 5.0 | 5.7 | 356,439 | 0.0% |
| mercurius | Node.js | C3 | 6003 | 6.3 | 10.0 | 13.5 | 180,079 | 0.0% |
| apollo-server | Node.js | C3 | 3516 | 10.9 | 16.6 | 20.4 | 105,480 | 0.0% |
| strawberry | Python | C3 | 1355 | 27.7 | 42.1 | 76.8 | 40,637 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 9432 | 4.1 | 6.0 | 6.7 | 282,957 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 9199 | 4.2 | 6.1 | 6.8 | 275,963 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 9049 | 4.3 | 6.2 | 6.8 | 271,460 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 8486 | 4.6 | 6.6 | 7.3 | 254,571 | 0.0% |
| hasura | Haskell | HC3 | 2695 | 14.4 | 21.8 | 25.6 | 80,858 | 0.0% |
| postgraphile | Node.js | HC3 | 3581 | 10.7 | 16.1 | 21.7 | 107,429 | 0.0% |
| actix-web-rest | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | HC3 | 12129 | 3.1 | 5.0 | 5.7 | 363,856 | 0.0% |
| mercurius | Node.js | HC3 | 6358 | 6.0 | 9.6 | 13.0 | 190,728 | 0.0% |
| apollo-server | Node.js | HC3 | 3393 | 11.4 | 17.1 | 21.2 | 101,776 | 0.0% |
| strawberry | Python | HC3 | 1349 | 27.9 | 39.5 | 79.1 | 40,475 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1060 | 21.7 | 94.8 | 195.0 | 31,788 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1107 | 21.0 | 91.2 | 183.2 | 33,222 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1049 | 21.8 | 96.1 | 196.2 | 31,464 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1030 | 22.9 | 96.8 | 194.4 | 30,887 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 909 | 26.1 | 105.0 | 226.9 | 27,284 | 0.0% |
| hasura | Haskell | M1 | 1617 | 24.1 | 32.0 | 35.1 | 48,505 | 0.0% |
| postgraphile | Node.js | M1 | 2823 | 13.0 | 20.7 | 36.6 | 84,681 | 0.0% |
| actix-web-rest | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | M1 | 7230 | 5.4 | 7.5 | 8.2 | 216,890 | 0.0% |
| mercurius | Node.js | M1 | 3786 | 10.1 | 14.6 | 19.9 | 113,595 | 0.0% |
| apollo-server | Node.js | M1 | 2355 | 16.1 | 23.1 | 28.7 | 70,651 | 0.0% |
| strawberry | Python | M1 | 1175 | 32.4 | 41.4 | 82.4 | 35,241 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 8708 | 4.5 | 6.5 | 7.2 | 261,240 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 8513 | 4.6 | 6.5 | 7.2 | 255,383 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 5940 | 5.4 | 21.6 | 31.8 | 178,196 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 5696 | 5.7 | 22.3 | 31.9 | 170,873 | 0.0% |
| hasura | Haskell | F1 | 2769 | 14.0 | 21.9 | 24.9 | 83,058 | 0.0% |
| postgraphile | Node.js | F1 | 3100 | 12.4 | 18.7 | 24.2 | 93,005 | 0.0% |
| actix-web-rest | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F1 | 4431 | 8.8 | 13.4 | 15.3 | 132,928 | 0.0% |
| mercurius | Node.js | F1 | 4164 | 9.2 | 14.1 | 18.3 | 124,911 | 0.0% |
| apollo-server | Node.js | F1 | 2778 | 13.9 | 21.0 | 25.4 | 83,330 | 0.0% |
| strawberry | Python | F1 | 1132 | 33.6 | 43.4 | 86.0 | 33,948 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 7238 | 5.4 | 7.7 | 8.6 | 217,127 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 7124 | 5.5 | 7.9 | 8.7 | 213,727 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4364 | 7.0 | 31.7 | 38.4 | 130,908 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4389 | 7.2 | 30.1 | 37.5 | 131,680 | 0.0% |
| hasura | Haskell | F2 | 2260 | 17.1 | 25.6 | 29.4 | 67,815 | 0.0% |
| postgraphile | Node.js | F2 | 2345 | 16.3 | 25.0 | 31.8 | 70,351 | 0.0% |
| actix-web-rest | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F2 | 4428 | 8.2 | 15.2 | 17.7 | 132,833 | 0.0% |
| mercurius | Node.js | F2 | 3099 | 12.2 | 18.8 | 23.6 | 92,960 | 0.0% |
| apollo-server | Node.js | F2 | 1847 | 20.9 | 32.0 | 38.6 | 55,405 | 0.0% |
| strawberry | Python | F2 | 836 | 46.4 | 75.4 | 96.1 | 25,067 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 7743 | 5.0 | 7.2 | 8.0 | 232,304 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 7661 | 5.1 | 7.2 | 8.0 | 229,819 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7033 | 5.5 | 8.0 | 9.0 | 210,977 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6951 | 5.6 | 8.2 | 9.2 | 208,520 | 0.0% |
| hasura | Haskell | F3 | 2832 | 13.8 | 18.1 | 24.2 | 84,946 | 0.0% |
| postgraphile | Node.js | F3 | 2830 | 13.6 | 20.8 | 26.2 | 84,889 | 0.0% |
| actix-web-rest | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F3 | 1265 | 20.3 | 65.5 | 70.4 | 37,963 | 0.0% |
| mercurius | Node.js | F3 | 1328 | 20.3 | 69.1 | 80.0 | 39,844 | 0.0% |
| apollo-server | Node.js | F3 | 1382 | 28.5 | 41.0 | 47.8 | 41,463 | 0.0% |
| strawberry | Python | F3 | 846 | 45.6 | 63.5 | 101.2 | 25,378 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4703 | 8.1 | 12.8 | 14.6 | 141,095 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4717 | 8.1 | 12.7 | 14.4 | 141,522 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3021 | 10.8 | 34.1 | 39.9 | 90,644 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3014 | 10.7 | 33.9 | 39.9 | 90,406 | 0.0% |
| hasura | Haskell | T1 | 1633 | 23.6 | 33.7 | 36.9 | 48,995 | 0.0% |
| postgraphile | Node.js | T1 | 2029 | 18.7 | 29.2 | 41.8 | 60,880 | 0.0% |
| actix-web-rest | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | T1 | 4241 | 9.1 | 14.2 | 16.2 | 127,242 | 0.0% |
| mercurius | Node.js | T1 | 1658 | 23.2 | 32.1 | 36.8 | 49,752 | 0.0% |
| apollo-server | Node.js | T1 | 1206 | 31.9 | 43.1 | 49.0 | 36,189 | 0.0% |
| strawberry | Python | T1 | 585 | 66.2 | 98.9 | 137.5 | 17,536 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1056 | 22.0 | 95.1 | 193.1 | 31,689 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1072 | 21.5 | 93.3 | 198.1 | 32,171 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 984 | 23.6 | 99.9 | 215.1 | 29,530 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 995 | 23.4 | 99.0 | 206.4 | 29,858 | 0.0% |
| hasura | Haskell | MC1 | 967 | 40.4 | 50.0 | 53.5 | 29,004 | 0.0% |
| postgraphile | Node.js | MC1 | 1278 | 28.9 | 47.1 | 67.8 | 38,328 | 0.0% |
| actix-web-rest | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | MC1 | 1139 | 26.5 | 60.6 | 64.8 | 34,183 | 0.0% |
| mercurius | Node.js | MC1 | 1184 | 31.2 | 52.4 | 60.4 | 35,531 | 0.0% |
| apollo-server | Node.js | MC1 | 925 | 42.6 | 57.1 | 65.4 | 27,745 | 0.0% |
| strawberry | Python | MC1 | 501 | 76.8 | 114.9 | 138.4 | 15,017 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 7368 | 5.3 | 7.6 | 8.4 | 221,050 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 7796 | 4.9 | 7.2 | 8.0 | 233,892 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6929 | 5.6 | 8.2 | 9.1 | 207,867 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 6562 | 5.9 | 8.6 | 9.6 | 196,852 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1293 | 19.6 | 64.9 | 69.3 | 38,791 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1306 | 20.4 | 70.0 | 80.6 | 39,191 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1368 | 29.1 | 40.9 | 46.7 | 41,041 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 7038 | 5.6 | 7.9 | 8.7 | 211,151 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 7324 | 5.3 | 7.6 | 8.4 | 219,735 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 4737 | 6.7 | 27.5 | 35.3 | 142,103 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4614 | 7.0 | 27.7 | 35.1 | 138,412 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 4589 | 7.9 | 14.8 | 17.3 | 137,668 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3098 | 12.2 | 18.8 | 23.7 | 92,944 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1940 | 19.8 | 30.7 | 37.0 | 58,195 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1059 | 21.5 | 93.8 | 200.3 | 31,777 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1112 | 20.9 | 90.5 | 184.3 | 33,368 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1009 | 23.0 | 98.6 | 206.2 | 30,278 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1023 | 23.2 | 96.8 | 195.2 | 30,676 | 0.0% |
| async-graphql | Rust | M1_APQ | 7468 | 5.4 | 7.1 | 7.7 | 224,045 | 0.0% |
| mercurius | Node.js | M1_APQ | 3757 | 10.2 | 14.9 | 19.8 | 112,701 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2420 | 15.7 | 22.6 | 27.9 | 72,595 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1416 | 27.8 | 47.9 | 0.0% |
| mercurius | Node.js | 1331 | 19.8 | 81.2 | 0.0% |
| async-graphql | Rust | 1248 | 20.6 | 70.3 | 0.0% |
| strawberry | Python | 861 | 44.7 | 91.5 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 8008 | 4.8 | 7.9 | 0.0% |
| fraiseql-tv | Rust | 7807 | 5.1 | 7.9 | 0.0% |
| fraiseql-v-nocache | Rust | 7685 | 5.0 | 8.4 | 0.0% |
| fraiseql-v-cache | Rust | 6968 | 5.5 | 9.4 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2949 | 13.0 | 25.6 | 0.0% |
| hasura | Haskell | 2861 | 13.6 | 23.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 8008 | 4.8 | 7.9 |
| fraiseql-tv | Rust | graphql-precomputed | 7807 | 5.1 | 7.9 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 7685 | 5.0 | 8.4 |
| fraiseql-v-cache | Rust | graphql-precomputed | 6968 | 5.5 | 9.4 |
| postgraphile | Node.js | graphql-schema-first | 2949 | 13.0 | 25.6 |
| hasura | Haskell | graphql-schema-first | 2861 | 13.6 | 23.9 |
| apollo-server | Node.js | graphql | 1416 | 27.8 | 47.9 |
| mercurius | Node.js | graphql | 1331 | 19.8 | 81.2 |
| async-graphql | Rust | graphql | 1248 | 20.6 | 70.3 |
| strawberry | Python | graphql | 861 | 44.7 | 91.5 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 8008 | 93 | 0.0041 | 58 | 0.0066 | 115 | 0.0033 |
| fraiseql-tv | 7807 | 91 | 0.0042 | 56 | 0.0068 | 112 | 0.0034 |
| fraiseql-v-nocache | 7685 | 89 | 0.0043 | 55 | 0.0069 | 111 | 0.0034 |
| fraiseql-v-cache | 6968 | 81 | 0.0047 | 50 | 0.0076 | 100 | 0.0038 |
| postgraphile | 2949 | 34 | 0.0111 | 21 | 0.0179 | 42 | 0.0090 |
| hasura | 2861 | 33 | 0.0114 | 21 | 0.0184 | 41 | 0.0092 |
| apollo-server | 1416 | 16 | 0.0231 | 10 | 0.0372 | 20 | 0.0187 |
| mercurius | 1331 | 15 | 0.0246 | 10 | 0.0396 | 19 | 0.0199 |
| async-graphql | 1248 | 15 | 0.0262 | 9 | 0.0422 | 18 | 0.0212 |
| strawberry | 861 | 10 | 0.0380 | 6 | 0.0612 | 12 | 0.0307 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 232 | 2.2 | 165 | 12 | 154.5 |
| fraiseql-tv | Rust | 232 | 2.2 | 165 | 11 | 154.4 |
| fraiseql-v-nocache | Rust | 343 | 1.7 | 165 | 11 | 115.5 |
| fraiseql-v-cache | Rust | 343 | 1.7 | 165 | 12 | 126.0 |
| postgraphile | Node.js | 112 | 7.1 | 848 | 122 | 122.6 |
| hasura | Haskell | — | — | — | 135 | 158.5 |
| apollo-server | Node.js | 758 | 7.5 | 512 | 64 | 114.2 |
| mercurius | Node.js | 464 | 8.8 | 390 | 61 | 110.4 |
| async-graphql | Rust | 697 | 4.4 | 46 | 12 | 131.2 |
| strawberry | Python | 1,812 | 12.7 | 548 | 178 | 174.0 |
| fraiseql-tv-audit | Rust | — | — | 166 | 11 | 18.8 |

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

> **Peak**: fraiseql-tv-cache 1072 cycles/s (1 req) vs postgraphile 1278 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At its peak of ~1,107 `updateUser(bio)` mutations/second, FraiseQL drives **~12,181 cascade row-writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): the prior mutation burst (each bio edit fans out to ~11 cascade row-writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.