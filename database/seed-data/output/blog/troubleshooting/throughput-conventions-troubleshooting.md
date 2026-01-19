# **Debugging Throughput Conventions: A Troubleshooting Guide**

## **Introduction**
The **Throughput Conventions** (semantics for monitoring calculation) define how metrics like **requests per second (RPS), errors per second (EPS), active requests, etc.** should be structured to ensure consistency across distributed systems. These conventions are critical for observability, scaling decisions, and performance tuning.

This guide provides a **practical, step-by-step approach** to debugging common issues related to misconfigured or incorrectly implemented Throughput Conventions.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your system exhibits these symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Metric Mismatches** | Observed RPS/EPS doesn’t match expected workload | Incorrect scaling decisions |
| **Spikes in `active_requests`** | Sudden jumps despite stable load | Misleading concurrency assumptions |
| **Unbalanced Counters** | Some services show higher EPS than others | Debugging complexity |
| **High Latency despite Low RPS** | Slow responses even with low requests | Resource contention not captured |
| **Missing or Negative Metrics** | Counters resetting unexpectedly | Broken instrumentation |

If multiple symptoms appear, focus on **metric consistency** first.

---

## **2. Common Issues & Fixes**

### **Issue 1: Incorrect Counters ( EPS, RPS Misalignment )**
**Symptom:**
`errors_per_second` (EPS) ≠ `successful_requests_per_second` (RPS), or counters reset unexpectedly.

**Root Cause:**
- Forgetting to **increment counters only on successful executions** (EPS should only count errors).
- Using **floating-point arithmetic** for counters (leads to precision errors).
- **Resetting counters** (should be cumulative).

**Fix:**
```go
// Correct: Only increment EPS on errors
if err != nil {
    errorsPerSecond.Inc()
}

// Correct: Use integer counters (Prometheus, OpenMetrics)
var (
    totalRequests = metric.NewCounter(
        "http_requests_total",
        "Total HTTP requests",
        []string{"method", "path"},
    )
    errors = metric.NewCounter(
        "http_errors_total",
        "Total HTTP errors",
        []string{"method", "path", "status"},
    )
)
```
**Debugging Steps:**
1. Check if **EPS = RPS - successful_requests_per_second**.
2. Verify **no counter resets** (should be `int64`).
3. Use `Prometheus` or `OpenTelemetry` to inspect live metrics.

---

### **Issue 2: Active Requests (`active_requests` Mismatches)**
**Symptom:**
`active_requests` spikes arbitrarily or doesn’t reflect real concurrency.

**Root Cause:**
- **Double-counting** (e.g., incrementing on request start & finish).
- **Missing decrement** (e.g., goroutines not closing).
- **Context cancellation not tracked**.

**Fix:**
```go
// Correct: Increment on start, decrement on finish (with error handling)
func handleRequest(ctx context.Context) {
    activeRequests.Inc()
    defer func() {
        activeRequests.Dec()
    }()

    // Request processing with ctx cancellation check
    select {
    case <-ctx.Done():
        return
    default:
        // Process request...
    }
}
```
**Debugging Steps:**
1. **Profile goroutines** (`pprof`) to check for leaks.
2. **Sample active_requests** over time (use `histogram` for distribution).
3. **Validate with `netstat`/`htop`** to see real connection count.

---

### **Issue 3: Request Duration Misreporting**
**Symptom:**
`request_duration_seconds` doesn’t match real latency (e.g., 0ms or too high).

**Root Cause:**
- **Timer not started before request** (e.g., `time.Now()` called too late).
- **Timer not stopped** (e.g., missing `defer`).
- **Distributed tracing misalignment** (e.g., server-side duration ≠ client-side).

