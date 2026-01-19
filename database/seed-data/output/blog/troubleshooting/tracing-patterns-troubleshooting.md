# **Debugging Tracing Patterns: A Troubleshooting Guide**

## **Introduction**
**Tracing Patterns**—such as **Distributed Tracing**, **Structured Logging**, and **Correlation IDs**—are essential for debugging, monitoring, and understanding complex, distributed systems. When misconfigured or broken, these systems can lead to blind spots in observability, making it difficult to diagnose performance bottlenecks, latency issues, or failures across microservices.

This guide focuses on troubleshooting common issues with **distributed tracing**, **structured logging**, and **correlation-based debugging** in microservices architectures.

---

---

## **1. Symptom Checklist**
If you suspect a **Tracing Pattern** issue, check for the following symptoms:

### **A. Observability-Related Symptoms**
✅ **Missing or incomplete traces** in tracing systems (Jaeger, Zipkin, OpenTelemetry).
✅ **High latency** in trace ingestion or query performance.
✅ **Correlation IDs not propagating** across service boundaries.
✅ **Log entries missing context** (e.g., no `trace_id` or `span_id`).
✅ **Duplicate or missing spans** in distributed traces.
✅ **Tracing overhead is abnormally high** (e.g., 20%+ latency increase).
✅ **Auto-instrumentation errors** (e.g., SDKs failing to inject headers).

### **B. Functional Symptoms**
✅ **Requests appear to hang** but no trace is generated.
✅ **Logs and traces are out of sync** (e.g., log says "success" but trace shows an error).
✅ **Correlation IDs are reset** in downstream services.
✅ **Tracing works in staging but fails in production** (common in misconfigured environments).
✅ **Manual trace sampling fails**, causing missing critical paths.

### **C. Performance-Related Symptoms**
✅ **High CPU/memory usage** by tracing agents (e.g., OpenTelemetry Collector, Jaeger Agent).
✅ **Slow trace resolution** (e.g., taking seconds to render a trace).
✅ **Storage issues** (e.g., database full of discarded traces due to bad sampling).

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Missing or Broken Correlation IDs**
**Symptoms:**
- Logs in different services have no way to link requests.
- Debugging requires manual correlation.

**Root Causes:**
- Missing header injection in outbound calls.
- Header names mismatch between services.
- Headers stripped by proxies (e.g., AWS ALB, NGINX).

**Fixes:**

#### **A. Ensure Consistent Header Injection (Java - Spring Boot)**
```java
@RestController
public class MyController {

    @Value("${correlation.id.header:X-Correlation-ID}")
    private String correlationIdHeader;

    @GetMapping("/api/data")
    public ResponseEntity<String> getData() {
        String correlationId = request.getHeader(correlationIdHeader);
        if (correlationId == null) {
            correlationId = UUID.randomUUID().toString();
        }

        // Pass correlation ID to downstream call
        String response = callDownstreamService(correlationId);

        // Log with correlation ID
        logger.info("Processed request with ID: {}", correlationId);

        return ResponseEntity.ok(response);
    }

    private String callDownstreamService(String correlationId) {
        HttpHeaders headers = new HttpHeaders();
        headers.set(correlationIdHeader, correlationId); // Ensure header is passed

        return restTemplate.exchange(
            "http://downstream-service/api",
            HttpMethod.GET,
            new HttpEntity<>(headers),
            String.class
        ).getBody();
    }
}
```

#### **B. Fix for Proxy Stripping Headers (NGINX)**
If NGINX removes `X-Correlation-ID`, add this to your config:
```nginx
http {
    map $http_x_correlation_id $preserve_correlation_id {
        default $http_x_correlation_id;
    }

    server {
        location / {
            proxy_pass http://backend;
            proxy_set_header X-Correlation-ID $preserve_correlation_id;
        }
    }
}
```

---

### **Issue 2: Incomplete or Duplicated Spans**
**Symptoms:**
- Traces show missing segments (e.g., database calls are gone).
- Same operation appears multiple times in a trace.

