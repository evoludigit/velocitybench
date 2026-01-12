---
# **[Pattern] Availability Monitoring – Reference Guide**

---

## **1. Overview**

The **Availability Monitoring** pattern ensures that critical systems, services, or resources are operational, responsive, and accessible to end-users or dependent systems. It proactively detects outages, performance degradations, or failures, triggering alerts or corrective actions. This pattern is foundational for **High Availability (HA)**, **Disaster Recovery (DR)**, and **SLA compliance**, particularly in distributed systems, cloud environments, or mission-critical applications.

Availability monitoring complements other patterns like **Health Checks**, **Circuit Breakers**, and **Resilience Testing** by providing a holistic view of system uptime. It typically involves:
- **Ping/Probe-based checks** (HTTP, TCP, ICMP).
- **Business-Logic Monitoring** (e.g., verifying API responses, database transactions).
- **Third-Party Dependency Checks** (e.g., external APIs, payment gateways).
- **Automated Alerting** (via email, Slack, PagerDuty) and **Auto-Remediation** (e.g., scaling, failover).

By defining clear **SLAs (Service Level Agreements)** and **SLOs (Service Level Objectives)**, teams can prioritize monitoring efforts and measure reliability. This guide covers implementation strategies, schema references, and practical examples.

---

## **2. Key Concepts & Schema Reference**

### **Core Components of Availability Monitoring**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example Tools/Libraries**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------|
| **Monitoring Agent**        | Runs checks (active/passive) on targets (hosts, services, APIs).                                                                                                                                               | Prometheus, New Relic, Datadog, Custom scripts   |
| **Check Type**              | Defines how availability is verified (e.g., HTTP `2xx` response, CPU < 90%).                                                                                                                                    | ICMP, HTTP, DNS, TCP, Command, Metric Threshold |
| **Thresholds**              | Defines acceptable ranges (e.g., "99.9% uptime," "RTT < 500ms"). Used for alerts.                                                                                                                             | `SLO` (e.g., "Error Budget = 0.1%")             |
| **Alerting Policy**         | Rules for triggering notifications (e.g., `failures > 3 in 5 mins`).                                                                                                                                              | Slack, Email, PagerDuty, Opsgenie                 |
| **Auto-Remediation**        | Automated actions (e.g., restart a pod, scale-up a service) based on failures.                                                                                                                                   | Kubernetes HPA, Auto-Scaling, Ansible Playbooks |
| **Incident Response**       | Roles (e.g., on-call SREs), escalation paths, and playbooks.                                                                                                                                                  | Jira, ServiceNow, Custom dashboards              |
| **Dashboarding**            | Visual representation of uptime, errors, and trends (e.g., uptime %, latency percentiles).                                                                                                                       | Grafana, Datadog, Amazon CloudWatch              |
| **SLA/SLO Tracking**        | Measures compliance against agreed-upon availability targets (e.g., "Uptime 99.95%").                                                                                                                              | Prometheus Alertmanager, custom scripts          |

---

### **Schema Reference: Availability Monitoring Configuration**
Below is a schema for defining monitoring rules (e.g., for a microservice):

```json
{
  "name": "Order-Service-Availability",
  "description": "Monitors the Order Service API and critical dependencies.",
  "sls": [
    {
      "name": "Order-API-Uptime",
      "target": 0.999,  // 99.9% uptime
      "errorBudget": 0.001,  // 0.1% allowed errors
      "checks": [
        {
          "type": "http",
          "url": "https://api.example.com/orders",
          "method": "GET",
          "statusCodes": [200, 201],
          "timeout": "5s",
          "interval": "30s",
          "threshold": {
            "failures": {
              "count": 3,
              "window": "5m"
            }
          }
        },
        {
          "type": "database",
          "target": "orders-db",
          "check": "SELECT 1 FROM latency WHERE status = 'active'",
          "maxLatency": "200ms",
          "interval": "1m"
        }
      ],
      "alerting": {
        "escalationPolicy": "on-call-rotation",
        "channels": ["slack", "email"],
        "severity": "critical",
        "remediation": {
          "action": "scale-out",
          "minReplicas": 3
        }
      }
    }
  ],
  "dependencies": [
    {
      "name": "Payment-Gateway",
      "check": {
        "type": "http",
        "url": "https://payment-api.example.com/validate",
        "expectedResponse": {"status": "approved"}
      },
      "critical": true
    }
  ]
}
```

---

## **3. Implementation Details**

### **3.1 Active vs. Passive Monitoring**
| **Type**       | **Definition**                                                                 | **Use Case**                                                     | **Example Tools**               |
|----------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------|----------------------------------|
| **Active**     | Proactively sends requests to check availability (e.g., synthetic transactions). | Cloud services, third-party APIs, APIs with no inherent heartbeat. | Pingdom, Synthetics in Datadog  |
| **Passive**    | Relies on logs/metrics from the system itself (e.g., application logs).        | Internal services, self-health-checking apps.                 | ELK Stack, Prometheus + Grafana |

**Best Practice**: Combine both for comprehensive coverage.

---

