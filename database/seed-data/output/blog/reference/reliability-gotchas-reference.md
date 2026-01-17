---
# **[Pattern] Reliability Gotchas – Reference Guide**

---

## **Overview**
The **Reliability Gotchas** pattern identifies common pitfalls that can undermine system robustness, performance, or scalability when not properly addressed. While seemingly minor, these issues—such as **unhandled race conditions, improper retries, resource leaks, or optimistic concurrency assumptions**—can lead to cascading failures, data corruption, or degraded user experiences.

This guide provides a structured breakdown of **recurring anti-patterns** in distributed and concurrent systems, along with mitigation strategies and code-level considerations. It covers **best practices for resilience, error handling, and defensive programming**, ensuring systems remain stable under adverse conditions.

---

## **Key Concepts & Implementation Details**

### **1. Definition**
A **Reliability Gotcha** is a subtle flaw in system design, code, or configuration that:
- **Worsens under load** (e.g., cascading failures).
- **Assumes invariants that don’t hold** (e.g., "the network is always reliable").
- **Introduces hidden state** (e.g., racial conditions in distributed transactions).
- **Fails to account for edge cases** (e.g., partial updates, race conditions).

---

### **2. Common Categories of Gotchas**
| **Category**          | **Description**                                                                 | **Impact**                                                                 |
|-----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Concurrency**       | Race conditions, deadlocks, or unbounded retries during contention.          | Data corruption, lost updates, or system hangs.                            |
| **Retry & Backoff**   | Improper retry logic (e.g., exponential backoff misconfigured, retries on transient errors). | Amplifies load, leads to **thundering herd problems**.                       |
| **Resource Leaks**    | Unclosed DB connections, file handles, or sockets.                           | OOM errors, degraded performance.                                           |
| **Idempotency**       | Non-idempotent operations (e.g., `POST /create` without deduplication).   | Duplicate records, inconsistent state.                                      |
| **Distributed Assumptions** | Single-system optimizations (e.g., local caching, clock synchronization). | Failures in distributed environments (e.g., **clock skew** causing timeouts). |
| **Error Handling**    | Swallowing exceptions, lack of circuit breakers, or logging too little.     | Undetected failures, slow diagnoses.                                       |
| **Validation**        | Skipping input validation, immutable constraints (e.g., no "soft deletes"). | Security vulnerabilities, data integrity issues.                          |
| **Dependency Failures** | Hard dependencies (e.g., blocking calls to external APIs).                  | Latency spikes, cascading failures.                                         |

---

## **Schema Reference**

Below are **structural templates** for analyzing and documenting reliability gotchas in your system.

### **1. Gotcha Identification Template**
| **Field**            | **Description**                                                                 | **Example**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Name**             | Short, descriptive name (e.g., "Unbounded Retry Loop").                       | `RetryStorm`                                                                 |
| **Category**         | From the list above (e.g., *Concurrency*, *Retry & Backoff*).                  | `Concurrency`                                                               |
| **Root Cause**       | Why it happens (e.g., "Missing locks in distributed transaction.").          | "No retry limit + exponential backoff misconfigured."                       |
| **Symptoms**         | Observables (e.g., "5xx errors spike during peak traffic.").                 | "DB timeouts increase by 300% after patch."                                   |
| **Impact**           | Business/technical consequences.                                              | "Lost orders due to duplicate payments."                                    |
| **Mitigation**       | Fix or workaround.                                                           | "Implement circuit breakers with 3 retries + 1s jitter."                   |
| **Detection**        | How to find it (logs, metrics, tests).                                        | "Monitor `5xx` rate > 5% for 10 mins."                                      |
| **Prevention**       | Proactive measures (e.g., tests, code reviews).                              | "Add chaos engineering tests for retry storms."                             |

---

### **2. Code-Specific Gotcha Checklist**
Use this table to audit code for common pitfalls.

