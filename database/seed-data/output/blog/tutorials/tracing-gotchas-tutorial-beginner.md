```markdown
# **Tracing Gotchas: When Your Observability Breaks Without You Knowing**

*You enabled distributed tracing, but your logs look like a puzzle you can’t solve. A request that should be 50ms takes 30 seconds. Your team spin-wheels while debugging because tracing is missing critical parts of the transaction. Welcome to the world of tracing gotchas.*

Distributed tracing is powerful—it helps you visualize requests as they traverse microservices, identify bottlenecks, and debug latency. But tracing isn’t foolproof. Without careful implementation, you’ll face *silent failures*: traces that are incomplete, mislabeled, or missing entirely—leaving you blind to real issues.

This guide covers the **common pitfalls** of tracing and how to avoid them. We’ll walk through real-world examples, dive into code, and share lessons from production systems that hit these gotchas hard.

---

## **The Problem: Tracing Without Visibility**

Imagine this scenario:

*You deploy a new feature that fetches user data from a microservice before processing payments. Suddenly, payment requests start failing intermittently. With tracing enabled, you expect to see the full flow:*

```
**User Service (API Call)** → **User Data Service** → **Payment Service**
```

*But your trace looks like this:*
```
**User Service (API Call)** → (3s gap) → **Payment Service**
```

**Nothing about the `User Data Service`.** No errors, no warnings—just a hole in the trace. Now you have to:
- Check logs manually (slow)
- Rewrite service code to inject tracing (invasive)
- Accept "it might be happy" as an answer

This is a classic tracing gotcha: **missing spans** or **orphaned traces**. Other common issues include:
- **Sampling bias**: Your traces only show happy paths, so bugs on failure paths go undetected.
- **Trace context propagation errors**: Your services are losing context, causing "ghost" requests.
- **Overhead**: Tracing slows your app so much that it’s unusable in production.

---

## **The Solution: Tracing Gotchas & How to Fix Them**

Let’s break down the key gotchas and their fixes, with practical examples.

---

### **1. Orphaned Spans (Missing Middleware/Service Calls)**
**The Problem:**
You instrument a service endpoint, but **internal HTTP calls, database queries, or async tasks** don’t show up in traces.

**Example:**
```javascript
// Express.js with OpenTelemetry
const { tracer } = require('@opentelemetry/sdk-trace-node');

app.get('/order/:id', async (req, res) => {
  const span = tracer.startSpan('getOrder'); // This appears in traces
  try {
    const order = await fetchOrder(req.params.id); // Missing span
    res.json(order);
  } finally {
    span.end();
  }
});
```
This trace will show **only `getOrder`**—no visibility into the `fetchOrder` call.

**The Fix: Instrument Every Operation**
Use SDKs to auto-instrument HTTP clients, DB queries, and async tasks.

#### **With OpenTelemetry (Node.js):**
```javascript
// Enable auto-instrumentation for HTTP clients
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { fetchInstrumentation } = require('@opentelemetry/instrumentation-fetch');

const provider = new NodeTracerProvider();
provider.register();

// Auto-instrument fetch and HTTP clients
registerInstrumentations({
  instrumentations: [
    new HttpInstrumentation(),
    new fetchInstrumentation(),
  ],
});
```
Now, **every HTTP call** automatically gets a span:
```
User Service → fetchOrder → Database Query
```

---

### **2. Sampling Bias: Happy Paths Only**
**The Problem:**
You only trace **successful requests**, so failures are invisible. Worse, your sampling rate is too low, so rare errors never appear.

**Example:**
If you sample 1%, you’ll only see **1 in 100 failures**—never enough to debug.

**The Fix: Adjust Sampling & Prioritize Errors**
- **Error sampling**: Always trace failed requests.
- **Rate-based sampling with exceptions**: Sample 100% of requests under 100ms, but increase sampling for slow/error-heavy paths.

#### **OpenTelemetry Sampling Strategy (Node.js):**
```javascript
const { Resource } = require('@opentelemetry/resources');
const { Sampler } = require('@opentelemetry/sdk-trace-node');

const resource = new Resource({
  attributes: {
    service.name: 'user-service',
  },
});

const provider = new NodeTracerProvider({
  resource,
  sampler: new Sampler({
    decisionFn: (attributes) => {
      // Always sample if request is slow or errors
      if (attributes['http.responseTime'] > 500 || attributes['error']) {
        return Sampler DECISION_HEAD;
      }
      // Otherwise, use a low rate
      return Sampler DECISION_NOT_RECORD;
    },
  }),
});
provider.register();
```

---

### **3. Context Propagation Failures**
**The Problem:**
Your traces **lose context** when moving between services. This happens if:
- **Headers aren’t attached** (e.g., `traceparent`).
- **Async tasks don’t inherit context** (e.g., webhooks).

**Example:**
```javascript
// Express route with missing propagation
app.post('/webhook', async (req, res) => {
  // ❌ No propagation to async tasks!
  await processPayment(req.body);
});
```
The `processPayment` function won’t know about the original trace.

**The Fix: Ensure Context Propagation**
Use **W3C Trace Context** (standardized in `traceparent` headers) and propagate it everywhere.

#### **Correct Approach (OpenTelemetry):**
```javascript
// Automatically propagates context via HTTP headers
const { trace } = require('@opentelemetry/api');
const { fetchInstrumentation } = require('@opentelemetry/instrumentation-fetch');

