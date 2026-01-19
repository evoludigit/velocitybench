# **Debugging Tracing: A Troubleshooting Guide**

## **1. Introduction**
Tracing is a debugging pattern that captures the execution flow of an application, including method calls, request/response cycles, database queries, and external service interactions. It helps track slow performance, dependency failures, and logical errors by providing a chronological log of events.

Unlike logging, tracing:
- Follows a **single logical path** (e.g., a user request).
- Uses **correlation IDs** to link related events (e.g., request → DB → external service).
- Is **structured** (common frameworks like OpenTelemetry, Zipkin, or Jaeger enforce schemas).

This guide focuses on **practical troubleshooting** for tracing-related issues.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom** | **Possible Cause** |
|-------------|--------------------|
| Tracing data missing for recent requests | Tracer not initialized, sampling rate too low |
| Corrupted or incomplete traces | Improper span context propagation |
| High latency in trace visualization | Backend tracing backend (e.g., Jaeger/Zipkin) overloaded |
| Missing attributes in spans | Wrong instrumented code or missing exports |
| Traces show empty or null values | Incorrect data model or serialization issues |
| Tracing slows down production | Profiling overhead, too many spans |
| Integration with APM tools fails | SDK version mismatch or misconfiguration |

---

## **3. Common Issues & Fixes**

### **3.1 Issue: Tracer Not Initialized**
**Symptom:** No traces appear in the backend, even though code is instrumented.
**Root Cause:** The tracer was never initialized, or it’s disabled.

#### **Fix (Java with OpenTelemetry)**
```java
// Correct: Initialize tracer in application startup
TracerProvider tracerProvider = OpenTelemetrySdk.getTracerProviderBuilder()
    .setSampler(AlwaysOnSampler.getInstance()) // For debugging
    .build();

Tracer tracer = tracerProvider.getTracer("my-service");

// Instrumentation example:
Span span = tracer.spanBuilder("process-order")
    .setAttribute("order-id", "123")
    .startSpan();
```

**Why it fails:**
- If `tracerProvider` is null, spans won’t be recorded.
- **Check:** Log `tracerProvider.getTracer("my-service")` to see if it returns a valid instance.

---

### **3.2 Issue: Missing Span Context in Distributed Requests**
**Symptom:** Traces break when moving between services (e.g., `Service A → Service B`).
**Root Cause:** Span context not propagated via headers or gRPC metadata.

#### **Fix (HTTP/REST with OpenTelemetry)**
```java
// Service A: Inject span into outgoing request
Span currentSpan = tracer.spanBuilder("http-request").startSpan();
currentSpan.setAttribute("http.url", "https://service-b/api");

// Propagate as text map
TextMapPropagator propagator = ContextPropagators.getTextMapPropagator();
propagator.inject(Context.current(), new HttpHeadersCarrier(request.getHeaders()), currentSpan.getSpanContext());

// Service B: Extract span from incoming request
TextMapCarrier carrier = new HttpHeadersCarrier(request.getHeaders());
Context context = propagator.extract(Context.current(), carrier);
Span extractedSpan = tracer.spanBuilder("process").startSpan();
extractedSpan.setParent(Context.current().get(Span.class));
```

**Common mistakes:**
- Forgetting to propagate headers in load balancers/proxies.
- Using deprecated `Baggage` instead of `Span Context`.

---

### **3.3 Issue: Sampling Misses Critical Traces**
**Symptom:** High-traffic requests are dropped due to sampling.
**Root Cause:** Sampling rate too low (e.g., 1% when you need 10%).

#### **Fix (Adjust Sampling in OpenTelemetry)**
```java
TracerProvider tracerProvider = OpenTelemetrySdk.getTracerProviderBuilder()
    .setSampler(ParentBasedSampler.create(AlwaysOnSampler.getInstance()))
    .build();
```
**Use cases:**
- **AlwaysOnSampler** (100% of traces)
- **TraceIdRatioBasedSampler** (e.g., 50% of traces)
- **ParentBasedSampler** (sample parent → sample child)

**Check sampling:** Use `otel.sampler` env variable or check `jaeger-query` logs.

---

### **3.4 Issue: Traces Stuck in "In-Flight" Status**
**Symptom:** New traces appear but never complete.
**Root Cause:** Tracer or backend failure, or flaky instrumentation.

#### **Fix (Ensure Proper Span Finishing)**
```java
Span span = tracer.spanBuilder("process-order").startSpan();
try {
    // Business logic
} finally {
    span.end(); // Critical! Do NOT forget this.
}
```

**Why it matters:**
- Unfinished spans pollute trace storage.
- Check for `span.end()` in all code paths (including error handling).

---

### **3.5 Issue: Missing Attributes in Traces**
**Symptom:** Traces show no custom attributes (e.g., `user-id`, `status-code`).
**Root Cause:** Incorrect instrumentation or missing `setAttribute()` calls.

#### **Fix (Add Attributes to Spans)**
```java
Span span = tracer.spanBuilder("db-query")
    .setAttribute("db.system", "postgres")
    .setAttribute("query", "SELECT * FROM users")
    .startSpan();
```
**Common missing attributes:**
- `http.method`, `http.status_code`
- `db.operation`, `db.name`
- `error.type` (if an exception occurs)

---

### **3.6 Issue: Tracing Backend (Jaeger/Zipkin) Overloaded**
**Symptom:** Trace visualization slows to a crawl.
**Root Cause:** Too many traces or backend misconfiguration.

#### **Fix (Optimize Tracing Backend)**
**Option 1: Reduce Sampling**
```yaml
# Configuration (e.g., for Jaeger)
env:
  OTEL_TRACES_SAMPLER: "parentbased"{traceIdRatio:0.2}
```

