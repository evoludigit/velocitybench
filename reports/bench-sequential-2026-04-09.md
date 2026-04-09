# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-09  
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
| `tb_mutation_log` | 3.38 GB | 289.3 MB | 3.67 GB |
| `tv_comment` | 819.5 MB | 354.7 MB | 1.91 GB |
| `tvd_comment` | 477.6 MB | 51.4 MB | 1.13 GB |
| `tb_comment` | 294.6 MB | 82.2 MB | 376.9 MB |
| `tv_post` | 219.3 MB | 78.6 MB | 351.7 MB |
| `tvd_post` | 134.0 MB | 8.5 MB | 191.4 MB |
| `tb_post` | 133.6 MB | 20.0 MB | 153.6 MB |
| `tb_post_like` | 5.0 MB | 9.3 MB | 14.3 MB |
| `tv_user` | 8.2 MB | 6.0 MB | 14.2 MB |
| `tb_user` | 6.2 MB | 3.5 MB | 9.7 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `tvd_user` | 5.5 MB | 0.7 MB | 6.2 MB |

**TV tables**: 2.26 GB  
**TB tables (normalized baseline)**: 4.21 GB  
**Storage amplification**: 1.54× (TV adds 2.26 GB on top of the normalized 4.21 GB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 1875 | 21.0 | 23.5 | 24.7 | 37,508 | 0.0% |
| async-graphql | Rust | Q1 | 10682 | 3.5 | 6.8 | 8.8 | 213,648 | 0.0% |
| juniper | Rust | Q1 | 829 | 15.6 | 99.5 | 106.0 | 16,573 | 0.0% |
| go-gqlgen | Go | Q1 | 1115 | 6.6 | 94.7 | 104.0 | 22,294 | 0.0% |
| gin-rest | Go | Q1 | 1241 | 5.8 | 92.9 | 99.5 | 24,826 | 0.0% |
| go-graphql-go | Go | Q1 | 790 | 64.9 | 100.3 | 110.9 | 15,803 | 0.0% |
| graphql-go | Go | Q1 | 1123 | 7.1 | 94.1 | 100.3 | 22,459 | 0.0% |
| apollo-server | Node.js | Q1 | 988 | 24.4 | 87.6 | 98.5 | 19,761 | 0.0% |
| apollo-orm | Node.js | Q1 | 901 | 29.6 | 89.5 | 101.3 | 18,016 | 0.0% |
| express-rest | Node.js | Q1 | 800 | 35.3 | 97.4 | 106.1 | 15,997 | 0.0% |
| express-orm | Node.js | Q1 | 958 | 27.0 | 85.2 | 95.8 | 19,163 | 0.0% |
| express-graphql | Node.js | Q1 | 3984 | 9.6 | 14.2 | 16.3 | 79,672 | 0.0% |
| graphql-yoga | Node.js | Q1 | 9339 | 4.2 | 5.9 | 7.0 | 186,776 | 0.0% |
| mercurius | Node.js | Q1 | 9814 | 3.9 | 6.7 | 9.2 | 196,290 | 0.0% |
| postgraphile | Node.js | Q1 | 5249 | 7.4 | 10.8 | 13.0 | 104,983 | 0.0% |
| strawberry | Python | Q1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q1 | 1073 | 36.4 | 47.2 | 48.9 | 21,466 | 0.0% |
| fastapi-rest | Python | Q1 | 1325 | 17.0 | 79.3 | 89.4 | 26,494 | 0.0% |
| flask-rest | Python | Q1 | 274 | 148.2 | 222.0 | 254.7 | 5,474 | 0.0% |
| ariadne | Python | Q1 | 1108 | 35.5 | 43.2 | 45.6 | 22,169 | 0.0% |
| asgi-graphql | Python | Q1 | 1129 | 34.8 | 41.8 | 43.9 | 22,581 | 0.0% |
| spring-boot | Java | Q1 | 620 | 93.5 | 110.5 | 199.6 | 12,410 | 0.0% |
| spring-boot-orm | Java | Q1 | 1089 | 9.3 | 97.2 | 105.6 | 21,780 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 661 | 81.3 | 99.1 | 173.3 | 13,212 | 0.0% |
| micronaut-graphql | Java | Q1 | 555 | 79.2 | 124.0 | 187.5 | 11,093 | 0.0% |
| quarkus-graphql | Java | Q1 | 7862 | 3.4 | 9.5 | 51.5 | 157,246 | 0.0% |
| play-graphql | Scala | Q1 | 407 | 98.6 | 200.5 | 297.4 | 8,141 | 0.0% |
| ruby-rails | Ruby | Q1 | 741 | 45.4 | 120.9 | 190.9 | 14,824 | 0.0% |
| hanami | Ruby | Q1 | 475 | 21.3 | 693.5 | 808.6 | 9,496 | 0.0% |
| php-laravel | PHP | Q1 | 208 | 195.3 | 261.8 | 277.4 | 4,152 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 794 | 82.9 | 98.8 | 102.2 | 15,887 | 0.0% |
| csharp-dotnet | C# | Q1 | 6873 | 4.1 | 11.7 | 62.4 | 137,458 | 0.0% |
| fraiseql-tv | Rust | Q1 | 10942 | 3.3 | 7.3 | 9.8 | 218,839 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 9120 | 3.9 | 8.6 | 11.6 | 182,410 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 8821 | 4.0 | 9.0 | 12.1 | 176,422 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 10948 | 3.3 | 7.3 | 9.8 | 218,957 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 13304 | 2.0 | 8.7 | 15.0 | 266,076 | 0.0% |
| async-graphql | Rust | Q2 | 10603 | 3.4 | 7.3 | 10.2 | 212,059 | 0.0% |
| juniper | Rust | Q2 | 10851 | 3.5 | 6.3 | 8.1 | 217,011 | 0.0% |
| go-gqlgen | Go | Q2 | 2330 | 14.2 | 39.9 | 51.9 | 46,609 | 0.0% |
| gin-rest | Go | Q2 | 9434 | 3.5 | 9.4 | 13.9 | 188,675 | 0.0% |
| go-graphql-go | Go | Q2 | 1045 | 20.8 | 88.4 | 100.8 | 20,892 | 0.0% |
| graphql-go | Go | Q2 | 1089 | 20.9 | 86.1 | 98.2 | 21,778 | 0.0% |
| apollo-server | Node.js | Q2 | 6086 | 6.3 | 9.5 | 11.5 | 121,719 | 0.0% |
| apollo-orm | Node.js | Q2 | 4428 | 8.6 | 13.6 | 15.7 | 88,565 | 0.0% |
| express-rest | Node.js | Q2 | 7558 | 5.2 | 7.4 | 8.8 | 151,152 | 0.0% |
| express-orm | Node.js | Q2 | 3743 | 10.6 | 14.7 | 16.7 | 74,865 | 0.0% |
| express-graphql | Node.js | Q2 | 4233 | 9.0 | 13.4 | 15.0 | 84,651 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9861 | 3.9 | 5.8 | 8.5 | 197,218 | 0.0% |
| mercurius | Node.js | Q2 | 10506 | 3.6 | 6.4 | 8.6 | 210,113 | 0.0% |
| postgraphile | Node.js | Q2 | 6022 | 6.4 | 9.5 | 11.9 | 120,444 | 0.0% |
| strawberry | Python | Q2 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q2 | 1234 | 31.4 | 42.5 | 45.9 | 24,684 | 0.0% |
| fastapi-rest | Python | Q2 | 2740 | 14.6 | 16.0 | 19.6 | 54,809 | 0.0% |
| flask-rest | Python | Q2 | 322 | 128.0 | 192.1 | 225.8 | 6,442 | 0.0% |
| ariadne | Python | Q2 | 1286 | 30.1 | 38.2 | 42.5 | 25,719 | 0.0% |
| asgi-graphql | Python | Q2 | 1270 | 30.7 | 38.1 | 42.2 | 25,407 | 0.0% |
| spring-boot | Java | Q2 | 57 | 691.8 | 1205.8 | 1587.2 | 1,138 | 0.0% |
| spring-boot-orm | Java | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| spring-boot-orm-naive | Java | Q2 | 2618 | 12.4 | 37.3 | 55.3 | 52,365 | 0.0% |
| micronaut-graphql | Java | Q2 | 1050 | 20.5 | 81.9 | 91.1 | 20,992 | 0.0% |
| quarkus-graphql | Java | Q2 | 7878 | 3.8 | 13.4 | 23.0 | 157,569 | 0.0% |
| play-graphql | Scala | Q2 | 1189 | 18.8 | 96.1 | 102.2 | 23,779 | 0.0% |
| ruby-rails | Ruby | Q2 | 459 | 82.7 | 197.1 | 286.7 | 9,189 | 0.0% |
| hanami | Ruby | Q2 | 572 | 17.4 | 600.9 | 645.6 | 11,442 | 0.0% |
| php-laravel | PHP | Q2 | 182 | 211.4 | 285.4 | 294.8 | 3,631 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 853 | 13.3 | 98.6 | 103.4 | 17,051 | 0.0% |
| csharp-dotnet | C# | Q2 | 7170 | 4.6 | 9.8 | 35.4 | 143,404 | 0.0% |
| fraiseql-tv | Rust | Q2 | 10986 | 3.1 | 7.4 | 10.2 | 219,713 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 5275 | 6.6 | 16.0 | 21.7 | 105,498 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5245 | 6.7 | 16.2 | 22.0 | 104,896 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 11064 | 3.2 | 7.6 | 10.3 | 221,287 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 8283 | 4.8 | 5.7 | 6.3 | 165,653 | 0.0% |
| async-graphql | Rust | Q2b | 9573 | 4.1 | 6.2 | 7.5 | 191,458 | 0.0% |
| juniper | Rust | Q2b | 4608 | 8.1 | 12.5 | 18.2 | 92,155 | 0.0% |
| go-gqlgen | Go | Q2b | 1503 | 18.7 | 64.0 | 77.4 | 30,057 | 0.0% |
| gin-rest | Go | Q2b | 1031 | 26.5 | 84.1 | 97.6 | 20,621 | 0.0% |
| go-graphql-go | Go | Q2b | 821 | 28.4 | 99.1 | 109.0 | 16,421 | 0.0% |
| graphql-go | Go | Q2b | 858 | 24.0 | 97.7 | 107.4 | 17,157 | 0.0% |
| apollo-server | Node.js | Q2b | 3378 | 11.5 | 16.4 | 19.2 | 67,568 | 0.0% |
| apollo-orm | Node.js | Q2b | 2308 | 17.0 | 23.3 | 26.3 | 46,170 | 0.0% |
| express-rest | Node.js | Q2b | 5909 | 6.7 | 9.8 | 13.0 | 118,188 | 0.0% |
| express-orm | Node.js | Q2b | 2383 | 16.5 | 23.6 | 27.1 | 47,651 | 0.0% |
| express-graphql | Node.js | Q2b | 2809 | 13.6 | 18.5 | 21.5 | 56,178 | 0.0% |
| graphql-yoga | Node.js | Q2b | 4998 | 7.6 | 11.4 | 13.5 | 99,960 | 0.0% |
| mercurius | Node.js | Q2b | 6016 | 6.1 | 10.1 | 13.6 | 120,321 | 0.0% |
| postgraphile | Node.js | Q2b | 4613 | 8.4 | 12.4 | 14.7 | 92,260 | 0.0% |
| strawberry | Python | Q2b | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | Q2b | 790 | 49.5 | 62.9 | 66.1 | 15,802 | 0.0% |
| fastapi-rest | Python | Q2b | 2648 | 15.0 | 17.1 | 20.7 | 52,961 | 0.0% |
| flask-rest | Python | Q2b | 253 | 161.1 | 238.2 | 289.0 | 5,056 | 0.0% |
| ariadne | Python | Q2b | 813 | 48.3 | 57.9 | 64.1 | 16,262 | 0.0% |
| asgi-graphql | Python | Q2b | 781 | 51.2 | 60.9 | 66.3 | 15,628 | 0.0% |
| spring-boot | Java | Q2b | 57 | 696.7 | 1200.6 | 1400.8 | 1,137 | 0.0% |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | Q2b | 667 | 71.0 | 107.5 | 158.0 | 13,334 | 0.0% |
| quarkus-graphql | Java | Q2b | 5811 | 5.7 | 15.4 | 24.0 | 116,225 | 0.0% |
| play-graphql | Scala | Q2b | 940 | 24.6 | 93.6 | 105.7 | 18,804 | 0.0% |
| ruby-rails | Ruby | Q2b | 456 | 83.6 | 196.4 | 288.7 | 9,115 | 0.0% |
| hanami | Ruby | Q2b | 321 | 31.3 | 1012.9 | 1070.7 | 6,427 | 0.0% |
| php-laravel | PHP | Q2b | 183 | 210.3 | 277.5 | 287.7 | 3,654 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 728 | 89.2 | 99.7 | 184.0 | 14,556 | 0.0% |
| csharp-dotnet | C# | Q2b | 7792 | 4.5 | 8.9 | 16.4 | 155,850 | 0.0% |
| fraiseql-tv | Rust | Q2b | 9648 | 3.8 | 7.6 | 10.1 | 192,968 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 4498 | 8.0 | 17.9 | 24.1 | 89,960 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 4490 | 8.0 | 17.9 | 24.0 | 89,793 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9574 | 3.9 | 7.6 | 10.1 | 191,476 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 510 | 68.4 | 146.7 | 156.2 | 10,209 | 0.0% |
| async-graphql | Rust | M1 | 2000 | 16.7 | 40.0 | 57.8 | 39,991 | 0.0% |
| juniper | Rust | M1 | 1994 | 12.5 | 65.7 | 103.8 | 39,877 | 0.0% |
| go-gqlgen | Go | M1 | 690 | 37.2 | 187.5 | 302.2 | 13,791 | 0.0% |
| gin-rest | Go | M1 | 1626 | 16.0 | 78.1 | 120.9 | 32,514 | 0.0% |
| go-graphql-go | Go | M1 | 1629 | 16.0 | 64.5 | 76.8 | 32,589 | 0.0% |
| graphql-go | Go | M1 | 1330 | 19.4 | 82.3 | 99.1 | 26,598 | 0.0% |
| apollo-server | Node.js | M1 | 2187 | 12.3 | 55.9 | 85.7 | 43,742 | 0.0% |
| express-graphql | Node.js | M1 | 2222 | 12.2 | 53.2 | 83.3 | 44,446 | 0.0% |
| graphql-yoga | Node.js | M1 | 2127 | 12.2 | 59.1 | 91.6 | 42,546 | 0.0% |
| mercurius | Node.js | M1 | 746 | 32.5 | 175.0 | 299.3 | 14,927 | 0.0% |
| strawberry | Python | M1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | M1 | 1155 | 34.0 | 45.9 | 48.9 | 23,107 | 0.0% |
| fastapi-rest | Python | M1 | 307 | 55.9 | 525.9 | 902.7 | 6,136 | 0.0% |
| spring-boot | Java | M1 | 316 | 87.4 | 411.4 | 777.5 | 6,322 | 0.0% |
| spring-boot-orm | Java | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| micronaut-graphql | Java | M1 | 2109 | 17.2 | 34.4 | 38.5 | 42,176 | 0.0% |
| quarkus-graphql | Java | M1 | 2077 | 19.1 | 20.8 | 23.1 | 41,537 | 0.0% |
| play-graphql | Scala | M1 | 1984 | 16.6 | 46.4 | 67.9 | 39,677 | 0.0% |
| ruby-rails | Ruby | M1 | 737 | 44.8 | 122.9 | 195.7 | 14,745 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 501 | 90.0 | 189.5 | 202.4 | 10,019 | 0.0% |
| csharp-dotnet | C# | M1 | 2171 | 11.4 | 60.1 | 94.8 | 43,414 | 0.0% |
| fraiseql-tv | Rust | M1 | 1253 | 24.7 | 79.2 | 146.2 | 25,065 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 9152 | 4.0 | 7.6 | 10.0 | 183,044 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 1248 | 24.8 | 80.3 | 142.5 | 24,961 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 2102 | 11.4 | 53.3 | 114.5 | 42,048 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 9126 | 4.0 | 7.6 | 10.1 | 182,528 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 15051 | 1.9 | 7.4 | 12.1 | 301,014 | 0.0% |
| async-graphql | Rust | F1 | 10915 | 3.4 | 6.8 | 9.0 | 218,292 | 0.0% |
| juniper | Rust | F1 | 10904 | 3.4 | 6.6 | 8.6 | 218,077 | 0.0% |
| go-gqlgen | Go | F1 | 2733 | 11.8 | 35.5 | 47.5 | 54,660 | 0.0% |
| gin-rest | Go | F1 | 8855 | 3.8 | 10.1 | 14.7 | 177,101 | 0.0% |
| go-graphql-go | Go | F1 | 1082 | 20.7 | 86.7 | 98.6 | 21,634 | 0.0% |
| graphql-go | Go | F1 | 1077 | 20.6 | 87.6 | 98.8 | 21,541 | 0.0% |
| apollo-server | Node.js | F1 | 6167 | 6.2 | 9.3 | 11.8 | 123,336 | 0.0% |
| apollo-orm | Node.js | F1 | 4256 | 9.0 | 14.1 | 16.3 | 85,126 | 0.0% |
| express-rest | Node.js | F1 | 7814 | 5.0 | 7.3 | 10.0 | 156,275 | 0.0% |
| express-orm | Node.js | F1 | 3760 | 10.5 | 14.7 | 16.8 | 75,209 | 0.0% |
| express-graphql | Node.js | F1 | 4348 | 8.8 | 13.2 | 15.0 | 86,969 | 0.0% |
| graphql-yoga | Node.js | F1 | 10300 | 3.7 | 5.7 | 8.7 | 205,996 | 0.0% |
| mercurius | Node.js | F1 | 10483 | 3.6 | 6.2 | 8.4 | 209,665 | 0.0% |
| strawberry | Python | F1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | F1 | 1116 | 34.5 | 46.5 | 49.6 | 22,324 | 0.0% |
| fastapi-rest | Python | F1 | 3021 | 13.3 | 14.4 | 15.3 | 60,414 | 0.0% |
| flask-rest | Python | F1 | 311 | 131.6 | 189.6 | 225.7 | 6,219 | 0.0% |
| ariadne | Python | F1 | 1170 | 33.0 | 41.8 | 47.7 | 23,407 | 0.0% |
| asgi-graphql | Python | F1 | 1202 | 32.6 | 40.2 | 41.6 | 24,034 | 0.0% |
| spring-boot | Java | F1 | 57 | 691.7 | 1203.5 | 1488.8 | 1,139 | 0.0% |
| spring-boot-orm | Java | F1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| ruby-rails | Ruby | F1 | 454 | 83.8 | 196.6 | 286.6 | 9,087 | 0.0% |
| php-laravel | PHP | F1 | 181 | 212.1 | 283.6 | 295.7 | 3,618 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 848 | 13.0 | 98.8 | 103.7 | 16,967 | 0.0% |
| csharp-dotnet | C# | F1 | 7544 | 4.6 | 9.3 | 20.1 | 150,875 | 0.0% |
| fraiseql-tv | Rust | F1 | 10840 | 3.3 | 7.6 | 10.2 | 216,801 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 2296 | 14.0 | 41.1 | 52.5 | 45,924 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 2103 | 15.3 | 43.8 | 55.2 | 42,063 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 10803 | 3.3 | 7.6 | 10.4 | 216,060 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 9121 | 4.3 | 5.3 | 6.6 | 182,421 | 0.0% |
| async-graphql | Rust | F2 | 9462 | 4.1 | 6.3 | 7.6 | 189,244 | 0.0% |
| juniper | Rust | F2 | 4493 | 8.1 | 13.9 | 20.5 | 89,865 | 0.0% |
| go-gqlgen | Go | F2 | 1604 | 17.7 | 61.5 | 74.5 | 32,078 | 0.0% |
| gin-rest | Go | F2 | 1046 | 26.2 | 83.1 | 97.2 | 20,919 | 0.0% |
| go-graphql-go | Go | F2 | 847 | 24.9 | 98.1 | 107.7 | 16,941 | 0.0% |
| graphql-go | Go | F2 | 882 | 22.6 | 97.4 | 107.7 | 17,648 | 0.0% |
| apollo-server | Node.js | F2 | 3321 | 11.6 | 16.9 | 20.0 | 66,416 | 0.0% |
| apollo-orm | Node.js | F2 | 2293 | 17.0 | 23.5 | 26.9 | 45,861 | 0.0% |
| express-rest | Node.js | F2 | 6566 | 6.1 | 8.0 | 9.8 | 131,311 | 0.0% |
| express-orm | Node.js | F2 | 2421 | 16.2 | 23.2 | 26.7 | 48,429 | 0.0% |
| express-graphql | Node.js | F2 | 2904 | 13.1 | 18.2 | 21.0 | 58,072 | 0.0% |
| graphql-yoga | Node.js | F2 | 5370 | 7.0 | 10.9 | 13.6 | 107,392 | 0.0% |
| mercurius | Node.js | F2 | 5842 | 6.4 | 10.3 | 13.5 | 116,831 | 0.0% |
| strawberry | Python | F2 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | F2 | 748 | 51.7 | 66.2 | 72.9 | 14,969 | 0.0% |
| fastapi-rest | Python | F2 | 2839 | 14.1 | 15.7 | 19.6 | 56,784 | 0.0% |
| flask-rest | Python | F2 | 254 | 159.6 | 239.4 | 294.6 | 5,076 | 0.0% |
| ariadne | Python | F2 | 782 | 50.5 | 60.3 | 62.5 | 15,643 | 0.0% |
| asgi-graphql | Python | F2 | 728 | 54.2 | 67.0 | 70.9 | 14,570 | 0.0% |
| spring-boot | Java | F2 | 56 | 697.2 | 1199.3 | 1498.3 | 1,127 | 0.0% |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _known bug — skipped_ |
| ruby-rails | Ruby | F2 | 445 | 83.7 | 203.6 | 294.7 | 8,891 | 0.0% |
| php-laravel | PHP | F2 | 177 | 214.8 | 291.9 | 301.2 | 3,544 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 718 | 90.0 | 99.5 | 173.3 | 14,364 | 0.0% |
| csharp-dotnet | C# | F2 | 7692 | 4.6 | 9.0 | 16.7 | 153,844 | 0.0% |
| fraiseql-tv | Rust | F2 | 9395 | 4.0 | 7.5 | 9.8 | 187,909 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 1982 | 15.8 | 48.9 | 59.9 | 39,631 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 1979 | 15.7 | 48.7 | 59.0 | 39,572 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 9403 | 3.9 | 7.7 | 10.1 | 188,058 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| async-graphql | Rust | T1 | 8555 | 4.6 | 6.4 | 7.5 | 171,098 | 0.0% |
| juniper | Rust | T1 | 7281 | 5.1 | 7.5 | 9.0 | 145,615 | 0.0% |
| go-gqlgen | Go | T1 | 4198 | 8.2 | 20.1 | 27.8 | 83,961 | 0.0% |
| gin-rest | Go | T1 | 1674 | 19.6 | 56.8 | 78.9 | 33,484 | 0.0% |
| go-graphql-go | Go | T1 | 428 | 91.4 | 110.5 | 118.3 | 8,552 | 0.0% |
| graphql-go | Go | T1 | 942 | 21.7 | 90.4 | 99.8 | 18,847 | 0.0% |
| apollo-server | Node.js | T1 | 2944 | 12.8 | 18.4 | 23.9 | 58,877 | 0.0% |
| apollo-orm | Node.js | T1 | 2072 | 18.2 | 24.9 | 28.1 | 41,431 | 0.0% |
| express-rest | Node.js | T1 | 3162 | 12.0 | 18.9 | 24.7 | 63,248 | 0.0% |
| express-orm | Node.js | T1 | 3361 | 11.2 | 15.3 | 18.3 | 67,221 | 0.0% |
| express-graphql | Node.js | T1 | 2320 | 16.2 | 23.3 | 28.9 | 46,401 | 0.0% |
| graphql-yoga | Node.js | T1 | 4158 | 8.9 | 14.7 | 18.8 | 83,164 | 0.0% |
| mercurius | Node.js | T1 | 4540 | 8.2 | 13.1 | 17.2 | 90,798 | 0.0% |
| postgraphile | Node.js | T1 | — | — | — | — | — | _known bug — skipped_ |
| strawberry | Python | T1 | — | — | — | — | — | _service did not become healthy_ |
| graphene | Python | T1 | 708 | 55.0 | 70.4 | 73.6 | 14,170 | 0.0% |
| fastapi-rest | Python | T1 | 1764 | 22.5 | 25.8 | 31.9 | 35,286 | 0.0% |
| flask-rest | Python | T1 | 117 | 354.5 | 442.0 | 504.3 | 2,346 | 0.0% |
| ariadne | Python | T1 | 596 | 65.5 | 78.4 | 86.7 | 11,920 | 0.0% |
| asgi-graphql | Python | T1 | 572 | 69.0 | 82.9 | 93.5 | 11,441 | 0.0% |
| spring-boot | Java | T1 | 1595 | 21.2 | 59.3 | 85.0 | 31,896 | 0.0% |
| spring-boot-orm | Java | T1 | — | — | — | — | — | _known bug — skipped_ |
| spring-boot-orm-naive | Java | T1 | — | — | — | — | — | _known bug — skipped_ |
| micronaut-graphql | Java | T1 | 551 | 79.5 | 116.5 | 169.5 | 11,016 | 0.0% |
| quarkus-graphql | Java | T1 | 6118 | 5.4 | 16.1 | 23.6 | 122,358 | 0.0% |
| play-graphql | Scala | T1 | 853 | 24.7 | 99.1 | 109.9 | 17,051 | 0.0% |
| ruby-rails | Ruby | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| hanami | Ruby | T1 | 302 | 33.9 | 1091.5 | 1162.8 | 6,031 | 0.0% |
| php-laravel | PHP | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| webonyx-graphql-php | PHP | T1 | 643 | 92.5 | 102.0 | 192.5 | 12,851 | 0.0% |
| csharp-dotnet | C# | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv | Rust | T1 | 1506 | 20.7 | 60.0 | 72.7 | 30,126 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 1633 | 19.1 | 55.9 | 68.8 | 32,662 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 1573 | 19.6 | 57.8 | 70.5 | 31,461 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 1369 | 21.7 | 65.7 | 78.7 | 27,389 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 5399 | 7.2 | 11.7 | 13.8 | 107,985 | 0.0% |
| juniper | Rust | Q3 | 1075 | 32.1 | 66.3 | 79.5 | 21,509 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |
| quarkus-graphql | Java | Q3 | 2040 | 18.3 | 30.3 | 39.0 | 40,796 | 0.0% |
| fraiseql-tv | Rust | Q3 | 595 | 84.0 | 105.5 | 114.6 | 11,904 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 618 | 79.4 | 103.5 | 111.7 | 12,359 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 625 | 79.3 | 103.0 | 111.9 | 12,509 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 4896 | 7.9 | 11.2 | 13.1 | 97,911 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 9942 | 3.4 | 8.8 | 12.7 | 198,833 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 9686 | 3.5 | 9.1 | 13.6 | 193,725 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 10027 | 3.4 | 8.6 | 12.2 | 200,544 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 9925 | 3.4 | 8.8 | 12.4 | 198,501 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 8766 | 3.6 | 10.3 | 17.1 | 175,315 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 9939 | 3.4 | 8.8 | 12.9 | 198,775 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 9750 | 3.4 | 8.5 | 12.0 | 194,990 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 8823 | 3.6 | 10.7 | 18.0 | 176,453 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 1260 | 25.0 | 74.3 | 103.4 | 25,199 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 8126 | 3.9 | 10.3 | 28.0 | 162,518 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 9029 | 4.0 | 8.7 | 11.7 | 180,574 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 9052 | 4.0 | 8.7 | 11.6 | 181,048 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 10941 | 3.3 | 7.2 | 9.6 | 218,812 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1875 | 21.0 | 24.7 | 0.0% |
| fastapi-rest | Python | 1325 | 17.0 | 89.4 | 0.0% |
| gin-rest | Go | 1241 | 5.8 | 99.5 | 0.0% |
| spring-boot-orm | Java | 1089 | 9.3 | 105.6 | 0.0% |
| express-orm | Node.js | 958 | 27.0 | 95.8 | 0.0% |
| express-rest | Node.js | 800 | 35.3 | 106.1 | 0.0% |
| ruby-rails | Ruby | 741 | 45.4 | 190.9 | 0.0% |
| spring-boot-orm-naive | Java | 661 | 81.3 | 173.3 | 0.0% |
| spring-boot | Java | 620 | 93.5 | 199.6 | 0.0% |
| flask-rest | Python | 274 | 148.2 | 254.7 | 0.0% |
| php-laravel | PHP | 208 | 195.3 | 277.4 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| async-graphql | Rust | 10682 | 3.5 | 8.8 | 0.0% |
| mercurius | Node.js | 9814 | 3.9 | 9.2 | 0.0% |
| graphql-yoga | Node.js | 9339 | 4.2 | 7.0 | 0.0% |
| quarkus-graphql | Java | 7862 | 3.4 | 51.5 | 0.0% |
| csharp-dotnet | C# | 6873 | 4.1 | 62.4 | 0.0% |
| express-graphql | Node.js | 3984 | 9.6 | 16.3 | 0.0% |
| asgi-graphql | Python | 1129 | 34.8 | 43.9 | 0.0% |
| graphql-go | Go | 1123 | 7.1 | 100.3 | 0.0% |
| go-gqlgen | Go | 1115 | 6.6 | 104.0 | 0.0% |
| ariadne | Python | 1108 | 35.5 | 45.6 | 0.0% |
| graphene | Python | 1073 | 36.4 | 48.9 | 0.0% |
| apollo-server | Node.js | 988 | 24.4 | 98.5 | 0.0% |
| apollo-orm | Node.js | 901 | 29.6 | 101.3 | 0.0% |
| juniper | Rust | 829 | 15.6 | 106.0 | 0.0% |
| webonyx-graphql-php | PHP | 794 | 82.9 | 102.2 | 0.0% |
| go-graphql-go | Go | 790 | 64.9 | 110.9 | 0.0% |
| micronaut-graphql | Java | 555 | 79.2 | 187.5 | 0.0% |
| hanami | Ruby | 475 | 21.3 | 808.6 | 0.0% |
| play-graphql | Scala | 407 | 98.6 | 297.4 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-cache | Rust | 10948 | 3.3 | 9.8 | 0.0% |
| fraiseql-tv | Rust | 10942 | 3.3 | 9.8 | 0.0% |
| fraiseql-v-nocache | Rust | 9120 | 3.9 | 11.6 | 0.0% |
| fraiseql-v-cache | Rust | 8821 | 4.0 | 12.1 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 5249 | 7.4 | 13.0 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv-cache | Rust | graphql-precomputed | 10948 | 3.3 | 9.8 |
| fraiseql-tv | Rust | graphql-precomputed | 10942 | 3.3 | 9.8 |
| async-graphql | Rust | graphql | 10682 | 3.5 | 8.8 |
| mercurius | Node.js | graphql | 9814 | 3.9 | 9.2 |
| graphql-yoga | Node.js | graphql | 9339 | 4.2 | 7.0 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 9120 | 3.9 | 11.6 |
| fraiseql-v-cache | Rust | graphql-precomputed | 8821 | 4.0 | 12.1 |
| quarkus-graphql | Java | graphql | 7862 | 3.4 | 51.5 |
| csharp-dotnet | C# | graphql | 6873 | 4.1 | 62.4 |
| postgraphile | Node.js | graphql-schema-first | 5249 | 7.4 | 13.0 |
| express-graphql | Node.js | graphql | 3984 | 9.6 | 16.3 |
| actix-web-rest | Rust | rest | 1875 | 21.0 | 24.7 |
| fastapi-rest | Python | rest | 1325 | 17.0 | 89.4 |
| gin-rest | Go | rest | 1241 | 5.8 | 99.5 |
| asgi-graphql | Python | graphql | 1129 | 34.8 | 43.9 |
| graphql-go | Go | graphql | 1123 | 7.1 | 100.3 |
| go-gqlgen | Go | graphql | 1115 | 6.6 | 104.0 |
| ariadne | Python | graphql | 1108 | 35.5 | 45.6 |
| spring-boot-orm | Java | rest | 1089 | 9.3 | 105.6 |
| graphene | Python | graphql | 1073 | 36.4 | 48.9 |
| apollo-server | Node.js | graphql | 988 | 24.4 | 98.5 |
| express-orm | Node.js | rest | 958 | 27.0 | 95.8 |
| apollo-orm | Node.js | graphql | 901 | 29.6 | 101.3 |
| juniper | Rust | graphql | 829 | 15.6 | 106.0 |
| express-rest | Node.js | rest | 800 | 35.3 | 106.1 |
| webonyx-graphql-php | PHP | graphql | 794 | 82.9 | 102.2 |
| go-graphql-go | Go | graphql | 790 | 64.9 | 110.9 |
| ruby-rails | Ruby | rest | 741 | 45.4 | 190.9 |
| spring-boot-orm-naive | Java | rest | 661 | 81.3 | 173.3 |
| spring-boot | Java | rest | 620 | 93.5 | 199.6 |
| micronaut-graphql | Java | graphql | 555 | 79.2 | 187.5 |
| hanami | Ruby | graphql | 475 | 21.3 | 808.6 |
| play-graphql | Scala | graphql | 407 | 98.6 | 297.4 |
| flask-rest | Python | rest | 274 | 148.2 | 254.7 |
| php-laravel | PHP | rest | 208 | 195.3 | 277.4 |

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 9,152 M/s: **~558,284 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.6M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.