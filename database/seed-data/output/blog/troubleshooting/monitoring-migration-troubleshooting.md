---
# **Debugging Monitoring Migration: A Troubleshooting Guide**
*For backends handling observability tool transitions, legacy vs. modern monitoring, or migrating from on-prem to cloud-native monitoring.*

---

## **1. Title**
Debugging **Monitoring Migration**: Troubleshooting Guide for Backend Engineers

---

## **2. Symptom Checklist**
Before diving into fixes, verify if the following symptoms match your issue. Check each in order:

| Symptom Category       | Symptoms                                                                               | Likely Cause                                                                 |
|------------------------|---------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Data Loss/Gaps**     | Alerts missing; metrics appear incomplete; logs missing critical traces.            | Incorrect configuration, pipeline misalignment, or unhandled schema changes. |
| **Latency Spikes**     | Monitoring dashboards lag; API response delays; metric queries timeout.             | Poorly distributed tracing or metric scraping issues.                       |
| **False Positives**    | Alerts triggered for non-critical issues (e.g., "High CPU" when idle).             | Misconfigured thresholds, incorrect metric aggregation.                     |
| **Permission Errors**  | "Permission denied" in logs; roles not syncing between tools (e.g., Datadog vs. Prom).| RBAC misalignment during migration.                                          |
| **Tool Compatibility** | Legacy integrations (e.g., Nagios plugins) failing; cloud provider SDKs missing.     | Unpatched dependencies or outdated SDKs.                                    |
| **Cost Overruns**      | Unexpected charges in cloud-native monitoring (e.g., New Relic, Grafana Cloud).      | Unoptimized sampling rates or unconstrained scrape intervals.               |
| **Configuration Drift**| runtime configurations differ between environments (dev/stage/prod).                | Infrastructure-as-code misalignment or manual overrides.                  |

**Pro Tip:** If symptoms escalate after migration, revisit the **requirements** section and audit the new monitoring stack for deviations.

---

## **3. Common Issues and Fixes**
### **Issue 1: Metric/Data Inconsistencies**
**Symptoms:**
- Metrics from the old tool (e.g., Prometheus) match new tool (e.g., OpenTelemetry) only partially.
- **Code Example (Grafana Alert Rule):
  ```yaml
  # Old Prometheus alert rule (expected 99th percentile)
  - alert: HighLatency
      expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
      for: 10m
      labels: {
        severity: "critical"
      }
      annotations: {
        summary: "High latency detected"
      }
  ```
  **Fixed Rule for OpenTelemetry:**
  ```yaml
  - alert: HighLatencyOTel
      expr: histogram_quantile(0.99, rate(otel.http.server.duration_bucket{status=~"2.."}[5m]))
      for: 10m
      labels: {
        severity: "critical"
      }
      annotations: {
        summary: "OTel latency exceeds threshold"
      }
  ```

**Fix:** Use an **exporter bridge** (e.g., Prometheus adapter for OpenTelemetry) to reconcile metrics.
**Debug Steps:**
1. Export both tools' metrics to a time-series DB (e.g., TimescaleDB) and compare:
   ```bash
   # Compare Prometheus and OTel via CLI
   curl -G http://localhost:9090/api/v1/query\?query=up --output prometheus_data.json
   curl -G http://localhost:8080/v1/metrics\?export=prometheus --output otel_data.json
   ```
2. Check for missing labels or metric renames in the new tool’s schema.

---

### **Issue 2: Alerting Silos**
**Symptoms:**
- Alerts from the old system (e.g., PagerDuty) are not forwarding to the new alerting manager (e.g., Slack/VictorOps).
- **Broken Webhook Example:**
  ```python
  # Old implementation (fails due to HTTP 403)
  def forward_alert_to_slack(alert):
      response = requests.post(
          "https://hooks.slack.com/services/OLD_WEBHOOK",
          json=alert.to_dict()
      )
  ```
**Fix:** Validate webhook endpoints first:
```bash
# Test with curl (pre-migration)
curl -X POST https://hooks.slack.com/services/NEW_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"text": "Test alert from migration"}'
```

**Debug Steps:**
1. **Check SSL/TLS:** Ensure the new Slack/Teams webhook uses HTTPS.
2. **Rate Limits:** Some tools (e.g., Datadog) throttle webhook calls. Add retries:
   ```python
   from tenacity import retry, stop_after_attempt

   @retry(stop=stop_after_attempt(3))
   def send_alert(alert):
       requests.post(WEBHOOK_URL, json=alert.to_dict())
   ```

---

### **Issue 3: Dead Metric Scraping Targets**
**Symptoms:**
- Prometheus/Grafana reports `UP{job="my-service"}` as `0`.
- Logs show `permission denied` when scraping:
  ```log
  E1006 12:00:00.123 scrape.go:378] Failed to scrape <target>: dial tcp: lookup <hostname>: no such host
  ```

**Fix:** Update your `prometheus.yml`/`scrape_config`:
```yaml
scrape_configs:
- job_name: 'legacy-service'
  static_configs:
  - targets: ['legacy-service:8080']
    labels:
      env: 'production'
  # For cloud-hosted services (e.g., AWS ECS):
  - job_name: 'ecs-service'
    metrics_path: '/metrics'
    params:
      format: 'prometheus'
    scheme: 'http'
    tls_config:
      insecure_skip_verify: true  # Only for testing!
    relabel_configs:
    - source_labels: [__meta_ecs_task_arn]
      regex: '.*'
      target_label: 'ecs_task_id'
```

