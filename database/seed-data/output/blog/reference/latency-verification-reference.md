# **[Pattern] Latency Verification Reference Guide**

## **1. Overview**
Latency verification ensures that a system consistently meets predefined response-time targets (latency thresholds) for both internal and external endpoints. This pattern helps detect slow performance early, optimize critical paths, and enforce SLAs by validating actual latency against expected baselines. It’s essential for high-throughput systems, distributed architectures, or applications with strict performance requirements (e.g., real-time analytics, trading platforms, or interactive APIs).

Key objectives:
- **Proactive monitoring**: Measure end-to-end latency under realistic conditions.
- **Threshold enforcement**: Fail fast if latency exceeds predefined targets.
- **Root-cause analysis**: Identify bottlenecks (e.g., network delays, slow database queries).
- **SLA compliance**: Validate adherence to contractual or operational latency guarantees.

Latency verification pairs with other patterns like **Circuit Breaker**, **Rate Limiting**, and **Chaos Engineering** to build resilient systems. Implementations typically use synthetic transactions, distributed tracing, or in-production monitoring tools (e.g., Prometheus, Datadog, or custom scripts).

---

## **2. Schema Reference**
The following schema defines the core components of a latency verification system.

| **Field**               | **Type**          | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `verification_id`       | `string` (UUID)   | Unique identifier for the latency check. Used to correlate results across traces.                                                                                                             | `a1b2c3d4-5678-90ef-ghij-klmnopqrstuv` |
| `endpoint`              | `string`          | Fully qualified URL or service name being tested (e.g., `http://api.example.com/v1/users`).                                                                                                     | `payment-service:3000/process`       |
| `latency_threshold`     | `integer` (ms)    | Maximum acceptable latency (e.g., 200ms).                                                                                                                                                      | `200`                                 |
| `timeout`               | `integer` (ms)    | Maximum allowed time for the entire verification (must be ≥ `latency_threshold`).                                                                                                               | `500`                                 |
| `weight`                | `float` (0–1.0)   | Relative importance of this check (used for aggregated scoring). Higher weights indicate critical paths.                                                                                       | `0.85`                                |
| `tags`                  | `array<string>`   | Metadata labels (e.g., `["database", "auth"]`) for filtering results.                                                                                                                                 | `["payment-gateway", "high-priority"]` |
| `expected_response`     | `string`          | Optional: Expected response format (e.g., JSON schema or regex pattern).                                                                                                                              | `{"status": "success"}`               |
| `verification_type`     | `enum`            | How latency is measured:                                                                                                                                                                           | `synthetic`, `production`, `chaos`   |
|                           |                   | - `synthetic`: Simulated request (e.g., via load testing tools).                                                                                                                                   |                                       |
|                           |                   | - `production`: Real traffic (e.g., via APM tools).                                                                                                                                           |                                       |
|                           |                   | - `chaos`: Intentional disruption (e.g., network delay injection).                                                                                                                               |                                       |
| `metrics`               | `object`          | Collected metrics per execution:                                                                                                                                                                      | `{`                                  |
|                         |                   | - `p95_latency`: 95th percentile latency (ms).                                                                                                                                                   | `"180"`                               |
|                         |                   | - `error_rate`: % of failed verification runs.                                                                                                                                               | `0.05`                                |
|                         |                   | - `last_run`: Timestamp (ISO 8601).                                                                                                                                                         | `"2024-05-15T14:30:00Z"`              |
| `alert_threshold`       | `integer` (ms)    | Latency at which an alert is triggered (e.g., 90% of `latency_threshold`).                                                                                                                           | `180` (90% of 200ms)                  |
| `retries`               | `integer`         | Number of retry attempts if initial request fails.                                                                                                                                                   | `3`                                   |
| `retries_delay`         | `integer` (ms)    | Delay between retries (exponential backoff supported).                                                                                                                                               | `1000`                                |
| `dependencies`          | `array<string>`   | List of services/endpoints this latency check depends on (e.g., `["cache-service", "payment-db"]`). Used for dependency-aware alerts.                                                               | `["user-auth"]`                       |

