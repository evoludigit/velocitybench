**[Pattern] Durability Troubleshooting Reference Guide**

---

### **Overview**
Durability failures occur when a system fails to persist or retrieve data reliably, often due to infrastructure, configuration, or application-level issues. This guide provides a structured approach to diagnosing, isolating, and resolving durability problems in distributed systems, microservices, or database-intensive applications. Focus areas include **data persistence issues**, **replication lag**, **transaction failures**, and **resilience misconfigurations**. By following the provided **schema**, **query examples**, and **best practices**, you can systematically identify root causes and apply fixes tailored to your architecture.

---

### **Key Concepts & Implementation Details**
Durability issues typically stem from one or more of the following:

| **Category**               | **Definition**                                                                                     | **Common Causes**                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Data Loss**              | Permanent or unintended data corruption/erasure.                                                  | Unstable storage (e.g., unreliable disks), improper backup policies, or unhandled application errors. |
| **Replication Lag**        | Delayed synchronization between primary and secondary nodes.                                       | Network bottlenecks, slow replication throughput, or high write load.                              |
| **Transaction Failures**   | Failed or incomplete transactions (e.g., timeouts, deadlocks, or partial writes).                 | Long-running transactions, insufficient connection pools, or misconfigured retry logic.             |
| **Resource Constraints**   | Insufficient system resources (CPU, memory, I/O) to sustain durability guarantees.              | Under-provisioned infrastructure, unoptimized queries, or cascading failures.                       |
| **Network Partitions**     | Temporary or permanent disconnections affecting data propagation.                                | Poor network design, unhandled disconnects, or undetected failures in distributed systems.         |

---

### **Durability Troubleshooting Schema**
Use the following schema to diagnose and categorize issues systematically.

#### **1. Initial Symptoms**
| Field            | Description                                                                                     | Example Values                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Symptom**      | High-level description of observed behavior (e.g., "Data deleted unexpectedly").               | "Transactions roll back without error", "Replication lag > 10 mins", "Backup fails intermittently" |
| **Frequency**    | Occurrence rate (e.g., sporadic, consistent, post-event).                                      | "Triggers after `update_user` operations", "Happens during peak load (>10k RPS)"                 |
| **Affected Components** | Systems/applications impacted (e.g., database, cache, microservice).                          | "PostgreSQL primary node", "Redis cluster Node B", "Order Service"                               |
| **Error Logs**   | Relevant error messages or stack traces.                                                       | `ERROR: pg_backend_pid:25604: FATAL: disk full`, `Timeout exceeded for replication slot`        |

---

#### **2. Root Cause Analysis**
| Field            | Description                                                                                     | Example Values                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Layer**        | Technical layer (e.g., storage, network, application).                                         | "Storage (disk I/O)", "Network (replication channel)", "Application (transaction timeout)"      |
| **Root Cause**   | Specific issue (e.g., disk full, misconfigured retry policy).                                  | "Disk space exhausted on `/var/lib/postgresql`", "Retry interval too short for timeouts"        |
| **Evidence**     | Logs, metrics, or diagnostic commands confirming the cause.                                   | `df -h | grep postgres` (shows 99% disk usage), `pg_repack` output (table corruption)                  |
| **Impact Scope** | Extent of the problem (e.g., single node, cluster-wide).                                       | "Affects only Node C", "Entire Elasticsearch cluster"                                              |

