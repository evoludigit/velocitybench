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
| fraiseql-tv | Python | Q1 | 9334 | 3.7 | 9.1 | 12.6 | 280,035 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 8073 | 3.7 | 9.1 | 12.7 | 242,193 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 9347 | 3.7 | 9.3 | 12.9 | 280,402 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 9450 | 3.6 | 9.2 | 12.9 | 283,491 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 7210 | 4.7 | 12.2 | 18.6 | 216,287 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8197 | 4.3 | 9.6 | 12.9 | 245,905 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4569 | 8.4 | 12.8 | 15.6 | 137,080 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4515 | 8.5 | 13.0 | 16.0 | 135,463 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 7864 | 4.0 | 12.5 | 19.8 | 235,912 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 9617 | 3.5 | 9.3 | 13.5 | 288,497 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 7729 | 4.7 | 9.6 | 13.2 | 231,867 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 3377 | 5.3 | 42.5 | 86.7 | 101,320 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 8097 | 4.0 | 11.7 | 18.9 | 242,912 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 8746 | 3.9 | 10.0 | 14.2 | 262,385 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 6024 | 5.5 | 14.7 | 21.5 | 180,705 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8376 | 4.3 | 9.2 | 12.2 | 251,288 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 8947 | 3.8 | 9.2 | 12.7 | 268,419 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9425 | 3.7 | 8.9 | 12.3 | 282,746 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3896 | 9.7 | 17.0 | 21.2 | 116,893 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3904 | 9.7 | 16.8 | 21.0 | 117,133 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Python | 9334 | 3.7 | 12.6 | 0.0% |
| fraiseql-tv-nocache | Python | 8073 | 3.7 | 12.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Python | graphql-precomputed | 9334 | 3.7 | 12.6 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 8073 | 3.7 | 12.7 |