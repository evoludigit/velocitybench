# **Debugging Consistency Conventions: A Troubleshooting Guide**
**Version:** 1.0
**Last Updated:** [YYYY-MM-DD]

---

## **1. Overview of Consistency Conventions**
Consistency Conventions ensure that data remains uniform across distributed systems, databases, or services by enforcing rules like:
- **Atomicity:** Operations succeed or fail as a whole.
- **Durability:** Data persists after commits.
- **Isolation:** Transactions do not interfere with each other.
- **Exactly-once processing** (e.g., event sourcing, idempotent operations).

When these conventions fail, systems may exhibit:
- **Data corruption** (e.g., stale reads, race conditions).
- **Inconsistent state** (e.g., partial updates, phantom reads).
- **Failed transactions** (e.g., deadlocks, retries, or timeouts).

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                          | **How to Test**                                                                 | **Likely Cause**                          |
|--------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| Incomplete transactions              | Query logs for partial commits (e.g., `BEGIN`, `COMMIT` without `ROLLBACK`).  | Network failure, server crash, or timeout. |
| Duplicate events/notifications       | Check event logs (e.g., Kafka, RabbitMQ) for duplicate messages.               | Idempotency key missing, retries without deduplication. |
| Stale data reads                     | Compare timestamps on reads vs. writes (e.g., database cursors, caching layers). | Outdated caches, inconsistent replicas. |
| Deadlocks or timeouts                | Monitor transaction logs (e.g., `pg_locks`, `STACK_OVERFLOW` errors).         | Poor lock granularity, long-running transactions. |
| Missing records in distributed systems | Audit trail check (e.g., `SELECT COUNT(*) FROM table` across nodes).          | Network partition, failed replication.   |
| Idempotent API calls failing          | Test same request multiple times (should succeed or return "already processed"). | Missing idempotency keys or versioning.   |

**Action:**
- **Reproduce systematically** (e.g., load test, simulate network latency).
- **Check observability tools** (Prometheus, Datadog, ELK) for anomalies.
- **Review recent code changes** (CI/CD pipelines, feature flags).

---

## **3. Common Issues and Fixes**

### **Issue 1: Incomplete Transactions (Partial Writes)**
**Symptoms:**
- Database tables show `BEGIN` but no `COMMIT`.
- Application logs show timeouts (`POSTGRES: could not connect`).

**Root Causes:**
- Network failure between app and database.
- Long-running transactions blocking other queries.
- Misconfigured connection pools (e.g., too few idle connections).

**Fixes:**

#### **Immediate Workaround:**
```sql
-- Manually check and rollback stuck transactions (PostgreSQL example)
SELECT pid, now() - xact_start AS duration FROM pg_stat_activity
WHERE state = 'active' AND now() - xact_start > interval '5 minutes';

-- Kill stuck transactions (use cautiously!)
SELECT pg_terminate_backend(pid);
```

#### **Long-Term Fixes:**
1. **Add timeouts** to transactions:
   ```java
   // Spring Boot (JPA example)
   @Transactional(timeout = 30) // 30 seconds
   public void updateUser(String userId) { ... }
   ```
   (Configure timeout in `application.properties`: `spring.jpa.properties.hibernate.jdbc.batch_size=10`.)

2. **Implement retry logic with backoff**:
   ```python
   # Python (with `tenacity` library)
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def update_database():
       try:
           db.session.commit()
       except Exception as e:
           db.session.rollback()
           raise e
   ```

3. **Use distributed transactions (if needed)**:
   - For multi-database writes, consider **Saga pattern** or **2PC (Two-Phase Commit)**.
   - Example with **JPA + XA**:
     ```xml
     <!-- application.properties -->
     spring.datasource.url=jdbc:postgresql://db1:5432/users
     spring.datasource.driver-class-name=org.postgresql.ds.PGXADataSource
     ```

---

### **Issue 2: Duplicate Events (Non-Idempotent Processing)**
**Symptoms:**
- Same event processed multiple times (e.g., "Payment confirmed" appears twice).
- Idempotency key (e.g., `payment_id`) not enforced.

**Root Causes:**
- Event producer retries without deduplication.
- Consumer doesn’t handle duplicates (e.g., no `transaction_id` check).

**Fixes:**

