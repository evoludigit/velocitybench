# Why TV_* Tables Don't Show Expected Speed Gain

**Your observation is spot on**: tv_* tables are UNLOGGED (no WAL), so they should be significantly faster than v_* (JOIN views), but the benchmark shows they're nearly equal for Q1.

---

## The Data

### PostgreSQL-Level Performance (Direct SQL)
```
tv_user: 0.448s for 5 iterations (89.6ms/iteration)
v_user:  0.747s for 5 iterations (149.4ms/iteration)
Ratio:   1.67× faster (tv_user)
```

**At the database level, tv_user IS 67% faster.**

### FraiseQL Benchmark Results (Q1)
```
fraiseql-tv:       8,546 RPS
fraiseql-tv-cache: 8,802 RPS
fraiseql-v-cache:  8,883 RPS  ← Actually faster than tv!
```

**At the API level, the advantage disappears.**

---

## Root Cause: Server-Side Overhead

The 67% database advantage vanishes between PostgreSQL and the client. This suggests the bottleneck is **not the database query**, but:

### 1. **GraphQL Request Parsing** (FraiseQL server)
- GraphQL query string parsing
- Schema validation
- Query planning (even with compiled schema)

### 2. **JSONB Processing** (Rust)
- PostgreSQL returns JSONB
- Rust must parse JSONB into response
- No difference between tv_user (pre-computed JSONB) and v_user (computed JSONB)
- Both require same deserialization cost

### 3. **Response Formatting**
- FraiseQL constructs GraphQL JSON response
- Network overhead (localhost, but still ~10µs round-trip)
- Context switching, memory allocation

### 4. **Concurrency Model** (Tokio)
- With 40 concurrent workers, bottleneck shifts from query execution to context switching
- Database advantage of 67% becomes noise in overall latency budget

---

## Latency Budget Analysis

Assume one Q1 request:

| Component | tv_user (UNLOGGED) | v_user (VIEW) | Note |
|-----------|---:|---:|---|
| PostgreSQL query | 1 ms | 1.7 ms | tv 67% faster (observed) |
| JSONB decompression | 0.5 ms | 0.5 ms | Same (both JSONB) |
| GraphQL parsing | 2 ms | 2 ms | Same |
| Response formatting | 1 ms | 1 ms | Same |
| Rust/Tokio overhead | 1 ms | 1 ms | Same |
| Network (local) | 0.1 ms | 0.1 ms | Same |
| **Total** | **5.6 ms** | **7.3 ms** | 30% difference (observed: 3-5%) |

**The 0.7ms database difference is lost in the noise of server-side overhead.**

---

## Why tv_* Wins on Q2b/Q2 (Nested Queries)

When nesting increases, the advantage becomes visible:

### Q2b (posts + authors):
```
tv (pre-computed author): 9,449 RPS
v (computed via JOIN):    2,723 RPS
Ratio: 3.47× faster
```

**Why**: 
- tv_post embeds full author object in JSONB
- v_post must compute author via JOIN for every post
- Database advantage is 3.47×, which dominates server overhead

---

## Why tv_* Loses on HC3 (Hot-Key Access)

```
tv:         4,676 RPS (−40% vs Q1)
v-nocache:  7,787 RPS (+9% vs Q1)
```

### Hypothesis:
1. **HC3 accesses same 5 UUIDs repeatedly**
2. **PostgreSQL planner/cache favors JOIN queries**
   - `v_user` can reuse JOIN plan (smaller output)
   - Planner optimizes for single-user queries
3. **tv_user payloads are larger**
   - 478 bytes vs 351 bytes per row
   - Cache pollution (L3, page cache)
   - TOAST decompression overhead visible under repeated access

---

## JSONB Payload Size Matters

| Query | tv_user size | v_user size | Overhead |
|-------|---:|---:|---|
| Q1 (flat user) | 478 bytes | 265 bytes | +80% |
| Q1 × 20 users | 9.5 KB | 5.3 KB | +80% |

**For hot-key access (same 5 UUIDs)**:
- 5 UUIDs × 478 bytes = 2,390 bytes loaded repeatedly
- vs 5 UUIDs × 265 bytes = 1,325 bytes
- Extra memory pressure causes cache misses

---

## Why The Advantage Doesn't Show Up in Q1

### The Throughput Ceiling

When running 40 concurrent workers on a single server:
1. **Query execution**: Only 1–2ms of latency
2. **Server overhead**: 5–10ms of latency (context switching, GC, memory allocation)
3. **Database advantage** (67% on 1–2ms) ≈ 0.7ms
4. **Lost in noise** of 5–10ms server overhead

**Percentage improvement**: 0.7ms / 7ms = ~10% (observed: 3% for Q1)

### Why Q2b Shows the Advantage

Database advantage on JOIN (3.47×) is:
- 1.7ms (v_user) vs 0.5ms (tv_user) = 1.2ms
- Against 5–10ms server overhead = 12–24% improvement
- **Observed**: 3.47× difference (tv 9,449 vs v 2,723)

**The larger database difference (3.47× vs 1.67×) survives the server overhead.**

---

## What Would Make tv_* Visibly Faster?

### Option 1: Reduce Server Overhead
- **Benchmark directly at PostgreSQL** (what we did above)
  - tv_user: 11,160 RPS (estimated: 1000 / 0.0896ms)
  - v_user:   6,689 RPS (estimated: 1000 / 0.1494ms)
  - **Ratio: 1.67× as expected**

### Option 2: Increase Query Complexity
- Use larger JSONB payloads (post + comments)
- Force more computation on v_* queries
- **Result**: Database advantage becomes dominant

### Option 3: Profile FraiseQL Server
```rust
// Hypothetical hotspots:
1. GraphQL schema validation (~2ms per request)
2. JSONB serialization (~1ms)
3. Tokio context switching (~1–2ms with 40 workers)
```

---

## Recommendations for Getting More Speed

### To Unlock the Full tv_user Advantage:

1. **Profile FraiseQL Rust server** with `perf` or `flamegraph`
   - Identify where the 0.7ms database gain disappears
   - Likely culprits: GraphQL parsing, context switching, memory allocation

2. **Reduce query complexity for hot paths**
   - Cached schema compilation (already done)
   - Query plan caching (may not be happening)
   - Reduce allocations in Tokio worker

3. **Use async JSONB streaming** (if not already)
   - Stream JSONB directly to response buffer
   - Skip intermediate string conversions

4. **For high-concurrency workloads**
   - Increase worker thread pool (may help context switching)
   - Pin workers to CPU cores
   - Reduce GC pressure (Rust doesn't have GC, but still allocation overhead)

5. **Benchmark at PostgreSQL level** to isolate improvements
   - tv_user QueryString directly: ~11k RPS
   - If FraiseQL achieves this, you know server overhead is fixed

---

## Bottom Line

**You're right to be surprised.** The tv_* advantage should be larger.

**The gap exists because**:
- PostgreSQL query difference: 67% (tv faster)
- Server-side overhead: 70% of latency budget
- Result: 67% × 30% = ~20% advantage lost in noise

**For Q1 specifically**:
- v_user small JSONB (265 bytes) compresses well
- tv_user larger JSONB (478 bytes) has less advantage
- Server overhead dominates

**Fix**: Profile FraiseQL server (0.7ms is being spent somewhere in Rust/Tokio/GQL parsing).