| **Language/Framework** | **Gotcha**                     | **Red Flag Patterns**                          | **Fix**                                                                 |
|------------------------|---------------------------------|-----------------------------------------------|-------------------------------------------------------------------------|
| **Java (Spring)**      | Unbounded Retries               | `RetryTemplate` without `maxAttempts`.         | Set `maxAttempts=3` + `backoff=ExponentialBackoff(100ms, 2)`.            |
| **Python (Django)**    | Race Condition in ORM            | `select_for_update(skip_locked=False)`.        | Use `SERIALIZABLE` isolation or manual locks.                          |
| **Go**                | Resource Leak (SQL DB)          | `*sql.DB` not closed in `defer`.               | Always `defer db.Close()` in `init()` or `defer`.                        |
| **Kubernetes**        | Pod Restart Storm               | `livenessProbe` failure + no `maxUnavailable`. | Set `maxUnavailable: 25%`.                                               |
| **JavaScript (Node)** | Non-Idempotent API Calls        | `POST /pay` without deduplication.            | Use **idempotency keys** or **saga pattern**.                            |

---

## **Query Examples**
Use these **SQL/metric queries** to detect reliability gotchas in production.

### **1. Detecting Unhandled Retry Storms**
```sql
-- Find services with retry spikes (e.g., Spring Retry)
SELECT
  service_name,
  COUNT(*) as retry_count,
  AVG(retry_latency_ms)
FROM retry_attempts
WHERE retry_count > 1000 -- Threshold for "storm"
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY service_name
ORDER BY retry_count DESC;
```

### **2. Identifying Deadlocks (PostgreSQL)**
```sql
-- Find locked transactions causing deadlocks
SELECT
  pid,
  now() - query_start AS duration,
  query
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE locktype = 'transactionid'
  AND NOT l.mode < 'ExclusiveLock'
ORDER BY duration DESC;
```

### **3. Resource Leak Detection (Prometheus)**
```promql
# Find processes leaking open file handles
increase(process_open_fds[5m]) > 1000
and on(instance) process_name =~ "your-service"
```

### **4. Non-Idempotent Operation Alerts**
```sql
-- Duplicate order detections (e.g., same `payment_id` + `user_id`)
SELECT
  payment_id,
  COUNT(*) as duplicates,
  MAX(created_at)
FROM orders
GROUP BY payment_id
HAVING COUNT(*) > 1
ORDER BY duplicates DESC;
```

---

## **Related Patterns**
To mitigate reliability gotchas, combine with these complementary patterns:

| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                              |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevent cascading failures by throttling unhealthy services.               | When dependent services are unreliable (e.g., external APIs).               |
| **Saga Pattern**          | Manage distributed transactions via compensating actions.                  | For long-running workflows (e.g., order processing).                         |
| **Bulkhead**              | Isolate resource contention (e.g., thread pools, DB connections).          | High-concurrency scenarios (e.g., microservices).                            |
| **Exponential Backoff**   | Retry transient failures with increasing delays.                           |When dealing with API timeouts or network partitions.                         |
| **Idempotent Operations** | Ensure safe repeated execution (e.g., `PUT /update`).                     | For retriable or resendable operations (e.g., payments, webhooks).           |
| **Chaos Engineering**     | Proactively test system resilience.                                         | After major deployments or before critical events (e.g., Black Friday).    |
| **Retry with Jitter**     | Avoid thundering herd by randomizing retry delays.                         | For distributed systems (e.g., Redis, databases).                            |

---

## **Best Practices Summary**
1. **Assume nothing will work forever**: Design for **failure modes** (e.g., timeouts, network splits).
2. **Default to defensive programming**:
   - Validate **all** inputs/outputs.
   - Use **immutable objects** where possible.
   - Implement ** circuit breakers** for external calls.
3. **Monitor for anomalies**:
   - Track **retry rates**, **lock contention**, and **resource leaks** proactively.
   - Set **alerts** for sudden spikes in `5xx` errors or latency.
4. **Test reliability**:
   - Use **chaos experiments** (e.g., kill pods randomly).
   - Simulate **network partitions** (e.g., with `chaos mesh`).
5. **Document edge cases**:
   - Add **FAQs** or **runbooks** for known failure scenarios.
   - Update **SLO/SLI** metrics when fixing gotchas.

---
**Final Note**: Reliability gotchas are **everywhere**—even in well-tested systems. Treat them like **technical debt** and prioritize fixes based on impact. Start with **low-hanging fruit** (e.g., resource leaks) before tackling complex distributed issues.