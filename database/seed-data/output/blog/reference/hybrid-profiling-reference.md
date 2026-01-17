---
# **[Pattern] Hybrid Profiling Reference Guide**

---

## **Overview**
Hybrid Profiling is an advanced performance monitoring technique that combines **distributed tracing** (to track request flows across microservices) with **sampling-based profiling** (to analyze runtime behavior without overhead). This pattern enables high-resolution performance insights while minimizing resource impact, making it ideal for large-scale, distributed systems.

Hybrid Profiling leverages:
- **Tracing** for end-to-end latency analysis (e.g., OpenTelemetry, Jaeger).
- **Sampling Profiling** (e.g., pprof, flame graphs) for deep function-level insights at a subset of request paths.
- **Context Propagation** to correlate sampled traces with corresponding profile data.

Unlike pure sampling (e.g., 1% of requests), hybrid profiling dynamically adjusts sampling rates based on observed latency or user-defined rules, ensuring critical paths are deeply analyzed while maintaining scalability.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                 | **Example Tools/Technologies**                     |
|---------------------------|---------------------------------------------------------------------------------|----------------------------------------------------|
| **Hybrid Profiling Agent** | Instrumentation layer that collects tracing events and triggers profiles.       | OpenTelemetry AutoInstrumentation, eBPF, Xray      |
| **Sampling Strategy**      | Rules to determine which requests are profiled (e.g., latency threshold, path-based). | OpenTelemetry Sampling (e.g., TailSampling), Prometheus Alerts |
| **Profile Context**        | Metadata linking a sampled trace to its corresponding profile data.             | OpenTelemetry Resource/Attribute tags, W3C Context |
| **Aggregation Engine**     | Processes profile data into actionable insights (flame graphs, latency breakdowns). | pprof, FlameGraph, Grafana Dashboards              |
| **Storage Backend**        | Persists profiles and traces for analysis (e.g., time-series DBs, object storage). | Google Cloud Trace, Jaeger, ELK Stack, S3          |

### **Key Workflow**
1. **Instrumentation**: Inject tracing spans and profile hooks into the application.
2. **Sampling Trigger**: Agent evaluates triggers (e.g., slow request > 500ms).
3. **Context Propagation**: Correlates sampled traces with profiles using trace IDs or custom attributes.
4. **Data Collection**: Profiles are captured and sent to a backend storage.
5. **Visualization**: Aggregated data is rendered in dashboards (e.g., flame graphs).

---

## **Schema Reference**

### **1. Hybrid Profiling Instrumentation Schema**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `trace_id`              | UUID           | Unique identifier for the traced request (correlates with profile).              | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8`     |
| `span_context`          | Struct         | W3C Traceparent/TraceID headers for distributed tracing.                        | `{ "trace_id": "00-4bf96f7f75bcd327b8b5a..." }` |
| `sampled`               | Boolean        | Indicates whether the request should be profiled.                                | `true`                                     |
| `profile_sample_rate`   | Float (0.0–1.0) | Sampling rate for profiling (e.g., 0.1 = 10% of matching requests).              | `0.05`                                     |
| `latency_threshold_ms`  | Integer        | Minimum latency (ms) to trigger profiling.                                       | `500`                                      |
| `path_pattern`          | String[]       | HTTP paths to profile (e.g., regex or exact matches).                          | `["/api/v1/users/*", "/checkout"]`          |
| `profile_interval_ms`   | Integer        | Duration (ms) to capture a profile after the trigger.                           | `100`                                      |

---

### **2. Profile Data Schema**
| **Field**          | **Type**       | **Description**                                                                 | **Example Value**                          |
|--------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `timestamp`        | Unix Timestamp | When the profile was captured.                                                   | `2023-10-15T12:34:56.789Z`                |
| `trace_id`         | UUID           | Links to the corresponding trace.                                               | `a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8`     |
| `duration_ns`      | Integer        | Total profile capture duration.                                                  | `500000000` (500ms)                       |
| `threads`          | Struct[]       | Thread-level profiling data (CPU, goroutines, etc.).                            | `[ { "thread_id": 1, "stack": [ ... ] } ]` |
| `events`           | Struct[]       | Runtime events (e.g., GC pauses, locks).                                        | `[ { "type": "GC", "duration": 120000000 } ]` |

