**[Pattern] Latency Observability: Reference Guide**

---

### **Overview**
Latency observability is a **performance monitoring and debugging pattern** focused on tracking, analyzing, and optimizing system latency across applications, services, and infrastructure. By capturing time-based metrics (e.g., request processing duration, database queries, network hops), teams can proactively identify bottlenecks, correlate events, and ensure **real-time SLO compliance**. This guide covers core concepts, implementation strategies, schema references, and query best practices for integrating latency observability into your monitoring stack.

---

### **Key Concepts**
Latency observability relies on three pillars:
1. **Timing Metrics**: Capturing precise start/end timestamps for:
   - Application request lifecycles (e.g., HTTP endpoints, gRPC calls).
   - Database queries, external API calls, and storage operations.
   - Infrastructure events (e.g., cold starts, GC pauses).
2. **Contextual Annotations**: Attaching contextual data (e.g., request IDs, user sessions, tags) to correlate latency with business events.
3. **Sampling/Retention**: Balancing granularity (full tracing vs. sampling) and long-term storage strategies for historical analysis.

**Common Latency Sources**:
- **Client-Side**: User-agent latency (TTFB), network round trips.
- **Server-Side**: Application processing, dependency calls (e.g., `SELECT * FROM users`).
- **Infrastructure**: Docker container startup, load balancer routing.

---

### **Implementation Details**

#### **1. Data Schema**
Use the following schema to standardize latency traces across systems:

| **Field**               | **Type**       | **Description**                                                                                     | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `trace_id`              | UUID (string)  | Unique identifier for a root-to-leaf request flow.                                                 | `a1b2c3d4-5678-90ef-ghij-klmnopqr1234` |
| `span_id`               | UUID (string)  | Identifies a single operation within a trace.                                                      | `55b7d93b-2b4f-482a-9c1e-1f3d5e7a8b9c` |
| `operation_name`        | string         | Describes the operation (e.g., `GET /api/users`, `db.query`).                                      | `GET /users`                          |
| `start_timestamp`       | Unix epoch (ms)| Start time of the operation.                                                                        | `1712345678901`                       |
| `end_timestamp`         | Unix epoch (ms)| End time of the operation.                                                                      | `1712345679123`                       |
| `duration`              | float (ms)     | Computed as `end_timestamp - start_timestamp`.                                                     | `232.1`                               |
| `status_code`           | string         | HTTP status (e.g., `200`, `500`) or custom codes (e.g., `timeout`).                                  | `200`                                 |
| `error`                 | string         | Error message (if applicable).                                                                    | `Database connection timeout`         |
| `parent_span_id`        | UUID (string)  | Links spans in a hierarchical trace (e.g., `rpc_call` → `db_query`).                                | `a1b2c3d4-5678-90ef-ghij-klmnopqr1235` |
| `resource_tags`         | object         | Key-value pairs for filtering/analysis (e.g., `service: auth-service`, `database: postgres`).      | `{ "env": "prod", "region": "us-east" }` |
| `attributes`            | object         | Additional metadata (e.g., `user_id`, `request_body.size`).                                        | `{ "user_id": "123", "size": 4096 }`  |

