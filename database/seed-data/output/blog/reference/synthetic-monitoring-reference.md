**[Pattern] Synthetic Monitoring & End-to-End Testing – Reference Guide**
*Version 1.0 | Last Updated: [Insert Date]*

---

### **1. Overview**
Synthetic monitoring emulates real-user behavior (e.g., login flows, checkout processes) from distributed vantage points (geographic locations, browsers, devices) to proactively detect infrastructure, application, or dependency failures. Unlike reactive alerting systems, synthetic monitoring executes predefined paths *continuously*, ensuring observable uptime and performance for critical user journeys. This pattern supports:
- **Proactive issue detection** (e.g., failed API calls, slow response times) before end users are impacted.
- **End-to-end validation** of application stacks (frontend, backend, third-party services).
- **SLA compliance** by measuring uptime and latency metrics against predefined thresholds.
- **Geographic coverage** via globally distributed probes (e.g., Azure Monitor, Synthetic Monitoring APIs).

Key use cases include:
- E-commerce (checkout flows, inventory checks).
- SaaS applications (authentication, data retrieval).
- Web/mobile APIs (rate limits, payload validation).

---

### **2. Schema Reference**
Define the **Synthetic Test Definition** schema for YAML/JSON configuration. Below are required fields and optional parameters:

| **Field**               | **Type**       | **Required** | **Description**                                                                                     | **Example Values**                     |
|-------------------------|----------------|--------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| `test_name`             | string         | ✅ Yes        | Unique identifier for the synthetic test (used for reporting).                                         | `ecommerce_checkout_flow`             |
| `location`              | array          | ✅ Yes*       | Geographic distribution of probes (e.g., `["US-West", "EU-North", "APAC-South"]`).                   | `["azure-US-2", "azure-GB-2"]`         |
| `browser_type`          | string         | ✅ Yes        | Rendering engine for browser-based tests (e.g., Chrome, Firefox).                                   | `"chrome"`                             |
| `script_type`           | enum           | ✅ Yes        | Script language for test automation: `cucumber`, `javascript`, `rest_api`.                         | `"cucumber"`                           |
| `frequency`             | string         | ✅ Yes        | Execution cadence (e.g., `PT5M` for every 5 minutes, `PT1H` hourly).                                | `"PT5M"`                               |
| `checks`                | array          | ✅ Yes        | Sequence of validation steps (see below).                                                          | see *Checks Schema* table              |
| `timeout`               | string         | ❌ No (default: `PT60S`) | Max duration per test step (ISO 8601 format).                                             | `"PT30S"`                              |
| `alerting`              | object         | ❌ No         | Thresholds for failure rates/latency (integrates with Azure Monitor/Third-party APIs).          | `{"failures": 0, "latency_ms": 2000}` |
| `dependencies`          | array          | ❌ No         | External services/APIs required (e.g., payment gateway, analytics).                                  | `["stripe.com", "example-analytics.com"]` |

---
#### **Check Schema** (nested under `checks`)
| **Field**       | **Type**       | **Description**                                                                                     | **Example**                     |
|----------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `name`         | string         | Human-readable step name (e.g., "Login to Dashboard").                                               | `"api_login"`                    |
| `type`         | enum           | Validation type: `http_request`, `javascript_hook`, `data_validation`.                             | `"http_request"`                |
| `target`       | string         | URL or script endpoint (e.g., `https://api.example.com/login`).                                    | `"https://api.example.com/v1/auth"` |
| `method`       | string         | HTTP method (GET, POST, etc.).                                                                    | `"POST"`                        |
| `payload`      | object         | Request body (JSON/YAML).                                                                          | `{"username": "user123", ...}`   |
| `assertions`   | array          | Expected responses (e.g., status code, headers, body validation).                                   | `{"status_code": 200}`          |

---
#### **Location Schema** (nested under `location`)
| **Field**       | **Type**       | **Description**                                                                                     | **Example**                     |
|----------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `provider`     | string         | Cloud provider (e.g., `azure`, `aws`).                                                               | `"azure"`                        |
| `region`       | string         | Geographic region (e.g., `US-West`).                                                               | `"azure-US-2"`                  |
| `weight`       | number         | Relative importance (1-100, sums to 100).                                                           | `30`                            |

---

### **3. Query Examples**
#### **A. Create a Synthetic Test (YAML)**
```yaml
test_name: "user_registration_flow"
location:
  - provider: azure
    region: azure-US-2
    weight: 50
  - provider: azure
    region: azure-EU-2
    weight: 30
browser_type: chrome
script_type: cucumber
frequency: PT5M
checks:
  - name: "Navigate to Sign-Up Page"
    type: http_request
    target: "https://example.com/signup"
    method: GET
    assertions:
      - status_code: 200
      - contains_body: "Welcome"
  - name: "Submit Registration Form"
    type: http_request
    target: "https://example.com/api/v1/register"
    method: POST
    payload:
      email: "test@example.com"
      password: "SecurePass123"
    assertions:
      - status_code: 201
      - response_time_ms: "<2000"
alerting:
  failures: 0
  latency_ms: 1500
```

#### **B. Trigger a One-Time Test (REST API)**
```bash
curl -X POST "https://management.azure.com/subscriptions/<sub_id>/providers/Microsoft.Insights/syntheticTestLocations?api-version=2022-04-01" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "location": "azure-US-2",
    "type": "syntheticTest",
    "apiVersion": "2022-04-01",
    "properties": {
      "testName": "one_time_ping",
      "script": "const response = await fetch('https://example.com'); return response.ok;",
      "frequency": "PT1H" // Overrides frequency for one-time runs
    }
  }'
```

