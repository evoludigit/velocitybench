# **[Pattern] Rate Shaping & Flow Control: Reference Guide**

---

## **Overview**
**Rate Shaping & Flow Control** is a distributed system pattern used to manage, limit, or regulate the rate of data transmission between components to prevent overload, ensure fairness, and optimize performance. This pattern applies to scenarios where bursts of traffic, high-latency connections, or resource constraints could degrade system reliability or user experience.

The pattern enforces **rate limits** (controls the total volume of data transmitted over time) and **flow control** (adjusts transmission speed in real-time based on network or resource conditions). It is widely used in:

- **Networking** (e.g., TCP flow control, QoS policies)
- **Microservices & APIs** (e.g., limiting requests to prevent throttling)
- **Databases** (e.g., query rate limiting to avoid deadlocks)
- **Real-time systems** (e.g., buffering to smooth latency spikes)

By decoupling producers from consumers, this pattern ensures stable throughput while mitigating cascading failures.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Example Use Cases**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Token Bucket**          | Allows bursts of traffic up to a capacity, then refills tokens at a fixed rate.                                                                                                                                    | API rate limiting, disk I/O scheduling.                                                                     |
| **Leaky Bucket**          | Processes items at a constant rate; excess data is dropped.                                                                                                                                                      | Network traffic policing, logging rate limiting.                                                          |
| **Fixed Window**          | Divides time into fixed intervals and enforces a limit per window (e.g., 100 requests/second).                                                                                                                | Database query throttling, firewall rules.                                                                |
| **Sliding Window**        | Tracks usage over a dynamic time window (e.g., last 60 seconds) for smoother rate limiting.                                                                                                                    | Microservice call limits, distributed caching.                                                             |
| **Backpressure**          | Signals slower consumers to pause production; often tied to buffer thresholds.                                                                                                                                  | Kafka consumers, message queues.                                                                           |
| **Adaptive Thresholds**   | Dynamically adjusts limits based on system metrics (e.g., CPU load).                                                                                                                                           | Auto-scaling API gateways, cloud function invocations.                                                     |

---

## **Schema Reference**
Below are standardized data structures for implementing rate shaping/flow control. Use these as templates or adapt to your tech stack.

### **1. Rate Limit Configuration**
```json
{
  "rate_limit": {
    "type": "token_bucket" | "leaky_bucket" | "fixed_window" | "sliding_window",
    "limit": 100,                     // Max units (e.g., requests/sec)
    "interval": 60,                   // Refill interval (sec) for Token Bucket
    "burst_capacity": 200,            // Max burst size (Token Bucket only)
    "queue_depth": 1000,              // Buffer size (Leaky Bucket/Backpressure)
    "adaptive": false,                // Enable dynamic adjustments
    "adjustment_metric": "cpu_usage"  // e.g., "memory_utilization"
  }
}
```

### **2. Flow Control Signal**
| **Field**          | **Type**   | **Description**                                                                                                                                                     | **Example Values**                     |
|--------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------|
| `status`           | String     | Current flow state (`active`, `throttled`, `backpressured`, `error`).                                                                                              | `"throttled"`                           |
| `remaining_units`  | Integer    | Tokens left in the current window/bucket.                                                                                                                       | `32`                                     |
| `next_refill_ts`   | Timestamp  | When the next token will be available (for Token Bucket).                                                                                                       | `1712345678901` (UTC)                   |
| `queue_length`     | Integer    | Items waiting in the buffer (Backpressure).                                                                                                                     | `150`                                    |
| `reason`           | String     | Why throttling occurred (e.g., `rate_exceeded`, `consumer_slow`).                                                                                                | `"consumer_slow"`                       |
| `retry_after`      | Integer    | Milliseconds to wait before retrying (if applicable).                                                                                                             | `5000` (5 seconds)                      |

---

## **Implementation Examples**

### **1. Token Bucket in Python (Flask API)**
```python
from flask import Flask, request, jsonify
from ratelimit import limits, RateLimitExceeded

app = Flask(__name__)

@app.route("/api/data", methods=["GET"])
@limits(calls=100, period=60)  # 100 requests/minute
def fetch_data():
    return jsonify({"data": "sample"})

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return jsonify({"error": "Rate limit exceeded"}), 429
```
**Dependencies**:
```bash
pip install flask ratelimit
```

---

### **2. Sliding Window in Java (Spring Boot)**
```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import com.github.benmanes.caffeine.cache.Cache;
import java.util.concurrent.TimeUnit;

@RestController
public class RateLimitController {
    private final Cache<String, Integer> requestCache = Cache.builder()
            .expireAfterWrite(60, TimeUnit.SECONDS)
            .maximumSize(1000)
            .build();

    @GetMapping("/api/resource")
    public String getResource() {
        String key = request.getRemoteAddr(); // Or use user ID
        requestCache.put(key, requestCache.getIfPresent(key, k -> 0) + 1);
        Integer count = requestCache.get(key, k -> 0);
        if (count > 50) { // 50 requests/minute window
            throw new RateLimitExceededException();
        }
        return "Resource fetched";
    }
}
```
**Dependencies**:
```xml
<dependency>
    <groupId>com.github.benmanes</groupId>
    <artifactId>caffeine</artifactId>
    <version>3.1.5</version>
</dependency>
```

