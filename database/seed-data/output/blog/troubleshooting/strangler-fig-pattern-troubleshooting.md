# **Debugging the Strangler Fig Pattern: A Troubleshooting Guide**
*Gradually Migrating a Monolith Without Major Downtime*

## **1. Introduction**
The **Strangler Fig Pattern** is a refactoring approach for incrementally migrating a monolithic application into microservices by replacing small parts of the system at a time, while the legacy system remains operational. Common issues arise due to improper decomposition, communication bottlenecks, or incomplete migration strategies. This guide will help diagnose and resolve problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, assess whether your migration follows the Strangler Fig Pattern correctly:

| **Symptom**                          | **Possible Cause**                                                                 | **Quick Check** |
|---------------------------------------|------------------------------------------------------------------------------------|-----------------|
| Performance degradation after new API deployment | New microservices are overloaded or poorly integrated with the monolith. | Check API call logs, latency, and load balancer metrics. |
| Inconsistent data between old & new services | Transaction boundaries are not properly managed.                               | Verify database connections and event sourcing. |
| Increased error rates (5xx, 4xx)      | Microservices are unable to gracefully degrade or retry failed requests.         | Review error logs and circuit breaker configurations. |
| Slower migration progress than expected | New components are not fully decoupled from the monolith.                       | Audit API contracts and internal service calls. |
| Unstable CI/CD pipeline              | Incremental changes break existing functionality.                                 | Test each small refactor in isolation. |
| Integration tests failing intermittently | Legacy dependencies are not properly mocked or wrapped.                        | Replace real monolith calls with mocks in tests. |

---
## **3. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Poor API Contract Design (Tight Coupling)**
**Symptom:** New microservices depend too heavily on monolith APIs, slowing migration.

**Fix:** Enforce loose coupling via **API gateways, event-driven communication, and backward compatibility**.

#### **Solution: Use an API Gateway (Kong/Nginx)**
- Replace direct monolith calls with a **proxy layer** that forwards requests.
- Example: **Kong Gateway (Open-Source)**
```yaml
# Kong API Gateway Configuration (Nginx example)
upstream monolith_api {
    server monolith:8080;
}

server {
    listen 8080;
    location /v1/monolith-endpoint {
        proxy_pass http://monolith_api/monolith-endpoint;
        proxy_set_header Host $host;
    }
}
```
- **New Service:** Replace direct calls with the gateway.
```bash
curl http://localhost:8080/v1/monolith-endpoint/data
```
- **Prevention:** Institute a **contract-first API design** (OpenAPI/Swagger).

---

### **Issue 2: Transaction Management Failures (Distributed ACID)**
**Symptom:** Data inconsistencies when new services interact with the legacy DB.

**Fix:** Use **Saga Pattern** or **eventual consistency** with **event sourcing**.

#### **Solution: Saga Pattern (Eventual Consistency)**
```java
// Example in Java (Spring Cloud Stream)
@Service
public class OrderService {

    @KafkaListener(topics = "order_created")
    public void handleOrderCreated(OrderEvent event) {
        // Step 1: Create inventory reservation
        inventoryService.reserveStock(event.getProductId(), event.getQuantity());

        // Step 2: Send payment confirmation
        paymentService.processPayment(event.getPaymentId());

        // Step 3: Finalize order
        orderRepository.save(event);
    }
}
```
- **Prevention:** Implement **compensating transactions** for rollbacks.

---

### **Issue 3: Slow Migration Due to Monolith API Pollution**
**Symptom:** New services keep calling the monolith, making it hard to kill.

**Fix:** **Refactor incrementally** by replacing one feature at a time.

#### **Solution: Feature-Based Migration**
1. **Identify a small, isolated feature** (e.g., user registration).
2. **Extract it into a new service** with a **proxy wrapper**.
3. **Gradually redirect traffic** to the new service.

**Example: Proxy Wrapper (Node.js with Express)**
```javascript
// Old monolith endpoint (to be phased out)
app.get('/users/register', (req, res) => {
    res.redirect('/v1/users/register');
});

// New service endpoint (takeover)
app.get('/v1/users/register', (req, res) => {
    axios.post('http://users-service/register', req.body)
        .then(response => res.json(response.data))
        .catch(err => res.status(500).json({ error: err.message }));
});
```
- **Prevention:** Use **feature flags** to toggle between old/new implementations.

