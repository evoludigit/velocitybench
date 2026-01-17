```markdown
# Crash Reporting Patterns: Building Resilient Systems That Learn from Failure

*How to design crash reporting systems that capture, analyze, and act on errors—without breaking your application*

---

## Introduction

Every backend engineer has faced it: a critical production error that crashes your service, drops user requests, or—worse—goes silently unnoticed until users complain via support tickets. When systems fail, you need *crash reporting* to understand *why* and *how often* it happens. Crash reporting isn’t just about logging errors—it’s about designing a system that collects context, prioritizes severity, and enables quick recovery.

But crash reporting systems can be messy. If you just dump raw logs into a database, you’ll quickly drown in noise. If you rely on centralized logging without context, you’ll waste time debugging. And if you ignore performance tradeoffs, you might slow down your app during outages.

This guide covers **crash reporting patterns**—practical strategies to build systems that reliably capture failures, minimize false positives, and enable proactive fixes. We’ll discuss:
- How to structure crash data for efficiency
- When to collect rich context vs. minimal payloads
- Tradeoffs between centralized vs. distributed reporting
- How to avoid common anti-patterns

By the end, you’ll have actionable patterns to implement in your own systems, with code examples in Go, Python, and JavaScript.

---

## The Problem

Crash reporting is tricky because it combines two conflicting goals:
1. **Comprehensiveness** – Capture everything to prevent future failures.
2. **Performance** – Don’t overload your system during high load or crashes.

### Common Challenges

#### 1. **"Too Much Data" Syndrome**
   - Logs like `panic!` or `500 errors` flood your system, drowning out critical failures.
   - Example: A production API returns `200 OK` for all errors (silent failure), but you don’t know why.

#### 2. **Context Collapse**
   - When an error occurs, you often lose the surrounding context—user ID, request headers, or business state.
   - Example: A payment failure crashes without knowing if it was a test transaction or a $10,000 order.

#### 3. **Duplicate Errors**
   - The same crash occurs across servers, but you can’t correlate them.
   - Example: 10 different instances of `NullPointerException` in your Microservice A, but you don’t know they’re all caused by the same root cause.

#### 4. **False Positives & Noise**
   - Non-critical errors (e.g., connection retries, test failures) clog your system.
   - Example: A "429 Too Many Requests" error is logged but ignored, because it’s not a "real" crash.

#### 5. **Proactive vs. Reactive Tradeoff**
   - If you catch all errors upfront, you may slow down your app during peak traffic.
   - If you only log crashes retroactively, you miss out on immediate feedback.

---

## The Solution: Crash Reporting Patterns

The key is to **design systems that prioritize, filter, and enrich crash data** while keeping overhead low. Here’s the high-level approach:

1. **Categorize crashes** – Not all errors are equal. Distinguish between hard crashes (`500`) and soft errors (`429`).
2. **Context-aware sampling** – Collect rich data for critical failures but keep payloads small for common errors.
3. **Centralized aggregation with deduplication** – Avoid duplicate entries for the same crash across instances.
4. **Actionable insights first** – Surface crashes with high impact (high frequency, severe impact) first.
5. **Minimize latency** – Ensure crash reporting doesn’t delay your app’s response time.

---

## Crash Reporting Architecture

Let’s design a system with these components:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        Your Application                                       │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────────────┐
│                                 Crash Handler                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌───────────────────────────┐  │
│  │  Filtering      │    │  Context        │    │  Deduplication            │  │
│  │  (Severity)     │───▶│  Enrichment     │───▶│  (Grouping Identical      │  │
│  └───────────┬─────┘    └───────────┬─────┘    │   Crashes)               │  │
│               │                     │               └───────────────────┘  │
│               │                     │                                   │
│  ┌───────────▼───────────┐           │                                   │
│  │  Local Buffer        │───────────▶│                                   │
│  │  (Low Latency)       │           │                                   │
│  └──────────────────────┘           │                                   │
│                                   ▼                                   │
└───────────────────────────────────┬───────────────────────────────────────┘
                                   │
┌───────────────────────────────────▼───────────────────────────────────────┐
│                                 Crash Store                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  Time-Series    │    │  Search Index  │    │  Alerting Rules        │  │
│  │  (PostgreSQL)   │    │  (Elasticsearch)│    │  (Slack/PagerDuty)     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Crash Filtering**
   - Not all errors are crashes. Distinguish between:
     - **Critical crashes** (e.g., `panic!`, unhandled exceptions)
     - **Soft errors** (e.g., `429`, `404`)
     - **Informational errors** (e.g., debug logs)
   - **Rule:** Only report crashes that indicate a bug or system failure.

#### 2. **Context Enrichment**
   - Attach context to crashes to make debugging easier:
     - Request headers (user agent, IP)
     - Business context (cart ID, order amount)
     - Stack traces (if available)
   - **Tradeoff:** Rich context increases payload size. Use sampling for performance.

#### 3. **Deduplication**
   - If the same crash happens 100 times, only report it once.
   - **Example:** A `NullPointerException` in a background task should only be reported once per task instance (not per request).

#### 4. **Local Buffering**
   - During high load, buffer crashes locally and send them asynchronously.
   - **Example:** Use a queue (Redis, Kafka) to avoid blocking the main thread.

#### 5. **Centralized Store**
   - Store crashes in a searchable database (PostgreSQL for time-series data, Elasticsearch for full-text search).
   - **Schema Example:**
     ```sql
     CREATE TABLE crashes (
       id UUID PRIMARY KEY,
       timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
       severity VARCHAR(20) NOT NULL, -- "critical", "warning", "info"
       traceback TEXT,
       context JSONB, -- Request headers, user data, etc.
       error_type VARCHAR(100), -- e.g., "NullPointerException"
       application VARCHAR(100), -- Service name
       environment VARCHAR(20), -- "prod", "staging"
       is_duplicate BOOLEAN DEFAULT FALSE,
       deduplication_key VARCHAR(255) -- For grouping identical crashes
     );

     CREATE INDEX idx_crashes_severity ON crashes(severity);
     CREATE INDEX idx_crashes_timestamp ON crashes(timestamp);
     CREATE INDEX idx_crashes_error_type ON crashes(error_type);
     ```

#### 6. **Alerting**
   - Alert on crashes that:
     - Are new (`error_type` not seen before).
     - Occur frequently (e.g., >10 crashes/minute).
     - Have high severity (`critical`).

---

## Code Examples

### 1. Crash Handler (Go)
Here’s how to implement a crash handler in Go with filtering, context enrichment, and buffering:

```go
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"runtime/debug"
	"time"

	"github.com/google/uuid"
	"gopkg.in/pg.v5"
)

