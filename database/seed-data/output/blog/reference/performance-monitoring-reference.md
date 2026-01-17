# **[Pattern] Performance Monitoring Reference Guide**

---

## **Overview**
The **Performance Monitoring** design pattern enables organizations to collect, analyze, and visualize real-time or historical metrics to optimize system performance, detect anomalies, and ensure reliability. This pattern is critical for cloud-native applications, microservices, and distributed systems, where latency, throughput, and resource utilization must be continuously monitored to prevent downtime and degrade user experience.

Performance monitoring helps:
- **Proactively identify bottlenecks** before they impact users.
- **Correlate metrics** with business events (e.g., traffic spikes, failed transactions).
- **Set baselines** for normal operation and detect deviations.
- **Comply with SLA/SLOs** by enforcing thresholds and alerts.
- **Optimize resource allocation** (CPU, memory, network, storage).

It integrates with **logging, tracing, and observability** patterns to create a holistic view of system health.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| Component               | Description                                                                                     | Example Tools/Technologies                     |
|-------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Metrics Collection**  | Gather quantitative data (e.g., request latency, error rates, queue lengths).                 | Prometheus, Datadog, New Relic, AWS CloudWatch  |
| **Storage & Retention** | Persist metrics for analysis (time-series databases preferred).                                | InfluxDB, TimescaleDB, Elasticsearch          |
| **Aggregation & Analysis** | Compute statistical trends (e.g., averages, percentiles, anomalies).                         | Grafana, Kibana, custom dashboards             |
| **Alerting**           | Trigger notifications when metrics breach thresholds (e.g., >99th percentile latency).        | PagerDuty, Opsgenie, custom scripts            |
| **Visualization**      | Render metrics in dashboards for stakeholders (e.g., DevOps, SREs).                          | Grafana, Datadog, Amazon Managed Grafana       |
| **Anomaly Detection**  | Use ML or statistical models to flag unexpected patterns.                                     | Prometheus Alertmanager, ML libraries (TensorFlow) |
| **SLO/SLI Definitions** | Define **Service Level Indicators (SLIs)** (e.g., "99% of requests under 200ms") and **Objectives (SLOs)**. | Custom configs, Slack/PagerDuty integration   |

---

### **2. Data Models & Schema Reference**
Performance monitoring relies on standardized metrics. Below are common schemas:

#### **A. Basic Metric Schema**
| Field          | Type    | Description                                                                 | Example Value          |
|----------------|---------|-----------------------------------------------------------------------------|------------------------|
| `metric_name`  | String  | Unique identifier (e.g., `http_request_duration_seconds`).                  | `api.latency`           |
| `value`        | Float   | Numeric measurement (e.g., latency in seconds, error count).                | `0.154`                 |
| `unit`         | String  | Dimensional unit (e.g., `"seconds"`, `"requests/minute"`).                  | `"milliseconds"`        |
| `labels`       | Object  | Key-value pairs for categorization (e.g., `service="auth-service"`, `env="prod"`). | `{ service: "checkout", env: "staging" }` |
| `timestamp`    | ISO8601 | When the metric was recorded.                                                | `"2024-05-20T14:30:00Z"` |
| `counter`      | Boolean | Whether the metric is cumulative (e.g., total errors vs. rate).             | `true`                  |

#### **B. Anomaly Detection Schema**
| Field               | Type    | Description                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------|
| `metric_name`       | String  | Name of the metric being monitored.                                          |
| `anomaly_score`     | Float   | Scored likelihood of an anomaly (0–100).                                     |
| `is_anomaly`        | Boolean | Boolean flag if the anomaly was triggered.                                   |
| `baseline`          | Float   | Expected value (e.g., 95th percentile latency).                              |
| `actual`            | Float   | Observed value during the anomaly.                                           |
| `root_cause`        | String  | Suggested cause (e.g., `"database_connection_pools_exhausted"`).          |