### **3.2 Check Types & Use Cases**
| **Check Type** | **Purpose**                                                                                     | **Implementation Notes**                                                                                     |
|----------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **ICMP Ping**  | Verify network connectivity to a host.                                                          | Useful for infrastructure (servers, VMs). Avoid for application-layer checks.                              |
| **HTTP/HTTPS** | Validate API endpoints, pages, or microservices.                                               | Test endpoints with `curl`, `Postman`, or tools like `k6`. Add headers/auth if needed.                     |
| **TCP**        | Check if a port is open (e.g., database, Redis).                                               | Use `telnet` or `nc` for simple checks; embed in scripts for monitoring.                                  |
| **DNS**        | Ensure domain resolution works (e.g., `example.com → 192.168.1.1`).                           | Critical for CDNs, load balancers, and multi-region deployments.                                         |
| **Command**    | Run custom scripts (e.g., database health, file checks).                                      | Example: `pg_isready -U postgres` for PostgreSQL.                                                          |
| **Metric**     | Monitor thresholds (e.g., CPU > 80%, memory leaks).                                           | Configure in Prometheus/Grafana with `alertmanager` rules.                                               |
| **Business Logic** | Simulate user flows (e.g., checkout process, payment success).                            | Use tools like `Locust` or `k6` to mimic real-world traffic.                                             |

---

### **3.3 SLA/SLO Definitions**
- **SLA (Service Level Agreement)**: Contractual guarantee (e.g., "99.95% uptime").
- **SLO (Service Level Objective)**: Internal target derived from SLA (e.g., "Error Budget = 0.05%").
- **Error Budget**: Percentage of allowed failures (e.g., 0.05% × 30 days = **7.2 hours** of allowed downtime).

**Calculation**:
```
Error Budget = 1 - (SLO / 100)
Allowed Failures = Error Budget × Availability Window (e.g., 30d)
```

**Example**:
For a **99.99% SLO (4 nines)** over 30 days:
```
Error Budget = 1 - 0.9999 = 0.0001 → 1.44 minutes of allowed downtime per month.
```

---

### **3.4 Alerting Strategies**
| **Strategy**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Threshold-Based**        | Trigger alerts when metrics exceed thresholds (e.g., `latency > 1s` for 5 mins).                                                                                                                           | Performance monitoring, resource limits.                                                          |
| **State-Based**            | Alert on specific states (e.g., "Service Unavailable" HTTP 503).                                                                                                                                         | API/service health.                                                                                  |
| **Anomaly Detection**      | Uses ML (e.g., Prometheus Alertmanager, Datadog) to detect unusual patterns.                                                                                                                               | Unpredictable workloads (e.g., IoT, batch jobs).                                                  |
| **Multi-Level Escalation** | Escalates alerts if unacknowledged (e.g., after 1 hour, page the on-call team).                                                                                                                              | Critical systems requiring rapid response.                                                         |
| **Incident Postmortem**    | Requires acknowledgment before re-escalating (e.g., Jira tickets).                                                                                                                                         | High-severity incidents to avoid alert fatigue.                                                    |

---

### **3.5 Auto-Remediation Actions**
| **Action**               | **When to Use**                                                                 | **Example Tools/Methods**                          |
|--------------------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| **Restart Pods**         | Containerized apps failing due to crashes (e.g., Kubernetes).                 | Kubernetes `livenessProbe`, `readinessProbe`       |
| **Scale-Up/-Down**        | Handle traffic spikes or resource exhaustion.                                   | AWS Auto Scaling, Kubernetes HPA                   |
| **Failover**             | Switchover to a standby instance (e.g., database replicas).                     | PostgreSQL Streaming Replication, HAProxy           |
| **Retry/Backoff**        | Temporary failures (e.g., third-party API timeouts).                           | Circuit breakers (Hystrix, Resilience4j)           |
| **Config Adjustments**   | Dynamic tuning (e.g., increase JVM heap).                                    | Envoy, Istio, or custom scripts                     |
| **Reimage/Rebuild**      | Persistent corruption (e.g., disk failure).                                   | Terraform, Ansible Playbooks                       |

**Caution**: Auto-remediation should be **idempotent** (safe to retry) and **auditable**.

---

## **4. Query Examples**

### **4.1 Prometheus Alert Rules**
Define alerts in `alert.rules` (e.g., for high latency):

```yaml
groups:
- name: availability-alerts
  rules:
  - alert: HighOrderServiceLatency
    expr: histogram_quantile(0.95, rate(order_api_latency[5m])) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Order API latency > 1s (instance {{ $labels.instance }})"
      description: "95th percentile latency is {{ $value }}ms"
```

### **4.2 Grafana Dashboard Queries**
**Uptime % (Prometheus)**:
```
sum(rate(up{job="order-service"}[5m])) by (service) / count(up{job="order-service"}) * 100
```
**HTTP Error Rate**:
```
sum(rate(http_requests_total{status=~"5.."}[5m])) by (route) /
 sum(rate(http_requests_total[5m])) by (route) * 100
```

### **4.3 Custom Script (Bash)**
Check a database connection:
```bash
#!/bin/bash
if ! mysqladmin ping -h db.example.com -u user -p"password" --silent; then
  echo "ERROR: Database unavailable"
  exit 1
fi
```

