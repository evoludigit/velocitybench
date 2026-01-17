# **Debugging gRPC Observability: A Troubleshooting Guide**
*(Focused on Monitoring, Tracing, Metrics, and Logging in gRPC Services)*

---

## **1. Introduction**
gRPC Observability ensures visibility into service behavior, performance, and errors. This guide helps debug common issues in **tracing (OpenTelemetry, Jaeger), metrics (Prometheus), and structured logging** in gRPC systems.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                          | **Possible Cause**                          |
|---------------------------------------|---------------------------------------------|
| No metrics/span logs in observability backend | Missing instrumentation or misconfigured exporters |
| High latency in gRPC calls           | Slow instrumentation or expensive tracing |
| Missing error details in logs        | Incorrect OpenTelemetry span context propagation |
| Unreliable metrics (e.g., `grpc_server_handled_total`) | Misconfigured Prometheus scraper or incorrect collector |
| No traces visible in Jaeger/Zipkin   | Missing `grpc` span attributes or auto-instrumentation |
| High CPU/memory usage in collector   | Overhead from excessive tracing/metrics |

---
## **3. Common Issues & Fixes**

### **3.1 Missing OpenTelemetry Spans**
**Symptom:** No spans visible in Jaeger/Zipkin despite gRPC calls being made.

**Root Cause:**
- Auto-instrumentation not enabled.
- OpenTelemetry SDK not imported or initialized.

**Fix:**
```python
# Python (Auto-instrumentation via opentelemetry-instrumentation-grpc)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-grpc

# Initialize in your app
from opentelemetry import trace
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer

trace.set_tracer_provider(trace.get_tracer_provider())
GrpcInstrumentorServer().instrument()  # Auto-instrument gRPC server
```

**Verification:**
```bash
# Check if spans are emitted
jaeger query --service-name=your-service
```

---

### **3.2 High Latency in gRPC Calls**
**Symptom:** Slow responses with no clear delay source.

**Root Cause:**
- Heavy OpenTelemetry overhead (e.g., sampling too frequently).
- Unoptimized tracing (e.g., inline sampling profile: `AlwaysOn`).

**Fix:**
```python
# Enable adaptive sampling (recommended)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import AdaptiveSamplingStrategy

provider = TracerProvider(
    sampler=AdaptiveSamplingStrategy(
        initial_decision_probability=0.2,  # Lower than 1.0
        max_decision_probability=0.5,
    )
)
```

**Optimization:**
- Use **TraceID-only propagation** in high-throughput systems:
  ```go
  // Go (gRPC with OpenTelemetry)
  ctx := context.WithValue(ctx, opentrace.TraceIDKey, ctx.Value(opentrace.TraceIDKey))
  ```

---

### **3.3 Missing Error Context in Logs**
**Symptom:** Logs show no error details (e.g., missing stack traces, correlation IDs).

**Root Cause:**
- Span context not propagated to logs.
- Structured logging (e.g., JSON) missing trace context.

**Fix (Python):**
```python
from opentelemetry import trace
from opentelemetry.trace import get_current_span

logger = logging.getLogger(__name__)

def error_handler():
    span = get_current_span()
    logger.error(
        "Failed RPC call",
        extra={
            "trace_id": span.span_context.trace_id,
            "span_id": span.span_context.span_id,
            "status": span.status.status_code.value,
        }
    )
```

**Verification:**
```bash
# Filter logs by trace_id
grep -E "trace_id=.*" /var/log/your-service.log
```

---

### **3.4 Prometheus Metrics Not Scraped**
**Symptom:** No metrics in Grafana/Prometheus despite exposing `/metrics`.

**Root Cause:**
- Incorrect endpoint configuration.
- Firewall blocking Prometheus scraper.

**Fix:**
```python
# Python (Prometheus exporter)
from prometheus_client import start_http_server, Counter

metrics = Counter('grpc_server_handled_total', 'gRPC call count')

def rpc_handler(request, context):
    metrics.inc()
    # Handle request
    return grpc.Response()
```

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'grpc-service'
    static_configs:
      - targets: ['localhost:8000']  # Ensure this matches your server
```

---

### **3.5 Jaeger Traces Not Appearing**
**Symptom:** Jaeger shows no traces despite gRPC calls.

**Root Cause:**
- OpenTelemetry exporter misconfigured.
- Jaeger collector not receiving data.

**Fix (Python):**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)
provider = trace.TracerProvider(exporter=exporter)
trace.set_tracer_provider(provider)
```

**Verification:**
```bash
# Check Jaeger collector logs
docker logs -f jaeger-collector
```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                          | **Example Command**                     |
|------------------------|---------------------------------------|-----------------------------------------|
| **Jaeger CLI**         | Query traces by service/operation     | `jaeger query --service=payments`       |
| **Prometheus**         | Check metric availability             | `scrape_configs` in Prometheus UI        |
| **gRPCurl**            | Inspect gRPC calls interactively      | `grpcurl -plaintext localhost:50051 list` |
| **OpenTelemetry Collector** | Debug exporter issues          | `otelcol --config-file=config.yaml`     |
| **FlameGraph**         | Analyze CPU bottlenecks in traces    | `record software-dependencies` (PPROF)  |

---

### **Key Debugging Commands**
```bash
# Check gRPC connection
grpc_health_probe -addr=localhost:50051

# Verify metrics endpoint
curl http://localhost:8000/metrics | grep grpc

# Test OpenTelemetry span emission
otel trace export --format json | jq .
```

---

## **5. Prevention Strategies**
1. **Instrument Early:**
   - Use auto-instrumentation (e.g., `opentelemetry-instrumentation-grpc`).
   - Validate spans after each code change.

2. **Optimize Sampling:**
   - Avoid `AlwaysOn` in production; use `Adaptive` or `Probabilistic`.
   - Exclude high-latency paths from sampling.

3. **Monitor Instrumentation Overhead:**
   - Track `otel_processed_spans_total` in metrics.
   - Set alarms for abnormal sampling rates.

4. **Use Structured Logging:**
   - Always include `trace_id` and `span_id` in logs.

5. **Test Observability Locally:**
   ```bash
   # Run Jaeger locally
   docker-compose -f /path/to/jaeger.yaml up
   ```

---

## **6. Conclusion**
Common gRPC observability issues stem from **misconfiguration (sampling, exporters) or missing instrumentation**. Always:
- Validate spans/metrics in staging.
- Use auto-instrumentation where possible.
- Monitor collector health.

**Further Reading:**
- [OpenTelemetry gRPC Instrumentation](https://opentelemetry.io/docs/instrumentation/python/grpc/)
- [Prometheus gRPC Exporter](https://github.com/grpc-ecosystem/grpc-prometheus)

---
**Next Steps:**
- Apply fixes in a staging environment first.
- Set up alerts for missing traces/metrics.