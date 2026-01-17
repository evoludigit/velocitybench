```markdown
# Logging Techniques: A Practical Guide to Efficient, Reliable, and Actionable Observability

*Why your logs are probably more important than you think (and how to make them work harder for you)*

## **Introduction**

Logging is the lifeblood of observability in backend systems. Yet, despite its importance, many teams treat logging as an afterthought—adding basic debug statements here and there, relying on default configurations, and hoping for the best when something goes wrong. Poor logging practices lead to:
- **Blind spots** during debugging (logs missing critical context)
- **Data overload** (useless logs drowning out the signal)
- **Security risks** (exposing sensitive data or misconfiguring permissions)
- **Operational inefficiency** (slow queries or inefficient storage)

The good news? With intentional logging techniques, you can transform logs from a passive record of activity into an active tool for debugging, monitoring, and even proactive system improvements.

In this guide, we’ll cover **practical logging techniques** that go beyond basic `console.log`. We’ll explore:
- **Structured logging** (why JSON beats plain text)
- **Log levels** (when to log DEBUG vs. ERROR)
- **Log correlation** (connecting requests across services)
- **Log sampling** (controlling volume without sacrificing insights)
- **Log storage and retrieval** (how to query logs efficiently)
- **Security considerations** (what *not* to log)

We’ll use **real-world examples in Go, Python, and Node.js** to demonstrate how to implement these techniques in modern backend systems. Let’s get started.

---

## **The Problem: Why Your Current Logging Might Be Failing You**

Logging is often treated as a "set it and forget it" feature. But in real-world systems, poorly designed logs create **three critical problems**:

### 1. Logs Lack Context (The "Where’s the Request ID?" Problem)
Imagine this scenario:
A user reports a `500 Internal Server Error` on your payment page. Your error log shows:
```
ERROR: Failed to process payment
```
But how do you:
- Identify *which user* encountered the error?
- See *where* in the flow it failed?
- Check *what input* caused it?

Without **contextual metadata** (user ID, request path, timestamp, correlating traces), debugging is like searching for a needle in a haystack.

### 2. Log Volume is Unmanageable (The "I’m Drowning in Debug Logs" Problem)
Consider a high-traffic API endpoint:
```plaintext
2024-05-20 14:30:00.123 ERROR: User not found (ID: 123)
2024-05-20 14:30:00.124 DEBUG: Querying database for user
2024-05-20 14:30:00.125 DEBUG: Executing SQL: SELECT * FROM users WHERE id = 123
2024-05-20 14:30:00.126 ERROR: Failed to connect to database (timeout)
2024-05-20 14:30:00.127 DEBUG: Retrying connection...
```
Now scale this to **10,000 requests/second**. Your log storage costs skyrocket, and critical errors get lost in the noise.

### 3. Security Risks (The "Oops, We Just Leaked Passwords" Problem)
A common mistake is logging sensitive data:
```python
# ❌ Bad: Logging raw input
log.warning(f"User submitted payload: {request.body}")
```
If an attacker gains access to your logs, they now see:
```json
{
  "action": "reset_password",
  "credentials": {
    "email": "user@example.com",
    "password": "s3cr3tP@ssw0rd!"  // 😱
  }
}
```
This violates **GDPR, PCI-DSS**, and common sense.

---
## **The Solution: Modern Logging Techniques**

To address these problems, we’ll adopt these **five core logging techniques**:

1. **Structured Logging** (JSON over plain text)
2. **Log Correlation** (tracing requests across services)
3. **Log Sampling** (controlling volume intelligently)
4. **Proper Log Levels** (INFO vs. DEBUG vs. WARN)
5. **Security-Aware Logging** (redacting sensitive data)

We’ll implement these in **Go, Python, and Node.js**, with a focus on **practicality** and **real-world tradeoffs**.

---

## **1. Structured Logging: Why JSON Wins**

### **The Problem with Plain Text Logs**
Plain text logs are hard to:
- Parse programmatically.
- Filter in log analyzers ( ELK, Datadog, etc.).
- Correlate across services.

Example of a messy log:
```
[2024-05-20 14:30:00] ERROR: Failed to validate token. Token: eyJhbGci... (truncated)
```

### **Solution: Structured Logging (JSON)**
Structured logs use a consistent format (e.g., JSON) to embed metadata. Example:
```json
{
  "timestamp": "2024-05-20T14:30:00Z",
  "level": "ERROR",
  "service": "auth-service",
  "request_id": "abc123-456-xyz",
  "user_id": 42,
  "message": "Failed to validate token",
  "details": {
    "token": "eyJhbGci... (redacted)",
    "validation_error": "expired"
  }
}
```

### **Why JSON?**
✅ **Machine-readable**: Easily parsed by tools like ELK, Splunk, or custom scripts.
✅ **Filterable**: Query logs with:
   ```sql
   SELECT * FROM logs WHERE level = 'ERROR' AND service = 'auth-service';
   ```
✅ **Consistent**: Avoids ambiguity (e.g., timestamps in ISO 8601 format).

---

### **Code Examples: Structured Logging in 3 Languages**

#### **Example 1: Go (Using `log/json` or `zap`)**
```go
package main

