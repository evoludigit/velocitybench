# **[Pattern] Debugging Gotchas – Reference Guide**

---

## **Overview**
Debugging Gotchas refers to subtle, often overlooked issues that repeatedly cause bugs in systems, particularly in distributed or complex environments. These missteps often stem from assumptions about system behavior, race conditions, edge cases, or misconfigured dependencies. Mastering this pattern helps developers proactively identify and resolve issues before they escalate, reducing downtime and improving reliability.

A well-structured debugging approach involves systematically analyzing logs, metrics, and code behavior under stress, while accounting for common pitfalls like:
- **Race conditions** (e.g., thread scheduling, async delays)
- **Lack of transaction boundaries** (e.g., partial updates in distributed systems)
- **Implicit assumptions** (e.g., time synchronization, network latency)
- **Debugging in production** (e.g., logging noise, memory constraints)

This guide provides a checklist of known gotchas, practical debugging techniques, and mitigation strategies.

---

## **Schema Reference**
The following table categorizes **Debugging Gotchas** by their source and typical symptoms.

| **Gotcha Category**       | **Common Causes**                                                                 | **Symptoms**                                                                 | **Detection Methods**                                                                 | **Mitigation Strategies**                                                                 |
|----------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Concurrency Issues**     | Unsafe shared state, race conditions, deadlocks, lack of locks/mutexes.            | Random failures, data corruption, hangs.                                     | Thread dumps, race detector tools (e.g., `ThreadSanitizer`), stack traces under load. | Use locks (semaphores, mutexes), actor model, or immutable data structures.              |
| **Network/Transport**      | Timeouts, packet loss, retries without backoff, serialization issues.              | Flaky API calls, timeouts, duplicate requests, data deserialization errors.  | Network latency monitors, Wireshark, `tcpdump`, distributed tracing (e.g., Jaeger).   | Implement exponential backoff, idempotency checks, and circuit breakers.                  |
| **Time/Clock Dependencies**| Assumptions about system clocks (e.g., `DateTime.Now`), timezone mismatches.       | Time-based bugs (e.g., missed deadlines, duplicate processing).              | Log timestamps, use UTC, clock skew detection tools.                                 | Use distributed locks, cron jobs with jitter, or clock synchronization (e.g., NTP).     |
| **Logging & Observability**| Insufficient granularity, log forwarding failures, missing context.                | Hard-to-replicate bugs, silent failures.                                    | Structured logging (JSON), distributed tracing, error tracking (e.g., Sentry).      | Implement rich metadata in logs, correlation IDs, and agent-based logging.               |
| **Configuration Drift**    | Hidden dependencies (e.g., `env` variables, config files), missing defaults.      | Environment-specific failures, hidden bugs in staging.                      | Configuration diff tools, environment variable audits.                                | Use feature flags, strict validation, and immutable config management.                  |
| **Memory & GC Issues**     | Memory leaks, high GC pauses, object retention.                                    | Slow performance, crashes, or high CPU usage.                                | Heap dumps (VisualVM, `jmap`), GC logs, memory profilers.                           | Monitor heap growth, use weak references, or reduce object churn.                       |
| **Database & Storage**     | Untransacted operations, schema evolution, connection pooling leaks.              | Data inconsistency, timeouts, connection exhaustion.                         | SQL dumps, query execution plans, connection pool monitors.                          | Enforce transactions, use connection limits, and versioned schemas.                     |
| **Retry & Idempotency**    | Uncontrolled retries leading to duplicate work, no idempotency keys.              | Duplicate processing, race conditions in writes.                             | Audit logs, idempotency key tracking (e.g., UUIDs).                                  | Implement idempotency, deduplication, and retry circuits.                               |
| **API & Protocol Gotchas** | Version mismatches, missing error handling, over-reliance on default behavior.      | API failures, data corruption, unhandled exceptions.                          | API contract tests, Postman/Insomnia collections, contract testing (e.g., Pact).      | Use explicit versioning, strict error responses, and schema validation.                |
| **Dependency Hell**        | Version conflicts, circular dependencies, transitive deps.                       | Build failures, runtime crashes, incompatible libraries.                      | Dependency trees (e.g., `yarn why`, `mvn dependency:tree`).                         | Use dependency pinning, monorepos, or dependency isolation.                             |
| **Testing Gaps**           | Missing edge cases, flaky tests, incomplete coverage.                              | Undiscovered bugs, false negatives.                                          | Test coverage reports (e.g., JaCoCo), chaos engineering tools (e.g., Gremlin).      | Adopt property-based testing, test chaos, and integrate static analysis.                |

---

## **Query Examples**
Debugging Gotchas often require targeted queries to isolate issues. Below are common debugging scenarios and their tools/queries.

### **1. Detecting Race Conditions**
**Scenario**: A shared counter increments incorrectly under high load.
**Tools**:
- **ThreadSanitizer (TSan)**:
  ```bash
  clang -fsanitize=thread -g my_program.c -o my_program
  ./my_program
  ```
  *Output*: Points to unsafe access to `counter`.
