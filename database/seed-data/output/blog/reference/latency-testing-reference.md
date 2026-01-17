---
**# [Pattern] Latency Testing Reference Guide**

---

## **1. Overview**
Latency testing measures the delay between a request initiation and its completion (e.g., response time, network delay, or processing speed). This pattern evaluates system responsiveness across components—such as APIs, databases, microservices, or end-user interactions—and helps optimize performance, diagnose bottlenecks, and ensure compliance with SLOs (Service Level Objectives).

Key use cases include:
- Identifying slow network paths (e.g., cross-region API calls).
- Benchmarking system scaling under load.
- Validating transactional latency (e.g., payment processing).
- Comparing latency between SaaS integrations or legacy systems.

Latency testing often pairs with **throughput** and **reliability** patterns to form a holistic performance evaluation.

---

## **2. Schema Reference**
Below are standardized schemas for defining latency test configurations and results.

### **2.1 Test Configuration Schema**
| Field               | Type       | Description                                                                 | Required | Example Values                     |
|---------------------|------------|-----------------------------------------------------------------------------|----------|-------------------------------------|
| `test_name`         | string     | Descriptive name for the test (e.g., `user-auth-latency`).               | Yes      | `"api-v1-login"`                    |
| `target_service`    | string     | Fully qualified endpoint (e.g., URL, microservice name, or DB schema).     | Yes      | `"https://api.example.com/auth"`     |
| `test_type`         | enum       | Type of latency measurement (e.g., **RTT**, **p95**, **end-to-end**).     | Yes      | `"RTT"`, `"p95"`                   |
| `request_payload`   | object     | Structured input data (e.g., JSON, XML format).                          | No       | `{"token": "xyz", "version": "2"}`  |
| `auth_headers`      | object     | Authorization headers (e.g., API keys, OAuth tokens).                      | No       | `{"Authorization": "Bearer abc123"}`|
| `concurrency_level` | number     | Simulated concurrent requests (e.g., 100–10,000).                         | No       | `500`                               |
| `timeout_ms`        | number     | Max allowed latency before test failure (default: `5000`).                | No       | `3000`                              |
| `replicate_regions` | array      | Array of geographic regions for distributed testing.                      | No       | `["us-east-1", "eu-west-1"]`       |
| `metrics_to_collect`| array      | Custom metrics (e.g., `response_time_ms`, `error_rate`).                  | No       | `["response_time", "ttfb"]`        |

---

### **2.2 Test Results Schema**
| Field               | Type       | Description                                                                 | Example                     |
|---------------------|------------|-----------------------------------------------------------------------------|-----------------------------|
| `test_id`           | string     | Unique identifier for the test run.                                          | `"latency-2023-10-01-09:45"`|
| `start_timestamp`   | timestamp  | When the test began (ISO 8601 format).                                      | `"2023-10-01T09:45:12Z"`    |
| `end_timestamp`     | timestamp  | When the test concluded.                                                    | `"2023-10-01T09:47:30Z"`    |
| `duration_ms`       | number     | Total test duration in milliseconds.                                        | `1398`                       |
| `metrics`           | object     | Aggregated latency data per region.                                         | `{ "us-east-1": { "p95": 120 } }`|
| `critical_errors`   | number     | Number of failed requests due to latency/timeout.                           | `42`                         |
| `success_rate`      | number     | Percentage of successful requests.                                          | `0.98`                       |

---

### **2.3 Common Metrics**
| Metric              | Description                                                                 | Formula/Method                          |
|---------------------|-----------------------------------------------------------------------------|-----------------------------------------|
| **RTT (Round-Trip Time)** | Time for a request and its response to travel.                          | `start_timestamp - end_timestamp`       |
| **p50 / Median**     | Middle value of response times (avoids outliers).                         | Percentile of all successful latencies. |
| **p95**             | 95th percentile latency (how slow 95% of requests take).                   | Same as p50 but for higher percentile.  |
| **TTFB (Time to First Byte)** | Delay between request and first byte received.                          | `TTFB = time_to_first_byte - request_start` |
| **Request/Response**| Separately measures request processing time vs. network delay.           | Use middleware (e.g., Prometheus, OpenTelemetry). |

