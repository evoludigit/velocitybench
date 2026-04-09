# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-07  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 20s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q1 | 8140 | 4.0 | 11.1 | 18.1 | 162,792 | 0.0% |
| fraiseql-tv | Python | Q1 | 2704 | 12.9 | 31.7 | 43.3 | 54,076 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q2 | 6414 | 4.7 | 16.4 | 27.2 | 128,282 | 0.0% |
| fraiseql-tv | Python | Q2 | 2860 | 12.2 | 29.9 | 41.0 | 57,205 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q2b | 8682 | 4.1 | 9.1 | 12.1 | 173,636 | 0.0% |
| fraiseql-tv | Python | Q2b | 2659 | 13.0 | 32.4 | 44.3 | 53,184 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | Q3 | 4796 | 8.0 | 12.1 | 14.8 | 95,928 | 0.0% |
| fraiseql-tv | Python | Q3 | 5600 | 6.5 | 13.1 | 17.3 | 111,992 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | C3 | 2759 | 12.2 | 33.2 | 46.0 | 55,178 | 0.0% |
| fraiseql-tv | Python | C3 | 3176 | 10.6 | 29.9 | 41.3 | 63,510 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | M1 | 5581 | 5.7 | 16.6 | 27.2 | 111,622 | 0.0% |
| fraiseql-tv | Python | M1 | 6566 | 5.2 | 12.6 | 20.3 | 131,319 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 7412 | 4.8 | 10.1 | 15.2 | 148,230 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F1 | 8519 | 3.8 | 10.6 | 18.0 | 170,378 | 0.0% |
| fraiseql-tv | Python | F1 | 2871 | 12.1 | 30.2 | 41.0 | 57,427 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F2 | 8475 | 4.2 | 9.2 | 12.3 | 169,493 | 0.0% |
| fraiseql-tv | Python | F2 | 3033 | 11.1 | 30.9 | 42.7 | 60,666 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | F3 | 8722 | 3.9 | 10.1 | 15.1 | 174,435 | 0.0% |
| fraiseql-tv | Python | F3 | 2802 | 12.4 | 30.8 | 42.1 | 56,044 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv-nocache | Python | T1 | 3918 | 9.7 | 16.9 | 21.3 | 78,350 | 0.0% |
| fraiseql-tv | Python | T1 | 1261 | 30.0 | 58.2 | 73.9 | 25,213 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 8140 | 4.0 | 18.1 | 0.0% |
| fraiseql-tv | Python | 2704 | 12.9 | 43.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 8140 | 4.0 | 18.1 |
| fraiseql-tv | Python | graphql-precomputed | 2704 | 12.9 | 43.3 |