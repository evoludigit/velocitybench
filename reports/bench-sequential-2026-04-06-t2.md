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
| fraiseql-tv | Python | Q1 | 9722 | 3.6 | 8.7 | 11.8 | 291,657 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 8871 | 3.9 | 9.7 | 13.7 | 266,124 | 0.0% |
| fraiseql-v | Python | Q1 | 8023 | 4.3 | 10.4 | 14.4 | 240,700 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 10261 | 3.4 | 8.3 | 11.4 | 307,818 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 8890 | 3.7 | 10.1 | 15.5 | 266,706 | 0.0% |
| fraiseql-v | Python | Q2 | 5853 | 6.0 | 14.6 | 20.0 | 175,604 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 8021 | 4.4 | 10.2 | 14.2 | 240,638 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 8510 | 4.2 | 9.4 | 12.9 | 255,297 | 0.0% |
| fraiseql-v | Python | Q2b | 5119 | 6.9 | 15.9 | 21.4 | 153,564 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | 4588 | 8.4 | 12.9 | 15.8 | 137,648 | 0.0% |
| fraiseql-tv-nocache | Python | Q3 | 4728 | 8.1 | 12.4 | 15.2 | 141,840 | 0.0% |
| fraiseql-v | Python | Q3 | 829 | 34.4 | 96.7 | 105.6 | 24,866 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 1051 | 18.2 | 93.7 | 104.1 | 31,531 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 889 | 23.1 | 95.6 | 105.5 | 26,659 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 166 | 163.6 | 726.8 | 1119.6 | 4,988 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1583 | 15.4 | 83.3 | 133.3 | 47,486 | 0.0% |
| fraiseql-v | Python | M1 | 1628 | 15.3 | 79.2 | 125.2 | 48,834 | 0.0% |
| fraiseql-tv-audit | Python | M1 | — | — | — | — | — | _service did not become healthy_ |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 9341 | 3.7 | 9.2 | 12.7 | 280,238 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 9717 | 3.6 | 8.8 | 12.0 | 291,501 | 0.0% |
| fraiseql-v | Python | F1 | 3395 | 9.8 | 27.5 | 38.8 | 101,842 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 8452 | 4.3 | 9.3 | 12.4 | 253,546 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 8484 | 4.2 | 9.2 | 12.3 | 254,514 | 0.0% |
| fraiseql-v | Python | F2 | 2463 | 13.4 | 37.9 | 49.6 | 73,885 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 9112 | 3.8 | 9.4 | 13.0 | 273,364 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 8668 | 3.9 | 10.0 | 14.6 | 260,034 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | T1 | 3 | 7699.7 | 17855.7 | 18596.2 | 103 | 17.6% |
| fraiseql-tv-nocache | Python | T1 | 4 | 7349.3 | 18796.9 | 21330.3 | 126 | 8.7% |
| fraiseql-v | Python | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Python | 9722 | 3.6 | 11.8 | 0.0% |
| fraiseql-tv-nocache | Python | 8871 | 3.9 | 13.7 | 0.0% |
| fraiseql-v | Python | 8023 | 4.3 | 14.4 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Python | graphql-precomputed | 9722 | 3.6 | 11.8 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 8871 | 3.9 | 13.7 |
| fraiseql-v | Python | graphql-precomputed | 8023 | 4.3 | 14.4 |