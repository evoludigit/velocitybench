# **[Pattern] Tracing Guidelines Reference Guide**

---
## **Overview**
Tracing Guidelines is a design pattern that standardizes how distributed systems track and debug requests across microservices, APIs, and infrastructure components. By implementing consistent tracing practices, teams can:
- **Isolate latency bottlenecks** with end-to-end request flows.
- **Analyze dependencies** between services and detect cross-service failures.
- **Comply with observability best practices** (e.g., OpenTelemetry, Jaeger, Zipkin).

Best suited for **distributed systems, serverless architectures, and event-driven workflows**, this pattern ensures traces are **identifiable, portable, and traceable** from request initiation to final response. Key considerations include **scope, instrumentation, and correlation** rules to avoid performance overhead while maximizing debuggability.

---

## **Implementation Details**

### **1. Core Concepts**
| **Term**               | **Definition**                                                                 | **Key Attributes**                                                                 |
|------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Span**               | A single operation or function call within a trace (e.g., "API Gateway → Service A"). | Attributes: Name, Timestamp, Duration, Logs, Tags.                               |
| **Trace**              | A collection of spans linked by a common **trace ID** (end-to-end request). | Parent-Child relationships, hierarchical.                                        |
| **Trace Context**      | Metadata (e.g., `trace-id`, `span-id`) injected into requests.                | Ensures trace propagation across service boundaries.                             |
| **Sampler**            | Rules for how many traces to record (e.g., always, probabilistic, or trace-count-based). | Controls overhead (e.g., 1% of traces sampled for production).                     |

### **2. Key Implementation Steps**
1. **Instrumentation**
   - **Auto-instrument** using SDKs (OpenTelemetry, AWS X-Ray, Datadog).
   - **Manual instrumentation** for custom logic (e.g., database queries, external API calls).
   - Example (OpenTelemetry Python):
     ```python
     from opentelemetry import trace
     tracer = trace.get_tracer("my-service")

     with tracer.start_as_current_span("db_query"):
         # Execute database query
     ```

2. **Trace Propagation**
   - **Inject** `trace-id`/`span-id` into HTTP headers, context props, or gRPC metadata.
   - Example (HTTP header):
     ```
     traceparent: 00-<trace-id>-<parent-span-id>-01
     tracestate: rojict=00f067bb0bec06cdb745c30860a9e3anis-oneone
     ```

3. **Sampling Strategy**
   - **Always-on sampling**: Debugging environments (100% of traces).
   - **Probabilistic sampling**: Production (e.g., `p=0.1` for 10% of traces).
   - **Head-based sampling**: Sample based on request attributes (e.g., `/healthz` routes).

4. **Data Storage & Analysis**
   - **Backend**: Jaeger, Zipkin, AWS X-Ray, or custom Elasticsearch pipelines.
   - **Query tools**: Use filters (e.g., `service="payment-service"`) or custom dashboards.

---

## **Schema Reference**
Below is a standardized schema for tracing payloads (adaptable to your stack).

| **Field**          | **Type**       | **Description**                                                                 | **Example Value**                     |
|--------------------|----------------|-------------------------------------------------------------------------------|---------------------------------------|
| `trace_id`         | UUID           | Unique identifier for a trace.                                               | `00f067bb0bec06cdb745c30860a9e3a`    |
| `span_id`          | UUID           | Unique identifier for a span within a trace.                                 | `00f067bb0bec06cdb745c30860a9e3b`    |
| `parent_span_id`   | UUID           | Parent span ID (for hierarchical traces).                                    | `00f067bb0bec06cdb745c30860a9e3a`    |
| `name`             | String         | Descriptive name of the span (e.g., `"validate-payment"`).                   | `"api-call-to-bank"`                 |
| `start_time`       | ISO 8601       | When the span began.                                                          | `"2024-01-15T12:34:56.789Z"`        |
| `end_time`         | ISO 8601       | When the span ended.                                                           | `"2024-01-15T12:34:57.123Z"`        |
| `duration`         | Nanoseconds    | Span execution time.                                                           | `344000000`                          |
| `attributes`       | Key-Value      | Custom metadata (e.g., `{"status": "success", "user_id": "123"}`).            | `{ "http.method": "POST", "status": "200" }` |
| `logs`             | Array          | Timed events (e.g., `{"timestamp": "123456", "message": "DB query initiated"}`). | `[{"message": "Connected to DB"}]`    |
| `resource`         | Object         | Service context (e.g., `{"service.name": "order-service"}`).                  | `{"service.name": "checkout-api"}`   |

---

## **Query Examples**
### **1. Find Slow API Calls**
**Query (Jaeger/Zipkin):**
```sql
SELECT name, avg(duration)
FROM spans
WHERE name LIKE '%api%'
  AND duration > 1000000000  -- >1 second
  AND resource.service = 'checkout-service'
GROUP BY name
ORDER BY avg(duration) DESC;
```

**Output:**
| **Name**               | **Avg. Duration (ms)** |
|------------------------|------------------------|
| `call_to_payment_gw`   | 2400                   |
| `db_fraud_check`       | 1800                   |

---

### **2. Trace a Specific User Request**
**Command (OpenTelemetry CLI):**
```bash
opentelemetry-collector --query 'trace_id="00f067bb0bec06cdb745c30860a9e3a"'
```
**Expected Output (JSON):**
```json
{
  "traces": [
    {
      "spans": [
        {
          "name": "checkout/api/v1/orders",
          "duration": "344.2ms",
          "attributes": { "http.method": "POST", "user_id": "abc123" }
        },
        {
          "name": "db:orders.create",
          "duration": "120.5ms"
        }
      ]
    }
  ]
}
```

---

### **3. Find Correlated Failures**
**Query (Elasticsearch/Kibana):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "status.code": "500" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```
**Filter by:**
- `service.name` (e.g., `"payment-service"`).
- `http.status_code` (e.g., `>= 500`).

---

## **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|
| **Overhead from too many traces**     | Use **sampling** (e.g., `p=0.01` for production).                           |
| **Broken trace propagation**         | Validate headers/metadata **at service entry points**.                     |
| **Noisy logs in traces**              | Use **log levels** (e.g., only `ERROR` logs in `attributes`).               |
| **Inconsistent span names**           | Enforce **naming conventions** (e.g., `service/resource/action`).           |
| **Missing critical attributes**       | Instrument **all async operations** (e.g., SQS, Kafka consumers).          |

---

## **Related Patterns**
1. **Logging Guidelines**
   - *Complements*: Use traces for **timeline context** and logs for **detailed debugging**.

2. **Metrics Guidelines**
   - *Complements*: Trace-based metrics (e.g., `p99_latency`) and logs help correlate performance issues.

3. **Distributed Locks**
   - *Related*: Traces help debug **deadlocks** in distributed systems (e.g., `Raft` or `ZooKeeper`).

4. **Circuit Breakers**
   - *Related*: Traces show **failure cascades** when circuit breakers trip.

5. **Idempotency Keys**
   - *Related*: Correlate traces with **idempotency IDs** for retries (e.g., `order_id`).

---
## **Further Reading**
- [OpenTelemetry Specs](https://opentelemetry.io/docs/specs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/latest/)
- [AWS X-Ray Best Practices](https://docs.aws.amazon.com/xray/latest/devguide/xray-console.html)

---
**Last Updated:** [Date]
**Version:** 1.2