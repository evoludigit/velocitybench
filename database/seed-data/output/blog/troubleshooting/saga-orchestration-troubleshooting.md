# **Debugging Saga Orchestration vs. Choreography: A Troubleshooting Guide**

## **1. Introduction**
Sagas are a pattern for managing distributed transactions by breaking them into smaller, compensatable steps. There are two primary implementations:
- **Orchestration**: A central component (saga orchestrator) coordinates interactions between services.
- **Choreography**: Services communicate directly via events, with no central controller.

Misapplying either pattern can lead to **performance bottlenecks, consistency issues, scalability problems, and maintenance headaches**. This guide provides a structured approach to diagnosing and resolving common issues.

---

## **2. Symptom Checklist**
Check these symptoms when investigating saga-related problems:

| **Symptom**                          | **Likely Cause**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| Transactions fail intermittently     | Missing compensating transactions, event retries not configured, race conditions |
| Slow response times                  | Excessive orchestration coordination, lack of async processing                 |
| Eventual consistency issues           | Missing event idempotency, duplicate processing, or event ordering problems   |
| High latency in compensations        | Long-lived transactions, inefficient saga state storage                        |
| Integration failure between services | Event bus misconfiguration, schema mismatches, or missing event listeners       |
| Difficulty debugging failures         | Lack of transaction logs, poor visibility into saga state                      |
| Scalability bottlenecks               | Single orchestrator becoming a bottleneck, DB locks, or high message volume   |

If multiple symptoms appear, the issue is likely **multi-faceted** and requires a systematic approach.

---

## **3. Common Issues & Fixes (With Code)**

### **A. Orchestration-Specific Problems**

#### **Issue 1: Single Point of Failure (Orchestrator Overload)**
**Symptoms:**
- High CPU/memory usage in saga service.
- Timeouts when orchestrating too many transactions.

**Root Cause:**
- The orchestrator handles all coordination, becoming a bottleneck.

**Fix:**
Implement **horizontal scaling** with:
- **Leader election** (e.g., using ZooKeeper or Kubernetes headless services).
- **Partitioned sagas** (assign sagas to different orchestrators based on ID).

**Example (Kubernetes + Saga Service):**
```yaml
# Deploy multiple saga orchestrators with partitioned load
apiVersion: apps/v1
kind: Deployment
metadata:
  name: saga-orchestrator
spec:
  replicas: 5  # Scale horizontally
  selector:
    matchLabels:
      app: saga-orchestrator
  template:
    spec:
      containers:
      - name: saga-orchestrator
        env:
        - name: PARTITION_KEY
          valueFrom:
            fieldRef:
              fieldPath: metadata.name  # Assigns unique partition per pod
```

#### **Issue 2: Long-Lived Transactions (Orchestration)**
**Symptoms:**
- Compensation steps fail due to expired sessions.
- Slow rollback times.

**Root Cause:**
- Transactions take too long, leading to session timeouts.

**Fix:**
- **Use short-lived sessions** with exponential backoff.
- **Persist saga state** in a database with optimizations.

**Example (Database Optimization):**
```java
// Using JPA with batch updates to reduce DB load
@Repository
public interface SagaRepository extends JpaRepository<Saga, Long> {
    @Modifying
    @Query("UPDATE Saga s SET s.status = ?1 WHERE s.id = ?2")
    void updateStatus(Long status, Long sagaId);
}
```

---

### **B. Choreography-Specific Problems**

#### **Issue 1: Event Loss or Duplication**
**Symptoms:**
- Inconsistent state due to missing events.
- Duplicate processing of the same event.

**Root Cause:**
- No **event sourcing** or **idempotency keys**.
- Event bus retries without deduplication.

**Fix:**
- **Implement idempotency keys** (e.g., `eventId` + `aggregateId`).
- Use **exactly-once processing** (e.g., Kafka `isolation.level=read_committed`).

**Example (Idempotent Event Handling):**
```typescript
// Node.js - Using Redis for deduplication
const redis = require("redis");
const client = redis.createClient();

app.post("/process-event", async (req, res) => {
  const { eventId, aggregateId } = req.body;
  const key = `processed:${eventId}:${aggregateId}`;

  const isProcessed = await client.exists(key);
  if (!isProcessed) {
    await client.set(key, "1", "EX", 3600); // Expire after 1 hour
    await processEvent(eventId, aggregateId);
  }
  res.send("Processed (or already processed)");
});
```

#### **Issue 2: Race Conditions in Compensations**
**Symptoms:**
- Partial compensation (e.g., refund but no inventory restore).
- Deadlocks in compensating transactions.

**Root Cause:**
- No **transactional outbox** or **eventual consistency guarantees**.

**Fix:**
- **Use an outbox pattern** to ensure events are committed atomically.
- **Implement compensating transactions** with retries.

