**[Pattern] Latency Approaches Reference Guide**

---

### **Overview**
Latency approaches mitigate delays in distributed systems by optimizing data retrieval, processing, or user interaction. This pattern categorizes latency strategies—**caching, batching, asynchronicity, and adaptive buffering**—to reduce perceived or actual delay while preserving functionality. Key trade-offs include **speed vs. consistency**, **resource usage**, and **user experience (UX) impact**.

Latency approaches are essential for:
- Real-time applications (e.g., games, IoT platforms).
- High-throughput systems (e.g., analytics pipelines).
- User-facing services where delay correlates with engagement loss.

Use this guide to evaluate which latency approach aligns with your system’s constraints (e.g., latency thresholds, budget, and scalability needs).

---

### **1. Schema Reference**
| **Approach**       | **Description**                                      | **Use Case Examples**                          | **Key Parameters**                                                                 | **Trade-offs**                                                                 |
|--------------------|------------------------------------------------------|-----------------------------------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Caching**        | Stores copies of frequently accessed data/proxies closer to users. | CDNs, session data, query results.            | - Cache TTL (time-to-live) <br> - Hit ratio (e.g., 80%) <br> - Cache granularity (key/value vs. full-page). | Memory overhead, stale data if TTL expires.                                      |
| **Batching**       | Aggregates requests/responses to reduce round trips. | Analytics dashboards, log forwarding.         | - Batch size (e.g., 100 records) <br> - Threshold latency (e.g., 1 sec).            | Delayed user feedback, higher processing load.                                  |
| **Asynchronous**   | Decouples request/response with callbacks or queues. | Notifications, background jobs.                | - Queue depth (e.g., 10_000 messages) <br> - Timeout (e.g., 5 min).               | Complex error handling; eventual consistency.                                  |
| **Adaptive Buffering** | Dynamically adjusts buffering based on network conditions. | Video streaming, VoIP.                      | - Buffer threshold (e.g., 3 sec) <br> - Adaptive bitrate (ABR) levels.             | Increased CPU/memory for dynamic adjustments; higher initial load time.         |
| **Edge Computing** | Processes data closer to the user (e.g., IoT edge nodes). | IoT sensor data, AR/VR.                     | - Edge node latency (e.g., <50ms). <br> - Data synchronization interval.         | Limited compute resources; higher edge infrastructure cost.                      |

---

### **2. Implementation Details**

#### **A. Caching**
**Key Concepts:**
- **Cache Levels**: Local (browser/device), client-side (CDN), server-side (applications), distributed (Redis, Memcached).
- **Cache Invalidation**: Time-based (TTL), event-based (e.g., write-through), or hybrid.
- **Cache Eviction Policies**: LRU (Least Recently Used), LFU (Least Frequently Used), size-based.

**Implementation Steps:**
1. **Identify Cacheable Data**:
   - Static assets (HTML/CSS/JS), API responses, or user sessions.
   - Use tools like **Apache JMeter** to measure cache hit ratios.
2. **Select a Cache Tier**:
   - **CDN Caching**: For static assets (e.g., Cloudflare, Akamai).
   - **Application Caching**: For dynamic data (e.g., Redis via `redis-cli`).
   - **Database Caching**: Query-level caching (e.g., PostgreSQL’s `pg_cache`).
3. **Configure TTL**:
   - Short TTL (e.g., 5 min) for volatile data; long TTL (e.g., 1 hour) for static content.
   - Example (Redis):
     ```redis
     SETEX key "value" 300  # 5-minute TTL
     ```
4. **Handle Cache Stampedes**:
   - Use **locks** (e.g., Redis `SETNX`) or **pre-warming** (populate cache before request spikes).

**Example Architecture**:
```
User → CDN (Static Assets) → Application (Dynamic Data via Redis) → Database
```

---

#### **B. Batching**
**Key Concepts:**
- **Request Batching**: Combines multiple client requests into one (e.g., GraphQL batches).
- **Response Batching**: Aggregates server responses (e.g., log shipping).
- **Time vs. Size Batching**: Trigger batches after X time *or* X records.

**Implementation Steps:**
1. **Client-Side Batching**:
   - Example (JavaScript):
     ```javascript
     const batchRequests = [];
     const MAX_BATCH_SIZE = 10;

     function addToBatch(url, data) {
       batchRequests.push({ url, data });
       if (batchRequests.length >= MAX_BATCH_SIZE) {
         fetchAll(batchRequests);
         batchRequests = [];
       }
     }
     ```
