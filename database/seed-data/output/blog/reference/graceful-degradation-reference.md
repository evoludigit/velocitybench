**[Pattern] Graceful Degradation Patterns – Reference Guide**

---

### **1. Overview**
Graceful degradation is a resilience pattern that ensures a system remains operational—albeit with reduced functionality—when non-critical components fail. Instead of crashing or failing entirely, the system prioritizes core functionality while gracefully falling back to alternative behaviors (e.g., default values, simpler workflows, or cached responses). This approach minimizes downtime and preserves user experience by transparently adapting to failures, ensuring availability even under degraded conditions.

Key benefits:
- **High availability**: Continues partial functionality during failures.
- **Better UX**: Users face frustration reduction over abrupt outages.
- **Operational resilience**: Eases recovery during cascading failures.

Typical applications include:
- Falling back to static content when dynamic services fail.
- Replacing complex algorithms (e.g., AI recommendations) with precomputed results.
- Retrying or queuing requests during transient failures (e.g., payment gateways).

---

### **2. Schema Reference**
The following schema outlines core components and their relationships for implementing graceful degradation:

| **Component**          | **Description**                                                                                     | **Example Values/Attributes**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Primary Service**    | The core functionality being protected (e.g., recommendation engine, payment processor).             | `RecommendationService`, `PaymentGateway`                                                      |
| **Fallback Service**   | Alternative or simplified service that provides limited functionality when the primary fails.      | `PopularItemsCache`, `RetryQueue`                                                                 |
| **Monitoring Trigger** | Condition (e.g., health check failure, timeout, or error rate) that activates the fallback.         | `PrimaryService.HealthCheck.Failed`, `TimeoutAfter.3Seconds`                                   |
| **Degradation Rule**   | Policy defining when and how to activate the fallback (e.g., priority, timeout thresholds).           | `{ priority: "high", fallback: "show_popular_items", threshold_ms: 2000 }                     |
| **User Context**       | Metadata about the user/request to tailor the fallback (e.g., session ID, user role).             | `{ user_id: "123", session: "active" }                                                          |
| **Logging/Audit**      | Records degradation events for debugging and analytics.                                             | `{ timestamp: "2024-05-01T12:00:00", severity: "WARN", message: "Fallback triggered" }       |
| **Retry Policy**       | Parameters for retrying failed primary service calls (e.g., max retries, backoff strategy).        | `maxRetries: 3, backoffFactor: 2`                                                               |

---

### **3. Implementation Details**

#### **3.1. Key Concepts**
1. **Fallback Strategies**:
   - **Static Fallback**: Use precomputed data (e.g., cached popular items).
   - **Dynamic Fallback**: Redirect to a simpler alternative (e.g., retry queuing).
   - **Hybrid Fallback**: Combine static and dynamic (e.g., show cached items + retry background tasks).

2. **Activation Triggers**:
   - **Health Checks**: Monitor primary service health via HTTP/ping endpoints.
   - **Error Rates**: Activate fallback if errors exceed a threshold (e.g., 90% failure rate).
   - **Timeouts**: Fall back after a configured delay (e.g., 1-second latency).

3. **Prioritization**:
   - Use degradation rules to define which features tolerate failures (e.g., "low-priority" vs. "critical").

4. **Circuit Breakers**:
   - Stop retries after repeated failures to avoid cascading issues (e.g., Hystrix, Resilience4j).

---

#### **3.2. Implementation Patterns**
| **Scenario**                          | **Fallback Mechanism**                                                                       | **Example Code Snippet**                                                                       |
|---------------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **API Timeout**                       | Return cached response or default data.                                                     | ```javascript                                                                                   // Pseudo-code                                                                   const getRecommendations = async (userId) => {                                                                   try {                                                                       const response = await recommendationService.get(userId);                                                                       return response;                                                                   } catch (err) {                                                                       if (err.code === "TIMEOUT") {                                                                           return cachedService.getPopularItems();                                                                       }                                                                   }                                                                   };                                                                   ```                                                                                       |
| **Database Failure**                  | Use a read replica or fallback to a lightweight schema.                                      | ```java                                                                                         // Spring Data Example                                                                   @Service                                                                   public class ProductService {                                                                       @Autowired private PrimaryProductRepository primaryRepo;                                                                       @Autowired private FallbackProductRepository fallbackRepo;                                                                       public List<Product> getProducts() {                                                                           try {                                                                               return primaryRepo.findAll();                                                                           } catch (DataAccessException e) {                                                                               return fallbackRepo.findLightweightProducts();                                                                           }                                                                       }                                                                   }                                                                                       |
| **External Service Down**             | Queue requests and retry later (e.g., using a message queue).                                | ```python                                                                                       # Celery Task                                                                   @task(autoretry_for=(Exception,), max_retries=3, default_retry_delay=5)                                                                   def process_payment(order_id):                                                                       payment_gateway.process(order_id)                                                                   ```                                                                                       |
| **AI Model Unavailable**              | Switch to rule-based recommendations.                                                        | ```python                                                                                       def get_suggestions(user_prefs):                                                                           if ai_model_available():                                                                               return ai_model.predict(user_prefs)                                                                           else:                                                                               return rule_engine.generate_suggestions(user_prefs)                                                                       ```                                                                                       |

