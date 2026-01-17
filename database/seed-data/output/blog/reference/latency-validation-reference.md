# **[Pattern] Latency Validation Reference Guide**

---
## **Overview**
Latency validation ensures that system responses, external API calls, or network transactions adhere to defined performance thresholds (e.g., max acceptable delay). This pattern helps detect slow endpoints, degraded services, or misconfigured dependencies that may impact user experience, reliability, or business metrics.

Key use cases include:
- **Pre-deployment checks**: Validating SLA compliance before releasing updates.
- **Runtime monitoring**: Detecting regressions in production via automated alerts.
- **Performance optimization**: Identifying bottlenecks (e.g., database queries, third-party APIs).
- **Contract validation**: Enforcing latency guarantees between microservices.

Latency validation differs from traditional health checks by focusing on *timing* rather than success/failure states. It integrates with observability tools (e.g., Prometheus, Datadog) and CI/CD pipelines to enforce consistency.

---
## **Implementation Details**

### **Key Concepts**
| Term               | Definition                                                                                     | Example Values/Metrics                     |
|--------------------|---------------------------------------------------------------------------------------------|--------------------------------------------|
| **Latency Threshold** | Maximum allowed response time (e.g., 95th percentile < 200ms).                             | `p95_latency < 200ms`                      |
| **Baseline**       | Historical average latency for comparison (e.g., pre-rollout benchmark).                    | `avg_latency = 120ms`                     |
| **Degradation Threshold** | Percentage increase beyond baseline (e.g., 2x latency triggers alert).              | `latency > 1.5 * baseline`                 |
| **Sampling Rate**  | Percentage of requests tested (e.g., 1% for high-traffic endpoints).                       | `sampling_rate = 0.01` (1%)                |
| **Validation Scope**| Scope of validation (e.g., endpoint, API call, database query).                              | `/api/v1/users`, `payment-processor.get()` |

---

### **Validation Types**
| Type                     | Description                                                                                     | Use Case Example                          |
|--------------------------|---------------------------------------------------------------------------------------------|--------------------------------------------|
| **Fixed Threshold**      | Hardcoded maximum latency (e.g., "fail if > 500ms").                                         | Critical user flows (checkout, login).      |
| **Dynamic Threshold**    | Thresholds adjusted based on SLOs (e.g., 99th percentile < SLO).                            | High-availability services (e.g., banking APIs). |
| **Baseline Comparison**  | Current latency vs. historical baseline (e.g., "must be < 120% of baseline").             | Post-deployment regression testing.         |
| **Dependency Validation**| Validates latency of external calls (e.g., 3rd-party APIs).                                    | Payment gateway responses.                  |

---

### **Implementation Steps**

#### **1. Define Latency Metrics**
Use existing monitoring systems (e.g., Prometheus, OpenTelemetry) or instrument code with libraries like:
- **OpenTelemetry** (auto-instrumentation for HTTP/gRPC).
- **Datadog/New Relic** (pre-built latency dashboards).
- **Custom metrics** (e.g., `latency_microseconds` histogram).

**Example Metrics Schema:**
```plaintext
{
  "type": "histogram",
  "name": "http_request_duration_seconds",
  "buckets": [0.1, 0.5, 1, 2, 5, 10],  # Percentile thresholds
  "labels": ["endpoint", "service", "request_id"]
}
```

#### **2. Set Thresholds**
Configure thresholds per endpoint/service in:
- **Configuration files** (YAML/JSON):
  ```yaml
  latency_rules:
    - endpoint: "/api/checkout"
      type: "fixed_threshold"
      threshold: 200ms  # p95
      alert_level: "critical"
  ```
- **Orchestration tools**: Kubernetes `HPA` (Horizontal Pod Autoscaler) or Istio `DestinationRule`.

#### **3. Run Validations**
- **CI/CD Pipelines**: Validate latency before deploying (e.g., GitHub Actions, Jenkins).
  ```yaml
  # Example GitHub Action step
  - name: Run latency validation
    run: |
      curl -w "%{time_total}s" -o /dev/null http://localhost:8080/api/users
      if (( $(awk '{print $1}' results.txt) > 300 )); then
        exit 1
      fi
  ```
- **Runtime Monitoring**: Use tools like **Prometheus Alertmanager** or **Grafana Annotations**:
  ```yaml
  # Alert rule (Prometheus)
  ALERT HighLatency
    IF rate(http_request_duration_seconds{endpoint="/api/users"}[5m]) > 100
    FOR 1m
    LABELS {severity="warning"}
  ```

#### **4. Handle Degradations**
- **Automated Scaling**: Trigger auto-scaling (e.g., Kubernetes HPA) if latency exceeds thresholds.
- **Circuit Breakers**: Isolate failing dependencies (e.g., Hystrix, Resilience4j).
- **Graceful Degradation**: Fallback to cached responses or simpler UIs.

---

