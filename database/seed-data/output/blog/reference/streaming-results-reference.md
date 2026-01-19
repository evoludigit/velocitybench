# **[Pattern] Streaming Large Result Sets – Reference Guide**

---

## **Overview**
The **Streaming Large Result Sets** pattern ensures efficient data retrieval when querying large datasets by progressively sending results to the client instead of loading the entire result set into memory. This approach minimizes server load, reduces latency, and prevents memory overflow, especially useful for analytical queries, logs, or real-time monitoring systems.

Key benefits:
- **Memory efficiency** – Avoids holding massive datasets in RAM.
- **Scalability** – Handles large datasets without degrading performance.
- **Responsive UIs** – Enables incremental rendering of results (e.g., paginated interfaces).
- **Resource conservation** – Reduces server CPU/memory usage.

This pattern is ideal for:
- Long-running analytical queries (e.g., SQL `SELECT * FROM huge_log_table`).
- Event log analysis (e.g., streaming kubernetes pod logs).
- Real-time dashboards with time-series data.

---

## **Schema Reference**

| **Component**          | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Cursor-Based Pagination** | Uses a token (e.g., last seen row ID) to fetch next batch of results. Avoids recalculating offsets for every request.                                                                                      | `LIMIT 100 OFFSET cursor_value` (PostgreSQL) or `WHERE id > last_id` (custom cursor logic).   |
| **Offset-Based Pagination** | Fetches results starting from a specific index. Inefficient for very large datasets (requires recalculating offsets on each paginate call).                                                           | `LIMIT 100 OFFSET 1000` (SQL)                                                                   |
| **Key-Value Cursor**   | Uses a hash of the last returned row (e.g., `(id, timestamp) → MD5`) to uniquely identify the next batch. Supports dynamic ordering (e.g., by timestamp).                                          | `cursor = md5(id || timestamp)`                                                                 |
| **Server-Sent Events (SSE)** | Enables real-time streaming of results via HTTP long-polling. Clients subscribe to a stream (e.g., WebSocket or SSE) to receive updates incrementally.                                                        | SSE: `Server-Send-Event: data: {"row": {...}}`                                                  |
| **Chunking**           | Splits results into fixed-size chunks (e.g., 1000 rows per chunk) with a completion indicator (e.g., `is_last_chunk: true`). Clients request the next chunk via a token (e.g., chunk_id).                     | `{"chunk_id": "abc123", "rows": [...], "is_last_chunk": false}`                                  |
| **Batch Processing**   | Processes data in batches (e.g., 1000 rows at a time) with metadata (e.g., total rows, remaining batches). Clients track progress via batch counters.                                                  | `{"total_rows": 10000, "current_batch": 1, "rows": [...]}`                                     |
| **Indexing**           | Underlying data must be indexed on pagination/cursor fields (e.g., `PRIMARY KEY`, `INDEX (timestamp)`) to enable efficient range queries.                                                                 | `CREATE INDEX idx_timestamp ON logs(timestamp);`                                                 |
| **Client State**       | Clients maintain state (e.g., last cursor, unprocessed chunks) to resume streaming after disconnections.                                                                                                   | `client_state = {"last_cursor": "abc123", "unprocessed": [1, 2]}`                              |
| **Error Handling**     | Implements retry logic for failed chunks (e.g., transient errors) or client disconnections (e.g., reconnect with last known cursor).                                                                     | `retry_after: 5s, last_cursor: "abc123"`                                                         |
| **Client API**         | Standardized endpoint for streaming (e.g., `GET /api/v1/stream?cursor=abc123&limit=1000`). Supports headers (e.g., `Accept: application/x-ndjson`) for streaming formats.                              | `GET /api/v1/stream?cursor=abc123 HTTP/1.1`                                                     |
| **Streaming Formats**  | Data sent as:
   - **JSON Lines (NDJSON)**: One JSON object per line (efficient parsing).
   - **Protocol Buffers**: Binary encoding for high-performance streaming.                                                                                                                            | `data: {"id": 1, "name": "Alice"}` (NDJSON)                                                    |
| **Server Timeout**     | Configurable timeout per chunk (e.g., 30s) to prevent long-running idle streams. Clients must request the next chunk before timeout to avoid disconnection.                                                  | `server_timeout: 30s`                                                                           |
| **Rate Limiting**      | Limits concurrent streaming requests per client to prevent abuse (e.g., 5 simultaneous streams).                                                                                                         | `X-RateLimit-Limit: 5`                                                                        |

---

## **Implementation Details**