---

### **3. Sampling Rules Schema**
| **Field**          | **Type**       | **Description**                                                                 | **Example Value**                          |
|--------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------------|
| `rule_id`          | String         | Unique identifier for the rule.                                                  | `"latency_high"`                           |
| `type`             | String         | Rule type (`latency`, `path`, `custom_attributes`).                               | `"latency"`                                |
| `threshold`        | Any            | Rule-specific threshold (e.g., latency in ms, path regex).                     | `700`                                      |
| `sample_rate`      | Float          | Sampling rate for the rule.                                                      | `0.1`                                      |
| `priority`         | Integer        | Rule priority (higher values override lower ones).                                | `10`                                       |

---

## **Query Examples**

### **1. Filter Traces by Hybrid Profile Context**
```sql
-- SQL-like pseudocode for trace aggregation with profile context
SELECT
    trace_id,
    request_path,
    AVG(latency_ms) as avg_latency,
    COUNT(*) as profile_count
FROM traces
WHERE
    sampled = true
    AND latency_ms > 500
    AND profile_sample_rate = 0.05
GROUP BY trace_id, request_path
ORDER BY avg_latency DESC;
```

### **2. Extract Flame Graph Data from Profiles**
```bash
# Using OpenTelemetry + pprof to generate a flame graph
otelcol-contrib --config=otel-config.yaml \
    | pprof -http=":8080" \
    | flamegraph.pl > profile_flame.svg
```
**Input (pprof binary data):**
```plaintext
sample_type: cpu
time_nanos: 1697234567890123456
- main.main()
  - github.com/user/app/handler.GetUser()
    - runtime.mallocgc()
    - github.com/user/app/db.QueryUser()
```

### **3. Correlate Traces with Profiles in Jaeger**
```bash
# Query Jaeger for traces where profiling was triggered
curl -X POST "http://jaeger:16686/api/traces" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": [{
      "key": "hybrid_profile.sampled",
      "value": "true"
    }]
  }'
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **Use Case**                                  |
|---------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Distributed Tracing**   | Tracks requests across services using trace IDs.                                | Debugging cross-service latency.              |
| **Sampling Profiling**    | Captures stack traces at a low rate to analyze performance.                     | CPU bottleneck analysis.                     |
| **EBPF-Based Profiling**  | Uses kernel-level sampling for minimal overhead.                                | Real-time system monitoring.                 |
| **Adaptive Sampling**     | Dynamically adjusts sampling based on observed anomalies.                       | Auto-scaling profile collection.              |
| **Service Mesh Observability** | Integrates tracing/profiling with Istio/Linkerd for fine-grained control. | Cloud-native environments.                   |

---

## **Best Practices**
1. **Set Appropriate Thresholds**:
   - Start with conservative `latency_threshold_ms` (e.g., 300–500ms) to avoid noise.
   - Adjust `profile_interval_ms` to capture the full slow path.

2. **Correlation First**:
   - Ensure `trace_id` and `span_context` are propagated across profiling agents.
   - Use OpenTelemetry’s `Resource` attributes for metadata (e.g., `service.name`).

3. **Storage Efficiency**:
   - Compress profiles (e.g., using `go pprof`'s `-compress` flag).
   - Retain profiles for 24–72 hours (longer for critical systems).

4. **Visualization**:
   - Use **FlameGraph** for CPU profiling.
   - Combine with **trace visualization tools** (e.g., Jaeger, OpenTelemetry UI) for end-to-end context.

5. **Security**:
   - Validate `trace_id` and `profile_sample_rate` to prevent DoS via excessive sampling.
   - Encrypt profile data in transit (e.g., using TLS).

---
**References**:
- [OpenTelemetry Hybrid Profiling](https://opentelemetry.io/docs/specs/otel/protocol/metrics/)
- [FlameGraph Documentation](https://github.com/brendangregg/FlameGraph)
- [Google’s pprof Guide](https://github.com/google/pprof)