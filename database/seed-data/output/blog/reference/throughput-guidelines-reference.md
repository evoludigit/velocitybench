# **[Pattern] Throughput Guidelines Reference Guide**

---

## **1. Overview**
The **Throughput Guidelines** pattern standardizes performance expectations for systems by defining **target throughput ranges** (e.g., requests per second, transactions per minute) for different workloads, environments, and failure conditions. This ensures predictable behavior, helps capacity planning, and enables proactive scaling.

Throughput guidelines apply to:
- **APIs and microservices** (REST, gRPC, event-driven)
- **Databases** (SQL, NoSQL, caches)
- **Batch processing systems** (ETL pipelines, data warehouses)
- **Infrastructure** (CPU, memory, I/O under load)

By documenting *minimum acceptable*, *target*, and *maximum* throughput limits—alongside degradation thresholds—teams can align expectations, avoid surprise outages, and optimize resource allocation.

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                 | **Example**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Baseline Throughput** | Minimum guaranteed throughput under normal conditions.                        | API: 1,000 RPS (Requests Per Second) under 99th-percentile latency < 100ms. |
| **Target Throughput**  | Ideal or operational goal for sustained performance.                       | DB: 10,000 writes/sec in production with < 5% read stalls.                  |
| **Peak Throughput**    | Maximum supported throughput (short-term, e.g., during traffic spikes).      | Batch job: 500MB/s during monthly reporting cron.                          |
| **Degradation Threshold** | Throughput at which performance degrades (e.g., latency spikes, errors).   | API: < 500 RPS if latency > 500ms (fallback to queueing).                   |
| **Failure Throughput** | Throughput under partial failure (e.g., one availability zone down).         | DB: 5,000 RPS with one replica offline (vs. 20,000 RPS full capacity).       |
| **Resource Constraints** | Hard limits tied to infrastructure (e.g., CPU, memory, network).           | "Throughput capped at 20,000 RPS due to 10Gbps ingress bandwidth."        |

---

## **3. Schema Reference**

### **Core Schema: `ThroughputGuideline`**
```json
{
  "id": "string (unique identifier, e.g., 'api-v1-write')",
  "name": "string (e.g., 'Order Service Write Operations')",
  "description": "string (purpose/context)",
  "component": "enum (API, DB, Batch, Cache, etc.)",
  "environment": "enum (Dev, Staging, Prod, Multi-Region)",
  "metrics": [
    {
      "name": "requests_per_second",
      "baseline": { "value": 1000, "unit": "RPS" },
      "target": { "value": 5000, "unit": "RPS" },
      "peak": { "value": 10000, "unit": "RPS" },
      "degradation": {
        "threshold": 3000,
        "unit": "RPS",
        "action": "Enable auto-scaling"
      },
      "failure": {
        "scenario": "One AZ down",
        "throughput": 4000,
        "unit": "RPS"
      }
    }
  ],
  "resource_constraints": [
    {
      "type": "CPU",
      "limit": "8 vCPUs (max)",
      "impact": "Throughput drops if CPU > 90% for >5min"
    }
  ],
  "monitoring": {
    "metrics": ["latency_p95", "error_rate", "queue_length"],
    "alerts": [
      {
        "condition": "latency_p95 > 500ms",
        "severity": "WARNING",
        "action": "Notify DevOps"
      }
    ]
  },
  "valid_from": "ISO8601 timestamp",
  "valid_until": "ISO8601 timestamp (optional)",
  "references": ["doc-link-1", "doc-link-2"]
}
```

---

## **4. Query Examples**

### **4.1 Find Baseline Throughput for a Specific Component**
```sql
SELECT baseline.value, baseline.unit
FROM throughput_guidelines
WHERE id = 'db-inventory-read'
  AND component = 'DB'
  AND metrics.name = 'read_requests_per_second';
```

**Expected Output:**
```
1000 RPS
```

---

### **4.2 Identify Degradation Thresholds for APIs Under Load**
```sql
SELECT name, description, metrics.degradation.threshold, metrics.degradation.unit
FROM throughput_guidelines
WHERE component = 'API'
  AND metrics.degradation.threshold IS NOT NULL;
```

**Expected Output:**
| Name               | Description                          | Threshold | Unit |
|--------------------|--------------------------------------|-----------|------|
| `user-auth`        | JWT validation endpoint              | 500       | RPS  |
| `order-processor`  | Core order processing API            | 2000      | RPS  |

---

### **4.3 Alert on Failed Throughput Scenarios**
```sql
SELECT id, name, failure.scenario, failure.throughput
FROM throughput_guidelines
WHERE failure.scenario = 'Regional Outage';
```

**Expected Output:**
| ID               | Name                          | Scenario            | Throughput |
|------------------|-------------------------------|---------------------|------------|
| `cache-redis`    | Session cache                  | Regional Outage     | 2000 RPS   |

---

