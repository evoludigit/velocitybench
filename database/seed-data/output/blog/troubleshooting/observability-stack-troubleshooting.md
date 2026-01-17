# **Debugging Observability: Metrics, Logs, and Traces – A Troubleshooting Guide**

## **1. Introduction**
Observability is critical for modern applications. When metrics, logs, and traces are implemented correctly, they allow engineers to:
- **Detect bottlenecks** (slow applications)
- **Understand root causes** (unexpected errors)
- **Resolve incidents faster** (structured debugging)

This guide covers common issues, debugging techniques, and prevention strategies for **Metrics, Logs, and Traces (MLT)** patterns.

---

## **2. Symptom Checklist**
Before diving into debugging, identify which of these symptoms match your issue:

### **A. Slow Application Issues**
- [ ] Application response times are **inconsistently high** (e.g., P99 latency spikes)
- [ ] CPU/memory usage is **unexpectedly high** in certain services
- [ ] **No clear correlation** between logs and performance degradation
- [ ] **Database queries** taking longer than expected (without logging)
- [ ] **Third-party API calls** timing out or failing silently

### **B. Unexpected Errors in Production**
- [ ] Errors appear **without meaningful context** in production
- [ ] Logs are **incomplete or missing** critical details (e.g., request IDs, payloads)
- [ ] **Errors are intermittent**, making reproduction difficult
- [ ] **No traceability** between frontend and backend failures
- [ ] **Health checks pass**, but users report issues

### **C. Difficult Incident Response**
- [ ] It takes **hours to diagnose** why a service failed
- [ ] **Logs are flooded with noise**, making root cause analysis hard
- [ ] **Metrics lack granularity** (e.g., only aggregate stats, no request-level data)
- [ ] **Traces show noise** (e.g., too many spans, missing key operations)
- [ ] **No clear ownership** of incidents (who should investigate?)

---

## **3. Common Issues & Fixes**

### **A. Slow Application → No Clear Bottleneck**
#### **Issue:** Application is slow, but metrics/logs don’t show the cause.
**Common Causes:**
- **Missing performance metrics** (e.g., no latency breakdown by component)
- **Logs lack context** (e.g., no request IDs, missing timestamps)
- **Traces are incomplete** (e.g., missing spans for DB calls)
- **Sampling too aggressive** (e.g., traces only capture 1% of requests)

#### **Fixes with Code Examples**
✅ **Add granular metrics per component**
```python
# Example: Track DB query latency separately
import time

start_time = time.time()
query_result = db.execute("SELECT * FROM users")
db_latency = time.time() - start_time
metrics.increment("db.query.latency", { "operation": "select_users", "duration": db_latency })
```

✅ **Log structured data with request context**
```python
# Example: Log with request ID and user ID
logger.info(
    "User lookup failed",
    extra={
        "request_id": request.headers.get("X-Request-ID"),
        "user_id": user_id,
        "error": str(e)
    }
)
```

✅ **Ensure full trace coverage (reduce sampling if needed)**
```yaml
# Example: Jaeger/OpenTelemetry config to reduce sampling
sampling:
  decision_wait: 50ms
  initial_sample_rate: 0.1  # Start with 10% sampling
  max_traces_per_seconds: 2000
```

✅ **Use distributed tracing to identify slow endpoints**
```go
// Example: OpenTelemetry span for HTTP request
span := otel.Tracer("http-tracer").Start("get_user", trace.SpanKindServer)
defer span.End()

start := time.Now()
user, err := fetchUserFromDB(userID)
elapsed := time.Since(start)

span.Record("db_query_latency", float64(elapsed.Milliseconds()))
```

---

### **B. Unexpected Errors → No Context in Logs**
#### **Issue:** Errors appear in production, but logs lack debugging info.
**Common Causes:**
- **Logs are unstructured** (e.g., plaintext without metadata)
- **Stack traces are missing** (e.g., no frame details)
- **Error boundaries swallow exceptions** (e.g., silent failures)
- **Logs are rotated too aggressively** (older logs missing)

#### **Fixes with Code Examples**
✅ **Log structured errors with context**
```javascript
// Example: Structured error logging in Node.js
app.use((err, req, res, next) => {
  console.error({
    error: err.message,
    stack: err.stack,
    requestId: req.headers['x-request-id'],
    userId: req.user?.id
  });
  res.status(500).send("Internal Server Error");
});
```

✅ **Avoid silent failures (wrap errors properly)**
```python
# Example: Proper error handling with logging
try:
    process_payment(user_id, amount)
except PaymentFailedError as e:
    logger.error(
        "Payment failed for user %s", user_id,
        extra={
            "status_code": 402,
            "payment_id": e.payment_id,
            "error_type": type(e).__name__
        }
    )
    raise
```

