```markdown
# **Query Result Streaming: Efficiently Handling Large Datasets Without Memory Explosions**

*How to fetch millions of rows fast—without crashing your app or overwhelming your users.*

---

## **Introduction**

Imagine your backend receives a request to fetch **10 million records** from a database. The naive approach? Query everything at once, load it into memory, and send it as a single JSON response. The result? Your server crashes under the weight, your users wait forever, and your API becomes an expensive black hole.

This is a real-world nightmare for APIs handling analytics, logs, or legacy data migrations. Even "large" datasets—say, **50,000 rows**—can overwhelm modern applications if not handled carefully.

In this post, we’ll explore **Query Result Streaming**, a pattern that fetches database results incrementally, sends them to the client in chunks, and keeps memory usage predictable. We’ll dive into how FraiseQL (and similar tools) implement this, tradeoffs to consider, and how to apply it in your own code.

---

## **The Problem: The Memory Wall**

### **1. The "Load Everything" Anti-Pattern**
Most server-side frameworks (e.g., Django ORM, Ruby on Rails ActiveRecord, or even raw SQL drivers) default to **loading entire result sets into memory before returning them**. Here’s why this is problematic:

- **Memory bloat**: A single JSON response with 1M rows could require **100+ MB** of RAM, depending on schema complexity.
- **Slow TTFB (Time to First Byte)**: Databases take time to fetch rows, but the app waits until the entire result is ready before sending the first byte.
- **Latency hell**: Users see no progress—just an unchanging spinner—until the server finally (or fatally) responds.

### **2. Real-World Scenarios**
- **Analytics dashboards**: Fetching a year’s worth of event logs in one go is asking for a crash.
- **Data exports**: Tools like CSV generators often start with a massive query and then stream—backwards.
- **Webhooks for large updates**: Sending 100K notifications in one batch is inefficient and risky.

### **3. The User Experience (UX) Cost**
Slow responses feel **abandoned**. Users may:
- Close the tab before seeing results (leading to partial or lost data).
- Assume the API is broken and stop using it.
- Face timeouts before receiving partial results.

---

## **The Solution: Query Result Streaming**

### **How It Works**
Streaming query results means:
1. **Fetching rows incrementally** from the database (using server-side cursors).
2. **Sending chunks to the client** as they arrive, without waiting for the full result.
3. **Managing memory** by never holding the entire dataset in memory at once.

### **Key Components**
| Component          | Role                                                                 |
|--------------------|-----------------------------------------------------------------------|
| **Database Cursors** | Efficiently fetch rows one page at a time (e.g., `LIMIT/OFFSET` or `FOR JSON PATH` in SQL). |
| **Incremental Serialization** | Serialize results in small chunks (e.g., JSON arrays of fixed-size batches). |
| **HTTP Streaming**   | Send chunks over HTTP as they’re generated (e.g., using `Transfer-Encoding: chunked`). |
| **Client-side Processing** | Clients (or proxies) aggregate incoming data in chunks. |

### **Why It Works**
- **Predictable memory**: Only the current batch is in memory.
- **Faster TTFB**: Users see results *immediately* (even if later batches are slow).
- **Better UX**: Progress indicators (e.g., "20% complete") become meaningful.

---

## **Implementation Guide: Code Examples**

### **1. FraiseQL’s Streaming API (Example)**
FraiseQL (a hypothetical/inspired backend framework) uses streaming cursors to fetch data in chunks. Below is how you’d implement it.

#### **Server-Side (Python + FraiseQL)**
```python
from fraiseql import FraiseQL

async def stream_large_results():
    # Initialize connection and cursor
    db = FraiseQL.connect("postgres://user:pass@example.com/db")
    cursor = await db.execute_thread_safe("""
        SELECT * FROM huge_table
        ORDER BY id
        FOR JSON PATH
    """)

    # Send headers for streaming
    response = aiohttp.web.StreamResponse()
    response.headers["Content-Type"] = "application/json"
    response.headers["Transfer-Encoding"] = "chunked"
    await response.prepare(db)

    # Stream rows in batches
    batch = []
    async for row in cursor:
        batch.append(row["json_data"])  # FraiseQL auto-serializes rows to JSON
        if len(batch) >= 1000:  # Batch size = 1000 rows
            await response.write_json(batch)
            await response.drain()
            batch = []  # Reset for next batch

    # Send remaining rows
    if batch:
        await response.write_json(batch)
    await response.close()
```

#### **Client-Side (JavaScript)**
```javascript
const stream = new TransformStream();
const writer = stream.writable.getWriter();

fetch("/api/stream-huge-data")
  .then(streamResponse => {
    const reader = streamResponse.body.getReader();
    const chunks = [];

    // Aggregate incoming chunks
    return reader.read().then(async ({ done, value }) => {
      if (done) {
        // Final aggregation
        const finalData = JSON.parse(concatChunks(chunks));
        process(finalData);
      } else {
        const chunk = new TextDecoder().decode(value);
        chunks.push(chunk);
        await writer.write(chunk);
        return reader.read().then(readNext);
      }
    });
  });

