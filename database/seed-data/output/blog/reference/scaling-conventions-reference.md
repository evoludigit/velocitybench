# **[Scaling Conventions] Reference Guide**

---

## **Overview**
The **Scaling Conventions** pattern standardizes how metric, log, and trace data is structured when exporting from distributed systems like microservices, cloud applications, or large-scale applications. By enforcing consistent naming, tagging, and formatting conventions, this pattern enables:
- **Interoperability** between tools (e.g., Prometheus, Grafana, Datadog, CloudWatch).
- **Easier aggregation** of metrics across services.
- **Reduced ambiguity** in monitoring queries, logs, and traces.
- **Better compatibility** with observability platforms and third-party integrations.

Conventions are critical when:
- Deploying multi-team applications with heterogeneous monitoring stacks.
- Using polyglot architectures (e.g., Go, Python, Java).
- Integrating with logging/observability vendors (e.g., Lighthouse, ELK).

---

## **Key Concepts**
### **1. Metric Naming & Dimensions**
Metrics follow the **`{namespace}/{subsystem}/{metric_name}`** structure (e.g., `database/postgres/connection_count`).
**Dimensions (tags)** must use:
- **Snake case** (e.g., `http_status_code`, not `HTTPStatusCode`).
- **Consistent prefixes/suffixes** (e.g., `job:`, `instance_id:`).
- **Avoid reserved prefixes** (e.g., `service`, `app`, `host` can conflict).

### **2. Log & Trace Structure**
- **Log format**: Structured JSON with mandatory fields like `level`, `service`, `trace_id`, and `timestamp`.
- **Trace structure**: Explicitly linked to metrics via shared `trace_id`/`span_id`.

### **3. Time Series Alignment**
- Metrics must align with the **export interval** (e.g., 15s, 60s).
- Avoid over-sampling or down-sampling unless explicitly documented.

---

## **Schema Reference**
| **Component**       | **Field**               | **Allowed Values**                          | **Requirements**                                                                 |
|----------------------|--------------------------|---------------------------------------------|---------------------------------------------------------------------------------|
| **Metrics**          | Namespace               | Lowercase, no special chars (e.g., `api`)    | Must prefix all metrics from the same service.                                  |
|                      | Subsystem               | Lowercase, no spaces (e.g., `auth`, `cache`) | Describes the subsystem (e.g., `database/redis`).                               |
|                      | Metric Name             | Snake case (e.g., `latency_ms`, `error_rate`) | Must avoid platform-specific names (e.g., `http_requests_total`).                |
| **Dimensions**       | Field Name              | Snake case (e.g., `http_method`)            | Use consistent prefixes (e.g., `route:`, `user:`).                               |
|                      | Reserved Fields         | `job`, `instance_id`, `service_version`     | Mandatory if applicable.                                                          |
| **Logs**             | Structured Key          | `level`, `service`, `trace_id`              | `level` must be lowercase (e.g., `warn`, `error`).                               |
|                      | Dynamic Fields          | Any valid JSON key                          | Prefix with `custom:` (e.g., `custom:user_id`).                                 |
| **Traces**           | Span Attributes         | `operation_name`, `http.method`             | Mirror metric dimensions for correlation (e.g., `route:api/v2/users`).            |
| **Sampling**         | Rate                   | 1.0 (default), <1.0 (e.g., `0.5`)            | Document sampling strategy in `README.md`.                                      |

---

## **Query Examples**
### **Metric Queries**
| **Use Case**               | **Example Query**                                                                 | **Notes**                                                                          |
|----------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Service-wide latency**   | `sum(rate(api/cache/call_latency_ms[5m])) by (service, route)`                     | Aggregates latency by route across services.                                        |
| **Error rate filtering**   | `histogram_quantile(0.99, sum(rate(api/auth/auth_failures[1m])) by (http_method))` | Quantile analysis for errors.                                                       |
| **Log correlation**        | `logs{level="error", service="api", route="/payments"} |trace_id="abc123"`                          | Filters logs linked to a specific trace/span.                                      |
| **Trace sampling**         | `traces{service="auth", operation="login", sampling_rate=0.5}`                    | Adjusts trace sampling to balance load.                                             |

