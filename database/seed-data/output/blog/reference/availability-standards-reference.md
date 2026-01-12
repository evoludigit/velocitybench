**[Pattern] Availability Standards Reference Guide**
*Version 1.2* | *Last Updated: [Insert Date]*

---

### **1. Overview**
The **Availability Standards** pattern defines measurable, system-wide requirements for uptime, reliability, and service continuity. It ensures that systems adhere to predefined availability thresholds—critical for mission-critical applications, compliance, or SLA guarantees. This pattern:

- **Standardizes** availability metrics (e.g., uptime %, mean time between failures).
- **Enforces** accountability via targets, monitoring, and alerting.
- **Aligns** with internal policies, regulatory frameworks (e.g., PCI DSS, HIPAA), or third-party SLAs.

It applies to cloud services, on-premises infrastructure, microservices architectures, and hybrid environments. Key trade-offs include cost (redundancy vs. simplicity) and operational complexity (proactive monitoring).

---

### **2. Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Availability SLAs**  | Target uptime percentages (e.g., 99.9%, 99.99%) for services or components.    | Cloud provider guarantees 99.95% availability for a region.                 |
| **MTBF (Mean Time Between Failures)** | Average time between system failures. Higher MTBF = fewer outages.         | A database cluster with an MTBF of 3,040 hours (~4 months).                   |
| **MTTR (Mean Time To Recovery)** | Average time to restore service after a failure. Lower MTTR = faster recovery. | A Kubernetes cluster recovers in <15 minutes post-node failure.              |
| **Redundancy Factor**  | Number of identical active instances to tolerate failures (e.g., N+1).       | A 2+1 redundancy ensures service if two nodes fail.                          |
| **Graceful Degradation** | System reduces performance/functionality instead of crashing during overload. | A website serves static content during peak traffic.                        |
| **Degradation Thresholds** | Predefined metrics (CPU, latency) triggering auto-scaling or failover.      | CPU > 80% triggers spinning up a new pod in Kubernetes.                     |

---

### **3. Schema Reference**
Define availability standards using this schema for consistency:

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     | **Notes**                                  |
|-------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|--------------------------------------------|
| `sla_name`              | String (required) | Unique identifier for the SLA (e.g., "DatabaseService").                     | `"WebAPI_Global_SLA"`                    | Use hyphens for readability.             |
| `target_uptime`         | Float (required) | Target availability (e.g., 99.99 = 99.99%).                                     | `99.95`                               | Must be ≤ 100.0.                          |
| `metrics`               | Array (required) | Array of metric objects (e.g., uptime, MTBF, MTTR).                          | `[{"type": "uptime", "value": 0.9995}]` | Include at least one metric.              |
| `components`            | Array (required) | List of system/components covered by the SLA (e.g., VMs, APIs).              | `[{"name": "PrimaryDB", "type": "PostgreSQL"}]` | Scope SLAs to specific services.          |
| `redundancy`            | Object          | Redundancy configuration (e.g., active-active, N+X).                          | `{"strategy": "active-active", "factor": 2}` | Optional; omit if not applicable.         |
| `degradation_rules`     | Array           | Rules for graceful degradation (e.g., auto-scale, failover thresholds).       | `[{"trigger": "high_latency", "action": "scale-out"}]` | Define key metrics (e.g., latency, CPU).  |
| `monitoring`            | Object          | Monitoring tool and alerting configuration.                                   | `{"tool": "Prometheus", "alerts": ["SLOViolation"]}` | Include critical alerts.                  |
| `compliance_requirements` | Array      | Regulatory or internal policies linked to this SLA.                            | `[{"standard": "PCI_DSS_3.2.1", "section": "9.9"}]` | Use for audit trails.                     |
| `owner`                 | String          | Team/role responsible for maintaining the SLA.                                | `"DevOps Team - Tier 2"`              | Critical for accountability.              |
| `effective_date`        | Date (required) | Date the SLA becomes enforceable.                                             | `"2024-05-01"`                        | Backward-compatible SLAs require explicit dates. |

