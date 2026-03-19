# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-03-01  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 15s per scenario  
**Warmup**: 3s per scenario  
**Cooldown**: 5s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q1 | 3620 | 9.2 | 23.9 | 33.8 | 54,303 | 0.0% |
| fraiseql-tv-nocache | Python | Q1 | 4655 | 8.1 | 13.9 | 17.5 | 69,824 | 0.0% |
| fraiseql-v | Python | Q1 | 3386 | 9.8 | 25.5 | 34.7 | 50,791 | 0.0% |
| actix-web-rest | Rust | Q1 | 4551 | 8.5 | 12.7 | 14.9 | 68,271 | 0.0% |
| async-graphql | Rust | Q1 | 4207 | 8.9 | 15.9 | 21.4 | 63,098 | 0.0% |
| go-gqlgen | Go | Q1 | 3983 | 9.4 | 15.7 | 23.0 | 59,745 | 0.0% |
| gin-rest | Go | Q1 | 4714 | 8.2 | 12.5 | 14.9 | 70,704 | 0.0% |
| apollo-server | Node.js | Q1 | 1749 | 14.7 | 21.8 | 23.1 | 26,237 | 36.4% |
| express-rest | Node.js | Q1 | 2027 | 12.7 | 16.3 | 22.1 | 30,403 | 33.8% |
| graphql-yoga | Node.js | Q1 | 4068 | 8.4 | 16.5 | 29.6 | 61,023 | 0.0% |
| strawberry | Python | Q1 | 828 | 47.4 | 59.0 | 62.7 | 12,415 | 0.0% |
| fastapi-rest | Python | Q1 | 4481 | 8.6 | 12.9 | 15.3 | 67,219 | 0.0% |
| apollo-orm | Node.js | Q1 | 1688 | 14.1 | 18.1 | 21.7 | 25,327 | 43.1% |
| express-orm | Node.js | Q1 | 1568 | 19.4 | 35.4 | 44.9 | 23,524 | 24.4% |
| express-graphql | Node.js | Q1 | 1420 | 13.9 | 17.0 | 21.7 | 21,305 | 52.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2 | 3617 | 9.4 | 22.9 | 31.7 | 54,255 | 0.0% |
| fraiseql-tv-nocache | Python | Q2 | 4701 | 8.0 | 14.0 | 17.8 | 70,511 | 0.0% |
| fraiseql-v | Python | Q2 | 3160 | 10.3 | 27.7 | 37.3 | 47,405 | 0.0% |
| actix-web-rest | Rust | Q2 | 4559 | 8.1 | 15.5 | 20.6 | 68,390 | 0.0% |
| async-graphql | Rust | Q2 | 4219 | 8.8 | 16.4 | 22.0 | 63,282 | 0.0% |
| go-gqlgen | Go | Q2 | 4328 | 8.6 | 15.6 | 20.1 | 64,922 | 0.0% |
| gin-rest | Go | Q2 | 4043 | 8.7 | 19.5 | 28.8 | 60,640 | 0.0% |
| apollo-server | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-rest | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| graphql-yoga | Node.js | Q2 | 2932 | 10.7 | 16.0 | 22.6 | 43,983 | 13.1% |
| strawberry | Python | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fastapi-rest | Python | Q2 | 3832 | 9.8 | 17.5 | 22.1 | 57,483 | 0.0% |
| apollo-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-orm | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-graphql | Node.js | Q2 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q2b | 3643 | 9.4 | 22.7 | 31.5 | 54,648 | 0.0% |
| fraiseql-tv-nocache | Python | Q2b | 4448 | 8.5 | 14.7 | 18.4 | 66,724 | 0.0% |
| fraiseql-v | Python | Q2b | 2868 | 11.4 | 29.9 | 39.4 | 43,025 | 0.0% |
| actix-web-rest | Rust | Q2b | 4322 | 8.7 | 15.4 | 19.7 | 64,828 | 0.0% |
| async-graphql | Rust | Q2b | 3553 | 10.3 | 19.8 | 25.9 | 53,301 | 0.0% |
| go-gqlgen | Go | Q2b | 4201 | 8.9 | 16.2 | 21.9 | 63,014 | 0.0% |
| gin-rest | Go | Q2b | 3061 | 11.3 | 26.3 | 35.9 | 45,909 | 0.0% |
| apollo-server | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-rest | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| graphql-yoga | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| strawberry | Python | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fastapi-rest | Python | Q2b | 4057 | 9.2 | 16.5 | 21.2 | 60,858 | 0.0% |
| apollo-orm | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-orm | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| express-graphql | Node.js | Q2b | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | Q3 | — | — | — | — | — | _known bug — skipped_ |
| fraiseql-tv-nocache | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v | Python | Q3 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| async-graphql | Rust | Q3 | 1857 | 20.2 | 38.7 | 47.9 | 27,862 | 0.0% |
| go-gqlgen | Go | Q3 | — | — | — | — | — | _known bug — skipped_ |

