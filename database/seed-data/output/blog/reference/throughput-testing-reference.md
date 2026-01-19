---
# **[Pattern] Throughput Testing Reference Guide**

---

## **Overview**
Throughput testing evaluates how a system performs under **a sustained, high-volume workload** to measure its ability to process requests over time. Unlike load testing (which focuses on peak capacity) or stress testing (which identifies breaking points), throughput testing assesses **steady-state performance**, scalability, and efficiency under prolonged load.

This pattern is critical for:
- **Performance optimization** of long-running applications (e.g., financial systems, e-commerce platforms).
- **Resource allocation** (CPU, memory, I/O) to prevent bottlenecks.
- **Benchmarking** against service-level agreements (SLAs) (e.g., "Handle 10,000 requests/second with <200ms latency").

Key metrics include:
- **Requests/second (RPS)** – Sustainable workload capacity.
- **Latency (P99, P95, Avg.)** – Response times under sustained load.
- **Resource utilization** – CPU, memory, disk I/O, network bandwidth.
- **Error rates** – % of failed requests during prolonged testing.

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Example Values**                          | **Tools/Metrics**                     |
|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------|---------------------------------------|
| **Workload Profile**        | Defines the test scenario (e.g., user actions, data volume, concurrency).      | 10K concurrent users, 50% checkout events.  | JMeter, Locust, Gatling.               |
| **Load Generator**          | Simulates concurrent users/requests to mimic real-world traffic.              | Virtual users (VUs), requests per minute.  | New Relic, k6, Tsung.                 |
| **Test Duration**           | How long the test runs to evaluate sustained performance.                      | 1 hour, 12 hours, 24+ hours.               | Custom scripts, CI/CD pipelines.      |
| **Response Metrics**        | Tracks latency, throughput, and error rates during the test.                  | P99: 300ms, Errors: 0.5%, Throughput: 8K RPS. | Prometheus, Grafana, Datadog.        |
| **Resource Monitors**       | Logs system-level metrics (CPU, memory, disk, network) during testing.         | CPU: 85%, Memory: 64GB, Disk I/O: 120MB/s.  | Nagios, Zabbix, AWS CloudWatch.       |
| **Throttling Rules**        | Controls ramp-up, ramp-down, or steady-state load to avoid system overload.     | Linear ramp-up (5K VUs/hr), steady for 2hr.  | JMeter, k6 built-in throttling.       |
| **Data Volume**             | Simulates real-world data patterns (e.g., 10GB/sec transactions).             | Database reads/writes, API payload sizes.   | MongoDB Atlas, AWS DynamoDB.          |
| **Validation Scripts**      | Checks for correctness (e.g., business logic, data integrity) under load.      | API responses, transaction success rates.  | Postman, Selenium, custom assertions. |
| **Alerting Thresholds**     | Defines failure conditions (e.g., "Latency > 500ms for 5 mins triggers alert"). | `IF (latency_p99 > 500ms) THEN notify().` | PagerDuty, Slack, Opsgenie.            |

---

## **Implementation Details**

### **1. Define Test Objectives**
Clarify goals before implementation:
- **SLA Compliance**: "Can the system handle 5K RPS with <10% error rate?"
- **Resource Stress Testing**: "What’s the CPU threshold before degradation?"
- **Scalability Limits**: "How does throughput change with added nodes?"

**Best Practice**:
Use the **80/20 rule**—prioritize high-impact workloads (e.g., checkout flows vs. static content).

---

### **2. Workload Design**
#### **A. Request Patterns**
| **Pattern**               | **Use Case**                                  | **Tools**                          |
|---------------------------|-----------------------------------------------|------------------------------------|
| **Constant Throughput**   | Simulate steady traffic (e.g., 24/7 services). | JMeter, k6.                        |
| **Ramp-Up/Down**          | Gradually increase load to avoid spikes.      | Gatling, LoadRunner.               |
| **Soak Testing**          | Extended testing (e.g., 12+ hours) for leaks. | Custom scripts, Docker + Kafka.    |
| **Skewed Workloads**      | Model real-world bursts (e.g., Black Friday). | Locust, Tsung.                     |

