# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-10  
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
| `tb_mutation_log` | 3.62 GB | 309.2 MB | 3.92 GB |
| `tv_comment` | 819.5 MB | 354.7 MB | 1.91 GB |
| `tvd_comment` | 477.6 MB | 51.4 MB | 1.13 GB |
| `tb_comment` | 294.6 MB | 82.2 MB | 376.9 MB |
| `tv_post` | 219.3 MB | 78.6 MB | 351.7 MB |
| `tvd_post` | 134.0 MB | 8.5 MB | 191.4 MB |
| `tb_post` | 133.6 MB | 20.0 MB | 153.6 MB |
| `tb_post_like` | 5.0 MB | 9.3 MB | 14.3 MB |
| `tv_user` | 8.2 MB | 6.0 MB | 14.2 MB |
| `tb_user` | 6.2 MB | 4.0 MB | 10.3 MB |
| `tb_user_follows` | 2.1 MB | 4.5 MB | 6.6 MB |
| `tvd_user` | 5.5 MB | 0.7 MB | 6.2 MB |
| `sessions` | 0.0 MB | 0.0 MB | 0.0 MB |
| `failed_jobs` | 0.0 MB | 0.0 MB | 0.0 MB |
| `migrations` | 0.0 MB | 0.0 MB | 0.0 MB |
| `users` | 0.0 MB | 0.0 MB | 0.0 MB |
| `jobs` | 0.0 MB | 0.0 MB | 0.0 MB |
| `cache_locks` | 0.0 MB | 0.0 MB | 0.0 MB |
| `password_reset_tokens` | 0.0 MB | 0.0 MB | 0.0 MB |
| `job_batches` | 0.0 MB | 0.0 MB | 0.0 MB |
| `cache` | 0.0 MB | 0.0 MB | 0.0 MB |

