# **Debugging Hybrid Integration: A Troubleshooting Guide**
*For Backend Engineers Handling Microservices, APIs, and Legacy System Connections*

---

## **Introduction**
The **Hybrid Integration** pattern combines **synchronous API calls, asynchronous event-driven messaging (e.g., Kafka, RabbitMQ), and batch processing** to integrate disparate systems—often legacy monoliths with cloud-native microservices. While powerful, this architecture introduces complexity, leading to latency issues, failed transactions, and inconsistent state.

This guide helps you **quickly diagnose and resolve** common Hybrid Integration failures by focusing on **symptoms, root causes, and actionable fixes**.

---

## **🔍 Symptom Checklist: When to Use This Guide**
Check if your system exhibits any of these signs:

| **Symptom** | **Likely Cause** |
|-------------|------------------|
| **API calls to legacy systems timeout or fail sporadically** | Network issues, throttling, or DB locks |
| **Event consumers (Kafka/RabbitMQ) miss messages** | Consumer lag, partition rebalancing, or message TTL expiration |
| **Duplicate/out-of-order transactions in hybrid flows** | Idempotency issues, retry loops, or inconsistent event ordering |
| **Batch jobs hang or fail silently** | Deadlocks, large payloads, or resource exhaustion |
| **Database transactions fail with `SERIALIZATION_FAILURE`** | Unhandled retries causing race conditions |
| **Logging shows `5xx` errors but no clear retry logic** | Missing circuit breakers or exponential backoff |
| **Monitoring shows spikes in `HTTP 429` or `503` errors** | Rate limiting or API gateway throttling |

If you see **any of these**, proceed to the next section for targeted fixes.

---

## **🐛 Common Issues & Fixes**

### **1. API Timeouts & Failed Requests**
**Symptom:**
- HTTP calls to legacy systems (`/api/orders/process`) return `5xx` or time out.
- Client-side retries fail after 3 attempts.

**Root Causes:**
✅ **Network Latency** – Legacy systems may be slow due to cold starts or DB queries.
✅ **Legacy System Rate Limiting** – Unconfigured `requestTimeout` or `connectTimeout`.
✅ **Database Locks** – Long-running transactions block subsequent calls.
✅ **API Gateway Throttling** – Too many concurrent requests hit the `429` limit.

#### **Quick Fixes (Code Examples)**

**A. Increase Timeout & Retry with Backoff (Java/Spring Boot)**
```java
@RestController
public class OrderController {

    @Value("${legacy.api.timeout:5000}") // Default 5s, adjust as needed
    private int legacyApiTimeout;

    @Retry(name = "legacyApiRetry", maxAttempts = 3)
    @CircuitBreaker(name = "legacyApiCircuit", fallbackMethod = "fallbackProcessOrder")
    public ResponseEntity<Order> processOrder(OrderInput input) {
        return restTemplate.exchange(
            "http://legacy-system/api/orders",
            HttpMethod.POST,
            new HttpEntity<>(input),
            Order.class,
            new HttpClientRequestFactory() {
                @Override
                public HttpURLConnection createConnection(HttpURLConnection urlConnection) {
                    urlConnection.setConnectTimeout(legacyApiTimeout);
                    urlConnection.setReadTimeout(legacyApiTimeout);
                    return urlConnection;
                }
            }
        );
    }

    // Fallback method if circuit breaks
    public ResponseEntity<Order> fallbackProcessOrder(OrderInput input, Exception e) {
        // Log & return a degraded response
        return ResponseEntity.status(503).body(new Order("Fallback processed"));
    }
}
```

**B. Handle 429/503 Errors with Jittered Retries (Python/Requests)**
```python
import backoff
from requests import RequestException

@backoff.on_exception(
    backoff.expo,
    RequestException,
    max_tries=5,
    jitter=backoff.full_jitter
)
def call_legacy_api(order_data):
    url = "http://legacy-system/api/orders"
    headers = {"X-RateLimit-Retry-After": "3"}  # Handle 429 delays
    response = requests.post(url, json=order_data, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
```

**C. Check Legacy System Logs for Deadlocks**
```sql
-- Run in legacy DB to find blocking queries
SELECT * FROM v$locked_object WHERE blocking_session IS NOT NULL;
-- Or check app logs for "timeout expired" warnings
```

---

### **2. Missing/Out-of-Order Events (Kafka/RabbitMQ)**
**Symptom:**
- Event consumers process messages with gaps or duplicates.
- Transactional integrity broken (e.g., order `created` but `paid` event missing).

