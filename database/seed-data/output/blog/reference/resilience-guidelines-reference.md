# **[Pattern] Resilience Guidelines Reference Guide**

---

## **Overview**
Resilience Guidelines define best practices, thresholds, and fallback behaviors that systems should adhere to when handling failures, network partitions, or unexpected conditions. These guidelines ensure graceful degradation, prevent cascading failures, and maintain system stability under adverse conditions. This reference covers key concepts, implementation schemas, query patterns, and related resilience patterns for designing robust microservices, distributed systems, or cloud-native applications.

Resilience Guidelines can be documented in:
- **API contracts** (e.g., OpenAPI/Swagger specs)
- **Infrastructure-as-Code (IaC)** (e.g., Terraform, Kubernetes manifests)
- **Deployment policies** (e.g., Kubernetes Horizontal Pod Autoscaler rules)
- **Configuration files** (e.g., `resilience4j.yml`, `configmaps`)

---

## **Implementation Details**

### **Key Concepts**
| Concept               | Description                                                                                     | Example Use Case                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Fallback Behavior** | Defines what the system should do when a primary operation fails (e.g., retry, degrade).        | If payment gateway fails, use a backup gateway.                                  |
| **Circuit Breaker**   | Stops cascading failures by tripping after repeated errors.                                     | Stop calling a flaky third-party API after 5 failures.                           |
| **Rate Limiting**     | Controls request volume to prevent overload.                                                   | Throttle API requests during traffic spikes.                                    |
| **Timeouts**          | Limits how long an operation can run before being aborted.                                     | Timeout database queries after 2s to prevent hanging.                            |
| **Retries**           | Automatically reattempt failed operations with backoff.                                        | Retry failed HTTP calls with exponential delay.                                 |
| **Bulkheads**         | Isolate resource-heavy operations to prevent system-wide disruptions.                          | Run analytics jobs in separate containers.                                       |
| **Degradation**       | Reduces functionality under stress (e.g., disable non-critical features).                       | Disable user profile generation during peak load.                               |
| **Monitoring Thresholds** | Defines metrics (e.g., error rate, latency) that trigger alerts or adjustments.          | Alert if API error rate exceeds 1% for 5 minutes.                                |

---

## **Schema Reference**
Below are common schema structures for defining **Resilience Guidelines** in APIs, infrastructure, or code.

---

### **1. API Contract (OpenAPI/Swagger)**
```yaml
openapi: 3.0.0
info:
  title: "Order Service - Resilience Guidelines"
  version: "1.0.0"
components:
  schemas:
    ResilienceConfig:
      type: object
      properties:
        circuitBreaker:
          type: object
          properties:
            enabled: { type: boolean, default: true }
            failureThreshold: { type: integer, example: 5 }
            resetTimeout: { type: string, format: duration, example: "30s" }
        retry:
          type: object
          properties:
            maxAttempts: { type: integer, example: 3 }
            backoff:
              type: object
              properties:
                initialInterval: { type: string, format: duration, example: "100ms" }
                multiplier: { type: number, example: 2.0 }
                maxInterval: { type: string, format: duration, example: "10s" }
        timeout:
          type: string
          format: duration
          example: "5s"
        fallback:
          type: string
          description: "URL or fallback behavior (e.g., 'degraded_mode')"
          example: "http://fallback-service/api/v1/orders"

  responses:
    '429':
      description: "Rate limit exceeded. Resilience guidelines triggered."
```

---

### **2. Kubernetes Pod Resilience Spec**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: payment-service
        image: payment-service:v1
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
        env:
        - name: CIRCUIT_BREAKER_FAILURE_THRESHOLD
          value: "3"
        - name: RETRY_MAX_ATTEMPTS
          value: "2"
```

---

### **3. Resilience4j Configuration (Java)**
```java
@Configuration
public class ResilienceConfig {

    @Bean
    public CircuitBreakerConfig circuitBreakerConfig() {
        return CircuitBreakerConfig.custom()
            .failureRateThreshold(50)  // % of calls that fail to trip
            .slowCallRateThreshold(50)  // % of calls slower than 1s
            .slowCallDurationThreshold(Duration.ofSeconds(1))
            .waitDurationInOpenState(Duration.ofMillis(1000))
            .permittedNumberOfCallsInHalfOpenState(3)
            .slidingWindowSize(5)
            .minimumNumberOfCalls(10)
            .recordExceptions(IOException.class, TimeoutException.class)
            .build();
    }
}
```

---

### **4. Terraform Resilience Policy**
```hcl
resource "aws_appautoscaling_target" "example" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = aws_lambda_function.example.arn
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"

  depends_on = [aws_lambda_function.example]
}

