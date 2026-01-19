# **[Pattern] Reference Guide: Throughput Conventions**

---

## **Overview**
The **Throughput Conventions** pattern standardizes how applications measure, report, and interpret performance metrics—particularly **event throughput**, **success rates**, and related dimensions—to enable consistent monitoring, anomaly detection, and system comparison. Originating from **OpenTelemetry** and **W3C’s Tracing Architecture**, this pattern defines a **dimensional model** (e.g., `operation`, `status`, `outcome`, `attributes`) for quantifying how frequently operations complete successfully or fail, under what conditions, and at what rate.

Unlike traditional **counter** or **histogram** metrics, Throughput Conventions **explicitly tie success/failure to discrete operations** (e.g., API calls, database queries) while accounting for **sampling bias** and **control flow** (e.g., retries, parallelism). This makes it ideal for distributed systems where **latency alone** does not convey throughput reliability.

---

## **Key Concepts & Implementation Details**
### **1. Core Dimensions**
Throughput is measured along these **mandatory axes** (extendable via custom attributes):

| **Dimension**       | **Purpose**                                                                 | **Example Values**                                                                 |
|----------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Operation**        | Identifies the atomic unit of work (e.g., `/api/checkout`, `SELECT * FROM users`) | `"checkout_api_call"`, `"db_query"`, `"payment_processing"`                     |
| **Status**           | Classifies success/failure (critical for distinguishing noise from issues) | `"ok"`, `"error"`, `"timeout"`, `"retried"`                                       |
| **Outcome**          | Describes the result’s impact (useful for business logic analysis)         | `"purchased"`, `"failed_payment"`, `"item_out_of_stock"`                           |
| **Attributes**       | Key-value pairs for contextual richness (e.g., `user_id`, `region`)         | `"user_id": "12345"`, `"retries": "3"`                                             |

### **2. Metric Types**
| **Metric**           | **Definition**                                                                 | **Unit**       | **Use Case**                                                                       |
|----------------------|-------------------------------------------------------------------------------|----------------|-----------------------------------------------------------------------------------|
| **Total Throughput** | Count of all operations (successes + failures) across a time window.        | `events/sec`   | Capacity planning, load testing.                                                   |
| **Successful Throughput** | Count of operations with `status="ok"`.                                   | `events/sec`   | SLA compliance, reliability monitoring.                                           |
| **Error Throughput** | Count of operations with `status="error"` (excluding retries unless noted). | `events/sec`   | Error budgeting, incident triage.                                                  |
| **Retry Throughput** | Count of operations retried (post-failure) or intentionally repeated.       | `events/sec`   | Debugging transient failures.                                                      |
| **Latency-Adjusted Throughput** | Throughput weighted by operation latency (e.g., `successful_events / avg_latency`). | `events/(sec·ms)` | Performance tuning, QoS analysis.                                                   |

### **3. Sampling Considerations**
- **Event Sampling**: Throughput metrics *must* account for **sampling ratios** (e.g., `sampled=true` flag) to avoid overcounting.
  - Example: If 1% of requests are sampled, multiply raw counts by `100`.
- **Control Flow**: Parallel/retried operations require **de-duplication** (e.g., count only the *final* outcome, not intermediate retries).

### **4. Best Practices**
- **Granularity**: Align `operation` names with **service boundaries** (e.g., `service=payment` + `operation=validate_card`).
- **Stability**: Avoid changing `operation` definitions mid-deployment (breaks historical comparisons).
- **Negative Values**: Throughput metrics are *non-negative*; use separate metrics for failures (e.g., `errors_total`).
- **Headers/Context Propagation**: Attach `operation`, `status`, and `outcome` to traces/spans for correlated analysis.

---

## **Schema Reference**
Below is the **mandatory schema** for Throughput Conventions (compatible with OpenTelemetry’s `Metrics` API).

