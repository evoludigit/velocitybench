```markdown
# Mastering API Design: The Availability Conventions Pattern for Reliable Backend Systems

![Availability Conventions Pattern](https://miro.medium.com/max/1400/1*X67QIaMfTJT8fvqJ3o5JTg.png)
*Ensuring consistent availability patterns across distributed systems*

As backend systems grow in complexity, one challenge remains constant: **how do we design APIs and databases that remain resilient during failures?** Whether it's handling gracefully degrading services, temporary network partitions, or cascading failures, modern applications need intentional strategies to maintain consistent availability.

This is where the *Availability Conventions* pattern comes into play. Unlike traditional error-handling approaches, this pattern shifts focus to **making availability expectations explicit**—both in your application's design and in its interactions with clients. By defining clear conventions for how your APIs behave under different availability conditions, you create predictable systems that can self-heal and gracefully accommodate failure.

In this guide, we'll explore:
- Why availability conventions matter beyond just error codes
- How to design APIs that gracefully degrade rather than crash
- Practical implementations using REST, GraphQL, and microservices
- Tradeoffs and common pitfalls to avoid

Let’s begin by examining why availability conventions are essential.
---

## The Problem: When APIs Break the Unwritten Rules of Availability

Without explicit availability conventions, APIs behave like the Wild West—each service decides its own rules for handling failure. Here’s what happens when you don’t define these rules:

### 1. **Unexpected Timeouts Turn Into 500 Errors**
Consider a payment processing API that fails due to a payment gateway outage. If your API doesn’t handle this gracefully, the response might be a `500` error, leaving your frontend team stumped about whether the issue is temporary or permanent. Here’s a real-world example:

```http
# Poor: No availability convention
GET /api/payments/process?id=123
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": "Payment gateway timeout"
}
```

The lack of context forces the client to retry indefinitely, potentially flooding the system with requests.

### 2. **Race Conditions in Distributed Systems**
When multiple services rely on each other, failures cascade unpredictably. For instance, if your authentication service times out, but your API doesn’t distinguish between transient and permanent failures, it might reject all requests until the service recovers—even though the issue could be temporary.

### 3. **Clients Can’t Self-Recover**
Without clear availability signals, clients can’t implement intelligent retry logic. Should they retry immediately? Wait 10 seconds? Try a fallback? Your API must **tell them**.

### 4. **Operational Noise and Alert Fatigue**
When every failure triggers a critical alert (e.g., a `500` error), teams drown in noise. Availability conventions help differentiate between:
- **Transient failures** (e.g., "Database connection lost—retrying in 30 seconds")
- **Permanent failures** (e.g., "Feature disabled due to maintenance—use fallback")

---

## The Solution: Availability Conventions

Availability conventions are **standards for how your API communicates availability status** to clients. They define:
1. **Response codes or headers** for different availability states.
2. **Retry strategies** (timeouts, delays, fallbacks).
3. **Fallback responses** when features are unavailable.

The goal is to **make availability a first-class concern**, not an afterthought.

### Core Principles of Availability Conventions
1. **Explicit Over Implicit**: Always communicate availability clearly.
2. **Decouple Behavior from Failure**: Gracefully degrade instead of crashing.
3. **Empower Clients**: Give clients the tools to self-recover.

---

## Components/Solutions: Building Availability Conventions

### 1. **HTTP Status Codes for Availability**
Use HTTP status codes to signal availability, not just success/failure. Some conventions:
- `200 OK`: Feature is available.
- `204 No Content`: Feature is temporarily unavailable (e.g., under maintenance).
- `429 Too Many Requests`: Rate-limited (with `Retry-After` header).
- `503 Service Unavailable`: Permanent downtime (with `Retry-After` header).

#### Example: REST API with Availability Headers
```http
# Good: Availability headers
GET /api/payments/process?id=123
HTTP/1.1 200 OK
Content-Type: application/json
X-Availability-Status: operational
X-Retry-After: 10  # (seconds until retry recommended)