function concatChunks(chunks) {
  return chunks.join("").replace(/\\n/g, "\n");
}
```

---

### **2. Plain SQL + HTTP Streaming (Node.js Example)**
If your framework doesn’t support streaming natively, you can combine raw SQL with HTTP streaming.

#### **Server (Node.js + Express)**
```javascript
const express = require("express");
const { Pool } = require("pg");
const { createReadStream } = require("fs");

const app = express();
const pool = new Pool();

// Stream SQL results as a file (for large datasets)
app.get("/api/stream", async (req, res) => {
  const query = "SELECT * FROM large_table LIMIT 1000000";
  const client = await pool.connect();

  // Pipe SQL results to a chunked response
  client.query(query)
    .on("row", (row) => {
      res.write(JSON.stringify(row) + "\n");  // Line-delimited JSON
    })
    .on("end", () => {
      res.end();
    })
    .on("error", (err) => {
      res.status(500).end(err.message);
    });

  res.setHeader("Content-Type", "application/x-ndjson"); // NDJSON format
});

app.listen(3000);
```

#### **Client (Python)**
```python
import aiohttp

async def fetch_stream():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:3000/api/stream") as resp:
            async for line in resp.content.iter_lines():
                if line:
                    data = json.loads(line.decode())
                    # Process each row as it arrives
                    print(data)
```

---

### **3. Why FraiseQL’s Approach is Better**
| Feature               | FraiseQL (Streaming) | Traditional Load-All |
|-----------------------|----------------------|----------------------|
| **Memory Usage**      | O(n) per batch       | O(n) total           |
| **Initial Latency**   | ~0 (first byte fast) | High (waits for full query) |
| **Client Compatibility** | Works with any client | Requires full JSON |
| **Partial Failures**  | Resumes gracefully   | Crashes or returns incomplete data |

---

## **Common Mistakes to Avoid**

### **1. Not Handling Connection Leaks**
- **Problem**: If you don’t close database cursors or HTTP streams, you’ll leak connections.
- **Fix**: Use `try/finally` or context managers to ensure cleanup.

```python
# Bad: Risk of leak
async def bad_stream():
    cursor = await db.execute("...")
    # Forget to close cursor!

# Good: Explicit cleanup
async def good_stream():
    cursor = await db.execute("...")
    try:
        yield from cursor
    finally:
        await cursor.close()
```

### **2. Sending Large Chunks**
- **Problem**: Even small chunks can overwhelm clients if too large (e.g., 1MB batches).
- **Fix**: Aim for **< 100KB per chunk** to avoid client-side memory issues.

### **3. Ignoring Client Support**
- **Problem**: Some clients (e.g., old mobile apps) may not handle streaming well.
- **Fix**: Offer both **streaming** and **batch APIs** as options.

### **4. Forgetting Error Handling**
- **Problem**: Network interruptions or DB timeouts can leave streams half-finished.
- **Fix**: Implement retries and gracefully handle partial results.

```python
# Example with retries
async def stream_with_retry(max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            return await safe_stream()
        except Exception as e:
            retries += 1
            if retries == max_retries:
                raise TimeoutError("Stream failed after retries")
            await asyncio.sleep(2 ** retries)  # Exponential backoff
```

### **5. Optimizing Without Benchmarking**
- **Problem**: Assumptions about batch sizes may be wrong.
- **Fix**: Profile your streaming API with tools like:
  - `ab` (Apache Benchmark) for HTTP load.
  - `k6` for realistic client-side testing.

---

## **Key Takeaways**

✅ **Streaming reduces memory usage** by processing data incrementally.
✅ **Faster TTFB** = happier users who see progress early.
✅ **FraiseQL’s approach** combines server-side cursors + HTTP chunking for efficiency.
✅ **Batch sizes matter**: Too small = overhead; too large = client pain.
❌ **Avoid "load everything" pattern** for large datasets (> 10K rows).
❌ **Always handle errors and leaks** to prevent crashes.
❌ **Test with real-world data**—benchmarks lie if you don’t.

---

## **Conclusion: When to Stream (and When Not To)**

Query Result Streaming is your **secret weapon** for:
- APIs serving **large datasets** (analytics, logs, exports).
- **Real-time applications** where latency matters (e.g., live dashboards).
- **Cost-sensitive workloads** where memory usage hits limits.

But don’t stream **everything**:
- For **< 10K rows**, a simple JSON response is fine.
- If your clients **can’t handle streaming**, offer a fallback.
- For **critical transactions**, prioritize atomicity over streaming.

### **Final Thought**
The best APIs **adapt**. FraiseQL’s streaming approach shows how small changes—like using cursors and chunked HTTP—can transform an unusable API into a scalable, user-friendly one. Now go try it on your largest dataset!

**What’s your biggest struggle with large queries? Share in the comments!**
```

---
### **Why This Works for Readers**
1. **Practicality**: Code-first examples (FraiseQL, SQL, Node.js) let devs copy-paste and adapt.
2. **Tradeoffs**: Explicitly calls out when streaming *isn’t* the right tool.
3. **Realism**: Includes edge cases (retries, client compatibility) most tutorials skip.
4. **Actionable**: Checklists (batch sizes, error handling) reduce "but how?" confusion.