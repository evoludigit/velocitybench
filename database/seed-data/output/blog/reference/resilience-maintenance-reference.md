# **[Pattern] Resilience Maintenance Reference Guide**

---

## **Overview**
The **Resilience Maintenance** pattern ensures systems remain operational despite failures, degradations, or unexpected load surges. This pattern integrates **retry mechanisms**, **circuit breakers**, **fallbacks**, **rate limiting**, and **self-healing** to mitigate disruptions while maintaining minimal service degradation. Unlike reactive recovery, resilience maintenance is **proactive**, continuously adapting to failures, throttling dependencies, and optimizing resource usage for sustained availability.

Key use cases include:
- **Microservices architectures** (to isolate failures in dependent services).
- **Cloud-native applications** (handling transient infrastructure failures).
- **High-availability systems** (minimizing downtime during cascading failures).
- **IoT/edge systems** (where network partitions or sensor failures occur frequently).

This pattern does not replace traditional error handling but **complements** it by applying resilience strategies at the **strategic** (architectural), **tactical** (implementation), and **operational** (runtime monitoring) levels.

---

## **Schema Reference**
Below is a structured schema defining core components of the **Resilience Maintenance** pattern:

| **Component**               | **Description**                                                                                                                                                                                                 | **Attributes**                                                                                                                                                                                                                                                                                   |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**         | Prevents cascading failures by stopping requests to a failing service after a threshold of failures, then retries periodically after recovery.                                                           | - `FailureThreshold` (e.g., 5 failures in 30s)<br>- `ResetTimeout` (e.g., 1 minute)<br>- `Half-Open Testing` (number of allowed requests post-reset)<br>- `FallbackBehavior` (e.g., return cached data, degrade gracefully)                                                  |
| **Retry Policy**            | Configures how many times and under what conditions a failed request is retried (exponential backoff, fixed delay, jitter).                                                                                 | - `MaxRetries` (e.g., 3)<br>- `InitialDelay` (e.g., 100ms)<br>- `BackoffFactor` (e.g., 2.0 for exponential)<br>- `MaxDelay` (e.g., 10s)<br>- `RetryOn` (e.g., `TransientError`, `Timeout`, `RateLimitExceeded`)                                               |
| **Fallback Mechanism**      | Provides a substitute response when the primary service fails (e.g., cached data, default values, or degraded functionality).                                                                                   | - `FallbackType` (e.g., `Cache`, `MockResponse`, `DegradedUI`)<br>- `CacheTTL` (e.g., 5 minutes)<br>- `Priority` (e.g., `High` for critical services)<br>- `FallbackDataSource` (e.g., backup DB, static config)                                               |
| **Rate Limiter**            | Controls the request volume to a dependent service to prevent overload (e.g., token bucket, sliding window).                                                                                               | - `Rate` (e.g., 100 requests/sec)<br>- `BurstCapacity` (e.g., 50 requests)<br>- `QueueTimeout` (e.g., 100ms)<br>- `RejectionBehavior` (e.g., `HTTP 429`, `ThrottleAndRetry`)                                                                                     |
| **Self-Healing Logic**      | Automatically restores failed components (e.g., restarting containers, rescheduling tasks, or repairing connections) without manual intervention.                                                            | - `DetectionThreshold` (e.g., 3 consecutive failures)<br>- `HealingAction` (e.g., `RestartPod`, `Reconnect`, `RollbackVersion`)<br>- `CooldownPeriod` (e.g., 1 hour)<br>- `LoggingLevel` (e.g., `WARN`, `ERROR`)                                                          |
| **Monitoring & Alerts**     | Tracks resilience metrics (e.g., failure rates, retry success) and triggers alerts for proactive intervention.                                                                                              | - `MetricsExposed` (e.g., Prometheus, Datadog)<br>- `AlertThresholds` (e.g., `>5% failure rate`)<br>- `NotificationChannels` (e.g., Slack, PagerDuty)<br>- `AnomalyDetection` (e.g., `UnexpectedLatency`, `CircuitOpenDuration`)                         |
| **Dependency Isolation**    | Logically separates critical and non-critical dependencies to limit blast radius.                                                                                                                          | - `DependencyTier` (e.g., `Critical`, `Secondary`, `Optional`)<br>- `IsolationStrategy` (e.g., `Service Mesh`, `API Gateway`)<br>- `FallbackPriority` (e.g., `Critical > Secondary`)                                                                                     |

