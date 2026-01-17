# **Debugging Failover Migration: A Troubleshooting Guide**

## **1. Introduction**
Failover migration involves moving a service between environments (e.g., from Development → Staging → Production) while ensuring minimal downtime and data consistency. Common issues arise due to misconfiguration, network delays, or state mismatches. This guide covers symptoms, root causes, fixes, debugging tools, and prevention strategies.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **Unreachable Endpoints**            | Services fail to respond after migration (e.g., 503 errors, timeouts).          |
| **Data Inconsistency**               | Database records differ between source and target after cutover.                 |
| **Slow Performance**                 | Latency spikes in new environment post-migration.                              |
| **Connection Resets**                | Network-level failures (e.g., TCP resets, DNS resolution issues).               |
| **State Mismatch**                   | Process state lost (e.g., in-memory caches, queues) during migration.           |
| **Log Errors**                       | High-volume logs indicating connection drops, deadlocks, or schema mismatches.   |
| **Rollback Failures**                | Failed attempts to revert to the previous environment.                           |

---

## **3. Common Issues & Fixes**
### **A. Unreachable Endpoints**
**Cause:** Misconfigured DNS, load balancers, or firewall rules blocking traffic.
**Fix:**
- **Verify DNS Records:**
  ```sh
  dig failover-service.example.com  # Check propagation
  nslookup failover-service.example.com
  ```
- **Check Load Balancer Health:**
  ```sh
  curl -v http://<load-balancer-ip>  # Test endpoint connectivity
  ```
- **Firewall/Network Policies:**
  Ensure outbound traffic is allowed on required ports (e.g., 80, 443, custom TCP/UDP).
  ```yaml
  # Example: Kubernetes NetworkPolicy allowing HTTP traffic
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-http
  spec:
    podSelector: {}
    ingress:
    - ports:
      - protocol: TCP
        port: 80
  ```

---

### **B. Data Inconsistency**
**Cause:** Race conditions during cutover, uncommitted transactions, or schema drift.
**Fix:**
- **Use Transactions for Atomic Cutover:**
  ```sql
  -- Example: PostgreSQL atomic migration
  BEGIN;
  INSERT INTO orders (id, amount) VALUES (1, 100);
  -- Verify source & target match before commit.
  COMMIT;
  ```
- **Validate Data Post-Migration:**
  ```python
  # Python script to compare records
  def compare_records(source_conn, target_conn):
      source_data = source_conn.execute("SELECT * FROM orders")
      target_data = target_conn.execute("SELECT * FROM orders")
      assert list(source_data) == list(target_data)
  ```

---

### **C. Slow Performance**
**Cause:** Underpowered target environment, cold cache, or high latency.
**Fix:**
- **Benchmark Target Environment:**
  ```sh
  ab -n 1000 -c 10 http://failover-service.example.com/api  # Apache Benchmark
  ```
- **Warm Caches:**
  ```sh
  # Example: Pre-load Redis caches before failover
  redis-cli --scan --pattern "*"  # Cache keys from source
  ```

---

### **D. State Mismatch**
**Cause:** In-memory state lost during migration (e.g., Redis, session stores).
**Fix:**
- **Persist State Before Cutover:**
  ```javascript
  // Node.js example: Save Redis to disk
  const redis = require("redis");
  const client = redis.createClient();
  client.save((err) => {
      if (err) console.error("Save failed:", err);
  });
  ```
- **Reinitialize State on Target:**
  ```bash
  # Example: Rebuild session store on new host
  ./rebuild-sessions.sh  # Custom script to repopulate
  ```

---

### **E. Rollback Failures**
**Cause:** Orphaned resources, stuck transactions, or incomplete reverse-migration scripts.
**Fix:**
- **Test Rollback Scripts in Staging First:**
  ```bash
  # Example: Dry-run reverse migration
  ./rollback.sh --dry-run
  ```
