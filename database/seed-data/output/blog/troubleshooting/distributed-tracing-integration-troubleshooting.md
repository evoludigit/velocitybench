# **Debugging Distributed Tracing Integration: A Troubleshooting Guide**

## **Introduction**
Distributed tracing is a critical tool for observing microservices architectures, identifying performance bottlenecks, and debugging latency issues. When OpenTelemetry (OTel) or Jaeger integration fails, it can disrupt observability, making troubleshooting distributed systems far harder.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving common distributed tracing issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify which symptoms match your issue:

| **Symptom**                                  | **Likely Cause**                          |
|---------------------------------------------|-------------------------------------------|
| No traces appear in Jaeger/OTel Collector   | Instrumentation not working (missing spans). |
| Incomplete traces (missing contexts)        | Sampling rate too low or context propagation failure. |
| High latency in trace processing           | Backend bottleneck (OTel Collector, Jaeger Query). |
| Spans missing key attributes (e.g., `service.name`) | Incorrect auto-instrumentation or manual instrumentation issues. |
| Tracing works in dev but fails in production | Environment misconfiguration (agents, exporters, etc.). |
| High CPU/memory usage in tracing stack      | Overhead from excessive spans or inefficient sampling. |

---

## **2. Common Issues & Fixes**

### **2.1. Missing Traces in Jaeger/OTel Collector**
**Symptom:** No traces appear in Jaeger, despite instrumentation being present.

#### **Root Causes & Fixes**
1. **Incorrect Exporter Configuration**
   - Ensure the OpenTelemetry SDK is configured to export spans to the correct backend (Jaeger, OTel Collector, etc.).
   - **Example (Python with `opentelemetry-sdk`):**
     ```python
     from opentelemetry import trace
     from opentelemetry.sdk.trace import TracerProvider
     from opentelemetry.sdk.trace.export import (
         BatchSpanProcessor,
         ConsoleSpanExporter,
         JaegerExporter,
     )

     # Configure Jaeger exporter (replace with your Jaeger agent URL)
     jaeger_exporter = JaegerExporter(
         endpoint="http://localhost:14268/api/traces",
         service_name="my-service"
     )

     # Set up trace provider
     provider = TracerProvider()
     processor = BatchSpanProcessor(jaeger_exporter)
     provider.add_span_processor(processor)
     trace.set_tracer_provider(provider)
     ```
   - **Common Mistake:** Forgetting to add the exporter to the `SpanProcessor`.

2. **Network/Connectivity Issues**
   - Verify that the service can reach the Jaeger agent/OTel Collector.
   - **Check:**
     ```sh
     curl http://<jaeger-agent>:14268/api/traces  # Should return OK
     ```
   - If behind a proxy/firewall, ensure outbound traffic is allowed.

3. **Resource Name Misconfiguration**
   - If using Kubernetes, ensure `service.name` is correctly set (default: pod name).
   - **Fix:** Override in code:
     ```python
     tracer = trace.get_tracer(__name__)
     with tracer.start_as_current_span("test-span") as span:
         span.set_attribute("service.name", "my-custom-service")
     ```

---

### **2.2. Incomplete or Missing Context Propagation**
**Symptom:** Traces show partial requests (e.g., only the first microservice).

#### **Root Causes & Fixes**
1. **Context Not Propagated Between Services**
   - HTTP headers (`traceparent`, `tracestate`) must be passed.
   - **Check:** Use `curl -v` to inspect headers:
     ```sh
     curl -v -H "traceparent: 00-<trace-id>-<span-id>-01" http://your-api
     ```
   - **Fix in Code (Python):**
     ```python
     from opentelemetry import trace
     from opentelemetry.propagate import set_global_textmap

     # Ensure headers are propagated
     set_global_textmap(lambda ctx, key, val: ctx.set(key, val), lambda ctx, key: ctx.get(key))
     ```

2. **Sampling Rate Too Low**
   - If traces are dropped due to sampling, increase the rate.
   - **Example (OTel Collector):**
     ```yaml
     # In otel-collector-config.yml
    receivers:
       otlp:
         protocols:
           grpc:
             sampling:
               initial: 1.0  # Accept all traces initially
     ```

---

### **2.3. High Latency in Trace Processing**
**Symptom:** Traces appear delayed (minutes/hours) or take long to query.

#### **Root Causes & Fixes**
1. **OTel Collector Backlog**
   - If the collector is overwhelmed, adjust batch settings.
   - **Fix:**
     ```yaml
     processors:
       batch:
         timeout: 1s  # Reduce batching delay
         send_batch_size: 1000
     ```

