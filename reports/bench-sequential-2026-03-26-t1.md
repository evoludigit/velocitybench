# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-26  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 10s per scenario  
**Warmup**: 3s per scenario  
**Cooldown**: 3s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 12595 | 2.3 | 8.6 | 14.1 | 125,947 | 0.0% |
| async-graphql | Rust | Q1 | 6199 | 5.3 | 14.7 | 22.0 | 61,991 | 0.0% |
| juniper | Rust | Q1 | 8514 | 4.7 | 8.1 | 10.1 | 85,135 | 0.0% |
| go-gqlgen | Go | Q1 | 1892 | 18.1 | 46.8 | 61.7 | 18,922 | 0.0% |
| gin-rest | Go | Q1 | 3447 | 7.4 | 34.4 | 56.1 | 34,474 | 0.0% |
| go-graphql-go | Go | Q1 | 851 | 28.7 | 97.7 | 108.3 | 8,510 | 0.0% |
| graphql-go | Go | Q1 | 906 | 24.8 | 95.0 | 106.0 | 9,065 | 0.0% |
| apollo-server | Node.js | Q1 | 4938 | 7.8 | 11.5 | 13.8 | 49,385 | 0.0% |
| apollo-orm | Node.js | Q1 | 3859 | 10.2 | 14.7 | 17.4 | 38,588 | 0.0% |
| express-rest | Node.js | Q1 | 9729 | 4.0 | 5.7 | 7.2 | 97,293 | 0.0% |
| express-orm | Node.js | Q1 | 3837 | 10.3 | 14.6 | 16.6 | 38,366 | 0.0% |
| express-graphql | Node.js | Q1 | 4145 | 9.2 | 13.7 | 16.2 | 41,453 | 0.0% |
| graphql-yoga | Node.js | Q1 | 9437 | 4.1 | 6.0 | 8.4 | 94,371 | 0.0% |
| mercurius | Node.js | Q1 | 9849 | 3.8 | 7.0 | 9.3 | 98,488 | 0.0% |
| postgraphile | Node.js | Q1 | 5406 | 7.2 | 10.6 | 13.5 | 54,057 | 0.0% |
| strawberry | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q1 | 1076 | 37.0 | 47.3 | 49.3 | 10,763 | 0.0% |
| fastapi-rest | Python | Q1 | 3753 | 10.7 | 11.7 | 13.5 | 37,531 | 0.0% |
| flask-rest | Python | Q1 | 240 | 174.2 | 244.7 | 306.0 | 2,403 | 0.0% |
| ariadne | Python | Q1 | 1092 | 36.7 | 44.6 | 48.1 | 10,915 | 0.0% |
| asgi-graphql | Python | Q1 | 1100 | 36.5 | 43.0 | 44.9 | 10,997 | 0.0% |
| spring-boot | Java | Q1 | 548 | 94.3 | 196.3 | 201.4 | 5,484 | 0.0% |
| spring-boot-orm | Java | Q1 | 1159 | 6.2 | 97.2 | 101.6 | 11,586 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 1649 | 8.4 | 86.9 | 100.0 | 16,486 | 0.0% |
| micronaut-graphql | Java | Q1 | 458 | 87.9 | 188.8 | 282.2 | 4,579 | 0.0% |
| quarkus-graphql | Java | Q1 | 4534 | 4.3 | 51.4 | 60.1 | 45,340 | 0.0% |
| play-graphql | Scala | Q1 | 246 | 110.5 | 298.4 | 595.7 | 2,464 | 0.0% |
| ruby-rails | Ruby | Q1 | 737 | 42.3 | 128.6 | 195.5 | 7,370 | 0.0% |
| hanami | Ruby | Q1 | 436 | 23.0 | 773.9 | 828.5 | 4,359 | 0.0% |
| php-laravel | PHP | Q1 | 205 | 198.2 | 262.2 | 283.0 | 2,049 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 729 | 86.0 | 100.1 | 106.1 | 7,289 | 0.0% |
| csharp-dotnet | C# | Q1 | 3573 | 6.0 | 46.4 | 94.2 | 35,726 | 0.0% |
| fraiseql-tv | Python | Q1 | 5249 | 5.8 | 19.6 | 30.8 | 52,488 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 3979 | 7.9 | 24.8 | 35.7 | 39,786 | 0.0% |
| fraiseql-v | Python | Q1 | 8540 | 4.2 | 9.5 | 12.7 | 85,398 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 4203 | 5.8 | 29.2 | 48.5 | 42,031 | 0.0% |
| async-graphql | Rust | Q2 | 2934 | 11.6 | 30.7 | 42.1 | 29,344 | 0.0% |
| juniper | Rust | Q2 | 7757 | 4.2 | 11.6 | 18.8 | 77,573 | 0.0% |
| go-gqlgen | Go | Q2 | 2426 | 14.2 | 36.3 | 49.5 | 24,257 | 0.0% |
| gin-rest | Go | Q2 | 7352 | 3.8 | 15.4 | 25.6 | 73,520 | 0.0% |
| go-graphql-go | Go | Q2 | 1225 | 20.9 | 78.8 | 93.0 | 12,249 | 0.0% |
| graphql-go | Go | Q2 | 1265 | 20.9 | 76.7 | 89.8 | 12,649 | 0.0% |
| apollo-server | Node.js | Q2 | 6810 | 5.7 | 8.4 | 10.0 | 68,105 | 0.0% |
| apollo-orm | Node.js | Q2 | 5012 | 7.8 | 11.4 | 13.3 | 50,120 | 0.0% |
| express-rest | Node.js | Q2 | 10354 | 3.7 | 5.9 | 8.5 | 103,544 | 0.0% |
| express-orm | Node.js | Q2 | 4648 | 8.5 | 12.0 | 13.5 | 46,478 | 0.0% |
| express-graphql | Node.js | Q2 | 4642 | 8.3 | 12.3 | 14.8 | 46,421 | 0.0% |
| graphql-yoga | Node.js | Q2 | 10206 | 3.6 | 7.0 | 9.2 | 102,057 | 0.0% |
| mercurius | Node.js | Q2 | 9242 | 3.9 | 8.2 | 10.6 | 92,424 | 0.0% |
| postgraphile | Node.js | Q2 | 6191 | 6.3 | 8.9 | 11.3 | 61,912 | 0.0% |
| strawberry | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q2 | 1243 | 31.7 | 41.7 | 44.2 | 12,433 | 0.0% |
| fastapi-rest | Python | Q2 | 3586 | 11.0 | 13.2 | 19.3 | 35,861 | 0.0% |
| flask-rest | Python | Q2 | 337 | 121.3 | 179.1 | 218.8 | 3,368 | 0.0% |
| ariadne | Python | Q2 | 1281 | 31.1 | 38.3 | 40.2 | 12,808 | 0.0% |
| asgi-graphql | Python | Q2 | 1298 | 30.6 | 37.4 | 40.8 | 12,982 | 0.0% |
| spring-boot | Java | Q2 | 1014 | 8.7 | 96.1 | 101.8 | 10,136 | 0.0% |
| spring-boot-orm | Java | Q2 | 123 | 234.9 | 806.3 | 1175.8 | 1,228 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 2938 | 9.4 | 41.3 | 64.8 | 29,385 | 0.0% |
| micronaut-graphql | Java | Q2 | 954 | 22.0 | 90.1 | 97.9 | 9,540 | 0.0% |
| quarkus-graphql | Java | Q2 | 2966 | 11.4 | 31.6 | 43.0 | 29,663 | 0.0% |
| play-graphql | Scala | Q2 | 511 | 96.7 | 105.0 | 208.6 | 5,106 | 0.0% |
| ruby-rails | Ruby | Q2 | 497 | 79.8 | 186.1 | 263.2 | 4,972 | 0.0% |
| hanami | Ruby | Q2 | 570 | 17.1 | 589.2 | 628.2 | 5,701 | 0.0% |
| php-laravel | PHP | Q2 | 191 | 206.0 | 270.2 | 282.4 | 1,906 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 784 | 80.5 | 99.9 | 106.1 | 7,835 | 0.0% |
| csharp-dotnet | C# | Q2 | 7631 | 4.5 | 9.5 | 16.3 | 76,307 | 0.0% |
| fraiseql-tv | Python | Q2 | 2396 | 14.6 | 35.2 | 48.3 | 23,956 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 2378 | 14.6 | 36.2 | 49.2 | 23,784 | 0.0% |
| fraiseql-v | Python | Q2 | 5953 | 5.6 | 15.3 | 22.8 | 59,527 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 9878 | 3.0 | 10.4 | 17.0 | 98,780 | 0.0% |
| async-graphql | Rust | Q2b | 7439 | 4.8 | 9.7 | 13.8 | 74,389 | 0.0% |
| juniper | Rust | Q2b | 4708 | 7.6 | 14.9 | 20.1 | 47,085 | 0.0% |
| go-gqlgen | Go | Q2b | 1609 | 20.5 | 54.1 | 69.1 | 16,089 | 0.0% |
| gin-rest | Go | Q2b | 1314 | 22.9 | 74.6 | 96.6 | 13,135 | 0.0% |
| go-graphql-go | Go | Q2b | 889 | 27.0 | 96.6 | 108.3 | 8,887 | 0.0% |
| graphql-go | Go | Q2b | 894 | 26.4 | 95.4 | 108.1 | 8,937 | 0.0% |
| apollo-server | Node.js | Q2b | 3672 | 10.4 | 15.5 | 18.0 | 36,715 | 0.0% |
| apollo-orm | Node.js | Q2b | 2644 | 14.8 | 20.3 | 22.9 | 26,443 | 0.0% |
| express-rest | Node.js | Q2b | 7940 | 4.6 | 6.6 | 8.5 | 79,402 | 0.0% |
| express-orm | Node.js | Q2b | 2930 | 13.5 | 19.3 | 21.1 | 29,300 | 0.0% |
| express-graphql | Node.js | Q2b | 3033 | 12.5 | 17.5 | 20.3 | 30,330 | 0.0% |
| graphql-yoga | Node.js | Q2b | 5685 | 6.8 | 9.7 | 12.0 | 56,853 | 0.0% |
| mercurius | Node.js | Q2b | 6617 | 5.7 | 9.2 | 12.4 | 66,168 | 0.0% |
| postgraphile | Node.js | Q2b | 4578 | 8.5 | 12.6 | 14.9 | 45,776 | 0.0% |
| strawberry | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q2b | 814 | 48.3 | 61.0 | 62.7 | 8,145 | 0.0% |
| fastapi-rest | Python | Q2b | 3447 | 11.6 | 12.8 | 18.0 | 34,467 | 0.0% |
| flask-rest | Python | Q2b | 264 | 152.5 | 232.8 | 283.6 | 2,636 | 0.0% |
| ariadne | Python | Q2b | 822 | 48.2 | 57.4 | 59.1 | 8,217 | 0.0% |
| asgi-graphql | Python | Q2b | 832 | 47.6 | 56.3 | 58.6 | 8,316 | 0.0% |
| spring-boot | Java | Q2b | 917 | 10.4 | 97.4 | 102.4 | 9,172 | 0.0% |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | 470 | 89.0 | 173.8 | 195.8 | 4,701 | 0.0% |
| quarkus-graphql | Java | Q2b | 5372 | 5.7 | 21.5 | 28.7 | 53,718 | 0.0% |
| play-graphql | Scala | Q2b | 554 | 95.8 | 105.2 | 198.8 | 5,539 | 0.0% |
| ruby-rails | Ruby | Q2b | 481 | 82.0 | 189.5 | 266.9 | 4,806 | 0.0% |
| hanami | Ruby | Q2b | 340 | 29.9 | 965.6 | 1046.1 | 3,396 | 0.0% |
| php-laravel | PHP | Q2b | 195 | 204.1 | 277.5 | 292.0 | 1,949 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 731 | 88.3 | 99.6 | 189.2 | 7,311 | 0.0% |
| csharp-dotnet | C# | Q2b | 7275 | 4.6 | 10.1 | 20.8 | 72,753 | 0.0% |
| fraiseql-tv | Python | Q2b | 5502 | 5.7 | 17.5 | 26.9 | 55,018 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 3256 | 9.9 | 29.2 | 41.9 | 32,558 | 0.0% |
| fraiseql-v | Python | Q2b | 5757 | 6.2 | 13.7 | 18.1 | 57,573 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1529 | 26.1 | 28.8 | 30.5 | 15,287 | 0.0% |
| async-graphql | Rust | M1 | 1981 | 17.0 | 40.3 | 57.6 | 19,812 | 0.0% |
| juniper | Rust | M1 | 1985 | 12.4 | 65.9 | 103.7 | 19,853 | 0.0% |
| go-gqlgen | Go | M1 | 813 | 33.6 | 149.5 | 229.5 | 8,126 | 0.0% |
| gin-rest | Go | M1 | 727 | 33.0 | 191.2 | 294.3 | 7,266 | 0.0% |
| go-graphql-go | Go | M1 | 1687 | 16.6 | 61.9 | 75.2 | 16,874 | 0.0% |
| graphql-go | Go | M1 | 1259 | 21.6 | 75.8 | 92.1 | 12,588 | 0.0% |
| apollo-server | Node.js | M1 | 2227 | 11.9 | 55.3 | 86.5 | 22,268 | 0.0% |
| express-graphql | Node.js | M1 | 2188 | 12.3 | 55.2 | 85.7 | 21,875 | 0.0% |
| graphql-yoga | Node.js | M1 | 749 | 34.1 | 167.9 | 267.0 | 7,493 | 0.0% |
| mercurius | Node.js | M1 | 1833 | 13.9 | 69.1 | 106.9 | 18,334 | 0.0% |
| strawberry | Python | M1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | M1 | 1186 | 33.3 | 44.4 | 47.1 | 11,863 | 0.0% |
| fastapi-rest | Python | M1 | 2190 | 12.4 | 54.8 | 85.3 | 21,900 | 0.0% |
| spring-boot | Java | M1 | 377 | 84.8 | 322.3 | 514.2 | 3,773 | 0.0% |
| spring-boot-orm | Java | M1 | 979 | 18.2 | 161.0 | 297.4 | 9,788 | 0.0% |
| micronaut-graphql | Java | M1 | 2100 | 17.4 | 34.7 | 39.1 | 21,001 | 0.0% |
| quarkus-graphql | Java | M1 | 1860 | 21.4 | 22.1 | 25.4 | 18,604 | 0.0% |
| play-graphql | Scala | M1 | 1436 | 19.2 | 83.0 | 121.8 | 14,359 | 0.0% |
| ruby-rails | Ruby | M1 | 747 | 33.5 | 153.5 | 204.4 | 7,470 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 528 | 86.8 | 184.5 | 199.2 | 5,285 | 0.0% |
| csharp-dotnet | C# | M1 | 2122 | 11.8 | 62.1 | 94.9 | 21,225 | 0.0% |
| fraiseql-tv | Python | M1 | 1733 | 12.9 | 80.3 | 127.2 | 17,329 | 0.0% |
| fraiseql-tv-nocache | Python | M1 | 1701 | 13.3 | 80.4 | 128.1 | 17,010 | 0.0% |
| fraiseql-v | Python | M1 | 625 | 37.8 | 213.5 | 374.9 | 6,250 | 0.0% |
| fraiseql-tv-audit | Python | M1 | 165 | 173.8 | 707.0 | 1091.6 | 1,651 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 4817 | 5.0 | 25.5 | 43.7 | 48,167 | 0.0% |
| async-graphql | Rust | F1 | 3146 | 10.6 | 29.6 | 41.3 | 31,455 | 0.0% |
| juniper | Rust | F1 | 6839 | 4.8 | 13.5 | 21.0 | 68,391 | 0.0% |
| go-gqlgen | Go | F1 | 2473 | 13.8 | 35.5 | 48.8 | 24,729 | 0.0% |
| gin-rest | Go | F1 | 8347 | 3.2 | 14.1 | 24.3 | 83,466 | 0.0% |
| go-graphql-go | Go | F1 | 1187 | 21.8 | 79.5 | 93.8 | 11,874 | 0.0% |
| graphql-go | Go | F1 | 1223 | 21.6 | 77.1 | 90.9 | 12,232 | 0.0% |
| apollo-server | Node.js | F1 | 6644 | 5.8 | 8.7 | 10.8 | 66,437 | 0.0% |
| apollo-orm | Node.js | F1 | 4834 | 8.0 | 11.9 | 14.4 | 48,339 | 0.0% |
| express-rest | Node.js | F1 | 10394 | 3.7 | 5.8 | 7.9 | 103,936 | 0.0% |
| express-orm | Node.js | F1 | 4657 | 8.5 | 12.0 | 13.2 | 46,568 | 0.0% |
| express-graphql | Node.js | F1 | 4744 | 8.1 | 12.0 | 13.5 | 47,439 | 0.0% |
| graphql-yoga | Node.js | F1 | 9528 | 3.8 | 8.1 | 10.2 | 95,279 | 0.0% |
| mercurius | Node.js | F1 | 9112 | 4.0 | 8.2 | 10.3 | 91,124 | 0.0% |
| strawberry | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | F1 | 1140 | 34.5 | 45.6 | 47.5 | 11,403 | 0.0% |
| fastapi-rest | Python | F1 | 3594 | 11.1 | 12.2 | 15.9 | 35,937 | 0.0% |
| flask-rest | Python | F1 | 327 | 125.5 | 182.0 | 219.2 | 3,270 | 0.0% |
| ariadne | Python | F1 | 1164 | 34.0 | 42.0 | 43.8 | 11,643 | 0.0% |
| asgi-graphql | Python | F1 | 1175 | 33.8 | 41.0 | 43.6 | 11,746 | 0.0% |
| spring-boot | Java | F1 | 1202 | 10.0 | 91.1 | 103.2 | 12,020 | 0.0% |
| spring-boot-orm | Java | F1 | 516 | 73.3 | 147.7 | 183.4 | 5,162 | 0.0% |
| ruby-rails | Ruby | F1 | 481 | 80.9 | 190.7 | 295.1 | 4,811 | 0.0% |
| php-laravel | PHP | F1 | 184 | 209.7 | 283.7 | 295.1 | 1,844 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 772 | 82.3 | 99.7 | 105.4 | 7,718 | 0.0% |
| csharp-dotnet | C# | F1 | 6618 | 4.7 | 11.1 | 50.8 | 66,181 | 0.0% |
| fraiseql-tv | Python | F1 | 2663 | 12.8 | 33.8 | 46.5 | 26,634 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 2579 | 13.3 | 33.9 | 45.5 | 25,788 | 0.0% |
| fraiseql-v | Python | F1 | 5980 | 5.6 | 14.9 | 21.4 | 59,799 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 9718 | 3.4 | 9.4 | 14.4 | 97,176 | 0.0% |
| async-graphql | Rust | F2 | 7755 | 4.6 | 9.1 | 14.6 | 77,548 | 0.0% |
| juniper | Rust | F2 | 4657 | 7.8 | 13.6 | 21.1 | 46,572 | 0.0% |
| go-gqlgen | Go | F2 | 1652 | 20.4 | 52.4 | 67.6 | 16,517 | 0.0% |
| gin-rest | Go | F2 | 1349 | 21.6 | 72.8 | 93.7 | 13,488 | 0.0% |
| go-graphql-go | Go | F2 | 902 | 26.6 | 94.3 | 105.9 | 9,025 | 0.0% |
| graphql-go | Go | F2 | 899 | 25.2 | 96.8 | 108.7 | 8,988 | 0.0% |
| apollo-server | Node.js | F2 | 3675 | 10.5 | 15.2 | 17.6 | 36,753 | 0.0% |
| apollo-orm | Node.js | F2 | 2431 | 16.2 | 22.0 | 25.2 | 24,307 | 0.0% |
| express-rest | Node.js | F2 | 8642 | 4.6 | 6.8 | 9.5 | 86,419 | 0.0% |
| express-orm | Node.js | F2 | 2854 | 13.8 | 19.8 | 21.9 | 28,544 | 0.0% |
| express-graphql | Node.js | F2 | 3181 | 12.0 | 16.7 | 19.2 | 31,812 | 0.0% |
| graphql-yoga | Node.js | F2 | 6111 | 6.2 | 9.5 | 12.3 | 61,113 | 0.0% |
| mercurius | Node.js | F2 | 6545 | 5.8 | 9.0 | 11.0 | 65,453 | 0.0% |
| strawberry | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | F2 | 764 | 51.4 | 64.5 | 66.8 | 7,644 | 0.0% |
| fastapi-rest | Python | F2 | 3525 | 11.3 | 12.5 | 14.1 | 35,253 | 0.0% |
| flask-rest | Python | F2 | 262 | 155.8 | 226.6 | 273.9 | 2,622 | 0.0% |
| ariadne | Python | F2 | 778 | 50.8 | 60.4 | 62.6 | 7,778 | 0.0% |
| asgi-graphql | Python | F2 | 781 | 50.6 | 59.5 | 61.2 | 7,813 | 0.0% |
| spring-boot | Java | F2 | 1261 | 21.6 | 83.3 | 96.0 | 12,613 | 0.0% |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | 464 | 83.8 | 191.1 | 266.0 | 4,642 | 0.0% |
| php-laravel | PHP | F2 | 189 | 208.8 | 277.3 | 287.3 | 1,887 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 711 | 90.3 | 99.6 | 113.4 | 7,107 | 0.0% |
| csharp-dotnet | C# | F2 | 7555 | 4.8 | 9.6 | 13.4 | 75,550 | 0.0% |
| fraiseql-tv | Python | F2 | 3755 | 8.0 | 27.5 | 40.0 | 37,554 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 3958 | 7.9 | 25.1 | 37.2 | 39,580 | 0.0% |
| fraiseql-v | Python | F2 | 5770 | 6.2 | 13.6 | 18.1 | 57,700 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| async-graphql | Rust | T1 | 7593 | 5.1 | 7.3 | 8.6 | 75,929 | 0.0% |
| juniper | Rust | T1 | 3891 | 9.3 | 17.6 | 24.2 | 38,907 | 0.0% |
| go-gqlgen | Go | T1 | 3443 | 9.7 | 25.7 | 35.3 | 34,430 | 0.0% |
| gin-rest | Go | T1 | 1014 | 34.6 | 81.9 | 113.3 | 10,136 | 0.0% |
| go-graphql-go | Go | T1 | 180 | 222.6 | 233.2 | 246.3 | 1,800 | 0.0% |
| graphql-go | Go | T1 | 982 | 22.7 | 88.8 | 99.2 | 9,820 | 0.0% |
| apollo-server | Node.js | T1 | 2730 | 13.9 | 19.4 | 23.0 | 27,296 | 0.0% |
| apollo-orm | Node.js | T1 | 1925 | 19.8 | 27.2 | 29.9 | 19,253 | 0.0% |
| express-rest | Node.js | T1 | 3230 | 11.7 | 19.7 | 25.7 | 32,299 | 0.0% |
| express-orm | Node.js | T1 | 3716 | 10.3 | 13.9 | 15.5 | 37,164 | 0.0% |
| express-graphql | Node.js | T1 | 2415 | 15.6 | 20.5 | 23.3 | 24,154 | 0.0% |
| graphql-yoga | Node.js | T1 | 3970 | 9.4 | 15.0 | 20.5 | 39,700 | 0.0% |
| mercurius | Node.js | T1 | 4563 | 8.3 | 12.4 | 15.3 | 45,633 | 0.0% |
| postgraphile | Node.js | T1 | — | — | — | — | — | _known bug — skipped_ |
| strawberry | Python | T1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | T1 | 708 | 54.5 | 69.5 | 82.8 | 7,080 | 0.0% |
| fastapi-rest | Python | T1 | 1811 | 22.3 | 23.3 | 24.2 | 18,107 | 0.0% |
| flask-rest | Python | T1 | 114 | 365.1 | 465.3 | 744.0 | 1,135 | 0.0% |
| ariadne | Python | T1 | 578 | 68.3 | 79.8 | 82.3 | 5,783 | 0.0% |
| asgi-graphql | Python | T1 | 582 | 68.1 | 78.7 | 80.9 | 5,820 | 0.0% |
| spring-boot | Java | T1 | 636 | 81.2 | 112.6 | 181.5 | 6,359 | 0.0% |
| spring-boot-orm | Java | T1 | — | — | — | — | — | _known bug — skipped_ |
| spring-boot-orm-naive | Java | T1 | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | T1 | 457 | 89.9 | 172.3 | 199.1 | 4,568 | 0.0% |
| quarkus-graphql | Java | T1 | 5091 | 6.5 | 18.2 | 25.9 | 50,914 | 0.0% |
| play-graphql | Scala | T1 | 869 | 23.4 | 98.5 | 110.2 | 8,689 | 0.0% |
| ruby-rails | Ruby | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| hanami | Ruby | T1 | 264 | 41.0 | 1268.8 | 1401.7 | 2,643 | 0.0% |
| php-laravel | PHP | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| webonyx-graphql-php | PHP | T1 | 613 | 93.3 | 100.8 | 189.6 | 6,133 | 0.0% |
| csharp-dotnet | C# | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Python | T1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | T1 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-v | Python | T1 | — | — | — | — | — | _known bug — skipped_ |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 5437 | 7.1 | 11.8 | 14.1 | 54,368 | 0.0% |
| juniper | Rust | Q3 | 1044 | 32.9 | 68.5 | 78.8 | 10,436 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| quarkus-graphql | Java | Q3 | 2129 | 16.7 | 33.4 | 41.1 | 21,289 | 0.0% |
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 10658 | 3.4 | 7.4 | 9.9 | 106,575 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 10624 | 3.4 | 7.3 | 9.7 | 106,241 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 4845 | 6.1 | 21.7 | 32.9 | 48,448 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 6024 | 5.0 | 16.9 | 27.1 | 60,240 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 12595 | 2.3 | 14.1 | 0.0% |
| express-rest | Node.js | 9729 | 4.0 | 7.2 | 0.0% |
| express-orm | Node.js | 3837 | 10.3 | 16.6 | 0.0% |
| fastapi-rest | Python | 3753 | 10.7 | 13.5 | 0.0% |
| gin-rest | Go | 3447 | 7.4 | 56.1 | 0.0% |
| spring-boot-orm-naive | Java | 1649 | 8.4 | 100.0 | 0.0% |
| spring-boot-orm | Java | 1159 | 6.2 | 101.6 | 0.0% |
| ruby-rails | Ruby | 737 | 42.3 | 195.5 | 0.0% |
| spring-boot | Java | 548 | 94.3 | 201.4 | 0.0% |
| flask-rest | Python | 240 | 174.2 | 306.0 | 0.0% |
| php-laravel | PHP | 205 | 198.2 | 283.0 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| mercurius | Node.js | 9849 | 3.8 | 9.3 | 0.0% |
| graphql-yoga | Node.js | 9437 | 4.1 | 8.4 | 0.0% |
| juniper | Rust | 8514 | 4.7 | 10.1 | 0.0% |
| async-graphql | Rust | 6199 | 5.3 | 22.0 | 0.0% |
| apollo-server | Node.js | 4938 | 7.8 | 13.8 | 0.0% |
| quarkus-graphql | Java | 4534 | 4.3 | 60.1 | 0.0% |
| express-graphql | Node.js | 4145 | 9.2 | 16.2 | 0.0% |
| apollo-orm | Node.js | 3859 | 10.2 | 17.4 | 0.0% |
| csharp-dotnet | C# | 3573 | 6.0 | 94.2 | 0.0% |
| go-gqlgen | Go | 1892 | 18.1 | 61.7 | 0.0% |
| asgi-graphql | Python | 1100 | 36.5 | 44.9 | 0.0% |
| ariadne | Python | 1092 | 36.7 | 48.1 | 0.0% |
| graphene | Python | 1076 | 37.0 | 49.3 | 0.0% |
| graphql-go | Go | 906 | 24.8 | 106.0 | 0.0% |
| go-graphql-go | Go | 851 | 28.7 | 108.3 | 0.0% |
| webonyx-graphql-php | PHP | 729 | 86.0 | 106.1 | 0.0% |
| micronaut-graphql | Java | 458 | 87.9 | 282.2 | 0.0% |
| hanami | Ruby | 436 | 23.0 | 828.5 | 0.0% |
| play-graphql | Scala | 246 | 110.5 | 595.7 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-v | Python | 8540 | 4.2 | 12.7 | 0.0% |
| fraiseql-tv | Python | 5249 | 5.8 | 30.8 | 0.0% |
| fraiseql-tv-nocache | Python | 3979 | 7.9 | 35.7 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 5406 | 7.2 | 13.5 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| actix-web-rest | Rust | rest | 12595 | 2.3 | 14.1 |
| mercurius | Node.js | graphql | 9849 | 3.8 | 9.3 |
| express-rest | Node.js | rest | 9729 | 4.0 | 7.2 |
| graphql-yoga | Node.js | graphql | 9437 | 4.1 | 8.4 |
| fraiseql-v | Python | graphql-precomputed | 8540 | 4.2 | 12.7 |
| juniper | Rust | graphql | 8514 | 4.7 | 10.1 |
| async-graphql | Rust | graphql | 6199 | 5.3 | 22.0 |
| postgraphile | Node.js | graphql-schema-first | 5406 | 7.2 | 13.5 |
| fraiseql-tv | Python | graphql-precomputed | 5249 | 5.8 | 30.8 |
| apollo-server | Node.js | graphql | 4938 | 7.8 | 13.8 |
| quarkus-graphql | Java | graphql | 4534 | 4.3 | 60.1 |
| express-graphql | Node.js | graphql | 4145 | 9.2 | 16.2 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 3979 | 7.9 | 35.7 |
| apollo-orm | Node.js | graphql | 3859 | 10.2 | 17.4 |
| express-orm | Node.js | rest | 3837 | 10.3 | 16.6 |
| fastapi-rest | Python | rest | 3753 | 10.7 | 13.5 |
| csharp-dotnet | C# | graphql | 3573 | 6.0 | 94.2 |
| gin-rest | Go | rest | 3447 | 7.4 | 56.1 |
| go-gqlgen | Go | graphql | 1892 | 18.1 | 61.7 |
| spring-boot-orm-naive | Java | rest | 1649 | 8.4 | 100.0 |
| spring-boot-orm | Java | rest | 1159 | 6.2 | 101.6 |
| asgi-graphql | Python | graphql | 1100 | 36.5 | 44.9 |
| ariadne | Python | graphql | 1092 | 36.7 | 48.1 |
| graphene | Python | graphql | 1076 | 37.0 | 49.3 |
| graphql-go | Go | graphql | 906 | 24.8 | 106.0 |
| go-graphql-go | Go | graphql | 851 | 28.7 | 108.3 |
| ruby-rails | Ruby | rest | 737 | 42.3 | 195.5 |
| webonyx-graphql-php | PHP | graphql | 729 | 86.0 | 106.1 |
| spring-boot | Java | rest | 548 | 94.3 | 201.4 |
| micronaut-graphql | Java | graphql | 458 | 87.9 | 282.2 |
| hanami | Ruby | graphql | 436 | 23.0 | 828.5 |
| play-graphql | Scala | graphql | 246 | 110.5 | 595.7 |
| flask-rest | Python | rest | 240 | 174.2 | 306.0 |
| php-laravel | PHP | rest | 205 | 198.2 | 283.0 |