## C3 — `user(id: UUID) { id username fullName }` — single entity by UUID (cache warm)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | C3 | 1570 | 24.7 | 36.1 | 42.9 | 23,550 | 0.0% |
| fraiseql-tv-nocache | Python | C3 | 765 | 50.3 | 76.0 | 89.5 | 11,472 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-tv-nocache | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| fraiseql-v | Python | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| actix-web-rest | Rust | M1 | — | — | — | — | — | _known bug — skipped_ |
| async-graphql | Rust | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| go-gqlgen | Go | M1 | 0 | 0.0 | 0.0 | 0.0 | 0 | 100.0% |
| gin-rest | Go | M1 | — | — | — | — | — | _known bug — skipped_ |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F1 | 3833 | 8.9 | 21.7 | 30.2 | 57,499 | 0.0% |
| fraiseql-tv-nocache | Python | F1 | 4563 | 8.3 | 14.4 | 18.1 | 68,448 | 0.0% |
| fraiseql-v | Python | F1 | 3823 | 9.0 | 20.9 | 29.1 | 57,339 | 0.0% |
| actix-web-rest | Rust | F1 | 4607 | 8.0 | 15.0 | 20.0 | 69,110 | 0.0% |
| async-graphql | Rust | F1 | 3979 | 9.2 | 17.8 | 24.6 | 59,691 | 0.0% |
| go-gqlgen | Go | F1 | 4476 | 8.3 | 15.2 | 21.9 | 67,145 | 0.0% |
| gin-rest | Go | F1 | 3963 | 8.9 | 19.4 | 29.9 | 59,449 | 0.0% |
| apollo-server | Node.js | F1 | 1760 | 10.4 | 21.4 | 36.1 | 26,394 | 44.0% |
| express-rest | Node.js | F1 | 2482 | 8.9 | 14.9 | 17.7 | 37,226 | 32.1% |
| graphql-yoga | Node.js | F1 | 1685 | 9.1 | 30.5 | 85.5 | 25,268 | 37.7% |
| strawberry | Python | F1 | 419 | 50.2 | 91.6 | 124.3 | 6,288 | 73.2% |
| fastapi-rest | Python | F1 | 4009 | 9.3 | 16.9 | 21.5 | 60,132 | 0.0% |
| apollo-orm | Node.js | F1 | 1373 | 13.4 | 19.0 | 24.7 | 20,590 | 54.5% |
| express-orm | Node.js | F1 | 961 | 14.8 | 19.5 | 22.9 | 14,416 | 69.0% |
| express-graphql | Node.js | F1 | 1483 | 12.7 | 17.1 | 23.0 | 22,248 | 52.8% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F2 | 3337 | 9.7 | 27.0 | 38.2 | 50,053 | 0.0% |
| fraiseql-tv-nocache | Python | F2 | 4236 | 8.8 | 15.9 | 21.1 | 63,542 | 0.0% |
| fraiseql-v | Python | F2 | 3360 | 10.4 | 23.4 | 31.8 | 50,405 | 0.0% |
| actix-web-rest | Rust | F2 | 4323 | 8.7 | 15.5 | 19.6 | 64,850 | 0.0% |
| async-graphql | Rust | F2 | 3651 | 10.2 | 18.2 | 23.5 | 54,772 | 0.0% |
| go-gqlgen | Go | F2 | 3628 | 9.7 | 21.5 | 30.2 | 54,427 | 0.0% |
| gin-rest | Go | F2 | 3219 | 10.8 | 24.4 | 34.6 | 48,278 | 0.0% |
| apollo-server | Node.js | F2 | 884 | 14.9 | 32.3 | 39.8 | 13,262 | 65.6% |
| express-rest | Node.js | F2 | 3240 | 9.4 | 16.8 | 19.7 | 48,598 | 13.9% |
| graphql-yoga | Node.js | F2 | 2014 | 9.5 | 16.9 | 25.0 | 30,205 | 39.4% |
| strawberry | Python | F2 | 488 | 71.1 | 144.1 | 174.5 | 7,327 | 0.0% |
| fastapi-rest | Python | F2 | 3721 | 10.0 | 18.2 | 22.9 | 55,822 | 0.0% |
| apollo-orm | Node.js | F2 | 271 | 19.5 | 23.1 | 27.9 | 4,067 | 91.3% |
| express-orm | Node.js | F2 | 639 | 20.4 | 22.2 | 24.2 | 9,582 | 77.9% |
| express-graphql | Node.js | F2 | 17 | 14.5 | 29.6 | 36.8 | 261 | 99.5% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Python | F3 | 3320 | 9.8 | 26.6 | 36.7 | 49,804 | 0.0% |
| fraiseql-tv-nocache | Python | F3 | 4472 | 8.4 | 14.7 | 18.8 | 67,074 | 0.0% |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| gin-rest | Go | 4714 | 8.2 | 14.9 | 0.0% |
| actix-web-rest | Rust | 4551 | 8.5 | 14.9 | 0.0% |
| fastapi-rest | Python | 4481 | 8.6 | 15.3 | 0.0% |
| express-rest | Node.js | 2027 | 12.7 | 22.1 | 33.8% |
| express-orm | Node.js | 1568 | 19.4 | 44.9 | 24.4% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| async-graphql | Rust | 4207 | 8.9 | 21.4 | 0.0% |
| graphql-yoga | Node.js | 4068 | 8.4 | 29.6 | 0.0% |
| go-gqlgen | Go | 3983 | 9.4 | 23.0 | 0.0% |
| apollo-server | Node.js | 1749 | 14.7 | 23.1 | 36.4% |
| apollo-orm | Node.js | 1688 | 14.1 | 21.7 | 43.1% |
| express-graphql | Node.js | 1420 | 13.9 | 21.7 | 52.0% |
| strawberry | Python | 828 | 47.4 | 62.7 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv-nocache | Python | 4655 | 8.1 | 17.5 | 0.0% |
| fraiseql-tv | Python | 3620 | 9.2 | 33.8 | 0.0% |
| fraiseql-v | Python | 3386 | 9.8 | 34.7 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| gin-rest | Go | rest | 4714 | 8.2 | 14.9 |
| fraiseql-tv-nocache | Python | graphql-precomputed | 4655 | 8.1 | 17.5 |
| actix-web-rest | Rust | rest | 4551 | 8.5 | 14.9 |
| fastapi-rest | Python | rest | 4481 | 8.6 | 15.3 |
| async-graphql | Rust | graphql | 4207 | 8.9 | 21.4 |
| graphql-yoga | Node.js | graphql | 4068 | 8.4 | 29.6 |
| go-gqlgen | Go | graphql | 3983 | 9.4 | 23.0 |
| fraiseql-tv | Python | graphql-precomputed | 3620 | 9.2 | 33.8 |
| fraiseql-v | Python | graphql-precomputed | 3386 | 9.8 | 34.7 |
| express-rest | Node.js | rest | 2027 | 12.7 | 22.1 |
| apollo-server | Node.js | graphql | 1749 | 14.7 | 23.1 |
| apollo-orm | Node.js | graphql | 1688 | 14.1 | 21.7 |
| express-orm | Node.js | rest | 1568 | 19.4 | 44.9 |
| express-graphql | Node.js | graphql | 1420 | 13.9 | 21.7 |
| strawberry | Python | graphql | 828 | 47.4 | 62.7 |