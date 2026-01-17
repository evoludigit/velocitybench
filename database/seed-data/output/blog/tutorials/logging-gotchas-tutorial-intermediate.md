```markdown
---
title: "Logging Gotchas: How to Avoid Common Pitfalls in Backend Logging"
author: "Alex Chen"
date: "June 15, 2024"
description: "A deep dive into common logging gotchas and how to implement robust logging practices in your backend applications. Learn from real-world mistakes and code examples."
tags: ["backend", "logging", "observability", "debugging", "DDD", "patterns"]
---

# Logging Gotchas: How to Avoid Common Pitfalls in Backend Logging

## Introduction

Logging is a fundamental tool for debugging, monitoring, and maintaining robust backend systems. But what seems like a simple feature—writing messages to disk—can become a source of subtle bugs and performance issues if not implemented carefully. As backends grow in complexity, logging patterns that work for simple CRUD applications often fail under the strain of microservices, distributed systems, and high-throughput APIs.

In this guide, we’ll dissect **common logging gotchas**—pitfalls that even experienced engineers face—and provide practical solutions. We’ll explore real-world examples, code patterns, and anti-patterns you should avoid. By the end, you’ll have a checklist to ensure your logging setup is reliable, performant, and maintainable.

---

## The Problem

Logging is often treated as an afterthought: "Just add it later if needed." But when exceptions fly, latency spikes, or production bugs appear, logging becomes a lifeline—or a frustration. Here are some of the critical pain points you’ll encounter without proper attention:

1. **Performance Bottlenecks**: Logging can slow down your application—sometimes drastically—if not optimized. A single slow log output can delay a request by 50ms or more in high-traffic systems.
2. **Incomplete Context**: Logs often miss critical context (e.g., request headers, state changes) because engineers assume "it’s obvious." When something breaks, you’re left with cryptic entries like `ERROR: Database connection failed`.
3. **Log Sprawl**: Over-logging creates noise while under-logging leaves blind spots. Balancing verbosity without drowning in noise is an art.
4. **Centralization Failures**: Aggregating logs from microservices often leads to disjointed data due to missing timestamps, inconsistent formatting, or poor correlation IDs.
5. **Security Risks**: Logs can leak sensitive data if not redacted or if your log retention policy exposes old logs to unintended eyes.
6. **Debugging Nightmares**: When logs are unstructured or lack clear causality, debugging distributed systems becomes a guessing game.

### Example of a Flawed Log Setup
Consider a hypothetical payment service:

```python
# Example: Bad logging in a payment service
def process_payment(order_id, amount):
    try:
        payment = Payment.create(amount)
        db.save(payment)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to process payment {order_id}: {e}")
        return {"status": "error"}
```

What’s wrong here? The error log misses:
- The original request headers (e.g., `X-User-ID`).
- The final transaction state (e.g., refunded, declined).
- Whether it’s a duplicate payment attempt.
- The exact timestamp of the failure.

This leads to logs like `ERROR: Failed to process payment 12345: IntegrityError`, which are nearly useless for debugging.

---

## The Solution

The key to robust logging is **intentional design**. Here’s how to approach it systematically:

1. **Adopt a Structured Approach**: Use structured logging (e.g., JSON) to ensure consistency across services.
2. **Include Context**: Correlate logs with request IDs and metadata.
3. **Optimize Performance**: Avoid blocking operations and batch logs.
4. **Secure Sensitive Data**: Redact PII before logging.
5. **Centralize Logs**: Use tools like ELK, Loki, or Datadog for correlation.
6. **Log Strategically**: Focus on errors, state changes, and user flows.

---

## Components/Solutions

### 1. Structured Logging
Unstructured logs (e.g., `INFO: User logged in at 10:00`) are hard to parse and analyze. Structured logging formats logs as JSON, enabling rich querying. Example with Python:

```python
import json
import logging

logging.basicConfig(level=logging.INFO)

def log_structured(message, context={}):
    log_entry = {"timestamp": datetime.now().isoformat(), **context, "level": logging.getLevelName(logging.INFO), "message": message}
    logging.info(json.dumps(log_entry))

