```markdown
# **API Client Patterns: Designing Robust and Maintainable REST Clients**

You've built a beautiful API—now you need to consume it. Whether you're working with a third-party service like Stripe or a microservice in your own stack, writing client code can quickly become messy if you don't follow intentional patterns. Poorly designed API clients often lead to:
- **Spaghetti code** (every request handled differently)
- **Hard-to-debug errors** (no consistent error handling)
- **Flaky integrations** (no retries, no rate-limiting, no idempotency)
- **Tight coupling** (business logic mixed with HTTP calls)

This tutorial covers **API client patterns**—best practices for writing clean, resilient, and maintainable HTTP clients in backend applications. We'll explore:
- **Core components** of a proper API client
- **Real-world implementations** in Go, Python, and JavaScript
- **Tradeoffs** and when to bend (or break) the rules
- **Common pitfalls** and how to avoid them

By the end, you'll have the tools to write clients that are as robust as the APIs you call.

---

## **The Problem: Why API Clients Go Wrong**

API consumption is often an afterthought. Developers might start with simple `fetch` calls in JavaScript or `requests` in Python, but as complexity grows, the codebase becomes a nightmare. Here are common issues:

### **1. No Error Handling**
```javascript
// ❌ Poor error handling
fetch("https://api.example.com/data")
  .then(res => res.json())
  .then(json => console.log(json));
```
What if the API returns a `404`? What if the network fails? Without proper error handling, failures are silent or catastrophic.

### **2. No Retry Logic**
APIs sometimes fail temporarily due to network issues or rate limits. A client that never retries will break under load.

### **3. Hardcoded Requests**
Every API call is written manually, leading to:
- **Duplicate code** (e.g., always adding `Authorization` headers)
- **Inconsistent parameter formats**
- **No type safety** (JSON parsed as raw objects)

### **4. No Rate Limiting or Throttling**
Hitting an API too aggressively can lead to:
- Temporary bans
- Increased latency due to backoff
- Wasted resources

### **5. No Reusability**
Each client is a one-off. Want to use the same API in another service? You’re rewriting everything.

---

## **The Solution: API Client Patterns**

A well-designed API client follows these principles:
✅ **Decouple HTTP from business logic** (clients should be stateless)
✅ **Standardize error handling** (consistent responses for failures)
✅ **Support retries and timeouts** (handle transient failures gracefully)
✅ **Be configurable** (base URLs, headers, timeouts should be injectable)
✅ **Be type-safe** (use strong typing where possible)
✅ **Support async operations** (non-blocking requests)

---

## **Components of a Robust API Client**

A good API client has three layers:

### **1. Transport Layer**
Handles raw HTTP requests. This is where libraries like `http.Client` (Go), `requests` (Python), or `axios` (JavaScript) live.
**Tradeoff:** Over-reliance on a HTTP library can make it harder to mock or test.

### **2. Client Layer**
Wrap transport calls with business logic:
- **Request formatting** (query params, headers, body)
- **Error handling** (convert HTTP errors to domain errors)
- **Retry logic**
- **Rate limiting**
**Tradeoff:** Adds complexity but pays off in maintainability.

### **3. Business Layer**
Uses the client to interact with the API in a way that makes sense for your app.
**Example:** A "UserService" might call the API client to fetch or create users.

---

## **Implementation Guide: Code Examples**

Let’s build a **Go**, **Python**, and **JavaScript** client for a hypothetical `Order` API.

---

### **1. Go Example: Structured Client with Retries**
```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Order represents the expected API response.
type Order struct {
	ID     string    `json:"id"`
	Status string    `json:"status"`
	Items  []Item    `json:"items"`
}
type Item struct {
	ProductID string `json:"product_id"`
	Quantity  int    `json:"quantity"`
}

// Client wraps HTTP calls with retries and timeouts.
type Client struct {
	baseURL   string
	httpClient *http.Client
}

// NewClient creates a new API client.
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL:   baseURL,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// GetOrder retrieves an order with retry logic.
func (c *Client) GetOrder(ctx context.Context, orderID string) (*Order, error) {
	url := fmt.Sprintf("%s/orders/%s", c.baseURL, orderID)
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	var order Order
	err = c.doWithRetry(ctx, req, &order)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch order: %v", err)
	}

	return &order, nil
}

// doWithRetry retries on temporary failures.
func (c *Client) doWithRetry(
	ctx context.Context,
	req *http.Request,
	v interface{},
) error {
	var lastErr error
	for i := 0; i < 3; i++ { // Max 3 retries
		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = err
		} else {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return json.NewDecoder(resp.Body).Decode(v)
			}
			lastErr = fmt.Errorf("unexpected status: %s", resp.Status)
		}
		time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
	}
	return lastErr
}

func main() {
	client := NewClient("https://api.example.com/v1")
	order, err := client.GetOrder(context.Background(), "123")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	fmt.Printf("Order: %+v\n", order)
}
```

**Key Takeaways:**
- **Retry logic** (3 attempts with exponential backoff)
- **Context support** (cancellation support)
- **Type safety** (`Order` struct enforces response shape)

---

### **2. Python Example: Using `requests` with Retries**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional

class OrderAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_order(self, order_id: str) -> Optional[dict]:
        url = f"{self.base_url}/orders/{order_id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()  # Raises HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch order: {e}")
            return None

if __name__ == "__main__":
    client = OrderAPIClient("https://api.example.com/v1")
    order = client.get_order("123")
    if order:
        print(order)
```