---
#### **2. Instrumentation Strategies**
**A. Application-Level**
- **SDKs/Libraries**:
  Use OpenTelemetry SDKs (e.g., `opentelemetry-python`, `opentelemetry-auto-instrumentation`) to auto-instrument frameworks (Flask, Express, Spring Boot).
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("get_users"):
      # Your business logic here
  ```
- **Manual Instrumentation**:
  Explicitly wrap slow operations (e.g., database calls) with span contexts.
  ```python
  span = tracer.start_span("db.query", attributes={"query": "SELECT * FROM users"})
  try:
      result = db.execute_query()
  finally:
      span.end()
  ```

**B. Infrastructure-Level**
- **Cloud Providers**:
  Enable native tracing in AWS X-Ray, Azure Application Insights, or GCP Trace.
- **Databases**:
  Use extension tools like [PGTap](https://github.com/dimitri/PGTap) for PostgreSQL or [MySQL Slow Query Log](https://dev.mysql.com/doc/refman/8.0/en/slow-query-log.html).
- **Network**:
  Capture TCP/UDP latencies via `netdata` or `Prometheus` metrics (e.g., `http_request_duration_seconds`).

**C. Edge/Client-Side**
- **Browser**: Integrate [OpenTelemetry Web](https://opentelemetry.io/docs/instrumentation/js/getting-started/) SDKs.
- **Mobile**: Use [OpenTelemetry SDK for iOS/Android](https://opentelemetry.io/docs/instrumentation/native/).

---
#### **3. Storage & Retention**
| **Tool**               | **Use Case**                          | **Retention Policy**                     |
|------------------------|---------------------------------------|-------------------------------------------|
| **Tempo (Grafana)**    | Logs + traces                         | 30 days (default), customizable           |
| **Jaeger**             | Distributed tracing                   | 7–30 days                                 |
| **Datadog**            | All-in-one observability              | 30–365 days (varies by tier)             |
| **AWS X-Ray**          | Serverless/AWS-native apps            | 15–365 days                               |
| **Self-Hosted (Elasticsearch)** | High-volume traces | 1–5 years (compressed)                  |

---
### **Query Examples**
#### **1. Identify Top-Latency Services**
**Schema Focus**: `resource_tags.service`, `duration`
**PromQL (Prometheus)**:
```promql
# Average duration by service (last 24h)
histogram_quantile(0.95, sum by (service) (rate(duration_bucket[1h]))) > 500
```
**Grafana Loki**:
```logql
# Filter logs with spans > 1s
{job="myapp"} | json | duration > 1000
```

#### **2. Correlate Latency with Errors**
**Schema Focus**: `error`, `operation_name`, `status_code`
**Elasticsearch (Painless)**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "status_code": { "value": "500" } } },
        { "range": { "duration": { "gt": 300 } } }
      ]
    }
  }
}
```

#### **3. Trace Root Cause Analysis**
**Schema Focus**: `trace_id`, `parent_span_id`, `operation_name`
**Jaeger Query**:
```
find service="auth-service" | duration > 2s | limit 10
```

---
### **Related Patterns**
1. **[Distributed Tracing](https://www.oreilly.com/library/view/observability-engineering/9781492033345/ch07.html)**
   - Extends latency observability with cross-service end-to-end traces.
   - **Tools**: OpenTelemetry Collector, Zipkin.

2. **[Error Budgeting](https://sre.google/sre-book/monitoring-distributed-systems/#error-budgeting)**
   - Aligns latency/SLO violations with error budgets to prevent "alert fatigue."

3. **[Canary Analysis](https://www.datadoghq.com/blog/aws-canary-analysis/)**
   - Uses latency trends to detect regressions in incremental deployments.

4. **[Performance Budgeting](https://css-tricks.com/performance-budgets/)**
   - Sets latency thresholds (e.g., "90th percentile < 300ms") for CI/CD gates.

5. **[Observability for Serverless](https://aws.amazon.com/blogs/compute/serverless-observability-using-aws-x-ray/)**
   - Adapts latency patterns for AWS Lambda/DynamoDB.

---
### **Best Practices**
1. **Standardize Naming**: Use consistent `operation_name` conventions (e.g., `GET /api/v1/users`).
2. **Sample Wisely**: Use **adaptive sampling** (e.g., OpenTelemetry’s `sampler.head`) to reduce cost for high-volume traces.
3. **Alert on Slopes**: Monitor **latency percentiles** (e.g., 95th) for gradual degradation, not just spikes.
4. **Context Matters**: Enrich spans with business context (e.g., `user_id`, `session_type`).
5. **Avoid Noisy Data**: Exclude backend instrumentation noise (e.g., SDK overhead) from SLOs.

---
### **Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| High latency in one service   | Check `duration` histograms for the service.                                  | Optimize code/database queries.                                               |
| Missing traces                | Verify SDK auto-instrumentation is enabled.                                   | Reinstall SDKs or manually instrument critical paths.                        |
| Corrupted trace IDs           | Inconsistent `trace_id`/`span_id` in logs.                                   | Use OpenTelemetry’s propagation headers (e.g., `traceparent`).                |
| Storage costs rising           | High-volume sampling or long retention.                                      | Adjust sampling rate or archive old traces.                                  |

---
### **Example Workflow**
1. **Detect**: A 95th-percentile spike in `GET /api/users` (latency: 1.2s → 3.5s).
2. **Trace**: Query Jaeger for traces with `operation_name = "GET /users"` and `duration > 1000ms`.
3. **Drill Down**: Identify a slow `db.query` span (500ms) under `parent_span_id`.
4. **Fix**: Optimize the query or add a cache (Redis).
5. **Validate**: Re-run the latency query to confirm improvement.

---
**See Also**:
- [OpenTelemetry Latency Guidelines](https://opentelemetry.io/docs/specs/semconv/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/latest/)