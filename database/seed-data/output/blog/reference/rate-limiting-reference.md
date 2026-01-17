# **[Pattern] API Rate Limiting Reference Guide**

---

## **1. Overview**
API rate limiting enforces request quotas to prevent misuse, ensure system stability, and distribute load fairly. Common use cases include:

- **Security:** Mitigating DDoS attacks and credential stuffing.
- **Cost Control:** Limiting scraping or batch operations that incur per-request costs.
- **Stability:** Preventing cascading failures by throttling excessive requests.
- **Fairness:** Enforcing consistent service levels for all clients.

This pattern defines patterns for tracking request counts, applying limits, and handling violations (e.g., retries or 429 responses). Algorithms like **fixed window**, **sliding window**, **token bucket**, and **leaky bucket** each balance complexity and accuracy.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**       | **Description**                                                                 |
|---------------------|-------------------------------------------------------------------------------|
| **Time Window**     | Interval (e.g., 1 minute, 1 hour) over which requests are counted.           |
| **Rate Limit**      | Maximum number of requests allowed per window (e.g., 100 requests/minute). |
| **Counter**         | Tracks request counts per client (IP address, API key, or user).              |
| **Decision Engine** | Evaluates requests against limits using predefined algorithms.              |
| **Violation Handler** | Defines responses for exceeding limits (e.g., `429 Too Many Requests`).      |

---

### **2.2 Rate Limiting Algorithms**
Compare four common approaches by **accuracy**, **complexity**, and **use cases**:

| **Algorithm**       | **How It Works**                                                                 | **Pros**                              | **Cons**                              | **Use Case**                          |
|---------------------|-------------------------------------------------------------------------------|---------------------------------------|---------------------------------------|---------------------------------------|
| **Fixed Window**    | Divides time into fixed buckets (e.g., every minute). Resets counter at window boundaries. | Simple, low overhead.                | Can allow bursts at window edges.      | Low-cost, coarse-grained limits.      |
| **Sliding Window Log** | Maintains timestamps of recent requests; counts within the last `N` seconds. | Accurate for short windows.          | High memory usage for many requests.  | Precision-heavy scenarios (e.g., bots).|
| **Sliding Window Counter** | Approximates counts using delta = `(current time - last reset) / window size`. | Balanced accuracy and memory.        | Slight inaccuracy at edges.           | General-purpose limits.              |
| **Token Bucket**    | Replenishes tokens at a fixed rate; requests consume tokens.                 | Allows burst traffic.                | Complex to implement.                 | High-variance workloads (e.g., IoT).   |
| **Leaky Bucket**    | Requests enter at a fixed rate; excesses are dropped or queued.               | Predictable throughput.               | High latency for bursts.              | Time-sensitive systems (e.g., sensors).|

---
**Recommendation:**
- Use **sliding window counter** for most cases (trade-off between accuracy and simplicity).
- Use **token bucket** if burst tolerance is critical (e.g., mobile apps).
- Avoid **fixed window** for precise enforcement.

---

### **2.3 Example Flow**
1. **Client Request:** A request arrives with an `X-Client-ID` header (e.g., API key).
2. **Counter Lookup:** The system checks the client’s request count in the current window.
3. **Decision:** If counts < limit, the request proceeds. Otherwise:
   - **Option 1:** Return `429` with `Retry-After` header (e.g., `Retry-After: 30`).
   - **Option 2:** Queue requests (leaky bucket) or allow partial access (token bucket).
4. **Update Counter:** Increment the client’s count and reset the window if needed.

---
**Note:** Distributed systems require coordination (e.g., Redis) to share counters across instances.

---

## **3. Schema Reference**
### **3.1 Rate Limit Configuration**
| **Field**          | **Type**   | **Description**                                                                 | **Example Value**               |
|--------------------|------------|-------------------------------------------------------------------------------|----------------------------------|
| `limit`            | Integer    | Max requests per window.                                                     | `100`                            |
| `window_ms`        | Integer    | Window duration in milliseconds.                                              | `60000` (1 minute)               |
| `algorithm`        | Enum       | One of: `fixed_window`, `sliding_window`, `token_bucket`, `leaky_bucket`. | `sliding_window`                 |
| `tokens_per_sec`   | Float      | Token replenish rate (token bucket only).                                     | `2.0` (2 tokens/sec)             |
| `bucket_capacity`  | Integer    | Max tokens in bucket (token bucket only).                                    | `50`                             |
| `drop_policy`      | Enum       | For leaky bucket: `drop` or `queue`.                                          | `drop`                           |

---
### **3.2 Client Rate Limit Record**
| **Field**          | **Type**   | **Description**                                                                 | **Example**                      |
|--------------------|------------|-------------------------------------------------------------------------------|----------------------------------|
| `client_id`        | String     | Unique identifier (IP, API key, user ID).                                     | `"user_123"` or `"192.0.2.1"`    |
| `total_requests`   | Integer    | Cumulative requests in current window.                                        | `98`                             |
| `last_reset`       | Timestamp  | When the counter was last reset (fixed window) or last token replenish (token bucket). | `2023-10-01T12:00:00Z` |
| `queue_size`       | Integer    | Pending requests (leaky bucket only).                                         | `3`                              |