**Root Causes:**
- **Auto-instrumentation misconfiguration** (e.g., wrong library version).
- **Explicit span creation conflicts** with auto-instrumentation.
- **Duplicate SDK initialization** (e.g., multiple OpenTelemetry SDKs loaded).

**Fixes:**

#### **A. Disable Auto-Instrumentation for Specific Libraries**
If auto-instrumentation conflicts with manual spans:
```yaml
# OpenTelemetry JavaAgent config (application.properties)
opentelemetry.sdk.disabled=true  # Disable auto-instrumentation
```

#### **B. Ensure Correct Span Context Propagation (Python - OpenTelemetry)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Initialize tracer
provider = TracerProvider()
processor = BatchSpanProcessor(JaegerExporter(
    endpoint="http://jaeger:14250/api/traces",
    agent_host_name="jaeger-agent"
))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Get a tracer
tracer = trace.get_tracer(__name__)

# Manually propagate context
def call_downstream():
    with tracer.start_as_current_span("downstream_call") as span:
        # Ensure context is propagated
        span.context.copy_to(request.headers.get("x-otel-traceparent"))
        # Make HTTP request
        response = requests.get("http://downstream-service")
        return response.text
```

---

### **Issue 3: High Tracing Overhead**
**Symptoms:**
- Latency increases by 30-50% due to tracing.
- CPU usage spikes during high traffic.

**Root Causes:**
- **Too frequent sampling** (e.g., 100% trace rate).
- **Unoptimized trace propagation** (e.g., heavy serialization).
- **Too many spans per request** (e.g., logging every micro-operation).

**Fixes:**

#### **A. Adjust Sampling Rate**
```yaml
# OpenTelemetry Collector config (sampling.yml)
sampling_rules:
  - name: low_latency_rule
    type: probabilistic
    probability: 0.1  # Sample 10% of traces
```

#### **B. Optimize Span Batching (Go - OpenTelemetry)**
```go
// Configure batching to reduce overhead
bsp := batch.NewSpanProcessor(
    otlp.NewExporter(otlp.WithEndpoint("http://otel-collector:4317"))
)
provider := tracing.NewTracerProvider(
    tracing.WithSampler(sampling.NewProbabilitySampler(0.1)), // 10% sampling
    tracing.WithSpanProcessor(bsp),
)
trace.SetTracerProvider(provider)
```

---

### **Issue 4: Sampling Fails to Capture Critical Paths**
**Symptoms:**
- Important errors are missed due to sampling.
- Debugging requires manual trace collection.

**Root Causes:**
- ** too aggressive sampling rules.
- **Sampler not accounting for slow operations**.

**Fixes:**

#### **A. Use Adaptive Sampling**
```yaml
# OpenTelemetry Collector config (adaptive_sampling.yml)
sampling_rules:
  - name: high_latency_rule
    type: rate_limiting
    max_traces_per_minute: 1000
    max_attribute_matches: 1
    matches:
      - attribute:
          key: "http.method"
          value: "POST"
          comparator: "="
```

#### **B. Force Sample Critical Paths**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import SamplingDecision

# Custom sampler
class CriticalPathSampler:
    def should_sample(self, context, trace_id, name):
        if "critical_path" in trace_id:
            return SamplingDecision.RECORD_AND_SAMPLE  # Force sample
        return SamplingDecision.RECORD_ONLY  # Lightweight sampling

provider = TracerProvider(sampler=CriticalPathSampler())
```

---

### **Issue 5: Tracing Works in Dev but Fails in Prod**
**Symptoms:**
- Traces work locally but are missing in production.
- Environment variables differ between stages.

**Root Causes:**
- **Missing OTLP exporter in prod**.
- **Incorrect endpoint configurations**.
- **Network policies blocking trace ingestion**.

**Fixes:**

#### **A. Verify OTLP Endpoint in Production**
```bash
# Check if OTLP is configured
docker exec <container> grep -i "otel.*endpoint" /etc/otel-config.yaml
```