### **1. Cursor-Based Pagination (Recommended)**
- **How it works**: The server returns a token (e.g., `last_id` or a hashed cursor) that clients include in subsequent requests to fetch the next batch.
- **Example Flow**:
  1. Client requests `cursor=null` → Server returns rows 1–100 + cursor for row 100.
  2. Client requests `cursor=row_100_id` → Server returns rows 101–200 + next cursor.
- **Pros**: Efficient for large datasets (no offset recalculation).
- **Cons**: Requires unique, sortable cursor values (e.g., primary keys or composite keys).

```sql
-- PostgreSQL example (cursor-based pagination)
SELECT * FROM logs
WHERE id > last_id
ORDER BY id
LIMIT 100;
```

### **2. Offset-Based Pagination (Legacy)**
- **How it works**: Uses `OFFSET` to skip rows, but recalculates the offset on every request (inefficient for large datasets).
- **Example**:
  ```sql
  -- First page: OFFSET 0
  SELECT * FROM logs LIMIT 100;

  -- Second page: OFFSET 100
  SELECT * FROM logs OFFSET 100 LIMIT 100;
  ```
- **When to use**: Small datasets or read-heavy systems where offset recalculation is acceptable.

### **3. Server-Sent Events (SSE)**
- **How it works**: Clients open a long-lived HTTP connection (e.g., `GET /stream?filter=active` with `Accept: text/event-stream`). The server pushes events incrementally.
- **Example SSE Response**:
  ```
  data: {"id": 1, "name": "Alice"}
  data: {"id": 2, "name": "Bob"}

  -- End of stream
  event: end
  ```
- **Use case**: Real-time updates (e.g., live logs, stock tickers).

### **4. Chunking with Metadata**
- **How it works**: Results are split into chunks with metadata (e.g., `is_last_chunk`, `total_rows`).
- **Example API Response**:
  ```json
  {
    "chunk_id": "abc123",
    "rows": [
      {"id": 1, "value": "A"},
      {"id": 2, "value": "B"}
    ],
    "is_last_chunk": false,
    "total_rows": 10000,
    "total_chunks": 10
  }
  ```
- **Client logic**: Tracks `chunk_id` to request the next chunk via `GET /stream?chunk_id=abc123`.

### **5. WebSocket Streaming**
- **How it works**: Clients establish a WebSocket connection (`ws://host/stream`) and receive data in real-time.
- **Example WebSocket Message**:
  ```json
  {"type": "data", "payload": {"id": 1, "name": "Alice"}}
  {"type": "complete", "total": 10000}
  ```
- **Use case**: Low-latency applications (e.g., trading systems).

---

## **Query Examples**

### **1. Cursor-Based Streaming (SQL)**
```sql
-- Initialize stream (first page)
SELECT * FROM large_table
WHERE id > '0'  -- Start before all rows
ORDER BY id
LIMIT 100;

-- Next page (client provides last_id)
SELECT * FROM large_table
WHERE id > '12345'  -- Last ID from previous batch
ORDER BY id
LIMIT 100;
```

### **2. Cursor-Based Streaming (Application Logic)**
```python
# Pseudocode for a cursor-based stream in Python
class StreamClient:
    def __init__(self, db):
        self.db = db
        self.last_cursor = None

    def fetch_next_batch(self, limit=100):
        query = """
            SELECT * FROM logs
            WHERE id > %s
            ORDER BY id
            LIMIT %s
        """
        rows = self.db.execute(query, (self.last_cursor, limit))
        if rows:
            self.last_cursor = rows[-1]["id"]  # Update cursor
        return rows
```

### **3. SSE Endpoint (HTTP)**
```http
GET /api/v1/logs/stream?app=backend&limit=100 HTTP/1.1
Accept: text/event-stream

-- Server response (SSE)
data: {"id": 1, "timestamp": "2023-01-01", "message": "Start"}
data: {"id": 2, "timestamp": "2023-01-02", "message": "Error"}
event: end
```

### **4. Chunked Response (REST API)**
```http
GET /api/v1/large_query?cursor=initial&chunk_size=1000 HTTP/1.1

-- Response (JSON Lines format)
data: {"id": 1, "data": "A"}
data: {"id": 2, "data": "B"}
data: {"is_last_chunk": true}
```

### **5. WebSocket Stream**
```javascript
// Client-side WebSocket stream
const socket = new WebSocket("ws://host/stream");
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "data") {
    console.log(data.payload);
  } else if (data.type === "complete") {
    console.log("Stream complete");
  }
};
```

---

## **Error Handling and Retries**
| **Scenario**               | **Action**                                                                                     |
|----------------------------|------------------------------------------------------------------------------------------------|
| **Network interruption**   | Client resumes from last known cursor (e.g., `cursor=last_id`).                              |
| **Server error (5xx)**     | Client implements exponential backoff (e.g., retry after 5s, 10s, 20s).                         |
| **Invalid cursor**         | Server returns `400 Bad Request` with `error: "invalid_cursor"` and suggested next action.     |
| **Rate limit exceeded**    | Server returns `429 Too Many Requests` with `Retry-After: 60s`.                                |
| **Chunk timeout**          | Client requests the same chunk again after `server_timeout` expires.                           |

