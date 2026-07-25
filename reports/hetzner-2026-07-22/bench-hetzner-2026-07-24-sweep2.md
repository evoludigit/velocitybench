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
| Run timestamp | 2026-07-24T18:30:56+00:00 |

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
| `tv_post` | 210.4 MB | 68.7 MB | 310.7 MB |
| `tb_post` | 133.6 MB | 20.4 MB | 154.1 MB |
| `tb_mutation_log` | 36.4 MB | 2.9 MB | 39.3 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.7 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `bench_bio_snapshot` | 2.2 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.4 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 598.9 MB  
**Storage amplification**: 3.29× (TV adds 1.34 GB on top of the normalized 598.9 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9926 | 4.0 | 5.1 | 5.6 | 297,777 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9871 | 4.0 | 5.2 | 5.7 | 296,121 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8924 | 4.4 | 5.8 | 6.9 | 267,719 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8948 | 4.4 | 5.8 | 6.6 | 268,426 | 0.0% |
| hasura | Haskell | Q1 | 3628 | 10.6 | 17.2 | 19.5 | 108,852 | 0.0% |
| postgraphile | Node.js | Q1 | 3491 | 11.1 | 16.5 | 20.9 | 104,718 | 0.0% |
| actix-web-rest | Rust | Q1 | 1672 | 23.4 | 27.5 | 30.0 | 50,159 | 0.0% |
| async-graphql | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1 | 1446 | 17.9 | 65.6 | 77.8 | 43,382 | 0.0% |
| apollo-server | Node.js | Q1 | 1566 | 24.6 | 40.9 | 50.8 | 46,986 | 0.0% |
| strawberry | Python | Q1 | 996 | 38.7 | 50.2 | 76.2 | 29,870 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11298 | 3.5 | 4.5 | 5.1 | 338,945 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11197 | 3.5 | 4.6 | 5.1 | 335,896 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7511 | 4.5 | 14.8 | 25.1 | 225,334 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7464 | 4.4 | 16.1 | 25.6 | 223,932 | 0.0% |
| hasura | Haskell | Q2 | 3866 | 10.0 | 12.7 | 18.9 | 115,974 | 0.0% |
| postgraphile | Node.js | Q2 | 3962 | 9.7 | 14.8 | 19.0 | 118,868 | 0.0% |
| actix-web-rest | Rust | Q2 | 14046 | 2.8 | 3.3 | 3.7 | 421,393 | 0.0% |
| async-graphql | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2 | 4904 | 7.8 | 11.9 | 14.7 | 147,125 | 0.0% |
| apollo-server | Node.js | Q2 | 3100 | 12.5 | 18.6 | 21.6 | 92,989 | 0.0% |
| strawberry | Python | Q2 | 1399 | 27.1 | 35.3 | 60.2 | 41,976 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9380 | 4.2 | 5.4 | 6.0 | 281,397 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9323 | 4.3 | 5.4 | 6.0 | 279,683 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5364 | 5.7 | 27.5 | 33.8 | 160,905 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5353 | 5.8 | 27.5 | 33.8 | 160,594 | 0.0% |
| hasura | Haskell | Q2b | 3197 | 11.9 | 19.0 | 21.3 | 95,912 | 0.0% |
| postgraphile | Node.js | Q2b | 2915 | 13.3 | 19.0 | 23.4 | 87,444 | 0.0% |
| actix-web-rest | Rust | Q2b | 4872 | 8.2 | 9.2 | 9.7 | 146,170 | 0.0% |
| async-graphql | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b | 3441 | 11.1 | 16.6 | 20.4 | 103,223 | 0.0% |
| apollo-server | Node.js | Q2b | 2115 | 18.3 | 27.6 | 32.8 | 63,443 | 0.0% |
| strawberry | Python | Q2b | 1006 | 38.2 | 63.9 | 71.7 | 30,173 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7339 | 5.4 | 7.0 | 7.7 | 220,165 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7265 | 5.5 | 7.0 | 7.8 | 217,955 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3424 | 8.5 | 37.7 | 42.9 | 102,730 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3411 | 8.5 | 37.7 | 42.9 | 102,321 | 0.0% |
| hasura | Haskell | Q3 | 2615 | 14.7 | 22.0 | 24.1 | 78,444 | 0.0% |
| postgraphile | Node.js | Q3 | 1824 | 21.1 | 32.4 | 37.9 | 54,709 | 0.0% |
| actix-web-rest | Rust | Q3 | 4340 | 9.2 | 10.2 | 10.9 | 130,190 | 0.0% |
| async-graphql | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q3 | 1046 | 38.1 | 49.3 | 52.6 | 31,386 | 0.0% |
| apollo-server | Node.js | Q3 | 782 | 50.8 | 65.1 | 69.6 | 23,448 | 0.0% |
| strawberry | Python | Q3 | 539 | 71.1 | 109.1 | 115.7 | 16,163 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11611 | 3.4 | 4.4 | 4.8 | 348,331 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11723 | 3.4 | 4.3 | 4.8 | 351,679 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11428 | 3.5 | 4.4 | 4.9 | 342,850 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11250 | 3.5 | 4.5 | 4.9 | 337,492 | 0.0% |
| hasura | Haskell | C3 | 3480 | 11.0 | 17.6 | 20.1 | 104,406 | 0.0% |
| postgraphile | Node.js | C3 | 4332 | 8.9 | 13.3 | 17.6 | 129,956 | 0.0% |
| actix-web-rest | Rust | C3 | 18275 | 2.2 | 2.5 | 2.8 | 548,246 | 0.0% |
| async-graphql | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | C3 | 7408 | 5.1 | 8.0 | 10.7 | 222,232 | 0.0% |
| apollo-server | Node.js | C3 | 4203 | 9.2 | 13.7 | 16.5 | 126,091 | 0.0% |
| strawberry | Python | C3 | 1588 | 23.6 | 34.4 | 56.5 | 47,644 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11744 | 3.4 | 4.3 | 4.7 | 352,311 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11525 | 3.5 | 4.4 | 4.8 | 345,753 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11321 | 3.5 | 4.4 | 4.9 | 339,637 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11314 | 3.5 | 4.5 | 4.9 | 339,427 | 0.0% |
| hasura | Haskell | HC3 | 3472 | 11.1 | 17.3 | 20.0 | 104,146 | 0.0% |
| postgraphile | Node.js | HC3 | 4380 | 8.8 | 13.1 | 17.2 | 131,400 | 0.0% |
| actix-web-rest | Rust | HC3 | 18366 | 2.2 | 2.5 | 2.8 | 550,971 | 0.0% |
| async-graphql | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | HC3 | 7293 | 5.2 | 8.1 | 10.9 | 218,799 | 0.0% |
| apollo-server | Node.js | HC3 | 4230 | 9.1 | 13.6 | 16.5 | 126,909 | 0.0% |
| strawberry | Python | HC3 | 1615 | 23.2 | 35.6 | 56.1 | 48,451 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1144 | 19.5 | 89.8 | 190.1 | 34,310 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1131 | 20.4 | 90.4 | 182.6 | 33,922 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1118 | 20.1 | 92.2 | 187.8 | 33,540 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1119 | 20.0 | 92.1 | 193.1 | 33,575 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1068 | 21.5 | 94.0 | 186.0 | 32,026 | 0.0% |
| hasura | Haskell | M1 | 1964 | 19.2 | 26.9 | 31.5 | 58,931 | 0.0% |
| postgraphile | Node.js | M1 | 3578 | 10.4 | 16.1 | 21.7 | 107,342 | 0.0% |
| actix-web-rest | Rust | M1 | 5210 | 7.6 | 8.4 | 9.9 | 156,297 | 0.0% |
| async-graphql | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1 | 4422 | 8.7 | 12.3 | 16.6 | 132,656 | 0.0% |
| apollo-server | Node.js | M1 | 2769 | 13.6 | 19.5 | 24.7 | 83,064 | 0.0% |
| strawberry | Python | M1 | 1313 | 29.2 | 36.4 | 65.2 | 39,386 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10155 | 3.9 | 5.2 | 5.8 | 304,656 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 9980 | 4.0 | 5.3 | 5.9 | 299,402 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10639 | 3.7 | 4.8 | 5.4 | 319,156 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10518 | 3.8 | 4.9 | 5.4 | 315,555 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6929 | 4.7 | 19.4 | 28.7 | 207,878 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6836 | 4.7 | 19.7 | 28.4 | 205,079 | 0.0% |
| hasura | Haskell | F1 | 3503 | 11.0 | 17.3 | 19.5 | 105,100 | 0.0% |
| postgraphile | Node.js | F1 | 3731 | 10.3 | 15.5 | 20.0 | 111,924 | 0.0% |
| actix-web-rest | Rust | F1 | 13369 | 2.9 | 3.5 | 3.8 | 401,056 | 0.0% |
| async-graphql | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F1 | 4695 | 8.2 | 12.3 | 15.1 | 140,847 | 0.0% |
| apollo-server | Node.js | F1 | 3147 | 12.4 | 18.4 | 21.4 | 94,409 | 0.0% |
| strawberry | Python | F1 | 1291 | 30.5 | 41.8 | 69.9 | 38,737 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8908 | 4.5 | 5.7 | 6.3 | 267,226 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8881 | 4.5 | 5.7 | 6.3 | 266,420 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 5194 | 5.9 | 28.3 | 34.6 | 155,824 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 5196 | 5.9 | 28.3 | 34.3 | 155,885 | 0.0% |
| hasura | Haskell | F2 | 2864 | 13.3 | 20.5 | 22.7 | 85,915 | 0.0% |
| postgraphile | Node.js | F2 | 2819 | 13.5 | 21.0 | 26.5 | 84,582 | 0.0% |
| actix-web-rest | Rust | F2 | 4728 | 8.4 | 9.4 | 9.9 | 141,832 | 0.0% |
| async-graphql | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F2 | 3400 | 11.3 | 16.8 | 20.3 | 102,004 | 0.0% |
| apollo-server | Node.js | F2 | 2166 | 17.8 | 27.2 | 32.4 | 64,976 | 0.0% |
| strawberry | Python | F2 | 947 | 50.1 | 60.4 | 93.1 | 28,424 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9540 | 4.2 | 5.3 | 5.9 | 286,197 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9634 | 4.1 | 5.2 | 5.8 | 289,011 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8729 | 4.6 | 5.8 | 6.5 | 261,884 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8765 | 4.5 | 5.8 | 6.5 | 262,936 | 0.0% |
| hasura | Haskell | F3 | 3633 | 10.6 | 16.4 | 19.3 | 108,979 | 0.0% |
| postgraphile | Node.js | F3 | 3433 | 11.2 | 17.3 | 21.8 | 102,995 | 0.0% |
| actix-web-rest | Rust | F3 | 1594 | 24.6 | 28.6 | 31.4 | 47,825 | 0.0% |
| async-graphql | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F3 | 1449 | 17.9 | 64.9 | 76.7 | 43,456 | 0.0% |
| apollo-server | Node.js | F3 | 1561 | 24.7 | 40.8 | 50.7 | 46,822 | 0.0% |
| strawberry | Python | F3 | 979 | 46.9 | 72.3 | 104.3 | 29,384 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5810 | 6.8 | 8.9 | 9.9 | 174,307 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5821 | 6.8 | 8.9 | 9.9 | 174,631 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3408 | 9.2 | 32.6 | 37.5 | 102,232 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3359 | 9.4 | 32.9 | 38.0 | 100,757 | 0.0% |
| hasura | Haskell | T1 | 2166 | 17.4 | 25.7 | 28.2 | 64,972 | 0.0% |
| postgraphile | Node.js | T1 | 2468 | 15.5 | 23.8 | 30.1 | 74,042 | 0.0% |
| actix-web-rest | Rust | T1 | 3293 | 12.1 | 13.4 | 14.2 | 98,786 | 0.0% |
| async-graphql | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | T1 | 2000 | 19.0 | 26.0 | 29.8 | 60,009 | 0.0% |
| apollo-server | Node.js | T1 | 1440 | 26.5 | 35.4 | 39.9 | 43,212 | 0.0% |
| strawberry | Python | T1 | 665 | 57.8 | 92.1 | 101.9 | 19,964 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1125 | 20.1 | 91.8 | 188.5 | 33,753 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1118 | 20.7 | 90.7 | 187.4 | 33,547 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1108 | 20.6 | 90.6 | 190.9 | 33,246 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1106 | 20.1 | 92.7 | 204.4 | 33,193 | 0.0% |
| hasura | Haskell | MC1 | 1215 | 32.1 | 39.9 | 41.5 | 36,455 | 0.0% |
| postgraphile | Node.js | MC1 | 1539 | 24.4 | 36.4 | 46.3 | 46,161 | 0.0% |
| actix-web-rest | Rust | MC1 | 1353 | 29.0 | 33.2 | 35.2 | 40,593 | 0.0% |
| async-graphql | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | MC1 | 1336 | 27.1 | 47.6 | 54.5 | 40,091 | 0.0% |
| apollo-server | Node.js | MC1 | 1059 | 37.4 | 48.1 | 55.8 | 31,778 | 0.0% |
| strawberry | Python | MC1 | 566 | 68.7 | 103.2 | 115.1 | 16,976 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9413 | 4.2 | 5.3 | 5.9 | 282,377 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9449 | 4.2 | 5.3 | 5.9 | 283,459 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8459 | 4.7 | 6.1 | 6.8 | 253,767 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8430 | 4.7 | 6.0 | 6.7 | 252,899 | 0.0% |
| async-graphql | Rust | Q1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1_APQ | 1453 | 18.2 | 64.0 | 74.9 | 43,582 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1576 | 25.0 | 37.2 | 46.5 | 47,270 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9142 | 4.4 | 5.5 | 6.1 | 274,256 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9073 | 4.4 | 5.5 | 6.1 | 272,197 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5196 | 5.9 | 28.1 | 34.2 | 155,867 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5149 | 6.0 | 28.2 | 34.3 | 154,479 | 0.0% |
| async-graphql | Rust | Q2b_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b_APQ | 3434 | 11.1 | 16.7 | 20.5 | 103,010 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 2190 | 17.6 | 26.9 | 31.8 | 65,700 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1131 | 20.5 | 89.0 | 180.5 | 33,938 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1107 | 20.6 | 91.3 | 197.3 | 33,213 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1102 | 20.7 | 91.7 | 195.1 | 33,059 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1121 | 20.7 | 90.7 | 186.1 | 33,627 | 0.0% |
| async-graphql | Rust | M1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1_APQ | 4396 | 8.7 | 12.2 | 16.4 | 131,866 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2801 | 13.5 | 19.4 | 24.5 | 84,021 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1672 | 23.4 | 30.0 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1566 | 24.6 | 50.8 | 0.0% |
| mercurius | Node.js | 1446 | 17.9 | 77.8 | 0.0% |
| strawberry | Python | 996 | 38.7 | 76.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 9926 | 4.0 | 5.6 | 0.0% |
| fraiseql-tv-cache | Rust | 9871 | 4.0 | 5.7 | 0.0% |
| fraiseql-v-cache | Rust | 8948 | 4.4 | 6.6 | 0.0% |
| fraiseql-v-nocache | Rust | 8924 | 4.4 | 6.9 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 3628 | 10.6 | 19.5 | 0.0% |
| postgraphile | Node.js | 3491 | 11.1 | 20.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 9926 | 4.0 | 5.6 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 9871 | 4.0 | 5.7 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8948 | 4.4 | 6.6 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8924 | 4.4 | 6.9 |
| hasura | Haskell | graphql-schema-first | 3628 | 10.6 | 19.5 |
| postgraphile | Node.js | graphql-schema-first | 3491 | 11.1 | 20.9 |
| actix-web-rest | Rust | rest | 1672 | 23.4 | 30.0 |
| apollo-server | Node.js | graphql | 1566 | 24.6 | 50.8 |
| mercurius | Node.js | graphql | 1446 | 17.9 | 77.8 |
| strawberry | Python | graphql | 996 | 38.7 | 76.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 9926 | 115 | 0.0033 | 72 | 0.0053 | 143 | 0.0027 |
| fraiseql-tv-cache | 9871 | 115 | 0.0033 | 71 | 0.0053 | 142 | 0.0027 |
| fraiseql-v-cache | 8948 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| fraiseql-v-nocache | 8924 | 104 | 0.0037 | 64 | 0.0059 | 128 | 0.0030 |
| hasura | 3628 | 42 | 0.0090 | 26 | 0.0145 | 52 | 0.0073 |
| postgraphile | 3491 | 41 | 0.0094 | 25 | 0.0151 | 50 | 0.0076 |
| actix-web-rest | 1672 | 19 | 0.0196 | 12 | 0.0315 | 24 | 0.0158 |
| apollo-server | 1566 | 18 | 0.0209 | 11 | 0.0336 | 23 | 0.0169 |
| mercurius | 1446 | 17 | 0.0226 | 10 | 0.0364 | 21 | 0.0183 |
| strawberry | 996 | 12 | 0.0329 | 7 | 0.0529 | 14 | 0.0266 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 159.0 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 159.4 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 125.1 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 12 | 115.1 |
| hasura | Haskell | — | — | — | 134 | 160.7 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 127 | 119.1 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 105.0 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 66 | 112.5 |
| mercurius | Node.js | 464 | 8.8 | 104 | 57 | 105.5 |
| strawberry | Python | 1,812 | 12.7 | 136 | 180 | 175.3 |
| fraiseql-tv-audit | Rust | — | — | 43 | 11 | 20.1 |

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

> **Peak**: fraiseql-tv 1125 cycles/s (1 req) vs postgraphile 1539 cycles/s (2 req) — 0.7× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 5,210 M/s: **~57,308 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.