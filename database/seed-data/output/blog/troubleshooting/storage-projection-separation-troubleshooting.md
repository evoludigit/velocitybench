# **Debugging "Storage-Projection Separation" Pattern: A Troubleshooting Guide**

## **Introduction**
The **Storage-Projection Separation** pattern decouples raw data storage (e.g., `tb_users`, `tb_orders`) from API-facing projections (e.g., `v1_users`, `v2_users`). This approach enables independent scaling, versioning, and evolution of APIs without requiring database schema changes.

However, misimplementation can lead to performance bottlenecks, versioning conflicts, and inefficient data flow. This guide focuses on diagnosing and resolving common issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

✅ **API Changes Require Database Migrations**
   - Schema updates in `v_*` tables to match API contracts.
   - Risk of downtime or version conflicts.

✅ **Inability to Maintain Multiple API Versions**
   - `v1_users` and `v2_users` drift apart due to inconsistent projections.
   - No clear way to handle deprecated or new fields.

✅ **DBA/API Designer Workflow Conflicts**
   - Backend engineers block DBAs with frequent schema changes.
   - API designers must coordinate with DBAs for every field addition.

✅ **Inefficient Denormalization**
   - Overly complex joins between `tb_*` and `v_*` tables.
   - Duplicate data across projections without proper sync mechanisms.

✅ **Slow Query Performance**
   - Projections are rebuilt frequently, causing high CPU/memory usage.
   - Missing indexes on frequently queried projection fields.

✅ **Eventual Consistency Issues**
   - Delays between `tb_*` updates and `v_*` synchronization.
   - Race conditions in concurrent writes.

✅ **Overhead in Data Replication**
   - Unnecessary data duplication between storage and projections.
   - Network latency in distributed systems.

---

## **2. Common Issues & Fixes**

### **Issue 1: Projections Fall Out of Sync with Storage Tables**
**Symptoms:**
- `v1_users` shows stale data (e.g., last name not updated).
- Queries return inconsistent results between `tb_users` and `v1_users`.

**Root Cause:**
- No automated synchronization mechanism.
- Manual triggers or batch jobs fail silently.

**Fix: Implement Event-Driven Sync**
Use **Change Data Capture (CDC)** to detect and apply changes in real-time.

**Example (Kafka + Debezium + PostgreSQL):**
```java
// Kafka Consumer (Java) to sync tb_users → v1_users
public void listenForChanges(ConsumerRecords<String, UserChangeEvent> records) {
    for (ConsumerRecord<String, UserChangeEvent> record : records) {
        UserChangeEvent change = record.value();
        switch (change.getType()) {
            case INSERT:
                projectionService.insertOrUpdateV1User(change.getUser());
                break;
            case UPDATE:
                projectionService.partialUpdateV1User(change.getUserId(), change.getDelta());
                break;
            case DELETE:
                projectionService.deleteV1User(change.getUserId());
                break;
        }
    }
}
```
**Alternative (Triggers + Stored Procedures):**
```sql
-- PostgreSQL Trigger for v1_users
CREATE OR REPLACE FUNCTION update_v1_user_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Denormalize data when tb_users changes
    INSERT INTO v1_users (id, name, email)
    VALUES (NEW.id, NEW.first_name || ' ' || NEW.last_name, NEW.email)
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        email = EXCLUDED.email;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_v1_user_sync
AFTER INSERT OR UPDATE ON tb_users
FOR EACH ROW EXECUTE FUNCTION update_v1_user_trigger();
```

---

### **Issue 2: Projections Are Too Slow to Query**
**Symptoms:**
- `v1_users` queries take seconds instead of milliseconds.
- CPU/Memory spikes due to excessive re-projection.

**Root Cause:**
- Projections are recomputed on every read instead of cached.
- Missing indexes on `v_*` tables.

**Fix: Optimize Projection Caching**
**Option A: Materialized Views (Database-Level Caching)**
```sql
-- PostgreSQL Materialized View
CREATE MATERIALIZED VIEW v1_users_mv AS
SELECT
    u.id,
    u.first_name || ' ' || u.last_name AS full_name,
    u.email,
    COUNT(o.id) AS order_count
FROM tb_users u
LEFT JOIN tb_orders o ON u.id = o.user_id
GROUP BY u.id;

-- Refresh periodically (cron job)
REFRESH MATERIALIZED VIEW v1_users_mv;
```

