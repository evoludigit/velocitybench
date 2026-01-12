**[Pattern] Availability Conventions Reference Guide**

---

### **Overview**
The **Availability Conventions** pattern standardizes how systems communicate the operational status of components, services, or infrastructure. It enables consistent monitoring, alerting, and observability across distributed systems by defining machine-readable **availability states** and their semantic meanings. This pattern is critical for DevOps, SRE, and observability pipelines, ensuring that teams can quickly interpret system health and respond to incidents or degradations.

Key benefits include:
- **Unambiguous status communication** (e.g., "degraded" vs. "unavailable").
- **Interoperability** between tools (e.g., Prometheus, OpenTelemetry, or custom dashboards).
- **Reduced alert fatigue** via clear severity mappings.
- **Alignment with industry standards** (e.g., [OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/specification/tree/main/specification/trace/semantic_conventions)).

This guide covers schema definitions, query patterns, and integration points.

---

## **Implementation Details**

### **Core Concepts**
| Concept               | Description                                                                                                                                 |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Availability State** | A discrete label describing system health (e.g., `ok`, `degraded`, `unavailable`). Must be *exhaustive* (all possible states covered). |
| **Severity**          | Optional enumerated value linking to alerting (e.g., `critical`, `warning`). Helps prioritize responses.                                       |
| **Metadata**          | Key-value pairs (e.g., `error_type="timeout"`) adding context to the state.                                                                  |
| **Transitions**       | Rules governing state changes (e.g., `unavailable → degraded` after 5 minutes).                                                             |
| **Duration**          | Optional time-bound state (e.g., "temporarily degraded during maintenance").                                                                  |

**Example State Definitions:**
```json
{
  "state": "degraded",
  "severity": "warning",
  "metadata": {
    "component": "database",
    "error_type": "high_cpu",
    "duration": "PT10M"  // ISO 8601 duration string
  }
}
```

---

## **Schema Reference**
The following schema defines the standardized availability convention payload. Use this as a template for APIs, metrics, or logs.

