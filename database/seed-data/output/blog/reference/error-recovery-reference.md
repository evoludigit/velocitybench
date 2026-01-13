# **[Pattern] Error Recovery Strategies – Reference Guide**

---

## **Overview**
Error Recovery Strategies is a **resilience pattern** designed to minimize the impact of failures in distributed systems, microservices, and cloud-native applications. When faults occur—such as network timeouts, service unavailability, or data corruption—this pattern ensures graceful degradation, retries with exponential backoff, fallback mechanisms, and automatic recovery.

Unlike reactive patterns (e.g., Circuit Breaker) or compensating actions (e.g., Saga), Error Recovery Strategies focus on **post-failure mitigation** by:
- **Detecting** failures via health checks or monitoring.
- **Resolving** them through retries, backpressure, or manual intervention.
- **Recovering** system state, logs, or dependent services.
- **Preventing** cascading failures via isolation and circuit breakers.

Best suited for **stateless or idempotent operations**, it integrates with **retry policies**, **fallback services**, and **dead-letter queues (DLQ)** to ensure durability.

---

## **Schema Reference**
Below are core components and their relationships in an **Error Recovery Strategies** implementation.

| **Component**               | **Description**                                                                                     | **Attributes**                                                                                     | **Example Values**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Failure Detector**        | Identifies failures (timeouts, exceptions, 5XX errors)                                             | - Detection Threshold (ms) <br> - Monitoring Endpoint <br> - Health Check Interval             | `timeout: 5000ms`, `healthCheckURL: /actuator/health`                               |
| **Retry Policy**            | Defines retry attempts, backoff, and jitter                                                           | - Max Retries (`int`) <br> - Initial Backoff (`ms`) <br> - Max Backoff (`ms`) <br> - Jitter Type (`exponential/constant`) | `maxRetries: 3`, `initialBackoff: 100`, `maxBackoff: 2000`, `jitter: exponential` |
| **Fallback Mechanism**      | Provides alternative behavior if primary fails                                                      | - Fallback Service Endpoint <br> - Priority Order <br> - Timeout (ms)                              | `fallbackURL: /api/backup-service`, `timeout: 3000`                                |
| **Dead Letter Queue (DLQ)** | Stores failed messages/events for later analysis                                                     | - Queue Type (`RabbitMQ/Kafka`) <br> - TTL (`days`) <br> - Retry Count (`int`)                  | `queue: failed-orders`, `ttl: 30`, `maxRetries: 2`                                |
| **Circuit Breaker**         | Prevents cascading failures by stopping retries after threshold                                    | - Failure Threshold (`%`) <br> - Reset Timeout (`ms`) <br> - State (`OPEN/CLOSED/HALF_OPEN`)    | `threshold: 50%`, `resetTimeout: 30000`, `state: OPEN`                               |
| **Recovery Handler**        | Executes cleanup or compensation logic post-recovery                                                | - Script/Function Name <br> - Input Parameters <br> - Output Log Location                      | `handler: "cleanupCache.sh"`, `params: { key: "cache-invalidated" }`               |
| **Monitoring & Alerts**     | Tracks recovery metrics and triggers alerts for SLO violations                                        | - Alert Threshold (`%`) <br> - Notification Channels (`Email/SMS`) <br> - Dashboard Integrations | `threshold: 99.9%`, `channels: ["slack", "pagerduty"]`                             |

---

## **Implementation Details**
### **1. Failure Detection**
Use **active health checks** (e.g., `/health` endpoints) or **passive monitoring** (e.g., metrics from Prometheus).
- **Example Trigger**:
  ```java
  if (requestTimeout > failureThreshold) {
      failureDetector.record(FailureType.TIMEOUT);
  }
  ```

### **2. Retry Strategy**
Implement **exponential backoff with jitter** to avoid thundering herds:
```python
retry_count = 0
while retry_count < max_retries:
    try:
        response = call_service(timeout=5000)
        break
    except TimeoutError:
        retry_count += 1
        delay = min(initial_backoff * (2 ** retry_count), max_backoff)
        time.sleep(delay + random.uniform(0, jitter))
```

### **3. Fallback Mechanisms**
- **Caching**: Serve stale data (e.g., Redis).
- **Alternate Services**: Route to a backup API (e.g., `/v2` instead of `/v1`).
- **Graceful Degradation**: Skip non-critical operations (e.g., analytics during peak load).

