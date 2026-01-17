# **[Pattern] Consistency Troubleshooting: Reference Guide**
*Ensure data integrity across distributed systems, APIs, and event-driven architectures.*

---

## **Overview**
Data *inconsistency* arises when system states diverge (e.g., due to network delays, retries, or misconfigured transactions). This guide provides a structured approach to diagnosing and resolving consistency gaps in distributed systems, covering:
- **Root causes** (e.g., eventual vs. strong consistency, idempotency issues).
- **Diagnostic patterns** (logs, tracing, and validation checks).
- **Mitigation strategies** (compensating transactions, retries with backoff, and schema validation).

Follow this guide to systematically identify and resolve inconsistencies, improving reliability for APIs, microservices, and event-driven workflows.

---

## **Key Concepts & Troubleshooting Schema**

### **1. Consistency Models**
| **Model**               | **Definition**                                                                 | **Use Case**                          | **When to Suspect Issues**                          |
|-------------------------|-------------------------------------------------------------------------------|----------------------------------------|----------------------------------------------------|
| **Strong Consistency**  | Immediate, uniform state across all replicas.                               | ACID transactions, banking systems.    | Delays in `PATCH`/`DELETE` responses.             |
| **Eventual Consistency**| Changes propagate asynchronously; staleness may occur.                     | Social media feeds, caching layers.   | Out-of-date UI data after writes.                  |
| **Causal Consistency**  | Events with causal dependencies are ordered; others may vary.               | Chat apps (message threading).        | Replaying messages in wrong order.                 |
| **Session Consistency** | Client sees consistent state for the duration of a session.                | E-commerce carts.                     | Cart updates not reflecting in checkout.           |

---

### **2. Common Failure Modes**
| **Failure Type**        | **Symptoms**                                                                 | **Likely Causes**                                  | **Diagnostic Tools**                          |
|-------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|-----------------------------------------------|
| **Network Partition**   | Timeout errors, `503 Service Unavailable`.                                  | Unreliable connectivity (e.g., Kafka lag, HTTP retries). | Tracer (e.g., OpenTelemetry), `curl -v` logs. |
| **Idempotency Violation** | Duplicate payments, conflicting updates.                                    | Missing `idempotency-key` or race conditions.     | Check transaction logs for duplicate IDs.     |
| **Schema Drift**        | API responses fail validation (`400 Bad Request`).                           | Backend schema updates not propagated to frontend. | Use OpenAPI/Swagger to compare schemas.        |
| **Retry Storm**         | Backend overload due to exponential retries.                               | Missing exponential backoff in SDK.              | Monitor backend CPU/memory spikes.            |
| **TTL/Expiration Mismatch** | Stale data in caches (e.g., Redis).                                       | Inconsistent `TTL` settings across environments. | Check Redis `INFO` command output.             |

---

### **3. Troubleshooting Workflow**
Follow this **step-by-step diagnostic tree** to isolate issues:

1. **Reproduce the Issue**
   - **Action**: Execute the problematic workflow (e.g., `POST /orders` followed by `GET /orders/{id}`).
   - **Tools**:
     - `curl --request POST --data '{}' http://api.example.com/orders`
     - Postman/Insomnia for replaying failed requests.

2. **Check Logs & Traces**
   - **Where to Look**:
     - **Client logs**: Retry policies, timeout errors.
     - **Server logs**: `INFO`, `WARN`, `ERROR` levels (e.g., `retriable_exception`).
     - **Distributed traces**: Latency spikes (e.g., in Jaeger, Zipkin).
   - **Example Query**:
     ```sql
     -- Find delayed Kafka messages (eventual consistency lag)
     SELECT producer_id, lag(msgs_received) OVER (PARTITION BY topic ORDER BY timestamp)
     FROM kafka_topic_metrics
     WHERE lag > 10000; -- >10s delay
     ```

3. **Validate Data States**
   - **Strong Consistency Check**:
     ```bash
     # Compare DB state vs. API response
     psql -c "SELECT * FROM orders WHERE id='123';"  # DB
     curl http://api.example.com/orders/123          # API
     ```
   - **Eventual Consistency Check**:
     ```bash
     # Wait for replication to catch up (Redis example)
     watch -n 1 redis-cli GET user:123:address
     ```

4. **Test Edge Cases**
   - **Race Conditions**:
     ```bash
     # Stress-test concurrent writes
     for i in {1..100}; do curl -X POST http://api.example.com/inventory/decrement?item=123; done
     ```
   - **Idempotency**:
     ```bash
     # Simulate duplicate transaction
     curl -X POST -H "Idempotency-Key: abc123" http://api.example.com/orders
     ```

