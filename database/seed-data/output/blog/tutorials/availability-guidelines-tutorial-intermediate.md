```markdown
# **Availability Guidelines: Designing APIs for Graceful Failure**

*How to build resilient systems that handle downtime, rate limits, and edge cases without crashing*

---

## **Introduction**

Have you ever built an API that worked flawlessly in development but collapsed under real-world conditions? Maybe it choked when a database went offline, or it failed spectacularly when hit with a traffic spike. These aren’t hypotheticals—they’re the harsh realities of production systems where uptime isn’t optional.

The **Availability Guidelines** pattern is a systematic approach to designing APIs that degrade gracefully when things go wrong. Instead of crashing when a dependency fails, your backend should:
- Return meaningful feedback.
- Prioritize critical data.
- Fall back to acceptable defaults.

This pattern isn’t about making your system 100% available—it’s about **minimizing the blast radius** when failures occur and ensuring users or downstream services don’t lose trust in your API.

In this guide, we’ll explore:
✅ Why APIs fail and how availability guidelines help.
✅ Practical strategies to implement graceful degradation.
✅ Real-world tradeoffs and pitfalls to avoid.
✅ Code examples in Go, Python, and Node.js.

---

## **The Problem: When APIs Break, Users Lose Trust**

APIs are supposed to be **invisible**—reliable, predictable, and always available. But in reality, failures are inevitable:
- **Database downtime**: A single query timeout can break an entire transactional workflow.
- **Third-party timeouts**: Payment gateways, weather APIs, or CDNs may fail intermittently.
- **Rate limits**: APIs like Stripe or Twilio enforce quotas, and hitting them can break workflows.
- **Network partitions**: Microservices may lose connectivity between each other.

Without proper handling, these failures manifest as:
🔥 **Non-informative errors**: `500 Internal Server Error` with no details.
🔥 **Data loss**: Transactions roll back silently, leaving users in inconsistent states.
🔥 **Cascading failures**: An unrecovered error in Service A crashes Service B, then Service C.

Even worse, clients (mobile apps, frontend services) often treat API errors as **permanent failures**—they retry indefinitely, hammering your system further.

---

## **The Solution: Availability Guidelines**

The Availability Guidelines pattern is a **proactive strategy** to ensure your API:
1. **Fails fast** when it detects a critical issue (e.g., database corruption).
2. **Degrades gracefully** when it can’t fulfill a request (e.g., during a rate limit).
3. **Provides clear feedback** to clients so they can handle failures correctly.

This pattern isn’t just about error handling—it’s about **designing for failure**.

### **Core Principles**
1. **Assume failures will happen**—plan for them.
2. **Expose transparency**—let clients know why a request failed.
3. **Prioritize critical data**—avoid revealing internal state.
4. **Use circuit breakers**—prevent cascading failures.
5. **Provide fallback defaults**—when data is unavailable, give something usable.

---

## **Components/Solutions**

### **1. Circuit Breakers**
A **circuit breaker** monitors dependencies (databases, external APIs) and automatically blocks requests when they fail repeatedly.

**Example (Go with `github.com/avast/retry-go`):**
```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/avast/retry-go"
)

type PaymentGatewayAPI struct {
	client *http.Client
}

func (g *PaymentGatewayAPI) ProcessPayment(ctx context.Context, amount int, currency string) error {
	// Simulate a circuit breaker (e.g., using Polly or GoCircuitBreaker)
	retryable := retry.Do(func() error {
		req, _ := http.NewRequestWithContext(ctx, "POST", "https://api.stripe.com/charges", nil)
		req.Header.Set("Authorization", "Bearer YOUR_KEY")
		resp, err := g.client.Do(req)
		if err != nil {
			return fmt.Errorf("gateway error: %v", err)
		}
		defer resp.Body.Close()
		return nil
	}, retry.WithMaxRetries(3), retry.WithDelay(1*time.Second))

	if retryable != nil {
		return fmt.Errorf("payment gateway unavailable: %v", retryable)
	}
	return nil
}
```

### **2. Retry Policies with Exponential Backoff**
Instead of retrying immediately, wait longer between attempts to avoid overwhelming a slow dependency.

**Example (Python with `tenacity`):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_user_data(user_id: int) -> dict:
    response = requests.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()  # Raises HTTPError for bad responses
    return response.json()
```

### **3. Fallback Responses**
When a primary data source fails, return an acceptable approximation.

**Example (JSON API response for a failed database query):**
```json
{
  "status": "partial_success",
  "data": {
    "current_user": {
      "id": 123,
      "name": "Admin User",
      "email": "admin@example.com",
      "last_login": "2023-11-15T12:00:00Z"
    },
    "premium_features": null,
    "message": "Some data could not be loaded due to temporary downtime."
  }
}
```

### **4. Transparent Error Messages**
Instead of generic `500` errors, return structured errors with:
- A clear cause (e.g., `RateLimitExceeded`).
- A timestamp.
- Retry-after headers (if applicable).

