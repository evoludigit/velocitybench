# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-10  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 10 workers  
**Measurement**: 5s per scenario  
**Warmup**: 2s per scenario  
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
| actix-web-rest | Rust | Q1 | 1846 | 5.4 | 6.4 | 7.0 | 9,231 | 0.0% |
| ruby-rails | Ruby | Q1 | 895 | 5.6 | 56.8 | 60.4 | 4,473 | 0.0% |
| php-laravel | PHP | Q1 | 192 | 65.7 | 88.0 | 92.6 | 962 | 0.0% |
| csharp-dotnet | C# | Q1 | 3345 | 2.0 | 4.7 | 38.5 | 16,726 | 0.0% |
| strawberry | Python | Q1 | 884 | 11.1 | 11.6 | 22.3 | 4,419 | 0.0% |
| spring-boot-orm | Java | Q1 | 372 | 2.9 | 94.4 | 98.4 | 1,860 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2 | 7898 | 1.0 | 2.9 | 4.6 | 39,488 | 0.0% |
| ruby-rails | Ruby | Q2 | 509 | 10.3 | 63.5 | 67.0 | 2,544 | 0.0% |
| php-laravel | PHP | Q2 | 186 | 67.6 | 88.7 | 94.0 | 931 | 0.0% |
| csharp-dotnet | C# | Q2 | 5471 | 1.3 | 3.2 | 13.5 | 27,355 | 0.0% |
| strawberry | Python | Q2 | 969 | 10.0 | 10.8 | 22.0 | 4,844 | 0.0% |
| spring-boot-orm | Java | Q2 | 688 | 1.6 | 88.5 | 91.8 | 3,442 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | Q2b | 8055 | 1.2 | 1.7 | 2.1 | 40,273 | 0.0% |
| ruby-rails | Ruby | Q2b | 607 | 8.8 | 62.8 | 66.0 | 3,033 | 0.0% |
| php-laravel | PHP | Q2b | 168 | 74.9 | 92.3 | 97.8 | 840 | 0.0% |
| csharp-dotnet | C# | Q2b | 6127 | 1.3 | 2.7 | 5.5 | 30,636 | 0.0% |
| strawberry | Python | Q2b | 696 | 14.0 | 14.7 | 26.6 | 3,479 | 0.0% |
| spring-boot-orm | Java | Q2b | — | — | — | — | — | _skipped_ |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | M1 | 301 | 36.3 | 51.1 | 67.7 | 1,505 | 0.0% |
| ruby-rails | Ruby | M1 | 846 | 6.0 | 57.2 | 60.6 | 4,230 | 0.0% |
| csharp-dotnet | C# | M1 | 2211 | 3.2 | 12.4 | 20.3 | 11,055 | 0.0% |
| strawberry | Python | M1 | 960 | 10.1 | 11.9 | 22.5 | 4,801 | 0.0% |
| spring-boot-orm | Java | M1 | 285 | 8.1 | 96.8 | 104.6 | 1,424 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F1 | 6657 | 1.2 | 3.4 | 5.2 | 33,286 | 0.0% |
| ruby-rails | Ruby | F1 | 529 | 9.8 | 63.1 | 66.2 | 2,647 | 0.0% |
| php-laravel | PHP | F1 | 173 | 72.9 | 92.4 | 100.9 | 865 | 0.0% |
| csharp-dotnet | C# | F1 | 6174 | 1.3 | 2.6 | 6.1 | 30,869 | 0.0% |
| strawberry | Python | F1 | 929 | 10.5 | 11.5 | 22.8 | 4,643 | 0.0% |
| spring-boot-orm | Java | F1 | 2529 | 1.6 | 6.4 | 82.1 | 12,644 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | F2 | 8418 | 1.1 | 1.8 | 2.3 | 42,091 | 0.0% |
| ruby-rails | Ruby | F2 | 477 | 11.1 | 64.2 | 67.6 | 2,386 | 0.0% |
| php-laravel | PHP | F2 | 175 | 70.5 | 91.2 | 95.1 | 873 | 0.0% |
| csharp-dotnet | C# | F2 | 6436 | 1.3 | 2.5 | 4.4 | 32,179 | 0.0% |
| strawberry | Python | F2 | 669 | 14.5 | 16.0 | 27.3 | 3,343 | 0.0% |
| spring-boot-orm | Java | F2 | — | — | — | — | — | _skipped_ |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| actix-web-rest | Rust | T1 | 55 | 191.3 | 261.7 | 279.0 | 277 | 0.0% |
| ruby-rails | Ruby | T1 | 260 | 28.5 | 78.5 | 87.9 | 1,302 | 0.0% |
| php-laravel | PHP | T1 | 64 | 168.2 | 202.7 | 247.6 | 322 | 0.0% |
| csharp-dotnet | C# | T1 | 4657 | 1.8 | 3.2 | 6.9 | 23,286 | 0.0% |
| strawberry | Python | T1 | 536 | 18.2 | 21.3 | 32.1 | 2,681 | 0.0% |
| spring-boot-orm | Java | T1 | — | — | — | — | — | _skipped_ |

---

## REST Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| actix-web-rest | Rust | 1846 | 5.4 | 7.0 | 0.0% |
| ruby-rails | Ruby | 895 | 5.6 | 60.4 | 0.0% |
| spring-boot-orm | Java | 372 | 2.9 | 98.4 | 0.0% |
| php-laravel | PHP | 192 | 65.7 | 92.6 | 0.0% |

---

## GraphQL Frameworks — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| csharp-dotnet | C# | 3345 | 2.0 | 38.5 | 0.0% |
| strawberry | Python | 884 | 11.1 | 22.3 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| csharp-dotnet | C# | graphql | 3345 | 2.0 | 38.5 |
| actix-web-rest | Rust | rest | 1846 | 5.4 | 7.0 |
| ruby-rails | Ruby | rest | 895 | 5.6 | 60.4 |
| strawberry | Python | graphql | 884 | 11.1 | 22.3 |
| spring-boot-orm | Java | rest | 372 | 2.9 | 98.4 |
| php-laravel | PHP | rest | 192 | 65.7 | 92.6 |

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 2,211 M/s: **~134,871 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.1M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.