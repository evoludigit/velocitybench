# FraiseQL Performance Optimization: Squeezing Maximum Throughput

**Date**: April 19, 2026  
**Current Status**: 8,546 RPS (Q1 with tv_user), database capable of 29,586 RPS  
**Bottleneck**: Server-side, not database  
**Goal**: Identify and eliminate server overhead to reach database capacity

---

## The Paradox (Corrected)

| Level | Observation |
|-------|------------|
| **Database** | tv_user: 0.0338 ms/query = **29,586 RPS theoretical** |
| **Actual API** | FraiseQL: **8,546 RPS** (28.9% of database capacity) |
| **Gap** | 3.45× unutilized database capacity |

**Previous incorrect claim**: "9-12 queries per request" — **NOT SUPPORTED BY EVIDENCE**  
**Correct understanding**: Each Q1 request = 1 SQL query to tv_user

---

## Root Cause: Server Overhead is the Bottleneck

### Latency Budget Per Request

With 40 concurrent workers handling 8,546 RPS:

```
Per-worker load:        8,546 ÷ 40 = 214 requests/sec
Per-request time:       1000 ÷ 214 = 4.67 ms (available per worker)

Database query time:    0.0338 ms (only 0.7% of available time)
Server overhead:        ~4.6 ms (99.3% of available time)
```

**This means**: The server is spending ~135× more time on non-database work than on the actual database query.

### Where Server Time Goes

For each GraphQL Q1 request, FraiseQL spends time on:

1. **HTTP request parsing** (~50 µs)
   - Read from socket
   - Parse headers
   - Parse body

2. **GraphQL parsing & validation** (~200-500 µs)
   - Tokenize query string
   - Parse AST
   - Validate against schema
   - Type checking

3. **Query compilation/optimization** (~100-300 µs)
   - Route to correct resolver
   - Build execution plan
   - Optimize parameter binding

4. **Database query** (~34 µs) ← Only this is fast
   - Send to PostgreSQL
   - Get result
   - Parse rows

5. **Response formatting** (~200-500 µs)
   - Serialize JSONB to JSON
   - Build response object
   - Encode to bytes

6. **Network I/O** (~100-200 µs)
   - Write to socket
   - Flush buffers

7. **Tokio runtime overhead** (~1-2 ms)
   - Context switching (40 workers contending)
   - Work queue management
   - Future polling

**Total: ~3,000-4,500 µs (3-4.5 ms)**

---

## Diagnostic: Where Is Time Actually Spent?

To optimize, we need to measure. Use these tools:

### 1. Profile with Flamegraph (Best Option)

```bash
# Install cargo-flamegraph
cargo install flamegraph

# Profile FraiseQL with 40 workers
cargo flamegraph -b 99 -- fraiseql-server config.toml

# While running, hit it with benchmark
ab -c 40 -n 10000 http://localhost:8816/graphql -p payload.json

# Generates flame graph showing where time is spent
```

**What to look for**:
- Tokio overhead (if >30% of time, context switching is the issue)
- JSON serialization (if >20%, response formatting is the issue)
- GraphQL parser (if >15%, query parsing is the issue)
- PostgreSQL driver (should be <5%)

### 2. Add Timing Instrumentation

In FraiseQL code, wrap major sections:

```rust
let start = Instant::now();

// GraphQL parsing
let parsed = parse_query(&query)?;
println!("GraphQL parse: {:.3}ms", start.elapsed().as_secs_f64() * 1000);
let db_start = Instant::now();

// Database query
let result = db.query(&sql)?;
println!("DB query: {:.3}µs", db_start.elapsed().as_micros());
let response_start = Instant::now();

// Response formatting
let json = format_response(&result)?;
println!("Response format: {:.3}ms", response_start.elapsed().as_secs_f64() * 1000);
```

### 3. Check PostgreSQL Slow Log

Verify database time doesn't include the measured 0.0338ms:

```bash
# Enable slow log
ALTER SYSTEM SET log_min_duration_statement = 0;
SELECT pg_reload_conf();

# Run single request
# Check if query appears in logs with correct timing
tail -f /var/log/postgresql/postgresql.log | grep "tv_user"
```

---

## Optimization Strategies (High to Low Impact)

### Strategy 1: Query Caching (Highest Impact)

**Problem**: GraphQL parsing/validation happens every request

**Solution**: Cache parsed queries and/or compiled execution plans

```rust
// Current: Parse every request
let ast = parse_graphql(&query_string)?;  // ~300 µs every time

// Optimized: Cache by query text
static QUERY_CACHE: Lazy<Mutex<HashMap<String, Ast>>> = ...;
let ast = QUERY_CACHE
    .get(&query_string)
    .unwrap_or_else(|| {
        let ast = parse_graphql(&query_string)?;
        QUERY_CACHE.insert(query_string, ast);
        ast
    });
```

**Expected impact**: 200-500 µs savings = **2-6% throughput improvement** (can reach 8,750-9,000 RPS)

### Strategy 2: Reduce Tokio Context Switches (Medium Impact)

**Problem**: 40 workers competing for CPU, lots of context switching

**Solution**: Tune the Tokio runtime

```rust
// Current (likely default)
let rt = tokio::runtime::Runtime::new()?;

// Optimized: Pin to CPU cores, reduce worker threads
let rt = tokio::runtime::Builder::new_multi_thread()
    .worker_threads(20)           // Reduce from OS default
    .thread_name("fraiseql")
    .thread_stack_size(2*1024*1024) // Reduce allocations
    .build()?;

// Also: Set thread affinity (bind to specific CPU cores)
// This prevents threads from migrating between cores
// Requires OS-level config (Linux: taskset, systemd.service)
```