- **Clean Up Orphaned Resources:**
  ```sql
  -- Find dangling database connections
  SELECT pid, query, now() - query_start AS duration
  FROM pg_stat_activity
  WHERE state = 'idle in transaction';
  ```

---

## **4. Debugging Tools & Techniques**
### **A. Observability Stack**
| **Tool**          | **Use Case**                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Prometheus + Grafana** | Monitor latency, error rates, and throughput across environments.          |
| **Distributed Tracing** | Identify bottlenecks (e.g., Jaeger, OpenTelemetry).                       |
| **Logging Aggregations** | Correlate logs across services (e.g., ELK Stack).                          |
| **Database Replication Checks** | Verify lag in async replication (e.g., `SHOW REPLICA STATUS;` in MySQL).      |

**Example: Tracing a Request End-to-End**
```bash
# Jaeger query for slow API calls
curl -X POST http://jaeger-query:16686/search?service=failover-service
```

---

### **B. Network Debugging**
- **Packet Capture:**
  ```bash
  tcpdump -i any port 80 -w failover_traffic.pcap  # Capture HTTP traffic
  ```
- **Port Scanning:**
  ```bash
  nmap -p 80,443 failover-service.example.com
  ```

---

### **C. Performance Profiling**
- **CPU/Memory:**
  ```bash
  # Check resource usage on target host
  top -c  # Linux
  ```
- **Database Queries:**
  ```sql
  -- Slow query log (PostgreSQL)
  SELECT query, calls, total_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;
  ```

---

## **5. Prevention Strategies**
### **A. Pre-Migration Checklist**
1. **Test Cutover in Staging**
   - Simulate production load with tools like Locust or Gatling.
2. **Validate Replication Lag**
   - For databases, ensure lag <1s during cutover:
     ```sql
     SELECT Seconds_Behind_Master FROM performance_schema.replication_connection_status;
     ```
3. **Backup Critical Data**
   - Use consistent snapshots (e.g., logical backups, `pg_dump` for PostgreSQL).
4. **Document Rollback Plan**
   - Include steps for undoing changes (e.g., revert database migrations, redirect traffic).

### **B. Automated Safeguards**
- **Canary Deployments:**
  Route a small % of traffic to the new environment first.
  ```bash
  # Example: Use Nginx canary routing
  upstream failover {
      least_conn;
      server staging:80 weight=1;  # 10% traffic
      server production:80 weight=9; # 90% traffic
  }
  ```
- **Feature Flags:**
  Disable critical features until migration is confirmed.
  ```python
  if not feature_flag.get("failover_ok"):
      raise Exception("Migration incomplete")
  ```

### **C. Monitoring Alerts**
- **Set Up SLOs (Service Level Objectives)**
  - Alert on:
    - >3s API latency.
    - >5% error rate.
    - Replication lag >5s.
- **Example Alert (Prometheus):**
  ```yaml
  - alert: HighLatency
    expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
    for: 5m
    labels:
      severity: critical
  ```

---

## **6. Conclusion**
Failover migration failures often stem from **network misconfigurations, data races, or untested rollback plans**. Focus on:
1. **Validation:** Compare data pre/post-migration.
2. **Observability:** Use tracing/logs to spot anomalies early.
3. **Automation:** Test rollbacks and canary deployments in staging.

**Quick Fix Cheat Sheet:**
| **Issue**               | **Immediate Fix**                          |
|--------------------------|--------------------------------------------|
| Endpoint Unreachable     | Check DNS, LB health, firewalls.           |
| Data Mismatch            | Re-run atomic transactions.                |
| Slow Performance         | Warm caches, scale up target environment. |
| State Loss               | Persist state pre-cutover.                  |
| Rollback Fails           | Dry-run rollback scripts in staging.       |

By following this guide, you can reduce failover downtime and ensure smoother migrations. Always prioritize **testing** in staging and **monitoring** post-migration.