5. **Compare Environments**
   - **Example**: Staging vs. Production schema drift.
     ```bash
     # Diff schemas using OpenAPI (Swagger)
     swagger-cli diff --api1 staging.yaml --api2 production.yaml
     ```

6. **Apply Fixes** (see [Mitigation Patterns](#mitigation-patterns)).

---

## **Query Examples**

### **1. Database Schema Validation**
Verify tables align across environments:
```sql
-- Check for schema drift in PostgreSQL
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'orders'
ORDER BY table_name, ordinal_position;
```

### **2. API Response Consistency**
Compare a single resource’s state across endpoints:
```bash
# Get order from REST API and GraphQL
ORDER_ID=123
REST_RESPONSE=$(curl http://api.example.com/orders/$ORDER_ID)
GRAPHQL_RESPONSE=$(curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"{ order(id: \"'$ORDER_ID'\") { status } }"}' \
  http://gql.example.com)

echo "REST Status: $(jq -r '.status' <<< "$REST_RESPONSE")"
echo "GraphQL Status: $(jq -r '.data.order.status' <<< "$GRAPHQL_RESPONSE")"
```

### **3. Event-Driven Lag Detection**
Identify delayed events in Kafka:
```python
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'consistency-checker'
})
consumer.subscribe(['order-events'])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg.error():
        print(f"Error: {msg.error()}")
    else:
        print(f"Offset: {msg.offset()}, Timestamp: {msg.timestamp()}")
        # Compare with DB write time (if applicable)
```

### **4. Cache Invalidation Check**
Verify cache hits/misses match backend writes:
```bash
# Monitor Redis cache hits vs. backend calls
redis-cli info stats | grep -E "keyspace_hits|keyspace_misses"
```

---

## **Mitigation Patterns**
Apply these patterns based on the root cause:

| **Pattern**               | **Description**                                                                 | **Example Implementation**                                  |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Idempotency Keys**      | Ensure retries don’t cause duplicates by using unique keys.                    | `Idempotency-Key: <sha256(request_body)>`.                  |
| **Compensating Transactions** | Roll back side effects if primary transaction fails.               | `BEGIN TRANSACTION; UPDATE inventory; COMMIT;` + `ROLLBACK` on failure. |
| **Event Sourcing + Snapshots** | Reconstruct state from events; use snapshots for performance.       | Event store (e.g., EventStoreDB) + periodic DB snapshots. |
| **CRDTs**                 | Conflict-free replicated data types for offline-first apps.                 | Yjs (collaborative docs), Automerge.                        |
| **Schema Registry**       | Version-controlled schemas to avoid drift.                                | Confluent Schema Registry for Avro/Protobuf.               |
| **Retry with Backoff**    | Exponential backoff to avoid retry storms.                                | `retry: maxAttempts=5, backoff={type: exponential, base: 100}` |
| **Precondition Headers**  | Validate state before writes (e.g., `If-Match`).                          | `curl -X PUT -H "If-Match: ETag-123" ...`.                  |

---

## **Related Patterns**
| **Pattern**                          | **Purpose**                                                                 | **Reference**                          |
|---------------------------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **[Saga Pattern]**                    | Manage long-running transactions across services.                          | [Saga Pattern Docs](#)                |
| **[CQRS]**                            | Separate read/write models for scalability.                                 | [CQRS Guide](#)                        |
| **[Idempotent Producer]**             | Ensure Kafka consumers process messages exactly once.                       | [Kafka Docs: Idempotent Producer](#)  |
| **[Database Per Service]**            | Isolate schema changes per microservice.                                   | [DDD Blueprints](#)                   |
| **[Eventual Consistency Tolerance]**  | Design APIs to handle staleness gracefully.                                 | [Event Storming Guide](#)              |

---

## **Tools & References**
| **Tool**               | **Purpose**                                                                 | **Link**                                  |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **OpenTelemetry**      | Distributed tracing for latency analysis.                                  | [otel.io](https://opentelemetry.io)       |
| **PostgreSQL `pgBadger`** | Log analysis for inconsistencies.                                         | [pgbadger.darold.net](https://pgbadger.darold.net) |
| **Kafka Lag Exporter** | Monitor Kafka consumer lag.                                               | [GitHub](https://github.com/blancoFang/kafka-lag-exporter) |
| **Schema Registry**    | Enforce schema consistency.                                               | [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html) |
| **Testcontainers**     | Spin up consistent DB instances for testing.                               | [Testcontainers](https://www.testcontainers.org/) |

---
**Note**: Always validate fixes in a **staging environment** before production deployment. Use feature flags to toggle consistency checks incrementally.