| Field        | Type          | Required | Description                                                                                     | Example Values                          |
|--------------|---------------|----------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `state`      | `string`      | ✅        | Current availability state (see [State Enumeration](#state-enumeration)).                     | `"ok"`, `"degraded"`, `"unavailable"`   |
| `severity`   | `string`      | ❌        | Optional severity for alerting (map to SLOs/alerts).                                             | `"critical"`, `"warning"`, `"info"`     |
| `metadata`   | `object`      | ❌        | Additional context (use semantic keys for consistency).                                         | `{"region": "us-west-2", "retry_count": 3}` |
| `last_updated` | `timestamp`  | ✅        | RFC 3339 timestamp (e.g., `2024-01-01T12:00:00Z`) of the last state change.                     | N/A                                     |
| `reason`     | `string`      | ❌        | Human-readable explanation (for debugging).                                                    | `"Disk quota exceeded"`                 |
| `duration`   | `string`      | ❌        | ISO 8601 duration (e.g., `PT5M`) if state is temporary.                                         | `"PT60S"`, `null`                      |

---

### **State Enumeration**
| State         | Definition                                                                                                                                 | Transition Triggers                                                                             |
|---------------|---------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `ok`          | All components functioning as expected.                                                                                                   | Manually reset or automatic recovery (e.g., retry logic).                                     |
| `degraded`    | Performance or functionality impacted (e.g., latency > 1s). Users may notice slowness but the system remains usable.                        | Threshold breaches (e.g., CPU > 90% for 3 minutes).                                           |
| `unavailable` | Component/service is broken or offline. Users cannot interact successfully.                                                             | Critical failures (e.g., database corruption, network partition).                              |
| `maintenance` | Planned outage (use `duration` to specify end time).                                                                                     | Scheduled events (e.g., `"start_time": "2024-01-02T02:00:00Z"`).                             |
| `unknown`     | State cannot be determined (e.g., probe timeout).                                                                                         | Timeouts in health checks or unreadable metrics.                                               |

**Note:** Avoid custom states beyond these; extend only if justified by domain-specific needs (e.g., `backlogged` for a queue).

---

## **Query Examples**

### **1. Filtering by State (Prometheus/Grafana)**
```promql
# Count degraded services in the last 5 minutes
sum by (service) (
  rate(availability_state{state="degraded"}[5m])
) > 0
```

**Label Alignment:**
| Prometheus Label       | Availability Convention Field |
|------------------------|--------------------------------|
| `service`              | `metadata.component`            |
| `state`                | `state`                         |
| `severity`             | `severity`                      |

---

### **2. State Transition Analysis (OpenTelemetry)**
**Log Query (LF/ELK):**
```json
// Find degraded → unavailable transitions
state:degraded
| filter("last_updated" < "now() - 1h")
| where state:unavailable
| sort by @timestamp desc
```

**Trace Context:**
Attach state transitions as spans with:
```json
{
  "name": "state_change",
  "attributes": {
    "availability.state": "unavailable",
    "availability.previous_state": "degraded",
    "availability.reason": "disk_full"
  }
}
```

---

### **3. Alerting Rules (Terraform + Prometheus)**
```hcl
resource "prometheus_alert_rule" "degraded_service" {
  name = "service_degraded"
  rules {
    alert = "ServiceDegraded"
    expr = 'availability_state{state="degraded", severity="warning"} == 1'
    for = "5m"
    labels {
      severity = "warning"
    }
    annotations {
      summary = "{{ $labels.service }} is degraded (instance: {{ $labels.instance }})"
    }
  }
}
```

---

### **4. CLI Output (Custom Tool)**
```bash
# Example: Fetch current state of a Kubernetes pod
kubectl get pod my-pod --output=jsonpath='{.status.conditions[?(@.type=="Availability")].status}'
# Output: "True" (ok) or "False" (unavailable)
```

**Integration Pattern:**
Wrap API responses in a standardized header:
```http
HTTP/1.1 200 OK
X-Availability-State: degraded
X-Availability-Severity: warning
```

---

## **Metadata Semantics**
Use **reserved keys** for consistency across systems:

| Key               | Type          | Example                          | Purpose                                                                 |
|-------------------|---------------|----------------------------------|-------------------------------------------------------------------------|
| `component`       | `string`      | `"payment-service"`               | Identifies the system module.                                          |
| `region`          | `string`      | `"eu-central-1"`                  | Geographic scope (for multi-region deploys).                           |
| `error_type`      | `string`      | `"connection_refused"`           | Machine-parsable error category (map to error codes in logs).           |
| `slo_violation`   | `boolean`     | `true`                           | `true` if the state violates a Service Level Objective (SLO).           |
| `recovery_action` | `string`      | `"restart-worker"`                | Suggested next step (e.g., for runbooks).                               |

**Avoid:**
- Vendor-specific keys (e.g., `aws_error_code`).
- Overly broad keys (e.g., `notes` without structure).

---

## **Related Patterns**
1. **[Health Checks](https://cloud.google.com/architecture/designing-health-checks-for-distributed-systems)**
   - *How*: Define endpoints that emit Availability Conventions.
   - *Why*: Health checks trigger state updates (e.g., `unavailable` on 5xx responses).

2. **[Circuit Breakers](https://microservices.io/patterns/reliability/circuit-breaker.html)**
   - *How*: Use `state="unavailable"` to trigger circuit breaker trips.
   - *Why*: Align failure modes with observability signals.

3. **[Tagging Conventions](https://docs.aws.amazon.com/AWSBillings/latest/DevelopmentGuide/amazon-cloudwatch-metrics-naming-conventions.html)**
   - *How*: Extend metadata with cost-center or team tags.
   - *Why*: Correlate availability with business impact.

4. **[OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/specification/blob/main/specification/trace/semantic_conventions/README.md)**
   - *How*: Map `state` to `process.state` or `service.status` in traces.
   - *Why*: Unify tracing and observability data.

5. **[Service Level Indicators (SLIs)](https://cloud.google.com/blog/products/observability/service-level-indicators-measuring-service-level-objectives)**
   - *How*: Define SLIs using threshold-based transitions (e.g., `degraded` when error rate > 1%).
   - *Why*: Link availability states to business metrics.

---

## **Best Practices**
1. **Exhaustiveness**: Ensure all possible states are covered (e.g., don’t omit "maintenance").
2. **Immutability**: Treat `last_updated` as a single source of truth for state history.
3. **Tooling Support**: Integrate with:
   - **Monitoring**: Prometheus, Datadog, New Relic.
   - **Logging**: OpenTelemetry Collector, Loki.
   - **Incident Management**: PagerDuty, Opsgenie (map severity to on-call escalation).
4. **Backward Compatibility**: Use optional fields (e.g., `severity`) for gradual adoption.
5. **Document Thresholds**: Define how states map to metrics (e.g., "degraded" = `p99_latency > 500ms`).

---
## **Example Workflow**
1. **Detection**: A database probe returns `5xx` → health check emits:
   ```json
   { "state": "unavailable", "metadata": { "component": "db-primary" } }
   ```
2. **Propagation**: OpenTelemetry Collector forwards this to Prometheus as a metric:
   ```promql
   availability_state{state="unavailable", component="db-primary"} = 1
   ```
3. **Alerting**: Prometheus fires an alert triggering a PagerDuty incident.
4. **Resolution**: DevOps team restarts the DB → health check emits:
   ```json
   { "state": "ok", "last_updated": "2024-01-01T12:15:00Z" }
   ```
5. **Analysis**: Logs correlate with traces showing the `state_change` span.

---
**See Also:**
- [OpenTelemetry Availability Metrics](https://github.com/open-telemetry/specification/blob/main/specification/metrics/data-model.md#availability-metrics).
- [SRE Book: Error Budgets](https://sre.google/sre-book/metrics-monitoring-alerting/#error_budgets).