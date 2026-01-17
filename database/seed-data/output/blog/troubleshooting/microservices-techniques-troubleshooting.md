---
# **Debugging Microservices: A Troubleshooting Guide**
*For Backend Engineers*

Microservices architectures offer scalability and modularity but introduce complexity in debugging. This guide focuses on **practical, actionable steps** to resolve common issues efficiently.

---

## **1. Symptom Checklist**
Before diving deep, systematically verify these symptoms:

| **Symptom**                     | **Question to Ask**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------|
| Service crashes repeatedly       | Is it a code bug, resource constraint, or external dependency failure?              |
| Latency spikes                   | Are requests queuing up? Is inter-service communication the bottleneck?            |
| Data inconsistency               | Are events not being processed correctly? Is eventual consistency failing?         |
| Service discovery failures       | Are services failing to register/discover each other?                               |
| Database connection issues       | Are connection pools exhausted? Is retries/backoff configured?                      |
| Logging/Observability gaps       | Are logs missing? Are metrics/monitoring missing insights?                          |
| Authentication issues           | Are JWT/OAuth tokens failing to validate? Is API Gateway misconfiguring headers?    |
| Version skew errors              | Are incompatible versions of libraries/services causing failures?                   |

---

## **2. Common Issues and Fixes**

### **Issue 1: Service Crashes (5xx Errors)**
**Symptoms:**
- Random crashes with no logs.
- High CPU/memory usage in crash reports.

**Root Causes:**
- **Thread leaks** (e.g., unclosed connections).
- **Uncaught exceptions** (missing `@ExceptionHandler` in Spring Boot).
- **Resource exhaustion** (heap dump reveals OOM).

**Fixes:**
#### **Code Example: Graceful Shutdown + Resource Leak Prevention**
```java
// Spring Boot (Java) - Configure graceful shutdown
@SpringBootApplication
public class MicroserviceApp {
    @Bean
    public CommandLineRunner setup() {
        return args -> {
            // Ensure DB connections are closed on shutdown
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                // Explicitly release resources
                DataSource dataSource = ApplicationContextProvider.getApplicationContext()
                    .getBean(DataSource.class);
                ((HikariDataSource) dataSource).close();
            }));
        };
    }
}
```

#### **Debugging Steps:**
1. **Check heap dumps** (`jcmd <pid> GC.heap_dump`).
2. **Enable detailed logging** for the failing service:
   ```yaml
   # application.yml
   logging:
     level:
       org.springframework: DEBUG
   ```
3. **Use `jstack`** to inspect thread dumps:
   ```bash
   jstack <pid> > thread_dump.log
   ```

---

### **Issue 2: High Latency (Slow Responses)**
**Symptoms:**
- **99th percentile latency > 1s**.
- API Gateway logs show upstream service timeouts.

**Root Causes:**
- **Unoptimized database queries** (N+1 problem).
- **No circuit breakers** (cascading failures).
- **Inefficient inter-service communication** (gRPC vs REST tradeoffs).

**Fixes:**
#### **Code Example: Circuit Breaker with Resilience4j**
```java
// Add dependency: org.springframework.cloud:spring-cloud-starter-circuitbreaker-resilience4j
@Service
public class OrderService {
    @CircuitBreaker(name = "paymentService", fallbackMethod = "fallback")
    public String processPayment(PaymentRequest request) {
        return paymentClient.charge(request);
    }

    public String fallback(PaymentRequest request, Exception ex) {
        return "Retry later (breaker tripped)";
    }
}
```

