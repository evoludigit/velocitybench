# **[Pattern] Availability Testing: Reference Guide**

---

## **Overview**
**Availability Testing** is a reliability testing pattern designed to assess how well a system maintains continuous operational readiness under expected and simulated peak loads. This pattern evaluates a system’s ability to remain accessible (with minimal downtime or performance degradation) over time, ensuring it meets **Service Level Objectives (SLOs)** for uptime (e.g., 99.9% uptime). Common use cases include:
- Validating cloud/hosting provider uptime guarantees.
- Simulating traffic surges (e.g., seasonal spikes, DDoS attacks).
- Proactively identifying single points of failure.
- Ensuring compliance with contractual SLAs (e.g., uptime clauses).

Availability testing differs from **load testing** (which focuses on performance under heavy loads) or **stress testing** (which pushes systems to breaking points). Instead, it emphasizes **durability** and **resilience** over sustained periods (from hours to months) while maintaining predefined availability thresholds.

---

## **Implementation Details**
### **Key Concepts**
| Term                     | Definition                                                                                     | Example                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Availability Window**  | The fixed timeframe (e.g., 30 days) during which uptime is measured.                           | "99.9% availability over 90 days."                                                         |
| **Mean Time Between Failures (MTBF)** | Average time between failures; used to calculate uptime probability.                          | MTBF = 2,000 hours → ~99.95% uptime (assuming MTTR = 30 mins).                             |
| **Mean Time To Recovery (MTTR)** | Time taken to restore service after a failure.                                                 | Automated failover reduces MTTR from 120 mins → 5 mins.                                   |
| **Uptime Threshold**     | Minimum acceptable uptime percentage (e.g., 99.99% for critical systems).                      | Fail the test if uptime < 99.8% during the window.                                         |
| **Simulated Failures**   | Deliberately induced disruptions (e.g., node failures, network partitions) to test recovery. | Injecting a database outage to verify backup failover.                                     |
| **Monitoring Granularity** | Frequency of health checks (e.g., every 5 minutes).                                          | API ping checks every 10 seconds during load.                                              |
| **Dependency Testing**   | Validating third-party service resilience (e.g., payment processors, CDNs).                   | Testing payment gateway availability during peak hours.                                   |
| **Concurrent Users**     | Number of simulated users generating requests simultaneously.                              | 10,000 concurrent users for an e-commerce site.                                             |
| **Geographic Testing**   | Assessing availability across multiple regions/edge locations.                                | Testing failover from AWS EU (Frankfurt) to AWS US (Virginia).                             |

---

### **Schema Reference**
Below is a reference schema for defining availability tests in a declarative format (e.g., YAML/JSON).

| Field                | Type       | Description                                                                                     | Required | Example Values                                                                 |
|----------------------|------------|-------------------------------------------------------------------------------------------------|----------|---------------------------------------------------------------------------------|
| `test_id`            | String     | Unique identifier for the test.                                                                | Yes       | `"availability_sla_test_2024"`                                                 |
| `name`               | String     | Human-readable test name.                                                                      | Yes       | `"Q3 2024 Regional Availability Test"`                                        |
| `window_start`       | ISO8601    | Start datetime of the availability window.                                                       | Yes       | `"2024-09-01T00:00:00Z"`                                                      |
| `window_duration`    | Duration   | Duration of the measurement window (e.g., "P90D" for 90 days).                                 | Yes       | `"P30D"`                                                                       |
| `target_availability`| Float      | Uptime percentage threshold (e.g., 0.9999).                                                    | Yes       | `0.999` (99.9%)                                                                 |
| `endpoints`          | Array      | List of monitored endpoints (e.g., APIs, webhooks).                                           | Yes       | `[{"url": "https://api.example.com/health", "method": "GET", "critical": true}]`|
| `check_interval`     | Duration   | Frequency of health checks (e.g., "PT5S" for 5 seconds).                                       | No        | `"PT30S"` (default: `"PT1M"`)                                                 |
| `simulated_failures` | Array      | List of failures to inject during testing.                                                     | No        | `[{"type": "node_failure", "target": "db-primary", "duration": "PT10M"}]`       |
| `dependencies`       | Object     | Third-party services to monitor (e.g., payment gateways).                                       | No        | `{"stripe": {"endpoint": "https://api.stripe.com/v1/ping"}}`                    |
| `regions`            | Array      | Geographic locations for distributed testing.                                                   | No        | `["us-west-2", "eu-central-1", "ap-southeast-1"]`                           |
| `alert_thresholds`   | Object     | Notifications triggered at specific uptime breaches.                                           | No        | `{"warning": 0.995, "critical": 0.99}`                                       |
| `retries`            | Integer    | Max retries per failed check (e.g., 3).                                                         | No        | `3`                                                                            |
| `timeout`            | Duration   | Max time to wait for a response (e.g., "PT2S").                                                 | No        | `"PT5S"`                                                                       |