### **4.4 k6 Synthetic Monitoring**
Test API availability with `k6`:
```javascript
import http from 'k6/http';

export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95th percentile < 500ms
    checks: ['rate>0.95']            // 95% pass rate
  }
};

export default function () {
  const res = http.get('https://api.example.com/orders');
  return res.status === 200;
}
```

---

## **5. Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                          | **When to Use Together**                                                                                     |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **[Health Checks]**              | Exposes `/health` endpoints to monitor system status.                                                                                                               | Critical for auto-scaling, failover, and circuit breakers.                                                 |
| **[Circuit Breaker]**             | Prevents cascading failures by stopping requests to a failing service.                                                                                            | Combine with availability monitoring to isolate degraded dependencies.                                       |
| **[Resilience Testing]**          | Simulates failures (e.g., network partitions) to validate recovery.                                                                                                | Use before production deployment to stress-test availability monitoring.                                    |
| **[Chaos Engineering]**           | Deliberately injects failures (e.g., kill pods) to test resilience.                                                                                                | Validate auto-remediation and alerting workflows.                                                            |
| **[Distributed Tracing]**        | Tracks requests across services to identify bottlenecks.                                                                                                          | Correlate with availability monitoring to diagnose latency spikes.                                            |
| **[Canary Deployments]**          | Gradually rolls out changes to a subset of users.                                                                                                                 | Monitor availability of canary traffic separately to detect regressions early.                               |
| **[Multi-Region Deployments]**    | Deploys services across regions for HA.                                                                                                                         | Critical for global availability; monitor cross-region latency and failovers.                               |

---

## **6. Best Practices**

1. **Define Clear SLAs/SLOs**:
   - Align with business priorities (e.g., "Payment processing must be 99.999%").
   - Use **error budgets** to balance reliability vs. innovation.

2. **Monitor What Matters**:
   - Focus on **end-user impact** (e.g., "Can users checkout?" > "Is the cache warm?").
   - Avoid alert fatigue; prioritize critical paths.

3. **Combine Active + Passive Checks**:
   - Active checks verify **availability from the outside**.
   - Passive checks capture **internal failures** (e.g., logs, metrics).

4. **Automate Incident Response**:
   - Use **runbooks** (e.g., Ansible, Terraform) for repeatable remediation.
   - Integrate with **ticketing systems** (Jira, ServiceNow) for tracking.

5. **Test Monitoring Reliability**:
   - Simulate failures to ensure alerts fire (e.g., kill a node, throttle network).
   - Validate **alert threshold tuning** (e.g., adjust `failures > 3 in 5m`).

6. **Document Failures**:
   - Maintain a **postmortem database** to identify recurring issues.
   - Use **blameless retrospectives** to improve processes.

7. **Plan for Disasters**:
   - Define **disaster recovery SLAs** (e.g., "Restore in < 4 hours").
   - Test **chaos scenarios** (e.g., region outage).

8. **Tooling Stack**:
   - **Metrics**: Prometheus, Datadog, CloudWatch.
   - **Alerting**: Alertmanager, PagerDuty, Opsgenie.
   - **Incidents**: PagerDuty, Opsgenie, Slack.
   - **Dashboards**: Grafana, Datadog, Amazon Managed Grafana.

---

## **7. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                                                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Alert Fatigue**                     | Set **adaptive thresholds**, use **anomaly detection**, and **prioritize alerts** (severity-based).                                                      |
| **Over-Monitoring**                  | Focus on **business-critical paths**; avoid monitoring low-impact services excessively.                                                                     |
| **False Positives**                  | Use **multi-check validation** (e.g., combine HTTP + metric checks).                                                                                      |
| **Ignored Alerts**                   | Enforce **SLA ownership** (e.g., teams must acknowledge alerts).                                                                                               |
| **No Auto-Remediation**               | Define **idempotent actions** (e.g., restart pods, not delete configs).                                                                                       |
| **Region-Specific Failures**         | Deploy **multi-region monitoring** and test **cross-region failovers**.                                                                                     |
| **Metric Cardinality Explosion**     | Limit labels (e.g., `job`, `service`) to avoid Prometheus/Grafana overload.                                                                                 |
| **No Postmortem Culture**            | Mandate **retrospectives** after incidents to improve processes.                                                                                              |

---

## **8. Example Workflow**
1. **Define SLO**: "Order Service must have 99.9% uptime."
2. **Set Up Checks**:
   - HTTP check for `/orders` (every 30s).
   - Database latency check (every 1m).
3. **Configure Alerts**:
   - Alert if `failures > 3 in 5m` (severity: critical).
   - Escalate after 1 hour if unacknowledged.
4. **Auto-Remediation**:
   - Scale-up if CPU > 90% for 2 mins.
   - Restart pods if `livenessProbe` fails.
5. **Incident Handling**:
   - Slack alert → Jira ticket → On-call SRE investigates.
   - Runbook: Check logs → Restart pod → Verify fix.
6. **Review**:
   - Postmortem: "Root cause was a misconfigured load balancer."
   - Update runbook to include LB checks.

---
**End of Guide**