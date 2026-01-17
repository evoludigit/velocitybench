# **[Pattern] Failover Migration Reference Guide**

## **Overview**
The **Failover Migration** pattern enables seamless data or service migration between environments (e.g., primary and secondary systems) with minimal downtime. This pattern is critical for high-availability (HA) systems, disaster recovery (DR), and multi-region deployments, ensuring continuity when a primary system fails.

Failover migration involves **synchronized data replication**, **automatic failover detection**, and **switching traffic** to a secondary system without user interruptions. It integrates with **event-driven architectures**, **circuit breakers**, and **asynchronous processing** to handle failures gracefully.

This guide covers key concepts, implementation steps, schema references, and related patterns to help architects and engineers design resilient systems.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                 | **Key Considerations**                                                                 |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Primary System**     | The active system serving live traffic.                                        | Must support real-time synchronization with secondary systems.                      |
| **Secondary System**   | The standby system (e.g., DR site, backup database).                          | Should be kept in sync (or near-sync) with the primary system.                     |
| **Synchronization Layer** | Mechanisms (e.g., CDC, Change Data Capture, log replication) to keep systems in sync. | Low-latency replication is critical; tolerance for drift must be defined.       |
| **Failover Trigger**   | Detects primary system failure (e.g., health checks, heartbeat monitoring).   | Must be fault-tolerant to avoid false positives/negatives.                            |
| **Traffic Switcher**   | Router/DNS-based mechanism to redirect traffic to the secondary system.       | Should support **active-active** or **active-passive** failover modes.               |
| **Recovery Orchestrator** | Automates rollback to primary system post-repair.                             | Must handle partial failures and cascading rollbacks.                                |
| **Audit & Rollback**   | Logs migration changes for accountability and undo operations.                 | Must support point-in-time recovery (PITR).                                          |

---

### **2. Synchronization Strategies**
| **Strategy**               | **Description**                                                                 | **Use Case**                                                                         | **Pros**                          | **Cons**                          |
|----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|
| **Synchronous Replication** | Primary system waits for confirmation before committing changes.             | Low-tolerance environments (e.g., financial transactions).                         | Strong consistency.               | High latency, single point of failure. |
| **Asynchronous Replication** | Primary commits changes immediately; secondary updates later.                 | High-throughput systems (e.g., logs, analytics).                                   | Scalable, low latency.            | Risk of data loss on failure.      |
| **Quorum-Based Replication** | Requires majority acknowledgment for commit (e.g., Raft, Paxos).            | Distributed systems (e.g., databases, Kafka).                                     | Fault-tolerant, no single PoF.    | Complex coordination overhead.    |
| **Change Data Capture (CDC)** | Captures and streams changes (e.g., Debezium, Kafka Connect).                | Real-time ETL, microservices.                                                      | Near real-time sync.              | Requires CDC infrastructure.      |

---

### **3. Failover Detection Mechanisms**
| **Mechanism**            | **How It Works**                                                                 | **Example Tools**                                                                   |
|--------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Heartbeat Monitoring** | Primary system sends periodic pings; secondary detects silence.               | Prometheus, Nagios.                                                              |
| **Health Check Endpoints** | Secondary probes primary for liveness/readiness (e.g., HTTP 200/5xx responses). | Kubernetes LivenessProbes, AWS Health API.                                         |
| **Database Replication Lag** | Monitors replication lag (e.g., `pg_isready`, `SHOW REPLICA STATUS`).        | PostgreSQL, MySQL.                                                                |
| **Distributed Locks**    | Uses consensus algorithms (e.g., ZooKeeper, Etcd) to detect leader failures.   | Apache ZooKeeper, Consul.                                                        |
| **Application-Level Failover** | Business logic detects failures (e.g., timeouts, errors).                   | Custom retry circuits (e.g., Resilience4j).                                       |

---