---

### **3. Backpressure in Go (Buffer-Based)**
```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type Buffer struct {
	mu        sync.Mutex
	data      []string
	capacity  int
	notify    chan struct{}
}

func (b *Buffer) Push(data string) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if len(b.data) >= b.capacity {
		<-b.notify // Wait if buffer is full
	}
	b.data = append(b.data, data)
}

func (b *Buffer) Pop() (string, bool) {
	b.mu.Lock()
	defer b.mu.Unlock()
	if len(b.data) == 0 {
		return "", false
	}
	data := b.data[0]
	b.data = b.data[1:]
	close(b.notify) // Notify if waiting
	return data, true
}

func main() {
	buffer := &Buffer{capacity: 10}
	go func() {
		for i := 0; i < 20; i++ {
			buffer.Push(fmt.Sprintf("item%d", i))
			time.Sleep(100 * time.Millisecond)
		}
	}()
	for {
		data, ok := buffer.Pop()
		if !ok {
			break
		}
		fmt.Println("Popped:", data)
	}
}
```

---

## **Query Examples (Database/Monitoring)**
### **1. Check Rate Limit Status (SQL)**
```sql
-- Track requests per user in a 1-minute sliding window
SELECT
    user_id,
    COUNT(*) as request_count,
    SUM(CASE WHEN timestamp > NOW() - INTERVAL '1 minute' THEN 1 ELSE 0 END) as recent_requests
FROM requests
WHERE timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY user_id
HAVING recent_requests > 100;
```

### **2. Prometheus Metrics for Flow Control**
```promql
# alert if HTTP requests exceed rate limit
rate(http_requests_total{status="2xx"}[1m]) > 100

# buffer backpressure level
sum(rate(buffer_fill_level[1m])) by (service) > 0.8
```

### **3. Kafka Consumer Lag Monitoring**
```bash
# Check if consumer is falling behind due to slow processing
kafka-consumer-groups --bootstrap-server broker:9092 --describe --group my-group
```
**Look for**:
- `LAG`: Number of unprocessed messages.
- `THROTTLE_TIME_MS`: Backpressure applied by the broker.

---

## **Best Practices**
1. **Granularity**: Apply limits at the right level (e.g., per user, per IP, or per API endpoint).
2. **Fairness**: Use weighted limits (e.g., gold/silver tier users) if needed.
3. **Graceful Degradation**: Log throttled requests for analytics (e.g., `429 Too Many Requests`).
4. **Dynamic Adjustments**: Enable `adaptive: true` if your system can auto-scale (e.g., based on CPU/memory).
5. **Testing**: Simulate traffic spikes with tools like **Locust** or **JMeter** to validate limits.
6. **Client-Side Hints**: Return `Retry-After` headers for HTTP APIs to guide clients.

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use Together**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/circuit-breaker.html)** | Stop cascading failures by halting calls to unhealthy services.           | Use with Rate Limiting to avoid overwhelming a recovering service.                                          |
| **[Bulkhead](https://microservices.io/patterns/reliability/bulkhead.html)** | Isolate resource-heavy operations to prevent one failure from affecting others. | Combine with Flow Control to limit concurrent operations (e.g., database connections).                      |
| **[Retry with Exponential Backoff](https://docs.aws.amazon.com/whitepapers/latest/well-architected-patterns/retry-pattern.html)** | Handle transient failures gracefully.                                      | Pair with Rate Limiting to avoid retry storms.                                                               |
| **[Queue-Based Asynchrony](https://microservices.io/patterns/data/queue.html)** | Decouple producers/consumers to handle spikes.                             | Use for Backpressure: Queue messages when consumers are slow.                                                |
| **[Rate Limiter as a Service](https://cloud.google.com/blog/products/api-management/rate-limiting-with-cloud-endpoints)** | Centralized rate limiting for APIs.                                        | Deploy a dedicated service (e.g., Redis + Nginx) for cross-service limits.                                   |

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                                                                 | **Solution**                                                                                                   |
|-------------------------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **False Positives on Limits**       | Clock skew in distributed systems.                                            | Use [NTP](https://www.ietf.org/rfc/rfc5905.txt) for synchronized time.                                        |
| **Burst Rejections**                | Token Bucket burst_capacity too low.                                           | Increase `burst_capacity` or switch to a Leaky Bucket.                                                         |
| **High Latency Under Load**         | Backpressure not triggered early enough.                                      | Monitor `queue_length` and adjust thresholds proactively.                                                     |
| **Unfair Distribution**             | Fixed-time windows misalign with user activity.                               | Use **Sliding Window** for smoother rate limiting.                                                             |
| **Client Ignores Retry-After**       | No client-side enforcement of `Retry-After`.                                   | Implement retry logic in clients (e.g., HTTP clients with exponential backoff).                               |

---
**See also**:
- [IETF RFC 6587 (Rate Limiting for HTTP)](https://datatracker.ietf.org/doc/html/rfc6587)
- [AWS Rate Limiting Guide](https://docs.aws.amazon.com/whitepapers/latest/well-architected-patterns/retry-pattern.html)