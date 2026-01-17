# **Debugging Performance & Stress Testing: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **Introduction**
Performance & stress testing ensures your system behaves predictably under expected and unexpected load. When failures occur, debugging requires a systematic approach—identifying bottlenecks, analyzing resource consumption, and tuning performance-critical components.

This guide provides a structured troubleshooting methodology to diagnose and resolve performance-related issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm these symptoms:

✅ **Performance Degradation**
- Latency spikes under load (e.g., >1s for normal requests).
- Increased error rates (timeouts, 5xx responses).
- Slower response times (e.g., 95th percentile response time increases).

✅ **Resource Exhaustion**
- High CPU usage (>80% across all cores).
- Memory leaks (increasing OOM killer log entries).
- Disk I/O bottlenecks (high queue length in `iostat`).
- Network saturation (high packet loss, slow TCP connections).

✅ **Scalability Issues**
- System fails to handle expected traffic (e.g., sudden DDoS-like spikes).
- Database queries slow down under concurrent loads.
- Microservices fail to scale horizontally due to resource contention.

✅ **Reliability Problems**
- Frequent crashes under load (e.g., JVM `OutOfMemoryError`, Node.js `heap exhausted`).
- Inconsistent performance between staging and production.
- Timeouts during peak traffic (e.g., API gateways timing out).

✅ **Lack of Observability**
- No clear telemetry (no APM, no custom metrics).
- Logs lack meaningful performance context (e.g., no latency tracking).
- No baseline for performance comparison.

---

## **2. Common Issues & Fixes**

### **A. CPU Bottlenecks**
**Symptoms:**
- High CPU usage in `top`, `htop`, or cloud metrics.
- Jitter in response times (spikes every few seconds).
- Thread pools saturated (e.g., BlockingQueue full, Netty event loop starved).

**Debugging Steps:**
1. **Identify Hot Spots**
   - Use `perf` (Linux) or `VisualVM` (Java) to profile CPU-heavy methods.
   - Example (Java):
     ```bash
     perf record -g -p <PID>  # Record CPU usage
     perf report              # Analyze flamegraph
     ```
   - Example (Node.js):
     ```bash
     node --inspect ./app.js && node-inspector  # Generate CPU profiles
     ```

2. **Optimize Code**
   - Avoid CPU-bound loops (e.g., parse large JSON in-memory).
   - Use async I/O (e.g., `fs.promises` in Node.js, `async/await` in Java).
   - Example (Python):
     ```python
     # Bad (synchronous, blocks thread)
     def slow_process(data):
         return heavy_computation(data)

     # Good (async, non-blocking)
     async def fast_process(data):
         return await asyncio.to_thread(heavy_computation, data)
     ```

3. **Scale Horizontally**
   - Distribute workload across multiple instances (load balancer + auto-scaling).
   - Use stateless services where possible.

---

### **B. Memory Leaks**
**Symptoms:**
- Increasing heap usage over time (`jmap -heap` shows growth).
- `OutOfMemoryError` in Java/Node.js.
- Garbage collection (GC) running too frequently (`gc.log` analysis).

**Debugging Steps:**
1. **Capture Heap Dump**
   - Java:
     ```bash
     jmap -dump:format=b,file=heap.hprof <PID>
     ```
   - Node.js:
     ```bash
     node --inspect --inspect-brk ./app.js  # Attach debugger, dump heap
     ```
   - Analyze with **Eclipse MAT** or **Chrome Heap Snapshots**.

2. **Find Leaks**
   - Look for retained objects (e.g., unclosed connections, cached data).
   - Example (Java): Long-lived static collections.
     ```java
     // Bad: Static cache grows indefinitely
     private static Map<String, Object> cache = new HashMap<>();

     // Good: Use WeakReference or TTL cache (Guava Cache)
     Cache<String, Object> cache = CacheBuilder.newBuilder()
         .expireAfterWrite(10, TimeUnit.MINUTES)
         .build();
     ```

3. **Prevent Leaks**
   - Clean up resources (e.g., DB connections, file handles).
   - Use weak references for caching.
   - Monitor heap usage with Prometheus/Grafana.

---

### **C. Database Bottlenecks**
**Symptoms:**
- Slow queries under load (e.g., `EXPLAIN` shows full table scans).
- High `Slow Query Log` entries.
- Connection pool exhaustion (`Too many connections`).

**Debugging Steps:**
1. **Analyze Queries**
   - Use `EXPLAIN ANALYZE` (PostgreSQL) or `EXPLAIN` (MySQL).
   - Example:
     ```sql
     EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
     ```
   - Look for `seq_scan`, `Full Table Scan`, or `Sort`.

