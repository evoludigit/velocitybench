```markdown
# **"Logging Guidelines: Build Reliable Systems with Structured, Practical Logging"**

*By [Your Name], Senior Backend Engineer*

Logging isn’t just about writing debug statements—it’s the lifeline for debugging, monitoring, and maintaining production systems. Without **consistent logging guidelines**, teams write logs haphazardly, leading to:

- **Cluttered logs** that are hard to parse
- **Missing critical information** during outages
- **Security risks** from poorly handled sensitive data
- **Inconsistent debugging experience** across services

This post covers **practical logging guidelines**—what to log, how to structure it, and how to avoid common pitfalls. We’ll explore:
- **What to log** (and what to avoid)
- **Best practices for log formatting and structure**
- **Tools and integrations** (e.g., structured logging, log aggregation)
- **Real-world tradeoffs** (performance vs. verbosity, security vs. usability)

By the end, you’ll have a **production-ready logging strategy** you can implement today.

---

## **The Problem: Why Logging Guidelines Matter**

Logging is one of the most underrated yet critical aspects of backend development. Without standards, even well-written systems become **debugging nightmares**:

### **1. Unstructured Logs Are Useless**
Consider this example from a poorly logged API:

```javascript
// ❌ Unstructured log: Hard to query or analyze
console.log("User login attempted");
console.log("Status:", 200);
console.log("IP:", req.ip);
console.log("Timestamp:", new Date());
```

Now, how would you **filter logs** for failed logins from a specific IP? You’d have to **grep through raw text**—inefficient and error-prone.

### **2. Security Risks from Improper Logging**
Ever seen something like this?

```python
# ❌ Logging sensitive data
logger.info(f"User {user.id} (PII: {user.ssn}) accessed dashboard")
```

This **exposes sensitive data** in logs, violating compliance (e.g., GDPR, HIPAA). Even if you scrub PII later, **logs may still persist in backups**.

### **3. Log Overload and Performance Issues**
Logging **too much** can:
- **Slow down your app** (especially in high-traffic systems).
- **Fill up disk space** (leading to log rotation failures).
- **Drown out important errors** in noise.

### **4. Inconsistent Debugging Across Services**
If **Service A** logs at `DEBUG` level and **Service B** at `ERROR`, troubleshooting becomes a **log-hopping nightmare**. Each service should follow the same **log format and severity levels**.

---

## **The Solution: Structured Logging Guidelines**

The key to **reliable logging** is:
1. **Structure** (machine-readable format)
2. **Consistency** (same fields across services)
3. **Control** (proper log levels and retention)
4. **Security** (avoid logging sensitive data)

### **1. Use Structured Logging (JSON > Plain Text)**
**Plain text logs** are hard to parse. **Structured logs** (e.g., JSON) enable:
- **Efficient querying** (e.g., `grep "status:500"`).
- **Automated analysis** (ELK Stack, Datadog, Splunk).
- **Retention policies** (e.g., only keep logs for 30 days).

#### **Example: Structured vs. Unstructured Logging**
```javascript
// ❌ Unstructured (hard to parse)
console.log("User login failed. IP: 127.0.0.1, User: john.doe");

// ✅ Structured (JSON, easy to query)
logger.info({
  event: "login_attempt",
  status: "failed",
  user_id: "john.doe",
  ip: "127.0.0.1",
  timestamp: new Date().toISOString()
});
```

### **2. Standardize Log Fields**
Every log entry should include **core metadata**:
| Field          | Purpose |
|----------------|---------|
| `timestamp`    | When the event occurred (ISO 8601 format) |
| `service`      | Which microservice generated the log |
| `level`        | Severity (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`) |
| `trace_id`     | Correlation ID for distributed tracing |
| `user_id`      | (If applicable) Anonymous if not needed |

**Example in Go:**
```go
package main

import (
	"log"
	"time"
)

type LogEntry struct {
	Timestamp string `json:"timestamp"`
	Level     string `json:"level"`
	Service   string `json:"service"`
	Message   string `json:"message"`
	Data      map[string]interface{} `json:"data"`
}

func main() {
	logEntry := LogEntry{
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		Level:     "INFO",
		Service:   "user-service",
		Message:   "User created successfully",
		Data:      map[string]interface{}{"user_id": "123", "email": "john@example.com"},
	}
	jsonLog, _ := json.Marshal(logEntry)
	log.Println(string(jsonLog))
}
```

**Output:**
```json
{
  "timestamp": "2024-05-20T14:30:00Z",
  "level": "INFO",
  "service": "user-service",
  "message": "User created successfully",
  "data": { "user_id": "123", "email": "john@example.com" }
}
```

