**[Pattern] Reference Guide: Monolith Troubleshooting**

---

### **Overview**
This guide provides a structured approach to diagnosing and resolving issues in **monolithic applications**. Unlike distributed systems, monoliths present unique challenges due to their tightly coupled components, single-process architecture, and shared memory/resources. This pattern outlines systematic troubleshooting techniques, including log analysis, performance bottlenecks, dependency conflicts, and deployment failures. The goal is to minimize downtime, improve stability, and optimize performance without refactoring into microservices.

Key focus areas:
- **Log and Metrics Analysis** – Parsing consolidated logs and interpreting performance metrics.
- **Memory and CPU Pressure** – Identifying leaks, slow queries, or inefficient loops.
- **Database Bottlenecks** – Query optimization, connection pooling, and schema issues.
- **Dependency Resolution** – NPM/Yarn/Pip conflicts, version mismatches, and build failures.
- **Deployment Failures** – Rollback strategies, A/B testing, and canary deployments.
- **Network and External Service Issues** – Timeouts, retries, and dependency chokepoints.

---

## **Schema Reference**
Below are structured tables for common monolith troubleshooting scenarios.

### **1. Log Analysis Template**
| **Category**          | **Example Pattern**                     | **Likely Cause**                          | **Action Items**                                                                 |
|-----------------------|-----------------------------------------|------------------------------------------|---------------------------------------------------------------------------------|
| **Crash Dumps**       | `Segmentation fault at [timestamp]`     | Memory corruption, buffer overflow        | Reproduce in staging, check for malicious input or corruption.                  |
| **Database Errors**   | `Query timeout: SELECT * FROM users`    | Slow query, missing indexes               | Add indexes, optimize queries, check for `N+1` issues.                          |
| **Dependency Errors** | `ModuleNotFoundError: packageX`          | Version mismatch, missing package         | Update `requirements.txt/package.json`, check virtualenv/container versions.   |
| **Network Failures**  | `Connection refused to DB`              | DB down, network partition, firewall     | Check DB health, retry logic, network traces.                                   |
| **Slow Endpoints**    | `200 OK but 400ms response`             | Bloated response, unoptimized code        | Profile with `cProfile` (Python), Chrome DevTools (JS), or `trace` (Java).      |

---

### **2. Performance Bottleneck Checklist**
| **Metric**            | **Threshold**       | **Diagnostic Steps**                                                                 | **Fix**                                                                          |
|-----------------------|---------------------|--------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **CPU Usage**         | >80% for 5 mins     | Check for CPU-intensive loops, unoptimized algorithms (e.g., O(n²) sorts).         | Refactor, use caching, or scale horizontally (if possible).                      |
| **Memory Growth**     | Steady increase     | Leaks in objects (e.g., unclosed DB cursors, unmarked GC roots).                   | Enable GC logs (`gc.set_debug(stats=True)`), fix dangling references.             |
| **DB Query Time**     | >1s for common ops | Slow joins, missing indexes, or `SELECT *`.                                          | Use `EXPLAIN ANALYZE`, add composite indexes, paginate results.                 |
| **GC Pauses**         | >100ms (Java/Python)| Large object allocations, fragmentation.                                             | Increase heap size, tune GC (e.g., `-Xmx`, `-Xms`), break monolith into services. |
| **HTTP Latency**      | >500ms (p99)        | Unoptimized templates (e.g., ERB/JSX), external API calls.                           | Cache responses, lazy-load assets, reduce payload size.                          |

---

### **3. Deployment Failure Taxonomy**
| **Failure Type**      | **Symptoms**                          | **Root Cause**                              | **Mitigation**                                                                   |
|-----------------------|---------------------------------------|--------------------------------------------|---------------------------------------------------------------------------------|
| **Rollback Required** | `500 errors` post-deploy              | Bad dependency, race condition             | Use **blue-green** or **canary** deployments; auto-rollback on health checks.    |
| **Build Failures**    | `npm ERR! code ELIFECYCLE`            | Missing build tools, version conflicts      | Pin exact versions in `package-lock.json`, use Docker for consistent builds.     |
| **Config Errors**     | `Missing required env var`            | Misconfigured `.env` or secrets            | Validate configs pre-deploy, use tools like `envsubst` or `Sentry`.             |
| **Database Migrations** | `Foreign key violation`          | Schema drift between deployments            | Test migrations in staging, enforce `transactional` migrations.                 |
| **Race Conditions**   | `Inconsistent state`                  | Async operations without locks             | Use `asyncio` locks (Python), `ReentrantLock` (Java), or event sourcing.        |

---

## **Query Examples**

### **1. Finding Slow Queries (PostgreSQL)**
```sql
-- Top 5 slowest queries by execution time (last 24h)
SELECT
    query,
    total_time,
    calls,
    mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 5;
```
**Action:** Add indexes to tables in the `query` column, review `EXPLAIN` plans.

