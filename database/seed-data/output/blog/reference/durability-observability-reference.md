# **[Pattern] Durability Observability – Reference Guide**

---
## **Overview**
The **Durability Observability** pattern ensures that distributed systems can reliably detect and diagnose failures in long-running transactions, eventually consistent operations, or stateful workflows—where data integrity may be compromised by partial failures (e.g., node crashes, network partitions, or timeouts). Observability here encompasses **tracing** persistent operations, **monitoring** for anomalies in consistency guarantees, **logging** recovery state, and **alerting** on durability risks.

This pattern is critical for systems where:
- **Eventual consistency** is used (e.g., CAP theorem trade-offs).
- **Idempotent retries** must be safely managed.
- **Eventual recovery** from outages is required.
- **Audit trails** of state changes are necessary for compliance or debugging.

By combining **retention policies** (how long to track operations) and **sampling strategies** (which operations to observe), this pattern balances overhead with accuracy, ensuring that failed durability attempts are surfaced for corrective action.

---

## **Schema Reference**
The following tables define key schemas for Durability Observability.

### **1. Core Observability Entities**
| **Entity**               | **Fields**                                                                 | **Description**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `DurabilityOperation`    | `id` (str), `transaction_id` (str), `start_time` (ISO8601), `status` (enum: *PENDING*, *CONFIRMED*, *FAILED*, *ROLLED_BACK*), `end_time` (ISO8601, nullable), `retries` (int), `context` (JSON) | Represents a unit of work (e.g., DB write, event publish) requiring durability. |
| `DurabilityCheckpoint`   | `operation_id` (str), `checkpoint_id` (str), `state` (str), `timestamp` (ISO8601), `last_updated_by` (str) | Tracks recovery state of an operation (e.g., "COMMITTED", "PARTIALLY_APPLIED"). |
| `DurabilityAlert`       | `trigger_id` (str), `severity` (enum: *CRITICAL*, *WARNING*), `cause` (str), `resolved` (bool), `links` (array of `DurabilityOperation` IDs) | Alerts for failed durability guarantees (e.g., "Transaction timed out"). |

---

### **2. Relationships**
| **From**               | **To**                     | **Type**          | **Description**                                  |
|------------------------|----------------------------|-------------------|--------------------------------------------------|
| `DurabilityOperation`  | `DurabilityCheckpoint`     | *one-to-many*     | Each operation may have multiple checkpoints.    |
| `DurabilityOperation`  | `DurabilityAlert`          | *one-to-one*      | A failed operation triggers an alert (if configured). |

---

### **3. Example Data Model (JSON-LD)**
```json
{
  "@context": "https://example.com/durability-observability",
  "@id": "op_12345",
  "@type": "DurabilityOperation",
  "status": "FAILED",
  "retries": 3,
  "checkpoints": [
    {
      "@id": "chk_67890",
      "@type": "DurabilityCheckpoint",
      "state": "PARTIALLY_APPLIED",
      "last_updated_by": "node_2"
    }
  ],
  "alert": {
    "@id": "alert_999",
    "@type": "DurabilityAlert",
    "severity": "CRITICAL",
    "cause": "Network partition detected"
  }
}
```

---

## **Implementation Details**

### **1. Key Concepts**
| **Concept**            | **Definition**                                                                 | **Implementation Notes**                                                                 |
|------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Checkpointing**      | Periodically saving the state of a durability-critical operation.              | Use **log-structured storage** (e.g., WAL) or **distributed locks** to avoid race conditions. |
| **Idempotency Keys**   | Unique identifiers to ensure retries don’t cause duplicate side effects.       | Store keys in a **distributed cache** (e.g., Redis) with TTLs.                         |
| **Sampling**           | Observing a subset of operations to reduce overhead.                           | Apply **stratified sampling** (e.g., prioritize high-value operations).                |
| **Retention Policy**   | How long to store durability traces for compliance or debugging.              | Align with **SLA requirements** (e.g., 7 days for debugging, 1 year for compliance).    |

---

