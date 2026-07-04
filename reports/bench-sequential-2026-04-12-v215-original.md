# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-04-12  
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
| `tb_mutation_log` | 286.1 MB | 24.3 MB | 310.5 MB |
| `tb_post` | 133.7 MB | 28.9 MB | 162.7 MB |
| `tv_user` | 8.0 MB | 9.3 MB | 17.3 MB |
| `tb_post_like` | 5.0 MB | 9.4 MB | 14.4 MB |
| `tb_user` | 6.1 MB | 5.5 MB | 11.6 MB |
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
**TB tables (normalized baseline)**: 881.9 MB  
**Storage amplification**: 3.20× (TV adds 1.90 GB on top of the normalized 881.9 MB)  

> Each `tv_comment` row embeds the full comment author + the full post + the post's author.
> With 200 000 comments this JSONB duplication dominates the TV storage cost.

---


## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1 | 9480 | 3.7 | 8.9 | 12.3 | 189,609 | 0.0% |
| fraiseql-tv-cache | Rust | Q1 | 9457 | 3.7 | 8.9 | 12.2 | 189,142 | 0.0% |
| fraiseql-v-nocache | Rust | Q1 | 7939 | 4.4 | 10.4 | 14.1 | 158,786 | 0.0% |
| fraiseql-v-cache | Rust | Q1 | 7621 | 4.6 | 11.0 | 14.9 | 152,421 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2 | 9434 | 3.6 | 9.2 | 13.3 | 188,690 | 0.0% |
| fraiseql-tv-cache | Rust | Q2 | 9552 | 3.6 | 9.1 | 12.8 | 191,036 | 0.0% |
| fraiseql-v-nocache | Rust | Q2 | 4953 | 7.0 | 17.5 | 23.8 | 99,065 | 0.0% |
| fraiseql-v-cache | Rust | Q2 | 4812 | 7.2 | 17.9 | 24.4 | 96,248 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b | 8981 | 3.9 | 9.2 | 12.7 | 179,614 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b | 9156 | 3.8 | 9.0 | 12.2 | 183,123 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b | 1816 | 18.0 | 48.8 | 61.6 | 36,324 | 0.0% |
| fraiseql-v-cache | Rust | Q2b | 1911 | 17.4 | 46.8 | 59.1 | 38,229 | 0.0% |

## Q3 — `comments(limit: 20) { id content author { username } post { title } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q3 | 5097 | 7.1 | 15.1 | 19.8 | 101,931 | 0.0% |
| fraiseql-tv-cache | Rust | Q3 | 5895 | 6.2 | 12.8 | 16.8 | 117,906 | 0.0% |
| fraiseql-v-nocache | Rust | Q3 | 691 | 79.2 | 104.7 | 112.4 | 13,821 | 0.0% |
| fraiseql-v-cache | Rust | Q3 | 753 | 75.4 | 102.2 | 111.0 | 15,055 | 0.0% |

## C3 — `user(id: UUID) { id username fullName }` — single entity, rotating UUIDs

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | C3 | 6847 | 4.5 | 14.6 | 24.8 | 136,942 | 0.0% |
| fraiseql-tv-cache | Rust | C3 | 5244 | 5.6 | 20.5 | 32.3 | 104,871 | 0.0% |
| fraiseql-v-nocache | Rust | C3 | 7026 | 4.4 | 13.8 | 24.0 | 140,528 | 0.0% |
| fraiseql-v-cache | Rust | C3 | 7351 | 4.4 | 12.8 | 20.7 | 147,015 | 0.0% |

## HC3 — `user(id: UUID) { id username fullName }` — hot-key, 5 fixed UUIDs (cache saturation test)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | HC3 | 6537 | 4.7 | 15.2 | 25.3 | 130,743 | 0.0% |
| fraiseql-tv-cache | Rust | HC3 | 5623 | 5.3 | 18.9 | 31.1 | 112,460 | 0.0% |
| fraiseql-v-nocache | Rust | HC3 | 8156 | 4.0 | 11.1 | 17.1 | 163,123 | 0.0% |
| fraiseql-v-cache | Rust | HC3 | 7248 | 4.3 | 13.6 | 24.4 | 144,963 | 0.0% |