**Example (HTTP `429 Too Many Requests` with Retry-After):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 10
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "You’ve hit the rate limit of 100 requests per minute."
  }
}
```

---

## **Implementation Guide**

### **Step 1: Define Availability Thresholds**
Decide what failures are critical and what are acceptable. For example:
- **Critical**: Database connection lost (immediately fail with `503 Service Unavailable`).
- **Non-critical**: Slow query (return cached data with a warning).

### **Step 2: Use a Resilience Library**
- **Go**: [`github.com/avast/retry-go`](https://github.com/avast/retry-go), [GoCircuitBreaker](https://github.com/sony/gobreaker)
- **Python**: [`tenacity`](https://tenacity.readthedocs.io/), [`responses`](https://github.com/getsentry/responses)
- **JavaScript**: [`opossum`](https://github.com/joecomport/opossum), [`retry-as-promised`](https://github.com/sindresorhus/retry-as-promised)

### **Step 3: Implement Circuit Breakers**
Wrap external dependencies (e.g., databases, payment gateways) with circuit breakers.

**Example (Node.js with `retry-as-promised`):**
```javascript
const retry = require('retry-as-promised');

async function processOrder(userId) {
  const retryConfig = { retries: 3, minTimeout: 1000, maxTimeout: 5000 };
  const paymentService = new PaymentService();
  return await retry(retryConfig, async () => {
    const result = await paymentService.charge(userId);
    if (!result.success) throw new Error('Payment failed');
    return result;
  });
}
```

### **Step 4: Design Fallback Responses**
For APIs, structure responses to include:
- **Success**: Full data.
- **Partial failure**: Missing fields + a message.
- **Complete failure**: A safe default + retry instructions.

**Example (REST API for user profile):**
```json
# Full success
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "premium": true,
    "last_login": "2023-11-15T12:00:00Z"
  }
}

# Partial failure (missing premium features)
{
  "user": {
    "id": 1,
    "name": "Alice",
    "email": "alice@example.com",
    "premium": null,
    "last_login": "2023-11-15T12:00:00Z",
    "message": "Premium features could not be loaded due to temporary downtime."
  }
}
```

### **Step 5: Log Failures for Monitoring**
Track failures to detect patterns (e.g., "Database queries fail every Monday at 2PM"). Use tools like:
- **Prometheus + Grafana** (for metrics).
- **Sentry** (for error tracking).
- **Datadog/New Relic** (for APM).

**Example (Go logging):**
```go
import "log"

func fetchData(ctx context.Context) (*Data, error) {
  resp, err := http.Get("https://api.example.com/data")
  if err != nil {
    log.Printf("Failed to fetch data: %v", err)
    return nil, fmt.Errorf("unavailable: %w", err)
  }
  defer resp.Body.Close()
  // ... parse response
}
```

---

## **Common Mistakes to Avoid**

### **1. Ignoring Rate Limits**
Clients often blindly retry failed requests, causing **thundering herds**. Always:
- Return `Retry-After` headers.
- Use exponential backoff on the client side.

### **2. Over-Retrying**
Retrying too often (or indefinitely) can worsen failures. Follow the **"retry only once"** rule unless explicitly needed.

### **3. Exposing Sensitive Errors**
Never leak internal errors (e.g., stack traces) in production. Return generic messages:
```json
{
  "error": {
    "code": "internal_server_error",
    "message": "Something went wrong. Please try again later."
  }
}
```

### **4. Not Testing Failure Modes**
Always test:
- Database downtime.
- Third-party API failures.
- Network partitions.

**Example (Test with `testcontainers` for DB failures):**
```go
func TestUserService_DatabaseFailure(t *testing.T) {
  db, err := testcontainers.PostgreSQLContainer(t)
  if err != nil {
    t.Fatal(err)
  }
  defer db.Terminate(t)

  // Simulate a crash
  db.ForceCrash()

  // Verify graceful degradation
  user := userService.GetUser(1)
  if user.Email != "fallback@example.com" {
    t.Error("Expected fallback user")
  }
}
```

### **5. Not Documenting Fallbacks**
Clients need to know how to handle failures. Document:
- Which endpoints might return partial data.
- What retry delays are expected.
- When to abort retrying.

---

## **Key Takeaways**

✔ **Fail fast, fail gracefully**—don’t let one component break the whole system.
✔ **Use circuit breakers** to prevent cascading failures.
✔ **Return structured errors** with retry instructions.
✔ **Prioritize critical data**—don’t let missing details break UX.
✔ **Test failure modes**—assume dependencies will fail.
✔ **Monitor failures** to catch patterns before they escalate.

---

## **Conclusion**

Availability Guidelines aren’t about making your API **100% uptime**—they’re about **minimizing the impact of failures** when they happen. By designing for resilience upfront, you build APIs that:
✅ **Recover from outages** without crashing.
✅ **Communicate clearly** with clients.
✅ **Maintain trust** even under pressure.

Start small: pick one dependency to wrap with a circuit breaker, then expand. Over time, your system will become more robust—and your users will thank you when things inevitably go wrong.

---
**Further Reading**
- [Resilience Patterns by Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/resilience-patterns)
- [Circuit Breaker Pattern on Wikipedia](https://en.wikipedia.org/wiki/Circuit_breaker_(software))
- [PostgreSQL Connection Pooling (with fallback)](https://www.pgpool.net/)

**Try It Out**
Experiment with your favorite language’s resilience library:
- [Go Retry Guide](https://pkg.go.dev/github.com/avast/retry-go)
- [Python Tenacity](https://tenacity.readthedocs.io/en/latest/)
- [Node.js Retry-as-Promised](https://github.com/sindresorhus/retry-as-promised)
```