### **3. Define Proper Log Levels**
| Level      | Usage |
|------------|-------|
| `DEBUG`    | Detailed debug info (disable in production) |
| `INFO`     | Normal operation events (e.g., "API called") |
| `WARN`     | Potential issues (e.g., "Low disk space") |
| `ERROR`    | Failed operations (recoverable) |
| `FATAL`    | Critical failures (application exit) |

**Example in Python (with `loguru`):**
```python
from loguru import logger

logger.add("app.log", rotation="10 MB")

def process_payment(user_id, amount):
    try:
        # Log at INFO level for successful operations
        logger.info(
            "Payment processed",
            extra={
                "user_id": user_id,
                "amount": amount,
                "service": "payment-service"
            }
        )
    except Exception as e:
        logger.error(
            "Payment failed",
            extra={
                "user_id": user_id,
                "error": str(e),
                "service": "payment-service"
            }
        )
```

### **4. Avoid Logging Sensitive Data**
- **Never log passwords, tokens, or PII** (even if "scrubbed").
- Use **environment variables** for secrets and **contextual logging** (e.g., log `user_id` instead of `user.email`).

**Bad (logs full email):**
```python
logger.error("Failed login", extra={"email": "john@example.com"})
```

**Good (logs anonymized):**
```python
logger.error("Failed login", extra={"user_id": "123"})
```

### **5. Use Correlation IDs for Distributed Tracing**
In microservices, **requests span multiple services**. A `trace_id` helps track them:

```javascript
// Express.js middleware to add trace_id
app.use((req, res, next) => {
  req.trace_id = crypto.randomUUID();
  next();
});

// Logging with trace_id
logger.info({
  service: "order-service",
  trace_id: req.trace_id,
  action: "create_order",
  status: 200
});
```

### **6. Rotate and Retain Logs Wisely**
- **Rotate logs** (e.g., daily/weekly) to prevent disk fills.
- **Archive old logs** (e.g., S3, cold storage).
- **Set TTL policies** (e.g., delete logs older than 90 days).

**Example (Logrotate in Linux):**
```
/var/log/app {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 640 app app
}
```

---

## **Implementation Guide: Step-by-Step**

### **Step 1: Choose a Logging Library**
| Language  | Recommended Library | Why? |
|-----------|---------------------|------|
| Python    | `loguru` / `structlog` | Structured logging out of the box |
| Java      | SLF4J + Logback | Standardized, flexible |
| Go        | `zap` | High performance, structured |
| JavaScript| `pino` / `winston` | Lightweight, JSON-friendly |

**Example: Structured Logging in Node.js (Pino)**
```javascript
const pino = require('pino')({
  level: process.env.LOG_LEVEL || 'info',
  base: null, // No timestamp prefix
  serializers: {
    args: (args) => args // Keep structured logs intact
  }
});

app.use(pino.logger()); // Middleware for Express
app.use(pino.http());   // HTTP request logging

// Log with context
pino.info({
  service: "api-gateway",
  path: req.path,
  method: req.method,
  status: res.statusCode
}, "Request processed");
```

### **Step 2: Define a Centralized Log Format**
All services should follow this **log schema**:
```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARN|ERROR",
  "service": "string",
  "trace_id": "uuid",
  "message": "string",
  "data": { "key": "value" }
}
```

**Example in Terraform (IaC for Loggers):**
```hcl
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ecs/my-service"
  retention_in_days = 90
}

resource "aws_iam_role_policy" "log_export" {
  name = "AllowLogExport"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["logs:*"],
      Resource = "*"
    }]
  })
}
```

### **Step 3: Integrate with a Log Aggregator**
| Tool          | Use Case |
|---------------|----------|
| **ELK Stack** | Full-text search, visualizations |
| **Datadog**   | APM + logs in one place |
| **Loki**      | Lightweight log aggregation |
| **CloudWatch** | AWS-native logging |

**Example: Sending Logs to Loki (Grafana)**
```go
package main

import (
	"context"
	"time"

	loki "github.com/grafana/loki/pkg/logproto"
	"google.golang.org/grpc"
)

func sendToLoki(logEntry LogEntry) error {
	conn, err := grpc.Dial("loki:3100", grpc.WithInsecure())
	if err != nil {
		return err
	}
	defer conn.Close()

	client := loki.NewLokiClient(conn)

	stream, err := client.WriteLogs(context.Background())
	if err != nil {
		return err
	}

	// Convert logEntry to Loki's Stream and Entry
	stream.Send(&loki.Stream{
		Labels: map[string]string{
			"service": logEntry.Service,
			"level":   logEntry.Level,
		},
		Entries: []*loki.Entry{
			{
				Ts:      time.Now().UnixNano(),
				Line:    logEntry.Message,
				Labels: map[string]string{
					"trace_id": logEntry.TraceID,
				},
			},
		},
	})
	return nil
}
```

