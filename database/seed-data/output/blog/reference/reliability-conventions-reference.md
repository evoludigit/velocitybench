# **[Pattern] Reliability Conventions Reference Guide**

---

## **Overview**
The **Reliability Conventions** pattern defines standardized naming, tagging, and configuration strategies to ensure consistent system reliability across distributed services, microservices, and infrastructure components. This pattern helps organizations predictably monitor, troubleshoot, and enforce reliability policies (e.g., SLOs, SLIs) by aligning naming schemes, metrics, and failure classification. By adopting these conventions, teams reduce ambiguity in observability data, automate reliability checks, and simplify compliance with service-level agreements (SLAs).

Conventions in this pattern include:
- **Service and component naming**: Structured, machine-readable identifiers.
- **Error and failure classification**: Standardized taxonomies for incidents.
- **Metric and alerting prefixes**: Uniform naming for observability signals.
- **Policy tagging**: Consistent labeling for SLO tracking.

This guide covers implementation details, schema definitions, and practical examples for enforcing reliability conventions in modern cloud-native architectures.

---

## **Key Concepts**
### **1. Core Principles**
| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Consistency**         | Uniform naming across services, components, and observability systems.      |
| **Machine Readability** | Structured formats (e.g., `service-name/environment/component`) for parsing. |
| **Extensibility**       | Supports hierarchical and versioned naming (e.g., `v1`, `v2`).              |
| **Auditability**        | Unique identifiers for tracing failures back to root causes.                |
| **Tooling Integration** | Works with Prometheus, Grafana, OpenTelemetry, and incident management tools.|

### **2. Key Components**
| Component          | Purpose                                                                   |
|--------------------|-----------------------------------------------------------------------------|
| **Service Naming**  | Standardized names for services (e.g., `auth-service-prod`).              |
| **Failure Taxonomy**| Structured failure types (e.g., `rate-limiter:429`, `db-connection:failed`).|
| **Metric Prefixes** | Unique prefixes for observability (e.g., `auth_service` for service A).     |
| **SLO Tags**        | Labels for SLO tracking (e.g., `slo:auth_latency_p99 < 200ms`).              |
| **Policy Configs**  | Centralized rules for alerts, budgets, and remediation.                    |

---

## **Schema Reference**
### **1. Service Naming Convention**
| Field          | Format                          | Example                     | Notes                                  |
|----------------|---------------------------------|-----------------------------|----------------------------------------|
| **Service Type** | `[type]/[environment]`         | `api/prod`                   | `type`: `api`, `db`, `cache`, `worker` |
| **Component**   | `[service-type]-[name]`        | `api/auth-service`           | Use hyphens for readability.           |
| **Version**     | `-[version]` (optional)        | `api/auth-service-v2`        | Append versions for tracking.          |
| **Instance ID** | `-[instance-suffix]` (optional)| `api/auth-service-prod-a`    | Distinguish multi-region instances.    |

**Full Example:**
`api/prod/auth-service-v2`

---

### **2. Failure Classification Schema**
| Field          | Format                          | Example                     | Description                                  |
|----------------|---------------------------------|-----------------------------|----------------------------------------------|
| **Category**   | `[provider]`                    | `db`, `network`, `auth`      | High-level failure source.                   |
| **Subcategory**| `[category]:[specific]`         | `db:connection-timeout`     | Narrower failure type.                       |
| **Severity**   | `[subcategory]-[severity]`      | `db:connection-timeout:critical` | Severity levels: `critical`, `warning`, `info`. |
| **Context**    | (Optional) `[{key:val}]`        | `db:connection-timeout:critical[region=eu-west]` | Additional metadata for filtering.          |

**Examples:**
- `db:connection-timeout:critical`
- `cache:memory-exhausted:warning[instance=cache-prod-b]`

---

### **3. Metric Prefix Standard**
| Prefix          | Format                          | Example Metric               | Purpose                                  |
|-----------------|---------------------------------|------------------------------|------------------------------------------|
| **Service**     | `{service-name}_`               | `auth_service_latency_ms`    | Namespacing for service-specific metrics. |
| **Component**   | `{service}_{component}`         | `auth_service_db_connections`| Granular metrics per component.          |
| **Operation**   | `{service}_{operation}`         | `auth_service_login_attempts`| Action-based metrics.                    |
| **Error**       | `{service}_errors_{category}`   | `auth_service_errors_auth`    | Error-type metrics.                       |

**Full Example:**
`auth_service_db_query_time_ms`

---

### **4. SLO Tagging Schema**
| Tag Key          | Format                          | Example Value               | Description                          |
|------------------|---------------------------------|-----------------------------|--------------------------------------|
| **SLO Name**     | `slo:{service}-{metric}`        | `slo:auth-service:login_p99` | Matches metric prefix.               |
| **Target**       | `<value>[<unit>]`                | `500ms`                      | SLI/SLO target (e.g., latency).      |
| **Budget**       | `budget:{error-rate}`            | `budget:1e-3`                | Error budget (e.g., 0.1% errors).     |
| **Window**       | `window:{duration}`              | `window:1h`                  | Evaluation window (e.g., hourly).     |

**Examples:**
- `slo:auth-service:login_p99 < 500ms`
- `budget:auth-service:errors:5m < 0.05`

