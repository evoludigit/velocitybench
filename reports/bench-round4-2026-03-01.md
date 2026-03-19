# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-01  
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
| actix-web-rest | Rust | Q1 | 4499 | 8.6 | 13.0 | 15.3 | 89,975 | 0.0% |
| async-graphql | Rust | Q1 | 4629 | 8.2 | 14.0 | 18.0 | 92,589 | 0.0% |
| juniper | Rust | Q1 | 4199 | 9.2 | 13.8 | 16.3 | 83,971 | 0.0% |
| go-gqlgen | Go | Q1 | 4400 | 8.8 | 13.3 | 15.6 | 87,992 | 0.0% |
| gin-rest | Go | Q1 | 4524 | 8.5 | 13.2 | 15.9 | 90,482 | 0.0% |
| go-graphql-go | Go | Q1 | 3821 | 9.7 | 17.9 | 23.2 | 76,424 | 0.0% |
| graphql-go | Go | Q1 | 4264 | 9.1 | 13.6 | 16.0 | 85,279 | 0.0% |
| apollo-server | Node.js | Q1 | 1018 | 13.5 | 20.8 | 22.3 | 20,359 | 67.7% |
| apollo-orm | Node.js | Q1 | 980 | 15.2 | 28.3 | 37.7 | 19,594 | 63.9% |
| express-rest | Node.js | Q1 | 1366 | 13.3 | 17.1 | 20.2 | 27,318 | 56.1% |
| express-orm | Node.js | Q1 | 1082 | 16.9 | 29.4 | 35.5 | 21,647 | 58.0% |
| express-graphql | Node.js | Q1 | 954 | 13.3 | 15.7 | 20.0 | 19,071 | 70.0% |
| graphql-yoga | Node.js | Q1 | 4234 | 8.8 | 14.5 | 15.3 | 84,676 | 0.0% |
| mercurius | Node.js | Q1 | 4001 | 9.8 | 13.8 | 15.9 | 80,026 | 0.0% |
| postgraphile | Node.js | Q1 | 1060 | 12.0 | 15.4 | 20.2 | 21,191 | 68.2% |
| strawberry | Python | Q1 | 834 | 47.2 | 58.4 | 59.4 | 16,670 | 0.0% |
| graphene | Python | Q1 | 935 | 41.1 | 50.6 | 51.7 | 18,697 | 11.4% |
| fastapi-rest | Python | Q1 | 4513 | 8.5 | 12.9 | 15.1 | 90,251 | 0.0% |
| flask-rest | Python | Q1 | — | — | — | — | — | _known bug — skipped_ |
| ariadne | Python | Q1 | 963 | 41.1 | 47.6 | 48.7 | 19,252 | 0.0% |
| asgi-graphql | Python | Q1 | 969 | 40.6 | 47.1 | 49.7 | 19,374 | 0.0% |
| spring-boot | Java | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| spring-boot-orm | Java | Q1 | 3634 | 10.2 | 19.1 | 24.7 | 72,677 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 4641 | 8.3 | 12.6 | 15.1 | 92,811 | 0.0% |
| micronaut-graphql | Java | Q1 | 3224 | 9.0 | 19.7 | 31.9 | 64,486 | 0.0% |
| quarkus-graphql | Java | Q1 | 2164 | 17.5 | 31.6 | 39.3 | 43,285 | 0.0% |
| play-graphql | Scala | Q1 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q1 | 1490 | 24.9 | 41.6 | 64.9 | 29,804 | 0.0% |
| hanami | Ruby | Q1 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q1 | 76 | 577.8 | 679.4 | 722.6 | 1,517 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 1023 | 24.0 | 32.8 | 44.7 | 20,455 | 29.9% |
| csharp-dotnet | C# | Q1 | 3884 | 9.7 | 16.9 | 21.2 | 77,682 | 0.0% |
| fraiseql-tv | Python | Q1 | 156 | 242.1 | 383.3 | 437.1 | 3,128 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 163 | 231.2 | 362.1 | 411.2 | 3,259 | 0.0% |
| fraiseql-v | Python | Q1 | 137 | 276.1 | 384.3 | 451.7 | 2,731 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 4774 | 7.8 | 14.5 | 18.9 | 95,481 | 0.0% |
| async-graphql | Rust | Q2 | 4549 | 8.2 | 14.7 | 19.8 | 90,980 | 0.0% |
| juniper | Rust | Q2 | 4259 | 8.9 | 15.6 | 19.7 | 85,179 | 0.0% |
| go-gqlgen | Go | Q2 | 4536 | 8.3 | 14.5 | 18.6 | 90,715 | 0.0% |
| gin-rest | Go | Q2 | 5155 | 7.4 | 12.6 | 15.4 | 103,093 | 0.0% |
| go-graphql-go | Go | Q2 | 4084 | 9.1 | 16.7 | 21.6 | 81,677 | 0.0% |
| graphql-go | Go | Q2 | 3835 | 9.7 | 17.8 | 22.9 | 76,707 | 0.0% |
| apollo-server | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| apollo-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-rest | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-graphql | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| graphql-yoga | Node.js | Q2 | 6 | 9.6 | 18.2 | 22.2 | 119 | 99.8% |
| mercurius | Node.js | Q2 | 346 | 8.7 | 15.2 | 19.4 | 6,913 | 89.7% |
| postgraphile | Node.js | Q2 | 341 | 10.9 | 16.6 | 21.2 | 6,811 | 89.8% |
| strawberry | Python | Q2 | 174 | 41.7 | 52.3 | 57.6 | 3,473 | 94.2% |
| graphene | Python | Q2 | 121 | 14.6 | 36.8 | 46.2 | 2,412 | 96.4% |
| fastapi-rest | Python | Q2 | 3822 | 9.9 | 17.2 | 21.3 | 76,436 | 0.0% |
| flask-rest | Python | Q2 | — | — | — | — | — | _known bug — skipped_ |
| ariadne | Python | Q2 | 15 | 12.1 | 23.0 | 28.1 | 299 | 99.5% |
| asgi-graphql | Python | Q2 | 23 | 12.4 | 41.4 | 59.2 | 465 | 99.3% |
| spring-boot | Java | Q2 | 1590 | 23.9 | 41.2 | 56.2 | 31,808 | 0.0% |
| spring-boot-orm | Java | Q2 | 4257 | 8.7 | 16.5 | 22.1 | 85,148 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 4062 | 8.5 | 19.9 | 29.0 | 81,245 | 0.0% |
| micronaut-graphql | Java | Q2 | 3590 | 8.6 | 15.3 | 21.7 | 71,790 | 0.0% |
| quarkus-graphql | Java | Q2 | 2403 | 15.5 | 30.2 | 38.8 | 48,059 | 0.0% |
| play-graphql | Scala | Q2 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2 | 688 | 47.3 | 105.4 | 132.2 | 13,753 | 0.0% |
| hanami | Ruby | Q2 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2 | 59 | 668.7 | 1369.9 | 1479.1 | 1,186 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| csharp-dotnet | C# | Q2 | 3682 | 10.3 | 17.6 | 21.7 | 73,633 | 0.0% |
| fraiseql-tv | Python | Q2 | 39 | 944.1 | 1608.6 | 1846.0 | 778 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 42 | 888.7 | 1471.4 | 1645.2 | 842 | 0.0% |
| fraiseql-v | Python | Q2 | 24 | 1616.6 | 2575.8 | 2885.5 | 471 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 4433 | 8.4 | 15.1 | 20.0 | 88,660 | 0.0% |
| async-graphql | Rust | Q2b | 3737 | 10.0 | 17.6 | 23.0 | 74,738 | 0.0% |
| juniper | Rust | Q2b | 3211 | 11.9 | 19.4 | 23.2 | 64,222 | 0.0% |
| go-gqlgen | Go | Q2b | 4248 | 8.9 | 15.4 | 19.2 | 84,952 | 0.0% |
| gin-rest | Go | Q2b | 3310 | 10.6 | 23.7 | 31.2 | 66,190 | 0.0% |
| go-graphql-go | Go | Q2b | 1501 | 25.2 | 39.8 | 48.2 | 30,016 | 0.0% |
| graphql-go | Go | Q2b | 1084 | 35.9 | 50.5 | 57.2 | 21,687 | 0.0% |
| apollo-server | Node.js | Q2b | 1383 | 13.8 | 18.4 | 23.3 | 27,656 | 54.8% |
| apollo-orm | Node.js | Q2b | 1182 | 18.6 | 23.1 | 31.8 | 23,630 | 54.9% |
| express-rest | Node.js | Q2b | 2600 | 8.5 | 13.1 | 18.4 | 52,005 | 34.1% |
| express-orm | Node.js | Q2b | 901 | 21.2 | 31.0 | 37.8 | 18,024 | 59.3% |
| express-graphql | Node.js | Q2b | 1285 | 15.6 | 20.4 | 70.9 | 25,692 | 52.7% |
| graphql-yoga | Node.js | Q2b | 1732 | 8.5 | 11.2 | 15.5 | 34,630 | 54.7% |
| mercurius | Node.js | Q2b | 2643 | 8.4 | 12.6 | 16.9 | 52,855 | 34.0% |
| postgraphile | Node.js | Q2b | 1053 | 13.2 | 15.7 | 20.0 | 21,068 | 66.9% |
| strawberry | Python | Q2b | 382 | 62.5 | 76.8 | 79.0 | 7,644 | 78.2% |
| graphene | Python | Q2b | 528 | 51.2 | 63.3 | 65.3 | 10,564 | 71.3% |
| fastapi-rest | Python | Q2b | 3778 | 10.0 | 17.6 | 21.9 | 75,567 | 0.0% |
| flask-rest | Python | Q2b | — | — | — | — | — | _known bug — skipped_ |
| ariadne | Python | Q2b | 410 | 56.0 | 71.0 | 173.8 | 8,196 | 72.4% |
| asgi-graphql | Python | Q2b | 501 | 52.2 | 60.7 | 65.2 | 10,013 | 67.4% |
| spring-boot | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | 1576 | 11.2 | 25.4 | 39.8 | 31,525 | 0.0% |
| quarkus-graphql | Java | Q2b | 2346 | 15.7 | 32.1 | 41.1 | 46,927 | 0.0% |
| play-graphql | Scala | Q2b | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2b | — | — | — | — | — | _known bug — skipped_ |
| hanami | Ruby | Q2b | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2b | 55 | 665.2 | 812.3 | 3240.3 | 1,099 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| csharp-dotnet | C# | Q2b | 3552 | 10.8 | 18.1 | 22.2 | 71,044 | 0.0% |
| fraiseql-tv | Python | Q2b | 17 | 2073.0 | 4078.9 | 4637.4 | 349 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 18 | 2069.0 | 3901.0 | 4584.3 | 355 | 0.0% |
| fraiseql-v | Python | Q2b | 9 | 4355.9 | 7846.4 | 9106.7 | 179 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | — | — | — | — | — | _known bug — skipped_ |
| async-graphql | Rust | M1 | — | — | — | — | — | _known bug — skipped_ |
| go-gqlgen | Go | M1 | — | — | — | — | — | _known bug — skipped_ |
| gin-rest | Go | M1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv | Python | M1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | M1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-v | Python | M1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-audit | Python | M1 | — | — | — | — | — | _known bug — skipped_ |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 4898 | 7.7 | 13.8 | 17.7 | 97,955 | 0.0% |
| async-graphql | Rust | F1 | 4285 | 8.5 | 16.6 | 24.8 | 85,705 | 0.0% |
| juniper | Rust | F1 | 4284 | 8.8 | 15.6 | 19.7 | 85,672 | 0.0% |
| go-gqlgen | Go | F1 | 4687 | 8.1 | 13.9 | 17.6 | 93,747 | 0.0% |
| gin-rest | Go | F1 | 4777 | 7.9 | 14.0 | 17.5 | 95,541 | 0.0% |
| go-graphql-go | Go | F1 | 4314 | 8.8 | 15.3 | 19.2 | 86,271 | 0.0% |
| graphql-go | Go | F1 | 3862 | 9.7 | 17.8 | 22.8 | 77,247 | 0.0% |
| apollo-server | Node.js | F1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| apollo-orm | Node.js | F1 | 22 | 11.5 | 25.1 | 30.0 | 446 | 99.2% |
| express-rest | Node.js | F1 | 1556 | 25.0 | 48.3 | 65.2 | 31,129 | 0.5% |
| express-orm | Node.js | F1 | 37 | 12.9 | 33.0 | 48.6 | 738 | 98.7% |
| express-graphql | Node.js | F1 | 56 | 10.5 | 19.3 | 23.8 | 1,114 | 98.3% |
| graphql-yoga | Node.js | F1 | 1957 | 10.4 | 14.9 | 17.5 | 39,143 | 44.3% |
| mercurius | Node.js | F1 | 1790 | 12.0 | 15.0 | 18.1 | 35,791 | 47.6% |
| strawberry | Python | F1 | 845 | 45.8 | 58.5 | 59.9 | 16,895 | 7.1% |
| graphene | Python | F1 | 771 | 40.1 | 51.1 | 52.4 | 15,413 | 53.5% |
| fastapi-rest | Python | F1 | 3763 | 10.1 | 17.6 | 21.9 | 75,261 | 0.0% |
| flask-rest | Python | F1 | — | — | — | — | — | _known bug — skipped_ |
| ariadne | Python | F1 | 845 | 40.1 | 48.6 | 59.1 | 16,897 | 37.6% |
| asgi-graphql | Python | F1 | 770 | 39.5 | 48.3 | 88.6 | 15,395 | 44.7% |
| spring-boot | Java | F1 | 1682 | 22.7 | 39.1 | 46.7 | 33,642 | 0.0% |
| spring-boot-orm | Java | F1 | 4104 | 8.8 | 18.3 | 25.4 | 82,081 | 0.0% |
| ruby-rails | Ruby | F1 | 835 | 44.1 | 73.7 | 82.5 | 16,709 | 0.0% |
| php-laravel | PHP | F1 | 48 | 662.6 | 2778.5 | 3145.8 | 962 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 466 | 23.2 | 29.4 | 38.8 | 9,313 | 85.3% |
| csharp-dotnet | C# | F1 | 3021 | 10.8 | 18.5 | 22.7 | 60,421 | 0.0% |
| fraiseql-tv | Python | F1 | 42 | 876.9 | 1488.8 | 1672.3 | 846 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 42 | 870.1 | 1506.0 | 1688.5 | 839 | 0.0% |
| fraiseql-v | Python | F1 | 24 | 1613.2 | 2468.4 | 2945.4 | 478 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 4571 | 8.3 | 14.3 | 17.7 | 91,416 | 0.0% |
| async-graphql | Rust | F2 | 3667 | 10.2 | 18.1 | 23.2 | 73,333 | 0.0% |
| juniper | Rust | F2 | 3208 | 12.0 | 19.6 | 23.2 | 64,159 | 0.0% |
| go-gqlgen | Go | F2 | 4408 | 8.5 | 15.1 | 20.4 | 88,160 | 0.0% |
| gin-rest | Go | F2 | 4284 | 8.6 | 16.3 | 23.4 | 85,687 | 0.0% |
| go-graphql-go | Go | F2 | 1523 | 24.7 | 39.8 | 47.7 | 30,452 | 0.0% |
| graphql-go | Go | F2 | 1103 | 35.2 | 48.9 | 55.2 | 22,059 | 0.0% |
| apollo-server | Node.js | F2 | 69 | 17.3 | 23.4 | 137.0 | 1,388 | 97.8% |
| apollo-orm | Node.js | F2 | 42 | 27.5 | 38.0 | 69.6 | 842 | 98.7% |
| express-rest | Node.js | F2 | 449 | 9.2 | 16.4 | 20.0 | 8,976 | 77.6% |
| express-orm | Node.js | F2 | 13 | 97.3 | 116.1 | 122.8 | 263 | 99.5% |
| express-graphql | Node.js | F2 | 42 | 16.7 | 21.4 | 29.0 | 836 | 98.8% |
| graphql-yoga | Node.js | F2 | 407 | 8.8 | 14.5 | 18.9 | 8,135 | 88.2% |
| mercurius | Node.js | F2 | 1033 | 8.6 | 13.4 | 17.9 | 20,665 | 70.7% |
| strawberry | Python | F2 | 46 | 27.9 | 79.9 | 102.5 | 912 | 98.6% |
| graphene | Python | F2 | 198 | 17.5 | 56.6 | 76.6 | 3,956 | 93.7% |
| fastapi-rest | Python | F2 | 3909 | 9.6 | 17.1 | 21.8 | 78,172 | 0.0% |
| flask-rest | Python | F2 | — | — | — | — | — | _known bug — skipped_ |
| ariadne | Python | F2 | 39 | 14.4 | 54.3 | 85.2 | 774 | 98.8% |
| asgi-graphql | Python | F2 | 144 | 17.0 | 77.5 | 160.0 | 2,873 | 95.2% |
| spring-boot | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | — | — | — | — | — | _known bug — skipped_ |
| php-laravel | PHP | F2 | 60 | 611.6 | 813.4 | 2272.9 | 1,202 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| csharp-dotnet | C# | F2 | 3549 | 10.7 | 18.4 | 22.7 | 70,972 | 0.0% |
| fraiseql-tv | Python | F2 | 18 | 2126.3 | 3458.0 | 4596.5 | 350 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 18 | 2044.0 | 4153.5 | 4651.8 | 353 | 0.0% |
| fraiseql-v | Python | F2 | 9 | 4325.6 | 7415.2 | 8568.0 | 185 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 2188 | 17.0 | 33.1 | 41.3 | 43,761 | 0.0% |
| juniper | Rust | Q3 | 1533 | 25.9 | 28.7 | 30.2 | 30,657 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| quarkus-graphql | Java | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 854 | 45.5 | 66.9 | 79.0 | 17,070 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 855 | 45.4 | 66.9 | 77.4 | 17,091 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 160 | 237.0 | 352.4 | 405.4 | 3,202 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 160 | 236.7 | 364.0 | 428.8 | 3,205 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| spring-boot-orm-naive | Java | 4641 | 8.3 | 15.1 | 0.0% |
| gin-rest | Go | 4524 | 8.5 | 15.9 | 0.0% |
| fastapi-rest | Python | 4513 | 8.5 | 15.1 | 0.0% |
| actix-web-rest | Rust | 4499 | 8.6 | 15.3 | 0.0% |
| spring-boot-orm | Java | 3634 | 10.2 | 24.7 | 0.0% |
| ruby-rails | Ruby | 1490 | 24.9 | 64.9 | 0.0% |
| express-rest | Node.js | 1366 | 13.3 | 20.2 | 56.1% |
| express-orm | Node.js | 1082 | 16.9 | 35.5 | 58.0% |
| php-laravel | PHP | 76 | 577.8 | 722.6 | 0.0% |
| spring-boot | Java | 0 | 0.0 | 0.0 | 100.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| async-graphql | Rust | 4629 | 8.2 | 18.0 | 0.0% |
| go-gqlgen | Go | 4400 | 8.8 | 15.6 | 0.0% |
| graphql-go | Go | 4264 | 9.1 | 16.0 | 0.0% |
| graphql-yoga | Node.js | 4234 | 8.8 | 15.3 | 0.0% |
| juniper | Rust | 4199 | 9.2 | 16.3 | 0.0% |
| mercurius | Node.js | 4001 | 9.8 | 15.9 | 0.0% |
| csharp-dotnet | C# | 3884 | 9.7 | 21.2 | 0.0% |
| go-graphql-go | Go | 3821 | 9.7 | 23.2 | 0.0% |
| micronaut-graphql | Java | 3224 | 9.0 | 31.9 | 0.0% |
| quarkus-graphql | Java | 2164 | 17.5 | 39.3 | 0.0% |
| webonyx-graphql-php | PHP | 1023 | 24.0 | 44.7 | 29.9% |
| apollo-server | Node.js | 1018 | 13.5 | 22.3 | 67.7% |
| apollo-orm | Node.js | 980 | 15.2 | 37.7 | 63.9% |
| asgi-graphql | Python | 969 | 40.6 | 49.7 | 0.0% |
| ariadne | Python | 963 | 41.1 | 48.7 | 0.0% |
| express-graphql | Node.js | 954 | 13.3 | 20.0 | 70.0% |
| graphene | Python | 935 | 41.1 | 51.7 | 11.4% |
| strawberry | Python | 834 | 47.2 | 59.4 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 163 | 231.2 | 411.2 | 0.0% |
| fraiseql-tv | Python | 156 | 242.1 | 437.1 | 0.0% |
| fraiseql-v | Python | 137 | 276.1 | 451.7 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 1060 | 12.0 | 20.2 | 68.2% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| spring-boot-orm-naive | Java | rest | 4641 | 8.3 | 15.1 |
| async-graphql | Rust | graphql | 4629 | 8.2 | 18.0 |
| gin-rest | Go | rest | 4524 | 8.5 | 15.9 |
| fastapi-rest | Python | rest | 4513 | 8.5 | 15.1 |
| actix-web-rest | Rust | rest | 4499 | 8.6 | 15.3 |
| go-gqlgen | Go | graphql | 4400 | 8.8 | 15.6 |
| graphql-go | Go | graphql | 4264 | 9.1 | 16.0 |
| graphql-yoga | Node.js | graphql | 4234 | 8.8 | 15.3 |
| juniper | Rust | graphql | 4199 | 9.2 | 16.3 |
| mercurius | Node.js | graphql | 4001 | 9.8 | 15.9 |
| csharp-dotnet | C# | graphql | 3884 | 9.7 | 21.2 |
| go-graphql-go | Go | graphql | 3821 | 9.7 | 23.2 |
| spring-boot-orm | Java | rest | 3634 | 10.2 | 24.7 |
| micronaut-graphql | Java | graphql | 3224 | 9.0 | 31.9 |
| quarkus-graphql | Java | graphql | 2164 | 17.5 | 39.3 |
| ruby-rails | Ruby | rest | 1490 | 24.9 | 64.9 |
| express-rest | Node.js | rest | 1366 | 13.3 | 20.2 |
| express-orm | Node.js | rest | 1082 | 16.9 | 35.5 |
| postgraphile | Node.js | graphql-schema-first | 1060 | 12.0 | 20.2 |
| webonyx-graphql-php | PHP | graphql | 1023 | 24.0 | 44.7 |
| apollo-server | Node.js | graphql | 1018 | 13.5 | 22.3 |
| apollo-orm | Node.js | graphql | 980 | 15.2 | 37.7 |
| asgi-graphql | Python | graphql | 969 | 40.6 | 49.7 |
| ariadne | Python | graphql | 963 | 41.1 | 48.7 |
| express-graphql | Node.js | graphql | 954 | 13.3 | 20.0 |
| graphene | Python | graphql | 935 | 41.1 | 51.7 |
| strawberry | Python | graphql | 834 | 47.2 | 59.4 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 163 | 231.2 | 411.2 |
| fraiseql-tv | Python | graphql-precomputed | 156 | 242.1 | 437.1 |
| fraiseql-v | Python | graphql-precomputed | 137 | 276.1 | 451.7 |
| php-laravel | PHP | rest | 76 | 577.8 | 722.6 |
| spring-boot | Java | rest | 0 | 0.0 | 0.0 |