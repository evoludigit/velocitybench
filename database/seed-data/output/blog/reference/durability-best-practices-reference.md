# **[Pattern] Durability Best Practices – Reference Guide**

---

## **Overview**
Durability best practices ensure that applications reliably persist critical data, recover from failures, and maintain consistency across distributed systems. This pattern emphasizes **atomicity, consistency, isolation, and durability (ACID)** principles, **replication**, **backup strategies**, **error handling**, and **recovery mechanisms** to minimize data loss and ensure system resilience. Common use cases include financial transactions, healthcare records, supply chain tracking, and mission-critical databases. By implementing these practices, developers can mitigate risks of lost updates, partial writes, and unrecoverable failures while maintaining performance and scalability.

---

## **Schema Reference**

| **Category**               | **Component**                     | **Description**                                                                                     | **Example Technologies/Tools**                     |
|----------------------------|-----------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Data Storage**           | ACID-Compliant Database            | Relational or NoSQL databases that support transactions, consistency checks, and crash recovery.   | PostgreSQL, Oracle DB, MongoDB (with WiredTiger)   |
|                            | Distributed Transactions           | Protocols ensuring consistency across multiple systems (e.g., **Saga Pattern**, **Two-Phase Commit**). | Apache Kafka, Saga libraries, SagaJS                |
| **Replication & Redundancy** | Master-Slave Replication          | Synchronize data copies across multiple nodes for fault tolerance.                                 | MySQL Replication, Cassandra, etcd                  |
|                            | Multi-Region Replication          | Replicate data globally with low latency for disaster recovery.                                     | AWS Global Table, Google Cloud Spanner              |
| **Backup & Recovery**      | Automated Backups                  | Scheduled snapshots, differential backups, or continuous archiving.                                | pg_dump (PostgreSQL), AWS RDS Snapshots, BackupPC   |
|                            | Point-in-Time Recovery (PITR)      | Restore data to a specific timestamp after corruption or failure.                                   | PostgreSQL WAL Archiving, TimeScaleDB               |
| **Error Handling**         | Retry Policies                    | Exponential backoff for transient failures (e.g., network timeouts).                              | Resilience4j, Axon Framework                       |
|                            | Dead Letter Queues (DLQ)           | Isolate failed operations for manual review or reprocessing.                                      | RabbitMQ, Apache Kafka DLQ                          |
| **Consistency Mechanisms** | Conflict-Free Replicated Data Type (CRDT) | Eventually consistent data structures for offline-first applications.                          | Yjs,-Otto, Automerge                               |
|                            | Quorum-Based Writes               | Require a majority of replicas to acknowledge writes before committing.                           | DynamoDB, Cassandra                               |
| **Audit & Monitoring**     | Change Data Capture (CDC)         | Real-time tracking of data changes for auditing and replay.                                         | Debezium, AWS DMS                                  |
|                            | Observability Tools               | Logs, metrics, and traces to detect failures and bottlenecks.                                      | Prometheus, Grafana, OpenTelemetry                 |
| **Application Design**     | Idempotent Operations             | Ensure repeated identical requests don’t cause unintended side effects.                          | UUID-based request IDs, Saga Patterns              |
|                            | Checkpointing                     | Periodically save application state to disk for recovery.                                          | Akka Persistence, Kafka Streams                    |

---

## **Implementation Details**

### **1. Choose the Right Storage Model**
- **ACID Databases**: Use for strong consistency (e.g., PostgreSQL, SQL Server).
  - *Example*: Financial transactions requiring exact balance updates.
- **Eventual Consistency**: Use for high availability (e.g., DynamoDB, Cassandra).
  - *Example*: Social media feeds where stale data is acceptable.
- **Hybrid Approach**: Combine ACID for critical paths and eventual consistency for secondary data.

### **2. Implement Replication Strategies**
| **Strategy**               | **Use Case**                          | **Trade-offs**                                  |
|----------------------------|---------------------------------------|-------------------------------------------------|
| **Synchronous Replication** | High availability (e.g., banking).   | Higher latency; risk of write failures.         |
| **Asynchronous Replication** | Low-latency writes (e.g., logs).     | Risk of data loss during replication lag.       |
| **Multi-Lead Replication**   | Global scalability (e.g., e-commerce). | Complex conflict resolution.                    |

### **3. Backup and Recovery**
- **Full Backups**: Complete database snapshots (e.g., `mysqldump` for MySQL).
- **Incremental Backups**: Only store changes since the last backup (reduces storage costs).
- **WAL (Write-Ahead Log) Archiving**:
  - Critical for crash recovery (e.g., PostgreSQL’s `pg_wal`).
  - Enable point-in-time recovery (PITR) with `pg_restore`.
- **Geographically Distributed Backups**:
  - Use cloud providers (AWS S3, Azure Blob) for offline cold storage.
  - Rotate backups to avoid single points of failure.

### **4. Handle Failures Gracefully**
- **Retry Logic**:
  - Exponential backoff for transient errors (e.g., `retry(backoffExponential)` in Resilience4j).
  - Avoid retries for idempotent operations (e.g., `PUT` requests).
