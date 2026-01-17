# **[Pattern] Profiling & Debugging Reference Guide**

---

## **Overview**
The **Profiling & Debugging** pattern provides structured methods to identify, analyze, and resolve performance bottlenecks, logical errors, and runtime anomalies in software applications. This guide covers key techniques—including flame graphs, memory profiling, logging, and tracing—while emphasizing tooling, metrics, and best practices for efficient debugging in production and development environments.

Profiling helps quantify inefficiencies (e.g., CPU, memory, I/O) via low-overhead instrumentation, while debugging isolates root causes using structured logs, stack traces, and replayable sessions. By combining static analysis (code reviews) with dynamic profiling (runtime data), teams can reduce mean time to resolve (MTTR) from hours to minutes.

---

## **Schema Reference**
Key components of the Profiling & Debugging pattern:

| **Component**               | **Description**                                                                                     | **Key Tools/Techs**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Profiling Tools**         | Capture runtime metrics (CPU, memory, latency)                                                      | CPU profilers: (pprof, VTune, YourKit)                                                                     |
|                             |                                                                                                     | Memory profilers: (Heaptrack, Valgrind, Ruby-Memory-Profiler)                                             |
|                             |                                                                                                     | Sampling: (perf, dtrace, eBPF)                                                                           |
| **Logging & Tracing**       | Structured logging (levels, correlation IDs) & distributed tracing (context propagation)           | ELK Stack (Elasticsearch, Logstash, Kibana), Jaeger, OpenTelemetry, Structured Logging (JSON/Protobuf) |
| **Error Tracking**          | Aggregate and alert on exceptions, crashes, and SLO violations                                      | Sentry, Datadog Error Tracking, Honeycomb                                                                 |
| **Stack Traces**            | Debug context via thread stacks and backtraces                                                         | Core dumps, `gdb`, LLDB, Chrome DevTools (for JS)                                                       |
| **Replay Systems**          | Record/replay user sessions or failures for deterministic debugging                                 | Bugsnag, Dynatrace Session Replay, custom replay frameworks                                             |
| **Static Analysis**         | Preemptive detection of code issues (race conditions, memory leaks)                                  | SonarQube, CodeQL, Clang Static Analyzer                                                                |
| **Distributed Debugging**  | Debug multi-service failures with service mesh integration                                          | Kiali, Jaeger, Envoy Helper, Ambient Tracing (OpenTelemetry)                                           |
| **Chi-Squared Testing**     | Statistically validate hypothesis-driven changes (e.g., "Fix X reduced crashes by 30%")              | Google Data Validation, Python SciPy                                                                      |

---
**Note:** Tools may overlap; prioritize based on language/runtime (e.g., Java: `VisualVM`, Python: `cProfile`).

---

## **Implementation Details**
### **1. Profiling Workflow**
#### **Step 1: Define Metrics**
Start with measurable goals (e.g., "Reduce 99th-percentile latency by 20%").
Example metrics:
- **CPU:** % time spent in functions (flame graphs).
- **Memory:** Allocation rates, heap fragmentation.
- **Latency:** End-to-end user flows (trace spans).
- **Error Rates:** Exception counts per endpoint.

#### **Step 2: Instrument the Application**
- **CPU Profiling:** Use sampling tools (e.g., `perf` for Linux) to avoid slowdowns:
  ```bash
  perf record -g ./your_app
  ```
- **Memory Profiling:** Capture heap snapshots:
  ```bash
  go tool pprof -http=:8080 profile.pprof  # Go example
  ```