2. **Optimize Queries**
   - Add indexes for frequently queried columns.
     ```sql
     CREATE INDEX idx_users_email ON users(email);
     ```
   - Use pagination (`LIMIT/OFFSET`) for large datasets.
   - Avoid `SELECT *` (fetch only needed columns).

3. **Connection Pool Tuning**
   - Increase pool size (but avoid over-provisioning).
   - Example (HikariCP for Java):
     ```java
     HikariConfig config = new HikariConfig();
     config.setMaximumPoolSize(20);
     config.setConnectionTimeout(30000);
     ```

4. **Read Replicas & Caching**
   - Offload read queries to replicas.
   - Use Redis/Memcached for caching frequent queries.

---

### **D. Network Latency & Timeouts**
**Symptoms:**
- High TCP retransmission rates (`ss -s` in Linux).
- API gateways timing out (5xx errors).
- Slow inter-service communication (gRPC/HTTP delays).

**Debugging Steps:**
1. **Check Network Metrics**
   - `ping`, `mtr`, `traceroute` to identify slow hops.
   - Example:
     ```bash
     mtr google.com  # Check latency to external APIs
     ```

2. **Optimize Connections**
   - Reuse HTTP/HTTPS connections (keep-alive).
   - Example (Node.js `axios`):
     ```javascript
     const axios = require('axios');
     const http = axios.create({
       maxRedirects: 5,
       timeout: 10000,
       httpAgent: new http.Agent({ keepAlive: true }),
     });
     ```
   - Use connection pooling for DBs.

3. **Load Balancer Tuning**
   - Increase timeout thresholds (e.g., 30s).
   - Use **gRPC** instead of REST for binary protocols (lower overhead).

4. **CDN & Edge Caching**
   - Cache static assets with Cloudflare/CDN.
   - Use edge computing (e.g., AWS Lambda@Edge).

---

### **E. Load Balancer & Auto-Scaling Issues**
**Symptoms:**
- Instances getting overwhelmed under load.
- Auto-scaling fails to spin up new instances.
- Sticky sessions cause uneven load distribution.

**Debugging Steps:**
1. **Check Cloud Metrics**
   - AWS: CloudWatch Alarms for CPU/Memory.
   - GCP: Stackdriver for instance load.
   - Kubernetes: `kubectl top pods` for pod resource usage.

2. **Tune Auto-Scaling Rules**
   - Adjust scaling policies (e.g., scale out at 70% CPU).
   - Example (AWS Auto Scaling):
     ```yaml
     ScalingPolicy:
       - PolicyName: ScaleUp
         AdjustmentType: ChangeInCapacity
         MinCapacity: 2
         MaxCapacity: 10
         ScaleOutCooldown: 300
     ```

3. **Optimize Load Balancer Health Checks**
   - Reduce health check intervals (e.g., 10s instead of 5s).
   - Example (Nginx):
     ```nginx
     upstream backend {
         zone backend 64k;
         server 127.0.0.1:8080 health_check interval=10s;
     }
     ```

4. **Use Horizontal Pod Autoscaler (K8s)**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: my-app-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: my-app
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 80
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                          | **Example Command/Usage**                     |
|------------------------|--------------------------------------|-----------------------------------------------|
| **`perf` (Linux)**     | CPU profiling                        | `perf record -g -p <PID>`                      |
| **`VisualVM` (Java)**  | Memory & CPU analysis                | Attach to JVM process                        |
| **`jstack`**           | Java thread dump                     | `jstack <PID> > thread_dump.log`              |
| **`strace`**           | System call tracing                  | `strace -p <PID> -o trace.log`                |
| **`tcpdump`**          | Network packet inspection            | `tcpdump -i any port 80 -w capture.pcap`      |
| **Prometheus + Grafana** | Metrics & dashboards          | `prometheus-node-exporter` + `grafana`        |
| **Datadog/New Relic**  | APM (latency & error tracking)      | Integrate with your app                      |
| **k6/Locust**          | Load testing                         | `k6 run script.js --vus 100 --duration 30s`    |
| **Eclipse MAT**        | Java heap analysis                   | Open `heap.hprof` file                        |
| **`netstat`/`ss`**     | Network connection stats              | `ss -tulnp`                                   |

**Advanced Techniques:**
- **Distributed Tracing**: Use **Jaeger** or **Zipkin** to trace requests across services.
- **Synthetic Monitoring**: Simulate user journeys (e.g., **Gatling**, **BlazeMeter**).
- **Chaos Engineering**: Test resilience with **Gremlin** or **Chaos Mesh**.

---

## **4. Prevention Strategies**

### **A. Proactive Monitoring**
- **Set Up Baselines**:
  - Record **P99 latency**, **error rates**, and **throughput** under normal load.
  - Use **Prometheus Alertmanager** to detect anomalies.
