# **[Pattern] Logging Profiling Reference Guide**

---

## **Overview**
The **Logging Profiling** pattern combines **application logging** with **performance profiling** to capture detailed runtime telemetry, execution flows, and performance metrics in real time. This pattern is useful for diagnosing:
- Slow operations, bottlenecks, or memory leaks.
- Unexpected behavior (e.g., deadlocks, race conditions).
- Latency spikes or irregular patterns in distributed systems.

Unlike traditional logging alone, **Logging Profiling** embeds **CPU, memory, and execution-time** measurements alongside structured log events, allowing precise correlation between business logic and system behavior.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **Sampling Profiling**  | Periodically captures call-stack snapshots to track function execution (e.g., CPU time, duration). |
| **Instrumentation**     | Adding profiler hooks to code (e.g., libraries like `pprof`, OpenTelemetry).                     |
| **Trace IDs**           | Unique identifiers linking related logs, metrics, and traces (e.g., distributed tracing).        |
| **Profiling Granularity**| Controls when data is collected (e.g., per-function, per-thread, or aggregated).                |
| **Log Correlations**    | Matching profiling data (e.g., CPU spikes) to specific log entries (e.g., API calls).             |

---

## **Schema Reference**
Below is a reference schema for structured logging + profiling data.

### **1. Log Entry Schema**
```json
{
  "timestamp": "ISO8601",          // e.g., "2024-05-20T12:34:56.789Z"
  "trace_id": "UUID",              // Correlates across services (e.g., "1234abc-5678def")
  "span_id": "UUID",               // Unique to this operation (e.g., "ghij456-klmn789")
  "level": "INFO|WARNING|ERROR",  // Severity level
  "message": "String",             // Human-readable log
  "metadata": {                     // Key-value pairs (e.g., user_id: "123", status: "PENDING")
    "key1": "value",
    "key2": "value"
  },
  "profiling_context": {           // Profiling data (optional)
    "cpu_time_ns": 1500000,        // Nanoseconds spent in this log entry
    "memory_bytes": 123456,        // Memory allocated (if tracked)
    "parent_span_id": "UUID"       // For hierarchical traces
  }
}
```

### **2. Profiling Data Schema**
| **Field**               | **Type**       | **Description**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `profile_type`          | `"cpu"|"mem"|"mutex"` | Type of profiling data (CPU time, memory, or lock contention).                                   |
| `duration_ns`           | `Long`         | Time spent in the sampled operation (nanoseconds).                                                  |
| `sample_count`          | `Int`          | Number of samples taken (for aggregated stats).                                                     |
| `allocation_bytes`      | `Long`         | Memory allocated in this context (if profiled).                                                    |
| `call_stack`            | `String[]`     | Stack trace of the function call (e.g., `["main()", "processRequest()"]`).                         |
| `thread_id`             | `String`       | Unique thread identifier (useful for concurrency debugging).                                       |

---

## **Implementation Details**

### **1. Choose a Profiler**
| **Tool/Library**       | **Language** | **Pros**                                                                 | **Cons**                                  |
|-------------------------|--------------|--------------------------------------------------------------------------|-------------------------------------------|
| **pprof (Go)**          | Go           | Built-in, low overhead, flame graphs.                                    | Limited to Go.                           |
| **OpenTelemetry**       | Multi-lang   | Standardized, supports distributed tracing, integrates with logs/metrics.| Higher setup complexity.                 |
| **JVM Profilers**       | Java         | VisualVM, Async Profiler (CPU/memory).                                   | JVM-specific.                            |
| **Perf (Linux)**        | System-wide  | Low-level, kernel profiling.                                             | Requires admin access.                   |
| **Custom Logging**      | Any          | Full control, but manual instrumentation required.                       | Error-prone without tooling.              |

### **2. Instrumentation Steps**
#### **A. Add Profiling Hooks**
- **For CPU Profiling** (e.g., Go `pprof`):
  ```go
  import _ "net/http/pprof" // Enable default pprof endpoints

  func main() {
      go func() {
          log.Println(http.ListenAndServe("0.0.0.0:6060", nil)) // pprof server
      }()
      // ... your app logic
  }
  ```
