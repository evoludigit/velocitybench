```markdown
# **Logging Anti-Patterns: What to Avoid in Your Backend Logging Strategy**

![Logging Anti-Patterns Cover Image](https://images.unsplash.com/photo-1621146181274-6047a5b8ba9f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80)
*Image: A logger drowning in noise (not the good kind).*

---

## **Introduction**

Logging is the backbone of observability. A well-designed logging system helps you:
- Debug issues in production
- Monitor application health
- Track user behavior
- Ensure compliance

But if you don’t design your logging strategy carefully, you’ll end up with:
- **Noise overload** – drowning in logs that add no value
- **Performance bottlenecks** – slow applications due to excessive logging
- **Security risks** – exposing sensitive data in logs
- **Storage explosion** – logging everything costs money

In this guide, we’ll explore **common logging anti-patterns**, why they’re problematic, and how to fix them with practical examples.

---

## **The Problem: When Logging Goes Wrong**

### **1. Logging Everything (The "Debug Mode Always On" Trap)**
Many developers implement logging like this:

```go
// Go example: Logging every function call
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    logger.Info("Handling request", "method", r.Method, "path", r.URL.Path)
    // ... business logic ...
    logger.Info("Request completed")
}
```

**The Issue:**
- Every minor operation creates log entries.
- Logs become unreadable (too much noise).
- Storage costs skyrocket.

### **2. Logs Full of Sensitive Data (Leaking Secrets)**
A common mistake is logging raw data without sanitization:

```python
# Python example: Logging passwords without care
def validateUser(user):
    if user.password == "admin123":
        logger.warning(f"Invalid credentials for user: {user.email}")  # BAD!
```
**The Issue:**
- Logs may contain PII (Personally Identifiable Information).
- Attackers can scrape logs for leaked credentials.

### **3. Logs Without Context (The "What Happened?" Mystery)**
Some logs lack critical context:

```javascript
// Node.js example: Log without metadata
app.use((req, res, next) => {
    console.log("Request received"); // Missing: user ID, timestamp, HTTP method
    next();
});
```
**The Issue:**
- Hard to correlate logs with errors.
- Debugging becomes a guessing game.

### **4. Logs That Break Under Load (The "I/O Wall" Problem)**
Many applications log synchronously, causing performance issues:

```ruby
# Ruby example: Synchronous logging blocking I/O
def process_order(order)
  logger.info("Processing order #{order.id}")
  # Heavy operation...
end
```
**The Issue:**
- Slow applications under high load.
- Logs may get dropped if the system is overloaded.

---

## **The Solution: Logging Best Practices**

### **1. Log Only What You Need (The "Goldilocks Principle")**
**Rule of thumb:**
- **Log errors, warnings, and critical events** (high severity).
- **Avoid logging every single function call** (low severity).

**Example (Go with structured logging):**
```go
package main

import (
	"log/slog"
	"time"
)

func HandleRequest(w http.ResponseWriter, r *http.Request) {
	// Log only when necessary
	if r.Method == "POST" && r.URL.Path == "/api/submit" {
		slog.Info(
			"Request processed",
			"method", r.Method,
			"path", r.URL.Path,
			"duration", time.Since(startTime).String(),
		)
	}
}
```

**Key Adjustments:**
- Use **log levels** (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
- Avoid `DEBUG` logging in production unless absolutely necessary.

---

### **2. Sanitize Logs Before Writing (PII Protection)**
Never log raw sensitive data. Instead:
- **Mask passwords, tokens, and PII.**
- Use **placeholders** (`"email": "[REDACTED]"`).

**Example (Python with `python-json-logger`):**
```python
import json_logger
from logging import Logger

class SensitiveFilter(json_logger.JsonFormatter):
    def format(self, record):
        if hasattr(record, 'args'):
            record.args = {k: v.replace("password", "[REDACTED]") for k, v in record.args.items()}
        return json.dumps(record.__dict__)

logger = Logger("app")
logger.addHandler(json_logger.JSONHandler(
    formatter=SensitiveFilter(),
    filename="app.log"
))

# Logs user data safely
logger.info("User login", user={"email": "user@example.com", "password": "secret123"})
// Output: { "user": { "email": "user@example.com", "password": "[REDACTED]" } }
```

---

### **3. Add Context to Logs (Structured Logging)**
Use structured logging to include:
- **Request ID** (for tracing)
- **User ID** (if applicable)
- **Timestamp** (for correlation)

**Example (Node.js with `pino`):**
```javascript
const pino = require('pino')();

app.use((req, res, next) => {
    const logger = pino({
        level: 'info',
        name: 'api',
        base: {
            reqId: req.id,
            userId: req.user?.id,
        },
    });

    req.logger = logger;
    next();
});

