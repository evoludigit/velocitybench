# **Debugging *Distributed Setup* Patterns: A Troubleshooting Guide**
*A focused guide for diagnosing and resolving issues in microservices, distributed messaging, and cluster-based architectures.*

---

## **1. Introduction**
The **Distributed Setup** pattern refers to systems where multiple components (services, databases, queues, or nodes) operate across machines, networks, or cloud regions. Common implementations include:
- **Microservices architectures**
- **Event-driven systems (Kafka, RabbitMQ, AWS SNS/SQS)**
- **Clustered databases (Cassandra, MongoDB Sharded)**
- **Load-balanced APIs (Nginx, HAProxy, Kubernetes Services)**

Because distributed systems rely on network communication, eventual consistency, and fault tolerance, they introduce complexity. This guide helps diagnose and resolve issues quickly.

---

## **2. Symptom Checklist**
Start by identifying **which layer** is failing:
- **Network/Connectivity Issues** (e.g., timeouts, 504 errors)
- **Service/Component Failures** (e.g., slow responses, crashes)
- **Data Inconsistency** (e.g., missing transactions, stale reads)
- **Resource Contention** (e.g., throttling, OOM kills)
- **Configuration Mismatches** (e.g., env vars, secrets, timeouts)

| **Symptom**               | **Possible Cause**                          | **Immediate Check**                          |
|---------------------------|--------------------------------------------|---------------------------------------------|
| API requests hang/time out | Network latency, load balancer misconfig    | `curl -v <endpoint>`                         |
| Duplicated/lost messages  | Broken consumers, retries, or dead-letter   | Check queue lag (`kafka-consumer-groups`)    |
| Inconsistent DB reads     | Eventual consistency, stale cache          | `SELECT * FROM table FORCE INDEX`            |
| High CPU/memory in pods   | Memory leaks, unoptimized queries           | `kubectl top pods`, `jstack <pid>`           |
| Service-to-service 502s   | Circuit breakers, downstreams overloaded   | Check service mesh logs (Istio, Linkerd)     |
| Timeouts in distributed transactions | Long-running RPCs, no retries              | Adjust timeouts (`openTelemetry`, `Prometheus`) |

---
---

## **3. Common Issues & Fixes**
### **A. Network/Connectivity Problems**
#### **Issue: Timeout Errors (504, 408)**
- **Symptom**: Client waits >30s before failing.
- **Root Cause**:
  - Downstream service is unresponsive.
  - Network partition (e.g., AWS AZ failover).
  - Load balancer misconfigured (e.g., unhealthy checks too slow).
- **Fix**:
  ```java
  // Adjust timeout in Spring Boot
  @Bean
  public RestTemplate restTemplate() {
      HttpClient httpClient = HttpClients.custom()
          .setConnectionTimeout(Duration.ofMillis(5000))
          .setSocketTimeout(Duration.ofMillis(8000))
          .build();
      return new RestTemplate(httpClient);
  }
  ```
  - **Auto-scaling**: Ensure sufficient pods (`kubectl get hpa`).
  - **Circuit Breaker**: Use Resilience4j or Hystrix to fail fast.
    ```java
    @CircuitBreaker(name = "order-service", fallbackMethod = "fallback")
    public String getOrder(String orderId) { ... }
    ```

#### **Issue: Deadlocks in Distributed Transactions**
- **Symptom**: Long-running transactions, `TimeoutException`.
- **Root Cause**:
  - Two-phase commit (2PC) is blocking.
  - No retries in saga pattern.
- **Fix**:
  - Use **compensating transactions** (saga pattern):
    ```python
    # Example: Order Service (Python + RQ)
    @celery.task(bind=True)
    def place_order(self, order_data):
        try:
            pay_order(order_data)
            ship_order(order_data)
        except Exception as e:
            cancel_payment(order_data)  # Compensating action
            raise
    ```
  - **Timeout handling**:
    ```java
    // Spring Retry with backoff
    @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 1000))
    public void retryOnTimeout() { ... }
    ```

---

### **B. Data Inconsistency**
#### **Issue: Missing/Duplicate DB Writes**
- **Symptom**: `SELECT` returns fewer rows than expected.
- **Root Cause**:
  - Async writes not acknowledged.
  - Client retries after failure.
- **Fix**:
  - **Idempotent writes** (use `UUID` or `transactionId`):
    ```sql
    -- PostgreSQL: Check if record exists first
    INSERT INTO orders (id, amount)
    VALUES (uuid_generate_v4(), 100)
    ON CONFLICT (id) DO NOTHING;
    ```
  - **Event sourcing**: Log all changes to a log (Kafka).
  - **Database retries**:
    ```python
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def safe_write(data):
        db.execute("INSERT INTO ...", data)
    ```

#### **Issue: Stale Caches**
- **Symptom**: `GET /user` returns old data.
- **Root Cause**:
  - Cache invalidation lag.
  - No TTL on Redis/Memcached.
- **Fix**:
  - **Cache-aside pattern** with TTL:
    ```java
    // Spring Cache with 5-min TTL
    @Cacheable(value = "users", key = "#id", unless = "#result == null")
    public User getUser(Long id) { ... }
    ```
  - **Write-through cache**:
    ```python
    # Python + Redis
    def update_user(user):
        r = redis.Redis()
        r.set(f"user:{user.id}", user.to_json(), ex=300)  # 5 min TTL
        db.update(user)
    ```

---

### **C. Resource Contention**
#### **Issue: High CPU in Pods**
- **Symptom**: Pods hit `OOMKilled` or CPU throttling.
- **Root Cause**:
  - Memory leaks (e.g., unclosed JDBC connections).
  - Full GC pauses.