#### **C. Filter Synthetic Test Metrics (KQL)**
```kql
SyntheticResults
| where TimeGenerated > ago(24h)
| where TestName == "ecommerce_checkout_flow"
| summarize
    avg(ResponseTimeMs) by bin(TimeGenerated, 1h),
    FailureCount = countif(ResponseTimeMs > 0 and isempty(ResponseTimeMs))
| order by TimeGenerated asc
```

---

### **4. Implementation Steps**
#### **Step 1: Define Test Scenarios**
- Map critical user journeys (e.g., login → dashboard → purchase).
- Prioritize high-impact paths (e.g., checkout success > feature flags).
- Use **user session replay tools** (e.g., Azure Application Insights) to identify bottlenecks.

#### **Step 2: Configure Probes**
```bash
az monitor synthetic-locations create
  --name "global-probes"
  --location azure-US-2
  --sku Standard
```
- **Recommended probe distribution**: At least 3 regions (e.g., `US`, `EU`, `APAC`) with weighted importance.
- **Browser/OS support**: Match target audience (e.g., 80% Chrome, 20% Firefox for e-commerce).

#### **Step 3: Write Scripts**
- **For APIs**: Use `fetch`/`axios` in JavaScript or REST clients (e.g., Postman for validation).
- **For UI**: Employ **Puppeteer** or **Playwright** scripts (convert to Cucumber/Gherkin for readability).
  Example Cucumber snippet:
  ```gherkin
  Feature: Checkout Flow
    Scenario: Purchase Item
      Given I navigate to "/cart"
      When I select item "Laptop"
      And I click "Checkout"
      Then I should see "Order Confirmation"
  ```

#### **Step 4: Set Alerting Thresholds**
- **Failure rate**: <1% for production-critical tests.
- **Latency**: 95th percentile response time < 2s (adjust per SLO).
- Integrate with **Azure Monitor Alerts** or **PagerDuty** for escalations.

#### **Step 5: Validate and Deploy**
- **Test in staging**: Simulate traffic spikes (e.g., 100 RPS) to validate scalability.
- **Canary deploy**: Gradually roll out to 1 region before global rollout.
- **Rollback plan**: Automate test deletion/pause via API during incidents.

---

### **5. Query Examples (Advanced)**
#### **A. Detect Anomalies in Latency**
```kql
SyntheticResults
| where TestName == "login_auth"
| summarize
    avg(ResponseTimeMs) by bin(TimeGenerated, 1h)
| extend is_anomaly = ResponseTimeMs > 1000
| where is_anomaly
| project TimeGenerated, avg_ResponseTimeMs = avg(ResponseTimeMs)
```

#### **B. Correlate with Infrastructure Metrics**
```kql
union withsource=type(SyntheticResults), source=type(AppServiceMetrics)
| where TimeGenerated > ago(1d)
| where SourceType == "Synthetic" or MetricName == "CPU Usage"
| summarize
    avg(ResponseTimeMs) by bin(TimeGenerated, 1m),
    avg_CPU = avg(CpuPercentage)
```

#### **C. Compare Test Results Across Regions**
```kql
SyntheticResults
| where TestName == "global_checkout"
| summarize
    avg(ResponseTimeMs) by Location, bin(TimeGenerated, 1h)
| order by TimeGenerated asc
```

---

### **6. Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Tests failing intermittently**    | Network latency spikes or API throttling.                                     | Increase `timeout` field; add retries in script.                            |
| **High failure rate in 1 region**  | Localized infrastructure outage (e.g., Azure region downtime).               | Verify probe status via `az monitor synthetic-locations show`.               |
| **False positives in assertions**  | Loose assertions (e.g., `status_code: 200` includes 4xx redirects).           | Use stricter checks (e.g., `status_code: 200 and contains_header: "Location"`). |
| **Scripts failing silently**       | Missing error handling in custom scripts.                                     | Add `try/catch` blocks; log errors to Azure Monitor.                       |

---

### **7. Related Patterns**
1. **[Infrastructure as Code (IaC) for Synthetics]**
   - Use **Azure Bicep/Terraform** to provision probes and tests declaratively.
   - Example: [Azure Bicep Module for Synthetic Tests](https://github.com/Azure/azure-quickstart-templates/tree/master/synthetic-tests).

2. **[Distributed Tracing for Synthetics]**
   - Correlate synthetic test failures with end-user traces using **W3C Trace Context**.
   - Integrate with **Azure Application Insights** for joint analysis.

3. **[Chaos Engineering for Synthetics]**
   - Inject failures (e.g., `curl -X POST https://example.com/api/force-failure`) to test recovery.
   - Automate with **Azure Chaos Studio**.

4. **[Canary Releases with Synthetics]**
   - Deploy tests alongside feature flags to validate new flows before full rollout.

5. **[Multi-Cloud Synthetic Testing]**
   - Extend probes to **AWS CloudWatch Synthetics** or **GCP Synthetic Monitoring** for hybrid environments.
   - Use **OpenTelemetry** for cross-cloud metrics.

---
### **8. Resources**
- **Azure Docs**: [Synthetic Monitoring Overview](https://docs.microsoft.com/en-us/azure/azure-monitor/app/synthetic-overview)
- **Cucumber Playwright**: [Selenium Alternative Guide](https://playwright.dev/docs/intro)
- **KQL Cheatsheet**: [Azure Monitor Query Language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/)