#### **B. Data Realism**
- **Database**: Use realistic schemas (e.g., 80% reads, 20% writes).
- **Payloads**: Mirror production data sizes (e.g., JSON payloads of ~1KB).
- **User Behavior**: Add delays between actions (e.g., "users take 2 sec to click 'Buy'").

**Example Data Profile**:
```json
{
  "users": 10000,
  "actions": [
    {"type": "product_view", "delay": 1.5},
    {"type": "checkout", "delay": 5}
  ],
  "data_volume": "10GB/database_transactions"
}
```

---

### **3. Tools & Infrastructure**
| **Tool**          | **Purpose**                                      | **Pros**                          | **Cons**                          |
|--------------------|--------------------------------------------------|-----------------------------------|-----------------------------------|
| **JMeter**         | Java-based load testing with plugins.            | Open-source, GUI-friendly.        | Steeper learning curve.           |
| **k6**             | Developer-friendly, scriptable (JavaScript).      | Cloud-ready, real-time metrics.   | Limited advanced features.        |
| **Gatling**        | High-performance Scala-based tester.             | Great for HTTP/REST APIs.         | Less support for complex protocols.|
| **Locust**         | Python-based, scalable with distributed workers. | Easy to extend.                   | Less polished UI.                 |
| **Grafana + Prom** | Visualize metrics in real-time.                  | Dashboards, alerts.               | Requires setup.                   |

**Infrastructure**:
- **Cloud**: AWS/GCP load balancers for distributed testing.
- **On-Prem**: Kubernetes clusters for scaling generators.
- **Database**: Mock services (e.g., Mockoon) or real replicas.

---

### **4. Execution & Monitoring**
#### **A. Phases**
1. **Ramp-Up**: Gradually increase load (e.g., 1K → 10K VUs over 30 mins).
2. **Steady-State**: Maintain load for 1–24 hours (monitor metrics).
3. **Ramp-Down**: Slowly decrease load to analyze recovery.

#### **B. Key Metrics to Track**
| **Metric**               | **Threshold**               | **Tools**                     |
|--------------------------|-----------------------------|-------------------------------|
| **Throughput (RPS)**     | Should stabilize ≥80% of max.| Prometheus, Grafana.          |
| **Latency (P99)**        | ≤500ms (adjust per SLA).    | New Relic, k6 built-in.       |
| **Error Rate**           | <1% failed requests.        | JMeter assertions, Datadog.   |
| **Resource Utilization** | CPU < 90%, Memory < 85%.   | CloudWatch, Zabbix.           |
| **Queue Lengths**        | No spikes in DB/API queues. | ELK Stack, Grafana.           |

#### **C. Alerting Rules**
```yaml
# Example Prometheus alert for throughput degradation
- alert: HighLatency
  expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 0.5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "P99 latency exceeded 500ms"
```

---

### **5. Analysis & Reporting**
#### **Pass/Fail Criteria**
| **Metric**       | **Pass**                          | **Fail**                          |
|------------------|-----------------------------------|-----------------------------------|
| Throughput       | ≥90% of target RPS sustained.     | <80% for >2 consecutive minutes.  |
| Latency          | P99 < 500ms (adjust per SLA).     | P99 spikes > 1s for 1 minute.    |
| Errors           | <1% error rate.                   | >2% errors for >5 minutes.        |
| Resource Leaks   | No memory leaks, CPU stable.      | Exponential growth in any metric.|

#### **Report Template**
```markdown
## Throughput Test Report: [Date]
**System**: E-commerce API
**Test Duration**: 3 hours
**Load**: 8,000 VUs (50% checkout, 50% browse)

| Metric          | Target   | Actual   | Status   |
|-----------------|----------|----------|----------|
| RPS             | 8,000    | 7,950    | ✅ Pass  |
| Latency P99     | <500ms   | 450ms    | ✅ Pass  |
| Error Rate      | <1%      | 0.3%     | ✅ Pass  |
| CPU Usage       | <85%     | 82%      | ✅ Pass  |

**Bottlenecks**:
- Database queries under 200ms (10% degradation at peak).
- Recommend: Add read replicas.

**Attachments**:
- Grafana dashboards
- JMeter test logs
- Screenshot of alerts
```

