# **Debugging Availability Troubleshooting: A Practical Guide**

## **Introduction**
Availability issues in distributed systems can lead to degraded performance, timeouts, or complete system outages. This guide focuses on **quickly diagnosing and resolving** availability problems, ensuring minimal downtime.

---
## **Symptom Checklist**
Before diving into fixes, confirm the issue matches these symptoms:

✅ **High Latency / Timeouts** – Requests slow down or fail after a delay.
✅ **Failed Requests** – HTTP 5xx, connection refused, or connection timeouts.
✅ **Error Spikes** – Sudden increase in errors in logs/monitoring tools.
✅ **Resource Exhaustion** – High CPU, memory, or disk usage.
✅ **Service Unavailability** – Entire service or microservice becomes unresponsive.
✅ **Network Issues** – Inter-service communication failures (DNS, network partitions).
✅ **Dependency Failures** – External APIs, databases, or caches failing.

---
## **Common Issues & Fixes**
### **1. High Latency / Timeouts**
#### **Root Cause:**
- Database queries taking too long.
- Slow third-party API responses.
- Network congestion between services.
- Insufficient instance scaling.

#### **Quick Fixes:**
- **Database Optimization:**
  ```sql
  -- Check slow queries (PostgreSQL example)
  SELECT query, total_time, calls
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;
  ```
  - Add indexes to frequently queried columns.
  - Consider connection pooling (e.g., **PgBouncer** for PostgreSQL).

- **API Response Timeouts:**
  ```yaml
  # Example in Node.js (Express + Axios timeout)
  const axios = require('axios');
  axios.get('https://slow-api.example.com/data', {
    timeout: 5000, // 5s timeout
  });
  ```
  - Implement **circuit breakers** (e.g., **Resilience4j** for Java, **Hystrix** alternative).

- **Network Optimization:**
  - Use **load balancers** (NGINX, AWS ALB) to distribute traffic.
  - Check **MTU** issues (fragmentation) if packets are dropping.

- **Scaling:**
  ```bash
  # Example Kubernetes horizontal pod autoscaler
  kubectl autoscale deployment my-service --cpu-percent=80 --min=3 --max=10
  ```

---

### **2. Failed Requests (5xx Errors)**
#### **Root Cause:**
- **CrashLoopBackOff** (Kubernetes) → Pod crashes repeatedly.
- **Out-of-memory (OOM) kills** → Container restarts but fails again.
- **Permission issues** → Service lacks access to databases/storage.

#### **Quick Fixes:**
- **Check CrashLoopBackOff:**
  ```bash
  kubectl describe pod <pod-name> | grep CrashLoopBackOff
  ```
  - Fix app errors (check logs: `kubectl logs <pod-name>`).
  - Increase memory limits in deployment:
    ```yaml
    resources:
      limits:
        memory: "512Mi"
    ```

- **OOM Issues:**
  - Reduce memory usage in code (e.g., avoid loading large datasets).
  - Adjust JVM heap size (for Java):
    ```bash
    -Xms512m -Xmx1024m
    ```
  - Use **stateless services** where possible to avoid memory leaks.

- **Permission Errors:**
  ```bash
  # Check AWS IAM roles (if using ECS/EKS)
  aws iam get-role --role-name my-service-role
  ```
  - Grant `AmazonDynamoDBReadWriteAccess` or equivalent permissions.

---

### **3. Error Spikes in Logs**
#### **Root Cause:**
- **Burst traffic** → DB overload, API rate limits.
- **Bug in new release** → Regression in error handling.
- **Third-party outages** → External API failures.

#### **Quick Fixes:**
- **Rate Limiting (APIs):**
  ```python
  # Flask rate limiting example
  from flask_limiter import Limiter
  limiter = Limiter(app, key_func=get_remote_address)
  @app.route('/api/data')
  @limiter.limit("100 per minute")
  def get_data():
      return "Data"
  ```

- **Monitor & Alert Early:**
  - Use **Prometheus + Grafana** to track error rates:
    ```promql
    rate(http_requests_total{status=~"5.."}[5m]) > 0.1  # Alert if >10% errors
    ```

- **Rollback Deployments:**
  ```bash
  # If using Docker/Kubernetes
  kubectl rollout undo deployment my-service
  ```

---

### **4. Resource Exhaustion (CPU/Memory/Disk)**
#### **Root Cause:**
- **Unbounded loops** → CPU spikes.
- **Large logs** → Disk fills up.
- **Database table bloat** → Slow queries + high I/O.

#### **Quick Fixes:**
- **CPU Throttling:**
  - Use **CPU affinity** (Kubernetes):
    ```yaml
    affinity:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
          - matchExpressions:
            - key: "kubernetes.io/arch"
              operator: In
              values: ["amd64"]
    ```
  - Profile CPU-heavy code (e.g., **pprof** for Go):
    ```bash
    go tool pprof http://localhost:6060/debug/pprof/profile
    ```

- **Disk Space Issues:**
  - Check for log bloating (`/var/log`):
    ```bash
    du -sh /var/log/* | sort -h
    ```
  - Rotate logs with **Logrotate**:
    ```conf
    /var/log/myapp/*.log {
      daily
      missingok
      rotate 7
      compress
      delaycompress
      notifempty
      create 640 myuser mygroup
    }
    ```

- **Database Cleanup:**
  ```sql
  -- Example: Truncate old logs (PostgreSQL)
  TRUNCATE TABLE logs WHERE created_at < NOW() - INTERVAL '30 days';
  ```

---

### **5. Network Issues (DNS, Partitioning, Timeouts)**
#### **Root Cause:**
- **DNS failures** → Services can’t resolve hostnames.
- **Network partitions** → Services lose connectivity.
- **Firewall/ACLs blocking traffic.**

