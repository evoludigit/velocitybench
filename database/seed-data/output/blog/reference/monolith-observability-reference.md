---
**[Pattern] Monolith Observability: Reference Guide**
*Observability for Traditional, Multi-Layered Applications*

---

### **Overview**
The **Monolith Observability** pattern addresses the challenges of monitoring, tracing, and debugging complex, vertically integrated applications built around a single cohesive codebase. Unlike microservices, monoliths consolidate multiple functionalities (e.g., frontend, backend, database, caching) into a single deployable unit, which complicates observability due to:
- **High coupling**: Instrumentation must span disparate layers (e.g., API, business logic, persistence).
- **Distributed execution**: Monoliths may interact with external dependencies (e.g., databases, queues), requiring cross-layer tracing.
- **Performance bottlenecks**: Performance issues often arise from unoptimized dependencies within the monolith.

This pattern provides strategies to **instrument**, **collect**, and **analyze** telemetry data (metrics, logs, traces) for monolithic architectures, ensuring visibility into system health, latency, and anomalies. It leverages existing observability tools (e.g., Prometheus, Jaeger, ELK) with customizations for monoliths, including:
- **Layer-aware instrumentation** (e.g., separating backend/logic/middleware telemetry).
- **Context propagation** across service boundaries (e.g., via headers or middleware).
- **Aggregated metrics** to avoid noise from internal interactions.

---

### **Key Concepts & Implementation Details**
#### **1. Telemetry Collection Layers**
Monoliths require targeted instrumentation to avoid overwhelming systems with irrelevant data. Focus on:

| **Layer**          | **Purpose**                          | **Data Types**                          | **Instrumentation Techniques**                          |
|--------------------|--------------------------------------|----------------------------------------|---------------------------------------------------------|
| **API Gateway**    | External request/response tracking   | Metrics (latency, errors), Traces      | HTTP middleware (e.g., Prometheus client, OpenTelemetry) |
| **Application**    | Business logic & workflows           | Traces, Metrics (custom business ops)  | Aspect-oriented (AOP) or decorator patterns               |
| **Database**       | Query performance & failed operations| Metrics (query time, retries), Logs    | JDBC/ORM interceptors (e.g., P6Spy, Hibernate stats)    |
| **Caching**        | Cache hit/miss ratios & invalidation | Metrics (cache size, evictions)        | Cache provider hooks (e.g., Redis stats, Ehcache)        |
| **External Deps**  | Third-party service interactions     | Traces, Metrics (response times)       | Client-side SDKs (e.g., HTTP clients with OpenTelemetry) |

---

#### **2. Schema Reference**
**Standardized Telemetry Schema for Monoliths**
Use these attributes to ensure consistency across layers. Custom fields should follow a prefixing convention (e.g., `app.`, `cache.`).

| **Category**       | **Attribute**               | **Description**                                                                 | **Example Value**                          | **Data Type**       |
|--------------------|----------------------------|-------------------------------------------------------------------------------|--------------------------------------------|---------------------|
| **Trace Context**  | `trace_id`                  | Unique identifier for a distributed trace.                                   | `123e4567-1234-5678-90ab-cdef01234567`    | UUID                 |
| **Request**        | `http.method`               | HTTP method (if applicable).                                                   | `GET`                                      | String               |
| **Resource**       | `resource.type`             | Layer/application component (e.g., `backend`, `database`).                     | `backend.service.order`                    | String               |
| **Performance**    | `duration_ms`               | End-to-end or layer-specific latency.                                         | `150`                                      | Long                 |
| **Error**          | `error.code`                | Standardized error codes (e.g., `DB_CONNECTION_ERROR`).                       | `HTTP_500`                                 | String               |
| **Business**       | `business.op`               | Custom business operation (e.g., `process_order`).                             | `order_placement`                          | String               |
| **Dependency**     | `dependency.name`           | Name of external service (e.g., `payment_gateway`).                           | `payment-service`                          | String               |
| **Cache**          | `cache.hits`                | Cache hit/miss metrics.                                                      | `42`                                       | Long                 |

---
#### **3. Query Examples**
Use these queries to analyze monolith telemetry in tools like Prometheus, Grafana, or Elasticsearch.

##### **A. High-Level Overview (Prometheus)**
```promql
# API Gateway: Request Latency (P99)
histogram_quantile(0.99, sum(rate(http_request_size_bucket[5m])) by (le))

# Business Operation Failures
count(increase(http_errors_total[5m])) by (business_op)
```

##### **B. Database Query Bottlenecks (Prometheus)**
```promql
# Slowest database queries (top 5)
topk(5, rate(jdbc_query_time_seconds_sum[5m])) by (query)
```

##### **C. Distributed Trace Analysis (Jaeger/Zipkin)**
```sql
# Traces where 'payment_gateway' dependency failed
SELECT * FROM traces
WHERE spans.dependency.name = 'payment_gateway'
AND spans.error_code IS NOT NULL
ORDER BY duration_ms DESC
LIMIT 100;
```