- **Java `jstack`**:
  ```bash
  jstack -l <pid> | grep "blocked on"
  ```

**Mitigation**: Replace with `AtomicInteger` or use a lock:
```java
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet(); // Thread-safe
```

---

### **2. Network Latency & Timeouts**
**Scenario**: API calls hang intermittently.
**Tools**:
- **Wireshark Filter**:
  ```bash
  tcp.port == 8080 && tcp.analysis.acked_segments > 0
  ```
  *Look for*: Slow acknowledgments (RTO > 3s).
- **Prometheus/Grafana**:
  ```promql
  rate(http_requests_total{status=~"5.."}[1m]) > 0
  ```
  *Alert if*: HTTP 5xx errors spike.
**Mitigation**: Add retry with jitter:
```python
# Using `tenacity` library
retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
```

---

### **3. Clock Skew Issues**
**Scenario**: Two services disagree on timestamps, causing duplicate processing.
**Tools**:
- **Log Analysis**:
  ```bash
  grep "timestamp" /var/log/app.log | sort -n | uniq -c | sort -nr
  ```
  *Look for*: Large gaps (e.g., 10m+ between logs).
- **NTP Stats**:
  ```bash
  ntpq -p
  ```
  *Check*: `offset` > 1s indicates skew.
**Mitigation**: Use distributed locks or record-then-playback:
```go
// Using a distributed lock (e.g., Redis)
lock, _ := redis.Lock(ctx, "job:process", 5*time.Second)
defer lock.Unlock(ctx)
```

---

### **4. Memory Leaks**
**Scenario**: Memory usage grows linearly with traffic.
**Tools**:
- **Java Heap Analysis**:
  ```bash
  jmap -dump:format=b,file=heap.hprof <pid>
  ```
  *Analyze with*: Eclipse MAT or `gcviewer`.
- **Go Profile**:
  ```bash
  go tool pprof http://localhost:8080/debug/pprof/heap
  ```
**Mitigation**: Find and close resources:
```python
# Python: Use contextlib
with open("file.txt", "r") as f:
    data = f.read()  # File is auto-closed
```

---

### **5. Database Inconsistency**
**Scenario**: Orders and payments are desynchronized.
**Tools**:
- **SQL Audit**:
  ```sql
  SELECT o.order_id, COUNT(p.payment_id)
  FROM orders o
  LEFT JOIN payments p ON o.order_id = p.order_id
  WHERE o.status = 'completed'
  GROUP BY o.order_id
  HAVING COUNT(p.payment_id) = 0;
  ```
- **Distributed Transaction Check**:
  ```bash
  pg_stat_activity | grep "in transaction"
  ```
**Mitigation**: Enforce transactions:
```sql
BEGIN;
INSERT INTO orders VALUES (...);
INSERT INTO payments VALUES (...);
COMMIT;
```

---

## **Related Patterns**
Debugging Gotchas intersects with several anti-patterns and best practices:

| **Related Pattern**               | **Connection**                                                                 | **Key Resources**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Circuit Breaker**                | Prevents retries from exacerbating network failures.                          | [Resilience4j](https://resilience4j.readme.io/), [Spring Retry](https://docs.spring.io/spring-retry/docs/1.2.x/reference/html/) |
| **Idempotency Key**                | Ensures duplicate requests don’t cause side effects.                         | [AWS Idempotency Guide](https://docs.aws.amazon.com/amazons3/latest/userguide/using-virtual-hosting.html#vhosting-idempotency) |
| **Chaos Engineering**              | Proactively tests failure scenarios.                                         | [Chaos Mesh](https://chaos-mesh.org/), [Gremlin](https://www.gremlin.com/)       |
| **Distributed Tracing**           | Correlates logs across services to debug latency.                            | [OpenTelemetry](https://opentelemetry.io/), [Jaeger](https://www.jaegertracing.io/) |
| **Feature Flags**                  | Isolates buggy features without redeploying.                                 | [LaunchDarkly](https://launchdarkly.com/), [Unleash](https://www.getunleash.io/) |
| **Observability Stack**            | Logs + Metrics + Traces for root-cause analysis.                              | [ELK Stack](https://www.elastic.co/elastic-stack), [Datadog](https://www.datadoghq.com/) |
| **Postmortem Culture**             | Document failures to prevent recurrence.                                     | [Google’s Postmortem Guide](https://landing.google.com/sre/sre-book/table-of-contents.html#postmortems) |

---

## **Key Takeaways**
1. **Assume everything can fail**: Design for concurrency, network partitions, and clock skew.
2. **Instrument early**: Log structured data, trace requests, and monitor edge cases.
3. **Test failure modes**: Use chaos engineering to validate resilience.
4. **Automate detection**: Set up alerts for anomalies (e.g., sudden latency spikes).
5. **Document gotchas**: Maintain a living list of pitfalls in your team’s knowledge base.

By internalizing these gotchas, teams can shift from reactive debugging to proactive reliability engineering.