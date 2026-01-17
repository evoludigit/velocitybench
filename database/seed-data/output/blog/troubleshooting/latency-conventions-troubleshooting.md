# **Debugging Latency Conventions: A Troubleshooting Guide**
*Ensuring Consistent, Measurable, and Actionable Latency Reporting*

---

## **1. Introduction**
Latency conventions define standardized ways to measure, record, and communicate latency metrics across distributed systems. Poor latency reporting leads to:
- Misinterpreted performance data
- Difficulty correlating issues between services
- Inconsistent SLO/SLI tracking
- Wasted time debugging "phantom" bottlenecks

This guide helps diagnose common latency convention issues and provides actionable fixes.

---

## **2. Symptom Checklist: When Latency Metrics Aren’t Working**
✅ **Inconsistent Observability** – Latency spikes in one service but not another for the same API call.
✅ **Missing or Incorrect Timestamps** – Metrics show latency, but timestamps don’t align with event order.
✅ **"Latency Too Short" Warnings** – Latency reported as < 1ms despite obvious delays (e.g., DB queries).
✅ **No Context in Traces** – Distributed traces lack latency breakdowns for individual components.
✅ **SLO Violations Without Root Cause** – Alerts fire, but latency data doesn’t pinpoint the cause.
✅ **Unified Latency ≠ Sum of Components** – Total latency isn’t the sum of service-level latencies.
✅ **Metric Overload** – Too many latency variants (e.g., p99, p99.9, average) but no clear correlation.

---

## **3. Common Issues and Fixes**

### **A. Missing or Misaligned Timestamps**
**Symptom:** Latency reported as negative or zero, or traces show out-of-order events.
**Root Cause:**
- Clock skew between services (e.g., microservices on different time zones).
- Missing start/stop timestamps in instrumentation.

#### **Fix: Use Monotonic Timers**
```java
// Correct: Use MonotonicClock for start/stop
private final MonotonicClock clock = MonotonicClock.systemUTC();

public void execute() {
    long start = clock.timestamp();
    // Business logic
    Duration latency = Duration.between(start, clock.timestamp());
    // Record latency
}
```
**Alternative (if UTC is required):**
```python
# Python (using time.monotonic_ns)
start_ns = time.monotonic_ns()
# ... business logic ...
end_ns = time.monotonic_ns()
latency_ns = end_ns - start_ns
```

---

### **B. Latency Not Matching Trace Spans**
**Symptom:** Metrics show low latency, but traces show a long chain of operations.
**Root Cause:**
- Metrics and traces use different sampling strategies.
- Metrics aggregate latencies, while traces show individual spans.

#### **Fix: Ensure Aligned Sampling**
```golang
// OpenTelemetry: Link metrics to traces
ctx, span := tracer.Start(ctx, "process_request")
defer span.End()

// Record latency in metrics
latencyMs := time.Since(startTime).Milliseconds()
metrics.MustRecord(ctx, []string{"http.server.duration"}, latencyMs)
```
**Check:**
- Use a distributed tracing tool (Jaeger, OpenTelemetry) to verify spans align with metrics.

---

### **C. Latency Too Short (Underreporting)**
**Symptom:** Latency reported as < 1ms, but clearly there’s a delay (e.g., DB query).
**Root Cause:**
- Timer starts *after* an async operation begins.
- Overhead of context switching is excluded.

#### **Fix: Measure Real Wall-Time Latency**
```rust
// Correct: Start timer before async operation
let start = Instant::now();
tokio::spawn(async {
    // Heavy DB query
    let result = query_db().await;
    let duration = start.elapsed();
    metrics::record("db.query.latency", duration);
});
```
**Bad Example (common mistake):**
```python
# Wrong: Starts timer *after* async call begins
async def process():
    start = time.monotonic_ns()
    result = await db.query()
    # Latency already includes blocking time!
```

---

### **D. Unified Latency ≠ Sum of Components**
**Symptom:** `total_latency != sum(service1_latency + service2_latency)`.
**Root Cause:**
- Overlapping timers (e.g., service1 starts, then service2 starts before service1 ends).
- Parallel execution not accounted for.

#### **Fix: Use Root Span for Total Latency**
```javascript
// OpenTelemetry: Root span captures total latency
const rootSpan = ot.trace.startSpan("process_order", { attributes: { "http.method": "POST" } });
const childSpan = ot.trace.startSpan("call_db", { parent: rootSpan });
// After async operations, rootSpan.end() provides total latency
```
**Debugging Tip:**
- Check for **overlapping spans** in distributed traces.
- Ensure no `End`/`Finish` is missed.