#### **Debugging Steps:**
1. **Trace the full call stack** using distributed tracing (see [Observability Tools](#debugging-tools)).
2. **Enable APM tools** (e.g., New Relic, Datadog) to identify bottlenecks.
3. **Compare baseline metrics** (e.g., Prometheus) to spot spikes.

---

### **Issue 3: Data Inconsistency (Eventual Consistency Issues)**
**Symptoms:**
- Orders show "paid" but no payment record exists.
- Race conditions in distributed transactions.

**Root Causes:**
- **No idempotency keys** (duplicate events).
- **Eventual consistency not enforced** (e.g., Kafka lag).
- **Database transactions across services** (2PC is dead, use SAGA).

**Fixes:**
#### **Code Example: SAGA Pattern with Compensating Transactions**
```java
// Kafka-based SAGA for payments
@KafkaListener(topics = "payment.failed")
public void handlePaymentFailure(@Payload PaymentFailedEvent event) {
    // Compensating transaction: refund
    refundService.refund(event.getOrderId());
}

// Spring Kafka dependency: org.springframework.kafka:spring-kafka
```

#### **Debugging Steps:**
1. **Replay events** from Kafka (`kafka-console-consumer --bootstrap-server localhost:9092 --from-beginning --topic payment.events`).
2. **Check event timestamps** for ordering issues:
   ```sql
   -- Example: Find out-of-order events in DB
   SELECT * FROM events WHERE processed_at < created_at;
   ```
3. **Use event sourcing** tools like **Apache Kafka Streams** for audits.

---

### **Issue 4: Service Discovery Failures**
**Symptoms:**
- `ServiceUnavailable` errors (Eureka/Consul).
- Services can’t find each other.

**Root Causes:**
- **Eureka heartbeats failing** (network issues).
- **Registries misconfigured** (TTL too short).
- **DNS resolution delays** (Cloud DNS vs local).

**Fixes:**
#### **Code Example: Eureka Client Configuration**
```yaml
# application.yml
eureka:
  client:
    serviceUrl:
      defaultZone: http://eureka-server:8761/eureka
    fetchRegistry: true
    registerWithEureka: true
    healthcheck:
      enabled: true
    lease:
      renewalIntervalInSeconds: 10
```

#### **Debugging Steps:**
1. **Check Eureka dashboard** for missing instances:
   ![Eureka Dashboard](https://i.imgur.com/xyz123.png)
2. **Test network connectivity**:
   ```bash
   curl -v http://eureka-server:8761/eureka/apps
   ```
3. **Enable Eureka logs**:
   ```yaml
   logging:
     level:
       com.netflix.eureka: DEBUG
   ```

---

### **Issue 5: Database Connection Pool Exhaustion**
**Symptoms:**
- `SQLTransientConnectionException`.
- High `connectionUsed` in HikariCP metrics.

**Root Causes:**
- **Too few connections** (under-provisioned).
- **Long transactions** (leaking connections).
- **No connection validation**.

**Fixes:**
#### **Code Example: HikariCP Tuning**
```yaml
# application.yml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      validation-timeout: 5000
      isolate-internal-queries: true
```

#### **Debugging Steps:**
1. **Check metrics** (Prometheus):
   ```bash
   curl http://localhost:8080/actuator/prometheus | grep hikari
   ```
2. **Enable SQL logging**:
   ```yaml
   spring:
     jpa:
       show-sql: true
       properties:
         hibernate:
           format_sql: true
   ```
3. **Use `pgBadger` (PostgreSQL)** to find long-running queries.

---

## **3. Debugging Tools and Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|-----------------------------------------------|---------------------------------------------|
| **Distributed Tracing** | Trace requests across services (Zipkin, Jaeger) | `curl -XPOST http://jaeger:16686/api/traces` |
| **APM Tools**          | Latency breakdown (New Relic, Datadog)        | `nr1` (New Relic CLI)                       |
| **Metrics Scraping**   | Monitor service health (Prometheus + Grafana) | `prometheus --config.file=prometheus.yml`   |
| **Log Aggregation**    | Centralized logs (ELK, Loki)                 | `kibana`                                    |
| **Heap Dump Analyzer** | Memory leaks (Eclipse MAT, VisualVM)          | `jmap -dump:format=b,file=heap.hprof <pid>`  |
| **Network Debugging**  | Check inter-service calls (Wireshark, tcpdump) | `tcpdump -i any host 8080`                  |
| **Chaos Engineering**  | Test resilience (Gremlin, Chaos Mesh)        | `gremlin.sh kill --pods=payment-service`    |

**Quick Debugging Workflow:**
1. **Check APM** → Isolate slow service.
2. **Trace request** → Follow dependencies.
3. **Inspect logs** → Look for errors/stack traces.
4. **Run heap dump** → If OOM suspected.
5. **Simulate failure** → Verify circuit breakers.

---

## **4. Prevention Strategies**
### **Infrastructure**
- **Auto-scaling**: Use Kubernetes HPA or AWS Auto Scaling.
- **Multi-region deployments**: Avoid single point of failure.
- **Chaos testing**: Regularly inject failures (e.g., kill random pods).

### **Code Practices**
- **Idempotency keys**: Prevent duplicate events.
- **Retries with backoff**:
  ```java
  // Spring Retry dependency: org.springframework.retry:spring-retry
  @Retryable(maxAttempts = 3, backoff = @Backoff(delay = 1000))
  public String callExternalService() { ... }
  ```
- **Health checks**: `/actuator/health` should return fast.
- **Feature flags**: Roll out changes safely.

### **Observability**
- **Centralized logging** (ELK, Loki).
- **Metrics per endpoint** (Prometheus + Grafana).
- **Distributed tracing** (Zipkin).

### **CI/CD**
- **Canary deployments**: Gradually roll out updates.
- **Postmortem templates**: Standardize incident reviews.

---

## **5. Final Checklist for Quick Resolution**
| **Step**               | **Action**                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **Isolate the issue**  | Check logs, metrics, and traces for the exact failing service.           |
| **Reproduce locally**  | Spin up a dev environment with the same config.                          |
| **Compare baselines**  | Compare current vs. historical metrics (e.g., CPU, latency).             |
| **Test fixes**         | Deploy a hotfix and monitor impact (roll back if needed).                |
| **Document**           | Update runbooks for future incidents.                                     |

---
**Key Takeaway**: Microservices debugging requires **distributed thinking**. Use tools to **trace, monitor, and isolate**, then apply **retries, circuit breakers, and observability** to prevent future issues. Always **start with the symptoms** and work backward.

Would you like a deep dive into any specific area (e.g., Kafka debugging, Kubernetes networking)?