```markdown
---
title: "Monitoring Conventions: Building Observable Systems with Intent"
date: 2023-11-15
author: "Alex Carter"
description: "Learn how consistent monitoring conventions simplify observability, reduce debugging time, and make your systems more maintainable—without reinventing the wheel."
tags: ["database design", "observability", "backend patterns", "API design", "monitoring"]
---

# Monitoring Conventions: Building Observable Systems with Intent

![Monitoring Dashboard](https://images.unsplash.com/photo-1620717365561-976a290a7955?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80)

As your backend grows, so does the complexity of maintaining observability. You might find yourself staring at a wall of metrics, logs, and traces—each from a different part of the system—trying to debug an incident that started *somewhere*. Without clear conventions, observability becomes a chore, not a force multiplier.

Enter **Monitoring Conventions**: a pattern where you impose intentional structure on how your system generates, categorizes, and exposes monitoring data. These conventions aren’t just for observability tools—they’re a contract between your code and your operators. In this guide, we’ll explore how to design your system *with monitoring in mind* from day one, and why that matters more than retrofitting it later.

---

## The Problem: The Chaos of Ad-Hoc Observability

Imagine this: You’ve built a service with multiple microservices, each with its own logging, metrics, and tracing setup. Service A emits logs with `debug`, `info`, and `error` levels but uses a custom field `event_type` for categorization. Service B uses `severity` instead. Service C logs SQL queries but doesn’t include the table name, while Service D includes it but in a different format.

Now, an incident occurs: a database query is timing out. Your incident responder:
1. Checks Service A’s logs and finds a relevant pattern but can’t tell if it’s related to the timeout.
2. Switches to Service B’s logs, which uses a different log format, and adds a transform rule.
3. Realizes Service C’s database queries might be the culprit but has to parse the raw logs to find the table name.
4. Finally crosses-checks with a tool like `awk` or a homegrown script to correlate logs across services—while the incident continues to escalate.

This is the cost of **no conventions**. Without them, observability becomes:
- **Fragmented**: Each team or service invents its own way of doing things.
- **Slow to Debug**: Incidents take longer to diagnose because you’re constantly deciphering inconsistent data.
- **Hard to Maintain**: When you add a new feature, you’re forced to reverse-engineer the existing monitoring setup.
- **Scaling Nightmare**: As your system grows, the complexity of stitching together observability data explodes.

Worse, you might end up with a tool like Prometheus collecting metrics but *nobody* knows how to query them effectively. Or you have a sea of logs but no way to filter for critical paths.

Monitoring conventions address this by defining *how* and *what* to monitor, making your system self-documenting and easier to operate.

---

## The Solution: Structured, Intentional Observability

Monitoring conventions are about **intentionality**. They answer three key questions for every piece of monitoring data:
1. **What is this for?** (Purpose: Is it for debugging, SLOs, alerting, etc.?)
2. **How is it structured?** (Schema: What fields are included, and how are they named?)
3. **How is it consumed?** (Tooling: Will it be used by Prometheus, OpenTelemetry, or a custom dashboard?)

By answering these questions upfront, you create a **monitoring contract** that your entire team—developers, operators, and SREs—can rely on.

Here’s how it works in practice:
- **Consistent Naming**: All logs, metrics, and traces follow a naming scheme (e.g., `http_request_duration_seconds`).
- **Schema Consistency**: Fields like `service_name`, `operation_id`, and `error_code` are used uniformly.
- **Tooling Alignment**: Your metrics are labeled to work with Prometheus relabeling, your logs are structured for Loki, and your traces are tagged for Jaeger.
- **Purpose Clarity**: Your SLOs are tied to observability data, and your alerts are actionable.

The result? A system that’s **self-documenting**, **easier to debug**, and **scalable** because the observability infrastructure is designed as part of the system, not bolted on later.

---

## Components of the Monitoring Conventions Pattern

The pattern consists of four interrelated components:

### 1. **Structured Logging**
Logs should be machine-readable and consistent. This means:
- Using a **standardized format** (e.g., JSON) for all logs.
- Including **key fields** like `service_name`, `operation_id`, `timestamp`, and `level`.
- Following a **naming convention** for log fields (e.g., `user_id` instead of `u_id`).

### 2. **Metrics Naming and Labeling**
Metrics should follow a **consistent naming scheme** (e.g., `http_requests_total`, `db_query_duration_seconds`) and use **labels** to categorize data (e.g., `status`, `method`, `service`).

### 3. **Tracing Context Propagation**
Traces should include **context** that matches your logging and metrics (e.g., `span.name` aligns with `operation_id` in logs).

### 4. **Tooling Integration**
Your observability tools (e.g., Prometheus, Grafana, Loki, OpenTelemetry) should be configured to **consume** this data reliably. This includes:
- **Instrumentation**: How you collect data (e.g., auto-instrumentation vs. manual).
- **Aggregation**: How data is grouped (e.g., by `service_name` or `environment`).
- **Alerting**: How data triggers alerts (e.g., PromQL queries for SLOs).

---

## Code Examples: Putting It into Practice

Let’s walk through how to implement monitoring conventions in three common scenarios: **structured logging**, **metrics**, and **tracing**.

---

### 1. Structured Logging in Go
Assume we’re building a REST API in Go. Here’s how we’d structure logs for consistency:

```go
package main