---

### **E. Metric Overload (Too Many Variants)**
**Symptom:** Confusion between `latency_p50`, `latency_p99`, `latency_max`.
**Root Cause:** Business logic mixes percentile and absolute metrics.

#### **Fix: Standardize on Percentiles + Histograms**
```java
// Prometheus Histogram (captures percentiles)
Histogram hist = Metrics.builder("request_latency_ms")
    .baseUnit("milliseconds")
    .explicitBucketBoundaries(10, 50, 100, 500, 1000, 5000)
    .register();

hist.observe(requestDuration.toMillis());
```
**Recommendation:**
- Use **p99, p95, p50** for SLOs.
- Avoid `latency_max` unless explicitly needed.

---

### **F. Clock Skew Between Services**
**Symptom:** Latency spikes when no real delay occurred.
**Root Cause:** Services use different system clocks.

#### **Fix: Sync Clocks via NTP or Cloud Time Sync**
```bash
# Linux: Configure NTP
sudo apt install ntp
sudo systemctl enable --now ntp
```
**For Kubernetes:**
```yaml
# Deployments should have time sync enabled
containers:
  - name: app
    image: my-app
    resources:
      time:
        enabled: true
```

---

## **4. Debugging Tools and Techniques**

### **A. Validate Timestamps**
- **Tool:** `date` (CLI) or `chrony` (NTP monitoring).
- **Check:**
  ```bash
  date -u  # Verify UTC sync
  chronyc tracking  # Check NTP skew
  ```

### **B. Correlate Metrics & Traces**
- **Tool:** OpenTelemetry Collector, Jaeger, Zipkin.
- **Command:**
  ```bash
  # Filter traces for slow requests
  jaeger query --service=api --duration-gt=1000ms
  ```

### **C. Inspect Histogram Buckets**
- **Tool:** Prometheus + Grafana.
- **Query:**
  ```promql
  histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
  ```

### **D. Check for Missing Spans**
- **Tool:** OpenTelemetry SDK’s `autoInstrumentation` flags.
- **Debug:**
  ```bash
  # Enable verbose logging for spans
  OTEL_LOG_LEVEL=debug
  ```

---

## **5. Prevention Strategies**

### **A. Instrumentation Guidelines**
✔ **Start timers before async operations.**
✔ **Use root spans for total latency.**
✔ **Avoid timer leaks (always call `End()`).**
✔ **Standardize on percentiles (p50, p99).**

### **B. CI/CD Checks**
✔ **Validate latency distribution:**
  ```bash
  # Example: Check for negative latencies
  grep -E "latency: -.*" logs && exit 1
  ```
✔ **Test clock skew tolerance:**
  ```python
  # Mock clock skew tests
  def test_latency_with_skew():
      clock = FakeMonotonicClock(100)  # 100ms skew
      assert latency(clock) >= 0
  ```

### **C. Documentation**
✔ **Document latency conventions in `README`:**
  ```markdown
  ## Latency Metrics
  - **Total:** Root span duration.
  - **Components:** Child spans (e.g., `db.query`, `external.api`).
  - **Percentiles:** p50, p99 used for SLOs.
  ```

### **D. Alerting on Anomalies**
✔ **Alert when:**
- `rate(latency < 1ms) > 0` (possible underreporting).
- `histogram_quantile(0.99, latency) > threshold`.

---

## **6. Summary of Fixes**
| **Issue**                     | **Quick Fix**                          | **Tool to Verify**               |
|--------------------------------|----------------------------------------|-----------------------------------|
| **Negative Latency**           | Use `MonotonicClock`                   | `time.monotonic_ns()`             |
| **Missing Trace Context**      | Link spans to root span                | OpenTelemetry traces              |
| **Latency Underreporting**     | Measure before async ops               | Distributed tracing               |
| **Clock Skew**                 | Sync via NTP                           | `chronyc tracking`                |
| **Metric Overload**            | Standardize on percentiles             | Prometheus histograms             |

---
**Final Tip:** If latency data feels "off," **always verify timestamps first**—90% of latency issues stem from clock or timer misalignment.

---
**References:**
- [OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/semantic-conventions)
- [Prometheus Histogram Docs](https://prometheus.io/docs/practices/histograms/)
- [Latency Best Practices (Google SRE Book)](https://sre.google/sre-book/latency/)