**[Pattern] Uptime Monitoring Patterns – Reference Guide**

---

### **1. Overview**
Uptime monitoring ensures systems, applications, or services remain available and operational as expected. This guide outlines common **uptime monitoring patterns**—structured approaches to proactively detect and respond to downtime. These patterns help define monitoring scope, frequency, alerts, and recovery workflows. Key use cases include:
- **Infrastructure uptime** (servers, databases, APIs)
- **Business service reliability** (web apps, SaaS platforms)
- **Third-party dependencies** (payment gateways, CDNs)
- **Multi-region failover validation**

Patterns range from **basic availability checks** to **detailed SLA-based monitoring**, enabling teams to align monitoring with risk tolerance and business impact.

---

### **2. Schema Reference**
| **Component**               | **Description**                                                                 | **Example Values**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Pattern Type**           | Classification (e.g., proactive, reactive, SLA-aligned)                       | `Proactive`, `SLA-Based`, `Multi-Region`                                           |
| **Monitoring Scope**       | What is being monitored (e.g., endpoint, service, dependency)                 | `HTTP Endpoint`, `Database Transaction`, `Third-Party API`                          |
| **Check Frequency**        | How often to verify uptime (e.g., 5s, 1m, 5m)                                 | `60s`, `300s (5m)`                                                                |
| **Alert Thresholds**       | Conditions to trigger alerts (e.g., latency > 1s, error rate > 5%)             | `{ "latency": 1000ms, "errors": 5% }`                                             |
| **Recovery Workflow**       | Steps to take when downtime occurs                                         | `Restart service`, `Notify incident team`, `Rollback failed deployment`           |
| **Data Sources**           | Where to collect uptime metrics (e.g., synthetic transactions, logs)         | `Pingdom`, `New Relic`, `AWS CloudWatch`, `Prometheus`                            |
| **Tools/Frameworks**       | Supported tools for implementation                                        | `UptimeRobot`, `Grafana`, `Datadog`, `Custom Scripts`                             |
| **SLA Tiers**              | Expected availability (e.g., 99.9%, 99.99%)                                   | `99.9%`, `99.99%`                                                                 |
| **Geographic Locations**   | Regions/cities for distributed checks                                       | `US-East, EU-West, APAC-Singapore`                                                 |

---

### **3. Implementation Patterns**

#### **A. Basic Availability Checks**
**Use Case:** Fast, low-overhead monitoring of core endpoints.
**Key Steps:**
1. **Ping Interval:** Send HTTP `HEAD` or `GET` requests at predefined intervals (e.g., every 60 seconds).
2. **Alert Triggers:**
   - Status code ≠ `2xx`.
   - Latency exceeds threshold (e.g., >1 second).
3. **Data Storage:** Log response times and failures in a time-series database (e.g., InfluxDB).
4. **Tools:** UptimeRobot, Pingdom, or custom `curl`-based scripts.

**Example Query (PromQL):**
```sql
sum(rate(http_request_duration_seconds_count{status=~"2.."}[1m])) by (service) > 0
```
**Recovery Action:** Notify on-call engineers via Slack/PagerDuty.

---

#### **B. SLA-Based Monitoring**
**Use Case:** Align monitoring with contractual availability guarantees (e.g., 99.9%).
**Key Steps:**
1. **Calculate Uptime %:**
   - Total uptime = `(Total minutes - Downtime minutes) / Total minutes * 100`.
   - Example: 30 days = 43,200 minutes → 42,268.8 uptime minutes for 99.9% SLA.
2. **Rolling Window:** Track uptime over sliding 30-day windows.
3. **Alerting:**
   - Alert if downtime exceeds threshold (e.g., >0.1% unavailability).
   - Example: `30 days * 0.001 = 0.3 hours downtime allowed`.

**Tools:** Datadog, New Relic, or custom scripts parsing logs.

**Example Alert Rule (Datadog):**
```json
{
  "query": "avg:avg{*}.as_count > 0",
  "threshold": 0.001,
  "eval_metrics": ["avg:avg{*}.as_count"]
}
```

---

#### **C. Multi-Region Failover Validation**
**Use Case:** Ensure global services failover correctly between regions.
**Key Steps:**
1. **Distributed Checks:** Run probes from multiple AWS/Azure/GCP regions.
2. **Failover Simulation:**
   - Force traffic to a secondary region (via DNS or load balancer).
   - Verify response times and success rates.