---

### **4. Implementation Details**
#### **4.1. Defining SLAs**
1. **Scope**: Align SLAs with business-critical systems (e.g., payment processors have higher uptime targets than analytics dashboards).
2. **Hierarchy**:
   - **Service-Level Agreement (SLA)**: Overall system target (e.g., 99.9% for "E-commerce Platform").
   - **Service-Level Objective (SLO)**: Breakdown of SLAs into measurable targets (e.g., 99.99% uptime for the "Checkout Service").
   - **Service-Level Indicator (SLI)**: Metric used to track SLOs (e.g., "5xx error rate < 0.01%").
3. **Tools**:
   - **Configuration**: Store SLAs in infrastructure-as-code (e.g., Terraform, Kubernetes `CustomResourceDefinitions`).
   - **Example (Terraform)**:
     ```hcl
     resource "availability_sla" "web_api" {
       name          = "WebAPI_Global_SLA"
       target_uptime = 0.9995
       components   = [{ name = "api-gateway", type = "Kubernetes" }]
       compliance   = ["PCI_DSS_3.2.1"]
     }
     ```

#### **4.2. Monitoring and Alerting**
- **Critical Alerts**: Trigger when SLIs breach thresholds (e.g., Prometheus alerts for `error_rate > 0.01`).
- **Tools**:
  - **Prometheus + Grafana**: Visualize SLO compliance over time.
  - **Alertmanager**: Escalate alerts to Slack/PagerDuty.
  - **Example Alert Rule**:
    ```yaml
    - alert: SLO_Violation
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
      for: 15m
      labels:
        severity: critical
      annotations:
        summary: "SLO breach for {{ $labels.instance }} (5xx errors > 1%)"
    ```

#### **4.3. Redundancy Strategies**
| **Strategy**       | **Use Case**                          | **Implementation**                                                                 |
|--------------------|---------------------------------------|------------------------------------------------------------------------------------|
| **Active-Active**  | High availability (e.g., databases).  | Multi-region PostgreSQL with synchronous replication.                              |
| **Active-Standby** | Cost-effective HA (e.g., backup DBs). | Cloud RDS Multi-AZ deployment.                                                     |
| **N+X Redundancy** | Tolerate X failures in N components.   | Kubernetes `PodDisruptionBudget` with `minAvailable: 2` in a 3-node cluster.       |

#### **4.4. Degradation Rules**
Define thresholds for automated actions:
- **Example (Terraform + Kubernetes)**:
  ```hcl
  resource "kubernetes_horizontal_pod_autoscaler" "cpu_trigger" {
    metadata {
      name = "frontend-hpa"
    }
    spec {
      scale_target_ref {
        api_version = "apps/v1"
        kind        = "Deployment"
        name        = "frontend"
      }
      min_replicas = 2
      max_replicas = 10
      metrics {
        type = "Resource"
        resource {
          name = "cpu"
          target {
            type = "Utilization"
            average_utilization = 70 # Scale out if CPU > 70%
          }
        }
      }
    }
  }
  ```

#### **4.5. Compliance Mapping**
Link SLAs to regulations:
| **Regulation**       | **Relevant SLA Field**               | **Example**                                      |
|----------------------|--------------------------------------|--------------------------------------------------|
| **PCI DSS 3.2.1**    | `compliance_requirements`            | `"{standard: "PCI_DSS", section: "9.9"}`         |
| **HIPAA**            | `target_uptime` (99.999%)            | Healthcare APIs must meet 99.999% uptime.        |
| **SOC 2 Type II**    | `monitoring` (audit logs)             | Enable Prometheus for 100% uptime of audit trails. |

---

### **5. Query Examples**
#### **5.1. Querying SLA Compliance (PromQL)**
```promql
# Check if current 5xx error rate exceeds SLO threshold (1%)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
```

