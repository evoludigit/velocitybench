# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-04  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 30s per scenario  
**Warmup**: 10s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 12588 | 2.0 | 9.9 | 17.2 | 377,625 | 0.0% |
| async-graphql | Rust | Q1 | 7905 | 4.7 | 9.1 | 12.1 | 237,163 | 0.0% |
| juniper | Rust | Q1 | 4499 | 8.2 | 16.0 | 19.2 | 134,962 | 0.0% |
| go-gqlgen | Go | Q1 | 6442 | 4.3 | 18.2 | 30.1 | 193,249 | 0.0% |
| gin-rest | Go | Q1 | 5586 | 4.5 | 22.0 | 37.2 | 167,581 | 0.0% |
| go-graphql-go | Go | Q1 | 7045 | 4.6 | 13.2 | 20.8 | 211,352 | 0.0% |
| graphql-go | Go | Q1 | 7576 | 4.3 | 12.2 | 19.3 | 227,269 | 0.0% |
| apollo-server | Node.js | Q1 | 4513 | 7.5 | 21.4 | 31.6 | 135,385 | 0.0% |
| apollo-orm | Node.js | Q1 | 2984 | 9.9 | 16.1 | 24.6 | 89,524 | 0.0% |
| express-rest | Node.js | Q1 | 7513 | 3.8 | 5.7 | 7.7 | 225,394 | 0.0% |
| express-orm | Node.js | Q1 | 4185 | 9.4 | 13.5 | 14.1 | 125,545 | 0.0% |
| express-graphql | Node.js | Q1 | 4624 | 8.5 | 12.1 | 13.0 | 138,729 | 0.0% |
| graphql-yoga | Node.js | Q1 | 5712 | 4.1 | 9.9 | 14.0 | 171,356 | 0.0% |
| mercurius | Node.js | Q1 | 9008 | 4.0 | 8.4 | 10.7 | 270,237 | 0.0% |
| postgraphile | Node.js | Q1 | 5403 | 6.5 | 8.5 | 10.6 | 162,083 | 0.0% |
| strawberry | Python | Q1 | 868 | 44.4 | 58.1 | 102.3 | 26,031 | 0.0% |
| graphene | Python | Q1 | 1074 | 36.8 | 47.4 | 49.7 | 32,208 | 0.0% |
| fastapi-rest | Python | Q1 | 3623 | 11.0 | 12.5 | 15.8 | 108,691 | 0.0% |
| flask-rest | Python | Q1 | 238 | 171.3 | 253.6 | 306.1 | 7,135 | 0.0% |
| ariadne | Python | Q1 | 1100 | 36.6 | 43.8 | 46.1 | 32,992 | 0.0% |
| asgi-graphql | Python | Q1 | 1118 | 35.8 | 42.8 | 45.8 | 33,552 | 0.0% |
| spring-boot | Java | Q1 | 9150 | 3.3 | 11.0 | 17.4 | 274,509 | 0.0% |
| spring-boot-orm | Java | Q1 | 2523 | 13.5 | 35.1 | 52.5 | 75,697 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 2474 | 13.2 | 36.2 | 54.3 | 74,212 | 0.0% |
| micronaut-graphql | Java | Q1 | 2515 | 14.9 | 27.6 | 31.4 | 75,441 | 0.0% |
| quarkus-graphql | Java | Q1 | 2647 | 12.7 | 35.2 | 48.8 | 79,400 | 0.0% |
| play-graphql | Scala | Q1 | 6182 | 5.0 | 16.2 | 26.9 | 185,467 | 0.0% |
| ruby-rails | Ruby | Q1 | 5642 | 5.5 | 17.7 | 26.8 | 169,251 | 0.0% |
| hanami | Ruby | Q1 | 938 | 7.6 | 252.4 | 634.4 | 28,150 | 0.0% |
| php-laravel | PHP | Q1 | 376 | 69.9 | 126.6 | 321.6 | 11,284 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 4501 | 6.3 | 16.9 | 27.2 | 135,039 | 0.0% |
| csharp-dotnet | C# | Q1 | 3338 | 4.6 | 10.2 | 13.8 | 100,145 | 0.0% |
| fraiseql-tv | Python | Q1 | 2917 | 9.6 | 32.4 | 47.7 | 87,496 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 3093 | 9.8 | 33.1 | 48.1 | 92,784 | 0.0% |
| fraiseql-v | Python | Q1 | 6513 | 5.6 | 10.8 | 13.8 | 195,391 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 6138 | 3.7 | 21.0 | 36.8 | 184,148 | 0.0% |
| async-graphql | Rust | Q2 | 2480 | 13.9 | 35.3 | 48.1 | 74,412 | 0.0% |
| juniper | Rust | Q2 | 5705 | 5.9 | 15.7 | 21.6 | 171,144 | 0.0% |
| go-gqlgen | Go | Q2 | 7833 | 4.1 | 12.1 | 19.5 | 234,988 | 0.0% |
| gin-rest | Go | Q2 | 10180 | 2.7 | 11.1 | 18.6 | 305,406 | 0.0% |
| go-graphql-go | Go | Q2 | 7475 | 4.1 | 13.3 | 22.9 | 224,257 | 0.0% |
| graphql-go | Go | Q2 | 8027 | 4.1 | 11.3 | 16.9 | 240,803 | 0.0% |
| apollo-server | Node.js | Q2 | 3262 | 7.5 | 23.7 | 30.8 | 97,868 | 0.0% |
| apollo-orm | Node.js | Q2 | 2878 | 7.5 | 11.8 | 17.2 | 86,332 | 0.0% |
| express-rest | Node.js | Q2 | 10918 | 3.3 | 7.1 | 10.7 | 327,546 | 0.0% |
| express-orm | Node.js | Q2 | 5134 | 7.7 | 10.6 | 11.8 | 154,019 | 0.0% |
| express-graphql | Node.js | Q2 | 5139 | 7.6 | 10.7 | 11.9 | 154,172 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9213 | 3.9 | 8.5 | 11.1 | 276,376 | 0.0% |
| mercurius | Node.js | Q2 | 8584 | 4.4 | 8.2 | 10.7 | 257,524 | 0.0% |
| postgraphile | Node.js | Q2 | 7029 | 5.6 | 7.5 | 10.8 | 210,858 | 0.0% |
| strawberry | Python | Q2 | 802 | 37.9 | 51.0 | 59.4 | 24,068 | 0.1% |
| graphene | Python | Q2 | 1241 | 31.7 | 42.4 | 44.2 | 37,218 | 0.0% |
| fastapi-rest | Python | Q2 | 3577 | 11.1 | 12.9 | 17.8 | 107,297 | 0.0% |
| flask-rest | Python | Q2 | 339 | 121.2 | 180.1 | 210.5 | 10,167 | 0.0% |
| ariadne | Python | Q2 | 1288 | 30.8 | 38.2 | 39.9 | 38,644 | 0.0% |
| asgi-graphql | Python | Q2 | 1068 | 30.3 | 82.0 | 104.9 | 32,055 | 0.0% |
| spring-boot | Java | Q2 | 8877 | 3.5 | 10.6 | 16.6 | 266,314 | 0.0% |
| spring-boot-orm | Java | Q2 | 663 | 52.8 | 121.2 | 161.4 | 19,879 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 2444 | 13.3 | 36.6 | 55.6 | 73,321 | 0.0% |
| micronaut-graphql | Java | Q2 | 6300 | 4.7 | 12.1 | 17.0 | 189,014 | 0.0% |
| quarkus-graphql | Java | Q2 | 2825 | 11.8 | 33.3 | 46.2 | 84,758 | 0.0% |
| play-graphql | Scala | Q2 | 5525 | 5.2 | 20.1 | 32.2 | 165,748 | 0.0% |
| ruby-rails | Ruby | Q2 | 3692 | 8.4 | 25.5 | 39.5 | 110,759 | 0.0% |
| hanami | Ruby | Q2 | 1027 | 7.2 | 259.3 | 589.4 | 30,802 | 0.0% |
| php-laravel | PHP | Q2 | 309 | 116.6 | 214.7 | 260.8 | 9,271 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 5331 | 5.9 | 14.3 | 21.1 | 159,924 | 0.0% |
| csharp-dotnet | C# | Q2 | 3418 | 4.8 | 10.5 | 14.3 | 102,545 | 0.0% |
| fraiseql-tv | Python | Q2 | 1806 | 19.2 | 44.5 | 60.7 | 54,189 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 1767 | 19.6 | 45.9 | 62.0 | 53,022 | 0.0% |
| fraiseql-v | Python | Q2 | 2108 | 18.1 | 26.5 | 31.2 | 63,255 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 11019 | 2.4 | 11.0 | 19.1 | 330,564 | 0.0% |
| async-graphql | Rust | Q2b | 4229 | 8.2 | 19.2 | 25.3 | 126,884 | 0.0% |
| juniper | Rust | Q2b | 3405 | 11.2 | 14.5 | 16.3 | 102,159 | 0.0% |
| go-gqlgen | Go | Q2b | 6271 | 5.0 | 15.7 | 24.6 | 188,126 | 0.0% |
| gin-rest | Go | Q2b | 6818 | 4.3 | 15.5 | 23.8 | 204,554 | 0.0% |
| go-graphql-go | Go | Q2b | 6475 | 5.0 | 14.6 | 22.4 | 194,244 | 0.0% |
| graphql-go | Go | Q2b | 7323 | 4.5 | 11.9 | 18.1 | 219,685 | 0.0% |
| apollo-server | Node.js | Q2b | 2403 | 9.9 | 36.7 | 50.7 | 72,093 | 0.0% |
| apollo-orm | Node.js | Q2b | 1491 | 13.0 | 17.4 | 23.8 | 44,718 | 0.0% |
| express-rest | Node.js | Q2b | 7573 | 4.3 | 8.0 | 11.5 | 227,183 | 0.0% |
| express-orm | Node.js | Q2b | 3176 | 12.4 | 17.8 | 18.5 | 95,271 | 0.0% |
| express-graphql | Node.js | Q2b | 3582 | 10.9 | 14.3 | 16.6 | 107,460 | 0.0% |
| graphql-yoga | Node.js | Q2b | 6437 | 5.6 | 7.7 | 10.8 | 193,113 | 0.0% |
| mercurius | Node.js | Q2b | 8252 | 4.5 | 7.9 | 11.6 | 247,566 | 0.0% |
| postgraphile | Node.js | Q2b | 5481 | 7.2 | 9.1 | 11.0 | 164,442 | 0.0% |
| strawberry | Python | Q2b | 668 | 58.2 | 74.5 | 86.4 | 20,027 | 0.0% |
| graphene | Python | Q2b | 798 | 49.0 | 62.6 | 65.5 | 23,939 | 0.0% |
| fastapi-rest | Python | Q2b | 3417 | 11.3 | 12.5 | 13.7 | 102,518 | 0.0% |
| flask-rest | Python | Q2b | 271 | 154.2 | 221.3 | 263.3 | 8,116 | 0.0% |
| ariadne | Python | Q2b | 822 | 48.2 | 57.1 | 59.0 | 24,664 | 0.0% |
| asgi-graphql | Python | Q2b | 494 | 48.7 | 123.8 | 159.9 | 14,818 | 0.2% |
| spring-boot | Java | Q2b | 5265 | 6.0 | 18.1 | 27.9 | 157,941 | 0.0% |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | 2063 | 8.8 | 27.6 | 32.3 | 61,891 | 0.0% |
| quarkus-graphql | Java | Q2b | 3939 | 8.2 | 24.4 | 34.5 | 118,184 | 0.0% |
| play-graphql | Scala | Q2b | 7421 | 4.6 | 11.8 | 16.6 | 222,621 | 0.0% |
| ruby-rails | Ruby | Q2b | 3607 | 8.6 | 26.4 | 42.2 | 108,221 | 0.0% |
| hanami | Ruby | Q2b | 594 | 10.5 | 370.6 | 980.8 | 17,813 | 0.0% |
| php-laravel | PHP | Q2b | 351 | 92.6 | 114.4 | 150.7 | 10,539 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 3029 | 7.0 | 11.8 | 16.2 | 90,857 | 0.0% |
| csharp-dotnet | C# | Q2b | 6386 | 5.2 | 11.5 | 15.6 | 191,570 | 0.0% |
| fraiseql-tv | Python | Q2b | 1115 | 31.8 | 68.3 | 90.1 | 33,461 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 1152 | 30.8 | 66.5 | 88.0 | 34,551 | 0.0% |
| fraiseql-v | Python | Q2b | 923 | 40.8 | 64.0 | 77.2 | 27,696 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1223 | 21.3 | 102.3 | 160.2 | 36,704 | 0.0% |
| async-graphql | Rust | M1 | 2023 | 16.7 | 39.1 | 54.9 | 60,683 | 0.0% |
| juniper | Rust | M1 | 278 | 78.3 | 500.0 | 896.4 | 8,332 | 0.0% |
| go-gqlgen | Go | M1 | 2001 | 12.4 | 65.3 | 104.5 | 60,037 | 0.0% |
| gin-rest | Go | M1 | 404 | 52.4 | 361.7 | 694.6 | 12,131 | 0.0% |
| go-graphql-go | Go | M1 | 5860 | 5.1 | 18.1 | 28.2 | 175,800 | 0.0% |
| graphql-go | Go | M1 | 418 | 49.2 | 322.3 | 747.6 | 12,547 | 0.0% |
| apollo-server | Node.js | M1 | 16 | 83.8 | 4387.7 | 8592.4 | 489 | 25.7% |
| express-graphql | Node.js | M1 | 2075 | 12.7 | 59.0 | 91.6 | 62,260 | 0.0% |
| graphql-yoga | Node.js | M1 | 1808 | 13.1 | 72.7 | 128.5 | 54,243 | 0.0% |
| mercurius | Node.js | M1 | 1686 | 13.5 | 79.0 | 148.7 | 50,588 | 0.0% |
| strawberry | Python | M1 | 961 | 40.8 | 54.9 | 59.1 | 28,838 | 0.0% |
| graphene | Python | M1 | 1141 | 33.9 | 46.3 | 50.7 | 34,231 | 0.0% |
| fastapi-rest | Python | M1 | — | — | — | — | — | _known bug — skipped_ |
| spring-boot | Java | M1 | 489 | 39.2 | 277.2 | 654.1 | 14,674 | 0.0% |
| spring-boot-orm | Java | M1 | 1403 | 16.8 | 94.7 | 152.3 | 42,101 | 0.0% |
| micronaut-graphql | Java | M1 | 201 | 54.3 | 609.5 | 1712.9 | 6,039 | 0.0% |
| quarkus-graphql | Java | M1 | 1669 | 17.1 | 68.6 | 117.8 | 50,071 | 0.0% |
| play-graphql | Scala | M1 | 1729 | 16.1 | 48.0 | 76.3 | 51,867 | 0.0% |
| ruby-rails | Ruby | M1 | 5739 | 5.2 | 18.1 | 28.2 | 172,184 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 46 | 13.4 | 83.8 | 9296.1 | 1,377 | 2.8% |
| csharp-dotnet | C# | M1 | 154 | 175.7 | 784.1 | 1209.6 | 4,627 | 0.0% |
| fraiseql-tv | Python | M1 | 1248 | 15.9 | 113.4 | 219.2 | 37,429 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1772 | 12.5 | 77.8 | 125.3 | 53,173 | 0.0% |
| fraiseql-v | Python | M1 | 1798 | 12.4 | 77.0 | 121.7 | 53,953 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 1765 | 12.6 | 78.2 | 124.7 | 52,945 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 5017 | 4.2 | 27.0 | 49.0 | 150,509 | 0.0% |
| async-graphql | Rust | F1 | 3518 | 8.7 | 29.3 | 42.1 | 105,539 | 0.0% |
| juniper | Rust | F1 | 5789 | 5.8 | 15.4 | 21.2 | 173,667 | 0.0% |
| go-gqlgen | Go | F1 | 4754 | 6.1 | 23.2 | 36.0 | 142,626 | 0.0% |
| gin-rest | Go | F1 | 9566 | 2.9 | 11.8 | 19.4 | 286,985 | 0.0% |
| go-graphql-go | Go | F1 | 7577 | 4.4 | 11.8 | 17.0 | 227,308 | 0.0% |
| graphql-go | Go | F1 | 7873 | 4.2 | 11.6 | 17.6 | 236,176 | 0.0% |
| apollo-server | Node.js | F1 | 6162 | 5.7 | 11.6 | 19.9 | 184,850 | 0.0% |
| apollo-orm | Node.js | F1 | 1688 | 8.0 | 14.8 | 42.7 | 50,631 | 0.0% |
| express-rest | Node.js | F1 | 10557 | 3.4 | 7.4 | 10.8 | 316,720 | 0.0% |
| express-orm | Node.js | F1 | 4975 | 8.0 | 11.1 | 12.1 | 149,249 | 0.0% |
| express-graphql | Node.js | F1 | 5148 | 7.6 | 10.6 | 12.1 | 154,446 | 0.0% |
| graphql-yoga | Node.js | F1 | 8757 | 4.1 | 8.7 | 10.5 | 262,722 | 0.0% |
| mercurius | Node.js | F1 | 8456 | 4.5 | 8.4 | 10.7 | 253,673 | 0.0% |
| strawberry | Python | F1 | 918 | 41.6 | 57.6 | 73.0 | 27,531 | 0.0% |
| graphene | Python | F1 | 1129 | 34.7 | 46.3 | 48.6 | 33,862 | 0.0% |
| fastapi-rest | Python | F1 | 3586 | 11.0 | 13.0 | 18.7 | 107,575 | 0.0% |
| flask-rest | Python | F1 | 328 | 123.3 | 185.3 | 226.0 | 9,850 | 0.0% |
| ariadne | Python | F1 | 1168 | 34.0 | 42.0 | 43.9 | 35,026 | 0.0% |
| asgi-graphql | Python | F1 | 572 | 33.5 | 67.1 | 105.6 | 17,157 | 0.2% |
| spring-boot | Java | F1 | 8888 | 3.5 | 10.6 | 16.4 | 266,628 | 0.0% |
| spring-boot-orm | Java | F1 | 645 | 53.9 | 125.4 | 171.9 | 19,355 | 0.0% |
| ruby-rails | Ruby | F1 | 3589 | 8.6 | 26.5 | 41.6 | 107,677 | 0.0% |
| php-laravel | PHP | F1 | 245 | 80.7 | 144.1 | 843.1 | 7,360 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 2629 | 6.6 | 14.5 | 19.5 | 78,883 | 0.0% |
| csharp-dotnet | C# | F1 | 7267 | 5.0 | 10.8 | 14.3 | 218,018 | 0.0% |
| fraiseql-tv | Python | F1 | 1903 | 18.2 | 42.7 | 58.2 | 57,085 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 1865 | 18.5 | 43.7 | 59.9 | 55,947 | 0.0% |
| fraiseql-v | Python | F1 | 2105 | 18.1 | 26.6 | 31.4 | 63,161 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 10895 | 2.4 | 11.3 | 19.8 | 326,840 | 0.0% |
| async-graphql | Rust | F2 | 4220 | 8.3 | 19.4 | 25.5 | 126,610 | 0.0% |
| juniper | Rust | F2 | 3491 | 11.2 | 14.6 | 16.7 | 104,744 | 0.0% |
| go-gqlgen | Go | F2 | 4060 | 7.4 | 25.7 | 38.0 | 121,805 | 0.0% |
| gin-rest | Go | F2 | 8213 | 3.8 | 12.1 | 17.6 | 246,403 | 0.0% |
| go-graphql-go | Go | F2 | 6940 | 4.8 | 12.9 | 19.3 | 208,204 | 0.0% |
| graphql-go | Go | F2 | 6756 | 4.9 | 13.5 | 20.2 | 202,666 | 0.0% |
| apollo-server | Node.js | F2 | 4387 | 8.9 | 11.9 | 14.4 | 131,600 | 0.0% |
| apollo-orm | Node.js | F2 | 1352 | 14.1 | 21.2 | 50.8 | 40,549 | 0.0% |
| express-rest | Node.js | F2 | 8559 | 4.4 | 8.6 | 12.0 | 256,765 | 0.0% |
| express-orm | Node.js | F2 | 3093 | 12.7 | 18.3 | 19.1 | 92,781 | 0.0% |
| express-graphql | Node.js | F2 | 3715 | 10.5 | 13.8 | 15.9 | 111,444 | 0.0% |
| graphql-yoga | Node.js | F2 | 6941 | 5.4 | 8.9 | 13.6 | 208,226 | 0.0% |
| mercurius | Node.js | F2 | 5871 | 4.7 | 7.3 | 10.6 | 176,136 | 0.0% |
| strawberry | Python | F2 | 648 | 60.1 | 76.8 | 81.3 | 19,434 | 0.0% |
| graphene | Python | F2 | 743 | 51.9 | 65.7 | 69.0 | 22,279 | 0.0% |
| fastapi-rest | Python | F2 | 3406 | 11.7 | 13.2 | 19.3 | 102,169 | 0.0% |
| flask-rest | Python | F2 | 266 | 155.3 | 224.6 | 271.9 | 7,972 | 0.0% |
| ariadne | Python | F2 | 771 | 51.2 | 60.8 | 63.3 | 23,136 | 0.0% |
| asgi-graphql | Python | F2 | 436 | 50.5 | 62.7 | 82.6 | 13,087 | 0.2% |
| spring-boot | Java | F2 | 5227 | 6.0 | 18.0 | 27.8 | 156,823 | 0.0% |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | 3511 | 8.3 | 29.3 | 46.6 | 105,322 | 0.0% |
| php-laravel | PHP | F2 | 347 | 78.5 | 92.0 | 168.2 | 10,422 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 4072 | 6.9 | 10.9 | 13.9 | 122,156 | 0.0% |
| csharp-dotnet | C# | F2 | 6664 | 5.4 | 11.6 | 15.4 | 199,917 | 0.0% |
| fraiseql-tv | Python | F2 | 1128 | 31.3 | 67.7 | 89.3 | 33,845 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 1163 | 30.4 | 66.0 | 88.5 | 34,888 | 0.0% |
| fraiseql-v | Python | F2 | 921 | 40.9 | 64.2 | 76.9 | 27,624 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 2178 | 17.6 | 30.3 | 37.2 | 65,326 | 0.0% |
| juniper | Rust | Q3 | 1496 | 23.6 | 26.8 | 29.1 | 44,878 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| quarkus-graphql | Java | Q3 | 3696 | 6.5 | 11.4 | 14.4 | 110,889 | 0.0% |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 147 | 234.8 | 441.6 | 579.0 | 4,406 | 0.0% |
| fraiseql-v | Python | Q3 | 65 | 550.0 | 877.3 | 1051.2 | 1,957 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 7683 | 4.4 | 11.8 | 17.5 | 230,491 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 8046 | 4.2 | 11.0 | 15.8 | 241,385 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 2804 | 11.1 | 35.6 | 50.4 | 84,111 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 2582 | 12.4 | 37.4 | 52.4 | 77,467 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 12588 | 2.0 | 17.2 | 0.0% |
| spring-boot | Java | 9150 | 3.3 | 17.4 | 0.0% |
| express-rest | Node.js | 7513 | 3.8 | 7.7 | 0.0% |
| ruby-rails | Ruby | 5642 | 5.5 | 26.8 | 0.0% |
| gin-rest | Go | 5586 | 4.5 | 37.2 | 0.0% |
| express-orm | Node.js | 4185 | 9.4 | 14.1 | 0.0% |
| fastapi-rest | Python | 3623 | 11.0 | 15.8 | 0.0% |
| spring-boot-orm | Java | 2523 | 13.5 | 52.5 | 0.0% |
| spring-boot-orm-naive | Java | 2474 | 13.2 | 54.3 | 0.0% |
| php-laravel | PHP | 376 | 69.9 | 321.6 | 0.0% |
| flask-rest | Python | 238 | 171.3 | 306.1 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| mercurius | Node.js | 9008 | 4.0 | 10.7 | 0.0% |
| async-graphql | Rust | 7905 | 4.7 | 12.1 | 0.0% |
| graphql-go | Go | 7576 | 4.3 | 19.3 | 0.0% |
| go-graphql-go | Go | 7045 | 4.6 | 20.8 | 0.0% |
| go-gqlgen | Go | 6442 | 4.3 | 30.1 | 0.0% |
| play-graphql | Scala | 6182 | 5.0 | 26.9 | 0.0% |
| graphql-yoga | Node.js | 5712 | 4.1 | 14.0 | 0.0% |
| express-graphql | Node.js | 4624 | 8.5 | 13.0 | 0.0% |
| apollo-server | Node.js | 4513 | 7.5 | 31.6 | 0.0% |
| webonyx-graphql-php | PHP | 4501 | 6.3 | 27.2 | 0.0% |
| juniper | Rust | 4499 | 8.2 | 19.2 | 0.0% |
| csharp-dotnet | C# | 3338 | 4.6 | 13.8 | 0.0% |
| apollo-orm | Node.js | 2984 | 9.9 | 24.6 | 0.0% |
| quarkus-graphql | Java | 2647 | 12.7 | 48.8 | 0.0% |
| micronaut-graphql | Java | 2515 | 14.9 | 31.4 | 0.0% |
| asgi-graphql | Python | 1118 | 35.8 | 45.8 | 0.0% |
| ariadne | Python | 1100 | 36.6 | 46.1 | 0.0% |
| graphene | Python | 1074 | 36.8 | 49.7 | 0.0% |
| hanami | Ruby | 938 | 7.6 | 634.4 | 0.0% |
| strawberry | Python | 868 | 44.4 | 102.3 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-v | Python | 6513 | 5.6 | 13.8 | 0.0% |
| fraiseql-tv-nocache | Python | 3093 | 9.8 | 48.1 | 0.0% |
| fraiseql-tv | Python | 2917 | 9.6 | 47.7 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 5403 | 6.5 | 10.6 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| actix-web-rest | Rust | rest | 12588 | 2.0 | 17.2 |
| spring-boot | Java | rest | 9150 | 3.3 | 17.4 |
| mercurius | Node.js | graphql | 9008 | 4.0 | 10.7 |
| async-graphql | Rust | graphql | 7905 | 4.7 | 12.1 |
| graphql-go | Go | graphql | 7576 | 4.3 | 19.3 |
| express-rest | Node.js | rest | 7513 | 3.8 | 7.7 |
| go-graphql-go | Go | graphql | 7045 | 4.6 | 20.8 |
| fraiseql-v | Python | graphql-precomputed | 6513 | 5.6 | 13.8 |
| go-gqlgen | Go | graphql | 6442 | 4.3 | 30.1 |
| play-graphql | Scala | graphql | 6182 | 5.0 | 26.9 |
| graphql-yoga | Node.js | graphql | 5712 | 4.1 | 14.0 |
| ruby-rails | Ruby | rest | 5642 | 5.5 | 26.8 |
| gin-rest | Go | rest | 5586 | 4.5 | 37.2 |
| postgraphile | Node.js | graphql-schema-first | 5403 | 6.5 | 10.6 |
| express-graphql | Node.js | graphql | 4624 | 8.5 | 13.0 |
| apollo-server | Node.js | graphql | 4513 | 7.5 | 31.6 |
| webonyx-graphql-php | PHP | graphql | 4501 | 6.3 | 27.2 |
| juniper | Rust | graphql | 4499 | 8.2 | 19.2 |
| express-orm | Node.js | rest | 4185 | 9.4 | 14.1 |
| fastapi-rest | Python | rest | 3623 | 11.0 | 15.8 |
| csharp-dotnet | C# | graphql | 3338 | 4.6 | 13.8 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 3093 | 9.8 | 48.1 |
| apollo-orm | Node.js | graphql | 2984 | 9.9 | 24.6 |
| fraiseql-tv | Python | graphql-precomputed | 2917 | 9.6 | 47.7 |
| quarkus-graphql | Java | graphql | 2647 | 12.7 | 48.8 |
| spring-boot-orm | Java | rest | 2523 | 13.5 | 52.5 |
| micronaut-graphql | Java | graphql | 2515 | 14.9 | 31.4 |
| spring-boot-orm-naive | Java | rest | 2474 | 13.2 | 54.3 |
| asgi-graphql | Python | graphql | 1118 | 35.8 | 45.8 |
| ariadne | Python | graphql | 1100 | 36.6 | 46.1 |
| graphene | Python | graphql | 1074 | 36.8 | 49.7 |
| hanami | Ruby | graphql | 938 | 7.6 | 634.4 |
| strawberry | Python | graphql | 868 | 44.4 | 102.3 |
| php-laravel | PHP | rest | 376 | 69.9 | 321.6 |
| flask-rest | Python | rest | 238 | 171.3 | 306.1 |