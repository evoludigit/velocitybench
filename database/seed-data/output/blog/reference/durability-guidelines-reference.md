**[Pattern] Durability Guidelines Reference Guide**

---

# **Overview**
The **Durability Guidelines** pattern ensures that your system maintains data consistency and resilience across failures by defining explicit rules for handling inevitable data loss or corruption. This pattern is critical for distributed systems, where nodes may fail, networks partition, or data become inconsistently replicated. By standardizing durability requirements, teams can proactively mitigate risks, balance performance vs. reliability trade-offs, and align architecture decisions with business continuity needs. This guide outlines key concepts, implementation strategies, and schema references to operationalize durability in your system.

---

## **Key Concepts**
Durability guarantees are categorized by their failure scenarios and recovery mechanisms:

| **Term**               | **Definition**                                                                                     | **Implementation Example**                                  |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Strong Durability**  | Data is safely written to a majority of replicas before acknowledgment.                            | Multi-node commit logs with quorum-based writes (e.g., ZooKeeper). |
| **Eventual Durability**| Data is eventually synchronized across all replicas without immediate acknowledgment.            | Asynchronous replication to backup nodes (e.g., Kafka).     |
| **At-Least-Once Durability** | Ensures no data loss but may duplicate writes due to retries.                                      | Idempotent operations with retry logic (e.g., HTTP POSTs with `idempotency-key`). |
| **Failure Modes**      | **Network Partition**: Splits system into isolated subsets.<br>**Node Failure**: Replica crashes.<br>**Storage Corruption**: Media failure. | Use consensus protocols (e.g., Paxos/Raft) for partitions.   |
| **Recovery Strategies**| **Point-in-Time Recovery**: Restore from backups.<br>**Log Replay**: Reconstruct state from logs. | Append-only logs (e.g., WAL) + periodic snapshots.           |
| **Trade-offs**         | **Latency vs. Reliability**: Strong durability adds overhead.<br>**Consistency vs. Availability**: CAP Theorem trade-offs. | Prioritize durability for critical paths (e.g., financial transactions). |

---

## **Schema Reference**
Below is a schema for defining durability requirements in a system. Use this as a template to document durability policies across services.

| **Field**               | **Type**       | **Description**                                                                                     | **Default Example**          | **Notes**                                  |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|-------------------------------|--------------------------------------------|
| `pattern_name`          | String         | Name of the pattern (e.g., "DurabilityGuidelines").                                                 | `durability_guidelines`       | Used for cross-service alignment.        |
| `requirements`          | Array[Object]  | List of durability rules per component (e.g., database, cache).                                    | `{ "strong": true }`          | Combine multiple requirements.           |
| `requirements.*`        | Object         | Durability constraints for a component.                                                            |                               |                                            |
| `requirements.*type`    | String         | Scope of durability (e.g., "write", "read", "transaction").                                         | `write`                       |                                            |
| `requirements.*level`   | String         | Durability level: `strong`, `eventual`, `at_least_once`, or `none`.                               | `strong`                     |                                            |
| `requirements.*failure_modes` | Array[String] | Failures this must survive (e.g., `["node_failure", "network_partition"]`).                    | `["node_failure"]`            |                                            |
| `requirements.*timeout_ms` | Integer       | Max time to acknowledge durability (e.g., 5000 for 5s).                                            | `3000`                        |                                            |
| `recovery_strategy`     | String         | Method for recovery (e.g., "snapshot", "log_replay", "manual").                                    | `log_replay`                  |                                            |
| `trade_off_notes`       | String         | Justification for chosen trade-offs (e.g., "Latency increased by 20% for 99.99% uptime").         | N/A                           | Critical for design reviews.              |
| `components`            | Array[String]  | Services affected (e.g., `["order_service", "payment_processor"]`).                                | `["order_service"]`           |                                            |
| `version`               | String         | Schema version for backward compatibility.                                                          | `"1.0"`                       |                                            |

**Example JSON Configuration:**
```json
{
  "pattern_name": "durability_guidelines",
  "requirements": [
    {
      "type": "write",
      "level": "strong",
      "failure_modes": ["node_failure"],
      "timeout_ms": 3000,
      "components": ["order_service"]
    },
    {
      "type": "transaction",
      "level": "at_least_once",
      "recovery_strategy": "log_replay",
      "trade_off_notes": "Accepts duplicate invoices to ensure no loss."
    }
  ],
  "version": "1.0"
}
```

---

## **Implementation Details**
### **1. Define Durability Policies Per Service**
- **Example for a Payment Service**:
  - **Write Durability**: Strong (quorum-based writes to 3 replicas).
  - **Failure Modes**: Node failures and network partitions.
  - **Recovery**: Log replay from WAL + manual override for critical data.

