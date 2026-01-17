**[Pattern] Performance Conventions Reference Guide**

---

## **Overview**
The **Performance Conventions** pattern standardizes how metrics, traces, and other performance instrumentation are named, structured, and aggregated across services. By defining consistent naming rules, schema formats, and query conventions, this pattern reduces ambiguity, enables cross-service observability, and simplifies analytics workflows (e.g., logs, metrics, traces).

Key benefits include:
- **Consistency**: Uniform instrumentation reduces cognitive load and tooling overhead.
- **Interoperability**: Tools like Prometheus, OpenTelemetry, and ELK can query heterogeneous data reliably.
- **Cost Efficiency**: Avoids redundant instrumentation (e.g., duplicate tags or metrics).
- **Scalability**: Standardized schemas ensure observability tools can process high-volume data efficiently.

This guide covers schema design, naming conventions, query best practices, and integration with related patterns.

---

## **1. Schema Reference**
Performance data (logs, metrics, traces) must adhere to a **unified schema** to ensure compatibility. Below are core conventions:

### **1.1 Core Schema Attributes**
| **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `service_name`     | String        | Name of the emitting service (lowercase, no spaces).                                             | `auth-service`, `order-api`                                                         |
| `resource_type`    | Enum          | Logs, Metrics, Traces, or DistributedTrace.                                                       | `metrics`, `logs` (`distributed_trace` for OpenTelemetry span IDs)                  |
| `environment`      | String        | Deployment context (e.g., dev, staging, prod) with lowercase, hyphen-separated.                     | `prod-us-west`, `dev-eu-central`                                                    |
| `namespace`        | String        | Optional organizational tag (e.g., team, project).                                                 | `finance`, `payment-gateway`                                                        |
| `timestamp`        | ISO 8601      | Record timestamp (UTC).                                                                           | `2024-05-20T14:30:00Z`                                                              |
| `severity`         | Enum          | Logs only: `debug`, `info`, `warning`, `error`, `critical`.                                        | `error`                                                                             |
| `metric_name`      | String        | Metric identifier (kebab-case, lowercase). Required for `resource_type=metrics`.                   | `http_request_duration_ms`, `cache_hit_rate`                                        |
| `span_id`          | String/UUID   | Trace identifier (optional unless `resource_type=distributed_trace`).                               | `6d77f90b-0c91-4294-903a-a968c6d1376b`                                             |
| `trace_id`         | String/UUID   | Parent trace ID for distributed context.                                                          | Same as `span_id` for root spans; linked via `traceparent` header in traces.        |

---

### **1.2 Metric-Specific Schema**
For **metrics**, extend the core schema with **metric-specific attributes**:

| **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `unit`             | String        | SI units (e.g., `ms`, `samples`, `bytes`).                                                          | `ms`, `requests`                                                                   |
| `dimensions`       | Key-Value Map | Optional: Key = metric dimension (e.g., `method`, `status_code`), Value = value (string/number). | `{"method": "POST", "status_code": "404"}`                                          |
| `value`            | Number        | Numeric value of the metric (e.g., rate, count).                                                    | `42.5`, `1000`                                                                     |

**Example Metric Payload**:
```json
{
  "service_name": "user-service",
  "resource_type": "metrics",
  "environment": "prod-us-west",
  "namespace": "auth",
  "timestamp": "2024-05-20T14:30:00Z",
  "metric_name": "user_login_attempts",
  "unit": "count",
  "value": 42,
  "dimensions": {
    "auth_method": "oauth2",
    "region": "us-east"
  }
}
```

---

### **1.3 Log-Specific Schema**
For **logs**, include structured fields alongside free-form `message`:

| **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `message`          | String        | Human-readable log entry (optional if structured fields are sufficient).                            | `"User login failed: invalid credentials"`                                           |
| `context`          | Object        | Key-value pairs for unstructured data (e.g., `user_id`, `ip_address`).                             | `{"user_id": "123", "ip": "192.168.1.1"}`                                          |

