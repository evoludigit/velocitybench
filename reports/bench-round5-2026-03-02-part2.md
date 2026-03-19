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
| ariadne | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | Q1 | 4077 | 9.0 | 17.0 | 22.4 | 81,537 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 4634 | 8.2 | 13.0 | 17.0 | 92,677 | 0.0% |
| micronaut-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q1 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q1 | 954 | 25.8 | 95.0 | 109.3 | 19,078 | 0.0% |
| hanami | Ruby | Q1 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q1 | 101 | 380.3 | 555.4 | 575.5 | 2,021 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q1 | 4173 | 9.1 | 15.1 | 18.5 | 83,459 | 0.0% |
| fraiseql-tv | Python | Q1 | 157 | 194.0 | 303.7 | 9420.4 | 3,148 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 176 | 203.3 | 379.4 | 472.9 | 3,529 | 0.0% |
| fraiseql-v | Python | Q1 | 100 | 366.6 | 677.0 | 840.7 | 2,000 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| ariadne | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q2 | 1040 | 27.3 | 79.4 | 114.2 | 20,791 | 0.0% |
| spring-boot-orm | Java | Q2 | 4479 | 8.3 | 15.6 | 20.7 | 89,577 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 4617 | 8.0 | 15.3 | 20.3 | 92,340 | 0.0% |
| micronaut-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2 | 710 | 41.6 | 134.1 | 149.1 | 14,205 | 0.0% |
| hanami | Ruby | Q2 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2 | 84 | 466.0 | 669.0 | 706.4 | 1,673 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q2 | 3429 | 10.1 | 23.6 | 32.7 | 68,576 | 0.0% |
| fraiseql-tv | Python | Q2 | 38 | 938.7 | 1640.9 | 1823.6 | 770 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 40 | 903.7 | 1584.3 | 1756.2 | 801 | 0.0% |
| fraiseql-v | Python | Q2 | 17 | 2218.9 | 3868.3 | 5457.8 | 343 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| ariadne | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2b | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2b | 407 | 46.3 | 144.4 | 164.9 | 8,134 | 0.0% |
| hanami | Ruby | Q2b | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2b | 82 | 481.4 | 654.2 | 688.1 | 1,646 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q2b | 3869 | 9.5 | 17.9 | 26.8 | 77,387 | 0.0% |
| fraiseql-tv | Python | Q2b | 17 | 2130.8 | 4233.6 | 4886.5 | 345 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 13 | 2761.8 | 5265.4 | 6674.6 | 266 | 0.0% |
| fraiseql-v | Python | Q2b | 9 | 4506.5 | 7274.5 | 8771.0 | 176 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| ariadne | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | F1 | 1099 | 22.7 | 40.3 | 59.4 | 21,984 | 0.0% |
| spring-boot-orm | Java | F1 | 4438 | 8.3 | 16.1 | 22.2 | 88,767 | 0.0% |
| ruby-rails | Ruby | F1 | 338 | 80.2 | 156.2 | 2650.5 | 6,769 | 0.0% |
| php-laravel | PHP | F1 | 90 | 434.1 | 598.2 | 628.9 | 1,795 | 0.0% |
| webonyx-graphql-php | PHP | F1 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | F1 | 2200 | 10.7 | 24.6 | 34.0 | 44,001 | 0.0% |
| fraiseql-tv | Python | F1 | 42 | 870.5 | 1491.3 | 1645.4 | 843 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 36 | 975.2 | 1841.2 | 2369.8 | 715 | 0.0% |
| fraiseql-v | Python | F1 | 22 | 1799.1 | 2660.5 | 3404.7 | 434 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| ariadne | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | F2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | 404 | 94.2 | 157.1 | 174.8 | 8,084 | 0.0% |
| php-laravel | PHP | F2 | 43 | 421.4 | 650.8 | 718.6 | 859 | 99.2% (connection_refused: 94%, connection_error: 6%, json_error: 0%) |
| webonyx-graphql-php | PHP | F2 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | F2 | 3245 | 10.7 | 24.5 | 33.4 | 64,908 | 0.0% |
| fraiseql-tv | Python | F2 | 16 | 2309.2 | 4787.1 | 6386.3 | 311 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 17 | 2154.6 | 3593.0 | 4496.2 | 349 | 0.0% |
| fraiseql-v | Python | F2 | 9 | 4511.3 | 7172.1 | 9765.0 | 175 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| spring-boot | Java | M1 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv-nocache | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-v | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv-audit | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| quarkus-graphql | Java | Q3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 531 | 47.3 | 77.4 | 107.1 | 10,614 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 283 | 86.5 | 170.7 | 213.0 | 5,667 | 0.7% (connection_error: 100%) |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 118 | 313.7 | 484.8 | 571.8 | 2,367 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 204 | 187.6 | 274.3 | 317.4 | 4,073 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| spring-boot-orm-naive | Java | 4634 | 8.2 | 17.0 | 0.0% |
| spring-boot-orm | Java | 4077 | 9.0 | 22.4 | 0.0% |
| ruby-rails | Ruby | 954 | 25.8 | 109.3 | 0.0% |
| php-laravel | PHP | 101 | 380.3 | 575.5 | 0.0% |
| spring-boot | Java | 0 | 0.0 | 0.0 | 100.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| csharp-dotnet | C# | 4173 | 9.1 | 18.5 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 176 | 203.3 | 472.9 | 0.0% |
| fraiseql-tv | Python | 157 | 194.0 | 9420.4 | 0.0% |
| fraiseql-v | Python | 100 | 366.6 | 840.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| spring-boot-orm-naive | Java | rest | 4634 | 8.2 | 17.0 |
| csharp-dotnet | C# | graphql | 4173 | 9.1 | 18.5 |
| spring-boot-orm | Java | rest | 4077 | 9.0 | 22.4 |
| ruby-rails | Ruby | rest | 954 | 25.8 | 109.3 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 176 | 203.3 | 472.9 |
| fraiseql-tv | Python | graphql-precomputed | 157 | 194.0 | 9420.4 |
| php-laravel | PHP | rest | 101 | 380.3 | 575.5 |
| fraiseql-v | Python | graphql-precomputed | 100 | 366.6 | 840.7 |
| spring-boot | Java | rest | 0 | 0.0 | 0.0 |