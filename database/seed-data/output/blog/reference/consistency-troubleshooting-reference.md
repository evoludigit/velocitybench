# **[Pattern] Consistency Troubleshooting Reference Guide**

---

## **Overview**
The **Consistency Troubleshooting Pattern** provides a structured approach to diagnosing and resolving inconsistencies across distributed systems, databases, and microservices. Inconsistencies arise when data or state diverges between systems due to network latency, retries, partial failures, or conflicting operations. This guide outlines key strategies, diagnostic tools, and best practices for identifying and fixing consistency issues in real-time and event-driven architectures.

The pattern focuses on:
- **Detecting** inconsistencies (e.g., stale reads, missing events, or divergent records).
- **Localizing** the root cause (network issues, transaction rollbacks, or logic errors).
- **Mitigating** impact (retries, compensating transactions, or manual overrides).
- **Preventing** future occurrences (reliable eventing, idempotent operations).

This reference assumes familiarity with distributed systems, transaction patterns (e.g., saga, two-phase commit), and observability tools like logs, metrics, and tracing.

---

## **Key Concepts & Implementation Details**

### **1. Types of Consistency Issues**
| **Issue Type**            | **Description**                                                                 | **Common Causes**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Stale Reads**           | A client reads outdated data due to eventual consistency delays.               | Long-running transactions, lazy replication, or high latency.                    |
| **Missing Events**        | An event is lost or not processed (e.g., Kafka message dropped).              | Broker misconfiguration, network partitions, or consumer crashes.                 |
| **Divergent State**       | Systems disagree on a shared state (e.g., inventory vs. order processing).   | Uncompensated side-effects, retries without idempotency, or unordered events.    |
| **Deadlocks/Timeouts**    | Long-running operations block other transactions.                              | Poor lock granularity, cascading rollbacks, or unbounded retries.                |
| **Duplicate Events**      | An event is processed multiple times (e.g., due to retries).                  | Non-idempotent operations or unreliable delivery semantics.                      |

---

### **2. Debugging Workflow**
Follow this **step-by-step troubleshooting approach**:

#### **Step 1: Reproduce the Issue**
- **Logs**: Search for errors (e.g., `TimeoutException`, `DuplicateTransaction`) in application logs.
- **Metrics**: Monitor latency spikes, error rates, or retry loops (e.g., Prometheus alerts).
- **Traces**: Use distributed tracing (e.g., Jaeger, OpenTelemetry) to track request flows.

#### **Step 2: Isolate the Scope**
Identify affected components:
- **Single Service**: Check local state (e.g., database transactions).
- **Cross-Service**: Verify event propagation (e.g., Kafka topics, HTTP calls).
- **Infrastructure**: Network partitions, disk I/O, or container failures.

#### **Step 3: Analyze Root Cause**
| **Diagnostic Tool**       | **Use Case**                                                                 | **Example Query**                                                                 |
|---------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Database Queries**      | Compare record versions across nodes.                                      | `SELECT * FROM orders WHERE id = 123 AND version != MAX(version)`                 |
| **Event Logs**            | Check for missing/duplicate events in Kafka/RabbitMQ.                     | `kafka-console-consumer --bootstrap-server <broker> --topic orders --from-beginning` |
| **Distributed Locks**     | Detect deadlocks in ZooKeeper/Redis locks.                                  | `redis-cli monitor` (look for `WATCH` commands).                                |
| **Idempotency Keys**      | Verify replayed events with the same key were processed correctly.           | `SELECT COUNT(*) FROM events WHERE idempotency_key = "order_123"`                 |

#### **Step 4: Apply Mitigation**
| **Mitigation Strategy**   | **When to Use**                                                                 | **Implementation Notes**                                                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Retry with Backoff**    | Temporary network failures.                                                    | Exponential backoff (e.g., `retry: maxAttempts: 3, delay: 100ms * 2^x`).          |
| **Compensating Transactions** | Undo side effects (e.g., cancel an unshipped order).                  | Design saga workflows with explicit rollback steps.                               |
| **Idempotent Operations** | Prevent duplicate processing.                                                 | Use UUIDs or database constraints (e.g., `UNIQUE(index)`).                      |
| **Manual Intervention**   | Critical data corruption.                                                      | Freeze writes, restore from backup, or audit manually.                           |

#### **Step 5: Prevent Recurrence**
- **Design**:
  - Use **CQRS** for eventual consistency when reading.
  - Implement **Sagas** for long-running transactions.