resource "aws_appautoscaling_policy" "scaling_policy" {
  name               = "scale-on-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.example.resource_id
  scalable_dimension = aws_appautoscaling_target.example.scalable_dimension
  service_namespace  = aws_appautoscaling_target.example.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300  # 5 minutes
    scale_out_cooldown = 60   # 1 minute
  }
}
```

---

## **Query Examples**

### **1. Checking Resilience Status via API**
```bash
# Curl request to check circuit breaker status
curl -X GET "http://localhost:8080/actuator/health/circuitbreakers" \
  -H "Accept: application/vnd.circuitbreaker+v1+json" \
  -u admin:admin
```
**Expected Response:**
```json
{
  "status": "OPEN",
  "count": 5,
  "failureRate": 80,
  "timeRemaining": 1000
}
```

---

### **2. Kubernetes Query for Resource Constraints**
```bash
# Describe pod resilience policies
kubectl describe pod payment-service-5c7d9f8b6c -n default | grep -A 5 "Resources:"
```
**Output:**
```
Resources:
  Limits:
    cpu:    500m
    memory: 512Mi
  Requests:
    cpu:     100m
    memory:  256Mi
```

---

### **3. Resilience4j Metrics Query**
```java
// Query circuit breaker metrics
CircuitBreaker circuitBreaker = CircuitBreaker.of("exampleService", config);
System.out.println("Number of calls: " + circuitBreaker.getMetrics().getNumberOfCalls());
System.out.println("Number of failures: " + circuitBreaker.getMetrics().getNumberOfFailures());
```

---

### **4. Terraform CloudWatch Alerts**
```hcl
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "HighPaymentGatewayErrorRate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert if payment gateway errors exceed 10 in 2 minutes"
  dimensions = {
    FunctionName = aws_lambda_function.payment-gateway.arn
  }
  alarm_actions = [aws_sns_topic.ops-alerts.arn]
}
```

---

## **Related Patterns**

| Pattern                          | Description                                                                                     | When to Use                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Circuit Breaker**               | Prevents cascading failures by stopping calls to failing services.                            | When dependent services are unreliable (e.g., third-party APIs).                              |
| **Bulkhead**                      | Isolates resource-heavy operations to prevent system-wide disruptions.                        | When a single operation (e.g., database query) can overload the system.                       |
| **Retry with Backoff**            | Automatically retries failed operations with exponential delays.                              | When transient failures (e.g., network timeouts) are expected.                                |
| **Rate Limiting**                 | Controls request volume to prevent overload.                                                  | During traffic spikes or DDoS attacks.                                                         |
| **Fallback**                      | Provides alternative behavior when primary operations fail.                                   | When graceful degradation is preferred (e.g., show cached data).                              |
| **Degradation**                   | Reduces functionality under stress (e.g., disable non-critical features).                      | During peak load or resource constraints.                                                    |
| **Resilient Messaging**           | Ensures messages are processed even if downstream systems fail.                               | For event-driven architectures (e.g., Kafka, RabbitMQ).                                       |
| **Chaos Engineering**             | Deliberately introduces failures to test resilience.                                           | During system development or maintenance.                                                    |
| **Polyglot Persistence**          | Uses multiple database types to ensure data availability.                                     | When single-database failure would disrupt critical operations.                               |

---

## **Best Practices**
1. **Document Thresholds Clearly**: Define what constitutes a "failure" (e.g., latency > 1s, error rate > 1%).
2. **Avoid Over-Retries**: Exponential backoff reduces load but should not exceed a reasonable limit (e.g., 5 retries).
3. **Monitor Circuit Breaker States**: Use tools like Prometheus to track `OPEN`, `HALF_OPEN`, and `CLOSED` states.
4. **Combine Patterns**: Use **Circuit Breaker + Retry + Fallback** for robust failure handling.
5. **Test Resilience Guidelines**: Simulate failures (e.g., kill pods in Kubernetes) to validate responses.
6. **Log Failures**: Correlate failures with resilience events for debugging (e.g., "Circuit breaker tripped for `payment-gateway`").
7. **Adjust Dynamically**: Use metrics to adjust thresholds (e.g., increase retry limits during low-load periods).

---
## **Troubleshooting**
| Issue                          | Cause                                      | Solution                                                                                     |
|--------------------------------|--------------------------------------------|---------------------------------------------------------------------------------------------|
| **Circuit Breaker Trips Too Soon** | Low failure threshold or noisy neighbors. | Increase `failureThreshold` or filter transient errors.                                      |
| **Retries Exhaust All Budgets**     | No backoff or excessive retries.           | Adjust `maxAttempts` and `multiplier` in backoff strategy.                                  |
| **Degradation Triggers Too Early** | Overly conservative thresholds.           | Increase latency/error rate tolerances or use predictive scaling.                            |
| **Resilience Config Not Applied** | Misconfigured or missing annotations.      | Verify schema compliance in API/contracts and IaC templates.                                 |
| **Metrics Not Updated**          | Monitoring tool misconfiguration.         | Check Prometheus/Grafana dashboards for missing metrics.                                      |

---
This guide provides a structured approach to implementing **Resilience Guidelines** across systems. Adjust schemas and thresholds based on your specific architecture and SLAs.