---

## **3. Query Examples**
### **3.1. Verify Endpoint Latency (Synthetic)**
```python
import requests

def verify_latency(endpoint: str, threshold_ms: int = 200) -> bool:
    start_time = time.time()
    try:
        response = requests.get(endpoint, timeout=threshold_ms * 1.2)  # Timeout slightly higher than threshold
        latency_ms = int((time.time() - start_time) * 1000)
        if latency_ms > threshold_ms:
            raise TimeoutError(f"Latency ({latency_ms}ms) exceeded threshold ({threshold_ms}ms)")
        return True
    except Exception as e:
        log_error(f"Verification failed for {endpoint}: {str(e)}")
        return False
```
**Use Case**: Periodic checks in a CI/CD pipeline or an internal monitoring script.

---

### **3.2. Distributed Tracing (Production)**
**OpenTelemetry Trace Example**:
```yaml
# config.yaml
traces:
  - name: payment-service-latency
    endpoints:
      - url: http://payment-service:3000/process
        latency_threshold: 150
        tags: ["payment-gateway", "high-priority"]
    sampler: "always_on"  # Sample all requests
    exporters:
      - otlp:http://otel-collector:4318
```
**Tooling**: Integrate with Jaeger, Zipkin, or Prometheus for visualization.
**Key Metric**: Query `http_server_request_duration_seconds{p95 > 150}`.

---

### **3.3. Chaos Engineering (Latency Injection)**
**Chaos Mesh Example**:
```yaml
# latency-delay.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: delay-payment-service
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: payment-service
  delay:
    latency: "250ms"  # Inject 250ms delay
  duration: "30s"
```
**Verification Step**:
- Run latency checks before/after the experiment.
- Compare `p95_latency` to baseline (e.g., `p95_before: 120ms → p95_after: 370ms`).

---

### **3.4. SQL Query (Database Latency)**
```sql
-- Check if query latency exceeds threshold (e.g., 500ms) in PostgreSQL
SELECT
  query,
  pg_stat_statements.query,
  AVG(execution_time) as avg_latency_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time) as p95_latency_ms
FROM pg_stat_statements
WHERE query LIKE '%SELECT * FROM orders%'
GROUP BY query
HAVING p95_latency_ms > 500;
```
**Alert Rule**:
```promql
histogram_quantile(0.95, rate(pg_stat_statements_execution_time_seconds_bucket[5m])) > 0.5
```

---

## **4. Implementation Details**
### **4.1. Key Concepts**
1. **Synthetic vs. Production Traffic**:
   - *Synthetic*: Controlled, repeatable tests (e.g., using Locust or k6).
   - *Production*: Real-world monitoring (e.g., via APM tools like Datadog or New Relic).

2. **Latency Thresholds**:
   - Set thresholds based on:
     - Business requirements (e.g., "99% of requests must respond in <100ms").
     - Historical baselines (e.g., `p95` from production traffic).
     - Dependency constraints (e.g., downstream service limits).

3. **Retry Logic**:
   - Retries should be **configurable** (e.g., `max_retries: 3`, `backoff: exponential`).
   - Avoid masking intermittent issues; log retries separately.

4. **Alerting Strategies**:
   - **Threshold Alerts**: Trigger when `latency > alert_threshold` (e.g., 90% of `latency_threshold`).
   - **Anomaly Detection**: Use statistical methods (e.g., z-scores) to detect spikes.
   - **Multi-Dimensional Alerts**: Group by `tags` (e.g., "All payments endpoints > 200ms").