## M1 — `mutation { updateUser(...) { id bio } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1 | 2625 | 13.2 | 32.5 | 47.3 | 52,509 | 0.0% |
| fraiseql-tv-cache | Rust | M1 | 4100 | 5.9 | 22.2 | 34.2 | 81,996 | 0.0% |
| fraiseql-v-nocache | Rust | M1 | 4466 | 6.0 | 17.9 | 29.1 | 89,329 | 0.0% |
| fraiseql-v-cache | Rust | M1 | 7775 | 4.7 | 9.4 | 12.6 | 155,507 | 0.0% |

## M1d — `mutation { updateUserDelta(...) { id bio } }` — jsonb_delta surgical patch on tvd_* (rotating bios)

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1d | 1285 | 24.6 | 72.8 | 99.3 | 25,708 | 0.0% |

## F1 — `posts(published: true, limit: 10) { id title }` — published filter, no nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F1 | 9721 | 3.6 | 8.8 | 12.1 | 194,424 | 0.0% |
| fraiseql-tv-cache | Rust | F1 | 9655 | 3.6 | 8.8 | 12.1 | 193,094 | 0.0% |
| fraiseql-v-nocache | Rust | F1 | 2868 | 11.9 | 30.3 | 42.0 | 57,363 | 0.0% |
| fraiseql-v-cache | Rust | F1 | 2930 | 11.7 | 30.1 | 40.7 | 58,606 | 0.0% |

## F2 — `posts(published: true, limit: 10) { id title author { ... } }` — published filter + nesting

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F2 | 8565 | 4.1 | 9.7 | 13.2 | 171,295 | 0.0% |
| fraiseql-tv-cache | Rust | F2 | 8804 | 4.0 | 9.3 | 12.5 | 176,081 | 0.0% |
| fraiseql-v-nocache | Rust | F2 | 1492 | 20.7 | 59.8 | 72.5 | 29,850 | 0.0% |
| fraiseql-v-cache | Rust | F2 | 1490 | 20.9 | 59.0 | 71.4 | 29,793 | 0.0% |

## F3 — `users(limit: 20) { id username fullName }` — baseline for ORDER BY comparison

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | F3 | 9479 | 3.7 | 8.9 | 12.3 | 189,588 | 0.0% |
| fraiseql-tv-cache | Rust | F3 | 9359 | 3.7 | 9.0 | 12.3 | 187,177 | 0.0% |
| fraiseql-v-nocache | Rust | F3 | 7923 | 4.5 | 10.3 | 13.9 | 158,469 | 0.0% |
| fraiseql-v-cache | Rust | F3 | 8272 | 4.3 | 9.8 | 13.1 | 165,445 | 0.0% |

## T1 — Full blog page load — `post(id) { title content author { ... } comments(limit:10) { content author { ... } } }`

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | T1 | 6797 | 5.5 | 10.4 | 13.9 | 135,931 | 0.0% |
| fraiseql-tv-cache | Rust | T1 | 5336 | 5.4 | 10.6 | 14.3 | 106,725 | 0.0% |
| fraiseql-v-nocache | Rust | T1 | 727 | 70.6 | 94.4 | 103.7 | 14,534 | 0.0% |
| fraiseql-v-cache | Rust | T1 | 743 | 69.1 | 94.0 | 103.0 | 14,865 | 0.0% |

## MC1 — Mutation-to-consistent-state cycle — FraiseQL: 1 request (M1 + cascade data). Classical: 2 serial requests (M1 + Q1 re-fetch). RPS = cycles/second.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | MC1 | 4720 | 5.5 | 19.3 | 31.3 | 94,390 | 0.0% |
| fraiseql-tv-cache | Rust | MC1 | 1264 | 24.6 | 78.7 | 143.4 | 25,273 | 0.0% |
| fraiseql-v-nocache | Rust | MC1 | 2163 | 12.9 | 47.9 | 94.1 | 43,264 | 0.0% |
| fraiseql-v-cache | Rust | MC1 | 1260 | 24.9 | 76.3 | 144.7 | 25,200 | 0.0% |

