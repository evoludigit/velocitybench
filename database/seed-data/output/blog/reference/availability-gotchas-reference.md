# **[Pattern] Availability Gotchas Reference Guide**

---

## **Overview**
The **Availability Gotchas** pattern identifies subtle, often overlooked challenges that can undermine system reliability, performance, or user experience even when core infrastructure appears stable. These "gotchas" frequently stem from misconfigured dependencies, cascading failures, throttling limits, race conditions, or hidden latency, leading to unexpected downtime or degraded availability. Unlike traditional failure modes, these issues often manifest under non-critical loads or during transitions (e.g., scaling events, configuration changes, or user spikes), making them harder to detect in pre-production testing. This guide categorizes common pitfalls, their root causes, mitigation strategies, and detection techniques, with a focus on cloud-native systems, microservices architectures, and distributed applications.

---

## **Key Concepts & Implementation Details**

### **Core Definitions**
| Term | Definition |
|------|------------|
| **Availability Gotcha** | A non-obvious failure mode that reduces system availability beyond expected SLAs, often triggered by edge cases or interactions between components. |
| **Thundering Herd** | A surge in concurrent requests (e.g., after a cache miss or failover) overwhelming a system, causing cascading failures. |
| **Sticky Session Conflict** | Race conditions in session affinity where requests are unexpectedly routed to overloaded instances. |
| **Dependency Cascading** | A failure in dependent services (e.g., databases, APIs) propagating to primary services, exacerbating latency or downtime. |
| **Cold Start Latency** | Delays in provisioning resources (e.g., VMs, containers) during autoscaling, causing brief unavailability. |
| **Throttling Backlog** | Queued requests during rate-limiting, leading to delayed processing and perceived downtime. |
| **Configuration Drift** | Inconsistent settings across instances or environments, causing inconsistent behavior (e.g., retry policies, timeouts). |

### **Common Categories of Gotchas**
| Category | Description | Example Scenarios |
|----------|-------------|-------------------|
| **Scaling & Autoscaling** | Issues arising from dynamic resource allocation (e.g., warm-up delays, uneven scaling). | Autoscaling group under-provisioning during traffic spikes; cold starts in serverless functions. |
| **Networking & Connectivity** | Latency, packet loss, or partitions affecting availability. | Region failover delays; DNS propagation gaps. |
| **State Management** | Race conditions or inconsistencies in distributed state (e.g., sessions, locks). | Sticky session timeouts; distributed cache stampedes. |
| **API & Dependency Limits** | External API throttling, quotas, or cascading failures. | Third-party API rate-limiting causing downstream outages. |
| **Monitoring & Observability Gaps** | Missing alerts or metrics for edge-case failures. | Unmonitored database connection pool exhaustion. |
| **Configuration & Deployment** | Misconfigurations or rollout errors affecting availability. | Incorrect retry policies; failed feature flag toggles. |

---

## **Schema Reference**
Below is a **reference schema** for documenting availability gotchas in your system. Use this template to log incidents or preemptively identify risks.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| **Gotcha ID** | String (UUID) | Unique identifier for the gotcha. | `GOT-2023-0042` |
| **Category** | Enum | Predefined categories (e.g., `Scaling`, `Networking`, `State`). | `Scaling` |
| **Title** | String | Concise description of the issue. | "Autoscaling Group Cold Start Latency" |
| **Root Cause** | String | Technical explanation (e.g., "Inadequate warm-up pools"). | "VM instances in autoscaling groups have no prior traffic, causing 30s+ cold start delays." |
| **Impact** | String | SLAs affected (e.g., "99.9% → 99.5% availability"). | "Increased latency spikes during scaling events; potential 5xx errors during traffic surges." |
| **Trigger Conditions** | Array | Scenarios that activate the gotcha. | `[{ "event": "TrafficSpike", "threshold": "5000+ RPS" }]` |
| **Detection Methods** | Array | Tools/techniques to identify the issue. | `[{ "metric": "aws.ec2.cpu.utilization", "threshold": ">80% for 5m" }, { "tool": "Prometheus Alertmanager" }]` |
| **Mitigation Strategies** | Array | Fixes or workarounds. | `[{ "action": "Pre-warm instances", "implementation": "AWS Compute Optimizer" }, { "action": "Adjust autoscaling cooldown", "value": "300s" }]` |
| **Severity** | Enum | (`Low`, `Medium`, `High`, `Critical`) | `High` |
| **Status** | Enum | (`Open`, `Resolved`, `Mitigated`) | `Mitigated` |
| **Affected Components** | Array | Services/modules impacted. | `["API Gateway", "Order Service", "Database Proxy"]` |
| **References** | Array | Links to docs, tickets, or related incidents. | `[{ "url": "https://aws.amazon.com/autoscaling/cooldown/", "type": "AWS Docs" }]` |
| **Last Reviewed** | Date (ISO) | Date of last validation. | `2023-11-15` |
| **Owner** | String | Team/accountable for resolution. | `"SRE Team"`

