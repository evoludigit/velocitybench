**[Pattern] Resilience Approaches Reference Guide**

---
### **Overview**
The **Resilience Approaches** pattern defines methods to build systems that gracefully handle failures, recover from disruptions, and maintain functionality under adverse conditions. Resilience ensures high availability, reliability, and performance by mitigating risks such as hardware faults, network latency, cascading failures, or external dependencies. This pattern focuses on **key strategies** (e.g., redundancy, circuit breaking, retries, and fallback mechanisms) and **best-practice implementations** across distributed systems, microservices, and monolithic applications.

Implementing resilience improves system robustness, reduces downtime, and enhances user experience. It aligns with devops and site reliability engineering (SRE) principles while addressing common challenges like transient faults and operational failures.

---
### **Implementation Details**

#### **1. Key Strategies**
| **Strategy**           | **Description**                                                                                     | **Use Case**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Redundancy**         | Deploy multiple instances of components/services to replace failed ones.                           | High-availability databases, load balancers, or critical API endpoints.                        |
| **Circuit Breaker**    | Stops cascading failures by halting requests to a failing service until it recovers.                | External API calls, third-party dependencies (e.g., payment gateways).                         |
| **Retries with Backoff** | Automatically retransmits failed requests with exponential delays to reduce load on faulty systems. | Transient network errors (e.g., DB timeouts).                                                 |
| **Fallback Mechanisms** | Provides degraded or cached responses when primary services are unavailable.                       | Personalized recommendations → fall back to static content.                                    |
| **Bulkheads**          | Isolates failures in one component from affecting others (e.g., thread pools, queues).               | Preventing a single API call from crashing the entire application.                             |
| **Rate Limiting**      | Controls request volume to avoid overloads and throttles abusive traffic.                           | Preventing DDoS attacks or resource exhaustion.                                                 |
| **Graceful Degradation**| Reduces functionality rather than crashing when under heavy load.                                  | Disabling non-critical features during peak traffic.                                          |
| **Chaos Engineering**  | Proactively tests system resilience by injecting failures (e.g., killing pods, simulating latency). | Improving recovery time objectives (RTOs) and identifying weaknesses.                          |

---

#### **2. Schema Reference**
Resilience configurations often involve **configurable rules** (e.g., retry limits, timeout values). Below are common schema examples:

| **Component**       | **Field**               | **Type**       | **Description**                                                                               | **Example**                          |
|---------------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------|--------------------------------------|
| **Circuit Breaker** | `maxFailures`           | `int`          | Maximum allowed failures before tripping.                                                    | `5`                                  |
|                     | `timeoutMs`             | `int`          | Time (ms) to wait before retrying.                                                          | `1000`                               |
|                     | `resetTimeoutMs`        | `int`          | Duration (ms) before resetting the circuit breaker.                                         | `30000`                              |
| **Retry Policy**    | `maxRetries`            | `int`          | Maximum number of retry attempts.                                                           | `3`                                  |
|                     | `exponentialBackoff`    | `bool`         | Enable exponential backoff between retries.                                                  | `true`                               |
|                     | `baseDelayMs`           | `int`          | Base delay (ms) for exponential backoff.                                                     | `100`                                |
| **Bulkhead**        | `maxConcurrentRequests` | `int`          | Maximum concurrent requests allowed.                                                         | `10`                                 |
| **Rate Limiter**    | `tokensPerSecond`       | `float`        | Tokens refilled per second (bucket rate).                                                    | `100`                                |
|                     | `burstCapacity`         | `int`          | Maximum tokens allowed in the bucket.                                                        | `200`                                |

---
#### **3. Query Examples**
Resilience patterns often interact with **infrastructure tools** (e.g., Prometheus, Kubernetes) or **logging systems**. Below are practical use cases:

##### **A. Circuit Breaker Trip Detection (PromQL)**
```promql
# Alert when circuit breaker trips (e.g., in Istio)
up{circuit_breaker_tripped="true"} == 1
```
**Mitigation:** Check logs for affected services and manually reset the breaker (if allowed) or configure auto-reset via `resetTimeoutMs`.

