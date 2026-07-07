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
| Run timestamp | 2026-07-07T10:06:53+00:00 |

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
| `tv_comment` | 692.7 MB | 322.2 MB | 1.62 GB |
| `tb_comment` | 294.7 MB | 81.5 MB | 376.4 MB |
| `tv_post` | 200.7 MB | 72.2 MB | 322.1 MB |
| `tb_post` | 133.8 MB | 19.8 MB | 153.7 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.6 MB | 3.1 MB | 7.8 MB |
| `tb_user_follows` | 2.1 MB | 4.6 MB | 6.8 MB |
| `tb_mutation_log` | 3.5 MB | 0.3 MB | 3.8 MB |
| `bench_bio_snapshot` | 2.3 MB | 0.0 MB | 2.3 MB |
| `tvd_comment` | 0.6 MB | 0.1 MB | 0.7 MB |
| `tvd_post` | 0.2 MB | 0.0 MB | 0.3 MB |
| `tvd_user` | 0.1 MB | 0.0 MB | 0.1 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 562.8 MB  
**Storage amplification**: 4.55× (TV adds 1.95 GB on top of the normalized 562.8 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 6523 | 6.0 | 8.4 | 9.4 | 195,696 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 6588 | 5.9 | 8.3 | 9.3 | 197,653 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 6317 | 6.2 | 8.7 | 9.8 | 189,519 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 6304 | 6.2 | 8.8 | 10.0 | 189,131 | 0.0% |
| hasura | Haskell | Q1 | 1051 | 37.5 | 48.2 | 53.7 | 31,542 | 0.0% |
| postgraphile | Node.js | Q1 | 2099 | 18.2 | 28.9 | 40.7 | 62,960 | 0.0% |
| actix-web-rest | Rust | Q1 | 1330 | 29.4 | 35.4 | 38.2 | 39,907 | 0.0% |
| async-graphql | Rust | Q1 | 1146 | 22.6 | 68.4 | 73.1 | 34,386 | 0.0% |
| mercurius | Node.js | Q1 | 1233 | 22.1 | 72.2 | 82.1 | 37,002 | 0.0% |
| apollo-server | Node.js | Q1 | 1304 | 30.2 | 43.2 | 51.1 | 39,129 | 0.0% |
| strawberry | Python | Q1 | 849 | 45.5 | 63.1 | 81.2 | 25,482 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 7433 | 5.3 | 7.4 | 8.3 | 222,994 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7338 | 5.3 | 7.5 | 8.3 | 220,126 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5552 | 6.1 | 20.3 | 30.0 | 166,558 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5667 | 6.0 | 18.2 | 28.1 | 170,013 | 0.0% |
| hasura | Haskell | Q2 | 1146 | 35.2 | 41.3 | 50.3 | 34,395 | 0.0% |
| postgraphile | Node.js | Q2 | 2203 | 17.2 | 27.2 | 39.4 | 66,079 | 0.0% |
| actix-web-rest | Rust | Q2 | 8959 | 4.4 | 5.3 | 6.0 | 268,769 | 0.0% |
| async-graphql | Rust | Q2 | 6224 | 6.0 | 9.6 | 11.2 | 186,715 | 0.0% |
| mercurius | Node.js | Q2 | 2821 | 13.1 | 22.9 | 30.3 | 84,640 | 0.0% |
| apollo-server | Node.js | Q2 | 2060 | 18.6 | 28.8 | 37.2 | 61,800 | 0.0% |
| strawberry | Python | Q2 | 1255 | 30.9 | 36.6 | 58.5 | 37,663 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 6406 | 6.1 | 8.6 | 9.6 | 192,193 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 6288 | 6.2 | 8.7 | 9.6 | 188,655 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4147 | 7.6 | 30.6 | 37.4 | 124,400 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4126 | 7.6 | 31.1 | 37.9 | 123,768 | 0.0% |
| hasura | Haskell | Q2b | 908 | 43.6 | 55.4 | 59.3 | 27,225 | 0.0% |
| postgraphile | Node.js | Q2b | 1925 | 19.6 | 31.4 | 44.3 | 57,757 | 0.0% |
| actix-web-rest | Rust | Q2b | 4325 | 9.0 | 10.9 | 12.1 | 129,745 | 0.0% |
| async-graphql | Rust | Q2b | 4122 | 9.0 | 16.2 | 19.9 | 123,660 | 0.0% |
| mercurius | Node.js | Q2b | 2177 | 17.1 | 28.7 | 37.2 | 65,302 | 0.0% |
| apollo-server | Node.js | Q2b | 1483 | 25.5 | 41.6 | 51.5 | 44,491 | 0.0% |
| strawberry | Python | Q2b | 834 | 43.9 | 66.5 | 92.4 | 25,025 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 3162 | 10.2 | 34.6 | 41.3 | 94,874 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 3161 | 10.2 | 34.8 | 41.5 | 94,831 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 1302 | 19.7 | 73.4 | 92.0 | 39,072 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 1306 | 19.9 | 72.4 | 89.3 | 39,191 | 0.0% |
| hasura | Haskell | Q3 | 936 | 41.3 | 55.6 | 63.0 | 28,091 | 0.0% |
| postgraphile | Node.js | Q3 | 1168 | 31.5 | 57.7 | 77.3 | 35,043 | 0.0% |
| actix-web-rest | Rust | Q3 | 3254 | 12.1 | 14.4 | 16.2 | 97,629 | 0.0% |
| async-graphql | Rust | Q3 | 1444 | 26.8 | 50.2 | 60.8 | 43,316 | 0.0% |
| mercurius | Node.js | Q3 | 664 | 58.8 | 87.4 | 100.6 | 19,914 | 0.0% |
| apollo-server | Node.js | Q3 | 511 | 76.9 | 109.0 | 122.6 | 15,335 | 0.0% |
| strawberry | Python | Q3 | 476 | 78.7 | 113.9 | 141.9 | 14,272 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 7566 | 5.2 | 7.1 | 7.9 | 226,974 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 7641 | 5.1 | 7.1 | 7.8 | 229,244 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7489 | 5.2 | 7.2 | 8.0 | 224,679 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7480 | 5.3 | 7.2 | 7.9 | 224,393 | 0.0% |
| hasura | Haskell | C3 | 975 | 41.1 | 52.3 | 56.7 | 29,252 | 0.0% |
| postgraphile | Node.js | C3 | 2477 | 15.1 | 24.3 | 37.8 | 74,305 | 0.0% |
| actix-web-rest | Rust | C3 | 11122 | 3.5 | 4.2 | 5.0 | 333,646 | 0.0% |
| async-graphql | Rust | C3 | 10864 | 3.5 | 5.1 | 5.8 | 325,908 | 0.0% |
| mercurius | Node.js | C3 | 3936 | 9.5 | 16.0 | 21.3 | 118,065 | 0.0% |
| apollo-server | Node.js | C3 | 2493 | 15.3 | 23.8 | 30.4 | 74,798 | 0.0% |
| strawberry | Python | C3 | 1271 | 29.1 | 45.6 | 65.0 | 38,124 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 7666 | 5.1 | 7.1 | 7.9 | 229,976 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 7675 | 5.1 | 7.1 | 7.8 | 230,258 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 7266 | 5.4 | 7.4 | 8.1 | 217,987 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7403 | 5.3 | 7.3 | 8.0 | 222,090 | 0.0% |
| hasura | Haskell | HC3 | 1050 | 38.5 | 48.8 | 54.6 | 31,488 | 0.0% |
| postgraphile | Node.js | HC3 | 2516 | 15.0 | 23.3 | 37.8 | 75,489 | 0.0% |
| actix-web-rest | Rust | HC3 | 11059 | 3.6 | 4.2 | 4.7 | 331,773 | 0.0% |
| async-graphql | Rust | HC3 | 10874 | 3.5 | 5.2 | 6.1 | 326,207 | 0.0% |
| mercurius | Node.js | HC3 | 4040 | 9.3 | 15.1 | 19.7 | 121,185 | 0.0% |
| apollo-server | Node.js | HC3 | 2345 | 16.4 | 25.0 | 31.0 | 70,346 | 0.0% |
| strawberry | Python | HC3 | 1327 | 31.8 | 42.4 | 64.1 | 39,821 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }` — 20 user UUIDs × 10 bio values, rotating: every request is a real write

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 90 | 236.5 | 1438.4 | 3319.3 | 2,685 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 91 | 225.2 | 1481.0 | 3470.3 | 2,717 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 95 | 187.2 | 1608.3 | 3078.3 | 2,858 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 91 | 178.6 | 1804.2 | 4072.7 | 2,737 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 91 | 191.7 | 1601.2 | 4738.9 | 2,718 | 0.0% |
| hasura | Haskell | M1 | 679 | 60.1 | 72.4 | 80.9 | 20,358 | 0.0% |
| postgraphile | Node.js | M1 | 2076 | 17.2 | 31.1 | 69.8 | 62,282 | 0.0% |
| actix-web-rest | Rust | M1 | 1658 | 24.8 | 29.8 | 32.8 | 49,755 | 0.0% |
| async-graphql | Rust | M1 | 6480 | 6.2 | 7.7 | 8.5 | 194,387 | 0.0% |
| mercurius | Node.js | M1 | 2560 | 14.3 | 23.4 | 34.4 | 76,812 | 0.0% |
| apollo-server | Node.js | M1 | 1676 | 22.0 | 35.6 | 51.1 | 50,281 | 0.0% |
| strawberry | Python | M1 | 1072 | 34.7 | 54.9 | 73.9 | 32,147 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 6870 | 5.7 | 7.9 | 9.0 | 206,102 | 0.0% |
| fraiseql-tv-cache | Rust | M1d | 6697 | 5.9 | 8.1 | 9.3 | 200,907 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 7105 | 5.5 | 7.7 | 8.6 | 213,138 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 7203 | 5.4 | 7.6 | 8.6 | 216,083 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4716 | 6.5 | 30.4 | 37.1 | 141,481 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4666 | 6.6 | 30.6 | 37.2 | 139,966 | 0.0% |
| hasura | Haskell | F1 | 993 | 40.2 | 51.7 | 56.9 | 29,798 | 0.0% |
| postgraphile | Node.js | F1 | 2065 | 18.2 | 29.2 | 45.9 | 61,938 | 0.0% |
| actix-web-rest | Rust | F1 | 9027 | 4.3 | 5.3 | 6.2 | 270,808 | 0.0% |
| async-graphql | Rust | F1 | 6174 | 6.1 | 9.6 | 11.2 | 185,213 | 0.0% |
| mercurius | Node.js | F1 | 2730 | 13.6 | 23.1 | 30.9 | 81,907 | 0.0% |
| apollo-server | Node.js | F1 | 1989 | 19.3 | 29.9 | 36.8 | 59,657 | 0.0% |
| strawberry | Python | F1 | 1110 | 37.3 | 46.5 | 68.3 | 33,308 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 6127 | 6.4 | 9.0 | 10.0 | 183,804 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 6112 | 6.4 | 8.9 | 9.9 | 183,373 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 3551 | 8.2 | 38.5 | 44.2 | 106,516 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 3592 | 8.3 | 37.3 | 43.1 | 107,773 | 0.0% |
| hasura | Haskell | F2 | 835 | 47.4 | 59.9 | 64.5 | 25,061 | 0.0% |
| postgraphile | Node.js | F2 | 1736 | 21.2 | 37.7 | 53.5 | 52,093 | 0.0% |
| actix-web-rest | Rust | F2 | 3642 | 10.6 | 14.5 | 17.7 | 109,274 | 0.0% |
| async-graphql | Rust | F2 | 3966 | 9.4 | 16.6 | 20.2 | 118,967 | 0.0% |
| mercurius | Node.js | F2 | 2003 | 18.2 | 33.0 | 41.7 | 60,084 | 0.0% |
| apollo-server | Node.js | F2 | 1428 | 26.2 | 43.7 | 56.3 | 42,850 | 0.0% |
| strawberry | Python | F2 | 772 | 48.2 | 72.6 | 97.8 | 23,161 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 6427 | 6.1 | 8.4 | 9.4 | 192,820 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 6660 | 5.9 | 8.2 | 9.2 | 199,811 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 6182 | 6.3 | 8.8 | 9.9 | 185,465 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 6123 | 6.4 | 9.0 | 10.1 | 183,701 | 0.0% |
| hasura | Haskell | F3 | 1061 | 37.4 | 47.0 | 53.3 | 31,827 | 0.0% |
| postgraphile | Node.js | F3 | 1914 | 19.5 | 33.2 | 52.9 | 57,407 | 0.0% |
| actix-web-rest | Rust | F3 | 1304 | 30.2 | 35.3 | 38.7 | 39,117 | 0.0% |
| async-graphql | Rust | F3 | 1160 | 22.4 | 68.0 | 73.0 | 34,785 | 0.0% |
| mercurius | Node.js | F3 | 1228 | 22.2 | 72.2 | 81.7 | 36,849 | 0.0% |
| apollo-server | Node.js | F3 | 1306 | 30.3 | 43.3 | 50.2 | 39,174 | 0.0% |
| strawberry | Python | F3 | 836 | 46.0 | 63.1 | 80.6 | 25,093 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 4040 | 9.5 | 14.4 | 16.5 | 121,191 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 3876 | 10.0 | 14.7 | 16.6 | 116,290 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 2100 | 13.6 | 48.8 | 57.5 | 63,010 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 2114 | 13.3 | 48.8 | 57.2 | 63,420 | 0.0% |
| hasura | Haskell | T1 | 656 | 60.9 | 75.7 | 81.0 | 19,685 | 0.0% |
| postgraphile | Node.js | T1 | 1658 | 22.2 | 38.0 | 70.6 | 49,735 | 0.0% |
| actix-web-rest | Rust | T1 | 2572 | 15.5 | 17.3 | 19.3 | 77,149 | 0.0% |
| async-graphql | Rust | T1 | 3936 | 9.8 | 15.3 | 18.5 | 118,082 | 0.0% |
| mercurius | Node.js | T1 | 1204 | 31.6 | 48.9 | 56.4 | 36,118 | 0.0% |
| apollo-server | Node.js | T1 | 913 | 41.6 | 64.0 | 77.0 | 27,378 | 0.0% |
| strawberry | Python | T1 | 558 | 74.1 | 105.1 | 120.2 | 16,749 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical GraphQL: 2 serial requests (M1 + Q1 re-fetch). REST: 2 serial requests (PUT + GET re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 93 | 262.1 | 1266.4 | 2577.2 | 2,781 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 92 | 216.1 | 1517.4 | 3573.7 | 2,752 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 94 | 189.5 | 1608.4 | 3712.8 | 2,810 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 93 | 178.2 | 1687.4 | 4110.1 | 2,778 | 0.0% |
| hasura | Haskell | MC1 | 409 | 98.7 | 111.9 | 115.7 | 12,260 | 0.0% |
| postgraphile | Node.js | MC1 | 947 | 38.6 | 69.2 | 107.6 | 28,408 | 0.0% |
| actix-web-rest | Rust | MC1 | 950 | 40.8 | 49.3 | 55.3 | 28,486 | 0.0% |
| async-graphql | Rust | MC1 | 1025 | 29.2 | 64.6 | 68.7 | 30,744 | 0.0% |
| mercurius | Node.js | MC1 | 1083 | 34.3 | 53.1 | 63.0 | 32,485 | 0.0% |
| apollo-server | Node.js | MC1 | 769 | 48.9 | 67.3 | 83.0 | 23,083 | 0.0% |
| strawberry | Python | MC1 | 480 | 87.5 | 119.6 | 131.7 | 14,390 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 6194 | 6.3 | 8.9 | 9.8 | 185,824 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 6016 | 6.5 | 9.1 | 10.1 | 180,495 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 6084 | 6.4 | 9.0 | 10.1 | 182,514 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 6045 | 6.5 | 9.1 | 10.4 | 181,349 | 0.0% |
| async-graphql | Rust | Q1_APQ | 1149 | 22.5 | 68.8 | 73.7 | 34,457 | 0.0% |
| mercurius | Node.js | Q1_APQ | 1226 | 22.4 | 71.8 | 82.3 | 36,772 | 0.0% |
| apollo-server | Node.js | Q1_APQ | 1289 | 30.8 | 43.4 | 50.3 | 38,676 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 6027 | 6.5 | 9.0 | 10.0 | 180,800 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 5943 | 6.6 | 9.2 | 10.2 | 178,291 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 3958 | 7.8 | 33.2 | 39.8 | 118,753 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 4013 | 7.8 | 32.2 | 38.5 | 120,399 | 0.0% |
| async-graphql | Rust | Q2b_APQ | 4189 | 8.8 | 15.9 | 19.4 | 125,676 | 0.0% |
| mercurius | Node.js | Q2b_APQ | 2144 | 17.2 | 30.2 | 38.4 | 64,331 | 0.0% |
| apollo-server | Node.js | Q2b_APQ | 1544 | 24.5 | 39.4 | 49.1 | 46,322 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 92 | 257.4 | 1300.6 | 2460.4 | 2,766 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 90 | 214.3 | 1686.7 | 4268.6 | 2,715 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 94 | 187.6 | 1500.3 | 3955.0 | 2,828 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 92 | 174.6 | 1616.5 | 4246.6 | 2,765 | 0.0% |
| async-graphql | Rust | M1_APQ | 7099 | 5.5 | 7.1 | 7.8 | 212,961 | 0.0% |
| mercurius | Node.js | M1_APQ | 2454 | 14.7 | 25.0 | 37.4 | 73,608 | 0.0% |
| apollo-server | Node.js | M1_APQ | 1746 | 21.2 | 32.3 | 48.1 | 52,379 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1330 | 29.4 | 38.2 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| apollo-server | Node.js | 1304 | 30.2 | 51.1 | 0.0% |
| mercurius | Node.js | 1233 | 22.1 | 82.1 | 0.0% |
| async-graphql | Rust | 1146 | 22.6 | 73.1 | 0.0% |
| strawberry | Python | 849 | 45.5 | 81.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 6588 | 5.9 | 9.3 | 0.0% |
| fraiseql-tv | Rust | 6523 | 6.0 | 9.4 | 0.0% |
| fraiseql-v-nocache | Rust | 6317 | 6.2 | 9.8 | 0.0% |
| fraiseql-v-cache | Rust | 6304 | 6.2 | 10.0 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 2099 | 18.2 | 40.7 | 0.0% |
| hasura | Haskell | 1051 | 37.5 | 53.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 6588 | 5.9 | 9.3 |
| fraiseql-tv | Rust | graphql-precomputed | 6523 | 6.0 | 9.4 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 6317 | 6.2 | 9.8 |
| fraiseql-v-cache | Rust | graphql-precomputed | 6304 | 6.2 | 10.0 |
| postgraphile | Node.js | graphql-schema-first | 2099 | 18.2 | 40.7 |
| actix-web-rest | Rust | rest | 1330 | 29.4 | 38.2 |
| apollo-server | Node.js | graphql | 1304 | 30.2 | 51.1 |
| mercurius | Node.js | graphql | 1233 | 22.1 | 82.1 |
| async-graphql | Rust | graphql | 1146 | 22.6 | 73.1 |
| hasura | Haskell | graphql-schema-first | 1051 | 37.5 | 53.7 |
| strawberry | Python | graphql | 849 | 45.5 | 81.2 |

---

## Cost Composite

> Measured Q1 throughput priced on Hetzner dedicated-vCPU instances (prices captured 2026-07-04, EUR excl. VAT — `costs/instance-prices-2026-07.yaml`).  
> **€ / 1M requests** = price/month ÷ (RPS × 2 628 000 s) × 10⁶ — the instance cost attributable to one million requests at sustained measured throughput.  
> Only meaningful for sweeps run **on** the priced instance class; on other hardware it is a projection.

| Framework | Q1 RPS | ccx23 RPS/€mo | ccx23 € / 1M requests | ccx33 RPS/€mo | ccx33 € / 1M requests | cpx42 RPS/€mo | cpx42 € / 1M requests |
|-----------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|
| fraiseql-tv-cache | 6588 | 77 | 0.0050 | 48 | 0.0080 | 95 | 0.0040 |
| fraiseql-tv | 6523 | 76 | 0.0050 | 47 | 0.0081 | 94 | 0.0041 |
| fraiseql-v-nocache | 6317 | 73 | 0.0052 | 46 | 0.0083 | 91 | 0.0042 |
| fraiseql-v-cache | 6304 | 73 | 0.0052 | 46 | 0.0084 | 91 | 0.0042 |
| postgraphile | 2099 | 24 | 0.0156 | 15 | 0.0251 | 30 | 0.0126 |
| actix-web-rest | 1330 | 15 | 0.0246 | 10 | 0.0396 | 19 | 0.0199 |
| apollo-server | 1304 | 15 | 0.0251 | 9 | 0.0404 | 19 | 0.0203 |
| mercurius | 1233 | 14 | 0.0265 | 9 | 0.0427 | 18 | 0.0214 |
| async-graphql | 1146 | 13 | 0.0285 | 8 | 0.0460 | 16 | 0.0231 |
| hasura | 1051 | 12 | 0.0311 | 8 | 0.0501 | 15 | 0.0251 |
| strawberry | 849 | 10 | 0.0385 | 6 | 0.0620 | 12 | 0.0311 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv-cache | Rust | 243 | 2.1 | 43 | 12 | 133.9 |
| fraiseql-tv | Rust | 243 | 2.1 | 43 | 12 | 134.3 |
| fraiseql-v-nocache | Rust | 529 | 1.3 | 43 | 11 | 89.9 |
| fraiseql-v-cache | Rust | 529 | 1.3 | 43 | 12 | 103.1 |
| postgraphile | Node.js | 112 | 7.1 | 196 | 124 | 116.6 |
| actix-web-rest | Rust | 760 | 3.7 | 12 | 5 | 92.4 |
| apollo-server | Node.js | 758 | 7.5 | 120 | 65 | 106.5 |
| mercurius | Node.js | 464 | 8.8 | 104 | 56 | 98.3 |
| async-graphql | Rust | 697 | 4.4 | 12 | 12 | 122.8 |
| hasura | Haskell | — | — | — | 133 | 153.7 |
| strawberry | Python | 1,812 | 12.7 | 136 | 180 | 161.8 |
| fraiseql-tv-audit | Rust | — | — | 43 | 10 | 2.5 |

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

> **Peak**: fraiseql-tv 93 cycles/s (1 req) vs mercurius 1083 cycles/s (2 req) — 0.1× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 6,480 M/s: **~395,253 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.