2. **Server-Side Batching**:
   - Use frameworks like **Spring Batch** (Java) or **Dask** (Python) for ETL pipelines.
   - Example (Python with Dask):
     ```python
     import dask.bag as db
     batch = db.from_delimited_text("log_file.csv").map(process_log).compute()
     ```
3. **Monitor Batching Impact**:
   - Track **batch latency** (e.g., Prometheus metrics) and **throughput**.

**Trade-off Management**:
- Balance batch size vs. timeout (e.g., `batch_size=200`, `timeout=1000ms`).

---

#### **C. Asynchronous Processing**
**Key Concepts:**
- **Message Queues**: Kafka, RabbitMQ, AWS SQS.
- **Callbacks/Polling**: Client-side async patterns (e.g., WebSockets).
- **Event Sourcing**: Store state changes as events for replayability.

**Implementation Steps:**
1. **Queue-Based Asynchronicity**:
   - Example (Kafka Producer/Consumer):
     ```java
     // Producer
     producer.send(new ProducerRecord<>("topic", key, value));

     // Consumer
     consumer.subscribe(Collections.singletonList("topic"));
     ```
2. **Callback Systems**:
   - Example (Node.js with Express):
     ```javascript
     app.post("/upload", async (req, res) => {
       const result = await uploadToS3(req.file);
       res.json({ status: "async", callbackUrl: `callback?id=${result.id}` });
     });
     ```
3. **Error Handling**:
   - Implement **retry policies** (exponential backoff) and **dead-letter queues** for failed tasks.

**Example Workflow**:
```
User → API (Response: "Async, id=123") → Queue → Worker → Callback URL
```

---

#### **D. Adaptive Buffering**
**Key Concepts:**
- **Real-Time Adaptive Streaming (RTAS)**: Adjusts buffer based on network conditions (e.g., HLS, DASH).
- **Dynamic Payload Splitting**: For low-latency video (e.g., 3GPP’s CMAF).

**Implementation Steps:**
1. **ABR Algorithms**:
   - Use **BBA (Buffer-Based Adaptation)** or **PBA (Predictive Buffer Adaptation)**.
   - Example (FFmpeg for HLS):
     ```bash
     ffmpeg -i input.mp4 -c:v libx264 -f hls -hls_time 4 -hls_playlist_type vod output.m3u8
     ```
2. **Client-Side Buffer Management**:
   - JavaScript (Mozilla’s `MediaSourceExtensions` API):
     ```javascript
     const mediaSource = new MediaSource();
     mediaSource.addEventListener("sourceopen", () => {
       const buffer = mediaSource.addSourceBuffer("video/mp4");
       buffer.appendBuffer(chunkData);
     });
     ```
3. **Server-Side DASH**:
   - Use **MPEG-DASH** with adaptive bitrate (ABR) segments.

**Latency Metrics to Monitor**:
- **Start-up latency** (time to first frame).
- **Rebuffering ratio** (% of time spent buffering).

---

#### **E. Edge Computing**
**Key Concepts:**
- **Edge Nodes**: Deploy compute closer to users (e.g., AWS Local Zones, Cloudflare Workers).
- **Edge Database**: Distributed caches (e.g., Redis Edge).

**Implementation Steps:**
1. **Select Edge Deployment**:
   - **CDN Edge**: For static content (Cloudflare).
   - **Edge Functions**: For runtime logic (AWS Lambda@Edge).
2. **Data Replication**:
   - Sync data between edge and central databases (e.g., using **CockroachDB**).
3. **Latency Testing**:
   - Use **Pingdom** or **New Relic** to measure edge node latency.

**Example Architecture**:
```
User → Edge Node (Compute/Cache) → Origin Server (Fallback)
```

---

### **3. Query Examples**
#### **Caching Queries**
- **Redis CLI**:
  ```bash
  # Check cache hit ratio
  INFO stats | grep "keyspace_hits"

  # Invalidate key
  DEL user:123
  ```
- **SQL (PostgreSQL)**:
  ```sql
  -- Enable query caching
  SET enable_seqscan = off;

  -- Check cache
  SELECT * FROM pg_stat_activity WHERE query ILIKE '%SELECT%';
  ```

#### **Batching Queries**
- **GraphQL (Batching Example)**:
  ```graphql
  query {
    user(id: 1) { name }
    post(id: 1) { title }
    # Batching reduces round trips
  }
  ```
- **PostgreSQL (Batch Fetch)**:
  ```sql
  -- Fetch 100 records at once
  SELECT * FROM users LIMIT 100 OFFSET 0;
  ```