---

## **4. Query Examples**
### **4.1 Checking Limits**
**Request:**
```http
GET /api/rate-limit?client_id=user_123&window=60s HTTP/1.1
```

**Response (JSON):**
```json
{
  "limit": 100,
  "remaining": 2,
  "reset_time": "2023-10-01T12:01:00Z",
  "algorithm": "sliding_window"
}
```

---
### **4.2 Updating a Rate Limit**
**Request (PUT):**
```http
PUT /api/rate-limit/user_123
Content-Type: application/json

{
  "limit": 50,
  "window_ms": 30000,
  "algorithm": "token_bucket",
  "tokens_per_sec": 1.666
}
```

**Response:**
```json
{
  "status": "success",
  "new_limit": 50,
  "window_size": "30s"
}
```

---
### **4.3 Handling a Violation**
**Request (Exceeds Limit):**
```http
GET /api/data?client_id=user_123 HTTP/1.1
```

**Response (429):**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 15
{
  "error": "rate_limit_exceeded",
  "remaining": 0,
  "limit": 100,
  "reset_time": "2023-10-01T12:05:00Z"
}
```

---

## **5. Implementation Considerations**
### **5.1 Data Storage**
- **In-Memory (Single Node):** Use a `HashMap` (e.g., Java `ConcurrentHashMap`) for low latency.
- **Distributed (Multi-Node):** Use Redis (with `INCR`, `EXPIRE`, or Lua scripts for atomic updates).
- **Persistent Storage:** Databases (e.g., PostgreSQL) for audit logs or long-term limits.

---
### **5.2 Client-Side Retry Logic**
Clients should:
1. Check `Retry-After` header and retry after the specified delay.
2. Use exponential backoff (e.g., `delay = delay * 2` on failure).
3. Implement client-side caching of limits to reduce server load.

**Pseudocode:**
```python
def make_request(url, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers={"X-Retry": str(retries)})
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 5)
                time.sleep(retry_after)
                retries += 1
                continue
            return response
        except requests.exceptions.RequestException:
            retries += 1
            time.sleep(2 ** retries)
    raise Exception("Max retries exceeded")
```

---
### **5.3 Edge Cases**
| **Scenario**               | **Handling**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Client IP Rotation**     | Use API keys or session tokens instead of IPs.                              |
| **Burst Traffic**          | Token bucket or sliding window with larger windows.                         |
| **Distributed Clients**    | Federate counters across regions (e.g., Redis Cluster).                     |
| **Time Sync Issues**       | Use monotonic time or NTP-synchronized clocks.                              |

---

## **6. Benchmarking & Tuning**
| **Metric**          | **Tool**               | **Recommendation**                          |
|---------------------|------------------------|---------------------------------------------|
| **Latency**         | `ab` (Apache Bench)    | Target <50ms for 99th percentile.           |
| **Throughput**      | `wrk`                  | Ensure system handles 1.2x the limit.       |
| **Memory Usage**    | `valgrind`/`htop`      | Optimize Redis/TLS overhead.                |
| **Accuracy**        | Custom load tester     | Validate sliding window doesn’t leak requests.|

**Tuning Tips:**
- Start with **sliding window counter** and adjust `window_ms` based on traffic patterns.
- For token buckets, set `tokens_per_sec = limit / window_ms`.
- Monitor `remaining` counts to detect anomalies (e.g., sudden spikes).

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **[Circuit Breaker]**     | Temporarily stops calls to failing services to prevent cascading failures.      | Combine with rate limiting for APIs.     |
| **[Exponential Backoff]** | Delays retries after failures to reduce load.                               | Pair with `429` responses.                |
| **[Request Tracing]**     | Correlates requests across services for debugging.                           | Audit rate limit violations.              |
| **[API Versioning]**      | Manages backward compatibility for evolving APIs.                           | Use separate limits per API version.      |
| **[Consistent Hashing]**  | Distributes load evenly across servers.                                     | Scale rate limit counters horizontally.   |

---
## **8. References**
- **Algorithms:**
  - [Token Bucket Explained](https://medium.com/@nikhilvishwakarma/token-bucket-algorithm-in-depth-explanation-6c01d05f951d)
  - [Sliding Window vs. Fixed Window](https://www.baeldung.com/cs/rate-limiting-algorithms)
- **Infrastructure:**
  - [Redis Rate Limiting](https://redis.io/docs/stack/development/rate-limiting/)
  - [AWS WAF Rate Limiting](https://docs.aws.amazon.com/waf/latest/apireference/wafv2-rate-based-rule.html)
- **Standards:**
  - [RFC 6585 (429 Status Code)](https://tools.ietf.org/html/rfc6585)