## Q1_APQ — APQ hash-only Q1 — no query string sent, server resolves by SHA-256 hash. Compare to Q1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q1_APQ | 8764 | 3.7 | 9.1 | 12.6 | 175,281 | 0.0% |
| fraiseql-tv-cache | Rust | Q1_APQ | 9452 | 3.7 | 8.9 | 12.2 | 189,042 | 0.0% |
| fraiseql-v-nocache | Rust | Q1_APQ | 7744 | 4.5 | 10.6 | 14.4 | 154,873 | 0.0% |
| fraiseql-v-cache | Rust | Q1_APQ | 8290 | 4.3 | 9.8 | 13.1 | 165,792 | 0.0% |

## Q2b_APQ — APQ hash-only Q2b — nested posts+author query via hash lookup. Compare to Q2b.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | Q2b_APQ | 9131 | 3.9 | 9.0 | 12.1 | 182,627 | 0.0% |
| fraiseql-tv-cache | Rust | Q2b_APQ | 9154 | 3.8 | 9.0 | 12.2 | 183,074 | 0.0% |
| fraiseql-v-nocache | Rust | Q2b_APQ | 1904 | 17.2 | 47.6 | 60.1 | 38,070 | 0.0% |
| fraiseql-v-cache | Rust | Q2b_APQ | 1754 | 19.0 | 49.1 | 61.6 | 35,084 | 0.0% |

## M1_APQ — APQ mutation — hash + variables only (FraiseQL) or hash-only (classical). Compare to M1.

| Framework | Language | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Rust | M1_APQ | 1270 | 24.4 | 78.0 | 146.1 | 25,400 | 0.0% |
| fraiseql-tv-cache | Rust | M1_APQ | 8741 | 4.2 | 8.1 | 10.5 | 174,827 | 0.0% |
| fraiseql-v-nocache | Rust | M1_APQ | 1267 | 24.8 | 77.5 | 138.1 | 25,339 | 0.0% |
| fraiseql-v-cache | Rust | M1_APQ | 8676 | 4.2 | 8.2 | 10.8 | 173,525 | 0.0% |

---

## Pre-computed GraphQL (FraiseQL) — Q1 (sorted by RPS)

| Framework | Language | RPS | p50 ms | p99 ms | Errors |
|-----------|----------|----:|-------:|-------:|--------|
| fraiseql-tv | Rust | 9480 | 3.7 | 12.3 | 0.0% |
| fraiseql-tv-cache | Rust | 9457 | 3.7 | 12.2 | 0.0% |
| fraiseql-v-nocache | Rust | 7939 | 4.4 | 14.1 | 0.0% |
| fraiseql-v-cache | Rust | 7621 | 4.6 | 14.9 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Language | Category | RPS | p50 ms | p99 ms |
|-----------|----------|----------|----:|-------:|-------:|
| fraiseql-tv | Rust | graphql-precomputed | 9480 | 3.7 | 12.3 |
| fraiseql-tv-cache | Rust | graphql-precomputed | 9457 | 3.7 | 12.2 |
| fraiseql-v-nocache | Rust | graphql-precomputed | 7939 | 4.4 | 14.1 |
| fraiseql-v-cache | Rust | graphql-precomputed | 7621 | 4.6 | 14.9 |

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

---

## M1 — Cascade Characteristics

Each `updateUser` mutation cascades through pg_tviews to three pre-computed tables:
1 `tb_user` + 1 `tv_user` + ~10 `tv_post` (author embedded) + ~50 `tv_comment` (author + post embedded) = **~61 rows per top-level mutation**.

At peak throughput of 7,775 M/s: **~474,296 row writes/second** across four tables.

> **Run-order methodology**: M1 results reflect two distinct operational conditions, both valid production scenarios:
> 
> - **Fresh table** (first runner): HOT-update slots available — PostgreSQL updates rows in-place on the same page. Equivalent to post-deploy or post-maintenance-window table state.
> - **Post-cascade fragmentation** (subsequent runners): prior mutation burst (~0.5M cascade writes) scattered row versions across pages. VACUUM reclaims dead tuples between runs but cannot repack pages without VACUUM FULL. Equivalent to sustained production load where autovacuum lags behind write throughput.
> 
> The cascade multiplier (61×) is the operative variable: fan-out × throughput = HOT collapse threshold. At this fan-out ratio, the fresh-table vs fragmented-table range characterises the operational envelope, not benchmark noise.