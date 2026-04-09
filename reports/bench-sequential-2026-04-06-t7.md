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
| fraiseql-tv | Python | Q1 | 9189 | 3.8 | 9.3 | 13.0 | 275,671 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 9215 | 3.8 | 9.2 | 12.9 | 276,447 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 9463 | 3.6 | 9.1 | 12.8 | 283,891 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 9648 | 3.6 | 8.9 | 12.4 | 289,428 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8274 | 4.3 | 9.6 | 12.8 | 248,230 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8298 | 4.3 | 9.5 | 12.6 | 248,945 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4539 | 8.5 | 12.9 | 15.8 | 136,161 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4390 | 8.7 | 13.5 | 16.7 | 131,707 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 9399 | 3.5 | 9.7 | 14.7 | 281,978 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 9893 | 3.4 | 9.0 | 12.8 | 296,776 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 3751 | 8.3 | 23.3 | 39.7 | 112,533 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 7919 | 4.6 | 9.2 | 13.1 | 237,557 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 9243 | 3.7 | 9.1 | 12.5 | 277,294 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9026 | 3.7 | 9.3 | 12.9 | 270,788 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8227 | 4.3 | 9.6 | 12.8 | 246,822 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8048 | 4.5 | 9.8 | 13.1 | 241,448 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 9382 | 3.7 | 9.0 | 12.3 | 281,473 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9352 | 3.7 | 8.8 | 11.9 | 280,558 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3797 | 10.0 | 17.6 | 22.0 | 113,918 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3779 | 10.1 | 17.4 | 21.7 | 113,379 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 9215 | 3.8 | 12.9 | 0.0% |
| fraiseql-tv | Python | 9189 | 3.8 | 13.0 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 9215 | 3.8 | 12.9 |
| fraiseql-tv | Python | graphql-precomputed | 9189 | 3.8 | 13.0 |