app.get('/search', (req, res) => {
    req.logger.info({ query: req.query.q }, "Search request");
});
```
**Output:**
```json
{
  "level": "info",
  "time": "2024-05-20T12:34:56.789Z",
  "reqId": "abc123",
  "userId": "user456",
  "msg": "Search request",
  "query": "Query here"
}
```

---

### **4. Async Logging (Avoid Blocking I/O)**
Use **buffered logging** to prevent slowdowns.

**Go Example (Async Logging with `slog`):**
```go
package main

import (
	"log/slog"
	"sync"
)

var logger *slog.Logger

func init() {
	// Enable async logging
	var opts slog.HandlerOptions
	opts.AddSource = true
	opts.Level = slog.LevelInfo
	opts.Handler = slog.NewJSONHandler(os.Stderr, &opts)
	logger = slog.New(opts.Handler)
}

func HandleRequest(w http.ResponseWriter, r *http.Request) {
	// Log asynchronously
	go func() {
		logger.Info("Request processed", "method", r.Method, "path", r.URL.Path)
	}()
}
```

**Key Takeaways:**
- **Always log asynchronously** in high-traffic systems.
- Use **write-ahead logging** (e.g., Kafka, ES) for extreme scalability.

---

## **Implementation Guide: How to Fix Your Logging**

### **Step 1: Audit Your Current Logging**
- Check what’s being logged (`DEBUG`, `INFO`, `ERROR` levels).
- Identify sensitive data leakage risks.

**Tools to Help:**
- **`grep` / `awk` (Linux)** – Filter logs for sensitive data.
- **ELK Stack (Elasticsearch, Logstash, Kibana)** – Analyze log patterns.

### **Step 2: Refactor to Structured Logging**
- Switch from plain text (`console.log`) to **JSON/Structured Logs**.
- Use libraries like:
  - **Go:** `slog` (built-in), `zap`
  - **Python:** `json-logger`, `structlog`
  - **Node.js:** `pino`, `winston`
  - **Java:** `Logback`, `Logstash`

### **Step 3: Implement Log Rotation & Retention**
- Avoid infinite log growth with **rotation** (e.g., `logrotate`).
- Example `.logrotate` config:
  ```
  /var/log/app.log {
      daily
      rotate 30
      compress
      missingok
      maxsize 100M
      create 640 app app
  }
  ```

### **Step 4: Test Log Performance Under Load**
- Simulate high traffic with:
  ```sh
  ab -n 10000 -c 1000 http://localhost:8080/
  ```
- Monitor CPU/latency spikes due to logging.

---

## **Common Mistakes to Avoid**

| **Anti-Pattern** | **Why It’s Bad** | **Solution** |
|------------------|----------------|-------------|
| **Logging raw SQL queries** | Exposes DB schemas & credentials | Use parameterized logs (`"SELECT * FROM users WHERE id = ?"`). |
| **Ignoring log retention policies** | Unbounded storage costs | Set TTL (Time-To-Live) for logs. |
| **Not using log levels** | Overwhelming noise | Enforce `INFO` for production, `DEBUG` for dev. |
| **Logging in error-handling paths** | Deadlocks if logging fails | Use **retryable logging** or **dead-letter queues**. |
| **Logging without correlation IDs** | Hard to track requests | Always include `request_id` in logs. |

---

## **Key Takeaways**

✅ **Log Less, Log Better** – Avoid `DEBUG` logs in production.
✅ **Sanitize Sensitive Data** – Mask passwords, tokens, and PII.
✅ **Use Structured Logging** – JSON > plain text for parsing.
✅ **Log Asynchronously** – Prevent I/O bottlenecks.
✅ **Rotate & Retain Logs** – Avoid infinite disk usage.
✅ **Test Under Load** – Ensure logging doesn’t break your app.

---

## **Conclusion**

Logging is **not just "print stuff to a file"**—it’s a **critical observability system** that needs care. By avoiding these anti-patterns, you’ll:
- **Reduce noise** in production logs.
- **Improve security** by protecting sensitive data.
- **Boost performance** with async logging.
- **Simplify debugging** with structured, contextual logs.

**Next Steps:**
1. Audit your current logging.
2. Switch to structured logging (`JSON` or similar).
3. Implement log rotation & retention.
4. Test performance under load.

Would you like a deeper dive into **log aggregation tools (ELK, Loki, Splunk)** or **custom log shippers**? Let me know in the comments!

---
**Happy Logging!** 🚀
```

---
### **Why This Works**
- **Code-first approach** – Shows **real examples** (Go, Python, Node.js, Ruby) instead of vague theory.
- **Balanced tradeoffs** – Explains **why** anti-patterns are bad (performance, security, costs).
- **Actionable guide** – Provides **step-by-step fixes** (audit → refactor → test).
- **Engaging tone** – Friendly but professional, with **bullet points** for skimmable takeaways.

Would you like any modifications (e.g., more focus on a specific language or log shipper)?