- **Fix**:
  - **Profile memory**:
    ```bash
    kubectl exec <pod> -it -- java -XX:+PrintGCDetails -XX:+PrintGCTimeStamps -XX:+HeapDumpOnOutOfMemoryError -jar app.jar
    ```
  - **Optimize queries**:
    ```sql
    -- Add index if missing
    CREATE INDEX idx_user_email ON users(email);
    ```
  - **Horizontal scaling**: Increase replicas (`kubectl scale deployment nginx --replicas=5`).

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                              | **Example Command**                     |
|------------------------|------------------------------------------|------------------------------------------|
| **Network Inspection** | Check latency, drops                      | `tcpdump -i eth0 host example.com`       |
| **Distributed Tracing** | Trace RPC calls (Latency, errors)        | `curl http://localhost:16686` (Jaeger)   |
| **Metrics**            | Monitor service health (CPU, DB queries) | `prometheus --web.listen-address=0.0.0.0:9090` |
| **Logging**            | Correlate logs across services            | `EFK Stack (Elasticsearch, Fluentd, Kibana)` |
| **Database Tools**     | Analyze slow queries                     | `EXPLAIN ANALYZE SELECT * FROM orders;` |
| **Load Testing**       | Simulate traffic                         | `locust -f load_test.py`                |
| **Chaos Engineering**  | Test failure resilience                  | `kubectl delete pod <pod-name>` (Gremlin)|

---
### **Key Debugging Workflow**
1. **Isolate**: Check if the issue is in one service or all.
   ```bash
   # Check service logs (Kubernetes)
   kubectl logs <pod> --tail=100 -n <namespace>
   ```
2. **Reproduce**: Simulate the condition (e.g., kill a pod).
3. **Trace**: Use Jaeger to follow a request across services.
4. **Measure**: Compare metrics (latency, errors) before/after fix.
   ```bash
   # PromQL query for 5xx errors
   sum(rate(http_requests_total{status=~"5.."}[1m])) by (service)
   ```

---

## **5. Prevention Strategies**
### **A. Observability First**
- **Centralized logging**:
  - Use **Loki** (Grafana) or **ELK Stack** for log aggregation.
- **Metrics**:
  - Expose Prometheus endpoints (`/actuator/prometheus` in Spring Boot).
  - Alert on:
    - `error_rate > 0.1%`
    - `latency_p99 > 500ms`
- **Tracing**:
  - Instrument all services with **OpenTelemetry**.

### **B. Resilience Patterns**
| **Pattern**            | **Implementation**                          | **Example**                              |
|------------------------|--------------------------------------------|------------------------------------------|
| **Circuit Breaker**    | Fail fast if downstream fails             | Resilience4j, Hystrix                   |
| **Bulkhead**           | Limit concurrent requests                  | Thread pools, Kubernetes HPA            |
| **Retry with Backoff** | Exponential delay between retries         | Spring Retry, Tenacity (Python)         |
| **Timeouts**           | Hard limit on operation duration          | gRPC timeouts, Netty                      |
| **Dead Letter Queue**  | Isolate failed messages                    | Kafka `dlq-topic`, RabbitMQ `x-death`    |

### **C. Configuration Best Practices**
- **Infrastructure as Code**:
  - Use **Terraform** or **Kubernetes manifests** for consistency.
- **Feature Flags**:
  - Roll out changes gradually (e.g., **LaunchDarkly**).
- **Chaos Testing**:
  - **Gremlin** or **Chaos Mesh** to test failure modes.

### **D. Testing Distributed Systems**
- **Contract Testing**:
  - Use **Pact** to verify service interactions.
- **Chaos Testing**:
  - Randomly kill pods (`kubectl delete pod <pod>`).
- **Performance Testing**:
  - **Locust** or **k6** to simulate load.

---

## **6. Quick-Reference Cheat Sheet**
| **Problem**               | **Check First**                          | **Fix**                                  |
|---------------------------|------------------------------------------|------------------------------------------|
| **Timeouts**              | Load balancer health checks              | Increase timeout, add circuit breaker    |
| **Data Duplication**      | Async retries, no idempotency             | Use UUIDs, saga pattern                  |
| **Slow Queries**          | Missing indexes, N+1 selects              | Add indexes, use DTOs                     |
| **High Latency**          | Network hops, unoptimized RPCs           | Use gRPC, reduce payload size            |
| **Inconsistent Caches**   | Stale TTL, missing cache invalidation    | Use write-through cache                  |

---

## **7. When to Escalate**
- **Unknown dependencies**: If the issue crosses teams (e.g., "DB team owns this table").
- **Unrecoverable state**: Data corruption (e.g., lost Kafka logs).
- **Security breaches**: Unauthorized access to secrets.

**Escalation Path**:
1. **Team Lead** → Review logs/metrics.
2. **Architect** → Check design decisions (e.g., "Why no retries?").
3. **Vendor Support** → For managed services (e.g., AWS RDS).

---
## **Final Notes**
Distributed systems are **unpredictable**—focus on **observability** and **resilience**. Start with **logs + metrics**, then **traces**, and **reproduce** the issue in staging.

**Key Takeaways**:
✅ **Timeouts?** → Adjust timeouts + circuit breakers.
✅ **Data issues?** → Saga pattern + idempotency.
✅ **Performance?** → Profile + optimize queries.
✅ **Prevent?** → Chaos testing + observability.

---
**Next Steps**:
- Run a **chaos experiment** (kill a pod).
- Set up **Prometheus alerts** for latency errors.
- Review **recent deployments** for anti-patterns.