**Example (Outbox Pattern in SQL):**
```sql
-- Table to hold unprocessed events
CREATE TABLE event_outbox (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50),
    payload JSONB NOT NULL,
    processed_at TIMESTAMP NULL
);

-- Trigger to publish on insert
CREATE OR REPLACE FUNCTION publish_event()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO event_bus (event_data)
    VALUES (NEW.payload);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_publish
AFTER INSERT ON event_outbox
FOR EACH ROW EXECUTE FUNCTION publish_event();
```

---

### **C. Shared Issues (Orchestration + Choreography)**

#### **Issue 1: Lack of Visibility into Saga State**
**Symptoms:**
- Hard to debug failed transactions.
- No metrics on saga progress.

**Fix:**
- **Centralized logging** (ELK, Datadog).
- **Expose saga status via API** (e.g., `/sagas/{id}/status`).

**Example (Prometheus + Grafana Metrics):**
```java
// Spring Boot Actuator metrics
@Bean
public MetricRegistry metricRegistry() {
    return new MetricRegistry();
}

@Bean
public SagaStatusEndpoint sagaStatusEndpoint() {
    return new SagaStatusEndpoint(metricRegistry());
}
```

#### **Issue 2: Eventual Consistency Not Handled Gracefully**
**Symptoms:**
- Clients see stale data.
- No fallback mechanism.

**Fix:**
- **Implement read repair** (e.g., refresh stale data on read).
- **Use optimistic locking** for critical operations.

**Example (Optimistic Locking in JPA):**
```java
@Entity
@Table(name = "orders")
public class Order {
    @Id
    private Long id;
    @Version  // Optimistic lock field
    private Integer version;
    private String status;
}
```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**               | **Use Case**                                                                 |
|-----------------------------------|------------------------------------------------------------------------------|
| **Distributed Tracing (Jaeger, OpenTelemetry)** | Track saga execution across services.                                      |
| **APM (New Relic, Datadog)**      | Monitor latency, errors, and throughput.                                    |
| **Event Bus Inspection (Kafka CLI, RabbitMQ Management)** | Check for lost/duplicate events.                                            |
| **Database Query Profiler**       | Identify slow saga state updates.                                           |
| **Saga Simulation (Chaos Engineering)** | Test failure recovery scenarios.                                           |
| **Logging Correlation IDs**       | Link related logs across services.                                          |

**Example (Jaeger Tracing in Spring Boot):**
```yaml
# application.yml
spring:
  sleuth:
    sampler:
      probability: 1.0  # Always trace
  zipkin:
    base-url: http://jaeger:9411/
```

---

## **5. Prevention Strategies**

### **A. Design-Time Best Practices**
✅ **Choose the Right Pattern Early**
- Use **orchestration** when you need strict control over workflows.
- Use **choreography** for simplicity and resilience.

✅ **Define Clear Compensation Logic**
- Every step must have a compensating action.
- **Example:**
  - **Step:** "Reserve product in inventory."
  - **Compensation:** "Release reserved inventory."

✅ **Optimize for Failure**
- **Retry failed steps** (exponential backoff).
- **Dead-letter queues** for unprocessable events.

### **B. Runtime Best Practices**
✅ **Monitor Saga Health**
- Track **active sagas, failed steps, and timeouts**.
- Set up **alerts for abnormal patterns**.

✅ **Test for Edge Cases**
- **Chaos testing:** Kill containers, simulate network failures.
- **Load testing:** Simulate high transaction volumes.

✅ **Keep Saga State Small**
- **Avoid storing large payloads** in DB (use references).
- **Use blob storage** for attachments (e.g., S3 for large files).

### **C. Operational Best Practices**
✅ **Automate Recovery**
- **Saga timeout alerts** (e.g., Slack/email if saga runs > 24h).
- **Automated rollback** if compensation fails repeatedly.

✅ **Document Compensation Logic**
- Maintain a **saga workflow diagram**.
- Keep **runbooks** for common failure scenarios.

---

## **6. Quick Resolution Checklist**
| **Step** | **Action** |
|----------|------------|
| 1 | **Identify the pattern** (orchestration vs. choreography). |
| 2 | **Check logs** (application, event bus, database). |
| 3 | **Verify compensations** (are they idempotent & retried?). |
| 4 | **Monitor performance** (latency, throughput, errors). |
| 5 | **Simplify if possible** (can choreography replace orchestration?). |
| 6 | **Scale if needed** (add more orchestrators, optimize DB). |
| 7 | **Test fixes** (run a controlled rollout). |

---

## **7. Final Recommendations**
- **Start simple**: Use **choreography** for new projects unless strict control is needed.
- **Avoid over-engineering**: Don’t add orchestration if events alone suffice.
- **Monitor aggressively**: **Distributed tracing** is your best friend.
- **Automate recovery**: **Retries, dead-letter queues, and alerts** save time.

By following this guide, you should be able to **diagnose, resolve, and prevent** saga-related issues efficiently.