#### **Producer-Side Fix (Idempotency Keys):**
```go
// Go (using UUID for idempotency)
package main

import (
	"crypto/uuid"
	"database/sql"
	_ "github.com/lib/pq"
)

func ProcessPayment(payment Payment) error {
	idempotencyKey := uuid.New().String()
	_, err := db.Exec(`
		INSERT INTO payment_processed (idempotency_key, amount, tx_id)
		VALUES ($1, $2, $3)
		ON CONFLICT (idempotency_key) DO NOTHING`,
		idempotencyKey, payment.Amount, payment.TxID)
	if err != nil {
		return err
	}
	return nil
}
```

#### **Consumer-Side Fix (Deduplication):**
```python
# Python (RabbitMQ consumer with Redis acknowledgment)
import redis
import json

def process_event(event):
    event_id = event['event_id']
    redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

    # Deduplicate: return if already processed
    if redis_client.exists(f"processed:{event_id}"):
        return

    # Process and mark as seen
    try:
        # ... business logic ...
        redis_client.set(f"processed:{event_id}", "true", ex=86400)  # TTL=1 day
    except Exception as e:
        logger.error(f"Failed to process {event_id}: {e}")
```

---

### **Issue 3: Stale Reads (Dirty Reads / Phantom Reads)**
**Symptoms:**
- Application reads old data (e.g., cache inconsistency).
- Database shows "phantom rows" (new rows appear in a `WHERE` query during execution).

**Root Causes:**
- Missing `SELECT FOR UPDATE` locks.
- Caching layer outdated (Redis, Memcached).
- Lack of **MVCC (Multi-Version Concurrency Control)** support.

**Fixes:**

#### **Database-Level Fixes:**
```sql
-- PostgreSQL: Use serializable isolation for critical reads
BEGIN;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
-- Business logic here
COMMIT;
```

#### **Application-Level Fixes:**
1. **Enable strong consistency in cache**:
   ```python
   # Using Redis with caching enabled
   import redis
   r = redis.Redis()
   data = r.get("user:123", get_or_create=lambda: fetch_from_db(123))
   ```
   (Ensure cache invalidation on write.)

2. **Use optimistic locking**:
   ```java
   // Spring Data JPA example
   @Entity
   public class User {
       @Version
       private long version;
       // ...
   }
   ```
   - Throws `OptimisticLockingFailureException` if version mismatch.

---

### **Issue 4: Deadlocks**
**Symptoms:**
- Application hangs with no response.
- Database logs show `DEADLOCK DETECTED`.

**Root Causes:**
- Circular dependencies (e.g., `User → Order ← Product`).
- Long-running transactions holding locks.

**Fixes:**

#### **Prevent Deadlocks:**
1. **Order locks consistently**:
   ```sql
   -- Always lock tables in the same order (e.g., by ID)
   LOCK TABLE users IN SHARE MODE;
   LOCK TABLE orders IN SHARE MODE;
   ```

2. **Use smaller transactions**:
   - Break large operations into smaller chunks.
   - Example: Batch updates instead of a single `INSERT` of 10,000 rows.

3. **Add timeout to locks**:
   ```sql
   -- PostgreSQL: Lock with timeout
   SELECT pg_try_lock('lock_user_123', 5000); -- 5-second timeout
   ```

#### **Handle Deadlocks Gracefully:**
```python
# Python with retry on deadlock
from tenacity import retry

@retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(psycopg2.OperationalError))
def update_order():
    with db.cursor() as cur:
        cur.execute("BEGIN")
        try:
            cur.execute("UPDATE orders SET status='shipped' WHERE id=%s", [order_id])
            cur.execute("COMMIT")
        except psycopg2.DatabaseError as e:
            cur.execute("ROLLBACK")
            raise e
```

---

## **4. Debugging Tools and Techniques**
| **Tool/Technique**               | **Purpose**                                                                 | **Example Commands/Configs**                          |
|-----------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------|
| **Database Insights**             | Check locks, transactions, and queries.                                   |                                                                 |
| PostgreSQL: `pg_stat_activity`    | List active transactions/locks.                                             | `SELECT * FROM pg_stat_activity WHERE state = 'active';` |
| MySQL: `SHOW PROCESSLIST`         | Identify blocking queries.                                                  | `SHOW ENGINE INNODB STATUS;`                          |
| **APM Tools**                     | Trace distributed transactions.                                            | Datadog APM, New Relic, Jaeger.                        |
| **Transaction Tracing**           | Log SQL queries in a transaction.                                          | Spring: `@Transactional(propagation=Propagation.REQUIRES_NEW)` |
| **Event Logs**                    | Audit messages in Kafka/RabbitMQ.                                           | `kafka-consumer-groups --bootstrap-server ... --describe` |
| **Network Monitoring**            | Check RPC/API latency between services.                                     | `tcpdump`, `k6` load test, Prometheus `http_request_duration_seconds`. |
| **Idempotency Testing**           | Verify same request executes safely.                                        | Write a script to call `POST /payments` 10 times.     |

