# **[Pattern] Tracing Profiling – Reference Guide**

---

## **Overview**
**Tracing Profiling** is a performance analysis technique that combines **distributed tracing** with **profiling** to collect detailed runtime data across microservices, functions, or components. Unlike traditional sampling-based profilers, tracing profiling records **end-to-end call paths**, latency metrics, and execution contexts at **high granularity**, enabling precise bottlenecks identification in distributed systems.

This pattern is critical for diagnosing:
- **Latency spikes** in distributed transactions
- **Resource contention** across services
- **Hot paths** (highly traversed code)
- **Inter-service communication inefficiencies**

It leverages **trace-based instrumentation** (e.g., OpenTelemetry, Jaeger) alongside **CPU/memory profilers** (e.g., `pprof`, New Relic) to correlate low-level performance data with high-level workflows.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                                                                                                     | **Tools/Technologies**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Trace Span**         | A unit of work (e.g., API call, database query) with start/end timestamps, duration, and context tags. Spans form **traces** for end-to-end analysis.                     | OpenTelemetry, Jaeger, Zipkin                                                                             |
| **Sampling Rate**      | Controls trace volume (e.g., 0.1% for production). Higher rates capture more detail but increase overhead.                                                            | OpenTelemetry `Sampler`, Datadog Sampling                                                                 |
| **Attributes**         | Key-value metadata (e.g., `service.name`, `http.method`) attached to spans. Enables filtering and correlation.                                                       | OpenTelemetry `Resource` and `Span` attributes                                                             |
| **Profiling Data**     | Low-level CPU, memory, and lock contention snapshots (e.g., per-thread stack traces). Merged with traces for context.                                           | `pprof`, Google Cloud Profiling, Netflix Hystrix                                                                 |
| **Trace Context Propagation** | Injecting trace IDs (`traceparent` header) to correlate cross-service calls.                                                                                     | W3C Trace Context, OpenTelemetry Auto-Instrumentation                                                          |
| **Backend Storage**    | Stores traces (e.g., per-minute aggregations) and snapshots for query/replay.                                                                                     | Jaeger, Lightstep, AWS X-Ray, Elasticsearch (for long-term retention)                                     |

---

### **2. Data Flow**
1. **Instrumentation**: Add tracing SDKs (e.g., `opentelemetry-java`) to code to auto-generate spans.
2. **Sampling**: Filter traces (e.g., `always_on` for critical paths, probabilistic for others).
3. **Propagation**: Attach trace IDs to HTTP/gRPC calls via headers.
4. **Collection**: Ship traces to a backend (e.g., Jaeger collector).
5. **Analysis**: Query traces + profiles to correlate slow spans with CPU/memory hotspots.

---

### **3. Instrumentation Strategies**
| **Strategy**               | **Use Case**                          | **Example Implementation**                                                                                     |
|----------------------------|---------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Auto-Instrumentation**   | SDKs (e.g., `opentelemetry-auto-instrumentation`) wrap HTTP/gRPC calls. | Add `opentelemetry-javaagent` to JVM apps.                                                                  |
| **Manual Instrumentation** | Custom business logic (e.g., `BEGIN`/`END` spans). | Span `span = tracer.startSpan("user.signup");`; `span.end();`                                                 |
| **Library Support**        | Integrate with ORMs (e.g., Spring Data), caches (Redis), or databases. | Use `@EnableTracing` in Spring Boot + `@Trace` annotations for repositories.                              |

---

### **4. Profiling Integration**
Combine traces with **CPU/memory profiles** to pinpoint bottlenecks:
- **CPU Profiling**: Record stack traces during slow spans (e.g., `pprof` with tracing hooks).
- **Memory Profiling**: Heap snapshots for leaks during high-latency traces.
- **Lock Contention**: Use `pprof`’s `goroutine` command to analyze blocked goroutines in traces.

**Example Workflow**:
1. Identify a slow trace (e.g., `POST /checkout` = 2.1s).
2. Correlate with CPU profile: Discover `orderService.processPayment()` uses 80% CPU.
3. Check stack trace: `paymentValidator.validate()` hits a hot loop.

---

### **5. Storage & Querying**
| **Storage Layer**   | **Use Case**                          | **Query Tools**                                                                               |
|---------------------|---------------------------------------|-----------------------------------------------------------------------------------------------|
| **In-Memory (e.g., Jaeger Query)** | Real-time debugging for recent traces. | Filter by service, duration, or error.                                                          |
| **Time-Series DB (e.g., Prometheus)** | Aggregated latency percentiles (p99). | `histogram_quantile(0.99, sum(rate(trace_duration_bucket[5m])) by (le))`                     |
| **Search Engine (e.g., Elasticsearch)** | Full-text search on span attributes. | Kibana queries: `service.name: "payment-service" AND duration > 500ms`                          |
| **Trace Replay**    | Reconstruct slow traces locally.      | Jaeger “Trace Replay” tool, Lightstep’s “Event View”                                             |

---

