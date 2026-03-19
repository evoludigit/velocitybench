# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-04  
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
| fraiseql-tv-nocache | Python | Q1 | 6890 | 5.2 | 11.4 | 14.9 | 206,705 | 0.0% |
| fraiseql-v | Python | Q1 | 6529 | 5.6 | 10.7 | 13.8 | 195,866 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q2 | 2965 | 12.2 | 24.6 | 31.4 | 88,941 | 0.0% |
| fraiseql-v | Python | Q2 | 2086 | 18.3 | 27.0 | 31.7 | 62,593 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q2b | 1553 | 23.4 | 45.9 | 58.7 | 46,587 | 0.0% |
| fraiseql-v | Python | Q2b | 899 | 41.9 | 65.8 | 79.4 | 26,977 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | C3 | 10106 | 3.5 | 8.3 | 11.3 | 303,190 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | M1 | 2118 | 11.2 | 62.7 | 99.1 | 63,552 | 0.0% |
| fraiseql-v | Python | M1 | 1865 | 12.3 | 73.0 | 117.1 | 55,941 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 695 | 29.6 | 207.2 | 396.0 | 20,845 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F1 | 3146 | 11.5 | 23.4 | 30.4 | 94,371 | 0.0% |
| fraiseql-v | Python | F1 | 2088 | 18.3 | 26.9 | 31.8 | 62,641 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F2 | 1636 | 22.2 | 44.1 | 56.6 | 49,067 | 0.0% |
| fraiseql-v | Python | F2 | 899 | 41.9 | 65.7 | 79.2 | 26,976 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F3 | 6800 | 5.0 | 12.3 | 18.8 | 203,997 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 6890 | 5.2 | 14.9 | 0.0% |
| fraiseql-v | Python | 6529 | 5.6 | 13.8 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 6890 | 5.2 | 14.9 |
| fraiseql-v | Python | graphql-precomputed | 6529 | 5.6 | 13.8 |