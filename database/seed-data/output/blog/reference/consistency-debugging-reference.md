# **[Pattern] Consistency Debugging Reference Guide**

## **Overview**
Consistency debugging ensures that data across distributed systems appears accurate, synchronized, and interpretable, despite concurrent operations, retries, or network failures. This pattern identifies discrepancies (e.g., stale reads, race conditions, or data corruption) by comparing expected vs. actual states. It’s critical for systems relying on eventual consistency models, distributed transactions, or graph databases where data conflicts are inevitable.

Unlike traditional error detection, consistency debugging focuses on validating **invariants**—logical rules dictating how data should relate (e.g., "all transactions must balance credits and debits"). Common scenarios include:
- Detecting missing or duplicated records in event-sourced systems.
- Reconciling divergent views in replicated caches.
- Validating constraints across microservices with eventual consistency.

---

## **Implementation Details**
### **Key Concepts**
| Concept               | Description                                                                                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Invariant**         | A logical rule enforced between data entities (e.g., `sum(appends) = sum(commits)` in a versioned log).                                                        |
| **State Comparison**  | Comparing the system’s current state to a **ground truth** (e.g., a transactional database snapshot, a canonical source, or a pre-computed hash).            |
| **Delta Analysis**    | Scanning for changes between two states (e.g., examining writes since the last consistency check).                                                            |
| **Conflict Resolution** | Detecting conflicts (e.g., last-write-wins vs. merge strategies) and flagging them for manual review.                                                          |
| **Rollback Proxy**    | Temporarily reverting a system to a known-good state to isolate inconsistency causes (e.g., via time-travel debugging).                                      |
| **Observability Hooks** | Logging hooks tracing how invariants are violated (e.g., timestamps, request IDs, or affected entities).                                                      |

### **Core Techniques**
1. **Static Validation**
   - Predefined invariants (e.g., SQL `CHECK` constraints, schema rules) run during deployment or scheduled scans.
   - *Example*: Verify no user has negative credit after all transactions.

2. **Dynamic Monitoring**
   - Continuously probe invariants using sidecars, agents, or distributed transaction tools (e.g., [Jepsen](https://jepsen.io/)).
   - *Example*: Trigger checks when a critical endpoint (e.g., `POST /checkout`) completes.

3. **End-to-End Transactions**
   - Use distributed coordination (e.g., Saga pattern, 2PC) to enforce consistency *across services*. Fail fast if invariants are breached.
   - *Example*: A payment service must align with inventory service state within a 5-minute timeout.

4. **Sampling vs. Full Scans**
   - **Sampling**: Efficiency for high-volume systems (e.g., check 1% of transactions).
   - **Full Scans**: Run periodically (e.g., nightly) for critical data (e.g., financial records).

5. **Root Cause Analysis (RCA) Tools**
   - Correlate inconsistencies with:
     - Failed retries (e.g., circuit-breaker logs).
     - Network partitions (e.g., latency spikes).
     - Schema migrations (e.g., deprecated fields).

---

## **Schema Reference**
Below is a schema for a consistency debugging pipeline, supporting both ad-hoc checks and scheduled runs.

### **1. Invariants Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Consistency Invariant",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "minLength": 1 },
    "description": { "type": "string" },
    "type": {
      "type": "string",
      "enum": [
        "sum",     // sum(A) == sum(B)
        "ratio",   // A / B == constant
        "presence",// A must exist if B exists
        "unique"   // all(A) must be unique
      ]
    },
    "entities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "collection": { "type": "string" }, // e.g., "users", "orders"
          "field": { "type": "string" },      // e.g., "balance", "status"
          "filter": { "type": "object" }      // optional query filter
        }
      }
    },
    "threshold": { "type": "number", "minimum": 0 },
    "severity": {
      "type": "string",
      "enum": ["low", "medium", "critical"]
    },
    "checkInterval": { "type": "string", "format": "duration" } // e.g., "PT1H"
  },
  "required": ["id", "name", "type", "entities"]
}
```
**Example Invariant YAML**:
```yaml
id: "inv-001"
name: "Bank Balance Reconciliation"
description: "Ensure total deposits match total withdrawals."
type: "sum"
entities:
  - collection: "transactions"
    field: "amount"
    filter: { status: "completed" }
severity: "critical"
checkInterval: "PT1H"
```

---

### **2. Debug Session Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Debug Session",
  "type": "object",
  "properties": {
    "sessionId": { "type": "string", "format": "uuid" },
    "startTime": { "type": "string", "format": "date-time" },
    "endTime": { "type": "string", "format": "date-time" },
    "status": {
      "type": "string",
      "enum": ["running", "completed", "failed"]
    },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "invariantId": { "type": "string" },
          "status": {
            "type": "string",
            "enum": ["passed", "failed", "partial"]
          },
          "violations": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "entity": { "type": "string" },
                "actualValue": { "type": "any" },
                "expectedValue": { "type": "any" },
                "cause": { "type": "string" } // e.g., "network timeout"
              }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "samplingRate": { "type": "number" },
        "reproSteps": { "type": "array", "items": { "type": "string" } }
      }
    }
  }
}
```

---

## **Query Examples**
### **1. SQL-Based Validation**
**Check**: "All active users must have a non-null `last_login` timestamp."
```sql
SELECT u.id, u.last_login
FROM users u
WHERE u.active = true AND u.last_login IS NULL;
```

