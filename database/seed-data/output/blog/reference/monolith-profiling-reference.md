# **[Pattern] Monolith Profiling – Reference Guide**

---

## **1. Overview**
**Monolith Profiling** is a performance investigation pattern used to analyze runtime behavior in **large, tightly coupled applications (monoliths)**. Unlike microservices, monoliths lack clear service boundaries, making profiling challenging but critical for identifying bottlenecks in CPU, memory, I/O, or network latency.

This pattern involves:
- **Instrumentation**: Integrating profiling tools (e.g., Java Flight Recorder, Py-Spy, or CPU profilers).
- **Data Collection**: Capturing execution traces, heap dumps, and thread activity.
- **Analysis**: Using visual tools (e.g., JFR, Perf, or Grafana) to identify:
  - Hot methods (CPU/memory hotspots).
  - GC (Garbage Collection) pauses.
  - Lock contention or deadlocks.
- **Actionable Insights**: Guiding optimizations like algorithm tuning, cache improvements, or refactoring.

Monolith profiling is essential for **legacy systems**, **microservice consolidation**, or **large-scale monolithic applications** where granular tracing is impossible.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**          | **Description**                                                                 | **Example Tools**                     |
|------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **Profiling Agent**    | Instrumentation runtime (e.g., JVM agent, Python profiler) to capture data.     | Java Flight Recorder (JFR), Py-Spy    |
| **Data Collection**    | Records execution traces, heap usage, or event logs.                            | CPU flame graphs, GC logs, thread dumps |
| **Analysis Tool**      | Visualizes data to pinpoint bottlenecks.                                       | YourKit, JProfiler, Perf (Linux)      |
| **Filtering**          | Focuses on critical paths (e.g., high CPU usage, long GC cycles).               | Custom JFR queries, Perf scripts      |
| **Action Plan**        | Recommendations for fixes (e.g., reduce allocations, optimize DB queries).      | Code reviews, benchmarking            |

---

### **2.2 Profiling Strategies**
| **Strategy**           | **Use Case**                                  | **Tools/Techniques**                          |
|------------------------|-----------------------------------------------|-----------------------------------------------|
| **CPU Profiling**      | Identify slow methods or thread starvation.   | JFR CPU Sampling, Perf (Linux), VTune (Intel) |
| **Memory Profiling**   | Detect memory leaks or high heap usage.      | JFR Heap Dump, Valgrind (C), HeapHero       |
| **Thread Profiling**   | Find deadlocks or lock contention.           | Thread Dump Analysis, JFR Thread Profiling   |
| **I/O Profiling**      | Analyze slow disk/network operations.         | JFR File I/O, Perf I/O Latency Analysis     |
| **Database Profiling** | Optimize SQL queries or connection pooling.   | PgBadger, Slow Query Logs, Explain Plans    |

---

### **2.3 When to Use This Pattern**
✅ **Legacy Monoliths**: No microservices decomposition yet.
✅ **High-Latency Issues**: Users report slow responses.
✅ **Memory Leaks**: Unexpected OOM errors or growing heap.
✅ **Unstable Production**: Frequent crashes or timeouts.
✅ **Pre-Migration Analysis**: Before splitting into services.

❌ **Avoid if**:
- The app is already split into microservices (use **Distributed Tracing** instead).
- The issue is clearly a database schema problem (use **Query Optimization** patterns).

---

## **3. Schema Reference**

### **3.1 Profiling Data Structure (Example: JFR)**
| **Field**               | **Type**   | **Description**                                                                 | **Example Value**                     |
|-------------------------|------------|-------------------------------------------------------------------------------|----------------------------------------|
| `event`                 | String     | Type of profiling event (e.g., `jvm/gc-start`, `jvm/thread-park`).              | `"jvm/gc-start"`                      |
| `timestamp`             | Timestamp  | When the event occurred (nanoseconds since epoch).                           | `1712345678901234`                    |
| `thread`                | String     | Thread name or ID (e.g., `Thread-1`).                                        | `"main"`                               |
| `method`                | String     | Fully qualified method (e.g., `java.util.concurrent.locks.ReentrantLock.lock`). | `"com.example.service.OrderService.processOrder"` |
| `cpu_time`              | Numeric    | CPU time consumed (microseconds).                                             | `123456`                               |
| `heap_memory`           | Numeric    | Memory allocated (bytes).                                                     | `5242880` (5MB)                        |
| `exception`             | String     | Exception details (if any).                                                   | `"java.lang.OutOfMemoryError"`         |
| `db_query`              | String     | SQL query (for database profiling).                                          | `"SELECT * FROM users WHERE active = true"` |

---

## **4. Query Examples**
Below are **JFR (Java Flight Recorder) query examples** to extract key metrics. These can be run in tools like **VisualVM** or **JFR IDE Plugins**.

### **4.1 Find Top CPU-Consuming Methods**
```sql
-- Query: Methods consuming > 100ms CPU time
SELECT
    method,
    SUM(duration) AS total_cpu_time_ms,
    COUNT(*) AS call_count
FROM jstack.details
WHERE duration > 100000 AND class = 'java.lang.Thread'
GROUP BY method
ORDER BY total_cpu_time_ms DESC
LIMIT 10;
```

### **4.2 Detect Long GC Pauses**
```sql
-- Query: GC events with pause > 500ms
SELECT
    jvm.gc-start.start_time,
    jvm.gc-start.gc_type,
    jvm.gc-start.duration_ms,
    jvm.gc-start.heap_before_bytes,
    jvm.gc-start.heap_after_bytes
FROM jvm.gc-start
WHERE duration_ms > 500
ORDER BY duration_ms DESC;
```