{
  "status": "completed",
  "transaction_id": "txn_12345"
}
```

```http
# Transient failure with retry guidance
GET /api/payments/process?id=123
HTTP/1.1 503 Service Unavailable
Content-Type: application/json
X-Availability-Status: degraded
X-Retry-After: 60  # (retry after 60 seconds)
Retry-After: 60

{
  "error": "Payment gateway unavailable. Retry later."
}
```

### 2. **GraphQL: Use Directives for Availability**
GraphQL APIs can use directives (like `@deprecated` or custom ones) to signal availability:
```graphql
type Query {
  paymentProcess(id: ID!): Payment @availability(status: "degraded", retryAfter: 60)
}

type Payment {
  id: ID!
  status: String!
  message: String
}
```

### 3. **Microservices: Circuit Breakers and Retry Policies**
Use tools like **Resilience4j** or **Hystrix** to implement circuit breakers. Define conventions for:
- **Open state**: "Service unavailable—retry later."
- **Half-open state**: "Partial availability—try with fallback."
- **Closed state**: "Service restored."

#### Example: Spring Boot with Resilience4j
```java
@CircuitBreaker(name = "paymentService", fallbackMethod = "fallbackPayment")
public PaymentProcessResponse processPayment(String paymentId) {
    return paymentService.process(paymentId);
}

public PaymentProcessResponse fallbackPayment(String paymentId, Exception e) {
    if (e instanceof TimeoutException) {
        return new PaymentProcessResponse(
            "PENDING",
            "Payment gateway timed out. Retry in 30 seconds.",
            "retry-after: 30"
        );
    }
    throw e;
}
```

### 4. **Database-Level Retries**
For database operations, use retry policies with exponential backoff:
```sql
-- PostgreSQL: Retry on deadlocks
BEGIN;
    -- Critical transaction (may deadlock)
    INSERT INTO orders (customer_id, amount) VALUES (123, 100.00);
COMMIT;

-- If deadlock occurs, retry with backoff:
SELECT pg_sleep(10 * (2^attempt)); -- Exponential backoff
```

---

## Implementation Guide: Step-by-Step

### Step 1: Define Your Availability States
Start by documenting your system’s availability states. Example:
| State            | Description                          | HTTP Status | Headers/Fields          |
|------------------|--------------------------------------|-------------|-------------------------|
| Operational      | Full functionality                   | 200         | `X-Availability-Status: operational` |
| Degraded         | Partial functionality                | 204         | `X-Availability-Status: degraded` |
| Unavailable      | Temporarily offline                  | 503         | `Retry-After: 60`       |
| Maintenance      | Scheduled downtime                   | 503         | `X-Maintenance-Ends: 2024-01-01T12:00:00Z` |

### Step 2: Instrument Your APIs
Add availability headers to all responses:
```go
// Go example: Adding availability headers
func processPayment(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("X-Availability-Status", "operational")
    w.Header().Set("Retry-After", "0") // No retry needed
    // ... handle request
}
```

### Step 3: Implement Fallbacks
For degraded state, return meaningful fallbacks:
```python
# Flask example: Fallback for unavailable features
@app.route('/api/payments/process')
def process_payment():
    if is_payment_gateway_unavailable():
        return jsonify({
            "status": "pending",
            "message": "Payment processing temporarily disabled. Use manual payment.",
            "retry_after": 3600
        }), 204
    # ... normal logic