**Example Log Payload**:
```json
{
  "service_name": "payment-service",
  "resource_type": "logs",
  "environment": "dev",
  "timestamp": "2024-05-20T14:30:00Z",
  "severity": "error",
  "message": "Payment processing failed",
  "context": {
    "transaction_id": "txn_456",
    "amount": 99.99,
    "error_code": "INSUFFICIENT_FUNDS"
  }
}
```

---

### **1.4 Trace-Specific Schema**
For **distributed traces**, include:
- **Parent/Child Relationships**: Use `parent_span_id` to link spans.
- **Attributes**: Key-value pairs for trace context (e.g., `http.method`, `db.operation`).

| **Field**          | **Type**       | **Description**                                                                                     | **Example Values**                                                                 |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `span_name`        | String        | Operation name (e.g., `get_user`, `pay_order`).                                                     | `process_payment`                                                                   |
| `start_time`       | ISO 8601      | Span start timestamp (UTC).                                                                       | `2024-05-20T14:30:01Z`                                                              |
| `end_time`         | ISO 8601      | Span end timestamp (UTC).                                                                         | `2024-05-20T14:30:02Z`                                                              |
| `attributes`       | Key-Value Map | Contextual data (e.g., `http.status_code`, `user_id`).                                             | `{"http.method": "POST", "user_id": "789"}`                                          |
| `parent_span_id`   | String/UUID   | ID of parent span (empty for root spans).                                                          | `d8e7b9c5-...` (or empty)                                                            |

**Example Trace Payload**:
```json
{
  "service_name": "order-service",
  "resource_type": "distributed_trace",
  "trace_id": "a1b2c3...",
  "span_id": "d8e7b9c5...",
  "span_name": "validate_order",
  "start_time": "2024-05-20T14:30:01Z",
  "end_time": "2024-05-20T14:30:02Z",
  "attributes": {
    "http.method": "POST",
    "order_id": "ord_123",
    "user_id": "789"
  },
  "parent_span_id": null
}
```

---

## **2. Naming Conventions**
### **2.1 Service Names**
- **Format**: kebab-case, lowercase.
- **Rules**:
  - Use domain-specific prefixes (e.g., `auth-service`, `inventory-api`).
  - Avoid abbreviations unless widely understood (e.g., `user-mgmt` over `u-mgmt`).
  - Example: `payment-gateway` (not `pay-gw`).

### **2.2 Metric Names**
- **Format**: kebab-case, lowercase.
- **Rules**:
  - Start with a verb (e.g., `process_`).
  - Avoid generic names like `count`; specify context (e.g., `user_login_attempts`).
  - Include units in names if ambiguous (e.g., `http_request_duration_ms`).
  - Example: `cache_miss_rate` (not `miss` or `cache`).

### **2.3 Log Severity Levels**
- **Values**: `debug`, `info`, `warning`, `error`, `critical`.
- **Usage**:
  - `debug`: Verbose logs for troubleshooting.
  - `info`: Routine operations (e.g., `user logged in`).
  - `warning`: Potential issues (e.g., `retries exceeded`).
  - `error`: Failed operations (e.g., `database connection failed`).
  - `critical`: System-threatening events (e.g., `disk space exhausted`).

### **2.4 Trace Attributes**
- **Prefixes**: Use dot notation to avoid collisions (e.g., `http.method`, `db.query`).
- **Examples**:
  - `http.status_code`
  - `user.id`
  - `payment.amount`

---

## **3. Query Examples**
### **3.1 Aggregating Metrics**
**Query**: *"Show average HTTP response time by environment for the last hour."*
**Tool**: Prometheus
**Query**:
```promql
avg by (environment) (
  rate(http_request_duration_seconds_bucket[1h])
) unless on(environment) count_over_time(http_request_duration_seconds_bucket[1h]) == 0
```

**Equivalent in OpenTelemetry Query**:
```sql
SELECT AVG(duration)
FROM traces
WHERE service_name = 'auth-service'
  AND timestamp >= now() - 1h
GROUP BY environment;
```

---

