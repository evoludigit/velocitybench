```markdown
---
title: "Tracing Gotchas: The Hidden Pitfalls in Distributed Systems Observability"
author: "Alexandra Chen"
date: "2023-11-15"
categories: ["backend", "distributed systems", "observability"]
---

# Tracing Gotchas: When Your Distributed Tracing Gives You False Hope

You've implemented distributed tracing—your span IDs are flowing through microservices, your latency histograms look impressive, and you even have a sleek dashboard that makes you feel like a observability guru. But here’s the hard truth: **tracing is only as good as the gotchas you’ve accounted for**.

Tracing is supposed to make distributed systems debuggable: it should let you see exactly how requests flow through your architecture, identify bottlenecks, and troubleshoot failures. Yet, in practice, even well-designed tracing systems often fail to deliver because of overlooked edge cases. Whether it's misconfigured propagation, incorrect sampling rates, or subtle timing issues, these gotchas can leave you chasing ghosts—seeing spans where there are none, or worse, seeing false patterns that mislead your entire observability stack.

In this post, I’ll cover the most insidious tracing gotchas you might be missing, explain why they’re problematic, and give you practical examples of how to detect and fix them. We’ll dive into real-world scenarios with code snippets (OpenTelemetry, Jaeger, and Zipkin) so you can spot these issues before they lead you down a rabbit hole.

---

## The Problem: Tracing Without Context is Just Noise

Tracing is a double-edged sword. On one hand, it provides end-to-end visibility into systems that are inherently opaque. On the other hand, the complexity of distributed systems means tracing can introduce more problems than it solves if not handled carefully.

### **Common Issues Tracing Gets Wrong**
1. **Incomplete Traces**: Spans go missing because of misconfigured propagation or unsupported formats.
2. **False Bottlenecks**: Sampling rates are too coarse or too fine, obscuring or distorting real performance issues.
3. **Timing Errors**: Spans aren’t properly aligned in time across services, leading to misleading latency calculations.
4. **PLG (Propagated Latency Ghosts)**: Latency is incorrectly attributed to services that aren’t actually handling the workload.
5. **Propagation Failures**: Headers are malformed or ignored, and spans aren’t linked correctly.

These issues are often silent—they don’t crash your system, but they make your observability less useful, wasting your time and leading to incorrect conclusions.

---

## The Solution: How to Avoid Tracing Gotchas

The key to robust tracing is planning for the edge cases upfront. Below are the most common gotchas, how to identify them, and how to fix them.

---

### **1. Incomplete Traces: When Spans Disappear**

#### **The Problem**
Spans vanish between services, leaving you with "holes" in your traces. This usually happens because:
- The trace context (headers) isn’t correctly propagated.
- The format (W3C Trace Context, Baggage headers) isn’t supported by all services.
- Headers are stripped by proxies or load balancers.

#### **Example: Missing Context Propagation**
Here’s how a trace should work in a microservice architecture, but often fails:

```java
// Service A starts a trace
Span span = tracer.startSpan("processOrder");
String traceId = span.getContext().getTraceId();
String spanId = span.getContext().getSpanId();

// Forward trace context to Service B (W3C Trace Context headers)
Map<String, String> headers = new HashMap<>();
headers.put("traceparent", "00-" + traceId + "-" + spanId + "-" + 1);
// Send request to Service B with headers
client.sendRequest(headers, payload);

// Service B receives but incorrectly parses headers
String badTraceId = headers.get("tracestate"); // Wrong key!
if (badTraceId == null) {
    // No trace context found → orphaned spans
}
```

#### **The Fix**
- Use the **W3C Trace Context** standard (`traceparent` header) for trace IDs and `tracestate` for extensions (like baggage).
- Validate headers on both ends:
  ```java
  // Correctly parsing W3C Trace Context
  String traceContext = headers.get("traceparent");
  if (traceContext != null) {
      TraceContext traceContext = TraceContext.fromString(traceContext);
      SpanContext spanContext = traceContext.toSpanContext();
      tracer.addSpanContext(spanContext); // Inject into current span
  }
  ```
- Ensure intermediaries (proxies, NATs) don’t strip headers. Configure them to preserve trace context.

---

### **2. False Bottlenecks: Sampling Gone Wrong**

#### **The Problem**
Sampling is essential for scalability, but bad sampling makes your traces misleading:
- **Too coarse**: You don’t see critical paths.
- **Too fine**: You’re drowning in noise.
- **Biased sampling**: Your traces represent a skewed subset of traffic.

#### **Example: Bad Sampling in OpenTelemetry**
```yaml
# OpenTelemetry Collector Config
sampling:
  decision_wait: 500ms
  sample_rate: 0.1  # Only 10% of traces
  randomness: true
