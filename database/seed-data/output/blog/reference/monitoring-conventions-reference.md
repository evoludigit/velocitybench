# **[Pattern] Monitoring Conventions Reference Guide**

---

## **Overview**
The **Monitoring Conventions** pattern establishes standardized naming, tagging, and structure rules for metrics, logs, and traces to ensure consistency, interoperability, and ease of observability across distributed systems. By enforcing uniform patterns—such as metric naming, unit consistency, and hierarchical tagging—organizations avoid confusion, improve alerting reliability, and simplify integration with monitoring tools (e.g., Prometheus, OpenTelemetry, Datadog).

This guide covers key schema conventions, implementation best practices, and query-building examples. Adherence to these standards is critical for large-scale systems where observability must scale with complexity.

---

## **Key Concepts**

### **1. Metrics Naming**
Use **descriptive, camelCase** names with **slashes (`/`) to denote hierarchy** (e.g., `network.tcp.connections.active`). Avoid special characters and spaces.

### **2. Unit Consistency**
Metrics must include **SI or standardized units** (e.g., `bytes`, `milliseconds`) via:
- **Metric name suffixes** (e.g., `count`, `bytes_received`).
- **Labels** (e.g., `unit="bytes"` or `unit="ms"`).

### **3. Tagging (Labels)**
Use **semantic tags** with these guidelines:
- **namespace** (e.g., `service=web-api`).
- **dimensions** (e.g., `instance=prod-1`).
- **classifiers** (e.g., `env=production`).
- **Avoid** highly cardinal tags (e.g., dynamic IDs; use hashes or aggregates).

### **4. Log Formatting**
Logs must follow **JSON structured format** for parsing consistency:
```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "service": "auth-service",
  "level": "ERROR",
  "user_id": "abc123",
  "trace_id": "12345678",
  "message": "Login attempt failed"
}
```

### **5. Trace Hierarchy**
Traces should include:
- **Span IDs** (unique per operation).
- **Resource tags** (e.g., `service.version=1.2.0`).
- **Parent-child relationships** (e.g., RPC calls, external APIs).

---

## **Schema Reference**

| **Component**       | **Rule**                                                                                                                                                                                                 | **Example**                              |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Metric Name**     | CamelCase, `/`-delimited hierarchy, no spaces or special chars                                                                                                                                | `http.requests.latency`                  |
| **Units**           | Append unit to name or use a `unit` label                                                                                                                                                           | `name="bytes_sent", unit="bytes"`        |
| **Labels**          | Lowercase, `-` separated, semantic (e.g., `instance`, `region`)                                                                                                                              | `service=payment-service, instance=ny1`  |
| **Log Field**       | JSON keys: lowercase, `_` for multi-word (avoid `CamelCase` or `snake_case`)                                                                                                                  | `"error_code": 404`                      |
| **Trace Tag**       | Prefix with `trace.` or `span.` (e.g., `trace.id`, `span.name`)                                                                                                                                 | `span.name="db.query"`                   |

---

## **Implementation Details**

### **1. Metric Naming Hierarchy**
Metrics should reflect **hierarchical meaning** (e.g., `/` separates categories):
- **High-level category** → **Subcategory** → **Metric**
- Example: `network/tcp/connections/active`

### **2. Label Cardinality**
**Critical:** Limit labels to avoid metrics explosion.
- **High cardinality labels** (e.g., `user_id`): Aggregate or hash (e.g., `user_id_hash`).
- **Low cardinality labels** (e.g., `env`, `service`): Standardize prefixes/suffixes.

### **3. Log Correlation**
Link logs to traces using:
- **Trace IDs** in log fields (e.g., `trace_id`).
- **Log sampling** (e.g., sample 1% of logs for high-volume services).

### **4. Exceptions**
- **Legacy systems**: Deprecate non-compliant metrics over 2–3 releases.
- **Vendor-specific**: Document deviations from this pattern.

---

## **Query Examples**

### **1. PromQL (Metrics)**
**Query:** *"Average latency of HTTP requests in `web-service` over the last 5 minutes."*
```promql
rate(http_request_duration_seconds_sum[5m])
  / rate(http_request_duration_seconds_count[5m])
  > 1000
  and service = "web-service"
```

**Query:** *"Active TCP connections per instance."*
```promql
sum by (instance) (tcp_connections_active)
```

### **2. LogQL (Loki)**
**Query:** *"Errors in `auth-service` where `user_id` is not null."*
```logql
{service="auth-service"} | json | log_level="ERROR" | user_id != ""
```

**Query:** *"Filter logs by trace ID."*
```logql
{service="payment-service"} | json | trace_id="12345678"
```

### **3. OpenTelemetry Trace Filter**
**Query:** *"Find spans with `db.query` in `database` service."*
```spql
resource.service.name="database" AND span.name="db.query"
```

---

## **Tool-Specific Notes**

| **Tool**         | **Convention Enforcement**                                                                                                                                                                                                 | **Example Rule**                          |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Prometheus**   | Labels must match metric names; units enforced in alerts.                                                                                                                                                       | `if (http_requests_errors > 10) ...`       |
| **OpenTelemetry**| Mandate `resource` attributes (e.g., `service.name`).                                                                                                                                                                     | `resource.attributes["service.name"]`      |
| **Elasticsearch**| Log ingest pipeline validates JSON structure.                                                                                                                                                                       | `"process": "required"`                    |
| **Grafana**      | Dashboards use templated variables for dynamic labels (e.g., `$service`).                                                                                                                                            | `selected.service: $service`               |

---

## **Common Pitfalls**
- **Over-tagging**: Excessive labels increase storage costs and slow queries.
- **Unit conflicts**: Mixing `count` and `total` without clarifying (e.g., `total_bytes` vs. `bytes_sent`).
- **Inconsistent naming**: `RequestDuration` vs. `request_duration` causes alerting blind spots.
- **No sampling**: High-volume services produce log/trace noise.

---

## **Related Patterns**
1. **[Instrumentation Best Practices]**
   - Guides for adding metrics/logs from code (e.g., auto-instrumentation libraries).

2. **[Alerting Rules]**
   - How to design alerts using standardized metrics (e.g., SLO-based thresholds).

3. **[Observability Data Retention]**
   - Policies for archiving vs. deleting old metrics/logs/traces.

4. **[Canary Analysis]**
   - Use monitoring conventions to compare canary vs. production metrics.

5. **[Context Propagation]**
   - Ensures trace IDs/log correlations across microservices.

---
## **Further Reading**
- [Prometheus Label Naming](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Schema Spec](https://github.com/open-telemetry/semantic_conventions)
- [Loki LogQL Guide](https://grafana.com/docs/loki/latest/logql/)
- [Google SLO Best Practices](https://cloud.google.com/blog/products/observability/slo-based-alerting)