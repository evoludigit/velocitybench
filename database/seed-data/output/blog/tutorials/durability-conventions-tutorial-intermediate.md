```markdown
# **Durability Conventions: How to Build Fault-Tolerant APIs Without Reinventing the Wheel**

*By [Your Name], Senior Backend Engineer*

### **Introduction**

APIs are the backbone of modern distributed systems—but what happens when a request fails mid-flight? Or when a database connection drops after a transient network blip? Without proper durability guarantees, your system could lose transactions, duplicate work, or even crash under load.

Most backend engineers know *why* durability matters (ACID, eventual consistency, etc.), but implementing it effectively is harder. That’s where **Durability Conventions** come in—a simple yet powerful pattern to ensure your APIs handle failures gracefully without requiring complex retry logic, compensating transactions, or distributed locks.

This pattern is already used by major platforms (think: Stripe, Uber’s fleet systems, or Airbnb’s inventory management) but remains underdiscussed in the wider engineering community. In this guide, we’ll break down:

- **Why durability is brittle** without conventions
- **How Durability Conventions solve it** with six key rules
- **Practical code examples** in Go, Python, and SQL
- **Anti-patterns** that waste time and money

By the end, you’ll know how to design APIs that survive outages, network partitions, and even developer mistakes.

---

## **The Problem: Why APIs Lose Data Without Durability Conventions**

Durability is often an afterthought—until it’s not. Here’s what happens without explicit conventions:

### **1. Silent Data Loss**
Imagine a payment API that debits your bank account but *accidentally* deduplicates the charge because the DB transaction rolled back due to a network glitch. The money disappears, but your code doesn’t report an error.

```go
// What happens when the DB rollback is silent?
func TransferMoney(src, dest Account, amount float64) error {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    db, err := getDB(ctx) // Network partition → DB connection fails
    if err != nil {
        return fmt.Errorf("DB connection failed: %w", err)
    }

    _, err = db.Exec(`
        UPDATE accounts
        SET balance = balance - ? WHERE id = ?
        RETURNING balance
    `, amount, src.ID)

    // Silent failure: No error, but the transfer *should* have failed
    return err // Returns nil if DB is dead
}
```

**Result?**
- The caller thinks the transfer succeeded.
- The source account retains the money.
- The destination account is short.

### **2. Race Conditions Under Load**
High-traffic APIs often face **smart retries**—clients keep hammering endpoints until they succeed. This leads to:

- **Duplicate operations** (e.g., twice the same invoice generated)
- **Stale reads** (users see inconsistent data)
- **Cascading failures** (a single API call triggers an unsupported retry storm)

```python
# Example: A retry loop without isolation
def bookHotel(guest_id, hotel_id):
    for _ in range(3):  # Retry 3 times
        try:
            # No idempotency key → race condition
            db.execute(
                "UPDATE rooms SET booked = 1 WHERE id = ? AND booked = 0",
                hotel_id
            )
            return {"status": "success"}
        except DatabaseError:
            continue
    return {"status": "failed"}  # What if *another* request won?
