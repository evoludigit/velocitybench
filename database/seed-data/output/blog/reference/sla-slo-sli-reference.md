---
# **[Pattern] Service-Level Agreement (SLA), Service-Level Objective (SLO), and Service Level Indicator (SLI) Reference Guide**

## **Overview**
Service-Level Agreements (SLAs), Service-Level Objectives (SLOs), and Service-Level Indicators (SLIs) form the foundation of modern **reliability engineering**, enabling teams to quantify, track, and improve system performance while balancing availability, latency, and cost. This pattern defines a structured approach to:
- **SLIs**: Quantifiable metrics that track system behavior (e.g., error rates, response times).
- **SLOs**: Target thresholds for SLIs (e.g., "99.9% availability"), aligned with business needs.
- **SLAs**: High-level commitments to stakeholders (e.g., "We guarantee 99.95% uptime for Critical Service A").

By decoupling **measurable SLIs** from **commitment-driven SLOs**, teams can iteratively adapt to operational realities while maintaining transparency with customers. This guide covers core concepts, implementation best practices, and tooling considerations.

---

## **Key Concepts & Definitions**

| **Term**       | **Definition**                                                                 | **Key Characteristics**                                                                 |
|---------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **SLI**       | A measurable indicator of service behavior (e.g., request success rate, latency percentiles). | - **Objective**: Focuses on *how* the service performs. <br> - **Granular**: Often decomposed by region, service tier, or traffic type. <br> - **Example**: `p99 latency < 500ms for API calls`. |
| **SLO**       | A target threshold for an SLI, expressed as a percentage or absolute goal (e.g., "99.95% request success rate"). | - **Subjective**: Represents a *commitment* (e.g., budgeted for errors). <br> - **Time-bound**: Often tied to a rolling window (e.g., 30-day SLO). <br> - **Derived from SLIs**: e.g., `SLO = "Error Budget ≤ 0.05% per month"`. |
| **SLA**       | A contract between a provider and consumer, stating guarantees for SLIs/SLOs (e.g., "We refund 10% if SLOs are breached"). | - **Legal/Business**: Defines penalties, compensation, or service tiers. <br> - **Aggregated**: May combine multiple SLOs (e.g., "99.9% *and* 95% latency targets"). <br> - **Example**: *"Our SLA for Database X guarantees 99.99% uptime for Production workloads."* |
| **Error Budget** | The "slack" in an SLO (e.g., if SLO = 99.95%, error budget = 0.05%). Teams can spend this budget during incidents before alerting stakeholders. | - **Dynamic**: Resets over the SLO window (e.g., monthly). <br> - **Trade-off**: Higher SLOs = stricter reliability; lower SLOs = flexibility. <br> - **Calculation**: `Error Budget = 100% - SLO%`. |
| **Burn Rate** | The rate at which an error budget is consumed (e.g., "We’re burning 0.01% of our budget daily"). | - **Monitoring**: Helps teams avoid SLO breaches proactively. <br> - **Alerting**: Trigger warnings when burn rate approaches the error budget. |

---

## **Implementation Schema Reference**

### **1. SLI Schema**
Define SLIs with:
- **Name**: Human-readable identifier (e.g., `api_success_rate`).
- **Definition**: Clear description of the metric (e.g., "Percentage of requests with HTTP 2xx/3xx responses").
- **Measurement Method**: How to compute (e.g., `count_of_successful_requests / total_requests`).
- **Data Source**: Logging/observability tool (e.g., Prometheus, Datadog).
- **Dimensions**: Breakdowns (e.g., `region`, `service_version`, `user_type`).
- **Unit**: Time window (e.g., per minute, per day).

| **Field**          | **Type**       | **Example**                          | **Notes**                                  |
|--------------------|----------------|--------------------------------------|--------------------------------------------|
| `sli_name`         | String         | `api_latency_p99`                    | Unique identifier.                        |
| `description`      | String         | "99th percentile latency for API X." | Must be actionable.                       |
| `calculation`      | Formula        | `histogram_quantile(0.99, ...)`      | Use tool-specific queries.                 |
| `data_source`      | String         | `prometheus:job=api_service`         | Link to observability pipeline.            |
| `dimensions`       | Array[Object]  | `[{name: "region", value: "us-west"}]` | Filter for granular analysis.              |
| `window`           | Duration       | `PT1M` (1 minute)                    | Typically aligned with SLO windows.       |
| `excluded_traffic` | Array[String]  | `[ "health_checks", "internal_api" ]` | Filter out noise (e.g., monitoring traffic). |

---

### **2. SLO Schema**
Define SLOs by referencing SLIs and setting targets:

