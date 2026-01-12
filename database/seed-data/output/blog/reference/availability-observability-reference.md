# **[Pattern] Availability Observability: Reference Guide**

---

## **Overview**
**Availability Observability** is a monitoring and maintenance practice that provides real-time visibility into system uptime, component failures, and degradation patterns. Unlike traditional monitoring—which often focuses on error rates or logs—this pattern emphasizes **proactive detection of unavailability** across infrastructure, applications, and services. By correlating telemetry data (e.g., uptime percentages, incident frequency, and anomaly thresholds), teams can predict outages, reduce mean time to resolution (MTTR), and align availability metrics with SLA commitments (e.g., 99.9% uptime).

Key use cases include **cloud service reliability, multi-region failover systems, and critical infrastructure health checks**. This guide outlines foundational concepts, data schemas, query examples, and related patterns to implement Availability Observability effectively.

---

## **Key Concepts**
| Concept               | Definition                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Availability Score** | % of time a system/resource is operational (e.g., 99.9% = 8.76 hours/year downtime). |
| **Anomaly Detection** | AI/ML-based flagging of unexpected downtime spikes (e.g., 5x higher failure rate). |
| **Dependency Mapping** | Visualizing how failures propagate through service dependencies.          |
| **Incident Window**   | Timeframe between a failure and its resolution (used to calculate MTTR).    |
| **SLA Violation Alert** | Triggered when uptime dips below agreed thresholds (e.g., 99.5% → alert).   |
| **Capacity Planning** | Proactive scaling to prevent availability degradation under load.          |

---

## **Schema Reference**
Below are core schemas for Availability Observability data models.

### **1. System Health Metrics**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `system_id`         | String     | Unique identifier for the service/component (e.g., `api-app-staging`).     |
| `availability_score`| Float      | Uptime percentage (0.0–1.0).                                                 |
| `timestamp`         | Timestamp  | When the metric was recorded.                                               |
| `incident_count`    | Integer    | Total failures in the observed window (e.g., last 7 days).                 |
| `last_failure_time` | Timestamp  | When the most recent outage occurred.                                       |
| `region`            | String     | Geographic deployment (e.g., `us-east-1`, `eu-west-2`).                      |

**Example Record:**
```json
{
  "system_id": "database-primary",
  "availability_score": 0.998,
  "timestamp": "2023-11-15T14:30:00Z",
  "incident_count": 2,
  "last_failure_time": "2023-11-14T09:15:00Z",
  "region": "ap-southeast-1"
}
```

---

### **2. Dependency Graph**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `provider`          | String     | Service/component name (e.g., `auth-service`).                               |
| `consumer`          | String     | Service dependent on `provider`.                                            |
| `dependency_type`   | Enum       | `http`, `database`, `kafka`, `load_balancer`.                               |
| `health_score`      | Float      | Combined availability score from both ends (0–1).                           |
| `failure_propagation`| Boolean    | `true` if `consumer` failure correlates with `provider` failure.           |

**Example Record:**
```json
{
  "provider": "payment-processor",
  "consumer": "checkout-service",
  "dependency_type": "http",
  "health_score": 0.95,
  "failure_propagation": true
}
```

---

### **3. SLA Compliance Events**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `sla_threshold`     | Float      | Target availability (e.g., 0.999 for 99.9%).                                |
| `violation_time`    | Timestamp  | When uptime fell below threshold.                                           |
| `duration_seconds`  | Integer    | Length of SLA breach.                                                       |
| `remediation_action`| String     | Resolved by (e.g., `rollback`, `auto-scaling`).                            |

**Example Record:**
```json
{
  "sla_threshold": 0.995,
  "violation_time": "2023-11-10T11:45:00Z",
  "duration_seconds": 3600,
  "remediation_action": "restarted-micro-service"
}
```

---

## **Query Examples**
### **1. Fetch Availability Scores (Last 7 Days)**
**Query (SQL-like pseudo-code):**
```sql
SELECT
  system_id,
  AVG(availability_score) AS avg_uptime,
  COUNT(incident_count) AS total_incidents
FROM system_health
WHERE timestamp > DATEADD(day, -7, NOW())
GROUP BY system_id
ORDER BY avg_uptime ASC;
```
**Expected Output:**
| `system_id`       | `avg_uptime` | `total_incidents` |
|-------------------|--------------|-------------------|
| `cache-node-3`    | 0.992        | 5                 |
| `api-gateway`     | 0.998        | 1                 |

---

### **2. Detect Cascading Failures**
**Query (GraphQL-like):**
```graphql
query DependencyFailures {
  dependencyGraph(
    where: { failure_propagation: true }
    limit: 10
  ) {
    provider
    consumer
    health_score
    last_failure_time
  }
}
```
**Expected Output:**
```json
[
  {
    "provider": "cache-service",
    "consumer": "user-auth",
    "health_score": 0.85,
    "last_failure_time": "2023-11-12T08:00:00Z"
  }
]
```

---

### **3. SLA Violation Trends**
**Query (InfluxDB-like):**
```sql
from(bucket: "availability_metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "sla_violations")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```
**Expected Output (Time Series):**
| Time               | `mean_violation_duration_s` |
|--------------------|----------------------------|
| 2023-11-08T00:00:00Z| 1200                       |
| 2023-11-09T00:00:00Z| 450                        |

---

## **Implementation Best Practices**
1. **Data Sources:**
   - **Infrastructure:** Cloud provider metrics (AWS CloudWatch, GCP Monitoring).
   - **Applications:** APM tools (Datadog, New Relic) for transaction-level uptime.
   - **Synthetic Monitoring:** Simulated user requests (e.g., Pingdom, UptimeRobot).

2. **Thresholds:**
   - Set SLA-based alerts (e.g., alert at 99.0% → investigate; alert at 98.5% → escalate).

3. **Visualization:**
   - Use dashboards to show:
     - Uptime trends over time.
     - Dependency graphs with failure propagation arrows.
     - SLA compliance heatmaps (green/yellow/red).

4. **Automation:**
   - **Auto-remediation:** Trigger rollbacks or scaling if `availability_score < 0.95`.
   - **Anomaly Detection:** Use ML (e.g., AWS Outliers) to flag unusual failure patterns.

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Error Budgeting**         | Allocates a % of failures to planned work (e.g., 0.1% budget for deploys). |
| **Chaos Engineering**       | Proactively tests failure scenarios to improve resilience.                  |
| **Distributed Tracing**     | Correlates latency/failure across microservices (e.g., Jaeger, OpenTelemetry). |
| **Infrastructure as Code (IaC)** | Ensures consistent deployments with built-in availability checks.      |
| **Multi-Region Failover**   | Automatically routes traffic if primary region fails (e.g., DNS-based).    |

---
**Further Reading:**
- [SRE Book: Reliability Engineering](https://sre.google/sre-book/)
- [AWS Well-Architected Availability Framework](https://aws.amazon.com/architecture/well-architected/)