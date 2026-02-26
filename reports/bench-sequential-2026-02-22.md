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
| actix-web-rest | Q1 | 5501 | 7.0 | 10.3 | 12.0 | 110,015 | 0.0% |
| async-graphql | Q1 | 4038 | 8.7 | 19.6 | 29.8 | 80,756 | 0.0% |
| juniper | Q1 | 4658 | 8.3 | 12.5 | 15.0 | 93,170 | 0.0% |
| go-gqlgen | Q1 | 5019 | 7.7 | 11.5 | 13.4 | 100,378 | 0.0% |
| gin-rest | Q1 | 5850 | 6.6 | 10.0 | 11.6 | 117,007 | 0.0% |
| go-graphql-go | Q1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Q1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-orm | Q1 | — | — | — | — | — | _service did not become healthy_ |
| express-rest | Q1 | — | — | — | — | — | _service did not become healthy_ |
| express-orm | Q1 | — | — | — | — | — | _service did not become healthy_ |
| express-graphql | Q1 | 692 | 12.8 | 14.6 | 16.3 | 13,831 | 79.7% |
| graphql-yoga | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| mercurius | Q1 | 4681 | 7.6 | 13.0 | 14.8 | 93,621 | 3.3% |
| strawberry | Q1 | 906 | 42.3 | 52.3 | 53.1 | 18,122 | 0.0% |
| graphene | Q1 | — | — | — | — | — | _service did not become healthy_ |
| fastapi-rest | Q1 | 1707 | 12.9 | 14.8 | 21.2 | 34,139 | 47.0% |
| flask-rest | Q1 | — | — | — | — | — | _service did not become healthy_ |
| ariadne | Q1 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Q1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Q1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot-orm | Q1 | 4693 | 7.7 | 15.7 | 20.1 | 93,856 | 0.0% |
| micronaut-graphql | Q1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Q1 | 4913 | 7.5 | 14.0 | 20.7 | 98,264 | 0.0% |
| play-graphql | Q1 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Q1 | — | — | — | — | — | _service did not become healthy_ |
| hanami | Q1 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| webonyx-graphql-php | Q1 | 63 | 644.6 | 778.3 | 813.7 | 1,259 | 0.0% |
| csharp-dotnet | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Q1 | 2258 | 14.3 | 39.7 | 50.0 | 45,162 | 0.0% |
| fraiseql-tv-nocache | Q1 | 5545 | 6.9 | 11.5 | 14.0 | 110,906 | 0.0% |
| fraiseql-v | Q1 | 2221 | 14.9 | 40.0 | 50.2 | 44,427 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Q2 | 5648 | 6.7 | 11.7 | 14.5 | 112,963 | 0.0% |
| async-graphql | Q2 | 4197 | 8.2 | 19.2 | 32.5 | 83,934 | 0.0% |
| juniper | Q2 | 4843 | 7.7 | 13.8 | 19.3 | 96,858 | 0.0% |
| go-gqlgen | Q2 | 980 | 40.1 | 66.5 | 82.1 | 19,590 | 0.0% |
| gin-rest | Q2 | 6422 | 5.9 | 10.3 | 12.6 | 128,442 | 0.0% |
| go-graphql-go | Q2 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Q2 | — | — | — | — | — | _service did not become healthy_ |
| apollo-orm | Q2 | — | — | — | — | — | _service did not become healthy_ |
| express-rest | Q2 | — | — | — | — | — | _service did not become healthy_ |
| express-orm | Q2 | — | — | — | — | — | _service did not become healthy_ |
| express-graphql | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| graphql-yoga | Q2 | 1406 | 7.0 | 11.8 | 13.7 | 28,116 | 64.6% |
| mercurius | Q2 | 133 | 10.3 | 16.6 | 22.8 | 2,666 | 96.1% |
| strawberry | Q2 | 143 | 13.1 | 37.8 | 47.5 | 2,858 | 95.8% |
| graphene | Q2 | — | — | — | — | — | _service did not become healthy_ |
| fastapi-rest | Q2 | 78 | 9.7 | 19.6 | 24.8 | 1,569 | 97.7% |
| flask-rest | Q2 | — | — | — | — | — | _service did not become healthy_ |
| ariadne | Q2 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Q2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Q2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot-orm | Q2 | 6137 | 6.1 | 11.1 | 15.2 | 122,746 | 0.0% |
| micronaut-graphql | Q2 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Q2 | 3478 | 9.0 | 28.2 | 40.3 | 69,559 | 0.0% |
| play-graphql | Q2 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Q2 | — | — | — | — | — | _service did not become healthy_ |
| hanami | Q2 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| webonyx-graphql-php | Q2 | 63 | 644.0 | 785.6 | 841.8 | 1,257 | 0.0% |
| csharp-dotnet | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Q2 | 2181 | 15.6 | 40.3 | 50.2 | 43,614 | 0.0% |
| fraiseql-tv-nocache | Q2 | 5412 | 7.0 | 12.1 | 16.1 | 108,249 | 0.0% |
| fraiseql-v | Q2 | 2167 | 15.7 | 40.4 | 50.4 | 43,347 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Q2b | 5752 | 6.6 | 11.5 | 14.2 | 115,041 | 0.0% |
| async-graphql | Q2b | 2992 | 11.8 | 25.8 | 34.2 | 59,846 | 0.0% |
| juniper | Q2b | 3417 | 11.5 | 14.6 | 16.6 | 68,343 | 0.0% |
| go-gqlgen | Q2b | — | — | — | — | — | _known bug — skipped_ |
| gin-rest | Q2b | 2881 | 12.8 | 26.3 | 33.3 | 57,614 | 0.0% |
| go-graphql-go | Q2b | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Q2b | — | — | — | — | — | _service did not become healthy_ |
| apollo-orm | Q2b | — | — | — | — | — | _service did not become healthy_ |
| express-rest | Q2b | — | — | — | — | — | _service did not become healthy_ |
| express-orm | Q2b | — | — | — | — | — | _service did not become healthy_ |
| express-graphql | Q2b | 1412 | 15.0 | 18.4 | 24.8 | 28,238 | 52.8% |
| graphql-yoga | Q2b | 806 | 8.5 | 11.6 | 17.8 | 16,122 | 77.7% |
| mercurius | Q2b | 967 | 7.7 | 14.6 | 19.7 | 19,332 | 73.3% |
| strawberry | Q2b | 431 | 54.5 | 67.2 | 70.1 | 8,622 | 77.8% |
| graphene | Q2b | — | — | — | — | — | _service did not become healthy_ |
| fastapi-rest | Q2b | 1120 | 13.6 | 15.3 | 17.7 | 22,402 | 66.0% |
| flask-rest | Q2b | — | — | — | — | — | _service did not become healthy_ |
| ariadne | Q2b | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Q2b | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Q2b | — | — | — | — | — | _service did not become healthy_ |
| spring-boot-orm | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Q2b | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Q2b | 3414 | 11.0 | 20.2 | 25.3 | 68,288 | 0.0% |
| play-graphql | Q2b | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Q2b | — | — | — | — | — | _service did not become healthy_ |
| hanami | Q2b | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | Q2b | — | — | — | — | — | _known bug — skipped_ |
| webonyx-graphql-php | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| csharp-dotnet | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Q2b | 2013 | 17.5 | 42.7 | 52.9 | 40,261 | 0.0% |
| fraiseql-tv-nocache | Q2b | 5011 | 7.5 | 13.1 | 18.2 | 100,220 | 0.0% |
| fraiseql-v | Q2b | 1835 | 20.2 | 45.8 | 56.4 | 36,692 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Cache | RPS | p50 ms | p99 ms |
|-----------|-------|----:|-------:|-------:|
| gin-rest | on | 5850 | 6.6 | 11.6 |
| fraiseql-tv-nocache | off | 5545 | 6.9 | 14.0 |
| actix-web-rest | on | 5501 | 7.0 | 12.0 |
| go-gqlgen | on | 5019 | 7.7 | 13.4 |
| quarkus-graphql | on | 4913 | 7.5 | 20.7 |
| spring-boot-orm | on | 4693 | 7.7 | 20.1 |
| mercurius | on | 4681 | 7.6 | 14.8 |
| juniper | on | 4658 | 8.3 | 15.0 |
| async-graphql | on | 4038 | 8.7 | 29.8 |
| fraiseql-tv | on | 2258 | 14.3 | 50.0 |
| fraiseql-v | on | 2221 | 14.9 | 50.2 |
| fastapi-rest | on | 1707 | 12.9 | 21.2 |
| strawberry | on | 906 | 42.3 | 53.1 |
| express-graphql | on | 692 | 12.8 | 16.3 |
| webonyx-graphql-php | on | 63 | 644.6 | 813.7 |
| graphql-yoga | on | 0 | 0.0 | 0.0 |
| php-laravel | on | 0 | 0.0 | 0.0 |
| csharp-dotnet | on | 0 | 0.0 | 0.0 |