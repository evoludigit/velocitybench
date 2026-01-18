# **[Pattern] Reliability Troubleshooting Reference Guide**

---

## **Overview**
The **Reliability Troubleshooting** pattern provides a structured approach to diagnosing and resolving issues affecting system performance, availability, or consistency. This guide outlines methodologies for identifying failures, analyzing root causes, and implementing corrective measures while minimizing downtime and impact. The pattern applies to distributed systems, cloud-native architectures, microservices, and legacy systems, ensuring adherence to **SLAs, error budgets, and resilience principles**.

Key focus areas include:
- **Proactive monitoring** (identifying anomalies before outages)
- **Reactive diagnostics** (isolating failures under pressure)
- **Post-mortem analysis** (preventing recurrence via improvements)
- **Automated remediation** (self-healing systems)

---

## **Implementation Details**

### **1. Key Concepts**
| Concept               | Definition                                                                                     | Example                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Symptom**           | Observable degradation or failure (e.g., latency spikes, 5xx errors).                          | `HTTP 500 errors` or `Database connection timeouts`.                     |
| **Root Cause**        | Underlying issue causing the symptom (e.g., misconfigured load balancer, cascading failures).| `Replica lag` due to slow disk I/O on a primary database node.         |
| **Impact**            | Scope of affected users/services (e.g., 10% of API calls).                                     | `Regional outage` affecting users in `us-east-1`.                       |
| **Mitigation**        | Temporary fix to restore functionality (e.g., rolling back a deployment).                     | `Scaling up a read replica` to reduce query load.                        |
| **Resolution**        | Permanent fix addressing the root cause.                                                     | `Upgrading storage tier` to reduce latency.                              |
| **Error Budget**      | Allowed degradation per SLO (e.g., 1% uptime tolerance).                                     | `SLO: 99.95% availability → 0.05% allowed outage`.                       |

---

### **2. Troubleshooting Workflow**
The pattern follows a **4-phase lifecycle**:

#### **Phase 1: Detection**
- **Objective**: Identify deviations from expected behavior.
- **Tools**:
  - **Metrics**: Prometheus, Datadog, New Relic.
  - **Logs**: ELK Stack, Loki.
  - **Tracing**: Jaeger, OpenTelemetry.
- **Example Query**:
  ```sql
  -- Alert for 99th percentile latency exceeding threshold
  SELECT avg(latency) FROM request_metrics
  WHERE avg(latency) > 500ms AND service = "payment-gateway";
  ```

#### **Phase 2: Isolation**
- **Objective**: Narrow the issue to a specific component.
- **Techniques**:
  - **Binary search**: Compare metrics between healthy and affected nodes.
  - **A/B testing**: Isolate changes (e.g., deploy a canary release).
  - **Dependency mapping**: Use tools like `chaos engineering` (e.g., Gremlin) to test resilience.
- **Example Scenario**:
  - Symptom: `Payment failures` in `checkout-service`.
  - Hypothesis: `Database timeouts` → Verify with `pg_stat_activity` or `CloudWatch Database Insights`.

#### **Phase 3: Root Cause Analysis (RCA)**
- **Tools**:
  - **Structured RCA**: Use the **5 Whys** or **Fishbone Diagram** (Ishikawa).
  - **Correlation Analysis**: Join logs + metrics (e.g., `ELASTICSEARCH` + `GRAFANA`).
- **Example Root Cause**:
  ```
  1. Symptom: `Checkout API latency > 2s`.
  2. Hypothesis: `External API dependency failing`.
  3. Evidence: `HTTP 429 errors` from `payment-processor` in logs.
  4. Root Cause: `Rate limiting` on `payment-processor` due to unhandled backpressure.
  ```

#### **Phase 4: Resolution & Improvements**
- **Mitigation**:
  - **Short-term**: Circuit breakers (e.g., `Hystrix`, `Resilience4j`), fallbacks.
  - **Long-term**: Retry policies, circuit breaker thresholds, or scaling adjustments.