### **4. Traffic Switching Methods**
| **Method**               | **Description**                                                                 | **Pros**                          | **Cons**                          |
|--------------------------|-------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|
| **DNS-Based Failover**   | Updates DNS records to point to secondary (e.g., via TTL changes).            | Simple, no client-side changes.   | Slow (TTL-dependent), not real-time. |
| **Load Balancer Redirect** | Load balancer (e.g., HAProxy, AWS ALB) reroutes traffic.                     | Fast, dynamic.                    | Requires LB configuration.        |
| **Service Mesh**         | Istio, Linkerd intercept traffic and route based on health checks.           | Fine-grained control.              | Steeper learning curve.           |
| **Client-Side Failover** | Clients poll a failover API to determine the active endpoint.               | Decentralized control.            | Adds complexity to client apps.   |
| **Database Router**      | SQL routers (e.g., PgBouncer, ProxySQL) switch reads/writes dynamically.     | Works at DB level.                | Limited to database workloads.    |

---

### **5. Rollback & Recovery**
- **Automatic Rollback**: If the primary system recovers, traffic is routed back via:
  - **Health checks** (e.g., primary responds → switch back).
  - **Manual override** (admin-triggered via CLI/API).
- **Data Synchronization**:
  - **For synchronous replication**: Secondary must be **caught up** before reassigning primary role.
  - **For CDC/async replication**: Use **binlog replay** or **transaction log recovery**.
- **Audit Logs**:
  - Track failover events (e.g., timestamps, affected data, recovery steps).
  - Example fields:
    ```json
    {
      "event": "failover_triggered",
      "timestamp": "2024-05-20T12:00:00Z",
      "primary": "db-primary-1",
      "secondary": "db-secondary-1",
      "reason": "health_check_failure",
      "data_lag": "5s",
      "recovery_status": "in_progress"
    }
    ```

---

## **Schema Reference**

### **1. Database Replication Schema**
| **Field**               | **Type**       | **Description**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------|
| `replication_group_id`  | UUID           | Unique identifier for the replication pair.                                     |
| `primary_host`         | VARCHAR(255)   | Current primary system endpoint (e.g., `db-primary.example.com`).               |
| `secondary_host`       | VARCHAR(255)   | Secondary system endpoint.                                                      |
| `sync_method`          | ENUM           | `synchronous`, `asynchronous`, `cdc`, `quorum`.                                  |
| `replication_lag`      | TIME           | Current lag between primary and secondary (e.g., `00:00:05`).                   |
| `last_failover_time`   | TIMESTAMP      | Timestamp of last failover event.                                               |
| `failover_state`       | ENUM           | `active`, `recovering`, `failed`, `manual_override`.                            |
| `recovery_progress`    | FLOAT(0,2)     | % completion of recovery (0–100).                                               |

**Example Query:**
```sql
SELECT
    replication_group_id,
    primary_host,
    secondary_host,
    sync_method,
    replication_lag,
    failover_state
FROM replication_status
WHERE failover_state = 'recovering';
```

---

### **2. Failover Event Log Schema**
| **Field**               | **Type**       | **Description**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------|
| `event_id`              | BIGINT         | Auto-incremented event ID.                                                      |
| `timestamp`            | TIMESTAMP      | When the event occurred.                                                         |
| `replication_group_id` | UUID           | Associated replication group.                                                   |
| `event_type`           | ENUM           | `failover_triggered`, `rollback_started`, `recovery_complete`.                 |
| `details`              | JSON           | Structured event data (e.g., reason, affected systems).                          |
| `status`               | ENUM           | `success`, `partial`, `failed`, `pending`.                                       |

**Example JSON Payload for `details`:**
```json
{
  "reason": "primary_db_crash",
  "affected_systems": ["db-primary-1", "app-service-1"],
  "data_loss_estimated": "0 records",
  "recovery_instructions": "Run 'pg_rewind' to restore secondary."
}
```

---

## **Query Examples**

### **1. Check Replication Health**
```sql
-- PostgreSQL: Check replication lag
SELECT
    pg_is_in_recovery() AS is_replica,
    pg_current_wal_lsn() AS primary_lsn,
    pg_last_wal_receive_lsn() AS replica_lsn,
    pg_current_wal_lsn() - pg_last_wal_receive_lsn() AS lag_bytes
FROM pg_stat_replication;
```