**TV tables**: 2.26 GB  
**TB tables (normalized baseline)**: 4.47 GB  
**Storage amplification**: 1.51× (TV adds 2.26 GB on top of the normalized 4.47 GB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q1 | 1725 | 21.5 | 40.3 | 47.8 | 34,499 | 0.0% |
| async-graphql | Rust | Q1 | 8088 | 4.3 | 10.3 | 15.1 | 161,766 | 0.0% |
| juniper | Rust | Q1 | 877 | 12.0 | 98.4 | 106.8 | 17,540 | 0.0% |
| go-gqlgen | Go | Q1 | 1103 | 7.3 | 94.4 | 103.4 | 22,057 | 0.0% |
| gin-rest | Go | Q1 | 1250 | 6.1 | 92.4 | 98.8 | 25,006 | 0.0% |
| go-graphql-go | Go | Q1 | 974 | 23.4 | 93.6 | 105.8 | 19,472 | 0.0% |
| graphql-go | Go | Q1 | 985 | 10.2 | 96.8 | 108.4 | 19,704 | 0.0% |
| apollo-server | Node.js | Q1 | 1028 | 23.8 | 84.4 | 93.6 | 20,561 | 0.0% |
| apollo-orm | Node.js | Q1 | 884 | 29.9 | 90.3 | 101.9 | 17,686 | 0.0% |
| express-rest | Node.js | Q1 | 760 | 71.1 | 97.7 | 106.2 | 15,206 | 0.0% |
| express-orm | Node.js | Q1 | 908 | 28.6 | 88.4 | 98.2 | 18,163 | 0.0% |
| express-graphql | Node.js | Q1 | 3936 | 9.7 | 14.4 | 16.7 | 78,725 | 0.0% |
| graphql-yoga | Node.js | Q1 | 9042 | 4.4 | 6.2 | 7.9 | 180,849 | 0.0% |
| mercurius | Node.js | Q1 | 9459 | 4.0 | 7.0 | 9.4 | 189,178 | 0.0% |
| postgraphile | Node.js | Q1 | 5158 | 7.5 | 11.1 | 13.7 | 103,160 | 0.0% |
| strawberry | Python | Q1 | 904 | 43.0 | 56.9 | 58.2 | 18,070 | 0.0% |
| graphene | Python | Q1 | 1072 | 36.1 | 47.5 | 53.8 | 21,433 | 0.0% |
| fastapi-rest | Python | Q1 | 976 | 25.3 | 85.1 | 93.2 | 19,518 | 0.0% |
| flask-rest | Python | Q1 | 291 | 140.4 | 212.0 | 247.8 | 5,829 | 0.0% |
| ariadne | Python | Q1 | 1092 | 35.8 | 43.9 | 47.7 | 21,834 | 0.0% |
| asgi-graphql | Python | Q1 | 1110 | 35.1 | 42.7 | 48.6 | 22,191 | 0.0% |
| spring-boot | Java | Q1 | 621 | 92.7 | 175.8 | 200.2 | 12,423 | 0.0% |
| spring-boot-orm | Java | Q1 | 989 | 14.9 | 96.8 | 102.8 | 19,783 | 0.0% |
| spring-boot-orm-naive | Java | Q1 | 619 | 86.3 | 99.6 | 170.4 | 12,376 | 0.0% |
| micronaut-graphql | Java | Q1 | 505 | 80.3 | 175.7 | 227.0 | 10,108 | 0.0% |
| quarkus-graphql | Java | Q1 | 6779 | 4.1 | 13.0 | 50.2 | 135,575 | 0.0% |
| play-graphql | Scala | Q1 | 397 | 99.1 | 199.8 | 292.2 | 7,931 | 0.0% |
| ruby-rails | Ruby | Q1 | 736 | 56.8 | 118.7 | 189.6 | 14,722 | 0.0% |
| hanami | Ruby | Q1 | 503 | 20.3 | 695.1 | 785.5 | 10,053 | 0.0% |
| php-laravel | PHP | Q1 | 201 | 199.8 | 275.8 | 292.6 | 4,015 | 0.0% |
| webonyx-graphql-php | PHP | Q1 | 704 | 86.6 | 101.4 | 113.9 | 14,082 | 0.0% |
| csharp-dotnet | C# | Q1 | 5926 | 4.5 | 14.3 | 69.4 | 118,523 | 0.0% |
| fraiseql-tv | Rust | Q1 | 8592 | 3.9 | 10.1 | 14.8 | 171,845 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 9054 | 3.9 | 8.9 | 11.8 | 181,075 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 9077 | 3.9 | 8.8 | 11.8 | 181,539 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 8072 | 4.1 | 11.1 | 17.9 | 161,434 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 14999 | 1.8 | 7.7 | 12.3 | 299,988 | 0.0% |
| async-graphql | Rust | Q2 | 8244 | 4.1 | 10.3 | 16.1 | 164,886 | 0.0% |
| juniper | Rust | Q2 | 9585 | 3.8 | 7.9 | 10.5 | 191,701 | 0.0% |
| go-gqlgen | Go | Q2 | 2740 | 11.9 | 35.7 | 48.5 | 54,809 | 0.0% |
| gin-rest | Go | Q2 | 9387 | 3.3 | 9.9 | 15.1 | 187,739 | 0.0% |
| go-graphql-go | Go | Q2 | 1137 | 21.0 | 85.0 | 98.6 | 22,747 | 0.0% |
| graphql-go | Go | Q2 | 1065 | 23.2 | 86.0 | 100.0 | 21,295 | 0.0% |
| apollo-server | Node.js | Q2 | 5977 | 6.5 | 9.6 | 11.5 | 119,534 | 0.0% |
| apollo-orm | Node.js | Q2 | 4580 | 8.4 | 12.9 | 15.2 | 91,600 | 0.0% |
| express-rest | Node.js | Q2 | 7535 | 5.2 | 7.3 | 8.6 | 150,702 | 0.0% |
| express-orm | Node.js | Q2 | 3828 | 10.4 | 13.9 | 15.8 | 76,562 | 0.0% |
| express-graphql | Node.js | Q2 | 3977 | 9.7 | 14.3 | 16.7 | 79,545 | 0.0% |
| graphql-yoga | Node.js | Q2 | 9855 | 3.9 | 6.1 | 8.4 | 197,098 | 0.0% |
| mercurius | Node.js | Q2 | 9477 | 3.9 | 7.6 | 9.9 | 189,532 | 0.0% |
| postgraphile | Node.js | Q2 | 5981 | 6.5 | 9.5 | 12.0 | 119,612 | 0.0% |
| strawberry | Python | Q2 | 1011 | 38.0 | 51.9 | 57.0 | 20,220 | 0.0% |
| graphene | Python | Q2 | 1238 | 31.4 | 42.5 | 44.4 | 24,764 | 0.0% |
| fastapi-rest | Python | Q2 | 2832 | 14.0 | 16.1 | 20.8 | 56,630 | 0.0% |
| flask-rest | Python | Q2 | 334 | 123.4 | 188.8 | 222.2 | 6,682 | 0.0% |
| ariadne | Python | Q2 | 1273 | 30.4 | 38.6 | 43.0 | 25,459 | 0.0% |
| asgi-graphql | Python | Q2 | 1319 | 29.8 | 36.7 | 37.9 | 26,385 | 0.0% |
| spring-boot | Java | Q2 | 57 | 684.8 | 1297.9 | 1590.7 | 1,142 | 0.0% |
| spring-boot-orm | Java | Q2 | 2631 | 11.6 | 38.7 | 87.5 | 52,620 | 0.0% |
| spring-boot-orm-naive | Java | Q2 | 2616 | 13.0 | 35.4 | 53.7 | 52,324 | 0.0% |
| micronaut-graphql | Java | Q2 | 1020 | 22.6 | 81.7 | 90.6 | 20,406 | 0.0% |
| quarkus-graphql | Java | Q2 | 3250 | 10.4 | 28.3 | 39.0 | 65,007 | 0.0% |
| play-graphql | Scala | Q2 | 1193 | 21.7 | 94.5 | 101.9 | 23,867 | 0.0% |
| ruby-rails | Ruby | Q2 | 448 | 85.1 | 195.7 | 277.8 | 8,961 | 0.0% |
| hanami | Ruby | Q2 | 677 | 15.6 | 497.2 | 610.7 | 13,535 | 0.0% |
| php-laravel | PHP | Q2 | 170 | 224.2 | 295.6 | 314.9 | 3,409 | 0.0% |
| webonyx-graphql-php | PHP | Q2 | 755 | 83.4 | 100.3 | 107.7 | 15,098 | 0.0% |
| csharp-dotnet | C# | Q2 | 7359 | 4.7 | 9.6 | 18.4 | 147,175 | 0.0% |
| fraiseql-tv | Rust | Q2 | 8123 | 3.9 | 11.4 | 21.7 | 162,459 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 6124 | 5.8 | 13.7 | 18.5 | 122,482 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 5973 | 5.8 | 14.3 | 19.6 | 119,459 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 7115 | 4.2 | 14.7 | 26.2 | 142,295 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 7717 | 5.0 | 7.0 | 9.4 | 154,340 | 0.0% |
| async-graphql | Rust | Q2b | 8748 | 4.4 | 7.1 | 8.8 | 174,961 | 0.0% |
| juniper | Rust | Q2b | 4576 | 8.1 | 13.2 | 19.1 | 91,510 | 0.0% |
| go-gqlgen | Go | Q2b | 1495 | 21.0 | 59.9 | 74.8 | 29,894 | 0.0% |
| gin-rest | Go | Q2b | 1024 | 27.2 | 84.6 | 98.2 | 20,478 | 0.0% |
| go-graphql-go | Go | Q2b | 900 | 24.7 | 97.2 | 108.7 | 18,009 | 0.0% |
| graphql-go | Go | Q2b | 846 | 28.4 | 98.2 | 109.8 | 16,930 | 0.0% |
| apollo-server | Node.js | Q2b | 3369 | 11.5 | 16.5 | 18.8 | 67,382 | 0.0% |
| apollo-orm | Node.js | Q2b | 2312 | 16.9 | 23.7 | 26.4 | 46,238 | 0.0% |
| express-rest | Node.js | Q2b | 6194 | 6.5 | 8.5 | 10.3 | 123,885 | 0.0% |
| express-orm | Node.js | Q2b | 2429 | 16.2 | 23.1 | 26.2 | 48,571 | 0.0% |
| express-graphql | Node.js | Q2b | 2596 | 14.7 | 20.3 | 23.6 | 51,926 | 0.0% |
| graphql-yoga | Node.js | Q2b | 5069 | 7.4 | 11.3 | 14.1 | 101,377 | 0.0% |
| mercurius | Node.js | Q2b | 5850 | 6.4 | 10.4 | 13.7 | 117,009 | 0.0% |
| postgraphile | Node.js | Q2b | 4529 | 8.5 | 12.9 | 15.6 | 90,589 | 0.0% |
| strawberry | Python | Q2b | 660 | 59.1 | 75.3 | 78.2 | 13,197 | 0.0% |
| graphene | Python | Q2b | 769 | 49.2 | 64.5 | 100.5 | 15,382 | 0.0% |
| fastapi-rest | Python | Q2b | 2682 | 14.7 | 18.3 | 23.3 | 53,638 | 0.0% |
| flask-rest | Python | Q2b | 271 | 151.4 | 226.6 | 264.9 | 5,415 | 0.0% |
| ariadne | Python | Q2b | 850 | 46.1 | 55.7 | 58.5 | 16,993 | 0.0% |
| asgi-graphql | Python | Q2b | 870 | 45.1 | 53.6 | 55.7 | 17,404 | 0.0% |
| spring-boot | Java | Q2b | 56 | 695.8 | 1202.9 | 1501.1 | 1,130 | 0.0% |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _skipped_ |
| micronaut-graphql | Java | Q2b | 587 | 78.5 | 112.8 | 167.4 | 11,748 | 0.0% |
| quarkus-graphql | Java | Q2b | 5625 | 5.9 | 17.3 | 23.9 | 112,491 | 0.0% |
| play-graphql | Scala | Q2b | 962 | 26.2 | 92.0 | 107.5 | 19,242 | 0.0% |
| ruby-rails | Ruby | Q2b | 442 | 84.9 | 197.9 | 287.0 | 8,836 | 0.0% |
| hanami | Ruby | Q2b | 326 | 31.7 | 1010.4 | 1071.4 | 6,528 | 0.0% |
| php-laravel | PHP | Q2b | 169 | 223.7 | 297.0 | 309.6 | 3,383 | 0.0% |
| webonyx-graphql-php | PHP | Q2b | 668 | 90.4 | 106.2 | 192.7 | 13,366 | 0.0% |
| csharp-dotnet | C# | Q2b | 7222 | 4.8 | 10.0 | 19.1 | 144,433 | 0.0% |
| fraiseql-tv | Rust | Q2b | 9212 | 3.8 | 8.8 | 11.9 | 184,232 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 2480 | 13.8 | 35.2 | 46.6 | 49,607 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 2445 | 14.0 | 35.4 | 46.3 | 48,896 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9212 | 3.8 | 8.9 | 12.0 | 184,243 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 1618 | 20.0 | 41.3 | 47.6 | 32,360 | 0.0% |
| async-graphql | Rust | M1 | 1993 | 16.9 | 40.2 | 56.8 | 39,861 | 0.0% |
| juniper | Rust | M1 | 1331 | 15.4 | 100.9 | 208.9 | 26,628 | 0.0% |
| go-gqlgen | Go | M1 | 1821 | 14.2 | 69.9 | 106.7 | 36,413 | 0.0% |
| gin-rest | Go | M1 | 1752 | 14.5 | 73.4 | 114.1 | 35,044 | 0.0% |
| go-graphql-go | Go | M1 | 1866 | 14.9 | 59.2 | 73.7 | 37,329 | 0.0% |
| graphql-go | Go | M1 | 1386 | 20.2 | 74.6 | 94.7 | 27,723 | 0.0% |
| apollo-server | Node.js | M1 | 2182 | 12.3 | 55.7 | 86.0 | 43,640 | 0.0% |
| express-graphql | Node.js | M1 | 2196 | 12.4 | 54.5 | 84.5 | 43,927 | 0.0% |
| graphql-yoga | Node.js | M1 | 2108 | 12.2 | 59.5 | 93.2 | 42,158 | 0.0% |
| mercurius | Node.js | M1 | 397 | 45.5 | 404.5 | 812.0 | 7,942 | 0.0% |
| strawberry | Python | M1 | 918 | 42.0 | 57.4 | 62.4 | 18,359 | 0.0% |
| graphene | Python | M1 | 1182 | 33.2 | 45.0 | 48.3 | 23,634 | 0.0% |
| fastapi-rest | Python | M1 | 891 | 28.6 | 141.3 | 237.2 | 17,817 | 0.0% |
| spring-boot | Java | M1 | 980 | 16.9 | 170.4 | 310.5 | 19,605 | 0.0% |
| spring-boot-orm | Java | M1 | 1303 | 17.0 | 102.8 | 192.6 | 26,052 | 0.0% |
| micronaut-graphql | Java | M1 | 2142 | 17.0 | 33.8 | 37.7 | 42,845 | 0.0% |
| quarkus-graphql | Java | M1 | 2087 | 19.1 | 20.8 | 22.9 | 41,733 | 0.0% |
| play-graphql | Scala | M1 | 1901 | 17.2 | 48.4 | 71.1 | 38,018 | 0.0% |
| ruby-rails | Ruby | M1 | 718 | 58.5 | 124.6 | 194.5 | 14,365 | 0.0% |
| webonyx-graphql-php | PHP | M1 | 496 | 89.5 | 189.0 | 201.9 | 9,923 | 0.0% |
| csharp-dotnet | C# | M1 | 2183 | 11.4 | 59.3 | 93.4 | 43,665 | 0.0% |
| fraiseql-tv | Rust | M1 | 1342 | 23.7 | 75.2 | 137.1 | 26,836 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 7047 | 5.1 | 10.7 | 15.5 | 140,940 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 6019 | 5.2 | 13.6 | 24.3 | 120,381 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 5719 | 5.6 | 15.7 | 26.5 | 114,389 | 0.0% |
| fraiseql-tv-audit | Rust | M1 | 6918 | 4.7 | 10.2 | 19.3 | 138,356 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 14361 | 1.9 | 8.0 | 12.8 | 287,220 | 0.0% |
| async-graphql | Rust | F1 | 8275 | 4.1 | 10.4 | 16.8 | 165,502 | 0.0% |
| juniper | Rust | F1 | 9453 | 3.8 | 8.1 | 10.9 | 189,063 | 0.0% |
| go-gqlgen | Go | F1 | 2734 | 12.4 | 33.8 | 45.6 | 54,690 | 0.0% |
| gin-rest | Go | F1 | 8875 | 3.6 | 10.4 | 15.6 | 177,495 | 0.0% |
| go-graphql-go | Go | F1 | 1085 | 23.1 | 85.3 | 99.5 | 21,700 | 0.0% |
| graphql-go | Go | F1 | 1058 | 23.1 | 86.6 | 99.4 | 21,161 | 0.0% |
| apollo-server | Node.js | F1 | 6001 | 6.4 | 9.6 | 11.8 | 120,028 | 0.0% |
| apollo-orm | Node.js | F1 | 4341 | 8.8 | 13.8 | 16.5 | 86,817 | 0.0% |
| express-rest | Node.js | F1 | 8014 | 4.9 | 7.0 | 8.9 | 160,273 | 0.0% |
| express-orm | Node.js | F1 | 3872 | 10.3 | 13.8 | 15.6 | 77,439 | 0.0% |
| express-graphql | Node.js | F1 | 4337 | 8.8 | 13.4 | 16.5 | 86,733 | 0.0% |
| graphql-yoga | Node.js | F1 | 9704 | 3.9 | 7.0 | 9.4 | 194,071 | 0.0% |
| mercurius | Node.js | F1 | 9299 | 4.0 | 7.7 | 9.9 | 185,976 | 0.0% |
| strawberry | Python | F1 | 926 | 41.4 | 56.5 | 58.8 | 18,530 | 0.0% |
| graphene | Python | F1 | 1110 | 34.8 | 47.7 | 51.3 | 22,192 | 0.0% |
| fastapi-rest | Python | F1 | 2908 | 13.5 | 16.7 | 21.2 | 58,170 | 0.0% |
| flask-rest | Python | F1 | 337 | 121.3 | 185.3 | 221.6 | 6,745 | 0.0% |
| ariadne | Python | F1 | 1182 | 33.0 | 41.4 | 43.0 | 23,634 | 0.0% |
| asgi-graphql | Python | F1 | 1194 | 32.8 | 40.4 | 42.9 | 23,871 | 0.0% |
| spring-boot | Java | F1 | 57 | 691.7 | 1205.4 | 1597.9 | 1,144 | 0.0% |
| spring-boot-orm | Java | F1 | 4541 | 6.1 | 23.8 | 37.8 | 90,822 | 0.0% |
| ruby-rails | Ruby | F1 | 436 | 85.1 | 200.6 | 311.2 | 8,728 | 0.0% |
| php-laravel | PHP | F1 | 173 | 218.7 | 291.2 | 300.8 | 3,466 | 0.0% |
| webonyx-graphql-php | PHP | F1 | 750 | 83.9 | 100.5 | 107.7 | 14,993 | 0.0% |
| csharp-dotnet | C# | F1 | 7396 | 4.8 | 9.6 | 16.3 | 147,911 | 0.0% |
| fraiseql-tv | Rust | F1 | 9129 | 3.7 | 9.4 | 13.5 | 182,580 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 2812 | 12.0 | 32.1 | 43.5 | 56,240 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 2650 | 12.8 | 33.4 | 45.3 | 52,998 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 9483 | 3.7 | 8.9 | 12.2 | 189,660 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 8667 | 4.3 | 8.1 | 11.3 | 173,341 | 0.0% |
| async-graphql | Rust | F2 | 8575 | 4.4 | 7.3 | 9.3 | 171,498 | 0.0% |
| juniper | Rust | F2 | 4425 | 8.2 | 14.2 | 21.0 | 88,502 | 0.0% |
| go-gqlgen | Go | F2 | 1615 | 19.6 | 58.2 | 73.5 | 32,309 | 0.0% |
| gin-rest | Go | F2 | 1056 | 26.1 | 82.8 | 97.2 | 21,123 | 0.0% |
| go-graphql-go | Go | F2 | 823 | 31.0 | 98.7 | 110.0 | 16,456 | 0.0% |
| graphql-go | Go | F2 | 839 | 28.7 | 98.9 | 109.5 | 16,781 | 0.0% |
| apollo-server | Node.js | F2 | 3386 | 11.4 | 16.3 | 18.9 | 67,711 | 0.0% |
| apollo-orm | Node.js | F2 | 2267 | 17.2 | 24.1 | 27.5 | 45,344 | 0.0% |
| express-rest | Node.js | F2 | 6217 | 6.3 | 9.7 | 13.5 | 124,349 | 0.0% |
| express-orm | Node.js | F2 | 2478 | 15.9 | 22.6 | 25.4 | 49,558 | 0.0% |
| express-graphql | Node.js | F2 | 2912 | 13.0 | 18.0 | 21.0 | 58,244 | 0.0% |
| graphql-yoga | Node.js | F2 | 4934 | 7.6 | 12.5 | 16.6 | 98,680 | 0.0% |
| mercurius | Node.js | F2 | 5751 | 6.5 | 10.4 | 13.9 | 115,026 | 0.0% |
| strawberry | Python | F2 | 622 | 62.3 | 79.7 | 83.8 | 12,439 | 0.0% |
| graphene | Python | F2 | 752 | 51.4 | 66.6 | 72.3 | 15,050 | 0.0% |
| fastapi-rest | Python | F2 | 2808 | 14.1 | 16.2 | 21.1 | 56,155 | 0.0% |
| flask-rest | Python | F2 | 286 | 145.8 | 223.4 | 275.5 | 5,729 | 0.0% |
| ariadne | Python | F2 | 793 | 49.5 | 59.6 | 62.0 | 15,861 | 0.0% |
| asgi-graphql | Python | F2 | 804 | 48.7 | 58.4 | 61.2 | 16,082 | 0.0% |
| spring-boot | Java | F2 | 56 | 697.0 | 1199.4 | 1409.8 | 1,126 | 0.0% |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _skipped_ |
| ruby-rails | Ruby | F2 | 433 | 86.1 | 200.7 | 297.3 | 8,667 | 0.0% |
| php-laravel | PHP | F2 | 164 | 234.1 | 301.7 | 345.7 | 3,281 | 0.0% |
| webonyx-graphql-php | PHP | F2 | 663 | 91.0 | 103.9 | 192.3 | 13,268 | 0.0% |
| csharp-dotnet | C# | F2 | 6771 | 4.9 | 11.1 | 33.9 | 135,418 | 0.0% |
| fraiseql-tv | Rust | F2 | 9090 | 3.8 | 8.8 | 11.8 | 181,799 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 1536 | 20.3 | 57.7 | 70.0 | 30,713 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 1522 | 20.4 | 58.0 | 69.9 | 30,435 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8055 | 3.9 | 8.8 | 12.0 | 161,104 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 61 | 678.4 | 813.4 | 889.8 | 1,224 | 0.0% |
| async-graphql | Rust | T1 | 7978 | 4.9 | 7.1 | 8.6 | 159,562 | 0.0% |
| juniper | Rust | T1 | 7095 | 5.4 | 8.4 | 9.9 | 141,894 | 0.0% |
| go-gqlgen | Go | T1 | 4243 | 7.7 | 21.3 | 30.0 | 84,869 | 0.0% |
| gin-rest | Go | T1 | 1500 | 21.7 | 63.9 | 89.7 | 29,992 | 0.0% |
| go-graphql-go | Go | T1 | 426 | 92.0 | 109.9 | 117.2 | 8,520 | 0.0% |
| graphql-go | Go | T1 | 958 | 23.8 | 88.6 | 99.4 | 19,168 | 0.0% |
| apollo-server | Node.js | T1 | 2936 | 12.9 | 18.1 | 22.9 | 58,714 | 0.0% |
| apollo-orm | Node.js | T1 | 2138 | 17.6 | 24.5 | 27.3 | 42,768 | 0.0% |
| express-rest | Node.js | T1 | 3090 | 12.3 | 19.6 | 25.3 | 61,793 | 0.0% |
| express-orm | Node.js | T1 | 3544 | 10.8 | 14.5 | 16.4 | 70,878 | 0.0% |
| express-graphql | Node.js | T1 | 2410 | 15.6 | 21.4 | 26.4 | 48,210 | 0.0% |
| graphql-yoga | Node.js | T1 | 3865 | 9.7 | 15.7 | 21.0 | 77,304 | 0.0% |
| mercurius | Node.js | T1 | 4476 | 8.3 | 13.8 | 17.9 | 89,527 | 0.0% |
| postgraphile | Node.js | T1 | — | — | — | — | — | _skipped_ |
| strawberry | Python | T1 | 507 | 76.9 | 96.8 | 100.5 | 10,144 | 0.0% |
| graphene | Python | T1 | 707 | 54.6 | 71.6 | 77.9 | 14,143 | 0.0% |
| fastapi-rest | Python | T1 | 1786 | 22.3 | 24.3 | 29.8 | 35,713 | 0.0% |
| flask-rest | Python | T1 | 128 | 325.9 | 428.1 | 481.6 | 2,550 | 0.0% |
| ariadne | Python | T1 | 607 | 64.8 | 76.9 | 79.9 | 12,131 | 0.0% |
| asgi-graphql | Python | T1 | 608 | 64.6 | 75.7 | 79.4 | 12,164 | 0.0% |
| spring-boot | Java | T1 | 4095 | 8.2 | 20.6 | 31.9 | 81,903 | 0.0% |
| spring-boot-orm | Java | T1 | — | — | — | — | — | _skipped_ |
| spring-boot-orm-naive | Java | T1 | — | — | — | — | — | _skipped_ |
| micronaut-graphql | Java | T1 | 559 | 79.8 | 116.3 | 165.6 | 11,182 | 0.0% |
| quarkus-graphql | Java | T1 | 5793 | 5.5 | 18.2 | 24.6 | 115,861 | 0.0% |
| play-graphql | Scala | T1 | 877 | 25.1 | 97.9 | 112.5 | 17,543 | 0.0% |
| ruby-rails | Ruby | T1 | 190 | 200.1 | 368.5 | 454.0 | 3,804 | 0.0% |
| hanami | Ruby | T1 | 292 | 34.6 | 1124.2 | 1198.2 | 5,848 | 0.0% |
| php-laravel | PHP | T1 | 64 | 616.0 | 691.6 | 698.9 | 1,286 | 0.0% |
| webonyx-graphql-php | PHP | T1 | 593 | 93.2 | 113.3 | 195.2 | 11,863 | 0.0% |
| csharp-dotnet | C# | T1 | 4982 | 7.0 | 13.2 | 42.2 | 99,637 | 0.0% |
| fraiseql-tv | Rust | T1 | 7267 | 5.2 | 9.2 | 12.0 | 145,341 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v-cache | Rust | T1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv-cache | Rust | T1 | 7289 | 5.2 | 9.2 | 12.1 | 145,775 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | Q3 | 5176 | 7.5 | 12.2 | 14.6 | 103,526 | 0.0% |
| juniper | Rust | Q3 | 1007 | 34.7 | 72.2 | 89.4 | 20,133 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _skipped_ |
| quarkus-graphql | Java | Q3 | 2051 | 18.3 | 29.8 | 38.3 | 41,022 | 0.0% |
| fraiseql-tv | Rust | Q3 | 7751 | 4.8 | 9.1 | 11.9 | 155,016 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 741 | 76.2 | 102.8 | 111.9 | 14,822 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 758 | 75.1 | 101.6 | 110.9 | 15,158 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 7785 | 4.7 | 9.2 | 11.9 | 155,698 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| async-graphql | Rust | MC1 | 2197 | 15.5 | 35.3 | 49.7 | 43,937 | 0.0% |
| graphql-yoga | Node.js | MC1 | 1108 | 21.5 | 119.8 | 203.2 | 22,154 | 0.0% |
| mercurius | Node.js | MC1 | 2104 | 13.6 | 54.7 | 84.7 | 42,080 | 0.0% |
| fraiseql-tv | Rust | MC1 | 4810 | 6.1 | 21.5 | 33.4 | 96,199 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 6994 | 5.0 | 11.0 | 17.8 | 139,880 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 6883 | 5.1 | 11.4 | 17.7 | 137,662 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1212 | 25.3 | 82.6 | 150.9 | 24,232 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 3309 | 9.6 | 29.8 | 42.4 | 66,175 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 3385 | 9.5 | 28.8 | 41.5 | 67,696 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 4388 | 6.7 | 24.2 | 36.4 | 87,766 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 3195 | 10.0 | 30.7 | 43.0 | 63,899 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 3930 | 7.7 | 26.3 | 38.9 | 78,593 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 3581 | 8.5 | 29.0 | 41.8 | 71,623 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 4441 | 6.4 | 25.1 | 37.9 | 88,827 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 3132 | 10.2 | 31.2 | 44.0 | 62,637 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 6437 | 5.3 | 12.9 | 21.4 | 128,735 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 8148 | 4.1 | 10.9 | 16.2 | 162,965 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 9005 | 4.0 | 8.9 | 11.8 | 180,100 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8820 | 4.0 | 8.8 | 12.0 | 176,398 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 8175 | 4.1 | 10.8 | 16.7 | 163,504 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 8973 | 3.8 | 8.9 | 12.4 | 179,463 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 8960 | 4.0 | 8.8 | 11.7 | 179,199 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8930 | 4.0 | 8.9 | 11.8 | 178,592 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 8520 | 4.0 | 10.3 | 15.8 | 170,406 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9241 | 3.8 | 8.8 | 11.8 | 184,818 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 2031 | 16.4 | 43.9 | 56.3 | 40,614 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 2149 | 15.8 | 40.3 | 51.4 | 42,986 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9108 | 3.8 | 8.8 | 11.9 | 182,152 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1239 | 25.3 | 79.2 | 145.4 | 24,779 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 8410 | 4.4 | 8.6 | 11.2 | 168,190 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 7637 | 4.5 | 9.7 | 15.1 | 152,743 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 8429 | 4.3 | 8.5 | 11.5 | 168,573 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1725 | 21.5 | 47.8 | 0.0% |
| gin-rest | Go | 1250 | 6.1 | 98.8 | 0.0% |
| spring-boot-orm | Java | 989 | 14.9 | 102.8 | 0.0% |
| fastapi-rest | Python | 976 | 25.3 | 93.2 | 0.0% |
| express-orm | Node.js | 908 | 28.6 | 98.2 | 0.0% |
| express-rest | Node.js | 760 | 71.1 | 106.2 | 0.0% |
| ruby-rails | Ruby | 736 | 56.8 | 189.6 | 0.0% |
| spring-boot | Java | 621 | 92.7 | 200.2 | 0.0% |
| spring-boot-orm-naive | Java | 619 | 86.3 | 170.4 | 0.0% |
| flask-rest | Python | 291 | 140.4 | 247.8 | 0.0% |
| php-laravel | PHP | 201 | 199.8 | 292.6 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| mercurius | Node.js | 9459 | 4.0 | 9.4 | 0.0% |
| graphql-yoga | Node.js | 9042 | 4.4 | 7.9 | 0.0% |
| async-graphql | Rust | 8088 | 4.3 | 15.1 | 0.0% |
| quarkus-graphql | Java | 6779 | 4.1 | 50.2 | 0.0% |
| csharp-dotnet | C# | 5926 | 4.5 | 69.4 | 0.0% |
| express-graphql | Node.js | 3936 | 9.7 | 16.7 | 0.0% |
| asgi-graphql | Python | 1110 | 35.1 | 48.6 | 0.0% |
| go-gqlgen | Go | 1103 | 7.3 | 103.4 | 0.0% |
| ariadne | Python | 1092 | 35.8 | 47.7 | 0.0% |
| graphene | Python | 1072 | 36.1 | 53.8 | 0.0% |
| apollo-server | Node.js | 1028 | 23.8 | 93.6 | 0.0% |
| graphql-go | Go | 985 | 10.2 | 108.4 | 0.0% |
| go-graphql-go | Go | 974 | 23.4 | 105.8 | 0.0% |
| strawberry | Python | 904 | 43.0 | 58.2 | 0.0% |
| apollo-orm | Node.js | 884 | 29.9 | 101.9 | 0.0% |
| juniper | Rust | 877 | 12.0 | 106.8 | 0.0% |
| webonyx-graphql-php | PHP | 704 | 86.6 | 113.9 | 0.0% |
| micronaut-graphql | Java | 505 | 80.3 | 227.0 | 0.0% |
| hanami | Ruby | 503 | 20.3 | 785.5 | 0.0% |
| play-graphql | Scala | 397 | 99.1 | 292.2 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-v-cache | Rust | 9077 | 3.9 | 11.8 | 0.0% |
| fraiseql-v-nocache | Rust | 9054 | 3.9 | 11.8 | 0.0% |
| fraiseql-tv | Rust | 8592 | 3.9 | 14.8 | 0.0% |
| fraiseql-tv-cache | Rust | 8072 | 4.1 | 17.9 | 0.0% |

---

## Schema-first GraphQL — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| postgraphile | Node.js | 5158 | 7.5 | 13.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| mercurius | Node.js | graphql | 9459 | 4.0 | 9.4 |
| fraiseql-v-cache | Rust | graphql-precomputed | 9077 | 3.9 | 11.8 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 9054 | 3.9 | 11.8 |
| graphql-yoga | Node.js | graphql | 9042 | 4.4 | 7.9 |
| fraiseql-tv | Rust | graphql-precomputed | 8592 | 3.9 | 14.8 |
| async-graphql | Rust | graphql | 8088 | 4.3 | 15.1 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 8072 | 4.1 | 17.9 |
| quarkus-graphql | Java | graphql | 6779 | 4.1 | 50.2 |
| csharp-dotnet | C# | graphql | 5926 | 4.5 | 69.4 |
| postgraphile | Node.js | graphql-schema-first | 5158 | 7.5 | 13.7 |
| express-graphql | Node.js | graphql | 3936 | 9.7 | 16.7 |
| actix-web-rest | Rust | rest | 1725 | 21.5 | 47.8 |
| gin-rest | Go | rest | 1250 | 6.1 | 98.8 |
| asgi-graphql | Python | graphql | 1110 | 35.1 | 48.6 |
| go-gqlgen | Go | graphql | 1103 | 7.3 | 103.4 |
| ariadne | Python | graphql | 1092 | 35.8 | 47.7 |
| graphene | Python | graphql | 1072 | 36.1 | 53.8 |
| apollo-server | Node.js | graphql | 1028 | 23.8 | 93.6 |
| spring-boot-orm | Java | rest | 989 | 14.9 | 102.8 |
| graphql-go | Go | graphql | 985 | 10.2 | 108.4 |
| fastapi-rest | Python | rest | 976 | 25.3 | 93.2 |
| go-graphql-go | Go | graphql | 974 | 23.4 | 105.8 |
| express-orm | Node.js | rest | 908 | 28.6 | 98.2 |
| strawberry | Python | graphql | 904 | 43.0 | 58.2 |
| apollo-orm | Node.js | graphql | 884 | 29.9 | 101.9 |
| juniper | Rust | graphql | 877 | 12.0 | 106.8 |
| express-rest | Node.js | rest | 760 | 71.1 | 106.2 |
| ruby-rails | Ruby | rest | 736 | 56.8 | 189.6 |
| webonyx-graphql-php | PHP | graphql | 704 | 86.6 | 113.9 |
| spring-boot | Java | rest | 621 | 92.7 | 200.2 |
| spring-boot-orm-naive | Java | rest | 619 | 86.3 | 170.4 |
| micronaut-graphql | Java | graphql | 505 | 80.3 | 227.0 |
| hanami | Ruby | graphql | 503 | 20.3 | 785.5 |
| play-graphql | Scala | graphql | 397 | 99.1 | 292.2 |
| flask-rest | Python | rest | 291 | 140.4 | 247.8 |
| php-laravel | PHP | rest | 201 | 199.8 | 292.6 |

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

> **Peak**: fraiseql-tv 4810 cycles/s (1 req) vs async-graphql 2197 cycles/s (2 req) — 2.2× more cycles/s with half the round trips.

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 7,047 M/s: **~429,867 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.4M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.