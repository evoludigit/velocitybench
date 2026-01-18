# **Debugging Availability: A Troubleshooting Guide**

## **Introduction**
Availability issues—where services fail to respond or degrade under load—can cripple user experience and business operations. This guide provides a structured approach to diagnosing, fixing, and preventing availability problems in distributed systems.

---

## **Symptom Checklist**
Before diving into fixes, confirm the issue using these checks:

| Symptom                          | How to Verify                                                                 |
|----------------------------------|-------------------------------------------------------------------------------|
| **High Latency**                 | Check response times (e.g., `ping`, `traceroute`, APM tools like Datadog, New Relic) |
| **Service Unavailability**       | Test endpoints (`curl`, `Postman`, health checks)                              |
| **Resource Exhaustion**          | Monitor CPU, memory, disk I/O, and network (Prometheus, Grafana, `top`, `htop`) |
| **Connection Timeouts**          | Validate TCP/UDP connections (`netstat -tun`, `telnet`)                        |
| **Database Locks/Blocks**        | Query deadlocks (`pg_locks` in PostgreSQL, `SHOW PROCESSLIST` in MySQL)       |
| **Cascading Failures**           | Check dependencies (circular waits, unhandled exceptions)                     |
| **DNS Resolution Failures**      | Test DNS (`nslookup`, `dig`)                                                 |
| **Load Imbalance**               | Compare load across nodes (e.g., K8s metrics, custom health checks)          |
| **Network Partitioning**         | Verify split-brain scenarios (e.g., HAProxy, Consul)                         |

---

## **Common Issues & Fixes**

### **1. High Latency**
**Symptom:** Endpoints respond slowly (>1s for critical paths).
**Root Causes:**
- **CPU Throttling:** High contention in hot paths (e.g., DB queries, crypto ops).
- **Database Bottlenecks:** Slow joins, missing indexes, or connection pooling issues.
- **Network Overhead:** High TTL, TCP retries, or slow responses from upstream services.
- **Cold Starts:** Unprepared environments (e.g., serverless, Kubernetes scaling).

#### **Fixes with Code Examples**
**A. Optimize Database Queries**
```sql
-- Bad: Full table scan (slow)
SELECT * FROM users WHERE created_at > '2023-01-01';

-- Good: Indexed range query (fast)
CREATE INDEX idx_users_created_at ON users(created_at);
SELECT * FROM users WHERE created_at > '2023-01-01' LIMIT 1000;
```

**B. Enable Connection Pooling**
```java
// Spring Boot with HikariCP (default pool)
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
```

**C. Use Caching (Redis)**
```python
# Python + Redis (fast in-memory cache)
import redis
r = redis.Redis()
r.setex('user:123:cache', 300, json.dumps(user_data))  # Cache for 5 mins
```

**D. Reduce Network Hops**
- **Localize services:** Deploy database alongside app (e.g., Kubernetes `podAntiAffinity`).
- **Use gRPC instead of REST** for binary protocol efficiency.

---

### **2. Service Unavailability**
**Symptom:** Endpoints return `5xx` or `timeout` errors.
**Root Causes:**
- **Crash Loop:** Uncaught exceptions, OOM kills, or infinite loops.
- **Missing Dependencies:** Downstream services (e.g., Redis, external APIs).
- **Improper Circuit Breakers:** Overly aggressive retries/failovers.
- **Configuration Drift:** Misaligned env vars across deployments.

#### **Fixes with Code Examples**
**A. Implement Resilience Patterns**
```java
// Spring Retry + Circuit Breaker (Resilience4j)
@CircuitBreaker(name = "paymentService", fallbackMethod = "fallback")
public PaymentProcessed processPayment(PaymentRequest req) {
    return paymentClient.charge(req);
}

private PaymentProcessed fallback(PaymentRequest req, Exception e) {
    log.error("Fallback: " + e.getMessage());
    return new PaymentProcessed(false, "Payment service unavailable");
}
```

**B. Graceful Shutdown Handling**
```python
# Python (FastAPI + aiohttp)
@app.on_event("shutdown")
async def shutdown_event():
    # Close DB connections, clean up background tasks
    await db.close()
```

**C. Health Checks & Liveness Probes**
```yaml
# Kubernetes Deployment (liveness probe)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

### **3. Resource Exhaustion**
**Symptom:** OOM errors, disk full, or CPU saturation.
**Root Causes:**
- **Memory Leaks:** Unclosed connections, cached data not evicted.
- **Disk I/O Bottlenecks:** Logs, backups, or temporary files filling up.
- **Unbounded Retries:** Exponential backoff not implemented.

#### **Fixes with Code Examples**
**A. Detect & Fix Memory Leaks**
```go
// Go (garbage collector tuning)
func main() {
    runtime.SetBlockProfileRate(1)  // Monitor allocations
    runtime.SetMutexProfileFraction(1)
    // Use `go build -gcflags=-m` to check for unreachable code
}
```

**B. Set Resource Limits**
```yaml
# Kubernetes Pod (resource constraints)
resources:
  limits:
    cpu: "1"
    memory: "512Mi"
  requests:
    cpu: "500m"
    memory: "256Mi"
