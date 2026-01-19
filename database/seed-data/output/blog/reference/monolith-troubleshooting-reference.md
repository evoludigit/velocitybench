# **[Pattern] Monolith Troubleshooting Reference Guide**

---

## **Overview**
A **Monolith Troubleshooting** pattern is a structured approach to diagnosing, isolating, and resolving issues in a monolithic application. Unlike microservices, monoliths bundle all components (logic, data, and services) into a single executable, making diagnostic challenges distinct: **resource contention, cascading failures, and performance bottlenecks** often interact across tightly coupled layers. This guide provides structured steps, tools, and techniques to efficiently troubleshoot common and critical issues while minimizing downtime.

---

## **Key Concepts & Implementation Details**

| **Concept**               | **Description**                                                                                     | **Example Scenario**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Benchmark Baseline**    | Establish a normalized performance baseline to detect anomalies.                                   | Compare current CPU/memory usage against historical logs during peak traffic.       |
| **Layered Decomposition** | Isolate issues in the **frontend, business logic, database, or networking** layers.               | Slow API responses may stem from ORM inefficiencies or slow database queries.         |
| **Dependency Mapping**    | Identify external dependencies (e.g., APIs, external services) and their failure points.         | A 3rd-party payment service timeout delays transaction processing.                    |
| **Circuit Breaking**      | Mitigate cascading failures by failing fast and retrying.                                          | Disable DB connections after X retries to prevent resource exhaustion.                 |
| **Distributed Tracing**   | Track requests across layers using tools like OpenTelemetry.                                       | Trace a request from the API gateway through business logic to database and back.     |
| **Log Correlation**       | Use unique request IDs to correlate logs across microservices (if applicable) or monolith layers.  | Group logs by `X-Request-ID` to track a user’s session.                               |
| **Profiling & Bottlenecks**| Use **CPU, memory, and I/O profiling** (e.g., `pprof`, VisualVM) to identify hotspots.             | A `for` loop with linear search on 50K records slows execution.                       |
| **Dependency Injection Analysis** | Check for **hard dependencies** (e.g., global state, static variables) that cause race conditions. | A shared cache used across threads without synchronization leads to corrupted data.    |
| **Load Testing Simulation** | Reproduce production-like conditions in staging to validate fixes.                                 | Simulate 10K concurrent users to confirm a caching optimization works.               |
| **Rollback Strategy**     | Define rollback steps (e.g., reverting to a stable commit, disabling new features).                 | Revert a recent config change if it caused a memory leak.                           |

---

## **Schema Reference**
Below are key data structures and patterns used in monolith troubleshooting.

| **Schema**                     | **Structure**                                                                                     | **Purpose**                                                                                     |
|--------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Error Log Entry**           | `{ timestamp, severity, component, request_id, stack_trace, metadata }`                       | Capture structured errors for correlation and analysis.                                        |
| **Performance Metric**        | `{ metric_name (CPU, memory, latency), value, timestamp, layer (API/DB) }`                     | Track real-time performance to detect anomalies.                                             |
| **Dependency Graph**          | `{ service_name, dependencies (URLs, ports), health_status, last_failure }`                     | Visualize service dependencies to diagnose cascading failures.                                |
| **Request Trace**             | `{ trace_id, steps (API → ServiceA → DB → ServiceB), timestamps, errors }`                     | Trace a request’s journey through the system.                                                  |
| **Build Config**              | `{ framework (Spring Boot, Django), dependencies, version, build_timestamp }`                   | Compare configs to identify misconfigurations.                                                |
| **User Session Context**      | `{ user_id, session_id, start_time, last_activity, errors }`                                    | Correlate user actions with application behavior.                                             |

---

## **Troubleshooting Workflow**
Follow this structured approach when diagnosing issues:

### **Step 1: Reproduce the Issue**
- **Check Logs**: Filter by `ERROR`/`CRITICAL` severity using tools like:
  - `grep "ERROR" /var/log/app.log | tail -n 50`
  - ELK Stack (Elasticsearch + Logstash + Kibana) for structured logs.
