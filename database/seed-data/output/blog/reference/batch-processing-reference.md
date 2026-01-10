---
**[Pattern] Batch Processing vs. Individual Requests – Reference Guide**
*Optimize performance by reducing network overhead and transaction latency.*

---

## **Overview**
Batch processing consolidates multiple operations (e.g., inserts, updates, or deletes) into a single request, minimizing redundant network round-trips, connection handling, and transaction overhead. While individual requests are intuitive, batching significantly reduces latency—e.g., a loop of 1,000 `INSERT` statements (30 seconds) becomes a single bulk operation (100ms). This pattern is critical for high-volume APIs, ETL pipelines, and data-heavy applications. Misapplied batching risks memory exhaustion, timeouts, or data corruption; thus, proper chunking and error handling are essential.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Use Case**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Batch Processing**   | Combining N discrete operations into one logical unit (e.g., one API call, DB transaction).    | Bulk data ingestion, cron jobs, or large-scale updates.                                          |
| **Bulk Operation**     | A single database statement (e.g., `INSERT`, `UPDATE`) targeting multiple rows.                 | Reducing DB round-trips; e.g., `INSERT INTO table VALUES (...), (...), (...)`                 |
| **Chunking**           | Breaking large datasets into smaller, manageable batches (e.g., 1,000 rows per batch).         | Preventing memory overload; accommodating DB memory limits.                                      |
| **Individual Requests**| Sequential API calls (e.g., HTTP `POST /users` per user).                                         | Low-volume or real-time updates where atomicity is critical.                                    |
| **Idempotency**        | Ensuring repeated batch executions produce the same result without unintended side effects.      | Safe retry logic for failed batches.                                                            |
| **Transaction Scope**  | Atomicity of batch operations (ACID compliance).                                                   | Ensuring consistency across dependent operations (e.g., payments + inventory updates).          |

---

## **Schema Reference**

### **Database Schemas**
| **Pattern**       | **Table**               | **Example Syntax**                                                                                     |
|-------------------|-------------------------|-------------------------------------------------------------------------------------------------------|
| **Bulk Insert**   | `users`                 | `INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com'), ('Bob', 'bob@example.com')`   |
| **Batch Update**  | `orders`                | `UPDATE orders SET status = 'shipped' WHERE id IN (1001, 1002, 1003)`                                |
| **Chunked Delete**| `temp_data`             | `DELETE FROM temp_data WHERE batch_id IN (SELECT batch_id FROM chunks WHERE status = 'ready')`         |

---

## **API Schema**
### **Batch vs. Individual Request Examples**

| **Pattern**            | **Endpoint**               | **Request Body**                                                                                     | **Response**                                                                                     |
|------------------------|----------------------------|-------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Individual Insert**  | `POST /users`              | `{ "name": "Alice", "email": "alice@example.com" }`                                                  | `{ "id": 1, "status": "created" }`                                                               |
| **Batch Insert**       | `POST /users/batch`        | `[{ "name": "Alice", "email": "alice@example.com" }, { ... }]`                                       | `{ "total": 2, "created": 2, "errors": [] }`                                                     |
| **Chunked Processing** | `POST /process/chunk`      | `{ "chunk_id": 1, "data": [ { ... }, { ... } ] }` (from a queue like Kafka/Pulsar)               | `{ "status": "queued", "chunk_id": 1 }`                                                            |

---

## **Implementation Details**

### **1. Database-Level Batch Processing**
#### **Bulk Insert (SQL)**
```sql
-- PostgreSQL example (explicit VALUES)
INSERT INTO users (name, email)
VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com');

-- PostgreSQL COPY (fastest for large data)
COPY users FROM '/path/to/data.csv' CSV HEADER;

-- MySQL (multi-row INSERT)
INSERT INTO users (name, email)
VALUES ('Alice', 'alice@example.com'), ('Bob', 'bob@example.com');
```

#### **Transaction Management**
```sql
BEGIN TRANSACTION;
-- Bulk insert 1000 rows
INSERT INTO logs (user_id, action) VALUES
    (1, 'login'), (2, 'purchase'), ...; -- 1000 rows
COMMIT; -- Atomic commit
```

#### **Error Handling**
- Use **`ON CONFLICT`** (PostgreSQL) or **`IGNORE`/`ON DUPLICATE KEY UPDATE`** (MySQL) to skip duplicates.
- Log individual failures for retries:
  ```sql
  INSERT INTO users (name, email)
  VALUES (...)
  ON CONFLICT (email) DO NOTHING
  RETURNING email;
  ```

---

### **2. API-Level Batch Processing**
#### **Design Considerations**
- **Payload Size Limits**: Set `Content-Length` headers (e.g., `<= 10MB`).
- **Idempotency Keys**: Allow retrying failed batches (e.g., `idempotency_key: "batch-123"`).
- **Rate Limiting**: Use `X-RateLimit-Limit` headers to throttle batch sizes.