---

## **3. Query Examples**
Use these queries to analyze latency data in tools like **Prometheus**, **Grafana**, or **custom dashboards**.

### **3.1 Detecting High-Latency Endpoints**
```promql
# Find endpoints with p95 > 200ms
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
by (endpoint)
> 0.2
```

### **3.2 Comparing Region Performance**
```sql
-- SQL (e.g., using InfluxDB)
SELECT
  region,
  p95_latency_ms,
  avg_latency_ms
FROM latency_tests
WHERE test_name = 'api-v1-payment'
GROUP BY region
ORDER BY p95_latency_ms DESC;
```

### **3.3 Identifying Threshold Breaches**
```python
# Python (with Pandas)
import pandas as pd

data = pd.read_csv("latency_results.csv")
violations = data[data["p95_ms"] > data["threshold_ms"]]["endpoint"].unique()
print("Breached endpoints:", violations)
```

### **3.4 Time-Series Correlation**
```grafana
# Grafana Dashboard Panel
- Query: `sum(by(instance, endpoint) ratelatency_ms{job="api"})`
- Compare with CPU/memory usage to isolate bottlenecks.
```

---

## **4. Implementation Details**
### **4.1 Tools & Frameworks**
| Tool               | Use Case                                                    | Example Command                     |
|--------------------|------------------------------------------------------------|-------------------------------------|
| **k6**             | Load-testing with latency simulation.                        | `k6 run --vus 100 --duration 1m script.js` |
| **Locust**         | Distributed latency testing across regions.                 | `locust -f locustfile.py --headless -u 1000 -r 100` |
| **Gatling**        | High-fidelity latency scenarios with visual reports.        | `gatling.sh -s MySimulation`         |
| **New Relic/Synthetic Monitoring** | Cloud-based latency tracking for SaaS integrations.    | Use "Monitors" > "Latency"           |
| **OpenTelemetry**  | Open-source instrumentation for latency observability.       | Add `otel-trace` tags to requests.  |

---

### **4.2 Best Practices**
1. **Isolate Variables**: Test one endpoint/region at a time to avoid noise.
2. **Use Realistic Data**: Simulate production-like payloads (e.g., avg. request size).
3. **Warm-Up**: Account for cold starts (e.g., serverless functions) with pre-warming.
4. **Distributed Testing**: Use cloud providers (e.g., AWS Lambda@Edge) to test global latency.
5. **Sliding Windows**: Compare historical trends (e.g., "latency increased by 15% YoY").

---
### **4.3 Common Pitfalls**
- **Overhead Misattribution**: Confuse client-side parsing latency with server-side processing.
- **Ignoring Network Variability**: Assume all regions share the same latency profile.
- **No Baseline**: Compare test results against historical data, not absolute values.
- **False Positives**: Thresholds too tight may flag legitimate spikes (e.g., traffic surges).

---

## **5. Related Patterns**
| Pattern               | Relationship to Latency Testing                                                                 |
|-----------------------|------------------------------------------------------------------------------------------------|
| **Load Testing**      | Complements latency testing by evaluating system behavior under scale.                           |
| **Throughput Testing**| Measures requests per second (RPS) alongside latency to isolate performance trade-offs.       |
| **Chaos Engineering** | Introduces controlled failures to measure system resilience during latency spikes.             |
| **Distributed Tracing**| Correlates latency with specific service calls in a microservices architecture.              |
| **SLA/SLO Monitoring**| Uses latency data to enforce service-level agreements (e.g., "99% p95 < 300ms").             |

---
**Note:** For advanced use cases, combine latency testing with **automated remediation** (e.g., auto-scaling based on `p95` thresholds).