```markdown
# **Debugging Conventions: A Backend Engineer’s Guide to Writing Logs and Traces That Actually Help**

Debugging is the unsung hero of backend development. Even the most elegant API or well-optimized database schema will eventually fail—or at least, behave unexpectedly. When it does, you’ll either be:
- **Staring at a blank error screen** in production, trying to recall how data flows through your system.
- **Sifting through a log file of a thousand identical `[INFO] User logged in` messages** like a detective in a noir novel.
- **Wishing you had a crystal ball** that showed you exactly why a transaction rolled back at 3:17 AM.

Debugging conventions—the thoughtful patterns for logging, tracing, and error handling—are your crystal ball. They make it easier to:
✅ **Reproduce issues** without guessing where to look.
✅ **Share context** with teammates (or future you) in a structured way.
✅ **Avoid "log spam"** that dilutes important signals.

This guide will take you through the key debugging conventions used in production systems, complete with tradeoffs and practical examples. We’ll cover logging standards, distributed tracing, error classification, and how to implement these patterns in code.

---

## **The Problem: Debugging Without Conventions**

Let’s start with a real-world scenario. Imagine this:

**Scenario:** Your team’s newest feature—a real-time notification system—starts failing intermittently. Users report that emails stop arriving after a few hours. You check the logs and see:

```
[WARNING] User 421315: Notification failed
[DEBUG] Email service timeout (retrying)
[ERROR] Database connection rejected (code: 1045)
[INFO] User 421315 logged out
[DEBUG] Cache miss for user 421315
```

Now, what’s happening?
1. **Is it a database issue?** Maybe, but the warning doesn’t say where the failure occurred.
2. **Is it a race condition?** The cache miss is suspicious, but is it correlated?
3. **Is this an infrastructure problem?** The timeout could be network-related, but is it a spurious warning?

Without conventions, the logs are:
- **Noisy:** You can’t tell the signal (`ERROR`) from the noise (`INFO`).
- **Contextless:** A single line doesn’t tell you *why* something failed or *where* it happened.
- **Inconsistent:** Some developers throw `DEBUG` logs, others use `WARN` for everything.

The result? You might spend hours chasing red herrings instead of fixing the root cause.

### **Common Pitfalls**
- **"Log everything" anti-pattern:** Adding `DEBUG` logs to every function bloats logs and obscures important data.
- **Over-relying on "stack traces" only:** Production stack traces are often truncated or unreproducible.
- **Ignoring correlation IDs:** Without a way to follow a request across microservices, debugging feels like herding cats.
- **Hardcoded error messages:** `"Something went wrong"` isn’t helpful—you need structured data.

---

## **The Solution: Debugging Conventions**

Debugging conventions are a set of **standards** for:
1. **Log structure** (what to log, when, and how).
2. **Error handling** (how to classify and report failures).
3. **Tracing** (how to track requests across services).
4. **Metadata** (adding context without clutter).

The goal is to make debugging **predictable, efficient, and scalable**.

Here’s how to approach it:

| **Convention**          | **Purpose**                                                                 | **Example Use Case**                          |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Structured Logging**  | Logs are machine-readable and queryable.                                    | Finding all 403 errors for a specific user.    |
| **Correlation IDs**     | Track a request across services.                                            | Debugging a failed payment workflow.          |
| **Error Classification**| Standardized error types (e.g., `ValidationError`, `TimeoutError`).       | A/B testing which errors are most common.     |
| **Sampling**            | Avoid log overload by logging less frequently for non-critical paths.       | Reducing logs for read-only API calls.         |
| **Context Propagation** | Attach metadata (user ID, session, etc.) to logs without hardcoding.      | Debugging a race condition in a cart system. |

---

## **Components/Solutions**

Let’s dive into each convention with code examples.

---

### **1. Structured Logging**
**Problem:** Unstructured logs (`"User login failed: invalid password"`) are hard to parse and search.
**Solution:** Use a **key-value format** (e.g., JSON) for logs.

#### **Example: Structured Logging in Python**
```python
import json
import logging

# Configure a custom logger with JSON formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("app")

def login_user(user_id, attempt):
    try:
        # Simulate a login check
        if attempt > 3:
            raise ValueError("Too many attempts")
        # Log with structured data
        logger.info(
            json.dumps({
                "event": "user_login",
                "user_id": user_id,
                "status": "success",
                "metadata": {"attempt": attempt}
            })
        )
    except Exception as e:
        logger.error(
            json.dumps({
                "event": "user_login_failure",
                "user_id": user_id,
                "error_type": str(type(e).__name__),
                "details": str(e)
            })
        )

