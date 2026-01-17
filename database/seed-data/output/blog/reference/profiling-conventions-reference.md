# **[Pattern] Profiling Conventions Reference Guide**

---

## **Overview**
**Profiling Conventions** is a structured approach to tagging, categorizing, and querying application performance data (e.g., requests, database calls, microservices) to improve observability, debugging, and performance tuning. This pattern standardizes how metrics, logs, and traces are labeled with consistent *profiles*, enabling cross-cutting analysis, aggregation, and alerting. By enforcing key-value-based schemes, teams can efficiently filter, correlate, and act on profiling data without vendor lock-in.

Use cases include:
- **Debugging anomalies** (e.g., "All `db_write` operations with `priority=high` latency > 500ms").
- **Performance baselining** (e.g., "Compare `user_auth` workflows by region").
- **Capacity planning** (e.g., "Identify top 10 slowest profiles in `payment_service`").
- **Compliance auditing** (e.g., "Log all requests with `sensitive_data=true`").

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example Values**                                |
|------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Profile**            | A high-level category defining a group of related profiling events (e.g., `user_auth`, `order_process`). | `auth/login`, `db/search`, `api/payment_gateway` |
| **Tags/Key-Values**    | Labels attached to profiling events to specify context (e.g., `service`, `user_role`, `region`).  | `{service: "order-service", role: "premium"}`     |
| **Metadata**           | Structured data added to events (e.g., instrumented by profiling SDKs) for richer queries.        | `{client_ip: "192.168.1.100", correlation_id: "abc123"}` |
| **Scope**              | The context in which a profile applies (e.g., `service`, `module`, `database`).                  | `service:payments`, `module:discount_calculator` |
| **Severity**           | A predefined classification of impact (e.g., `critical`, `warning`, `info`).                     | `critical`, `high`, `medium`                      |

---

## **Schema Reference**
### **1. Core Profile Schema**
| Field          | Type        | Required | Description                                                                                     | Example Values                          |
|----------------|-------------|----------|-------------------------------------------------------------------------------------------------|-----------------------------------------|
| `profile`      | string      | Yes      | A user-defined identifier for the profiling category.                                           | `user_register`, `cart_add_item`        |
| `timestamp`    | datetime    | Yes      | When the event occurred (ISO 8601 format).                                                      | `2024-03-15T14:30:45Z`                 |
| `tags`         | object      | No       | Key-value pairs defining contextual metadata.                                                   | `{service: "checkout", region: "us-east"}` |
| `metadata`     | object      | No       | Additional unstructured data (e.g., SDK-specific fields).                                       | `{user_id: "user_123", status: "success"}` |

### **2. Standardized Tag Keys (Recommended)**
Use these tags to ensure consistency across systems. Custom keys are allowed but discouraged.

| Tag Key           | Type   | Description                                                                                     | Example Values                          |
|-------------------|--------|-------------------------------------------------------------------------------------------------|-----------------------------------------|
| `service`         | string | Name of the service/module generating the profile.                                             | `product-service`, `inventory`          |
| `operation`       | string | Specific action within the service (e.g., API endpoint, DB query).                            | `get_products`, `update_user`           |
| `user_role`       | string | User access level (if applicable).                                                             | `admin`, `customer`, `guest`            |
| `http_method`     | string | HTTP verb for API calls.                                                                       | `GET`, `POST`, `PUT`                    |
| `region`          | string | Geographic location (e.g., data center, client region).                                         | `us-west2`, `eu-central`                |
| `status`          | string | Outcome of the operation (predefined options preferred).                                       | `success`, `error`, `timeout`           |
| `latency_ms`      | number  | Duration of the event (milliseconds).                                                          | `120`, `500`                            |
| `queue_time_ms`   | number  | Time spent waiting (e.g., in a message queue).                                                 | `85`, `1200`                            |
| `error_code`      | string  | Vendor-specific error identifier (e.g., HTTP status code).                                     | `500`, `404`, `db_connection_failed`   |
| `correlation_id`  | string  | Unique ID for tracing requests across systems.                                                  | `req_abc123xyz`                         |

### **3. Severity Levels**
Use these for alerting and filtering. Extend if needed.

| Severity     | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `critical`   | System-wide outage or severe data loss.                                      |
| `high`       | Major degradation (e.g., 99th percentile latency > 2s).                     |
| `medium`     | Noticeable slowdowns or infrequent failures.                               |
| `low`        | Minor performance issues (e.g., 95th percentile latency > 500ms).           |
| `info`       | Normal operation or non-critical events.                                    |

---

## **Implementation Details**

### **1. Profiling Data Sources**
Profiling Conventions apply to:
- **Traces**: Distributed request flows (e.g., OpenTelemetry spans).
- **Metrics**: Performance counters (e.g., Prometheus, Datadog).
- **Logs**: Structured event logs (e.g., JSON-formatted entries).

