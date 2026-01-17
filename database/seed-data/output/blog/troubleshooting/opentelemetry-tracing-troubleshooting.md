# **Debugging OpenTelemetry Tracing: A Troubleshooting Guide**

OpenTelemetry (OTel) tracing enables distributed tracing across microservices, helping you identify bottlenecks, latency issues, and missing context propagation. However, misconfigurations, tooling issues, or incorrect instrumentations can lead to incomplete or missing traces. This guide provides a structured approach to diagnosing and resolving common OpenTelemetry Tracing problems.

---

## **1. Symptom Checklist**
Before diving into fixes, verify the following symptoms to narrow down the issue:

### **A. Trace Data Issues**
- [ ] No traces appear in Jaeger/Zipkin/OTLP collector.
- [ ] Traces are incomplete (missing spans or payload).
- [ ] Trace IDs appear in logs but are missing in tracing tools.
- [ ] Context propagation fails across services (e.g., headers lost in HTTP calls).

### **B. Performance & Latency Issues**
- [ ] Slow database queries are not visible in traces.
- [ ] End-to-end latency is higher than expected.
- [ ] Spans for specific services are missing or delayed.

### **C. Tooling & Configuration Problems**
- [ ] OTel Collector logs show errors during ingestion.
- [ ] Auto-instrumentation (e.g., OpenTelemetry Operator) fails.
- [ ] Custom SDKs (e.g., `opentelemetry-java`, `opentelemetry-go`) crash or log warnings.

---

## **2. Common Issues & Fixes**

### **Issue 1: No Traces in Backend (Collector/Backend Not Receiving Data)**
**Symptoms:**
- No spans in Jaeger/Zipkin despite running instrumentation.
- OTel Collector logs show `EINVAL` or `connection refused` errors.

**Root Cause:**
- Incorrect OTLP exporter configuration.
- Firewall/network blocking OTLP endpoints.
- Collector not running or misconfigured.

**Fix (OTLP Collector Example):**
```yaml
# Example: OTLP Collector Config (reloadding config)
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:
  logging:  # For debugging
    loglevel: debug
  jaeger:
    endpoint: "jaeger-collector:14250"
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging, jaeger]
```
**Checklist:**
- Verify OTel Collector logs: `journalctl -u otel-collector -f`
- Test connectivity: `nc -zv jaeger-collector 14250`
- Ensure `tracing.yml` is correct and reloaded (`curl -XPOST http://localhost:4318/v1/config`).

---

### **Issue 2: Missing Context Propagation (e.g., Missing Trace ID in HTTP Calls)**
**Symptoms:**
- Spans in one service, but next service has no trace context.
- Logs show `WARN: TraceContext not found`.

**Root Cause:**
- Missing `B3` or `W3C` header propagation.
- Incorrect auto-instrumentation settings.

**Fix (Java SDK Example):**
```java
// Ensure Context Propagation is Enabled
TracerProvider provider = SdkTracerProvider.builder()
    .addSpanProcessor(BatchSpanProcessor.builder(exporter).build())
    .setContextPropagationBytesFormat(ContextPropagation.B3_FORMAT) // or W3C
    .build();

// For HTTP Clients (Spring Boot Example)
@Bean
public TracingConfigurer tracingConfigurer() {
    return TracingConfigurer.builder()
            .propagationFormat(ContextPropagation.B3_SIMPLE)
            .build();
}
```
**Checklist:**
- Verify headers in HTTP requests (`curl -v` or browser DevTools).
- Use `otelcontext` to debug propagation:
  ```sh
  kubectl logs <pod> | grep -i "context"
  ```

---

### **Issue 3: Slow or Missing Database Queries in Traces**
**Symptoms:**
- Database spans are missing from traces.
- SQL latency not visible in tracing UI.

**Root Cause:**
- Instrumentation not applied to DB client.
- Custom SQL queries are not auto-instrumented.

