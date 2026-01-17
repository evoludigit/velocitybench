# **[Pattern] Profiling Observability: Reference Guide**

---

## **Overview**
The **Profiling Observability** pattern enhances system diagnostics by collecting **low-overhead, high-precision execution data** (e.g., CPU sampling, memory allocation, lock contention, and I/O latency) to analyze performance bottlenecks. Unlike traditional metrics (e.g., latency percentiles), profiling provides **deep insights into code execution**, enabling targeted optimizations. This pattern integrates with **observability stacks** (telemetry, tracing, and logs) to correlate profiling data with business context.

Key use cases:
- Identifying **CPU-bound loops**, **memory leaks**, or **inefficient algorithms**.
- Analyzing **real-world latency** (not just request timings).
- Pinpointing **hot paths** in microservices or serverless functions.
- Detecting **race conditions** or **synchronization bottlenecks**.

Profiling works best with **languages/frameworks** that support runtime instrumentation (e.g., Java, Go, .NET, Node.js, Python). Tools like **pprof (Go)**, **Async Profiler (Java)**, and **eBPF-based profilers** (e.g., Flamenco) enable efficient sampling without significant runtime overhead.

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Attributes**                                                                 | **Example Tools**                     |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **Profiling Instrument**    | Captures execution data via sampling or tracing.                              | - Sampling rate (Hz)<br>- Memory allocation tracking<br>- Lock contention events<br>- Stack trace depth | pprof, Async Profiler, Xray          |
| **Profiling Data**          | Raw or processed profiling output.                                            | - CPU time (nanoseconds)<br>- Memory alloc/free (bytes)<br>- Lock wait time (µs)<br>- Inclusive/exclusive time | PPROF binary format, FlameGraphs     |
| **Aggregator**              | Processes raw data into actionable insights (e.g., hot paths, memory usage). | - Time window (e.g., 1m, 5m)<br>- Sampling granularity<br>- Anomaly detection thresholds | Prometheus (via custom metrics), OpenTelemetry |
| **Visualizer**              | Renders profiling data for analysis (e.g., flame graphs, timeline views).    | - Support for PPROF, FlameGraphs, SpeedScope<br>- Correlation with traces/logs | pprof web UI, FlameGraph, SpeedTracer |
| **Storage Backend**         | Persists profiling data for historical analysis or SLO enforcement.          | - Retention policy (hours/days)<br>- Compression (e.g., zstd)<br>- Queryable format (e.g., Time Series DB) | S3, Prometheus, Grafana Loki          |
| **Alerting Rule**           | Triggers alerts when profiling data exceeds thresholds.                        | - CPU sampling % > 90%<br>- Memory growth > 10%/min<br>- Lock contention > 50ms | Prometheus Alertmanager, Datadog     |
| **Correlation Engine**      | Links profiling data with traces/logs/metrics for contextual analysis.        | - Trace ID correlation<br>- Sampling timestamp alignment<br>- Event enrichment | OpenTelemetry, Jaeger, Zipkin        |

---

## **Query Examples**

### **1. CPU Profiling (Hot Function Identification)**
**Use Case**: Find the top CPU-consuming functions in a microservice.
**Tools**: `pprof`, `Async Profiler`, or `eBPF-based samplers`.
**Commands/Queries**:
```bash
# Start sampling (Go pprof)
go tool pprof http://localhost:8080/debug/pprof/profile
# Top 5 functions by CPU time:
top
```
**Output Analysis**:
```
Total: 100 samples
  45%  github.com/myapp/handler.processRequest
   25%  github.com/myapp/db.query
   15%  github.com/myapp/utils.encrypt
    5%  runtime.mallocgc
```
**Action**: Optimize `processRequest` or switch to a faster database query.

---

### **Allocation Profiling (Memory Leaks)**
**Use Case**: Detect memory growth in a Java application.
**Tools**: Async Profiler, VisualVM.
**Commands**:
```bash
# Start async profiling (Java)
async-profiler start -d 60 -f alloc_objects.csv
```
**Query (Grafana/Time Series DB)**:
```sql
-- Memory allocation rate (bytes/sec)
SELECT
  avg(allocated_bytes) AS allocations_per_sec
FROM profiling_data
WHERE service = 'my-java-app'
  AND timestamp > now() - interval '5 minutes'
GROUP BY 5min
```
**Threshold Alert**:
`IF allocations_per_sec > 100_000_000 THEN alert("Memory leak suspected")`

---

### **Latency Profiling (I/O Bottlenecks)**
**Use Case**: Identify slow database calls in a Node.js app.
**Tools**: `pprof` (Node.js), `SpeedTracer`.
**Command**:
```bash
node --prof process.js
```
**Analyze trace**:
```bash
node --prof-process=*.prof > flame.svg
```
**Key Findings**:
- Database queries account for **60% of latency** in `userService.getOrders()`.
- Fix: Add caching (Redis) or optimize SQL queries.

---

### **Lock Contention Profiling**
**Use Case**: Detect thread-starved locks in a Go service.
**Tools**: `pprof` lock profiling.
**Command**:
```bash
go test -cpuprofile=cpu.prof -blockprofile=block.prof -bench=.
```
**Query Block Profiling**:
```bash
go tool pprof http://localhost:8080/debug/pprof/block
```
**Output**:
```
Total: 1000 lock events
   40%  sync.RWMutex.RLock
   30%  github.com/myapp/cache.get
```
**Action**: Replace `RWMutex` with `sync.Map` or shard the cache.