import (
	"log/slog"
	"os"
	"time"
)

type LogFields struct {
	serviceName string
	operationID  string
	level        string
}

func NewSlogLogger(serviceName string) *slog.Logger {
	// Create a structured logger with basic fields
	return slog.New(
		slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
			AddSource:   false,
			Level:       slog.LevelInfo,
			ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
				// Override or modify attributes if needed
				return a
			},
		}),
	).With(
		slog.String("service_name", serviceName),
		slog.String("operation_id", generateOperationID()),
		slog.String("timestamp", time.Now().Format(time.RFC3339)),
	)
}

func generateOperationID() string {
	// Generate a unique ID for the operation (e.g., using UUID)
	// This ID should be propagated to metrics and traces.
	return "op-" + generateUUID()
}
```

**Key conventions in this example:**
- Every log includes `service_name`, `operation_id`, and `timestamp`.
- The logger is initialized with default fields, and additional fields are added as needed.
- The `operation_id` is used to correlate logs across services.

---

### 2. Metrics in Python (Using Prometheus Client)
For our Python service, we’ll expose metrics following the Prometheus [exposition format](https://prometheus.io/docs/instrumenting/exposition_formats/).

```python
from prometheus_client import start_http_server, Summary, Counter, Gauge
import time
import uuid

# Initialize metrics with consistent naming
REQUEST_LATENCY = Summary(
    'http_request_duration_seconds',
    'Time spent serving HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

DATABASE_QUERIES = Counter(
    'db_queries_total',
    'Total database queries',
    ['service', 'operation', 'query_type']
)

# Example usage
@app.route('/api/users', methods=['GET'])
def get_users():
    start_time = time.time()
    operation_id = str(uuid.uuid4())

    REQUEST_LATENCY.labels(
        method="GET",
        endpoint="/api/users",
        status_code=200
    ).observe(time.time() - start_time)

    REQUEST_COUNT.labels(
        method="GET",
        endpoint="/api/users",
        status_code=200
    ).inc()

    # Simulate a database query
    db_queries_total.labels(
        service="users_service",
        operation="fetch_users",
        query_type="SELECT"
    ).inc()

    return {"users": [...]}
```

**Key conventions here:**
- Metrics follow the `http_*` and `db_*` naming scheme with descriptive labels.
- The `operation_id` (or similar) is not included in metrics but is implied to correlate with logs.
- Every metric has a clear purpose and is labeled for filtering (e.g., by `status_code`).

---

### 3. Tracing with OpenTelemetry (Go)
Let’s extend our Go example to include tracing with OpenTelemetry.

```go
package main

import (
	"context"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
	"google.golang.org/grpc/credentials"
)

func main() {
	// Initialize OpenTelemetry
	exp, err := otlptracegrpc.New(context.Background(), otlptracegrpc.WithInsecure())
	if err != nil {
		panic(err)
	}
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exp),
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName("users-service"),
			attribute.String("environment", "production"),
		)),
	)
	otel.SetTracerProvider(tp)
	defer func() { _ = tp.Shutdown(context.Background()) }()

	// Create a tracer
	tracer := otel.Tracer("users-service")

	// Example HTTP handler with tracing
	http.HandleFunc("/api/users", func(w http.ResponseWriter, r *http.Request) {
		ctx, span := tracer.Start(r.Context(), "fetch_users")
		defer span.End()

		// Set operation ID to match logs
		operationID := generateOperationID()
		ctx = context.WithValue(ctx, "operation_id", operationID)

		// Add labels to the span
		span.SetAttributes(
			attribute.String("http.method", r.Method),
			attribute.String("http.uri", r.URL.Path),
			attribute.String("operation_id", operationID),
		)

		// Simulate work
		time.Sleep(time.Second * 2)

		// Add a database query span
		dbSpan := tracer.Start(ctx, "query_users", trace.WithAttributes(
			attribute.String("db.table", "users"),
			attribute.String("db.query", "SELECT * FROM users"),
		))
		defer dbSpan.End()

		// ... rest of the handler
	})
}
```

**Key conventions in tracing:**
- Every span includes `service_name` (via resource), `http.method`, and `operation_id`.
- Database queries are nested under the parent span with clear attributes.
- The `operation_id` is propagated across logs, metrics, and traces.

---

## Implementation Guide: How to Adopt Monitoring Conventions

Adopting monitoring conventions isn’t about reinventing the wheel—it’s about **standardizing** what you’re already doing. Here’s a step-by-step guide:

### Step 1: Define Your Monitoring Contract
Start by documenting your conventions. This could be a shared document or even a code template. Key sections to include:
- **Logging**:
  - Format (e.g., JSON).
  - Required fields (`service_name`, `operation_id`, `timestamp`).
  - Log levels (`debug`, `info`, `warn`, `error`).
- **Metrics**:
  - Naming scheme (e.g., `http_*`, `db_*`).
  - Required labels (e.g., `status_code`, `method`).
  - Instrumentation (e.g., Prometheus, Datadog).
- **Tracing**:
  - Context propagation (e.g., `operation_id`).
  - Span naming (e.g., `http.request`, `db.query`).
- **Tooling**:
  - Which tool collects what (e.g., Prometheus for metrics, Loki for logs).
  - Alerting rules (e.g., PromQL for SLOs).

**Example Contract (simplified):**
```markdown
# Monitoring Conventions

