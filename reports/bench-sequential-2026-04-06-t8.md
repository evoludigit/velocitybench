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
| fraiseql-tv | Python | Q1 | 9425 | 3.7 | 9.0 | 12.4 | 282,743 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 9137 | 3.7 | 9.0 | 12.4 | 274,115 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 9492 | 3.6 | 9.1 | 12.7 | 284,760 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 9434 | 3.6 | 9.2 | 12.8 | 283,011 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8462 | 4.2 | 9.4 | 12.5 | 253,860 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8159 | 4.3 | 9.9 | 14.3 | 244,777 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4627 | 8.3 | 12.5 | 15.2 | 138,823 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4709 | 8.2 | 12.4 | 15.2 | 141,263 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 8811 | 3.7 | 10.4 | 16.2 | 264,319 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 6256 | 5.0 | 15.8 | 25.2 | 187,683 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 8265 | 4.4 | 8.7 | 11.3 | 247,946 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 7485 | 4.8 | 10.1 | 14.2 | 224,552 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 9225 | 3.7 | 9.3 | 12.9 | 276,763 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9433 | 3.7 | 9.1 | 12.5 | 282,985 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8041 | 4.4 | 9.8 | 13.2 | 241,229 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 7626 | 4.7 | 10.4 | 14.2 | 228,769 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 9633 | 3.6 | 8.6 | 11.7 | 289,001 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9076 | 3.8 | 9.4 | 13.0 | 272,283 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3856 | 9.9 | 16.9 | 20.8 | 115,678 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3868 | 9.8 | 16.9 | 21.0 | 116,039 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Python | 9425 | 3.7 | 12.4 | 0.0% |
| fraiseql-tv-nocache | Python | 9137 | 3.7 | 12.4 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Python | graphql-precomputed | 9425 | 3.7 | 12.4 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 9137 | 3.7 | 12.4 |