log_structured(
    "User logged in",
    {
        "user_id": "12345",
        "request_id": "req-7890",
        "headers": {"X-Forwarded-For": "192.168.1.1"}
    }
)
```

**Output**:
```json
{
  "timestamp": "2024-06-15T14:30:00.000Z",
  "level": "INFO",
  "message": "User logged in",
  "user_id": "12345",
  "request_id": "req-7890",
  "headers": {"X-Forwarded-For": "192.168.1.1"}
}
```

**Why it matters**: Tools like Splunk or Loki can now query logs like `request_id: "req-7890" AND "failed" IN message`.

---

### 2. Context Preservation
Correlate logs with a unique request ID (e.g., UUID) to track a user’s journey across services.

#### Code Example: Request Context
```python
import uuid
from contextvars import ContextVar

# Global context variable to store request ID
request_id_var = ContextVar("request_id")

def get_request_id():
    return request_id_var.get()

def set_request_id(request_id):
    request_id_var.set(request_id)

# Middleware/Wrapper to add context
def log_with_context(func):
    def wrapper(*args, **kwargs):
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        try:
            result = func(*args, **kwargs)
        finally:
            log_structured(
                f"Request completed: {func.__name__}",
                {"request_id": request_id, "duration_ms": 100}
            )
        return result
    return wrapper

@log_with_context
def process_payment(order_id, amount):
    # ... existing code ...
```

**Key Takeaway**: Every log entry includes `request_id`, linking logs across microservices.

---

### 3. Logging Performance Considerations
Avoid blocking the main thread with slow I/O. Batch logs or use async logging:

#### Code Example: Async Logging (Python)
```python
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

# Set up a logging queue
log_queue = Queue(maxsize=1000)
queue_handler = QueueHandler(log_queue)
logging.getLogger().addHandler(queue_handler)

# Worker thread to process logs
def log_worker():
    listener = QueueListener(log_queue, lambda msg: print(f"[LOG]: {msg}"))
    listener.start()

asyncio.create_task(log_worker())

# Async log function
async def alogger(message):
    logging.info(message)
    # Simulate async non-blocking I/O
    await asyncio.sleep(0.01)  # Emulate network delay
```

**Tradeoff**: Async logging adds complexity. For most systems, a QueueHandler + QueueListener is sufficient.

---

### 4. Security: Redacting Sensitive Data
Never log passwords, tokens, or PII directly. Use redaction:

```python
import re

def redact_sensitive_data(log_entry):
    # Redact tokens, passwords, and PII
    for key, value in log_entry.items():
        if "password" in str(key).lower() or "token" in str(key).lower():
            log_entry[key] = "[REDACTED]"
    return log_entry

log_structured("User login", {"user_id": "12345", "password": "mypassword"})
# Output after redaction: {"password": "[REDACTED]"}
```

**Pro Tip**: Use environment variables to define what to redact (e.g., `SENSITIVE_KEYS="password token secret"`).

---

### 5. Log Aggregation and Correlation
Correlate logs from multiple services using a shared request ID and timestamp.

**Example with OpenTelemetry (Python)**:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Set up tracer
provider = TracerProvider()
processor = BatchSpanProcessor(...)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

def process_order(order_id):
    with tracer.start_as_current_span("process_order"):
        # Your business logic
```

**Why it matters**: OpenTelemetry links spans (traces) and logs, enabling full request analysis.

---

## Implementation Guide

### Step 1: Choose a Logging Library
| Language  | Recommended Library       | Why                                  |
|-----------|---------------------------|--------------------------------------|
| Python    | `structlog` + `json`      | Flexible, supports async           |
| Java      | SLF4J + Logback           | Industry standard, structured logs   |
| Go        | `zap`                     | High performance, structured        |
| Node.js   | `winston`                 | Highly configurable                 |
| C#        | `Serilog`                 | Extensible, JSON support            |

---

### Step 2: Add Context to Every Log
Ensure logs include:
- `request_id`: Unique identifier per request.
- `user_id`: If applicable.
- `service_name`: To filter logs per service.
- `timestamp`: ISO format for time-based queries.

---

### Step 3: Optimize Performance
- Use async logging (QueueHandler in Python, `zap` in Go).
- Avoid `console.log` (slows down JavaScript apps).
- Batch logs when possible (e.g., every 100ms).

---

### Step 4: Centralize Logs
- Use a log aggregator (ELK, Loki, Datadog).
- Ensure timestamps are consistent (use UTC).
- Retain logs for 30–90 days (balance cost and compliance).

