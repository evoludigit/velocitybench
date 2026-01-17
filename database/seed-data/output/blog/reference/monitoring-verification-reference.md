---
# **[Pattern] Monitoring Verification Reference Guide**

---

## **Overview**
**Monitoring Verification** is a pattern used to ensure that system metrics, logs, events, and alerts align with expected behavior. This pattern validates that monitoring systems (e.g., Prometheus, Datadog, CloudWatch) correctly report data from instruments (e.g., applications, infrastructure components) by comparing observed values against known benchmarks, thresholds, or historical baselines. It reduces false positives/negatives in alerts, improves observability accuracy, and maintains operational trust.

Key use cases:
- Confirming metric collection pipelines and storage integrity.
- Detecting anomalies in instrumentation (e.g., missing data points).
- Validating alerting rules against real-world conditions.
- Auditing monitoring configurations for misconfigurations.

**When to apply:**
- Deploying new monitoring systems.
- Introducing changes to metrics/instruments.
- Investigating alert fatigue or missed outages.
- Performing compliance or audit checks.

---

## **Implementation Details**
### **Core Concepts**
1. **Verification Targets**
   - Metrics: Gauges, counters, histograms, summaries.
   - Logs/Events: Structured messages tagged by severity or event type.
   - Alerts: Rules fired or suppressed.

2. **Verification Methods**
   - **Static Checks:** Validate labels, formats, or unit consistency.
   - **Dynamic Checks:** Compare observed values to expected benchmarks (e.g., *latency < 1s*).
   - **Time-Based Checks:** Ensure metrics are sampled at expected intervals (e.g., `query_interval`).
   - **Dependencies:** Verify external services (e.g., API monitoring) respond as expected.

3. **Verification Frequency**
   - Scheduled (e.g., hourly/daily checks via cron).
   - On-demand (e.g., after deployments or config updates).
   - Continuous (e.g., embedded in CI/CD pipelines).

4. **Tools & Libraries**
   - **Prometheus:** `record` + `alertmanager` for custom rule verification.
   - **Grafana:** Query execution and visualization debugging.
   - **Synthetics (e.g., Gremlin, CloudWatch Synthetics):** Simulate user flows to verify latency.
   - **Custom Scripts:** Python (Prometheus API), Bash (log parsing), or Terraform (infrastructure checks).

---

## **Schema Reference**
| **Component**       | **Key Attributes**                                                                 | **Example Values**                                                                 |
|----------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Verification Rule** | - **Type:** Static/Dynamic/Time-Based                                             | `metric_format`, `value_comparison`                                                  |
|                      | - **Target:** Metric/Log/Alert                                                      | `/http_requests_total`, `{app="my-service", severity="error"}`                    |
|                      | - **Scope:** Global/Label-Specific                                                 | `job=prometheus`, `env=prod`                                                        |
|                      | - **Threshold:** Standard/Relative/Delta                                            | `value > 100`, `value > prior_value * 1.5`                                          |
| **Check Definition**  | - **Query:** PromQL/GraphQL/Grep                                                    | `rate(http_requests_total{status=5xx}[5m]) > 0`                                      |
|                      | - **Expected Value:** Static/Dynamic (e.g., "95th percentile < 1s")               | `"< 100ms"`                                                                         |
|                      | - **Timeout:** Seconds for query completion                                         | `15s`                                                                               |
|                      | - **Dependencies:** Required external services                                     | `database:ready`, `external_api:healthy`                                            |
| **Verification Result** | - **Status:** Pass/Fail/Timeout                                                      | `ok`, `fail: missing_data`                                                          |
|                      | - **Timestamp:** When the check was run                                             | `2024-05-20T12:00:00Z`                                                             |
|                      | - **Annotations:** Context for failures (e.g., `labels="env=dev"`)                | `error: "query_syntax_error"`                                                      |
| **Remediation Action** | - **Auto-Remediation:** Retry/Notify (e.g., Slack, PagerDuty)                       | `retry_query:yes`, `notify_team:critical`                                           |
|                      | - **Owner:** Team responsible (e.g., SRE, DevOps)                                  | `owner=platform-team`                                                              |

---

