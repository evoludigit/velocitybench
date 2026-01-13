# **[Availability Troubleshooting] Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing and resolving availability issues in distributed systems, cloud services, or on-premises infrastructure. Availability troubleshooting involves identifying root causes (e.g., component failures, resource exhaustion, misconfigurations) and mitigating their impact on uptime and performance. This pattern covers **proactive monitoring, reactive diagnosis, and recovery strategies** while ensuring minimal downtime. It applies to **services, APIs, databases, microservices, or entire infrastructure layers**.

Key focus areas:
- **Root cause analysis (RCA)** – Isolating failures from logs, metrics, and events.
- **Dependency mapping** – Tracing failures across services, networks, or third-party integrations.
- **Mitigation strategies** – Applying fixes (rollbacks, scaling, failovers) with minimal disruption.
- **Prevention** – Adjusting configurations, alerts, and resilience mechanisms.

This guide assumes familiarity with **observability tools** (logs, metrics, traces), **infrastructure as code (IaC)**, and **cloud provider APIs**.

---

## **Schema Reference**
Below are key objects, events, and attributes used in availability troubleshooting.

| **Category**               | **Schema Name**               | **Description**                                                                                     | **Example Attributes**                                                                 |
|----------------------------|-------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Monitoring Signals**     | `ServiceMetric`               | Metrics (CPU, latency, error rates) indicating degraded performance or failures.                   | `metric_name: "request_latency_p99", value: 5000ms, threshold: 2s, timestamp: 2024-01-01T12:00:00Z` |
|                            | `LogEntry`                    | Structured or unstructured logs from applications, middleware, or infrastructure.                | `"level": "ERROR", "message": "Connection timeout to DB", "service": "user-service"`   |
|                            | `AlertEvent`                  | Alerts from monitoring systems (e.g., Prometheus, Datadog, AWS CloudWatch).                       | `severity: CRITICAL, rule: "HighErrorRate", affected_service: "auth-api"`              |
| **Dependencies**           | `ServiceDependency`           | Graph of service-to-service or service-to-infra relationships (e.g., API → Database → Load Balancer). | `depends_on: ["db-primary", "cache-cluster"]`                                           |
| **Incident States**        | `IncidentRecord`              | Tracker for incidents (status, assignee, resolution time).                                         | `id: "INC-20240101-001", status: "IN_PROGRESS", root_cause: "DiskFull"`               |
| **Mitigation Actions**     | `RemediationPlan`             | Predefined or ad-hoc fixes (e.g., rollback, scale-up, patch).                                      | `action: "restart_k8s_pod", target: "order-service-v1", executed_at: "2024-01-01T13:15:00Z"` |
| **Performance Baselines**  | `ServiceBaseline`             | Historical averages for latency, throughput, or error rates to detect anomalies.                 | `p99_latency: 300ms, error_rate: 0.01%, baseline_window: "2023-12-01–2023-12-31"`    |

---

## **Query Examples**
Use these queries (in SQL, PromQL, or Elasticsearch DSL) to diagnose availability issues.

---

### **1. Identifying High-Error Rates**
**Scenario**: A spike in 5xx errors for an API endpoint.
**Tools**: Prometheus, Datadog, or CloudWatch Metrics.

**PromQL Query**:
```sql
rate(http_requests_total{status=~"5.."}[1m])
  > on(instance) group_left
  cluster:rate(http_requests_total[1m])
  and
  cluster:sum(rate(http_requests_total[1m]))
    by (cluster)
```
**Output Interpretation**:
- Identify clusters or endpoints with error rates exceeding thresholds (e.g., >1%).
- Cross-reference with `ServiceDependency` to trace upstream/downstream impacts.

**Elasticsearch Query (Kibana)**:
```json
GET /logs-* /_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "by_service": { "terms": { "field": "service.name" } }
  }
}
```

---

### **2. Tracing Latency Spikes**
**Scenario**: End-to-end request latency exceeds SLA (e.g., >1s for 99% of requests).
**Tools**: OpenTelemetry, Jaeger, or AWS X-Ray.

**OpenTelemetry Query (Grafana)**:
```sql
select
  service_name,
  span_name,
  avg(duration) as avg_duration,
  percentile(duration, 99) as p99_duration
from traces
where timestamp > now() - 1h
group by service_name, span_name
order by p99_duration desc
limit 10
```

**AWS CloudWatch Logs Insights**:
```sql
stats avg(@duration) as p99 by @service
| filter @duration > 1000
| sort @p99 desc
```

---

### **3. Dependency Analysis**
**Scenario**: A database outage cascades to multiple services.
**Tools**: Custom dependency graphs (e.g., using Python’s `networkx`) or tools like **Grafana Tempo**.