**Option B: In-Memory Cache (Redis)**
```java
// Spring Boot + Redis Cache
@Cacheable(value = "v1Users", key = "#id")
public UserV1 getUserV1(Long id) {
    return projectionService.fetchFromStorage(id);
}
```

**Option C: Add Indexes**
```sql
-- Index for faster lookups in v1_users
CREATE INDEX idx_v1_users_id ON v1_users (id);
CREATE INDEX idx_v1_users_email ON v1_users (email);
```

---

### **Issue 3: Versioning Becomes Unmanageable**
**Symptoms:**
- `v1_users` and `v2_users` diverge due to ad-hoc changes.
- No clear strategy for deprecating old versions.

**Root Cause:**
- Lack of a versioning policy.
- Manual updates in projections without automation.

**Fix: Enforce Versioning Discipline**
1. **Use a Versioned Projection Strategy**
   - Append new fields to `v2_users` instead of modifying `v1_users`.
   - Example:
     ```json
     // v1_users (legacy)
     { "id": 1, "name": "John", "email": "john@example.com" }

     // v2_users (extended)
     { "id": 1, "name": "John", "email": "john@example.com", "premium": true }
     ```

2. **Automate Version Migrations**
   - Use **Flyway/Liquibase** to manage projection schema changes:
     ```xml
     <!-- Example Flyway SQL migration -->
     <changeSet id="add-premium-field-to-v2" author="me">
         <addColumn tableName="v2_users">
             <column name="premium" type="boolean" defaultValue="false"/>
         </addColumn>
     </changeSet>
     ```

3. **Deprecate Old Versions Gracefully**
   - Redirect old version requests to a new endpoint with a warning:
     ```http
     GET /api/v1/users/1 → 307 Temporary Redirect → /api/v2/users/1 with deprecation header
     ```

---

### **Issue 4: High Write Overhead Due to Projections**
**Symptoms:**
- Writes to `tb_users` are slow because they trigger `v1_users` and `v2_users` updates.
- Increased latency in microservices with multiple projections.

**Root Cause:**
- Every write to `tb_*` forces updates in all projections.
- No batching or async processing.

**Fix: Batch Updates & Async Processing**
**Option A: Batch Inserts for Projections**
```java
// Batch insert into v1_users after CDC event batch
List<User> users = ...; // From Kafka batch
projectionService.batchInsertV1Users(users);
```

**Option B: Async Task Queue (SQS/Spring `@Async`)**
```java
@Service
public class ProjectionService {
    @Async
    public CompletableFuture<Void> asyncUpdateV1User(Long userId) {
        projectionRepository.updateV1User(userId);
        return CompletableFuture.completedFuture(null);
    }
}
```

**Option C: Schema-Free Projections (JSON Columns)**
- Store projections as JSON in `tb_users` (denormalized) to avoid extra tables:
  ```sql
  ALTER TABLE tb_users ADD COLUMN v1_projection JSONB;
  ALTER TABLE tb_users ADD COLUMN v2_projection JSONB;
  ```
  - Update on write:
    ```java
    user.setV1Projection(
        UserV1Mapper.toV1(user.getFirstName(), user.getLastName(), user.getEmail())
    );
    ```

---

### **Issue 5: Eventual Consistency Breaks User Experience**
**Symptoms:**
- User sees `v1_users` data that hasn’t synced with `tb_users`.
- Race conditions in concurrent writes.

**Root Cause:**
- No **transactional outbox pattern** or compensating transactions.
- Simple event consumers fail silently.

**Fix: Implement Compensating Actions & Transactions**
**Option A: Transactional Outbox (Database-Level)**
```sql
-- Add outbox table
CREATE TABLE event_outbox (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    payload JSONB,
    status VARCHAR(20) DEFAULT 'PENDING',
    processed_at TIMESTAMP
);

-- Trigger after tb_users update
INSERT INTO event_outbox (event_type, payload)
VALUES ('user_updated', to_jsonb(NEW::jsonb))
ON CONFLICT (id) DO NOTHING;
```

