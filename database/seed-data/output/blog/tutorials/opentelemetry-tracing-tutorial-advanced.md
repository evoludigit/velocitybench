```markdown
# **Distributed Tracing with OpenTelemetry: Solving the "Query Execution Blackbox" Problem**

*How to instrument, trace, and debug complex databases and APIs in distributed systems*

---

## **Introduction**

As backend systems grow, so does their complexity. Modern applications span multiple services, databases, and microservices—all communicating over HTTP, gRPC, or message queues. When a database query or API call fails, debugging becomes a nightmare: Is the issue with the database? The network? A third-party service? Without visibility into the full execution flow, problems often go unresolved or surface as mysterious errors in production.

**Distributed tracing** solves this by tracking requests across services, capturing timing information, and associating details like query execution time, database calls, and external service invocations. OpenTelemetry (OTel) is the modern, vendor-agnostic standard for collecting telemetry data—including traces, metrics, and logs—from distributed applications. In this guide, we’ll focus on **OpenTelemetry Tracing (OTel Tracing)**, exploring how to instrument a backend system for observability, using **Jaeger**, **Zipkin**, and **OTLP** as tracing backends.

By the end, you’ll understand:
✅ How to set up **OpenTelemetry Tracing** in a database-heavy application
✅ How to instrument **query execution phases** and propagate context
✅ How to visualize traces in **Jaeger** vs. **Zipkin**
✅ Common pitfalls and best practices

Let’s dive in.

---

## **The Problem: No Visibility into Query Execution Breakdown**

Imagine this scenario:

You receive a user report: *"The `/api/reports` endpoint is slow."* You check the application logs, but they only show a 500ms response time. Digging deeper, you notice that the logs don’t indicate **how long the database query took** or whether it was retried. The only clue is a generic error: `PostgresConnectionError: Timeout expired`.

But here’s the catch: you don’t know if:
- The timeout happened during the initial query.
- It occurred after a failed retry.
- The issue was in a downstream service called mid-query.

Without **distributed tracing**, you’re left guessing.

---

### **The Query Execution Blackbox**
Even simple applications like FraiseQL—where users run complex SQL queries—can become opaque. Consider this workflow:

1. A user submits a **`SELECT query`** via the API.
2. The request is parsed, validated, and **instrumented** by a query planner.
3. The query is executed across **multiple database nodes** (for shard splitting).
4. Results are aggregated and returned.

At any step, something could go wrong:
- A **shard query times out**.
- A **network partition** delays response.
- A **secondary service** fails during the aggregation phase.

Without tracing, these issues become invisible.

---

## **The Solution: OpenTelemetry Tracing for Distributed Debugging**

OpenTelemetry provides a **standardized way** to:
✔ **Instrument** applications with spans (timed operations).
✔ **Propagate context** (like request IDs) across services.
✔ **Export traces** to backends like **Jaeger**, **Zipkin**, or **OTLP-compatible services**.

The key components are:

| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Spans**          | Represent work done (e.g., SQL query, API call).                        |
| **Traces**         | A collection of spans forming a single request path.                      |
| **Attributes**     | Metadata attached to spans (e.g., `query="SELECT * FROM users"`).      |
| **Links**          | Associate related traces (e.g., link a downstream service call).        |
| **Propagators**    | Attach trace context to HTTP headers or message envelopes.              |

### **How OpenTelemetry Tracing Works**
1. **Instrument** the code to create spans for critical operations (e.g., DB queries).
2. **Propagate** trace context (e.g., `traceparent` header) between services.
3. **Export** traces to a backend (Jaeger, Zipkin, or OTLP).
4. **Visualize** and analyze traces for bottlenecks.

---

## **Components / Solutions**

### **1. OpenTelemetry Collector (Otelcol)**
A lightweight agent that:
- Receives telemetry data from applications.
- Processes and forwards it to backends (Jaeger, Zipkin, etc.).

**Example Config (`config.yaml`):**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:
  jaeger:
    endpoint: "jaeger:14250"
  zipkin:
    endpoint: "http://zipkin:9411/api/v2/spans"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, zipkin]
```

### **2. Backend: Jaeger vs. Zipkin**
| Feature          | Jaeger                                                                 | Zipkin                                                                 |
|------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Pros**         | Rich visualization, service graphs, long-term storage.                 | Lightweight, great for simple latency analysis.                         |
| **Cons**         | Slightly heavier setup.                                                 | Limited advanced features (no dependency graphs).                       |
| **Best For**     | Complex distributed systems.                                            | Lightweight tracing with minimal overhead.                             |

---

## **Code Examples: Instrumenting a Database Query**

Let’s implement OpenTelemetry tracing in a backend service using **Node.js (Express)** and **FraiseQL** (a hypothetical query executor).

---

### **Step 1: Install OpenTelemetry SDK**
```bash
npm install @opentelemetry/sdk-node @opentelemetry/exporter-jaeger @opentelemetry/tracing
```

---

### **Step 2: Set Up Tracing in Express**
```javascript
// app.js
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');

// Initialize tracing
const provider = new NodeTracerProvider();
const exporter = new JaegerExporter({
  endpoint: 'http://localhost:14268/api/traces',
});
provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
provider.register();

// Instrument Express
registerInstrumentations({
  instrumentations: [new ExpressInstrumentation()],
});

const express = require('express');
const app = express();
const { fraiseQL } = require('./fraiseql'); // Hypothetical query executor

// Middleware to propagate trace context
app.use((req, res, next) => {
  // Automatically handled by ExpressInstrumentation via request headers
  next();
});

// Query endpoint with tracing
app.post('/api/query', async (req, res) => {
  const span = provider.getTracer('fraiseql').startSpan('query.execution');
  span.addEvent('query.started');

  try {
    const { sql } = req.body;
    const result = await fraiseQL.execute(sql); // Hypothetical call
    span.addAttributes({ query: sql, rows_fetched: result.rowCount });
    span.end();
    res.json(result);
  } catch (err) {
    span.recordException(err);
    span.end();
    throw err;
  }
});
```

