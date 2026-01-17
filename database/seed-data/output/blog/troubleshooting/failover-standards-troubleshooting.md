# **Debugging Failover Standards: A Troubleshooting Guide**

## **1. Introduction**
The **Failover Standards** pattern ensures high availability by dynamically switching to a backup service when the primary fails. This guide helps diagnose and resolve common issues in distributed systems, microservices, or database failover scenarios.

---

## **2. Symptom Checklist**
Before diving into debugging, check for these symptoms to narrow down potential failures:

### **Primary Service Failures**
- [ ] Primary node returns **5xx errors** or **timeouts** (e.g., 503 Service Unavailable).
- [ ] API responses are **inconsistent** (successful requests intermittently fail).
- [ ] Requests **hang indefinitely** without a response.
- [ ] **Health check endpoints** (e.g., `/health`) fail intermittently.

### **Failover-Related Issues**
- [ ] **Backup service is unreachable** (no response from `backup-service:8080`).
- [ ] Failover **does not trigger automatically** (traffic remains on the failed primary).
- [ ] **Race conditions** occur during failover (inconsistent data states).
- [ ] **Circular failovers** (system keeps switching between primary and backup).

### **Data Consistency Issues**
- [ ] **Stale data** is returned after failover (database replication lag).
- [ ] **Inconsistent transactions** (e.g., partial writes due to failed retries).
- [ ] **Duplicate operations** (e.g., double bookings in financial systems).

### **Monitoring & Logging**
- [ ] **No logs** in failover-related components (e.g., load balancer, circuit breakers).
- [ ] **Metrics indicate high latency** between primary and backup.
- [ ] **Prometheus/Grafana alerts** show unexpected spikes in failover attempts.

---

## **3. Common Issues & Fixes**

### **3.1. Primary Service Unavailable (No Failover Triggered)**
**Symptom:**
- Primary node crashes, but traffic continues to route there instead of failing over.

**Root Causes:**
- **Load Balancer Misconfiguration** (not checking health endpoints).
- **Circuit Breaker Not Tripping** (e.g., Hystrix, Resilience4j not detecting failures).
- **DNS Propagation Delay** (if using DNS-based failover).

**Fixes:**

#### **A. Verify Load Balancer Health Checks**
If using **NGINX**, ensure `health_check` is configured:
```nginx
upstream primary {
    server primary:8080 max_fails=3 fail_timeout=10s;
    server backup:8080 backup; # Only used if primary fails
    health_check path=/health status=200;
}
```
- **Test:** `curl http://primary:8080/health` should return `200`.

#### **B. Enable Circuit Breaker in Microservices**
If using **Resilience4j**, ensure the circuit trips on failures:
```java
@CircuitBreaker(name = "serviceA", fallbackMethod = "fallback")
public String callServiceA() {
    return restTemplate.getForObject("http://primary-service", String.class);
}

private String fallback(Exception e) {
    return restTemplate.getForObject("http://backup-service", String.class);
}
```
- **Test:** Force a timeout (`ab -n 1000 -c 10 http://primary:8080`)—should trigger failover.

#### **C. Use DNS-Based Failover with Short TTL**
If using **Cloudflare/DNS failover**:
```plaintext
primary-service.example.com. IN A 10.0.0.1 (TTL=30)
backup-service.example.com. IN A 10.0.0.2 (TTL=30)
```
- **Verify:** `dig primary-service.example.com` should return `10.0.0.2` if primary fails.

---

### **3.2. Failover Triggered but Backup Still Unavailable**
**Symptom:**
- Failover happens, but the backup service returns **5xx errors**.

**Root Causes:**
- **Backup service is overloaded** (high CPU/memory).
- **Database replication lag** (read replicas not in sync).
- **Network partition** (backup service isolated from primary).

**Fixes:**

#### **A. Check Backup Service Health**
```bash
# Check CPU/Memory usage
docker stats backup-service
# OR
kubectl top pod -n failover-namespace
```
- **Fix:** Scale backup service (`kubectl scale deployment backup-service --replicas=3`).

#### **B. Verify Database Replication Lag**
If using **PostgreSQL with Streaming Replication**:
```sql
SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
```
- **Fix:** Increase WAL buffers or reduce `max_replication_slots`.

#### **C. Test Network Connectivity**
```bash
# From backup service, ping primary DB
ping primary-db:5432
# OR
telnet primary-db 5432
```
- **Fix:** If blocked, adjust **security groups/firewall rules**.

