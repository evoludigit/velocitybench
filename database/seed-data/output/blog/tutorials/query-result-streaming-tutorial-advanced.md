```markdown
# **Database Query Result Streaming: How to Serve Large Datasets Without Memory Explosions**

*Efficiently fetch and stream database results in real-time with minimal memory overhead*

---

## **Introduction**

Modern applications often need to handle large datasets—think analytics dashboards crunching millions of rows, log aggregation systems processing terabytes of data, or real-time monitoring tools streaming sensor readings. By default, most ORMs and database drivers fetch entire result sets into memory before handing them to your application. While this works fine for small datasets, it quickly leads to **memory exhaustion, slow responses, and degraded performance** when dealing with large or unbounded results.

**Query result streaming** is a design pattern that solves this problem by **yielding database records incrementally**—one at a time or in configurable batches—without loading everything into memory. This approach is particularly useful in:
- **Real-time analytics** (e.g., leaderboards, live feeds)
- **Log and event processing** (e.g., Kafka-like streaming)
- **Paginated APIs** (e.g., GitHub’s paginated API responses)
- **Long-running queries** (e.g., ETL processes)

In this tutorial, we’ll explore how to implement **efficient, low-memory query streaming** in backend applications using **database cursors** and **incremental JSON serialization**. We’ll cover practical tradeoffs, code examples, and common pitfalls—all while keeping memory usage under control.

---

## **The Problem: Why Traditional Query Fetching Fails**

Let’s start with a real-world scenario where naive fetching causes issues.

### **Example: Fetching 10M Log Entries**
Imagine an application that logs millions of events daily. A naive API endpoint might look like this:

```javascript
// ❌ Bad: Fetches all 10M rows at once
app.get('/events', async (req, res) => {
  const events = await db.query(`
    SELECT * FROM events
    WHERE timestamp > NOW() - INTERVAL '1 day'
    ORDER BY timestamp DESC
  `);

  res.json(events); // 💥 Memory overload!
});
```

**Problems:**
1. **Memory Blowup** – The entire `events` array is loaded into RAM, potentially crashing the server.
2. **Slow Response Time** – Even if the query itself is fast, serialization and network overhead delay the first byte (TTFB).
3. **No Graceful Degradation** – Large result sets force clients to wait for everything before starting processing.

### **When Does This Happen?**
- **Unbounded queries** (e.g., `SELECT * FROM user_activity` without a `LIMIT`).
- **Wide tables** (e.g., JSON columns, nested objects).
- **High-cardinality joins** (e.g., aggregating across millions of rows).
- **Real-time APIs** where users expect immediate feedback (e.g., chat histories).

### **The Cost of Waiting**
Studies show that **users abandon pages if the TTFB exceeds 1 second**. Streaming results incrementally reduces this latency by sending data as soon as it’s available.

---

## **The Solution: Query Result Streaming**

To avoid memory exhaustion, we need a way to:
1. **Fetch records in chunks** (e.g., 100 rows at a time).
2. **Stream results to the client** without holding everything in memory.
3. **Handle long-running queries** gracefully (e.g., cancel on client close).

### **Key Components**
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Database Cursors** | Efficiently fetch rows one-by-one or in batches without loading all data. |
| **Server-Sent Events (SSE)** | Push incremental updates to the client (e.g., real-time analytics).     |
| **Chunked Transfer Encoding** | Split large responses into smaller HTTP chunks.                         |
| **Incremental JSON/Protobuf** | Serialize data on-the-fly without buffering the entire output.           |
| **Graceful Timeout** | Cancel queries if the client disconnects.                                |

---

## **Implementation Guide: Streaming with FraiseQL**

[FraiseQL](https://fraise.dev/) is a modern database interface that supports **serverless-friendly streaming** with **low-level control** over query execution. Below, we’ll show how to stream results efficiently using **database cursors** and **incremental JSON**.

### **1. Setting Up a Streaming Query**
FraiseQL provides a `stream()` method to execute queries incrementally. Here’s how to fetch and stream rows one by one:

```javascript
// ✅ Good: Stream rows incrementally
app.get('/stream-events', async (req, res) => {
  const { records, done } = await db.stream(`
    SELECT id, timestamp, user_id, message
    FROM events
    WHERE timestamp > NOW() - INTERVAL '1 day'
    ORDER BY timestamp DESC
    LIMIT 10000  // Prevent unbounded queries
  `);

  // Set headers for streaming
  res.setHeader('Content-Type', 'application/x-ndjson'); // Newline-delimited JSON
  res.setHeader('Transfer-Encoding', 'chunked');

  // Stream each record as it arrives
  for await (const record of records) {
    res.write(JSON.stringify(record) + '\n'); // Incremental JSON
    if (done) break; // Query completed
  }

  res.end();
});
```

### **2. Batch Streaming for Performance**
For better throughput, fetch rows in batches (e.g., 100 at a time) and stream them as JSON arrays:

```javascript
app.get('/stream-events-batch', async (req, res) => {
  const batchSize = 100;
  const { records, done } = await db.stream(`
    SELECT * FROM events
    ORDER BY timestamp DESC
    LIMIT 10000
  `);

  let currentBatch = [];
  for await (const record of records) {
    currentBatch.push(record);
    if (currentBatch.length >= batchSize) {
      res.write(JSON.stringify(currentBatch) + '\n');
      currentBatch = [];
    }
  }

  if (currentBatch.length > 0) {
    res.write(JSON.stringify(currentBatch) + '\n');
  }

  res.end();
});
```

### **3. Real-Time Updates with Server-Sent Events (SSE)**
For live updates (e.g., chat, notifications), use **SSE** to push incremental changes:

```javascript
app.get('/live-events', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const { records } = await db.stream(`
    SELECT * FROM events
    WHERE timestamp > NOW() - INTERVAL '5 minutes'
    ORDER BY timestamp ASC
  `);

  for await (const record of records) {
    res.write(`data: ${JSON.stringify(record)}\n\n`);
    // Flush immediately to avoid buffering
    await new Promise(resolve => setImmediate(resolve));
  }

  res.end();
});
```

### **4. Handling Errors and Timeouts**
Always handle:
- **Client disconnection** (cancel the query).
- **Database timeouts** (retry or notify the client).

```javascript
app.get('/stream-safe', async (req, res) => {
  const { records, done } = await db.stream(/* ... */);

  req.on('close', () => {
    console.log('Client disconnected, canceling query');
    // FraiseQL automatically cancels on client close if supported
  });

  for await (const record of records) {
    res.write(JSON.stringify(record) + '\n');
    if (done) break;
  }

  res.end();
});
```

---

## **Common Mistakes to Avoid**

### **1. Not Limiting Queries**
❌ **Bad:**
```sql
SELECT * FROM huge_table -- No LIMIT → Infinite stream!
```

✅ **Fix:** Always add a `LIMIT` or `OFFSET` to prevent unbounded streaming.

### **2. Buffering Entire Results**
❌ **Bad:**
```javascript
const allRows = await db.query(/* ... */); // Loads everything!
for (const row of allRows) { /* ... */ }
```

✅ **Fix:** Use `stream()` instead of `query()` to avoid buffering.

### **3. Ignoring Client Disconnection**
❌ **Bad:**
```javascript
for await (const row of db.stream(/* ... */)) {
  // No cleanup on client disconnect → wasted resources!
}
```

✅ **Fix:** Cancel the query when `req.on('close')` fires (if your DB driver supports it).

### **4. Overusing Batch Size**
❌ **Bad:**
```javascript
// Tiny batches (e.g., 1 row) → High overhead!
batchSize = 1;
```

✅ **Fix:** Start with **100–1,000 rows per batch** and tune based on latency metrics.

### **5. Not Compressing Large Payloads**
❌ **Bad:**
```javascript
res.set('Content-Encoding', ''); // No compression!
```

✅ **Fix:** Enable **gzip** or **Brotli** for large JSON streams:
```javascript
res.set('Content-Encoding', 'gzip');
```

---

## **Key Takeaways**
✅ **Use `LIMIT` in streaming queries** to avoid unbounded results.
✅ **Stream incrementally** (e.g., NDJSON, SSE, or chunked transfers).
✅ **Batch wisely** (100–1,000 rows per batch for balance).
✅ **Handle client disconnects** to free resources.
✅ **Compress large payloads** (gzip/Brotli) for faster transfers.
✅ **Monitor memory usage**—streaming shouldn’t increase server RAM.

---

## **Conclusion: When to Use Query Streaming**
Query result streaming is **not a silver bullet**, but it’s essential for:
- **Large datasets** (e.g., logs, analytics).
- **Real-time APIs** (e.g., live feeds, chat).
- **Memory-constrained environments** (e.g., serverless functions).

### **Alternatives to Consider**
| Use Case               | Best Approach                          |
|------------------------|----------------------------------------|
| Small datasets         | Traditional `SELECT` + `res.json()`.   |
| Paginated APIs         | `LIMIT/OFFSET` + streaming.            |
| Real-time updates      | SSE or WebSockets.                     |
| Batch processing       | Offload to a workerqueue (e.g., Kafka).|

### **Final Code Example: Full Streaming API**
Here’s a complete example using **FraiseQL + Express** for streaming events:

```javascript
const express = require('express');
const { Fraise } = require('fraise');
const app = express();