#### **Quick Fixes:**
- **Test DNS Resolution:**
  ```bash
  dig example.com  # Check if DNS resolves
  nslookup my-db-service
  ```

- **Network Partition Debugging:**
  - Use `ping` and `traceroute`:
    ```bash
    ping my-db-service
    traceroute my-db-service
    ```
  - Check **kube-dns** (if on Kubernetes):
    ```bash
    kubectl get pods -n kube-system | grep dns
    ```

- **Firewall Rules:**
  ```bash
  # Check AWS Security Groups (if using EC2)
  aws ec2 describe-security-groups --group-ids sg-123456
  ```
  - Ensure inbound/outbound rules allow necessary ports (e.g., **443, 80, 5432**).

---

### **6. Dependency Failures**
#### **Root Cause:**
- **Database down** → App fails.
- **Queue service deadlocked** → Messages pile up.
- **Cache hit ratio too low** → Performance degrades.

#### **Quick Fixes:**
- **Database Failover:**
  - Use **read replicas** (PostgreSQL example):
    ```sql
    SELECT * FROM pg_readall_distance(); -- Check replication lag
    ```
  - Failover if primary node fails:
    ```bash
    pg_ctl promote /path/to/standby_data  # PostgreSQL
    ```

- **Queue Deadlocks (Kafka/RabbitMQ):**
  ```bash
  # Check RabbitMQ queue length
  rabbitmqctl list_queues name messages_ready messages_unacknowledged
  ```
  - **Consume messages manually** (e.g., `rabbitmqadmin`) to unblock.

- **Cache Warmup:**
  ```python
  # Example: Pre-load cache on startup (Python + Redis)
  import redis
  r = redis.Redis()
  for key in cached_keys:
      if not r.exists(key):
          r.set(key, fetch_from_db(key))
  ```

---

## **Debugging Tools & Techniques**
| **Tool**               | **Purpose**                          | **Example Usage**                     |
|------------------------|--------------------------------------|---------------------------------------|
| **Prometheus + Grafana** | Metrics & alerting                   | `http_request_duration_seconds`        |
| **Kubernetes `kubectl`** | Pod/Service debugging               | `kubectl logs`, `kubectl describe pod` |
| **Netdata**            | Real-time system monitoring          | `netdata logs`                        |
| **Jaeger/Tracing**     | Distributed tracing                  | `jaeger query --service=my-service`   |
| **`strace`/`tcpdump`** | Low-level network debugging           | `strace -p <PID>`                     |
| **`perf`**             | CPU profiling                        | `perf top`                            |
| **`ttl; rm -rf ~`**    | Emergency cleanup                    | (Never do this, but useful for panic!) |

### **Debugging Workflow:**
1. **Check Logs** (`kubectl logs`, `journalctl`, Sentry).
2. **Monitor Metrics** (Prometheus, Datadog).
3. **Isolate the Issue** (Is it a single pod, DB, or external API?).
4. **Apply Fixes** (Scale up, patch code, adjust configs).
5. **Verify** (Check metrics, roll back if needed).

---

## **Prevention Strategies**
### **1. Infrastructure Resilience**
- **Multi-AZ Deployments** (AWS RDS, Kubernetes clusters).
- **Auto-Scaling** (Kubernetes HPA, AWS Auto Scaling).
- **Circuit Breakers** (Resilience4j, Hystrix).

### **2. Observability**
- **Centralized Logging** (ELK Stack, Loki).
- **Distributed Tracing** (Jaeger, OpenTelemetry).
- **S Synthetic Monitoring** (Pingdom, New Relic).

### **3. Code-Level Safeguards**
- **Graceful Degradation** (Fallbacks for failed dependencies).
  ```python
  # Example: Fallback to cache if DB fails
  def get_data():
      data = cache.get("data")
      if data is None:
          try:
              data = db.query("SELECT * FROM table")
          except:
              return cache.get("data")  # Return stale data
      cache.set("data", data)
      return data
  ```
- **Idempotency** (Ensure retries don’t cause duplicate actions).
- **Rate Limiting** (Prevent API abuse).

### **4. Chaos Engineering**
- **Chaos Mesh (Kubernetes)** – Inject failures for testing.
  ```yaml
  # Example: Chaos Mesh pod kill
  apiVersion: chaos-mesh.org/v1alpha1
  kind: PodChaos
  metadata:
    name: pod-kill
  spec:
    action: pod-kill
    mode: one
    selector:
      namespaces:
        - default
      labelSelectors:
        app: my-service
  ```
- **Netflix Simian Army** (Chaos Monkey, Latency Monkey).

### **5. Disaster Recovery Plan**
- **Backup Strategy** (Regular DB snapshots, Immutable Backups).
- **RTO/RPO** (Recovery Time Objective, Recovery Point Objective).
  - Example: **RTO = 15 mins**, **RPO = 5 mins**.

---
## **Final Checklist Before Going Live**
✅ **Load Test** (Locust, JMeter) under expected traffic.
✅ **Chaos Testing** (Random failures in staging).
✅ **Rollback Plan** (Test rollback in production).
✅ **Alerting** (Slack/PagerDuty for critical failures).
✅ **Documentation** (Runbooks for common outages).

---
## **Conclusion**
Availability issues are often **symptom-driven**, meaning quick checks in the right order save time. Focus on:
1. **Logs & Metrics** (Where is it failing?).
2. **Dependencies** (Is it the DB, API, or network?).
3. **Resources** (Are pods crashing due to OOM?).
4. **Prevention** (Chaos testing, auto-scaling, observability).

By following this guide, you can **diagnose and resolve availability issues efficiently**, minimizing downtime. 🚀