## **Query Examples**
### **1. Metric Verification (Prometheus)**
**Check:** Ensure CPU usage stays under 80% during peak hours.
```promql
# Dynamic Check: Alert if CPU usage exceeds threshold
max_over_time(container_cpu_usage_seconds_total{container!="POD"}[5m])
  / max_over_time(container_cpu_usage_seconds_total{container!="POD"}[1h])
  > 0.8
  and on() group_left(pod_name) namespace="default"
  OR
# Static Check: Verify metric labels are present
absent(container_cpu_usage_seconds_total{namespace="default", pod_name!=""})
```
**Output:**
```plaintext
{namespace="default", pod_name="web-pod-1"} 85.2
{namespace="default", pod_name="db-pod-1"} 90.1 → FAIL
```

### **2. Log Verification (Grep/LogsQL)**
**Check:** Confirm error logs are tagged with severity="error".
```bash
# Shell Script: Validate log format
grep -E '{"severity":"error","message":"[^"]+",' /var/log/myapp/error.log |
  awk 'NR==0 {log_expected=1}' END {if (log_expected) print "FAIL: No errors found"}
```
**Output:**
```plaintext
FAIL: No errors found
```

### **3. Alert Verification (Alertmanager Config)**
**Check:** Ensure alerts for `HighLatency` fire only for production.
```yaml
# Alertmanager rule: Verify alert targets correct environment
groups:
- name: verification
  rules:
  - alert: HIGH_LATENCY_VERIFICATION
    expr: alertmanager_rules_evaluated{alert="HighLatency"} != 0
    labels:
      severity: warning
    annotations:
      description: "HighLatency alert fired on {{ $labels.env }}. Expected env: prod"
    conditions:
    - type: matches
      matchers:
        - env="prod"
```
**Output:**
```plaintext
HIGH_LATENCY_VERIFICATION: 1 {env="dev"} → FAIL (alert fired in wrong env)
```

---

## **Query Examples: Synthetics**
**Check:** Simulate a user flow to verify API response times.
```python
# Gremlin Script (Synthetics)
import gremlin

@gremlin_script
def verify_api():
    response = gremlin.http.get("https://api.example.com/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"
    return {"latency": response.elapsed.total_seconds()}
```
**Output:**
```json
{"latency": 0.45, "status": "pass"}
{"latency": 2.1, "status": "fail: timeout"}
```

---

## **Related Patterns**
1. **[Canary Analysis](canary_analysis.md)**
   - *Why?* Complementary for gradual deployment monitoring.
   - *How?* Use verification rules to validate canary metrics before rolling out globally.

2. **[Health Checks](health_check.md)**
   - *Why?* Low-level dependencies (e.g., DB, cache) should be verified before monitoring alerts.
   - *How?* Embed verification rules in health check endpoints (e.g., `/healthz`).

3. **[Observability Pipeline](observability_pipeline.md)**
   - *Why?* Essential for monitoring system health to validate data pipelines.
   - *How?* Apply verification rules to metrics ingestion pipelines (e.g., Flume, Fluentd).

4. **[Retroactive Anomaly Detection](anomaly_detection.md)**
   - *Why?* Detects unexpected patterns post-hoc for verification benchmarking.
   - *How?* Use verification results to train anomaly models.

5. **[Chaos Engineering](chaos_engineering.md)**
   - *Why?* Introduces controlled failures to test monitoring resilience.
   - *How?* Verify monitoring still reports correctly during chaos experiments.

---

## **Best Practices**
1. **Start Small:** Begin with critical metrics/logs (e.g., P99 latency, error rates).
2. **Automate:** Embed checks in CI/CD (e.g., Prometheus `alertmanager` tests in GitHub Actions).
3. **Collaborate:** Involve DevOps/SREs to define verification thresholds.
4. **Audit Logs:** Track all verification failures for trend analysis.
5. **Document:** Maintain a living doc of verification rules and expectations.

---
**Further Reading:**
- [Prometheus Monitoring Verification](https://prometheus.io/docs/operating/verifying/)
- [Grafana Alerting Docs](https://grafana.com/docs/grafana/latest/alerting/alert-rules/)
- [SRE Book: Monitoring Systems](https://sre.google/sre-book/monitoring-distributed-systems/)