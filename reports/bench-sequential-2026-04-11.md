# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-11  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 20s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---
## Database Footprint

TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.
Views (v_*) add no storage — they are computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `tv_comment` | 697.2 MB | 291.9 MB | 1.58 GB |
| `tb_comment` | 294.7 MB | 81.3 MB | 376.1 MB |
| `tv_post` | 200.3 MB | 62.6 MB | 311.7 MB |
| `tb_mutation_log` | 256.4 MB | 21.7 MB | 278.2 MB |
| `tb_post` | 133.7 MB | 28.9 MB | 162.7 MB |
| `tv_user` | 8.0 MB | 9.3 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 6.1 MB | 5.3 MB | 11.4 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `tvd_comment` | 0.0 MB | 0.1 MB | 0.1 MB |
| `tvd_post` | 0.0 MB | 0.0 MB | 0.1 MB |
| `tvd_user` | 0.0 MB | 0.0 MB | 0.0 MB |
| `sessions` | 0.0 MB | 0.0 MB | 0.0 MB |
| `users` | 0.0 MB | 0.0 MB | 0.0 MB |
| `migrations` | 0.0 MB | 0.0 MB | 0.0 MB |
| `jobs` | 0.0 MB | 0.0 MB | 0.0 MB |
| `failed_jobs` | 0.0 MB | 0.0 MB | 0.0 MB |
| `cache_locks` | 0.0 MB | 0.0 MB | 0.0 MB |
| `password_reset_tokens` | 0.0 MB | 0.0 MB | 0.0 MB |
| `job_batches` | 0.0 MB | 0.0 MB | 0.0 MB |
| `cache` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.90 GB  
**TB tables (normalized baseline)**: 849.5 MB  
**Storage amplification**: 3.29× (TV adds 1.90 GB on top of the normalized 849.5 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 6801 | 3.5 | 19.1 | 33.9 | 136,028 | 0.0% |
| async-graphql | Rust | Q1 | 9003 | 4.0 | 8.8 | 12.2 | 180,066 | 0.0% |
| juniper | Rust | Q1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q1 | 2735 | 9.2 | 45.4 | 61.3 | 54,701 | 0.0% |
| gin-rest | Go | Q1 | 5071 | 5.3 | 22.7 | 36.2 | 101,424 | 0.0% |
| go-graphql-go | Go | Q1 | 1123 | 17.1 | 92.7 | 105.0 | 22,451 | 0.0% |
| graphql-go | Go | Q1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | Q1 | 4560 | 8.5 | 12.8 | 15.5 | 91,200 | 0.0% |
| apollo-orm | Node.js | Q1 | 3671 | 10.7 | 15.6 | 17.9 | 73,423 | 0.0% |
| express-rest | Node.js | Q1 | 8000 | 4.9 | 7.1 | 8.9 | 160,006 | 0.0% |
| express-orm | Node.js | Q1 | 3616 | 10.9 | 15.5 | 16.9 | 72,316 | 0.0% |
| express-graphql | Node.js | Q1 | 3940 | 9.8 | 14.4 | 16.1 | 78,790 | 0.0% |
| graphql-yoga | Node.js | Q1 | 8484 | 4.6 | 6.6 | 9.1 | 169,680 | 0.0% |
| mercurius | Node.js | Q1 | 8959 | 4.2 | 7.5 | 10.5 | 179,179 | 0.0% |
| postgraphile | Node.js | Q1 | 5116 | 7.6 | 11.0 | 13.7 | 102,315 | 0.0% |
| strawberry | Python | Q1 | 1827 | 21.4 | 31.0 | 37.2 | 36,532 | 0.0% |
| graphene | Python | Q1 | 2172 | 17.8 | 21.8 | 30.6 | 43,441 | 0.0% |
| fastapi-rest | Python | Q1 | 6978 | 5.6 | 7.2 | 9.4 | 139,568 | 0.0% |
| flask-rest | Python | Q1 | 256 | 177.6 | 282.5 | 304.9 | 5,128 | 0.0% |
| ariadne | Python | Q1 | 2247 | 17.5 | 22.4 | 26.0 | 44,932 | 0.0% |
| asgi-graphql | Python | Q1 | 2319 | 16.8 | 20.8 | 24.6 | 46,388 | 0.0% |
| spring-boot | Java | Q1 | 562 | 89.9 | 187.9 | 198.3 | 11,242 | 0.0% |
| spring-boot-orm | Java | Q1 | 817 | 16.0 | 102.8 | 180.7 | 16,336 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 1904 | 10.3 | 90.4 | 101.4 | 38,073 | 0.0% |
| micronaut-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q1 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q1 | 480 | 96.8 | 195.7 | 204.6 | 9,603 | 0.0% |
| ruby-rails | Ruby | Q1 | 737 | 43.2 | 123.4 | 192.0 | 14,747 | 0.0% |
| hanami | Ruby | Q1 | 493 | 21.1 | 664.0 | 779.2 | 9,860 | 0.0% |
| php-laravel | PHP | Q1 | 191 | 206.0 | 283.8 | 305.1 | 3,825 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 678 | 87.6 | 102.4 | 114.4 | 13,553 | 0.0% |
| csharp-dotnet | C# | Q1 | 6869 | 4.4 | 11.8 | 48.3 | 137,382 | 0.0% |
| fraiseql-tv | Rust | Q1 | 9214 | 3.8 | 9.2 | 12.8 | 184,289 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 8750 | 4.1 | 9.2 | 12.5 | 174,997 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8729 | 4.0 | 9.3 | 12.8 | 174,572 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9251 | 3.7 | 9.1 | 13.0 | 185,023 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 9452 | 2.5 | 13.5 | 24.5 | 189,033 | 0.0% |
| async-graphql | Rust | Q2 | 9275 | 3.8 | 8.8 | 12.3 | 185,508 | 0.0% |
| juniper | Rust | Q2 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q2 | 4907 | 5.7 | 23.0 | 34.3 | 98,135 | 0.0% |
| gin-rest | Go | Q2 | 9330 | 3.4 | 9.8 | 14.9 | 186,594 | 0.0% |
| go-graphql-go | Go | Q2 | 1396 | 14.9 | 82.2 | 96.5 | 27,918 | 0.0% |
| graphql-go | Go | Q2 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | Q2 | 6018 | 6.3 | 9.8 | 13.4 | 120,360 | 0.0% |
| apollo-orm | Node.js | Q2 | 4470 | 8.5 | 13.5 | 15.5 | 89,396 | 0.0% |
| express-rest | Node.js | Q2 | 6973 | 5.6 | 8.1 | 9.9 | 139,462 | 0.0% |
| express-orm | Node.js | Q2 | 3769 | 10.6 | 14.2 | 16.1 | 75,378 | 0.0% |
| express-graphql | Node.js | Q2 | 4168 | 9.2 | 13.7 | 17.0 | 83,352 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9433 | 4.1 | 6.1 | 9.5 | 188,660 | 0.0% |
| mercurius | Node.js | Q2 | 9418 | 3.9 | 7.7 | 10.4 | 188,362 | 0.0% |
| postgraphile | Node.js | Q2 | 5893 | 6.6 | 9.6 | 12.4 | 117,863 | 0.0% |
| strawberry | Python | Q2 | 1932 | 18.7 | 35.2 | 42.7 | 38,649 | 0.0% |
| graphene | Python | Q2 | 2355 | 15.3 | 28.0 | 39.8 | 47,097 | 0.0% |
| fastapi-rest | Python | Q2 | 5755 | 6.7 | 8.8 | 11.7 | 115,107 | 0.0% |
| flask-rest | Python | Q2 | 331 | 107.1 | 194.2 | 206.1 | 6,628 | 0.0% |
| ariadne | Python | Q2 | 2694 | 14.5 | 18.0 | 22.7 | 53,882 | 0.0% |
| asgi-graphql | Python | Q2 | 2740 | 15.6 | 19.0 | 24.8 | 54,803 | 0.0% |
| spring-boot | Java | Q2 | 2544 | 6.6 | 90.9 | 100.5 | 50,883 | 0.0% |
| spring-boot-orm | Java | Q2 | 4705 | 5.6 | 22.1 | 67.0 | 94,100 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 4224 | 6.9 | 25.2 | 38.8 | 84,476 | 0.0% |
| micronaut-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2 | 1601 | 15.8 | 86.1 | 99.2 | 32,021 | 0.0% |
| ruby-rails | Ruby | Q2 | 502 | 78.8 | 192.1 | 273.0 | 10,047 | 0.0% |
| hanami | Ruby | Q2 | 666 | 15.8 | 502.3 | 614.8 | 13,322 | 0.0% |
| php-laravel | PHP | Q2 | 174 | 217.7 | 304.9 | 362.4 | 3,479 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 759 | 82.4 | 101.0 | 109.7 | 15,178 | 0.0% |
| csharp-dotnet | C# | Q2 | 7222 | 4.6 | 9.8 | 27.9 | 144,435 | 0.0% |
| fraiseql-tv | Rust | Q2 | 8842 | 3.8 | 10.0 | 14.4 | 176,844 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 6031 | 5.8 | 14.1 | 19.2 | 120,624 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 8934 | 4.0 | 8.9 | 12.0 | 178,678 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 8455 | 3.8 | 10.5 | 16.1 | 169,093 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 8689 | 4.2 | 8.6 | 11.9 | 173,779 | 0.0% |
| async-graphql | Rust | Q2b | 8536 | 4.5 | 7.3 | 9.2 | 170,714 | 0.0% |
| juniper | Rust | Q2b | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q2b | 2338 | 11.4 | 49.5 | 63.8 | 46,764 | 0.0% |
| gin-rest | Go | Q2b | 1457 | 17.8 | 76.6 | 92.5 | 29,134 | 0.0% |
| go-graphql-go | Go | Q2b | 1005 | 19.7 | 94.7 | 106.3 | 20,093 | 0.0% |
| graphql-go | Go | Q2b | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | Q2b | 3970 | 9.5 | 15.3 | 19.5 | 79,403 | 0.0% |
| apollo-orm | Node.js | Q2b | 2289 | 17.1 | 23.5 | 26.9 | 45,784 | 0.0% |
| express-rest | Node.js | Q2b | 5744 | 6.9 | 9.8 | 13.4 | 114,876 | 0.0% |
| express-orm | Node.js | Q2b | 2423 | 16.2 | 23.2 | 26.5 | 48,454 | 0.0% |
| express-graphql | Node.js | Q2b | 3513 | 10.7 | 16.1 | 19.3 | 70,262 | 0.0% |
| graphql-yoga | Node.js | Q2b | 5967 | 5.9 | 12.7 | 19.7 | 119,346 | 0.0% |
| mercurius | Node.js | Q2b | 6202 | 5.9 | 11.3 | 19.2 | 124,048 | 0.0% |
| postgraphile | Node.js | Q2b | 4348 | 8.8 | 13.7 | 18.3 | 86,957 | 0.0% |
| strawberry | Python | Q2b | 1482 | 26.2 | 39.4 | 44.5 | 29,643 | 0.0% |
| graphene | Python | Q2b | 1809 | 21.4 | 27.4 | 35.0 | 36,172 | 0.0% |
| fastapi-rest | Python | Q2b | 5485 | 7.2 | 9.5 | 12.4 | 109,698 | 0.0% |
| flask-rest | Python | Q2b | 280 | 121.6 | 208.4 | 283.2 | 5,599 | 0.0% |
| ariadne | Python | Q2b | 1873 | 21.7 | 26.7 | 32.0 | 37,459 | 0.0% |
| asgi-graphql | Python | Q2b | 1885 | 20.7 | 27.1 | 30.0 | 37,693 | 0.0% |
| spring-boot | Java | Q2b | 1558 | 17.1 | 71.5 | 91.7 | 31,152 | 0.0% |
| spring-boot-orm | Java | Q2b | 7252 | 4.4 | 12.4 | 18.8 | 145,033 | 0.0% |
| spring-boot-orm-naive | Java | Q2b | 7329 | 4.4 | 12.4 | 18.6 | 146,583 | 0.0% |
| micronaut-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | Q2b | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | Q2b | 1100 | 20.6 | 88.7 | 105.3 | 21,997 | 0.0% |
| ruby-rails | Ruby | Q2b | 479 | 80.8 | 192.9 | 289.5 | 9,582 | 0.0% |
| hanami | Ruby | Q2b | 432 | 25.4 | 770.2 | 900.8 | 8,644 | 0.0% |
| php-laravel | PHP | Q2b | 165 | 230.0 | 301.7 | 357.0 | 3,299 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 644 | 90.0 | 186.9 | 194.7 | 12,870 | 0.0% |
| csharp-dotnet | C# | Q2b | 7209 | 4.6 | 10.2 | 29.7 | 144,178 | 0.0% |
| fraiseql-tv | Rust | Q2b | 9371 | 3.8 | 8.5 | 11.4 | 187,421 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 2801 | 10.6 | 38.4 | 50.7 | 56,020 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 6181 | 4.7 | 24.6 | 32.0 | 123,627 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9577 | 3.7 | 8.5 | 11.4 | 191,538 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1947 | 20.9 | 23.0 | 24.1 | 38,940 | 0.0% |
| async-graphql | Rust | M1 | 1462 | 20.6 | 66.3 | 123.0 | 29,234 | 0.0% |
| juniper | Rust | M1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | M1 | 1757 | 14.4 | 72.8 | 113.7 | 35,135 | 0.0% |
| gin-rest | Go | M1 | 1705 | 14.6 | 77.5 | 119.0 | 34,108 | 0.0% |
| go-graphql-go | Go | M1 | 4163 | 5.2 | 38.9 | 58.7 | 83,269 | 0.0% |
| graphql-go | Go | M1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | M1 | 2207 | 12.2 | 55.3 | 84.2 | 44,132 | 0.0% |
| express-graphql | Node.js | M1 | 1998 | 13.5 | 60.1 | 94.6 | 39,953 | 0.0% |
| graphql-yoga | Node.js | M1 | 1902 | 13.5 | 66.7 | 105.1 | 38,037 | 0.0% |
| mercurius | Node.js | M1 | 2139 | 11.7 | 60.5 | 94.7 | 42,779 | 0.0% |
| strawberry | Python | M1 | 317 | 50.5 | 358.8 | 1700.8 | 6,341 | 0.0% |
| graphene | Python | M1 | 822 | 29.5 | 155.7 | 270.0 | 16,435 | 0.0% |
| fastapi-rest | Python | M1 | 2148 | 11.6 | 60.3 | 93.9 | 42,966 | 0.0% |
| spring-boot | Java | M1 | 955 | 17.6 | 168.6 | 376.6 | 19,105 | 0.0% |
| spring-boot-orm | Java | M1 | 1321 | 15.7 | 103.1 | 203.5 | 26,414 | 0.0% |
| micronaut-graphql | Java | M1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | M1 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | M1 | 1826 | 17.9 | 50.7 | 75.4 | 36,510 | 0.0% |
| ruby-rails | Ruby | M1 | 800 | 29.6 | 119.1 | 197.6 | 16,004 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 659 | 44.6 | 181.5 | 197.8 | 13,189 | 0.0% |
| csharp-dotnet | C# | M1 | 2235 | 10.6 | 60.0 | 94.8 | 44,698 | 0.0% |
| fraiseql-tv | Rust | M1 | 6996 | 5.0 | 11.2 | 16.3 | 139,922 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 6672 | 5.1 | 12.4 | 20.9 | 133,432 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 2395 | 7.3 | 55.0 | 109.7 | 47,900 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 4828 | 5.5 | 23.8 | 51.4 | 96,553 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 1260 | 24.8 | 77.8 | 139.9 | 25,205 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 11442 | 2.1 | 11.0 | 20.7 | 228,835 | 0.0% |
| async-graphql | Rust | F1 | 8888 | 3.9 | 9.3 | 13.6 | 177,756 | 0.0% |
| juniper | Rust | F1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | F1 | 3654 | 8.3 | 28.7 | 40.9 | 73,072 | 0.0% |
| gin-rest | Go | F1 | 8402 | 3.8 | 11.1 | 16.7 | 168,041 | 0.0% |
| go-graphql-go | Go | F1 | 4915 | 4.1 | 50.5 | 55.4 | 98,302 | 0.0% |
| graphql-go | Go | F1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | F1 | 6021 | 6.4 | 9.6 | 11.9 | 120,423 | 0.0% |
| apollo-orm | Node.js | F1 | 4284 | 8.9 | 14.3 | 16.9 | 85,675 | 0.0% |
| express-rest | Node.js | F1 | 6606 | 5.9 | 8.8 | 11.9 | 132,127 | 0.0% |
| express-orm | Node.js | F1 | 3663 | 10.8 | 15.4 | 16.6 | 73,268 | 0.0% |
| express-graphql | Node.js | F1 | 4232 | 9.1 | 13.5 | 16.7 | 84,644 | 0.0% |
| graphql-yoga | Node.js | F1 | 9808 | 3.9 | 6.1 | 9.0 | 196,150 | 0.0% |
| mercurius | Node.js | F1 | 9262 | 4.0 | 7.7 | 10.3 | 185,247 | 0.0% |
| strawberry | Python | F1 | 1816 | 23.4 | 32.6 | 45.1 | 36,322 | 0.0% |
| graphene | Python | F1 | 2377 | 16.3 | 19.4 | 29.2 | 47,538 | 0.0% |
| fastapi-rest | Python | F1 | 5857 | 6.8 | 7.9 | 9.2 | 117,142 | 0.0% |
| flask-rest | Python | F1 | 332 | 107.5 | 193.2 | 204.1 | 6,644 | 0.0% |
| ariadne | Python | F1 | 2446 | 15.9 | 21.6 | 24.8 | 48,930 | 0.0% |
| asgi-graphql | Python | F1 | 2466 | 16.3 | 21.2 | 25.6 | 49,326 | 0.0% |
| spring-boot | Java | F1 | 4053 | 7.2 | 26.5 | 39.4 | 81,052 | 0.0% |
| spring-boot-orm | Java | F1 | 5843 | 5.1 | 17.1 | 27.9 | 116,863 | 0.0% |
| spring-boot-orm-naive | Java | F1 | 4544 | 6.3 | 23.3 | 37.2 | 90,871 | 0.0% |
| ruby-rails | Ruby | F1 | 483 | 82.9 | 188.2 | 277.1 | 9,652 | 0.0% |
| php-laravel | PHP | F1 | 169 | 225.9 | 302.6 | 348.7 | 3,377 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 733 | 84.4 | 101.7 | 110.0 | 14,658 | 0.0% |
| csharp-dotnet | C# | F1 | 6546 | 4.8 | 12.1 | 39.4 | 130,910 | 0.0% |
| fraiseql-tv | Rust | F1 | 9329 | 3.7 | 9.2 | 13.0 | 186,588 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4061 | 8.5 | 21.5 | 30.4 | 81,226 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 7186 | 4.5 | 13.9 | 20.9 | 143,717 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 8164 | 4.0 | 11.1 | 18.5 | 163,276 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 8452 | 4.4 | 8.4 | 11.3 | 169,041 | 0.0% |
| async-graphql | Rust | F2 | 8493 | 4.5 | 7.3 | 9.0 | 169,856 | 0.0% |
| juniper | Rust | F2 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | F2 | 2338 | 11.4 | 50.1 | 65.4 | 46,753 | 0.0% |
| gin-rest | Go | F2 | 1268 | 20.0 | 78.9 | 93.8 | 25,359 | 0.0% |
| go-graphql-go | Go | F2 | 2850 | 5.1 | 65.9 | 84.4 | 57,009 | 0.0% |
| graphql-go | Go | F2 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | F2 | 4052 | 9.4 | 14.6 | 17.4 | 81,047 | 0.0% |
| apollo-orm | Node.js | F2 | 2207 | 17.7 | 24.4 | 28.1 | 44,145 | 0.0% |
| express-rest | Node.js | F2 | 5760 | 6.9 | 9.7 | 12.5 | 115,190 | 0.0% |
| express-orm | Node.js | F2 | 2341 | 16.8 | 24.0 | 27.9 | 46,821 | 0.0% |
| express-graphql | Node.js | F2 | 3446 | 11.0 | 16.4 | 19.8 | 68,926 | 0.0% |
| graphql-yoga | Node.js | F2 | 6568 | 5.8 | 8.9 | 12.6 | 131,356 | 0.0% |
| mercurius | Node.js | F2 | 6506 | 5.9 | 10.3 | 14.1 | 130,116 | 0.0% |
| strawberry | Python | F2 | 1232 | 28.6 | 52.1 | 81.3 | 24,640 | 0.0% |
| graphene | Python | F2 | 1565 | 23.3 | 42.8 | 52.7 | 31,307 | 0.0% |
| fastapi-rest | Python | F2 | 5466 | 7.1 | 9.0 | 11.8 | 109,323 | 0.0% |
| flask-rest | Python | F2 | 290 | 118.7 | 201.9 | 270.5 | 5,790 | 0.0% |
| ariadne | Python | F2 | 1748 | 22.4 | 29.7 | 32.2 | 34,950 | 0.0% |
| asgi-graphql | Python | F2 | 1661 | 23.8 | 33.3 | 52.9 | 33,227 | 0.0% |
| spring-boot | Java | F2 | 2096 | 12.4 | 55.2 | 71.7 | 41,925 | 0.0% |
| spring-boot-orm | Java | F2 | 7258 | 4.4 | 12.4 | 18.8 | 145,162 | 0.0% |
| spring-boot-orm-naive | Java | F2 | 7527 | 4.2 | 12.2 | 18.4 | 150,540 | 0.0% |
| ruby-rails | Ruby | F2 | 458 | 85.7 | 191.7 | 266.6 | 9,162 | 0.0% |
| php-laravel | PHP | F2 | 155 | 271.3 | 314.3 | 371.3 | 3,106 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 671 | 90.7 | 103.6 | 194.1 | 13,422 | 0.0% |
| csharp-dotnet | C# | F2 | 6917 | 4.9 | 10.7 | 32.9 | 138,333 | 0.0% |
| fraiseql-tv | Rust | F2 | 9276 | 3.8 | 8.6 | 11.7 | 185,522 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 1700 | 18.2 | 55.2 | 67.0 | 33,998 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 4883 | 5.0 | 34.4 | 43.5 | 97,657 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 9298 | 3.8 | 8.7 | 11.7 | 185,953 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 3848 | 9.0 | 22.1 | 30.8 | 76,961 | 0.0% |
| async-graphql | Rust | T1 | 7909 | 4.9 | 7.2 | 8.7 | 158,188 | 0.0% |
| juniper | Rust | T1 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | T1 | 5933 | 5.5 | 14.5 | 21.5 | 118,661 | 0.0% |
| gin-rest | Go | T1 | 1567 | 20.3 | 64.6 | 91.0 | 31,336 | 0.0% |
| go-graphql-go | Go | T1 | 472 | 84.5 | 88.2 | 91.9 | 9,433 | 0.0% |
| graphql-go | Go | T1 | — | — | — | — | — | _service did not become healthy_ |
| apollo-server | Node.js | T1 | 2940 | 12.6 | 19.1 | 26.4 | 58,799 | 0.0% |
| apollo-orm | Node.js | T1 | 2063 | 18.3 | 25.1 | 28.8 | 41,260 | 0.0% |
| express-rest | Node.js | T1 | 3102 | 12.4 | 17.7 | 24.6 | 62,044 | 0.0% |
| express-orm | Node.js | T1 | 3426 | 11.1 | 15.0 | 17.8 | 68,514 | 0.0% |
| express-graphql | Node.js | T1 | 2373 | 16.2 | 21.7 | 25.0 | 47,468 | 0.0% |
| graphql-yoga | Node.js | T1 | 4070 | 9.0 | 15.4 | 21.1 | 81,399 | 0.0% |
| mercurius | Node.js | T1 | 4529 | 8.3 | 12.3 | 18.0 | 90,576 | 0.0% |
| postgraphile | Node.js | T1 | 3423 | 11.2 | 17.3 | 19.2 | 68,467 | 0.0% |
| strawberry | Python | T1 | 1005 | 40.4 | 58.5 | 71.2 | 20,102 | 0.0% |
| graphene | Python | T1 | 1504 | 25.4 | 38.3 | 42.9 | 30,090 | 0.0% |
| fastapi-rest | Python | T1 | 3583 | 10.6 | 17.1 | 20.9 | 71,652 | 0.0% |
| flask-rest | Python | T1 | 129 | 304.5 | 409.6 | 491.7 | 2,577 | 0.0% |
| ariadne | Python | T1 | 1240 | 33.6 | 44.1 | 53.6 | 24,810 | 0.0% |
| asgi-graphql | Python | T1 | 1254 | 31.4 | 39.7 | 44.8 | 25,072 | 0.0% |
| spring-boot | Java | T1 | 3250 | 10.0 | 28.8 | 43.9 | 64,996 | 0.0% |
| spring-boot-orm | Java | T1 | 1496 | 22.0 | 61.4 | 84.3 | 29,921 | 0.0% |
| spring-boot-orm-naive | Java | T1 | 1374 | 25.8 | 64.5 | 92.7 | 27,490 | 0.0% |
| micronaut-graphql | Java | T1 | — | — | — | — | — | _service did not become healthy_ |
| quarkus-graphql | Java | T1 | — | — | — | — | — | _service did not become healthy_ |
| play-graphql | Scala | T1 | 953 | 22.5 | 95.5 | 109.1 | 19,063 | 0.0% |
| ruby-rails | Ruby | T1 | 250 | 163.5 | 316.1 | 401.0 | 4,994 | 0.0% |
| hanami | Ruby | T1 | 384 | 29.5 | 857.5 | 1002.6 | 7,682 | 0.0% |
| php-laravel | PHP | T1 | 62 | 665.9 | 779.8 | 814.7 | 1,240 | 0.0% |
| webonyx-graphql-php | PHP | T1 | 673 | 86.9 | 105.9 | 194.5 | 13,458 | 0.0% |
| csharp-dotnet | C# | T1 | 4733 | 6.8 | 17.0 | 51.1 | 94,656 | 0.0% |
| fraiseql-tv | Rust | T1 | 7487 | 5.1 | 8.9 | 11.6 | 149,745 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 797 | 55.8 | 90.7 | 99.3 | 15,938 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 755 | 66.4 | 92.4 | 100.8 | 15,092 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 7541 | 5.1 | 8.7 | 11.3 | 150,828 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 2720 | 13.6 | 26.4 | 33.1 | 54,407 | 0.0% |
| juniper | Rust | Q3 | — | — | — | — | — | _service did not become healthy_ |
| go-gqlgen | Go | Q3 | 985 | 25.0 | 91.0 | 104.0 | 19,703 | 0.0% |
| quarkus-graphql | Java | Q3 | — | — | — | — | — | _service did not become healthy_ |
| fraiseql-tv | Rust | Q3 | 6610 | 5.5 | 11.1 | 14.5 | 132,198 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 700 | 77.4 | 103.2 | 111.7 | 14,001 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 2294 | 6.4 | 72.7 | 76.6 | 45,870 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7153 | 5.2 | 9.8 | 12.7 | 143,063 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | MC1 | 697 | 49.3 | 123.7 | 181.0 | 13,945 | 0.0% |
| graphql-yoga | Node.js | MC1 | 2213 | 13.5 | 50.6 | 78.8 | 44,256 | 0.0% |
| mercurius | Node.js | MC1 | 2264 | 13.0 | 50.5 | 77.2 | 45,276 | 0.0% |
| fraiseql-tv | Rust | MC1 | 1268 | 24.6 | 77.9 | 143.8 | 25,366 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 7643 | 4.7 | 9.9 | 14.0 | 152,852 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1241 | 10.1 | 136.4 | 169.9 | 24,816 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 5739 | 5.8 | 15.4 | 24.4 | 114,774 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 5290 | 5.8 | 19.2 | 30.1 | 105,808 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 5160 | 5.8 | 20.5 | 32.1 | 103,193 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7705 | 4.3 | 11.8 | 17.9 | 154,093 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 4528 | 6.7 | 23.0 | 34.3 | 90,566 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 5956 | 5.2 | 17.1 | 27.1 | 119,120 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 5507 | 5.4 | 19.1 | 31.0 | 110,144 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 9244 | 3.7 | 9.5 | 13.2 | 184,880 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 4302 | 7.1 | 24.1 | 36.2 | 86,039 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 5344 | 5.7 | 17.5 | 27.8 | 106,882 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9548 | 3.7 | 8.7 | 12.0 | 190,953 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 8507 | 4.1 | 9.4 | 12.6 | 170,136 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8778 | 4.1 | 9.1 | 12.2 | 175,556 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9035 | 3.8 | 9.4 | 13.2 | 180,703 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 9304 | 3.8 | 9.0 | 12.5 | 186,080 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8628 | 4.1 | 9.3 | 12.5 | 172,559 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 9188 | 3.9 | 8.4 | 11.1 | 183,763 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9516 | 3.7 | 8.7 | 12.1 | 190,317 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 8900 | 3.9 | 9.4 | 13.1 | 178,008 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 1927 | 16.7 | 48.0 | 60.5 | 38,537 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 5846 | 4.7 | 28.6 | 35.5 | 116,917 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9013 | 3.9 | 9.2 | 12.8 | 180,264 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 8763 | 4.2 | 8.2 | 10.7 | 175,268 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 3661 | 8.7 | 23.9 | 43.3 | 73,228 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 8456 | 4.3 | 8.5 | 11.2 | 169,114 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 3361 | 9.7 | 25.5 | 47.1 | 67,221 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| express-rest | Node.js | 8000 | 4.9 | 8.9 | 0.0% |
| fastapi-rest | Python | 6978 | 5.6 | 9.4 | 0.0% |
| actix-web-rest | Rust | 6801 | 3.5 | 33.9 | 0.0% |
| gin-rest | Go | 5071 | 5.3 | 36.2 | 0.0% |
| express-orm | Node.js | 3616 | 10.9 | 16.9 | 0.0% |
| spring-boot-orm-naive | Java | 1904 | 10.3 | 101.4 | 0.0% |
| spring-boot-orm | Java | 817 | 16.0 | 180.7 | 0.0% |
| ruby-rails | Ruby | 737 | 43.2 | 192.0 | 0.0% |
| spring-boot | Java | 562 | 89.9 | 198.3 | 0.0% |
| flask-rest | Python | 256 | 177.6 | 304.9 | 0.0% |
| php-laravel | PHP | 191 | 206.0 | 305.1 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| async-graphql | Rust | 9003 | 4.0 | 12.2 | 0.0% |
| mercurius | Node.js | 8959 | 4.2 | 10.5 | 0.0% |
| graphql-yoga | Node.js | 8484 | 4.6 | 9.1 | 0.0% |
| csharp-dotnet | C# | 6869 | 4.4 | 48.3 | 0.0% |
| apollo-server | Node.js | 4560 | 8.5 | 15.5 | 0.0% |
| express-graphql | Node.js | 3940 | 9.8 | 16.1 | 0.0% |
| apollo-orm | Node.js | 3671 | 10.7 | 17.9 | 0.0% |
| go-gqlgen | Go | 2735 | 9.2 | 61.3 | 0.0% |
| asgi-graphql | Python | 2319 | 16.8 | 24.6 | 0.0% |
| ariadne | Python | 2247 | 17.5 | 26.0 | 0.0% |
| graphene | Python | 2172 | 17.8 | 30.6 | 0.0% |
| strawberry | Python | 1827 | 21.4 | 37.2 | 0.0% |
| go-graphql-go | Go | 1123 | 17.1 | 105.0 | 0.0% |
| webonyx-graphql-php | PHP | 678 | 87.6 | 114.4 | 0.0% |
| hanami | Ruby | 493 | 21.1 | 779.2 | 0.0% |
| play-graphql | Scala | 480 | 96.8 | 204.6 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 9251 | 3.7 | 13.0 | 0.0% |
| fraiseql-tv | Rust | 9214 | 3.8 | 12.8 | 0.0% |
| fraiseql-v-nocache | Rust | 8750 | 4.1 | 12.5 | 0.0% |
| fraiseql-v-cache | Rust | 8729 | 4.0 | 12.8 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 5116 | 7.6 | 13.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 9251 | 3.7 | 13.0 |
| fraiseql-tv | Rust | graphql-precomputed | 9214 | 3.8 | 12.8 |
| async-graphql | Rust | graphql | 9003 | 4.0 | 12.2 |
| mercurius | Node.js | graphql | 8959 | 4.2 | 10.5 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 8750 | 4.1 | 12.5 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8729 | 4.0 | 12.8 |
| graphql-yoga | Node.js | graphql | 8484 | 4.6 | 9.1 |
| express-rest | Node.js | rest | 8000 | 4.9 | 8.9 |
| fastapi-rest | Python | rest | 6978 | 5.6 | 9.4 |
| csharp-dotnet | C# | graphql | 6869 | 4.4 | 48.3 |
| actix-web-rest | Rust | rest | 6801 | 3.5 | 33.9 |
| postgraphile | Node.js | graphql-schema-first | 5116 | 7.6 | 13.7 |
| gin-rest | Go | rest | 5071 | 5.3 | 36.2 |
| apollo-server | Node.js | graphql | 4560 | 8.5 | 15.5 |
| express-graphql | Node.js | graphql | 3940 | 9.8 | 16.1 |
| apollo-orm | Node.js | graphql | 3671 | 10.7 | 17.9 |
| express-orm | Node.js | rest | 3616 | 10.9 | 16.9 |
| go-gqlgen | Go | graphql | 2735 | 9.2 | 61.3 |
| asgi-graphql | Python | graphql | 2319 | 16.8 | 24.6 |
| ariadne | Python | graphql | 2247 | 17.5 | 26.0 |
| graphene | Python | graphql | 2172 | 17.8 | 30.6 |
| spring-boot-orm-naive | Java | rest | 1904 | 10.3 | 101.4 |
| strawberry | Python | graphql | 1827 | 21.4 | 37.2 |
| go-graphql-go | Go | graphql | 1123 | 17.1 | 105.0 |
| spring-boot-orm | Java | rest | 817 | 16.0 | 180.7 |
| ruby-rails | Ruby | rest | 737 | 43.2 | 192.0 |
| webonyx-graphql-php | PHP | graphql | 678 | 87.6 | 114.4 |
| spring-boot | Java | rest | 562 | 89.9 | 198.3 |
| hanami | Ruby | graphql | 493 | 21.1 | 779.2 |
| play-graphql | Scala | graphql | 480 | 96.8 | 204.6 |
| flask-rest | Python | rest | 256 | 177.6 | 304.9 |
| php-laravel | PHP | rest | 191 | 206.0 | 305.1 |

---

## MC1 — Cascade Advantage

**Requests per cycle** (what a client must issue to reach fully consistent state after a mutation):

| Framework type | Requests/cycle | What is sent |
|----------------|---------------|--------------|
| FraiseQL | **1** | M1 mutation — `cascade` field in response contains all affected entities |
| Classical GraphQL | **2** | M1 mutation (1) + Q1 list re-fetch (2) |

RPS above = **cycles/second** (mutation-to-consistent-state cycles, not raw requests).  
At equal cycles/second, FraiseQL issues 2× fewer HTTP round trips and returns ~0 stale entities.  
Classical frameworks must fire follow-up queries to invalidate stale cache entries.

> **Peak**: fraiseql-tv-cache 5739 cycles/s (1 req) vs mercurius 2264 cycles/s (2 req) — 2.5× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 6,996 M/s: **~426,762 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.