### **2. List Failover Events**
```sql
-- Filter failover events for a specific group
SELECT
    timestamp,
    event_type,
    details->>'reason' AS reason,
    status
FROM failover_events
WHERE replication_group_id = '123e4567-e89b-12d3-a456-426614174000'
ORDER BY timestamp DESC
LIMIT 10;
```

### **3. Update Failover State**
```sql
-- Manually override failover (e.g., promote secondary)
UPDATE replication_status
SET
    primary_host = 'db-secondary-1',
    failover_state = 'active'
WHERE replication_group_id = '123e4567-e89b-12d3-a456-426614174000';
```

### **4. Detect Stalled Replication**
```python
# Python (using psycopg2) to check replication lag
import psycopg2

conn = psycopg2.connect("dbname=replication_metrics")
cursor = conn.cursor()
cursor.execute("""
    SELECT
        pg_is_in_recovery(),
        EXTRACT(EPOCH FROM (now() - pg_last_wal_receive_lsn()::timestamp)) AS lag_seconds
    FROM pg_stat_replication;
""")
lag = cursor.fetchone()[1]
if lag > 30:  # Threshold: 30s
    print("WARNING: Replication lag > 30s")
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                         | **Integration Points**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Temporarily stops calls to a failing service.                                      | High-latency or unstable systems.                                                      | Failover triggers can act as a circuit breaker.                                      |
| **[Saga Pattern](https://microservices.io/patterns/data/transactional-outbox.html)** | Manages distributed transactions via compensating actions.                       | Microservices with ACID-like guarantees across services.                               | Rollback logic in failover can use saga steps.                                        |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Stores state as a sequence of events.                                            | Systems requiring audit trails or time-travel debugging.                              | CDC-based failover syncs can leverage event streams.                                  |
| **[Bulkhead](https://microservices.io/patterns/reliability/bulkhead.html)** | Isolates failures to prevent cascading.                                           | Resilient microservices under load.                                                   | Failover can be triggered if bulkhead limits are hit.                                 |
| **[Database Sharding](https://martinfowler.com/eaaCatalog/databaseSharding.html)**  | Splits data across multiple DB instances.                                           | Horizontal scaling for read-heavy workloads.                                           | Failover can involve reassigning shards to secondary nodes.                            |
| **[Chaos Engineering](https://chaosengineering.io/)** | Proactively tests system resilience.                                              | Pre-failover testing and recovery validation.                                           | Failover patterns are validated via chaos experiments (e.g., kill primary node).    |

---

## **Best Practices**
1. **Define Recovery SLAs**: Set acceptable replication lag (e.g., < 5s).
2. **Test Failover Regularly**: Simulate failures in staging (e.g., `kill -9` primary process).
3. **Monitor Drift**: Use tools like **Prometheus + Grafana** to alert on replication lag.
4. **Minimize Data Loss**: For async replication, use **write-ahead logs (WAL)** or **CDC with timestamps**.
5. **Automate Rollback**: Implement a recovery script to re-promote the primary post-fix.
6. **Document Procedures**: Define step-by-step recovery playbooks (e.g., `FAILOVER_PROCEDURES.md`).
7. **Use Idempotent Operations**: Ensure failover actions can be retried without side effects.
8. **Limit Failover Scope**: Failover only critical services; others can degrade gracefully.

---
## **Example Architecture Diagram**
```
┌───────────────────────┐       ┌───────────────────────┐
│                       │       │                       │
│   Primary System      │──────▶│   Load Balancer      │
│   (Active)            │       │                       │
│                       │       └───────────────────────┘
└───────────────┬───────┘               ▲
                │                    │
                ▼                    │
┌───────────────────────┐       ┌───────────────────────┐
│                       │       │                       │
│   Async CDC Pipeline  │       │   Secondary System    │
│   (Debezium/Kafka)    │◀──────│   (Standby)           │
│                       │       │                       │
└───────────────┬───────┘       └───────────────────────┘
                │
                ▼
┌───────────────────────┐
│                       │
│   Failover Orchestrator│
│   (Kubernetes/CLI)    │
│                       │
└───────────────┬───────┘
                │
                ▼
┌───────────────────────┐
│                       │
│   Audit & Alerts      │
│   (Prometheus/Grafana)│
│                       │
└───────────────────────┘
```