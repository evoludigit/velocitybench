**[Pattern] Throughput Verification – Reference Guide**

---

### **Overview**
The **Throughput Verification** pattern ensures that a system, service, or component achieves and maintains target performance levels under expected load. Unlike stress testing (which explores failure states), throughput verification focuses on **steady-state behavior**—measuring consistent performance (e.g., requests/sec, transactions/sec) over time while validating:
- **Resource utilization** (CPU, memory, network).
- **Response time stability** (latency percentiles, e.g., p99).
- **Error rates** (failures, timeouts) under sustained load.

This pattern is critical for **production-grade systems**, microservices, databases, and distributed architectures. It validates:
- **Scalability** (does throughput improve with more resources?).
- **Fairness** (do all users/service types experience equitable response times?).
- **Long-term stability** (does performance degrade over time due to memory leaks, connection leaks, etc.).

Unlike load testing (which simulates peak demand), throughput verification assumes a **steady load** and measures **steady output** (e.g., "Can the system handle 1,000 requests/sec for 1 hour with <200ms p99 latency?").

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Definition                                                                 | Example                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Throughput**        | Rate of successful operations (e.g., req/sec, ops/sec) under sustained load. | "The API serves 500 requests/sec during a 30-minute test."               |
| **Steady-State Period** | Time window during which load is stable and metrics are measured.           | "Measure throughput after 5 minutes of load to avoid warm-up effects."  |
| **Baseline Metrics**  | Target values for throughput, latency, and error rates.                     | "Baseline: 1,000 req/sec, <150ms p99, <0.1% errors."                     |
| **Resource Constraints** | Limits (e.g., CPU, memory) that may impact throughput.                     | "Throughput drops when CPU exceeds 80% for >5 minutes."                  |
| **Error Boundaries**  | Acceptable failure thresholds (e.g., timeout rate, retry limits).           | "Timeouts >1% of requests trigger an alert."                            |
| **Synthetic Workload** | Programmatic load generated to simulate real-world usage.                  | Using **Locust**, **JMeter**, or **k6** to emulate user behavior at scale. |

---

### **Schema Reference**
Below is a reference schema for defining a throughput verification test:

| Field                | Type               | Description                                                                 | Required |
|----------------------|--------------------|-----------------------------------------------------------------------------|----------|
| **name**             | `string`           | Unique identifier for the test (e.g., `"order-service-throughput"`).      | Yes       |
| **description**      | `string`           | Purpose of the test (e.g., "Verify API handles 100K orders/sec").           | No        |
| **baseline**         | Object             | Target performance metrics.                                                | Yes       |
| &nbsp;&nbsp;`throughput` | `number` (req/sec) | Minimum expected throughput.                                               | Yes       |
| &nbsp;&nbsp;`latency`   | Object             | Latency percentiles (e.g., `{"p50": 50, "p99": 150}` in ms).              | Yes       |
| &nbsp;&nbsp;`error_rate` | `number` (%)       | Max allowed error rate (e.g., `0.01` = 1%).                                 | Yes       |
| **load_profile**     | Array[Object]      | User/workload scenarios with ramp-up/ramp-down phases.                     | Yes       |
| &nbsp;&nbsp;`scenario` | `string`          | Name of the workload (e.g., `"checkout-process"`).                         | Yes       |
| &nbsp;&nbsp;`r ramp_up`   | `number` (sec)     | Time to reach target load (e.g., `300` = 5 minutes).                       | Yes       |
| &nbsp;&nbsp;`target_load`| `number` (req/sec)| Peak load to simulate.                                                     | Yes       |
| &nbsp;&nbsp;`duration`   | `number` (sec)     | Test duration (e.g., `3600` = 1 hour).                                    | Yes       |
| **system_under_test** | `string`           | Target service/endpoint (e.g., `"orders-api:v2"`).                        | Yes       |
| **resources**        | Array[String]      | Constraints (e.g., `["cpu", "memory", "disk-io"]`).                       | No        |
| **pass_criteria**    | Object             | Conditions to deem the test a success.                                     | Yes       |
| &nbsp;&nbsp;`throughput_min` | `number`         | Minimum observed throughput during steady-state must ≥ `baseline.throughput`. | Yes       |
| &nbsp;&nbsp;`latency_max`  | Object            | Latency percentiles must ≤ `baseline.latency`.                           | Yes       |
| &nbsp;&nbsp;`error_max`    | `number` (%)       | Error rate must ≤ `baseline.error_rate`.                                  | Yes       |
| **steady_state_window** | `number` (sec)  | Duration to measure metrics after load stabilization.                     | Yes       |
| **alerting**         | Object             | Alert triggers for failures.                                              | No        |
| &nbsp;&nbsp;`thresholds` | Array[Object]     | Conditions for alerts (e.g., `{ "metric": "error_rate", "value": 0.02 }`). | No        |

---