| **Field**          | **Type**       | **Description**                                                                 | **Example**                                                                 |
|--------------------|----------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `measurements`     | Array          | List of throughput metrics (see table above).                                  | `[{"name": "total_events", "value": 500}, {"name": "successful_events", "value": 450}]` |
| `operation`        | String         | Required: Identifies the operation (use **stable, descriptive names**).       | `"db/update_user_profile"`                                                   |
| `status`           | String         | Required: One of `ok`, `error`, `timeout`, or custom (e.g., `cancelled`).     | `"error"`                                                                   |
| `outcome`          | String         | Optional: Business-level classification.                                        | `"profile_updated"`                                                          |
| `attributes`       | Object         | Key-value pairs for context (e.g., `user_id`, `region`).                         | `{"user_id": "42", "retries": "2"}`                                          |
| `sampling_ratio`   | Float (0–1)    | Sampling fraction (e.g., `0.01` for 1% sampling).                               | `0.05`                                                                      |
| `start_timestamp`  | Timestamp      | When the operation began (for latency calculations).                           | `2023-10-01T12:00:00Z`                                                      |
| `end_timestamp`    | Timestamp      | When the operation completed.                                                  | `2023-10-01T12:00:01.234Z`                                                  |

---

## **Query Examples**
### **1. Total Throughput (PromQL)**
```promql
# Count all operations (regardless of status) in the last 5 minutes.
sum(rate(throughput_total[5m])) by (operation)

# Aggregate by operation type.
sum(rate(throughput_total[5m])) by (operation)
```

### **2. Success Rate**
```promql
# Success rate (% of operations with status="ok").
100 * (
  sum(rate(throughput_successful[5m]))
  /
  sum(rate(throughput_total[5m]))
) by (operation)
```

### **3. Error Rate (with Retry Filtering)**
```promql
# Errors excluding retries (assuming `status="error"` excludes retried operations).
sum(rate(throughput_errors[5m])) by (operation)
```

### **4. Latency-Adjusted Throughput (OpenTelemetry)**
```sql
-- SQL-like pseudocode for weighted throughput:
SELECT
  operation,
  SUM(events) / AVG(latency_ms) AS effective_throughput
FROM throughput_metrics
WHERE status = 'ok'
GROUP BY operation;
```

### **5. Sampling-Adjusted Metrics**
```promql
# Correct for 1% sampling (multiply by 100).
100 * rate(throughput_total{sampling_ratio=0.01}[5m])
```

---

## **Related Patterns**
| **Pattern**                     | **Relationship**                                                                 | **When to Use Together**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **[Latency Monitoring](latency.md)** | Throughput Conventions complement latency by providing **context** (e.g., "90% of `timeout` errors had >1s latency"). | Analyzing **performance bottlenecks**.                                                   |
| **[Error Budgeting](error_budgeting.md)** | Uses `throughput_errors` to calculate allowable failure rates.                  | Defining **reliability goals** (e.g., "99.9% uptime").                                     |
| **[Distributed Tracing](tracing.md)** | Attaches `operation`, `status`, and `outcome` to spans for **end-to-end analysis**. | Debugging **cross-service failures**.                                                   |
| **[Resource Limits](resource_limits.md)** | Throughput metrics inform **quota enforcement** (e.g., "Cap `operation=db_write` to 1000/s"). | **Auto-scaling** or **throttling** policies.                                               |
| **[Canary Analysis](canary.md)**  | Compare throughput between canary and production for **risk assessment**.        | **Gradual rollouts** or **feature flagging**.                                             |

---

## **Common Pitfalls & Fixes**
| **Issue**                                  | **Root Cause**                                      | **Solution**                                                                           |
|--------------------------------------------|-----------------------------------------------------|---------------------------------------------------------------------------------------|
| "Throughput spikes but no errors"          | Sampling bias or **duplicate counting**.            | Filter by `sampling_ratio`; use **distinct()** in queries.                           |
| "Success rate drops after deployment"      | Changed `operation` name or **status classification**. | Audit `operation` definitions; log `status` transitions.                             |
| "Retries inflate success counts"           | Counting retried operations as "successful".       | Exclude `status="retried"` from `successful_events`; track `retry_total` separately. |
| "Low granularity for business outcomes"    | Missing `outcome` dimension.                         | Add `outcome` to high-value operations (e.g., `purchase_confirmed`).                   |

---
**See Also**:
- [OpenTelemetry Metrics Spec](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/metrics/throughput.md)
- [W3C Tracing Architecture](https://www.w3.org/TR/trace-context/#tracing-conventions)