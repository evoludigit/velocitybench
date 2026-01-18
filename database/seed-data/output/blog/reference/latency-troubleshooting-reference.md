# **[Pattern] Latency Troubleshooting: Reference Guide**

---

## **Overview**
Latency troubleshooting involves identifying, diagnosing, and resolving performance bottlenecks that cause delays in system responses, transactions, or data processing. This pattern provides a structured approach to detecting latency issues, analyzing root causes (e.g., network congestion, inefficient algorithms, hardware limitations), and applying optimizations. Targeted at **developers, DevOps engineers, and performance analysts**, this guide outlines key metrics, tools, and troubleshooting steps to minimize response times in distributed systems, APIs, databases, and applications.

---

## **Key Concepts**
Latency is the time delay between a request and its response. Common latency sources include:
- **Network latency** (TTFB, packet loss, ISP throttling).
- **Application latency** (slow queries, I/O bottlenecks, serialization overhead).
- **Infrastructure latency** (CPU throttling, disk I/O, memory swapping).
- **Dependencies** (third-party APIs, external services, caching misses).

---

## **Schema Reference**
| **Category**               | **Metric**                     | **Description**                                                                 | **Tools/Metrics**                                                                 |
|----------------------------|--------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Network Latency**         | TTFB (Time to First Byte)      | Time from client request to first byte received.                                | `curl -w "%{time_first_byte}"`, APM tools (New Relic, Datadog)                   |
|                            | Round-Trip Time (RTT)          | Time for a packet to travel to a server and back.                                | `ping`, `mtr`, network monitoring tools                                           |
|                            | Packet Loss (%)                | Percentage of lost packets between client and server.                            | `ping -l`, Wireshark, `nping`                                                     |
| **Application Latency**    | Response Time (P50/P90/P99)    | Percentile latencies (e.g., 90% of requests take ≤ X ms).                       | APM tools, Prometheus, Grafana, APM SDKs                                          |
|                            | DB Query Execution Time        | Time taken by a single database query.                                          | Database logs, `EXPLAIN`, `Slow Query Log`                                        |
|                            | Serialization Overhead         | Time spent converting data (e.g., JSON/XML) for transmission.                   | Profiling tools (e.g., `pprof` for Go, `async-profiler` for Java)                |
| **Infrastructure Latency** | CPU Usage (%)                  | Percentage of CPU cycles utilized by a process.                                  | `top`, `htop`, Prometheus metrics (`process_cpu_usage`)                           |
|                            | Disk I/O Latency               | Time taken for disk read/write operations.                                       | `iostat`, `vmstat`, `fio`, database storage engines (e.g., InnoDB stats)         |
|                            | Memory Swap (%)                | Percentage of memory swapped to disk.                                            | `free -h`, `vmstat`, `top`                                                       |
| **Dependencies**           | Third-Party API Latency        | Response time from external services.                                            | API monitoring (e.g., Postman, Locust), circuit breakers (Hystrix, Resilience4j) |
|                            | Cache Hit/Miss Rate            | Ratio of successful vs. failed cache lookups.                                    | Redis/Memcached metrics, APM tools                                                |

---

## **Implementation Steps**

### **1. Measure Baseline Latency**
- **Tools**: Use `curl`, `ab` (Apache Benchmark), or distributed tracing (Jaeger, OpenTelemetry).
  ```bash
  # Measure TTFB with curl
  curl -o /dev/null -s -w "%{time_first_byte}" http://example.com/api/endpoint

  # Load test with ab
  ab -n 1000 -c 50 http://example.com/api/endpoint
  ```
- **Key Metrics**:
  - **P50/P90/P99**: Identify outliers (e.g., 99th percentile > 1s indicates spikes).
  - **TTFB**: High TTFB often points to server-side bottlenecks.

### **2. Isolate Latency Sources**
Use the **5 Whys** or **Bulkhead Pattern** to narrow down issues:
1. **Network**: Check RTT, packet loss, and DNS resolution (`dig example.com`).
2. **Application**: Profile slow endpoints (e.g., database queries, external calls).
3. **Infrastructure**: Monitor CPU, memory, and disk I/O under load.
4. **Dependencies**: Trace external API calls (e.g., using OpenTelemetry).

#### **Query Examples**
##### **Database Query Analysis**
```sql
-- Check slow queries (PostgreSQL example)
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- Redis latency monitoring
INFO commandstats | grep latency
```