## **Schema Reference**
### **1. Latency Validation Rule Schema**
| Field               | Type    | Required | Description                                                                                     | Example Value                     |
|---------------------|---------|----------|---------------------------------------------------------------------------------------------|-----------------------------------|
| `endpoint`          | String  | Yes      | Target URL/path for validation.                                                                  | `/api/payment`                    |
| `metric_name`       | String  | Yes      | Prometheus/OpenTelemetry metric name.                                                         | `http_request_duration_seconds`   |
| `validation_type`   | Enum    | Yes      | Type of validation (`fixed_threshold`, `dynamic`, `baseline`).                               | `dynamic`                         |
| `threshold`         | Number  | Yes      | Max allowed latency (ms/seconds) or percentage.                                               | `200` (ms)                        |
| `baseline`          | Number  | No       | Historical average latency (used for `baseline` type).                                       | `150`                             |
| `sampling_rate`     | Float   | No       | Fraction of requests to test (0–1).                                                           | `0.01` (1%)                        |
| `alert_policy`      | Object  | No       | Slack/email/PagerDuty configuration for alerts.                                              | `{ "channel": "#alerts", "level": "warning" }` |
| `dependencies`      | Array   | No       | External services to validate (if applicable).                                                | `[ { "service": "payment-gateway", "url": "https://gateway.example.com" } ]` |

---

### **2. Example Rule (YAML)**
```yaml
latency_validations:
  - endpoint: "/api/checkout"
    metric_name: "http_request_duration_seconds"
    validation_type: "fixed_threshold"
    threshold: 200  # ms
    sampling_rate: 0.05
    alert_policy:
      severity: "critical"
      recipients: ["team@company.com"]

  - endpoint: "/api/users"
    metric_name: "database_query_latency"
    validation_type: "baseline"
    baseline: 120  # ms
    degradation_threshold: 1.5  # 50% increase triggers alert
```

---

## **Query Examples**
### **1. PromQL Query (Fixed Threshold Alert)**
```plaintext
# Alert if 95th percentile latency exceeds 200ms for /api/checkout
rate(http_request_duration_seconds_bucket{endpoint="/api/checkout"}[5m])
  > histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
  and on(endpoint) histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 200
```

### **2. OpenTelemetry Query (Dynamic SLO)**
```plaintext
# Check if 99th percentile latency exceeds SLO (e.g., 1 second)
record:opentelemetry.slo.http_request_latency
  where
    {service.name="ecommerce", http.route="/checkout"}
    and
    histogram.quantile(0.99, sum by (le) (rate(http.duration[5m]))) > 1000
```

### **3. Bash Script (Baseline Validation)**
```bash
#!/bin/bash
# Compare current latency vs. baseline (stored in $BASELINE_FILE)
BASELINE_FILE="baseline_latency.json"
ENDPOINT="http://localhost:8080/api/users"

# Get current latency (mean of 5 samples)
CURRENT_LATENCY=$(seq 1 5 | xargs -I{} curl -s -o /dev/null -w "%{time_total}s" "$ENDPOINT" | awk '{sum+=$1} END {print sum/NR}')

# Load baseline
BASELINE=$(jq '.users' "$BASELINE_FILE")

# Validate
if (( $(echo "$CURRENT_LATENCY > $BASELINE * 1.5" | bc -l) )); then
  echo "⚠️ Latency exceeded 150% of baseline ($BASELINE vs $CURRENT_LATENCY)"
  exit 1
fi
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                          |
|-----------------------------|---------------------------------------------------------------------------------------------|--------------------------------------|
| **[Health Checks]**         | Validate if a service is up (HTTP 200/500).                                                  | Basic uptime monitoring.             |
| **[Circuit Breaker]**       | Stop calling failing dependencies after N retries/failures.                                  | External API failures.                |
| **[Load Testing]**          | Simulate traffic to identify performance bottlenecks.                                        | Pre-release performance tuning.       |
| **[SLO/SLI Monitoring]**    | Track service-level objectives (e.g., "99.9% availability").                                  | Long-term reliability tracking.       |
| **[Canary Releases]**       | Gradually roll out changes to a subset of users.                                             | Safer deployment with latency checks. |
| **[Retries & Backoffs]**    | Exponential backoff for transient failures.                                                 | Resilient API calls.                  |

---
## **Tools & Libraries**
| Category               | Tools/Libraries                                                                             | Links                              |
|------------------------|-------------------------------------------------------------------------------------------|------------------------------------|
| **Observability**      | Prometheus, Grafana, OpenTelemetry, Datadog, New Relic.                                    | [Prometheus](https://prometheus.io) |
| **CI/CD Integration**  | GitHub Actions, Jenkins, ArgoCD.                                                          | [GitHub Actions](https://github.com) |
| **Auto-Scaling**       | Kubernetes HPA, AWS Auto Scaling, Serverless (Knative).                                   | [Kubernetes HPA](https://kubernetes.io) |
| **Dependencies**       | Resilience4j (Java), Hystrix (Legacy), Go’s `context.Timeout`.                           | [Resilience4j](https://resilience4j.io) |
| **Scripting**         | Bash, Python (`requests`, `urllib3`), Go (`net/http/httptest`).                           | [Python `requests`](https://docs.python-requests.org) |

---
## **Best Practices**
1. **Start Small**: Validate critical endpoints first (e.g., checkout, login).
2. **Use Percentiles**: Focus on `p95`/`p99` to avoid outliers skewing results.
3. **Integrate Early**: Add latency checks to CI/CD pipelines before performance testing.
4. **Set Realistic Baselines**: Use historical data from staging/production.
5. **Combine with Other Patterns**:
   - Pair with **Circuit Breakers** to handle failures gracefully.
   - Use **Load Testing** to stress-test thresholds.
6. **Document SLAs**: Clearly define latency expectations for stakeholders.
7. **Monitor False Positives**: Tune thresholds based on noise (e.g., network blips).