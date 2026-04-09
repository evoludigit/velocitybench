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
| fraiseql-tv | Python | Q1 | 5909 | 4.9 | 18.5 | 28.8 | 177,265 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 7643 | 4.2 | 11.4 | 17.3 | 229,286 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 5483 | 4.9 | 21.4 | 32.0 | 164,502 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 8703 | 3.9 | 10.2 | 14.9 | 261,077 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 4804 | 5.9 | 22.9 | 34.5 | 144,134 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 6505 | 5.1 | 13.8 | 20.7 | 195,160 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 5417 | 6.7 | 13.3 | 17.5 | 162,522 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4207 | 8.7 | 13.5 | 16.8 | 126,196 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 3997 | 7.5 | 26.6 | 37.9 | 119,916 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 7201 | 4.4 | 12.7 | 19.3 | 216,037 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 7539 | 4.8 | 9.9 | 13.9 | 226,162 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 7519 | 4.8 | 10.0 | 13.8 | 225,582 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 4360 | 6.7 | 24.4 | 35.0 | 130,806 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 7156 | 4.5 | 13.5 | 20.9 | 214,688 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 6115 | 5.1 | 16.4 | 25.2 | 183,445 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8261 | 4.3 | 9.5 | 12.6 | 247,836 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 5133 | 5.7 | 20.8 | 31.0 | 153,986 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9398 | 3.7 | 8.9 | 12.3 | 281,949 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 2698 | 12.2 | 33.8 | 46.9 | 80,943 | 0.0% |
| fraiseql-tv-nocache | Python | T1 | 3760 | 9.8 | 17.1 | 21.6 | 112,810 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 7643 | 4.2 | 17.3 | 0.0% |
| fraiseql-tv | Python | 5909 | 4.9 | 28.8 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 7643 | 4.2 | 17.3 |
| fraiseql-tv | Python | graphql-precomputed | 5909 | 4.9 | 28.8 |