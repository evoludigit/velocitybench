# **[Pattern] Query Result Streaming Reference Guide**

---

## **Overview**

The **Query Result Streaming** pattern enables FraiseQL to efficiently process large datasets by streaming results incrementally rather than loading them entirely into memory. This pattern leverages **database cursors** (where supported) and **incremental JSON serialization** to optimize memory usage while ensuring low-latency Time-To-First-Byte (TTFB) performance. By breaking query results into manageable chunks, applications avoid memory exhaustion and reduce processing bottlenecks.

This pattern is particularly useful when querying:
- Large tables (millions/billions of rows)
- Long-running analytical queries
- Real-time data processing pipelines

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Supported Databases**       | **FraiseQL Keyword/Parameter**       |
|-----------------------------|-------------------------------------------------------------------------------|--------------------------------|---------------------------------------|
| **Cursor**                  | A lightweight handle to track query progress through a result set.         | PostgreSQL, MySQL, SQLite      | `cursor()` function                   |
| **Batch Size**              | Number of rows returned per stream chunk. Adjustable to balance memory/CPU. | All supported databases      | `LIMIT` clause (e.g., `LIMIT 1000`) |
| **Pagination**              | Method to retrieve next batches via cursor position.                        | PostgreSQL, MySQL              | `OFFSET` (or `cursor_state` in PostgreSQL) |
| **Incremental JSON**        | JSON serialization that emits chunks as rows arrive (instead of full payload). | All supported databases      | `STREAM` clause (experimental)      |
| **Stream Completion**       | Signal indicating the end of streaming.                                      | All supported databases      | `IS_DONE` field (in JSON output)     |

---

## **Key Concepts**

### **1. Database Cursors**
FraiseQL supports persistent cursors (where available) to fetch results incrementally.
**PostgreSQL Example:**
```sql
-- Open a cursor
DECLARE my_cursor CURSOR FOR
SELECT id, name FROM users WHERE status = 'active';

-- Fetch in batches
FETCH 1000 FROM my_cursor;
```
**MySQL Example:**
```sql
-- Enable cursor support (requires `CURSOR` session variable)
SET SESSION cursor_type = "FORWARD_ONLY";
DECLARE user_cursor CURSOR FOR SELECT * FROM users WHERE age > 18;
-- Fetch manually with LOOP (not supported natively in FraiseQL; see below).
```

### **2. Client-Side Streaming (Recommended)**
FraiseQL streams results via **JSON chunks** over HTTP (REST API) or WebSockets (gRPC). Each chunk contains:
- A subset of rows (`batch_size` rows).
- A `cursor_state` (for pagination).
- An `is_done` flag to indicate completion.

**Example Response Structure:**
```json
{
  "cursor_state": "abc123...",
  "rows": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "is_done": false
}
```

### **3. Incremental JSON Serialization**
FraiseQL serializes results incrementally using a **streaming parser** (e.g., `json-stream` in Node.js). This avoids buffering the entire result set in memory.

**Example Query (Streaming Mode):**
```sql
-- Enable streaming (experimental)
SELECT * FROM large_table
STREAM BY ROWS AS JSON;  -- Emits rows as they’re fetched
```

---

## **Query Examples**

### **1. Basic Streaming Query**
Fetch 1,000 rows at a time from a large table:
```sql
-- FraiseQL API Endpoint: `/query`
{
  "query": "SELECT id, name FROM users LIMIT 1000 OFFSET 0",
  "stream": true,
  "batch_size": 1000
}
```
**Response:**
```json
{
  "cursor_state": "eyJzY29wZSI6IkFSQ0VUUkVDIn0...",
  "rows": [{"id": 1, "name": "Alice"}, ...],
  "is_done": false
}
```