#### **B. Use Environment Variables for Config**
```yaml
# application-prod.yaml
otel.endpoint: "http://prod-otel-collector:4317"
otel.service.name: "prod-microservice"
```

#### **C. Test Network Connectivity to Tracer**
```bash
# From a prod container, test connectivity
curl -v http://prod-otel-collector:4317/v1/traces
```

---

## **3. Debugging Tools & Techniques**

### **A. Essential Tools**
| Tool | Purpose | Command/Usage |
|------|---------|--------------|
| **Jaeger CLI** | Query traces | `jaeger query <trace_id>` |
| **OpenTelemetry Collector** | Local tracing | `otelcol --config=otel-config.yml` |
| **Kubernetes `kubectl`** | Check container logs | `kubectl logs <pod> -c otel-agent` |
| **Wireshark** | Inspect HTTP headers | Capture `X-Trace-ID` |
| **Prometheus + Grafana** | Monitor sampling rates | `otel_http_requests_total` |

### **B. Debugging Techniques**

#### **1. Check Trace Generation Locally**
```bash
# Force a trace in dev
curl -H "X-Trace-ID: test123" http://localhost:8080/api
```
→ If trace appears, the issue is likely **propagation** in prod.

#### **2. Validate Headers with `curl`**
```bash
curl -v -H "X-Correlation-ID: debug123" http://service/api
```
→ Look for `X-Correlation-ID` in logs.

#### **3. Use `strace` for Low-Level Debugging**
```bash
strace -f -e trace=open,write ./my-service
```
→ Check if tracing libraries are being loaded.

#### **4. Enable Debug Logging for Tracing SDKs**
```yaml
# OpenTelemetry Java config
otel.javaagent.debug=true
otel.debug=true
```

#### **5. Test with Synthetic Load**
```bash
# Use k6 to generate traces
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% < 500ms
  },
};

export default function () {
  const params = {
    headers: {
      'X-Correlation-ID': 'test-' + Math.random().toString(36).substring(2),
    },
  };
  const res = http.get('http://service/api', params);
  check(res, { 'status was 200': (r) => r.status === 200 });
}
```

---

## **4. Prevention Strategies**

### **A. Best Practices for Tracing Patterns**
✔ **Standardize Correlation IDs** (Use `X-Correlation-ID`, `traceparent`).
✔ **Avoid Over-Sampling** (Default to 10-20% sampling).
✔ **Monitor Tracing Overhead** (Alert if latency increases by >10%).
✔ **Use Structured Logging** (JSON logs with `trace_id`, `span_id`).
✔ **Test in Staging** (Ensure tracing works before production).
✔ **Document Schema** (Agree on `span.names` and `attributes`).

### **B. Automated Checks**
| Check | Tool | Implementation |
|-------|------|----------------|
| **Correlation ID Propagation** | Unit Tests | Mock HTTP calls, verify headers |
| **Trace Completeness** | OpenTelemetry Collector | Validate no missing spans |
| **Sampling Rate** | Prometheus | Alert if sampling drops below threshold |
| **Header Presence** | k6 Load Tests | Ensure headers are always passed |

### **C. CI/CD Integration**
```yaml
# GitHub Actions: Validate tracing
- name: Test Tracing
  run: |
    # Run a test with tracing enabled
    ./test-with-tracing.sh
    # Check if traces were generated
    curl http://localhost:16686/api/traces?service=test-service | grep -q 'test123'
    if [ $? -ne 0 ]; then exit 1; fi
```

---

## **5. Conclusion**
Tracing patterns are **critical** for debugging distributed systems, but misconfigurations can lead to blind spots. By following this guide, you can:
✅ **Identify missing traces** with correlation checks.
✅ **Optimize sampling** to avoid performance overhead.
✅ **Debug propagation issues** using `curl` and logs.
✅ **Prevent future issues** with automated tests and monitoring.

**Final Tip:**
> *"If traces disappear in production but work in dev, check environment variables, network policies, and sampling rules first."*

---
Would you like a deeper dive into any specific area (e.g., OpenTelemetry Collector tuning, Jaeger query optimizations)?