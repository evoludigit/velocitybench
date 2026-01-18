# **[Pattern] Availability Troubleshooting Reference Guide**

---

## **Overview**
The **Availability Troubleshooting** pattern provides a structured approach to diagnosing and resolving issues that degrade system availability. Availability refers to the percentage of time a system or service is operational and accessible to users. This pattern helps identify root causes—such as hardware failures, dependency breakdowns, or misconfigurations—that lead to downtime or degraded performance. It integrates proactive monitoring, log analysis, and performance benchmarking to ensure rapid diagnosis and resolution of availability-related incidents.

Key focus areas include:
- **Proactive detection** (e.g., via synthetic transactions, anomaly detection).
- **Root cause analysis** (e.g., tracing failures through distributed system logs).
- **Remediation strategies** (e.g., failover testing, capacity planning adjustments).
- **Prevention techniques** (e.g., chaos engineering, automated recovery procedures).

This guide assumes familiarity with observability concepts (metrics, logs, and traces) and basic DevOps practices.

---

## **Schema Reference**
The following table outlines core components of the **Availability Troubleshooting** pattern, categorized by stage:

| **Category**               | **Component**                     | **Description**                                                                 | **Key Attributes**                                                                 |
|----------------------------|-----------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Proactive Monitoring**   | **Synthetic Transactions**        | Simulated user requests to detect failures before end-users notice them.        | - Endpoint URLs, success/failure thresholds, frequency.                              |
|                            | **Anomaly Detection**             | AI/ML-based detection of deviations from baseline performance.                   | - Alert thresholds, time windows, correlation rules.                                 |
| **Diagnostic Tools**       | **Log Aggregation**               | Centralized collection and analysis of application/log server logs.              | - Retention period, query language (e.g., ELK, Splunk).                             |
|                            | **Distributed Tracing**           | Tracing requests across microservices to identify bottlenecks.                  | - Trace sampling rate, latency thresholds, service dependency mapping.             |
|                            | **Performance Benchmarks**        | Historical or baseline performance metrics for comparison.                      | - Response time percentiles (P99, P95), request volume trends.                     |
| **Root Cause Analysis**    | **Dependency Analysis**           | Mapping system dependencies (e.g., databases, APIs) to identify cascading failures. | - Dependency graphs, health check intervals, retry policies.                        |
|                            | **Failure Modes**                 | Predefined failure scenarios (e.g., network partition, disk failure).          | - Mitigation steps, recovery time objectives (RTOs).                                |
| **Remediation**            | **Automated Rollbacks**           | Auto-revert to a stable version if health checks fail.                           | - Rollback triggers, rollback windows.                                               |
|                            | **Failover Testing**              | Simulating failover scenarios to validate redundancy mechanisms.                 | - Failover duration, fallback timeouts.                                             |
|                            | **Capacity Planning Adjustments** | Scaling resources (e.g., adding nodes) based on load patterns.                  | - Auto-scaling policies, scaling thresholds.                                        |
| **Prevention**             | **Chaos Engineering**              | Deliberately inducing failures to test resilience.                              | - Fault injection types (e.g., latency, node kill), probability.                    |
|                            | **Automated Recovery Procedures** | Scripted responses to common failure scenarios.                                | - Playbook triggers, integration with monitoring tools (e.g., PagerDuty, Opsgenie). |

---

## **Query Examples**
Below are examples of queries and commands used in each stage of troubleshooting availability issues. Assume a logging platform like **ELK Stack (Elasticsearch, Logstash, Kibana)** or **Prometheus/Grafana** for metrics.

---

### **1. Proactive Monitoring**
#### **Synthetic Transaction Query (Example: API Latency Monitoring)**
**Tool:** Synthetic transaction testing tool (e.g., Datadog Synthetics, New Relic Synthetics).
**Query:**
```sql
-- Check for failed synthetic transactions (e.g., API endpoints)
SELECT
    endpoint,
    COUNT(*) as failure_count,
    AVG(duration) as avg_duration
FROM synthetic_transactions
WHERE status = 'FAILED'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY endpoint
ORDER BY failure_count DESC
LIMIT 10;
```
**Output Interpretation:**
- High `failure_count` indicates a critical endpoint degradation.
- Compare `avg_duration` with historical baselines to confirm anomalies.

#### **Anomaly Detection Alert (Example: PromQL)**
**Tool:** Prometheus.
**Query (Alert Rule):**
```yaml
groups:
- name: high-latency-alerts
  rules:
  - alert: HighApiLatency
    expr: histogram_quantile(0.99, sum(rate(api_request_duration_seconds_bucket[5m])) by (le, endpoint)) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency (> 2s) detected on {{ $labels.endpoint }}"
```

---

### **2. Diagnostic Tools**
#### **Log Analysis for Failures (Example: ELK Query)**
**Tool:** Kibana Discover.
**Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h", "lte": "now" } } }
      ]
    }
  }
}
```
**Action Items:**
- Filter by `service_name` or `exception_type` to narrow down root causes.
- Use `X-Pack` features to correlate logs with metrics/traces.

#### **Distributed Tracing Query (Example: Jaeger)**
**Tool:** Jaeger UI.
**Query:**
```bash
# Find slowest spans across a service
curl "http://jaeger:16686/search?service=payment-service&limit=100&search=duration:>500ms"
```
**Output Interpretation:**
- Identify long-duration spans (e.g., database queries) that contribute to latency.
- Check `tags` for error codes or dependency calls.

#### **Performance Benchmark Comparison (Example: PromQL)**
**Tool:** Grafana.
**Query:**
```promql
# Compare current 99th percentile latency with historical baseline
histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[1m])) -
histogram_quantile(0.99, avg_over_time(rate(api_request_duration_seconds_bucket[1m])[7d]))
```
**Threshold:**
- Alert if current value exceeds baseline by >30%.

---

### **3. Root Cause Analysis**
#### **Dependency Analysis (Example: Graph Query)**
**Tool:** Custom script (Python + NetworkX) or **Dynatrace**.
**Query (Python Example):**
```python
import networkx as nx