---

## **Implementation Details**

### **1. Profiling Strategies**
| **Strategy**       | **Pros**                                  | **Cons**                                  | **Use Case**                          |
|--------------------|------------------------------------------|------------------------------------------|---------------------------------------|
| **CPU Sampling**   | Low overhead (~0.1–1% CPU)               | Lower precision                           | General performance tuning            |
| **Tracing**        | Precise, function-level timing           | Higher overhead (~5–10%)                   | Latency debugging                      |
| **Allocation Tracing** | Tracks heap growth per function      | Memory-heavy                              | Memory leak detection                 |
| **Lock Profiling** | Identifies contention hotspots            | Requires language support (e.g., Go)     | High-concurrency systems              |
| **eBPF Profiling** | Kernel-level, near-zero overhead        | Complex setup                             | Production environments               |

---

### **2. Integration with Observability Stacks**
| **Component**       | **Profiling Integration**                                                                 | **Tools**                              |
|--------------------|----------------------------------------------------------------------------------------|----------------------------------------|
| **Metrics**        | Export profiling data as custom metrics (e.g., `cpu_samples_total`, `alloc_bytes`).      | Prometheus, OpenTelemetry              |
| **Traces**         | Annotate profiling samples with trace IDs for correlation.                               | Jaeger, Zipkin                        |
| **Logs**           | Associate profiling events with log entries (e.g., "Function X took 200ms (CPU: 150ms)"). | ELK Stack, Loki                        |
| **Alerts**         | Trigger alerts based on profiling thresholds (e.g., "CPU > 80% for 5m").                 | Datadog, Grafana Alerting              |

**Example OpenTelemetry Export**:
```yaml
# otel-collector-config.yaml
receivers:
  pprof:
    endpoint: 0.0.0.0:6060
processors:
  batch:
exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
service:
  pipelines:
    metrics:
      receivers: [pprof]
      processors: [batch]
      exporters: [prometheus]
```

---

### **3. Best Practices**
1. **Sampling Rate**:
   - Start with **100–500Hz** for CPU profiling (adjust based on noise).
   - Use **higher rates** (1kHz+) for short-lived functions (e.g., serverless).

2. **Context Propagation**:
   - Correlate profiling samples with **trace IDs** and **request context** (e.g., user ID).
   - Example (OpenTelemetry):
     ```go
     ctx, span := otel.Tracer("myapp").Start(ctx, "processOrder")
     defer span.End()
     // Profile within the span:
     pp.Sample(ctx)
     ```

3. **Storage Efficiency**:
   - **Compress** profiling data (e.g., `zstd` for PPROF files).
   - **Aggregate** samples (e.g., 1-minute averages) for historical analysis.

4. **Security**:
   - **Anonymous sampling**: Avoid exposing sensitive stack traces in production.
   - **Rate limiting**: Restrict profiling to specific services/environments.

5. **Tooling**:
   - **Go**: `pprof` (built-in), `pprofui` (web UI).
   - **Java**: Async Profiler, YourKit.
   - **eBPF**: Flamenco, BPF Compiler Collection (BCC).

---

## **Related Patterns**
| **Pattern**                     | **Relation to Profiling Observability**                                                                 | **When to Use Together**                          |
|----------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| **[Distributed Tracing]**       | Profiling provides **latency breakdowns**; tracing links them to **end-to-end requests**.             | Analyzing slow API calls across services.         |
| **[Structured Logging]**        | Logs can **annotate profiling samples** with business context (e.g., user actions).                  | Correlating user flows with performance drops.    |
| **[Metrics-based Alerting]**    | Profiling **exports metrics** (e.g., `alloc_rate`) for alerting on anomalies.                       | Detecting memory leaks proactively.             |
| **[Service Mesh Observability]** | Profiles **sidecar proxies** (e.g., Envoy) for network latency.                                       | Debugging gRPC timeouts in Kubernetes.            |
| **[Chaos Engineering]**          | Profiling validates **failure impact** (e.g., "How does DB latency affect CPU?").                   | Testing resilience under load.                   |
| **[A/B Testing]**                | Profile **feature flags** to compare performance between variants.                                    | Measuring impact of a new algorithm.             |

---

## **Example Workflow**
1. **Deploy**:
   - Instrument app with `pprof` (Go) or Async Profiler (Java).
   - Configure OpenTelemetry to export profiling data to Prometheus.

2. **Detect**:
   - Query Prometheus for `cpu_samples_total` spikes:
     ```
     rate(pprof_cpu_samples_total[5m]) > 1000
     ```
   - Trigger alert: *"CPU sampling increased 3x; investigate hot paths."*

3. **Diagnose**:
   - Run `pprof http://service:6060/debug/pprof/profile`.
   - Generate FlameGraph: `go tool pprof -svg profile.prof > flame.svg`.

4. **Act**:
   - Optimize `processPayment()` (found in FlameGraph).
   - Deploy fix and verify with **canary profiling**.

5. **Automate**:
   - Schedule **nightly profiling jobs** for critical services.
   - Set SLOs: *"99% of requests must have < 80% CPU sampling."*

---
**Note**: Profiling should be **opt-in in production** (disable by default) to avoid overhead. Use **staging environments** for continuous profiling.