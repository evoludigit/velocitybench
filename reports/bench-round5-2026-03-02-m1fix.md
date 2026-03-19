# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-02  
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
| fraiseql-tv | Python | Q1 | 210 | 182.0 | 263.5 | 298.0 | 4,195 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 208 | 180.3 | 278.3 | 341.5 | 4,167 | 0.0% |
| fraiseql-v | Python | Q1 | 145 | 255.2 | 395.8 | 466.7 | 2,904 | 0.0% |
| ruby-rails | Ruby | Q1 | 891 | 40.8 | 81.0 | 97.3 | 17,817 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 39 | 933.0 | 1570.7 | 1775.4 | 787 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 42 | 883.2 | 1492.6 | 1658.4 | 841 | 0.0% |
| fraiseql-v | Python | Q2 | 23 | 1683.3 | 2581.9 | 3057.1 | 458 | 0.0% |
| ruby-rails | Ruby | Q2 | 588 | 60.7 | 123.8 | 143.1 | 11,756 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 18 | 2085.6 | 3945.0 | 4371.1 | 356 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 18 | 2035.7 | 4055.9 | 4690.5 | 358 | 0.0% |
| fraiseql-v | Python | Q2b | 9 | 4425.4 | 6933.4 | 8497.7 | 180 | 0.0% |
| ruby-rails | Ruby | Q2b | 444 | 92.9 | 134.8 | 149.8 | 8,880 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 842 | 46.0 | 69.1 | 80.2 | 16,834 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 795 | 48.5 | 74.7 | 89.0 | 15,893 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv-nocache | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-v | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv-audit | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ruby-rails | Ruby | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 42 | 865.4 | 1462.4 | 1611.6 | 847 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 40 | 920.4 | 1557.2 | 1738.1 | 800 | 0.0% |
| fraiseql-v | Python | F1 | 14 | 2662.7 | 4385.2 | 5326.6 | 282 | 0.0% |
| ruby-rails | Ruby | F1 | 437 | 92.9 | 145.5 | 160.6 | 8,733 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 18 | 2107.9 | 3920.7 | 4787.8 | 355 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 17 | 2304.0 | 4201.2 | 5041.1 | 332 | 0.0% |
| fraiseql-v | Python | F2 | 7 | 5671.3 | 9476.6 | 12376.8 | 145 | 0.0% |
| ruby-rails | Ruby | F2 | 845 | 38.2 | 108.4 | 132.7 | 16,908 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 205 | 184.8 | 274.4 | 325.1 | 4,099 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 213 | 179.1 | 262.6 | 301.4 | 4,262 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| ruby-rails | Ruby | 891 | 40.8 | 97.3 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Python | 210 | 182.0 | 298.0 | 0.0% |
| fraiseql-tv-nocache | Python | 208 | 180.3 | 341.5 | 0.0% |
| fraiseql-v | Python | 145 | 255.2 | 466.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| ruby-rails | Ruby | rest | 891 | 40.8 | 97.3 |
| fraiseql-tv | Python | graphql-precomputed | 210 | 182.0 | 298.0 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 208 | 180.3 | 341.5 |
| fraiseql-v | Python | graphql-precomputed | 145 | 255.2 | 466.7 |