**Key Takeaways:**
- **Retry strategy** (using `urllib3.Retry`)
- **Session reuse** (better performance)
- **Type hints** (better IDE support)

---

### **3. JavaScript Example: Axios with Interceptors**
```javascript
import axios from "axios";
import { RateLimiter } from "limiter";

// Configure a rate limiter (e.g., 10 requests per second)
const rateLimiter = new RateLimiter({ tokensPerInterval: 10, interval: "second" });

const apiClient = axios.create({
  baseURL: "https://api.example.com/v1",
  timeout: 10000,
});

// Add request interceptor for rate limiting
apiClient.interceptors.request.use(async (config) => {
  await rateLimiter.removeTokens(1);
  return config;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // API responded with a non-2xx status
      throw new Error(`API error: ${error.response.status}`);
    } else if (error.request) {
      // Request was made but no response (e.g., network issue)
      throw new Error("Network error: request timed out or failed");
    } else {
      // Something else happened (e.g., Axios config error)
      throw new Error("Unexpected error: " + error.message);
    }
  }
);

// Example usage
async function fetchOrder(orderId) {
  try {
    const order = await apiClient.get(`/orders/${orderId}`);
    return order;
  } catch (err) {
    console.error("Failed to fetch order:", err);
    throw err;
  }
}

// Usage
fetchOrder("123")
  .then((order) => console.log(order))
  .catch((err) => console.error(err));
```

**Key Takeaways:**
- **Rate limiting** (prevents hitting API limits)
- **Axios interceptors** (consistent error handling)
- **Clean async/await** (better readability)

---

## **Common Mistakes to Avoid**

### **1. Not Handling Timeouts**
Always set a timeout. Without one, your app could hang indefinitely on slow APIs.
```javascript
// ❌ No timeout (bad)
axios.get(url);

// ✅ With timeout (good)
axios.get(url, { timeout: 10000 });
```

### **2. Ignoring HTTP Status Codes**
Treat `4xx` and `5xx` errors differently. A `404` might mean "valid but not found," while a `503` means "try again later."
```go
// ❌ Treats all errors the same
err := c.do(req)

// ✅ Handles different status codes
if resp.StatusCode == http.StatusNotFound {
  return nil, nil // "Not found" is a valid case
}
```

### **3. Hardcoding API URLs**
Use environment variables or config files for base URLs.
```javascript
// ❌ Hardcoded (bad)
const url = "https://api.example.com/v1";

// ✅ Configurable (good)
const baseURL = process.env.API_BASE_URL || "https://api.example.com/v1";
```

### **4. No Retry Logic for Transient Failures**
Assume all network calls can fail. Implement retries for `5xx` errors and timeouts.
```python
# ❌ No retries (bad)
response = self.session.get(url)

// ✅ With retries (good)
retry_strategy = Retry(total=3, backoff_factor=0.3)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
```

### **5. Mixing Business Logic with HTTP**
Keep clients stateless. Move business logic (e.g., validation) to a separate service.
```go
// ❌ Business logic in client (bad)
func (c *Client) GetOrder(ctx context.Context, orderID string) (*Order, error) {
  order, err := c.fetchOrder(orderID) // <-- HTTP call
  if err != nil {
    return nil, err
  }
  if order.Status != "fulfilled" { // <-- Business logic
    return nil, errors.New("order not ready")
  }
  return order, nil
}

// ✅ Client is stateless (good)
func (c *Client) GetOrder(ctx context.Context, orderID string) (*Order, error) {
  return c.fetchOrder(orderID)
}

// Business logic goes in a separate service
func (s *OrderService) GetReadyOrder(orderID string) (*Order, error) {
  order, err := s.client.GetOrder(context.Background(), orderID)
  if err != nil || order.Status != "fulfilled" {
    return nil, errors.New("order not ready")
  }
  return order, nil
}
```

---

## **Key Takeaways**
Here’s what you should remember:

✔ **Decouple HTTP from business logic** – Clients should not know about your app’s domain.
✔ **Standardize errors** – Always return consistent error types.
✔ **Use retries for transient failures** – Networks are unreliable.
✔ **Add timeouts** – Prevent hanging indefinitely.
✔ **Support rate limiting** – Avoid being blocked by APIs.
✔ **Be type-safe** – Use structs/interfaces to enforce data contracts.
✔ **Use config over hardcoding** – Store endpoints, tokens, and timeouts externally.
✔ **Mock clients in tests** – Avoid flaky integration tests.

---

## **Conclusion**

API clients are the glue that holds distributed systems together. Poorly written clients lead to spaghetti code, flaky integrations, and debugging nightmares. By following these patterns, you’ll write clients that are:
- **Resilient** (handle failures gracefully)
- **Maintainable** (clean separation of concerns)
- **Reusable** (work across services)
- **Type-safe** (fewer runtime bugs)

Start small—you don’t need all these features immediately. But as your system grows, revisit your clients and apply these principles. A well-designed client today will save you hours of debugging tomorrow.

**Next Steps:**
- Experiment with mocking HTTP clients in tests.
- Try integrating with a real API (e.g., Stripe, Mapbox) using these patterns.
- Explore libraries like [Go’s `httptest`](https://pkg.go.dev/net/http/httptest), [Python’s `responses`](https://github.com/getsentry/responses), or [JavaScript’s `msw`](https://mswjs.io/) for mocking.

Happy coding!
```