```

**Result?**
- A room gets booked twice.
- Double charges happen in payment processing.
- Users report "ghost reservations."

### **3. Distributed Locks Are Overkill**
Many teams solve durability by slapping **distributed locks** (Redis, ZooKeeper) onto every API. This introduces:
- **Latency spikes** due to lock contention
- **Complexity** that most services don’t need
- **Single points of failure** if the lock service goes down

**Why?**
Most APIs don’t need locks *per se*—they need **predictable failure modes**.

---

## **The Solution: Durability Conventions**

The **Durability Conventions** pattern is a set of **six shared principles** to bake failure resilience into your API contract. It’s inspired by patterns like **idempotency keys, exponential retries, and error codes**, but with a focus on **explicit failure handling** at the API level.

| Conventions                | Purpose                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| **Idempotency Keys**       | Prevent duplicate operations by making requests retry-safe.             |
| **Exponential Backoff**    | Reduce load on downstream systems during retries.                       |
| **Unique Error Codes**     | Distinguish transient failures from permanent ones.                     |
| **Client-Side Retry Tokens**| Let clients retry without causing duplicates.                          |
| **Resource Versioning**    | Avoid "lost updates" with optimistic concurrency control.                |
| **Durable Transactions**   | Use 2PC or saga patterns where ACID isn’t viable.                      |

The key insight:
> **"Make failure a first-class citizen in your API design."**

---

## **Code Examples: Implementing Durability Conventions**

### **1. Idempotency Keys (Prevent Duplicates)**
Every API request gets a unique `Idempotency-Key`. If the same key is used again, the server returns a `200 OK` (no-op) or `409 Conflict` (already processed).

```javascript
// API Gateway (Fastify/Express example)
app.post("/orders", async (req, res) => {
    const { idempotencyKey } = req.headers;
    if (req.inFlight[idempotencyKey]) {
        return res.status(200).send("Already processed");
    }

    try {
        req.inFlight[idempotencyKey] = true;
        const order = await db.createOrder(req.body);
        res.status(201).send(order);
    } catch (err) {
        res.status(500).send(err);
    } finally {
        delete req.inFlight[idempotencyKey];
    }
});
```

**Client-side retry example (Postman):**
```javascript
async function createOrder(order) {
    const idempotencyKey = crypto.randomUUID();
    let retries = 3;

    while (retries--) {
        try {
            const response = await fetch("/orders", {
                method: "POST",
                headers: { "Idempotency-Key": idempotencyKey },
                body: JSON.stringify(order),
            });
            if (response.status === 200 || response.status === 201) {
                return response.json();
            }
        } catch (err) {
            if (retries === 0) throw err;
            await exponentialBackoff(1000);
        }
    }
}
```

### **2. Exponential Backoff (Reduce Load)**
Clients should retry with increasing delays after transient failures (e.g., `5xx` errors).

```go
// Go implementation (with jitter)
func exponentialBackoff(maxAttempts int, delay time.Duration) (time.Duration, error) {
    var attempts int
    var totalDelay time.Duration

    for attempts < maxAttempts {
        attempts++
        totalDelay += delay * time.Duration(attempts)
        if totalDelay > 5*time.Minute { // Cap at 5 minutes
            return 0, errors.New("max delay reached")
        }
        time.Sleep(totalDelay)
    }
    return totalDelay, nil
}
```

### **3. Resource Versioning (Avoid Lost Updates)**
Track updates with a version field to prevent overwrites.

```sql
-- SQL: Optimistic concurrency control
BEGIN TRANSACTION;
UPDATE users
SET name = 'New Name', version = version + 1
WHERE id = 123 AND version = 42; -- Current version check
-- If no rows updated → conflict detected
COMMIT;
```

**API response example:**
```json
{
  "status": "conflict",
  "error": "ETAG_MISMATCH",
  "current_version": 43,
  "client_version": 42
}
```

### **4. Durable Transactions (When ACID Isn’t Enough)**
For distributed systems, use **sagas** (choreography or orchestration) or **two-phase commit (2PC)**.

```python
# Example: Choreography Saga (eventual consistency)
def processPayment(order, payment):
    # Step 1: Reserve inventory
    inventory.update(order.product_id, quantity=-1)

    # Step 2: Charge payment (event-based)
    payment_service.charge(
        order.id,
        payment.amount,
        on_success=lambda: inventory.confirm_reservation(order.id),
        on_failure=lambda: inventory.release_reservation(order.id)
    )
```

---

## **Implementation Guide: How to Adopt Durability Conventions**

### **Step 1: Audit Your APIs for Durability Risks**
Before adding conventions, identify:
- Endpoints that modify state (`POST`, `PUT`, `DELETE`).
- Services with external dependencies (DBs, message queues).
- High-latency or flaky integrations.

**Tool:** Static analysis (e.g., `golangci-lint` for Go, `pylint` for Python) to flag undefined retries.

### **Step 2: Define the Conventions**
Pick 2-3 conventions per API (start small!):

| API Type         | Recommended Conventions                     |
|------------------|--------------------------------------------|
| Payment APIs     | Idempotency, Exponential Backoff            |
| Order Processing | Idempotency, Resource Versioning           |
| User Profiles    | Resource Versioning, Client Retries         |

### **Step 3: Instrument Your Code**
- Add headers for idempotency keys.
- Log failed requests with context for debugging.
- Use middleware to enforce retries (e.g., `Go: retry-go`, `Python: tenacity`).

```go
// Go example with retry middleware
type DurableHandler struct {
    next http.HandlerFunc
}