- **User Reports**: Gather symptoms (e.g., "checkout fails after 3 minutes").
- **Reproduce in Staging**: Use **feature flags** to isolate the problematic behavior.

### **Step 2: Isolate the Layer**
Use **layered decomposition** to narrow down the issue:

| **Layer**       | **Diagnostic Tools**                          | **Example Check**                                                                 |
|-----------------|-----------------------------------------------|-----------------------------------------------------------------------------------|
| **Frontend**    | Browser DevTools, HAR files                    | Test API endpoints with `curl` or Postman directly.                                 |
| **Business Logic** | IDE Debugger (e.g., IntelliJ, VS Code)      | Step through code with breakpoints for logic errors.                               |
| **Database**    | `EXPLAIN ANALYZE` (PostgreSQL), `SHOW PROFILE` (MySQL) | Check slow queries with `pg_stat_statements`.                                     |
| **Network**     | Wireshark, `tcpdump`, `ping`/`mtr`           | Detect packet loss or latency between service tiers.                                 |
| **External Dependencies** | `curl`, Prometheus Alerts                   | Verify 3rd-party API responses (e.g., `curl -v https://api.paypal.com/v1/payments`). |

### **Step 3: Analyze Bottlenecks**
- **CPU/Memory Profiling**:
  ```bash
  # Linux CPU profiling with perf
  perf record -g ./my_monolith
  perf report --stdio
  ```
- **Database Bottlenecks**:
  ```sql
  -- PostgreSQL slow query log
  SET log_min_duration_statement = 100; -- Log queries >100ms
  -- Analyze query plans
  EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active';
  ```
- **API Latency**:
  Use `netdata` or `Prometheus` to track:
  - `http_request_duration_seconds` (histogram).
  - `jvm_gc_time_seconds` (for JVM-based apps).

### **Step 4: Fix & Validate**
- **Temporary Fixes**:
  - Add **rate limiting** (e.g., `guava RateLimiter`) for API endpoints.
  - Enable **connection pooling** (e.g., HikariCP for JDBC).
- **Permanent Fixes**:
  - Refactor slow loops (e.g., replace O(n²) with O(n log n)).
  - Optimize database queries (e.g., add indexes).
- **Validation**:
  - **Load Test**: Use **JMeter** or **k6** to simulate traffic.
    ```bash
    # JMeter script example
    jmeter -n -t test_plan.jmx -l results.jtl -e -o report
    ```
  - **Canary Deploy**: Roll out fixes to 10% of traffic first.

### **Step 5: Document & Prevent Recurrence**
- Update the **runbook** with:
  - Root cause analysis (RCA).
  - Fix details (code changes, config updates).
  - Mitigation steps (e.g., "Add health checks for DB connections").
- Set up **alerts** for future occurrences:
  ```yaml
  # Prometheus Alert Rule Example
  - alert: HighDatabaseLatency
    expr: postgres_query_duration_seconds > 500
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Database query latency >500ms"
  ```

---

## **Query Examples**
### **1. Find Slow Database Queries (PostgreSQL)**
```sql
-- Top 10 slowest queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### **2. Filter Logs by Component (ELK Stack)**
```json
// Kibana Discover Query
component: "payment_service" AND @timestamp > now-1d AND level: ERROR
```

### **3. Check Live CPU/Memory Usage (Linux)**
```bash
# Top CPU-consuming process
top -c -n 1 | grep -E 'java|node|python'

# Memory usage
free -h
```

### **4. Trace Request Flow (OpenTelemetry)**
```bash
# Export traces to Jaeger
otelcol --config-file=otel-config.yaml
```
**Example `otel-config.yaml` snippet**:
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
processors:
  batch:
exporters:
  jaeger:
    endpoint: "jaeger:14250"
    tls:
      insecure: true
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
```

### **5. Stress-Test API Endpoints (k6)**
```javascript
// script.js
import http from 'k6/http';

export default function () {
  const res = http.get('https://api.example.com/orders');
  if (res.status !== 200) {
    console.error(`Failed: ${res.status}`);
  }
}
```
Run with:
```bash
k6 run --vus 100 --duration 30s script.js
```

