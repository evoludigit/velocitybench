# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-05  
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
| fraiseql-tv | Python | Q1 | 10839 | 3.3 | 7.5 | 10.3 | 325,183 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 10842 | 3.3 | 7.5 | 10.2 | 325,270 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 10210 | 3.3 | 8.7 | 13.2 | 306,314 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 10267 | 3.3 | 8.5 | 12.8 | 308,018 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 9759 | 3.8 | 7.5 | 9.9 | 292,782 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 9694 | 3.8 | 7.7 | 10.3 | 290,814 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 155 | 235.0 | 410.1 | 505.8 | 4,644 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 180 | 204.3 | 402.7 | 561.5 | 5,388 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 1430 | 17.2 | 92.3 | 147.5 | 42,899 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1447 | 16.9 | 91.1 | 144.2 | 43,410 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 10624 | 3.2 | 8.0 | 11.3 | 318,731 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9782 | 3.4 | 9.0 | 14.9 | 293,466 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 9733 | 3.8 | 7.6 | 10.1 | 291,985 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 9791 | 3.8 | 7.5 | 9.9 | 293,725 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 11098 | 3.2 | 7.2 | 9.8 | 332,946 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 10572 | 3.3 | 7.7 | 11.3 | 317,171 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv-nocache | Python | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 10842 | 3.3 | 10.2 | 0.0% |
| fraiseql-tv | Python | 10839 | 3.3 | 10.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 10842 | 3.3 | 10.2 |
| fraiseql-tv | Python | graphql-precomputed | 10839 | 3.3 | 10.3 |