**Fix:**
```go
// Correct: Use Prometheus' Histogram with proper timing
var requestDuration = metric.NewHistogram(
    "http_request_duration_seconds",
    "Request latency",
    []string{"method", "path"},
    prometheus.DefBuckets,
)

// Start timer immediately
timer := time.Now()
defer func() {
    duration := time.Since(timer).Seconds()
    requestDuration.Observe(duration)
}()

// Process request...
```
**Debugging Steps:**
1. **Check timer placement** (should be inside the HTTP handler).
2. **Verify histogram buckets** (e.g., `DefBuckets` covers your latency range).
3. **Compare with `NewRelic`/`Datadog`** for cross-verification.

---

### **Issue 4: Distributed Context Timeout Mismatch**
**Symptom:**
Service A reports 500ms latency, but Service B reports 2s (unexpected delay).

**Root Cause:**
- **Client and server timers don’t sync** (e.g., client starts timer after call begins).
- **Context cancellation not propagated** (e.g., parent context not passed).

**Fix:**
```go
// Correct: Pass context down the call chain
func handler(ctx context.Context, w http.ResponseWriter) {
    reqCtx, cancel := context.WithTimeout(ctx, 1*time.Second)
    defer cancel()

    // Pass reqCtx to downstream calls
    go worker(reqCtx)
}
```
**Debugging Steps:**
1. **Enable distributed tracing** (`OpenTelemetry`/`Jaeger`).
2. **Check context deadlines** (`ctx.Deadline()`).
3. **Log spans** to see where delay occurs.

---

## **3. Debugging Tools & Techniques**

| **Tool** | **Use Case** | **Command/Setup** |
|----------|-------------|------------------|
| **Prometheus** | Check counters, histograms, and samples | `http://<cluster>/metrics` |
| **pprof** | Detect goroutine leaks | `go tool pprof http://localhost:6060/debug/pprof/goroutine` |
| **Netdata** | Real-time metric visualization | `netdata install` |
| **OpenTelemetry** | Distributed tracing | `otel-collector` config |
| **Grafana** | Alerts & dashboards | `prometheus + grafana` |
| **Strace** | System call blocking | `strace -c ./your_binary` |

**Advanced Debugging:**
- **Chaos Engineering:** Kill random pods (`kubectl delete pod`) to test recovery.
- **Rate Limiting:** Simulate traffic spikes (`kubectl run load-test --image=busybox --restart=Never -- sleep 60 && for i in {1..1000}; do curl http://<svc>; done`).

---

## **4. Prevention Strategies**
To avoid future issues:

### **1. Instrumentation Best Practices**
✅ **Use cumulative counters** (never reset `int64`).
✅ **Aligned timers** (start before request, stop after completion).
✅ **Distributed tracing** (ensure server/client timers match).
✅ **Histogram for latencies** (not just p99).

### **2. Testing**
- **Unit tests** for counter increments/decrements.
- **Load tests** (`k6`, `Locust`) to validate RPS/EPS.
- **Chaos tests** (random pod kills to check recovery).

### **3. Monitoring**
- **Alerts for metric anomalies** (e.g., EPS > 10% RPS).
- **Dashboards for active_requests vs. goroutines**.
- **SLO-based alerting** (e.g., "99% requests < 2s").

### **4. Documentation**
- **Add comments** explaining counter logic.
- **Annotate histograms** with expected buckets.
- **Update runbooks** for common failures.

---

## **Conclusion**
Throughput Conventions are **not optional**—they ensure observability and scalability. The key fixes are:
1. **Correct counter increments/decrements** (EPS ≠ RPS).
2. **Proper timer management** (no missed `defer`).
3. **Distributed context alignment** (timeouts must propagate).
4. **Real-time validation** (tools like `Prometheus` + `Grafana`).

**Final Checklist Before Production:**
✔ Counters are **cumulative (`int64`)**.
✔ Timers are **started before request** and **stopped via `defer`**.
✔ **Distributed tracing** syncs client/server timers.
✔ **Load tests** confirm RPS/EPS match expectations.

By following this guide, you’ll **minimize metric misreporting** and **debug faster** when issues arise. 🚀