| **Field**          | **Type**       | **Example**                          | **Notes**                                  |
|--------------------|----------------|--------------------------------------|--------------------------------------------|
| `slo_name`         | String         | `api_availability_slo`               | Must match SLI’s context.                  |
| `sli_reference`    | Object         | `{name: "api_success_rate", window: "PT1M"}` | Links to SLI schema.                     |
| `target`           | Float (0–100)  | `99.95`                              | Percentage or absolute value (e.g., `>95%`). |
| `window`           | Duration       | `P30D` (30 days)                     | Rolling window for error budget tracking.  |
| `error_budget`     | Float          | `0.05` (derived from `100 - target`) | Auto-calculated.                          |
| `owner`            | String         | `team_apis@company.com`              | Responsible team for maintaining the SLO. |
| `notes`            | String         | `"Includes outages during maintenance windows."` | Context for SLO exceptions.               |

---

### **3. SLA Schema**
Translate SLOs into stakeholder commitments:

| **Field**          | **Type**       | **Example**                          | **Notes**                                  |
|--------------------|----------------|--------------------------------------|--------------------------------------------|
| `sla_name`         | String         | `production_sla_db_y`               | Aligns with business units.                |
| `slo_references`   | Array[Object]  | `[{slo: "api_availability_slo", weight: 0.7}]` | Aggregate multiple SLOs (weighted if needed). |
| `guarantee`        | String         | `"99.9% uptime for Critical Workloads"` | Human-readable promise.                    |
| `penalties`        | Object         | `{breach_threshold: 0.01%, refund: "10%"}` | Defines consequences for SLO violations.   |
| `exclusions`       | Array[String]  | `[ "scheduled_downs", "natural_disasters" ]` | Events that don’t trigger penalties.      |
| `stakeholder`      | String         | `"customer_support@company.com"`     | Escalation contact.                       |

---

## **Query Examples**
### **1. Calculating an SLI (Prometheus)**
```promql
# Success rate SLI (1-minute window)
sum(rate(http_requests_total{status=~"^2..|^3.."}[1m])) by (service)
  /
sum(rate(http_requests_total[1m])) by (service)
```

**Output**:
```plaintext
service=api_v1 0.9993
service=auth_v1 0.9987
```

### **2. Monitoring SLO Burn Rate (Grafana Dashboard)**
```sql
-- Daily error budget burn rate for `api_success_rate` SLO (99.95% target)
SELECT
  DATE_TRUNC('day', timestamp) AS day,
  SUM(error_count) / SUM(total_requests) AS daily_error_rate,
  (SUM(error_count) / SUM(total_requests) - 0.0005) * 100 AS budget_burn_percentage
FROM metrics
WHERE sli = 'api_success_rate'
GROUP BY day
ORDER BY day DESC
LIMIT 30;
```

**Alert Condition**:
```plaintext
IF budget_burn_percentage > 90% THEN "Imminent SLO breach!"
```

### **3. Checking Error Budget (Custom Script)**
```python
# Python example to track error budget consumption
slo_target = 0.9995
error_budget = 1 - slo_target
current_errors = get_metric("api_errors_30d")
total_requests = get_metric("api_requests_30d")
burn_rate = (current_errors / total_requests) / error_budget

if burn_rate > 1.0:
    print(f"ERROR: SLO breached! Burn rate = {burn_rate:.2f}")
```

---

## **Best Practices & Anti-Patterns**

### **✅ Best Practices**
1. **Start Broad, Refine Narrowly**
   - Begin with **high-level SLIs** (e.g., "error rate") before deep-diving into latency percentiles.
   - Use **blameless postmortems** to adjust SLOs after incidents.

2. **Align SLOs with Business Impact**
   - Example: A `payment_processing` service might have a stricter SLO (99.99%) than a `marketing_analytics` service (99.5%).
   - Avoid **over-optimizing for vanity metrics** (e.g., p50 latency instead of p99).

3. **Communicate Transparently**
   - Publish **SLO dashboards** for stakeholders (e.g., "We’re at 99.8% availability, burning 0.15% of our budget").
   - Use **error budget** to justify trade-offs (e.g., "We’re spending 0.05% of our budget on this incident").

4. **Design for Change**
   - **Modular SLIs**: Update SLIs independently (e.g., swapping a Prometheus query).
   - **Versioned SLOs**: Tag SLOs with deployments (e.g., `v1.0.0`) to track historical targets.

5. **Handle Edge Cases**
   - **Maintenance Windows**: Exclude planned downtime from SLO calculations.
   - **Traffic Spikes**: Use **sliding windows** (e.g., 1-hour vs. 1-day) to avoid false positives.

