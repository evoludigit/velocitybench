# **Debugging Microservices Migration: A Troubleshooting Guide**

## **Introduction**
Microservices architecture offers scalability, independence, and agility but introduces complexity during migration. Issues like network failures, inter-service communication breakdowns, performance bottlenecks, and data consistency problems are common. This guide provides a **practical, step-by-step approach** to diagnosing and resolving microservices migration issues quickly.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically check for these symptoms:

### **A. Deployment & Service Discovery Issues**
✅ **Symptoms:**
- Services fail to register with the service registry (e.g., Consul, Eureka, Kubernetes DNS).
- Clients cannot resolve service names (e.g., `ServiceUnavailable` in gRPC, `DNS failure` in HTTP).
- Pods/VMs crash immediately after deployment.
- Health checks (`/health`) return `UNKNOWN` or `FAIL`.

### **B. Inter-Service Communication Failures**
✅ **Symptoms:**
- Timeouts when calling downstream services (e.g., `Connection refused`, `Read timeout`).
- Partial responses (e.g., missing fields, truncated JSON).
- Inconsistent behavior between identical service calls.
- Circuit breakers (e.g., Resilience4j, Hystrix) tripping frequently.

### **C. Performance & Latency Spikes**
✅ **Symptoms:**
- Sudden increase in request latency (e.g., 100ms → 5s).
- High CPU/memory usage in newly migrated services.
- Garbage collection (GC) pauses causing timeouts.
- Database query performance degradation.

### **D. Data Inconsistency & Transaction Issues**
✅ **Symptoms:**
- Duplicate transactions (e.g., `OrderService` & `PaymentService` don’t agree).
- Stale data reads (e.g., `OrderService` reflects changes after 30s delay).
- Deadlocks or long-running transactions.
- Distributed transaction failures (e.g., Saga pattern rollback errors).

### **E. Observability & Monitoring Gaps**
✅ **Symptoms:**
- Logs are fragmented or missing critical details.
- Metrics (e.g., request rates, error rates) are incomplete.
- Distributed tracing (e.g., Jaeger, Zipkin) fails to correlate requests.
- Alerts fire but no root cause is visible in dashboards.

---
## **2. Common Issues & Fixes (With Code Examples)**

### **A. Service Discovery Failures**
**Issue:** A service fails to register with the service mesh or registry.
**Root Cause:**
- Incorrect configuration in `application.yml`/`application.properties`.
- Network firewall blocking registry ports (e.g., 8500 for Consul, 8761 for Eureka).
- Misconfigured `spring.cloud.discovery.client.simple.instances` (Kubernetes).

**Fix:**
#### **For Consul/Eureka:**
```yaml
# application.yml (Consul example)
spring:
  cloud:
    consul:
      host: consul-service
      port: 8500
      discovery:
        instance-id: ${spring.application.name}:${spring.application.instance-id:${random.value}}
server:
  port: 8080
```

#### **For Kubernetes (K8s DNS):**
```yaml
# deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: my-service
        env:
        - name: SPRING_CLOUD_KUBERNETES_SERVICE_HOST
          value: "my-service.namespace.svc.cluster.local"
```

**Debug Steps:**
1. **Check registry logs:** `kubectl logs -l app=consul -c consul` (for Consul in K8s).
2. **Test connectivity:** `telnet consul-service 8500` or `nc -zv consul-service 8500`.
3. **Verify pod readiness:** `kubectl get pods -l app=my-service -o wide`.

---

### **B. Inter-Service Communication Timeouts**
**Issue:** Service A calls Service B, but B responds too slowly.
**Root Cause:**
- Service B is overloaded (high CPU/memory).
- Database queries are blocking (e.g., no indexes, large transactions).
- Network latency between pods (e.g., cross-cloud regions).
- Circuit breaker thresholds too low (e.g., `maxRetries = 0`).

**Fix:**
#### **1. Optimize Service B:**
```java
// Use reactive programming (e.g., Spring WebFlux) for I/O-bound tasks
@GetMapping("/orders")
public Mono<Order> getOrder(@RequestParam Long id) {
    return orderRepository.findById(id)
        .switchIfEmpty(Mono.error(new OrderNotFoundException()));
}
```

