# **[Design Pattern] Tracing Gotchas – Reference Guide**

---

## **Overview**
Tracing is essential for observability, debugging, and performance analysis in distributed systems. However, improper implementation or misconfiguration can lead to critical issues: **tracing data overload, missed spans, incorrect propagation, inefficient storage, and integration conflicts**. This guide outlines common pitfalls, their impact, and mitigation strategies to ensure reliable tracing without performance or operational overhead.

---

## **Key Concepts & Schema Reference**

### **1. Core Concepts**
| Concept       | Description |
|--------------|------------|
| **Span**     | A single operation (e.g., HTTP request, database query) with metadata (timestamps, attributes, logs). |
| **Trace**    | A collection of related spans forming a request flow across services. |
| **Context Propagation** | Mechanism to pass trace IDs between services (headers, cookies, or custom formats). |
| **Sampling** | Selecting traces for recording (e.g., always-on, probabilistic, or custom rules) to balance detail and cost. |
| **Backpressure** | Handling high-volume tracing data without overwhelming storage/infrastructure. |

---

### **2. Schema Reference**
Below are common tracing schemas and their pitfalls.

#### **OTel Trace Schema (Common Fields)**
| Field          | Type        | Example Value          | Gotcha Risk                                                                 |
|----------------|-------------|------------------------|------------------------------------------------------------------------------|
| `trace_id`     | `[u8; 16]`  | `0x1234...abcdef`      | **ID Collision**: Ensure IDs are unique across distributed systems.          |
| `span_id`      | `[u8; 8]`   | `0x456...7890`         | **ID Duplication**: Avoid reusing span IDs in the same trace.               |
| `parent_id`    | `[u8; 8]`   | `0x00...` (root span) | **Orphaned Spans**: Missing `parent_id` causes trace fragmentation.        |
| `name`         | `String`    | `"user.login"`         | **Overly Detailed Names**: Long names add overhead (limit to 64 chars).     |
| `attributes`   | `Map<String, Value>` | `{"user": "John", "db": "postgres"}` | **Attribute Bloat**: Too many attributes slow down parsing/storage.          |
| `start_time`   | `Timestamp` | `2024-01-01T12:00:00Z` | **Clock Skew**: Ensure all services sync time sources (NTP).               |
| `end_time`     | `Timestamp` | `2024-01-01T12:00:02Z` | **Missing End Times**: Incomplete spans break trace analysis.              |
| `duration`     | `Duration`  | `2ms`                  | **Negative Duration**: Ensure `end_time > start_time`.                       |
| `status`       | `Status`    | `{"code": "ERROR", "message": "DB timeout"}` | **Unset Status**: Critical errors without context are harder to debug.      |

---

## **Common Tracing Gotchas & Mitigations**

### **1. Context Propagation Failures**
**Gotcha**: Trace IDs not carried across service boundaries due to incorrect headers or missing middleware.
**Impact**: Silent trace loss; debugging becomes impossible for cross-service flows.
**Mitigation**:
- **Standardize Headers**: Use `traceparent` (W3C Trace Context) or `X-B3-TraceId` (Zipkin).
  ```http
  # Correct (W3C Trace Context header)
  Traceparent: 00-123abc456def7890-123abc456def7890-01
  ```
- **Validate Headers**: Log warnings if headers are missing or malformed.
- **Fallback**: Attach trace IDs to cookies (less secure but works for web apps).

---

### **2. Sampling Errors**
**Gotcha**:
- **Over-Sampling**: Recording every trace bloats storage/CPU (e.g., 99% sampling).
- **Under-Sampling**: Critical issues (e.g., rare errors) are missed.
**Impact**: Storage costs spike or important errors go unnoticed.
**Mitigation**:
- **Use Adaptive Sampling**: Start with **1%** sampling, then increase based on error rates.
- **Rule-Based Sampling**: Target high-value traces (e.g., `/api/checkout` paths).
- **Head-Based Sampling**: Sample traces based on hash (e.g., `trace_id % 100 < 10`).

**Example Sampling Rules (OpenTelemetry):**
```yaml
# OpenTelemetry sampler config
samplers:
  head:
    decision_wait: 10ms
    randomized: true
    sampling_percentage: 5  # 5% of traces
  traceid:
    hash_mod: 100
    expected_trace_per_second: 1000
```

---

### **3. Attribute & Log Overhead**
**Gotcha**: Excessive attributes/logs slow down:
- **Span processing** (CPU-bound).
- **Storage costs** (e.g., per-attribute pricing in APM tools).
**Impact**: High latency or abandoned traces.
**Mitigation**:
- **Limit Attributes**: Restrict to **10–50 per span** (OTel recommends ≤100).
- **Drop Sensitive Data**: Never include PII (e.g., passwords) in traces.
- **Compress Logs**: Use protobuf/gzip for large log payloads.

**Example (Attribute Pruning):**
```python
# Python (OpenTelemetry)
from opentelemetry import trace

def safe_span():
    with trace.start_as_current_span("user.login") as span:
        span.set_attribute("user_id", "123")  # OK
        span.set_attribute("password", "redacted")  # Avoid!
```

---