---

#### **3.3. Best Practices**
1. **Prioritize Critical Paths**:
   - Ensure core user flows (e.g., checkout) have higher degradation thresholds than non-critical features.

2. **Monitor and Alert**:
   - Track fallback activations (e.g., Prometheus metrics) and alert on suspicious patterns (e.g., repeated failures).

3. **User Transparency**:
   - Inform users of degraded features (e.g., "Personalized recommendations are unavailable; showing popular items instead.").

4. **A/B Testing Fallbacks**:
   - Test fallbacks in staging to ensure they don’t degrade performance further.

5. **Graceful Recovery**:
   - Automatically switch back to the primary service when it recovers (e.g., via health checks).

---

### **4. Query Examples**
#### **4.1. Fallback Activation Check (SQL)**
```sql
-- Check if recommendation service is down (using a monitoring table)
SELECT COUNT(*) AS failure_count
FROM service_health_logs
WHERE service_name = 'recommendation_service'
  AND status = 'down'
  AND timestamp > NOW() - INTERVAL '1 hour';
-- If failure_count > threshold (e.g., 3), trigger fallback.
```

#### **4.2. Circuit Breaker Logic (Pseudocode)**
```javascript
// Simplified circuit breaker with fallback
const circuitBreaker = {
  state: 'closed',
  threshold: 5,
  failures: 0,
  execute: async (fn) => {
    if (this.state === 'open') {
      return fallbackFn(); // Use fallback
    }
    try {
      return await fn();
    } catch (err) {
      this.failures++;
      if (this.failures >= this.threshold) {
        this.state = 'open';
      }
      return fallbackFn();
    }
  },
  reset: () => {
    this.state = 'closed';
    this.failures = 0;
  }
};
```

#### **4.3. Fallback in Microservices (API Gateway)**
```yaml
# Kong API Gateway configuration for graceful degradation
plugins:
  - name: request-transformer
    config:
      add:
        headers:
          x-fallback: "recommendation_service_down"
        query:
          fallback_mode: "true"
```

---
### **5. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use Together**                                                                         |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Stops cascading failures by stopping retries after a threshold.                                    | Use with graceful degradation to avoid overloading fallbacks.                                  |
| **Bulkheading**           | Isolates components to prevent failure propagation.                                                | Protects fallback services from being overwhelmed during primary service failures.              |
| **Retry with Backoff**    | Retries failed requests with exponential backoff.                                                  | Combine with graceful degradation to retry transient failures before falling back.               |
| **Rate Limiting**         | Limits requests to a service to avoid overload.                                                   | Prevents degradation from cascading due to retry storms.                                       |
| **Chaos Engineering**     | Tests resilience by intentionally causing failures.                                               | Validate degradation strategies before production deployment.                                  |
| **Bulkhead Worker**       | Limits concurrent executions of a resource-intensive task.                                       | Ensures fallbacks don’t degrade performance further.                                          |

---
### **6. Example Architecture**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌───────────────────────────────────┐  │
│   │             │    │             │    │                               │  │
│   │  Primary    ├──┬──│  Fallback   ├──┬──│               User            │  │
│   │  Service    │   │  Service    │   │   │              (e.g., Browser)  │  │
│   │  (e.g., AI   │   │  (e.g.,     │   │   └───────────────┬───────────────┘  │
│   │   Recommend) │   │   Cached     │   │                    │                   │
│   │             │   │   Popular    │   │                    ▼                   │
│   └─────────────┘   │   Items)     │   │               ┌─────────────────┐     │
│                     │             │───┘               │                 │     │
│                     └─────────────┘                   │  Degradation     │     │
│                                                         │  Rules Engine    │     │
│                                                         │                 │     │
│                                                         └─────────────────┘     │
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌───────────────────────────────────┐  │
│   │             │    │             │    │                               │  │
│   │ Monitoring  ├──┬──│  Logging    ├──┬──│  Alerting System            │  │
│   │ (e.g.,      │   │  (e.g.,     │   │   │  (e.g., PagerDuty)          │  │
│   │  Prometheus) │   │  Loki)      │   │   └───────────────┬───────────┘  │
│   │             │   │             │   │                    │                   │
│   └─────────────┘   └─────────────┘                   │                   │
│                                                         ▼                   │
│                                                         Health Checks       │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---
### **7. Metadata**
- **Categories**: Resilience, Fault Tolerance
- **Tags**: #degradation #fallback #reliability #observability
- **Dependencies**: Circuit Breaker, Retry Pattern, Monitoring
- **Anti-Patterns**: "Blacklisting" users during degradation (increases frustration).