# **[Pattern] Debugging Technique Reference Guide**

---

## **Overview**
Debugging is the systematic process of identifying, analyzing, and resolving issues or bugs in software, hardware, or systems. This guide outlines core debugging techniques—**logging, tracing, breakpoints, watchpoints, profiling, assertions, and reverse debugging**—providing structured best practices, implementation details, and tools to streamline issue resolution.

Effective debugging minimizes downtime, improves reliability, and enhances developer productivity. Whether debugging distributed systems or low-level code, these techniques complement each other to create a robust debugging workflow. This guide assumes familiarity with basic programming concepts and development environments.

---

## **1. Key Concepts & Debugging Techniques**

### **Table 1. Debugging Technique Schema Reference**

| **Technique**          | **Description**                                                                 | **Use Case**                                                                 | **When to Use**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Logging**            | Recording events, errors, or runtime data to files or logs.                   | Tracking application flow, errors, or performance.                          | Early-stage development, production monitoring.                                 |
| **Tracing**            | Following the execution path via explicit trace events or stack traces.       | Debugging asynchronous or complex workflows (e.g., microservices).          | Deep-dive troubleshooting, distributed systems.                                 |
| **Breakpoints**        | Halting execution at a specific line of code to inspect variables/state.     | Inspecting variable values, function calls, or conditional logic.            | Interactive debugging in IDEs or CLI tools.                                      |
| **Watchpoints**        | Monitoring variable changes to trigger breakpoints dynamically.               | Detecting race conditions or unintended variable modifications.              | Memory or synchronization debugging.                                            |
| **Profiling**          | Measuring performance metrics (CPU, memory, latency) to identify bottlenecks.| Optimizing slow functions or high-memory usage.                             | Profiling highly performant or memory-intensive applications.                   |
| **Assertions**         | Validating assumptions at runtime (e.g., `assert(x > 0)`).                     | Catching logic errors or invalid states early.                                | Unit testing, pre-release validation.                                            |
| **Reverse Debugging**  | Replaying execution steps backward to identify root causes.                   | Analyzing crashes or unexpected states post-failure.                         | Post-mortem analysis, reproducible bugs.                                         |

---

## **2. Implementation Details**

### **2.1. Logging**
**Purpose:** Capture runtime data for later analysis.
**Key Components:**
- **Log Levels:** `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`.
- **Timestamps:** Include timestamps for chronological ordering.
- **Context:** Add request IDs, user sessions, or correlation IDs for distributed tracing.

**Example (Python):**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug("User logged in: %s", user_id)  # Logs with DEBUG level.
```

**Best Practices:**
- Avoid logging sensitive data (e.g., passwords).
- Use structured logging (JSON) for easier parsing:
  ```json
  {"timestamp": "2023-10-01T12:00:00", "level": "ERROR", "message": "Database connection failed"}
  ```

---

### **2.2. Tracing**
**Purpose:** Track execution flow across services.
**Tools:**
- **OpenTelemetry:** Standardized tracing for distributed systems.
- **Distributed IDs:** Correlate requests across services (e.g., `trace_id`, `span_id`).

**Example (Java with OpenTelemetry):**
```java
Tracer tracer = // Initialize tracer;
Span span = tracer.spanBuilder("processOrder").startSpan();
try (Scope scope = span.makeCurrent()) {
    // Business logic
    span.addEvent("Order processed");
} finally {
    span.end();
}
```

**Best Practices:**
- Instrument critical paths (e.g., payment processing).
- Sample traces to reduce overhead in production.

---

### **2.3. Breakpoints & Watchpoints**
**Purpose:** Pause execution for inspection.
**IDE Tools:**
- **VS Code:** Set breakpoints via gutter icons.
- **GDB (Linux):** Conditional breakpoints:
  ```bash
  break my_function if x == 5  # Break when x equals 5.
  ```

**Watchpoints (GDB):**
```bash
watch -l my_var  # Trigger on any modification to `my_var`.
```

**Best Practices:**
- Use conditional breakpoints to avoid noisy debugging.
- Combine with `printf` debug statements for lightweight checks.

---

### **2.4. Profiling**
**Purpose:** Identify performance bottlenecks.
**Tools:**
- **CPU Profiling:** `perf` (Linux), Xcode Instruments (macOS), Visual Studio Profiler (Windows).
- **Memory Profiling:** Heap dumps, Valgrind (`memcheck`).

**Example (Python `cProfile`):**
```python
import cProfile
cProfile.run("my_function()", sort="cumtime")  # Profiles by cumulative time.
```

**Best Practices:**
- Profile with representative workloads.
- Focus on top contributors (e.g., 80% of runtime).

---

### **2.5. Assertions**
**Purpose:** Validate assumptions at runtime.
**Syntax (Python):**
```python
assert x > 0, "x must be positive"  # Raises AssertionError if false.
```

**Use Cases:**
- Input validation (e.g., `assert len(data) > 0`).
- Logic checks (e.g., `assert sorted_list == sorted(data)`).

**Best Practices:**
- Disable assertions in production (`-O` flag in Python).
- Use for critical invariants, not general logging.

---

### **2.6. Reverse Debugging**
**Purpose:** Analyze crashes step-by-step backward.
**Tools:**
- **GDB Reverse Debugging:**
  ```bash
  gdb --reverse --exact my_program core
  ```
- **Windows Debugging Tools:** `WinDbg` with reverse debugging.

**Best Practices:**
- Requires symbolic debug info (`.pdb` files).
- Useful for analyzing core dumps or hung applications.

---

## **3. Query Examples**
### **Logging Queries (ELK Stack)**
```json
// Query logs for "database_error" in last 24h.
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "database_error" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  }
}
```

### **Tracing Queries (Jaeger)**
```bash
# Find all spans with error status in "payment-service".
jaeger query --service payment-service --operation payment --filter "tags.error==true"
```

### **Profiling Queries (Flame Graphs)**
```bash
# Generate flame graph from perf data.
perf script | stackcollapse-perf.pl | flamegraph.pl > profile.svg
```

---

## **4. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Observability**         | Combines logging, metrics, and tracing for system health monitoring.           | Production environments, DevOps workflows.                                      |
| **Chaos Engineering**     | Intentionally introduces failures to test resilience.                           | High-availability systems, disaster recovery planning.                          |
| **Unit Testing**          | Isolates code components for automated validation.                             | Early-stage debugging, regression testing.                                     |
| **Error Handling**        | Structures how errors are caught and propagated.                              | Robust applications, graceful degradation.                                     |
| **Heap Profiling**        | Analyzes memory allocation patterns.                                           | Memory leaks, garbage collection tuning.                                        |

---

## **5. Troubleshooting**
| **Issue**                  | **Solution**                                                                   |
|----------------------------|-------------------------------------------------------------------------------|
| Logs are too verbose.      | Filter log levels or use structured logging.                                   |
| Breakpoints not hit.       | Check breakpoint conditions or IDE settings.                                   |
| Profiling overhead high.   | Sample profiles instead of full traces.                                        |
| Reverse debugging fails.   | Ensure debug symbols are available.                                           |
| Tracing IDs lost.          | Enforce correlation IDs across services.                                       |

---
**See Also:**
- [Logging Best Practices](https://www.google.com/search?q=logging+best+practices)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)

---
**Last Updated:** 2023-10-01
**Version:** 1.2