**Check**: "Order quantities in inventory must match subtotals in orders."
```sql
SELECT
    o.order_id,
    SUM(oi.quantity) AS order_items,
    SUM(i.quantity) AS inventory
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
JOIN inventory i ON oi.product_id = i.product_id
WHERE o.status = 'fulfilled'
GROUP BY o.order_id
HAVING order_items != inventory;
```

---

### **2. NoSQL MongoDB Aggregation**
**Check**: "No duplicate emails in `users` collection."
```javascript
db.users.aggregate([
  { $group: {
      _id: "$email",
      count: { $sum: 1 },
      ids: { $push: "$_id" }
    }},
  { $match: { count: { $gt: 1 } } }
]);
```

---

### **3. Distributed Transaction Log Analysis**
**Check**: "Confirm all committed transactions appear in the ledger."
```bash
# Using a tool like Apache Kafka's `kafka-consumer-groups`
kafka-consumer-groups --bootstrap-server broker:9092 \
  --describe --group txn-processor \
  --match "txn-*"
```
*Follow-up*: Compare offsets with a database snapshot via:
```sql
SELECT COUNT(*) FROM transactions
WHERE id IN (SELECT id FROM kafka_log OFFSET 1000 LIMIT 1M);
```

---

### **4. Event-Sourced System Reconciliation**
**Check**: "Compare event counts between Kafka and database."
```python
# Pseudocode using `faust` (Kafka client)
from faust import KafkaHandler

async def event_count_mismatch(kafka_topic: KafkaHandler):
    kafka_count = await kafka_topic.count()
    db_count = await db.execute("SELECT COUNT(*) FROM events")
    if kafka_count != db_count:
        print(f"MISMATCH: Kafka={kafka_count}, DB={db_count}")
```

---

## **Automated Tooling**
| Tool               | Use Case                                      | Example Command                          |
|--------------------|-----------------------------------------------|------------------------------------------|
| **Jepsen**         | Test distributed systems for consistency bugs | `jepsen cassandra --test <script>`       |
| **Testcontainers** | Spin up ephemeral clusters for debugging      | `docker run testcontainers/postgresql`   |
| **Kubernetes**     | Probe pods for resource leaks                | `kubectl exec -it pod -- ps aux`         |
| **Prometheus**     | Alert on invariant violations                 | `sum(rate(violations_total[5m])) > 0`    |
| **Custom Agent**   | Poll APIs for invariants                      | `python3 invariant_checker.py --dry-run` |

---

## **Related Patterns**
1. **[Idempotency Ensuring](https://docs.microsoft.com/en-us/azure/architecture/patterns/idempotency)**
   - Design systems to handle duplicate operations safely (e.g., retrying a `POST /order`).
   - *Link*: Ensure consistency debugging aligns with idempotent endpoints.

2. **[Saga Pattern](https://microservices.io/patterns/data/saga.html)**
   - Manage distributed transactions via compensating actions.
   - *Link*: Use sagas to enforce invariants during long-running workflows.

3. **[CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)**
   - Separate read/writes to avoid consistency bottlenecks.
   - *Link*: Debugging may focus on event-sourced models in CQRS.

4. **[Circuit Breaker](https:// docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)**
   - Fail fast if invariants are violated repeatedly.
   - *Link*: Integrate circuit breakers with consistency alerts.

5. **[Time-Travel Debugging](https://temporal.io/blog/time-travel-debugging)**
   - Replay events to isolate root causes.
   - *Link*: Useful for debugging eventual consistency in event logs.

---
## **Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                                                 |
|-----------------------------------|----------------------------------------------------------------------------|
| **False Positives**               | Tune thresholds (e.g., allow ±1% variance for floating-point data).         |
| **Performance Overhead**          | Sample data or use probabilistic checks (e.g., [HyperLogLog](https://github.com/RedisInsight/RedisInsight/wiki/Redis-HyperLogLog)). |
| **State Drift**                   | Use [clock synchronization](https://en.wikipedia.org/wiki/Distributed_computing#Clock_synchronization) (e.g., NTP). |
| **Debugging Complex Workflows**    | Correlate traces with [W3C Trace Context](https://www.w3.org/TR/trace-context/). |
| **Schema Evolution**              | Version invariants (e.g., `v1` vs. `v2`).                                  |

---
## **Example Workflow**
1. **Define Invariants**:
   ```yaml
   # invariants.yml
   - id: "inv-balance"
     name: "Account Balance"
     type: "sum"
     entities:
       - collection: users
         field: balance
   ```
2. **Run Check**:
   ```bash
   ./consistency-debugger \
     --config invariants.yml \
     --db "postgresql://user:pass@host/db" \
     --sample-rate 0.1
   ```
3. **Analyze Results**:
   ```
   [FAIL] inv-balance: 10 accounts have negative balances.
   [CORRELATION] 5 of these failed a transaction retry (see #txn-456).
   ```
4. **Respond**:
   - Roll back `txn-456` via Saga compensator.
   - Adjust the invariant threshold or add a `min_balance` field.

---
**Further Reading**:
- [Google’s "How We Debugged a 60% Data Loss"](https://blog.golang.org/release-1.11)
- [Jepsen Framework](https://jepsen.io/) (for distributed system testing).
- [EventStoreDB’s Consistency Models](https://www.eventstore.com/vm-blog/post/20160425105240/Consistency_Models_in_Distributed_Systems).