**Option B: Retry Logic for Failed Projections**
```java
// Dead-letter queue (DLQ) handling
public void processProjectionEvent(UserChangeEvent event, DeadLetterQueue dlg) {
    try {
        projectionService.applyChange(event);
    } catch (Exception e) {
        dlg.publish(event, "Failed to update projection: " + e.getMessage());
    }
}
```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example Command/Query**                     |
|--------------------------|---------------------------------------|-----------------------------------------------|
| **Kafka Consumer Lag**   | Check CDC synchronization delays     | `kafka-consumer-groups --bootstrap-server <broker> --group <group>` |
| **Database Profiler**    | Slow query analysis                   | PostgreSQL: `EXPLAIN ANALYZE SELECT * FROM v1_users WHERE email = 'x@x.com';` |
| **Redis Insights**       | Cache hit/miss ratios                 | `RESPONSE STATS` in Redis CLI                  |
| **Prometheus + Grafana** | Monitor projection sync latency       | Query: `rate(projection_sync_duration_seconds_count[5m])` |
| **SQL Injection Detection** | Ensure projection updates are safe | Use prepared statements in CDC consumers      |
| **Schema Comparison**    | Detect drift between `tb_*` and `v_*` | `pg_diff` (PostgreSQL) or `Liquibase diff`     |

---

## **4. Prevention Strategies**

### **1. Design Principles for Storage-Projection Separation**
✔ **Keep Projections Denormalized by Purpose**
   - `v1_users` = Minimal fields for API v1.
   - `v2_users` = Extended fields for API v2.

✔ **Use Event Sourcing for Complex Projections**
   - Store append-only events (e.g., `UserUpdated`) and replay to rebuild projections.

✔ **Document Versioning Rules**
   - Clearly define how new fields are added to projections (e.g., "Append-only").

### **2. Automate Projection Management**
- **CI/CD Pipeline for Projections**
  - Run projection schema migrations in CI before deployments.
  - Example GitHub Actions workflow:
    ```yaml
    - name: Run Flyway Migrations
      run: flyway migrate -url=$DB_URL -user=$DB_USER -password=$DB_PASSWORD
    ```

- **Schema Registry for APIs**
  - Use **OpenAPI/Swagger** to version API contracts independently of DB schemas.

### **3. Monitoring & Alerting**
- **Set Up Alerts for Sync Lag**
  - Alert if Kafka consumer lag > 5 minutes.
  - Example Prometheus alert:
    ```yaml
    - alert: HighProjectionSyncLag
      expr: kafka_lag{topic="user_updates"} > 5 * 60
      for: 1m
      labels:
        severity: warning
    ```

- **Monitor Projection Query Performance**
  - Track slow queries on `v_*` tables with APM tools (e.g., New Relic).

### **4. Testing Strategies**
- **Integration Tests for Projection Sync**
  ```java
  @Test
  public void testProjectionSync() {
      // Given
      User user = new User("John", "Doe");
      userRepository.save(user);

      // When
      user.setLastName("Smith");
      userRepository.save(user);

      // Then (with retry logic due to async)
      assertThat(projectionService.getV1User(user.getId())).extracting("name").isEqualTo("John Smith");
  }
  ```

- **Chaos Engineering for Eventual Consistency**
  - Kill projection consumers and verify fallback behavior.

---

## **5. Quick Reference Table (Summary)**
| **Issue**                  | **Root Cause**               | **Fix**                          | **Tools**                     |
|----------------------------|------------------------------|----------------------------------|-------------------------------|
| **Out-of-sync projections** | No real-time sync            | CDC + Event-Driven Updates       | Debezium, Kafka, Triggers     |
| **Slow projection queries** | Missing indexes/caching      | Materialized Views, Redis Cache  | PostgreSQL MV, Redis          |
| **Unmanageable versioning** | No versioning policy         | Schema migrations, deprecation   | Flyway, Liquibase, OpenAPI     |
| **High write latency**      | Batch inefficiency           | Async tasks, batch inserts       | SQS, `@Async`, Batch DB ops   |
| **Consistency breaks**      | No compensating actions      | Transactional outbox, DLQ         | Database outbox, RabbitMQ      |

---

## **Final Checklist for Healthy Storage-Projection Separation**
✅ [ ] Projections are synced via CDC/event-driven updates.
✅ [ ] Projections are indexed for performance.
✅ [ ] API versions are versioned independently (append-only).
✅ [ ] Write operations are async/batched where possible.
✅ [ ] Consistency is monitored with alerts.
✅ [ ] Testing covers sync, versioning, and edge cases.

By following this guide, you can diagnose and resolve storage-projection separation issues efficiently. For persistent problems, consider reviewing your **event sourcing**, **CQRS**, or **schema evolution** patterns next.