func (h *DurableHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    if r.Method == "POST" {
        // Add idempotency key to context
        ctx = context.WithValue(ctx, "idempotency_key", r.Header.Get("Idempotency-Key"))
    }
    h.next.ServeHTTP(w, r.WithContext(ctx))
}
```

### **Step 4: Test for Durability**
- **Chaos testing:** Kill DB/pods during requests.
- **Load testing:** Simulate retries (e.g., `k6`, `Locust`).
- **Contract tests:** Verify idempotency keys work (e.g., `Postman Mock Server`).

```bash
# Example: k6 script for idempotency testing
import http from 'k6/http';

export const options = {
    retries: 3,
    thresholds: { http_req_duration: ['p(95)<1000'] },
};

export default function () {
    const payload = { item: "test" };
    const res = http.post('http://localhost:3000/orders', payload, {
        headers: { 'Idempotency-Key': 'unique-key-123' },
    });
    console.log(res.json());
}
```

### **Step 5: Document the Conventions**
Add to your API specs (OpenAPI/Swagger):

```yaml
# OpenAPI example
paths:
  /orders:
    post:
      summary: Create an order (idempotent)
      parameters:
        - $ref: '#/components/parameters/IdempotencyKey'
      responses:
        409:
          description: Already processed (idempotency conflict)
```

---

## **Common Mistakes to Avoid**

### ❌ **Mistake 1: Assuming "It Works on My Machine"**
- **Problem:** Locally, retries succeed because the DB is fast. In production, retries cause cascading failures.
- **Fix:** Test with network partitions (`Chaos Monkey`, `net-emulator`).

### ❌ **Mistake 2: Over-Retries**
- **Problem:** Exponential backoff with no max delay = infinite retries.
- **Fix:** Set a reasonable cap (e.g., 5 minutes).

```javascript
// Bad: No timeout
function retry() { while (true) { try { /* request */ } catch { await new Promise(_ => setTimeout(_, 100)); } } }

// Good: Timeout after 5 minutes
function retry(maxRetries = 10, delay = 100) {
    for (let i = 0; i < maxRetries; i++) {
        try { return await request(); }
        catch { if (i === maxRetries - 1) throw; await new Promise(_ => setTimeout(_, delay * Math.pow(2, i))); }
    }
}
```

### ❌ **Mistake 3: Ignoring Client Errors**
- **Problem:** Clients see `500 Internal Server Error` but keep retrying.
- **Fix:** Return **specific HTTP codes** for retriable vs. permanent errors:
  - `429 Too Many Requests` (rate-limited)
  - `503 Service Unavailable` (retryable)
  - `409 Conflict` (not retriable)

```go
// HTTP codes for retries
if err := db.Execute("..."); err != nil {
    if strings.Contains(err.Error(), "timeout") {
        return errors.New("retryable: database timeout"), http.StatusServiceUnavailable
    }
    return err, http.StatusInternalServerError
}
```

### ❌ **Mistake 4: Skipping Idempotency for Simple APIs**
- **Problem:** "I don’t need it—it’s a CRUD API!"
- **Fix:** Even `GET /users?id=123` can benefit from idempotency if it’s part of a workflow.

---

## **Key Takeaways**

✅ **Start small:** Pick 1-2 conventions per API (e.g., idempotency + backoff).
✅ **Fail fast:** Return HTTP codes that guide clients, not just `500` errors.
✅ **Test failures:** Use chaos engineering to catch durability holes early.
✅ **Document:** Clients need to know how to retry correctly.
✅ **Avoid over-engineering:** Distributed locks are rarely needed—conventions are enough.

---

## **Conclusion**

Durability isn’t about building unbreakable systems—it’s about **making failures predictable**. By adopting Durability Conventions, you trade complexity for resilience: your APIs will handle retries gracefully, prevent duplicates, and recover from outages without manual intervention.

**Next steps:**
1. Pick one API to audit for durability risks.
2. Add idempotency keys to your `POST`/`PUT` endpoints.
3. Test with `Chaos Monkey` or `k6`.
4. Iterate—start small!

As the saying goes:
> *"A system is only as durable as its weakest retry."*

Now go make your APIs more resilient—one convention at a time.

---
**Further Reading:**
- [AWS Durability Best Practices](https://docs.aws.amazon.com/whitepapers/latest/reliability-at-scale/durable-data.html)
- [Idempotency in Distributed Systems](https://martinfowler.com/articles/idempotency.html)
- [Exponential Backoff Guide (Netflix OSS)](https://github.com/Netflix/archaius/wiki/Exponential-Backoff-and-Jitter)
```