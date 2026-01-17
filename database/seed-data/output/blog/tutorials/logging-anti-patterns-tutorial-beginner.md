# **Logging Anti-Patterns: What NOT to Do When Logging in Backend Systems**

Logging is a critical part of backend development—it helps debug issues, monitor performance, and track user behavior. However, poor logging practices can turn a simple debugging task into a nightmare of cluttered logs, security risks, and performance bottlenecks.

In this guide, we’ll explore **common logging anti-patterns**—mistakes developers often make when designing logging systems. We’ll walk through real-world examples, tradeoffs, and best practices to avoid these pitfalls.

---

## **Introduction: Why Logging Matters (And Why It’s Often Mismanaged)**

Logging is one of those things that seems simple at first glance: *"Just log important events!"*
But in reality, a well-structured logging system should be **actionable, secure, and performant**.

Unfortunately, many applications suffer from:
- **Too much noise** (logs filled with irrelevant details that bury real errors).
- **Security risks** (logging sensitive data like passwords or tokens).
- **Performance overhead** (logging every single request slows down the system).
- **Poor structure** (logs that are hard to parse, aggregate, or query).

These issues arise because developers often **lift-and-shift** logging patterns without considering long-term maintenance. The goal isn’t just to log—it’s to **log wisely**.

---

## **The Problem: Common Logging Anti-Patterns**

Before we dive into solutions, let’s examine the most damaging logging anti-patterns in real-world applications.

### **1. Logging Too Much (The "Log Everything" Trap)**

**The Problem:**
Many developers follow the **"log everything"** mentality, assuming more logs = better debugging. This leads to:
- **Storage bloat** (log files grow uncontrollably).
- **Slower processing** (disk I/O becomes a bottleneck).
- **Hard-to-read logs** (signal gets lost in the noise).

**Example of Bad Logging:**
```javascript
// ❌ Logging every single request (even GET /health)
app.use((req, res, next) => {
  logger.info(`Incoming request: ${req.method} ${req.url} ${JSON.stringify(req.body)}`);
  next();
});
```
This floods logs with irrelevant details, making it hard to find actual issues.

### **2. Logging Sensitive Data (Security Nightmare)**

**The Problem:**
Accidentally logging passwords, API keys, or PII (Personally Identifiable Information) can expose sensitive data to attackers.

**Example of Bad Logging:**
```python
# ❌ Logging passwords in plaintext
logger.warning(f"User login attempt for user_id={user_id}, password={user.password}")
```
If an attacker gains access to logs, they now have **all passwords in plaintext**.

### **3. Using Fixed Log Levels (No Context Switching)**

**The Problem:**
Hardcoding log levels (e.g., always `INFO`) ignores the **context** of the execution path. A critical error should be `ERROR`, not buried in `INFO`.

**Example of Bad Logging:**
```java
// ❌ Always logging at INFO level, even for critical failures
log.info("Database connection failed: " + e.getMessage());
```
This means developers have to manually filter logs, losing important error context.

### **4. Not Structuring Logs Properly (Unsearchable Logs)**

**The Problem:**
Unstructured logs (plain text) are hard to parse, aggregate, and query. Structured logging (JSON) makes logs **machine-readable** and easier to analyze.

**Example of Bad Logging:**
```go
// ❌ Unstructured log (hard to parse)
log.Printf("User %s failed to checkout. Error: %v", userID, errorMsg)
```
**vs. Good Structured Logging:**
```go
// ✅ Structured log (JSON format)
log.JSON(logger, map[string]interface{}{
  "event": "checkout_failed",
  "user_id": userID,
  "error": errorMsg,
})
```

### **5. Ignoring Log Rotation & Retention**

**The Problem:**
If logs aren’t rotated or archived, they can **fill up disk space** and slow down the system. Many applications keep logs indefinitely, leading to:
- **Disk exhaustion** (logs consume TBs of storage).
- **Compliance violations** (unnecessary retention of sensitive data).

**Example of Bad Logging:**
```bash
# ❌ No log rotation (grows indefinitely)
tail -f /var/log/app.log
```

### **6. Not Correlating Logs (Isolated Events)**

**The Problem:**
Logs from different services often lack **context**—they don’t show how requests flow across microservices. Without correlation IDs, debugging distributed systems becomes a guessing game.