```

### Step 4: Client-Side Handling
Clients should parse availability headers and implement retries:
```javascript
// JavaScript client example
async function processPayment(paymentId) {
  const response = await fetch(`/api/payments/process?id=${paymentId}`);
  const retryAfter = response.headers.get("Retry-After");

  if (response.status === 503 && retryAfter) {
    console.log(`Service unavailable. Retrying in ${retryAfter} seconds...`);
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return processPayment(paymentId); // Retry
  }
  return response.json();
}
```

### Step 5: Monitor and Alert
Use tools like Prometheus to monitor availability headers:
```promql
# Alert if X-Availability-Status is "degraded" for too long
alert(HighDegradationDuration) if (
    avg_over_time(http_request_duration_seconds[5m]) > 10 &&
    sum(rate(http_requests_total{status="204"}[5m])) > 0
)
```

---

## Common Mistakes to Avoid

### 1. **Assuming Clients Understand Your Conventions**
Don’t rely on clients reading headers. Document your conventions clearly:
```markdown
## API Availability Conventions

| Header               | Values                     | Description                                  |
|----------------------|----------------------------|----------------------------------------------|
| `X-Availability-Status` | `operational`, `degraded`, `unavailable` | Current service state.                      |
| `Retry-After`        | Seconds until retry         | How long to wait before retrying.           |
```

### 2. **Overloading Status Codes**
Avoid mixing availability signals with error codes. Use:
- `429` for rate-limiting.
- `503` for service unavailability.
- `400`/`404` for logical errors (not availability).

### 3. **Ignoring Database-Specific Retries**
Different databases handle retries differently:
- **PostgreSQL**: Use `pg_retry` or `REPEATABLE READ` for deadlocks.
- **MongoDB**: Implement retries for network errors with `maxRetries`:
```javascript
await collection.insertOne({ /* ... */ }, {
  retryWrites: true,
  maxRetryTimeMS: 30000
});
```

### 4. **Not Testing Failure Scenarios**
Write tests for degraded states:
```python
# Pytest example: Test degraded state
def test_degraded_payment_processing(app):
    with app.test_client() as client:
        response = client.get("/api/payments/process?id=123")
        assert response.status_code == 204
        assert response.headers["X-Availability-Status"] == "degraded"
        assert response.headers["Retry-After"] == "60"
```

### 5. **Forgetting About Timeouts**
Set reasonable timeouts for calls to degraded services:
```java
// Java: Configure timeout for degraded services
RestTemplate restTemplate = new RestTemplate();
restTemplate.setConnectTimeout(1000); // 1 second
restTemplate.setReadTimeout(2000);     // 2 seconds
```

---

## Key Takeaways

✅ **Availability is a feature**: Treat it like any other API design decision.
✅ **Use headers for clarity**: `X-Availability-Status`, `Retry-After`, etc.
✅ **Empower clients**: Give them tools to self-recover (retries, fallbacks).
✅ **Document conventions**: Clients need to know how to interpret signals.
✅ **Test failure scenarios**: Ensure your system behaves predictably under load.
✅ **Balance resilience and performance**: Avoid endless retries that worsen outages.
✅ **Leverage existing tools**: Use circuit breakers (Resilience4j), retries (ExponentialBackoff), and monitoring (Prometheus).

---

## Conclusion: Building Resilient Systems

Availability conventions are the secret sauce that turns brittle APIs into resilient systems. By making availability explicit—through headers, fallbacks, and clear documentation—you reduce debugging time, improve user experience, and build systems that can handle failure gracefully.

Remember:
- **Start small**: Add availability headers to one API endpoint and measure the impact.
- **Iterate**: Refine your conventions based on feedback from clients and operations teams.
- **Stay consistent**: Use the same patterns across all services in your stack.

As your system scales, availability conventions will save you from the chaos of "works on my machine" failures. They’re not just a nice-to-have—they’re the foundation of a reliable backend.

Now go forth and design APIs that can handle anything.
```

---
**Further Reading**:
- [Resilience Patterns by Michael Nygard](https://www.oreilly.com/library/view/resilience-patterns/9781491938859/)
- [HTTP Status Codes for Availability](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [Circuit Breaker Pattern (Resilience4j)](https://resilience4j.readme.io/docs/circuitbreaker)