### **2. Paginated Cursor-Based Streaming (PostgreSQL)**
Use `cursor()` for efficient pagination:
```sql
-- Start cursor
SELECT cursor('users_active_cursor') AS cursor_state
FROM users WHERE status = 'active';

-- Fetch next batch (1,000 rows) via API
{
  "query": "SELECT * FROM users WHERE status = 'active'
            FOR CSV CURRENT OF users_active_cursor LIMIT 1000",
  "stream": true
}
```

### **3. Real-Time Analytics with Streaming**
Aggregate data in chunks (e.g., for time-series analysis):
```sql
-- FraiseQL API (with `STREAM` clause)
{
  "query": "SELECT COUNT(*), AVG(value)
              FROM sensor_readings
              WHERE timestamp > NOW() - INTERVAL '1 hour'
              STREAM BY TIMESLICE('5 min')",
  "stream": true
}
```
**Output:** Receives partial aggregates every 5 minutes.

---

## **Implementation Considerations**

### **Database Limitations**
| Database       | Cursor Support | Streaming JSON | Notes                          |
|----------------|-----------------|-----------------|--------------------------------|
| PostgreSQL     | Yes             | Yes             | Native `cursor()`, `FOR CSV`    |
| MySQL          | Limited         | No              | Use `SESSION cursor_type`       |
| SQLite         | No              | No              | Use `LIMIT/OFFSET` for workarounds |

### **Performance Tips**
1. **Batch Size Tuning**: Adjust `batch_size` (e.g., 500–5,000 rows) to balance memory/CPU.
2. **Indexing**: Ensure columns in `WHERE`/`ORDER BY` are indexed for fast cursor seek.
3. **Connection Pooling**: Reuse connections for long-running cursors.
4. **Error Handling**: Monitor `cursor_state` for stale cursors (e.g., if the table is modified).

### **Error Cases**
| Scenario                          | Solution                                      |
|-----------------------------------|-----------------------------------------------|
| Cursor invalid (e.g., table DDL)  | Recreate cursor or use server-side reset.    |
| Network timeout                   | Implement retry logic with exponential backoff. |
| Memory exhaustion                 | Reduce `batch_size` or switch to polling.     |

---

## **Related Patterns**

1. **[Batch Processing](https://fraise.io/docs/batch-processing)**
   - Process results in bulk (vs. streaming) for smaller datasets.
   - Use when memory constraints are minimal.

2. **[Incremental Aggregation](https://fraise.io/docs/incremental-agg)**
   - Combine streaming with partial aggregations (e.g., sliding windows).

3. **[Serverless Query Execution](https://fraise.io/docs/serverless)**
   - Offload large queries to serverless functions for auto-scaling.

4. **[Event-Driven Archiving](https://fraise.io/docs/event-driven)**
   - Pipe streaming results to Kafka/SNS for async processing.

---

## **API Reference (Streaming Endpoint)**
### **Endpoint**
`POST /v1/stream`
### **Request Body**
```json
{
  "query": "SELECT * FROM large_table WHERE ...",
  "stream": true,
  "batch_size": 1000,
  "cursor_state": "optional_initial_state"  // For pagination
}
```
### **Response Headers**
| Header               | Description                          |
|----------------------|--------------------------------------|
| `Content-Type`       | `application/json-stream`            |
| `X-Stream-Total-Rows`| Total estimated rows (if known)      |

### **Example Client Implementation (Node.js)**
```javascript
const axios = require('axios');
const { transformStream } = require('stream-json');

const response = await axios.post('/stream', {
  query: 'SELECT * FROM users',
  stream: true
});

const stream = response.data;
const parser = transformStream(streamData => {
  console.log(`Received ${streamData.rows.length} rows`);
  if (streamData.is_done) process.exit(0);
});
```

---
**Note:** Streaming is experimental in FraiseQL v1.3. Consult the [release notes](https://fraise.io/releases) for updates. For MySQL/SQLite, consider hybrid approaches (e.g., chunked `OFFSET` queries).

---
**Last Updated:** 2024-05-15
**Feedback:** [contact@fraise.io](mailto:contact@fraise.io)