### **❌ Anti-Patterns**
| **Anti-Pattern**               | **Why It’s Bad**                                                                 | **Fix**                                  |
|---------------------------------|-----------------------------------------------------------------------------------|------------------------------------------|
| **Static SLIs**                 | Metrics don’t adapt to traffic patterns or business needs.                         | Use **dynamic thresholds** (e.g., SLOs tied to traffic volume). |
| **SLOs Without Error Budgets**   | Teams lack clarity on trade-off flexibility.                                       | Always define **error budgets** upfront.  |
| **SLOs Based on Unreliable Data** | Noisy or excluded metrics (e.g., counting health checks as "successes").        | **Audit data sources** regularly.        |
| **Overlapping SLOs**            | Conflicting commitments (e.g., "99.9% uptime" *and* "0ms latency") are impossible. | **Prioritize** critical SLOs.            |
| **Silos Between Teams**         | DevOps and Product teams misaligned on reliability goals.                          | **Collaborate** early (e.g., joint SLO reviews). |

---

## **Tooling & Integration**

| **Category**          | **Tools**                                  | **Use Case**                                                                 |
|-----------------------|--------------------------------------------|------------------------------------------------------------------------------|
| **Observability**     | Prometheus, Datadog, Grafana, OpenTelemetry | Query SLIs and visualize burn rates.                                        |
| **SLO Management**    | ErrorBudgets (Google Cloud), SLO Dashboards | Track error budgets and alert on breaches.                                   |
| **Alerting**          | VictoriaMetrics,PagerDuty,Opsgenie       | Trigger alerts when burn rate exceeds 80% of error budget.                    |
| **Incident Management** | Jira, Linear, PagerDuty                   | Link incidents to SLO burn and postmortems.                                   |
| **Documentation**     | Confluence, Notion, Markdown               | Store SLIs/SLOs/SLAs in a searchable repo with owner contact info.             |

**Example Workflow**:
1. **Query SLI** (Prometheus) → Compute success rate.
2. **Calculate Burn Rate** (Grafana dashboard) → Compare to error budget.
3. **Alert on Threshold** (PagerDuty) → Escalate if >90% consumed.
4. **Post-Incident Review** → Update SLOs based on findings.

---

## **Related Patterns**
1. **[Chaos Engineering](https://chaosengineering.io/)**
   - *How to*: Use experiments (e.g., chaos monkey) to validate SLO resilience.
   - *Connection*: Chaos tests should **never** exceed error budgets.

2. **[Circuit Breaker Pattern](https://microservices.io/patterns/reliability/circuit-breaker.html)**
   - *How to*: Implement retry/logic to fail gracefully when SLIs degrade.
   - *Connection*: Circuit breakers help **manage error budgets** during outages.

3. **[Blame-Free Postmortems](https://www.atlassian.com/incident-management/guide/postmortem)**
   - *How to*: Analyze incidents to adjust SLIs/SLOs without punishment.
   - *Connection*: Postmortems **justify SLO revisions** (e.g., "We lowered the SLO by 0.1% after 3 outages").

4. **[Canary Analysis](https://www.brad-smith.me/canary-analysis)**
   - *How to*: Gradually roll out changes while monitoring SLIs.
   - *Connection*: Canary deployments **protect error budgets** during transitions.

5. **[Service Decomposition](https://martinfowler.com/eaaCatalog/serviceDecomposition.html)**
   - *How to*: Split monoliths into independent services with differentiated SLIs.
   - *Connection*: Enables **tailored SLOs** per service (e.g., "Legacy system: 99.5%; New API: 99.99%").

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **SLO Breach Unexpectedly**        | Check for data corruption or excluded traffic in SLI definition.              | Validate SLI queries and dimensions.                                         |
| **Error Budget Burn Rate Spikes**   | Sudden traffic increase or undetected failures.                              | Implement **auto-scaling** or **chaos tests** to preemptively stress-test. |
| **Stakeholder Pushback on SLOs**    | SLOs seem "too aggressive" or "too lenient".                                   | Conduct **workshop** to align on business impact and error budget trade-offs. |
| **SLI Drift Over Time**            | Metric definitions change without updating SLOs.                               | **Version SLIs** and document changes in the knowledge base.                |
| **Tooling Doesn’t Support SLOs**   | Observability stack lacks error budget features.                             | Use **open-source tools** (e.g., Prometheus + Grafana) or vendor extensions. |

---

## **Further Reading**
- [SRE Book: SLIs, SLOs, and Error Budgets](https://sre.google/sre-book/table-of-contents/#sre_book_slos_and_error_budgets)
- [Google’s Error Budget Calculator](https://cloud.google.com/blog/products/observability/error-budget-calculator)
- [Cloudflare’s SLI/SLO Guide](https://www.cloudflare.com/learning/performance/sli-slo-sla/)
- [Better Uptime’s SLO Tool](https://www.betteruptime.com/slo) (for visualization).