**Advanced Debugging:**
- **SQL Profiler**: Enable `pg_stat_statements` (PostgreSQL) to see slow queries.
- **Distributed Tracing**: Use OpenTelemetry to track request flows across services.
- **Chaos Engineering**: Simulate network partitions with tools like **Gremlin** or **Chaos Mesh**.

---

## **5. Prevention Strategies**
### **1. Design-Time Mitigations**
- **Enforce ACID in critical paths**:
  - Use databases (PostgreSQL, MySQL) over NoSQL for transactions.
  - Avoid "eventual consistency" where strong consistency is needed.
- **Idempotency by default**:
  - Add idempotency keys to all APIs (e.g., `X-Idempotency-Key: uuid`).
  - Example header in API Gateway:
    ```http
    POST /payments
    Headers: X-Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000
    ```
- **Saga Pattern for Distributed TXs**:
  - Break into compensating transactions.
  - Example (Python with Celery):
    ```python
    @celery.task(bind=True, max_retries=3)
    def transfer_funds(self, amount, sender_id, receiver_id):
        try:
            db.transfer(sender_id, receiver_id, amount)
            # Publish "TransferCompleted" event
        except Exception as e:
            self.retry(exc=e, countdown=60)
    ```

### **2. Runtime Safeguards**
- **Circuit Breakers**:
  - Fail fast if database is down (e.g., Hystrix, Resilience4j).
  - Example:
    ```java
    @CircuitBreaker(name = "databaseService", fallbackMethod = "fallback")
    public User getUser(Long id) { ... }
    ```
- **Connection Pooling**:
  - Configure pools with timeouts (e.g., HikariCP).
  ```properties
  # application.properties
  spring.datasource.hikari.maximum-pool-size=10
  spring.datasource.hikari.connection-timeout=30000  # 30s
  ```
- **Regular Audits**:
  - Schedule checks for orphaned transactions:
    ```bash
    # PostgreSQL: Find long-running transactions
    psql -c "SELECT pid, now() - age(now(), xact_start) AS duration FROM pg_stat_activity WHERE state = 'active';"
    ```

### **3. Observability**
- **Alerts for Anomalies**:
  - Set up alerts for:
    - Transaction duration > 1s (Prometheus alert rule).
    - Duplicate events in Kafka (custom script).
- **Distributed Tracing**:
  - Instrument all services with OpenTelemetry.
  - Example (Python):
    ```python
    from opentelemetry import trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_payment"):
        # Business logic
    ```

### **4. Testing**
- **Chaos Testing**:
  - Kill database pods in Kubernetes to test failure recovery.
- **Contract Testing**:
  - Use Pact to verify API consistency between services.
- **End-to-End Idempotency Tests**:
  ```python
  # Example: Test API idempotency
  def test_idempotent_payment():
      key = "test-idempotency-key"
      for _ in range(3):
          response = requests.post("/payments", headers={"X-Idempotency-Key": key})
          assert response.status_code == 200
  ```

---

## **6. Checklist for Quick Resolution**
1. **Isolate the failure scope**:
   - Is it a single transaction, a service, or the entire system?
2. **Check logs first**:
   - Database (`pg_log`), application (`stdout`, ELK), infrastructure (Kubernetes events).
3. **Reproduce locally**:
   - Spin up a test environment with the same config.
4. **Apply fixes in layers**:
   - Database → Application → Network → Infrastructure.
5. **Validate with metrics**:
   - Ensure fixes resolve the root cause (e.g., `pg_buffer_cache_hit_ratio` improves).
6. **Document the incident**:
   - Add to runbook for future reference.

---
## **7. Further Reading**
- [PostgreSQL: Deadlocks and Locking](https://www.postgresql.org/docs/current/ddl-locking.html)
- [Idempotency in Distributed Systems (Martin Kleppmann)](https://martin.kleppmann.com/2017/05/22/the-problem-with-idempotency.html)
- [Saga Pattern (Microsoft Docs)](https://docs.microsoft.com/en-us/azure/architecture/patterns/saga)
- [Chaos Engineering](https://principlesofchaos.org/)

---
**Final Note:** Consistency Conventions are complex but manageable with observability, testing, and disciplined design. Start with the simplest fix (e.g., timeouts) before diving into advanced patterns like 2PC. Always validate changes in staging!