- **Post-Mortem**:
  - **Template**:
    ```markdown
    - **Issue**: [Symptom]
    - **Root Cause**: [Analysis]
    - **Impact**: [Scope]
    - **Mitigation**: [Action]
    - **Resolution**: [Fix]
    - **Prevention**: [Proposal] (e.g., "Add auto-scaling for DB replicas")
    ```
  - **Tools**: `Blameless Postmortems` (Google’s approach), `PagerDuty Incident Reports`.

---

## **Schema Reference**
| **Component**         | **Schema**                                                                                     | **Example Value**                          |
|-----------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------|
| **Alert Rule**        | `{ severity: [critical/warning], condition: <metric_expression>, action: [pagerduty/slack] }`| `{ severity: "critical", condition: "latency > 1000ms", action: "slack" }` |
| **Incident Ticket**   | `{ id: <string>, status: [open/in_progress/resolved], root_cause: <string>, resolution: <string> }` | `{ "id": "INC-123", "status": "resolved", "root_cause": "disk full", "resolution": "rebooted node" }` |
| **Dependency Graph**  | `{ service: <string>, depends_on: [<list of services>], health_metric: <string> }`           | `{ "service": "order-service", "depends_on": ["payment-gateway"], "health_metric": "http_code_2xx" }` |

---

## **Query Examples**
### **1. Alerting on Error Budgets**
```sql
-- Check if error rate exceeds SLO (99.9% available → 0.1% errors allowed)
SELECT service, count(*) * 100.0 / SUM(count(*)) OVER () AS error_percentage
FROM error_logs
WHERE timestamp > now() - interval '1h'
GROUP BY service
HAVING error_percentage > 0.1;
```

### **2. Database Replica Lag Detection**
```sql
-- Query for PostgreSQL replication lag (using `pg_stat_replication`)
SELECT pid, lag_bytes, lag_duration
FROM pg_stat_replication
WHERE state = 'streaming' AND lag_bytes > 1000000;  -- >1MB lag
```

### **3. Chaos Engineering Experiment**
```bash
# Simulate node failure using Gremlin (Chaos Mesh)
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - default
    labelSelector:
      app: my-app
EOF
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Use Case**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **[Circuit Breaker]**            | Prevents cascading failures by stopping calls to failing services.                                | `API gateways` handling third-party payments.                              |
| **[Retries & Backoff]**          | Automatically retries failed operations with exponential backoff to manage transient errors.       | `Database connections` recovering from network splits.                      |
| **[Rate Limiting]**              | Controls request volumes to prevent overload.                                                      | `User API` during sudden traffic spikes.                                   |
| **[Chaos Engineering]**          | Proactively tests system resilience by injecting failures.                                         | `Pre-launch stress testing` for new deployments.                            |
| **[Distributed Tracing]**        | Tracks requests across services to diagnose latency bottlenecks.                                   | `End-to-end transaction tracing` in microservices.                          |
| **[Golden Signals]**             | Focuses monitoring on **Latency, Traffic, Errors, Saturation** (LTEs).                            | `SRE teams` optimizing service health.                                     |

---

## **Best Practices**
1. **Automate Detection**: Use tools like **Prometheus Alertmanager** or **Datadog Alerts** to reduce mean time to detect (MTTD).
2. **Document Incidents**: Maintain a **blameless post-mortem** database (e.g., `Confluence`, `Notion`).
3. **Chaos Testing**: Run **chaos experiments** regularly (e.g., `Gremlin`, `Chaos Mesh`) to validate resilience.
4. **Error Budgets**: Allocate **1-5% error tolerance** per SLO to balance innovation and stability.
5. ** On-Call Rotation**: Rotate **PagerDuty/Splunk** on-call teams to avoid alert fatigue.

---
**See also**:
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/)
- [Chaos Engineering Principles](https://www.chaosengineering.io/principles.html)