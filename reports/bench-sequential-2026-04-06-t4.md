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
| fraiseql-tv | Python | Q1 | 8808 | 3.8 | 9.9 | 14.7 | 264,227 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 7745 | 4.0 | 10.0 | 14.3 | 232,357 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 8859 | 3.8 | 10.0 | 14.8 | 265,760 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 8578 | 3.9 | 10.3 | 15.4 | 257,339 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8474 | 4.2 | 9.4 | 12.6 | 254,226 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8422 | 4.2 | 9.5 | 12.8 | 252,646 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4629 | 8.3 | 12.8 | 15.8 | 138,880 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4685 | 8.2 | 12.6 | 15.6 | 140,558 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 6998 | 4.4 | 14.4 | 23.8 | 209,938 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 6063 | 5.1 | 17.0 | 27.0 | 181,897 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 7070 | 5.0 | 11.0 | 16.9 | 212,105 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1270 | 24.5 | 77.2 | 143.2 | 38,100 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 8736 | 3.7 | 9.0 | 12.4 | 262,067 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9466 | 3.7 | 9.0 | 12.6 | 283,986 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8483 | 4.2 | 9.2 | 12.2 | 254,503 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8358 | 4.3 | 9.4 | 12.5 | 250,729 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 8716 | 3.9 | 9.9 | 14.2 | 261,485 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9234 | 3.8 | 9.2 | 12.7 | 277,012 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3909 | 9.7 | 17.0 | 21.0 | 117,257 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3874 | 9.8 | 17.1 | 21.4 | 116,209 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Python | 8808 | 3.8 | 14.7 | 0.0% |
| fraiseql-tv-nocache | Python | 7745 | 4.0 | 14.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Python | graphql-precomputed | 8808 | 3.8 | 14.7 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 7745 | 4.0 | 14.3 |