---

### **Issue 4: High Latency Between Monolith & New Services**
**Symptom:** API calls between monolith and microservices are slow.

**Fix:** **Cache responses** and **reduce chattiness** with **asynchronous requests**.

#### **Solution: Redis Caching**
```python
# Flask Example
from flask import Flask, jsonify
import redis

redis_client = redis.Redis(host='localhost', port=6379)

@app.route('/api/products/<id>')
def get_product(id):
    cache_key = f"product:{id}"
    product = redis_client.get(cache_key)

    if not product:
        product = monolith_api.get_product(id)  # Call monolith
        redis_client.setex(cache_key, 300, product)  # Cache for 5 min

    return jsonify(product)
```
- **Prevention:** Use **edge caching** (CDN) for HTTP responses.

---

### **Issue 5: CI/CD Pipeline Breaks with Incremental Changes**
**Symptom:** New service deploys break existing functionality.

**Fix:** **Isolate tests** and **mock monolith dependencies**.

#### **Solution: Mocking with WireMock**
```java
// Test New Service Without Monolith
public class UserServiceTest {

    @Test
    public void testRegisterUser() {
        stubFor(post(urlEqualTo("/users/register"))
            .willReturn(aResponse()
                .withStatus(200)
                .withHeader("Content-Type", "application/json")
                .withBody("{\"id\":123}")));

        User newUser = new User("test@example.com", "pass123");
        User savedUser = userService.register(newUser);

        assertEquals(123, savedUser.getId());
    }
}
```
- **Prevention:** Use **contract tests** (Pact) to verify API compatibility.

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**          | **Use Case**                                                                 | **Example Command** |
|-----------------------------|-----------------------------------------------------------------------------|---------------------|
| **Tracing (OpenTelemetry, Jaeger)** | Track request flow across monolith & microservices.                     | `curl http://jaeger:16686/search` |
| **Load Testing (k6, Gatling)** | Identify performance bottlenecks before full rollout.                   | `k6 run --vus 100 -d 30s script.js` |
| **Database Auditing (pgAudit, AWS CloudTrail)** | Detect unintended data changes.                                         | `SELECT * FROM pg_stat_statements;` |
| **API Monitoring (Prometheus + Grafana)** | Track latency, error rates, and traffic shifts.                           | `prometheus --config.file=prometheus.yml` |
| **Logging Aggregation (ELK, Loki)** | Correlate logs across services.                                          | `grep "error" /var/log/app.log` |
| **Canary Deployments (Flagger, Istio)** | Gradually shift traffic to new services.                                  | `kubectl apply -f canary.yaml` |

---

## **5. Prevention Strategies**

### **Do:**
✅ **Start small** – Pick a single feature to migrate first.
✅ **Enforce backward compatibility** – New APIs should not break old clients.
✅ **Automate testing** – Use contract tests (Pact, Postman) to validate APIs.
✅ **Monitor aggressively** – Set up alerts for latency spikes, errors, and traffic shifts.
✅ **Use feature flags** – Enable/disable new features without deployment.
✅ **Document contracts** – Keep OpenAPI/Swagger specs updated.

### **Don’t:**
❌ **Migrate everything at once** – Stick to the "strangler" principle.
❌ **Ignore database dependencies** – Plan for eventual consistency early.
❌ **Assume the monolith is stable** – Test new services in staging.
❌ **Skip load testing** – Confirm new services handle production traffic.
❌ **Forget to deprecate old APIs** – Set clear EOL dates for monolith calls.

---

## **6. Final Checklist Before Full Migration**
Before killing the monolith dependency:
1. [ ] **All critical features** are in new services.
2. [ ] **Zero direct calls** to the monolith exist.
3. [ ] **Fallback mechanisms** are in place for edge cases.
4. [ ] **Rollback plan** is documented (e.g., traffic reversal).
5. [ ] **Performance under load** is validated (99th percentile < SLA).
6. [ ] **Monitoring is in place** for the new-only stack.

---
### **Next Steps**
1. **Audit current API calls** (e.g., `grep "http://monolith" -r .`).
2. **Prioritize the most called endpoints** for migration.
3. **Start with a non-critical feature** to validate the process.

By following this guide, you should be able to **diagnose and fix most Strangler Fig migration issues efficiently**. If problems persist, revisit the **decomposition strategy**—are you cutting the right "fig"? 🌿