registerInstrumentations({
  instrumentations: [new fetchInstrumentation()],
});

// Inside an async function (e.g., processPayment)
async function processPayment(paymentData) {
  const span = trace.getSpan(trace.getCurrentSpanContext());
  // Span now carries the original trace context!
}
```

---

### **4. Database Query Visibility**
**The Problem:**
You miss **SQL execution times** and **query details** because your ORM/database driver isn’t instrumented.

**Example:**
```javascript
// Without auto-instrumentation
await db.query('SELECT * FROM users WHERE id = ?', [userId]);
```
No trace span for this query.

**The Fix: Auto-Instrument DB Drivers**
Use OpenTelemetry plugins for your DB:

#### **MySQL Example (Node.js):**
```javascript
const { MySqlInstrumentation } = require('@opentelemetry/instrumentation-mysql');
registerInstrumentations({
  instrumentations: [new MySqlInstrumentation()],
});
```

Now, your trace will show:
```
User Service → fetchOrder → MySQL Query
```

---

### **5. Overhead: Tracing Slows Down Your App**
**The Problem:**
Tracing adds latency, and if you’re not careful, it **degrades performance**.

**Example:**
- A 100ms request becomes 300ms because tracing overhead.
- Some services (e.g., long-running async tasks) get **unpredictable delays**.

**The Fix: Optimize Sampling & Async Tracing**
- **Async tasks**: Use `setImmediate` or `queueMicrotask` for non-blocking spans.
- **Circuit breakers**: Avoid tracing **long-running requests** unless critical.

#### **Async Span Example (OpenTelemetry):**
```javascript
async function fetchUserAsync() {
  const span = trace.startSpan('fetchUserAsync');
  trace.setSpan(trace.getCurrentSpan(), span);

  // Non-blocking span
  await fetch('https://api.example.com/users')
    .then(res => res.json())
    .finally(() => span.end());
}
```

---

## **Implementation Guide: Setting Up Tracing Properly**

### **Step 1: Choose a Tracing System**
| Tool          | Pros                          | Cons                          |
|---------------|-------------------------------|-------------------------------|
| OpenTelemetry  | Open-source, vendor-agnostic  | Requires setup                |
| Datadog       | Managed, great UI             | Expensive                     |
| Jaeger        | Lightweight, flexible         | Less observability features   |
| AWS X-Ray     | Tight AWS integration         | AWS-only                      |

**Recommendation for beginners:** Start with **OpenTelemetry** (free, standard).

### **Step 2: Instrument All Critical Paths**
- **HTTP Endpoints** → Use middleware (Express, Flask, etc.).
- **Database Queries** → Auto-instrument DB drivers.
- **Async Tasks** → Ensure context propagates.
- **External Calls** → Auto-instrument `fetch`, `axios`, etc.

### **Step 3: Configure Sampling**
- **Start with 5-10% sampling** (adjust based on needs).
- **Always trace errors** (set `error` attribute to `true`).

### **Step 4: Monitor Trace Coverage**
- If traces are **too sparse**, increase sampling.
- If traces are **too noisy**, filter by service/operation.

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Not Instrumenting Database Queries**
**Symptom:** Your traces show service calls but **no SQL data**.
**Fix:** Use OpenTelemetry’s MySQL/PostgreSQL plugins.

### **❌ Mistake 2: Ignoring Async Context**
**Symptom:** Webhooks/background jobs **lose trace context**.
**Fix:** Pass the `traceparent` header or use `context.active()`.

### **❌ Mistake 3: Over-Sampling Every Request**
**Symptom:** Your trace backend **gets overwhelmed**.
**Fix:** Use **adaptive sampling** (e.g., more sampling for slow requests).

### **❌ Mistake 4: Not Setting Resource Attributes**
**Symptom:** Your traces **all look the same** (no service name, version, etc.).
**Fix:** Add `service.name`, `service.version`, etc., to `Resource`.

---
## **Key Takeaways**
Here’s what you should remember:

✅ **Instrument everything** – HTTP calls, DB queries, async tasks.
✅ **Propagate context** – Use `traceparent` headers for service-to-service calls.
✅ **Smart sampling** – Trace errors 100%, sample happy paths wisely.
✅ **Optimize async tracing** – Avoid blocking operations in spans.
✅ **Monitor trace coverage** – Adjust sampling if traces are too sparse/noisy.
✅ **Start with OpenTelemetry** – It’s the most flexible choice.

---

## **Conclusion: Tracing Shouldn’t Be a Black Box**
Distributed tracing is **incredibly powerful**—but only if you set it up right. The gotchas we covered (orphaned spans, sampling bias, missing DB queries) are **common traps**, but avoidable.

**Next Steps:**
1. **Instrument your app** (start with OpenTelemetry).
2. **Test tracing in staging** before production.
3. **Iterate**—adjust sampling and coverage as needed.

Now go ahead and **debug like a pro**—with full visibility in your traces.

---
**Further Reading:**
- [OpenTelemetry Auto-Instrumentation Docs](https://opentelemetry.io/docs/instrumentation/)
- [Distributed Tracing Anti-Patterns (Google)](https://cloud.google.com/blog/products/observability/distributed-tracing-anti-patterns)
- [How We Traced 100% of Requests at Airbnb](https://medium.com/airbnb-engineering/tracing-100-of-requests-at-airbnb-7d1735258317)

---
**Got questions?** Drop them in the comments! 🚀
```