#### **2. Adjust Circuit Breaker Settings:**
```java
// Resilience4j configuration
@Bean
public Resilience4jCircuitBreakerFactory circuitBreakerFactory() {
    CircuitBreakerConfig config = CircuitBreakerConfig.custom()
        .failureRateThreshold(50) // Fail after 50% errors
        .waitDurationInOpenState(Duration.ofSeconds(30))
        .permitedNumberOfCallsInHalfOpenState(2)
        .build();
    return Resilience4jCircuitBreakerFactory.getInstance(config);
}
```

#### **3. Implement Retries with Backoff:**
```yaml
# application.yml (Resilience4j Retry)
resilience4j.retry:
  instances:
    orderServiceRetry:
      maxAttempts: 3
      waitDuration: 100ms
      enableExponentialBackoff: true
      backoffMultiplier: 2
```

**Debug Steps:**
1. **Check service metrics:** `kubectl exec -it pod/my-service -- curl http://localhost:8080/actuator/prometheus`.
2. **Trace slow calls:** Use **OpenTelemetry** or **Zipkin** to identify bottlenecks.
3. **Load test:** Simulate traffic with **Locust** or **k6**:
   ```python
   # k6 script to test Service B
   import http from 'k6/http';
   export default function() {
       const res = http.get('http://service-b:8080/orders/1');
       console.log(res.status, res.json());
   }
   ```

---

### **C. Data Consistency Issues (Saga Pattern)**
**Issue:** `OrderService` creates an order, but `PaymentService` fails to process it.
**Root Cause:**
- Saga steps are not idempotent (retries cause duplicate processing).
- Event publishing fails (e.g., Kafka partition out of sync).
- Compensating transactions not executed properly.

**Fix:**
#### **1. Ensure Idempotency:**
```java
// OrderService: Use a database lock or transaction idempotency key
@Transactional
public Order processOrder(Order order) {
    if (orderRepository.existsById(order.getId())) {
        throw new IllegalStateException("Duplicate order detected");
    }
    orderRepository.save(order);
    // Publish event
    eventPublisher.publishEvent(new OrderCreatedEvent(order));
    return order;
}
```

#### **2. Handle Event Failures with DLQ (Dead Letter Queue):**
```java
// Kafka consumer with DLQ
@KafkaListener(topics = "order-events", groupId = "order-group")
public void listen(OrderCreatedEvent event, @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
                   @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
                   @Header(KafkaHeaders.OFFSET) long offset,
                   @Header(KafkaHeaders.TIMESTAMP) long timestamp,
                   ConsumerRecord<?, ?> record,
                   Acknowledgment ack) {
    try {
        paymentService.processPayment(event);
        ack.acknowledge();
    } catch (Exception e) {
        // Send to DLQ
        kafkaTemplate.send("order-events-dlq", event);
        ack.nack(record.receivedPartition(), false); // Retry
    }
}
```

**Debug Steps:**
1. **Inspect Kafka logs:** `kafka-console-consumer --bootstrap-server kafka:9092 --topic order-events --from-beginning`.
2. **Check DLQ:** `kafka-console-consumer --bootstrap-server kafka:9092 --topic order-events-dlq --from-beginning`.
3. **Test compensating transactions:** Manually trigger a rollback and verify logs.

---

### **D. Performance Bottlenecks**
**Issue:** Service response time degrades after migration.
**Root Cause:**
- Database queries are suboptimal (e.g., `SELECT *` instead of indexed fields).
- Too many connections to the database (e.g., connection pool exhaustion).
- Uncached frequent requests (e.g., 3rd-party API calls).

**Fix:**
#### **1. Optimize Database Queries:**
```sql
-- Before (slow)
SELECT * FROM orders WHERE customer_id = 123;

-- After (fast with index)
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
SELECT id, status FROM orders WHERE customer_id = 123;
```

#### **2. Use Connection Pooling:**
```properties
# application.properties (HikariCP)
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.leak-detection-threshold=2000
```

#### **3. Implement Caching:**
```java
// Spring Cache with Redis
@Cacheable(value = "orders", key = "#customerId")
public List<Order> getOrdersByCustomer(Long customerId) {
    return orderRepository.findByCustomerId(customerId);
}
```