---

## **Related Patterns**
| **Pattern**                     | **Connection to Monolith Troubleshooting**                                                                 | **When to Use**                                                                 |
|----------------------------------|------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability-circuit-breaker.html)** | Prevents cascading failures by isolating dependencies.                                               | When external APIs or DB calls fail repeatedly.                                  |
| **[Bulkhead Pattern](https://martinfowler.com/bliki/BulkheadPattern.html)** | Limits resource contention (e.g., thread pools, connection pools).                                   | During sudden traffic spikes or resource exhaustion.                              |
| **[Retries with Backoff](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)** | Handles transient failures gracefully.                                                              | For timeouts or network issues with dependent services.                          |
| **[Feature Flags](https://launchdarkly.com/blog/feature-flags-vs-feature-toggles/)** | Safely roll out fixes without full deployment.                                                      | Deploying a fix but needing to validate in production.                           |
| **[Distributed Tracing](https://opentelemetry.io/)** | Correlates requests across services/monolith layers.                                                 | Debugging latency issues in complex flows.                                      |
| **[Observability Stack (ELK, Prometheus, Grafana)](https://www.elastic.co/observability)** | Centralizes logs, metrics, and traces for analysis.                                               | Real-time monitoring and post-incident analysis.                                 |
| **[Chaos Engineering](https://chaosengineering.io/)** | Proactively tests system resilience.                                                                  | Before major deployments or to identify hidden dependencies.                      |
| **[Database Sharding](https://www.percona.com/blog/2018/06/06/database-sharding-best-practices/)** | Scales read queries but complicates troubleshooting.                                               | If monolith DB becomes a bottleneck (advanced).                                  |

---

## **Tools & Libraries**
| **Category**       | **Tools/Libraries**                                                                 | **Use Case**                                                                 |
|--------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Logging**        | ELK Stack, Loki, Datadog                                                             | Centralized log aggregation and analysis.                                  |
| **Profiling**      | `pprof` (Go), VisualVM (Java), Py-Spy (Python)                                    | CPU/memory profiling.                                                      |
| **Tracing**        | OpenTelemetry, Jaeger, Zipkin                                                          | Distributed request tracing.                                               |
| **Monitoring**     | Prometheus + Grafana, New Relic, Datadog                                             | Metrics and alerts.                                                        |
| **Load Testing**   | JMeter, k6, Gatling                                                                  | Simulate traffic to validate fixes.                                        |
| **Debugging**      | IDE Debuggers (IntelliJ, VS Code), `strace` (Linux), `dtrace` (macOS)               | Step-through debugging, system call tracing.                               |
| **Database Tools** | pgAdmin (PostgreSQL), MySQL Workbench, `EXPLAIN ANALYZE`                           | Query optimization.                                                        |
| **Dependency Mgmt**| Maven/Gradle (Java), pip (Python), npm (Node.js)                                   | Identify version conflicts.                                               |
| **Chaos Testing**  | Chaos Mesh, Gremlin                                                                | Proactively test failure modes.                                            |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|--------------------------------------|--------------------------------------------------------------------------------|
| **Ignoring Baseline Comparisons**    | Always compare current metrics against historical baselines.                  |
| **Overlooking External Dependencies** | Map all external calls (APIs, DBs) and monitor their health.                 |
| **Silent Failures**                  | Use **positive affirmations** (e.g., `http.get()` with status validation).     |
| **Not Documenting RCAs**             | Maintain a **runbook** with past incidents and fixes.                          |
| **Assuming the Issue is the Latest Change** | Use **binary search** to isolate the problematic commit.                     |
| **Poor Logging Correlation**         | Always include `request_id`/`trace_id` in logs.                              |
| **Neglecting Database Indexes**      | Regularly analyze query plans and add indexes for frequent filters.           |

---
**Note**: For large monoliths, consider **gradual decomposition** into microservices (e.g., using **strangler pattern**) to improve maintainability long-term. However, always validate that this won’t introduce new complexity.