# Simulate dependency graph from logs/metrics
G = nx.DiGraph()
G.add_edges_from([
    ("app-service", "database"),
    ("app-service", "cache"),
    ("database", "storage")
])

# Identify single points of failure
print("Nodes with in-degree > 1 (potential bottlenecks):")
for node in G.nodes():
    if G.in_degree(node) > 1:
        print(node, G.in_degree(node))
```
**Output:**
- Nodes with high in-degree are critical dependencies requiring redundancy.

#### **Failure Mode Analysis (Example: Runbook)**
**Scenario:** Database connection pool exhaustion.
**Root Cause:**
- Unhandled connection leaks in application code.
**Mitigation Steps:**
```json
{
  "action": "increase_connection_pool_size",
  "parameters": {
    "target": "database_pool",
    "value": "100",
    "priority": "high"
  },
  "dependencies": [
    { "service": "app-service", "action": "restart" }
  ]
}
```

---

### **4. Remediation**
#### **Automated Rollback (Example: Kubernetes HPA)**
**Tool:** Kubernetes Horizontal Pod Autoscaler (HPA) + Prometheus.
**YAML Configuration:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_total
      target:
        type: AverageValue
        averageValue: 1000
```
**Trigger:**
- If `http_requests_total` > 1000 for 5m, scale to `maxReplicas`.

#### **Failover Testing Script (Example: Chaos Mesh)**
**Tool:** Chaos Mesh.
**YAML Manifest:**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: pod-network-latency
spec:
  action: delay
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: app-service
  delay:
    latency: "100ms"
    jitter: 10
  duration: "30s"
```
**Verification:**
- Monitor `error_rate` in Prometheus:
  ```promql
  sum(rate(http_requests_total{status=~"5.."}[1m])) by (service)
  ```

---

### **5. Prevention**
#### **Chaos Engineering Experiment (Example: Gremlin)**
**Tool:** Gremlin.
**Experiment:**
```bash
# Inject latency into a production service
curl -X POST http://gremlin/api/v1/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "latency-injection",
    "type": "latency",
    "target": "app-service:8080",
    "latency": 200,
    "probability": 0.3,
    "duration": "PT10M"
  }'
```
**Post-Experiment Checklist:**
1. Verify SLOs (Service Level Objectives) were met.
2. Review logs for recovered transactions.
3. Adjust failure budgets if needed.

#### **Automated Recovery Playbook (Example: Terraform + Ansible)**
**Tool:** Terraform (infrastructure) + Ansible (remediation).
**Terraform (`main.tf`):**
```hcl
resource "aws_autoscaling_group" "app_asg" {
  launch_configuration = aws_launch_configuration.app_lc.name
  min_size             = 2
  max_size             = 10
  health_check_type    = "ELB"

  lifecycle {
    create_before_destroy = true
  }
}
```
**Ansible Playbook (`recover.yml`):**
```yaml
- name: Recover from database failure
  hosts: localhost
  tasks:
    - name: Restart database pods
      community.kubernetes.k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: database
          spec:
            replicas: 3
```

---

## **Related Patterns**
1. **[Observability Pattern]**
   - *Why?* Availability troubleshooting relies on metrics, logs, and traces. This pattern provides the foundational observability stack (e.g., Prometheus, Fluentd, Jaeger).
   - *Key Integration:* Use metrics from Observability to trigger alerts in Availability Troubleshooting.

2. **[Resilience Pattern]**
   - *Why?* Resilience techniques (e.g., retries, circuit breakers) mitigate failures before they impact availability.
   - *Key Integration:* Apply resilience patterns (e.g., Hystrix, Resilience4j) to handle transient failures proactively.

3. **[Scalability Pattern]**
   - *Why?* Capacity throttling or scaling issues often cause availability degradation.
   - *Key Integration:* Use auto-scaling policies (e.g., Kubernetes HPA) as part of availability remediation.

4. **[Chaos Engineering Pattern]**
   - *Why?* Proactively tests failure scenarios to improve availability resilience.
   - *Key Integration:* Run chaos experiments during low-traffic periods to validate recovery procedures.

5. **[Site Reliability Engineering (SRE) Practices]**
   - *Why?* SRE frameworks (e.g., Google SRE Book) define SLIs, SLOs, and error budgets to quantify availability.
   - *Key Integration:* Use SLOs to prioritize troubleshooting efforts (e.g., "Fix the 99.9% uptime breach").

---

## **Best Practices**
1. **Define SLIs/SLOs:** Quantify availability goals (e.g., "99.95% uptime") to measure success.
2. **Automate Alerts:** Use multi-level alerting (e.g., warning → critical) to avoid alert fatigue.
3. **Document Failure Modes:** Maintain a runbook with step-by-step remediation for common failures.
4. **Conduct Postmortems:** After incidents, analyze root causes and update runbooks/alerts.
5. **Limit Testing Impact:** Use canary releases or staging environments for chaos experiments.