#### **5.2. Calculate MTBF**
```sql
-- SQL example for database uptime logs
SELECT
  DATE_TRUNC('day', event_time) AS day,
  COUNT(*) / NULLIF(SUM(duration_seconds), 0) AS daily_mtfb
FROM system_failures
GROUP BY day;
```

#### **5.3. Kubernetes SLO Check**
```bash
# Check if pods meet availability (e.g., 3/3 running)
kubectl get pods -n my-namespace --field-selector=status.phase=Running | wc -l
```

#### **5.4. Terraform Output for SLAs**
```bash
terraform output -json | jq '.availability_sla_web_api.target_uptime'
# Output: 0.9995
```

---

### **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Multi-Region Deployment](link)** | Deploy services across regions for global availability.               | High-latency tolerance or disaster recovery.     |
| **[Circuit Breaker](link)** | Automatically isolate failing services to prevent cascading failures.       | Microservices with external dependencies.        |
| **[Blue-Green Deployment](link)** | Zero-downtime updates by running two identical environments.               | Critical services requiring 99.99% uptime.       |
| **[Chaos Engineering](link)**  | Proactively test system resilience by injecting failures.                   | Validate MTTR and redundancy strategies.         |
| **[Configurable Quotas](link)** | Enforce limits on resource usage (e.g., CPU, I/O) to prevent degradation.  | Prevent noisy neighbors in shared environments. |

---

### **7. Best Practices**
1. **Start Conservatively**: Begin with achievable targets (e.g., 99.9% before aiming for 99.99%).
2. **Automate Recovery**: Use tools like Kubernetes `PodDisruptionBudgets` or AWS Auto Scaling.
3. **Document Failures**: Log incidents and MTTR improvements in a runbook (e.g., GitBook or Confluence).
4. **Review Quarterly**: Adjust SLAs based on usage patterns (e.g., seasonal traffic spikes).
5. **Communicate Transparently**: Notify users of planned maintenance (e.g., "SLA degraded to 99.9% during update").

---
### **8. Troubleshooting**
| **Issue**                     | **Root Cause**                          | **Solution**                                                                 |
|--------------------------------|-----------------------------------------|------------------------------------------------------------------------------|
| **SLA breaches without alerts** | Alert thresholds misconfigured.         | Verify Prometheus/Grafana alert rules with `kubectl logs -f` (for Kubernetes). |
| **High MTTR**                  | Manual recovery processes.              | Document runbooks; automate with Ansible/Terraform.                          |
| **Redundancy not activated**   | Failover triggers not met.              | Check health checks (e.g., `livenessProbe` in Kubernetes).                   |
| **False positives in alerts**  | Noisy metrics (e.g., spiky traffic).    | Use rolling windows (e.g., `rate(http_requests[5m])`) instead of instant values. |

---
### **9. Examples**
#### **Example 1: Database SLA**
```yaml
# availability_sla_yaml example
sla:
  name: "PrimaryDB_SLA"
  target_uptime: 99.999
  components:
    - name: "db-primary"
      type: "PostgreSQL"
  redundancy:
    strategy: "active-active"
    factor: 2
  monitoring:
    tool: "Prometheus"
    alerts: ["HighLatencyDBQuery", "ReplicationLag"]
  compliance:
    - standard: "PCI_DSS"
      section: "3.9"
```

#### **Example 2: Kubernetes Deployment**
```yaml
# deployment.yaml snippet with SLO-aware scaling
autoscaling:
  targetCPUUtilizationPercentage: 70
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---
### **10. References**
- **SRE Book (Google)**: [Site Reliability Engineering](https://sre.google/)
- **Prometheus Docs**: [Alerting](https://prometheus.io/docs/alerting/)
- **Kubernetes Best Practices**: [High Availability](https://kubernetes.io/docs/concepts/architecture/high-availability/)