---

## **Performance Considerations**
| **Factor**               | **Best Practice**                                                                               |
|--------------------------|-------------------------------------------------------------------------------------------------|
| **Indexing**             | Index cursor fields (e.g., `PRIMARY KEY` or `INDEX (timestamp)`) to avoid full table scans.    |
| **Batch size**           | Limit batch size to ~1MB–10MB to balance latency and memory usage.                                |
| **Compression**          | Use `gzip` or `br` for HTTP/SSE streams to reduce payload size.                                 |
| **Connection reuse**     | Clients should reuse long-lived connections (e.g., WebSocket/SSE) instead of opening new ones. |
| **Parallel streams**     | Allow multiple concurrent streams per client (e.g., 5 streams max) to avoid resource exhaustion. |
| **Memory limits**        | Configure server to kill queries exceeding memory limits (e.g., PostgreSQL `work_mem`).          |

---

## **Related Patterns**
1. ****Pagination (Offset vs. Cursor)***
   - Compare cursor-based (efficient for large datasets) vs. offset-based (simple but inefficient) pagination.
   - [Pattern: Pagination](link-to-pagination-pattern.md).

2. ****Event Sourcing***
   - Stream historical events incrementally (e.g., database change logs). Combines with this pattern for real-time analytics.
   - [Pattern: Event Sourcing](link-to-event-sourcing-pattern.md).

3. ****Lazy Loading***
   - Load data on-demand (e.g., in a UI) rather than pre-fetching, similar to streaming but client-side.
   - [Pattern: Lazy Loading](link-to-lazy-loading-pattern.md).

4. ****Batch Processing***
   - Process large datasets in batches (e.g., ETL pipelines) to avoid memory overload.
   - [Pattern: Batch Processing](link-to-batch-processing-pattern.md).

5. ****Caching (Streaming)***
   - Cache streamed results (e.g., Redis) to reduce database load for frequent queries.
   - [Pattern: Caching](link-to-caching-pattern.md).

6. ****Asynchronous Processing***
   - Offload streaming queries to background workers (e.g., Celery) to free up server resources.
   - [Pattern: Asynchronous Processing](link-to-async-pattern.md).

---

## **Tools and Libraries**
| **Tool/Library**          | **Use Case**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------|
| **PostgreSQL `cursor`**   | Native cursor-based pagination in PostgreSQL.                                                    |
| **Django Pagination**     | Built-in cursor-based pagination for Django ORM.                                                  |
| **SSE.js**                | Library for handling Server-Sent Events in browsers.                                            |
| **WebSocket Libraries**   | `ws` (Node.js), `websockets` (Python), `Socket.IO` (real-time apps).                             |
| **NDJSON Streams**        | `ndjson` module (Node.js) or `ijson` (Python) for parsing NDJSON streams.                       |
| **Kafka Streams**         | Distributed streaming for event-driven architectures.                                           |
| **Apache Flink**          | Stateful stream processing for large-scale data pipelines.                                      |

---
## **Example Architecture**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│             │     │             │     │                 │
│   Client    │───▶│   API Gateway│───▶│   Database      │
│  (Browser/) │     │             │     │   (Postgres/)   │
│   (Mobile)  │     └─────────────┘     └─────────────┬─────┘
└─────────────┘                                │
                                                        │
┌────────────────────────────────────────────────────────▼─────────┐
│                                                                     │
│                     Streaming Layer (SSE/WebSocket)                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```
- **Client**: Issues streaming request (e.g., via SSE or WebSocket).
- **API Gateway**: Routes requests, enforces rate limits, and forwards to backend.
- **Database**: Returns paginated/streamed results efficiently (e.g., cursor-based).

---
## **Anti-Patterns**
1. ****Loading Entire Result Sets***
   - Avoid `SELECT * FROM large_table` without pagination. Always stream or limit results.

2. ****Unbounded OFFSET Pagination***
   - `OFFSET 100000` forces the database to scan 100,000 rows before returning results. Use cursors instead.

3. ****No Cursor Persistence***
   - If the client crashes, the server must not lose the cursor state. Implement client-side caching or server-side storage.

4. ****Ignoring Timeouts***
   - Long-running streams can block server resources. Enforce timeouts per chunk (e.g., 30s).

5. ****No Error Handling***
   - Assume network issues will occur. Implement retries, exponential backoff, and client reconnection logic.