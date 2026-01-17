```markdown
---
title: "Debugging Like a Pro: Mastering Observability with Metrics, Logs, and Traces"
subtitle: "How to turn chaos into clarity in your backend systems"
date: "2024-03-15"
author: "Alex Carter"
---

# Debugging Like a Pro: Mastering Observability with Metrics, Logs, and Traces

![Observability illustration](https://miro.medium.com/max/1400/1*9ZQs5XrRrSZvJ9ZXZk5Q3g.png)

*Have you ever had a production outage where you stared at a blank dashboard, panicked when logs showed only "500 errors", and had no idea where to start? Observability gives you the tools to turn chaos into clarity.*

In today's complex microservices architectures—where requests bounce between dozens of services—you need more than one tool. You need the full observability stack: **Metrics** (performance numbers), **Logs** (detailed events), and **Traces** (request flows). Together, they act like a flight recorder for your system, helping you proactively monitor, diagnose, and recover from issues.

This guide will walk you through the practical implementation of observability using real-world examples. Whether you're debugging a slow API response or root-causing a cascading failure, you’ll learn how to instrument your code to get answers—**before your users notice the problem**.

---

## The Problem: Why Your Current Approach is Broken

Imagine this scenario:

- **Metrics-only**: You see a 99.9% success rate, but users report payment failures. Your dashboard says "everything's fine."
- **Logs-only**: A flood of error logs hits your server, but you can’t correlate them with user requests.
- **Traces-only**: You can see a slow response, but you don’t know if it’s your service or someone else’s.

Isolation is the enemy of observability. Without all three pillars working together:

- You can’t **proactively** detect anomalies before users are affected.
- You can’t **quickly** locate where a request is failing.
- You can’t **reproduce** issues that happen intermittently.
- You end up playing "whack-a-mole" with alerts that don’t help you fix the root cause.

---

## The Solution: Metrics, Logs, and Traces Together

Think of observability like a **crime scene investigation**:

1. **Metrics** = Surveillance cameras (when did it happen?)
   - Provide high-level system health (CPU, latency, error rates).
   - Example: "Your API response time spiked from 200ms to 2s at 3:15 PM."

2. **Logs** = Witness testimony (what happened?)
   - Detail what went wrong (specific failures, SQL queries).
   - Example: "User ID 12345 failed to execute this query: `SELECT * FROM orders WHERE user_id = ?`."

3. **Traces** = Video replay (where did the suspect go?)
   - Show the full path of a request across services.
   - Example: "Payment service called `validate_card`, then `charge_card`—but the latter failed."

**Together**, they paint a complete picture, turning blind spots into actionable insights.

---

## Implementation Guide: Adding Observability to Your Code

Let’s implement observability in a **Node.js/Express API** that interacts with a **PostgreSQL database**. We’ll use:

- **Metrics**: Prometheus client to track response times.
- **Logs**: Winston for structured logging.
- **Traces**: OpenTelemetry and Jaeger for distributed tracing.

---

### 1. Setting Up Metrics with Prometheus

Prometheus scrapes metrics from your app. We’ll track:

- HTTP request durations
- Error rates
- Database query performance

#### Example: Instrumenting Express APIs

```javascript
// app.js
const express = require('express');
const { CollectDefaultMetrics, Registry, Histogram } = require('prom-client');

const app = express();
const registry = new Registry();
CollectDefaultMetrics({ register: registry });

// Track request durations
const responseTimeHistogram = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5], // Adjust buckets as needed
});

// Middleware to capture metrics
app.use((req, res, next) => {
  const start = process.hrtime.bigint();
  res.once('finish', () => {
    const duration = Number(process.hrtime.bigint() - start) / 1e9; // Convert to seconds
    responseTimeHistogram
      .labels(req.method, req.path, res.statusCode)
      .observe(duration);
  });
  next();
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});