**Root Causes:**
✅ **Consumer Lag** – Messages accumulate faster than consumers process them.
✅ **Partition Rebalancing** – Kafka partitions resized, causing missed commits.
✅ **No Exactly-Once Semantics** – Duplicates due to retries without idempotency.
✅ **Event Ordering Violation** – Events from different services interleave incorrectly.

#### **Quick Fixes**

**A. Monitor Consumer Lag (Kafka)**
```bash
# Check lag in real-time
kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group my-consumer-group --describe

# If lag > 1000 messages, scale consumers or adjust fetch.min.bytes
```

**B. Enable Idempotent Consumers (Java/Kafka)**
```java
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT, "false");
props.put(ConsumerConfig.ISOLATION_LEVEL_READ_COMMITTED, "true");

KafkaConsumer<String, OrderEvent> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Collections.singletonList("orders-topic"));

try {
    while (true) {
        ConsumerRecords<String, OrderEvent> records = consumer.poll(100);
        for (ConsumerRecord<String, OrderEvent> record : records) {
            // Process with retry on failure
            if (processOrderEvent(record.value())) {
                consumer.commitSync(); // Only commit if successful
            }
        }
    }
} finally {
    consumer.close();
}
```

**C. Use Transactional Outbox Pattern (Spring Kafka)**
```java
@EnableTransactionManagement
@Service
public class OrderService {

    @Transactional
    public void createOrder(Order order) {
        // Save to DB (outbox)
        outboxRepository.save(new OrderOutbox(order, "ORDER_CREATED"));

        // Publish to Kafka (transactional)
        kafkaTemplate.send(TOPIC_ORDER_EVENTS, "ORDER_CREATED", order);
    }
}
```

---

### **3. Batch Job Failures (Deadlocks, Timeouts)**
**Symptom:**
- Scheduled batch jobs (e.g., `export-legacy-data`) hang or fail with `ResourceDeadlockException`.

**Root Causes:**
✅ **Large Payloads** – Processing 1M records in a single batch exceeds memory.
✅ **Optimistic Locking Conflicts** – `@Version` annotations cause retries.
✅ **Transaction Isolation Too High** – `SERIALIZABLE` blocks other transactions.

#### **Quick Fixes**

**A. Split Batch into Chunks (Spring Batch)**
```java
@Bean
public Step exportLegacyDataStep() {
    return stepBuilderFactory.get("exportLegacyDataStep")
        .<DataRecord, DataRecord>chunk(1000) // Process 1000 records at a time
        .reader(itemReader())
        .processor(itemProcessor())
        .writer(itemWriter())
        .build();
}
```

**B. Lower Transaction Isolation (JPA)**
```java
@Transactional(isolation = Isolation.READ_COMMITTED) // Default is SERIALIZABLE
public void updateLegacyData() {
    // ...
}
```

**C. Add Circuit Breaker for External Calls**
```java
@CircuitBreaker(name = "legacyBatchService", fallbackMethod = "fallbackBatch")
public void processLegacyBatch(List<Record> records) {
    legacyService.batchProcess(records);
}

public void fallbackBatch(Throwable t) {
    // Retry later or notify admin
    scheduler.schedule(() -> processLegacyBatch(records), 1, TimeUnit.HOURS);
}
```

---

### **4. Database Serialization Failures**
**Symptom:**
- `DataIntegrityViolationException: SQL09006N: Serialization failure...`

**Root Causes:**
✅ **Retry Storm** – Consumers retry failed transactions, causing deadlocks.
✅ **Long-Running Transactions** – Legacy DB holds locks too long.
✅ **Missing Retry Logic** – Failed API calls retry without backoff.

#### **Quick Fixes**

**A. Use Spring Retry with Exponential Backoff**
```xml
<!-- application.properties -->
spring.retry.max-attempts=5
spring.retry.backoff.initial-interval=1000
spring.retry.backoff.multiplier=2
spring.retry.backoff.max-interval=10000
```

**B. Shorten Transaction Timeouts (PostgreSQL)**
```sql
-- Set in legacy DB config
ALTER SYSTEM SET statement_timeout = '30s';
```

**C. Implement Saga Pattern for Long-Running Workflows**
```java
@Saga
public class OrderSaga {
    @SagaMethod(compensationMethod = "cancelOrder")
    public void createOrder(Order order) {
        // Call legacy system
        legacyService.placeOrder(order);
        // Publish event
        eventPublisher.publish(new OrderCreatedEvent(order));
    }

    @SagaMethod
    public void cancelOrder(Order order) {
        // Rollback steps
        legacyService.cancelOrder(order);
    }
}
```

---