### **4.3 Identify Thread Contention**
```sql
-- Query: Threads waiting for locks
SELECT
    thread,
    COUNT(*) AS contention_count,
    AVG(blocking_time_ms) AS avg_blocking_time
FROM jstack.thread
WHERE blocking_object IS NOT NULL
GROUP BY thread
ORDER BY contention_count DESC;
```

### **4.4 Database Query Profiling (PostgreSQL Example)**
```sql
-- Slow queries (execution > 1s)
SELECT
    query,
    execution_count,
    total_exec_time,
    avg_exec_time,
    rows_fetched
FROM pg_stat_statements
WHERE avg_exec_time > 1000
ORDER BY avg_exec_time DESC
LIMIT 20;
```

### **4.5 Memory Leak Analysis (Heap Dump Example)**
```sql
-- Objects leaking (e.g., unreferenced instances)
SELECT
    class_name,
    instance_count,
    retained_size_bytes,
    reference_paths
FROM heap_dump_analysis
WHERE instance_count > 1000
ORDER BY retained_size_bytes DESC;
```

---

## **5. Step-by-Step Workflow**
### **Step 1: Instrument the Monolith**
- **Java**: Enable JFR (`-XX:StartFlightRecording=filename=profile.jfr`).
- **Python**: Use `cProfile` or `Py-Spy` (`py-spy top --pid <PID>`).
- **Node.js**: Integrate `clinic.js` or `peed`.
- **Go**: Use `pprof` (`go tool pprof http://localhost:6060/debug/pprof`).

### **Step 2: Collect Data**
- Run the app under **load** (simulate production traffic).
- Capture:
  - **CPU**: Flame graphs (e.g., `flamegraph.pl`).
  - **Memory**: Heap dumps (`jmap -dump:format=b,file=heap.hprof <PID>`).
  - **Threads**: Thread dumps (`jstack <PID>`).

### **Step 3: Analyze with Tools**
| **Tool**          | **Purpose**                          | **Example Command**                     |
|--------------------|---------------------------------------|------------------------------------------|
| **VisualVM**       | Java heap/CPU profiling.              | `visualvm`                               |
| **JFR IDE Plugins**| Advanced JFR query analysis.          | Eclipse/JDK Mission Control              |
| **Perf (Linux)**   | System-wide CPU/I/O profiling.        | `perf record -g -p <PID>`                |
| **YourKit**        | Commercial deep code analysis.         | `--yourkit` JVM flag                     |
| **Grafana + Prometheus** | Metrics visualization.           | `prometheus(query="jvm_memory_used_bytes")` |

### **Step 4: Identify Bottlenecks**
- **Hot Methods**: Look for methods with high `cpu_time` or `duration`.
- **GC Pressure**: Check `jvm.gc-start.duration_ms`.
- **Locks**: Threads with `BLOCKED` state in thread dumps.
- **I/O**: Slow DB queries or file operations.

### **Step 5: Optimize & Validate**
- **Code Changes**: Refactor hot methods, reduce allocations.
- **Database**: Optimize queries, add indexes.
- **Monitor**: Re-profile post-fix to confirm improvements.

---

## **6. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **Use Case**                                  |
|---------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Distributed Tracing]**            | Trace requests across microservices.                                        | Post-monolith decomposition.                 |
| **[Query Optimization]**             | Reduce slow database queries.                                               | High-latency DB operations.                   |
| **[Circuit Breaker]**                | Prevent cascading failures in fault-tolerant apps.                           | Resilient microservices.                     |
| **[Microservice Decomposition]**     | Split monolith into smaller services.                                       | Long-term scaling of large monoliths.        |
| **[Load Testing]**                   | Simulate production traffic to find bottlenecks.                            | Performance validation.                      |
| **[Memory Leak Detection]**           | Find and fix memory leaks in Java/Python apps.                               | Unbounded memory growth.                     |

---

## **7. Best Practices**
1. **Profile Under Load**: Never analyze idle apps.
2. **Focus on Critical Paths**: Start with high-traffic endpoints.
3. **Avoid Over-Profiling**: Too much data slows down the app.
4. **Correlate with Metrics**: Combine profiling with APM tools (New Relic, Datadog).
5. **Document Findings**: Share results with the team (e.g., as a **Radar Chart** of bottlenecks).
6. **Automate Profiling**: Integrate into CI/CD (e.g., run JFR on every build).

---
## **8. Common Pitfalls & Fixes**
| **Pitfall**                          | **Cause**                              | **Solution**                                  |
|---------------------------------------|----------------------------------------|-----------------------------------------------|
| **False Positives in CPU Profiling**  | Noise from GC or JIT compilation.      | Use **sampling mode** (JFR `-s cpu`).         |
| **Heap Dump Too Large**               | High memory usage.                     | Limit dump size (`jmap -dump:size=512m`).      |
| **Thread Dump Misses Deadlocks**      | Deadlock occurs between dumps.         | Use **jstack + repeat** (every 5 seconds).    |
| **Database Profiling Overhead**       | Query logging slows down the app.      | Use **slow query logs** (PostgreSQL `log_min_duration_statement`). |
| **Profiling Slows Down the App**      | Heavy instrumentation (e.g., `assert`). | Reduce sampling rate or profile in staging.   |

---
## **9. Further Reading**
- [Oracle JFR Guide](https://docs.oracle.com/en/java/javase/17/jfr/jfr-guide.html)
- [Brendan Gregg’s Perf Tools](https://www.brendangregg.com/perf.html)
- [Java Profiling Best Practices](https://www.baeldung.com/java-profiling)
- [Py-Spy Documentation](https://github.com/joernhees/py-spy)

---
**Last Updated:** `[Insert Date]` | **Version:** `1.2`