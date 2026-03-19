# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-03  
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
| actix-web-rest | Rust | Q1 | 4241 | 8.3 | 18.2 | 27.4 | 84,817 | 0.0% |
| async-graphql | Rust | Q1 | 3769 | 9.5 | 19.8 | 27.5 | 75,380 | 0.0% |
| juniper | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q1 | 3555 | 9.5 | 23.7 | 33.9 | 71,107 | 0.0% |
| gin-rest | Go | Q1 | 3566 | 9.3 | 24.5 | 34.8 | 71,314 | 0.0% |
| go-graphql-go | Go | Q1 | 4146 | 8.8 | 17.0 | 23.8 | 82,910 | 0.0% |
| graphql-go | Go | Q1 | 4224 | 8.8 | 16.1 | 21.2 | 84,478 | 0.0% |
| apollo-server | Node.js | Q1 | 1059 | 11.5 | 14.8 | 21.2 | 21,171 | 69.0% (connection_error: 100%) |
| apollo-orm | Node.js | Q1 | 847 | 14.8 | 16.7 | 20.8 | 16,944 | 73.3% (connection_error: 100%) |
| express-rest | Node.js | Q1 | 4569 | 8.1 | 13.9 | 15.3 | 91,381 | 0.0% |
| express-orm | Node.js | Q1 | 910 | 16.0 | 17.3 | 19.6 | 18,190 | 71.1% (connection_error: 100%) |
| express-graphql | Node.js | Q1 | 721 | 13.2 | 15.0 | 16.7 | 14,413 | 78.6% (connection_error: 100%) |
| graphql-yoga | Node.js | Q1 | 4116 | 9.0 | 14.4 | 15.4 | 82,329 | 0.8% (connection_error: 100%) |
| mercurius | Node.js | Q1 | 4258 | 9.1 | 13.3 | 15.4 | 85,160 | 0.0% |
| postgraphile | Node.js | Q1 | 1123 | 12.2 | 15.6 | 20.1 | 22,458 | 66.3% (connection_error: 100%) |
| strawberry | Python | Q1 | 828 | 47.4 | 59.3 | 60.9 | 16,555 | 0.0% |
| graphene | Python | Q1 | 726 | 45.7 | 110.2 | 132.0 | 14,526 | 0.0% |
| fastapi-rest | Python | Q1 | 4583 | 8.2 | 14.3 | 17.8 | 91,653 | 0.0% |
| flask-rest | Python | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ariadne | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | Q1 | 4281 | 8.4 | 17.5 | 24.1 | 85,619 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 4491 | 8.0 | 16.7 | 23.9 | 89,815 | 0.0% |
| micronaut-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q1 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q1 | 1698 | 23.2 | 29.1 | 32.5 | 33,966 | 0.0% |
| hanami | Ruby | Q1 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q1 | 111 | 359.0 | 425.8 | 523.5 | 2,212 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q1 | 4070 | 9.3 | 15.9 | 20.0 | 81,404 | 0.0% |
| fraiseql-tv | Python | Q1 | 3679 | 10.2 | 18.2 | 23.6 | 73,585 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 3774 | 9.9 | 17.4 | 22.3 | 75,479 | 0.0% |
| fraiseql-v | Python | Q1 | 3096 | 11.9 | 22.3 | 28.2 | 61,913 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 4057 | 8.6 | 20.0 | 28.9 | 81,147 | 0.0% |
| async-graphql | Rust | Q2 | 3969 | 9.1 | 18.7 | 26.0 | 79,374 | 0.0% |
| juniper | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q2 | 3607 | 9.3 | 23.4 | 33.5 | 72,140 | 0.0% |
| gin-rest | Go | Q2 | 3309 | 9.6 | 27.7 | 38.7 | 66,171 | 0.0% |
| go-graphql-go | Go | Q2 | 4197 | 8.7 | 16.8 | 23.2 | 83,941 | 0.0% |
| graphql-go | Go | Q2 | 4266 | 8.5 | 16.9 | 23.8 | 85,322 | 0.0% |
| apollo-server | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| apollo-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| express-rest | Node.js | Q2 | 57 | 9.7 | 20.3 | 27.7 | 1,137 | 98.4% (connection_error: 100%) |
| express-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| express-graphql | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| graphql-yoga | Node.js | Q2 | 111 | 10.0 | 19.1 | 25.0 | 2,221 | 96.8% (connection_error: 100%) |
| mercurius | Node.js | Q2 | 1293 | 8.3 | 13.1 | 18.2 | 25,865 | 64.7% (connection_error: 100%) |
| postgraphile | Node.js | Q2 | 391 | 11.0 | 17.4 | 22.8 | 7,816 | 88.5% (connection_error: 100%) |
| strawberry | Python | Q2 | 242 | 41.2 | 43.2 | 54.6 | 4,847 | 91.6% (connection_error: 100%) |
| graphene | Python | Q2 | 269 | 38.9 | 72.0 | 86.2 | 5,373 | 88.4% (connection_error: 100%) |
| fastapi-rest | Python | Q2 | 4641 | 8.2 | 13.8 | 17.1 | 92,816 | 0.0% |
| flask-rest | Python | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ariadne | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q2 | 4459 | 8.4 | 15.2 | 19.7 | 89,183 | 0.0% |
| spring-boot-orm | Java | Q2 | 4116 | 8.6 | 18.9 | 27.1 | 82,326 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 4934 | 7.6 | 13.7 | 17.8 | 98,687 | 0.0% |
| micronaut-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2 | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2 | 1066 | 37.1 | 45.5 | 49.9 | 21,319 | 0.0% |
| hanami | Ruby | Q2 | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2 | 94 | 417.7 | 648.0 | 715.2 | 1,872 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q2 | 4191 | 9.1 | 15.2 | 18.8 | 83,817 | 0.0% |
| fraiseql-tv | Python | Q2 | 1790 | 20.1 | 39.2 | 51.7 | 35,797 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 1918 | 19.2 | 35.0 | 45.2 | 38,364 | 0.0% |
| fraiseql-v | Python | Q2 | 1776 | 21.6 | 31.1 | 36.5 | 35,512 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 4399 | 8.4 | 15.7 | 20.7 | 87,978 | 0.0% |
| async-graphql | Rust | Q2b | 3714 | 9.8 | 18.8 | 25.4 | 74,270 | 0.0% |
| juniper | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q2b | 4140 | 8.8 | 17.2 | 24.5 | 82,799 | 0.0% |
| gin-rest | Go | Q2b | 4037 | 9.1 | 17.6 | 23.3 | 80,741 | 0.0% |
| go-graphql-go | Go | Q2b | 285 | 139.5 | 150.6 | 156.3 | 5,696 | 0.0% |
| graphql-go | Go | Q2b | 1207 | 31.5 | 47.4 | 54.4 | 24,131 | 0.0% |
| apollo-server | Node.js | Q2b | 1456 | 13.5 | 18.1 | 22.5 | 29,121 | 53.4% (connection_error: 100%) |
| apollo-orm | Node.js | Q2b | 1183 | 18.7 | 23.4 | 32.5 | 23,667 | 55.8% (connection_error: 100%) |
| express-rest | Node.js | Q2b | 1905 | 8.2 | 12.9 | 17.9 | 38,094 | 51.1% (connection_error: 100%) |
| express-orm | Node.js | Q2b | 1136 | 19.7 | 23.8 | 29.4 | 22,723 | 56.5% (connection_error: 100%) |
| express-graphql | Node.js | Q2b | 1399 | 15.5 | 19.3 | 25.3 | 27,977 | 52.1% (connection_error: 100%) |
| graphql-yoga | Node.js | Q2b | 1819 | 8.6 | 12.3 | 17.2 | 36,378 | 52.3% (connection_error: 100%) |
| mercurius | Node.js | Q2b | 2488 | 8.5 | 12.7 | 16.5 | 49,769 | 37.5% (connection_error: 100%) |
| postgraphile | Node.js | Q2b | 900 | 12.9 | 16.4 | 21.4 | 18,010 | 73.2% (connection_error: 100%) |
| strawberry | Python | Q2b | 331 | 63.9 | 80.7 | 99.9 | 6,619 | 81.4% (connection_error: 100%) |
| graphene | Python | Q2b | 440 | 54.3 | 70.3 | 80.1 | 8,802 | 72.1% (connection_error: 100%) |
| fastapi-rest | Python | Q2b | 4699 | 8.1 | 13.6 | 16.7 | 93,981 | 0.0% |
| flask-rest | Python | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ariadne | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2b | — | — | — | — | — | _service did not become healthy_ |
| ruby-rails | Ruby | Q2b | 923 | 38.7 | 76.1 | 107.8 | 18,453 | 0.0% |
| hanami | Ruby | Q2b | — | — | — | — | — | _service did not become healthy_ |
| php-laravel | PHP | Q2b | 77 | 505.0 | 694.8 | 716.0 | 1,537 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | Q2b | 4213 | 9.1 | 15.0 | 18.3 | 84,258 | 0.0% |
| fraiseql-tv | Python | Q2b | 1061 | 34.5 | 63.4 | 80.0 | 21,224 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 1097 | 33.8 | 59.5 | 74.8 | 21,949 | 0.0% |
| fraiseql-v | Python | Q2b | 792 | 48.4 | 69.6 | 80.7 | 15,831 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1964 | 13.5 | 62.4 | 98.3 | 39,278 | 0.0% |
| async-graphql | Rust | M1 | 1875 | 18.0 | 42.5 | 60.0 | 37,508 | 0.0% |
| go-gqlgen | Go | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| gin-rest | Go | M1 | 2001 | 13.9 | 60.5 | 93.8 | 40,013 | 0.0% |
| spring-boot | Java | M1 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-tv | Python | M1 | 605 | 34.7 | 226.8 | 484.0 | 12,098 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1943 | 13.8 | 63.2 | 99.1 | 38,867 | 0.0% |
| fraiseql-v | Python | M1 | 2060 | 13.1 | 59.9 | 93.5 | 41,192 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 2097 | 12.4 | 59.3 | 93.0 | 41,948 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 3867 | 8.8 | 21.5 | 30.8 | 77,331 | 0.0% |
| async-graphql | Rust | F1 | 3800 | 9.2 | 20.7 | 29.6 | 75,991 | 0.0% |
| juniper | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | F1 | 4162 | 8.7 | 17.3 | 24.1 | 83,247 | 0.0% |
| gin-rest | Go | F1 | 3202 | 9.9 | 28.8 | 40.4 | 64,048 | 0.0% |
| go-graphql-go | Go | F1 | 4135 | 8.8 | 17.6 | 24.9 | 82,693 | 0.0% |
| graphql-go | Go | F1 | 3666 | 9.6 | 21.1 | 28.6 | 73,326 | 0.0% |
| apollo-server | Node.js | F1 | 41 | 10.2 | 19.9 | 25.7 | 823 | 98.8% (connection_error: 100%) |
| apollo-orm | Node.js | F1 | 139 | 9.9 | 18.6 | 24.3 | 2,777 | 96.0% (connection_error: 100%) |
| express-rest | Node.js | F1 | 4334 | 8.7 | 14.6 | 16.1 | 86,671 | 0.0% |
| express-orm | Node.js | F1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| express-graphql | Node.js | F1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| graphql-yoga | Node.js | F1 | 1833 | 10.3 | 14.8 | 17.4 | 36,664 | 48.5% (connection_error: 100%) |
| mercurius | Node.js | F1 | 2960 | 10.7 | 14.8 | 18.4 | 59,204 | 19.2% (connection_error: 100%) |
| strawberry | Python | F1 | 832 | 46.8 | 61.5 | 65.6 | 16,640 | 0.0% |
| graphene | Python | F1 | 837 | 41.0 | 52.6 | 60.2 | 16,747 | 39.8% (connection_error: 100%) |
| fastapi-rest | Python | F1 | 4697 | 8.1 | 13.5 | 16.4 | 93,938 | 0.0% |
| flask-rest | Python | F1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ariadne | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | F1 | 4404 | 8.5 | 15.3 | 19.8 | 88,089 | 0.0% |
| spring-boot-orm | Java | F1 | 4022 | 8.7 | 19.6 | 27.7 | 80,444 | 0.0% |
| ruby-rails | Ruby | F1 | 811 | 40.0 | 102.1 | 131.3 | 16,215 | 0.0% |
| php-laravel | PHP | F1 | 94 | 415.5 | 610.1 | 700.6 | 1,872 | 0.0% |
| webonyx-graphql-php | PHP | F1 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | F1 | 4120 | 9.2 | 15.7 | 19.8 | 82,403 | 0.0% |
| fraiseql-tv | Python | F1 | 1803 | 20.1 | 38.7 | 48.9 | 36,063 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 1887 | 19.4 | 36.2 | 46.9 | 37,739 | 0.0% |
| fraiseql-v | Python | F1 | 1802 | 21.3 | 30.5 | 35.4 | 36,044 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 4230 | 8.6 | 16.8 | 23.5 | 84,602 | 0.0% |
| async-graphql | Rust | F2 | 3539 | 10.1 | 20.6 | 28.2 | 70,778 | 0.0% |
| juniper | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | F2 | 4151 | 8.8 | 17.1 | 23.6 | 83,015 | 0.0% |
| gin-rest | Go | F2 | 3860 | 9.4 | 19.0 | 25.6 | 77,191 | 0.0% |
| go-graphql-go | Go | F2 | 282 | 140.1 | 154.8 | 161.9 | 5,635 | 0.0% |
| graphql-go | Go | F2 | 1218 | 31.1 | 47.5 | 54.5 | 24,352 | 0.0% |
| apollo-server | Node.js | F2 | 44 | 9.6 | 19.4 | 24.4 | 880 | 98.7% (connection_error: 100%) |
| apollo-orm | Node.js | F2 | 101 | 22.6 | 34.1 | 68.8 | 2,017 | 97.0% (connection_error: 100%) |
| express-rest | Node.js | F2 | 319 | 8.5 | 13.2 | 17.1 | 6,385 | 90.9% (connection_error: 100%) |
| express-orm | Node.js | F2 | 69 | 21.6 | 24.8 | 34.5 | 1,371 | 98.0% (connection_error: 100%) |
| express-graphql | Node.js | F2 | 147 | 16.8 | 20.8 | 29.1 | 2,933 | 95.6% (connection_error: 100%) |
| graphql-yoga | Node.js | F2 | 589 | 8.7 | 16.0 | 21.4 | 11,775 | 83.1% (connection_error: 100%) |
| mercurius | Node.js | F2 | 874 | 8.7 | 13.7 | 18.0 | 17,488 | 75.0% (connection_error: 100%) |
| strawberry | Python | F2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| graphene | Python | F2 | 170 | 16.4 | 55.7 | 68.8 | 3,390 | 94.5% (connection_error: 100%) |
| fastapi-rest | Python | F2 | 4547 | 8.3 | 14.2 | 17.7 | 90,934 | 0.0% |
| flask-rest | Python | F2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| ariadne | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| asgi-graphql | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| spring-boot | Java | F2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | 770 | 40.8 | 114.2 | 138.9 | 15,400 | 0.0% |
| php-laravel | PHP | F2 | 28 | 488.7 | 737.8 | 772.7 | 557 | 99.5% (connection_refused: 76%, connection_error: 24%, json_error: 0%) |
| webonyx-graphql-php | PHP | F2 | — | — | — | — | — | _service did not become healthy_ |
| csharp-dotnet | C# | F2 | 3768 | 10.1 | 17.2 | 21.4 | 75,359 | 0.0% |
| fraiseql-tv | Python | F2 | 1075 | 34.1 | 62.6 | 79.4 | 21,491 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 1067 | 34.3 | 63.4 | 80.3 | 21,338 | 0.0% |
| fraiseql-v | Python | F2 | 800 | 47.8 | 68.7 | 78.8 | 16,009 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 2054 | 17.7 | 37.0 | 46.4 | 41,081 | 0.0% |
| juniper | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| quarkus-graphql | Java | Q3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% (connection_error: 100%) |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 4838 | 7.9 | 13.4 | 16.6 | 96,770 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 4716 | 8.0 | 13.9 | 17.4 | 94,315 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 3632 | 10.2 | 18.7 | 25.4 | 72,635 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 3606 | 10.2 | 19.0 | 26.0 | 72,112 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fastapi-rest | Python | 4583 | 8.2 | 17.8 | 0.0% |
| express-rest | Node.js | 4569 | 8.1 | 15.3 | 0.0% |
| spring-boot-orm-naive | Java | 4491 | 8.0 | 23.9 | 0.0% |
| spring-boot-orm | Java | 4281 | 8.4 | 24.1 | 0.0% |
| actix-web-rest | Rust | 4241 | 8.3 | 27.4 | 0.0% |
| gin-rest | Go | 3566 | 9.3 | 34.8 | 0.0% |
| ruby-rails | Ruby | 1698 | 23.2 | 32.5 | 0.0% |
| express-orm | Node.js | 910 | 16.0 | 19.6 | 71.1% |
| php-laravel | PHP | 111 | 359.0 | 523.5 | 0.0% |
| flask-rest | Python | 0 | 0.0 | 0.0 | 100.0% |
| spring-boot | Java | 0 | 0.0 | 0.0 | 100.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| mercurius | Node.js | 4258 | 9.1 | 15.4 | 0.0% |
| graphql-go | Go | 4224 | 8.8 | 21.2 | 0.0% |
| go-graphql-go | Go | 4146 | 8.8 | 23.8 | 0.0% |
| graphql-yoga | Node.js | 4116 | 9.0 | 15.4 | 0.8% |
| csharp-dotnet | C# | 4070 | 9.3 | 20.0 | 0.0% |
| async-graphql | Rust | 3769 | 9.5 | 27.5 | 0.0% |
| go-gqlgen | Go | 3555 | 9.5 | 33.9 | 0.0% |
| apollo-server | Node.js | 1059 | 11.5 | 21.2 | 69.0% |
| apollo-orm | Node.js | 847 | 14.8 | 20.8 | 73.3% |
| strawberry | Python | 828 | 47.4 | 60.9 | 0.0% |
| graphene | Python | 726 | 45.7 | 132.0 | 0.0% |
| express-graphql | Node.js | 721 | 13.2 | 16.7 | 78.6% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 3774 | 9.9 | 22.3 | 0.0% |
| fraiseql-tv | Python | 3679 | 10.2 | 23.6 | 0.0% |
| fraiseql-v | Python | 3096 | 11.9 | 28.2 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 1123 | 12.2 | 20.1 | 66.3% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fastapi-rest | Python | rest | 4583 | 8.2 | 17.8 |
| express-rest | Node.js | rest | 4569 | 8.1 | 15.3 |
| spring-boot-orm-naive | Java | rest | 4491 | 8.0 | 23.9 |
| spring-boot-orm | Java | rest | 4281 | 8.4 | 24.1 |
| mercurius | Node.js | graphql | 4258 | 9.1 | 15.4 |
| actix-web-rest | Rust | rest | 4241 | 8.3 | 27.4 |
| graphql-go | Go | graphql | 4224 | 8.8 | 21.2 |
| go-graphql-go | Go | graphql | 4146 | 8.8 | 23.8 |
| graphql-yoga | Node.js | graphql | 4116 | 9.0 | 15.4 |
| csharp-dotnet | C# | graphql | 4070 | 9.3 | 20.0 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 3774 | 9.9 | 22.3 |
| async-graphql | Rust | graphql | 3769 | 9.5 | 27.5 |
| fraiseql-tv | Python | graphql-precomputed | 3679 | 10.2 | 23.6 |
| gin-rest | Go | rest | 3566 | 9.3 | 34.8 |
| go-gqlgen | Go | graphql | 3555 | 9.5 | 33.9 |
| fraiseql-v | Python | graphql-precomputed | 3096 | 11.9 | 28.2 |
| ruby-rails | Ruby | rest | 1698 | 23.2 | 32.5 |
| postgraphile | Node.js | graphql-schema-first | 1123 | 12.2 | 20.1 |
| apollo-server | Node.js | graphql | 1059 | 11.5 | 21.2 |
| express-orm | Node.js | rest | 910 | 16.0 | 19.6 |
| apollo-orm | Node.js | graphql | 847 | 14.8 | 20.8 |
| strawberry | Python | graphql | 828 | 47.4 | 60.9 |
| graphene | Python | graphql | 726 | 45.7 | 132.0 |
| express-graphql | Node.js | graphql | 721 | 13.2 | 16.7 |
| php-laravel | PHP | rest | 111 | 359.0 | 523.5 |
| flask-rest | Python | rest | 0 | 0.0 | 0.0 |
| spring-boot | Java | rest | 0 | 0.0 | 0.0 |