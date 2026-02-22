# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-02-22  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 20s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q1 | 2022 | 18.0 | 38.3 | 48.0 | 40,449 | 0.0% |
| fraiseql-v | Q1 | 1970 | 18.6 | 38.4 | 48.5 | 39,403 | 0.0% |
| go-gqlgen | Q1 | 4366 | 8.8 | 13.6 | 16.1 | 87,312 | 0.0% |
| actix-web-rest | Q1 | 5022 | 7.7 | 11.5 | 13.4 | 100,437 | 0.0% |
| async-graphql | Q1 | 3361 | 10.8 | 21.7 | 28.5 | 67,228 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2 | 1885 | 19.6 | 39.9 | 49.4 | 37,696 | 0.0% |
| fraiseql-v | Q2 | 1950 | 18.7 | 39.2 | 49.3 | 38,995 | 0.0% |
| go-gqlgen | Q2 | 969 | 40.2 | 68.2 | 79.9 | 19,381 | 0.0% |
| actix-web-rest | Q2 | 5167 | 7.3 | 12.9 | 16.0 | 103,331 | 0.0% |
| async-graphql | Q2 | 3185 | 11.0 | 24.9 | 33.0 | 63,698 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2b | 1889 | 19.4 | 40.3 | 50.2 | 37,774 | 0.0% |
| fraiseql-v | Q2b | 1960 | 18.5 | 40.2 | 51.2 | 39,195 | 0.0% |
| go-gqlgen | Q2b | — | — | — | — | — | _known bug — skipped_ |
| actix-web-rest | Q2b | 5209 | 7.3 | 12.7 | 15.7 | 104,181 | 0.0% |
| async-graphql | Q2b | 3966 | 9.3 | 17.2 | 24.2 | 79,315 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | RPS | p50 ms | p99 ms |
|-----------|----:|-------:|-------:|
| actix-web-rest | 5022 | 7.7 | 13.4 |
| go-gqlgen | 4366 | 8.8 | 16.1 |
| async-graphql | 3361 | 10.8 | 28.5 |
| fraiseql-tv | 2022 | 18.0 | 48.0 |
| fraiseql-v | 1970 | 18.6 | 48.5 |