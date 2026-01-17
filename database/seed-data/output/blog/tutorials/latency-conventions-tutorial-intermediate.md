```markdown
# **Latency Conventions: Structuring APIs for Real-Time Performance Expectations**

*How to design APIs that explicitly communicate response time guarantees—and why it matters*

## **Introduction**

APIs are no longer just about *what* data you return—they’re also about *when* you return it. In today’s zero-latency-acceptable world, users expect responses in milliseconds. Whether you’re building a high-frequency trading platform, a social media feed, or a gaming API, unmet latency expectations can lead to fractured user experiences, failed transactions, and lost revenue.

But how do you *design* an API to meet these expectations? How do you make it clear to consumers—which endpoints are fast, which are slow, and which might block or time-out? This is where **"latency conventions"** come in—not just as an afterthought, but as a fundamental design principle.

In this post, we’ll explore why conventionalizing latency matters, how leading systems structure APIs around it, and practical code examples to implement this pattern. We’ll also discuss trade-offs, common pitfalls, and when this pattern (or its alternatives) make the most sense for your system.

---

## **The Problem: When APIs Don’t Communicate Their Latency**

### **Silent Blocking: The User Experience Killer**
Imagine a mobile app where a "Submit Payment" button triggers an API call that takes **3 seconds** on average—but sometimes **15 seconds** during peak load. Users don’t know to wait. They assume something went wrong and tap "Back" or "Cancel," leaving your service with no chance to recover.

This is the **latency mismatch problem**: The API’s actual performance doesn’t match user expectations.

### **Poor API Documentation Leads to Technical Debt**
APIs often document:
- Input schemas
- Output schemas
- Success/failure response codes

But where’s the documentation on:
- Expected response time?
- Expected failure modes and retry strategies?
- Guaranteed vs. best-effort SLAs?

Without explicit latency conventions, API consumers are left guessing—which can lead to:
- Overly aggressive retries (wasting resources).
- Undersized clients (failing silently).
- Inconsistent error handling (some endpoints retry, others don’t).

### **Real-World Example: The E-Commerce Checkout API**
Consider an e-commerce API with these endpoints:
```json
{
  "get_cart_items": "Fast (avg 200ms)",
  "apply_discount": "Variable (avg 1s, can block)",
  "place_order": "Fast (avg 500ms)"
}
```
A naive implementation might treat all endpoints equally:
```typescript
// Client-side retry logic (bad)
async function tryPlaceOrder() {
  let attempts = 0;
  while (attempts < 3) {
    await api.place_order(); // No awareness of latency
    attempts++;
  }
}
```
In reality:
- `apply_discount` might block due to external services.
- `place_order` could be slow if involving payment gateways.

Without latency conventions, the client either:
- Retries `place_order` too aggressively (costly).
- Gives up too soon (user drop-off).

---

## **The Solution: Latency Conventions**

### **Core Idea**
Latency conventions are **explicit design patterns** that:
1. **Classify endpoints by performance characteristics** (e.g., "fast," "blocking," "streaming").
2. **Document these classifications in API specs** (OpenAPI, Protobuf, or custom).
3. **Enforce them at the client and server levels** (e.g., via timeouts, retries, or caching).

### **Why It Works**
- **Client-side awareness**: Consumers know which endpoints to retry, which to cache, and when to fallback.
- **Server-side optimizations**: Teams can focus on performance-critical paths.
- **Clear contracts**: No more "Surprise Latency" incidents.

---

## **Components of Latency Conventions**

### **1. Endpoint Classification**
Classify endpoints based on:
- **Response time** (e.g., <100ms, 100ms–1s, >1s).
- **Predictability** (e.g., deterministic vs. variable).
- **Side effects** (e.g., blocking vs. eventual consistency).

#### **Example: OpenAPI Extensions**
```yaml
openapi: 3.0.0
paths:
  /fast-endpoint:
    get:
      summary: "Fast listing (avg 50ms)"
      responses:
        200:
          description: "Cached response"
          headers:
            X-Latency-Class: "fast"
  /expensive-endpoint:
    get:
      summary: "Blocking operation (avg 2s)"
      responses:
        200:
          description: "Eventual consistency"
          headers:
            X-Latency-Class: "slow|blocking"
```

### **2. HTTP Headers for Latency Hints**
Expose latency hints via headers (e.g., `X-Latency-Class`, `Retry-After`):
```http
GET /analytics HTTP/1.1
X-Latency-Class: slow|eventual
Retry-After: 30  # Suggested retry delay

HTTP/1.1 200 OK
Content-Type: application/json
X-Latency-Class: fast|cached
```

### **3. Timeouts and Circuit Breakers**
- **Server-side**: Enforce timeouts for slow endpoints.
  ```go
  // Go example: Timeout for slow endpoint
  ctx, cancel := context.WithTimeout(ctx, 1*time.Second)
  defer cancel()
  data, _ := client.Get(ctx, "/slow-endpoint")
  ```
- **Client-side**: Use exponential backoff for slow/blocking endpoints.

### **4. Caching Strategies**
- **Fast endpoints**: Cache aggressively.
- **Slow/blocking endpoints**: Avoid caching or use stale-while-revalidate.

---

## **Code Examples**

### **Example 1: Fast Endpoint (Cached)**
```python
# Fast read-only endpoint (cached)
@app.get("/fast-items")
async def get_fast_items():
    cached_data = cache.get("items")
    if cached_data:
        return cached_data
    data = db.find_all()  # Simulate 50ms DB query
    cache.set("items", data, timeout=60)  # Cache for 60s
    return data