type CrashReport struct {
	ID          uuid.UUID  `json:"id"`
	Timestamp   time.Time  `json:"timestamp"`
	Severity    string     `json:"severity"` // "critical", "warning", "info"
	Traceback   string     `json:"traceback"`
	Context     json.RawMessage `json:"context"` // Request headers, user data, etc.
	ErrorType   string     `json:"error_type"`
	Application string     `json:"application"`
	Environment string     `json:"environment"`
	IsDuplicate bool       `json:"is_duplicate"`
	DeduplicationKey string   `json:"deduplication_key"`
}

var crashBuffer = make(chan CrashReport, 1000) // Local buffer

func initCrashHandler() {
	go func() {
		for report := range crashBuffer {
			// Send to database
			_, err := db.Exec(`
				INSERT INTO crashes
				(id, timestamp, severity, traceback, context, error_type, application, environment)
				VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
			`, report.ID, report.Timestamp, report.Severity, report.Traceback,
				report.Context, report.ErrorType, report.Application, report.Environment)
			if err != nil {
				log.Printf("Failed to save crash: %v", err)
			}
		}
	}()
}

func handleCrash(err error, ctx context.Context) {
	// Filter: Only report "critical" errors
	if !isCriticalError(err) {
		return
	}

	// Extract traceback
	traceback := debug.Stack()

	// Enrich context (e.g., user ID, request ID)
	var ctxData map[string]interface{}
	if v, ok := ctx.Value("userID").(string); ok {
		ctxData["userID"] = v
	}
	if v, ok := ctx.Value("requestID").(string); ok {
		ctxData["requestID"] = v
	}

	// Create crash report
	report := CrashReport{
		ID:          uuid.New(),
		Timestamp:   time.Now(),
		Severity:    "critical",
		Traceback:   string(traceback),
		Context:     json.RawMessage(ctxData),
		ErrorType:   fmt.Sprintf("Error: %v", err),
		Application: "user-service",
		Environment: "prod",
	}

	// Add to buffer
	crashBuffer <- report
}

func isCriticalError(err error) bool {
	// Example: Only panic! and unhandled exceptions are "critical"
	return errors.Is(err, context.DeadlineExceeded) || // Timeout (critical)
		errors.Is(err, http.ErrServerClosed) ||        // Server shutdown (critical)
		strings.HasPrefix(err.Error(), "panic:")       // Panic (critical)
}
```

### 2. Crash Sampling (Python)
For Python, we’ll use a sampling strategy to avoid overwhelming the system with low-severity errors:

```python
import json
import random
import time
from datetime import datetime
from typing import Dict, Any

