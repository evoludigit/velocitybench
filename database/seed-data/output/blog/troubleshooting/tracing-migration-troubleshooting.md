# **Debugging Tracing Migration: A Troubleshooting Guide**
*Ensuring Smooth Transition from Legacy to Distributed Tracing in Microservices*

---

## **1. Introduction**
The **Tracing Migration** pattern involves transitioning from legacy logging (e.g., `console.log`, `log4j`) to **distributed tracing** (e.g., OpenTelemetry, Jaeger, Zipkin) to improve observability, latency analysis, and debugging in microservices. While this migration enhances debugging, it introduces complexity—especially when migrating existing applications while ensuring no downtime.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving common issues during and after tracing migration.

---

## **2. Symptom Checklist**
Before diving into fixes, ensure you’ve verified these symptoms:

### **During Migration (Pre-Deployment)**
- [ ] **Tracing agents/instrumentation conflicts**: Mixed traces (legacy + new) or crashes.
- [ ] **Performance degradation**: Higher latency due to excessive overhead.
- [ ] **Missing spans**: Certain calls are not being traced.
- [ ] **Incorrect context propagation**: Span IDs not correctly passed between services.
- [ ] **Duplicate spans**: Same operation generating multiple spans.

### **Post-Migration (Runtime Issues)**
- [ ] **Incomplete traces**: Broken context in distributed calls.
- [ ] **Trace sampling issues**: Too few/many traces affecting performance.
- [ ] **Sampling rate mismatches**: Some traces missing in aggregators (Jaeger, Zipkin).
- [ ] **Instrumentation drift**: New traces don’t align with expected behavior.
- [ ] **Storage/aggregator overload**: High CPU/memory usage in tracing backends.

---

## **3. Common Issues and Fixes**

### **Issue 1: Missing Spans (No Traces in Backend)**
**Symptom**:
Traces appear empty or certain service calls are untraced.

**Root Causes**:
- Missing instrumentation in microservices.
- Incorrect OpenTelemetry/Jaeger agent configuration.
- Network/firewall blocking gRPC/HTTP instrumentation.

#### **Fix: Verify Instrumentation**
**For Java (OpenTelemetry AutoInstrumentation):**
```java
// Ensure auto-instrumentation is enabled in application.properties
otel.autoinstrumentation.enabled=true
otel.traces.exporter=zipkin
otel.zipkin.endpoint=http://zipkin:9411/api/v2/spans
```

**For Node.js:**
```javascript
// Check if @opentelemetry/auto-instrumentations-node is installed
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { ZipkinExporter } = require('@opentelemetry/exporter-zipkin');

// Initialize provider
const provider = new NodeTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(new ZipkinExporter({
  endpoint: 'http://zipkin:9411/api/v2/spans',
})));
provider.register();
```

**Debugging Steps**:
1. **Check logs** for instrumentation errors.
2. **Test manually** (e.g., force a span):
   ```java
   Span span = tracer.spanBuilder("test-span").startSpan();
   span.makeCurrent();
   // ... business logic ...
   span.end();
   ```

---

### **Issue 2: Broken Context Propagation**
**Symptom**:
Spans are created but lack child-parent relationships; traces are fragmented.

**Root Causes**:
- Incorrect `textmap` propagator settings.
- Missing headers in HTTP calls.
- gRPC/microservice calls not propagating `traceparent`/`tracestate`.

#### **Fix: Configure Propagator**
**For Java (HTTP):**
```java
// Ensure W3C Trace Context propagator is set
TracerProvider provider = OpenTelemetrySdk.getTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(
    new BatchSpanProcessor(new ZipkinExporter(...))
));

// Configure propagator
propagator = new W3CTraceContextPropagator();
```

**For Python:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ZipkinExporter(endpoint="http://zipkin:9411/api/v2/spans"))
)
```

**Debugging Steps**:
1. **Inspect HTTP headers**:
   ```bash
   curl -v http://service-endpoint
   ```
   Ensure `traceparent` header is present.
2. **Test with a minimal service call**:
   ```java
   // Force a new span and pass it to a downstream call
   Span newSpan = tracer.spanBuilder("test").startSpan();
   try (Scope scope = newSpan.makeCurrent()) {
       // Call external service
       HttpClient.newHttpClient().sendHttpRequest(...);
   } finally {
       newSpan.end();
   }
   ```

---

### **Issue 3: High Latency Due to Tracing Overhead**
**Symptom**:
Service response time increases significantly after migration.

**Root Causes**:
- Sampling rate too low → too many spans.
- Batch exporter delays causing delays.
- Agent-side bottlenecks.

#### **Fix: Optimize Sampling & Exporter**
**Adjust Sampling Rate (Java):**
```java
// Enable probabilistic sampling (default: 100%)
TracerProvider provider = OpenTelemetrySdk.getTracerProvider();
provider.addSpanProcessor(new ProbabilitySampler(0.1)); // 10% sampling
```

**Use Async Exporter (Node.js):**
```javascript
const { AsyncSpanProcessor } = require('@opentelemetry/sdk-trace-node');