---

### **3.3. Race Conditions During Failover**
**Symptom:**
- Inconsistent data after failover (e.g., partial transactions).

**Root Causes:**
- **No transactional consistency** (e.g., eventual consistency).
- **Long-running operations** not rolled back on failover.

**Fixes:**

#### **A. Use Distributed Transactions (Saga Pattern)**
Example with **Axoniq Event Sourcing**:
```java
@Aggregate
public class OrderAggregate {
    @AggregateMember
    private OrderStatus status;

    @CommandHandler
    public void handle(CreateOrder command) {
        // Start transaction
        apply(new OrderCreated(command.getId()));
        eventStore.append(command.getId(), new OrderCreated(command.getId()));
    }

    @EventSourcingHandler
    public void on(OrderCreated event) {
        status = OrderStatus.CREATED;
    }
}
```
- **Ensure:** All services publish events for **exactly-once processing**.

#### **B. Retry with Exponential Backoff**
```java
RetryTemplate retryTemplate = RetryTemplate.builder()
    .maxAttempts(3)
    .backoff(Duration.ofMillis(100))
    .build();

retryTemplate.execute(context -> {
    if (!primaryService.isAvailable()) {
        backupService.execute();
    }
});
```

---

### **3.4. Circular Failovers (Flapping)**
**Symptom:**
- System keeps switching between primary and backup due to **false positives**.

**Root Causes:**
- **Misconfigured health checks** (e.g., flaky `/health` endpoint).
- **Overloaded backup service** causing **auto-healing** failures.

**Fixes:**

#### **A. Improve Health Check Stability**
```java
@GetMapping("/health")
public ResponseEntity<String> healthCheck() {
    if (database.isAlive() && cache.isAvailable()) {
        return ResponseEntity.ok("UP");
    }
    return ResponseEntity.status(503).body("DOWN");
}
```
- **Test:** Use **locust** to simulate load without crashing the service.

#### **B. Add Manual Intervention for Recovery**
```yaml
# Kubernetes Liveness Probe (adjust threshold)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  failureThreshold: 5  # Wait 5 failures before declaring dead
```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Prometheus + Grafana** | Monitor failover metrics (latency, error rates).                          | `prometheus query "failover_attempts"`      |
| **Jaeger/Tracing**     | Track request flow during failover.                                        | `curl localhost:16686/search?service=app`   |
| **NetData**            | Real-time network/traffic analysis.                                         | `netdata-cli stats http_requests`           |
| ** docker exec -it**   | Debug container logs.                                                       | `docker logs backup-service`                |
| ** k6/Locust**         | Simulate failover conditions.                                               | `k6 run load_test.js`                       |
| ** Wireshark**         | Inspect TCP/UDP failover communication.                                     | `tcpdump -i eth0 port 8080`                 |
| ** kubectl describe**  | Check pod events during failover.                                          | `kubectl describe pod backup-service-1`    |

---

## **5. Prevention Strategies**

### **5.1. Design for Failover Resilience**
- **Use Multi-AZ Deployments** (AWS, GCP, Azure).
- **Implement Quorum-Based Failover** (e.g., **Raft consensus**).
- **Test Failover in Production** (Disaster Recovery Drills).

### **5.2. Automate Health Checks**
- **Kubernetes Liveness Readiness Probes** (fail fast).
- **Custom Health Endpoints** (e.g., `/healthz`).

### **5.3. Minimize Downtime**
- **Blue-Green Deployments** (zero-downtime failover).
- **Canary Releases** (gradual traffic shift to backup).

### **5.4. Log & Monitor Failover Events**
- **Centralized Logging** (ELK Stack, Loki).
- **Alert on Failover Events** (e.g., Slack/email alerts).

### **5.5. Batch Failover Testing**
```bash
# Chaos Engineering with Gremlin
gremlin inject -n 1000 -t 5m --rate 100 --host primary-service
```
- **Verify:** Backup service handles **high failover volume**.

---

## **6. Conclusion**
Failover issues can be complex, but **structured debugging** (health checks → network → data consistency) speeds up resolution. Always:
1. **Check logs first** (`docker logs`, `kubectl logs`).
2. **Simulate failures** (kill primary, test backup).
3. **Monitor metrics** (Prometheus/Grafana).

By following this guide, you can **minimize downtime** and **prevent future failover failures**. 🚀