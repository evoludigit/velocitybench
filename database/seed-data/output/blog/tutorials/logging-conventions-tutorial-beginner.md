```markdown
---
title: "Logging Conventions: Building Debuggable Systems from Day One"
date: 2023-11-15
author: "Alex Carter"
tags: ["backend", "database", "API design", "logging", "observability"]
description: "Learn how structured logging conventions can save you hours of debugging and make your team's life easier. Practical examples included."
---

# Logging Conventions: Building Debuggable Systems from Day One

If you’ve ever spent an hour sifting through cryptic log lines—trying to figure out why a payment failed, why a user got a 500 error, or why a database query suddenly took 10 seconds—you’ll know the pain of unstructured logs.

The good news? **You don’t have to keep writing logs like this:**

```
[2023-11-15T12:45:32.587Z] ERROR: User not found (id: 12345)
[2023-11-15T12:45:33.123Z] INFO: Database connection closed
[2023-11-15T12:45:34.765Z] WARNING: High latency on /api/v1/search
```

**Logging conventions** turn this noise into a structured, searchable, and actionable system. In this post, I’ll show you how to adopt consistent logging practices that make debugging faster, reduce downtime, and save your team from guesswork.

---

## The Problem: Why Logs Are Hard Without Conventions

Imagine you’re on-call at 2 AM, and an alert fires for failed transactions. You open your logs and see:

```
[ERROR] Could not process payment for user_id=12345
[ERROR] DB connection timeout
[ERROR] Failed to validate card details
```

Without a clear structure, you’re left to:
1. **Guess which log belongs to which request** (e.g., is this the same user_id from earlier?).
2. **Waste time filtering through irrelevant logs** (e.g., is this a database timeout unrelated to the payment failure?).
3. **Recreate the exact sequence of events manually**, which is error-prone and slow.

### Common Logging Pitfalls:
- **Lack of context**: Logs often lack request IDs, user IDs, or timestamps that correlate with other systems (e.g., databases, APIs).
- **Inconsistent formatting**: Mixing plain text, structured JSON, and raw numbers makes parsing difficult.
- **No severity prioritization**: Critical errors get buried under INFO messages about disk space.
- **Missing correlation IDs**: Without a unique ID per request, you can’t trace a user’s journey across services.

### The Cost of Poor Logging:
- **Slower incident resolution**: According to [Dynatrace’s 2023 State of DevOps report](https://www.dynatrace.com/resources/whitepapers/state-of-devops-report/), poor observability (which includes logging) adds **$1.7 million annually per 1,000 people** in lost productivity.
- **Debugging blind spots**: Without structured logs, you’ll miss correlated failures (e.g., a database timeout + a timeout in your payment service).
- **Team frustration**: Developers hate digging through logs. When logs are inconsistent, they’ll stop using them entirely.

---

## The Solution: Structured Logging Conventions

The fix? **Standardize your logs with these key principles:**
1. **Use structured logging** (e.g., JSON) to enable efficient querying.
2. **Correlate logs with requests** using request IDs and trace IDs.
3. **Include essential context** (timestamps, user IDs, service names).
4. **Enforce severity levels** (ERROR > WARNING > INFO > DEBUG).
5. **Log consistently across services** (avoid "service A logs differently than service B").

### How It Works:
Here’s what a well-structured log looks like (JSON format):
```json
{
  "timestamp": "2023-11-15T12:45:32.587Z",
  "request_id": "req_123abc",
  "trace_id": "trc_456xyz",
  "service": "payment-service",
  "level": "ERROR",
  "message": "Failed to process payment for user_id=12345",
  "user_id": "12345",
  "user_email": "user@example.com",
  "correlation": {
    "db_transaction": "txn_789def",
    "api_call": "/api/v1/payments/process"
  },
  "error": {
    "type": "ValidationError",
    "details": "Card expiry date too soon",
    "stacktrace": "..."
  }
}
```

### Why This Matters:
- **Queryable**: You can run `grep "user_id=12345"` or filter by `level=ERROR` in tools like ELK or Datadog.
- **Traceable**: The `request_id` and `trace_id` let you follow a user’s journey across microservices.
- **Actionable**: The `error.details` field gives you immediate context without extra digging.

---

## Components of Effective Logging Conventions

### 1. **Log Levels (Severity Priority)**
   Use standard levels to prioritize what matters:
   - `ERROR` (Critical failures)
   - `WARNING` (Non-critical issues)
   - `INFO` (Normal operation, e.g., API calls)
   - `DEBUG` (Detailed logs for developers)
   - `TRACE` (Extremely verbose, e.g., SQL queries)

   **Example in Python (using `logging` module):**
   ```python
   import logging

   logging.basicConfig(level=logging.INFO)  # Only show INFO and above
   logger = logging.getLogger(__name__)

   logger.error("Failed to process payment", extra={
       "user_id": 12345,
       "request_id": "req_123abc"
   })
   ```

   **Output:**
   ```
   ERROR:root:Failed to process payment user_id=12345 request_id=req_123abc
   ```

   **Pro Tip**: Use a library like [`structlog`](https://www.structlog.org/) (Python) or [`pino`](https://github.com/pinojs/pino) (Node.js) to format logs as JSON.

---

### 2. **Request and Trace IDs**
   Every log entry should include:
   - A **unique `request_id`** (per HTTP request).
   - A **`trace_id`** (for distributed tracing across services).

   **Example in Node.js (Express):**
   ```javascript
   const { v4: uuidv4 } = require('uuid');

   app.use((req, res, next) => {
     req.request_id = uuidv4();
     req.trace_id = uuidv4();
     next();
   });

   // Log middleware
   app.use((req, res, next) => {
     console.log(JSON.stringify({
       timestamp: new Date().toISOString(),
       request_id: req.request_id,
       trace_id: req.trace_id,
       service: "user-service",
       level: "INFO",
       message: "Incoming request",
       path: req.path
     }));
     next();
   });
   ```

   **Output (JSON):**
   ```json
   {
     "timestamp": "2023-11-15T12:45:32.587Z",
     "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
     "trace_id": "x9y0z1a2-b3c4-56d7-e8f9-g0h1i2j3k4l5",
     "service": "user-service",
     "level": "INFO",
     "message": "Incoming request",
     "path": "/api/v1/users/123"
   }
   ```

---

### 3. **Structured Data (JSON Fields)**
   Avoid plain text. Instead of:
   ```json
   { "message": "User not found: 12345" }
   ```
   Use:
   ```json
   {
     "level": "ERROR",
     "user_id": 12345,
     "user_email": "user@example.com",
     "error": {
       "type": "NotFoundError",
       "code": 404,
       "message": "User with ID 12345 does not exist"
     }
   }
   ```

   **Example in Go:**
   ```go
   package main

   import (
       "encoding/json"
       "log"
       "net/http"
   )

   func main() {
       http.HandleFunc("/users", func(w http.ResponseWriter, r *http.Request) {
           var logData = map[string]interface{}{
               "timestamp": time.Now().UTC().Format(time.RFC3339),
               "request_id": uuid.New().String(),
               "service":   "user-service",
               "level":     "ERROR",
               "message":   "User not found",
               "user_id":   12345,
               "error": map[string]string{
                   "type":    "NotFoundError",
                   "message": "User with ID 12345 does not exist",
               },
           }
           logJSON(logData)
       })
   }

   func logJSON(data map[string]interface{}) {
       jsonData, _ := json.Marshal(data)
       log.Printf("%s", string(jsonData))
   }
   ```

   **Output:**
   ```json
   {
     "timestamp": "2023-11-15T12:45:32.587Z",
     "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
     "service": "user-service",
     "level": "ERROR",
     "message": "User not found",
     "user_id": 12345,
     "error": {
       "type": "NotFoundError",
       "message": "User with ID 12345 does not exist"
     }
   }
   ```

---

### 4. **Correlation Fields**
   Link logs to other systems (e.g., database transactions, external APIs):
   ```json
   {
     "db_transaction": "txn_789def",
     "api_call": "/api/v1/payments/process",
     "correlation_id": "corr_abc123"
   }
   ```

   **Example in Java (Spring Boot):**
   ```java
   @RestController
   public class PaymentController {

       private final Logger logger = LoggerFactory.getLogger(PaymentController.class);

       @PostMapping("/process")
       public ResponseEntity<String> processPayment(@RequestBody PaymentRequest request) {
           String requestId = UUID.randomUUID().toString();
           String traceId = UUID.randomUUID().toString();

           logger.info("Processing payment for user {} (request: {})",
               request.getUserId(),
               requestId,
               buildLogFields(requestId, traceId, "/api/v1/payments/process"));

           // ... business logic ...
       }

       private Map<String, Object> buildLogFields(String reqId, String traceId, String path) {
           Map<String, Object> fields = new HashMap<>();
           fields.put("request_id", reqId);
           fields.put("trace_id", traceId);
           fields.put("service", "payment-service");
           fields.put("path", path);
           return fields;
       }
   }
   ```

   **Log Output (structured):**
   ```json
   {
     "timestamp": "2023-11-15T12:45:32.587Z",
     "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
     "trace_id": "x9y0z1a2-b3c4-56d7-e8f9-g0h1i2j3k4l5",
     "level": "INFO",
     "message": "Processing payment for user 12345",
     "user_id": 12345,
     "correlation": {
       "db_transaction": null,
       "api_call": "/api/v1/payments/process"
     }
   }
   ```

---

### 5. **Logging Middleware (APIs)**
   For APIs, log:
   - Incoming requests (with headers, body, and status).
   - Outgoing responses (with latency).
   - Errors (with full stack traces in DEBUG mode).

   **Example in Ruby (Rails):**
   ```ruby
   # config/initializers/logging.rb
   Rails.logger = Logger.new(STDOUT)
   Rails.logger.level = Logger::INFO

   Rails.application.config.middleware.use Rack::CommonLogger do |env|
     request_id = SecureRandom.uuid
     trace_id = SecureRandom.uuid

     begin
       status = env.at_path(env["PATH_INFO"], env)
       response = ActionDispatch::Response.new
       response.status = status

       json_log = {
         timestamp: Time.now.utc.iso8601,
         request_id: request_id,
         trace_id: trace_id,
         service: "user-service",
         level: "INFO",
         message: "Incoming request",
         method: env["REQUEST_METHOD"],
         path: env["PATH_INFO"],
         status: status,
         latency: env["action_dispatch.runtime"]
       }.to_json

       Rails.logger.info(json_log)
     rescue => e
       Rails.logger.error({ error: e.message }.to_json)
     end
   end
   ```

   **Output (JSON):**
   ```json
   {
     "timestamp": "2023-11-15T12:45:32.587Z",
     "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
     "trace_id": "x9y0z1a2-b3c4-56d7-e8f9-g0h1i2j3k4l5",
     "service": "user-service",
     "level": "INFO",
     "message": "Incoming request",
     "method": "POST",
     "path": "/api/v1/users",
     "status": 201,
     "latency": 45
   }
   ```

---

## Implementation Guide: How to Adopt Logging Conventions

### Step 1: Choose a Logging Library
Pick a library that supports structured logging:
- **Python**: `structlog`, `loguru`, `json-logging`
- **Node.js**: `pino`, `winston`
- **Go**: `zap`, `logrus`
- **Java**: `Logback` with JSON encoder, `SLF4J`
- **Ruby**: `Rails.logger` (JSON format), `logger`

### Step 2: Define a Standard Log Format
Agree on a schema (e.g., all logs must include `timestamp`, `request_id`, `level`, etc.).
Example schema:
```json
{
  "timestamp": "ISO_8601",
  "request_id": "UUID",
  "trace_id": "UUID",
  "service": "string",
  "level": "ERROR|WARNING|INFO|DEBUG",
  "message": "string",
  "context": {
    // Any additional fields (user_id, etc.)
  },
  "error": {
    "type": "string",
    "message": "string",
    "stacktrace": "string (optional)"
  }
}
```

### Step 3: Enforce Logging in All Services
- **APIs**: Log requests/responses (use middleware).
- **Databases**: Log queries with correlation IDs (e.g., `WITH trace_id = 'trc_...'` in SQL).
- **Background Jobs**: Include job IDs and parent request IDs.

### Step 4: Centralize Logs
Use a log aggregation tool:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Datadog**
- **Loki + Grafana**
- **AWS CloudWatch**

### Step 5: Automate Log Analysis
Set up alerts for:
- Spikes in `ERROR` logs.
- High latency (e.g., `latency > 500ms`).
- Missing `request_id` in logs.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Logging Too Much or Too Little
- **Too much**: DEBUG logs flooding your system (disable in production unless critical).
- **Too little**: Missing key context (e.g., `request_id`, `user_id`).

**Fix**: Start with `INFO` level in production, enable `DEBUG` only for troubleshooting.

### ❌ Mistake 2: Inconsistent Log Formats
Mixing plain text and JSON, or changing formats between services.

**Fix**: Enforce a single log format across all services (e.g., JSON only).

### ❌ Mistake 3: Not Correlating Across Services
Losing track of a user’s journey because logs aren’t linked.

**Fix**: Use `trace_id` and `request_id` to correlate logs across microservices.

### ❌ Mistake 4: Ignoring Performance
Overly verbose logs slow down your application.

**Fix**:
- Use async logging (e.g., `go.uber.org/zap` for Go).
- Sample logs (e.g., log 100% of `ERROR` but only 1% of `INFO`).

### ❌ Mistake 5: No Retention Policy
Storing logs forever bloats storage costs.

**Fix**: Set retention (e.g., 30 days for `INFO`, 90 days for `ERROR`).

### ❌ Mistake 6: Not Testing Logs
Assuming logs work until they fail in production.

**Fix**: Mock logging in unit tests:
```python
# Example: Test logging in Python
def test_payment_failure_logging():
    with patch('logging.getLogger') as mock_logger:
        mock_logger.return_value.error = MagicMock()
        process_payment(user_id=12345, card_expired=True)
        mock_logger.return_value.error.assert_called_with(
            "Failed to process payment for user 12345",
            extra={
                "user_id": 12345,
                "request_id": "req_123abc",
               