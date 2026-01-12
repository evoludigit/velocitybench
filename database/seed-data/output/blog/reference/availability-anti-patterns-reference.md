---
# **[Anti-Pattern] Availability Pitfalls Reference Guide**

## **Overview**
Availability Anti-Patterns describe common pitfalls in system design that compromise uptime, reliability, and user experience—directly opposing **Availability Best Practices**. These anti-patterns often arise from over-optimization for cost or complexity, leading to cascading failures, single points of failure, or unplanned downtime.

Key anti-patterns include **Resource Hoarding, Thundering Herd, Over-Reliance on Caching, Ignoring Circuit Breakers, and Poor Disaster Recovery Planning**. Each anti-pattern has distinct root causes, symptoms, and mitigation strategies. This guide categorizes them, provides diagnostic criteria (via **Schema Reference**), and offers actionable refactoring examples.

---

## **Availability Anti-Patterns Schema Reference**

| **Anti-Pattern**          | **Description**                                                                                     | **Symptoms**                                                                                     | **Root Causes**                                                                                     | **Mitigation Strategies**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| **Resource Hoarding**     | Over-provisioning critical resources (e.g., databases) to avoid throttling, while under-provisioning less critical ones. | High latency for non-priority users, frequent timeouts for secondary services.                    | Misaligned SLOs, "big bang" scaling, lack of load testing.                                         | Implement **auto-scaling policies**, use **horizontally scalable** architectures (e.g., Kubernetes HPA). |
| **Thundering Herd**       | Sudden spike in requests (e.g., cache invalidation, burst traffic) overwhelming backend systems.      | System crashes, cascading failures, degraded performance.                                           | Poorly optimized caching strategies, no gradual failover.                                          | Use **asynchronous invalidation**, **token bucket** rate limiting, **circuit breakers**.                     |
| **Over-Reliance on Caching** | Treating cache as a primary data layer instead of a secondary optimization, leading to stale data. | Inconsistent user experiences, race conditions during cache updates.                               | Cache invalidation not integrated with data layer writes.                                           | Adopt **eventual consistency**, **TTL-based cache sync**, **write-through caching**.                       |
| **Ignoring Circuit Breakers** | No protection against cascading failures when downstream services fail repeatedly.                   | Uncontrolled retries cause system overload, prolonged outages.                                    | No **resilience patterns** (e.g., retries + backoff, fallback mechanisms).                          | Implement **Hystrix-style circuit breakers**, **bulkheads**, **fallback responses**.                    |
| **Poor Disaster Recovery** | Inadequate backup, failover, or recovery testing, leading to prolonged downtime during outages.      | Extended outages, data loss, slow recovery from failures.                                         | Lack of **daily DR drills**, no multi-region replication, no **chaos engineering**.                   | Use **multi-AZ deployments**, **automated failover**, **backups with TTLs**, **chaos testing tools**.    |
| **Hot Partitioning**      | Uneven load distribution (e.g., all traffic to one shard or region).                                | Overloaded nodes, degraded performance for a subset of users.                                    | Poor **key distribution** (e.g., hashing without partitioning), no **auto-rebalancing**.             | Use **consistent hashing**, **range-partitioning**, **shard rebalancing**.                                |
| **Unbounded Retries**     | Uncontrolled retries on transient failures (e.g., network blips) without backoff.                 | Amplification of failure cascades, resource exhaustion.                                           | No **exponential backoff**, no **jitter**, infinite retry loops.                                     | Use **retry policies** (e.g., retry + delay), **circuit breakers**, **fallback queues**.                 |
| **Single Point of Failure** | Critical components (e.g., API gateways, message brokers) without redundancy.                      | Total system shutdown when a single component fails.                                              | Lack of **redundancy**, **active-active failovers**, no **health checks**.                          | Deploy **multi-instance** services, **active-active databases**, **health probes**.                      |
| **Lazy Initialization**   | Delaying system initialization until runtime, risking cold starts during traffic spikes.             | High latency for first request after idle periods.                                                 | Monolithic startup, no **pre-warming**, **idle-timeout** misconfigurations.                          | Use **graceful degradation**, **pre-warmed instances**, **warm-up requests**.                           |