import (
	"context"
	"log/json"
	"time"
)

func main() {
	logger := json.NewEncoder(log.Default())

	ctx := context.WithValue(context.Background(), "user_id", 42)
	ctx = context.WithValue(ctx, "request_id", "abc123-456-xyz")

	// Log a structured error
	err := fmt.Errorf("failed to validate token: expired")
	logData := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"level":     "ERROR",
		"service":   "auth-service",
		"message":   err.Error(),
		"details": map[string]string{
			"type":     "validation_error",
			"subtype":  "expired",
		},
	}
	logger.Encode(logData)

	// With context values
	logger.Encode(map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"level":     "INFO",
		"user_id":   ctx.Value("user_id"),
		"request_id": ctx.Value("request_id"),
		"action":    "login_attempt",
	})
}
```

#### **Example 2: Python (Using `structlog`)**
```python
import structlog
from structlog import get_logger

logger = structlog.get_logger()

# Bind context (e.g., request ID)
logger.bind(
    user_id=42,
    request_id="abc123-456-xyz",
    service="auth-service"
).info("login_attempt")

# Log an error with details
try:
    validate_token("invalid_token")
except ValueError as e:
    logger.bind(
        validation_error=str(e),
        token="eyJhbGci... (redacted)"  # Never log full tokens!
    ).error("failed_to_validate_token")
```

#### **Example 3: Node.js (Using `pino`)**
```javascript
const pino = require('pino')();

// Log a structured error
pino.error({
    service: 'auth-service',
    userId: 42,
    requestId: 'abc123-456-xyz',
    message: 'Failed to validate token',
    details: {
        type: 'validation_error',
        subtype: 'expired',
    },
});

// With request context
pino.info({ ...pino.requestCtx(), action: 'login_attempt' });
```

---

## **2. Log Correlation: Tracing Requests Across Services**

### **The Problem**
Modern systems are **distributed**: a single user request may touch:
1. API Gateway
2. Auth Service
3. Payment Service
4. Database

Without correlation, logs look like:
```
[ Auth Service ] ERROR: User not found (ID: 42)
[ Payment Service ] ERROR: Failed to charge user
```
You have **no way** to know these belong to the same request.

### **Solution: Request IDs and Distributed Traces**
Add a **unique `request_id`** to every log entry and propagate it across services.

#### **Example: Propagating `request_id` in Go**
```go
package main

import (
	"context"
	"log"
	"net/http"
	"uuid"
)

// Middleware to set request_id
func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		reqID := r.Context().Value("request_id")
		if reqID == nil {
			reqID = uuid.New()
			r = r.WithContext(context.WithValue(r.Context(), "request_id", reqID))
		}

		wrapped := loggingResponseWriter{ResponseWriter: w}
		defer logRequest(wrapped, r)

		next.ServeHTTP(w, r)
	})
}

// Log HTTP request/response
func logRequest(w wrappedResponseWriter, r *http.Request) {
	logger := log.Default()
	logData := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"level":     "INFO",
		"service":   "api-gateway",
		"request_id": r.Context().Value("request_id"),
		"method":    r.Method,
		"path":      r.URL.Path,
		"status":    w.Status(),
	}
	logger.Encode(logData)
}
```

#### **Example: Propagating `request_id` in Python (FastAPI)**
```python
from fastapi import FastAPI, Request, Header
import structlog
from uuid import uuid4

app = FastAPI()
logger = structlog.get_logger()

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid4())
        request.headers["X-Request-ID"] = request_id

    logger.bind(
        request_id=request_id,
        path=request.url.path,
        method=request.method
    ).info("incoming_request")

    response = await call_next(request)
    logger.bind(status=response.status_code).info("request_completed")
    return response
```

---

## **3. Log Sampling: Reducing Volume Without Losing Insights**

### **The Problem**
High-traffic systems generate **millions of logs per second**. If you log everything:
- **Storage costs explode** (e.g., $100/month for 1TB vs. $10/month for 100GB).
- **Performance degrades** (disk I/O, network overhead).
- **Signal gets lost** in noise (e.g., 99.9% of logs are `INFO` level).

### **Solution: Intelligent Sampling**
Instead of logging **everything**, log:
- **100% of ERROR/WARN logs** (critical issues).
- **1% of INFO logs** (randomly sampled).
- **0% of DEBUG logs** (except during debugging sessions).

#### **Example: Sampling in Go**
```go
import (
	"math/rand"
	"time"
)

func shouldLog(level string, sampleRate float64) bool {
	// Sample based on level and rate
	switch level {
	case "ERROR", "WARN":
		return true
	case "INFO":
		return rand.Float64() < sampleRate
	default:
		return false
	}
}

func logWithSampling(level, message string) {
	if shouldLog(level, 0.01) { // 1% sampling for INFO
		log.Printf("[%s] %s", level, message)
	}
}
```

#### **Example: Sampling in Python**
```python
import random