# Usage
login_user(421315, 1)  # Success
login_user(421315, 4)  # Fails (too many attempts)
```

#### **Output:**
```json
2023-11-15 14:30:45 INFO {"event": "user_login", "user_id": 421315, "status": "success", "metadata": {"attempt": 1}}
2023-11-15 14:31:00 ERROR {"event": "user_login_failure", "user_id": 421315, "error_type": "ValueError", "details": "Too many attempts"}
```

#### **Why This Works**
- **Queryable:** You can use tools like **ELK Stack (Elasticsearch, Logstash, Kibana)** to filter logs:
  ```sql
  -- Find all login failures for user 421315
  SELECT * FROM logs WHERE "event" = "user_login_failure" AND "user_id" = 421315;
  ```
- **Consistent:** Every log has the same schema, making parsing easier.
- **No noise:** Only relevant fields are included.

**Tradeoffs:**
- **Slightly more verbose** than plaintext logs.
- **Requires tooling** (e.g., JSON parsers, log aggregation).

---

### **2. Correlation IDs**
**Problem:** In a distributed system, logs from different services are disconnected. How do you follow a request from API → Cache → DB?
**Solution:** Attach a **unique ID** to each request and propagate it across services.

#### **Example: Correlation ID in Node.js**
```javascript
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

// Logger setup with correlation ID
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, level, message, correlationId }) => {
      return `${timestamp} [${level}] [${correlationId}] ${message}`;
    })
  )
});

async function processOrder(customerId, orderData) {
  const correlationId = uuidv4();

  try {
    logger.info(`Processing order ${orderData.id} for customer ${customerId}`, { correlationId });

    // Simulate calling external services (e.g., payment, inventory)
    const paymentRes = await callPaymentService(orderData, correlationId);
    const inventoryRes = await callInventoryService(orderData, correlationId);

    logger.info('Order processing completed', { correlationId });
  } catch (err) {
    logger.error('Order processing failed', { correlationId, error: err.message });
    throw err;
  }
}

function callPaymentService(orderData, correlationId) {
  logger.info(`Calling payment service for order ${orderData.id}`, { correlationId });
  // Simulate payment failure
  if (Math.random() > 0.5) throw new Error('Payment declined');
  return { success: true };
}
```

#### **Output (Simulated Logs Across Services):**
```
2023-11-15 15:00:00 [INFO] [a1b2c3d4] Processing order 123 for customer 999
2023-11-15 15:00:01 [INFO] [a1b2c3d4] Calling payment service for order 123
2023-11-15 15:00:02 [ERROR] [a1b2c3d4] Payment declined
2023-11-15 15:00:03 [ERROR] [a1b2c3d4] Order processing failed: Payment declined
```

#### **Why This Works**
- **End-to-end visibility:** Even if the payment service fails, you can see the **full chain** of events.
- **Debugging in production:** Use correlation IDs to correlate logs across microservices.

**Tradeoffs:**
- **Requires middleware** to inject correlation IDs into HTTP headers, DB queries, etc.
- **Overhead:** UUIDs add a tiny bit of overhead (but negligible in most cases).

---

### **3. Error Classification**
**Problem:** Errors are often generic (`"Internal Server Error"`), making it hard to categorize issues.
**Solution:** Define **standardized error types** and log them consistently.

#### **Example: Error Classification in Go**
```go
package main

import (
	"errors"
	"fmt"
	"log"
	"time"
)

type AppError struct {
	Code    string    // e.g., "VALIDATION_ERROR", "TIMEOUT_ERROR"
	Message string    // Human-readable message
	Details map[string]interface{} // Additional context
	Time    time.Time
}

