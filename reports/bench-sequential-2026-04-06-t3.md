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
| fraiseql-tv | Python | Q1 | 8894 | 3.8 | 9.7 | 14.3 | 266,824 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 9147 | 3.8 | 9.4 | 13.1 | 274,422 | 0.0% |
| fraiseql-v | Python | Q1 | 8907 | 4.0 | 9.1 | 12.3 | 267,202 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 8921 | 3.8 | 9.9 | 14.7 | 267,625 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 9370 | 3.6 | 9.3 | 13.3 | 281,092 | 0.0% |
| fraiseql-v | Python | Q2 | 7035 | 4.8 | 12.5 | 17.8 | 211,060 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8615 | 4.1 | 9.3 | 12.4 | 258,458 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8686 | 4.1 | 9.1 | 12.2 | 260,568 | 0.0% |
| fraiseql-v | Python | Q2b | 7179 | 4.9 | 10.9 | 15.2 | 215,376 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4688 | 8.2 | 12.6 | 15.5 | 140,646 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4685 | 8.2 | 12.6 | 15.4 | 140,550 | 0.0% |
| fraiseql-v | Python | Q3 | 672 | 73.5 | 99.8 | 108.1 | 20,175 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 8572 | 3.7 | 11.0 | 18.3 | 257,170 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 6828 | 4.2 | 14.5 | 24.4 | 204,832 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 1665 | 14.6 | 78.9 | 127.6 | 49,948 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 352 | 65.1 | 387.1 | 736.9 | 10,575 | 0.0% |
| fraiseql-v | Python | M1 | 1567 | 15.8 | 83.4 | 131.5 | 47,002 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 1309 | 19.1 | 99.1 | 157.8 | 39,278 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 9534 | 3.6 | 8.9 | 12.3 | 286,023 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9784 | 3.5 | 8.7 | 12.1 | 293,533 | 0.0% |
| fraiseql-v | Python | F1 | 2958 | 11.3 | 31.2 | 42.7 | 88,732 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8602 | 4.2 | 9.0 | 12.1 | 258,064 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8442 | 4.2 | 9.3 | 12.4 | 253,262 | 0.0% |
| fraiseql-v | Python | F2 | 2587 | 12.6 | 37.3 | 49.0 | 77,623 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 8498 | 3.9 | 10.4 | 16.4 | 254,946 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9312 | 3.7 | 9.1 | 13.0 | 279,370 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3939 | 9.6 | 16.8 | 21.0 | 118,178 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3952 | 9.6 | 16.5 | 20.5 | 118,567 | 0.0% |
| fraiseql-v | Python | T1 | 735 | 54.9 | 92.8 | 106.4 | 22,055 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 9147 | 3.8 | 13.1 | 0.0% |
| fraiseql-v | Python | 8907 | 4.0 | 12.3 | 0.0% |
| fraiseql-tv | Python | 8894 | 3.8 | 14.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 9147 | 3.8 | 13.1 |
| fraiseql-v | Python | graphql-precomputed | 8907 | 4.0 | 12.3 |
| fraiseql-tv | Python | graphql-precomputed | 8894 | 3.8 | 14.3 |