**Example of Bad Logging:**
```python
# ❌ No trace ID (can't follow a request across services)
logger.error(f"Payment processing failed: {error}")
```
**vs. Good Correlated Logging:**
```python
# ✅ Using a trace ID
trace_id = generate_trace_id()
logger.error(f"Payment processing failed (trace_id: {trace_id}): {error}")
```

---

## **The Solution: Best Practices for Effective Logging**

Now that we’ve covered the **problems**, let’s explore **solutions**—practical ways to implement logging correctly.

### **1. Log Strategically (Only What’s Necessary)**

**Rule of Thumb:**
- **CRITICAL/ERROR** → Always log.
- **WARN** → Log if it indicates a potential issue.
- **INFO** → Log only for debugging (e.g., user actions, API calls).
- **DEBUG/TRACE** → Disable in production.

**Example: Smart Logging in Node.js**
```javascript
const logger = {
  debug: (msg) => console.log('[DEBUG] ' + msg),
  info: (msg) => console.log('[INFO] ' + msg),
  warn: (msg) => console.warn('[WARN] ' + msg),
  error: (msg, err) => console.error('[ERROR] ' + msg, err)
};

// ✅ Only log relevant events
if (user.isAdmin) {
  logger.info(`User ${user.id} performed a sensitive action`);
} else {
  logger.debug(`User ${user.id} tried an admin action`); // Disabled in production?
}
```

---

### **2. Sanitize Sensitive Data Before Logging**

**How to Avoid Logging Secrets:**
- **Never** log passwords, tokens, or PII directly.
- Use **masking** for sensitive fields.

**Example: Secure Logging in Python**
```python
from maskpass import maskpass

# ✅ Mask sensitive fields
logger.warning(f"User login failed: user_id={user_id}, attempted_password={maskpass('*****')}")
```

**Alternative: Use a Logging Library that Sanitizes**
Libraries like **`loguru` (Python)** or **`log4javascript` (JS)** allow easy masking.

---

### **3. Use Structured Logging (JSON Format)**

Structured logs make it easy to:
- Filter logs in ELK (Elasticsearch, Logstash, Kibana).
- Query logs using tools like **Grafana** or **Datadog**.
- Automate log analysis (e.g., detect anomalies).

**Example: Structured Logging in Go**
```go
package main

import (
	"log"
	"os"
)

type structuredLogger struct{}

func (l *structuredLogger) Info(msg string, fields map[string]interface{}) {
	fields["level"] = "INFO"
	logJSON(fields, msg)
}

func logJSON(fields map[string]interface{}, msg string) {
	data := make(map[string]interface{})
	for k, v := range fields {
		data[k] = v
	}
	data["message"] = msg
	data["timestamp"] = time.Now().Format(time.RFC3339)
	json.NewEncoder(os.Stdout).Encode(data)
}

// Usage:
logger := &structuredLogger{}
logger.Info("User logged in", map[string]interface{}{
	"user_id": 123,
	"ip":      "192.168.1.1",
})
```
**Output:**
```json
{
  "message": "User logged in",
  "user_id": 123,
  "ip": "192.168.1.1",
  "timestamp": "2024-05-20T12:00:00Z",
  "level": "INFO"
}
```

---

### **4. Implement Log Rotation & Retention Policies**

**Best Practices:**
- **Rotate logs daily/weekly** (prevent disk exhaustion).
- **Archive old logs** (S3, GCS, or cold storage).
- **Delete logs after 30-90 days** (unless legally required).

**Example: Log Rotation in Linux (rsyslog)**
```bash
# /etc/rsyslog.conf
if $programname == 'app' then {
    /var/log/app.log {
        size 100m
        compress
        olddir /var/log/app/archives/
    }
}
```

---

### **5. Add Correlation IDs for Distributed Tracing**

**Why It Matters:**
Without correlation IDs, logs from different services are **incomprehensible**. Example:
- A user clicks "Checkout" → Payment fails → Order not created.
- Without a trace ID, you can’t see how these events connect.

**Example: Adding Trace IDs in Express.js**
```javascript
const uuid = require('uuid');

// Middleware to generate trace IDs
app.use((req, res, next) => {
  req.traceId = uuid.v4();
  next();
});

// Log with trace ID
app.post('/checkout', (req, res) => {
  logger.info({
    level: 'INFO',
    trace_id: req.traceId,
    event: 'checkout_started',
    user_id: req.user.id
  });
  // ...
});
```

**Output Log Example:**
```json
{
  "trace_id": "abc123",
  "level": "INFO",
  "event": "checkout_started",
  "user_id": 456,
  "timestamp": "2024-05-20T12:05:00Z"
}
```

