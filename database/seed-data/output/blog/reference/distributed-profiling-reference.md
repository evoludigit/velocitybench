# **[Pattern] Distributed Profiling Reference Guide**

## **Overview**
Distributed Profiling is a performance monitoring pattern used to collect, aggregate, and analyze runtime metrics across multiple nodes in a distributed system. Unlike traditional profiling, which focuses on a single process or machine, distributed profiling distributes profiling workloads across servers, containers, or microservices, enabling comprehensive insights into system-wide behavior.

This pattern is essential for diagnosing performance bottlenecks, memory leaks, CPU contention, and latency issues in scalable applications. It leverages lightweight instrumentation, asynchronous sampling, and centralized aggregation mechanisms to minimize overhead while maintaining accuracy.

## **Key Concepts**
Distributed Profiling relies on several core principles:

| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Instrumentation**       | Adding minimal code probes to track execution paths, memory allocations, and resource usage.      |
| **Event Sampling**        | Randomly sampling execution events to balance accuracy and overhead (e.g., CPU profiling).          |
| **Asynchronous Collection** | Collecting data without blocking application threads to avoid performance degradation.             |
| **Centralized Aggregation** | Gathering sampled data from multiple nodes into a unified dashboard or database for analysis.     |
| **Low-Overhead Probes**   | Using lightweight instrumentation (e.g., PPROF, `perf`, or custom probes) to minimize runtime impact. |
| **Span-Based Tracing**    | Capturing request flows across services using OpenTelemetry or Jaeger for latency analysis.         |

---

## **Implementation Details**

### **1. Instrumentation Strategies**
Distributed profiling instruments multiple components:

| **Component**            | **Instrumentation Method**                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| **Application Code**     | Embedded profilers (e.g., `pprof`, `perf`), custom metrics libraries (Prometheus, OpenTelemetry). |
| **Language Runtimes**    | JVM (`jvmstat`, Java Flight Recorder), Go (`pprof`), .NET (CLR Profiler).                      |
| **Network Stack**        | Packet tracing (e.g., `tcpdump`), gRPC/HTTP latency sampling.                                 |
| **Storage Layer**        | Database query logging (e.g., slow query logs, `pg_stat_activity`).                          |
| **Container Orchestration** | Kubernetes metrics (Prometheus Adapter, `kubectl top`).                                      |

---

### **2. Sampling Techniques**
To reduce overhead, distributed profiling uses probabilistic sampling:

| **Sampling Method**      | **Use Case**                                                                                   | **Example Tools**                          |
|--------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| **CPU Flame Graphs**     | Captures stack traces at random intervals.                                                    | `pprof`, `perf`, FlameGraph                |
| **Memory Sampling**      | Periodically snapshots heap memory to detect leaks.                                           | Java Flight Recorder, Go `pprof`            |
| **Latency Sampling**     | Tracks request durations across microservices.                                               | OpenTelemetry, Datadog APM, Jaeger         |
| **Event-Based Sampling** | Triggers profiling on specific events (e.g., errors, slow responses).                         | Custom probes, ELK Stack                    |

---

### **3. Data Collection Pipeline**
Distributed profiling follows this workflow:

1. **Instrumentation** → Embed probes in application code.
2. **Sampling** → Collect data asynchronously.
3. **Transport** → Ship data to a collector (e.g., via gRPC, HTTP, or log files).
4. **Aggregation** → Store in a time-series database (TSDB) or profiling database.
5. **Analysis** → Visualize with dashboards (Grafana, Datadog) or flame graphs.

---

## **Schema Reference**

### **1. Profiling Data Models**

#### **CPU Profile Schema**
| **Field**               | **Type**       | **Description**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `timestamp`             | `int64`        | Unix epoch time in nanoseconds.                                                                      |
| `cpu_usage_percent`     | `float64`      | CPU utilization for the sampled interval.                                                          |
| `sample_count`          | `int64`        | Number of stack trace samples collected.                                                           |
| `stack_traces`          | `[]StackTrace` | Array of sampled stack traces.                                                                     |
| ` goroutine_id`         | `int64`        | Unique identifier for a Go goroutine (or thread ID in other languages).                            |
| `frames`                | `[]Frame`      | Stack trace frames, including function names and line numbers.                                     |

**Example StackTrace:**
```json
{
  "goroutine_id": 12345,
  "frames": [
    {"function": "main.main", "file": "main.go", "line": 42},
    {"function": "runtime.main", "file": "runtime/proc.go", "line": 224}
  ]
}
```

#### **Memory Profile Schema**
| **Field**               | **Type**       | **Description**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `timestamp`             | `int64`        | Sampling time in nanoseconds.                                                                       |
| `heap_allocated_bytes`  | `int64`        | Total heap allocated since process start.                                                          |
| `heap_objects`          | `int64`        | Number of live heap objects.                                                                         |
| `gc_pause_seconds`      | `float64`      | Total garbage collection pause time.                                                              |
| `stack_objects`         | `int64`        | Number of stack-allocated objects.                                                                 |
| `inuse_objects`         | `int64`        | Currently allocated objects.                                                                         |