##### **Tracing Latency with OpenTelemetry**
```bash
# Instrument a Node.js app with OpenTelemetry
npm install @opentelemetry/sdk-node @opentelemetry/exporter-jaeger
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { JaegerExporter } = require('@opentelemetry/exporter-jaeger');
const { registerInstrumentations } = require('@opentelemetry/instrumentation');

const provider = new NodeTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(new JaegerExporter()));
provider.register();
registerInstrumentations({ instrumentations: [new HttpInstrumentation()] });
```

##### **Network Diagnostics**
```bash
# Check RTT and packet loss to a server
mtr example.com

# Trace path with traceroute
traceroute example.com

# Check firewall/NAT delays
ping -I eth0 example.com
```

### **3. Common Optimizations**
| **Root Cause**               | **Solution**                                                                 | **Tools/Techniques**                                                                 |
|------------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Slow DB Queries              | Index optimization, query tuning, connection pooling.                          | `EXPLAIN ANALYZE`, `pg_stat_statements`, Connection Pooling (HikariCP, PgBouncer)   |
| High Network Latency         | CDN, edge caching, protocol optimization (QUIC, HTTP/3).                      | Cloudflare, Varnish, nghttp3                                                              |
| CPU Bottlenecks              | Vertical scaling, multithreading, JIT compilation (GraalVM).                  | `perf`, `flamegraphs`, Kubernetes HPA (Horizontal Pod Autoscaler)                     |
| External API Latency         | Circuit breakers, retries with backoff, async processing.                     | Resilience4j, Hystrix, Kafka for async workflows                                       |
| Memory Pressure              | Garbage collection tuning, off-heap memory (e.g., MappedByteBuffer).         | JVM flags (`-Xmx`, `-XX:+UseG1GC`), Valgrind (for C/C++)                                |

### **4. Automated Monitoring**
- **APM Tools**: New Relic, Datadog, Dynatrace (track P99 latencies).
- **Synthetic Monitoring**: Pingdom, UptimeRobot (simulate user requests).
- **Alerting**: Prometheus + Alertmanager (alert on P99 > threshold).

**Example Alert Rule (Prometheus):**
```yaml
- alert: HighLatency
  expr: api_latency_seconds{quantile="0.99"} > 1000
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High API latency (instance {{ $labels.instance }})"
```

### **5. Validate Fixes**
- **A/B Testing**: Compare latencies before/after changes.
- **Chaos Engineering**: Use tools like Gremlin to simulate failures.
- **Canary Releases**: Roll out fixes to a subset of users first.

---

## **Related Patterns**
1. **[Performance Optimization Patterns](https://patterns.dev/performance-optimization)**
   - Caching Strategies (Local, Distributed, CDN).
   - Algorithmic Efficiency (Big-O Analysis, Data Structure Choices).
2. **[Resilience Patterns](https://patterns.dev/resilience)**
   - Circuit Breaker (Prevent cascading failures).
   - Retry with Backoff (Handle transient errors gracefully).
3. **[Observability Patterns](https://patterns.dev/observability)**
   - Distributed Tracing (Jaeger, Zipkin).
   - Log Aggregation (ELK Stack, Loki).
4. **[Scalability Patterns](https://patterns.dev/scalability)**
   - Load Balancing (Round Robin, Least Connections).
   - Sharding (Horizontal Partitioning).
5. **[Caching Patterns](https://patterns.dev/caching)**
   - Cache Asynchrony (Pre-fetching, Lazy Loading).
   - Cache Stampede Mitigation (Token Bucket, Locking).

---

## **Best Practices**
1. **Monitor Proactively**: Use SLOs (Service Level Objectives) to define latency budgets.
2. **Isolate Latency**: Use tools like OpenTelemetry to trace requests end-to-end.
3. **Test Under Load**: Simulate production traffic with Locust or k6.
4. **Document Changes**: Track latency regression risks in pull requests (e.g., via SonarQube).
5. **Optimize Iteratively**: Focus on the 80/20 rule—address the biggest bottlenecks first.

---
**See Also**:
- [Latency vs. Throughput](https://www.brendangregg.com/latency.html)
- [Latency Numbers Everyone Should Know](https://www.igvita.com/2014/03/27/latency-numbers-everyone-should-know/)