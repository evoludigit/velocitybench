**[Pattern] Failover Debugging Reference Guide**

---

### **Overview**
Failover debugging is a systematic approach to diagnosing and resolving system failures when primary components (e.g., servers, services, or databases) transition to secondary (backup) systems. This pattern ensures high availability by identifying root causes, log discrepancies, and configuration mismatches between primary and failover states. It applies to distributed systems, cloud deployments, and on-premises environments where redundancy is critical. Key goals include minimizing downtime, validating failover triggers, and restoring services efficiently while preserving transactional consistency.

---

### **Key Concepts & Requirements**
#### **Core Principles**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Primary/Secondary** | Primary: Active system handling requests; Secondary: Backup system waiting for activation. |
| **Failover Trigger**  | Event (e.g., hardware failure, network split, health check) initiating failover. |
| **Synchronization**   | Ensuring data/state consistency between primary and secondary before/after failover. |
| **Rollback**          | Reverting to primary if failover exposes issues (e.g., corrupted state).      |
| **Health Checks**     | Proactive monitoring to detect pre-failover degradation.                     |

#### **Preconditions**
- **Redundancy**: At least one secondary system must mirror critical components.
- **Logging**: Standardized logs for primary/secondary with timestamps and severity.
- **Metrics**: Performance monitoring (e.g., latency, error rates) to detect anomalies.
- **Alerting**: Configurations for alerts on failover events or degraded states.

---

### **Implementation Details**
#### **Step 1: Validate Failover Trigger**
1. **Check Logs**:
   - Primary: Look for logs indicating the trigger (e.g., `CRITICAL: Disk failure detected`).
   - Secondary: Verify failover initiation logs (e.g., `INFO: Promoted to primary at 15:30 UTC`).
   - *Tools*: Use regex or log analysis tools (e.g., ELK Stack, Splunk) to filter timestamps.

2. **Review Metrics**:
   - Correlate logs with metrics (e.g., high CPU on primary → failover).
   - Example query for Prometheus:
     ```sql
     sum(rate(node_cpu_seconds_total{mode="failover_triggered"}[5m])) by (instance)
     ```

#### **Step 2: Assess State Consistency**
1. **Data Synchronization**:
   - Compare primary/secondary database snapshots or transaction logs.
   - Use checksums or diff tools (e.g., `git diff`, `pg_dump` for PostgreSQL).
   - *Example*: For Kafka, check `offsets` consistency:
     ```bash
     kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
     ```

2. **Application State**:
   - Verify state machines (e.g., Redis sessions) are replicated.
   - Check reactive services (e.g., Spring Cloud Gateway) for stale routes.

#### **Step 3: Debug Failover Execution**
1. **Network Isolation**:
   - Confirm DNS changes (e.g., `A` records updated for secondary IP).
   - Validate load balancer rules (e.g., AWS ALB health checks passed for secondary).

2. **Load Testing**:
   - Simulate traffic on secondary to verify no degraded performance.
   - Tools: Locust, JMeter.

3. **Rollback Testing**:
   - Force a rollback to primary and confirm:
     - No data loss.
     - No orphaned transactions (e.g., in 2PC systems).

#### **Step 4: Log Analysis Framework**
| **Log Type**          | **Primary Focus**                          | **Secondary Focus**                     |
|-----------------------|--------------------------------------------|-----------------------------------------|
| **Application Logs**  | Failed requests before failover.            | Promoted state verification.            |
| **Database Logs**     | Replication lag or errors.                 | Standby recovery confirmation.          |
| **Infrastructure**    | VM/network changes (e.g., `gcloud compute` logs). | Failover script executions.          |

*Example Query for SQL Replication Lag*:
```sql
SELECT * FROM performance_schema.replication_group_member_stats
WHERE GROUP_NAME = 'cluster1' ORDER BY SECONDS_BEHIND_MASTER DESC;
```

---

### **Schema Reference**
| **Component**               | **Schema Example**                          | **Purpose**                                  |
|-----------------------------|--------------------------------------------|---------------------------------------------|
| **Failover Event Log**      | `failover_events(table: id, timestamp, cause, primary_ip, secondary_ip)` | Track trigger and system states.            |
| **Health Check Metrics**    | `healthchecks(table: check_id, timestamp, status, score)` | Monitor pre-failover health.               |
| **Replication Status**      | `replication_status(table: source, target, lag_seconds, error)` | Validate data sync.                        |
| **Failover Script Logs**    | `script_logs(table: script, command, exit_code, duration_ms)` | Debug automation failures.                 |

---

### **Query Examples**
#### **1. Find Failover Events with High Replication Lag**
```sql
SELECT f.timestamp, f.cause, r.lag_seconds
FROM failover_events f
JOIN replication_status r ON f.id = r.failover_event_id
WHERE r.lag_seconds > 10000 AND f.cause LIKE '%failure%';
```

#### **2. Identify Stale Health Checks**
```sql
SELECT check_id, timestamp
FROM healthchecks
WHERE status = 'failed' AND timestamp > DATEADD(hour, -1, GETDATE())
GROUP BY check_id
HAVING COUNT(*) > 3;
```

#### **3. Correlate Failover with Metrics Spikes**
```sql
-- PromQL (Prometheus)
rate(http_request_duration_seconds_count[5m])
/ on(instance)
rate(http_request_duration_seconds_sum[5m])
where {failover_event = "true"} > 10000;
```

---

### **Common Pitfalls & Mitigations**
| **Pitfall**                     | **Mitigation**                                      |
|----------------------------------|-----------------------------------------------------|
| **Unsynchronized Data**         | Use CDC (Change Data Capture) for real-time sync.    |
| **Overhead in Secondary**       | Optimize replication lag (e.g., PostgreSQL async).   |
| **Silent Failures**              | Enable comprehensive logging and alerts.            |
| **Manual Rollback Errors**       | Automate rollback validation (e.g., pre-checks).    |

---

### **Related Patterns**
1. **Circuit Breaker**: Complementary to failover; prevents cascading failures during debugging.
2. **Bulkhead**: Isolate failover components to contain issues.
3. **Retry with Backoff**: Used post-failover to recover gracefully.
4. **Distributed Tracing**: Trace requests across primary/secondary state changes.
5. **Chaos Engineering**: Proactively test failover resilience (e.g., using Chaos Monkey).

---
### **Tools & Libraries**
| **Category**               | **Tools/Libraries**                              |
|----------------------------|--------------------------------------------------|
| **Debugging**              | JStack (Java heap analysis), `strace` (Linux syscalls). |
| **Replication Checks**     | `pg_isready` (PostgreSQL), `kafka-consumer-groups`. |
| **Log Analysis**           | Loki, Datadog, OpenSearch.                       |
| **Automation**             | Ansible (failover playbooks), Kubernetes HPA.    |

---
**Note**: Always start debugging with the **failover trigger** before diving into logs or state validation. Use the schema tables to correlate events systematically. For complex systems, involve domain experts (e.g., DBAs) familiar with replication tech stacks.