✅ **Use correlation IDs for traceability**
```java
// Example: Spring Boot + Distributed Tracing
String requestId = UUID.randomUUID().toString();
RequestAttributes requestAttributes = RequestContextHolder.getRequestAttributes();
requestAttributes.setAttribute("requestId", requestId, RequestAttributes.SCOPE_REQUEST);

// Log with correlation ID
logger.error("Error occurred in /users/{}", userId, e, () -> {
    return Map.of(
        "requestId", requestId,
        "userId", userId
    );
});
```

---

### **C. Difficult Incident Response → Slow Diagnosis**
#### **Issue:** It takes too long to understand why something broke.
**Common Causes:**
- **No centralized observability dashboard**
- **Metrics lack alerts for critical thresholds**
- **Logs are overwhelming (too much noise)**
- **Traces are not correlated with logs/metrics**

#### **Fixes with Code Examples**
✅ **Set up proactive alerts**
```yaml
# Example: Prometheus alert rules for high latency
groups:
- name: latency-alerts
  rules:
  - alert: HighEndpointLatency
    expr: http_request_duration_seconds{quantile="0.99"} > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High latency in {{ $labels.route }}"
```

✅ **Use log sampling to reduce noise**
```bash
# Example: Fluentd filter to sample logs
<filter **>
  @type grep
  <exclude>
    key message
    pattern /^\[debug\]/
  </exclude>
</filter>
```

✅ **Correlate traces & metrics in dashboards**
```json
# Example: Grafana dashboard annotations for trace IDs
{
  "time": "now",
  "text": "Trace ID: {{ $labels.trace_id }}",
  "isRegion": false,
  "eventColor": "red"
}
```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**       | **Purpose** | **When to Use** |
|---------------------------|------------|----------------|
| **Prometheus + Grafana**  | Metrics visualization & alerting | Investigating performance trends |
| **ELK Stack (Elasticsearch, Logstash, Kibana)** | Log aggregation & search | Debugging intermittent errors |
| **Jaeger/Tempo**          | Distributed tracing | Finding latency bottlenecks |
| **OpenTelemetry**         | Unified observability (metrics, logs, traces) | Replacing multiple agents |
| **Structured Logging**    | Enrich logs with context | Debugging production issues |
| **SLO-based Alerting**    | Error budget monitoring | Proactive incident detection |
| **Trace Sampling**        | Reduce overhead in high-traffic apps | Optimizing trace collection |

### **Step-by-Step Debugging Workflow**
1. **Check Metrics First**
   - Look for spikes in latency, error rates, or resource usage.
   - Example: Is CPU > 90% for a specific microservice?

2. **Inspect Logs for Context**
   - Filter logs by timestamp, error level, or request ID.
   - Example: `grep "ERROR" /var/log/app.log | grep "payment_failed"`

3. **Trace the Request Flow**
   - Use distributed tracing to see where a request got stuck.
   - Example: Jaeger query for `spans[http_request]` where `duration > 500ms`.

4. **Reproduce Locally**
   - If possible, simulate the issue with test data.

---

## **5. Prevention Strategies**
### **A. Metrics Best Practices**
- **Track critical business metrics** (e.g., conversion rates, payment success).
- **Use dimensions for granular analysis** (e.g., `service=payment, action=charge`).
- **Set up dashboards for key services** (e.g., API latency, DB load).

### **B. Logging Best Practices**
- **Always include request IDs** for traceability.
- **Log at the right level** (avoid over-logging in production).
- **Use structured logging** (JSON > plaintext).
- **Consider log retention policies** (e.g., 30 days for errors, 7 days for debug).

### **C. Tracing Best Practices**
- **Instrument key user flows** (e.g., checkout process).
- **Avoid over-sampling** (balance coverage vs. overhead).
- **Correlate traces with logs & metrics** (e.g., link trace ID to log entries).

### **D. Proactive Monitoring**
- **Set up SLOs (Service Level Objectives)** to detect degradation early.
- **Use synthetic monitoring** (e.g., Pingdom, UptimeRobot) for uptime checks.
- **Automate incident response** (e.g., Slack alerts,PagerDuty).

---

## **6. Conclusion**
Observability is **not optional**—it’s the backbone of reliable production systems. By following this guide, you can:
✅ **Pinpoint bottlenecks** with metrics & traces
✅ **Debug errors faster** with structured logs
✅ **Respond to incidents proactively** with alerts & dashboards

**Next Steps:**
1. **Audit your current observability setup** (Are metrics, logs, and traces properly correlated?)
2. **Fix critical gaps** (e.g., missing traces, unstructured logs)
3. **Set up proactive alerts** (before issues become incidents)

**Example Fix Checklist:**
| **Issue**               | **Action** |
|-------------------------|------------|
| No latency breakdowns   | Add OpenTelemetry spans for DB calls |
| Logs lack request IDs    | Modify logging to include `X-Request-ID` |
| High trace overhead      | Adjust sampling rate (e.g., 20%) |
| No alerts for errors     | Set up Prometheus/PagerDuty alerts |

By systematically applying these fixes, you’ll **reduce mean time to detect (MTTD)** and **resolve incidents faster**. 🚀