### **4. Trace ID Collisions**
**Gotcha**: Two traces share the same `trace_id`, causing merge conflicts.
**Impact**: Mixed traces in analysis tools (e.g., "User A’s order appears to belong to User B").
**Mitigation**:
- **Use Cryptographic RNGs**: Generate `trace_id`/`span_id` with `/dev/urandom` (not sequential IDs).
- **Validate IDs**: Reject IDs with leading zeros (common in manual testing).

---

### **5. Orphaned Spans**
**Gotcha**: Spans without a `parent_id` (root spans) or missing `trace_id`.
**Impact**: Incomplete traces; tools like Jaeger/Zipkin show fragmented flows.
**Mitigation**:
- **Enforce Parent-Child Relationships**: Use `span.set_parent()` (OTel) or `B3 parent_id` header.
- **Auto-Inject Root Spans**: Ensure the first span in a trace has `parent_id = 0`.

**Example (OTel Parent-Child):**
```python
# Parent span
with trace.start_as_current_span("parent") as parent_span:
    # Child span (inherits trace context)
    with trace.start_as_current_span("child", links=[Link(trace_id=parent_span.span_context.trace_id)]) as child_span:
        pass
```

---

### **6. Backpressure & Storage Limits**
**Gotcha**: High-traffic systems generate too many spans, overwhelming:
- **APM Backends** (e.g., New Relic, Datadog).
- **Storage** (e.g., S3, Elasticsearch).
**Impact**: Drops, throttling, or increased costs.
**Mitigation**:
- **Rate Limiting**: Use OTel’s `BatchSpanProcessor` to batch spans before exporting.
- **Local Buffering**: Configure `max_queue_size` (e.g., 2048 spans).
- **Exponential Backoff**: Retry failed exports with jitter.

**Example (OTel Batch Processor):**
```yaml
# OpenTelemetry config
service:
  telemetry:
    metrics:
      export_interval: 30s
    traces:
      exporters:
        - batch/console
      processors:
        - batch
      export_interval: 10s
```

---

### **7. Clock Skew**
**Gotcha**: Services have misaligned clocks (e.g., ±10s), causing:
- Negative durations.
- Misaligned trace timelines.
**Impact**: Broken trace analysis (e.g., "Span B started before Span A").
**Mitigation**:
- **NTP Sync**: Enforce NTP on all machines (`ntpd`/`chronyd`).
- **Time Adjustment**: Use `start_time`/`end_time` offsets if skew is inevitable.

---

### **8. Vendor-Specific Format Conflicts**
**Gotcha**: Mixing APM tools (e.g., Datadog + Jaeger) with incompatible schemas.
**Impact**: Loss of traceability or duplicated spans.
**Mitigation**:
- **Standardize on OTLP**: OpenTelemetry Protocol is vendor-agnostic.
- **Schema Converters**: Use tools like [OpenTelemetry Protocol Converters](https://github.com/open-telemetry/opentelemetry-proto) for legacy formats.

---

## **Query Examples**
### **1. Finding Orphaned Spans (PromQL)**
```promql
# Jaeger Prometheus metrics (if exposed)
sum(rate(jaeger_span_processed_total{parent_id="0"}[1m])) by (service)
```
**Output**: Services with no parent-child relationships.

---

### **2. High-Latency Traces (Grafana/Loki)**
```loki
# Search for traces > 5s duration
{job="tracing-backend"}
| json
| duration > 5000000000  # 5s in nanoseconds
| group_by(service)
```
**Output**: Services with slow end-to-end flows.

---

### **3. Attribute Bloat Analysis (OpenSearch)**
```json
# Aggregation query to find spans with >50 attributes
GET /tracing-traces/_search
{
  "aggs": {
    "attr_count": {
      "terms": { "field": "attributes.keyword", "size": 0 },
      "aggs": {
        "span_count": { "count": {} }
      }
    }
  }
}
```
**Output**: Identify spans with excessive attributes.

---

## **Related Patterns**
| Pattern               | Description                                                                 | Why Combine?                                                                 |
|-----------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Resilience Patterns** (Circuit Breaker, Retry) | Handles failed spans gracefully.                                         | Prevents cascading failures from corrupting traces.                          |
| **Observability Stack** (Metrics + Traces + Logs) | Correlate traces with logs/metrics.                                         | Debug root causes faster (e.g., "Latency spike in trace X matches high CPU"). |
| **Distributed Locks** | Prevents duplicate trace processing.                                      | Ensures consistent sampling decisions across services.                       |
| **Chaos Engineering** | Tests tracing under load.                                                   | Validates gotchas in production-like conditions.                             |

---

## **Checklist for Tracing Implementation**
| Task                                | Done? (Y/N) |
|-------------------------------------|------------|
| Standardized trace headers (W3C/Zipkin) |            |
| Sampling strategy (>1% but <100%)     |            |
| Attribute limits (≤50 per span)      |            |
| NTP synchronization across services   |            |
| Orphaned span detection               |            |
| Backpressure handling (batch export)  |            |
| Clock skew monitoring                |            |
| Vendor tool compatibility             |            |

---
**Note**: Review this checklist periodically as traffic or tooling changes.