##### **B. Retry Policy Configuration (Envoy Filter)**
Configure retries in an **Envoy proxy** for outbound HTTP calls:
```yaml
static_resources:
  listeners:
    - name: listener_0
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                route_config:
                  virtual_hosts:
                    - name: local_service
                      routes:
                        - match: { prefix: "/" }
                          retry_policy:
                            retry_on: gateway-error,connect-failure,refused-stream
                            retries: 3
                            pertry_timeout: 2s
                            retry_duration: 10s
                            host_matching_strategy: prefix
```

##### **C. Bulkhead Enforcement (Spring Retry)**
Use Spring Retry to limit concurrent executions:
```java
@Retryable(value = TimeoutException.class, maxAttempts = 3, backoff = @Backoff(delay = 1000))
@RateLimiter(limit = 5, timeUnit = TimeUnit.MINUTES)
public void processOrder(Order order) {
    // Business logic
}
```

##### **D. Chaos Experiment (Gremlin/YAML)**
Test resilience by **killing pods** in Kubernetes:
```bash
kubectl delete pod <pod-name> --grace-period=0 --force
```
**Verify:** Check logs and metrics for auto-recovery (e.g., via Prometheus alerts).

---
#### **4. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                               |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Retry as a Service**    | Centralized retry logic (e.g., AWS SQS retry queues) instead of client-side handling.               | Decoupled microservices with transient failures.                                             |
| **Saga Pattern**          | Manages distributed transactions by coordinating local transactions via compensating actions.      | Long-running workflows with multiple services (e.g., order processing).                   |
| **Circuit Breaker as a Service** | Externalized circuit breakers (e.g., Netflix Hystrix, Linkerd).                              | Large-scale systems needing centralized monitoring.                                           |
| **Resilient Messaging**   | Ensures message delivery even if consumers fail (e.g., Kafka retries, dead-letter queues).      | Event-driven architectures with unreliable consumers.                                      |
| **Health Checks**         | Regular probes to detect unhealthy services (e.g., Kubernetes liveness/readiness probes).       | Auto-scaling and failover scenarios.                                                        |
| **Chaos Mesh**            | Kubernetes-native chaos engineering tool for injecting failures.                                  | Proactively testing resilience in production-like environments.                              |

---
### **Best Practices**
1. **Monitor Resilience Metrics**:
   - Track circuit breaker trips, retry failures, and bulkhead saturation.
   - Tools: Prometheus, Grafana, Datadog.

2. **Balance Aggressiveness**:
   - Too many retries can exacerbated failures; align with SLAs (e.g., `maxRetries` based on RTO).

3. **Testing**:
   - **Unit Tests**: Mock failures (e.g., `Mockito.when(service.call()).thenThrow(new TimeoutException())`).
   - **Chaos Testing**: Use tools like [Gremlin](https://www.gremlin.com/) or [Chaos Mesh](https://chaos-mesh.org/).

4. **Circuit Breaker Tuning**:
   - Start with conservative settings (e.g., `maxFailures=3`) and adjust based on failure patterns.

5. **Fallbacks Should Be UX-Friendly**:
   - Provide clear messages (e.g., "We’re experiencing high traffic; try again later").

---
### **Antipatterns**
| **Antipattern**               | **Risk**                                                                                             | **Solution**                                                                                  |
|-------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Silent Retries**            | Retries mask underlying issues (e.g., data corruption) without alerting.                           | Log retries and set up alerts for repeated failures.                                       |
| **Unlimited Retries**         | Infinite loops degrade performance and waste resources.                                             | Enforce `maxRetries` and use exponential backoff.                                           |
| **Ignoring Circuit Breaker**   | Overriding breakers leads to cascading failures.                                                   | Use `@CommonsRetryable` annotations or config flags to enforce breakers.                     |
| **No Fallback for Critical Paths** | System crashes when primary services fail.                                                      | Implement **degraded modes** (e.g., cache-only responses).                                   |
| **Over-Provisioning**         | Redundancy without cost/performance trade-offs.                                                     | Right-size bulkheads and replicas based on workload analysis.                               |