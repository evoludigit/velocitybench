# **[Pattern] Profiling Monitoring – Reference Guide**

---
## **Overview**
The **Profiling Monitoring** pattern involves collecting runtime behavior data (e.g., CPU, memory, I/O, latency, concurrency) of applications, services, or infrastructure components to identify performance bottlenecks, memory leaks, thread contention, and inefficient algorithms. Unlike traditional logging (which records events in sequence), profiling captures **real-time metrics** with high granularity to diagnose issues proactively. This pattern is critical for optimization in microservices, distributed systems, and high-throughput applications.

Key use cases include:
- **Performance tuning** (e.g., reducing latency in API responses).
- **Resource optimization** (e.g., detecting memory leakage in long-running processes).
- **Debugging** (e.g., tracing slow database queries or blocked threads).

Monitors may integrate with **APM tools** (e.g., Datadog, New Relic), **profilers** (e.g., `pprof` for Go, `perf` for Linux), or custom telemetry pipelines.

---

## **Schema Reference**
Below are the core metrics and entities used in Profiling Monitoring. Table schemas reflect common implementations.

| **Category**       | **Entity**               | **Attributes**                                                                 | **Example Value**                     | **Units**  |
|--------------------|--------------------------|-------------------------------------------------------------------------------|---------------------------------------|------------|
| **System Metrics** | `Process`                | `pid`, `name`, `start_time`, `user`, `memory_rss`, `cpu_usage`, `gc_time`    | `{ pid: 1234, cpu_usage: 45.2 }`      | %          |
|                    | `Thread`                 | `tid`, `name`, `state`, `stack_trace`, `blocked_time`                        | `{ blocked_time: 120ms }`             | ms         |
|                    | `MemoryHeap`             | `allocated`, `retained`, `reclaimed`, `fragmentation_ratio`                 | `{ retained: 450MB }`                | MB         |
| **I/O Metrics**    | `DiskIO`                 | `read_ops`, `write_ops`, `latency_avg`, `throughput`, `device`              | `{ latency_avg: 40ms }`              | ms         |
|                    | `NetworkRequest`         | `url`, `status_code`, `latency`, `payload_size`, `response_time`             | `{ latency: 125ms }`                 | ms         |
| **GC Metrics**     | `GCEvent`                | `timestamp`, `type` (minor/major), `duration`, `heap_before`, `heap_after`  | `{ duration: 150ms }`                 | ms         |
| **Custom Event**   | `TelemetryEvent`         | `timestamp`, `source` (service/container), `metrics` (custom keys/values)    | `{ "cache_hit_rate": 0.85 }`         | -          |
| **Distributed Tracing** | `Span`               | `trace_id`, `span_id`, `name`, `start_time`, `end_time`, `tags` (e.g., `db.query`) | `{ "db.query": "SELECT * FROM users" }` | -          |

---
### **Data Flow Schema**
```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Profiling  │──────▶│  Metric     │──────▶│  Storage/   │
│  Instrument │      │  Collection │      │  Visualizer  │
└─────────────┘       └─────────────┘       └─────────────┘
       ▲                    ▲               ▲
       │                    │               │
┌──────┴───────────────────┴────────────────┴──────┐
│  Application/Infrastructure (e.g., JVM, Go, NGINX) │
└─────────────────────────────────────────────────────┘
```

---
## **Implementation Details**

### **1. Profiling Techniques**
#### **A. Sampling vs. Full Profiling**
| **Technique**       | **Pros**                          | **Cons**                          | **Use Case**                          |
|--------------------|-----------------------------------|-----------------------------------|---------------------------------------|
| **Sampling**       | Low overhead, real-time.         | Less precise (misses spikes).     | High-frequency monitoring (e.g., web servers). |
| **Full Profiling** | High accuracy (captures every op).| High CPU/memory; slow.           | Debugging rare issues (e.g., deadlocks). |

#### **B. Common Profiling Tools**
| **Tool/Language**   | **Type**            | **Key Features**                                                                 |
|---------------------|---------------------|---------------------------------------------------------------------------------|
| `pprof` (Go)        | Sampling/CPU/Mem    | Built-in Go runtime support; integrates with `net/http/pprof`.                  |
| `perf` (Linux)      | Kernel-level       | Low-overhead CPU/IPC profiling; supports flame graphs.                          |
| `Java Flight Recorder` (JVM) | Full-stack      | Low-overhead; captures thread dumps, GC, and JVM internals.                     |
| `Python cProfile`   | Sampling           | Built-in; exports `.prof` files for analysis.                                  |
| **OpenTelemetry**   | Distributed        | Standardized tracing/metrics; vendor-agnostic (e.g., Jaeger, Prometheus).       |

---
### **2. Instrumentation Strategies**
#### **A. Agent-Based (External)**
- **Pros**: Non-intrusive; supports multiple languages.
- **Cons**: Overhead; may miss native code (e.g., C libraries).
- **Example**: Datadog Agent, New Relic.

#### **B. Instrumentation Libraries**
- **Pros**: Controlled; integrates tightly with code.
- **Cons**: Requires maintenance per language.
- **Examples**:
  - **Go**: `pprof` package.
  - **Java**: `Java Instrumentation API`.
  - **Node.js**: `clinic.js` or `languid`.