## **Query Examples**
### **1. Define a Throughput Test (Schema Example)**
```json
{
  "name": "ecommerce-api-throughput",
  "description": "Verify the checkout API handles 2,000 req/sec for 1 hour.",
  "baseline": {
    "throughput": 2000,
    "latency": { "p50": 80, "p99": 200 },
    "error_rate": 0.005
  },
  "load_profile": [
    {
      "scenario": "checkout-submission",
      "ramp_up": 300,
      "target_load": 2000,
      "duration": 3600
    }
  ],
  "system_under_test": "checkout-service:latest",
  "pass_criteria": {
    "throughput_min": 2000,
    "latency_max": { "p50": 80, "p99": 200 },
    "error_max": 0.005
  },
  "steady_state_window": 1800,
  "alerting": {
    "thresholds": [
      { "metric": "latency_p99", "value": 250, "action": "escalate" },
      { "metric": "error_rate", "value": 0.01, "action": "alert" }
    ]
  }
}
```

---

### **2. Execute a Throughput Test (CLI Commands)**
#### **Using Locust (Python)**
```bash
locust -f locustfile.py \
  --host=https://api.example.com \
  --headless \
  --users=500 \
  --spawn-rate=100 \
  --run-time=3600s \
  --expect-workers=2
```
- **Key Flags**:
  - `--users`: Total concurrent users (simulate load).
  - `--spawn-rate`: Users spawned per second (controls ramp-up).
  - `--run-time`: Test duration (steady-state period).
  - `--expect-workers`: Distributed testing (if using `locust-master/worker`).

#### **Using JMeter**
1. **Define a Test Plan**:
   - **Thread Group**: Set `Users = 500`, `Ramp-Up Period = 300s`.
   - **Sampler**: Target endpoint (e.g., `POST /checkout`).
   - **Listeners**: Save latency/error metrics (e.g., "Aggregate Report").
2. **Run in Non-GUI Mode**:
   ```bash
   jmeter -n -t throughput_test.jmx -l results.jtl -e -o report
   ```
3. **Validate Results**:
   - Check `results.jtl` for throughput (req/sec) and latency percentiles.
   - Compare against `pass_criteria` in the schema.

#### **Using k6 (JavaScript)**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '300s', target: 2000 }, // Ramp-up
    { duration: '3600s', target: 2000 }, // Steady-state
    { duration: '60s', target: 0 }     // Ramp-down
  ],
  thresholds: {
    'req_duration': ['p(99)<200'],     // p99 < 200ms
    'http_req_failed': ['rate<0.005']  // Error rate <0.5%
  }
};

export default function () {
  const res = http.post('https://api.example.com/checkout', JSON.stringify({ ... }));
  check(res, {
    'status was 200': (r) => r.status === 200,
    'response time <200ms': (r) => r.timings.duration < 200
  });
}
```
Run with:
```bash
k6 run --out inflate=json3,histogram throughput_test.js
```

---

### **3. Analyze Results**
| Metric                | Tool Output Example               | Pass/Fail Logic                                  |
|-----------------------|-----------------------------------|--------------------------------------------------|
| **Throughput**        | `2012 req/sec`                    | `2012 ≥ baseline.throughput (2000)` → **Pass**    |
| **Latency (p99)**     | `198ms`                           | `198 ≤ baseline.latency.p99 (200)` → **Pass**    |
| **Error Rate**        | `0.004%`                          | `0.004 ≤ baseline.error_rate (0.005)` → **Pass** |
| **CPU Usage**         | `72%` (peaked at 85%)             | `85% > 80% threshold` → **Alert** (if configured) |

---

## **Related Patterns**
| Pattern                  | Description                                                                 | When to Use With Throughput Verification |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **[Load Testing]**       | Simulates peak load to identify failure points.                            | Use before throughput testing to find max capacity. |
| **[Stress Testing]**     | Pushes system beyond limits to observe degradation/failure.                | Use to validate recovery from overload.     |
| **[Chaos Engineering]**  | Introduces random failures to test resilience.                            | Use to verify throughput under failure conditions. |
| **[Canary Testing]**     | Gradually rolls out changes to a subset of users.                          | Verify throughput impact of new features.   |
| **[Performance Budgeting]** | Defines acceptable performance targets for teams.                        | Align throughput tests with budgeted SLAs.    |

---

### **Best Practices**
1. **Isolate Tests**: Run throughput tests in **dedicated environments** (not staging/prod).
2. **Warm-Up**: Use a warm-up phase (e.g., 5 minutes) to avoid cold-start latency.
3. **Distributed Load**: Use tools like **Locust distributed** or **Gatling** for scale.
4. **Monitor Resources**: Correlate throughput with CPU/memory/disk I/O.
5. **Automate Alerts**: Integrate with **Prometheus/Grafana** or **Slack** for real-time alerts.
6. **Reproducible Load**: Define **synthetic user behavior** (e.g., think time, request patterns).
7. **Long-Duration Tests**: Run overnight to catch gradual degradation (e.g., memory leaks).

---
### **Anti-Patterns to Avoid**
- ❌ **Ignoring Steady-State**: Measuring metrics during ramp-up/down distorts results.
- ❌ **Overloading the System**: Stress testing ≠ throughput testing; don’t sacrifice stability.
- ❌ **Neglecting Real-World Traffic**: Use **historical data** to model realistic workloads.
- ❌ **Hardcoding Thresholds**: Baselines should adapt to **environment changes** (e.g., AWS vs. on-prem).

---
**References:**
- [Locust Documentation](https://locust.io/)
- [k6 Performance Testing](https://k6.io/docs/)
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/table-of-contents/) (Chap. 5: Measuring Success)