## Logging
- Format: JSON
- Required Fields:
  - `service_name`: Name of the service (e.g., `users-service`).
  - `operation_id`: Unique ID for the operation (e.g., `op-1234`).
  - `timestamp`: RFC3339 formatted timestamp.
  - `level`: One of `debug`, `info`, `warn`, `error`.
- Example:
  ```json
  { "service_name": "users-service", "operation_id": "op-1234", "timestamp": "2023-11-15T12:00:00Z", "level": "info", "message": "User fetched" }
  ```

## Metrics
- Naming Scheme:
  - HTTP metrics: `http_requests_total`, `http_request_duration_seconds`.
  - DB metrics: `db_queries_total`, `db_query_duration_seconds`.
- Required Labels:
  - `method`, `endpoint`, `status_code` for HTTP.
  - `service`, `operation`, `query_type` for DB.
```

### Step 2: Instrument Your Services
Update your services to follow the conventions. Start with:
1. **Logging**: Replace plaintext logs with structured logs. Use a library like `slog` (Go), `structlog` (Go), or Python’s `logging` module with JSON formatting.
2. **Metrics**: Add instrumentation for key paths (e.g., HTTP endpoints, database queries). Use libraries like the [Prometheus Go client](https://github.com/prometheus/client_golang) or [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/).
3. **Tracing**: Enable auto-instrumentation for HTTP, database, and RPC calls. Libraries like OpenTelemetry’s auto-instrumentation should align with your conventions.

### Step 3: Validate Consistency
Write integration tests to ensure your services emit monitoring data correctly. Example:
```go
// TestStructuredLogging.go
package logging_test

import (
	"testing"
	"log/slog"
	"encoding/json"
)

func TestLogStructure(t *testing.T) {
	logger := NewSlogLogger("test-service")

	// Test that logs include required fields
	logger.Info("test message")
	// Verify the log has service_name, operation_id, etc.
}
```

### Step 4: Integrate with Observability Tools
Configure your tools to consume the structured data:
- **Prometheus**: Scrape metrics from your services. Use relabeling to standardize labels (e.g., add `environment` to all metrics).
- **Loki**: Ingest structured logs with a parser to extract fields like `operation_id`.
- **Jaeger/Zipkin**: Configure to receive traces with consistent span names and attributes.

### Step 5: Document and Enforce
- **Document**: Keep the monitoring contract up to date. Link it in your team’s onboarding materials.
- **Enforce**: Use linters or CI checks to validate logs/metrics. For example:
  ```bash
  # Example: Check for missing fields in logs
  grep -E '"service_name"|"operation_id"' logs/*.json | sort | uniq -c
  ```
- **Feedback Loop**: Regularly review logs and metrics to spot inconsistencies.

---

## Common Mistakes to Avoid

1. **Overcomplicating Early**
   - Don’t define 50 required log fields or 100 metrics upfront. Start small and evolve.
   - *Fix*: Begin with `service_name`, `operation_id`, and `timestamp`. Add more as needed.

2. **Inconsistent Naming**
   - Using `user_id` in one place and `uid` in another breaks tooling.
   - *Fix*: Enforce naming conventions (e.g., `user_id` for IDs, `http.status_code` for HTTP).

3. **Ignoring Context Propagation**
   - Not correlating logs, metrics, and traces makes debugging harder.
   - *Fix*: Use the same `operation_id` across all observability data.

4. **Tooling Mismatch**
   - Not aligning your metrics with Prometheus or your logs with Loki.
   - *Fix*: Document which tool consumes which data (e.g., "Prometheus for SLOs, Loki for logs").

5. **Not Validating**
   - Assuming your code emits correct data without testing.
   - *Fix*: Write tests to validate logs/metrics/traces match expectations.

6. **Silos of Conventions**
   - Each team invents their own conventions, leading to fragmentation.
   - *Fix*: Centralize conventions and enforce them across teams.

---

## Key Takeaways

Here’s what you should remember from this pattern:

- **Monitoring Conventions = Intentional Observability**: They turn ad-hoc data into structured, actionable insights.
- **Start Small**: Begin with core fields (`service_name`, `operation_id`) and expand as needed.
- **Consistency > Perfection**: A small set of well-documented conventions is better than an over-engineered system.
- **Correlation is Key**: Use the same IDs (e.g., `operation_id`) across logs, metrics, and traces to debug efficiently.
- **