## **🛠 Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Command/Example** |
|----------|-------------|----------------------|
| **Kafka Consumer Lag Check** | Monitor event processing delays | `kafka-consumer-groups --describe` |
| **Prometheus + Grafana** | Track API latency, error rates | `rate(http_requests_total{status=~"5.."}[5m])` |
| **Spring Boot Actuator** | Check active threads, DB queries | `http://localhost:8080/actuator/threads` |
| **ELK Stack (Logstash/Elasticsearch)** | Correlate logs across services | `kibana query: "legacy.api timeout"` |
| **JDK Flight Recorder (JFR)** | Profile long-running transactions | `jcmd <pid> JFR.start duration=60s filename=profile.jfr` |
| **PostgreSQL pgBadger** | Analyze slow queries | `pgbadger -f postgresql.log` |
| **Chaos Engineering (Gremlin)** | Test resilience | `kill random pod in namespace=legacy` |

**Pro Tip:**
- **Use `tracer` (OpenTelemetry) to trace hybrid flows:**
  ```java
  @Trace("order-flow")
  public Order processOrder(OrderInput input) {
      // ...
  }
  ```
  Visualize in **Jaeger** or **Zipkin**.

---

## **🔧 Prevention Strategies**
To avoid Hybrid Integration pain points long-term:

### **1. Design for Resilience**
- **APIs:**
  - Implement **rate limiting** (`Resilience4j`).
  - Use **async processing** (e.g., send events to a queue instead of blocking calls).
- **Events:**
  - Enforce **exactly-once processing** (Kafka transactions + idempotent consumers).
  - Use **dead-letter queues (DLQ)** for failed events.
- **Batches:**
  - **Chunk processing** (10k records at max).
  - **Short-lived transactions** (avoid `SERIALIZABLE`).

### **2. Monitoring & Alerts**
- **Alert on:**
  - `KafkaConsumerLag > 1000` (for 5 mins).
  - `HTTP 5xx errors > 1%` (for 1 min).
  - `Database lock waits > 5s`.
- **Tools:**
  - **Prometheus Alertmanager** for SLOs.
  - **Datadog/New Relic** for APM.

### **3. Testing Strategies**
- **Chaos Engineering:**
  - Simulate **network partitions** (`Chaos Mesh`).
  - Kill **Kafka brokers** to test failover.
- **Contract Testing (Pact):**
  ```java
  @Pact(provider = "legacy-system", consumer = "my-service")
  public void verifyOrderApi() {
      given("an order is created")
          .uponReceiving("a POST request to /orders")
          .withRequestBody(new OrderInput("123", 100))
          .willRespondWith(200, "{\"id\":\"123\",\"status\":\"CREATED\"}");
  }
  ```
- **Integration Tests:**
  - Use **Testcontainers** for Kafka/RabbitMQ in CI.

### **4. Documentation & Runbooks**
- **Maintain a Hybrid Integration Cheat Sheet** (e.g., GitHub Wiki) with:
  - API timeouts & retries.
  - Event schema changes.
  - Batch job parameters.
- **Runbook for Failures:**
  ```
  1. If Kafka consumer lag > 5000:
     a. Scale consumers by 20%.
     b. Check for serialization errors in logs.
  2. If API timeouts > 5%:
     a. Increase `connectTimeout` by 2s.
     b. Notify legacy team for DB tuning.
  ```

---

## **🚀 Summary: Quick Action Plan**
| **Symptom** | **Immediate Fix** | **Long-Term Fix** |
|-------------|-------------------|-------------------|
| API timeouts | Increase timeouts + circuit breaker | Implement async processing |
| Missing events | Check Kafka lag + enable idempotency | Use transactional outbox |
| Batch deadlocks | Split chunks + lower isolation | Test with chaos engineering |
| Serialization fails | Retry with backoff | Optimize transactions |

---

## **📌 Final Checklist Before Going Live**
✅ **APIs:**
- [ ] Timeouts set to DB response time + buffer.
- [ ] Retry logic with jitter implemented.
- [ ] Circuit breakers configured.

✅ **Events:**
- [ ] Kafka partitions sized for throughput.
- [ ] Consumer groups scaled to match producers.
- [ ] Idempotency keys in event payloads.

✅ **Batches:**
- [ ] Chunk size < 10k records.
- [ ] Transaction isolation `READ_COMMITTED` by default.
- [ ] DLQ configured for failures.

✅ **Monitoring:**
- [ ] Alerts for lag, errors, and timeouts.
- [ ] Distributed tracing enabled.

---
**Hybrid Integration is complex, but with the right tools and checks, you can keep it running smoothly.** Start by fixing the **most frequent failures** (API timeouts, Kafka lag), then **prevent them** with resilience patterns and monitoring. 🚀