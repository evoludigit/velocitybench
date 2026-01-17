---

# **[Pattern] Profiling Setup Reference Guide**

---
## **Overview**
The **Profiling Setup** pattern enables systematic analysis of application behavior by collecting runtime data (e.g., CPU usage, memory allocation, I/O latency) to debug performance bottlenecks, memory leaks, or architectural inefficiencies. This guide outlines how to configure profiling tools (e.g., Java Flight Recorder, VisualVM, or CPU profilers) to capture metrics reliably while minimizing overhead. Use cases include:
- **Debugging slow endpoints** in microservices.
- **Optimizing database queries** or ORM operations.
- **Monitoring long-running processes** (e.g., batch jobs).
- **Profiling memory-heavy applications** (e.g., caching layers).

Key trade-offs:
✅ *Low overhead* (if sampling-based).
⚠️ *High overhead* (if full instrumentation).
🔹 *Tool selection* depends on language/runtime (e.g., JVM, .NET, Python).

---

## **1. Schema Reference**
Below is a standardized schema for profiling configurations. Values depend on the profiling tool (replace `<tool>` with specific tool terms, e.g., `JFR` for Java Flight Recorder).

| **Parameter**               | **Description**                                                                                     | **Default**               | **Example Values**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------|------------------------------------------------------------------------------------|
| **Sampling Method**         | How data is captured: *CPU*, *Memory*, *Heap*, *Thread*, or *Custom* events.                       | CPU                      | `CPU`, `Heap`, `GC (Garbage Collection)`                                           |
| **Sampling Rate**           | Frequency of samples (e.g., 10ms = 100 samples/sec). Defaults vary by tool.                        | Tool-specific            | `1ms`, `50ms` (higher = less overhead, lower = more detail)                       |
| **Sampling Scope**          | Targets for profiling: *All threads*, *Specific thread groups*, or *Custom filters*.            | All threads              | `com.example.service.*`, `threadPool-0`                                           |
| **Memory Allocation Tracking** | Enables tracking of heap allocations. Requires sufficient disk space.                          | Disabled                 | `Enabled`, `Sampling (5s interval)`                                                 |
| **Event Logging**           | Enables recording of runtime events (e.g., GC pauses, method calls).                               | Disabled                 | `GC Events`, `Method Entry/Exit`                                                    |
| **Disk Output**             | Configures where to store profiling data (e.g., `/tmp/profiler`, `S3 bucket`).                   | Current dir              | `/opt/profiler/data`, `s3://my-bucket/profiles`                                   |
| **Sampling Duration**       | How long to collect data (seconds). Defaults to tool-specific limits (e.g., 1h for JFR).         | Infinite                  | `30s`, `60m`                                                                       |
| **Filter Expressions**      | Regex or condition-based filtering (e.g., exclude `java.lang.*`).                                  | None                     | `exclude com.util.helper.*`, `methodName = "processOrder"`                        |
| **Profiling Context**       | Additional context (e.g., HTTP headers, environment variables) attached to samples.              | None                     | `userId: <request.header.X-User-ID>`, `env: dev`                                  |