---

## **Query Examples**
Use these **query patterns** (in SQL, PromQL, or CI/CD pipelines) to detect availability gotchas proactively.

---

### **1. Detecting Thundering Herd in Caching Layers**
**Tool:** PromQL (for Redis/Memcached)
**Query:**
```promql
# Cache miss ratio spiking during traffic events
increase(redis_keyspace_hits_total[1m]) / increase(redis_keyspace_misses_total[1m]) < 0.1
AND
rate(http_requests_total{path=~"/api/*"}[1m]) > 1000

# Alert if cache miss ratio drops below 10% (indicating stampede)
ALERT CacheStampede
  IF (1 - (rate(redis_keyspace_hits_total[1m]) / null(rate(redis_keyspace_misses_total[1m] + 0.001)))) > 0.9
  FOR 5m
  LABELS {severity="high"}
```

**Mitigation:**
- Implement **token bucket** or **reservation systems** (e.g., Redis `reservations`).
- Use **local cache invalidation** to prevent global stampedes.

---

### **2. Identifying Cold Start Delays in Serverless**
**Tool:** AWS CloudWatch (Lambda)
**Query:**
```sql
-- SQL-like pseudocode for CloudWatch Logs
SELECT
  duration,
  invoked_function_arn,
  COUNT(*) as cold_start_count
FROM cloudwatch_logs
WHERE log_stream LIKE '%Lambda/Execution/%'
  AND duration > 1000  -- >1s latency
  AND error_code IS NULL
GROUP BY invoked_function_arn
HAVING COUNT(*) > 5  -- Threshold for concern
ORDER BY cold_start_count DESC;
```

**Mitigation:**
- **Provisioned Concurrency**: Pre-warm instances for critical functions.
- **Optimize Dependencies**: Reduce package size (e.g., tree-shake Node.js dependencies).
- **Monitor**: Set alerts for `Duration > 1s` (CloudWatch Lambda Insights).

---

### **3. Detecting Sticky Session Conflicts**
**Tool:** Kubernetes (if using session affinity) or ELB Metrics
**Query (PromQL for ALB):**
```promql
# Session count disparities across targets
sum by(backend) (alb_http_server_timed_out_total) > 0
AND
(sum by(backend) (alb_http_request_count{http_code=~"2.."}) /
 sum by(backend) (alb_http_request_count)) < 0.8  -- <80% traffic share
```

**Mitigation:**
- **Disable sticky sessions** or use **hash-based routing** to distribute load.
- **Retry logic**: Configure clients to retry with a different instance on 5xx errors.

---

### **4. Catching Dependency Throttling Backlogs**
**Tool:** OpenTelemetry or AWS X-Ray
**Query (OpenTelemetry Trace Query):**
```sql
SELECT
  service_name,
  COUNT(*) as backlogged_requests,
  AVG(duration) as avg_latency
FROM traces
WHERE
  status_code = "ERROR"
  AND error_type = "RateLimitExceeded"
  AND timestamp > now() - 1h
GROUP BY service_name
HAVING COUNT(*) > 100
ORDER BY avg_latency DESC;
```