### **Step 4: Secure Log Storage**
- **Encrypt logs at rest** (e.g., AWS KMS, GCP CMEK).
- **Restrict log access** (IAM policies, RBAC).
- **Auditing**: Log access to logs (e.g., `aws logs:FilterLogEvents`).

**Example: IAM Policy for Secure Logs**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/ecs/my-service:*",
        "arn:aws:logs:*:*:log-stream:*"
      ]
    }
  ]
}
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Logging Too Much (Performance Impact)**
- **Fix**: Use `DEBUG` sparingly; default to `INFO`/`WARN` in production.
- **Tool**: Disable debug logs with environment variables:
  ```bash
  LOG_LEVEL=warn node server.js
  ```

### **❌ Mistake 2: Logging Raw Exceptions**
- **Problem**: Stack traces are hard to read.
- **Fix**: Log **only the error message** (or a summary) and the stack trace in `DEBUG`:
  ```python
  try:
      risky_operation()
  except Exception as e:
      logger.error("Operation failed", exc_info=True)  # Logs stack trace in DEBUG
  ```

### **❌ Mistake 3: Not Handling Log Failure**
- **Problem**: If logging fails, errors are silenced.
- **Fix**: Ensure log writes are **non-blocking** and retried:
  ```javascript
  const asyncLogger = async (level, message, data) => {
    try {
      await logger.log(level, message, data);
    } catch (err) {
      // Fallback to stderr
      console.error(`[LOG FAILURE] ${err.message}`);
    }
  };
  ```

### **❌ Mistake 4: Ignoring Log Rotation**
- **Problem**: Logs grow indefinitely, filling disk space.
- **Fix**: Use **log rotation** (e.g., `logrotate`, AWS CloudWatch Logs retention).

### **❌ Mistake 5: Mixing Logs with Business Logic**
- **Problem**: Logs become a code dump.
- **Fix**: Use **separate logging functions** for business vs. technical events:
  ```go
  func logBusinessEvent(userID string, action string) {
      logger.Info("user_action", map[string]interface{}{
          "user_id": userID,
          "action":  action,
      })
  }

  func logError(err error) {
      logger.Error("system_error", map[string]interface{}{
          "error":   err.Error(),
          "stack":   getStackTrace(), // Only in DEBUG
      })
  }
  ```

---

## **Key Takeaways (TL;DR)**

✅ **Structure logs** (JSON > plain text) for machine readability.
✅ **Standardize fields** (`timestamp`, `level`, `service`, `trace_id`).
✅ **Control verbosity** (avoid `DEBUG` in production; use proper log levels).
✅ **Never log sensitive data** (PII, passwords, tokens).
✅ **Use correlation IDs** (`trace_id`) for distributed tracing.
✅ **Rotate and retain logs** (prevent disk fills; archive old logs).
✅ **Integrate with observability tools** (ELK, Datadog, Loki).
✅ **Secure log storage** (encryption, IAM, auditing).
❌ **Avoid**: Unstructured logs, logging exceptions directly, silent log failures.

---

## **Conclusion: Build Observability from Day One**

Logging isn’t an afterthought—it’s the **backbone of observability**. By following these guidelines, you’ll:
- **Debug faster** with structured, queryable logs.
- **Reduce security risks** by avoiding sensitive data leaks.
- **Optimize performance** with controlled log levels.
- **Scale smoothly** with log aggregation and retention policies.

### **Next Steps**
1. **Audit your current logs**: Are they structured? Are sensitive fields redacted?
2. **Standardize your logging**: Adopt a schema and tooling (e.g., `zap` for Go, `loguru` for Python).
3. **Automate log collection**: Set up log forwarding to a central aggregator (ELK, Loki).
4. **Monitor log health**: Ensure logs aren’t failing silently.

**Pro tip**: Start with **one service**, then expand the pattern across your stack. Small, consistent improvements lead to **massive debugging savings** in production.

---
**What’s your biggest logging pain point?** Share in the comments—let’s discuss! 🚀
```

---
**Why this works:**
- **Practical first**: Code examples in multiple languages (Go, Python, JavaScript).
- **Tradeoffs explicit**: Performance vs. verbosity, security vs. usability.
- **Actionable**: Step-by-step implementation guide.
- **Audience-focused**: Targets senior engineers who want **real-world patterns**, not theory.