```

**C. Rate-Limit External Calls**
```python
# Python (slow down API calls)
import time
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=1)
def call_external_api():
    response = requests.get("https://external-api.com")
    return response.json()
```

---

### **4. Network Partitions**
**Symptom:** Split-brain scenarios, inconsistent reads.
**Root Causes:**
- **Improper Leader Election:** Consensus algorithms (e.g., Raft, Paxos) misconfigured.
- **DNS Misconfiguration:** Stale records causing traffic to dead nodes.
- **Firewall/NAT Issues:** Unidirectional traffic drops.

#### **Fixes with Code Examples**
**A. Configure Raft for HA**
```yaml
# etcd (Raft-based) config
cluster-state:
  initial-cluster: node1=http://10.0.0.1:2379,node2=http://10.0.0.2:2380
  initial-cluster-token: "raft-token"
```

**B. Use Failover DNS (e.g., Consul, Cloudflare)**
```bash
# Check DNS health
nslookup example.com
dig +short example.com | sort -u
```

**C. Implement Quorum Checks**
```java
// Java (Cassandra-like quorum validation)
public boolean isClusterHealthy() {
    Set<Node> aliveNodes = nodeHealthChecker.getAliveNodes();
    return aliveNodes.size() >= quorumSize;  // e.g., 3/5
}
```

---

## **Debugging Tools & Techniques**
| Tool Category       | Tools to Use                                                                 | How to Use                                                                 |
|----------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Infrastructure**   | Prometheus, Grafana, Kubernetes Events, AWS CloudWatch                      | Monitor metrics, alert on anomalies, check pod events.                     |
| **Tracing**          | Jaeger, OpenTelemetry, Zipkin                                              | Trace requests across microservices to find bottlenecks.                   |
| **Logging**          | ELK Stack (Elasticsearch, Logstash, Kibana), Loki, Datadog                  | Filter logs by error levels, correlate with timestamps.                   |
| **Network**          | Wireshark, tcpdump, `netstat`, `lsof`                                        | Inspect packets, check open connections, find leaks.                       |
| **Database**         | pgBadger (PostgreSQL), Percona PMM, MySQL Workbench                         | Analyze slow queries, deadlocks, replication lag.                         |
| **Chaos Engineering**| Gremlin, Chaos Mesh, Netflix Chaos Monkey                                    | Inject failures to test resilience (use cautiously!).                      |

**Debugging Workflow:**
1. **Reproduce** the issue (load test, simulate failure).
2. **Isolate** (check logs, trace, metrics).
3. **Hypothesize** (e.g., "Is it DB-related?").
4. **Validate** with targeted tools (e.g., `EXPLAIN ANALYZE` for slow SQL).
5. **Fix** and verify with canary deployments.

---

## **Prevention Strategies**
| Strategy                          | Implementation                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------|
| **Autoscaling**                   | Configure HPA (Horizontal Pod Autoscaler) based on CPU/memory metrics.        |
| **Multi-Region Deployment**       | Use active-active setups (e.g., Kubernetes federated clusters).              |
| **Chaos Testing**                 | Run periodic chaos experiments (e.g., kill pods randomly).                   |
| **Immutable Infrastructure**      | Avoid manual config changes; use GitOps (ArgoCD, Flux).                      |
| **Circuit Breakers & Retries**    | Enforce timeouts, retry policies, and fallback paths (Resilience4j, Hystrix).|
| **Database Read Replicas**        | Offload reads to replicas; use connection pooling.                          |
| **Feature Flags**                 | Roll out changes gradually (LaunchDarkly, Flagsmith).                         |
| **Postmortems**                   | Document root causes, fix remediation, and track recurrence in Jira/Confluence. |

**Example: Database High Availability**
```yaml
# Kubernetes StatefulSet (PostgreSQL HA)
replicas: 3
volumeClaimTemplates:
- metadata:
    name: data
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "ssd"
    resources:
      requests:
        storage: 100Gi
```

---

## **Conclusion**
Availability issues are rarely one-size-fits-all. Use this guide to:
1. **Systematically check symptoms** (latency, unavailability, resource exhaustion).
2. **Apply targeted fixes** (caching, retries, scaling).
3. **Prevent recurrence** with chaos testing, autoscaling, and immutable deployments.

**Final Checklist Before Production:**
- [ ] Load test under expected traffic.
- [ ] Validate circuit breakers and fallbacks.
- [ ] Monitor critical paths for 7+ days post-deployment.
- [ ] Document runbooks for common failures.

For further reading:
- [Google SRE Book (Site Reliability Engineering)](https://sites.google.com/a/google.com/srebook/)
- [Kubernetes Best Practices (CNCF)](https://kubernetes.io/docs/concepts/overview/working-with-objects/)