#### **C. Alert Schema**
| Field          | Type    | Description                                                                 |
|----------------|---------|-----------------------------------------------------------------------------|
| `alert_id`     | String  | Unique alert identifier.                                                    |
| `severity`     | String  | Severity level (`critical`, `warning`, `info`).                             |
| `metric`       | Object  | Reference to the triggering metric (see `Basic Metric Schema`).             |
| `trigger_time` | ISO8601 | When the alert was generated.                                               |
| `acknowledged` | Boolean | Whether the alert has been acknowledged (e.g., in a ticketing system).       |
| `resolved`     | Boolean | Whether the issue has been mitigated.                                      |

---

## **Implementation Guide**

### **1. Step 1: Define SLIs and SLOs**
- **SLI (Service Level Indicator):**
  Example: `"99% of API requests complete in <200ms"`.
- **SLO (Service Level Objective):**
  Example: `"Error rate < 0.1% over 30 days"`.
- **Tools:** Store these in a config file or database (e.g., GitHub/GitLab for versioning).

**Example SLO Definition (YAML):**
```yaml
slo:
  name: "Checkout API Latency"
  indicator: "p99_request_latency < 200ms"
  target: 0.999
  window: "30 days"
  alert_threshold: 0.99  # Trigger at 99% (1% above SLO)
```

---

### **2. Step 2: Instrument Your Application**
Inject metrics collection into your code (agents, SDKs, or manual logging).

#### **A. Example: Prometheus Client (Go)**
```go
import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	requestLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"route", "method"},
	)
)

func init() {
	prometheus.MustRegister(requestLatency)
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		duration := time.Since(start).Seconds()
		requestLatency.WithLabelValues(r.URL.Path, r.Method).Observe(duration)
	}()
	// Handle request...
}
```

#### **B. Example: AWS X-Ray (Node.js)**
```javascript
const AWSXRay = require('aws-xray-sdk-core');

AWSXRay.captureAWS(require('aws-sdk'));
AWSXRay.captureHTTP(require('aws-sdk'));
AWSXRay.captureNode('my-service', function() {
    // Your HTTP routes here
});
```

---

### **3. Step 3: Configure Storage & Aggregation**
- **Time-Series Databases:** Use Prometheus, InfluxDB, or TimescaleDB for high-cardinality metrics.
- **Sampling:** Reduce storage costs by sampling high-volume metrics (e.g., every 5 minutes instead of 1s).
- **Retention:** Archive older data to cheaper storage (e.g., S3 + Athena for long-term analytics).

**Example Prometheus Storage Config:**
```yaml
storage:
  tsdb:
    path: /prometheus/data
    retention.time: 30d
  remote_write:
    - url: "http://remote-write-endpoint:9090/api/v1/write"
```

---

### **4. Step 4: Set Up Alerting**
Define rules in Prometheus, Datadog, or a custom system.

**Example Prometheus Alert Rule:**
```yaml
groups:
- name: api-latency-alerts
  rules:
  - alert: HighLatency
    expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "99th percentile latency > 200ms"
      value: "{{ $value }}s"
```

---

### **5. Step 5: Visualize with Dashboards**
Build dashboards to monitor key metrics.

**Example Grafana Dashboard Panels:**
| Panel Type       | Metric Example                          | Example Query (PromQL)                     |
|------------------|----------------------------------------|--------------------------------------------|
| **Line Chart**   | Request latency over time              | `rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])` |
| **Gauge**        | Error rate                              | `rate(http_errors_total[5m])`              |
| **Histogram**    | Distribution of response times         | `http_request_duration_seconds_bucket`     |
| **Alert List**   | Open alerts                            | `alertmanager_alerts{status="firing"}`     |

---

### **6. Step 6: Anomaly Detection (Optional)**
Use ML or statistical methods to detect outliers.

**Example: Machine Learning Model (Python)**
```python
import numpy as np
from sklearn.ensemble import IsolationForest

# Train on historical data
model = IsolationForest(contamination=0.01)  # Expect 1% anomalies
model.fit(historical_metrics.reshape(-1, 1))

# Detect anomalies in new data
new_metrics = np.array([1200, 1500, 120]).reshape(-1, 1)
anomalies = model.predict(new_metrics)  # Returns -1 for anomalies
```