### **4. Dead Letter Queues (DLQ)**
Configure a DLQ in message brokers (e.g., Kafka, SQS) to store failed events for later analysis:
```yaml
# Kafka Consumer Config
enable.auto.commit=false
max.poll.interval.ms=300000
max.poll.records=500
```

### **5. Circuit Breaker Integration**
Use libraries like **Resilience4j** or **Hystrix** to enforce limits:
```java
CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("paymentService");
Supplier<Payment> paymentSupplier = () -> circuitBreaker.executeSupplier(() -> callPaymentAPI());
```

### **6. Recovery Handlers**
Automate post-recovery actions (e.g., database cleanup, SLA alerts):
```bash
#!/bin/bash
# cleanup.sh
aws s3 rm s3://failed-events/ --recursive
notify-slack "Recovery complete: Events deleted."
```

### **7. Observability**
- **Metrics**: Track `failedRequests`, `retryAttempts`, `fallbackSuccess`.
- **Logs**: Correlate failures with traces (e.g., OpenTelemetry).
- **Alerts**: Set up alerts for `retryCount > threshold`.

---

## **Query Examples**
### **1. Detecting Failures with Prometheus**
```promql
# Failed requests rate (last 5m)
rate(http_requests_total{status=~"5.."}[5m]) by (service)
```

### **2. Retry Policy in Terraform**
```hcl
resource "aws_lambda_function" "order_processor" {
  environment {
    variables = {
      MAX_RETRIES = "3"
      INITIAL_BACKOFF = "1000"
    }
  }
}
```

### **3. Fallback Endpoint in OpenAPI**
```yaml
paths:
  /checkout:
    post:
      servers:
        - url: https://api.example.com/v1
        - url: https://api.example.com/v2  # Fallback
      responses:
        "200":
          description: Success
        "503":
          description: Service Unavailable → Redirect to v2
```

### **4. DLQ Consumer in Python (Kafka)**
```python
from confluent_kafka import Consumer

conf = {'bootstrap.servers': 'kafka:9092', 'group.id': 'dlq-group'}
consumer = Consumer(conf)
consumer.subscribe(['failed-orders'])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg.error():
        print(f"Failed to consume: {msg.error()}")
    else:
        process_failed_order(msg.value())
```

---

## **Best Practices**
1. **Idempotency**: Ensure retries don’t cause duplicate side effects (e.g., `PUT` over `POST`).
2. **Timeouts**: Set **short** timeouts (e.g., 1–5s) to fail fast.
3. **Metrics First**: Instrument all recovery paths before writing code.
4. **Limit Retries**: Avoid infinite loops (e.g., `maxRetries: 3`).
5. **Fallback Testing**: Validate fallback services in staging.
6. **Circuit Breaker Thresholds**: Tune `failureThreshold` to avoid over/under-breaking (e.g., 50%).
7. **DLQ TTL**: Delete old entries to prevent queue bloat (e.g., `ttl: 7 days`).

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use Together**                                  |
|---------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures during retries                                        | Use alongside `Error Recovery` to avoid thrashing.        |
| **Bulkhead**              | Limits concurrent retries to prevent overload                                       | Deploy in high-contention scenarios (e.g., payment APIs). |
| **Retry with Backoff**    | Core mechanism for transient failures                                             | Essential for network-dependent operations.               |
| **Saga**                  | Manages distributed transactions after failures                                   | Recover from partial failures in microservices.          |
| **Bulkhead**              | Isolates failures to prevent resource exhaustion                                   | Pair with retries to avoid overwhelming a service.        |
| **Compensating Transactions** | Rolls back changes if recovery fails                                            | Use for critical financial operations.                   |
| **Rate Limiting**         | Controls fallback service load                                                     | Protect fallback endpoints from abuse.                   |

---

## **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│  Client     │───▶│  API Gateway│───▶│   Service A     │
└─────────────┘    └─────────────┘    └─────────────────┘
                                        ▲               ▲
                                        │               ▼
                                        │   ┌─────────────┐
                                        │   │  Retry      │
                                        │   │  (Exponential│
                                        │   │   Backoff)   │
                                        │   └─────────────┘
                                        │               ▲
                                        │               ▼
                                        └───────────────▶┐
                                                        ▼
                                              ┌─────────────┐
                                              │  Fallback   │
                                              │  Service B   │
                                              └─────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────┐
                                              │  DLQ        │
                                              │  (Failed Events)│
                                              └─────────────┘
```

---
**References**:
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Kubernetes Retry Policies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#retry-policy)
- [AWS Well-Architected: Reliability](https://aws.amazon.com/architecture/well-architected/reliability/)