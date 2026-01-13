# **[Pattern] Durability Profiling Reference Guide**

---

## **Overview**
**Durability Profiling** is a **Software Architecture Pattern** used to assess how well a system recovers from failures, ensuring data integrity and operational resilience. This pattern involves measuring system behavior under stress, such as crashes, network partitions, or disk failures, to identify weak points in state persistence, transaction recovery, or retry logic. It is particularly useful for:
- **Distributed systems** (e.g., microservices, event-driven architectures)
- **Stateful applications** (e.g., databases, caches, session storages)
- **High-availability systems** (e.g., cloud-native applications)

By profiling durability, teams can validate that their fault tolerance mechanisms (e.g., writes-ahead logs, checkpointing, idempotent operations) function as expected before deployment.

---

## **Key Concepts & Implementation Details**

### **1. Core Objectives**
| Objective               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **State Recovery**      | Ensure the system can restore to a consistent state after a failure.        |
| **Failure Injection**   | Simulate crashes, timeouts, or data corruption to test resilience.         |
| **Retry & Idempotency** | Validate retry mechanisms and ensure operations remain safe after retries.  |
| **Logging & Observability** | Capture durability events (e.g., failed writes, recovery time) for analysis. |

### **2. Common Techniques**
| Technique               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Crash Injection**     | Forcefully terminate the system mid-operation to test recovery logic.       |
| **Disk Corruption**     | Simulate disk failures (e.g., via `fallocate`/`dd` or kernel modules).      |
| **Network Partitioning**| Isolate components to test distributed transaction rollbacks.                |
| **Slow/Failed Writes**  | Introduce delays or failures in storage operations (e.g., via `iptables`). |
| **Clock Skew**          | Test time-based retries by artificially delaying system clocks.              |

### **3. Profiling Workflow**
1. **Define Failure Scenarios**
   - Identify critical operations (e.g., database commits, message publishes).
   - Prioritize scenarios based on risk (e.g., data loss vs. degraded performance).

2. **Instrument the System**
   - **Logging**: Track durability events (e.g., `RECOVERY_STARTED`, `TRANSACTION_ROLLBACK`).
   - **Metrics**: Monitor recovery time, retry counts, and error rates.
   - **Telemetry**: Use tools like OpenTelemetry or Prometheus for distributed tracing.

3. **Inject Failures**
   - Use tools like:
     - **[Chaos Engineering](https://chaosspecialinterestgroup.org/)** (e.g., Gremlin, LitmusChaos).
     - **Custom Scripts** (e.g., `kill -9` for crash testing).
     - **Containerized Environments** (e.g., Kubernetes `podDisruptionBudget`).

4. **Analyze Recovery**
   - Check for:
     - **Data Consistency**: Verify post-recovery state matches expectations.
     - **Performance**: Measure recovery latency and throughput drops.
     - **Error Handling**: Ensure graceful degradation (e.g., circuit breakers).

5. **Iterate & Optimize**
   - Refine durability strategies (e.g., tune retry backoffs, optimize snapshots).
   - Document findings in a **durability report** (see *Schema Reference*).

---

## **Schema Reference**
Below are key schemas for documenting durability profiles.

### **1. Durability Profile Metadata (JSON)**
```json
{
  "profile_id": "durability-v1",
  "description": "Tests database commit recovery under disk failures",
  "created": "2023-10-15T14:30:00Z",
  "scenarios": [
    {
      "scenario_id": "disk_failure_post_commit",
      "description": "Simulate disk failure after a database commit",
      "preconditions": {
        "database": "PostgreSQL",
        "state": "active_transaction"
      },
      "failure_injection": {
        "type": "disk_corruption",
        "tool": "fallocate",
        "target": "/var/lib/postgresql/data"
      },
      "expected_behavior": {
        "recovery_time": "< 5s",
        "data_loss": "none"
      },
      "metrics": [
        {
          "name": "recovery_latency",
          "unit": "ms",
          "threshold": 5000
        },
        {
          "name": "retry_attempts",
          "type": "counter",
          "expected": 0
        }
      ]
    }
  ],
  "tools_used": ["Prometheus", "Chaos Mesh"],
  "status": "passed"
}
```

### **2. Durability Event Log (CSV)**
| **Timestamp**       | **Type**          | **Component** | **Details**                     | **Severity** |
|---------------------|-------------------|---------------|---------------------------------|--------------|
| 2023-10-15T14:32:00 | RECOVERY_STARTED  | DB Node 1     | Postgres WAL replay initiated   | INFO         |
| 2023-10-15T14:32:02 | RETRY_FAILED     | Message Queue | Max retries (3) exceeded       | WARNING      |
| 2023-10-15T14:32:05 | RECOVERY_COMPLETE | DB Cluster    | All nodes synced                | INFO         |

---

## **Query Examples**
Use these **SQL/NoSQL queries** to analyze durability metrics from logs or databases.

### **1. Find Failed Recovery Attempts (SQL)**
```sql
SELECT
  component,
  event_type,
  COUNT(*) as failure_count,
  AVG(recovery_latency_ms) as avg_latency
FROM durability_events
WHERE event_type = 'RECOVERY_FAILED'
  AND timestamp > '2023-10-01'
GROUP BY component, event_type
ORDER BY failure_count DESC;
```

### **2. Check Idempotency in Retries (NoSQL - MongoDB)**
```javascript
db.durability_logs.aggregate([
  { $match: { operation: "publish_event", status: "idempotent_failure" } },
  { $group: {
      _id: "$event_id",
      count: { $sum: 1 },
      last_attempt: { $max: "$attempt_number" }
  }},
  { $match: { count: { $gt: 1 } } }
]);
```

### **3. Alert on High Retry Rates (PromQL)**
```promql
rate(retry_attempts_total[5m] > 10)
  * on (service) group_left(service)
  service_discovery_up
  unless on(service) up == 1
```

---

## **Related Patterns**
| **Pattern**               | **Relation to Durability Profiling**                                                                 | **Tools/Libraries**                          |
|---------------------------|-------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Circuit Breaker**       | Complements durability testing by limiting cascading failures during recovery.                      | Hystrix, Resilience4j                       |
| **Event Sourcing**        | Useful for replaying state changes during durability tests.                                        | Apache Kafka, EventStoreDB                  |
| **Chaos Engineering**     | Framework for injecting failures to profile resilience.                                           | Gremlin, Chaos Mesh                         |
| **Idempotent Operations** | Ensures retries don’t cause duplicate side effects during recovery.                                | AWS SDK (Idempotency Keys)                  |
| **Saga Pattern**          | Helps test distributed transaction rollbacks in long-running processes.                             | Axon Framework, Camunda                     |

---

## **Best Practices**
1. **Start Small**: Profile one critical component at a time (e.g., a single database node).
2. **Automate Testing**: Integrate durability checks into CI/CD (e.g., GitHub Actions + Chaos Mesh).
3. **Document Failures**: Use the schema above to track scenarios and outcomes.
4. **Prioritize Recovery Time**: Focus on SLAs for critical systems (e.g., < 1s recovery for payment processing).
5. **Test in Production-Like Environments**: Use staging clusters mirroring production topology.

---
**Further Reading**:
- [Chaos Engineering Handbook](https://www.chaosengineering.io/handbook/)
- [ACID vs. BASE: Durability Tradeoffs](https://martinfowler.com/articles/acid-transactions.html)
- [Kubernetes Durability Patterns](https://kubernetes.io/docs/concepts/cluster-administration/)