**Python Example (Dependency Graph)**:
```python
import networkx as nx

# Build graph from monitoring data
G = nx.DiGraph()
G.add_node("db-primary", type="database")
G.add_node("user-service", type="service")
G.add_edge("user-service", "db-primary", weight=90)  # 90% requests go to DB

# Detect disrupted edges (e.g., DB health < 90%)
disrupted_edges = [edge for edge in G.edges() if G.nodes[edge[1]]["health"] < 0.9]
print("Potential cascading failures:", disrupted_edges)
```

---

### **4. Incident Root Cause Analysis**
**Scenario**: Service degraded after a deployment. Use **postmortem data** to correlate events.
**Tools**: Jira, PagerDuty, or custom dashboards.

**SQL Query (Postgres)**:
```sql
SELECT
  i.incident_id,
  i.timestamp,
  s.service_name,
  a.severity,
  l.message,
  COUNT(*) OVER (PARTITION BY i.incident_id) as log_count
FROM incidents i
JOIN alerts a ON i.incident_id = a.incident_id
JOIN logs l ON i.incident_id = l.incident_id
WHERE i.timestamp > NOW() - INTERVAL '1 day'
  AND a.severity = 'CRITICAL'
ORDER BY i.timestamp DESC
LIMIT 50;
```

---

### **5. Preventive Checks**
**Scenario**: Proactively identify misconfigurations before failures.
**Tools**: Infrastructure-as-Code (IaC) validators (e.g., **Terraform + TFLint**).

**Terraform Validation Example**:
```hcl
# Check for under-replicated replicas in Kubernetes
data "kubernetes_namespace" "default" {
  metadata {
    name = "default"
  }
}
resource "kubectl_manifest" "pod_replicas" {
  yaml_body = file("${path.module}/pod-check.yaml")
}
# Output: Pods with replica count < desired (e.g., 0/1)
```

---

## **Mitigation Strategies**
Apply these patterns during troubleshooting:

| **Strategy**               | **When to Use**                          | **Example Actions**                                                                 |
|----------------------------|------------------------------------------|------------------------------------------------------------------------------------|
| **Isolation**              | Single component failure (e.g., pod crash). | Cordon faulty nodes in Kubernetes; disable problematic microservice.              |
| **Rollback**               | Deployment caused outage.                 | Revert to previous container image version or IaC template.                        |
| **Scaling**                | Resource exhaustion (CPU/memory).         | Auto-scale pods horizontally (K8s HPA) or vertically (resize VMs).                |
| **Failover**               | Primary service unavailable.              | Switch to read replicas (Postgres); route traffic to backup regions (AWS Global Accelerator). |
| **Circuit Breaking**       | Upstream service degraded.                | Enable Hystrix/Resilience4j in microservices to throttle calls.                     |
| **Configuration Fix**      | Misconfiguration (e.g., timeouts).       | Adjust API Gateway timeouts; update DB connection pool settings.                  |

---

## **Related Patterns**
1. **[Observability Patterns](https://example.com/observability)**
   - *Why*: Availability troubleshooting relies on logs, metrics, and traces. Reference this for **instrumentation strategies**.
2. **[Chaos Engineering](https://example.com/chaos)**
   - *Why*: Simulate failures to validate resilience. Use **Gremlin** or **Chaos Mesh** to test availability under stress.
3. **[Self-Healing Systems](https://example.com/self-healing)**
   - *Why*: Automate recovery (e.g., Kubernetes **PodDisruptionBudgets**, **Liveness Probes**).
4. **[Multi-Region Architecture](https://example.com/multi-region)**
   - *Why*: Reduce single-point failures with **active-active deployments** (e.g., AWS Global Accelerator).
5. **[Capacity Planning](https://example.com/capacity)**
   - *Why*: Prevent resource exhaustion with **load testing** (e.g., Locust, k6) and forecasting.

---
## **Next Steps**
1. **Instrument**: Ensure all services emit metrics/logs to a central system (e.g., Prometheus + Grafana).
2. **Automate**: Use **SLOs** (Service Level Objectives) to trigger alerts (e.g., "99.9% availability").
3. **Document**: Maintain a **runbook** for common outages (e.g., "How to handle DB replica lag").
4. **Review**: Conduct **postmortems** to update mitigation plans.

---
**References**:
- [Google SRE Book (Chapter 4: Measurement)](https://sre.google/sre-book/monitoring-distributed-systems/)
- [AWS Well-Architected Framework (Reliability Pillar)](https://aws.amazon.com/architecture/well-architected/)
- [Chaos Engineering Handbook](https://www.oreilly.com/library/view/chaos-engineering-handbook/9781492078372/)