---

## **Query Examples**

### **1. PromQL Queries**
| Use Case                          | Query                                                                 |
|-----------------------------------|-----------------------------------------------------------------------|
| **Average request latency**       | `rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])` |
| **Error rate**                    | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])` |
| **Top services by error rate**    | `sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)` |
| **Database connection pool usage**| `prometheus_app_db_connections_used`                                |
| **Memory usage**                  | `sum(container_memory_working_set_bytes{namespace="my-namespace"}) by (pod)` |

---

### **2. Grafana Dashboard Example**
**Title:** `Microservice Health`
**Panels:**
1. **Latency (95th percentile)** – Line chart of `http_request_duration_seconds`.
2. **Error Rate (%)** – Gauge showing `rate(http_errors_total[5m]) / rate(http_requests_total[5m]) * 100`.
3. **Throughput (RPS)** – Line chart of `rate(http_requests_total[5m])`.
4. **Active Alerts** – Alert list from Prometheus.

---

## **Related Patterns**

1. **[Logging Pattern]**
   - *Why?* Performance monitoring needs logs for root-cause analysis (e.g., tracing slow requests to specific log entries).
   - *Integration:* Correlate metric IDs with log traces (e.g., using `trace_id` labels).

2. **[Distributed Tracing Pattern]**
   - *Why?* Trace requests end-to-end to identify latency sources (e.g., database calls, external APIs).
   - *Integration:* Use OpenTelemetry to emit both metrics and traces.

3. **[Circuit Breaker Pattern]**
   - *Why?* Performance monitoring detects failures that trigger circuit breakers to prevent cascading outages.
   - *Integration:* Alert on `http_request_duration` spikes to trigger circuit breaker opens.

4. **[Auto-Scaling Pattern]**
   - *Why?* Performance metrics (e.g., CPU usage) drive scaling decisions.
   - *Integration:* Use Prometheus + Kubernetes HPA to auto-scale based on `container_cpu_usage_seconds_total`.

5. **[Chaos Engineering Pattern]**
   - *Why?* Performance monitoring validates resilience by observing system behavior under controlled failures.
   - *Integration:* Measure `error_rate` and `latency` during chaos experiments.

6. **[Observability Pattern]**
   - *Why?* Performance monitoring is a subset of observability; combine with logging and tracing for holistic insights.
   - *Integration:* Use OpenTelemetry to unify metrics, logs, and traces.

---
## **Best Practices**
1. **Start Small:** Monitor critical paths first (e.g., user-facing APIs).
2. **Label Metrics:** Use consistent labels (e.g., `env`, `service`, `version`) for filtering.
3. **Right-Sample:** Avoid over-collecting; sample high-cardinality metrics.
4. **Set Realistic Thresholds:** Avoid alert fatigue with conservative SLOs.
5. **Document On-Call:** Clearly define who owns which metrics/alerts.
6. **Automate Remediation:** Use PagerDuty + GitHub Actions to auto-fix or escalate.
7. **Retain Historical Data:** Archive older metrics for trend analysis.

---
## **Troubleshooting**
| Issue                          | Diagnosis                          | Solution                                  |
|--------------------------------|-------------------------------------|-------------------------------------------|
| **High cardinality**           | Too many labels → storage overload. | Reduce labels or aggregate with `group_by`. |
| **Alert noise**                | Thresholds too sensitive.           | Tune SLOs or use multi-level alerts.      |
| **Missing data**               | Scraping or agent issues.           | Check Prometheus target health.           |
| **Slow queries**               | Complex PromQL expressions.         | Use precomputed aggregations.             |
| **False positives**            | Anomaly detection misfires.         | Validate with manual inspection.          |

---
## **Further Reading**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Metrics](https://opentelemetry.io/docs/specs/otel/metrics/)
- [Google SRE Book (SLIs/SLOs)](https://sre.google/sre-book/table-of-contents/)
- [AWS Well-Architected Performance Monitoring](https://aws.amazon.com/architecture/well-architected/)