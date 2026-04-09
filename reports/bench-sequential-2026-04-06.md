# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-06  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 30s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q1 | 8278 | 4.0 | 10.8 | 15.9 | 248,352 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 8440 | 4.0 | 10.5 | 15.5 | 253,185 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 8230 | 4.0 | 11.1 | 17.9 | 246,895 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 8165 | 4.0 | 11.4 | 19.2 | 244,961 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8640 | 4.1 | 9.2 | 12.3 | 259,187 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8626 | 4.1 | 9.2 | 12.3 | 258,783 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4661 | 8.3 | 12.6 | 15.5 | 139,830 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4702 | 8.2 | 12.4 | 15.2 | 141,053 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 168 | 222.5 | 361.7 | 415.2 | 5,037 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 164 | 223.1 | 385.9 | 437.6 | 4,930 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 1510 | 16.1 | 87.2 | 141.5 | 45,311 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 374 | 54.8 | 388.6 | 780.9 | 11,215 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 8392 | 3.9 | 10.9 | 17.3 | 251,755 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 8703 | 3.9 | 10.2 | 15.4 | 261,094 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8654 | 4.1 | 9.1 | 12.2 | 259,620 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8679 | 4.1 | 9.1 | 12.2 | 260,383 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 8935 | 3.8 | 9.6 | 13.8 | 268,045 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 8477 | 4.0 | 10.3 | 15.3 | 254,303 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 4000 | 9.5 | 16.5 | 20.6 | 119,999 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3957 | 9.6 | 16.8 | 21.0 | 118,718 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 8440 | 4.0 | 15.5 | 0.0% |
| fraiseql-tv | Python | 8278 | 4.0 | 15.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 8440 | 4.0 | 15.5 |
| fraiseql-tv | Python | graphql-precomputed | 8278 | 4.0 | 15.9 |