func (e *AppError) Error() string {
	return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

func validateUserInput(email string) error {
	if email == "" {
		return &AppError{
			Code:    "VALIDATION_ERROR",
			Message: "Email is required",
			Details: map[string]interface{}{"field": "email"},
			Time:    time.Now(),
		}
	}
	return nil
}

func main() {
	email := ""

	if err := validateUserInput(email); err != nil {
		log.Printf("Error: %+v\n", err) // %+v prints struct fields
		// Output: Error: &{VALIDATION_ERROR Email is required map[field:email] 2023-11-15 16:00:00 +0000 UTC m=+0.000123}
	}
}
```

#### **Why This Works**
- **Consistent error handling:** All validation errors have the same structure.
- **Machine-friendly:** You can query logs for `VALIDATION_ERROR` and see patterns (e.g., "80% of errors are missing emails").

**Tradeoffs:**
- **Requires discipline** to classify errors correctly.
- **Overhead of structs** (but negligible).

---

### **4. Sampling**
**Problem:** Logging every request bloats storage and slows down systems.
**Solution:** **Sample logs** (e.g., log 10% of requests) or use **level-based filtering**.

#### **Example: Sampling in Python**
```python
import logging
import random

logger = logging.getLogger("sampler")

def shouldLog(event: str, probability: float = 0.1) -> bool:
    """Sample logs with a given probability."""
    return random.random() < probability

def processOrder(orderId):
    if shouldLog("process_order", 0.01):  # Log 1% of orders
        logger.info(f"Processing order {orderId}")
    # ... rest of the logic
```

#### **Why This Works**
- **Reduces log volume** without losing critical data.
- **Focuses on important events** (e.g., errors, slow requests).

**Tradeoffs:**
- **Misses edge cases** if sampling is too aggressive.
- **Requires correlation** to ensure critical paths are logged.

---

## **Implementation Guide**

### **Step 1: Choose a Logging Library**
Use libraries that support structured logging:
- **Python:** `structlog`, `logging` (with `json.dumps`).
- **Node.js:** `winston`, `pino`.
- **Go:** `zap`, `logrus`.
- **Java:** `Logback`, `SLF4J`.

### **Step 2: Define Log Levels**
Use standard levels but **avoid `DEBUG` for production**:
| Level       | Use Case                                      |
|-------------|-----------------------------------------------|
| `TRACE`     | Extremely verbose, internal debugging.         |
| `DEBUG`     | Development-only, low-level details.           |
| `INFO`      | Normal operation (e.g., "User logged in").    |
| `WARN`      | Potential issues (e.g., "Disk space low").     |
| `ERROR`     | Failed operations (e.g., "DB connection lost").|
| `CRITICAL`  | System-wide failures (e.g., "All workers dead").|

### **Step 3: Add Correlation IDs Everywhere**
- **HTTP Requests:** Inject `X-Request-ID` header.
- **Databases:** Attach correlation ID to queries.
- **Messages:** Include it in Kafka/RabbitMQ payloads.

#### **Example: Middleware for Correlation IDs (Express.js)**
```javascript
function addCorrelationId(req, res, next) {
  const correlationId = req.headers['x-request-id'] || req.id || req.getId();
  req.correlationId = correlationId;
  res.setHeader('x-request-id', correlationId);
  next();
}

app.use(addCorrelationId);
```

### **Step 4: Classify Errors Standardly**
Define a **global error map** (e.g., in a shared library):
```python
# shared/errors.py
ERROR_TYPES = {
    "VALIDATION_ERROR": 1001,
    "TIMEOUT_ERROR": 1002,
    "INTERNAL_ERROR": 5000,
}
```

### **Step 5: Implement Sampling**
- Use **log levels** to filter (e.g., only `ERROR` and `WARN` in production).
- For critical paths, **log always**; for others, **sample**.

---

## **Common Mistakes to Avoid**

### **1. "Log Everything" Anti-Pattern**
❌ **Bad:**
```python
logger.debug(f"User {user_id} has {len(user.items)} items in cart")
```
✅ **Good:**
```python
if user.items:  # Only log if there's data
    logger.info("User has items in cart", {"user_id": user_id, "count": len(user.items)})
```

### **2. Hardcoding Sensitive Data**
❌ **Bad:**
```python
logger.error("Failed to save payment", {"card_number": "4111111111111111"})
```
✅ **Good:**
```python
logger.error("Failed to save payment", {"card_last4": "1111"})
```

### **3. Ignoring Correlation IDs**
❌ **Bad:**
```javascript
// No correlation ID in DB query
db.query("SELECT * FROM orders WHERE user_id = ?", [userId]);
```
✅ **Good:**
```javascript
// Include correlation ID in all requests
db.query("SELECT * FROM orders WHERE user_id = ?", [userId], { correlationId: req.correlationId });
```

### **4. Overusing `DEBUG` in Production**
❌ **Bad:**
```python
logger.debug("Processing order %s", orderId)  // In production!
```
✅ **Good:**
```python
logger.info("Processing order %s", orderId)  // Only INFO/WARN/ERROR in prod
```

---

## **Key Takeaways**
Here’s a quick checklist for debugging conventions:

✔ **Log structured data** (JSON, key-value) for queryability.
✔ **Use correlation IDs** to track requests across services.
✔ **Classify errors** with standardized types (e.g., `VALIDATION_ERROR`).
✔ **Sample logs** to reduce noise without losing critical data.
✔ **Avoid logging sensitive data** (PII, secrets).
✔ **Propagate context** (user ID, session, request ID) through all layers.
✔ **Use appropriate log levels** (never `DEBUG` in production).
✔ **Instrument critical paths** (e.g., always log errors, sample others).
✔ **Test your logging** in staging before production.

---

## **Conclusion**
Debugging conventions aren’t about adding more code—they’re about **adding the right code**. A few well-placed logging patterns can turn a chaotic debugging session into a structured, efficient hunt for the root cause.

Start small:
1. Add structured logging to one service.
2. Inject correlation IDs in your HTTP middleware.
3. Classify errors globally.

As your system grows, these conventions will save you **hours of frustration** and help you build a more robust, observable backend.

---
**Further Reading:**
- [OpenTelemetry for Distributed Tracing](https://opentelemetry.io/)
- [Structured Logging Best Practices (Google)](https://cloud.google.com/logging/docs/view/structured-logging)
- [Designing Observability Into Systems (Martin Fowler)](https://martinfowler.com/articles/observability.html)

**What’s your biggest debugging challenge?** Share in the comments—let’s solve it together!
```