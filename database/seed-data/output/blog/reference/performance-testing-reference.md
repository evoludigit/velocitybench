# **[Pattern] Performance & Stress Testing: Reference Guide**

---

## **Overview**
Performance and stress testing patterns assess how an application behaves under **realistic loads (performance testing)** and **extreme conditions (stress testing)**. This ensures robustness, scalability, and resilience in production. The pattern covers:
- **Load testing** (simulating expected user traffic).
- **Stress testing** (pushing systems beyond normal parameters).
- **Scalability testing** (measuring horizontal/vertical growth).
- **Soak/Endurance testing** (long-duration stability checks).
- **SPIKE testing** (sudden, extreme load spikes).

This guide provides best practices for planning, execution, and analysis, ensuring reliable system performance under varying conditions.

---

## **Schema Reference**
| **Component**               | **Description**                                                                 | **Key Parameters**                                                                 | **Tools/Frameworks**                          |
|-----------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|-----------------------------------------------|
| **Load Profiles**           | Defines expected user behavior (e.g., request rates, session durations).        | RPS (requests per second), concurrent users, think time.                              | JMeter, Locust, Gatling                       |
| **Test Scenarios**          | Simulates real-world workflows (e.g., checkout, login).                        | Scenario steps, data distribution, error handling.                                   | Custom scripts, JMeter Correlated Tests      |
| **Stress Thresholds**       | Defines failure points (e.g., response time, error rates).                     | Target RT (latency), max memory usage, throughput limits.                           | New Relic, Dynatrace, custom metrics          |
| **Test Environment**        | Configures staging/cloning for accurate replication.                            | Hardware specs, network latency, database clones.                                   | Docker, Kubernetes, cloud snapshots          |
| **Metrics Collection**      | Tracks performance data during tests.                                           | CPU, memory, DB queries, HTTP status codes.                                         | Prometheus, Grafana, ELK Stack               |
| **Analysis Rules**          | Defines pass/fail criteria (e.g., 95th percentile RT < 500ms).                 | Thresholds (latency, errors), SLA deviations.                                       | Custom dashboards, alerting thresholds        |

---

## **Implementation Details**

### **1. Planning Phase**
#### **Key Activities**
- **Define Objectives**:
  - Performance goals (e.g., "Handle 10K RPS with <300ms latency").
  - Stress goals (e.g., "Recover within 2 minutes after 25K concurrent users").
- **Scope Selection**:
  - Prioritize critical user journeys (e.g., payment processing).
  - Exclude experimental features unless high-risk.
- **Tool Selection**:
  - **Open-source**: JMeter, Locust, k6.
  - **Commercial**: LoadRunner, BlazeMeter, Gatling.
  - **Cloud-based**: AWS Load Testing, Azure Load Testing.

#### **Best Practices**
- Use **historical data** to model realistic load patterns.
- Clone production-like environments (avoid stale data).
- Align tests with **SLA (Service Level Agreement)** metrics.

---

### **2. Test Design**
#### **Load Testing Scenarios**
| **Scenario**       | **Goal**                                  | **Example Metrics**                     |
|--------------------|------------------------------------------|-----------------------------------------|
| **Ramp-up Testing** | Gradually increase load to measure recovery. | Start at 100 RPS → peak at 5K RPS.      |
| **Volume Testing**  | Test system under heavy but stable load.  | 90% of max capacity for 1 hour.        |
| **Endurance Testing** | Long-duration stability.              | 24-hour continuous load at 80% capacity. |

#### **Stress Testing Scenarios**
| **Scenario**       | **Goal**                                  | **Example Metrics**                     |
|--------------------|------------------------------------------|-----------------------------------------|
| **Breakpoint Testing** | Identify failure thresholds.           | Crash point at 12K users (vs. target 10K). |
| **SPIKE Testing**   | Test recovery from sudden overload.     | 20K users for 5 minutes → drop to 1K.  |
| **Failure Injection** | Simulate component failures.           | Kill 30% of DB replicas during test.    |

#### **Data Correlation (Critical for Web Apps)**
- Replay **dynamic data** (e.g., JWT tokens, session IDs) using:
  - JMeter **CSV Data Config**.
  - Locust’s **parameterized tests**.
  - Custom scripts (Python, Java).