## **Schema Reference**
### **1. Trace Schema (OpenTelemetry)**
```json
{
  "traces": [
    {
      "trace_id": "1a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d",
      "spans": [
        {
          "span_id": "a1b2c3d4e5f6a7b8c9d0e1f2",
          "name": "GET /api/users",
          "duration": "120ms",
          "start_time": "2023-10-01T12:00:00Z",
          "attributes": {
            "http.method": "GET",
            "http.status_code": "200",
            "service.name": "user-service"
          },
          "links": [
            {
              "trace_id": "1a1b2c3d4e5f...",
              "span_id": "b1c2d3e4f5...",
              "type": "CHILD_OF"
            }
          ],
          "events": [
            {
              "name": "db.query",
              "timestamp": "2023-10-01T12:00:00.5Z",
              "attributes": { "db.statement": "SELECT * FROM users" }
            }
          ]
        }
      ]
    }
  ]
}
```

### **2. Profiling Data Schema**
```json
{
  "profile": {
    "cpu": {
      "samples": [
        {
          "location": {
            "file": "user_service.go",
            "line": 42,
            "function": "(*UserService).GetUser"
          },
          "time_nanos": 1000000000,
          "thread_id": 1
        }
      ]
    },
    "memory": {
      "heap objects": [
        {
          "type": "User",
          "size_bytes": 128,
          "count": 10000
        }
      ]
    }
  }
}
```

---

## **Query Examples**
### **1. Find Slow API Calls (SQL-like Pseudocode)**
```sql
SELECT
  service_name,
  avg(duration),
  percentile99(duration)
FROM traces
WHERE timestamp > now() - 1d
  AND operation_name LIKE '%/api%'
GROUP BY service_name
ORDER BY avg(duration) DESC
LIMIT 10;
```

### **2. Correlate Traces with High CPU Usage**
```bash
# Filter traces where span matches CPU hotspot
jaeger query \
  --service=user-service \
  --filter 'attributes.http.method="POST" AND attributes.db.statement="*"' \
  --limit 5
# Then run CPU profile on the same trace ID:
pprof --trace_id=1a1b2c3d... http://localhost:6060/debug/pprof/cpu
```

### **3. Identify Cross-Service Latency Bottlenecks**
```javascript
// Using Lightstep’s Query DSL
trace()
  | filter(service == "checkout-service" AND operation == "processPayment")
  | stats(duration)
  | join(
      trace()
        | filter(service == "payment-gateway" AND operation == "charge")
        | stats(duration)
    )
  | plot(durationCheckout, durationPayment);
```

### **4. Detect Memory Leaks in Long-Lived Traces**
```bash
# Query traces with long-running spans > 5s
kql |
  traces
  | where duration > 5000ms
  | project TraceId, Service, Duration, MemoryUsage
  | join kind=inner (
      memory_profiles
      | summarize avg(HeapUsedBytes) by bin(Timestamp, 1h)
    ) on $left.Timestamp == $right.Timestamp
  | order by avg_HeapUsedBytes desc
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Synergy**                                                                                           |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Distributed Tracing]**        | End-to-end flow tracking across services.                                                          | Tracing Profiling **extends** this with low-level performance data.                                  |
| **[Sampling-Based Profiling]**   | Uses CPU sampling to identify hot paths (e.g., `pprof`).                                             | Tracing Profiling **correlates** sample data with trace context to find *why* a path is slow.       |
| **[Circuit Breaker]**            | Limits cascading failures in distributed systems.                                                   | Tracing Profiling **helps diagnose** why a circuit breaker was triggered (e.g., latency spikes).    |
| **[Service Mesh Tracing]**       | Envoy/ISTIO injects traces into sidecar proxies.                                                     | Tracing Profiling **adds profiling** to mesh-generated traces for deeper analysis.                   |
| **[Observability as Code]**      | Infrastructure-as-code for telemetry (e.g., OpenTelemetry Collector).                              | Tracing Profiling **relies on** infrastructure to collect and correlate data.                          |

---

## **Best Practices**
1. **Start with High Impact**:
   - Focus on **top latency percentiles** (p99) before diving into traces.
   - Use **sampling** (e.g., 1% of traces) to avoid overwhelming storage.

2. **Instrument Critical Paths First**:
   - Add traces to **user-facing flows** (e.g., checkout) before internal services.

3. **Correlate Traces with Profiles**:
   - Use **trace IDs** to link high-level latency with CPU/memory snapshots.

4. **Avoid Overhead**:
   - Limit **attribute keys** (stick to <50 per span).
   - Use **compression** (e.g., gRPC/HTTP/2) for trace payloads.

5. **Retain Long-Term Data**:
   - Store **aggregated metrics** (e.g., p99 latencies) for weeks/months.
   - Archive raw traces for **post-mortems** (e.g., SLO violations).

6. **Automate Alerts**:
   - Set up alerts for:
     - `trace_duration > 3 * p99`
     - `span_error_rate > 0.1%`
     - `cpu.profile_hotspot_increase > 20%`

---

## **When to Avoid**
- **Monolithic Apps**: Use **local profiling** (`pprof`) instead if services are tightly coupled.
- **High-Latency Tolerance**: If SLAs allow 1s+ delays, tracing profiling may add unnecessary noise.
- **Resource-Constrained Environments**: Heavy instrumentation (e.g., 100% sampling) can degrade performance.

---
**Key Takeaway**: Tracing Profiling bridges the gap between **distributed tracing** (what happened) and **profiling** (why it happened), making it indispensable for modern, multi-service architectures. Start with auto-instrumentation, correlate traces with profiles, and iteratively optimize based on data.