// Sample route
app.get('/api/users/:id', async (req, res) => {
  try {
    // Simulate DB call
    const user = await getUserFromDB(req.params.id);
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

#### Key Takeaways:
- **Prometheus** scrapes `/metrics` every minute by default.
- Histograms help you **bucket response times** (e.g., "90% of requests take <1s").
- Always **label metrics** by route, status, and method for meaningful analysis.

---

### 2. Structured Logging with Winston

Logs should be **structured** (JSON format) for easy parsing and correlation. Example:

```javascript
// logger.js
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
  ],
});

// Example usage in a route
app.get('/api/users/:id', async (req, res) => {
  logger.info('Fetching user', { userId: req.params.id, method: req.method });

  try {
    const user = await getUserFromDB(req.params.id);
    res.json(user);
    logger.info('User fetched successfully', { userId: req.params.id });
  } catch (err) {
    logger.error('Failed to fetch user', {
      userId: req.params.id,
      error: err.message,
      stack: err.stack,
    });
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});
```

#### Key Takeaways:
- **Structured logs** (e.g., `{ timestamp, level, message, metadata }`) are easier to query than plain text.
- Include **request IDs** (see Traces section) to correlate logs across services.
- **Log levels matter**: Only log `error` for errors, `info` for business events, and avoid `debug` in production.

---

### 3. Distributed Traces with OpenTelemetry and Jaeger

Traces help you **see the full journey** of a request across services. Without them, you’re guessing where bottlenecks happen.

#### Setup:
1. Install OpenTelemetry:
   ```bash
   npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/exporter-jaeger
   ```

2. Instrument your app:

```javascript
// telemetry.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { PgInstrumentation } = require('@opentelemetry/instrumentation-pg');
const { DiagConsoleLogger, DiagLevel } = require('@opentelemetry/api');

// Configure OpenTelemetry
const provider = new NodeTracerProvider();
const exporter = new JaegerExporter({
  serviceName: 'user-service',
  agentHost: 'jaeger-collector', // Docker hostname if running in containers
  agentPort: 6831,
});
provider.addSpanProcessor(new exporter);
provider.register();

registerInstrumentations({
  instrumentations: [
    new ExpressInstrumentation(),
    new PgInstrumentation(), // For PostgreSQL queries
  ],
});

// Log traces to console (for debugging)
DiagConsoleLogger.install({ logLevel: DiagLevel.DEBUG });
```

#### Example: Adding Traces to a Route

OpenTelemetry automatically **scopes spans** to requests. Here’s how it looks under the hood:

```javascript
// Inside your route (automatically traced)
app.get('/api/users/:id', async (req, res) => {
  const traceId = req.headers['x-trace-id']; // For manual context passing
  logger.info('User request started', { traceId, userId: req.params.id });

  try {
    const user = await getUserFromDB(req.params.id);
    res.json(user);
  } catch (err) {
    logger.error('User fetch failed', { traceId, userId: req.params.id, error: err });
    res.status(500).json({ error: 'Failed' });
  }
});
```

#### How Traces Help:
- **Identify slow dependencies**: "The DB query took 800ms, but my API only took 50ms."
- **Find missing spans**: "Why isn’t my `payment-service` appearing in traces?"
- **Correlate logs**: "This `error` log matches trace ID `1234-5678`."

---

### 4. Connecting the Dots: Correlating Logs and Traces

To link logs with traces, add a **unique request ID** to both:

```javascript
// Middleware to add trace ID to logs
app.use((req, res, next) => {
  const traceId = req.headers['x-trace-id'] || req.id; // OpenTelemetry adds `req.id`
  req.traceId = traceId;
  logger.info('Incoming request', { traceId, path: req.path });
  next();
});

// In your route (example with Winston)
logger.info('User fetched', {
  traceId: req.traceId,
  userId: req.params.id,
  duration: '200ms',
});
```

Now, in your logs, you’ll see:
```json
{
  "timestamp": "2024-03-15T10:00:00Z",
  "level": "info",
  "message": "User fetched",
  "traceId": "1234-5678",
  "userId": "42",
  "duration": "200ms"
}
```

And in Jaeger, you’ll see:
![Jaeger trace example](https://miro.medium.com/max/1200/1*XyZQs5XrRrSZvJ9ZXZk5Q3g.png)

---

## Common Mistakes to Avoid

1. **Not Instrumenting Critical Paths**
   - *Mistake*: Only logging errors in `/api/health`.
   - *Solution*: Instrument **all** user-facing routes and DB calls.

2. **Ignoring Sampling**
   - *Mistake*: Sending every trace to Jaeger, overwhelming your collector.
   - *Solution*: Use **probabilistic sampling** (e.g., 1% of requests):
     ```javascript
     exporter = new JaegerExporter({ samplingProbability: 0.01 });
     ```

3. **Logging Raw Sensitive Data**
   - *Mistake*: Logging passwords or PII (Personally Identifiable Information).
   - *Solution*: Use a logger like Winston with redactions:
     ```javascript
     logger.info('User data', { user: { name: 'Alice', email: '[REDACTED]' } });
     ```

4. **Overloading Metrics**
   - *Mistake*: Adding 100 custom gauges to track "everything."
   - *Solution*: Focus on **critical paths** (e.g., API latency, DB query times).

5. **Isolating Observability Tools**
   - *Mistake*: Using Prometheus for metrics, ELK for logs, and Zipkin for traces.
   - *Solution*: Use a **single instrument (OpenTelemetry)** to emit all three.

---

## Key Takeaways

| **Pillar**       | **Purpose**                          | **Tools Used**                     | **Example Question Answered**               |
|------------------|--------------------------------------|------------------------------------|---------------------------------------------|
| **Metrics**      | Track system health at scale          | Prometheus, Grafana                | "Did my API response time spike at 3 PM?"   |
| **Logs**         | Debug specific failures               | ELK, Winston                       | "Why did this DB query fail for user 42?"   |
| **Traces**       | Follow request flows across services | Jaeger, OpenTelemetry              | "Where did this request take 300ms?"       |

1. **Start small**: Instrument **one critical service** before scaling.
2. **Automate alerts**: Use Prometheus Alertmanager for anomalies.
3. **Correlate everything**: Add trace IDs to logs for traceability.
4. **Optimize sampling**: Don’t overburden your observability stack.
5. **Document your schema**: Know what each metric/log/trace means.

---

## Conclusion: Observability as a Superpower

Observability isn’t just for production—it’s for **every stage** of development:

- **Local Dev**: Debug with logs + traces locally (using `otelcol-contrib`).
- **Staging**: Catch issues before they reach users.
- **Production**: Proactively detect and resolve incidents.

By combining **metrics**, **logs**, and **traces**, you transform your stack from a "black box" to a **glass box**. You’ll:

✅ **Reduce downtime** by catching issues before users notice.
✅ **Debug faster** with correlated logs and traces.
✅ **Prove reliability** with proactive monitoring.

### Next Steps:
1. [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/) – Learn to scrape metrics.
2. [OpenTelemetry Node.js](https://opentelemetry.io/docs/instrumentation/js/) – Extend instrumentation.
3. [Jaeger Getting Started](https://www.jaegertracing.io/docs/1.36/getting-started/) – Visualize traces.

---
*What’s your biggest observability challenge? Share in the comments! Need help setting up a specific tool? Ask away—I’m happy to help.*
```