---

## **Query Examples**
### **1. JMeter Test Plan (XML Snippet)**
```xml
<TestPlan>
  <ThreadGroup>
    <ThreadName>ThroughputTest</ThreadName>
    <NumThreads>8000</NumThreads>
    <RampUp>3600</RampUp> <!-- 1 hour ramp-up -->
    <LoopCount>1</LoopCount>
  </ThreadGroup>
  <Sampler>
    <HTTPSampler>
      <Name>ProductCheckout</Name>
      <URL>/api/checkout</URL>
      <ThreadCounts>8000</ThreadCounts>
    </HTTPSampler>
  </Sampler>
  <Listener>
    <AggregateReport/>
  </Listener>
</TestPlan>
```

### **2. k6 Script (JavaScript)**
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

const VUS = 1000;
const DURATION = '3600s'; // 1 hour

export const options = {
  vus: VUS,
  duration: DURATION,
  thresholds: {
    'http_req_duration': ['p(99) < 500'],
    'throughput': ['avg>8000'], // Target RPS
  },
};

export default function () {
  const res = http.post('https://api.example.com/checkout', JSON.stringify({ items: 3 }));
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1); // Simulate user delay
}
```

### **3. PromQL Query for Throughput**
```promql
# Requests per second (RPS) over time
rate(http_request_duration_seconds_count[1m])

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_request_failed_total[1m])) by (path) / sum(rate(http_request_duration_seconds_count[1m])) by (path)
```

---

## **Related Patterns**
1. **[Load Testing]**
   - Focuses on **peak capacity** (spikes, sudden surges) vs. throughput’s steady-state.
   - Use for **stress testing** (e.g., "How many users before the system crashes?").

2. **[Stress Testing]**
   - Identifies **breaking points** under extreme load.
   - Complements throughput by revealing fragilities not caught in sustained testing.

3. **[Canary Testing]**
   - Gradually rolls out changes under **real-world traffic** to monitor throughput impacts.
   - Example: Deploy new API version to 10% of users first.

4. **[Database Performance Tuning]**
   - Optimizes queries and indexes to **sustain high throughput**.
   - Tools: `EXPLAIN ANALYZE`, database profiling.

5. **[Auto-Scaling]**
   - Dynamically adjusts resources (e.g., Kubernetes HPA) to **maintain throughput** during load spikes.

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                      | **Fix**                                  |
|---------------------------------|-----------------------------------------------|------------------------------------------|
| **Testing Only at Peak Hours**  | Misses resource leaks under sustained load.   | Run tests during off-peak + extended soak.|
| **Ignoring Data Skew**          | Real-world data isn’t uniformly distributed.  | Use realistic datasets (e.g., power-law distributions). |
| **No Alerting**                | Bottlenecks go undetected until it’s too late.| Set up real-time alerts for thresholds.  |
| **Overlooking External Dependencies** | DB/API timeouts degrade throughput.       | Test with mock services or real replicas. |

---
**Next Steps**:
- Start with **soak tests** (12+ hours) to catch memory leaks.
- Use **distributed load generators** for large-scale tests.
- Correlate throughput data with **business metrics** (e.g., "How does checkout throughput affect revenue?").

---
**Tools Checklist**:
| **Phase**       | **Tools**                          |
|------------------|------------------------------------|
| Design           | JMeter, k6, Locust                 |
| Execution        | Kubernetes, AWS/GCP load balancers  |
| Monitoring       | Prometheus, Grafana, Datadog       |
| Alerting         | PagerDuty, Slack, Opsgenie         |
| Analysis         | custom scripts, ELK Stack          |