2. **Jaeger Query Backend Slow**
   - Jaeger’s Cassandra/Elasticsearch backend may need optimization.
   - **Check Jaeger Query Logs:**
     ```sh
     docker logs jaeger-query
     ```
   - **Temporary Workaround:** Reduce query timeouts (in `jaeger-query` config).

---

### **2.4. Missing Required Attributes**
**Symptom:** Spans lack critical metadata (e.g., `status`, `error` flags).

#### **Root Causes & Fixes**
1. **Auto-Instrumentation Not Properly Configured**
   - Ensure OpenTelemetry auto-instrumentation is enabled.
   - **Example (Docker):**
     ```sh
     docker run -e OTEL_SERVICE_NAME=my-service -e OTEL_TRACES_EXPORTER=jaeger jaegertracing/all-in-one:latest
     ```

2. **Manual Instrumentation Errors**
   - Check for missing `set_status()` or `set_attribute()` calls.
   - **Fix:**
     ```python
     if error_occurred:
         span.set_status(StatusCode.ERROR, "Request failed")
         span.record_exception(exception)
     ```

---

### **2.5. Resource Exhaustion (High CPU/Memory)**
**Symptom:** Tracing stack consumes excessive resources.

#### **Root Causes & Fixes**
1. **Too Many Spans Generated**
   - Reduce instrumentation granularity or use sampling.
   - **Fix:**
     ```yaml
     # OTel Collector sampling
     sampling:
       decision_wait: 100ms
       sampling_interval: 10s
     ```

2. **OTel Collector Config Too Aggressive**
   - Limit batch sizes and reduce memory usage.
   - **Fix:**
     ```yaml
     processors:
       memory_limiter:
         limit_mib: 2000  # Limit to 2GB
     ```

---

## **3. Debugging Tools & Techniques**

### **3.1. Log-Based Debugging**
- **Check OTel Collector Logs:**
  ```sh
  docker logs otel-collector
  ```
- **Enable Debug Logging in Code:**
  ```python
  import logging
  logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
  ```

### **3.2. Jaeger UI Inspection**
- Use the Jaeger UI to:
  - Verify if traces exist (`/search`).
  - Check for missing service names or incorrect service tags.
  - Inspect span durations and error rates.

### **3.3. Network Debugging**
- **Capture HTTP Headers:**
  ```sh
  docker run -it --rm -p 8080:8080 wireshark/wireshark  # Inspect traffic
  ```
- **Use `curl` with Verbose Mode:**
  ```sh
  curl -v -H "traceparent: 00-<trace-id>-..." http://your-service
  ```

### **3.4. Metrics-Based Validation**
- Check if spans are being received:
  ```sh
  # If using Prometheus/OTel Collector metrics
  curl http://localhost:8888/metrics | grep span_count
  ```

---

## **4. Prevention Strategies**
1. **Automated Instrumentation Testing**
   - Use **OpenTelemetry’s validation tools** to ensure spans are properly emitted.
   - Example:
     ```sh
     otelcol-contrib test
     ```

2. **Environment Parity**
   - Ensure tracing works the same in dev/staging/prod (e.g., mock Jaeger in tests).

3. **Sampling Rate Tuning**
   - Start with `100%` sampling in production, then adjust based on load.

4. **Regular Trace Review**
   - Monitor for anomalies in trace duration or error rates.

---

## **5. Quick Reference Table**
| **Issue**               | **Diagnostic Command**                     | **Fix**                          |
|-------------------------|--------------------------------------------|----------------------------------|
| No traces in Jaeger     | `curl http://jaeger-agent:14268/api/traces`| Check exporter config            |
| Missing context         | `curl -v -H "traceparent: ..."`           | Fix propagator in code           |
| High latency            | `docker logs jaeger-query`                | Optimize OTel Collector batching |
| Missing attributes      | Inspect Jaeger UI traces                  | Add `set_attribute()` calls      |

---

## **Conclusion**
Distributed tracing failures often stem from **misconfigurations, network issues, or sampling problems**. By following this guide, you can quickly identify and resolve common tracing issues while ensuring observability remains intact.

**Key Takeaways:**
✅ **Verify exporter config** (Jaeger/OTel Collector).
✅ **Check context propagation** (headers, SDK settings).
✅ **Monitor logs & metrics** for bottlenecks.
✅ **Test in staging before production** to catch misconfigurations early.

For further debugging, refer to:
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Jaeger Troubleshooting Guide](https://www.jaegertracing.io/docs/latest/configuration/)