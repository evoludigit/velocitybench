# **Debugging Tracing Setup: A Troubleshooting Guide**

## **Introduction**
Tracing is a critical component in modern distributed systems, enabling observability, performance analysis, and debugging. A well-implemented tracing setup helps identify latency bottlenecks, track request flows, and resolve issues across microservices. However, misconfigurations or implementation flaws can lead to degraded performance, incorrect traces, or complete tracing failures.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving common issues in tracing setups.

---

## **1. Symptom Checklist**
Before diving into debugging, verify if tracing-related symptoms match the following:

### **General Tracing Issues**
| Symptom | Description |
|---------|------------|
| **No traces appear in tracing backend (e.g., Jaeger, Zipkin, OpenTelemetry Collector)** | Tracing instrumentation may not be working, or spans are not being sent. |
| **Incomplete or missing spans** | Only partial traces are visible, indicating some spans are dropped or incorrectly propagated. |
| **High latency in trace generation** | Excessive time taken to process traces, suggesting backend or SDK misconfigurations. |
| **Duplicate traces or spans** | Traces contain redundant entries, often due to incorrect context propagation. |
| **Tracing errors in logs** | SDK or instrumentation errors (e.g., `Cannot acquire tracer`) suggest misconfiguration. |
| **High disk/CPU usage** | Tracing backend (e.g., Jaeger) consumes excessive resources, indicating misconfigured retention or sampling. |
| **Race conditions in distributed tracing** | Spans appear out of order or missing due to improper context handling. |

### **Environment-Specific Symptoms**
| Environment | Symptom |
|-------------|---------|
| **Local Development** | No traces appear in local collectors (e.g., `localhost:16686`). |
| **Containerized (Kubernetes)** | Traces not appearing in observability tools (e.g., Grafana Tempo + Loki). |
| **Cloud-Native (AWS/GCP)** | Traces not routed to cloud-based backends (e.g., AWS X-Ray). |
| **Legacy Monolithic Apps** | Tracing spans only capturing part of the request flow. |

**Next Step:** If symptoms match, proceed to **Common Issues & Fixes**.

---

## **2. Common Issues and Fixes**

### **Issue 1: Traces Not Appearing in the Backend**
**Symptoms:**
- Jaeger/Zipkin/OTel Collector shows no traffic.
- Logs contain warnings like:
  ```
  Failed to send span: connection refused (or timeout)
  ```

**Root Causes & Fixes:**
#### **A. Incorrect Tracer Provider Configuration**
- **Problem:** The tracer provider is not initialized correctly, or the exporter is misconfigured.
- **Fix:**
  ```go
  // Correct: Properly initialize TracerProvider with an exporter
  func main() {
      tp := sdk.NewTracerProvider(
          sdk.WithBatcher(
              exporter.NewZipkin(
                  exporter.WithEndpoint("http://zipkin-collector:9411/api/v2/spans"), // Ensure correct endpoint
              ),
          ),
      )
      sdk.SetGlobalTracerProvider(tp)
      defer func() { _ = tp.Shutdown(context.Background()) }()
      // Start application
  }
  ```
  - **Key Fixes:**
    - Verify the exporter endpoint (e.g., `http://zipkin-collector:9411`).
    - Ensure the collector service is running (`docker ps | grep zipkin`).

