# **[Pattern] Load & Stress Testing Reference Guide**

---

## **Overview**
Load & Stress Testing is a performance testing pattern designed to validate system behavior under **extreme load conditions**, ensuring stability, reliability, and scalability. Unlike functional testing—which verifies correctness—this pattern focuses on **performance bottlenecks, resource limits, and failure resilience**. It includes **stress testing** (pushing systems to failure) and **load testing** (simulating production traffic), helping teams identify weaknesses before deployment. Key goals include:
- Detecting **latency spikes, memory leaks, or cascading failures**.
- Estimating **scalability thresholds** (e.g., peak user demand).
- Validating **recovery mechanisms** post-crash.
- Optimizing **resource allocation** (CPU, memory, network).

This guide outlines **implementation steps, tooling, metrics, and best practices** to execute effective tests.

---

## **Schema Reference**

| **Component**          | **Description**                                                                 | **Key Metrics**                          | **Tools/Libraries**                     |
|-------------------------|-------------------------------------------------------------------------------|------------------------------------------|------------------------------------------|
| **Test Environment**    | Isolated, isolated staging or cloud-based replica mirroring production.        | Resource isolation (CPU, RAM, storage). | AWS CloudFormation, Docker, Kubernetes, Terraform |
| **Load Generator**      | Tools/agents simulating concurrent users, requests, or transactions.         | Requests/sec (RPS), concurrency levels.  | JMeter, Gatling, Locust, k6, Siege       |
| **Target System**       | Application, API, database, or microservice under test.                       | Latency (P99, avg), error rates.        | Custom apps, REST APIs, gRPC, Kafka      |
| **Monitoring Stack**    | Real-time observability for metrics, logs, and traces.                        | CPU %, memory usage, throughput.         | Prometheus, Grafana, ELK, Datadog, New Relic |
| **Test Scenario**       | Defined workflows (e.g., "Checkout Process under 10K users").                | Transaction success rate, failure modes.| JMeter scripts, custom scripts            |
| **Stress Triggers**     | Sudden spikes (e.g., 1K->50K users in 1 min) or sustained heavy load.        | Crash time, recovery time.               | Custom ramp-up, chaos engineering tools  |
| **Result Analysis**     | Post-test review of performance, failures, and thresholds.                     | Threshold breaches, bottleneck analysis. | Custom reports, GitHub Actions, Jenkins  |

---

## **Implementation Details**

### **1. Define Test Objectives**
Clarify goals before testing:
- **Load Testing**: Simulate expected production traffic (e.g., 5K concurrent users).
- **Stress Testing**: Push beyond normal limits (e.g., 10K+ users to break the system).
- **Spike Testing**: Sudden traffic surges (e.g., Black Friday promotions).
- **Soak Testing**: Long-duration load to check for leaks (e.g., 24-hour continuous run).

**Example Objectives**:
> *"Load-test the checkout API to handle 5K concurrent users with <500ms P99 latency.*
> *Stress-test the database to identify query timeouts under 100K concurrent reads."*

---

### **2. Set Up the Test Environment**
#### **Infrastructure Requirements**:
- **Isolation**: Deploy tests in a **separate cluster** (avoid polluting production).
- **Scalability**: Use auto-scaling groups (AWS ASG), Kubernetes HPA, or serverless (AWS Lambda) for load generators.
- **Network**: Ensure low-latency connections between generators and targets.

#### **Hardware/Cloud Setup**:
| **Resource**       | **Recommendation**                                                                 |
|---------------------|-----------------------------------------------------------------------------------|
| **Load Generator**  | Clustered VMs (e.g., 10x m5.large EC2 instances) or serverless (AWS Lambda).      |
| **Target System**   | Replica of production (same OS, DB version, cache layers).                       |
| **Monitoring**      | Centralized logging (ELK) + metrics (Prometheus) + synthetic monitoring (Synthetics). |

---

### **3. Design Test Scenarios**
#### **Load Test Example (E-commerce Site)**:
| **Phase**       | **Action**                          | **Concurrency** | **Duration** | **Goal**                          |
|------------------|-------------------------------------|-----------------|--------------|-----------------------------------|
| **Ramp-up**      | Gradually increase users to 5K      | 0 → 5K          | 5 min        | Smooth scaling                   |
| **Stable Load**  | Hold 5K users for 1 hour            | 5K              | 1 hour       | Check memory leaks, CPU usage    |
| **Peak Load**    | Spike to 10K users (30% increase)   | 10K             | 10 min       | Validate auto-scaling             |
| **Recovery**     | Drop load to 2K users               | 10K → 2K        | 5 min        | Test graceful degradation        |

#### **Stress Test Example (Database)**:
- Gradually increase **read/write queries** until:
  - Response time > 2s (50% of queries).
  - Database crashes or requires manual restart.
- **Goal**: Identify **query bottlenecks** or **connection pool exhaustion**.

---

### **4. Toolchain Selection**
| **Tool**          | **Best For**                          | **Key Features**                          |
|--------------------|---------------------------------------|-------------------------------------------|
| **JMeter**         | Load testing (HTTP, JMS, databases).   | Highly customizable, distributed testing. |
| **Gatling**        | Scalable, script-based load tests.     | Elastic load, real-time dashboard.        |
| **k6**             | Developer-friendly, scriptable.        | Supports HTTP, WebSockets, custom metrics.|
| **Locust**         | Python-based, easy parallel test gen. | Dynamic users, distributed mode.          |
| **Grafana/Loki**   | Visualizing metrics/logs.              | Dashboards for latency, error rates.      |
| **k6 Cloud**       | Cloud-hosted load testing.            | No infrastructure setup.                  |

**Example k6 Script Snippet**:
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 100 },  // Ramp-up
    { duration: '1m', target: 1000 }, // Steady state
    { duration: '30s', target: 0 },   // Ramp-down
  ],
};

