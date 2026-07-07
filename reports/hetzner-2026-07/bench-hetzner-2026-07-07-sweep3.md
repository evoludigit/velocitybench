# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-07-07  
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
| Kernel | 6.8.0-124-generic |
| PostgreSQL | 17.10 (Debian 17.10-1.pgdg13+1) |
| Load generator | k6-v2.0.0 |
| Target host | 10.7.0.2 |
| `tv_*` persistence | logged (WAL-durable — publishable profile) |
| `tv_*` trigger scope | FraiseQL frameworks only — classical stacks mutate a vanilla tb_user (they never deploy pg_tviews) |
| Dataset | MEDIUM — 10 000 users · 50 000 posts · 200 000 comments |
| Concurrency | 40 workers |
| Measurement / warmup / cooldown | 30s / 10s / 5s |
| Passes | 1 |
| Run timestamp | 2026-07-07T12:38:33+00:00 |

### Framework Versions

| Framework | Version |
|-----------|---------|
| fraiseql-tv | 2.11.0 |
| fraiseql-tv-audit | 2.11.0 |
| fraiseql-tv-cache | 2.11.0 |
| fraiseql-v-cache | 2.11.0 |
| fraiseql-v-nocache | 2.11.0 |
| hasura | v2.49.3-ce |
| postgraphile | 5.0.3 |
| strawberry | 1.0.0 |

## Reading These Numbers

- **Same-run rule**: every number below comes from one sequential sweep on one host. Compare rows within this report only — never across reports or hardware.
- **Q1 honesty note**: Q1 is a flat 20-row SELECT — the scenario where a schema-to-API engine has the least to offer over a hand-tuned endpoint, and FraiseQL's position there is mid-pack. The architectural gap appears in nested reads (Q2b, Q3), mutations (M1), and consistency cycles (MC1).
- **Errors disqualify**: a row with a non-zero error count is reported but not comparable; publishable tables require 0% errors.

---
## Database Footprint

TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.
Views (v_*) add no storage — they are computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `tv_comment` | 693.0 MB | 322.3 MB | 1.62 GB |
| `tb_comment` | 294.7 MB | 81.5 MB | 376.4 MB |
| `tv_post` | 200.8 MB | 72.2 MB | 322.2 MB |
| `tb_post` | 133.8 MB | 19.8 MB | 153.7 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.7 MB | 3.1 MB | 7.8 MB |
| `tb_mutation_log` | 6.6 MB | 0.6 MB | 7.2 MB |
| `tb_user_follows` | 2.1 MB | 4.6 MB | 6.8 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 566.2 MB  
**Storage amplification**: 4.53× (TV adds 1.95 GB on top of the normalized 566.2 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 6599 | 5.9 | 8.4 | 9.4 | 197,969 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 6495 | 6.0 | 8.5 | 9.6 | 194,848 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 6413 | 6.1 | 8.6 | 9.8 | 192,377 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 6451 | 6.1 | 8.6 | 9.8 | 193,525 | 0.0% |
| hasura | Haskell | Q1 | 1060 | 37.6 | 47.2 | 54.0 | 31,796 | 0.0% |
| postgraphile | Node.js | Q1 | 2048 | 18.8 | 28.3 | 38.8 | 61,440 | 0.0% |
| actix-web-rest | Rust | Q1 | 1339 | 29.2 | 34.7 | 40.2 | 40,182 | 0.0% |
| async-graphql | Rust | Q1 | 1144 | 22.8 | 68.6 | 73.6 | 34,334 | 0.0% |
| mercurius | Node.js | Q1 | 1216 | 22.4 | 72.3 | 81.7 | 36,489 | 0.0% |
| apollo-server | Node.js | Q1 | 1295 | 30.3 | 43.6 | 52.7 | 38,856 | 0.0% |
| strawberry | Python | Q1 | 856 | 45.1 | 62.0 | 78.5 | 25,695 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 7194 | 5.4 | 7.6 | 8.5 | 215,806 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7218 | 5.4 | 7.6 | 8.5 | 216,537 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5592 | 6.1 | 19.0 | 29.3 | 167,760 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5659 | 6.0 | 19.5 | 28.4 | 169,759 | 0.0% |
| hasura | Haskell | Q2 | 1130 | 35.6 | 44.6 | 51.8 | 33,908 | 0.0% |
| postgraphile | Node.js | Q2 | 2147 | 17.6 | 28.4 | 40.7 | 64,404 | 0.0% |
| actix-web-rest | Rust | Q2 | 8824 | 4.4 | 5.6 | 6.7 | 264,734 | 0.0% |
| async-graphql | Rust | Q2 | 6249 | 6.0 | 9.6 | 10.8 | 187,475 | 0.0% |
| mercurius | Node.js | Q2 | 2851 | 13.2 | 21.7 | 29.1 | 85,530 | 0.0% |
| apollo-server | Node.js | Q2 | 2060 | 18.6 | 29.0 | 37.9 | 61,791 | 0.0% |
| strawberry | Python | Q2 | 1256 | 30.7 | 35.9 | 59.4 | 37,688 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 6139 | 6.3 | 9.2 | 10.8 | 184,169 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 6249 | 6.3 | 8.7 | 9.7 | 187,462 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4097 | 7.6 | 31.4 | 38.4 | 122,912 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4082 | 7.5 | 32.9 | 39.0 | 122,459 | 0.0% |
| hasura | Haskell | Q2b | 947 | 43.0 | 54.5 | 58.8 | 28,403 | 0.0% |
| postgraphile | Node.js | Q2b | 1953 | 19.7 | 29.5 | 39.9 | 58,589 | 0.0% |
| actix-web-rest | Rust | Q2b | 4250 | 9.2 | 11.1 | 13.7 | 127,507 | 0.0% |
| async-graphql | Rust | Q2b | 4195 | 8.7 | 16.0 | 20.2 | 125,844 | 0.0% |
| mercurius | Node.js | Q2b | 2196 | 16.8 | 29.2 | 37.9 | 65,876 | 0.0% |
| apollo-server | Node.js | Q2b | 1439 | 26.3 | 42.9 | 52.8 | 43,180 | 0.0% |
| strawberry | Python | Q2b | 853 | 39.0 | 72.6 | 98.8 | 25,587 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 3207 | 10.4 | 32.3 | 39.8 | 96,221 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 3176 | 10.2 | 34.1 | 40.7 | 95,293 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1302 | 19.8 | 72.9 | 90.4 | 39,046 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1301 | 20.0 | 72.6 | 90.4 | 39,042 | 0.0% |
| hasura | Haskell | Q3 | 820 | 49.3 | 61.7 | 66.2 | 24,595 | 0.0% |
| postgraphile | Node.js | Q3 | 1177 | 31.4 | 57.4 | 74.8 | 35,309 | 0.0% |
| actix-web-rest | Rust | Q3 | 3281 | 11.9 | 14.1 | 15.1 | 98,441 | 0.0% |
| async-graphql | Rust | Q3 | 1421 | 27.3 | 50.8 | 61.9 | 42,632 | 0.0% |
| mercurius | Node.js | Q3 | 677 | 57.3 | 85.4 | 97.0 | 20,310 | 0.0% |
| apollo-server | Node.js | Q3 | 496 | 79.7 | 113.4 | 129.0 | 14,876 | 0.0% |
| strawberry | Python | Q3 | 462 | 80.2 | 119.8 | 152.3 | 13,849 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 7645 | 5.1 | 7.1 | 7.9 | 229,356 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 7628 | 5.1 | 7.1 | 7.9 | 228,849 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7485 | 5.2 | 7.2 | 8.0 | 224,536 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7017 | 5.5 | 8.0 | 9.4 | 210,513 | 0.0% |
| hasura | Haskell | C3 | 969 | 41.3 | 51.9 | 57.2 | 29,076 | 0.0% |
| postgraphile | Node.js | C3 | 2454 | 15.4 | 23.9 | 38.1 | 73,617 | 0.0% |
| actix-web-rest | Rust | C3 | 10941 | 3.6 | 4.3 | 5.1 | 328,240 | 0.0% |
| async-graphql | Rust | C3 | 10723 | 3.6 | 5.4 | 6.2 | 321,680 | 0.0% |
| mercurius | Node.js | C3 | 3861 | 9.7 | 16.0 | 21.0 | 115,826 | 0.0% |
| apollo-server | Node.js | C3 | 2331 | 16.3 | 25.7 | 32.6 | 69,918 | 0.0% |
| strawberry | Python | C3 | 1337 | 29.1 | 37.1 | 60.4 | 40,120 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 7656 | 5.1 | 7.1 | 7.8 | 229,688 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 7601 | 5.2 | 7.1 | 7.9 | 228,016 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 7526 | 5.2 | 7.2 | 7.9 | 225,790 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7412 | 5.3 | 7.3 | 8.2 | 222,374 | 0.0% |
| hasura | Haskell | HC3 | 981 | 41.0 | 51.1 | 56.0 | 29,442 | 0.0% |
| postgraphile | Node.js | HC3 | 2330 | 16.1 | 25.9 | 40.7 | 69,895 | 0.0% |
| actix-web-rest | Rust | HC3 | 11018 | 3.6 | 4.1 | 4.5 | 330,532 | 0.0% |
| async-graphql | Rust | HC3 | 10667 | 3.6 | 5.4 | 6.4 | 320,007 | 0.0% |
| mercurius | Node.js | HC3 | 3873 | 9.7 | 15.8 | 20.6 | 116,176 | 0.0% |
| apollo-server | Node.js | HC3 | 2275 | 16.7 | 25.9 | 33.6 | 68,242 | 0.0% |
| strawberry | Python | HC3 | 1275 | 30.1 | 41.5 | 63.3 | 38,252 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 89 | 223.0 | 1593.8 | 3348.6 | 2,658 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 90 | 194.8 | 1766.8 | 4320.1 | 2,702 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 91 | 190.0 | 1706.9 | 4393.8 | 2,719 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 92 | 208.7 | 1507.4 | 2923.1 | 2,773 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 92 | 191.4 | 1683.8 | 3745.4 | 2,746 | 0.0% |
| hasura | Haskell | M1 | 659 | 60.9 | 71.7 | 78.3 | 19,781 | 0.0% |
| postgraphile | Node.js | M1 | 2052 | 17.2 | 32.0 | 71.5 | 61,551 | 0.0% |
| actix-web-rest | Rust | M1 | 1646 | 24.9 | 27.5 | 29.0 | 49,387 | 0.0% |
| async-graphql | Rust | M1 | 6498 | 6.1 | 7.8 | 8.6 | 194,931 | 0.0% |
| mercurius | Node.js | M1 | 2514 | 14.5 | 24.5 | 33.8 | 75,412 | 0.0% |
| apollo-server | Node.js | M1 | 1631 | 22.3 | 36.4 | 53.8 | 48,931 | 0.0% |
| strawberry | Python | M1 | 1108 | 34.0 | 50.2 | 67.1 | 33,243 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 6783 | 5.8 | 8.0 | 9.1 | 203,487 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 6761 | 5.8 | 8.1 | 9.1 | 202,832 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 6984 | 5.6 | 7.9 | 8.8 | 209,524 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 6999 | 5.6 | 7.8 | 8.6 | 209,970 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4732 | 6.5 | 30.1 | 37.0 | 141,953 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4670 | 6.5 | 30.9 | 37.8 | 140,100 | 0.0% |
| hasura | Haskell | F1 | 981 | 40.7 | 51.9 | 56.7 | 29,431 | 0.0% |
| postgraphile | Node.js | F1 | 2082 | 18.0 | 29.4 | 45.6 | 62,458 | 0.0% |
| actix-web-rest | Rust | F1 | 8841 | 4.4 | 5.3 | 6.1 | 265,237 | 0.0% |
| async-graphql | Rust | F1 | 6010 | 6.3 | 10.1 | 11.8 | 180,313 | 0.0% |
| mercurius | Node.js | F1 | 2536 | 14.1 | 27.4 | 34.8 | 76,076 | 0.0% |
| apollo-server | Node.js | F1 | 2028 | 18.9 | 29.0 | 37.9 | 60,847 | 0.0% |
| strawberry | Python | F1 | 1091 | 30.5 | 63.4 | 88.1 | 32,740 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 6002 | 6.5 | 9.2 | 10.2 | 180,056 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 6042 | 6.5 | 9.0 | 10.1 | 181,251 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 3563 | 8.1 | 38.4 | 44.4 | 106,899 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 3555 | 8.2 | 38.0 | 43.9 | 106,640 | 0.0% |
| hasura | Haskell | F2 | 941 | 41.2 | 55.5 | 63.4 | 28,216 | 0.0% |
| postgraphile | Node.js | F2 | 1762 | 21.3 | 34.7 | 49.1 | 52,864 | 0.0% |
| actix-web-rest | Rust | F2 | 3633 | 10.7 | 13.6 | 16.3 | 109,001 | 0.0% |
| async-graphql | Rust | F2 | 3904 | 9.5 | 16.9 | 20.9 | 117,123 | 0.0% |
| mercurius | Node.js | F2 | 2062 | 17.8 | 31.3 | 39.3 | 61,861 | 0.0% |
| apollo-server | Node.js | F2 | 1452 | 25.8 | 43.2 | 54.0 | 43,563 | 0.0% |
| strawberry | Python | F2 | 837 | 45.8 | 69.8 | 80.5 | 25,113 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 6485 | 6.0 | 8.5 | 9.6 | 194,562 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 6518 | 6.0 | 8.4 | 9.3 | 195,527 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6267 | 6.3 | 8.7 | 9.8 | 188,010 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6348 | 6.2 | 8.6 | 9.8 | 190,450 | 0.0% |
| hasura | Haskell | F3 | 1060 | 37.5 | 48.4 | 53.3 | 31,813 | 0.0% |
| postgraphile | Node.js | F3 | 1977 | 19.0 | 31.4 | 50.2 | 59,310 | 0.0% |
| actix-web-rest | Rust | F3 | 1290 | 30.3 | 36.6 | 40.2 | 38,710 | 0.0% |
| async-graphql | Rust | F3 | 1142 | 22.7 | 68.7 | 73.5 | 34,271 | 0.0% |
| mercurius | Node.js | F3 | 1236 | 22.3 | 71.7 | 80.8 | 37,075 | 0.0% |
| apollo-server | Node.js | F3 | 1283 | 30.8 | 43.4 | 49.3 | 38,484 | 0.0% |
| strawberry | Python | F3 | 833 | 47.5 | 73.4 | 95.8 | 24,995 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4051 | 9.5 | 14.2 | 16.2 | 121,521 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 4044 | 9.6 | 14.1 | 16.1 | 121,316 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2117 | 13.0 | 49.3 | 59.7 | 63,519 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2091 | 13.8 | 48.6 | 56.7 | 62,743 | 0.0% |
| hasura | Haskell | T1 | 742 | 52.0 | 69.3 | 79.1 | 22,246 | 0.0% |
| postgraphile | Node.js | T1 | 1556 | 23.5 | 38.8 | 83.7 | 46,666 | 0.0% |
| actix-web-rest | Rust | T1 | 2568 | 15.4 | 17.3 | 18.1 | 77,041 | 0.0% |
| async-graphql | Rust | T1 | 3270 | 11.8 | 19.4 | 23.2 | 98,096 | 0.0% |
| mercurius | Node.js | T1 | 1214 | 31.0 | 49.1 | 57.2 | 36,432 | 0.0% |
| apollo-server | Node.js | T1 | 918 | 41.6 | 62.5 | 72.2 | 27,537 | 0.0% |
| strawberry | Python | T1 | 570 | 68.0 | 97.0 | 113.0 | 17,100 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 89 | 223.5 | 1568.3 | 3591.2 | 2,678 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 92 | 211.0 | 1483.1 | 3503.6 | 2,765 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 90 | 190.9 | 1726.6 | 5225.7 | 2,703 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 93 | 205.7 | 1582.8 | 2949.0 | 2,777 | 0.0% |
| hasura | Haskell | MC1 | 402 | 99.9 | 113.2 | 118.1 | 12,067 | 0.0% |
| postgraphile | Node.js | MC1 | 946 | 38.0 | 70.6 | 115.4 | 28,388 | 0.0% |
| actix-web-rest | Rust | MC1 | 955 | 40.6 | 48.6 | 53.6 | 28,639 | 0.0% |
| async-graphql | Rust | MC1 | 1025 | 30.1 | 63.5 | 67.6 | 30,754 | 0.0% |
| mercurius | Node.js | MC1 | 1082 | 34.3 | 53.1 | 63.6 | 32,448 | 0.0% |
| apollo-server | Node.js | MC1 | 791 | 48.1 | 62.7 | 79.9 | 23,739 | 0.0% |
| strawberry | Python | MC1 | 474 | 80.7 | 111.9 | 141.4 | 14,233 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 6141 | 6.4 | 8.9 | 9.8 | 184,222 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6296 | 6.2 | 8.6 | 9.5 | 188,869 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6024 | 6.5 | 9.1 | 10.1 | 180,727 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 5940 | 6.6 | 9.3 | 10.5 | 178,205 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1135 | 22.8 | 69.1 | 73.8 | 34,059 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1234 | 22.3 | 71.5 | 81.1 | 37,014 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1283 | 30.8 | 43.3 | 50.3 | 38,479 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 6161 | 6.3 | 8.9 | 9.8 | 184,829 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 5315 | 7.4 | 10.4 | 11.8 | 159,455 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 3955 | 7.9 | 32.6 | 39.3 | 118,640 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 3959 | 8.0 | 31.6 | 38.7 | 118,782 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 3966 | 9.4 | 16.7 | 20.4 | 118,995 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2162 | 17.2 | 28.4 | 37.8 | 64,856 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1503 | 25.1 | 40.8 | 51.2 | 45,104 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 87 | 228.7 | 1479.8 | 3323.3 | 2,622 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 94 | 212.3 | 1538.4 | 2840.7 | 2,806 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 90 | 192.3 | 1716.8 | 4176.7 | 2,707 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 93 | 206.3 | 1510.1 | 2893.0 | 2,794 | 0.0% |
| async-graphql | Rust | M1_APQ | 6760 | 5.8 | 7.6 | 8.3 | 202,793 | 0.0% |
| mercurius | Node.js | M1_APQ | 2502 | 14.6 | 24.9 | 36.8 | 75,062 | 0.0% |
| apollo-server | Node.js | M1_APQ | 1682 | 22.0 | 35.1 | 50.9 | 50,462 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1339 | 29.2 | 40.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1295 | 30.3 | 52.7 | 0.0% |
| mercurius | Node.js | 1216 | 22.4 | 81.7 | 0.0% |
| async-graphql | Rust | 1144 | 22.8 | 73.6 | 0.0% |
| strawberry | Python | 856 | 45.1 | 78.5 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 6599 | 5.9 | 9.4 | 0.0% |
| fraiseql-tv-cache | Rust | 6495 | 6.0 | 9.6 | 0.0% |
| fraiseql-v-cache | Rust | 6451 | 6.1 | 9.8 | 0.0% |
| fraiseql-v-nocache | Rust | 6413 | 6.1 | 9.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2048 | 18.8 | 38.8 | 0.0% |
| hasura | Haskell | 1060 | 37.6 | 54.0 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 6599 | 5.9 | 9.4 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 6495 | 6.0 | 9.6 |
| fraiseql-v-cache | Rust | graphql-precomputed | 6451 | 6.1 | 9.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 6413 | 6.1 | 9.8 |
| postgraphile | Node.js | graphql-schema-first | 2048 | 18.8 | 38.8 |
| actix-web-rest | Rust | rest | 1339 | 29.2 | 40.2 |
| apollo-server | Node.js | graphql | 1295 | 30.3 | 52.7 |
| mercurius | Node.js | graphql | 1216 | 22.4 | 81.7 |
| async-graphql | Rust | graphql | 1144 | 22.8 | 73.6 |
| hasura | Haskell | graphql-schema-first | 1060 | 37.6 | 54.0 |
| strawberry | Python | graphql | 856 | 45.1 | 78.5 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv | 6599 | 77 | 0.0050 | 48 | 0.0080 | 95 | 0.0040 |
| fraiseql-tv-cache | 6495 | 76 | 0.0050 | 47 | 0.0081 | 93 | 0.0041 |
| fraiseql-v-cache | 6451 | 75 | 0.0051 | 47 | 0.0082 | 93 | 0.0041 |
| fraiseql-v-nocache | 6413 | 75 | 0.0051 | 46 | 0.0082 | 92 | 0.0041 |
| postgraphile | 2048 | 24 | 0.0160 | 15 | 0.0257 | 29 | 0.0129 |
| actix-web-rest | 1339 | 16 | 0.0244 | 10 | 0.0393 | 19 | 0.0197 |
| apollo-server | 1295 | 15 | 0.0253 | 9 | 0.0407 | 19 | 0.0204 |
| mercurius | 1216 | 14 | 0.0269 | 9 | 0.0433 | 18 | 0.0217 |
| async-graphql | 1144 | 13 | 0.0286 | 8 | 0.0460 | 16 | 0.0231 |
| hasura | 1060 | 12 | 0.0309 | 8 | 0.0497 | 15 | 0.0249 |
| strawberry | 856 | 10 | 0.0382 | 6 | 0.0615 | 12 | 0.0309 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 133.2 |
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 136.8 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 103.4 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 12 | 90.1 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 127 | 113.4 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 91.9 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 64 | 108.4 |
| mercurius | Node.js | 464 | 8.8 | 104 | 55 | 99.4 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 119.6 |
| hasura | Haskell | — | — | — | 130 | 153.2 |
| strawberry | Python | 1,812 | 12.7 | 136 | 189 | 161.6 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.6 |

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

> **Peak**: fraiseql-tv-cache 92 cycles/s (1 req) vs mercurius 1082 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 6,498 M/s: **~396,359 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.