---

## **Implementation Details**
### **1. Circuit Breaker**
Prevents cascading failures by stopping calls to a failing dependency after a threshold.

**Key Strategies:**
- **State Management**: Tracks failures in `Closed` (normal), `Open` (failed), and `Half-Open` (testing) states.
- **Reset Mechanism**: Automatically closes the circuit after `ResetTimeout` or manual intervention.
- **Fallback Integration**: Returns cached/degraded data while the circuit is open.

**Example (Java with Hystrix):**
```java
@HystrixCommand(
    fallbackMethod = "fallbackMethod",
    circuitBreakerRequestVolumeThreshold = 10,
    circuitBreakerErrorThresholdPercentage = 50,
    circuitBreakerSleepWindowInMilliseconds = 5000
)
public String callExternalService() {
    return externalService.getData();
}

public String fallbackMethod() {
    return "Service degraded. Returning cached data.";
}
```

---

### **2. Retry Policy**
Configures retry attempts with backoff to avoid overwhelming failed services.

**Best Practices:**
- **Exponential Backoff**: Wait longer between retries (e.g., 100ms → 200ms → 400ms).
- **Jitter**: Adds randomness to prevent thundering herd (e.g., `100ms ± 50ms`).
- **Conditional Retries**: Retry only on transient errors (e.g., `5xx`, timeouts).

**Example (Python with Tenacity):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_api():
    response = requests.get("https://api.example.com")
    if response.status_code == 500:
        raise requests.exceptions.HTTPError("Server error")
    return response.json()
```

---

### **3. Fallback Mechanism**
Provides alternative responses when primary services fail.

**Types:**
- **Static Fallback**: Return hardcoded data (e.g., `"Service Unavailable"`).
- **Dynamic Fallback**: Query a backup service (e.g., read from a secondary DB).
- **Degraded UI**: Show simplified functionality (e.g., hide optional features).

**Example (Go with Context Timeout):**
```go
func callWithFallback(ctx context.Context, url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
    defer cancel()

    resp, err := http.Get(url)
    if err != nil || resp.StatusCode != http.StatusOK {
        // Fallback: Return cached data
        return fallbackData, nil
    }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}
```

---

### **4. Rate Limiting**
Prevents resource exhaustion by limiting request rates.

**Algorithms:**
- **Token Bucket**: Allows bursts up to a capacity (e.g., 100 tokens/sec, 50-capacity bucket).
- **Sliding Window**: Tracks requests over a fixed window (e.g., 60s).

**Example (Node.js with `rate-limiter-flexible`):**
```javascript
const { RateLimiterMemory } = require("rate-limiter-flexible");

const limiter = new RateLimiterMemory({
    points: 100,       // 100 requests
    duration: 60,      // per 60 seconds
});

