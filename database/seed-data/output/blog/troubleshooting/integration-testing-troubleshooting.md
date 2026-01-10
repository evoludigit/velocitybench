# **Debugging Integration Testing Patterns: A Troubleshooting Guide**

## **Introduction**
Integration testing ensures that components, services, and systems interact correctly—unlike unit testing, which isolates individual parts. When unit tests pass but the system fails in production, integration issues are often the culprit.

This guide helps **backend engineers** quickly identify, debug, and fix common integration problems with practical steps, code examples, and prevention strategies.

---

## **1. Symptom Checklist**
Before diving into code, verify these common symptoms:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **Unit tests pass, but deployed code crashes** | Tests work in isolation; real-world conditions fail | Missing dependency, configuration mismatch, race conditions |
| **API works alone but fails when calling external services** | Local API mocks succeed; real service calls fail | Network issues, auth failures, data format mismatches |
| **Database queries succeed in isolation but fail in transactions** | Individual queries work; combined operations crash | Deadlocks, schema inconsistencies, transaction isolation levels |
| **Caching behaves differently in integration vs. unit tests** | Cache hits/misses vary between test and production | Cache invalidation logic, stale data, concurrency conflicts |
| **Microservices fail to communicate via events/messaging** | Service A emits an event; Service B doesn’t receive it | Broker misconfiguration, serialization errors, retry logic |
| **API responses vary between local dev and staging** | Dev environment works; staging fails silently | Environment-specific configs, rate limits, dependent service downtime |

**Quick Check:**
✅ Are all dependencies mocked correctly in unit tests?
✅ Does the deployed system match the testing environment?
✅ Are there hidden dependencies (e.g., shared DB schema, shared caches)?

---

## **2. Common Issues & Fixes**

### **Issue 1: Missing or Misconfigured Dependencies**
**Symptom:**
- Unit tests pass (with mocks/stubs), but real integration fails.
- Error: `ServiceUnavailable`, `ConnectionRefused`, or `NullPointerException`.

**Root Cause:**
- Unit tests rely on mocks; production depends on real services.
- Configurations (e.g., `DATABASE_URL`, `API_KEY`) differ between test and prod.

**Debugging Steps:**
1. **Log actual dependency calls** (avoid `System.out.println`; use structured logging).
2. **Verify connection strings** in both test and production.

**Fix (Example - Spring Boot):**
```java
// Before (unit test works with mock)
@MockBean
private ExternalService externalService;

// After (real integration)
@Bean
public ExternalService realExternalService() {
    return new HttpClientExternalService("https://api.prod.example.com");
}
```

**Preventive Fix:**
- Use **test profiles** (`@SpringBootTest(properties = "config.location=classpath:test-config.properties")`).
- Store configs in **environment variables** (never hardcode).

---

### **Issue 2: API Calls Fail When Chaining Services**
**Symptom:**
- API works in isolation but fails when integrating with another service.
- Error: `401 Unauthorized`, `502 Bad Gateway`, or timeout.

**Root Cause:**
- Missing headers (e.g., `Authorization`, `Content-Type`).
- Serialization mismatch (e.g., JSON → XML).
- Rate limiting or health checks blocking requests.

**Debugging Steps:**
1. **Inspect network requests** (use Postman, cURL, or `curl -v`).
2. **Check logs** for API response errors.

**Fix (Example - Fetching with Headers):**
```java
// Correct: Send auth headers
String response = new HttpClient().execute(
    new Request.Builder()
        .url("https://api.example.com/data")
        .addHeader("Authorization", "Bearer " + getToken())
        .build()
);

// Incorrect: Missing headers → 401
String badResponse = new HttpClient().execute(Request.Builder().url("...").build());
```

**Preventive Fix:**
- Use **API client libraries** (e.g., `OkHttp`, `RestTemplate`, `Axios`) to handle retries, timeouts, and headers.
- **Mock external APIs in tests** to verify integration logic without real calls.

---

### **Issue 3: Database Transaction Failures**
**Symptom:**
- Individual queries work, but combined transactions fail.
- Error: `SQLException: Deadlock`, `ConstraintViolation`, or `Deadline Exceeded`.

**Root Cause:**
- **Race conditions** (e.g., two threads updating the same row).
- **Improper transaction isolation** (dirty reads, phantom reads).
- **Missing constraints** (foreign key violations).

**Debugging Steps:**
1. **Enable SQL logging** to see exact queries.
2. **Check for deadlocks** in DB logs.

**Fix (Example - Handling Deadlocks):**
```java
// Retry logic for deadlocks (PostgreSQL example)
int maxRetries = 3;
int retryCount = 0;
boolean success = false;

while (!success && retryCount < maxRetries) {
    try {
        transactionManager.begin();
        // Critical section
        success = true;
        transactionManager.commit();
    } catch (DeadlockLoserDataException e) {
        retryCount++;
        Sleep(100 * retryCount); // Exponential backoff
    }
}
```

**Preventive Fix:**
- **Use optimistic locking** (`@Version` in JPA).
- **Isolate transactions** (`@Transactional` with `timeout`).
- **Test concurrency** with `ThreadLocal` or `CountDownLatch`.

