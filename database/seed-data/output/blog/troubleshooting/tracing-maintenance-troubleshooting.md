# **Debugging *Tracing Maintenance*: A Practical Troubleshooting Guide**

## **Introduction**
Distributed tracing (e.g., OpenTelemetry, Jaeger, Zipkin) is essential for diagnosing latency, errors, and performance bottlenecks in microservices. However, tracing systems can degrade over time due to misconfigurations, resource exhaustion, or environment changes. This guide helps you identify, diagnose, and resolve common tracing-related issues.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to confirm tracing-related problems:

| **Symptom**                          | **Possible Cause**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------------|
| Requests appear to hang indefinitely  | Unbounded tracing spans, slow sampler, or collector overload                      |
| High CPU/memory usage in tracer/agent | Traces being too verbose, inefficient sampling, or no sampling                     |
| Corrupted/partial traces              | Network issues between client → collector, serialization errors, or timeouts      |
| Slow query performance in tracing UI  | Querying improperly filtered traces, no downsampling, or slow backend analysis    |
| Missing critical spans                | Excluded components, incorrect instrumentation, or sampling rate too low           |
| Tracing-breaking deploys              | Incompatible OpenTelemetry versions, missing auto-instrumentation libraries        |

---

## **2. Common Issues & Fixes**
### **Issue 1: Unbounded Trace Collection (CPU/Memory Spikes)**
**Problem:**
A poorly configured sampler (e.g., `AlwaysOnSampler`) or missing sampling causes excessive trace volume, overwhelming collectors.

**Diagnosis:**
- Check metrics: `otel_collector_span_count` (Prometheus) or Jaeger’s "Spans" chart.
- Look for sudden spikes in CPU/memory on collectors or tracing UIs.

**Fix:**
Configure a **sampling strategy** (e.g., parent-based, probabilistic, or tail sampling):
```yaml
sampler:
  type: parentbased_1000
  # OR
  type: probabilistic
  parameter: 0.1  # Sample 10% of traces
```
**Apply to collector config (`config.yaml`):**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        tracing:
          sampler:
            type: probabilistic
            parameter: 0.1
```

---

### **Issue 2: Timeouts in Collector or Backend**
**Problem:**
Traces take >30s to process due to slow aggregation or network bottlenecks.

**Diagnosis:**
- Check collector logs for `timeout` or `retry` errors.
- Monitor latency metrics (`otel_collector_processing_latencies`).

**Fix:**
- Reduce batch interval (default: 5s):
  ```yaml
  exporters:
    jaeger:
      endpoint: jaeger-collector:14250
      tls:
        insecure: true
      batch:
        timeout: 2s  # Lower than default
  ```
- Use **downsampling** (e.g., `downsample` exporter):
  ```yaml
  exporters:
    jaeger:
      downsample:
        strategy: linear
        factor: 1000
  ```

---

### **Issue 3: Missing Spans in Traces**
**Problem:**
Critical operations appear unreported in traces.

**Diagnosis:**
- Verify instrumentation exists (e.g., auto-instrumentation libraries loaded).
- Check if spans are marked `Recorded` in Jaeger’s UI.

**Fix:**
- Explicitly scope spans in code:
  ```python
  # OpenTelemetry Python example
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)

  with tracer.start_as_current_span("fetch_user"):
      user = fetch_user_from_db(user_id)
  ```
- Ensure auto-instrumentation is active (e.g., `opentelemetry-contrib`):
  ```bash
  curl -o opentelemetry-contrib-instrumentation.sh https://raw.githubusercontent.com/open-telemetry/opentelemetry-contrib/main/instrumentation/nodejs/otel-nodejs-instrumentation.sh
  chmod +x opentelemetry-contrib-instrumentation.sh
  ./otel-nodejs-instrumentation.sh
  ```

---

### **Issue 4: Corrupted/Partial Traces**
**Problem:**
Traces arrive malformed or truncated (e.g., missing attributes).

**Diagnosis:**
- Logs show `SerializationError` in collector.
- Jaeger UI shows "no data" for certain components.

**Fix:**
- Validate schema compliance (e.g., use `opentelemetry-proto`):
  ```go
  // Ensure spans are properly serialized
  span := trace.SpanFromContext(ctx)
  span.SetAttributes(
      attribute.String("key", "value"),
  )
  ```
- Enable **trace validation** in OpenTelemetry Collector:
  ```yaml
  processors:
    batch:
      timeout: 1s
    validator:  # Adds validation step
      check_exporter_batches: true
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Quick Fixes**                                                                 |
|-------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **OpenTelemetry Collector Metrics** | Monitor `otel_collector_*` (CPU, memory, processing time)                    | Adjust `batch/timeout` or scale collectors                                    |
| **Jaeger Query API**    | Check `http://jaeger-query:16686/search` for missing traces                 | Verify sampling, retry queries with `maxDuration`                            |
| **gRPC Tracing**        | Debug `opentelemetry-collector` ↔ exporter communication                   | Use `grpc-health-probe`; check for `UNIMPLEMENTED` errors                     |
| **OpenTelemetry SDK Logs** | Inspect `tracer`/`span` lifecycle issues                                    | Add debug logs to SDK (e.g., `os.Setenv("OTEL_LOG_LEVEL", "DEBUG")`)          |

**Example: Debugging Jaeger Query**
```bash
# Test query manually
curl "http://jaeger-query:16686/api/traces?service=my-service&start=now-1h"
```
**If empty:**
1. Check collector logs for `404 Not Found`.
2. Ensure `jaeger-ingester` is running:
   ```bash
   kubectl logs jaeger-ingester-pod
   ```

---

## **4. Prevention Strategies**
### **A. Auto-Scaling for Tracing**
Configure **HPA (Horizontal Pod Autoscaler)** for collectors:
```yaml
# Example: Scale Jaeger collector based on CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: jaeger-collector-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: jaeger-collector
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

### **B. Sampling Policies by Service**
- **Egress sampling** (per-service rate limits):
  ```yaml
  receivers:
    otlp:
      protocols:
        grpc:
          tracing:
            sampler:
              type: head
              sampling_strategy:
                - service_name: auth-service
                  encoding: custom
                  parameters:
            parameters:
              target: 1000  # 1k spans/sec
  ```
- **Downsampling** for UI:
  ```yaml
  exporters:
    prometheus:
      endpoint: "0.0.0.0:8888"
    jaeger:
      downsample:
        strategy: linear
        offset: 0.5
        factor: 1000
  ```

### **C. Circuit Breakers & Retries**
Add **exponential backoff** for failed exports:
```yaml
exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    retry:
      enabled: true
      initial_interval: 1s
      multiplier: 2.0
      max_interval: 30s
```

---

## **Final Checklist for Resolution**
1. **Verify sampling rates** (`AlwaysOn` → `Probabilistic/Parent-Based`).
2. **Check collector metrics** (`otel_collector_span_count`, `processing_duration`).
3. **Inspect backend logs** (Jaeger, Prometheus, collector).
4. **Test traces manually** via `curl` or UI.
5. **Replicate in staging** before applying fixes.

---
**Pro Tip:** Use **OpenTelemetry’s `opentelemetry-collector-contrib`** for additional processors (e.g., `tail_sampling` for cost savings). Always validate fixes in a **non-production environment** first.