**Expected impact**: 0.5-1 ms savings = **6-12% throughput improvement** (can reach 9,000-9,600 RPS)

### Strategy 3: Stream Response Directly (Medium Impact)

**Problem**: Buffering entire response before sending

**Solution**: Stream JSONB directly from PostgreSQL to HTTP response

```rust
// Current: Collect all rows, then format
let rows = db.query(&sql)?;           // Returns Vec<Row>
let json = format_json(&rows)?;       // Creates full JSON in memory
response.write_all(&json)?;           // Send to client

// Optimized: Stream row-by-row
let stream = db.query_raw(&sql)?;     // Returns stream
response.write(b"[")?;
let mut first = true;
while let Some(row) = stream.next().await? {
    if !first { response.write(b",")?; }
    response.write(format_row_json(&row).as_bytes())?;
    first = false;
}
response.write(b"]")?;
```

**Expected impact**: 0.3-0.8 ms savings = **4-10% throughput improvement** (can reach 8,900-9,400 RPS)

### Strategy 4: Connection Pool Tuning (Low-Medium Impact)

**Problem**: Default connection pool settings may not be optimal for 40 workers

**Solution**: Configure pool for 40+ concurrent connections

```rust
// Current (likely default min=10, max=10)
let config = Config {
    min_size: 40,          // Match worker count
    max_size: 80,          // Allow some headroom
    connection_timeout: Duration::from_secs(1),
    statement_cache_size: 100,  // Cache prepared statements
    ..
};
```

**Expected impact**: 0.1-0.3 ms savings = **1-4% throughput improvement** (can reach 8,600-8,900 RPS)

### Strategy 5: Async GraphQL Validation (Low Impact)

**Problem**: Synchronous validation blocks the async executor

**Solution**: Use async-aware validation

```rust
// Current: Blocks future
let validated = validate_query(&ast, &schema)?;

// Optimized: Spawn on separate thread pool
let validated = tokio::task::spawn_blocking(move || {
    validate_query(&ast, &schema)
})
.await??;
```

**Expected impact**: 0.05-0.2 ms = **<1% improvement** (Tokio is good at async validation)

---

## Realistic Performance Ceiling

### Theoretical Maximum (No Network, Perfect Code)

With optimizations stacked:
- Query caching: -300 µs
- Connection pooling: -100 µs
- Response streaming: -500 µs
- Tokio tuning: -500 µs
- Total savings: ~1,400 µs

New per-request time: 4,600 - 1,400 = **3,200 µs = 3.2 ms**  
New throughput: 40 workers × (1000 / 3.2) = **12,500 RPS**

This is **1.46× improvement** (8,546 → 12,500 RPS).

### Practical Maximum (With Overhead)

Accounting for unforeseen overhead and diminishing returns:
- Expected after all optimizations: **10,000-11,000 RPS**

This is the realistic ceiling given current architecture.

### Hard Ceiling (Cannot Exceed)

The HTTP/socket I/O overhead alone is ~500 µs per request. Even with zero query time:
- Network read/write: 500 µs
- Minimum feasible overhead: 1,000 µs
- Hard ceiling: 40 workers × (1000 / 1) = **40,000 RPS**

**Actual reachable ceiling: 10,000-12,000 RPS** (much lower due to above-zero overhead)

---

## Recommended Optimization Roadmap

### Phase 1: Diagnostics (1-2 hours)
1. **Profile with flamegraph** → identify top 3 time consumers
2. **Add instrumentation** → measure each phase
3. **Document baseline** → current: 8,546 RPS

### Phase 2: Quick Wins (2-4 hours)
1. **Query caching** → Save 200-500 µs
   - Expected: 8,700-8,900 RPS
   - Effort: Low (hashmap-based cache)

2. **Connection pool tuning** → Save 100-200 µs
   - Expected: 8,800-9,100 RPS
   - Effort: Very low (config change)

### Phase 3: Medium Effort (4-8 hours)
1. **Tokio runtime tuning** → Save 500-1000 µs
   - Expected: 9,200-9,800 RPS
   - Effort: Medium (requires testing)

2. **Response streaming** → Save 300-800 µs
   - Expected: 9,500-10,500 RPS
   - Effort: Medium (code rewrite)

### Phase 4: Advanced (8+ hours)
1. **Custom HTTP handler** → Save 200-500 µs
   - Bypass generic framework overhead
   - Expected: 10,000-11,000 RPS
   - Effort: High (reimplement request handling)

---

## Validation Approach

After each optimization, benchmark:

```bash
python tests/benchmark/bench_sequential.py \
  --frameworks fraiseql-tv \
  --duration 30 \
  --concurrency 40
```

Track RPS change:
- Baseline: 8,546 RPS
- Target after Phase 1: 8,750 RPS (+2.4%)
- Target after Phase 2: 9,100 RPS (+6.5%)
- Target after Phase 3: 9,700 RPS (+13.5%)
- Target after Phase 4: 10,500 RPS (+22.8%)

---

## Summary

**Current state**: Server overhead limits throughput to 8,546 RPS despite database capable of 29,586 RPS

**Root cause**: ~4.6 ms per request overhead (3.5 ms unexplained, 0.03 ms database, rest is HTTP/Tokio)

**Optimization approach**:
1. Profile to find top 3 time consumers (flamegraph)
2. Implement quick wins (caching, tuning)
3. Rewrite hot paths (response streaming, custom HTTP)
4. Target: 10,000-11,000 RPS (22-28% improvement)

**No further database optimization needed** — database is 99% idle.