---

### **6. Use Separate Log Levels for Different Environments**

**Good for Production:**
- Disable `DEBUG` logs.
- Use `INFO` for key events.
- `ERROR` for failures.

**Example: Log Level Configuration in Java**
```java
// application.properties
logging.level.com.myapp=INFO
logging.level.org.springframework.web=WARN
logging.level.org.hibernate=ERROR
```

---

## **Implementation Guide: How to Fix Logging in Your App**

Now that we’ve covered the **theory**, let’s break down a **step-by-step fix** for a real-world application.

### **Step 1: Audit Current Logging**
- Check where logs are written (`console.log`, files, external services).
- Identify **noisy** logs (e.g., every `GET /api/users`).
- Find **sensitive data** being logged.

**Tools to Help:**
- **`grep` / `awk`** (filter logs for PII).
- **`logz.io` / `Sentry`** (analyze log volume).

### **Step 2: Rewrite Logging Logic**
- **Remove unnecessary logs** (e.g., debug statements in production).
- **Add structured logging** (JSON format).
- **Sanitize sensitive fields**.

**Before:**
```python
logger.error(f"Failed to process payment: {user.card_number}")  # ❌ Bad
```
**After:**
```python
logger.error({
    "event": "payment_failed",
    "user_id": user.id,
    "masked_card": "****-****-****-1234",  # ✅ Good
})
```

### **Step 3: Configure Log Rotation**
- Set up **log rotation** (e.g., `logrotate` in Linux).
- Archive old logs to **S3/GCS**.
- Delete logs after **90 days** (if compliant).

**Example `logrotate` Config (`/etc/logrotate.d/app`):**
```
/var/log/app.log {
    daily
    missingok
    compress
    rotate 30
    maxsize 100M
    copytruncate
    notifempty
}
```

### **Step 4: Implement Correlation IDs**
- Add a **trace ID** middleware in your web framework.
- Pass the trace ID through **microservices** (via headers or context).

**Example in Go (Add Trace ID to HTTP Request):**
```go
func traceMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        traceID := uuid.New().String()
        r = r.WithContext(context.WithValue(r.Context(), "traceID", traceID))
        logger.Info("Request received", map[string]string{"trace_id": traceID})
        next.ServeHTTP(w, r)
    })
}
```

### **Step 5: Test & Monitor**
- **Deploy changes** and verify logs are cleaner.
- **Set up alerts** for critical log patterns (e.g., `404 errors > 1%`).
- **Use tools like ELK** to query logs efficiently.

---

## **Common Mistakes to Avoid**

| **Anti-Pattern**               | **Why It’s Bad**                          | **Fix** |
|---------------------------------|-------------------------------------------|---------|
| Logging passwords/API keys      | Security breach risk                      | Mask sensitive fields |
| Too much noise (e.g., `GET /`)  | Hard to debug real issues                 | Filter irrelevant logs |
| No log rotation                 | Disk fills up                             | Configure `logrotate` |
| Unstructured logs               | Hard to parse/query                       | Use JSON structured logs |
| No correlation IDs              | Can’t debug distributed systems           | Add trace IDs everywhere |
| Hardcoded log levels            | Context lost                              | Use dynamic log levels |

---

## **Key Takeaways (TL;DR)**

✅ **Log strategically** – Don’t log everything. Focus on **critical events**.
✅ **Sanitize sensitive data** – Never log passwords, tokens, or PII.
✅ **Use structured logging** – JSON makes logs **machine-readable**.
✅ **Rotate & archive logs** – Prevent disk exhaustion.
✅ **Add correlation IDs** – Track requests across services.
✅ **Test & monitor** – Ensure logs are useful in production.

---

## **Conclusion: Logging Well = Debugging Easier**

Logging is **not about quantity**—it’s about **quality**. A well-structured logging system:
✔ Helps debug issues **faster**.
✔ Prevents **security leaks**.
✔ Keeps logs **manageable** (no disk explosions).
✔ Makes **distributed systems** traceable.

**Next Steps:**
1. **Audit your current logs** – What’s too noisy? What’s sensitive?
2. **Refactor logging** – Remove bad practices, add structure.
3. **Monitor & improve** – Use tools like ELK or Datadog to refine logs.

By avoiding these anti-patterns, you’ll build **maintainable, secure, and efficient** logging systems.

---
**What’s your biggest logging struggle?** Drop a comment—let’s discuss! 🚀