##### **D. Cache Performance (Elasticsearch)**
```json
GET /logs/_search
{
  "query": {
    "match": {
      "cache.type": "redis"
    }
  },
  "aggs": {
    "cache_misses": { "sum": { "field": "cache.misses" } },
    "slow_operations": {
      "terms": { "field": "duration_ms", "order": { "duration_ms": "desc" } },
      "size": 10
    }
  }
}
```

##### **E. Business Operation Trace (OpenTelemetry)**
```go
// Instrumented business operation (e.g., order processing)
ctx, span := otel.Tracer("order-service").Start(ctx, "process_order")
defer span.End()

// Simulate external call
client := http.Client{
  Timeout: 5 * time.Second,
  Transport: &otelhttp.Transport{
    TracerProvider: otel.TracerProvider,
  },
}
resp, err := client.Get("https://payment-service/process")
span.SetAttribute("dependency.name", "payment-service")
```

---

#### **4. Implementation Checklist**
| **Step**               | **Action Items**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Instrumentation**    | Add OpenTelemetry/Prometheus auto-instrumentation agents to the app runtime.      |
| **Layer Separation**   | Use labels/attributes to distinguish API, application, and DB layers.           |
| **Context Propagation**| Inject `trace_id`, `span_id` into:
  - HTTP headers (for external calls).                                               |
  - Database queries (via JDBC interceptors).                                        |
| **Sampling**           | Apply adaptive sampling (e.g., lower sampling for high-volume endpoints).       |
| **Alerting**           | Define SLOs for:
  - API latency (P99 > 500ms).                                                      |
  - Database query time (P99 > 2s).                                                 |
  - Cache hit ratio (<80%).                                                          |
| **Log Correlation**    | Include `trace_id` and `span_id` in structured logs.                            |
| **Visualization**      | Create dashboards for:
  - End-to-end latency by business operation.                                         |
  - Dependency call graphs.                                                         |
  - Error rates per layer.                                                           |

---

#### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                                  |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Distributed Tracing]** | Extends monolith observability to external services.                           | Hybrid monolith-microservices architectures.  |
| **[Service Mesh Integration]** | Uses Envoy/Linkerd to instrument sidecar proxies for monoliths.              | When monoliths call external APIs.           |
| **[Anomaly Detection]**   | Applies ML to detect deviations in monolith telemetry (e.g., sudden spikes).   | Proactive issue detection.                    |
| **[Log Correlation]**     | Links logs, traces, and metrics using `trace_id` and `span_id`.              | Debugging complex failures across layers.     |
| **[Instrumentation as Code]** | Manages instrumentation via IaC (e.g., OpenTelemetry Operator).           | CI/CD consistency.                           |

---

#### **6. Tools & Libraries**
| **Category**       | **Tools/Libraries**                                                                 | **Notes**                                  |
|--------------------|------------------------------------------------------------------------------------|--------------------------------------------|
| **Metrics**        | Prometheus, Datadog, New Relic                                                | Use custom dimensions for layer separation. |
| **Traces**         | Jaeger, Zipkin, OpenTelemetry Collector                                        | Propagate context via W3C Trace Context.   |
| **Logs**           | ELK Stack, Loki, OpenSearch                                                   | Structured logs with `trace_id`.           |
| **Instrumentation**| OpenTelemetry Auto-Instrumentation, Prometheus Java Agent, Hibernate Stats       | Minimize code changes.                     |
| **Visualization**  | Grafana, Kibana, Datadog Dashboards                                            | Pre-built monolith dashboards available.    |

---
#### **7. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|--------------------------------------|--------------------------------------------------------------------------------|
| Over-instrumenting (performance impact) | Use sampling and focus on critical paths.                                   |
| Noisy metrics (e.g., internal DB queries) | Exclude internal calls with labels (e.g., `internal_only=true`).           |
| Context loss across layers           | Enforce context propagation in middleware (e.g., Spring AOP, Express middleware). |
| Correlating logs without `trace_id`  | Add a log processor to inject `trace_id` into unstructured logs.             |
| Alert fatigue from internal errors   | Filter alerts by `error.type` (e.g., `DB_CONNECTION_ERROR` vs. `USER_ERROR`). |

---
#### **8. Example Architecture**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                Monolith Observability                          │
├───────────────┬───────────────┬────────────────┬─────────────┬───────────────┤
│   API Layer   │  App Layer    │  Database      │  Cache       │  External Deps │
│ (Prometheus)  │ (OTel)        │ (JDBC Stats)   │ (Redis Stats)│ (OTel Client)  │
└───────────────┴───────────────┴────────────────┴─────────────┴───────────────┘
                                      ↑ Context Propagation via Headers/Interceptors
┌───────────────────────────────────────────────────────────────────────────────┐
│                                Observability Backend                            │
├───────────┬───────────┬───────────┬─────────────┬─────────────┤
│ Metrics   │  Traces   │  Logs     │  Alerts     │  Dashboards │
│ (Prom)    │ (Jaeger)  │ (ELK)     │ (PagerDuty) │ (Grafana)   │
└───────────┴───────────┴───────────┴─────────────┴─────────────┘
```

---
**Keywords**: Monolith Observability, Distributed tracing, Context propagation, OpenTelemetry, Prometheus, Jaeger, Log correlation, Microservices vs. Monoliths.