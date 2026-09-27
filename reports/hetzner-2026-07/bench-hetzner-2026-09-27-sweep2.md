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
| Run timestamp | 2026-09-27T12:32:32+00:00 |

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
| `tb_comment` | 294.4 MB | 82.4 MB | 376.8 MB |
| `tv_post` | 210.5 MB | 68.7 MB | 310.7 MB |
| `tb_post` | 133.6 MB | 19.6 MB | 153.2 MB |
| `tb_mutation_log` | 32.2 MB | 2.5 MB | 34.8 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `bench_bio_snapshot` | 2.2 MB | 0.0 MB | 2.3 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 593.8 MB  
**Storage amplification**: 3.31× (TV adds 1.34 GB on top of the normalized 593.8 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 7067 | 5.5 | 7.9 | 8.8 | 212,011 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 7429 | 5.2 | 7.6 | 8.4 | 222,880 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 7192 | 5.4 | 7.9 | 9.1 | 215,759 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7250 | 5.3 | 7.9 | 9.0 | 217,500 | 0.0% |
| hasura | Haskell | Q1 | 2828 | 13.8 | 20.8 | 24.4 | 84,828 | 0.0% |
| postgraphile | Node.js | Q1 | 2773 | 13.9 | 20.9 | 25.7 | 83,178 | 0.0% |
| actix-web-rest | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q1 | 1280 | 19.9 | 65.2 | 69.5 | 38,393 | 0.0% |
| mercurius | Node.js | Q1 | 1310 | 20.0 | 70.9 | 81.9 | 39,292 | 0.0% |
| apollo-server | Node.js | Q1 | 1404 | 27.7 | 41.1 | 49.8 | 42,121 | 0.0% |
| strawberry | Python | Q1 | 853 | 45.1 | 61.0 | 95.2 | 25,597 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 8235 | 4.7 | 6.9 | 7.7 | 247,057 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 8392 | 4.7 | 6.6 | 7.4 | 251,770 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 6500 | 5.2 | 13.7 | 27.1 | 194,991 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 6574 | 5.2 | 12.1 | 26.3 | 197,209 | 0.0% |
| hasura | Haskell | Q2 | 3114 | 12.5 | 18.7 | 22.9 | 93,405 | 0.0% |
| postgraphile | Node.js | Q2 | 3416 | 11.2 | 17.4 | 22.8 | 102,487 | 0.0% |
| actix-web-rest | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q2 | 4465 | 8.7 | 13.2 | 15.1 | 133,937 | 0.0% |
| mercurius | Node.js | Q2 | 4384 | 8.7 | 13.7 | 17.4 | 131,520 | 0.0% |
| apollo-server | Node.js | Q2 | 2799 | 13.8 | 20.9 | 25.2 | 83,956 | 0.0% |
| strawberry | Python | Q2 | 1254 | 30.4 | 37.7 | 73.8 | 37,625 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 6741 | 5.8 | 8.3 | 9.1 | 202,224 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 7087 | 5.5 | 7.9 | 8.8 | 212,618 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4794 | 6.8 | 26.2 | 34.2 | 143,831 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4794 | 6.7 | 26.5 | 34.7 | 143,819 | 0.0% |
| hasura | Haskell | Q2b | 2487 | 15.6 | 23.4 | 26.4 | 74,602 | 0.0% |
| postgraphile | Node.js | Q2b | 2515 | 15.4 | 22.7 | 28.8 | 75,448 | 0.0% |
| actix-web-rest | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q2b | 4486 | 8.0 | 15.2 | 17.9 | 134,571 | 0.0% |
| mercurius | Node.js | Q2b | 3171 | 11.9 | 18.4 | 23.3 | 95,119 | 0.0% |
| apollo-server | Node.js | Q2b | 1903 | 20.2 | 31.5 | 38.0 | 57,086 | 0.0% |
| strawberry | Python | Q2b | 888 | 52.1 | 67.7 | 103.1 | 26,636 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 5523 | 6.9 | 10.7 | 12.1 | 165,692 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 5716 | 6.7 | 10.3 | 11.6 | 171,469 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3138 | 9.8 | 37.4 | 43.9 | 94,126 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3121 | 9.8 | 37.8 | 44.2 | 93,624 | 0.0% |
| hasura | Haskell | Q3 | 1990 | 19.5 | 27.7 | 30.7 | 59,689 | 0.0% |
| postgraphile | Node.js | Q3 | 1539 | 25.0 | 38.6 | 45.3 | 46,170 | 0.0% |
| actix-web-rest | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | Q3 | 2027 | 18.7 | 34.8 | 40.7 | 60,817 | 0.0% |
| mercurius | Node.js | Q3 | 878 | 45.1 | 59.9 | 64.7 | 26,345 | 0.0% |
| apollo-server | Node.js | Q3 | 623 | 63.9 | 82.9 | 90.1 | 18,698 | 0.0% |
| strawberry | Python | Q3 | 475 | 84.8 | 128.9 | 150.9 | 14,262 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 8868 | 4.4 | 6.3 | 7.0 | 266,042 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 8898 | 4.4 | 6.2 | 6.8 | 266,939 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 8760 | 4.4 | 6.3 | 7.0 | 262,806 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 8411 | 4.7 | 6.5 | 7.2 | 252,341 | 0.0% |
| hasura | Haskell | C3 | 2695 | 14.4 | 21.6 | 25.4 | 80,859 | 0.0% |
| postgraphile | Node.js | C3 | 3667 | 10.4 | 15.9 | 20.4 | 110,019 | 0.0% |
| actix-web-rest | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | C3 | 13105 | 2.8 | 4.7 | 5.4 | 393,157 | 0.0% |
| mercurius | Node.js | C3 | 6120 | 6.2 | 9.8 | 13.2 | 183,615 | 0.0% |
| apollo-server | Node.js | C3 | 3614 | 10.6 | 16.2 | 20.1 | 108,418 | 0.0% |
| strawberry | Python | C3 | 1419 | 26.8 | 41.5 | 73.4 | 42,578 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 8762 | 4.5 | 6.4 | 7.0 | 262,848 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 8764 | 4.5 | 6.3 | 7.0 | 262,919 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 8562 | 4.6 | 6.5 | 7.1 | 256,872 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 8494 | 4.6 | 6.5 | 7.2 | 254,833 | 0.0% |
| hasura | Haskell | HC3 | 2705 | 14.4 | 20.8 | 24.6 | 81,150 | 0.0% |
| postgraphile | Node.js | HC3 | 3595 | 10.7 | 16.0 | 21.4 | 107,836 | 0.0% |
| actix-web-rest | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | HC3 | 12885 | 2.8 | 4.8 | 5.5 | 386,555 | 0.0% |
| mercurius | Node.js | HC3 | 6298 | 6.0 | 9.6 | 13.1 | 188,928 | 0.0% |
| apollo-server | Node.js | HC3 | 3538 | 10.9 | 16.6 | 20.4 | 106,148 | 0.0% |
| strawberry | Python | HC3 | 1356 | 27.9 | 38.9 | 78.8 | 40,680 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 973 | 24.4 | 99.3 | 198.8 | 29,184 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 976 | 23.7 | 99.9 | 211.6 | 29,275 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 965 | 24.3 | 102.4 | 207.2 | 28,937 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 985 | 23.7 | 99.8 | 209.8 | 29,558 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 960 | 24.6 | 100.7 | 211.9 | 28,791 | 0.0% |
| hasura | Haskell | M1 | 1604 | 24.1 | 32.9 | 36.8 | 48,112 | 0.0% |
| postgraphile | Node.js | M1 | 2864 | 12.8 | 20.8 | 34.9 | 85,934 | 0.0% |
| actix-web-rest | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | M1 | 6946 | 5.9 | 7.6 | 8.1 | 208,365 | 0.0% |
| mercurius | Node.js | M1 | 3840 | 10.0 | 14.6 | 19.9 | 115,203 | 0.0% |
| apollo-server | Node.js | M1 | 2369 | 15.9 | 23.2 | 29.3 | 71,072 | 0.0% |
| strawberry | Python | M1 | 1209 | 31.6 | 40.2 | 78.5 | 36,283 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 7842 | 5.0 | 7.2 | 8.0 | 235,248 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 7919 | 4.9 | 7.0 | 7.8 | 237,569 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 5628 | 5.6 | 25.0 | 33.0 | 168,827 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 5603 | 5.7 | 23.9 | 33.4 | 168,084 | 0.0% |
| hasura | Haskell | F1 | 2778 | 14.0 | 20.8 | 24.4 | 83,334 | 0.0% |
| postgraphile | Node.js | F1 | 3100 | 12.4 | 18.9 | 23.9 | 93,009 | 0.0% |
| actix-web-rest | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F1 | 4449 | 8.7 | 13.2 | 15.0 | 133,467 | 0.0% |
| mercurius | Node.js | F1 | 4325 | 8.8 | 13.7 | 17.8 | 129,740 | 0.0% |
| apollo-server | Node.js | F1 | 2768 | 14.0 | 21.3 | 25.9 | 83,033 | 0.0% |
| strawberry | Python | F1 | 1165 | 15.4 | 68.0 | 105.1 | 34,961 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 6505 | 6.0 | 8.7 | 9.6 | 195,143 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 6724 | 5.8 | 8.3 | 9.2 | 201,716 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 4233 | 7.3 | 32.3 | 39.5 | 126,996 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4353 | 7.2 | 31.1 | 38.4 | 130,577 | 0.0% |
| hasura | Haskell | F2 | 2221 | 17.5 | 25.6 | 29.0 | 66,642 | 0.0% |
| postgraphile | Node.js | F2 | 2474 | 15.4 | 24.2 | 31.2 | 74,233 | 0.0% |
| actix-web-rest | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F2 | 4361 | 8.4 | 15.3 | 17.7 | 130,831 | 0.0% |
| mercurius | Node.js | F2 | 3100 | 12.1 | 18.8 | 24.0 | 93,003 | 0.0% |
| apollo-server | Node.js | F2 | 1913 | 20.1 | 31.3 | 37.6 | 57,377 | 0.0% |
| strawberry | Python | F2 | 847 | 47.1 | 72.3 | 98.5 | 25,422 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 6858 | 5.8 | 8.1 | 8.9 | 205,755 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 7319 | 5.3 | 7.6 | 8.5 | 219,561 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6886 | 5.6 | 8.2 | 9.2 | 206,594 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6944 | 5.6 | 8.1 | 9.0 | 208,320 | 0.0% |
| hasura | Haskell | F3 | 2841 | 13.7 | 19.7 | 24.5 | 85,217 | 0.0% |
| postgraphile | Node.js | F3 | 2794 | 13.9 | 20.7 | 25.7 | 83,810 | 0.0% |
| actix-web-rest | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | F3 | 1281 | 19.9 | 65.1 | 70.1 | 38,442 | 0.0% |
| mercurius | Node.js | F3 | 1332 | 20.2 | 69.4 | 79.9 | 39,954 | 0.0% |
| apollo-server | Node.js | F3 | 1384 | 28.4 | 41.0 | 46.8 | 41,522 | 0.0% |
| strawberry | Python | F3 | 849 | 45.3 | 60.2 | 94.7 | 25,466 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4383 | 8.7 | 13.6 | 15.6 | 131,499 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4359 | 8.7 | 13.6 | 15.5 | 130,757 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3000 | 10.7 | 35.0 | 40.5 | 89,995 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2999 | 10.9 | 34.2 | 40.3 | 89,978 | 0.0% |
| hasura | Haskell | T1 | 1608 | 24.0 | 34.3 | 37.2 | 48,252 | 0.0% |
| postgraphile | Node.js | T1 | 2204 | 17.0 | 27.4 | 42.8 | 66,123 | 0.0% |
| actix-web-rest | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | T1 | 4246 | 9.0 | 14.1 | 16.1 | 127,373 | 0.0% |
| mercurius | Node.js | T1 | 1657 | 23.1 | 31.9 | 36.4 | 49,713 | 0.0% |
| apollo-server | Node.js | T1 | 1219 | 31.6 | 43.1 | 48.7 | 36,566 | 0.0% |
| strawberry | Python | T1 | 597 | 63.8 | 98.1 | 128.7 | 17,924 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 967 | 24.8 | 100.1 | 209.1 | 29,007 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 983 | 23.9 | 100.0 | 206.6 | 29,477 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1000 | 23.5 | 97.8 | 208.6 | 29,990 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 980 | 24.1 | 98.4 | 211.3 | 29,414 | 0.0% |
| hasura | Haskell | MC1 | 963 | 40.7 | 50.3 | 53.7 | 28,876 | 0.0% |
| postgraphile | Node.js | MC1 | 1283 | 28.8 | 46.0 | 66.7 | 38,488 | 0.0% |
| actix-web-rest | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| async-graphql | Rust | MC1 | 1117 | 26.7 | 62.0 | 66.0 | 33,506 | 0.0% |
| mercurius | Node.js | MC1 | 1190 | 30.8 | 52.7 | 60.4 | 35,689 | 0.0% |
| apollo-server | Node.js | MC1 | 904 | 43.5 | 58.3 | 68.3 | 27,133 | 0.0% |
| strawberry | Python | MC1 | 500 | 76.5 | 116.6 | 139.6 | 15,000 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 6630 | 6.0 | 8.3 | 9.1 | 198,891 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6646 | 6.0 | 8.2 | 9.1 | 199,376 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6722 | 5.8 | 8.4 | 9.4 | 201,671 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 6624 | 5.9 | 8.5 | 9.5 | 198,706 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1302 | 19.4 | 64.9 | 69.6 | 39,058 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1322 | 20.4 | 69.2 | 80.0 | 39,675 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1355 | 29.0 | 41.5 | 47.9 | 40,660 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 6587 | 5.9 | 8.5 | 9.3 | 197,598 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 6777 | 5.7 | 8.3 | 9.1 | 203,312 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 4641 | 6.9 | 27.4 | 35.6 | 139,226 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4661 | 6.9 | 27.0 | 35.5 | 139,842 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 4613 | 7.8 | 14.9 | 17.5 | 138,399 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 3106 | 12.2 | 19.0 | 23.6 | 93,188 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1910 | 20.1 | 31.1 | 37.3 | 57,315 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 965 | 24.8 | 100.6 | 208.5 | 28,939 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 992 | 23.7 | 98.1 | 201.4 | 29,760 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1007 | 23.4 | 97.8 | 199.3 | 30,199 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 986 | 23.8 | 100.4 | 203.1 | 29,572 | 0.0% |
| async-graphql | Rust | M1_APQ | 7748 | 5.1 | 6.9 | 7.4 | 232,428 | 0.0% |
| mercurius | Node.js | M1_APQ | 3790 | 10.1 | 14.6 | 19.7 | 113,697 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2408 | 15.8 | 22.9 | 28.8 | 72,227 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1404 | 27.7 | 49.8 | 0.0% |
| mercurius | Node.js | 1310 | 20.0 | 81.9 | 0.0% |
| async-graphql | Rust | 1280 | 19.9 | 69.5 | 0.0% |
| strawberry | Python | 853 | 45.1 | 95.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 7429 | 5.2 | 8.4 | 0.0% |
| fraiseql-v-cache | Rust | 7250 | 5.3 | 9.0 | 0.0% |
| fraiseql-v-nocache | Rust | 7192 | 5.4 | 9.1 | 0.0% |
| fraiseql-tv | Rust | 7067 | 5.5 | 8.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 2828 | 13.8 | 24.4 | 0.0% |
| postgraphile | Node.js | 2773 | 13.9 | 25.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 7429 | 5.2 | 8.4 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7250 | 5.3 | 9.0 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 7192 | 5.4 | 9.1 |
| fraiseql-tv | Rust | graphql-precomputed | 7067 | 5.5 | 8.8 |
| hasura | Haskell | graphql-schema-first | 2828 | 13.8 | 24.4 |
| postgraphile | Node.js | graphql-schema-first | 2773 | 13.9 | 25.7 |
| apollo-server | Node.js | graphql | 1404 | 27.7 | 49.8 |
| mercurius | Node.js | graphql | 1310 | 20.0 | 81.9 |
| async-graphql | Rust | graphql | 1280 | 19.9 | 69.5 |
| strawberry | Python | graphql | 853 | 45.1 | 95.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 7429 | 86 | 0.0044 | 54 | 0.0071 | 107 | 0.0036 |
| fraiseql-v-cache | 7250 | 84 | 0.0045 | 52 | 0.0073 | 104 | 0.0036 |
| fraiseql-v-nocache | 7192 | 84 | 0.0045 | 52 | 0.0073 | 103 | 0.0037 |
| fraiseql-tv | 7067 | 82 | 0.0046 | 51 | 0.0075 | 102 | 0.0037 |
| hasura | 2828 | 33 | 0.0116 | 20 | 0.0186 | 41 | 0.0094 |
| postgraphile | 2773 | 32 | 0.0118 | 20 | 0.0190 | 40 | 0.0095 |
| apollo-server | 1404 | 16 | 0.0233 | 10 | 0.0375 | 20 | 0.0188 |
| mercurius | 1310 | 15 | 0.0250 | 9 | 0.0402 | 19 | 0.0202 |
| async-graphql | 1280 | 15 | 0.0256 | 9 | 0.0412 | 18 | 0.0207 |
| strawberry | 853 | 10 | 0.0383 | 6 | 0.0618 | 12 | 0.0310 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 232 | 2.2 | 165 | 12 | 154.1 |
| fraiseql-v-cache | Rust | 343 | 1.7 | 165 | 12 | 124.5 |
| fraiseql-v-nocache | Rust | 343 | 1.7 | 165 | 12 | 115.3 |
| fraiseql-tv | Rust | 232 | 2.2 | 165 | 11 | 155.0 |
| hasura | Haskell | — | — | — | 135 | 154.6 |
| postgraphile | Node.js | 112 | 7.1 | 848 | 123 | 120.9 |
| apollo-server | Node.js | 758 | 7.5 | 512 | 65 | 114.7 |
| mercurius | Node.js | 464 | 8.8 | 390 | 56 | 109.5 |
| async-graphql | Rust | 697 | 4.4 | 46 | 12 | 131.9 |
| strawberry | Python | 1,812 | 12.7 | 548 | 178 | 174.9 |
| fraiseql-tv-audit | Rust | — | — | 166 | 11 | 18.4 |

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

> **Peak**: fraiseql-tv-cache 983 cycles/s (1 req) vs postgraphile 1283 cycles/s (2 req) — 0.8× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At its peak of ~985 `updateUser(bio)` mutations/second, FraiseQL drives **~10,837 cascade row-writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): the prior mutation burst (each bio edit fans out to ~11 cascade row-writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.