class CrashReporter:
    def __init__(self, max_samples_per_minute: int = 100):
        self.max_samples = max_samples_per_minute
        self.last_sample_time = time.time()

    def report(self, error: Exception, context: Dict[str, Any]) -> bool:
        # Filter: Only report errors with high impact
        if not self._is_severe_error(error):
            return False

        # Sample to avoid flooding
        now = time.time()
        if now - self.last_sample_time > 60:  # Reset every minute
            self.last_sample_time = now
        else:
            if random.random() > 1 - (self.max_samples / 100):  # 1% sampling rate
                return False

        # Enrich context
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "critical",
            "traceback": self._get_traceback(error),
            "context": context,
            "error_type": str(error),
            "application": "payment-service",
            "environment": "prod"
        }

        # Send to buffer/DB (simplified)
        self._send_to_db(report)
        return True

    def _is_severe_error(self, error: Exception) -> bool:
        # Example: Only report timeouts and crashes
        return isinstance(error, TimeoutError) or "panic" in str(error).lower()

    def _get_traceback(self, error: Exception) -> str:
        import traceback
        return "".join(traceback.format_exception(type(error), error, error.__traceback__))

    def _send_to_db(self, report: Dict[str, Any]):
        # In a real app, this would send to PostgreSQL, Kafka, etc.
        print("Reporting crash:", json.dumps(report))
```

### 3. Crash Deduplication (JavaScript)
For Node.js, we’ll implement deduplication using a sliding window:

```javascript
const { v4: uuidv4 } = require('uuid');
const { Redis } = require('ioredis');

class CrashHandler {
  constructor() {
    this.redis = new Redis(process.env.REDIS_URL);
    this.dedupeWindowMinutes = 60; // Dedupe crashes in the last 60 mins
  }

  async handleCrash(error, context) {
    // Filter: Only critical errors
    if (!this._isCriticalError(error)) return;

    // Generate a deduplication key (e.g., error type + context hash)
    const dedupeKey = this._generateDedupeKey(error, context);

    // Check if we've already seen this crash in the window
    const now = Date.now();
    const startTime = now - (this.dedupeWindowMinutes * 60 * 1000);
    const crashes = await this.redis.zrangebyscore(
      `crash:${dedupeKey}`,
      startTime,
      now
    );

    if (crashes.length > 0) {
      console.log('Duplicate crash skipped');
      return;
    }

    // Enrich context
    const report = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      severity: 'critical',
      traceback: this._getTraceback(error),
      context,
      errorType: error.name,
      application: 'api-gateway',
      environment: 'prod',
      deduplicationKey: dedupeKey,
    };

    // Store in Redis with TTL
    await this.redis.zadd(
      `crash:${dedupeKey}`,
      report.timestamp,
      report.id
    );
    await this.redis.expire(`crash:${dedupeKey}`, this.dedupeWindowMinutes * 60);

    // Send to DB/alerting
    await this._sendToDB(report);
  }

  _isCriticalError(error) {
    // Example: Only report unhandled exceptions and timeouts
    return error.name === 'Error' && !error.message.includes('timeout');
  }

  _generateDedupeKey(error, context) {
    return `${error.name}:${JSON.stringify(context)}`;
  }

  _getTraceback(error) {
    return error.stack;
  }

  async _sendToDB(report) {
    // Simulate sending to PostgreSQL/Elasticsearch
    console.log('Reporting crash:', JSON.stringify(report));
  }
}

// Usage
const handler = new CrashHandler();
process.on('uncaughtException', (error) => handler.handleCrash(error, {}));

// Or for async errors (e.g., Promises)
process.on('unhandledRejection', (reason, promise) => {
  handler.handleCrash(reason, {});
});
```

---

## Implementation Guide

### Step 1: Define Crash Severity Levels
Classify errors into tiers to prioritize reporting:
| Severity   | Example Errors                          | Should We Report? |
|------------|-----------------------------------------|-------------------|
| Critical   | Panics, OOM errors, server shutdowns    | ✅ Yes            |
| Warning    | Timeouts, retries                      | ⚠️ Conditional    |
| Info       | Debug logs, connection retries         | ❌ No             |

### Step 2: Implement Local Buffering
- Use a channel (Go), queue (Python), or Redis (Node.js) to avoid blocking your app.
- Buffer size should be large enough to handle spikes but small enough to avoid memory issues.

### Step 3: Enrich Crashes with Context
- **Must-have:** Timestamp, error type, application name.
- **Nice-to-have:** User ID, request headers, business context (e.g., order ID).
- **Avoid:** Sensitive data (PII).

### Step 4: Deduplicate Crashes
- Use a sliding window (e.g., last 60 minutes) to group identical crashes.
- Example: If `NullPointerException` occurs 1000 times in 5 minutes, only report it once.

### Step 5: Store Crashes Efficiently
- **Time-series DB (PostgreSQL):** Good for aggregations (e.g., "How many crashes per hour?").
- **Search Index (Elasticsearch):** Good for full-text search (e.g., "Find all crashes with `StackOverflowError`").

### Step 6: Alert on Critical Crashes
- Set up alerts for:
  - New crashes (`error_type` not seen before).
  - Frequent crashes (>10/minute).
  - High-severity crashes (`critical`).
-