#### **Example: REST Batch Endpoint**
```http
POST /users/batch
Content-Type: application/json
X-RateLimit-Limit: 1000

[
  { "name": "Alice", "email": "alice@example.com" },
  { "name": "Bob", "email": "bob@example.com" }
]
```
**Response:**
```json
{
  "success": 2,
  "failures": [
    { "index": 1, "error": "Duplicate email" }
  ]
}
```

---

### **3. Client-Side Chunking**
#### **Logic for Large Datasets**
1. **Fetch Chunks**: Retrieve data in batches (e.g., 500 rows at a time from a cursor-based API).
2. **Buffer Data**: Store chunks in memory or a queue (e.g., Redis, Kafka).
3. **Process Chunks**: Send to a batch endpoint or DB with retries for failures.

#### **Python Example (Chunked Processing)**
```python
import pandas as pd

def process_in_chunks(data: pd.DataFrame, chunk_size: int = 500):
    for i in range(0, len(data), chunk_size):
        chunk = data.iloc[i:i + chunk_size]
        # Send chunk to /users/batch endpoint
        response = requests.post(
            "https://api.example.com/users/batch",
            json=chunk.to_dict("records"),
            headers={"X-Batch-Id": f"batch-{i//chunk_size}"}
        )
        assert response.status_code == 200, f"Batch {i//chunk_size} failed"
```

---

## **Query Examples**

### **1. Bulk DB Operations**
#### **PostgreSQL: Bulk Insert with ON CONFLICT**
```sql
INSERT INTO users (name, email)
VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com')
ON CONFLICT (email) DO NOTHING
RETURNING email;
```

#### **MySQL: Multi-Table Batch Update**
```sql
START TRANSACTION;
UPDATE orders SET status = 'shipped' WHERE id IN (1001, 1002, 1003);
UPDATE inventory SET stock = stock - 1 WHERE product_id IN (SELECT product_id FROM orders WHERE id IN (1001, 1002, 1003));
COMMIT;
```

---

### **2. API Batch Endpoints**
#### **Microservices: Chunked Event Processing**
```http
# Kafka Consumer (processing chunks from a topic)
POST /events:batch
Content-Type: application/vnd.kafka.json.v2+json

{
  "records": [
    {"value": {"user": "Alice", "action": "login"}},
    {"value": {"user": "Bob", "action": "purchase"}}
  ]
}
```

---

## **Performance Trade-offs**

| **Criteria**          | **Individual Requests**       | **Batch Processing**               |
|-----------------------|-------------------------------|-------------------------------------|
| **Latency**           | High (N round-trips)          | Low (1 round-trip)                  |
| **Resource Usage**    | Low per request               | High (mem/Disk for large batches)   |
| **Atomicity**         | High (per request)            | High (if wrapped in transaction)   |
| **Error Handling**    | Easy (fail-fast)              | Complex (partial failures)          |
| **Use Case Fit**      | Low-volume, real-time         | High-volume, scheduled jobs         |

---

## **Related Patterns**
1. **[Pipeline Processing](link)**:
   Chaining batch operations (e.g., ETL: batch ingest → transform → load).
   *Example*: Use Kafka Streams to process batches in real-time.

2. **[Idempotent Operations](link)**:
   Ensuring batch retries don’t duplicate side effects.
   *Example*: Add `idempotency_key` to batch requests.

3. **[Connection Pooling](link)**:
   Reusing DB connections for batch operations to avoid overhead.
   *Example*: Configure `pg_bouncer` for PostgreSQL batches.

4. **[Circuit Breaker](link)**:
   Preventing cascading failures in batch systems.
   *Example*: Use Hystrix to timeout long-running batches.

5. **[Event Sourcing](link)**:
   Storing batches as events for replayability.
   *Example*: Append-only log of batch operations in Kafka.

---

## **Anti-Patterns & Pitfalls**
1. **Unbounded Batches**:
   - *Risk*: Memory exhaustion or DB timeouts.
   - *Fix*: Enforce chunk limits (e.g., `<= 10,000 rows`).

2. **No Error Isolation**:
   - *Risk*: One bad record fails the entire batch.
   - *Fix*: Use partial success (e.g., return `success: 2/5`).

3. **Ignoring Idempotency**:
   - *Risk*: Duplicate processing on retries.
   - *Fix*: Add `idempotency_key` to batch endpoints.

4. **Over-Batching**:
   - *Risk*: Long GC pauses or DB locks.
   - *Fix*: Test with `EXPLAIN ANALYZE` before committing to large batches.

5. **Tight Coupling**:
   - *Risk*: API changes break batch clients.
   - *Fix*: Version endpoints (e.g., `/v1/batch/users`).

---
**Best Practices Summary**:
- **Batch when**: Data volume is high (>1000 operations).
- **Chunk when**: Memory limits or DB constraints apply.
- **Test when**: Latency spikes or errors occur under load.
- **Monitor when**: Batch processing introduces new failures.