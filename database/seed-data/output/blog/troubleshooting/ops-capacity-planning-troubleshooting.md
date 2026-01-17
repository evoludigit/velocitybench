# **Debugging *Capacity Planning Patterns*: A Troubleshooting Guide**

Capacity planning ensures that your system can handle expected and unexpected workloads efficiently. Poor capacity planning can lead to performance degradation, resource exhaustion, and cascading failures—often detected only when it's too late. Below is a structured approach to diagnosing and resolving capacity-related issues.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the root cause based on observable symptoms:

| **Symptom** | **When to Suspect** | **Tools to Inspect** |
|-------------|---------------------|----------------------|
| **High CPU/Memory/Storage Usage** | System slows under load, processes fail due to OOM, or disk I/O spikes. | `top`, `htop`, `vmstat`, `iostat`, Prometheus/Grafana dashboards. |
| **Increased Latency/Timeouts** | API requests or database queries take longer than expected, or clients time out. | APM tools (New Relic, Datadog), `ping`, `traceroute`, or custom logging. |
| **Service Failures or Restarts** | Containers, VMs, or microservices crash or restart frequently. | Logs (`journalctl`, Kubernetes `kubectl logs`), crash dumps. |
| **Unpredictable Scaling Behavior** | Auto-scaling policies (K8s HPA, AWS ASG) fail to adjust capacity in time. | Cloud provider metrics (CloudWatch, GCP Monitoring), K8s HPA events. |
| **Unexpected Resource Spikes** | Sudden surges in network traffic, CPU, or memory without clear triggers. | Time-series databases (InfluxDB), log aggregation (ELK, Loki). |
| **Data Inconsistencies** | Duplicates, lost writes, or stale reads after load testing. | Database logs (`pg_log`, `mysql-bin`), consistency checks (e.g., MySQL `PTAS`). |

---

## **2. Common Issues & Fixes**
### **Issue 1: Insufficient Horizontal Scaling**
**Symptoms:**
- Requests queue up or time out during traffic spikes.
- CPU usage remains near 100% even after scaling.

**Root Cause:**
- Auto-scaling thresholds are misconfigured (e.g., CPU < 70% triggers scaling).
- Instance types are undersized (e.g., `t3.micro` for CPU-heavy workloads).
- Sticky sessions or database connections prevent efficient load distribution.

**Fixes:**
#### **A. Adjust Auto-Scaling Policies (Kubernetes Example)**
```yaml
# hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80  # Scale up at 80% CPU
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 90
```
**Key Adjustments:**
- Reduce `minReplicas` if cold starts are an issue (but ensure baseline availability).
- Increase `maxReplicas` for bursty traffic (e.g., marketing campaigns).
- Add **custom metrics** (e.g., request queue depth) if CPU isn’t the bottleneck.

#### **B. Use Right-Sized Instances**
- **AWS:** Replace `t3.medium` with `m5.large` for CPU-bound workloads.
- **GCP:** Use `n2-standard-4` for CPU-intensive tasks.
- **Azure:** Opt for `Standard_D4s_v3` for mixed workloads.

#### **C. Optimize Database Connections**
```java
// Java (HikariCP) example
HikariConfig config = new HikariConfig();
config.setMaximumPoolSize(20);  // Adjust based on RPS
config.setConnectionTimeout(30000);
config.setIdleTimeout(600000);
```
**Tip:** Use connection pooling (PgBouncer for PostgreSQL) to avoid database overload.

---

### **Issue 2: Throttling Due to Rate Limiting**
**Symptoms:**
- 429 (Too Many Requests) errors from APIs (e.g., AWS API Gateway, Cloudflare).
- Client-side retries exhaust backend resources.

**Root Cause:**
- Missing or misconfigured rate limits.
- Distributed systems don’t sync throttling state (e.g., Redis rate limiter failures).

**Fixes:**
#### **A. Implement Rate Limiting in API Gateway**
**AWS API Gateway:**
```json
// SAM template snippet
Resources:
  MyApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: Prod
      MethodSettings:
        - HttpMethod: "*"
          ResourcePath: "/*"
          ThrottlingBurstLimit: 100
          ThrottlingRateLimit: 50
```

