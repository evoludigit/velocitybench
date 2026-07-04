# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-14  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 30s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 5s between frameworks  

---
## Database Footprint

TV tables (pre-computed JSONB) inflate storage by embedding denormalized data at write time.
Views (v_*) add no storage — they are computed at query time.

| Table | Heap | Indexes | Total |
|-------|------|---------|-------|
| `tv_comment` | 696.3 MB | 322.1 MB | 1.62 GB |
| `tb_comment` | 294.8 MB | 82.3 MB | 377.2 MB |
| `tv_post` | 199.6 MB | 72.2 MB | 321.9 MB |
| `tb_post` | 133.6 MB | 20.0 MB | 153.7 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tv_user` | 8.0 MB | 5.8 MB | 13.8 MB |
| `tb_user` | 4.7 MB | 3.1 MB | 7.9 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.7 MB |
| `tvd_comment` | 0.1 MB | 0.1 MB | 0.2 MB |
| `tvd_post` | 0.0 MB | 0.0 MB | 0.1 MB |
| `tvd_user` | 0.0 MB | 0.0 MB | 0.0 MB |
| `tb_mutation_log` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 1.95 GB  
**TB tables (normalized baseline)**: 559.9 MB  
**Storage amplification**: 4.56× (TV adds 1.95 GB on top of the normalized 559.9 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 1866 | 20.8 | 24.8 | 28.7 | 55,969 | 0.0% |
| async-graphql | Rust | Q1 | 531 | 96.3 | 171.9 | 182.5 | 15,937 | 0.0% |
| juniper | Rust | Q1 | 502 | 93.1 | 185.0 | 198.1 | 15,056 | 0.0% |
| go-gqlgen | Go | Q1 | 644 | 84.8 | 114.9 | 190.6 | 19,327 | 0.0% |
| gin-rest | Go | Q1 | 761 | 20.4 | 110.4 | 188.6 | 22,836 | 0.0% |
| go-graphql-go | Go | Q1 | 579 | 88.5 | 116.4 | 189.0 | 17,379 | 0.0% |
| graphql-go | Go | Q1 | 590 | 88.0 | 118.1 | 190.7 | 17,686 | 0.0% |
| apollo-server | Node.js | Q1 | 681 | 69.4 | 106.8 | 122.8 | 20,420 | 0.0% |
| apollo-orm | Node.js | Q1 | 523 | 84.9 | 134.4 | 190.6 | 15,692 | 0.0% |
| express-rest | Node.js | Q1 | 525 | 86.5 | 175.4 | 194.4 | 15,756 | 0.0% |
| express-orm | Node.js | Q1 | 648 | 68.3 | 112.4 | 174.9 | 19,453 | 0.0% |
| express-graphql | Node.js | Q1 | 721 | 55.1 | 108.9 | 162.8 | 21,616 | 0.0% |
| graphql-yoga | Node.js | Q1 | 556 | 83.7 | 169.4 | 190.8 | 16,667 | 0.0% |
| mercurius | Node.js | Q1 | 581 | 82.4 | 170.3 | 190.4 | 17,435 | 0.0% |
| postgraphile | Node.js | Q1 | 4908 | 7.6 | 14.2 | 19.7 | 147,237 | 0.0% |
| strawberry | Python | Q1 | 1559 | 23.6 | 41.0 | 46.0 | 46,776 | 0.0% |
| graphene | Python | Q1 | 1596 | 24.5 | 39.8 | 48.2 | 47,872 | 0.0% |
| fastapi-rest | Python | Q1 | 497 | 89.9 | 171.9 | 188.5 | 14,924 | 0.0% |
| flask-rest | Python | Q1 | 220 | 192.6 | 285.9 | 299.8 | 6,597 | 0.0% |
| ariadne | Python | Q1 | 1704 | 20.7 | 36.0 | 42.5 | 51,133 | 0.0% |
| asgi-graphql | Python | Q1 | 1616 | 23.2 | 34.9 | 43.6 | 48,474 | 0.0% |
| spring-boot | Java | Q1 | 453 | 94.8 | 194.4 | 210.4 | 13,598 | 0.0% |
| spring-boot-orm | Java | Q1 | 918 | 21.1 | 102.1 | 189.3 | 27,532 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 597 | 88.1 | 100.7 | 177.8 | 17,923 | 0.0% |
| micronaut-graphql | Java | Q1 | 1926 | 18.2 | 36.6 | 43.8 | 57,765 | 0.0% |
| quarkus-graphql | Java | Q1 | 1141 | 34.5 | 37.1 | 48.7 | 34,236 | 0.0% |
| play-graphql | Scala | Q1 | 399 | 98.1 | 199.1 | 290.6 | 11,960 | 0.0% |
| ruby-rails | Ruby | Q1 | 636 | 69.1 | 122.1 | 192.6 | 19,093 | 0.0% |
| hanami | Ruby | Q1 | 1291 | 7.0 | 251.8 | 279.1 | 38,736 | 0.0% |
| php-laravel | PHP | Q1 | 212 | 191.6 | 250.7 | 281.6 | 6,361 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 608 | 87.9 | 114.7 | 191.4 | 18,225 | 0.0% |
| csharp-dotnet | C# | Q1 | 527 | 91.0 | 184.8 | 201.2 | 15,804 | 0.0% |
| fraiseql-tv | Rust | Q1 | 10778 | 3.2 | 7.8 | 10.7 | 323,350 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 7877 | 4.5 | 10.5 | 14.1 | 236,296 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7864 | 4.5 | 10.6 | 14.2 | 235,917 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 10622 | 3.3 | 8.0 | 11.0 | 318,649 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 16351 | 1.7 | 7.0 | 11.5 | 490,533 | 0.0% |
| async-graphql | Rust | Q2 | 10527 | 3.5 | 7.3 | 9.6 | 315,805 | 0.0% |
| juniper | Rust | Q2 | 9887 | 3.9 | 6.9 | 8.6 | 296,602 | 0.0% |
| go-gqlgen | Go | Q2 | 9475 | 3.6 | 9.3 | 13.5 | 284,254 | 0.0% |
| gin-rest | Go | Q2 | 8730 | 3.7 | 10.3 | 15.0 | 261,900 | 0.0% |
| go-graphql-go | Go | Q2 | 2479 | 6.9 | 64.0 | 81.8 | 74,367 | 0.0% |
| graphql-go | Go | Q2 | 1086 | 22.0 | 85.3 | 98.6 | 32,594 | 0.0% |
| apollo-server | Node.js | Q2 | 5815 | 6.4 | 10.8 | 17.4 | 174,445 | 0.0% |
| apollo-orm | Node.js | Q2 | 4080 | 9.0 | 16.2 | 23.1 | 122,395 | 0.0% |
| express-rest | Node.js | Q2 | 6288 | 6.1 | 9.4 | 15.1 | 188,631 | 0.0% |
| express-orm | Node.js | Q2 | 3579 | 11.0 | 15.7 | 18.6 | 107,371 | 0.0% |
| express-graphql | Node.js | Q2 | 4045 | 9.4 | 14.3 | 18.7 | 121,360 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9161 | 4.1 | 7.4 | 10.5 | 274,832 | 0.0% |
| mercurius | Node.js | Q2 | 8583 | 3.9 | 9.7 | 12.0 | 257,484 | 0.0% |
| postgraphile | Node.js | Q2 | 5618 | 6.6 | 13.2 | 17.7 | 168,540 | 0.0% |
| strawberry | Python | Q2 | 2137 | 18.0 | 29.4 | 33.7 | 64,121 | 0.0% |
| graphene | Python | Q2 | 2528 | 16.3 | 23.7 | 29.8 | 75,848 | 0.0% |
| fastapi-rest | Python | Q2 | 5212 | 7.0 | 12.2 | 13.1 | 156,369 | 0.0% |
| flask-rest | Python | Q2 | 320 | 109.4 | 193.6 | 202.9 | 9,600 | 0.0% |
| ariadne | Python | Q2 | 2663 | 14.3 | 22.1 | 25.6 | 79,902 | 0.0% |
| asgi-graphql | Python | Q2 | 2732 | 14.0 | 21.1 | 25.1 | 81,970 | 0.0% |
| spring-boot | Java | Q2 | 56 | 698.0 | 1202.5 | 1500.8 | 1,668 | 0.0% |
| spring-boot-orm | Java | Q2 | 7886 | 3.8 | 11.7 | 20.2 | 236,570 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 9158 | 3.4 | 10.2 | 16.0 | 274,754 | 0.0% |
| micronaut-graphql | Java | Q2 | 4077 | 7.9 | 22.2 | 48.9 | 122,297 | 0.0% |
| quarkus-graphql | Java | Q2 | 12165 | 2.9 | 6.9 | 9.4 | 364,953 | 0.0% |
| play-graphql | Scala | Q2 | 1482 | 19.1 | 68.6 | 93.0 | 44,455 | 0.0% |
| ruby-rails | Ruby | Q2 | 435 | 88.6 | 191.8 | 272.2 | 13,036 | 0.0% |
| hanami | Ruby | Q2 | 843 | 11.3 | 392.7 | 541.7 | 25,298 | 0.0% |
| php-laravel | PHP | Q2 | 168 | 225.0 | 296.8 | 322.7 | 5,053 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 688 | 86.5 | 103.5 | 112.0 | 20,626 | 0.0% |
| csharp-dotnet | C# | Q2 | 6184 | 4.8 | 14.1 | 42.3 | 185,515 | 0.0% |
| fraiseql-tv | Rust | Q2 | 11104 | 3.1 | 7.8 | 10.7 | 333,116 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5655 | 6.2 | 14.9 | 20.1 | 169,636 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5445 | 6.5 | 15.4 | 20.6 | 163,361 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 10811 | 3.1 | 7.8 | 10.7 | 324,336 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 8636 | 4.4 | 7.7 | 10.5 | 259,094 | 0.0% |
| async-graphql | Rust | Q2b | 8873 | 4.4 | 6.8 | 8.3 | 266,197 | 0.0% |
| juniper | Rust | Q2b | 4677 | 8.0 | 11.7 | 12.9 | 140,298 | 0.0% |
| go-gqlgen | Go | Q2b | 1723 | 17.1 | 56.9 | 70.1 | 51,696 | 0.0% |
| gin-rest | Go | Q2b | 2105 | 9.3 | 68.8 | 89.2 | 63,142 | 0.0% |
| go-graphql-go | Go | Q2b | 2039 | 7.4 | 74.4 | 88.9 | 61,157 | 0.0% |
| graphql-go | Go | Q2b | 797 | 54.4 | 99.6 | 110.0 | 23,923 | 0.0% |
| apollo-server | Node.js | Q2b | 3853 | 9.7 | 16.2 | 23.9 | 115,587 | 0.0% |
| apollo-orm | Node.js | Q2b | 2245 | 17.4 | 24.3 | 30.9 | 67,351 | 0.0% |
| express-rest | Node.js | Q2b | 4873 | 7.6 | 15.1 | 18.7 | 146,178 | 0.0% |
| express-orm | Node.js | Q2b | 2197 | 17.3 | 29.0 | 39.8 | 65,916 | 0.0% |
| express-graphql | Node.js | Q2b | 3399 | 10.8 | 17.6 | 24.8 | 101,979 | 0.0% |
| graphql-yoga | Node.js | Q2b | 5397 | 6.2 | 14.0 | 17.4 | 161,923 | 0.0% |
| mercurius | Node.js | Q2b | 5694 | 6.1 | 13.7 | 17.1 | 170,811 | 0.0% |
| postgraphile | Node.js | Q2b | 4382 | 8.7 | 13.6 | 20.2 | 131,452 | 0.0% |
| strawberry | Python | Q2b | 1524 | 25.3 | 39.9 | 43.0 | 45,709 | 0.0% |
| graphene | Python | Q2b | 1780 | 21.4 | 34.1 | 38.7 | 53,398 | 0.0% |
| fastapi-rest | Python | Q2b | 5086 | 7.5 | 12.1 | 14.5 | 152,594 | 0.0% |
| flask-rest | Python | Q2b | 256 | 175.6 | 212.6 | 287.5 | 7,677 | 0.0% |
| ariadne | Python | Q2b | 1862 | 23.0 | 27.5 | 33.2 | 55,856 | 0.0% |
| asgi-graphql | Python | Q2b | 1884 | 21.5 | 26.8 | 34.9 | 56,516 | 0.0% |
| spring-boot | Java | Q2b | 53 | 703.1 | 1293.4 | 1594.2 | 1,604 | 0.0% |
| spring-boot-orm | Java | Q2b | 7369 | 4.4 | 12.1 | 18.0 | 221,056 | 0.0% |
| spring-boot-orm-naive | Java | Q2b | 7364 | 4.4 | 12.3 | 18.4 | 220,923 | 0.0% |
| micronaut-graphql | Java | Q2b | 880 | 30.6 | 85.3 | 106.5 | 26,387 | 0.0% |
| quarkus-graphql | Java | Q2b | 5847 | 5.6 | 20.2 | 26.0 | 175,407 | 0.0% |
| play-graphql | Scala | Q2b | 962 | 25.7 | 91.7 | 105.8 | 28,853 | 0.0% |
| ruby-rails | Ruby | Q2b | 433 | 89.6 | 189.0 | 262.3 | 13,001 | 0.0% |
| hanami | Ruby | Q2b | 400 | 27.0 | 812.9 | 943.4 | 11,986 | 0.0% |
| php-laravel | PHP | Q2b | 168 | 224.0 | 294.7 | 304.5 | 5,053 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 531 | 92.8 | 193.3 | 204.3 | 15,924 | 0.0% |
| csharp-dotnet | C# | Q2b | 6500 | 4.8 | 12.8 | 37.7 | 195,005 | 0.0% |
| fraiseql-tv | Rust | Q2b | 9958 | 3.5 | 8.4 | 11.3 | 298,730 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 2506 | 13.4 | 36.4 | 47.6 | 75,192 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 2551 | 13.1 | 36.2 | 47.6 | 76,523 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9968 | 3.5 | 8.3 | 11.3 | 299,042 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 809 | 42.3 | 86.2 | 107.3 | 24,282 | 0.0% |
| async-graphql | Rust | M1 | 2168 | 15.3 | 37.6 | 54.3 | 65,045 | 0.0% |
| juniper | Rust | M1 | 2187 | 11.7 | 58.3 | 92.1 | 65,598 | 0.0% |
| go-gqlgen | Go | M1 | 2128 | 11.3 | 62.8 | 99.4 | 63,853 | 0.0% |
| gin-rest | Go | M1 | 2110 | 10.7 | 65.8 | 104.9 | 63,299 | 0.0% |
| go-graphql-go | Go | M1 | 1868 | 14.6 | 59.1 | 72.1 | 56,031 | 0.0% |
| graphql-go | Go | M1 | 2061 | 12.9 | 57.8 | 90.3 | 61,838 | 0.0% |
| apollo-server | Node.js | M1 | 2202 | 12.2 | 55.0 | 86.7 | 66,065 | 0.0% |
| express-graphql | Node.js | M1 | 2177 | 16.7 | 44.1 | 71.5 | 65,301 | 0.0% |
| graphql-yoga | Node.js | M1 | 2199 | 11.3 | 58.8 | 91.6 | 65,978 | 0.0% |
| mercurius | Node.js | M1 | 786 | 29.2 | 163.5 | 277.0 | 23,590 | 0.0% |
| strawberry | Python | M1 | 1945 | 19.6 | 32.0 | 37.9 | 58,363 | 0.0% |
| graphene | Python | M1 | 2138 | 16.2 | 37.9 | 59.3 | 64,132 | 0.0% |
| fastapi-rest | Python | M1 | 2223 | 11.5 | 57.2 | 89.8 | 66,678 | 0.0% |
| spring-boot | Java | M1 | 1221 | 13.9 | 112.7 | 301.3 | 36,640 | 0.0% |
| spring-boot-orm | Java | M1 | 1826 | 13.0 | 71.7 | 119.9 | 54,788 | 0.0% |
| micronaut-graphql | Java | M1 | 1082 | 18.6 | 88.4 | 150.3 | 32,458 | 0.0% |
| quarkus-graphql | Java | M1 | 2058 | 19.2 | 20.7 | 22.9 | 61,747 | 0.0% |
| play-graphql | Scala | M1 | 2182 | 14.9 | 42.9 | 63.2 | 65,460 | 0.0% |
| ruby-rails | Ruby | M1 | 702 | 60.3 | 128.6 | 197.9 | 21,060 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 460 | 91.6 | 190.2 | 202.8 | 13,806 | 0.0% |
| csharp-dotnet | C# | M1 | 2245 | 10.6 | 59.4 | 95.4 | 67,351 | 0.0% |
| fraiseql-tv | Rust | M1 | 4405 | 6.6 | 20.4 | 37.3 | 132,148 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 2958 | 9.2 | 36.5 | 68.8 | 88,738 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 3872 | 7.2 | 22.6 | 42.7 | 116,158 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 8736 | 4.2 | 8.2 | 10.6 | 262,092 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 899 | 13.2 | 64.1 | 142.9 | 26,968 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 16613 | 1.7 | 6.8 | 11.2 | 498,390 | 0.0% |
| async-graphql | Rust | F1 | 10303 | 3.6 | 7.3 | 9.5 | 309,099 | 0.0% |
| juniper | Rust | F1 | 9854 | 3.8 | 6.7 | 8.8 | 295,611 | 0.0% |
| go-gqlgen | Go | F1 | 7601 | 4.2 | 12.4 | 20.5 | 228,033 | 0.0% |
| gin-rest | Go | F1 | 7200 | 4.3 | 13.2 | 22.4 | 215,985 | 0.0% |
| go-graphql-go | Go | F1 | 1064 | 22.1 | 87.0 | 99.6 | 31,916 | 0.0% |
| graphql-go | Go | F1 | 1049 | 22.0 | 87.9 | 100.6 | 31,463 | 0.0% |
| apollo-server | Node.js | F1 | 5688 | 6.7 | 10.5 | 16.2 | 170,655 | 0.0% |
| apollo-orm | Node.js | F1 | 4044 | 9.4 | 14.9 | 19.1 | 121,326 | 0.0% |
| express-rest | Node.js | F1 | 6198 | 6.2 | 9.3 | 14.2 | 185,951 | 0.0% |
| express-orm | Node.js | F1 | 3430 | 11.4 | 16.4 | 19.4 | 102,899 | 0.0% |
| express-graphql | Node.js | F1 | 4270 | 9.0 | 13.3 | 15.4 | 128,109 | 0.0% |
| graphql-yoga | Node.js | F1 | 7910 | 4.7 | 9.8 | 12.3 | 237,295 | 0.0% |
| mercurius | Node.js | F1 | 8134 | 4.1 | 10.3 | 13.0 | 244,029 | 0.0% |
| strawberry | Python | F1 | 1980 | 19.3 | 32.7 | 35.1 | 59,392 | 0.0% |
| graphene | Python | F1 | 2363 | 16.2 | 27.0 | 29.1 | 70,883 | 0.0% |
| fastapi-rest | Python | F1 | 5225 | 7.7 | 10.7 | 14.3 | 156,747 | 0.0% |
| flask-rest | Python | F1 | 322 | 109.3 | 192.0 | 201.7 | 9,661 | 0.0% |
| ariadne | Python | F1 | 2384 | 17.4 | 24.1 | 32.0 | 71,506 | 0.0% |
| asgi-graphql | Python | F1 | 2460 | 16.8 | 23.3 | 31.2 | 73,791 | 0.0% |
| spring-boot | Java | F1 | 54 | 704.5 | 1294.6 | 1504.4 | 1,612 | 0.0% |
| spring-boot-orm | Java | F1 | 8499 | 3.7 | 10.8 | 16.5 | 254,971 | 0.0% |
| spring-boot-orm-naive | Java | F1 | 9469 | 3.3 | 9.8 | 15.7 | 284,074 | 0.0% |
| ruby-rails | Ruby | F1 | 427 | 89.4 | 194.4 | 273.9 | 12,814 | 0.0% |
| php-laravel | PHP | F1 | 165 | 226.5 | 305.3 | 375.3 | 4,958 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 671 | 87.3 | 104.5 | 112.5 | 20,140 | 0.0% |
| csharp-dotnet | C# | F1 | 6700 | 4.8 | 11.4 | 37.8 | 201,000 | 0.0% |
| fraiseql-tv | Rust | F1 | 10683 | 3.2 | 8.0 | 11.0 | 320,478 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 4577 | 7.7 | 18.6 | 25.3 | 137,298 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 4504 | 7.8 | 19.0 | 25.7 | 135,119 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10703 | 3.2 | 8.0 | 10.9 | 321,079 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 3957 | 9.7 | 15.3 | 22.2 | 118,704 | 0.0% |
| async-graphql | Rust | F2 | 8698 | 4.4 | 7.0 | 8.4 | 260,934 | 0.0% |
| juniper | Rust | F2 | 4362 | 8.8 | 12.2 | 13.3 | 130,870 | 0.0% |
| go-gqlgen | Go | F2 | 1768 | 16.4 | 57.3 | 71.2 | 53,045 | 0.0% |
| gin-rest | Go | F2 | 959 | 26.5 | 91.2 | 102.7 | 28,760 | 0.0% |
| go-graphql-go | Go | F2 | 799 | 52.3 | 99.8 | 110.7 | 23,972 | 0.0% |
| graphql-go | Go | F2 | 773 | 67.5 | 100.9 | 111.0 | 23,203 | 0.0% |
| apollo-server | Node.js | F2 | 3636 | 10.1 | 18.0 | 25.6 | 109,086 | 0.0% |
| apollo-orm | Node.js | F2 | 2038 | 18.7 | 28.5 | 40.4 | 61,136 | 0.0% |
| express-rest | Node.js | F2 | 4981 | 7.8 | 12.5 | 18.0 | 149,432 | 0.0% |
| express-orm | Node.js | F2 | 2248 | 17.5 | 25.2 | 28.7 | 67,442 | 0.0% |
| express-graphql | Node.js | F2 | 3268 | 11.3 | 18.9 | 25.3 | 98,027 | 0.0% |
| graphql-yoga | Node.js | F2 | 5575 | 6.6 | 11.6 | 16.7 | 167,256 | 0.0% |
| mercurius | Node.js | F2 | 5936 | 6.1 | 13.4 | 17.5 | 178,077 | 0.0% |
| strawberry | Python | F2 | 1422 | 27.0 | 42.6 | 46.5 | 42,668 | 0.0% |
| graphene | Python | F2 | 1672 | 25.2 | 33.1 | 41.1 | 50,146 | 0.0% |
| fastapi-rest | Python | F2 | 5167 | 7.1 | 12.9 | 15.6 | 155,023 | 0.0% |
| flask-rest | Python | F2 | 261 | 172.7 | 207.7 | 281.7 | 7,838 | 0.0% |
| ariadne | Python | F2 | 1732 | 22.4 | 30.9 | 39.5 | 51,947 | 0.0% |
| asgi-graphql | Python | F2 | 1756 | 22.3 | 29.6 | 32.1 | 52,687 | 0.0% |
| spring-boot | Java | F2 | 54 | 703.8 | 1210.1 | 1500.5 | 1,617 | 0.0% |
| spring-boot-orm | Java | F2 | 7277 | 4.5 | 12.3 | 18.4 | 218,308 | 0.0% |
| spring-boot-orm-naive | Java | F2 | 7388 | 4.3 | 12.2 | 18.3 | 221,635 | 0.0% |
| ruby-rails | Ruby | F2 | 418 | 88.9 | 199.8 | 291.5 | 12,527 | 0.0% |
| php-laravel | PHP | F2 | 164 | 232.3 | 301.7 | 359.3 | 4,917 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 481 | 94.3 | 196.3 | 207.9 | 14,435 | 0.0% |
| csharp-dotnet | C# | F2 | 6164 | 5.0 | 13.5 | 40.0 | 184,924 | 0.0% |
| fraiseql-tv | Rust | F2 | 9458 | 3.7 | 8.7 | 11.8 | 283,751 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 1632 | 18.7 | 56.7 | 69.1 | 48,957 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 1667 | 18.4 | 55.7 | 68.2 | 50,023 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 9454 | 3.7 | 8.7 | 11.8 | 283,606 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 50 | 799.9 | 910.5 | 975.9 | 1,501 | 0.0% |
| async-graphql | Rust | T1 | 8460 | 4.6 | 6.6 | 7.7 | 253,807 | 0.0% |
| juniper | Rust | T1 | 6982 | 5.6 | 8.5 | 9.9 | 209,452 | 0.0% |
| go-gqlgen | Go | T1 | 6856 | 5.0 | 11.3 | 15.6 | 205,680 | 0.0% |
| gin-rest | Go | T1 | 2364 | 13.2 | 42.5 | 63.0 | 70,921 | 0.0% |
| go-graphql-go | Go | T1 | 436 | 89.4 | 103.5 | 115.2 | 13,087 | 0.0% |
| graphql-go | Go | T1 | 961 | 23.1 | 88.6 | 99.3 | 28,837 | 0.0% |
| apollo-server | Node.js | T1 | 2511 | 13.0 | 30.7 | 35.1 | 75,341 | 0.0% |
| apollo-orm | Node.js | T1 | 2057 | 18.0 | 25.9 | 38.6 | 61,714 | 0.0% |
| express-rest | Node.js | T1 | 2679 | 12.3 | 29.2 | 35.0 | 80,367 | 0.0% |
| express-orm | Node.js | T1 | 3338 | 10.9 | 15.6 | 29.4 | 100,133 | 0.0% |
| express-graphql | Node.js | T1 | 2320 | 15.5 | 30.0 | 35.2 | 69,615 | 0.0% |
| graphql-yoga | Node.js | T1 | 3428 | 9.7 | 22.4 | 26.4 | 102,844 | 0.0% |
| mercurius | Node.js | T1 | 3877 | 8.3 | 20.4 | 23.4 | 116,299 | 0.0% |
| postgraphile | Node.js | T1 | 3343 | 11.1 | 19.6 | 26.2 | 100,295 | 0.0% |
| strawberry | Python | T1 | 1058 | 35.9 | 55.0 | 65.4 | 31,738 | 0.0% |
| graphene | Python | T1 | 1389 | 26.0 | 46.8 | 54.3 | 41,677 | 0.0% |
| fastapi-rest | Python | T1 | 3292 | 11.7 | 20.9 | 26.8 | 98,774 | 0.0% |
| flask-rest | Python | T1 | 122 | 310.5 | 412.1 | 491.9 | 3,667 | 0.0% |
| ariadne | Python | T1 | 1230 | 31.3 | 42.7 | 57.3 | 36,907 | 0.0% |
| asgi-graphql | Python | T1 | 1277 | 30.6 | 39.9 | 47.5 | 38,297 | 0.0% |
| spring-boot | Java | T1 | 5190 | 6.6 | 15.9 | 23.1 | 155,687 | 0.0% |
| spring-boot-orm | Java | T1 | 3459 | 10.1 | 22.4 | 33.2 | 103,756 | 0.0% |
| spring-boot-orm-naive | Java | T1 | 1731 | 18.8 | 53.8 | 79.7 | 51,923 | 0.0% |
| micronaut-graphql | Java | T1 | 580 | 79.0 | 114.2 | 170.6 | 17,404 | 0.0% |
| quarkus-graphql | Java | T1 | 6373 | 5.2 | 19.7 | 25.5 | 191,187 | 0.0% |
| play-graphql | Scala | T1 | 864 | 28.2 | 97.3 | 110.0 | 25,923 | 0.0% |
| ruby-rails | Ruby | T1 | 191 | 198.7 | 380.2 | 472.5 | 5,743 | 0.0% |
| hanami | Ruby | T1 | 398 | 28.0 | 829.1 | 1052.6 | 11,942 | 0.0% |
| php-laravel | PHP | T1 | 64 | 615.6 | 712.5 | 769.2 | 1,928 | 0.0% |
| webonyx-graphql-php | PHP | T1 | 498 | 94.8 | 194.6 | 203.2 | 14,934 | 0.0% |
| csharp-dotnet | C# | T1 | 5219 | 6.7 | 13.1 | 37.6 | 156,583 | 0.0% |
| fraiseql-tv | Rust | T1 | 6383 | 5.6 | 12.1 | 16.3 | 191,479 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 734 | 68.3 | 95.7 | 106.1 | 22,031 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 736 | 68.4 | 95.1 | 105.2 | 22,078 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 6518 | 5.5 | 11.8 | 16.1 | 195,540 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 5075 | 7.7 | 12.4 | 14.4 | 152,256 | 0.0% |
| juniper | Rust | Q3 | 1386 | 28.6 | 36.5 | 42.7 | 41,575 | 0.0% |
| go-gqlgen | Go | Q3 | 841 | 32.8 | 94.5 | 107.1 | 25,232 | 0.0% |
| quarkus-graphql | Java | Q3 | 2142 | 16.2 | 35.0 | 42.6 | 64,262 | 0.0% |
| fraiseql-tv | Rust | Q3 | 4878 | 7.5 | 15.8 | 20.8 | 146,347 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 580 | 86.6 | 108.9 | 116.8 | 17,400 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 547 | 88.6 | 109.4 | 117.2 | 16,397 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 4810 | 7.6 | 16.1 | 21.0 | 144,308 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | MC1 | 675 | 48.1 | 115.6 | 178.6 | 20,256 | 0.0% |
| graphql-yoga | Node.js | MC1 | 1048 | 27.0 | 90.2 | 103.5 | 31,448 | 0.0% |
| mercurius | Node.js | MC1 | 791 | 37.2 | 104.8 | 149.6 | 23,732 | 0.0% |
| fraiseql-tv | Rust | MC1 | 8761 | 4.2 | 8.1 | 10.6 | 262,820 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 8722 | 4.2 | 8.3 | 10.9 | 261,673 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 8397 | 4.2 | 8.6 | 11.8 | 251,897 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 6764 | 4.2 | 8.2 | 10.7 | 202,907 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 10836 | 3.1 | 8.1 | 11.3 | 325,085 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 10668 | 3.2 | 8.1 | 11.2 | 320,031 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 10574 | 3.2 | 8.2 | 11.4 | 317,218 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 10912 | 3.1 | 8.0 | 11.2 | 327,368 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 10743 | 3.2 | 8.2 | 11.5 | 322,295 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 4767 | 3.2 | 8.2 | 11.3 | 143,022 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 10474 | 3.3 | 8.4 | 11.5 | 314,220 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 10675 | 3.2 | 8.2 | 11.5 | 320,251 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 8866 | 4.1 | 8.0 | 10.4 | 265,995 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 10609 | 3.3 | 7.9 | 10.8 | 318,259 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7731 | 4.6 | 10.7 | 14.3 | 231,939 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 7761 | 4.5 | 10.7 | 14.3 | 232,825 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 10539 | 3.3 | 8.0 | 10.9 | 316,156 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 10576 | 3.3 | 7.9 | 10.7 | 317,274 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 7556 | 4.6 | 10.8 | 14.5 | 226,680 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 7611 | 4.6 | 10.9 | 14.6 | 228,329 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 10381 | 3.3 | 8.0 | 11.0 | 311,431 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9832 | 3.6 | 8.4 | 11.3 | 294,957 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 2241 | 14.6 | 41.6 | 53.6 | 67,222 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 2149 | 15.3 | 42.6 | 54.7 | 64,462 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9814 | 3.6 | 8.5 | 11.5 | 294,412 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 9209 | 4.0 | 7.6 | 9.9 | 276,256 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1891 | 13.7 | 53.9 | 111.0 | 56,720 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 9266 | 4.0 | 7.6 | 9.7 | 277,995 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 7764 | 4.2 | 9.1 | 14.5 | 232,922 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1866 | 20.8 | 28.7 | 0.0% |
| spring-boot-orm | Java | 918 | 21.1 | 189.3 | 0.0% |
| gin-rest | Go | 761 | 20.4 | 188.6 | 0.0% |
| express-orm | Node.js | 648 | 68.3 | 174.9 | 0.0% |
| ruby-rails | Ruby | 636 | 69.1 | 192.6 | 0.0% |
| spring-boot-orm-naive | Java | 597 | 88.1 | 177.8 | 0.0% |
| express-rest | Node.js | 525 | 86.5 | 194.4 | 0.0% |
| fastapi-rest | Python | 497 | 89.9 | 188.5 | 0.0% |
| spring-boot | Java | 453 | 94.8 | 210.4 | 0.0% |
| flask-rest | Python | 220 | 192.6 | 299.8 | 0.0% |
| php-laravel | PHP | 212 | 191.6 | 281.6 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| micronaut-graphql | Java | 1926 | 18.2 | 43.8 | 0.0% |
| ariadne | Python | 1704 | 20.7 | 42.5 | 0.0% |
| asgi-graphql | Python | 1616 | 23.2 | 43.6 | 0.0% |
| graphene | Python | 1596 | 24.5 | 48.2 | 0.0% |
| strawberry | Python | 1559 | 23.6 | 46.0 | 0.0% |
| hanami | Ruby | 1291 | 7.0 | 279.1 | 0.0% |
| quarkus-graphql | Java | 1141 | 34.5 | 48.7 | 0.0% |
| express-graphql | Node.js | 721 | 55.1 | 162.8 | 0.0% |
| apollo-server | Node.js | 681 | 69.4 | 122.8 | 0.0% |
| go-gqlgen | Go | 644 | 84.8 | 190.6 | 0.0% |
| webonyx-graphql-php | PHP | 608 | 87.9 | 191.4 | 0.0% |
| graphql-go | Go | 590 | 88.0 | 190.7 | 0.0% |
| mercurius | Node.js | 581 | 82.4 | 190.4 | 0.0% |
| go-graphql-go | Go | 579 | 88.5 | 189.0 | 0.0% |
| graphql-yoga | Node.js | 556 | 83.7 | 190.8 | 0.0% |
| async-graphql | Rust | 531 | 96.3 | 182.5 | 0.0% |
| csharp-dotnet | C# | 527 | 91.0 | 201.2 | 0.0% |
| apollo-orm | Node.js | 523 | 84.9 | 190.6 | 0.0% |
| juniper | Rust | 502 | 93.1 | 198.1 | 0.0% |
| play-graphql | Scala | 399 | 98.1 | 290.6 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 10778 | 3.2 | 10.7 | 0.0% |
| fraiseql-tv-cache | Rust | 10622 | 3.3 | 11.0 | 0.0% |
| fraiseql-v-nocache | Rust | 7877 | 4.5 | 14.1 | 0.0% |
| fraiseql-v-cache | Rust | 7864 | 4.5 | 14.2 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 4908 | 7.6 | 19.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 10778 | 3.2 | 10.7 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 10622 | 3.3 | 11.0 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 7877 | 4.5 | 14.1 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7864 | 4.5 | 14.2 |
| postgraphile | Node.js | graphql-schema-first | 4908 | 7.6 | 19.7 |
| micronaut-graphql | Java | graphql | 1926 | 18.2 | 43.8 |
| actix-web-rest | Rust | rest | 1866 | 20.8 | 28.7 |
| ariadne | Python | graphql | 1704 | 20.7 | 42.5 |
| asgi-graphql | Python | graphql | 1616 | 23.2 | 43.6 |
| graphene | Python | graphql | 1596 | 24.5 | 48.2 |
| strawberry | Python | graphql | 1559 | 23.6 | 46.0 |
| hanami | Ruby | graphql | 1291 | 7.0 | 279.1 |
| quarkus-graphql | Java | graphql | 1141 | 34.5 | 48.7 |
| spring-boot-orm | Java | rest | 918 | 21.1 | 189.3 |
| gin-rest | Go | rest | 761 | 20.4 | 188.6 |
| express-graphql | Node.js | graphql | 721 | 55.1 | 162.8 |
| apollo-server | Node.js | graphql | 681 | 69.4 | 122.8 |
| express-orm | Node.js | rest | 648 | 68.3 | 174.9 |
| go-gqlgen | Go | graphql | 644 | 84.8 | 190.6 |
| ruby-rails | Ruby | rest | 636 | 69.1 | 192.6 |
| webonyx-graphql-php | PHP | graphql | 608 | 87.9 | 191.4 |
| spring-boot-orm-naive | Java | rest | 597 | 88.1 | 177.8 |
| graphql-go | Go | graphql | 590 | 88.0 | 190.7 |
| mercurius | Node.js | graphql | 581 | 82.4 | 190.4 |
| go-graphql-go | Go | graphql | 579 | 88.5 | 189.0 |
| graphql-yoga | Node.js | graphql | 556 | 83.7 | 190.8 |
| async-graphql | Rust | graphql | 531 | 96.3 | 182.5 |
| csharp-dotnet | C# | graphql | 527 | 91.0 | 201.2 |
| express-rest | Node.js | rest | 525 | 86.5 | 194.4 |
| apollo-orm | Node.js | graphql | 523 | 84.9 | 190.6 |
| juniper | Rust | graphql | 502 | 93.1 | 198.1 |
| fastapi-rest | Python | rest | 497 | 89.9 | 188.5 |
| spring-boot | Java | rest | 453 | 94.8 | 210.4 |
| play-graphql | Scala | graphql | 399 | 98.1 | 290.6 |
| flask-rest | Python | rest | 220 | 192.6 | 299.8 |
| php-laravel | PHP | rest | 212 | 191.6 | 281.6 |

---

## Resource Metrics

> **LOC**: non-blank, non-comment lines in primary source files (excl. tests/vendor).  
> **Complexity**: decision-keyword occurrences per 100 LOC (if/for/while/catch/&&/|| etc.) — McCabe proxy.  
> **Image**: compressed docker image size.  
> **Peak RAM**: maximum RSS observed during the full benchmark run.  
> **Avg CPU**: mean CPU% sampled every 2 s during the benchmark run.

| Framework | Language | LOC | Complexity | Image (MB) | Peak RAM (MB) | Avg CPU (%) |
|-----------|----------|----:|-----------:|-----------:|--------------:|------------:|
| fraiseql-tv | Rust | 251 | 2.0 | 44 | 17 | 103.3 |
| fraiseql-tv-cache | Rust | 251 | 2.0 | 44 | 18 | 103.6 |
| fraiseql-v-nocache | Rust | 531 | 1.3 | 44 | 15 | 61.4 |
| fraiseql-v-cache | Rust | 531 | 1.3 | 44 | 15 | 89.3 |
| postgraphile | Node.js | 160 | 9.4 | 91 | 64 | 125.7 |
| micronaut-graphql | Java | 707 | 5.1 | 100 | 278 | 131.2 |
| actix-web-rest | Rust | 681 | 4.0 | 12 | 9 | 53.8 |
| ariadne | Python | 482 | 16.8 | 134 | 114 | 197.2 |
| asgi-graphql | Python | 589 | 15.1 | 134 | 111 | 197.1 |
| graphene | Python | 1,178 | 10.0 | 144 | 164 | 175.5 |
| strawberry | Python | 1,771 | 12.6 | 188 | 179 | 171.5 |
| hanami | Ruby | 464 | 5.2 | 108 | 116 | 200.1 |
| quarkus-graphql | Java | 549 | 6.7 | 125 | 457 | 133.9 |
| spring-boot-orm | Java | 461 | 1.5 | 133 | 659 | 156.3 |
| gin-rest | Go | 2,071 | 11.4 | 9 | 98 | 126.2 |
| express-graphql | Node.js | 481 | 8.1 | 98 | 56 | 101.7 |
| apollo-server | Node.js | 744 | 7.5 | 119 | 62 | 103.2 |
| express-orm | Node.js | 443 | 7.2 | 96 | 57 | 107.9 |
| go-gqlgen | Go | 7,225 | 13.1 | 10 | 43 | 144.5 |
| ruby-rails | Ruby | 494 | 5.9 | 283 | 592 | 177.5 |
| webonyx-graphql-php | PHP | 770 | 4.9 | 262 | 116 | 181.6 |
| spring-boot-orm-naive | Java | 268 | 1.5 | 101 | 564 | 141.0 |
| graphql-go | Go | 740 | 8.8 | 12 | 48 | 159.0 |
| mercurius | Node.js | 444 | 9.2 | 103 | 50 | 80.4 |
| go-graphql-go | Go | 2,969 | 12.1 | 7 | 38 | 161.9 |
| graphql-yoga | Node.js | 444 | 9.0 | 98 | 50 | 81.1 |
| async-graphql | Rust | 693 | 4.5 | 12 | 12 | 93.3 |
| csharp-dotnet | C# | 1,979 | 2.0 | 105 | 142 | 153.5 |
| express-rest | Node.js | 361 | 10.2 | 51 | 49 | 100.1 |
| apollo-orm | Node.js | 420 | 6.0 | 149 | 68 | 125.7 |
| juniper | Rust | 685 | 2.8 | 12 | 13 | 121.3 |
| fastapi-rest | Python | 1,769 | 11.4 | 68 | 151 | 145.0 |
| spring-boot | Java | 853 | 0.9 | 160 | 685 | 74.3 |
| play-graphql | Scala | 522 | 7.1 | 156 | 616 | 159.7 |
| flask-rest | Python | 571 | 13.5 | 56 | 181 | 203.9 |
| php-laravel | PHP | 2,241 | 2.9 | 359 | 73 | 199.8 |
| fraiseql-tv-audit | Rust | — | — | 44 | 13 | 20.1 |

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

> **Peak**: fraiseql-tv 8761 cycles/s (1 req) vs graphql-yoga 1048 cycles/s (2 req) — 8.4× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 8,736 M/s: **~532,920 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.5M cascade writes) scattered row versions across pages. VACUUM FULL compacts pages between framework runs; within a single M1 measurement window the heap accumulates fresh dead tuples as the run progresses. Equivalent to sustained production load.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.