- **For Distributed Tracing** (OpenTelemetry):
  ```python
  from opentelemetry import trace

  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("process_order"):
      # Your code here (automatically instrumented)
      pass
  ```

#### **B. Correlate Logs & Profiling Data**
- **Option 1: Manual Correlation** (e.g., attach `trace_id` to logs):
  ```javascript
  const tracer = new Tracer();
  const span = tracer.startSpan("payment-processor");
  console.log({ trace_id: span.spanContext().traceId, message: "Processing..." });
  ```
- **Option 2: Auto-Inject** (e.g., OpenTelemetry SDKs):
  ```python
  # OpenTelemetry automatically injects headers like `traceparent` into HTTP requests.
  ```

#### **C. Aggregate Data**
- **Flame Graphs** (for CPU):
  Use `pprof` or `perf` to generate flame graphs (e.g., [Brender](https://github.com/brendanzab/brendaz-flame-graph)).
- **Memory Profiling**:
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/heap
  ```
- **Distributed Traces**:
  Visualize with tools like [Jaeger](https://www.jaegertracing.io/) or [Zipkin](http://zipkin.io/).

---

## **Query Examples**
### **1. Find Slow API Endpoints (CPU Profiling)**
**Tool:** `pprof` (Go) or OpenTelemetry Query API
**Query:**
```bash
# Fetch top 5 CPU-heavy functions from pprof
go tool pprof -http=:2345 http://localhost:6060/debug/pprof/profile
# Filter for high CPU time:
(pprof) top 5
```
**Result:**
```
Total: 1000ms
          400ms  40.0%  400ms  40.0%  github.com/app/main.processRequest
            300ms 30.0%   300ms 30.0%   github.com/app/main.dbQuery
```

### **2. Correlate Logs with High-Latency Spans**
**Tool:** ELK Stack + OpenTelemetry
**Query (Elasticsearch Kibana):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "INFO" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ],
      "filter": {
        "exists": { "field": "trace_id" }
      }
    }
  },
  "aggs": {
    "avg_latency": {
      "avg": { "script": "doc['profiling_context.duration_ns'].value" }
    }
  }
}
```
**Filter for slow operations:**
```
Trace ID: 1234abc
Duration: 2.1s (vs. avg 500ms) → Investigate!
```

### **3. Detect Memory Leaks**
**Tool:** `pprof heap` or OpenTelemetry Memory Profiling
**Query:**
```bash
# Compare heap usage over time
go tool pprof http://localhost:6060/debug/pprof/heap?debug=1
(pprof) web
```
**Look for:**
- Growing heap allocation over time.
- Unreleased objects in stack traces.

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                  |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Distributed Tracing**   | Track requests across microservices.                                        | Debugging latency in distributed systems.        |
| **Structured Logging**    | Standardize log formats (JSON, protobuf).                                  | Correlation with observability tools.             |
| **Sampling**              | Reduce profiling overhead by sampling (e.g., 1% of requests).               | High-throughput systems.                        |
| **Metrics-Based Alerts**  | Set alerts for CPU/memory thresholds (e.g., Prometheus).                    | Proactive monitoring of performance regressions.  |
| **Context Propagation**   | Pass metadata (e.g., `trace_id`) between services.                          | Correlation across services.                      |

---

## **Best Practices**
1. **Balance Overhead**: Avoid profiling in production unless critical (use sampling).
2. **Standardize IDs**: Use `trace_id`/`span_id` for cross-system correlation.
3. **Retain Data**: Archive profiling data (e.g., flame graphs) for future analysis.
4. **Combine with Metrics**: Correlate logs with Prometheus/Grafana metrics.
5. **Automate Alerts**: Set up alerts for:
   - CPU > 80% for 5+ minutes.
   - Memory growth > 10% per hour.
   - 99th-percentile latency spikes.

---
**Example Workflow**:
1. **Profile**: Enable `pprof` or OpenTelemetry CPU profiling.
2. **Correlate**: Match logs with `trace_id` in ELK/Jira.
3. **Diagnose**: Use flame graphs to spot bottlenecks.
4. **Fix**: Optimize slow functions or add retries for timeouts.