export default function () {
  const res = http.get('https://api.example.com/items');
  check(res, {
    'Status is 200': (r) => r.status === 200,
    'Latency < 500ms': (r) => r.timings.duration < 500,
  });
}
```

---

### **5. Key Metrics to Track**
| **Category**          | **Metric**               | **Threshold**               | **What It Indicates**                     |
|-----------------------|--------------------------|-----------------------------|------------------------------------------|
| **Performance**       | P99 Latency              | < 500ms                     | 99% of requests complete fast.           |
|                       | Requests/sec (RPS)       | Stable under peak load.     | System throughput.                       |
| **Resource Usage**    | CPU Utilization          | < 80% (avoid throttling).   | Bottlenecks in compute.                  |
|                       | Memory Leak Rate         | < 5% growth per hour.       | Memory exhaustion risk.                  |
| **Error Resilience**  | Error Rate               | < 1%                        | System stability.                        |
|                       | Crash Frequency          | 0 crashes per test.         | Stability under stress.                  |
| **Scalability**       | Auto-scaling Events      | Minimal manual intervention.| Cloud resource efficiency.               |

---

### **6. Execute and Analyze**
#### **Test Execution**:
1. **Deploy the load generator** (e.g., 10x JMeter agents).
2. **Run the scenario** (monitor via Grafana/Prometheus).
3. **Capture metrics** (latency, errors, CPU) in real-time.

#### **Post-Test Analysis**:
- **Identify Bottlenecks**:
  - High latency? Check **database queries** or **third-party APIs**.
  - Memory leaks? Use **heap dumps** (Java) or **Valgrind** (C++).
- **Thresholds**:
  - If P99 latency spikes > 2s during load, **optimize caching** or **scale DB reads**.
- **Recovery Testing**:
  - After a crash, does the system **auto-recover**? Test **failover mechanisms**.

**Example Failure Mode**:
> *During stress testing, the API returns 503 errors after 8K concurrent users. Investigation reveals:*
> - **Root Cause**: Redis cache nodes overwhelmed.
> - **Fix**: Increase Redis cluster size + add circuit breakers.

---

### **7. Best Practices**
| **Best Practice**               | **Action Item**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|
| **Start Small**                  | Begin with 10% of expected peak load to validate setup.                         |
| **Use Realistic Data**           | Load test with **production-like payloads** (e.g., real user sessions).        |
| **Distributed Testing**          | Run generators **globally** to simulate edge cases (e.g., users in APAC vs. EMEA). |
| **Chaos Engineering**            | Inject failures (e.g., kill DB pods) to test resilience.                        |
| **Automate Reporting**           | Generate **PDF/Slack alerts** post-test with key metrics.                       |
| **Test Edge Cases**              | Cold starts, network partitions, or sudden traffic drops.                      |

---

## **Query Examples**
### **1. JMeter Groovy Script to Simulate User Sessions**
```groovy
import org.apache.jmeter.protocol.java.sampler.JSR223Sampler;
import org.apache.jmeter.protocol.java.sampler.JSR223SamplerContext;

def sampler = new JSR223Sampler();
sampler.setName("UserSessionTest");

sampler.setParameter(
    "code",
    """
    // Simulate 3-step checkout flow
    def baseUrl = "https://api.example.com";
    def steps = [
        "GET ${baseUrl}/cart",
        "POST ${baseUrl}/checkout?step=1",
        "POST ${baseUrl}/checkout?step=2",
        "POST ${baseUrl}/checkout?step=3"
    ];

    steps.each { step ->
        def res = httpRequest(samplerContext, step);
        samplerContext.variables.put("result_${step}", res);
    }
    """
);
```

### **2. PromQL Query for Latency percentiles**
```promql
# P99 latency for the /api/v1/items endpoint
rate(http_request_duration_seconds_bucket{uri="/api/v1/items"}[1m])
unless (rate(http_request_duration_seconds_bucket{uri="/api/v1/items",code=~"5.."}[1m]))
/ sum(
    rate(http_request_duration_seconds_bucket{uri="/api/v1/items"}[1m])
    unless (rate(http_request_duration_seconds_bucket{uri="/api/v1/items",code=~"5.."}[1m]))
)
by (le)
* on (le) group_left(uri) max(
    rate(http_request_duration_seconds_bucket{uri="/api/v1/items",le=~"0.5|1|2"}[1m])
    unless (rate(http_request_duration_seconds_bucket{uri="/api/v1/items",code=~"5..",le=~"0.5|1|2"}[1m]))
) by (uri)
```
*Trigger alert if P99 > 500ms for >5 minutes.*

### **3. k6 Command to Test API Endpoint**
```bash
k6 run \
  --vus 1000 \          # Virtual users
  --duration 1m \       # Test duration
  --out influxdb=http://localhost:8086/k6  \  # Export metrics
  load_test.js
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Chaos Engineering]**    | Deliberately introduce failures to test resilience.                            | Post-load testing to validate recovery.  |
| **[Canary Releases]**     | Gradually roll out changes to a subset of users.                                | Reduce risk during performance-critical updates. |
| **[Monitoring & Observability]** | Centralized metrics, logs, and traces for real-time insights.              | Required for Load/Stress Testing analysis. |
| **[Auto-scaling]**        | Dynamically adjust resources based on load.                                    | Critical for horizontal scaling under load. |
| **[Benchmarking]**        | Measure baseline performance for comparison.                                   | Pre-test to establish "healthy" metrics. |

---
**Next Steps**:
1. **Integrate testing into CI/CD** (e.g., Jenkins pipeline).
2. **Document failure modes** and fixes in a runbook.
3. **Re-test after fixes** to validate improvements.