- **Circuit Breakers**:
  - Stop retrying after repeated failures (e.g., Hystrix, Resilience4j).
  - Example:
    ```java
    CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("database-connector");
    circuitBreaker.executeSupplier(() -> queryDatabase());
    ```
- **Dead Letter Queues (DLQ)**:
  - Route failed messages to a DLQ for later inspection.
  - Example (Kafka):
    ```yaml
    producer:
      properties:
        delivery.timeout.ms: 120000
        max.in.flight.requests.per.connection: 1
    ```

### **5. Ensure Data Integrity**
- **Atomic Transactions**:
  - Use `BEGIN`, `COMMIT`, `ROLLBACK` in SQL.
  - For distributed transactions, consider **Saga Pattern**:
    ```mermaid
    graph LR
      A[Order Created] -->|Publish Event| B[Inventory Checked]
      B -->|Publish Event| C[Payment Processed]
      C -->|Publish Event| D[Order Fulfilled]
      D -->|Rollback Events| A
    ```
- **Checksums & Hashes**:
  - Validate data integrity with SHA-256 (e.g., checksum files for backups).
- **Immutable Logs**:
  - Append-only logs (e.g., Kafka, Bigtable) prevent tampering.

### **6. Optimize for Performance**
- **Indexing**: Add indexes to frequently queried columns (e.g., `WHERE created_at > '2023-01-01'`).
- **Caching**:
  - Use Redis or Memcached for read-heavy workloads.
  - Invalidate cache on write operations.
- **Read Replicas**:
  - Offload read queries from the primary database.

### **7. Audit and Monitor**
- **Change Data Capture (CDC)**:
  - Stream database changes to a log (e.g., Debezium + Kafka).
  - Example Debezium config:
    ```json
    {
      "name": "postgres-connector",
      "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "localhost",
        "database.port": "5432",
        "database.user": "user",
        "database.password": "password",
        "database.dbname": "appdb",
        "plugin.name": "pgoutput"
      }
    }
    ```
- **Metrics**:
  - Track replication lag, backup success rates, and failure rates.
  - Tools: Prometheus + Grafana dashboards.

---

## **Query Examples**

### **1. ACID Transaction (PostgreSQL)**
```sql
BEGIN;
-- Update accounts atomically
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
-- Verify balance constraint
SELECT * FROM accounts WHERE id = 1;
COMMIT; -- Or ROLLBACK on failure
```

### **2. Retry with Exponential Backoff (Python)**
```python
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def query_database_retry():
    response = requests.post("https://api.example.com/data", timeout=5)
    response.raise_for_status()
    return response.json()
```

### **3. Checkpointing in Event Sourcing (Java)**
```java
// Save state periodically
EventStore store = new EventStore();
store.saveSnapshot(new OrderSnapshot(orderId, currentState));
store.appendEvent(new OrderPaidEvent(orderId, amount));
```

### **4. Conflict Resolution with CRDTs (JavaScript)**
```javascript
import * as Y from 'yjs';

// Shared CRDT for collaborative editing
const yText = new Y.Text();
const provider = new WebsocketProvider("ws://server", "room", yText);
provider.awareness.setLocalStateField("user", { name: "Alice" });
yText.observe((update) => console.log("Conflict resolved:", update));
```

### **5. Backup Script (Bash)**
```bash
#!/bin/bash
# PostgreSQL backup with pg_dump + rotation
BACKUP_DIR="/backups/postgres"
LOG_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d).log"

# Create full backup
pg_dumpall -U postgres -f "$BACKUP_DIR/backup_$(date +%F).sql" > "$LOG_FILE" 2>&1

# Rotate logs (keep 7 days)
find "$BACKUP_DIR" -name "*.log" -mtime +7 -delete
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Saga Pattern**                 | Manage distributed transactions via orchestrated events.                       | Microservices with eventual consistency.         |
| **CQRS (Command Query Responsibility Segregation)** | Separate read and write models for scalability.                          | High-read workloads (e.g., e-commerce).         |
| **Event Sourcing**               | Store state changes as an immutable log.                                       | Audit trails, time-travel debugging.              |
| **Bulkhead Pattern**             | Isolate failures in parallel operations.                                         | Prevent cascading failures in high-throughput systems. |
| **Circuit Breaker**              | Stop cascading failures when downstream services degrade.                     | Resilient APIs with external dependencies.       |
| **Idempotency Key Pattern**      | Ensure duplicate requests yield the same result.                                | Payment APIs, order processing.                  |
| **Retry with Exponential Backoff** | Handle transient errors gracefully.                                            | Database connections, external APIs.             |
| **Leader Election**              | Elect a primary node for coordination in distributed systems.                 | Kafka, etcd clusters.                           |

---

## **Key Takeaways**
1. **Prioritize consistency** where it matters (e.g., financial data) and accept eventual consistency elsewhere.
2. **Replicate data** across regions for disaster recovery, but balance latency vs. durability.
3. **Automate backups** and test recovery procedures regularly.
4. **Handle failures explicitly** with retries, circuit breakers, and DLQs.
5. **Monitor** replication lag, backup success rates, and application state.
6. **Use patterns like Sagas** for distributed transactions and **CRDTs** for offline-first apps.

By following these best practices, you can build systems that survive outages, recover quickly, and maintain data integrity under heavy load.