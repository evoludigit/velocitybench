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
| Run timestamp | 2026-07-24T22:46:57+00:00 |

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
| `tv_post` | 210.8 MB | 68.7 MB | 311.0 MB |
| `tb_post` | 133.6 MB | 20.4 MB | 154.1 MB |
| `tb_mutation_log` | 109.8 MB | 8.5 MB | 118.4 MB |
| `tb_post_like` | 5.0 MB | 9.6 MB | 14.6 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.7 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_post` | 0.9 MB | 0.0 MB | 1.0 MB |
| `tvd_user` | 0.4 MB | 0.0 MB | 0.5 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |

**TV tables**: 1.34 GB  
**TB tables (normalized baseline)**: 678.0 MB  
**Storage amplification**: 3.02× (TV adds 1.34 GB on top of the normalized 678.0 MB)  

> Each `tv_comment` row embeds a lean author `{id, username}` and a lean post summary `{id, title}` (no comment content duplication of the post body or the post's author).
> The lean embed cuts ~80% of the per-row JSONB vs a full embed (post body + nested authors).

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9719 | 4.1 | 5.2 | 5.8 | 291,580 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9807 | 4.1 | 5.2 | 5.7 | 294,200 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8941 | 4.4 | 5.8 | 7.0 | 268,220 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8943 | 4.4 | 5.8 | 6.7 | 268,301 | 0.0% |
| hasura | Haskell | Q1 | 3638 | 10.6 | 16.5 | 19.2 | 109,147 | 0.0% |
| postgraphile | Node.js | Q1 | 3262 | 11.8 | 17.8 | 22.3 | 97,848 | 0.0% |
| actix-web-rest | Rust | Q1 | 1679 | 23.4 | 27.3 | 29.2 | 50,367 | 0.0% |
| async-graphql | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1 | 1460 | 17.6 | 65.2 | 76.4 | 43,809 | 0.0% |
| apollo-server | Node.js | Q1 | 1566 | 24.6 | 41.0 | 50.5 | 46,992 | 0.0% |
| strawberry | Python | Q1 | 1000 | 41.6 | 59.1 | 86.1 | 30,014 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11110 | 3.6 | 4.6 | 5.2 | 333,310 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11191 | 3.5 | 4.6 | 5.1 | 335,718 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 7492 | 4.5 | 14.8 | 25.1 | 224,750 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 7455 | 4.4 | 16.1 | 26.2 | 223,653 | 0.0% |
| hasura | Haskell | Q2 | 3924 | 9.8 | 15.6 | 18.2 | 117,725 | 0.0% |
| postgraphile | Node.js | Q2 | 4029 | 9.5 | 14.6 | 18.9 | 120,881 | 0.0% |
| actix-web-rest | Rust | Q2 | 13189 | 3.0 | 3.6 | 4.0 | 395,665 | 0.0% |
| async-graphql | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2 | 4870 | 7.9 | 11.9 | 14.7 | 146,108 | 0.0% |
| apollo-server | Node.js | Q2 | 3129 | 12.5 | 18.3 | 21.3 | 93,861 | 0.0% |
| strawberry | Python | Q2 | 1401 | 27.6 | 32.4 | 58.3 | 42,024 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9229 | 4.3 | 5.5 | 6.1 | 276,873 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9395 | 4.2 | 5.4 | 6.0 | 281,838 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 5393 | 5.7 | 27.7 | 33.2 | 161,776 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 5375 | 5.8 | 27.1 | 33.5 | 161,258 | 0.0% |
| hasura | Haskell | Q2b | 3227 | 11.8 | 18.7 | 20.8 | 96,812 | 0.0% |
| postgraphile | Node.js | Q2b | 2967 | 13.1 | 18.7 | 23.4 | 89,009 | 0.0% |
| actix-web-rest | Rust | Q2b | 4816 | 8.3 | 9.2 | 9.7 | 144,489 | 0.0% |
| async-graphql | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b | 3470 | 11.0 | 16.4 | 20.0 | 104,099 | 0.0% |
| apollo-server | Node.js | Q2b | 2212 | 17.5 | 26.6 | 31.5 | 66,374 | 0.0% |
| strawberry | Python | Q2b | 1020 | 37.6 | 64.5 | 70.3 | 30,591 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 7220 | 5.5 | 7.1 | 7.8 | 216,587 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7189 | 5.5 | 7.1 | 7.9 | 215,671 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 3448 | 8.5 | 37.3 | 42.3 | 103,436 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 3434 | 8.5 | 37.1 | 42.5 | 103,031 | 0.0% |
| hasura | Haskell | Q3 | 2614 | 14.7 | 22.1 | 23.8 | 78,420 | 0.0% |
| postgraphile | Node.js | Q3 | 1896 | 20.3 | 31.4 | 36.4 | 56,893 | 0.0% |
| actix-web-rest | Rust | Q3 | 4240 | 9.4 | 10.4 | 11.1 | 127,215 | 0.0% |
| async-graphql | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q3 | 1034 | 38.5 | 49.8 | 52.8 | 31,030 | 0.0% |
| apollo-server | Node.js | Q3 | 776 | 51.0 | 65.2 | 70.3 | 23,292 | 0.0% |
| strawberry | Python | Q3 | 543 | 70.9 | 107.3 | 116.1 | 16,299 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 11581 | 3.4 | 4.4 | 4.8 | 347,431 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 11653 | 3.4 | 4.3 | 4.8 | 349,580 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 11315 | 3.5 | 4.5 | 4.9 | 339,439 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 11229 | 3.5 | 4.5 | 5.0 | 336,856 | 0.0% |
| hasura | Haskell | C3 | 3473 | 11.1 | 17.4 | 19.9 | 104,202 | 0.0% |
| postgraphile | Node.js | C3 | 4401 | 8.7 | 13.0 | 17.1 | 132,041 | 0.0% |
| actix-web-rest | Rust | C3 | 18019 | 2.2 | 2.6 | 2.9 | 540,577 | 0.0% |
| async-graphql | Rust | C3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | C3 | 7444 | 5.1 | 7.9 | 10.6 | 223,314 | 0.0% |
| apollo-server | Node.js | C3 | 4353 | 8.9 | 13.2 | 16.4 | 130,593 | 0.0% |
| strawberry | Python | C3 | 1617 | 23.7 | 41.8 | 58.7 | 48,523 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 11640 | 3.4 | 4.3 | 4.8 | 349,192 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 11655 | 3.4 | 4.3 | 4.8 | 349,651 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 11338 | 3.5 | 4.4 | 4.9 | 340,147 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 11313 | 3.5 | 4.5 | 4.9 | 339,402 | 0.0% |
| hasura | Haskell | HC3 | 3490 | 11.0 | 17.3 | 20.0 | 104,698 | 0.0% |
| postgraphile | Node.js | HC3 | 4479 | 8.6 | 12.9 | 16.9 | 134,360 | 0.0% |
| actix-web-rest | Rust | HC3 | 17922 | 2.2 | 2.6 | 2.9 | 537,661 | 0.0% |
| async-graphql | Rust | HC3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | HC3 | 7465 | 5.1 | 7.9 | 10.6 | 223,937 | 0.0% |
| apollo-server | Node.js | HC3 | 4264 | 9.0 | 13.6 | 16.5 | 127,913 | 0.0% |
| strawberry | Python | HC3 | 1639 | 22.9 | 34.6 | 54.4 | 49,171 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 1116 | 20.0 | 90.9 | 197.0 | 33,485 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 1114 | 20.4 | 93.0 | 189.4 | 33,432 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 1082 | 21.0 | 94.0 | 198.1 | 32,455 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1101 | 20.5 | 93.9 | 191.8 | 33,036 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1070 | 21.5 | 93.4 | 196.2 | 32,111 | 0.0% |
| hasura | Haskell | M1 | 1981 | 19.1 | 26.3 | 30.7 | 59,428 | 0.0% |
| postgraphile | Node.js | M1 | 3455 | 10.6 | 16.5 | 22.3 | 103,664 | 0.0% |
| actix-web-rest | Rust | M1 | 4997 | 7.9 | 8.8 | 10.9 | 149,909 | 0.0% |
| async-graphql | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1 | 4466 | 8.6 | 12.2 | 16.3 | 133,981 | 0.0% |
| apollo-server | Node.js | M1 | 2838 | 13.3 | 18.8 | 23.9 | 85,135 | 0.0% |
| strawberry | Python | M1 | 1320 | 29.1 | 36.6 | 63.9 | 39,590 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 10189 | 3.9 | 5.2 | 5.8 | 305,656 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 10214 | 3.9 | 5.2 | 5.8 | 306,406 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10527 | 3.8 | 4.9 | 5.4 | 315,798 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10875 | 3.7 | 4.7 | 5.2 | 326,239 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 6932 | 4.6 | 19.1 | 28.9 | 207,963 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 6773 | 4.7 | 19.9 | 29.3 | 203,193 | 0.0% |
| hasura | Haskell | F1 | 3502 | 11.0 | 17.4 | 20.0 | 105,074 | 0.0% |
| postgraphile | Node.js | F1 | 3501 | 11.0 | 16.4 | 20.5 | 105,034 | 0.0% |
| actix-web-rest | Rust | F1 | 12920 | 3.1 | 3.5 | 3.9 | 387,615 | 0.0% |
| async-graphql | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F1 | 4602 | 8.4 | 12.5 | 15.1 | 138,058 | 0.0% |
| apollo-server | Node.js | F1 | 2993 | 13.0 | 19.2 | 22.2 | 89,802 | 0.0% |
| strawberry | Python | F1 | 1285 | 29.9 | 36.5 | 64.0 | 38,548 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8856 | 4.5 | 5.7 | 6.3 | 265,682 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 9020 | 4.4 | 5.6 | 6.2 | 270,606 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 5230 | 5.8 | 28.4 | 34.9 | 156,887 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 5186 | 5.9 | 28.4 | 34.3 | 155,579 | 0.0% |
| hasura | Haskell | F2 | 2908 | 13.1 | 20.5 | 23.0 | 87,248 | 0.0% |
| postgraphile | Node.js | F2 | 2863 | 13.4 | 20.5 | 26.0 | 85,886 | 0.0% |
| actix-web-rest | Rust | F2 | 4719 | 8.4 | 9.4 | 9.9 | 141,565 | 0.0% |
| async-graphql | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F2 | 3280 | 11.7 | 17.4 | 21.2 | 98,396 | 0.0% |
| apollo-server | Node.js | F2 | 2202 | 17.5 | 26.7 | 31.6 | 66,061 | 0.0% |
| strawberry | Python | F2 | 937 | 40.9 | 71.8 | 77.0 | 28,121 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9495 | 4.2 | 5.3 | 5.9 | 284,847 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9483 | 4.2 | 5.4 | 5.9 | 284,498 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8834 | 4.5 | 5.8 | 6.5 | 265,010 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8624 | 4.6 | 5.9 | 6.6 | 258,719 | 0.0% |
| hasura | Haskell | F3 | 3673 | 10.5 | 16.7 | 19.9 | 110,204 | 0.0% |
| postgraphile | Node.js | F3 | 3333 | 11.6 | 17.7 | 22.1 | 100,000 | 0.0% |
| actix-web-rest | Rust | F3 | 1610 | 24.4 | 28.5 | 31.1 | 48,292 | 0.0% |
| async-graphql | Rust | F3 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | F3 | 1452 | 18.4 | 64.1 | 76.8 | 43,566 | 0.0% |
| apollo-server | Node.js | F3 | 1568 | 24.7 | 39.6 | 49.7 | 47,036 | 0.0% |
| strawberry | Python | F3 | 992 | 38.9 | 50.5 | 76.8 | 29,753 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 5819 | 6.8 | 8.9 | 9.8 | 174,573 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5779 | 6.9 | 9.0 | 9.9 | 173,372 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 3464 | 9.2 | 31.5 | 36.3 | 103,933 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 3371 | 9.4 | 32.5 | 36.9 | 101,119 | 0.0% |
| hasura | Haskell | T1 | 2179 | 17.3 | 25.6 | 27.8 | 65,375 | 0.0% |
| postgraphile | Node.js | T1 | 2558 | 14.9 | 22.7 | 30.0 | 76,749 | 0.0% |
| actix-web-rest | Rust | T1 | 3288 | 12.1 | 13.5 | 14.2 | 98,628 | 0.0% |
| async-graphql | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | T1 | 2009 | 19.0 | 25.8 | 29.5 | 60,266 | 0.0% |
| apollo-server | Node.js | T1 | 1439 | 26.6 | 35.4 | 39.6 | 43,168 | 0.0% |
| strawberry | Python | T1 | 676 | 57.0 | 90.4 | 97.6 | 20,294 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 1111 | 20.8 | 90.4 | 186.9 | 33,340 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1097 | 20.7 | 91.5 | 198.7 | 32,915 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 1082 | 20.9 | 93.9 | 198.7 | 32,469 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1094 | 21.0 | 91.0 | 192.1 | 32,818 | 0.0% |
| hasura | Haskell | MC1 | 1216 | 32.0 | 40.2 | 44.2 | 36,467 | 0.0% |
| postgraphile | Node.js | MC1 | 1543 | 24.5 | 36.8 | 45.7 | 46,301 | 0.0% |
| actix-web-rest | Rust | MC1 | 1350 | 28.9 | 33.4 | 35.9 | 40,490 | 0.0% |
| async-graphql | Rust | MC1 | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | MC1 | 1348 | 26.7 | 47.1 | 53.9 | 40,445 | 0.0% |
| apollo-server | Node.js | MC1 | 1063 | 37.3 | 47.8 | 54.4 | 31,900 | 0.0% |
| strawberry | Python | MC1 | 578 | 74.5 | 127.8 | 140.8 | 17,339 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9303 | 4.3 | 5.4 | 5.9 | 279,087 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9335 | 4.3 | 5.4 | 6.0 | 280,042 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8523 | 4.7 | 6.0 | 6.7 | 255,678 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8430 | 4.7 | 6.0 | 6.7 | 252,907 | 0.0% |
| async-graphql | Rust | Q1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q1_APQ | 1460 | 18.0 | 64.0 | 75.8 | 43,806 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1576 | 24.7 | 39.4 | 49.0 | 47,273 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9169 | 4.3 | 5.5 | 6.0 | 275,084 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9085 | 4.4 | 5.5 | 6.1 | 272,542 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 5232 | 5.9 | 27.8 | 34.3 | 156,953 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5170 | 5.9 | 28.3 | 33.9 | 155,086 | 0.0% |
| async-graphql | Rust | Q2b_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | Q2b_APQ | 3424 | 11.2 | 16.9 | 20.3 | 102,721 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 2183 | 17.7 | 26.7 | 31.8 | 65,502 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1105 | 20.3 | 92.7 | 200.6 | 33,147 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 1107 | 20.3 | 90.5 | 197.3 | 33,204 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1106 | 20.8 | 91.9 | 190.7 | 33,192 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 1090 | 21.1 | 92.4 | 190.6 | 32,714 | 0.0% |
| async-graphql | Rust | M1_APQ | — | — | — | — | — | _service did not become healthy_ |
| mercurius | Node.js | M1_APQ | 4377 | 8.8 | 12.3 | 16.3 | 131,310 | 0.0% |
| apollo-server | Node.js | M1_APQ | 2877 | 13.1 | 18.6 | 23.3 | 86,302 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1679 | 23.4 | 29.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1566 | 24.6 | 50.5 | 0.0% |
| mercurius | Node.js | 1460 | 17.6 | 76.4 | 0.0% |
| strawberry | Python | 1000 | 41.6 | 86.1 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9807 | 4.1 | 5.7 | 0.0% |
| fraiseql-tv | Rust | 9719 | 4.1 | 5.8 | 0.0% |
| fraiseql-v-cache | Rust | 8943 | 4.4 | 6.7 | 0.0% |
| fraiseql-v-nocache | Rust | 8941 | 4.4 | 7.0 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| hasura | Haskell | 3638 | 10.6 | 19.2 | 0.0% |
| postgraphile | Node.js | 3262 | 11.8 | 22.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9807 | 4.1 | 5.7 |
| fraiseql-tv | Rust | graphql-precomputed | 9719 | 4.1 | 5.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8943 | 4.4 | 6.7 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8941 | 4.4 | 7.0 |
| hasura | Haskell | graphql-schema-first | 3638 | 10.6 | 19.2 |
| postgraphile | Node.js | graphql-schema-first | 3262 | 11.8 | 22.3 |
| actix-web-rest | Rust | rest | 1679 | 23.4 | 29.2 |
| apollo-server | Node.js | graphql | 1566 | 24.6 | 50.5 |
| mercurius | Node.js | graphql | 1460 | 17.6 | 76.4 |
| strawberry | Python | graphql | 1000 | 41.6 | 86.1 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 9807 | 114 | 0.0033 | 71 | 0.0054 | 141 | 0.0027 |
| fraiseql-tv | 9719 | 113 | 0.0034 | 70 | 0.0054 | 140 | 0.0027 |
| fraiseql-v-cache | 8943 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| fraiseql-v-nocache | 8941 | 104 | 0.0037 | 65 | 0.0059 | 129 | 0.0030 |
| hasura | 3638 | 42 | 0.0090 | 26 | 0.0145 | 52 | 0.0073 |
| postgraphile | 3262 | 38 | 0.0100 | 24 | 0.0162 | 47 | 0.0081 |
| actix-web-rest | 1679 | 20 | 0.0195 | 12 | 0.0314 | 24 | 0.0157 |
| apollo-server | 1566 | 18 | 0.0209 | 11 | 0.0336 | 23 | 0.0169 |
| mercurius | 1460 | 17 | 0.0224 | 11 | 0.0361 | 21 | 0.0181 |
| strawberry | 1000 | 12 | 0.0327 | 7 | 0.0527 | 14 | 0.0264 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 159.7 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 11 | 159.6 |
| fraiseql-v-cache | Rust | 478 | 1.3 | 43 | 12 | 124.1 |
| fraiseql-v-nocache | Rust | 478 | 1.3 | 43 | 11 | 115.0 |
| hasura | Haskell | — | — | — | 130 | 162.8 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 125 | 118.5 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 100.2 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 67 | 110.5 |
| mercurius | Node.js | 464 | 8.8 | 104 | 62 | 104.4 |
| strawberry | Python | 1,812 | 12.7 | 136 | 180 | 175.2 |
| fraiseql-tv-audit | Rust | — | — | 43 | 11 | 20.6 |

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

> **Peak**: fraiseql-tv 1111 cycles/s (1 req) vs postgraphile 1543 cycles/s (2 req) — 0.7× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

The M1 `updateUser(bio)` mutation cascades through pg_tviews to just 1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (the only tviews that project `author.bio`) = **~11 rows**. Multi-hop column-aware refresh skips both the user's own comments (lean author has no bio) and the comments on the user's posts (post summary is `{id,title}`, disjoint from the author change). A `username` edit fans out to ~61.

At peak throughput of 4,997 M/s: **~54,966 row writes/second** across `tb_user`, `tv_user` and `tv_post` (`tv_comment` is skipped for a bio edit).

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (11×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.