---
**Note:** Consult the tool’s documentation for schema extensions (e.g., [Async Profiler](https://github.com/jvm-profiling-tools/async-profiler) supports `stack_collection_period`).

---

## **2. Implementation Details**
### **2.1 Key Concepts**
- **Sampling vs. Full Profiling**:
  - *Sampling*: Low overhead; periodic snapshots (e.g., every 5ms). Use for broad trends.
  - *Full Profiling*: High overhead; continuous instrumentation (e.g., method tracing). Use for deep dives.
- **Runtime Overhead**:
  - **CPU Profiling**: Typically <5% overhead.
  - **Memory Profiling**: Can spike GC pauses by 20–30% if enabled aggressively.
- **Data Storage**:
  - Profiling data is binary (e.g., `.jfr` for JFR, `.heapdump` for JVM). Convert to human-readable formats (e.g., with [Async Profiler GUI](https://github.com/jvm-profiling-tools/async-profiler) or [JFR Tools](https://github.com/chetanmehta/java-flight-recorder-tools)).

### **2.2 Tool-Specific Notes**
| **Tool**               | **Setup Command**                                                                 | **Key Flags/Parameters**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Java Flight Recorder (JFR)** | `java -XX:+FlightRecorder -XX:StartFlightRecording=duration=60s,filename=profile.jfr -jar app.jar` | `filename`, `settings=profile`, `compression=none` (for large logs)                     |
| **Async Profiler**      | `sudo ./profiler.sh -d 30 -f /tmp/profile flame`                                   | `-d` (duration), `-f` (output), `--stack` (stack traces), `--pid <PID>` (attach)         |
| **VisualVM**            | Attach via `jstack -l <PID>` or add to IDE runtime args: `-agentpath:/path/to/libvisualvm.so=port=1080` | `--debug` (enable remote debugging)                                                      |
| **.NET Profiling**      | `dotnet --profile <profileName> run`                                                | `<profileName>`: `dotnet-tracing`, `perfcollect` (collects CPU, memory, GC)             |
| **Python (cProfile)**   | `python -m cProfile -o profile.prof script.py`                                        | `-o` (output file), `--sort=calls` (sort by call count)                                 |

---

## **3. Query Examples**
### **3.1 CPU Profiling (Async Profiler)**
**Command:**
```bash
sudo ./profiler.sh -d 60 -f /tmp/cpu_profile -e flame --pid $(pgrep -f "app.jar")
```
**Output Analysis:**
- Open `/tmp/cpu_profile` with the [Async Profiler GUI](https://github.com/jvm-profiling-tools/async-profiler).
- Identify hot methods (e.g., `sort()` in a loop) or blocked threads (long green bars).

**Filter for High-CPU Methods:**
```bash
# Use JFR tools to extract top methods:
jfr-viewer profile.jfr --query "event=method/profiled AND cpu>0.1" --sort=cpu
```

### **3.2 Memory Profiling (JFR)**
**Command:**
```bash
java -XX:+FlightRecorder -XX:StartFlightRecording=filename=mem_profile.jfr,settings=memory -jar app.jar
```
**Key Queries:**
1. **Heap Allocations**:
   ```bash
   jfr-viewer mem_profile.jfr --query "event=alloc_object AND class=java.util.HashMap"
   ```
2. **GC Pauses**:
   ```bash
   jfr-viewer mem_profile.jfr --chart=gc --duration=20s
   ```

### **3.3 Thread Profiling**
**Command (Async Profiler):**
```bash
sudo ./profiler.sh -d 30 -f /tmp/thread_profile --threads 10 --pid $(pgrep -f "app.jar")
```
**Identify Thread Contention:**
- Look for threads stuck in `BLOCKED` or `WAITING` states in the GUI.
- Example filter:
  ```bash
  jstack <PID> | grep BLOCKED
  ```

### **3.4 Custom Event Tracking**
**Example (Java Agent):**
Add to `application.properties` (Spring Boot):
```properties
spring.main.jvm-args=-javaagent:/path/to/agent.jar=config=custom-events
```
**Agent Config (`agent.properties`):**
```properties
# Log HTTP request durations
event.class=com.example.ProfilingAgent
event.method=onRequest
event.params=uri,responseTime
```

---

## **4. Best Practices**
### **4.1 Minimizing Overhead**
- **Prioritize Sampling**: Use `-d 10ms` (CPU) or `-f duration=30s` (Async Profiler) for low-overhead profiles.
- **Target Specific Methods**: Exclude known fast paths (e.g., `com.util.helper.*`) in filters.
- **Schedule Profiling**: Run during low-traffic periods (e.g., `cron job` with `pm2` for Node.js).

### **4.2 Data Storage**
- **Clean Up Old Data**: Automation:
  ```bash
  find /opt/profiler/data -name "*.jfr" -mtime +7 -delete
  ```
- **Compress Large Logs**: Use `tar` or `gzip` for JFR files:
  ```bash
  tar -czf profile.tar.gz /tmp/profile.jfr
  ```

### **4.3 Tool-Specific Tips**
| **Tool**       | **Tip**                                                                                     |
|-----------------|--------------------------------------------------------------------------------------------|
| **JFR**         | Enable `settings=profile` for balanced CPU/memory profiling.                               |
| **Async Profiler** | Use `--stack` for detailed stack traces (higher overhead).                                   |
| **VisualVM**    | Prefer "Sampler" thread for low-overhead CPU profiling.                                     |
| **.NET**        | Combine `dotnet-tracing` (CPU) with `perfcollect` (memory) for comprehensive profiles.    |

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Bulkhead Pattern]**           | Isolate profiling workloads to prevent cascading failures during memory-heavy profiling.           | Profiling in high-traffic environments.                                                             |
| **[Circuit Breaker]**            | Protect profiling endpoints from cascading failures if tool metrics overload the system.         | When profiling tools trigger high latency in dependent services.                                   |
| **[Distributed Tracing]**       | Correlate profiling data with traces (e.g., OpenTelemetry) for end-to-end analysis.              | Debugging latency in distributed systems (e.g., microservices).                                    |
| **[Feature Toggles]**            | Enable/disable profiling dynamically (e.g., via feature flags) to test configurations.           | A/B testing profiling impact on production performance.                                             |
| **[Observability Pipeline]**     | Ingest profiling data into a time-series database (e.g., Prometheus) for long-term analysis.    | Monitoring trends over time (e.g., memory growth).                                                 |

---

## **6. Troubleshooting**
| **Issue**                          | **Root Cause**                                  | **Solution**                                                                                     |
|-------------------------------------|--------------------------------------------------|---------------------------------------------------------------------------------------------------|
| High CPU overhead (>10%)           | Full profiling enabled.                          | Switch to sampling (`-d 10ms` in Async Profiler).                                               |
| Profiling tool crashes              | Permissions on `/tmp` or out-of-disk-space.     | Run as `sudo` or increase disk space: `df -h`.                                                   |
| Missing critical methods           | Filter too restrictive.                          | Loosen filters (e.g., `exclude com.util.helper` → `exclude com.util.helper.*`).                 |
| JFR log corruption                  | Disk I/O errors.                                | Use `compression=none` or profile to a network share (e.g., `s3://`).                           |
| Thread sampling skipped            | Tool not attached to target process.             | Verify PID: `pgrep -f "app.jar"`. Attach manually with `sudo ./profiler.sh --pid <PID>`.          |

---

## **7. Example Workflow**
### **Scenario**: Debug high memory usage in a Spring Boot app.
1. **Start Profiling**:
   ```bash
   java -XX:+FlightRecorder -XX:StartFlightRecording=duration=60s,filename=mem.jfr,settings=memory -jar app.jar
   ```
2. **Reproduce Issue**: Load-test with `locust` or simulate traffic:
   ```bash
   locust -f test_locust.py --host=http://localhost:8080
   ```
3. **Analyze**:
   ```bash
   jfr-viewer mem.jfr --query "event=heap/alloc_object AND class=com.example.DatabaseCache"
   ```
4. **Optimize**: Refactor `DatabaseCache` to use `SoftReference` or reduce allocation frequency.
5. **Validate**: Rerun profiling to confirm memory usage drops.

---
**References**:
- [Async Profiler Docs](https://github.com/jvm-profiling-tools/async-profiler)
- [JFR User Guide](https://docs.oracle.com/en/java/javase/17/docs/specs/man/jcmd.html#jcmd-flightrecorder)
- [VisualVM Guide](https://visualvm.github.io/)