---

## **Implementation Details**
### **1. Enforcement Rules**
| Rule                | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Naming Enforcement** | Use tools like **Terraform**, **Kubernetes admission controllers**, or **CI/CD validations** to reject non-compliant names. |
| **Metric Labeling**  | Enforce metric labels via **Prometheus relabeling config** or **Grafana dashboards**. |
| **Failure Classification** | Standardize with **OpenTelemetry structured logging** or **custom severity levels** in observability tools. |
| **SLO Tracking**    | Use **Google Cloud’s SLO tooling**, **Prometheus Alertmanager**, or **custom scripts** to validate tags. |

### **2. Tooling Integration**
| Tool/Service       | Use Case                                                                 |
|--------------------|--------------------------------------------------------------------------|
| **Prometheus**     | Relabel metrics to enforce prefixes (e.g., `relabel_configs` in `prometheus.yml`). |
| **OpenTelemetry**  | Tag spans with structured failure classifications.                         |
| **Grafana**        | Create dashboards filtering by SLO tags (e.g., `slo:auth-service:login_p99`). |
| **Incident Tools** | Integrate with **PagerDuty**, **Opsgenie**, or **Jira** to auto-tag incidents (e.g., `failure:db:connection-timeout`). |
| **CI/CD Pipelines**| Fail builds if naming conventions aren’t met (e.g., via **GitHub Actions** or **Jenkins plugins**). |

---

## **Query Examples**
### **1. Prometheus Queries for Reliability**
**Example 1: Auth Service Latency (SLO Check)**
```promql
sum(rate(auth_service_login_latency_ms_sum[5m])) by (slo) / sum(rate(auth_service_login_count[5m])) by (slo)
< 500  # Check if SLO is violated
```

**Example 2: Error Budget Consumption**
```promql
sum(rate(auth_service_errors_auth_total[1h])) by (slo)
> (1e-3 * sum(auth_service_login_count))  # Check if budget exceeded
```

**Example 3: Filter Failures by Taxonomy**
```promql
histogram_quantile(0.95, sum(rate(db_operation_latency_bucket[5m])) by (le, failure_category))
where failure_category == "db:connection-timeout:critical"
```

---

### **2. OpenTelemetry Trace Filtering**
**Example: Query for Auth Service Failures (in Jaeger/Grafana)**
```
service.name = "auth-service"
resource.attributes["failure.type"] = "auth:token_validation_failed"
severity.text = "ERROR"
```

---

### **3. SLO Validation Script (Python Example)**
```python
import prometheus_client

# Fetch SLO metrics
latency = prometheus_client.GaugeMetricFamily(
    name="auth_service_login_p99",
    value=1200,  # ms (from Prometheus)
    labels={"slo": "auth-service:login_p99"}
)
error_rate = prometheus_client.GaugeMetricFamily(
    name="auth_service_errors_ratio",
    value=0.002,  # 0.2% errors
    labels={"budget": "auth-service:errors_5m"}
)

# Validate against targets
if latency.value > 500:
    print("SLO Violation: Latency > 500ms")
if error_rate.value > 0.001:
    print("Budget Exceeded: Errors > 0.1%")
```

---

## **Related Patterns**
| Pattern Name               | Description                                                                 | Relationship to Reliability Conventions                          |
|----------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------|
| **[Observability-Driven Development](link)** | Emphasizes observability from day 1 of development.                      | **Complements** by providing the data needed to enforce conventions.|
| **[Chaos Engineering](link)** | Proactively tests failure scenarios.                                     | **Uses** reliability conventions to classify and analyze chaos test failures. |
| **[Service Level Objectives (SLOs)](link)** | Defines measurable reliability targets.                                   | **Relies on** conventions for consistent SLO tagging and validation.  |
| **[Error Budget Allocation](link)** | Distributes error tolerance across services.                             | **Leverages** failure taxonomy to calculate budgets per service.     |
| **[Multi-Region Resilience](link)** | Ensures reliability across geographic boundaries.                        | **Extends** naming conventions to include region-specific instances.|

---

## **Best Practices**
1. **Start Small**: Adopt conventions for one service or component first, then expand.
2. **Document as Code**: Store schemas (e.g., failure taxonomies) in **Markdown** or **JSON** files in your repo.
3. **Automate Validation**: Use **linters** (e.g., for naming) or **CI checks** to catch violations early.
4. **Iterate with Feedback**: Refine taxonomies based on real-world failure data.
5. **Tooling**: Prefer open standards (e.g., OpenTelemetry) over vendor lock-in.
6. **Training**: Educate teams on why conventions matter (e.g., reduce on-call noise).

---
**Example Workflow**:
1. A failure occurs in `auth-service-prod`.
2. The error is classified as `auth:token_validation_failed:warning[instance=auth-prod-a]`.
3. Prometheus alerts trigger based on the `auth_service_errors_auth_total` metric.
4. The incident tool auto-tags the issue with `failure:auth:token_validation_failed`.
5. SLO validation detects a 0.3% error rate, exceeding the `budget:auth-service:errors_5m < 0.05` target.
6. Teams investigate using traces filtered by `service.name="auth-service"` and `failure.type="auth:token_validation_failed"`.