### **2. Observability Signals**
Track these metrics for durability:
| **Signal**                  | **Type**       | **Example Query**                          | **Thresholds**                          |
|-----------------------------|----------------|--------------------------------------------|-----------------------------------------|
| `durability.operation.latency` | Histogram      | `histogram_quantile(0.95, rate(durability_latency_bucket[5m]))` | >1s = **WARNING**, >5s = **CRITICAL** |
| `durability.failure.rate`   | Counter        | `rate(durability_failure_total[1m]) / rate(durability_operation_total[1m])` | >0.1% = **WARNING**                     |
| `checkpoint.age`            | Gauge          | `durability_checkpoint_age_seconds`        | >30s = **WARNING**                      |

---

### **3. Workflow Example**
1. **Operation Initiated**:
   - A `DurabilityOperation` is created with `status=PENDING`.
   - A checkpoint (`state=IN_PROGRESS`) is added.
2. **Partial Success**:
   - If the operation fails mid-execution, a `checkpoint.state=PARTIALLY_APPLIED` is recorded.
   - An alert is triggered if the operation hasn’t recovered within `T`.
3. **Recovery**:
   - The system retries using the **idempotency key**.
   - A new checkpoint (`state=RECOVERED`) is added if successful.

---

## **Query Examples**

### **1. Find Failed Operations in the Last Hour**
```sql
SELECT o.id, o.status, o.start_time, c.state, alert.cause
FROM DurabilityOperation o
JOIN DurabilityCheckpoint c ON o.id = c.operation_id
LEFT JOIN DurabilityAlert alert ON o.id = alert.operation_id
WHERE o.status = 'FAILED'
  AND o.start_time > NOW() - INTERVAL '1 hour'
ORDER BY o.start_time DESC;
```

### **2. Alert on Checkpoints Stuck in "IN_PROGRESS"**
```promql
count_over_time(durability_checkpoint_state{state="IN_PROGRESS"}[5m]) > 5
```
**Alert Rule**:
```yaml
- alert: DurabilityCheckpointStuck
  expr: count_over_time(durability_checkpoint_state{state="IN_PROGRESS"}[5m]) > 5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Checkpoint {{ $labels.instance }} stuck in 'IN_PROGRESS' for 10m"
```

### **3. Trace an Operation Through Checkpoints**
```graphql
query durabilityTrace($operationId: ID!) {
  operation(id: $operationId) {
    checkpoints {
      id
      state
      timestamp
    }
    alert {
      cause
      severity
    }
  }
}
```

---

## **Related Patterns**
| **Pattern**                          | **When to Use**                                                                 | **Complementary to Durability Observability**                     |
|--------------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------|
| **Saga Pattern**                     | Long-running transactions requiring compensating actions.                      | Observability helps track saga recovery state.                   |
| **Circuit Breaker**                  | Prevent cascading failures in dependent services.                              | Durability observability ensures retries aren’t lost.             |
| **Idempotent Producer-Consumer**     | Message systems with retry logic.                                              | Checkpoints verify message delivery consistency.                |
| **Chaos Mesh**                       | Intentional failure testing for resilience.                                   | Observes how durability handles chaos scenarios.                 |
| **Distributed Tracing**              | Latency analysis across microservices.                                         | Correlates durability failures with service-level traces.       |

---

## **Best Practices**
1. **Prioritize Critical Operations**:
   Use **dynamic sampling** to observe high-value operations more frequently.
2. **Correlate with Distributed Traces**:
   Attach `trace_id` to `DurabilityOperation` for root-cause analysis.
3. **Limit Checkpoint Overhead**:
   Only checkpoint for **stateful** operations (e.g., DB writes, not reads).
4. **Automate Recovery**:
   Integrate with **SLO dashboards** to auto-scale observability resources during outages.

---
**See Also**:
- [OpenTelemetry Durability Extensions](https://opentelemetry.io/docs/specs/extensions/durability/)
- [CFR (Consistency, Fault Tolerance, Recovery) Framework](https://www.usenix.org/system/files/conference/osdi17/osdi17-li.pdf)