```

### **Example 2: Slow Endpoint (With Timeout)**
```typescript
// Slow endpoint with timeout (TypeScript)
async function getSlowData(url: string, maxRetries = 3) {
  let attempt = 0;
  while (attempt < maxRetries) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout
      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      return response.json();
    } catch (err) {
      attempt++;
      if (attempt === maxRetries) throw err;
      await new Promise(resolve => setTimeout(resolve, 1000)); // Exponential backoff
    }
  }
}
```

### **Example 3: Blocking Endpoint (With Async Processing)**
```java
// Java: Asynchronous processing for blocking tasks
public CompletableFuture<TransactionResponse> placeOrder(Order order) {
  return CompletableFuture.supplyAsync(() -> {
    // Simulate slow payment processing
    Thread.sleep(3000);
    return new TransactionResponse("Success", "Pending");
  });
}
```

---

## **Implementation Guide**

### **Step 1: Audit Your API**
- Identify endpoints with variable latency.
- Classify them as:
  - **Fast** (<100ms)
  - **Slow** (100ms–1s)
  - **Blocking** (>1s, may time out)
  - **Eventual** (e.g., Webhooks, async processing)

### **Step 2: Add Latency Headers**
Extend your OpenAPI/Swagger docs:
```yaml
components:
  headers:
    X-Latency-Class:
      schema:
        type: string
        enum: [fast, slow, blocking, eventual]
```

### **Step 3: Enforce Timeouts**
- **Server**: Use frameworks like FastAPI, Express, or Spring WebFlux to set request timeouts.
- **Client**: Implement retries with exponential backoff.

### **Step 4: Document Client-Side Behavior**
Provide examples of how to handle each class:
```markdown
### Fast Endpoint Usage
```javascript
// No retries needed—just cache aggressively
const data = await fetchCachedData("/fast-items");
```

### Blocking Endpoint Usage
```javascript
// Use async processing or polling
await asyncPlaceOrder(order, { retry: true });
```

### Eventual Endpoint Usage
```javascript
// Poll for status or use webhooks
const txId = await placeOrderAsync(order);
const status = await pollStatus(txId); // Or set up webhook listener
```

---

## **Common Mistakes to Avoid**

### **1. Ignoring Latency in Documentation**
API docs should **explicitly** note:
- Expected response times.
- Whether an endpoint is blocking or non-blocking.
- Required retries/retry strategies.

### **2. Over-Reliance on Timeouts**
Timeouts alone don’t solve latency issues. Combine them with:
- Caching for fast endpoints.
- Async processing for blocking endpoints.

### **3. Inconsistent Latency Classification**
Don’t mix "fast" and "slow" endpoints in the same system without clear demarcation. Example:
```python
# Bad: Mixed latency in one endpoint
@app.get("/mixed")
def mixed_endpoint():
    fast_data = cache.get("fast")  # 50ms
    slow_data = db.query_slowly() # 2s
    return { "fast": fast_data, "slow": slow_data }  # User waits 2s for fast data!
```

### **4. Not Handling Retries Correctly**
- **Fast endpoints**: No retries (idempotent).
- **Slow/blocking endpoints**: Exponential backoff.
- **Eventual endpoints**: Poll or use webhooks.

### **5. Assuming All Clients Understand Latency**
Not every client will implement retry logic. Provide:
- SDKs with built-in retries.
- Clear error messages (e.g., `429 Too Many Requests`).

---

## **Key Takeaways**
✅ **Latency conventions** make APIs explicit about performance expectations.
✅ **Classify endpoints** as fast, slow, blocking, or eventual.
✅ **Use HTTP headers** (`X-Latency-Class`) to document latency.
✅ **Enforce timeouts** and implement retries where needed.
✅ **Cache fast endpoints**, async-process slow ones.
✅ **Document client behavior** for each latency class.
❌ **Avoid silent blocking**—users and clients must know what to expect.
❌ **Don’t mix latency types** in the same endpoint.
❌ **Assume clients won’t handle retries**—provide SDKs or clear guidance.

---

## **Conclusion**

Latency conventions aren’t just an optimization—they’re a **contract** between your API and its consumers. By explicitly defining how long operations take, you:
- Reduce user frustration.
- Avoid technical debt from silent failures.
- Enable better client implementations.

Start small:
1. Audit your slowest endpoints.
2. Add latency headers to your API docs.
3. Enforce timeouts and provide retries where appropriate.

The result? APIs that feel **instant**—even when they’re not. Because in the world of user expectations, **perception is performance**.

---
**Further Reading**
- [AWS API Gateway Latency Best Practices](https://aws.amazon.com/blogs/compute/optimizing-microservices-latency-with-amazon-api-gateway/)
- [Google’s gRPC Timeout and Deadline Handling](https://grpc.io/docs/guides/timeouts/)
- [FastAPI Caching](https://fastapi.tiangolo.com/tutorial/caching/)

**Try It Out**
Clone [this example repo](https://github.com/your-repo/latency-conventions-demo) and experiment with timeouts, caching, and async processing!
```