def should_log(level: str, sample_rate: float = 0.01) -> bool:
    if level in ["ERROR", "WARN"]:
        return True
    elif level == "INFO":
        return random.random() < sample_rate
    return False

def log_with_sampling(level: str, message: str, **kwargs):
    if should_log(level):
        structlog.get_logger().bind(**kwargs).log(level=level, message=message)
```

---

## **4. Proper Log Levels: When to Use What**

| Log Level | Use Case                          | Example                          |
|-----------|-----------------------------------|----------------------------------|
| `TRACE`   | Low-level debugging (internal libs) | `debug_query_execution_time`     |
| `DEBUG`   | Detailed troubleshooting         | `sql_query: SELECT * FROM users` |
| `INFO`    | Normal operational messages        | `user_login_successful`           |
| `WARN`    | Suspicious/non-critical issues    | `high_latency_detected`           |
| `ERROR`   | Critical failures                 | `database_connection_failed`      |
| `CRITICAL`| System-critical errors            | `disk_full_no_writes_possible`   |

### **Anti-Patterns to Avoid**
❌ **Overusing `DEBUG`**:
   ```go
   log.Println("User ID:", userID) // Too verbose!
   ```
✅ **Better**:
   ```go
   logger.Info("user_login", structlog.Fields{
       "user_id": userID,
   })
   ```

❌ **Swallowing errors in production**:
   ```python
   try:
       do_something()
   except Exception:
       pass  # 🚨 Lost error!
   ```
✅ **Better**:
   ```python
   try:
       do_something()
   except Exception as e:
       logger.error("operation_failed", exc_info=True)
   ```

---

## **5. Security-Aware Logging: What NOT to Log**

### **Sensitive Data to Avoid Logging**
| Data Type               | Why It’s Dangerous                          | Example                          |
|-------------------------|--------------------------------------------|----------------------------------|
| Passwords               | Leaks violate compliance (GDPR, PCI-DSS).  | `password: "s3cr3t"`              |
| API Keys                | Enables unauthorized access.                | `api_key: "sk_live_abc123"`       |
| PII (Personally Identifiable Info) | Privacy violations.       | `user_email: "user@example.com"` |
| Full error stacks       | Helps attackers exploit vulnerabilities.    | `Traceback (most recent call last):` |
| Tokens (JWT, OAuth)     | Can be reused for impersonation.           | `token: "eyJhbGciOiJIUzI1NiI"`

### **How to Log Securely**
1. **Redact sensitive fields**:
   ```go
   logger.Info("login_attempt",
       structlog.Fields{
           "user_email": "user@example.com",
           "password":   "[REDACTED]",
       })
   ```
2. **Use `exc_info=False` for stack traces in production**:
   ```python
   logger.exception("failed_to_process payment", exc_info=False)
   ```
3. **Avoid logging raw input**:
   ```javascript
   // ❌ Bad
   pino.info({ request_body: req.body });

   // ✅ Better
   pino.info({
       request_method: req.method,
       request_path: req.path,
       user_agent: req.headers['user-agent'],
   });
   ```

---

## **Implementation Guide: A Checklist**

| Step                          | Action Items                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| **1. Choose a Structured Logger** | Use `zap` (Go), `structlog` (Python), or `pino` (Node.js).               |
| **2. Add Request Correlation**  | Propagate `request_id` across services via headers/context.                |
| **3. Define Log Levels**       | Use `INFO` for normal ops, `ERROR` for failures, avoid `DEBUG` in prod.   |
| **4. Implement Sampling**      | Sample `INFO` logs at 1-10%, log all `ERROR`/`WARN`.                        |
| **5. Secure Logs**             | Redact passwords, tokens, and PII. Use `exc_info=False` in production.    |
| **6. Store Logs Efficiently**  | Use log shippers (Fluentd, Logstash) to filter noise before storage.      |
| **7. Monitor Log Volume**      | Set alerts for sudden log spikes (e.g., 10x increase in 5 minutes).         |

---

## **Common Mistakes to Avoid**

### ❌ **Mistake 1: Logging Too Much (or Too Little)**
- **Over-logging**: Fills storage, slows down apps, and drowns out important logs.
- **Under-logging**: Leaves you blind during outages.
- **Fix**: Use **sampling** and **log levels** strategically.

### ❌ **Mistake 2: Ignoring Log Retention**
- **Problem**: Old logs bloat storage.
- **Solution**: Set retention policies (e.g., 30 days for `INFO`, 90 days for `ERROR`).

### ❌ **Mistake 3: Not Testing Logs in Production**
- **Problem**: Your dev environment logs `DEBUG`, but production is `INFO`. You miss bugs.
- **Solution**: Use **feature flags** to toggle log levels:
  ```go
  if os.Getenv("LOG_LEVEL") == "DEBUG" {
      logger.Debug("detailed_operation")
  }
  ```

### ❌ **Mistake 4: Logging Raw SQL