const processor = new AsyncSpanProcessor(new ZipkinExporter({ endpoint }));
provider.addSpanProcessor(processor);
```

**Debugging Steps**:
1. **Profile CPU usage** with `htop`/`jstat`.
2. **Monitor exporter queue size**:
   ```bash
   kubectl top pods  # For Kubernetes
   ```

---

### **Issue 4: Duplicate Spans**
**Symptom**:
Same operation generates multiple spans with identical IDs.

**Root Causes**:
- Duplicate instrumentation (e.g., `@opentelemetry/instrumentation-*` + manual spans).
- Library conflicts (e.g., multiple HTTP clients with tracing).

#### **Fix: Avoid Over-Instrumentation**
**Java Example:**
```java
// Disable auto-instrumentation for a specific library
otel.auto.instrumentation.http.enabled=true
otel.auto.instrumentation.http.disable_for_urls="http://unwanted-service"
```

**Python Example:**
```python
# Exclude unwanted libraries
from opentelemetry.instrumentation import http
http.disable_for_url("http://unwanted-service")
```

**Debugging Steps**:
1. **List active instrumentation**:
   ```bash
   kubectl logs <pod> | grep "AutoInstrumentation"
   ```
2. **Check for manual span leaks**:
   ```java
   // Ensure spans are properly ended
   try (Scope ignored = newSpan.makeCurrent()) {
       // Do work
   } // Span auto-ends
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|------------------------------------------------------------------------------|-----------------------------------------------|
| **OpenTelemetry SDK Logs** | Debug SDK initialization errors.                                             | `otel-service logs \| grep "ERROR"`            |
| **Jaeger Query UI**    | Check if traces exist for a specific service.                                | `jaeger query http://jaeger:16686`            |
| **Kubernetes `kubectl`** | Inspect tracing pods for crashes.                                             | `kubectl logs <tracing-agent-pod>`            |
| **Prometheus/Grafana** | Monitor tracing backend latency/storage usage.                               | `prometheus -query "otel_exporter_latency"`    |
| **Wireshark**          | Verify `traceparent` headers in network traffic.                             | `tshark -f "tcp port 8080"`                    |
| **OpenTelemetry Dump** | Manually force trace export for testing.                                     | `otel-collector dump --exporter zipkin`        |

**Advanced Debugging**:
- **Set `OTEL_PYTHON_TRACING_CONFIG`** (Python):
  ```bash
  export OTEL_PYTHON_TRACING_CONFIG='{"sampler": {"name": "always_on"}}'
  ```
- **Enable DevTools in Jaeger**:
  ```bash
  jaeger-agent --dev --collectorzipkin.http-port=9411
  ```

---

## **5. Prevention Strategies**

### **Before Migration**
✅ **Test in Staging First**
- Deploy tracing in a non-production environment to catch issues early.

✅ **Use Feature Flags**
- Enable tracing for a subset of users (e.g., 10%) before full rollout.

✅ **Benchmark Before/After**
- Measure impact on:
  - P99 latency
  - Throughput (req/sec)
  - Memory usage

### **During Migration**
✅ **Gradual Rollout**
- Use **canary releases** to avoid impacting all users at once.

✅ **Monitor Sampling**
- Start with **100% sampling** in dev → reduce to 10-50% in staging.

✅ **Validate Context Propagation**
- Write integration tests to ensure spans are correctly linked.

### **Post-Migration**
✅ **Set Up Alerts**
- Alert on:
  - High trace generation rate (possible doS via tracing).
  - Backend storage errors.
  - Missing traces (e.g., `trace_count == 0`).

✅ **Document Tracing Schema**
- Maintain an **OpenTelemetry spec** for custom attributes/spans.

✅ **Regular Audits**
- Remove unused spans/instrumentation to reduce noise.

---

## **6. Sample Debugging Workflow**
**Scenario**: *"Traces are missing for DB calls in a Spring Boot app."*

1. **Check instrumentation**:
   ```bash
   curl -I http://service:8080/health | grep "traceparent"
   ```
   → If missing, enable **Spring Boot Auto-Config**:
   ```properties
   spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
   ```

2. **Inspect logs for errors**:
   ```bash
   kubectl logs <pod> | grep "otel"
   ```
   → Look for `No active span` errors.

3. **Test manually**:
   ```java
   @Autowired
   private Tracer tracer;

   @GetMapping("/test")
   public String test() {
       Span span = tracer.spanBuilder("db-call").startSpan();
       try (Scope scope = span.makeCurrent()) {
           // Force a DB call
           jdbcTemplate.queryForList("SELECT 1");
       } finally {
           span.end();
       }
       return "OK";
   }
   ```

4. **Verify in Jaeger**:
   ![Jaeger Trace Example](https://www.jaegertracing.io/img/jaeger-ui-trace.png)
   → If still missing, check **JDBC instrumentation**:
   ```java
   DependencyInjectionInstrumentor.instrument(DriverManager.class, new JdbcInstrumentor());
   ```

---

## **7. Conclusion**
Tracing migration is **not a one-time task**—it requires:
✔ **Gradual testing**
✔ **Context-aware debugging**
✔ **Performance monitoring**

By following this guide, you can **minimize downtime, avoid trace fragmentation, and ensure your distributed systems remain observable**. Always **start small, validate thoroughly, and monitor aggressively**.

---
**Further Reading**:
- [OpenTelemetry Instrumentation Guide](https://opentelemetry.io/docs/instrumentation/)
- [Jaeger Best Practices](https://www.jaegertracing.io/docs/latest/best-practices/)
- [Sampling Strategies](https://opentelemetry.io/docs/specs/semconv/trace/sampling/#sampling-strategies)