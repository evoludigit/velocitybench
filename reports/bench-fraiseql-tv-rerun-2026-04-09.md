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
| `tb_mutation_log` | 3.60 GB | 307.6 MB | 3.90 GB |
| `tv_comment` | 819.5 MB | 354.7 MB | 1.91 GB |
| `tvd_comment` | 477.6 MB | 51.4 MB | 1.13 GB |
| `tb_comment` | 294.6 MB | 82.2 MB | 376.9 MB |
| `tv_post` | 219.3 MB | 78.6 MB | 351.7 MB |
| `tvd_post` | 134.0 MB | 8.5 MB | 191.4 MB |
| `tb_post` | 133.6 MB | 20.0 MB | 153.6 MB |
| `tb_post_like` | 5.0 MB | 9.3 MB | 14.3 MB |
| `tv_user` | 8.2 MB | 6.0 MB | 14.2 MB |
| `tb_user` | 6.2 MB | 3.7 MB | 10.0 MB |
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
**TB tables (normalized baseline)**: 4.45 GB  
**Storage amplification**: 1.51× (TV adds 2.26 GB on top of the normalized 4.45 GB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 11059 | 3.3 | 7.1 | 9.5 | 221,187 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 11315 | 3.1 | 7.4 | 10.0 | 226,293 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 9651 | 3.8 | 7.7 | 10.2 | 193,018 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 4957 | 7.8 | 11.1 | 13.0 | 99,135 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 9668 | 3.5 | 9.1 | 13.1 | 193,350 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 8716 | 3.7 | 10.7 | 17.8 | 174,318 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 3593 | 8.6 | 24.4 | 36.4 | 71,854 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 6020 | 4.1 | 17.9 | 55.0 | 120,390 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 10858 | 3.2 | 7.6 | 10.2 | 217,156 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 9425 | 4.0 | 7.5 | 9.8 | 188,498 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 10899 | 3.3 | 7.2 | 9.7 | 217,986 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 1380 | 21.5 | 65.9 | 77.9 | 27,601 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 11059 | 3.3 | 9.5 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 11059 | 3.3 | 9.5 |

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 3,593 M/s: **~219,154 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.2M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.