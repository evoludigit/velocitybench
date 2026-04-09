# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-26  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 10s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | Q1 | 8175 | 4.3 | 10.2 | 14.1 | 81,751 | 0.0% |
| fraiseql-tv | Python | Q1 | 8260 | 4.0 | 10.9 | 16.0 | 82,601 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 9001 | 3.7 | 9.8 | 14.4 | 90,010 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | Q2 | 6873 | 5.0 | 12.8 | 17.7 | 68,729 | 0.0% |
| fraiseql-tv | Python | Q2 | 7060 | 4.5 | 13.8 | 22.0 | 70,601 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 4677 | 6.2 | 23.2 | 35.0 | 46,769 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | Q2b | 5602 | 6.3 | 14.4 | 19.4 | 56,015 | 0.0% |
| fraiseql-tv | Python | Q2b | 7611 | 4.3 | 12.2 | 19.1 | 76,110 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 6760 | 4.5 | 14.9 | 26.0 | 67,600 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | M1 | 1862 | 12.3 | 72.3 | 116.0 | 18,619 | 0.0% |
| fraiseql-tv | Python | M1 | 1858 | 12.3 | 72.8 | 118.6 | 18,575 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 656 | 34.2 | 210.7 | 335.7 | 6,564 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 1841 | 12.3 | 74.6 | 117.7 | 18,411 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | F1 | 6833 | 5.0 | 12.7 | 17.9 | 68,330 | 0.0% |
| fraiseql-tv | Python | F1 | 5445 | 5.5 | 19.4 | 30.0 | 54,446 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 5894 | 5.2 | 17.4 | 27.1 | 58,938 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-v | Python | F2 | 5784 | 6.1 | 13.9 | 18.6 | 57,843 | 0.0% |
| fraiseql-tv | Python | F2 | 6907 | 4.6 | 13.8 | 21.6 | 69,073 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 7110 | 4.6 | 12.9 | 19.1 | 71,098 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 10274 | 3.5 | 7.6 | 10.3 | 102,740 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 10514 | 3.4 | 7.5 | 10.0 | 105,139 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 8857 | 3.8 | 9.9 | 14.3 | 88,568 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 9225 | 3.7 | 9.5 | 13.4 | 92,248 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 9001 | 3.7 | 14.4 | 0.0% |
| fraiseql-tv | Python | 8260 | 4.0 | 16.0 | 0.0% |
| fraiseql-v | Python | 8175 | 4.3 | 14.1 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-nocache | Python | graphql-precomputed | 9001 | 3.7 | 14.4 |
| fraiseql-tv | Python | graphql-precomputed | 8260 | 4.0 | 16.0 |
| fraiseql-v | Python | graphql-precomputed | 8175 | 4.3 | 14.1 |