**Option 2: Use a Lightweight Backend**
- **Zipkin (HBase):**
  ```sh
  docker run -d -p 9411:9411 openzipkin/zipkin
  ```
- **Tempo (with Grafana):** Better for high-volume traces.

**Option 3: Archive Old Traces**
- Jaeger: `jaeger-collector --archive-storage.path=/var/jaeger/archives`
- Zipkin: Use S3/HDFS for long-term storage.

---

### **3.7 Issue: External Service Timeout in Traces**
**Symptom:** Traces show "hanging" HTTP/DB calls.
**Root Cause:** Timeout not propagated to tracing system.

#### **Fix (Set Timeout in HTTP Clients)**
```java
// Java (OkHttp)
Request request = new Request.Builder()
    .url("https://api.example.com")
    .build();

Span span = tracer.spanBuilder("external-api-call").startSpan();
try (Response response = new OkHttpClient.Builder()
    .connectTimeout(2, TimeUnit.SECONDS) // Timeout
    .build()
    .newCall(request)
    .execute()) {
    span.setAttribute("http.status", response.code());
}
```

**Why it matters:** Without timeouts, traces may show `>60s` delays artificially.

---

## **4. Debugging Tools & Techniques**

### **4.1 Verify Tracer Initialization**
```sh
# Check if tracer is loaded (Java example)
curl -i http://localhost:8080/actuator/health | grep tracer
```
- If missing, tracer was never initialized.

### **4.2 Check Sampling Configuration**
```sh
# For OpenTelemetry
grep OTEL_TRACES_SAMPLER *env*
```
- Should return `0.1` (10%), `1.0` (100%), etc.

### **4.3 Validate Span Context Propagation**
```sh
# Test with cURL and Wireshark
curl -H "traceparent:00-1234..." http://service-b/api
```
- If the `traceparent` header is not forwarded, propagation fails.

### **4.4 Debug Jaeger/Zipkin Logs**
```sh
# Check collector logs (Docker example)
docker logs jaeger-collector
```
- Look for errors like `failed to flush batch`.

### **4.5 Use OpenTelemetry Tools**
| Tool | Purpose |
|------|---------|
| [`otel-collector-contrib`](https://github.com/open-telemetry/opentelemetry-collector-contrib) | Process traces before sending to backend |
| [`otel-cli`](https://github.com/open-telemetry/opentelemetry-js/tree/main/packages/opentelemetry-cli) | Debug traces locally |
| [`jaeger-cli`](https://www.jaegertracing.io/docs/latest/client-go/) | Query traces via CLI |

**Example: Query Jaeger CLI**
```sh
jaeger query --service=service-a --query-type=service
```

---

## **5. Prevention Strategies**

### **5.1 Instrument Early, Instrument Right**
- **Do:** Use auto-instrumentation (OpenTelemetry Auto) where possible.
- **Don’t:** Manually instrument every line (use libraries like `oteljava-contrib` for common patterns).

**Example (Auto-Instrumentation with OpenTelemetry)**
```java
@AutoInstrumented
public class MyService {
    // All HTTP calls, DB queries auto-traced
}
```

### **5.2 Set Up Alerting for Broken Traces**
- **Jaeger:** Use Prometheus + Grafana to alert on:
  - `jaeger_traces_processed_total` drops.
  - `jaeger_span_count` spikes.
- **Zipkin:** Monitor `zipkin_span` latency percentiles.

**Example Grafana Alert:**
- Trigger if `jaeger_traces_sampled > 10000` for 5 mins.

### **5.3 Use Structured Logging + Tracing**
- Correlate logs with traces using `traceparent` in log lines:
  ```json
  {
    "level": "ERROR",
    "message": "Failed to process order",
    "traceparent": "00-1234abc",
    "orderId": "123"
  }
  ```

### **5.4 Benchmark Tracing Overhead**
- **Goal:** <1% latency impact.
- **Test:** Load-test with traces enabled:
  ```sh
  ab -n 10000 -c 100 http://service/api
  ```
- **Optimize:** Reduce span count by:
  - Skipping spans in `DEV` (via `otel.service.name`).
  - Using `otel.propagation` filters.

### **5.5 Document Tracing Schema**
- Define **mandatory attributes** for each span (e.g., `http.method`, `db.query`).
- Example schema:
  ```json
  {
    "spans": [
      {
        "name": "http.request",
        "attributes": {
          "http.method": { "stringValue": "GET" },
          "http.status_code": { "intValue": 200 }
        }
      }
    ]
  }
  ```

---

## **6. Summary Checklist for Tracing Issues**
| **Step** | **Action** |
|----------|------------|
| 1 | Check if tracer is initialized (`tracerProvider != null`) |
| 2 | Verify sampling rate (`OTEL_TRACES_SAMPLER`) |
| 3 | Inspect span context propagation (headers/metadata) |
| 4 | Ensure all spans are finished (`span.end()`) |
| 5 | Check for missing attributes (e.g., `http.status`) |
| 6 | Monitor backend (Jaeger/Zipkin) logs |
| 7 | Profile tracing overhead (load test) |
| 8 | Correlate logs with traces (`traceparent`) |

---

## **7. Final Notes**
- **Start small:** Begin with 100% sampling in `DEV`, reduce in `PROD`.
- **Instrument incrementally:** Add traces to critical paths first.
- **Use existing tools:** Leverage OpenTelemetry, Jaeger, or Zipkin instead of rolling your own.
- **Automate fixes:** Use CI to scan for missing `span.end()` calls.

By following this guide, you can **quickly diagnose** and **prevent** tracing-related issues while maintaining observability.