```

If your 10% sample isn’t representative, you might miss:
- Rare failures that only happen in certain environments.
- Latency spikes in low-traffic scenarios.

#### **The Fix**
- **Adaptive sampling**: Dynamically adjust sampling based on performance metrics (e.g., latency spikes).
- **Stratified sampling**:
  ```javascript
  // Node.js example with OpenTelemetry
  const samplingResult = otel.tracerProvider.getSampler().shouldSample(
      context,
      spanName,
      attributes
  );

  // Stratified sampling: Sample more for error-prone paths
  if (spanName.includes("payment") || attributes["http.status_code"] >= 500) {
      samplingResult = { decision: SamplerDecision.RECORD_AND_SAMPLE }
  }
  ```
- **Hybrid sampling**: Combine probability-based with always-sample-for-specific-paths.

---

### **3. Timing Errors: When Spans Lie About Latency**

#### **The Problem**
If spans aren’t aligned in time, you’ll get wrong conclusions about where latency is happening:
- **Clock skew**: Services’ local time differs by milliseconds or seconds.
- **Async spans**: Spans are recorded after the request completes, distorting latency.
- **Batch processing**: Spans don’t reflect real-time latency.

#### **Example: Async vs. Synchronous Timing**
```go
// Service A: Async span (bad!)
span := tracer.Start(context.Background(), "asyncTask")
go func() {
    // Simulate work
    time.Sleep(2 * time.Second)
    span.End() // Ends *after* the request completes!
}()
```

Now, your trace shows `asyncTask` taking 2 seconds, but the request itself was only 100ms. That’s a misleading bottleneck!

#### **The Fix**
- **End spans synchronously**:
  ```python
  # Python example
  with tracer.start_as_current_span("processOrder") as span:
      # Critical path: end span when the request completes
      span.end()
  ```
- **Clock synchronization**: Use NTP or tools like [Chaos Monkey](https://github.com/Netflix/chaosmonkey) to test for drift.

---

### **4. PLG (Propagated Latency Ghosts)**

#### **The Problem**
Latency is incorrectly attributed to services that aren’t actually handling the workload:
- **Double counting**: Spans are nested incorrectly, adding redundant latency.
- **Misaligned timelines**: A span starts after the request was handled by another service.

#### **Example: Nested Spans Gone Wrong**
```java
// Service A
Span parent = tracer.startSpan("parent"); // Starts at request time
Span child = tracer.startSpan("child");   // Also starts at request time
child.end(); // Ends immediately → no latency attributed to Service A!

parent.end(); // Now Service A’s span shows 0ms, but Service B’s shows 150ms
```

Now, Service B’s latency looks worse than it is because Service A’s "latency" was lost!

#### **The Fix**
- **End spans only when the work is done**:
  ```go
  // Go example
  ctx, span := tracer.Start(context.Background(), "parent")
  defer span.End()

  // Start child span, but only end it when child work is truly done
  ctx, child := tracer.Start(ctx, "child")
  defer child.End()

  // Child work
  go doWork(ctx)
  ```
- **Use `StartAsChild` for async operations**:
  ```javascript
  const child = tracer.startSpan("child", { kind: SpanKind.SERVER, startAsChild: true });
  ```

---

### **5. Propagation Failures: Headers That No One Listens To**

#### **The Problem**
Your app sends trace headers, but downstream services ignore them because:
- The headers are malformed.
- The service doesn’t support W3C Trace Context.
- A firewall or proxy drops the headers.

#### **Example: Ignored Headers**
```java
// Service A sends W3C Trace Context
headers.put("traceparent", "00-abc123-xyz456-01");