### **4.4 Calculate Resource Impact at Peak Throughput**
```python
# Pseudocode for calculating CPU utilization at peak load
def calculate_cpu_impact(guideline):
    peak_rps = guideline["metrics"][0]["peak"]["value"]
    cpu_per_rps = 0.002  # Example: 0.2% CPU per RPS
    total_cpu = peak_rps * cpu_per_rps
    return total_cpu

result = calculate_cpu_impact({
  "id": "api-v1-write",
  "metrics": [{"name": "requests_per_second", "peak": {"value": 10000}}]
})
print(f"Peak CPU usage: {result*100}%")  # Output: 200%
```

---

## **5. Implementation Guidelines**

### **5.1 Defining Throughput Metrics**
- **Unit standardization**: Use consistent units (e.g., always "RPS" for requests, "MB/s" for bandwidth).
- **Granularity**: Break down by:
  - Endpoint (e.g., `/users`, `/orders`)
  - Database table/index
  - Batch job phase (e.g., "load" vs. "transform")
- **Caching impact**: Note if metrics exclude cached responses (e.g., "90% of reads served from cache").

### **5.2 Handling Variability**
| **Scenario**               | **Guideline**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|
| **Spiky traffic**          | Define peak throughput as a 15-minute rolling max (not hourly).               |
| **Seasonal patterns**      | Document "expected spikes" (e.g., "Black Friday: 3x baseline").               |
| **Autoscaling limits**     | Clarify if guidelines assume manual or auto-scaling (e.g., "Assume 30s scaling delay"). |

### **5.3 Monitoring and Alerting**
- **Latency thresholds**: Link degradation thresholds to observed P95/P99 latencies.
- **Error rates**: Monitor `4xx/5xx` errors to detect capacity issues before throughput drops.
- **Queue lengths**: For buffered systems (e.g., Kafka), track `enqueue_duration`.

**Example Alert Rule:**
> **"When RPS > 70% of `degradation.threshold` for >1 minute, trigger scaling."**

---

## **6. Related Patterns**

| **Pattern**               | **Relation to Throughput Guidelines**                                                                 | **When to Combine**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Throughput guidelines help define when to trip a circuit breaker (e.g., "If RPS > 1000, circuit break"). | High-latency APIs with variable load.                                               |
| **Bulkhead Pattern**      | Guidelines determine thread pool sizes (e.g., "Allocate 10 threads per 100 RPS").                      | CPU-bound microservices.                                                            |
| **Rate Limiting**         | Baselines/targets inform rate limit thresholds (e.g., "Set limit to 80% of baseline").                | External APIs with unpredictable traffic.                                          |
| **Retry with Backoff**    | Failure throughput scenarios guide retry logic (e.g., "Retry at 50% of `failure.throughput`").      | Idempotent operations in distributed systems.                                      |
| **Chaos Engineering**     | Throughput guidelines provide baselines for experiments (e.g., "Kill 30% of nodes; measure RPS drop"). | Testing failure resilience.                                                        |

---

## **7. Example: API Throughput Guideline**
```json
{
  "id": "api-v1-payments",
  "name": "Payment Service API",
  "description": "Handles Stripe-like payment processing with 3DS validation.",
  "component": "API",
  "environment": "Production",
  "metrics": [
    {
      "name": "process_payment",
      "baseline": { "value": 200, "unit": "RPS" },
      "target": { "value": 500, "unit": "RPS" },
      "peak": { "value": 1000, "unit": "RPS" },
      "degradation": {
        "threshold": 300,
        "unit": "RPS",
        "action": "Enable request queuing; notify payment team."
      },
      "failure": {
        "scenario": "Stripe API unavailable",
        "throughput": 50,
        "unit": "RPS",
        "action": "Fallback to local transaction log."
      }
    }
  ],
  "resource_constraints": [
    {
      "type": "CPU",
      "limit": "4 vCPUs",
      "impact": "Latency > 200ms if CPU > 85% for >30s."
    }
  ],
  "monitoring": {
    "metrics": ["p99_latency", "stripe_timeout_errors", "queue_size"],
    "alerts": [
      {
        "condition": "queue_size > 1000",
        "severity": "CRITICAL",
        "action": "Activate fallback mode."
      }
    ]
  }
}
```

---
## **8. Common Pitfalls**
1. **Overestimating baseline**: Always test under realistic load (e.g., include cold-start overhead for serverless).
2. **Ignoring cold starts**: Document expected throughput drops during scaling events.
3. **Static thresholds**: Revalidate guidelines quarterly or after major codebase changes.
4. **Silos**: Align throughput with cross-team SLIs (e.g., "This API supports 95% of order processing throughput").

---
## **9. Tools for Enforcement**
| **Tool**               | **Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Prometheus/Grafana** | Visualize real-time throughput vs. guidelines.                               |
| **OpenTelemetry**      | Trace requests to identify bottleneck endpoints.                             |
| **Terraform Cloud**    | Enforce resource limits (e.g., "auto-scaling group must stay below 80% CPU"). |
| **Confluent/Kafka**    | Monitor message throughput in event streams.                                |
| **Chaos Mesh**         | Inject failures to test `failure.throughput` scenarios.                     |

---
**Key Takeaway**: Throughput guidelines bridge engineering metrics with business expectations. Document them early, update them often, and integrate them into CI/CD pipelines (e.g., fail tests if peak load exceeds `peak.throughput`).