5. **Dependency Mapping**:
   - Visualize latency bottlenecks using graphs (e.g., [Grafana Tracing](https://grafana.com/docs/grafana-cloud/tracing/)).
   - Example:
     ```
     Client → [20ms] API Gateway → [150ms] Payment Service → [30ms] DB
     ```

---

### **4.2. Tools & Libraries**
| **Category**          | **Tools/Libraries**                                                                 | **Use Case**                                  |
|-----------------------|------------------------------------------------------------------------------------|-----------------------------------------------|
| **Synthetic Testing** | Locust, k6, Gatling                                                          | Load testing + latency verification.          |
| **APM**               | Datadog, New Relic, Dynatrace, OpenTelemetry                                    | Production monitoring.                        |
| **Chaos Engineering** | Chaos Mesh, Gremlin, Netflix Simian Army                                       | Intentional latency/timeout experiments.      |
| **Metrics**           | Prometheus, Grafana, CloudWatch                                               | Aggregation + visualization.                   |
| **CI/CD Integration** | GitHub Actions, Argo Workflows, Tekton                                          | Pre-deployment latency checks.                |
| **Database**          | pglogical (PostgreSQL), MySQL Proxy                                           | Track query-level latency.                    |

---

### **4.3. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------|
| **Flaky thresholds**                  | Use statistical methods (e.g., moving averages) or chaos-controlled baselines.                   |
| **Overhead from monitoring**         | Sample traces (e.g., 1% of requests) or use probabilistic sampling.                              |
| **Ignoring cold starts**              | Warm up services before verification (e.g., pre-heat caches).                                    |
| **False positives in alerts**        | Implement alert fatigue reduction (e.g., only notify after 3 consecutive failures).                |
| **Not testing edge cases**           | Include verification for:
   - High concurrency (e.g., 1000 RPS).
   - Network partitions (e.g., simulate AWS AZ failures).                                             |
| **Dependency blindness**             | Use distributed tracing to map latency across services.                                           |

---

## **5. Related Patterns**
| **Pattern**              | **Connection to Latency Verification**                                                                                                                                                                                                 | **When to Use Together**                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**      | Latency verification can trigger circuit breaks if thresholds are violated.                                                                                                                                                     | High-availability systems where degraded performance should short-circuit traffic.                        |
| **Rate Limiting**        | Correlate latency spikes with rate-limiting violations (e.g., throttled endpoints).                                                                                                                                             | APIs with usage-based pricing or abuse prevention.                                                          |
| **Chaos Engineering**    | Inject latency/errors to test failure recovery and verify latency thresholds hold under stress.                                                                                                                               | Post-mortem analysis or SLA validation.                                                                    |
| **Distributed Tracing** | Capture end-to-end latency (e.g., client → service → DB) for granular bottleneck analysis.                                                                                                                                 | Debugging multi-service latency issues.                                                                      |
| **Canary Releases**      | Gradually roll out changes and verify latency in a subset of traffic before full deployment.                                                                                                                                      | Reducing risk in large-scale deployments.                                                                     |
| **Retries & Backoff**   | Latency verification can validate retry logic doesn’t mask underlying issues.                                                                                                                                                     | Resilient microservices with transient failures.                                                          |
| **Auto-Scaling**         | Scale resources dynamically based on latency spikes (e.g., Kubernetes HPA with custom metrics).                                                                                                                                  | Cloud-native applications with variable load.                                                              |

---

## **6. Example Workflow**
1. **Define Verification Rules**:
   ```yaml
   # latency_rules.yaml
   - name: user-auth-service
     endpoint: http://auth-service:8080/login
     latency_threshold: 100
     alert_threshold: 90
     weight: 0.9
     tags: ["auth", "production"]
   ```
2. **Run Synthetic Checks**:
   ```bash
   # Using k6
   k6 run --vus 10 --duration 30s script.js
   ```
3. **Monitor Production**:
   - Query Prometheus:
     ```promql
     rate(http_request_duration_seconds_bucket{job="auth-service"}[1m])
     ```
4. **Alert & Remediate**:
   - Slack alert: `User auth latency (p95: 120ms) > threshold (100ms). Retrying...`
   - Action: Scale up auth-service or investigate DB connection pool exhaustion.

---
**Further Reading**:
- [OpenTelemetry Latency Metrics](https://opentelemetry.io/docs/specs/semantic_conventions/metrics/)
- [Chaos Engineering by Gartner](https://www.gartner.com/en/topics/chaos-engineering)
- [Latency Numbers Every Programmer Should Know](https://www.kegel.com/c10k.html)