#### **Latency Trace Schema (OpenTelemetry)**
| **Field**               | **Type**       | **Description**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `trace_id`              | `string`       | Unique trace identifier.                                                                             |
| `span_id`               | `string`       | Span identifier for a single operation.                                                               |
| `name`                  | `string`       | Operation name (e.g., `/api/v1/users`).                                                               |
| `start_time`            | `int64`        | Start time in nanoseconds.                                                                           |
| `end_time`              | `int64`        | End time in nanoseconds.                                                                             |
| `duration_ns`           | `int64`        | Duration of the span.                                                                               |
| `attributes`            | `map[string]string` | Key-value pairs (e.g., `{"service": "user-service", "http.status": "200"}`).                     |
| `links`                 | `[]Link`       | References to parent spans (for distributed tracing).                                               |

**Example Span:**
```json
{
  "trace_id": "a1b2c3...",
  "span_id": "d4e5f6...",
  "name": "process_order",
  "start_time": 1625097600000000000,
  "end_time": 1625097601000000000,
  "duration_ns": 1000000000,
  "attributes": {"service": "order-service", "user_id": "123"}
}
```

---

## **Query Examples**

### **1. Querying CPU Flame Graphs (via `pprof`)**
**Command:**
```bash
go tool pprof http://localhost:8080/debug/pprof/profile?seconds=5
```
**Analysis Steps:**
1. Load the profile in `pprof`:
   ```bash
   pprof -text http://localhost:8080/debug/pprof/profile
   ```
2. View top-consuming functions:
   ```bash
   top
   ```

### **2. Querying Memory Leaks (Go `pprof`)**
**Command (to generate heap dump):**
```bash
go tool pprof http://localhost:8080/debug/pprof/heap
```
**Analysis Steps:**
1. Identify leaking objects:
   ```bash
   pprof -type=goroutine http://localhost:8080/debug/pprof/goroutine
   ```
2. Filter by memory usage:
   ```bash
   top -cum
   ```

### **3. Analyzing Latency Traces (OpenTelemetry)**
**Query (using PromQL in Prometheus):**
```sql
histogram_quantile(
  0.95,
  sum(rate(otel_spans_duration_seconds_bucket[5m]))
) by (service)
```
**Breakout by service:**
```sql
sum(rate(otel_spans_duration_seconds_bucket{le="1s"}[1m]))
  by (service)
```

### **4. Aggregating Across Nodes (Prometheus)**
**Query to find slow API endpoints:**
```sql
sum(rate(http_server_requests_total{status=~"5.."}[1m]))
  by (handler)
```

---

## **Instrumentation Libraries**

| **Library/Tool**        | **Language** | **Type**               | **Key Features**                                                                 |
|-------------------------|--------------|------------------------|-----------------------------------------------------------------------------------|
| `google/pprof`          | Go           | CPU/Memory Profiling    | Low-overhead sampling, HTTP endpoint integration.                                |
| `Java Flight Recorder`  | Java         | Full-Stack Profiling   | High-resolution CPU, memory, and GC profiling.                                  |
| `OpenTelemetry`         | Multi-Lang   | Distributed Tracing    | Standardized spans, metrics, and logs collection.                                 |
| `Prometheus Client`     | Multi-Lang   | Metrics                | Scrapes runtime metrics to a central TSDB.                                       |
| `Kubernetes Metrics`    | Cluster      | Resource Monitoring    | Exposes CPU/memory usage per pod via Prometheus Adapter.                          |

---

## **Use Cases**
1. **Microservices Latency Analysis**
   - Trace requests across services to identify bottlenecks.
2. **Memory Leak Detection**
   - Continuously sample heap usage to catch growing allocations.
3. **CPU Hotspot Identification**
   - Detect functions consuming excessive CPU cycles.
4. **Database Query Optimization**
   - Log slow queries and analyze execution plans.

---

## **Best Practices**
1. **Minimize Overhead**
   - Use sampling instead of full instrumentation where possible.
   - Schedule profiling during off-peak hours.
2. **Centralized Storage**
   - Store profiles in a scalable database (e.g., TSDB, Elasticsearch).
3. **Automate Analysis**
   - Set up alerts for anomalies (e.g., sudden CPU spikes).
4. **Isolate Profiling Traffic**
   - Use separate networks for profiling data to avoid congestion.

---

## **Related Patterns**
1. **[Distributed Tracing](https://docs.google.com/document/d/...)**
   - Captures request flows across services with detailed timing.
2. **[Metrics Collection](https://prometheus.io/docs/practices/)**
   - Measures system health with aggregatable counters and gauges.
3. **[Instrumentation as Code](https://github.com/DataDog/instrumentation)**
   - Manages instrumentation via configuration files (e.g., OpenTelemetry SDK).
4. **[Observability Pipeline](https://www.martinfowler.com/articles/observability.html)**
   - Combines logs, metrics, and traces for holistic visibility.

---
**Further Reading:**
- [Google’s `pprof` Guide](https://github.com/google/pprof)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Kubernetes Profiling with Prometheus](https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/)