**Fix (Java JPA/Hibernate Example):**
```java
// Database Auto-Instrumentation (OpenTelemetry Auto-Instrumentation)
javaagent:/path/to/opentelemetry-javaagent.jar \
    -javaagent:/path/to/opentelemetry-auto-instrumentation-all.jar \
    -Dotel.service.name=my-service \
    -Dotel.auto-instrumentations.enabled=true \
    -Dotel.auto-instrumentations.hibernatesession.enabled=true \
    -Dotel.auto-instrumentations.jpa.enabled=true
```
**Checklist:**
- Verify DB spans in Jaeger:
  ![Jaeger DB Query Span Example](https://jaeger-io.github.io/jaeger/latest/img/jaeger-ui-query-filters.png)
- Manually add span for uninstrumented queries:
  ```java
  Span span = tracer.spanBuilder("custom-sql-query").startSpan();
  try (SQLContext context = tracer.withSpanContext(span.context())) {
      // Execute query
  } finally {
      span.end();
  }
  ```

---

### **Issue 4: Auto-Instrumentation Failing**
**Symptoms:**
- Auto-instrumentation agent crashes on startup.
- Logs show `ClassNotFoundException` for agent classes.

**Root Cause:**
- Incorrect agent version.
- Conflicting dependencies (e.g., wrong `hibernate` or `spring-boot-starter-data-jpa` version).

**Fix (Kubernetes Auto-Instrumentation Example):**
```yaml
# OpenTelemetry Operator + Auto-Instrumentation
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
spec:
  mode: deployment
  config:
    receivers:
      otlp:
        protocols:
          grpc:
          http:
    processors:
      batch:
    exporters:
      jaeger:
        endpoint: "jaeger-collector:14250"
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [batch]
          exporters: [jaeger]

---
# Auto-Instrumentation Sidecar
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: java-instrumentation
spec:
  propagations:
    - tracecontext
    - baggage
---
```

**Checklist:**
- Verify logs: `kubectl logs <instrumentation-pod> | grep -i "instrument"`
- Ensure `auto-instrumentation-all` is up-to-date:
  ```sh
  docker pull ghcr.io/open-telemetry/opentelemetry-auto-instrumentation-all:latest
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Key Tools**
| Tool | Purpose | Command/Usage |
|------|---------|--------------|
| **OTel Collector Logs** | Debug ingestion issues | `journalctl -u otel-collector -f` |
| **Jaeger CLI** | Query traces | `jaeger query --service-name=app --limit=1` |
| **OTel Collector Metrics** | Check exporter health | `prometheus query otel_collector_exporter_jaeger_span_processed_total` |
| **Wireshark/tcpdump** | Inspect OTLP traffic | `tcpdump -i eth0 -w otel.pcap port 4317` |

### **B. Debugging Techniques**
1. **Enable Debug Logging**
   ```yaml
   exporters:
     logging:
       loglevel: debug  # Add to Collector config
   ```
2. **Check Trace ID Propagation**
   ```sh
   curl -H "traceparent: 00-abc123..." http://service:port/api
   ```
3. **Manually Inject Spans**
   ```java
   tracer.inSpanBuilder("manual-span")
       .setAttribute("example.key", "example.value")
       .startSpan()
       .end();
   ```
4. **Use OpenTelemetry Python CLI**
   ```sh
   otel-collector-contrib \
     --config /path/to/config.yaml \
     --enable-debug
   ```

---

## **4. Prevention Strategies**

### **A. Best Practices for Stable Traces**
1. **Enable Auto-Instrumentation Early**
   - Use `opentelemetry-javaagent` in CI/CD pipelines.
   - Example Dockerfile:
     ```dockerfile
     RUN apt-get install -y ca-certificates && \
         mkdir -p /etc/ssl/certs && \
         curl -o /etc/ssl/certs/ca-certificates.crt https://curl.se/ca/cacert.pem && \
         docker run -e JAVA_OPTS="-javaagent:/path/to/opentelemetry-javaagent.jar" my-app
     ```
2. **Validate Context Propagation**
   - Test with `curl` or Postman:
     ```sh
     curl -H "traceparent: 00-abc123..." -H "baggage: key=value" http://service/api
     ```
3. **Monitor OTel Collector Health**
   - Set up Prometheus alerts for:
     - `otel_collector_exporter_jaeger_span_processed_total` (dropped spans)
     - `otel_collector_processor_batch_enqueued_spans` (backpressure)
4. **Use Resource Attributes**
   - Tag spans with environment, version, and deployment:
     ```java
     TracerProvider.builder()
         .addResource(Resource.getDefault()
             .toBuilder()
             .put("service.version", "1.2.3")
             .put("deployment.env", "prod")
             .build())
         .build();
     ```

### **B. Testing Strategies**
1. **Unit Test Span Propagation**
   ```java
   @Test
   public void testContextPropagation() {
       Span span = tracer.builder("test").startSpan();
       try (Context ignored = tracer.withSpanContext(span.context())) {
           assertNotNull(MDC.get("traceparent"));
       } finally {
           span.end();
       }
   }
   ```
2. **Chaos Testing**
   - Kill OTel Collector and verify recovery.
   - Simulate network drops between services.

---

## **Final Checklist for Resolution**
| Task | Verified? |
|------|-----------|
| ✅ OTel Collector running & healthy | [] |
| ✅ Context propagation working (headers) | [] |
| ✅ Database queries instrumented | [] |
| ✅ Auto-instrumentation logs clean | [] |
| ✅ Traces appear in Jaeger/Zipkin | [] |

By following this guide, you should be able to diagnose and resolve most OpenTelemetry tracing issues efficiently. If problems persist, consult the [OpenTelemetry Community Slack](https://open-telemetry.slack.com/) or [GitHub Issues](https://github.com/open-telemetry/opentelemetry-collector/issues).