### **Log Filtering**
```plaintext
# Search logs for 5xx errors in the 'orders' service
level="error" AND service="orders" AND http_status_code LIKE "5%"

# Filter by custom dimension
level="warn" AND custom:customer_id="12345" AND route="/checkout"
```

---

## **Implementation Rules**
### **1. Metric Naming**
- **Prefix**: Use the service namespace (e.g., `ecommerce`).
- **Subsystem**: Add a subsystem (e.g., `ecommerce/cart`).
- **Metric**: Avoid platform defaults (e.g., use `ecommerce/cart/items_added` instead of `cart_items_added`).

### **2. Log Structure**
```json
{
  "level": "warn",
  "service": "auth",
  "trace_id": "xyz789",
  "timestamp": "2023-11-15T12:34:56Z",
  "message": "Login failed for user_id=1001",
  "custom": {
    "user_id": "1001",
    "api_version": "v2"
  }
}
```

### **3. Trace Attributes**
Link metrics and logs to traces via:
- `trace_id` (same across spans).
- `span_id` (per operation).
- **Dimensions**: Mirror metric tags (e.g., `route:api/v2/users`).

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                     | **Mitigation**                                                                   |
|----------------------------------|----------------------------------------------------------------------------------|
| Inconsistent metric prefixes     | Enforce a naming convention via **GitHub Lint** or **custom CI checks**.        |
| Overusing dynamic log fields     | Restrict dynamic fields to `custom:*` prefix to avoid tooling conflicts.         |
| Trace sampling misconfiguration  | Document sampling rules in `README.md` and use **environment variables**.       |
| Long log lines                   | Truncate message fields to 4KB max; use structured JSON for critical data.       |

---

## **Related Patterns**
1. **[Micrometer + Prometheus Integration](https://micrometer.io/docs/binding/prometheus)** – Best practices for metric exports.
2. **[Structured Logging](https://structured-logging.dev/)** – Guidelines for log standardization.
3. **[OpenTelemetry Basics](https://opentelemetry.io/docs/)** – Standard for tracing and metrics.
4. **[Alert Manager Conventions](https://prometheus.io/docs/alerting/latest/configuration/)** – How to label alerts consistently.
5. **[SLOs & Error Budgets](https://sre.google/sre-book/monitoring-distributed-systems/)** – Complements observability by defining reliability targets.

---
## **Tools & Validation**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Prometheus Exporter** | Validate metric names via `http://<host>/metrics`                         |
| **Loki/Grafana**       | Check log schema consistency with **logsQL** queries.                       |
| **CI Linting**         | Use **Pre-commit hooks** to reject non-conforming metric/log names.        |
| **OpenTelemetry SDK**  | Enforce trace attribute conventions during SDK initialization.              |

---
## **Example Workflow**
1. **Export Metrics**: Use the `ecommerce/cart` namespace for all cart-related metrics.
   ```yaml
   # Prometheus exporter config
   - job_name: 'ecommerce_cart'
     metrics_path: '/metrics'
     static_configs:
       - targets: ['localhost:9100']
     relabel_configs:
       - source_labels: [__meta_kubernetes_pod_name]
         target_label: instance_id
   ```
2. **Log Structuring**: Enforce JSON logs with a **custom log shipper** (e.g., Fluentd).
3. **Trace Correlation**: Link metrics (e.g., `ecommerce/cart/cart_add_latency`) to logs/traces via `trace_id`.

---
## **Further Reading**
- [CNCF Observability Whitepaper](https://www.cncf.io/wp-content/uploads/2022/03/Observability_Whitepaper_v3.pdf)
- [Prometheus Namespace Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry Data Model](https://opentelemetry.io/docs/specs/otlp/)

---
**Last Updated**: [Insert Date]
**Maintainer**: [Team/Contact]