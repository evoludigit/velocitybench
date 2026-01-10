# **Debugging Distributed Tracing & Request Context: A Troubleshooting Guide**

## **Introduction**
Distributed tracing helps track requests across microservices, logging timestamps, dependencies, and errors in a single context. When misconfigured, this pattern leads to blind spots like missing spans, miscorrelated logs, or inefficient latency analysis.

This guide focuses on **quick resolution**—identifying issues, applying fixes, and preventing recurrence.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

| **Symptom**                          | **Likely Cause**                          | **Impact**                          |
|--------------------------------------|------------------------------------------|-------------------------------------|
| Requests appear fast in metrics but slow in user experience | Missing spans, partial tracing, or blocking calls | Inaccurate latency analysis |
| Logs from different services lack correlation | Context propagation failure (e.g., missing headers) | Debugging requires manual correlation |
| Tracing spans show gaps or missing segments | Incomplete instrumentation (e.g., missing `Tracer` calls) | Blind spots in service dependencies |
| High latency spikes with no clear root cause | Missing critical span instrumentation (DB calls, external APIs) | Difficult to optimize |
| Tracing dashboard shows orphaned spans | Context propagation failure or misconfigured sampling | Noisy traces, reduced visibility |

---

## **2. Common Issues and Fixes**

### **Issue 1: Tracer Not Initialized Properly**
**Symptoms:**
- Some services have no spans recorded.
- Only partial request flows appear in traces.

**Root Cause:**
- Tracer not initialized in a newly added service.
- Incorrect SDK version or misconfigured `Sampler`/`SpanProcessor`.

#### **Fix (Java/Go Example)**
**Java (OpenTelemetry):**
```java
// Wrong: Missing initialization
public class ServiceB {
    public void process() {
        Span span = tracer.spanBuilder("process").startSpan(); // Fails if tracer not set
    }
}

// Correct: Initialize tracer in a module
@Module
public class TracingModule {
    @Provides
    public TracerProvider tracerProvider() {
        TracerProvider provider = SdkTracerProvider.builder()
            .sampler(OtelCompositeSampler.create(
                AlwaysOnSampler.getInstance(),
                ParentBasedSampler.create(AlwaysOnSampler.getInstance())
            ))
            .build();
        provider.registerExtensionRegistry(ExtensionConfigParser.DEFAULT_EXTENSION_REGISTRY);
        return provider;
    }
}
```

**Go (OpenTelemetry):**
```go
// Wrong: No tracer initialization
func handleRequest(w http.ResponseWriter, r *http.Request) {
    ctx, span := tracer.Start(r.Context(), "handleRequest")
    defer span.End()
}

// Correct: Initialize tracer in main()
func main() {
    tp := sdk.NewTracerProvider()
    defer func() { _ = tp.Shutdown(ctx) }()
    tracerProvider = tp
    http.HandleFunc("/", handleRequest)
    http.ListenAndServe(":8080", nil)
}
```

---

### **Issue 2: Context Propagation Failure**
**Symptoms:**
- Logs from Service A and Service B have no correlation.
- Some services ignore request context.

**Root Cause:**
- Missing `traceparent` header in HTTP calls.
- Incorrect context extraction in RPC (gRPC, Kafka).

#### **Fix (HTTP Example)**
**Java (Spring Boot):**
```java
// Wrong: Manual span creation (no parent context)
@GetMapping("/api")
public String handleRequest() {
    Span span = tracer.spanBuilder("handleRequest").startSpan();
    try (Scope scope = span.makeCurrent()) {
        return "response";
    } finally { span.end(); }
}

// Correct: Use W3C trace context
@GetMapping("/api")
public String handleRequest(HttpServletRequest req) {
    Context context = Context.current();
    Context parent = Context.fromRequest(req);
    Span span = tracer.spanBuilder("handleRequest").setParent(Context.current().spanOrNull()).startSpan();
    try (Scope scope = span.makeCurrent()) {
        return "response";
    } finally { span.end(); }
}
```

**Go (Propagate headers):**
```go
// Wrong: No context propagation
func handler(w http.ResponseWriter, r *http.Request) {
    span := tracetracer.Start(r.Context(), "handler")
    defer span.End()
}

// Correct: Use OpenTelemetry HTTP middleware
http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    r = othttp.WithTracerProvider(r, tp)
    r = othttp.WithSpanFromContext(r, ctx)
    // Process request...
})
```

---

### **Issue 3: Missing Spans for External Calls**
**Symptoms:**
- Database calls or 3rd-party APIs appear as "black holes."
- Latency spikes tied to external dependencies.

**Root Cause:**
- No context passed to external calls.
- Missing instrumentation for blocking I/O.