**Debug Steps:**
1. **Profile database queries:** Use **Slow Query Log** (MySQL) or **PGBadger** (PostgreSQL).
2. **Check connection pool metrics:** `curl http://localhost:8080/actuator/health/db`.
3. **Use APM tools:** **New Relic**, **Datadog**, or **Jaeger** to identify slow endpoints.

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                                                 | **Example Command/Usage**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **Kubernetes `kubectl`** | Inspect pods, logs, and network issues.                                     | `kubectl logs -f <pod> --previous`                |
| **Telnet/Netcat**      | Test connectivity between services.                                         | `nc -zv service-b 8080`                           |
| **curl/wire**          | Debug HTTP/gRPC calls.                                                      | `curl -v http://service-b:8080/orders/1`           |
| **Jaeger/Zipkin**      | Distributed tracing for latency analysis.                                   | `jaeger query --service=payment-service`           |
| **Prometheus + Grafana** | Monitor metrics (latency, errors, throughput).                              | `kubectl port-forward svc/prometheus 9090`        |
| **Locust/k6**          | Load test microservices under stress.                                         | `k6 run load_test.js`                             |
| **Postman/Newman**     | Test API contracts post-migration.                                          | `newman run postman_collection.json`               |
| **Kafka Console**      | Inspect event streaming issues.                                              | `kafka-console-consumer --topic orders --from-beginning` |
| **Strace/Netstat**     | Debug low-level network issues (Linux).                                      | `strace -e trace=network my-service`               |

**Advanced Techniques:**
- **Chaos Engineering:** Use **Gremlin** or **Chaos Mesh** to simulate failures.
- **Canary Deployments:** Gradually roll out changes to detect issues early.
- **Feature Flags:** Isolate new features and disable them if needed.

---

## **4. Prevention Strategies**

### **A. Pre-Migration Checklist**
| **Check**                                  | **Action**                                                                 |
|--------------------------------------------|----------------------------------------------------------------------------|
| **Service Contracts**                      | Use OpenAPI/Swagger to validate API changes.                               |
| **Data Schema Compatibility**              | Test backward/forward compatibility (e.g., Avro, Protobuf schema evolution). |
| **Dependency Versions**                    | Pin all transitive dependencies (`maven dependency:tree`).                |
| **Load Testing**                          | Simulate production traffic (e.g., 10K RPS).                              |
| **Chaos Testing**                         | Kill pods randomly to test resilience.                                    |
| **Rollback Plan**                         | Define a rollback procedure (e.g., Blue-Green or Canary).                 |

### **B. Post-Migration Monitoring**
1. **Set Up Alerts:**
   - **High error rates** (>1%).
   - **Timeouts** (e.g., >500ms).
   - **Service unavailability** (e.g., Consul/Eureka registration drops).
2. **Log Aggregation:**
   - Use **ELK Stack (Elasticsearch, Logstash, Kibana)** or **Loki**.
   - Include **request IDs** for correlation.
3. **Synthetic Monitoring:**
   - Use **Pingdom** or **UptimeRobot** to test from multiple regions.

### **C. Long-Term Stability**
- **Automate Rollbacks:**
  ```yaml
  # Argo Rollouts (Canary deployment)
  apiVersion: argoproj.io/v1alpha1
  kind: Rollout
  spec:
    strategy:
      canary:
        steps:
        - setWeight: 20
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
  ```
- **Infrastructure as Code (IaC):**
  - Use **Terraform** or **Kubernetes Manifests** for reproducibility.
- **Security Scanning:**
  - **Trivy**, **Snyk**, or **OWASP ZAP** for vulnerability scans.

---

## **5. Conclusion**
Microservices migration is complex, but a **structured debugging approach** reduces downtime. Focus on:
1. **Service discovery** (registry issues, DNS resolution).
2. **Inter-service communication** (timeouts, retries, circuit breakers).
3. **Data consistency** (Saga patterns, idempotency, DLQ).
4. **Performance** (database queries, caching, connection pooling).
5. **Observability** (tracing, metrics, logs).

**Final Tip:** Always **test in staging** before production and **monitor aggressively** post-deployment.

---
**Next Steps:**
- Run a **load test** (`k6`/`Locust`) before going live.
- Set up **automated rollbacks** if metrics degrade.
- **Document failures** in a shared knowledge base (e.g., Notion, Confluence).

By following this guide, you’ll **minimize migration risks** and **resolve issues efficiently**. 🚀