#### **B. Network/Firewall Blocking Exports**
- **Problem:** The tracer cannot reach the backend due to network restrictions.
- **Fix:**
  ```bash
  # Test connectivity
  curl -v http://zipkin-collector:9411/api/v2/spans
  ```
  - If blocked, adjust **Kubernetes Service Rules** or **cloud security groups**.
  - Example (Kubernetes):
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata:
      name: allow-tracing
    spec:
      podSelector: {}
      policyTypes:
      - Egress
      egress:
      - to:
        - podSelector:
            matchLabels:
              app: zipkin-collector
        ports:
        - protocol: TCP
          port: 9411
    ```

#### **C. Collector Not Running or Misconfigured**
- **Problem:** The tracing backend (e.g., Jaeger collector) is down or improperly configured.
- **Fix:**
  - Check collector logs:
    ```bash
    docker logs jaeger-collector
    ```
  - Verify `jaeger-collector` is receiving traffic:
    ```bash
    kubectl port-forward svc/jaeger-collector 14268:14268  # Check if API is reachable
    ```

---

### **Issue 2: Incomplete or Missing Spans**
**Symptoms:**
- Some services generate traces, but others don’t.
- Logs show:
  ```
  Span context not found (or invalid)
  ```

**Root Causes & Fixes:**
#### **A. Improper Span Context Propagation**
- **Problem:** HTTP headers (e.g., `traceparent`) are not passed correctly between services.
- **Fix (Node.js Example):**
  ```javascript
  const { trace } = require('@opentelemetry/sdk-trace-node');
  const { registerInstrumentations } = require('@opentelemetry/instrumentation');
  const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');

  const tracer = new trace.TracerProvider();
  tracer.addSpanProcessor(new trace.SimpleSpanProcessor(new trace.ConsoleSpanExporter()));
  trace.setGlobalTracerProvider(tracer);

  // Ensure HTTP headers are propagated
  const httpInstrumentation = new HttpInstrumentation();
  registerInstrumentations({ instrumentations: [httpInstrumentation] });

  // Example: Express middleware to ensure headers are set
  app.use((req, res, next) => {
    const { traceparent } = req.headers;
    if (traceparent) {
      const spanContext = trace.SpanContext.fromTraceparent(traceparent);
      trace.setSpan(req[trace.SPAN_CONTEXT_KEY], spanContext);
    }
    next();
  });
  ```
  - **Key Fixes:**
    - Use **OTel’s built-in HTTP instrumentation** (e.g., `express-otel`).
    - Manually propagate `traceparent` in non-HTTP contexts (e.g., gRPC).

#### **B. Manual Span Creation Without Context**
- **Problem:** New spans are created without attaching the parent context.
- **Fix:**
  ```go
  // Bad: Missing context
  _, span := tp.Tracer("bad-service").Start(context.Background(), "operation")

  // Good: Using parent context
  ctx := context.WithValue(req.Context(), trace.SpanContextKey, spanContext)
  _, span := tp.Tracer("good-service").Start(ctx, "operation")
  ```

---

### **Issue 3: High Latency in Trace Generation**
**Symptoms:**
- Traces appear delayed (e.g., spans take minutes to appear in Jaeger).
- Backpressure in the collector (high `queue` or `buffer` errors).

**Root Causes & Fixes:**
#### **A. Collector Buffer/Queue Overflow**
- **Problem:** Too many spans cause the collector to slow down.
- **Fix:**
  ```yaml
  # Jaeger collector config (reducing batch size)
  collector:
    zipkin:
      http:
        endpoint: "0.0.0.0:9411"
    batch:
      send_batch_size: 1000  # Reduce batch size
      timeout: 5s           # Adjust timeout
  ```
  - **Alternative:** Use **sampling** to reduce load:
    ```go
    tp := sdk.NewTracerProvider(
        sdk.WithSampler(sdk.NewProbabilitySampler(0.1)), // Sample 10%
    )
    ```

#### **B. Slow Exporter (e.g., File-Based)**
- **Problem:** Writing traces to disk is slow.
- **Fix:** Use a **network-backed collector** (e.g., Jaeger All-In-One) instead of file storage.

---

### **Issue 4: Duplicate Spans**
**Symptoms:**
- The same trace appears multiple times in Jaeger.
- Logs show:
  ```
  Duplicate span ID detected
  ```

**Root Causes & Fixes:**
#### **A. Multiple Tracer Instances**
- **Problem:** Different tracer providers are active simultaneously.
- **Fix:**
  ```go
  // Ensure a single global tracer provider
  func init() {
      tp := sdk.NewTracerProvider(/* config */)
      sdk.SetGlobalTracerProvider(tp)
      // No other tracer providers should be created
  }
  ```

#### **B. Manual Span Creation Without Unique IDs**
- **Problem:** Spans are not properly linked via `traceID`.
- **Fix:** Always use `context.WithSpan()` to attach parent spans:
  ```go
  parentSpan := /* existing span */
  ctx := context.WithSpan(ctx, parentSpan)
  _, childSpan := tp.Tracer("child-service").Start(ctx, "operation")
  ```

---

### **Issue 5: Race Conditions in Distributed Tracing**
**Symptoms:**
- Spans appear out of order.
- Missing intermediate steps in the trace.

**Root Causes & Fixes:**
#### **A. Context Lost in Async Operations**
- **Problem:** A goroutine loses the `spanContext` after forking.
- **Fix (Go):**
  ```go
  // Bad: Passing bare context
  go func() {
      _, span := tp.Tracer("worker").Start(context.Background(), "async-op")
      span.End()
  }()

  // Good: Passing full context with span
  ctx := context.WithSpan(ctx, span)
  go func(ctx context.Context) {
      _, newSpan := tp.Tracer("worker").Start(ctx, "async-op")
      defer newSpan.End()
  }(ctx)
  ```

#### **B. Improper gRPC Interceptor Setup**
- **Problem:** gRPC spans are not properly linked.
- **Fix:**
  ```go
  // Correct gRPC interceptor setup
  grpcServer.Interceptors(
      otelgrpc.NewServerInterceptor(
          otelgrpc.WithTracerProvider(tp),
      ),
  )
  ```

---

## **3. Debugging Tools and Techniques**

### **A. Logging and SDK Debugging**
- Enable **verbose logging** in tracing SDKs:
  ```go
  // OpenTelemetry Go
  log.SetLevel(log.LevelDebug)
  ```
  - Check for errors like:
    - `failed to send span`
    - `invalid traceparent header`

- **OTel CLI Debugging:**
  ```bash
  # Test trace generation locally
  curl -H "traceparent: 00-<trace-id>-<span-id>-01" http://your-service/api
  ```

### **B. Network Debugging**
- **Check Collector Reachability:**
  ```bash
  telnet zipkin-collector 9411  # Should connect
  ```
- **Capture HTTP Traffic:**
  ```bash
  nc -lvnp 9411  # Manually forward traces
  ```

### **C. Observability Tools**
| Tool | Purpose |
|------|---------|
| **Jaeger Query UI** | Inspect traces in real-time. |
| **OTel Collector Metrics** | Check `span_processed_total` and `export_failed_total`. |
| **Kubernetes `kubectl logs`** | Inspect collector/pod logs. |
| **Prometheus + Grafana** | Monitor tracing pipeline health. |

### **D. Unit Testing Tracing**
- **Mock Tracer Provider:**
  ```go
  type MockTracer struct{}
  func (m *MockTracer) Start(ctx context.Context, name string) (context.Context, otel.Tracer) {
      return context.WithValue(ctx, "test-key", "mock-span"), m
  }
  ```
- **Test Trace Propagation:**
  ```go
  func TestSpanPropagation(t *testing.T) {
      ctx := context.WithValue(context.Background(), trace.SpanContextKey, spanContext)
      req, _ := http.NewRequest("GET", "http://example.com", nil)
      req = req.WithContext(ctx)
      // Verify headers are set
      assert.Equal(t, spanContext.TraceID(), req.Header.Get("traceparent"))
  }
  ```

---

## **4. Prevention Strategies**

### **A. Best Practices for Tracing Setup**
1. **Use a Single Tracer Provider**
   - Avoid multiple `TracerProvider` instances (leads to duplicates).
   ```go
   var globalTP = sdk.NewTracerProvider(/* config */)
   sdk.SetGlobalTracerProvider(globalTP)
   ```

2. **Enable AutoInstrumentation**
   - Use **auto-instrumentation libraries** (e.g., `opentelemetry-auto-instrumentation-nodejs`) to reduce manual setup.

3. **Configure Proper Sampling**
   - Adjust sampling rate based on workload:
     ```go
     tp := sdk.NewTracerProvider(
         sdk.WithSampler(sdk.NewProbabilitySampler(0.5)), // 50% sampling
     )
     ```

4. **Validate Trace Context Propagation**
   - Test across service boundaries:
     ```bash
     # Use `curl` to inject trace headers
     curl -H "traceparent: 00-<trace-id>-<span-id>-01" http://service-a/api
     ```

5. **Monitor Tracing Pipeline Health**
   - Set up alerts for:
     - `export_failed_total > 0` (Prometheus alert).
     - High latency in span processing.

### **B. Infrastructure Considerations**
- **Collector Resource Limits:**
  - Allocate sufficient CPU/memory for collectors (e.g., Jaeger):
    ```yaml
    resources:
      limits:
        cpu: "1"
        memory: "2Gi"
    ```
- **Retention Policies:**
  - Configure trace retention (e.g., 7 days) to avoid disk issues:
    ```yaml
    storage:
      local:
        path: "/var/jaeger/storage"
        trace_storage:
          max_segments: 100
          segment_size_mib: 10
    ```
- **Network Policies:**
  - Ensure collectors can reach each other (e.g., in Kubernetes).

### **C. CI/CD Integration**
- **Automated Tracing Validation:**
  - Add a linting step to check for:
    - Missing `traceparent` headers.
    - Incorrect span context propagation.
- **Example GitHub Action:**
  ```yaml
  - name: Test Tracing
    run: |
      curl -H "traceparent: 00-<trace-id>-<span-id>-01" http://localhost:3000/api
      # Verify response contains expected trace IDs
  ```

---

## **5. Summary Checklist for Tracing Debugging**
| Step | Action |
|------|--------|
| **1** | Verify traces appear in the backend (Jaeger/Zipkin). |
| **2** | Check collector logs and network connectivity. |
| **3** | Inspect SDK logs for errors (`export_failed_total`, `invalid traceparent`). |
| **4** | Test trace propagation manually (`curl` with `traceparent`). |
| **5** | Enable sampling to reduce load if needed. |
| **6** | Validate context handling in async operations. |
| **7** | Set up alerts for tracing pipeline health. |

---

## **6. Final Notes**
- **Start Small:** Begin with a single service, then scale.
- **Use OpenTelemetry:** It’s the industry standard for cross-language tracing.
- **Document Your Setup:** Keep tracing configuration in a `README` or Git repo.

By following this guide, you should be able to **quickly identify and resolve** tracing-related issues, ensuring your observability pipeline remains reliable.