**Debug Steps:**
1. **Verify Target Accessibility:**
   ```bash
   # Test connection manually
   curl -v http://legacy-service:8080/metrics
   ```
2. **Check Network Policies:** Ensure the monitoring tool’s pod/service can reach targets.

---

### **Issue 4: Tracing Corruption**
**Symptoms:**
- Traces in Jaeger/Zipkin show missing spans or incorrect IDs.
- Logs like:
  ```log
  E1006 12:00:00.123 trace.go:250] Failed to sample trace with ID 123456: trace not found
  ```

**Fix:** Re-inject the OpenTelemetry SDK with correct headers:
```java
// Java SDK (fixing auto-instrumentation)
otelSdk = OpenTelemetrySdk.builder()
    .setTracerProvider(tracerProvider)
    .build();
Tracer tracer = otelSdk.getTracer("com.example.app");
Span span = tracer.spanBuilder("request")
    .setAttribute(KeyValue.create("service.name", "legacy-service"))
    .startSpan();
```

**Debug Steps:**
1. **Export Traces for Comparison:**
   ```bash
   # Export OTel traces to Jaeger
   docker run -d --network=host jaegertracing/all-in-one:1.34
   ```
2. **Audit Span Context Propagation:**
   - Ensure all HTTP/gRPC endpoints propagate `traceparent` headers.

---

## **4. Debugging Tools and Techniques**
| Tool/Technique          | Use Case                                                                 | Example Command/Query                                                                 |
|-------------------------|---------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Prometheus Debugging** | Check scrape errors                                                      | `promtool check config /etc/prometheus/prometheus.yml`                                |
| **Grafana TSRB**         | Troubleshoot rule errors                                                 | `grafana-cli --debug alert-rules list`                                                  |
| **OpenTelemetry CLI**    | Validate exports                                                          | `otel-collector --config-file=collector-config.yml --log-level=debug`                 |
| **Chaos Engineering**    | Simulate failures (e.g., kill a pod to test alerting)                    | `kubectl delete pod <pod-name> --grace-period=0 --force`                               |
| **Prometheus Alertmanager** | Analyze alert silences/muting rules              | `alertmanager -config.file=/etc/alertmanager/config.yml test`                          |
| **Datadog/CloudWatch**    | Cross-tool metric reconciliation                                          | Use `dd-metric` CLI or AWS CLI to query both systems.                                  |

**Advanced: Distributed Tracing with eBPF**
- Use tools like **Bcc** or **Fluent Bit** to profile system calls:
  ```bash
  # Install BCC, then capture metrics
  sudo bpftool dump perf event <PID>
  ```

---

## **5. Prevention Strategies**
### **Pre-Migration Checklist**
1. **Audit Dependencies:**
   - List all monitoring integrations (e.g., Prometheus, Datadog, Splunk).
   - Document versions and compatibility:
     ```bash
     # Example: Check Datadog agent version
     /opt/datadog-agent/bin/agent status
     ```
2. **Load Test the New Stack:**
   - Simulate production traffic using **Locust** or **k6**:
     ```python
     # k6 script for monitoring migration load test
     import http from 'k6/http';

     export const options = {
       vus: 100,
       duration: '30s'
     };

     export default function () {
       http.get('http://new-monitoring-grafana:3000');
     }
     ```
3. **Canary Alerts:**
   - Route 5% of traffic to the new tool and compare:
     ```bash
     # Use Ansible to manage canary routing
     - hosts: loadbalancers
      tasks:
        - name: Update weight for new monitoring endpoint
          lineinfile:
            path: /etc/nginx/nginx.conf
            regexp: 'backend new-monitoring'
            line: '    weight=5;'
     ```

### **Post-Migration Best Practices**
- **Implement Golden Signals Monitoring:**
  - Latency, Traffic, Errors, Saturation (LTEs) for both tools until parity.
- **Use Infrastructure as Code (IaC):**
  - Example Terraform for Datadog monitoring:
    ```hcl
    resource "datadog_monitor" "high_latency" {
      name    = "legacy-service-high-latency"
      type    = "query alert"
      query   = "avg:http.request.duration{service:legacy-service} > 1000"
      message = "High latency detected"
      notify_no_data = true
    }
    ```
- **Rollback Plan:**
  - Maintain access to the old monitoring system for 24–48 hours post-migration.

---

## **6. Final Checklist Before Declaring Success**
✅ All alerts from the old system are migrated or archived.
✅ No data loss in the last 7 days (verify via time-series DB queries).
✅ Cost analysis shows no unexpected spikes (use **CloudWatch Cost Explorer** or **Datadog Cost Optimization**).
✅ Team runbooks have been updated with new monitoring URLs/alerts.

---
**Quick Reference:**
- **For Metric Issues:** Use `promtool` or `curl` to compare exports.
- **For Alerting:** Validate webhooks with `curl` and add retries.
- **For Tracing:** Check span IDs and propagate `traceparent`.

**Remember:** Monitoring migration is a **lens into system health**—use it to catch issues *before* they degrade user experience.