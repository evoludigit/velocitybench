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
| fraiseql-tv | Q1 | 2389 | 15.1 | 33.3 | 42.7 | 47,784 | 0.0% |
| fraiseql-v | Q1 | 2997 | 11.8 | 26.6 | 35.3 | 59,945 | 0.0% |
| go-gqlgen | Q1 | 4406 | 8.8 | 13.4 | 15.9 | 88,117 | 0.0% |
| actix-web-rest | Q1 | 5010 | 7.7 | 11.5 | 13.4 | 100,195 | 0.0% |
| async-graphql | Q1 | 3501 | 10.4 | 20.9 | 28.1 | 70,015 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2 | 2453 | 14.5 | 33.2 | 43.0 | 49,054 | 0.0% |
| fraiseql-v | Q2 | 2659 | 13.3 | 30.3 | 39.7 | 53,174 | 0.0% |
| go-gqlgen | Q2 | 958 | 40.2 | 73.8 | 83.3 | 19,158 | 0.0% |
| actix-web-rest | Q2 | 5290 | 7.2 | 12.5 | 15.4 | 105,797 | 0.0% |
| async-graphql | Q2 | 3134 | 11.3 | 25.2 | 34.0 | 62,672 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2b | 2608 | 13.3 | 31.6 | 41.5 | 52,156 | 0.0% |
| fraiseql-v | Q2b | 2353 | 15.1 | 33.8 | 43.4 | 47,054 | 0.0% |
| go-gqlgen | Q2b | — | — | — | — | — | _known bug — skipped_ |
| actix-web-rest | Q2b | 5171 | 7.3 | 12.8 | 15.7 | 103,422 | 0.0% |
| async-graphql | Q2b | 3323 | 10.9 | 21.5 | 28.8 | 66,466 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | RPS | p50 ms | p99 ms |
|-----------|----:|-------:|-------:|
| actix-web-rest | 5010 | 7.7 | 13.4 |
| go-gqlgen | 4406 | 8.8 | 15.9 |
| async-graphql | 3501 | 10.4 | 28.1 |
| fraiseql-v | 2997 | 11.8 | 35.3 |
| fraiseql-tv | 2389 | 15.1 | 42.7 |