---

### **Step 3: Instrument FraiseQL’s Query Execution**
```javascript
// fraiseql.js
const { tracer } = require('@opentelemetry/api');

async function execute(sql) {
  const rootSpan = tracer.startSpan('fraiseql.execute');
  const querySpan = rootSpan.startSpan('db.query');
  querySpan.setAttribute('sql', sql);

  try {
    // Simulate DB connection (replace with real logic)
    const startTime = Date.now();
    await new Promise(resolve => setTimeout(resolve, 100)); // Emulate DB delay
    const queryTime = Date.now() - startTime;

    querySpan.setAttribute('query_time_ms', queryTime);
    querySpan.end();

    rootSpan.end();
    return { rowCount: 5, data: [] };
  } catch (err) {
    querySpan.recordException(err);
    querySpan.end();
    throw err;
  }
}

module.exports = { execute };
```

---

### **Step 4: Propagate Context to Downstream Services**
When calling external services (e.g., caching layer), propagate the trace context:

```javascript
// fraiseql.js (extended)
const { Context, diode, headersAccessor } = require('@opentelemetry/api');

async function fetchFromCache(sql) {
  const httpSpan = tracer.startSpan('cache.fetch', { attributes: { sql } });

  try {
    const response = await fetch('https://cache-service/api/query', {
      headers: {
        'traceparent': diode.headers(headersAccessor(Context.current()).get('traceparent')),
      },
    });
    httpSpan.setAttribute('status', response.status);
    return await response.json();
  } catch (err) {
    httpSpan.recordException(err);
    throw err;
  } finally {
    httpSpan.end();
  }
}
```

---

## **Implementation Guide**

### **1. Set Up OpenTelemetry Collector**
Deploy a **Docker container** with the collector config:
```bash
docker run -d \
  --name=otel-collector \
  -v /path/to/config.yaml:/etc/otel-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-config.yaml
```

### **2. Configure Backend**
- **Instrument your app** (Node.js, Python, Go, etc.) with OTel SDK.
- **Add spans for critical paths** (DB queries, API calls, retries).
- **Use `startSpan`** for operations and `endSpan` when done.

### **3. Query Traces in Jaeger**
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14250:14250 \
  jaegertracing/all-in-one:latest
```
Visit `http://localhost:16686` and search for traces by trace ID.

### **4. Visualize in Zipkin**
```bash
docker run -d --name zipkin \
  -p 9411:9411 \
  openzipkin/zipkin
```
Visit `http://localhost:9411` and filter by `traceId`.

---

## **Common Mistakes to Avoid**

### **1. Not Instrumenting Critical Paths**
❌ **Mistake:** Only instrumenting API endpoints, skipping DB queries.
✅ **Fix:** Add spans for **every major operation** (e.g., `shard.split`, `cache.miss`).

### **2. Overhead from Excessive Spans**
❌ **Mistake:** Creating too many spans (e.g., per row in a query).
✅ **Fix:** Use **sampling** (e.g., `AlwaysOnSampler` for dev, `ParentBasedSampler` for prod).

### **3. Ignoring Context Propagation**
❌ **Mistake:** Forgetting to pass `traceparent` to downstream services.
✅ **Fix:** Use **propagators** (W3C Trace Context) for HTTP/async calls.

### **4. Not Attaching Useful Attributes**
❌ **Mistake:** Only log `status: "success"` without `query` or `shard`.
✅ **Fix:** Add **meaningful attributes** (e.g., `sql`, `user_id`, `shard`).

### **5. Not Handling Errors Properly**
❌ **Mistake:** Letting spans end without marking failures.
✅ **Fix:** Use `recordException()` and `setStatus(STATUS_ERROR)`.

---

## **Key Takeaways**

✔ **OpenTelemetry Tracing** provides **end-to-end visibility** into distributed systems.
✔ **Spans** track individual operations (e.g., DB queries), while **traces** link them.
✔ **Instrument key paths** (API → DB → Cache) for debugging.
✔ **Propagate trace context** (via headers) to maintain observability.
✔ **Use Jaeger/Zipkin** for visualization, but **OTLP** is the modern standard.
✔ **Avoid:**
   - Too many spans (use sampling).
   - Missing context propagation.
   - Incomplete error handling.

---

## **Conclusion**

Distributed tracing with **OpenTelemetry** transforms debugging from a **blackbox mystery** to a **guided investigation**. By instrumenting database queries, API calls, and external services, you gain insights into:
✅ Where bottlenecks occur.
✅ Which queries fail most often.
✅ How retries affect latency.

For **FraiseQL-like applications**, tracing reveals:
- **Long-running shard queries**.
- **Network delays** between nodes.
- **Cache misses** causing redundant DB work.

Start small: instrument **one critical path**, then expand. Use **Jaeger** for deep analysis, and **Zipkin** for lightweight checks. With OpenTelemetry, you’ll never be in the dark again.

---
**Next Steps:**
1. Try the [OpenTelemetry Node.js Quickstart](https://opentelemetry.io/docs/instrumentation/nodejs/getting-started/).
2. Explore [FraiseQL’s OTel instrumentation](https://github.com/fraise-io/fraise/tree/main/examples/opentelemetry).
3. Compare **Jaeger vs. Zipkin** for your use case.

Happy tracing! 🚀
```