- **Example for a Cache Layer**:
  - **Write Durability**: Eventual (asynchronous sync to backup cache nodes).
  - **Failure Modes**: Node failures only.
  - **Recovery**: Cache warm-up from primary node.

### **2. Align with Data Models**
| **Data Type**       | **Durability Level** | **Implementation**                          | **Example**                                  |
|---------------------|----------------------|---------------------------------------------|----------------------------------------------|
| Transaction Logs    | Strong               | Append-only WAL with quorum commits.        | PostgreSQL `fsync` + `synchronous_commit=on`. |
| User Preferences    | Eventual             | Async replication to secondary nodes.       | Redis Cluster with `replicaof`.              |
| Audit Logs          | At-Least-Once        | Idempotent writes with deduplication.       | Kafka topic with `min.insync.replicas=2`.    |

### **3. Monitoring and Validation**
- **Metrics to Track**:
  - `durability_acknowledged_latency`: Time to confirm write durability.
  - `durability_failure_rate`: % of writes failing durability checks.
  - `recovery_time_objective`: RTO for restoring from backups.
- **Validation Tools**:
  - **Unit Tests**: Simulate node failures during write operations.
  - **Chaos Engineering**: Inject partitions (e.g., using Chaos Mesh) to test eventual consistency.

### **4. Handling Edge Cases**
| **Scenario**               | **Solution**                                                                                     | **Tools/Libraries**                     |
|----------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| **Disk Full**              | Pause writes; trigger backup cleanup.                                                          | Custom monitoring + alerting.           |
| **Network Partition**      | Promote a replica leader (if using consensus).                                                 | Raft/Paxos libraries.                   |
| **Corrupted Data**         | Roll back to last consistent snapshot.                                                         | Time-travel queries (e.g., Delta Lake).  |
| **Slow Replicas**          | Time out and retry with stronger consistency guarantees.                                        | Custom retry logic + circuit breakers.   |

---

## **Query Examples**
### **1. Query Durability Requirements for a Service**
```sql
SELECT *
FROM durability_configurations
WHERE components = 'order_service'
AND requirements.type = 'write';
```
**Result**:
```json
{
  "requirements": [
    {
      "type": "write",
      "level": "strong",
      "failure_modes": ["node_failure", "network_partition"],
      "timeout_ms": 5000
    }
  ]
}
```

### **2. Check Replica Health for Strong Durability**
```bash
# Example: Verify quorum for strong durability in ZooKeeper
echo stat | nc localhost 2181
```
**Output**:
```
Mode: leader
...
Number of live connections: 3/3
```
*(Indicates 3/3 replicas are healthy.)*

### **3. Simulate Recovery Time for a Component**
```python
# Pseudocode to benchmark recovery from WAL
def test_recovery_time():
    start_time = time.time()
    replay_logs_from_snapshot()  # Custom function
    end_time = time.time()
    return end_time - start_time
print(f"Recovery took {test_recovery_time():.2f}s")
```

---

## **Related Patterns**
| **Pattern**                     | **Relation to Durability Guidelines**                                                                 | **When to Use Together**                          |
|---------------------------------|-------------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **[Idempotency Key Pattern]**   | Ensures retries don’t cause duplicate side effects, critical for `at_least_once` durability.        | When implementing retry logic.                    |
| **[Circuit Breaker Pattern]**   | Prevents cascading failures during node recoveries, protecting durability guarantees.               | For services with high failure rates.             |
| **[Saga Pattern]**              | Manages distributed transactions with compensating actions; aligns with eventual durability.       | For long-running processes (e.g., order fulfillment). |
| **[Leader Election]**           | Ensures single-writer consistency in partitioned systems (e.g., Raft).                               | When using strong durability across nodes.         |
| **[Backpressure]**               | Controls load to avoid overwhelming replicas during failures.                                       | During recovery phases or high-latency writes.     |

---

## **Best Practices**
1. **Start Conservative**: Default to `strong` durability for critical data, then optimize.
2. **Document Trade-offs**: Clearly state latency/availability impacts in design docs.
3. **Automate Validation**: Integrate durability checks into CI/CD pipelines.
4. **Isolate Durability Boundaries**: Use explicit layers (e.g., database vs. cache).
5. **Test Recovery Scenarios**: Simulate worst-case failures quarterly.

---
**Further Reading**:
- [CAP Theorem](https://en.wikipedia.org/wiki/CAP_theorem)
- [CRDTs for Eventual Consistency](https://crdt.tech/)
- [PostgreSQL Durability Settings](https://www.postgresql.org/docs/current/runtime-config-wal.html)