---
#### **3. Resolution Steps**
| Field            | Description                                                                                     | Example Values                                                                                     |
|------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Fix Type**     | Immediate (workaround) vs. Long-term (architectural).                                           | "Increase disk space", "Implement circuit breakers for retries"                                   |
| **Action**       | Specific action to resolve the issue.                                                           | `ALTER TABLE users REORGANIZE;`, `Adjust `max_replication_slots` in `postgresql.conf`            |
| **Verification** | How to confirm the fix worked.                                                                | "Check replication lag: `SELECT * FROM pg_stat_replication;`", "Verify backup success"           |
| **Prevention**   | Mitigation to avoid recurrence.                                                                | "Enable disk space monitoring alerts", "Add retries with exponential backoff"                     |

---

---
### **Query Examples for Diagnostics**
#### **1. Database-Level Checks**
| Purpose                          | Query (PostgreSQL)                                                                 | Purpose (Elasticsearch)                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Check replication lag**        | `SELECT * FROM pg_stat_replication;`                                                | `GET /_cat/recovery?pretty` (Kibana Dev Tools)                                           |
| **Identify slow transactions**   | `SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;`               | `GET /_nodes/stats/process/thread_pool` (for high CPU load)                              |
| **Find unclean shutdowns**       | `SELECT pg_is_in_recovery();`                                                       | `GET /_cluster/allocation/explain?pretty` (for unassigned shards)                           |
| **Disk space usage**             | `SELECT pg_database_size('*');`                                                     | `GET /_cat/allocation?v&h=node,shard,prirep&pretty`                                       |

#### **2. Application-Level Checks**
| Purpose                          | Command/Language Example                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------|
| **Check retry circuit breakers** | (Spring Boot) `management.endpoints.health.show-details=always`                          |
| **Log replication lag**          | (Python) `logger.warning(f"Replication lag: {lag_seconds}s")`                            |
| **Validate transaction IDs**     | (Java) `TransactionSynchronizationManager.isActualTransactionActive()`                    |

---
#### **3. Infrastructure-Level Checks**
| Purpose                          | Command                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------|
| **Network latency**              | `ping <database-node-ip>`                                                                 |
| **Disk I/O bottlenecks**         | `iostat -x 1` (Linux)                                                                     |
| **Load balancer health**         | `curl -I http://<load-balancer-ip>/health` (if applicable)                                 |
| **Replication lag monitoring**   | `watch -n 1 "pg_stat_replication"` (PostgreSQL)                                            |

---

### **Related Patterns**
1. **[Idempotency Pattern]**
   - *Why?* Ensures retries or duplicate operations don’t cause data corruption.
   - *Use with:* Durability troubleshooting for transactions where rollback is unsafe.

2. **[Circuit Breaker Pattern]**
   - *Why?* Prevents cascading failures during replication/network outages.
   - *Use with:* High-latency durability scenarios (e.g., microservices).

3. **[Compensating Transaction Pattern]**
   - *Why?* Rolls back partial operations if durability fails.
   - *Use with:* Distributed transactions requiring atomicity guarantees.

4. **[Backup & Restore Checksumming]**
   - *Why?* Validates data integrity after restores.
   - *Use with:* Recovery from disk corruption or accidental deletes.

5. **[Rate Limiting for Writes]**
   - *Why?* Prevents overload during high write volumes, reducing replication lag.
   - *Use with:* Systems with bursty durability requirements.

---
### **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| Ignoring **transaction timeouts**    | Set `timeout` based on workload (e.g., `SET LOCAL statement_timeout = '30s';`).                    |
| No **monitoring for replication lag** | Use tools like `pg_repack` or Elasticsearch’s `cluster-health` API with alerts.                 |
| **Disk space not monitored**         | Enable alerts for low disk space (e.g., Zabbix, Prometheus).                                      |
| **Retry logic without backoff**      | Implement exponential backoff (e.g., `retry: { max-attempts: 3, delay: 1s, multiplier: 2 }`). |
| **No **checksum validation** for backups | Use tools like `pg_basebackup --checkpoint=fast` or `elasticsearch-snapshot-restore`.          |

---
### **Example Workflow**
**Scenario:** Intermittent data loss in a PostgreSQL replica.
1. **Symptom:** `SELECT * FROM orders` returns fewer rows than the primary.
2. **Root Cause Analysis:**
   - **Layer:** Storage/Replication
   - **Evidence:** `pg_stat_replication` shows `lag = 5 mins`, disk I/O waits high.
   - **Root Cause:** Replication lag due to slow disk I/O on the replica.
3. **Resolution:**
   - **Fix:** Add a faster SSD to the replica (`/dev/sdb`).
   - **Verification:** `SELECT * FROM pg_stat_replication;` shows `lag < 1s`.
   - **Prevention:** Enable `wal_level = replica` and `max_wal_senders = 10`.

---
**Key Takeaway:** Durability issues are rarely one-dimensional. Use the schema to **categorize symptoms**, **query diagnostic tools**, and **apply targeted fixes**. Always validate with metrics and logs.