---

### **2. Memory Leak Detection (Python)**
```python
import gc
import psutil

def check_leak():
    objects_before = len(gc.get_objects())
    # Simulate user action
    user_trigger_action()
    objects_after = len(gc.get_objects())
    leak_size = (objects_after - objects_before) * psutil.virtual_memory().available / (1024**3)
    print(f"Potential leak: {leak_size:.2f} GB")
```
**Action:** Profile with `memory_profiler` to identify leaking objects.

---

### **3. Log Correlation (ELK Stack Example)**
**Kibana Query:**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```
**Action:** Use `correlate` API to link errors to specific transactions.

---

### **4. Dependency Conflict Resolution (Yarn)**
```bash
# Identify conflicting versions
yarn why node-fetch

# Force resolution
yarn add node-fetch@2.6.1 --force
```
**Action:** Update `overrides` in `package.json` or use `npm dedupe`.

---

## **Related Patterns**

| **Pattern**               | **Purpose**                                                                 | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Circuit Breaker]**     | Prevent cascading failures in external dependencies.                        | Monolith calls unstable APIs (e.g., third-party services).                    |
| **[Feature Flags]**       | Gradually roll out changes without full deployment.                          | Testing new features in production; mitigating deployment risks.               |
| **[Distributed Tracing]** | Trace requests across monolithic services (if partitioned internally).       | Debugging latency spikes in large apps (e.g., Django + Celery).               |
| **[Chaos Engineering]**    | Proactively test resilience to failures.                                    | Critical monoliths with high SLOs (e.g., payment systems).                    |
| **[Sidecar Containers]**  | Isolate non-core components (e.g., logging, caching).                      | Monoliths running in Kubernetes needing sidecar injection.                    |
| **[Database Sharding]**    | Split read/write load across DB instances.                                  | Monoliths with CPU-bound DB queries (e.g., CMS platforms).                     |

---

## **Tools & Libraries**
| **Tool**          | **Purpose**                                                                 | **Example Use Case**                                                          |
|--------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Prometheus**     | Metrics collection and alerting.                                             | Monitoring CPU/memory usage in real-time.                                     |
| **Sentry**         | Error tracking and performance profiling.                                    | Auto-correlating errors with stack traces.                                    |
| **New Relic**      | APM for monoliths (APIs, DB queries, caching).                               | Profiling slow endpoints in a Ruby on Rails app.                              |
| **Blackbox Exporter** | Synthetic transactions to test endpoints.                                    | Pinging `/health` endpoints from multiple regions.                            |
| **Docker + Compose** | Isolated environment for troubleshooting.                                  | Reproducing issues in staging without affecting production.                   |
| **GDB/LLDb**       | Debugging core dumps in compiled languages (C++, Go).                       | Analyzing segfaults in a Go monolith.                                         |
| **Chronograf**     | Time-series data visualization (InfluxDB).                                   | Debugging spikes in request volume.                                           |

---

## **Step-by-Step Workflow**
1. **Reproduce the Issue**
   - Use **synthetic transactions** (Postman, Locust) to trigger the problem.
   - Isolate in staging with **feature flags** or **canary deployments**.

2. **Gather Data**
   - **Logs:** Check centralised log management (ELK, Datadog).
   - **Metrics:** Query Prometheus/Grafana for spikes in latency/memory.
   - **Traces:** Use OpenTelemetry or Datadog to trace requests.

3. **Isolate the Component**
   - **Binary Search:** Comment out sections of code to narrow down the issue.
   - **Dependency Analysis:** Use `yarn why` or `pip freeze > requirements.txt` to check conflicts.

4. **Validate Fixes**
   - **Unit Tests:** Add tests for the problematic area.
   - **Load Testing:** Simulate production traffic with **JMeter** or **k6**.

5. **Document the Fix**
   - Update **runbooks** with steps to repro/fix the issue.
   - Add **alerting rules** for similar conditions.

---

## **Anti-Patterns to Avoid**
- **Ignoring Logs:** "It works on my machine" debugging without logs/metrics.
- **Over-Reliance on `kill -9`:** Crashing processes masks deeper issues.
- **Skipping Staging Tests:** Deploying to production without validating fixes.
- **No Rollback Plan:** Deploying without a revert mechanism (e.g., feature flags).
- **Silent Failures:** Allowing unobserved errors (e.g., missing `try-catch` in Python).

---
**Final Note:** Monoliths are **simpler to debug** than distributed systems but require disciplined logging, testing, and observability. Prioritize **proactive monitoring** over reactive fixes. For long-term scaling, evaluate **strangler pattern** or **modular monolith** refactors.