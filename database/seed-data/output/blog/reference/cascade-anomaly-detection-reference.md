# **[Pattern] Cascade Anomaly Detection Reference Guide**

---

## **Overview**
The **Cascade Anomaly Detection** pattern identifies unexpected trigger cascades—sequences of correlated events where a failure or anomaly in one system causes chain reactions in dependent systems. This pattern helps detect, monitor, and respond to systemic failures before they escalate.

Key use cases include:
- **Financial Systems:** Fraudulent transactions triggering account freezes and service disruptions.
- **IoT Networks:** Sensor failures causing cascading equipment shutdowns.
- **Cloud Operations:** A failed API call initiating retry storms in downstream services.
- **Logistics:** Supply chain disruptions from delayed shipments affecting multiple nodes.

By analyzing event dependencies and propagation patterns, this pattern enables proactive anomaly mitigation, reduces downtime, and improves resilience in distributed systems.

---

## **Implementation Details**

### **Core Concepts**
1. **Trigger-Propagator Pairs:**
   - A **trigger** is an event that initiates a cascade (e.g., a failed database query).
   - A **propagator** is the dependent system impacted (e.g., a microservice crashing due to a timeout).

2. **Cascade Patterns:**
   - **Linear Cascades:** Direct, step-by-step failures (A → B → C).
   - **Branching Cascades:** A trigger affects multiple propagators (A → B, A → C).
   - **Feedback Loops:** Propagators trigger new cascades (A → B → A).

3. **Anomaly Thresholds:**
   - **Baseline Propagation Speed:** Expected time between trigger and impact.
   - **Frequency Anomalies:** Unusual spike in cascades (e.g., 100% increase in 5 minutes).
   - **Depth Anomalies:** Unexpectedly deep cascades (e.g., 5 hops instead of 2).

4. **Mitigation Strategies:**
   - **Rate Limiting:** Throttle propagators during cascades.
   - **Circuit Breakers:** Temporarily halt dependent services.
   - **Automated Rollbacks:** Revert to a stable state if anomalies persist.

---

## **Schema Reference**

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|---------------|---------------------------------------------------------------------------------|----------------------------------------|
| `cascade_id`            | `string`      | Unique identifier for the cascade event.                                       | `"cascade_20240515-1234"`              |
| `trigger_event`         | `object`      | Details of the initiating event.                                               | `{ "type": "DB_QUERY_TIMEOUT", "time": "2024-05-15T12:00:00Z" }` |
| `propagator_path`       | `array`       | List of systems impacted, in order.                                            | `[{"service": "payment-gateway", "hop": 1}, {"service": "invoice-service", "hop": 2}]` |
| `baseline_propagation`  | `integer`     | Expected number of hops before anomaly detection.                             | `2`                                    |
| `observed_hops`         | `integer`     | Actual number of hops observed in this cascade.                                | `5`                                    |
| `anomaly_score`         | `float`       | Scaled score (0–100) indicating severity (higher = worse).                     | `89.3`                                 |
| `mitigation_action`     | `string`      | Applied or recommended action (e.g., "rate_limit", "rollback").                 | `"rate_limit_propagators"`              |
| `timestamp`             | `datetime`    | When the cascade was detected.                                                  | `"2024-05-15T12:02:45Z"`               |
| `resolved_at`           | `datetime`    | When the cascade was mitigated (optional).                                     | `"2024-05-15T12:15:00Z"`               |
| `related_events`        | `array`       | Linked events (e.g., logs, alerts) for debugging.                              | `[{"id": "log_789", "type": "WARNING"}]` |

---

## **Query Examples**

### **1. Detect Cascades with Unusual Depth**
```sql
SELECT
    cascade_id,
    trigger_event.type AS trigger_type,
    ARRAY_LENGTH(propagator_path, 1) AS observed_hops,
    baseline_propagation,
    anomaly_score
FROM cascade_events
WHERE observed_hops > (baseline_propagation + 2)
  AND anomaly_score > 70
ORDER BY anomaly_score DESC
LIMIT 5;
```
**Returns:** Top 5 cascades with depth anomalies (e.g., `observed_hops=5`, `baseline_propagation=2`).

---

### **2. Monitor Propagator Frequency Spikes**
```sql
WITH frequency_spikes AS (
    SELECT
        propagator_path[1].service AS affected_service,
        COUNT(*) AS cascade_count,
        AVG(anomaly_score) AS avg_score
    FROM cascade_events
    WHERE timestamp BETWEEN NOW() - INTERVAL '5 minutes' AND NOW()
    GROUP BY affected_service
    HAVING COUNT(*) > (
        SELECT AVG(cascade_count) * 1.5
        FROM (
            SELECT COUNT(*) AS cascade_count
            FROM cascade_events
            GROUP BY propagator_path[1].service
        ) AS avg_counts
    )
)
SELECT * FROM frequency_spikes
ORDER BY cascade_count DESC;
```
**Returns:** Services currently experiencing cascades 50% above normal frequency.

---

### **3. Filter by Mitigation Action**
```sql
SELECT
    cascade_id,
    trigger_event.type,
    mitigation_action,
    resolved_at
FROM cascade_events
WHERE mitigation_action = 'rate_limit_propagators'
  AND resolved_at IS NULL
ORDER BY timestamp DESC;
```
**Returns:** Unresolved cascades where rate limiting was applied.

---

### **4. Visualize Cascade Propagation Patterns**
```python
# Pseudocode (e.g., using PySpark or Pandas)
from pyspark.sql import functions as F

df = spark.sql("""
    SELECT * FROM cascade_events
    WHERE timestamp BETWEEN '2024-05-15' AND '2024-05-16'
""")

# Group by propagator path and count occurrences
path_counts = df.groupBy("propagator_path").count()
path_counts.sort(F.desc("count")).show(10, truncate=False)
```
**Output:** Top 10 most common propagation sequences (e.g., `["auth-service", "payment-service", "notification-service"]`).

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**       | Isolates failing services to prevent cascading failures.                          | When a single service’s failure risks infecting others.                         |
| **Rate Limiting**         | Controls request volume to prevent overload.                                    | During detected anomalies to stabilize propagators.                             |
| **Distributed Tracing**  | Tracks requests across microservices for root-cause analysis.                    | Debugging complex cascades with unclear propagation paths.                      |
| **Chaos Engineering**     | Proactively tests system resilience by injecting failures.                       | Designing systems to handle unforeseen cascades.                               |
| **Anomaly Detection (ML)**| Uses ML models to flag unexpected patterns in metrics.                          | When statistical baselines are unclear (e.g., new services).                  |

---
**Note:** Combine this pattern with **distributed tracing** for deeper diagnostics or **chaos engineering** to validate mitigation strategies.