---

## Common Mistakes to Avoid

### 1. Overlogging Everything
❌ **Mistake**: Logging every method call.
✅ **Solution**: Log only errors, state changes, and critical user actions.

```python
# Bad: Log every method (noise!)
def calculate_discount(user):
    log.info("Calculating discount for user %s", user.id)  # Too much noise
    discount = user.get_discount()
    log.info("Discount calculated: %f", discount)
```

✅ **Better**: Only log errors and results.
```python
try:
    discount = user.get_discount()
except DiscountError as e:
    log.error("Failed to calculate discount: %s", e, exc_info=True)
else:
    log.info("Discount applied: %f", discount)
```

---

### 2. Missing Log Correlation
❌ **Mistake**: Logs from different services appear unrelated.
✅ **Solution**: Use a shared request ID.

```python
# Without correlation
logger.error("Failed to validate credit card")

# With correlation
logger.error("Failed to validate credit card for user %s (req_id %s)",
             user_id, request_id_var.get())
```

---

### 3. Logging Exceptions Without Context
❌ **Mistake**:
```python
try:
    process_payment()
except Exception as e:
    logger.error(e)  # Missing context!
```

✅ **Better**: Include request details.
```python
try:
    process_payment(order_id, amount)
except Exception as e:
    logger.error(
        "Payment failed for order %s: %s",
        order_id,
        exc_info=True,  # Log stack trace
        user_id=user_id,
        request_id=get_request_id()
    )
```

---

### 4. Hardcoding Secrets in Logs
❌ **Mistake**:
```python
logger.info("API key is: %s", api_key)  # Never do this!
```

✅ **Better**: Redact or use environment variables.
```python
logger.info("API key usage detected: %s", api_key[:5] + "****")
```

---

### 5. Ignoring Log Rotation
❌ **Mistake**: Log files grow indefinitely, filling disk space.
✅ **Solution**: Configure rotation (e.g., `logrotate` on Linux).

```python
# Example rotation settings (Python)
log_handler = RotatingFileHandler(
    "app.log",
    maxBytes=10_000_000,  # 10MB
    backupCount=3
)
```

---

## Key Takeaways

Here’s your **checklist** for robust logging:

1. **Structured Logging**: Use JSON to enable querying.
2. **Context First**: Always include `request_id`, `user_id`, and `service_name`.
3. **Performance**: Avoid blocking I/O; use async or batching.
4. **Security**: Redact sensitive data (tokens, passwords, PII).
5. **Correlation**: Link logs across services with shared IDs.
6. **Centralization**: Aggregate logs in ELK/Loki/Datadog.
7. **Minimal Verbosity**: Log only what’s critical for debugging.
8. **Rotation**: Set up log rotation to avoid disk bloat.
9. **Tests**: Validate log output in unit tests.
10. **Monitor Log Errors**: Set up alerts for unhandled exceptions.

---

## Conclusion

Logging is not just about "writing messages"—it’s about **preserving context, ensuring observability, and avoiding debugging nightmares**. The gotchas we’ve covered—performance bottlenecks, missing context, security risks, and log sprawl—are all fixable with intentional design.

> **Pro Tip**: Start with a single structured logging library (e.g., `structlog` in Python) and gradually add context, correlation, and optimizations. Small steps lead to reliable systems.

By adopting these patterns, you’ll build backends that are not only performant but also a pleasure to debug. Next time you hit a production issue, your logs will be your most powerful ally—if you’ve laid the groundwork correctly.

---
**Further Reading**:
- [Structured Logging with Python’s `structlog`](https://www.structlog.org/)
- [OpenTelemetry for Distributed Tracing](https://opentelemetry.io/)
- [ELK Stack Guide](https://www.elastic.co/guide/en/elk-stack/index.html)

**Questions?** Share your logging pain points in the comments—I’d love to hear from you!
```

---
**Format Notes**:
- **Code blocks**: Used consistent syntax highlighting with triple backticks.
- **Tradeoffs**: Explicitly called out (e.g., async logging complexity).
- **Real-world examples**: Payment service, user login, etc.
- **Tone**: Professional but conversational (e.g., "Pro Tip").
- **Length**: ~1,800 words with room for expansion (e.g., deeper dives into SLF4J or Loki).