- **Latency Profiling:** Add distributed tracing headers (OpenTelemetry):
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("user_flow"):
      # Code here
  ```

#### **Step 3: Analyze Data**
- **Flame Graphs:** Parse profiling data (e.g., `bpftrace` → flamegraph.pl):
  ```bash
  bpftrace -e 'uprobe:./your_app:main { @[probe, pid] = stack(64); }' | flamegraph.pl > flame.svg
  ```
  ![Example Flame Graph](https://www.brendangregg.com/flamegraphs/cpu-flame-graph.png)
- **Log Analysis:** Query logs with structured fields:
  ```elasticsearch
  GET /logs/_search
  {
    "query": {
      "bool": {
        "must": [
          { "term": { "level": "ERROR" } },
          { "range": { "@timestamp": { "gte": "now-1h" } } }
        ]
      }
    }
  }
  ```

#### **Step 4: Hypothesize & Validate**
- Use chi-squared tests to compare metrics before/after changes:
  ```python
  from scipy.stats import chi2_contingency
  observed = [[100, 80], [20, 12]]  # "Before" vs. "After" errors
  chi2, p, _, _ = chi2_contingency(observed)
  if p < 0.05: print("Significant improvement!")
  ```

### **2. Debugging Techniques**
#### **Crash Dump Analysis**
1. Generate a core dump:
   ```bash
   gcore <pid>  # Linux
   ```
2. Analyze with `gdb`:
   ```bash
   gdb ./your_app core
   bt  # Backtrace
   ```

#### **Replay Debugging**
- **User Sessions:** Use tools like [Dynatrace Replay](https://www.dynatrace.com/products/replay/) to recreate UI failures.
- **Custom Replay:** Record HTTP requests/responses in a database:
  ```json
  {
    "request": { "method": "POST", "url": "/api/v1/user", "body": { "name": "Alice" } },
    "response": { "status": 200, "latency_ms": 120 }
  }
  ```

#### **Distributed Debugging**
- **Service Mesh:** Debug via `envoy` or `linkerd`:
  ```bash
  kubectl logs -l app=envoy -c envoy
  ```
- **Ambient Tracing:** Sample spans without instrumenting:
  ```python
  tracer = trace.get_tracer(__name__)
  tracer.add_span_processor(open_telemetry.instrumentation.ambient_context.AmbientSpanProcessor())
  ```

---

## **Query Examples**
### **1. CPU Profiling (Linux `perf`)**
```bash
# Record CPU events for 10 seconds
perf record -F 99 -g -p <pid> -- sleep 10

# Generate flamegraph
perf script | ./stackcollapse-perf.pl | ./flamegraph.pl > cpu_usage.svg
```

### **2. Memory Leak Detection (Go `pprof`)**
```go
// Enable memory profiling
go tool pprof http://localhost:8080/debug/pprof/heap
```

### **3. Logs Query (ELK Stack)**
```json
GET /logs-*/_search
{
  "aggs": {
    "high_latency": {
      "filter": { "range": { "@timestamp": { "gte": "now-1d" } } },
      "aggs": {
        "error_types": { "terms": { "field": "error.type" } }
      }
    }
  }
}
```

### **4. Distributed Trace Query (Jaeger)**
```bash
# Query traces by operation name
curl -s "http://jaeger-ui:16686/search?service=payment-service&limit=100"
```

---

## **Related Patterns**
1. **Observability Pipeline**
   - *Complements:* Profiling & Debugging relies on metrics/logs/traces (MLOps, SLO-based alerting).

2. **Chaos Engineering**
   - *Synergizes:* Use failure injection (e.g., Gremlin) to validate debugging tooling robustness.

3. **Circuit Breaker**
   - *Context:* Debugging distributed failures often starts with isolating dependent services.

4. **Feature Flags**
   - *Enables:* Test fixes in production without full rollouts (e.g., A/B debug).

5. **Static Analysis**
   - *Preemptive:* Reduces runtime debugging by catching issues early (e.g., SonarQube).

---

**Key Takeaway:** Profiling & Debugging is iterative. Start with metrics, narrow scope with sampling, and validate fixes statistically. Tools like OpenTelemetry and eBPF reduce boilerplate, but understanding core concepts (flame graphs, chi-squared tests) ensures accurate diagnostics.