# VelocityBench — Sequential Isolation Benchmark Results

**Date**: 2026-02-22  
**Dataset**: MEDIUM — 10 000 users · 50 000 posts · 200 000 comments  
**Method**: Sequential isolation — each framework runs alone, PostgreSQL stays up  
**Concurrency**: 40 workers  
**Measurement**: 20s per scenario  
**Warmup**: 5s per scenario  
**Cooldown**: 10s between frameworks  

---

## Q1 — `users(limit: 20) { id username fullName }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q1 | 2148 | 16.2 | 39.1 | 50.0 | 42,957 | 0.0% |
| fraiseql-tv-nocache | Q1 | 3122 | 10.3 | 30.5 | 44.5 | 62,440 | 0.0% |

## Q2 — `posts(limit: 10) { id title }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2 | 1635 | 23.9 | 48.4 | 59.7 | 32,696 | 0.0% |
| fraiseql-tv-nocache | Q2 | 2802 | 11.6 | 33.0 | 46.0 | 56,035 | 0.0% |

## Q2b — `posts(limit: 10) { id title author { username fullName } }`

| Framework | Query | RPS | p50 ms | p95 ms | p99 ms | Requests | Errors |
|-----------|-------|----:|-------:|-------:|-------:|---------:|--------|
| fraiseql-tv | Q2b | 1705 | 21.5 | 48.6 | 60.5 | 34,101 | 0.0% |
| fraiseql-tv-nocache | Q2b | 3498 | 9.8 | 23.6 | 37.1 | 69,963 | 0.0% |

---

## Summary — Q1 Cross-Framework (sorted by RPS)

| Framework | Cache | RPS | p50 ms | p99 ms |
|-----------|-------|----:|-------:|-------:|
| fraiseql-tv-nocache | off | 3122 | 10.3 | 44.5 |
| fraiseql-tv | on | 2148 | 16.2 | 50.0 |

---

## Phase 1 Analysis — Cache Effect in rc.3

### Finding: Cache overhead is negative in rc.3

The cache-enabled variant is **1.45–2.05× slower** than cache-disabled across all queries:

| Query | cache=off RPS | cache=on RPS | Overhead factor |
|-------|-------------:|-------------:|----------------:|
| Q1    | 3 122        | 2 148        | −31%            |
| Q2    | 2 802        | 1 635        | −42%            |
| Q2b   | 3 498        | 1 705        | −51%            |

The LRU cache in rc.3 adds per-request overhead (SHA-256 keying, lock acquisition)
that exceeds the read path cost for these queries. Cache hits are **slower** than
cold database reads.

Expected behavior (as seen in beta.4): cache-hit p50 < 2 ms, ≥ 5× speedup over cold.
Observed behavior (rc.3): cache-hit throughput is 31–51% below cold-read.

### Finding: Cold-read performance is also regressed

Even with cache disabled, fraiseql-tv-nocache achieves 3 122 RPS vs beta.4's 5 177 RPS
(−40%). The `refactor(cli): eliminate double-optimize` commit in rc.2 degraded the
compiled schema execution path independently of the cache regression.

### Regression summary

| Version   | Configuration | Q1 RPS | vs beta.4 |
|-----------|---------------|-------:|----------:|
| beta.4    | cache=on      | 5 177  | baseline  |
| rc.3      | cache=on      | 2 148  | −58%      |
| rc.3      | cache=off     | 3 122  | −40%      |

Both regressions are in the compiled execution engine, not in the benchmark setup.
They should be reported upstream against the fraiseql repository.