- **Infrastructure**:
  - Enable **exactly-once processing** in event streams (e.g., Kafka transactions).
  - Configure **health checks** for dependent services.
- **Observability**:
  - Set up **alerts** for consistency violations (e.g., `SELECT COUNT(*) WHERE timestamp_diff < -5s`).
  - Use **canary deployments** to test fixes in production-like environments.

---

## **Schema Reference**
Below are common schemas for tracking consistency issues.

### **1. Event Schema (Kafka/RabbitMQ)**
```json
{
  "event_id": "uuid4",           // Unique identifier for deduplication
  "source_service": "orders",    // Emitting service
  "event_type": "OrderCreated", // Event name
  "payload": {                   // Schema-specific data
    "order_id": "123",
    "status": "PENDING"
  },
  "metadata": {                  // Consistency tracking
    "timestamp": "ISO_8601",
    "correlation_id": "order_123", // Links related events
    "processing_attempts": 1     // Track retries
  }
}
```

### **2. Database Schema (Audit Table)**
```sql
CREATE TABLE consistency_audit (
  id SERIAL PRIMARY KEY,
  entity_type VARCHAR(50),    -- e.g., "Order", "Payment"
  entity_id VARCHAR(100),     -- Unique key
  expected_state JSONB,       -- Desired state (e.g., {"status": "SHIPPED"})
  actual_state JSONB,         -- Observed state
  detected_at TIMESTAMP,      -- When inconsistency was found
  resolved_at TIMESTAMP,      -- Optional: Resolution time
  resolution_action VARCHAR(255)  -- e.g., "Manual override", "Retry"
);
```

### **3. Tracing Context Schema**
```json
{
  "trace_id": "123e4567-e89b-12d3-a456-426614174000", // Distributed trace ID
  "span_id": "span_123",                             // Current operation
  "consistency_checks": [                           // Embedded checks
    {
      "check_id": "inventory_match",
      "status": "FAIL",
      "details": {
        "expected": 10,
        "actual": 5,
        "service": "inventory"
      }
    }
  ]
}
```

---

## **Query Examples**

### **1. Detect Stale Reads (PostgreSQL)**
```sql
-- Find records where the latest version was not read
SELECT
  r.record_id,
  r.version,
  m.version AS latest_version,
  r.created_at
FROM records r
JOIN (
  SELECT record_id, MAX(version) AS version
  FROM records
  GROUP BY record_id
) m ON r.record_id = m.record_id AND r.version < m.version;
```

### **2. Find Missing Events (Kafka)**
```bash
# Check for gaps in event sequences (e.g., missing OrderCreated for order 123)
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic orders \
  --from-offset 0 \
  --filter "\{\"order_id\":\"123\"}" --print-key \
  | jq 'select(.event_type == "OrderCreated")'
```

### **3. Audit Inconsistencies (SQL)**
```sql
-- Query unresolved inconsistencies
SELECT *
FROM consistency_audit
WHERE resolved_at IS NULL
  AND entity_type IN ('Order', 'Payment');
```

### **4. Trace Consistency Violations (Jaeger)**
```sql
# Filter traces where inventory and order states differ
jaeger query \
  --service=orders \
  --tags="consistency_check.inventory_mismatch=true"
```

---

## **Related Patterns**
Consistency troubleshooting often intersects with these patterns:

| **Pattern**               | **Description**                                                                 | **Use Case**                                                                     |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **[Saga Pattern]**        | Manages distributed transactions via compensating actions.                     | Long-running workflows (e.g., booking + payment).                              |
| **[Event Sourcing]**      | Stores state changes as immutable events.                                     | Audit trails and replayability.                                               |
| **[CQRS]**                | Separates read (optimized for speed) and write (strong consistency) models.  | High-throughput systems with eventual consistency.                            |
| **[Idempotent Operations]** | Ensures repeated calls have the same effect.                                  | Retry-safe APIs (e.g., payment processing).                                   |
| **[Retry with Backoff]**  | Exponentially delays retries to avoid thundering herds.                       | Resilient HTTP calls or database operations.                                    |
| **[Circuit Breaker]**     | Stops cascading failures by stopping calls to a failing service.              | Protects from cascading consistency errors.                                    |

---
**References**:
- [Distributed Systems Reading List](https://github.com/butlerx123/distributed-systems-reading-list)
- [AWS Well-Architected Consistency Framework](https://aws.amazon.com/architecture/well-architected/)