---

### **3. Execution**
#### **Pre-Test Checklist**
- [ ] Environment mirrors production (OS, DB, network).
- [ ] Load generators are distributed (avoid single-point failure).
- [ ] Monitoring tools are pre-configured (Prometheus, Datadog).
- [ ] Rollback plan is documented.

#### **During Test**
- **Monitor**:
  - Latency (P95/P99 percentiles).
  - Error rates (HTTP 5xx, DB timeouts).
  - Resource usage (CPU, memory, disk I/O).
- **Adjust**:
  - Dynamically scale test load if unexpected bottlenecks emerge.

#### **Post-Test**
- **Analyze**:
  - **Bottlenecks**: Slowest endpoints (via APM tools).
  - **Failures**: Error logs, DB locks, GC pauses.
- **Generate Reports**:
  - Pass/fail status per scenario.
  - Recommendations (e.g., "Optimize API v2 endpoints").

---

### **4. Optimization**
#### **Common Fixes**
| **Issue**               | **Solution**                                      | **Tools**                          |
|-------------------------|---------------------------------------------------|------------------------------------|
| High Latency            | Optimize DB queries, use caching (Redis).         | Redis, PostgreSQL Explain Analyze  |
| Memory Leaks            | Profile JVM/process memory (e.g., VisualVM).      | JProfiler, Eclipse MAT             |
| DB Overload             | Shard data, add read replicas.                   | Vitess, AWS Aurora                |
| Network Saturation      | Compress payloads, use CDN.                       | Gzip, Cloudflare                   |

#### **Iterative Improvements**
1. **Test → Debug → Fix → Retest** cycle.
2. Focus on **high-impact scenarios** first.
3. Document **baseline metrics** for future comparisons.

---

## **Query Examples**
### **1. JMeter Load Test Script (CSV-correlated)**
```groovy
// JMeter Test Plan: "E-commerce Checkout"
Config Element:
- CSV Data Config (users.csv: "user_id,product_id")
- HTTP Header Manager (Set "Authorization: Bearer ${token}")

Thread Group:
- Ramp-up: 300s
- Loop Count: 1
- Users: 1000

Samplers:
- HTTP Request: "POST /api/checkout" (Dynamic data: ${product_id})
- HTTP Request: "GET /api/order/${user_id}" (Correlated)

Listeners:
- Summary Report
- Response Time Graph
```

### **2. Locust Python Script**
```python
from locust import HttpUser, task, between

class CheckoutUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def add_to_cart(self):
        self.client.post("/api/cart", json={"item": "laptop"})

    @task(3)  # 3x more frequent than add_to_cart
    def checkout(self):
        # Dynamically pull order_id from session
        order_id = self.client.get("/api/orders").json()["latest"]
        self.client.post(f"/api/checkout/{order_id}")
```

### **3. PromQL Query (Stress Test Analysis)**
```sql
# High-latency requests (P99 > 500ms)
rate(http_request_duration_seconds_bucket{quantile="0.99"}[1m]) > 0.5

# Database query time spikes
sum(rate(postgres_query_duration_seconds_sum[5m]))
  by (query) where query =~ "SELECT .* FROM orders"

# Error rate threshold breach
increase(http_server_requests_total{status=~"5.."}[1m]) /
  increase(http_server_requests_total[1m]) > 0.05
```

---

## **Related Patterns**
1. **[Resilience Pattern]** – Complements stress testing by designing fault-tolerant systems (e.g., retries, circuit breakers).
2. **[Observability Pattern]** – Enables real-time monitoring of tests (metrics, logs, traces).
3. **[Microservices Testing]** – Stress-test individual services with contracts (e.g., API Gateway load).
4. **[Chaos Engineering]** – Extends beyond testing into deliberate failure injection (e.g., killing pods in production).
5. **[CI/CD Integration]** – Automates performance gates in pipelines (e.g., fail build if latency > threshold).

---
**Further Reading**:
- [Google SRE Book (Chapter 5: Measurement)](https://sre.google/sre-book/)
- [JMeter User’s Guide](https://jmeter.apache.org/usermanual/)
- [Locust Performance Testing](https://locust.io/)