**Mitigation:**
- **Implement exponential backoff** in client retries.
- **Queue requests**: Use SQS or Kafka to buffer during throttling.
- **Monitor**: Set alerts for `error_type="RateLimitExceeded"` (e.g., AWS CloudWatch for API Gateway).

---

### **5. Configuring Drift Detection**
**Tool:** Terraform + Custom Scripts
**Query (Python pseudocode for config drift):**
```python
import requests
import yaml

# Fetch live config from API
live_config = requests.get("http://config-center/api/v1/config").json()

# Compare with expected (e.g., from Git)
expected_config = yaml.safe_load(open("expected_config.yaml"))

# Flag mismatches
diffs = set(live_config.keys()) ^ set(expected_config.keys())
for key in diffs:
  print(f"Config drift detected: {key} (live: {live_config.get(key)}, expected: {expected_config.get(key)})")
```

**Mitigation:**
- **Automate drift correction** (e.g., GitOps tools like ArgoCD).
- **Alert on drift**: Integrate with PagerDuty for immediate action.

---

## **Related Patterns**
| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Prevents cascading failures by halting traffic to failing dependencies. | Mitigate dependency throttling backlogs. |
| **[Bulkhead](https://microservices.io/patterns/reliability/bulkhead.html)** | Isolates components to limit resource contention (e.g., thread pools). | Prevent thundering herds in stateful services. |
| **[Retries with Backoff](https://cloud.google.com/blog/products/devops-sre/exponential-backoff-and-jitter)** | Gradually retries failed requests to avoid retry storms. | Handle transient network errors or throttling. |
| **[Chaos Engineering](https://principlesofchaos.org/)** | Proactively tests failure modes to identify gotchas. | Validate resilience during scaling or discovery events. |
| **[Rate Limiting](https://www.awsarchitectureblog.com/2023/01/designing-rate-limited-systems.html)** | Controls request volume to prevent overload. | Protect APIs from thundering herds. |
| **[Service Mesh (e.g., Istio)](https://istio.io/latest/docs/concepts/traffic-management/)** | Manages traffic, retries, and circuit breaking at the network layer. | Complex distributed systems with many dependencies. |

---

## **Best Practices for Documentation**
1. **Log Gotchas**: Maintain a **gotcha database** (e.g., GitHub Issues, Confluence) with the schema above.
2. **Postmortems**: Include gotchas in incident retrospective reports to improve future detection.
3. **Automate Alerts**: Use tools like **Grafana Alerts**, **AWS CloudWatch**, or **Prometheus** to monitor for gotcha conditions.
4. **Run Chaos Experiments**: Simulate gotcha triggers (e.g., kill pods, throttle networks) to validate mitigations.
5. **Share Knowledge**: Add gotchas to **runbooks** and **onboarding docs** for new engineers.

---
**Example Gotcha Log Entry**:
```json
{
  "id": "GOT-2023-0042",
  "category": "Scaling",
  "title": "Autoscaling Group Cold Start Latency",
  "root_cause": "AWS Auto Scaling Groups lack pre-warm traffic, causing 30s cold starts for new instances.",
  "impact": "Increased latency during traffic spikes; potential 5xx errors if instances are slow to initialize.",
  "trigger_conditions": [
    {"event": "TrafficSpike", "threshold": "5000+ RPS", "time_window": "5m"}
  ],
  "detection_methods": [
    {"metric": "aws.ec2.cpu_credits_balance", "threshold": "< 5000", "tool": "CloudWatch"}
  ],
  "mitigation_strategies": [
    {"action": "Enable Provisioned Concurrency", "implementation": "AWS Lambda"},
    {"action": "Adjust autoscaling cooldown", "value": "300s"}
  ],
  "severity": "High",
  "status": "Mitigated",
  "affected_components": ["Order Service", "Payment Gateway"]
}
```

---
**Key Takeaway**: Availability gotchas are inevitable in distributed systems, but **proactive detection**, **structured documentation**, and **automated mitigations** can minimize their impact. Regularly review this guide and update it with new discoveries.