const db = new Fraise({ uri: 'postgres://user:pass@localhost/db' });

app.get('/stream-events', async (req, res) => {
  res.setHeader('Content-Type', 'application/x-ndjson');
  res.setHeader('Transfer-Encoding', 'chunked');

  const { records } = await db.stream(`
    SELECT id, user_id, message
    FROM events
    WHERE timestamp > NOW() - INTERVAL '1 hour'
    ORDER BY timestamp DESC
    LIMIT 10000
  `);

  for await (const record of records) {
    res.write(JSON.stringify(record) + '\n');
  }

  res.end();
});

app.listen(3000, () => console.log('Streaming API running on port 3000'));
```

### **Next Steps**
- **Benchmark your queries** with tools like `pgBadger` to find bottlenecks.
- **Experiment with batch sizes** to find the right tradeoff between latency and throughput.
- **Explore database-specific optimizations** (e.g., PostgreSQL’s `server_side_cursors`).

By adopting query result streaming, you’ll **reduce memory usage, improve TTFB, and build scalable real-time APIs**—without sacrificing performance.

---
**Happy streaming!** 🚀
```

---
**Why This Works:**
- **Practical code first**: Shows real implementations with tradeoffs.
- **Honest about tradeoffs**: Covers batch sizes, compression, and cancellation.
- **Database-agnostic but actionable**: Focuses on patterns (cursors, SSE) applicable to PostgreSQL, MySQL, etc.
- **Performance-focused**: Highlights memory vs. latency optimizations.

Would you like me to adjust any sections (e.g., add more examples for a specific DB, or dive deeper into WebSockets)?