#### **Asynchronous Queries**
- **Kafka Consumer (Python)**:
  ```python
  from kafka import KafkaConsumer
  consumer = KafkaConsumer("orders", bootstrap_servers="localhost:9092")
  for msg in consumer:
      print(f"Processed: {msg.value}")
  ```
- **WebSocket Callback (Node.js)**:
  ```javascript
  // Server
  const ws = new WebSocketServer({ port: 8080 });
  ws.on("connection", (conn) => {
    setTimeout(() => conn.send(JSON.stringify({ status: "completed" })), 5000);
  });
  ```

#### **Adaptive Buffering (FFmpeg)**
```bash
# Adaptive streaming with buffer hints
ffmpeg -i input.mp4 \
  -c:v libx264 -profile:v high -level 4.1 \
  -b:v 1000k -maxrate 1500k -bufsize 2000k \
  -hls_time 4 -hls_playlist_type vod \
  -hls_segment_type fmp4 \
  output.m3u8
```

---

### **4. Related Patterns**
| **Related Pattern**       | **Connection to Latency Approaches**                                                                 | **When to Use Together**                                 |
|---------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **Circuit Breaker**       | Reduces latency by avoiding failed dependencies (e.g., fallback to cache if DB is down).           | High-availability systems (e.g., e-commerce).         |
| **Pipelining**           | Overlaps processing steps to reduce idle time (e.g., HTTP pipelining).                           | Low-latency APIs (e.g., trading platforms).           |
| **Load Shedding**        | Dynamically reduces workload to manage latency spikes (e.g., drop non-critical queries).           | Autoscale environments with variable traffic.          |
| **Data Partitioning**    | Distributes data to reduce query latency (e.g., sharding).                                       | Global-scale apps (e.g., social networks).            |
| **Progressive Loading**  | Loads content incrementally to hide latency (e.g., lazy-loading images).                          | Mobile/web apps with long load times.                 |

---

### **5. Best Practices**
1. **Measure Before Optimizing**:
   - Use **latency percentiles** (P95, P99) to identify bottlenecks.
   - Tools: **New Relic**, **Datadog**, or custom **Prometheus/Grafana** dashboards.
2. **Start with Low-Hanging Fruit**:
   - Optimize caching first; then batch; finally async.
3. **Monitor Trade-offs**:
   - Cache: Track hit ratio vs. memory usage.
   - Batching: Monitor queue depth and end-to-end latency.
4. **Fallback Mechanisms**:
   - Cache invalidation → database fallback.
   - Async jobs → synchronous retry.
5. **User-Centric Design**:
   - Use **skeleton screens** (e.g., "Loading...") to mask latency.
   - Example (React):
     ```jsx
     function LoadingSkeleton() {
       return <div className="skeleton-loader"></div>;
     }
     ```

---
### **6. Anti-Patterns**
- **Over-Caching**: Caching stale data harms consistency (e.g., financial systems).
- **Unbounded Batching**: Causes timeouts (e.g., batch size = 1M records).
- **Blocking Asynchronous Code**: Mixing sync/async poorly (e.g., `await` in a callback hell).
- **Ignoring Edge Cases**: Edge computing fails if network partitions exist.

---
### **7. Tools & Libraries**
| **Category**       | **Tools/Libraries**                                                                                     | **Use Case**                                  |
|--------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Caching**        | Redis, Memcached, Varnish, CDN (Cloudflare)                                                         | High-throughput read-heavy workloads.      |
| **Batching**       | Spring Batch, Dask, Apache Beam, GraphQL Batching (relay)                                           | Data pipelines, analytics.                  |
| **Asynchronous**   | Kafka, RabbitMQ, AWS SQS/SNS, WebSockets                                                               | Event-driven architectures.                 |
| **Adaptive Buffering** | FFmpeg (HLS/DASH), MPV (video player), Mozilla’s `MediaSource` API                               | Video streaming.                            |
| **Edge Computing** | AWS Lambda@Edge, Cloudflare Workers, Akamai EdgeWorkers                                           | Low-latency global apps.                   |

---
### **8. Further Reading**
- **Books**:
  - *Designing Data-Intensive Applications* (Martin Kleppmann) – Ch. 3 (Replication), Ch. 4 (Partitioning).
- **Papers**:
  - "The Latency Numbers Every Programmer Should Know" (Jeff Dean) – [Link](https://research.google/pubs/pub36356/).
- **Blogs**:
  - [Cloudflare’s Guide to Edge Computing](https://www.cloudflare.com/learning/edge-network/edge-computing/).
  - [Kafka’s Asynchronous Processing Patterns](https://kafka.apache.org/documentation/#asynchronous).