3. **Automated Rollback:** If primary region recovers, reroute traffic back.

**Example Workflow (Terraform + Lambda):**
```hcl
resource "aws_lambda_function" "failover_monitor" {
  function_name = "multi-region-failover"
  handler       = "monitor.handler"

  environment {
    variables = {
      REGIONS = "us-east-1,eu-west-1,ap-southeast-1"
      PRIMARY = "us-east-1"
    }
  }
}
```

---

#### **D. Dependency Uptime Tracking**
**Use Case:** Monitor third-party services critical to your infrastructure.
**Key Steps:**
1. **Bulk Checks:** Use tools like `requests` (Python) or `curl` to ping dependencies.
2. **Impact Mapping:** Link dependencies to business services (e.g., Stripe payments → e-commerce).
3. **Escalation:** Alert when dependencies degrade before your service does.

**Example Script (Python):**
```python
import requests

dependencies = {
    "stripe": "https://api.stripe.com/v1/charges",
    "aws_s3": "https://s3.amazonaws.com"
}

for name, url in dependencies.items():
    try:
        response = requests.head(url, timeout=5)
        if response.status_code != 200:
            print(f"⚠️ {name} failed: {response.status_code}")
    except requests.exceptions.RequestException:
        print(f"❌ {name} unavailable")
```

---

#### **E. Synthetic Transactions**
**Use Case:** Simulate end-user workflows to catch UI/layout issues.
**Key Steps:**
1. **Browser Automation:** Use Selenium or Puppeteer to mimic user actions.
2. **Transaction Steps:**
   - Log in → Navigate to checkout → Place order.
3. **Alerts:** Fail if any step times out or fails.

**Example (Puppeteer):**
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com/checkout');
  await page.waitForSelector('#submit-button');
  const success = await page.evaluate(() => document.querySelector('#submit-button').click());
  await browser.close();
  console.log(success ? '✅ Transaction passed' : '❌ Transaction failed');
})();
```

---

### **4. Query Examples**
#### **Prometheus Query: Uptime % Over Time**
```sql
(1 - (count_over_time(http_request_duration_seconds_count{status=~"5.."}[1h]) by (service) / count_over_time(http_request_duration_seconds_count[1h]) by (service))) * 100
```

#### **Grafana Dashboard Alert: Latency Spikes**
```
avg(http_request_duration_seconds{status=~"2.."}) > 500ms for 3 consecutive checks
```

#### **AWS CloudWatch Metric Filter: 5xx Errors**
```
SELECT count(*) FROM "5xx-errors" WHERE timestamp > ago(5m)
```

---

### **5. Related Patterns**
| **Pattern**                  | **Description**                                                                 | **When to Use**                                                                 |
|------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Canary Releases**         | Gradually roll out changes to a subset of users to catch failures early.      | New feature deployments, A/B testing.                                           |
| **Chaos Engineering**       | Intentionally induce failures to test resilience.                               | Critical systems, disaster recovery testing.                                   |
| **Autoscaling Policies**    | Dynamically adjust resources based on load.                                    | Variable-traffic applications (e.g., e-commerce during sales).                 |
| **Distributed Tracing**     | Track requests across microservices for latency analysis.                     | Complex architectures with multiple services.                                 |
| **Incident Response Playbooks** | Standardized steps for addressing outages.                                  | Post-monitoring alerting to resolve issues.                                   |

---

### **6. Best Practices**
1. **Define SLAs Early:** Align monitoring with business needs (e.g., 99.9% for core services).
2. **Avoid Alert Fatigue:** Use severity levels (e.g., Critical > Warning > Info).
3. **Test Alerts:** Validate alerts in staging before production.
4. **Document Recovery Steps:** Keep runbooks updated for common failures.
5. **Use Synthetic + Real User Monitoring (RUM):** Combine automated checks with actual user data.
6. **Monitor Dependencies:** Track third-party uptime to forecast impact.

---
**References:**
- [Prometheus Documentation](https://prometheus.io/docs/prometheus/latest/querying/)
- [Datadog Uptime Monitoring](https://docs.datadoghq.com/monitor_uptime/)
- [SRE Book – Uptime SLIs](https://sre.google/sre-book/monitoring-distributed-systems/)