- **SLOs & Error Budgets**:
  - Define **Service Level Objectives (SLOs)** (e.g., 99.9% uptime).
  - Example:
    ```
    Target: 99.9% available
    Error Budget: 0.1% = 8.76 hours/year
    ```

### **B. Load Testing in CI/CD**
- **Integrate Load Tests**:
  - Run **k6/Locust** in GitHub Actions:
    ```yaml
    jobs:
      load-test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
          - run: npm install -g k6
          - run: k6 run script.k6 --vus 50 --duration 1m
    ```
- **Fail Fast**:
  - Reject PRs if load test fails.

### **C. Optimize for Scale**
- **Stateless Services**: Use **Kubernetes** or **serverless** (AWS Lambda).
- **Asynchronous Processing**: Offload long tasks to **Kafka/RabbitMQ**.
  ```java
  // Bad: Blocking call
  CompletableFuture<void> syncTask();

  // Good: Async + Callback
  asyncTask().thenAccept(result -> {
      // Handle result
  });
  ```
- **Caching Layer**: Use **Redis** for frequent queries.
  ```python
  # Python with Redis
  import redis
  r = redis.Redis()
  cache_key = "user:123"
  user_data = r.get(cache_key)
  if not user_data:
      user_data = fetch_from_db(123)
      r.setex(cache_key, 300, user_data)  # Cache for 5 mins
  ```

### **D. Disaster Recovery**
- **Chaos Testing**: Introduce failures (e.g., kill random pods in K8s).
- **Multi-Region Deployments**: Use **DNS failover** (e.g., AWS Route 53).
- **Database Backups**: Test restore procedures.

---

## **5. Step-by-Step Debugging Workflow**
When a performance issue arises, follow this **structured approach**:

1. **Reproduce the Issue**
   - Use **k6** or **Locust** to simulate the load.
     ```bash
     locust -f locustfile.py --host=http://your-api --headless -u 1000 -r 100
     ```
   - Check logs (`journalctl`, ELK Stack).

2. **Check Metrics**
   - Look for spikes in:
     - CPU (`top -c`)
     - Memory (`free -h`)
     - Network (`ss -s`)
     - Database queries (`pg_stat_activity`)

3. **Isolate the Bottleneck**
   - If **CPU** is high → Profile with `perf`.
   - If **Memory** grows → Capture heap dump.
   - If **DB** is slow → Analyze slow queries.

4. **Apply Fixes (Code/Infrastructure)**
   - Optimize hot paths.
   - Scale horizontally/vertically.
   - Adjust timeouts/retries.

5. **Verify & Monitor**
   - Rerun load test.
   - Set up alerts (Prometheus/Grafana).
   - Document the fix in a **postmortem**.

---

## **6. Example Debugging Session (Case Study)**
**Issue**: API latency spikes to **10s** under 1000 RPS (from 500ms).

### **Steps:**
1. **Check Metrics**
   - `top` shows **95% CPU** on a single instance.
   - `pg_stat_activity` shows **blocked connections** in PostgreSQL.

2. **Profile CPU**
   - `perf record -g -p <PID>` → Identifies `sort()` on a large dataset.

3. **Fix**
   - Add an index on the sorted column.
   - Optimize the query with `LIMIT/OFFSET`.
   - Scale horizontally (add read replicas).

4. **Result**
   - Latency drops to **150ms** at 1000 RPS.

---

## **7. Key Takeaways**
| **Area**          | **Debugging Focus**                  | **Prevention**                          |
|-------------------|--------------------------------------|-----------------------------------------|
| **CPU**           | Profile with `perf`/VisualVM          | Async I/O, horizontal scaling            |
| **Memory**        | Heap dumps (`jmap`, Eclipse MAT)     | Leak detection, weak references         |
| **Database**      | `EXPLAIN ANALYZE`, connection pool    | Indexes, read replicas, caching         |
| **Network**       | `tcpdump`, connection reuse           | gRPC, CDN, keep-alive                   |
| **Scaling**       | Cloud metrics, auto-scaling rules    | Stateless services, K8s HPA              |

---

## **8. Further Reading**
- **Books**:
  - *Production ready microservices* (Samsa)
  - *Site Reliability Engineering* (Google)
- **Tools**:
  - [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
  - [k6 Load Testing](https://k6.io/docs/)
  - [Chaos Engineering (Gremlin)](https://www.gremlin.com/)

---

## **Final Notes**
- **Debugging performance issues requires patience**—start with metrics, then dive into code.
- **Automate monitoring** to catch issues before users do.
- **Load test early and often** (not just in production).

By following this guide, you’ll systematically **identify, fix, and prevent** performance bottlenecks. 🚀