---

### **Issue 4: Caching Inconsistencies**
**Symptom:**
- Cache works in tests but fails in production (e.g., stale data, cache misses).
- Error: `NullPointerException` when accessing invalidated cache.

**Root Cause:**
- Cache invalidation not triggered on DB changes.
- Thread-safety issues in cache updates.
- Different cache eviction policies between test and prod.

**Debugging Steps:**
1. **Log cache hits/misses** (`CacheStats` in Java).
2. **Verify cache invalidation triggers** (e.g., `@CacheEvict` in Spring).

**Fix (Example - Cache Eviction on DB Update):**
```java
// Spring Boot with @CacheEvict
@CacheEvict(value = "userCache", key = "#user.id")
public User updateUser(Long id, UserDto dto) {
    return userRepository.save(user);
}
```

**Preventive Fix:**
- Use **distributed cache** (Redis, Hazelcast) for consistency.
- **Test cache invalidation** with `Mockito` or **Testcontainers**.

---

### **Issue 5: Microservice Communication Failures**
**Symptom:**
- Service A sends an event; Service B doesn’t process it.
- Error: `NoConsumers`, `MessageTimeout`, or `Consumer Lag`.

**Root Cause:**
- **Broker misconfiguration** (Kafka, RabbitMQ).
- **Schema mismatch** (e.g., Protobuf vs. JSON).
- **Consumer crashes silently** without retries.

**Debugging Steps:**
1. **Check broker logs** (Kafka: `kafka-consumer-groups`).
2. **Verify event serialization** (compare produced/consumed messages).

**Fix (Example - Kafka Consumer Retries):**
```java
// Configure retry in consumer
props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 5);
props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
```

**Preventive Fix:**
- **Use Idempotent consumers** (deduplicate messages).
- **Test event flow** with **Testcontainers** or **LocalStack**.

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command/Code** |
|----------|-------------|--------------------------|
| **Postman/cURL** | Test API endpoints | `curl -H "Authorization: Bearer token" https://api.example.com/data` |
| **SQL Logs** | Debug transaction issues | `spring.jpa.show-sql=true` |
| **Kafka Consumer Groups** | Monitor event processing | `kafka-consumer-groups --bootstrap-server localhost:9092 --describe` |
| **Redis CLI** | Check cache state | `redis-cli info stats` |
| **Thread Dumps (jstack)** | Detect deadlocks | `jstack <pid> > thread_dump.txt` |
| **Prometheus + Grafana** | Monitor service health | `curl http://localhost:9090/api/v1/query?query=up` |
| **Testcontainers** | Spin up real DBs/services in tests | `@Container` `PostgreSQLContainer db = new PostgreSQLContainer();` |

**Pro Tip:**
- **Use structured logging** (e.g., Logback with JSON):
  ```xml
  <configuration>
    <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
      <encoder>
        <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
      </encoder>
    </appender>
  </configuration>
  ```

---

## **4. Prevention Strategies**
| **Strategy** | **Action** | **Example** |
|-------------|-----------|-------------|
| **Isolated Test Dependencies** | Mock external services in unit tests | `@MockBean` in Spring Boot |
| **Environment Parity** | Match dev/staging/prod setups | Use `docker-compose` for local dev |
| **Idempotent Operations** | Ensure retries don’t cause duplicates | `INSERT ... ON CONFLICT DO NOTHING` |
| **Health Checks** | Detect service failures early | `/actuator/health` in Spring Boot |
| **Circuit Breakers** | Fail fast if dependencies are down | Hystrix/Resilience4j |
| **Chaos Engineering** | Test failure scenarios | Gremlin for controlled outages |

**Example: Resilience4j Circuit Breaker**
```java
@CircuitBreaker(name = "externalService", fallbackMethod = "fallback")
public String callExternalService() {
    return externalService.getData();
}

public String fallback(Exception e) {
    return "Fallback response";
}
```

---

## **5. Final Checklist for Quick Resolution**
When debugging integration issues, follow this flow:

1. **Reproduce locally** → Is it a test vs. prod issue?
2. **Check logs** → Are dependencies failing silently?
3. **Inspect network calls** → Are headers/metadata correct?
4. **Verify transactions** → Are deadlocks or timeouts happening?
5. **Test cache behavior** → Are invalidations working?
6. **Enable monitoring** → Are metrics showing unexpected spikes?
7. **Apply fixes incrementally** → Test each change.

---

## **Conclusion**
Integration testing failures are often **configuration, dependency, or concurrency issues**. By:
✔ **Logging dependencies explicitly**
✔ **Mocking real services in tests**
✔ **Using circuit breakers & retries**
✔ **Ensuring environment parity**

you can **minimize integration surprises** and **ship with confidence**.

**Next Steps:**
- Run a **targeted integration test suite** (not just unit tests).
- **Automate health checks** for dependent services.
- **Monitor in production** with distributed tracing (Jaeger, OpenTelemetry).

---
**Further Reading:**
- [Testcontainers for Integration Tests](https://www.testcontainers.org/)
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [PostgreSQL Deadlock Handling](https://www.postgresql.org/docs/current/sql-select.html)