### **2. Enforcement Mechanisms**
| Mechanism               | Description                                                                                     | Example Tools                          |
|-------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------|
| **Instrumentation SDK** | Auto-injects tags/metadata into profiling data.                                                | OpenTelemetry, Datadog APM SDK         |
| **Middleware**          | Intercepts requests/responses to add tags (e.g., `service`, `user_role`).                     | Express.js middleware, AWS Lambda hooks |
| **Configuration Files** | Defines default tags for services (e.g., `service: "orders"`).                                | Terraform, Kubernetes annotations      |
| **CI/CD Pipelines**     | Validates profiles against a schema before deployment.                                          | OpenPolicyAgent, Prisma Schema         |

### **3. Standardized Naming Conventions**
- **Profiles**: Use **kebab-case** (e.g., `user_payment_process`).
- **Tags**: Use **snake_case** (e.g., `user_role`, `http_method`).
- **Metadata**: Avoid reserved words (e.g., `timestamp`, `profile`).

---
## **Query Examples**
### **1. Filtering by Profile and Tags**
**Use Case**: *"Find all failed `user_payment` profiles in the `europe-west` region."*
```sql
SELECT *
FROM profiles
WHERE
  profile = "user_payment"
  AND tags.service = "payments-service"
  AND tags.region = "europe-west"
  AND metadata.status = "error";
```

**Grafana Loki Query**:
```sql
{profile="user_payment", tags_service="payments-service", region="europe-west"}
| json
| status="error"
```

### **2. Aggregating Latency by User Role**
**Use Case**: *"Average latency for `admin` vs. `customer` in `order_fulfillment`."*
```promql
sum(rate(profiles_latency_sum{profile="order_fulfillment", tags_user_role=~"admin|customer"}[1m]))
  /
sum(rate(profiles_latency_count{profile="order_fulfillment", tags_user_role=~"admin|customer"}[1m]))
by (tags_user_role)
```

### **3. Alerting on High Severity**
**Use Case**: *"Alert when `db_write` operations with `severity=high` exceed 500ms latency."*
**Prometheus Alert Rule**:
```yaml
- alert: HighDbWriteLatency
  expr: histogram_quantile(0.99, sum(rate(profiles_latency_bucket{profile="db_write", severity="high"}[5m])))
    > 0.5
  for: 5m
  labels:
    severity: critical
```

### **4. Correlating Traces and Logs**
**Use Case**: *"Link traces with logs using `correlation_id`."*
**Elasticsearch Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "profile": "user_auth" } },
        { "term": { "metadata.correlation_id": "req_abc123xyz" } }
      ]
    }
  }
}
```

### **5. Dynamic Tag Sourcing**
**Use Case**: *"Auto-populate `region` from client IP."*
**Example (OpenTelemetry SDK)**:
```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace

tracer_provider = TracerProvider()
tracer = trace.get_tracer(__name__)

def get_region(ip):
    # Logic to map IP to region (e.g., MaxMind GeoIP)
    return "us-west2"

@tracer_provider.add_span_processor
def add_region_tags(span, _):
    span.set_attribute("region", get_region(span.get_attribute("client_ip")))
```

---

## **Best Practices**
1. **Tag Sparsity**: Limit tags to 5–10 key-value pairs per event to avoid cardinality explosion.
2. **Consistency**: Enforce tags across services (e.g., `service` must match a known value).
3. **Deprecation**: Use `deprecated=true` for legacy tags to phase them out.
4. **Sampling**: Apply sampling rules (e.g., 100% for `severity=critical`, 1% for `info`).
5. **Documentation**: Maintain a **tag registry** (e.g., in a wiki or GitHub repo) listing all standardized keys.

---

## **Related Patterns**
| Pattern                          | Description                                                                                     | When to Use                                      |
|----------------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[Structured Logging](link)**   | Defines a standardized format for log messages to enable parsing and querying.                   | When logs need to be queried alongside metrics.   |
| **[Distributed Tracing](link)** | Tracks requests across microservices using trace IDs and spans.                               | For debugging latency in distributed systems.   |
| **[Service Mesh Instrumentation](link)** | Uses sidecar proxies (e.g., Istio, Linkerd) to auto-inject profiling data.                  | When deploying on a service mesh.                 |
| **[Metric Aggregation](link)**   | Defines how metrics are grouped (e.g., by `region`, `service`) for dashboards.                  | For designing observability dashboards.           |
| **[Observability Taxonomy](link)** | Classifies observability data into domains (e.g., "availability," "performance").           | For large-scale observability strategy.          |

---

## **Troubleshooting**
| Issue                          | Root Cause                          | Solution                                                                 |
|---------------------------------|-------------------------------------|--------------------------------------------------------------------------|
| **High Cardinality**           | Too many unique tag values.         | Reduce dynamic tags (e.g., `user_id`) or bucket rare values (e.g., `region`). |
| **Missing Data**               | Tags/metadata not injected.        | Validate SDK configuration or middleware hooks.                          |
| **Query Performance**          | Wide filtering (e.g., `tags.*`).    | Use static keys (e.g., `tags_region`) instead of wildcards.              |
| **Inconsistent Tagging**        | Services use different conventions. | Enforce a tag registry or use a policy engine (e.g., OPA).              |

---
## **See Also**
- [OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/semantic-conventions)
- [Cloud Observability Patterns](https://cloud.google.com/blog/products/observability)
- [Testing Observability Systems](https://www.oreilly.com/library/view/testing-observability-systems/9781492049043/)