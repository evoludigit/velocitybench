**[Pattern] Rate Limiting Algorithms Patterns – Reference Guide**

---

## **Overview**
Rate limiting is a traffic-shaping technique used to regulate API or service usage by enforcing predefined request quotas over a specified time window. This pattern mitigates abuse, ensures fair resource allocation, and prevents system overload by dynamically adjusting request throughput.

Common use cases include:
- **Preventing brute-force attacks** (e.g., login attempts).
- **Enforcing fair consumption** of paid API tiers.
- **Avoiding cascading failures** during high-concurrency events.

This guide covers key **rate-limiting algorithms and schemas**, implementation trade-offs, and query examples for popular patterns.

---

## **1. Schema Reference**

| **Algorithm**       | **Complexity** | **Memory Use** | **Use Case**                          | **Key Properties**                                                                 | **Implementation Notes**                                                                 |
|----------------------|----------------|----------------|----------------------------------------|-------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Fixed Window**     | O(1)           | O(1)           | Simple throttling                     | Divides time into fixed intervals (e.g., 1-min buckets).                          | First request allowed per bucket; subsequent requests blocked until next interval.      |
| **Sliding Window Log** | O(n) per query | O(n)           | Precise rate limiting                  | Tracks exact timestamps of recent requests.                                       | High memory usage for high throughput.                                                   |
| **Sliding Window Counter** | O(1)          | O(1)           | Approximate rate limiting              | Uses a counter reset after each window shift.                                     | May allow bursts above the limit due to rounding errors.                                 |
| **Token Bucket**     | O(1)           | O(1)           | Variable rate limiting                 | Fills tokens at a fixed rate; requests consume tokens.                             | Smoother traffic shaping; bursty requests allowed if tokens are available.               |
| **Leaky Bucket**     | O(1)           | O(1)           | Strict rate limiting                   | Requests are processed at a constant rate; excess is dropped.                       | Strict control but may reject bursts.                                                   |

---

## **2. Key Concepts & Implementation Details**

### **Core Components**
1. **Rate Limit Metric**:
   - Defined as `X requests per Y seconds`.
   - Example: `100 requests/minute`.

2. **Time Window**:
   - Fixed (e.g., 60-second increments).
   - Sliding (e.g., shifts every second).

3. **Counter/Token/Batch**:
   - Tracks allowed usage per window.

### **Algorithm-Specific Logic**
#### **Fixed Window**
- **Example**:
  - Time window: 60s.
  - Limit: 100 requests.
  - At `t=0`: Counter = 0 (bucket opens).
  - At `t=10s`: 100 requests → bucket fills.
  - At `t=60s`: Bucket resets to 0.

**Pros**: Simple, low overhead.
**Cons**: Allows bursts at window transitions.

#### **Sliding Window Log**
- **Example**:
  - Log: `[t=0, t=1, t=2, ...]` (timestamps of recent requests).
  - Compare `len(log) > limit` to allow/reject.

**Pros**: Accurate.
**Cons**: High memory for high rates.

#### **Sliding Window Counter**
- **Example**:
  - Current window: `t=0s` to `t=60s`.
  - Previous window: `t=59s` to `t=119s` (overlap).
  - Interpolate: `current + (remaining cap * overlap ratio)`.

**Pros**: Balances memory and accuracy.
**Cons**: Approximation errors.

#### **Token Bucket**
- **Example**:
  - Fill rate: 100 tokens/60s → 1.66 tokens/s.
  - Request at `t=0`: Consumes 1 token; refills over time.

**Pros**: Burst tolerance.
**Cons**: Complex backpressure handling.

#### **Leaky Bucket**
- **Example**:
  - Process rate: 1 request/ms.
  - Excess requests at `t=0` are dropped.

**Pros**: Strict fairness.
**Cons**: Rejects bursts entirely.

---

## **3. Query Examples**

### **Example 1: Fixed-Window Rate Limiting (Redis)**
```sql
-- Set rate limit: 100 requests/minute
SET key:rate:limit 100
SET key:rate:window 60

-- Track requests (using Redis INCR)
INCR key:rate:requests:current_window
```

**Check if allowed**:
```sql
IF (INCR key:rate:requests:current_window) <= 100 THEN
    ALLOW
ELSE
    REJECT
END IF
```

### **Example 2: Token Bucket (In-Memory)**
```python
from collections import deque

class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity = capacity  # 100 tokens
        self.rate = rate          # 1.66 tokens/s
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, amount):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens += (elapsed * self.rate)
        self.tokens = min(self.tokens, self.capacity)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False
```

### **Example 3: Sliding Window Counter (Database)**
```sql
-- Store window state (e.g., PostgreSQL)
INSERT INTO rate_limits (id, window_start, count)
VALUES ('api:user:123', NOW(), 0);

-- On request:
BEGIN;
UPDATE rate_limits
SET count = count + 1
WHERE id = 'api:user:123'
AND window_start = (NOW() - INTERVAL '60 seconds')::timestamp;

-- Check if exceeded:
IF (count > 100) THEN REJECT;
COMMIT;
```

---

## **4. Related Patterns**
1. **[Circuit Breaker]**
   - Complements rate limiting by halting traffic during failures.
2. **[Request Throttling]**
   - Generalizes rate limiting to non-API contexts (e.g., database queries).
3. **[Backpressure]**
   - Uses queueing or delays to handle bursts beyond limits.
4. **[Distributed Rate Limiting]**
   - Extends algorithms (e.g., Redis) to cluster environments.

---

## **5. Trade-Offs Summary**
| **Factor**          | **Fixed Window** | **Sliding Log** | **Token Bucket** | **Leaky Bucket** |
|---------------------|------------------|-----------------|------------------|------------------|
| **Accuracy**        | Low              | High            | Medium           | Strict           |
| **Memory**          | Low              | High            | Low              | Low              |
| **Burst Handling**  | Poor             | Good            | Good             | Poor             |
| **Complexity**      | Low              | Medium          | Medium           | Low              |

---
**Recommendation**:
- Use **Fixed Window** for simplicity.
- Use **Token Bucket** for burst tolerance.
- Use **Sliding Window Log/Counter** for precision in high-throughput systems.