#### **B. Distributed Rate Limiter (Redis Example)**
```python
# Python (Using redis-py)
import redis
import time

r = redis.Redis(host='redis', port=6379, db=0)

def rate_limit(key, max_requests, window_secs):
    current = int(time.time())
    pipe = r.pipeline()
    pipe.zadd(f"rate:{key}:{current}", {current: 1})
    pipe.zremrangebyscore(f"rate:{key}:*", 0, current - window_secs)
    pipe.expire(f"rate:{key}:{current}", window_secs)
    requests = pipe.execute()[0]
    if requests > max_requests:
        raise Exception("Rate limit exceeded")
```
**Use Case:** Limit API calls to 100 per minute per user (`key = f"user:{user_id}"`).

---

### **Issue 3: Gradual Performance Degradation**
**Symptoms:**
- System works fine at 50% load but crashes at 70%.
- Memory leaks or slow query accumulation over time.

**Root Cause:**
- **Memory leaks:** Unreleased objects (e.g., unclosed database connections).
- **Slow queries:** Unindexed database columns or N+1 query problems.
- **Caching issues:** Stale or inconsistent cache invalidation.

**Fixes:**
#### **A. Identify Memory Leaks**
**Tools:**
- **Java:** VisualVM, YourKit, or `jmap -heap <pid>`.
- **Node.js:** `--inspect` + Chrome DevTools.
- **Python:** `tracemalloc` or `objgraph`.

**Example (Java):**
```bash
# Capture heap dump when leak is suspected
jmap -dump:format=b,file=heap.hprof <pid>
```
**Fix:** Check for:
- Unclosed streams (e.g., file handles, JDBC connections).
- Large objects accumulating (e.g., in-memory caches).

#### **B. Optimize Database Queries**
**Problem:** Slow `SELECT *` on large tables.
**Fix:** Add indexes and limit columns:
```sql
-- Before (slow)
SELECT * FROM users WHERE email = 'user@example.com';

-- After (fast)
SELECT id, name FROM users WHERE email = 'user@example.com';
```
**Tool:** Use `EXPLAIN ANALYZE` in PostgreSQL/MySQL to debug queries.

#### **C. Implement Cache Invalidation**
```python
# Python (Redis cache with TTL)
@lru_cache(maxsize=128)
def get_expensive_data(key):
    return fetch_from_db(key)

# Or explicit TTL with Redis
r.setex(f"cache:key:{key}", 300, expensive_data)  # 5-minute TTL
```

---

### **Issue 4: Cold Start Latency in Serverless**
**Symptoms:**
- First request after inactivity is slow (e.g., AWS Lambda, Cloud Run).
- Auto-scaling fails due to delayed container initialization.

**Root Cause:**
- No warm-up traffic.
- Large dependencies (e.g., Java Spring Boot apps).
- Idle timeouts (e.g., Kubernetes pods terminated after 5 mins).

**Fixes:**
#### **A. Use Provisioned Concurrency (AWS Lambda)**
```bash
aws lambda update-function-configuration \
  --function-name my-function \
  --provisioned-concurrent-executions 5
```
**Trade-off:** Higher cost but faster cold starts.