---

## **Query Examples**
Availability tests can be executed via CLI, API, or orchestration tools (e.g., Terraform, Kubernetes). Below are examples.

---

### **1. CLI Example (Hypothetical `availability-test` Tool)**
```bash
# Run a 30-day availability test with simulated node failures
availability-test run \
  --test-id availability_sla_test_2024 \
  --window-duration P30D \
  --target-availability 0.999 \
  --endpoints '["https://api.example.com/health", "https://cdn.example.com/static"]' \
  --simulated-failures '[
    {"type": "node_failure", "target": "db-primary", "duration": "PT30M"},
    {"type": "network_partition", "duration": "PT15M"}
  ]' \
  --regions us-west-2 eu-central-1 \
  --check-interval PT1M
```

---
### **2. API Example (REST)**
**Endpoint:** `POST /v1/tests/availability`
**Request Body (JSON):**
```json
{
  "test_id": "black-friday-2024",
  "name": "Black Friday Load + Availability Test",
  "window_start": "2024-11-20T00:00:00Z",
  "window_duration": "P3D",
  "target_availability": 0.9995,
  "endpoints": [
    {
      "url": "https://checkout.example.com/pay",
      "method": "POST",
      "critical": true
    }
  ],
  "simulated_failures": [
    {
      "type": "dDos",
      "duration": "PT1H",
      "intensity": "high"
    }
  ],
  "dependencies": {
    "stripe": {
      "endpoint": "https://api.stripe.com/v1/events",
      "expected_status": 200
    }
  }
}
```
**Response (Success):**
```json
{
  "status": "queued",
  "test_id": "black-friday-2024",
  "start_time": "2024-11-20T00:00:00Z",
  "uptime": 0.9998,
  "failures": [
    {"endpoint": "https://checkout.example.com/pay", "reason": "timeout", "duration": "PT2M"}
  ]
}
```

---
### **3. Kubernetes Example (Custom Resource)**
```yaml
# File: availability-test.yaml
apiVersion: reliability.example.com/v1alpha1
kind: AvailabilityTest
metadata:
  name: monthly-sla-check
spec:
  testId: monthly-sla-check-jan2025
  windowDuration: "P30D"
  targetAvailability: 0.999
  endpoints:
    - url: http://my-service:8080/health
      checkInterval: "PT1M"
      retries: 3
  simulatedFailures:
    - nodeSelector: db-primary
      duration: "PT30M"
      probability: 0.1  # 10% chance of failure
  regions:
    - us-east-1
    - ap-northeast-1
---
```
Apply with:
```bash
kubectl apply -f availability-test.yaml
```

---

## **Querying Results**
Use the following queries to analyze test results (e.g., in Prometheus/Grafana or a custom dashboard).

---
### **Prometheus Query (Uptime Over Time)**
```promql
# Uptime percentage for an endpoint (1 - (failures / total checks))
1 - (
  sum(rate(api_requests_total{endpoint="health", status=~"5.."}[5m]))
  /
  sum(rate(api_requests_total{endpoint="health"}[5m]))
)
by (endpoint)
```
**Visualization:** Line chart showing uptime % over the test window.

---
### **SQL-like Query (Hypothetical Database)**
```sql
SELECT
  endpoint,
  DATE_TRUNC('hour', timestamp) AS hour,
  COUNT(*) AS check_count,
  SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) AS failure_count,
  1 - (failure_count::float / NULLIF(check_count, 0)) AS uptime_pct
FROM availability_checks
WHERE test_id = 'availability_sla_test_2024'
  AND timestamp BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY endpoint, hour
ORDER BY hour;
```

---