---

## **Query Examples & Diagnostic Checks**

### **1. Detecting Resource Hoarding**
**Symptom:** `GET /api/orders` returns `503 Service Unavailable` intermittently, while `GET /api/users` is unaffected.
**Schema Check:**
```sql
SELECT service_name, avg_latency_ms, error_rate
FROM system_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY service_name
ORDER BY error_rate DESC;
```
**Mitigation Query (Kubernetes HPA):**
```yaml
resources:
  limits:
    cpu: "1000m"
    memory: "1Gi"
  requests:
    cpu: "200m"
    memory: "500Mi"
autoscale:
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

---

### **2. Thundering Herd Detection**
**Symptom:** Cache invalidation at `T=12:00:00` causes `5xx` errors for 2 minutes.
**Schema Check:**
```sql
SELECT
  cache_key,
  COUNT(*) as invalidation_attempts,
  COUNT(DISTINCT user_id) as affected_users
FROM cache_hits
WHERE timestamp BETWEEN '2023-10-01 12:00:00' AND '2023-10-01 12:05:00'
GROUP BY cache_key;
```
**Mitigation Query (Async Invalidation):**
```javascript
// Using Redis Streams
pubsub.publish('cache:invalidate', JSON.stringify({
  key: 'user:123:profile',
  ttl: 60,
  async: true
}));
```

---

### **3. Circuit Breaker Failure**
**Symptom:** `POST /api/payment` fails with `504` for 10 minutes after `payments-service` crashes.
**Schema Check:**
```sql
SELECT
  failure_reason,
  COUNT(*) as failures,
  COUNT(DISTINCT call_id) as unique_calls
FROM circuit_breaker_logs
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY failure_reason
ORDER BY failures DESC;
```
**Mitigation Query (Hystrix-Style):**
```java
@HystrixCommand(fallbackMethod = "fallbackPayment")
public ResponseEntity<PaymentResponse> processPayment(PaymentRequest request) {
  // Business logic
}

public ResponseEntity<PaymentResponse> fallbackPayment(PaymentRequest request) {
  return ResponseEntity.ok(new PaymentResponse("Sandbox Mode: Payment failed."));
}
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Dynamically disable failing dependencies to prevent cascading failures.                             | When downstream services exhibit **transient or persistent failures**.                               |
| **Bulkhead**              | Isolate failure domains by limiting concurrent requests per thread pool.                            | To **prevent resource exhaustion** during spikes.                                                   |
| **Retry with Backoff**    | Exponentially delay retries to reduce load on recovering systems.                                   | For **idempotent operations** (e.g., database writes) with retriable errors.                        |
| **Multi-Region Deployment** | Deploy services across regions with automated failover.                                             | For **global low-latency** and **disaster recovery**.                                               |
| **Eventual Consistency**  | Accept temporary data inconsistencies for faster writes/reads.                                       | When **strong consistency is not critical** (e.g., user profiles vs. financial transactions).         |
| **Chaos Engineering**     | Proactively test system resilience by injecting failures.                                          | To **validate failure recovery** before real incidents occur.                                       |

---

## **Key Takeaways**
1. **Monitor Proactively:** Use metrics (latency, error rates, throughput) to detect anti-patterns early.
2. **Fail Fast, Recover Gracefully:** Implement **circuit breakers** and **fallbacks** to isolate failures.
3. **Avoid Monoliths:** Decouple services with **asynchronous processing** (e.g., queues, event sourcing).
4. **Test Resilience:** Run **chaos experiments** (e.g., kill random pods) to validate recovery.
5. **Document SLIs/SLOs:** Align teams on **availability targets** (e.g., 99.9% uptime for critical APIs).

---
**Further Reading:**
- [Resilience Patterns (Microsoft)](https://docs.microsoft.com/en-us/azure/architecture/patterns/)
- [Chaos Engineering by Netflix](https://netflixtechblog.com/)
- [Kubernetes Best Practices for High Availability](https://kubernetes.io/docs/concepts/cluster-administration/)