#### **C. Native Profiling**
- **Pros**: High precision (e.g., CPU cycles).
- **Cons**: Complex setup; language-specific.
- **Example**: Linux’s `perf record` for systems-level analysis.

---
### **3. Storage & Analysis**
| **Storage Type**    | **Use Case**                          | **Tools**                          |
|---------------------|---------------------------------------|------------------------------------|
| **Time-Series DB**  | Metrics (e.g., CPU, memory over time).| Prometheus, InfluxDB.               |
| **Log Storage**     | Raw tracebacks/stack dumps.           | ELK Stack, Loki.                   |
| **Trace Store**     | Distributed request flows.            | Jaeger, Zipkin.                    |
| **Blob Storage**    | Full profiling dumps (e.g., heap snapshots). | S3, GCS. |

---
## **Query Examples**
### **1. CPU Profiling (Go `pprof`)**
**Command**:
```bash
go tool pprof http://localhost:6060/debug/pprof/profile
```
**Key Queries**:
- **Top CPU-consuming functions**:
  ```bash
  (pprof) top10
  ```
- **Flame graph visualization**:
  ```bash
  (pprof) web
  ```

---
### **2. Memory Leak Detection (Java JFR)**
**Command** (record to `leak.jfr`):
```bash
jcmd <pid> JFR.start filename=leak.jfr settings=profile
```
**Query in JFR**:
Detect retained heap objects:
```sql
SELECT * FROM jdk.JavaObjectAllocEvent WHERE allocationSize > 1MB ORDER BY allocationSize DESC;
```

---
### **3. Network Latency (OpenTelemetry)**
**Query Prometheus**:
Find slow API endpoints:
```promql
rate(http_server_requests_seconds_sum[1m])
  /
rate(http_server_requests_count[1m])
  > 1000
```
**Filter by high latency**:
```promql
http_server_request_duration_seconds_bucket{le="1000"} > 0
```

---
### **4. Distributed Tracing (Jaeger)**
**Find slow spans**:
```sql
SELECT * FROM spans
WHERE duration > 1000
ORDER BY duration DESC
LIMIT 10;
```

---
## **Common Pitfalls & Best Practices**
### **⚠️ Pitfalls**
1. **Overhead**: Sampling adds ~1–5% CPU; full profiling can freeze the app.
2. **Noise**: Ignore profiling data from initialization/garbage collection phases.
3. **Resolution Trade-offs**: High-frequency sampling misses spikes; low-frequency misses details.

### **🔹 Best Practices**
1. **Profile in Production-like Environments**:
   - Test with real workloads (e.g., load-testing tools like Locust).
2. **Automate Profiling Triggers**:
   - Run profiles on **error thresholds** (e.g., 5xx errors > 10%).
   - Schedule periodic snapshots (e.g., nightly heap dumps).
3. **Combine with Logging**:
   - Correlate profiling data with logs/traces (e.g., trace IDs).
4. **Limit Scope**:
   - Profile **one service/component at a time** to avoid analysis paralysis.
5. **Use Flame Graphs**:
   - Visualize call stacks (tools: [`flamegraph`](https://github.com/brendangregg/FlameGraph)).

---
## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **Connection to Profiling Monitoring**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **[Logging](https://docs.patterns.dev/logging)** | Structured event recording.                                                  | Correlate profiling data with logs (e.g., link trace IDs to log entries).                              |
| **[Metrics Collection](https://docs.patterns.dev/metrics)** | Aggregated numerical data (e.g., requests/sec).                            | Profiling complements metrics (e.g., high CPU `%` → dig into profiling data).                         |
| **[Distributed Tracing](https://docs.patterns.dev/tracing)** | End-to-end request flows.                                                   | Profiling can identify slow operations **within** traced spans (e.g., a slow DB query).               |
| **[Circuit Breaker](https://docs.patterns.dev/circuit-breaker)** | Prevent cascading failures.                                                  | Profiling can help diagnose why a service is overloaded (e.g., memory leaks causing timeouts).       |
| **[Rate Limiting](https://docs.patterns.dev/rate-limiting)** | Throttle requests to prevent abuse.                                         | Profile to find bottlenecks **after** implementing rate limits (e.g., cache miss rates).             |
| **[Canary Releases](https://docs.patterns.dev/canary)** | Gradual feature rollouts.                                                    | Profile incrementally deployed versions to catch regressions early.                                    |

---
## **Further Reading**
1. **Books**:
   - *Production-Ready Microservices* (Samsa & O’Reilly) – Chapters on observability.
   - *The Art of Monitoring* (O’Reilly) – Covers profiling deeply.
2. **Tools**:
   - [pprof](https://github.com/google/pprof) (Go)
   - [Java Flight Recorder](https://docs.oracle.com/javacomponents/jfr/)
   - [OpenTelemetry](https://opentelemetry.io/)
3. **Talks**:
   - [GreenSock’s Profiling Guide](https://greensock.com/optimize/) (JavaScript).
   - [Brendan Gregg’s Flame Graphs](https://www.brendangregg.com/flamegraphs.html).