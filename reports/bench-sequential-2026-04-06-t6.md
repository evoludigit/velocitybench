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
| fraiseql-tv | Python | Q1 | 9251 | 3.7 | 9.2 | 12.7 | 277,530 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 9350 | 3.7 | 9.0 | 12.3 | 280,492 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 9384 | 3.7 | 9.2 | 12.9 | 281,523 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 9352 | 3.7 | 9.3 | 13.1 | 280,554 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8368 | 4.3 | 9.5 | 12.7 | 251,049 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8345 | 4.3 | 9.6 | 12.9 | 250,358 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4634 | 8.3 | 12.5 | 15.2 | 139,020 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4536 | 8.5 | 13.0 | 15.9 | 136,093 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 9623 | 3.5 | 9.2 | 13.0 | 288,683 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 7891 | 4.1 | 12.1 | 19.4 | 236,736 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 1262 | 24.7 | 76.1 | 139.2 | 37,866 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1248 | 24.8 | 79.4 | 143.7 | 37,441 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 9357 | 3.7 | 9.2 | 12.7 | 280,724 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 7659 | 3.7 | 9.2 | 12.8 | 229,783 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8222 | 4.4 | 9.6 | 12.8 | 246,659 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8114 | 4.4 | 9.7 | 13.1 | 243,428 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 9064 | 3.8 | 9.4 | 13.1 | 271,930 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9034 | 3.8 | 9.4 | 13.1 | 271,022 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3856 | 9.8 | 17.2 | 21.5 | 115,683 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3681 | 10.3 | 18.1 | 22.7 | 110,419 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 9350 | 3.7 | 12.3 | 0.0% |
| fraiseql-tv | Python | 9251 | 3.7 | 12.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 9350 | 3.7 | 12.3 |
| fraiseql-tv | Python | graphql-precomputed | 9251 | 3.7 | 12.7 |