#### **Fix (Database Example)**
**Java (JDBC):**
```java
// Wrong: Silent DB call (no span)
public List<User> getUsers() {
    try (Connection conn = ds.getConnection()) {
        return jdbcTemplate.query("SELECT * FROM users", new UserRowMapper());
    }
}

// Correct: Wrap DB calls in spans
public List<User> getUsers() {
    Span dbSpan = tracer.spanBuilder("getUsers").startSpan();
    try (Scope scope = dbSpan.makeCurrent()) {
        return jdbcTemplate.query("SELECT * FROM users", new UserRowMapper());
    } finally { dbSpan.end(); }
}
```

**Go (PostgreSQL):**
```go
// Wrong: No instrumentation
rows, err := db.Query("SELECT * FROM users")
// ...

// Correct: Use OpenTelemetry SQL instrumentation
db, err := otelsql.Open("postgres", "your-dsn", otelsql.WithConfig(otelsql.Config{
    DriverName: "pgx",
    Config:     pgx.Config{
        ConnConfig: pgx.ConnConfig{...},
    },
}))
```

---

### **Issue 4: Sampling Misconfiguration**
**Symptoms:**
- Too few traces (high sampling rate).
- Too many traces (overloaded tracing backend).

**Root Cause:**
- Sampling rate too aggressive (`AlwaysOnSampler`).
- Custom sampler logic fails.

#### **Fix (Adjust Sampling)**
**Java (Probability-Based Sampling):**
```java
TracerProvider provider = SdkTracerProvider.builder()
    .sampler(OtelCompositeSampler.create(
        AlwaysOnSampler.getInstance(),
        ParentBasedSampler.create(TraceIdRatioBasedSampler.fromParentSamplingDecision(
            0.1f // 10% of traces sampled
        ))
    ))
    .build();
```

**Go (Head-Based Sampling):**
```go
sampler := otelsdk.NewHeadBased(nopSampler.WithHead(int64(1/10)))
tp := sdk.NewTracerProvider(
    sdk.WithSampler(sampler),
    // ...
)
```

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example**                                  |
|--------------------------|---------------------------------------|---------------------------------------------|
| **Tracing Backend UI**   | Visualize traces                      | Jaeger, Zipkin, OpenTelemetry Collector    |
| **SDK Logs**             | Check for tracer errors               | `tracer.spanBuilder("...")` failures        |
| **Context Propagation**  | Verify headers/RPC context            | `curl -v http://service/api` (check headers) |
| **Trace IDs**            | Correlate logs across services        | `grep "trace_id=123" /var/log/app.log`      |
| **Metrics for Spans**    | Check span drop rates                 | `otel-spans-dropped` metric                 |

**Example Debug Workflow:**
1. **Reproduce issue** → Check tracing backend UI for missing spans.
2. **Check logs** → Look for `TracerException` or `SpanContext` errors.
3. **Isolate service** → Test context propagation manually (`curl` with headers).
4. **Verify SDK version** → Downgrade if known issues exist.

---

## **4. Prevention Strategies**

### **A. Best Practices for Tracing**
✅ **Instrumentation:**
- Wrap **all external calls** (DB, HTTP, gRPC) in spans.
- Use **auto-instrumentation** where possible (e.g., OpenTelemetry AutoInstrumentations).

✅ **Context Propagation:**
- Always **extract and inject** context in HTTP/RPC calls.
- Use **W3C Trace Context** (HTTP headers) or **OpenTelemetry format** (gRPC).

✅ **Sampling:**
- Start with **head-based sampling** (e.g., `1%`).
- Adjust based on **latency vs. cost tradeoff**.

✅ **Error Handling:**
- Log **failed spans** (e.g., `Span.setStatus(Status.ERROR)`).
- Use **structured logging** with `trace_id`.

### **B. Code Review Checklist**
- [ ] All external calls have spans.
- [ ] Context is propagated in HTTP/RPC.
- [ ] No manual `span.build()` without parent context.
- [ ] Sampling is configured (not `AlwaysOn`).
- [ ] Tracer is initialized (no `null` checks).

### **C. Testing**
- **Unit Tests:** Verify context propagation.
- **Integration Tests:** Check span correlation across services.
- **Chaos Testing:** Simulate latency spikes and verify traces.

---
## **Conclusion**
Distributed tracing should **never be an afterthought**. By focusing on:
1. **Proper tracer initialization**
2. **Context propagation**
3. **Full instrumentation**
4. **Sampling optimization**

You can avoid most debugging headaches. Start with **missing spans**, then **context issues**, and finally **sampling tweaks**. Use the tools above to **validate fixes quickly**.

**Final Tip:** If all else fails, **start with a blank slate**—disable tracing, redeploy with minimal instrumentation, and gradually add spans. This isolates misconfigurations.

---
**Need faster resolution?** Check:
- [OpenTelemetry GitHub Issues](https://github.com/open-telemetry/opentelemetry-java/issues)
- [Jaeger/Zipkin Debugging Docs](https://www.jaegertracing.io/docs/latest/deployment/)