#### **B. Keep Containers Warm (Kubernetes)**
```yaml
# deployment.yaml
spec:
  replicas: 2
  minReadySeconds: 30
  template:
    spec:
      containers:
      - name: my-app
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60  # Wait for startup
```
**Tool:** Use `kubectl top pods` to monitor CPU/memory during idle.

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                     |
|------------------------|-----------------------------------------------|------------------------------------------|
| **Prometheus + Grafana** | Monitor metrics (CPU, memory, latency).     | `prometheus-query --query="rate(http_requests_total[5m])"` |
| **JVM Profiler (Async Profiler)** | Find CPU bottlenecks in Java.          | Download from [async-profiler](https://github.com/jvm-profiling-tools/async-profiler) |
| **Blackbox Exporter**   | Synthetic monitoring (e.g., ping latency).   | `blackbox_exporter --config.file=config.yaml` |
| **k6 / Locust**         | Load test capacity limits.                  | `k6 run --vus 100 --duration 30m script.js` |
| **Trivero / Datadog**   | APM for distributed tracing.                 | Set up middleware (e.g., OpenTelemetry). |
| **AWS CloudWatch Logs Insights** | Query logs for errors.              | `filter @message like /ERROR/`          |

**Technique: Root Cause Analysis (RCA)**
1. **Reproduce the issue** (load test or wait for next spike).
2. **Isolate the component** (e.g., API vs. DB vs. caching layer).
3. **Check logs/metrics** for the component under stress.
4. **Test hypotheses** (e.g., modify `max-connections` in DB config).
5. **Iterate** until resolved.

---

## **4. Prevention Strategies**
### **A. Proactive Monitoring**
- **Set up alerts** for:
  - CPU > 90% for 5 mins.
  - Memory OOM kills.
  - Database replication lag.
- **Tools:**
  - Prometheus Alertmanager.
  - AWS CloudWatch Alarms.
  - Datadog Anomaly Detection.

### **B. Load Testing Before Deployment**
- **Tools:**
  - **k6:** Lightweight, scriptable (e.g., simulate 1,000 RPS).
  - **Gatling:** Advanced scenarios (e.g., think-time delays).
- **Example k6 Script:**
  ```javascript
  import http from 'k6/http';
  import { check, sleep } from 'k6';

  export const options = {
    vus: 100,    // Virtual users
    duration: '30s',
  };

  export default function () {
    const res = http.get('https://api.example.com/endpoint');
    check(res, {
      'status is 200': (r) => r.status === 200,
    });
    sleep(1);  // Simulate user think time
  }
  ```

### **C. Capacity Planning Best Practices**
1. **Historical Data Analysis:**
   - Use **time-series forecasting** (e.g., Prophet, ARIMA) to predict traffic.
   - Example: If daily traffic grows 20% MoM, plan for 30% buffer.
2. **Multi-Region Deployment:**
   - Use **cloud providers’ regional auto-scaling** (e.g., GCP Regions).
3. **Chaos Engineering:**
   - Test failure scenarios with **Gremlin** or **Chaos Mesh** (K8s).
   - Example: Kill 50% of pods to see if the system recovers.
4. **Document SLOs/SLIs:**
   - Define **Service Level Objectives (SLOs)** (e.g., "99.9% of requests < 500ms").
   - Use **Error Budgets** to balance reliability and innovation.

### **D. Architectural Patterns**
| **Pattern**            | **When to Use**                          | **Example**                          |
|------------------------|------------------------------------------|---------------------------------------|
| **Circuit Breaker**    | Prevent cascading failures.              | Hystrix, Resilience4j.                |
| **Queue-Based Scaling** | Decouple producers/consumers.           | Kafka, SQS with multiple consumers.   |
| **Multi-Tier Caching** | Reduce DB load.                          | Redis (L1) + Memcached (L2).          |
| **Sharding**           | Scale databases horizontally.            | MongoDB sharding by user ID.          |

---

## **5. Summary Checklist for Capacity Issues**
| **Action**                          | **Tool/Command**                          | **Owner**               |
|-------------------------------------|-------------------------------------------|-------------------------|
| Check CPU/Memory usage               | `top`, ` Prometheus queries               | SRE/DevOps              |
| Review auto-scaling policies         | `kubectl get hpa`, CloudWatch ASG         | DevOps/Platform Team    |
| Load test with realistic data       | k6, Gatling                              | QA/Engineering          |
| Optimize slow queries                | `EXPLAIN ANALYZE`, Database Profiler     | DBAs                   |
| Implement rate limiting              | Redis, API Gateway                        | Backend Engineers       |
| Monitor cold starts                  | Cloud Provider Metrics (Lambda, GKE)      | DevOps                  |
| Chaos test failure scenarios         | Gremlin, Chaos Mesh                       | Reliability Engineer    |

---

## **Final Notes**
- **Capacity planning is iterative.** Revisit thresholds every 3–6 months.
- **Automate scaling decisions** where possible (e.g., K8s HPA with custom metrics).
- **Document runbooks** for common capacity incidents (e.g., "How to handle a 3x traffic spike").

By following this guide, you can systematically diagnose and resolve capacity-related issues while preventing future bottlenecks.