async function processRequest() {
    try {
        await limiter.consume("api_key");
        const response = await fetchExternalService();
        return response;
    } catch (err) {
        return { error: "Rate limit exceeded" };
    }
}
```

---

### **5. Self-Healing**
Automatically recovers from failures without manual intervention.

**Actions:**
- **Restart Failed Pods**: Kubernetes `livenessProbe` + horizontal pod autoscaler.
- **Reconnect to DB**: Exponential backoff in connection pooling.
- **Rollback to Stable Version**: GitOps (e.g., ArgoCD) or feature flags.

**Example (Kubernetes Liveness Probe):**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

---

### **6. Monitoring & Alerts**
Tracks resilience metrics and triggers alerts.

**Key Metrics:**
- `FailureRate` (% of failed requests).
- `CircuitOpenDuration` (time circuits stay open).
- `RetrySuccessRate` (% of retries that succeed).
- `LatencyP99` (99th percentile response time).

**Example (Prometheus + Alertmanager):**
```yaml
# prometheus_rules.yml
groups:
- name: resilience-alerts
  rules:
  - alert: HighFailureRate
    expr: rate(failed_requests_total[5m]) > 0.05
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High failure rate in {{ $labels.service }}"
```

---

## **Query Examples**
### **1. Circuit Breaker State Query**
**Objective**: Check if a circuit is open and how long it will stay open.
**Tools**: Prometheus (`hystrix.stream` for Hystrix, `resilience4j-circuitbreaker` metrics).

**Query**:
```promql
# Circuit open duration (Resilience4j)
resilience4j_circuitbreaker_state_changes_total{state="OPEN"} > 0
```
**Expected Output**:
```
resilience4j_circuitbreaker_state_changes_total{state="OPEN"} 1
```

---

### **2. Retry Success Rate Analysis**
**Objective**: Calculate % of retries that succeeded.
**Tools**: Custom metrics or APM tools (e.g., Datadog).

**SQL (PostgreSQL)**:
```sql
SELECT
    COUNT(*) AS total_retries,
    SUM(CASE WHEN retry_success = true THEN 1 ELSE 0 END) AS successful_retries,
    ROUND(SUM(CASE WHEN retry_success = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate
FROM retry_attempts
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

---

### **3. Rate Limiter Rejection Rate**
**Objective**: Identify if rate limits are being hit.
**Tools**: APM (New Relic) or custom logging.

** ELK Query (Kibana)**:
```
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event.type": "rate_limiter_rejected" } },
        { "range": { "@timestamp": { "gte": "now-1h", "lte": "now" } } }
      ]
    }
  }
}
```

---

## **Related Patterns**
1. **Bulkhead Pattern**
   - *Relationship*: Both isolate failures, but Bulkhead limits concurrent executions (thread pools), while Resilience Maintenance focuses on recovery strategies.
   - *When to Use*: Combine them to create thread pools with circuit breakers (e.g., `Bulkhead + Circuit Breaker`).

2. **Retry Pattern**
   - *Relationship*: Retry is a sub-component of Resilience Maintenance, but this pattern can be used standalone for transient errors.
   - *When to Use*: Use Retry alone for simple transient failures; integrate it with Circuit Breakers for complex scenarios.

3. **Fallback Pattern**
   - *Relationship*: Fallback is a critical fallback for Resilience Maintenance but can be used independently (e.g., offline modes).
   - *When to Use*: Pair Fallback with Circuit Breakers to ensure graceful degradation.

4. **Circuit Breaker Pattern**
   - *Relationship*: Core to Resilience Maintenance; defines failure thresholds and recovery logic.
   - *When to Use*: Implement as the first line of defense in dependency calls.

5. **Rate Limiting Pattern**
   - *Relationship*: Prevents failures by controlling load; often used with Circuit Breakers to avoid cascading issues.
   - *When to Use*: Deploy before Circuit Breakers to mitigate overload conditions.

6. **Chaos Engineering**
   - *Relationship*: Proactively tests Resilience Maintenance by injecting failures.
   - *When to Use*: Validate resilience strategies with tools like Gremlin or Chaos Mesh.

7. **Saga Pattern**
   - *Relationship*: Handles distributed transactions; Resilience Maintenance ensures individual steps in a Saga recover gracefully.
   - *When to Use*: Use Saga for workflows and Resilience Maintenance for their components.

---

## **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                 | **Mitigation**                                                                 |
|---------------------------------|--------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Unbounded Retries**           | Infinite loops during permanent failures (e.g., DB gone).               | Set `MaxRetries` and use Circuit Breakers.                                   |
| **No Fallback for Critical Paths** | Complete service outage if primary fails.                          | Always define fallbacks for critical dependencies.                           |
| **Ignoring Circuit Breaker State** | Re-routing traffic to failing services.                                | Monitor `circuit_open` metrics and defer requests.                          |
| **Rate Limiting Without Graceful Degradation** | Silent failures or 429 errors without user feedback.             | Return fallback responses + retry logic.                                     |
| **Static Retry Delays**         | Thundering herd during recovery (all clients retry at once).           | Add jitter (`wait=wait_random_exponential`).                                |
| **Over-reliance on Monitoring** | Alert fatigue from too many false positives.                          | Set adaptive thresholds (e.g., anomaly detection).                          |

---
## **Tooling Ecosystem**
| **Tool**                  | **Purpose**                                                                 | **Language Support**                     | **Key Features**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------|---------------------------------------------------------------------------------|
| **Resilience4j**          | Circuit Breaker, Retry, Rate Limiter, Bulkhead.                            | Java/Kotlin                               | Lightweight, integration with Spring Boot.                                     |
| **Hystrix**               | Circuit Breaker, Fallback, Metrics.                                         | Java                                      | Part of Netflix OSS (now superseded by Resilience4j).                        |
| **Polly (Microsoft)**     | Retry, Circuit Breaker, Timeout.                                            | .NET, C#                                  | Exponential backoff, jitter, and fallback policies.                             |
| **Tenacity (Python)**     | Retry with advanced policies (exponential, stop conditions).                 | Python                                    | Plugin-based (e.g., `tenacity-asyncio`).                                      |
| **Istio**                 | Service Mesh for Resilience (Circuit Breaker, Retry, Rate Limiting).      | Multi-language                            | Envoy-sidecar integration, fine-grained traffic control.                       |
| **Linkerd**               | Lightweight service mesh with resilience features.                         | Multi-language                            | Automatic retries, circuit breaking, and failure detection.                   |
| **Retry (Node.js)**       | Retry library with jitter and backoff.                                     | JavaScript/TypeScript                     | `retry-axios`, `p-retry`.                                                     |
| **Chaos Mesh**            | Inject failures to test Resilience Maintenance.                             | Multi-language (Kubernetes-native)       | Pod/container kills, network partitions, latency injection.                    |

---
## **Best Practices**
1. **Prioritize Dependencies**:
   - Tag dependencies by criticality (`Critical`, `Secondary`, `Optional`).
   - Use stricter resilience (e.g., Circuit Breakers) for critical dependencies.

2. **Monitor & Optimize**:
   - Track `failure_rate`, `retry_success`, and `circuit_open_duration`.
   - Adjust thresholds based on SLOs (e.g., `P99 latency < 500ms`).

3. **Combine Patterns**:
   - **Circuit Breaker + Retry**: Retry on transient failures; break on permanent.
   - **Bulkhead + Rate Limiter**: Limit concurrency *and* request rate.

4. **Test Resilience**:
   - Use **Chaos Engineering** (e.g., kill pods, inject latency).
   - Simulate failures in staging (e.g., `chaos-mesh`).

5. **Document Fallbacks**:
   - Clearly define fallback behavior for each dependency.
   - Example:
     ```markdown
     | Dependency | Fallback Strategy          | Priority |
     |------------|---------------------------|----------|
     | DB Primary | Read from Replica         | High     |
     | External API | Return cached response   | Medium   |
     ```

6. **Graceful Degradation**:
   - Hide failed components behind feature flags (e.g., disable non-critical UI elements).

7. **Avoid Over-Engineering**:
   - Start with simple retries for transient errors.
   - Only add Circuit Breakers/Rate Limiting if failures are recurrent.

---
## **Troubleshooting**
| **Issue**                          | **Likely Cause**                          | **Debugging Steps**                                                                 | **Resolution**                                                                 |
|------------------------------------|------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **High Failure Rate**              | Dependency failing intermittently.      | Check logs (`failed_requests_total` in Prometheus).                                | Add Retry + Circuit Breaker.                                                 |
| **Circuit Never Closes**           | `ResetTimeout` too long or manual reset missed. | Inspect circuit state (`resilience4j_circuitbreaker_state`).                     | Reduce `ResetTimeout` or reset manually.                                      |
| **Thundering Herd on Recovery**    | All clients retry simultaneously.       | Enable jitter in retry policy.                                                     | Use `wait=wait_random_exponential` (Tenacity) or `backoff_jitter` (Resilience4j). |
| **Rate Limiter Too Aggressive**    | False positives blocking legitimate traffic. | Review `rate` and `burstCapacity` settings