// Service B (legacy) expects old-style headers
headers.put("X-B3-TraceId", "abc123"); // Legacy format
headers.put("X-B3-SpanId", "xyz456");
```

Now, Service B doesn’t recognize the W3C header and won’t associate its span with the trace.

#### **The Fix**
- **Support multiple header formats**:
  ```java
  public SpanContext extract(Context context, Map<String, String> headers) {
      // Try W3C first
      String traceparent = headers.get("traceparent");
      if (traceparent != null) {
          return TraceContext.fromString(traceparent).toSpanContext();
      }
      // Fall back to legacy
      String traceId = headers.get("X-B3-TraceId");
      if (traceId != null) {
          return B3SpanContext.create(traceId, headers.get("X-B3-SpanId"));
      }
      return SpanContext.getInvalid();
  }
  ```
- **Test propagation through all services**:
  ```bash
  curl -H "traceparent: 00-abc-xyz" http://service-b-api
  ```
  Verify the response includes a `traceparent` header.

---

## Implementation Guide: How to Test for Tracing Gotchas

1. **Test propagation** (does the trace context survive all services?):
   ```bash
   # Use a tool like `tracing-test` or `jrace` to verify headers
   tracing-test -h http://service-a --follow=service-b
   ```

2. **Check sampling** (are you missing critical paths?):
   - Compare traces with high vs. low sampling rates.
   - Use Jaeger’s `filter` to exclude low-traffic traces:
     ```sql
     SELECT * FROM "spans" WHERE "name" = "payment_processor";
     ```

3. **Validate timing** (are spans aligned?):
   - Look for gaps in traces where spans start/end at unexpected times.
   - Use OpenTelemetry’s `SpanKind` to distinguish between client/server.

4. **Audit header formats**:
   - Run a chaos experiment where headers are dropped randomly:
     ```python
     # Simulate header loss
     if random.random() < 0.1:  # 10% chance of dropping headers
         del headers["traceparent"]
     ```

5. **Monitor orphaned spans**:
   - Set up alerts for traces with unlinked spans:
     ```python
     # Example: Alert if a trace has more than 10 unlinked spans
     if len(trace.spans) > 10 and not trace.fully_linked():
         alert("Orphaned spans detected!")
     ```

---

## Common Mistakes to Avoid

| **Mistake**                   | **Why It’s Bad**                                                                 | **How to Fix It**                                                                 |
|-------------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| Ignoring legacy formats       | Breaks existing services that don’t support W3C Trace Context.                  | Support both formats for backward compatibility.                                   |
| Not validating headers        | Silent failures where traces disappear.                                        | Always check for malformed headers and fall back gracefully.                       |
| Using fixed sampling rates    | Misses critical paths or introduces noise.                                       | Use adaptive/stratified sampling.                                                   |
| Ending spans too early        | False bottlenecks in downstream services.                                       | End spans only when work is truly complete.                                         |
| Not testing propagation      | Assumes headers survive—until they don’t (they usually don’t).                   | Write integration tests that verify header flow through all services.             |
| Clock skew without sync       | Latency misattribution across time zones or unstable hosts.                      | Use NTP and test for drift with chaos tools.                                       |

---

## Key Takeaways

- **Tracing is only as good as its weakest link**. A missing header or misaligned span can ruin your observability.
- **Headers are fragile**. Always validate and support multiple formats (W3C + legacy).
- **Sampling is a balancing act**. Too coarse = blind spots; too fine = noise. Use adaptive techniques.
- **Time is everything**. Spans must align with request timelines; otherwise, your latency analysis is wrong.
- **Test propagation end-to-end**. Assume nothing works—verify it.
- **Orphaned spans are a red flag**. Alert on unlinked traces to catch misconfigurations early.
- **Legacy systems are everywhere**. Always account for backward compatibility.

---

## Conclusion

Distributed tracing is one of the most powerful tools in your observability toolkit—but it’s also one of the most deceptive. The gotchas we’ve covered here (incomplete traces, false bottlenecks, timing errors, PLG, and propagation failures) are silent killers of observability. They don’t crash your system, but they make your traces less useful, leaving you chasing ghosts rather than debugging in real time.

The good news? These problems are avoidable. By following the patterns and techniques in this post—validating headers, testing propagation, sampling intelligently, and aligning spans with reality—you can turn tracing from a potential liability into a reliable debugging superpower.

**Next steps:**
- Audit your traces for these gotchas (use Jaeger/Zipkin’s query tools).
- Write integration tests that verify header flow through all services.
- Gradually migrate to W3C Trace Context while supporting legacy formats.
- Monitor orphaned spans and false bottlenecks with alerts.

Now go forth and trace—**right this time**.

---
**Further Reading:**
- [OpenTelemetry’s Guide to W3C Trace Context](https://opentelemetry.io/docs/reference/specification/trace/semantic_conventions/)
- [Jaeger’s Troubleshooting Guide](https://www.jaegertracing.io/docs/latest/troubleshooting/)
- [Chaos Engineering for Observability](https://www.chaossummit.org/)
```

This post is structured for advanced developers, with a mix of problem-solution pairs, practical code examples, and clear tradeoffs. It avoids overpromising (e.g., no "silver bullet" tracing approach) and focuses on realistic challenges and fixes.