## **Related Patterns**
| Pattern                          | Description                                                                                     | When to Use                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Load Testing]**                | Simulates user traffic to measure performance under load.                                      | Before availability testing to ensure performance doesn’t degrade uptime.                       |
| **[Chaos Engineering]**           | Deliberately breaks systems to test resilience.                                                 | After availability testing to validate recovery mechanisms.                                     |
| **[Stress Testing]**              | Pushes systems to failure to measure breaking points.                                           | Rarely; only if availability testing reveals edge cases.                                         |
| **[Canary Testing]**              | Gradually rolls out updates to a subset of users.                                               | To test availability during feature rollouts.                                                   |
| **[Dependency Tracking]**         | Maps system dependencies (e.g., databases, third-party APIs).                                   | To identify single points of failure in availability tests.                                      |
| **[Auto-Remediation]**             | Automatically fixes issues (e.g., scaling, failover).                                          | To reduce MTTR in availability-critical systems.                                                 |

---
## **Best Practices**
1. **Align with SLAs**: Use the same uptime thresholds as your service-level agreements.
2. **Start with Dependencies**: Test third-party services (e.g., payment providers) first.
3. **Distributed Testing**: Run checks from multiple geographic locations to simulate global outages.
4. **Inject Realistic Failures**: Simulate failures that could occur in production (e.g., regional outages).
5. **Monitor Post-Test**: Use alerts to detect regressions after availability tests.
6. **Document Failures**: Log root causes of failures to improve reliability (e.g., "Database replica lag caused 30s downtime").
7. **Automate Remediation**: Integrate with auto-scaling or failover systems to reduce MTTR.
8. **Test Edge Cases**: Include maintenance windows, peak hours, and holidays in your test window.

---
## **Troubleshooting**
| Issue                          | Cause                                      | Solution                                                                                     |
|--------------------------------|--------------------------------------------|---------------------------------------------------------------------------------------------|
| **False Positives**            | Flaky checks (e.g., transient network errors). | Increase retries or use circuit breakers.                                                   |
| **High MTTR**                  | Manual intervention required.              | Automate failover/remediation (e.g., Kubernetes HPA, cloud auto-scaling).                    |
| **Dependency Failures**        | Third-party outages.                       | Test with mock dependencies or include them in SLOs.                                         |
| **Insufficient Check Frequency** | Missed failures due to long intervals.    | Reduce `check_interval` to detect issues faster.                                             |
| **Regional Unavailability**    | Localized outages (e.g., cloud provider region). | Run tests from multiple regions or use multi-region deployments.                           |

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                                     | Link                                                                          |
|----------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Locust**                 | Load testing with availability metrics.                                                   | [https://locust.io/](https://locust.io/)                                      |
| **k6**                     | Scriptable load/availability testing.                                                      | [https://k6.io/](https://k6.io/)                                              |
| **Chaos Mesh**             | Chaos engineering for availability testing.                                                | [https://chaos-mesh.org/](https://chaos-mesh.org/)                            |
| **Prometheus + Alertmanager** | Monitoring and alerting on uptime.                                                        | [https://prometheus.io/](https://prometheus.io/)                              |
| **SLO Dashboards**         | Visualizing availability metrics (e.g., Google Cloud’s SLOs).                            | [https://cloud.google.com/slo](https://cloud.google.com/slo)                   |
| **Terraform**              | Orchestrating availability tests across cloud providers.                                    | [https://www.terraform.io/](https://www.terraform.io/)                        |
| **Grafana**                | Custom dashboards for availability trends.                                                 | [https://grafana.com/](https://grafana.com/)                                  |

---
## **Example Workflow**
1. **Define Test**:
   - Set `target_availability = 0.9995` for a 30-day window.
   - Include endpoints: `/health`, `/api/v1/payment`, and `/static/assets`.
   - Simulate a 30-minute regional outage.

2. **Execute**:
   - Run test via CLI/API during off-peak hours to avoid interference.

3. **Monitor**:
   - Use Prometheus to track uptime in real-time.
   - Set alerts for `uptime < 0.995`.

4. **Analyze**:
   - If uptime = 0.998, investigate the 0.15% downtime (e.g., database maintenance).

5. **Remediate**:
   - Adjust failover policies or scale out during peak hours.

6. **Document**:
   - Update runbooks with findings (e.g., "Increase DB read replicas to reduce MTTR").