### **3.2 Filtering Logs**
**Query**: *"Find all `error` logs in `prod-us-west` for `payment-service` related to `INSUFFICIENT_FUNDS`."*
**Tool**: ELK (Kibana)
**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "service_name": "payment-service" } },
        { "term": { "environment": "prod-us-west" } },
        { "term": { "severity": "error" } },
        { "term": { "context.error_code": "INSUFFICIENT_FUNDS" } }
      ]
    }
  }
}
```

---

### **3.3 Trace Analysis**
**Query**: *"Show all root spans in `order-service` with `span_name` containing `validation`."*
**Tool**: Jaeger/Zipkin
**Query**:
```sql
SELECT * FROM distributed_traces
WHERE service_name = 'order-service'
  AND span_name LIKE '%validation%'
  AND parent_span_id IS NULL;
```

---

## **4. Integration with Related Patterns**
| **Pattern**               | **Interaction**                                                                                     | **Recommendations**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Telemetry Export**      | Performance conventions rely on exported data from this pattern.                                    | Use OpenTelemetry Collector to validate schema before ingestion.                                        |
| **Distributed Tracing**   | Traces must adhere to convention schema for interoperability.                                        | Standardize `traceparent` header format across services.                                               |
| **Observability Store**   | Query tools must support the defined schema for filtering/aggregation.                               | Choose tools with OpenTelemetry/SQL-compatible query languages (e.g., Grafana, Prometheus).            |
| **Service Mesh**          | Mesh components (e.g., Istio) may inject metadata (e.g., `pod_name`).                               | Include mesh-specific fields in traces/logs (e.g., `mesh.pod_name`).                                    |
| **Canary Analysis**       | Performance metrics inform canary rollouts.                                                         | Track `metric_name: service_latency` for canary vs. stable versions.                                    |

---

## **5. Validation and Enforcement**
### **5.1 Schema Validation**
- **Tools**: Use OpenAPI/Swagger for metrics/logs REST APIs or JSON Schema for direct ingestion.
- **Example JSON Schema Snippet**:
  ```json
  {
    "type": "object",
    "required": ["service_name", "resource_type", "timestamp"],
    "properties": {
      "service_name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
      "resource_type": { "enum": ["logs", "metrics", "distributed_trace"] },
      "timestamp": { "format": "date-time" }
    }
  }
  ```

### **5.2 Automated Compliance Checks**
- **CI/CD Pipeline**: Run linters (e.g., `jsonnet` for schema validation) against instrumentation code.
- **Example Rule**:
  ```bash
  # Check metric names for kebab-case compliance
  grep -E '^[a-z][a-z0-9-]*_' metrics.yaml || exit 1
  ```

### **5.3 Tooling**
- **Prometheus Alertmanager**: Validate metric names via `match[]` rules.
- **Loki**: Use structured logging parsers (e.g., Fluent Bit) to enforce schema.
- **OpenTelemetry Collector**: Configure `batch` processors to reject malformed spans/metrics.

---
## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                              | **Solution**                                                                                     |
|-------------------------------------|---------------------------------------------|--------------------------------------------------------------------------------------------------|
| Metrics missing from aggregators    | Incorrect `namespace` or `environment`.     | Verify schema payloads match tooling expectations (e.g., Prometheus `namespace` vs. `service_name`). |
| Traces show orphaned spans          | Missing `trace_id` or `span_id`.           | Ensure OpenTelemetry SDKs propagate `traceparent` headers.                                       |
| High cardinality in metrics         | Overuse of dimensions (e.g., `user_id`).   | Limit dimensions to business-relevant fields (e.g., `region`, `auth_method`).                   |
| Logs duplicated across environments| Misconfigured log shippers.                 | Use `environment` field to filter logs per deployment context.                                   |

---
## **7. See Also**
- **[Telemetry Export]** – How to collect and export performance data.
- **[Distributed Tracing]** – Linking spans across microservices.
- **[Observability Store]** – Tools for querying metrics/logs/traces.
- **[Service Mesh]** – Integrating conventions with Istio/Linkerd.