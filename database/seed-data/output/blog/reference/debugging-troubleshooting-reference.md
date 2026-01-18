# **[Pattern] Debugging & Troubleshooting Reference Guide**

---
## **Overview**
Debugging and troubleshooting is a structured, methodical approach to identifying, isolating, and resolving issues in software, systems, or applications. This pattern ensures efficiency by following a logical flow: **observation → hypothesis → testing → resolution**. It applies to all debugging contexts (e.g., frontend errors, backend crashes, network latency) and is crucial for reducing mean time to recovery (MTTR) and improving system reliability. This guide outlines a **standardized framework**, best practices, and tools to implement a robust debugging workflow.

---

## **Key Concepts & Implementation Details**

### **1. Debugging vs. Troubleshooting**
- **Debugging** focuses on identifying and fixing **root causes** of runtime errors, log anomalies, or unexpected behavior.
- **Troubleshooting** involves **symptom analysis** to diagnose broader operational issues (e.g., performance degradation, integration failures).
- **Key Overlap**: Both rely on **log analysis, metrics, and replication** of issues.

### **2. Debugging Workflow**
Follow this **5-step process** to resolve issues systematically:

| Step          | Action Items                                                                 |
|---------------|--------------------------------------------------------------------------------|
| **1. Reproduce** | Document the **symptoms**, environment, and steps to replicate the issue. Use a [bug report template](#template). |
| **2. Gather Data** | Collect:                                                                       |
|               | - **Logs** (application, system, browser console)                              |
|               | - **Metrics** (CPU, memory, latency, error rates)                             |
|               | - **Traces** (APM tools like OpenTelemetry, Datadog)                           |
|               | - **Relevant config files/dump files**                                         |
| **3. Narrow Down** | Use **binary search techniques** to isolate the issue:                         |
|               | - Compare **working vs. broken states**                                       |
|               | - Test **incremental changes** (e.g., disable features, roll back versions)    |
|               | - Isolate **dependent components** (e.g., databases, APIs)                   |
| **4. Hypothesize** | Formulate **testable hypotheses** based on data (e.g., "The API timeout is caused by DB query latency"). |
| **5. Test & Validate** |                                                                               |
|               | - Implement **temporary fixes** (e.g., patches, logs hooks) to confirm hypotheses |
|               | - Verify resolution via **automated tests** or manual validation              |
|               | - Document the **root cause** and **fix** in a knowledge base                 |

---
### **3. Debugging Tools & Techniques**
| Category               | Tools/Techniques                                                                 | Use Case                                                                 |
|------------------------|----------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Logging**            | `console.log()`, ELK Stack (Elasticsearch, Logstash, Kibana), CloudWatch           | Capture runtime events, filter errors by severity.                       |
| **APM (Application Performance Monitoring)** | New Relic, Dynatrace, OpenTelemetry                          | Trace requests end-to-end; identify bottlenecks.                          |
| **Profiling**          | `chrome://tracing`, `pprof` (Go), JProfiler (Java)                                | Analyze CPU, memory, and I/O usage.                                       |
| **Network Debugging**  | `curl`, Postman, Wireshark, Chrome DevTools Network Tab                            | Inspect HTTP headers, payloads, and latency.                              |
| **Database Debugging** | `EXPLAIN` (SQL), `pgbadger` (PostgreSQL), Query Store (SQL Server)              | Identify slow or malformed queries.                                      |
| **Code Debugging**     | IDE Debuggers (VS Code, IntelliJ), `gdb`, `pdb` (Python), Breakpoints, Step-through | Step into functions, inspect variables in real-time.                     |
| **Synthetic Monitoring** | Pingdom, Synthetic Transactions (AWS CloudWatch)                               | Simulate user interactions to detect outages proactively.                 |

---
### **4. Best Practices**
- **Isolate Environments**: Always test fixes in a **staging** or **dev** environment before production.
- **Automate Log Analysis**: Use **SLOs (Service Level Objectives)** to alert on anomalies (e.g., error rates > 1%).
- **Trend Analysis**: Correlate metrics over time (e.g., "Errors spiked after Deploy X").
- **Document Everything**: Maintain a **debugging notebook** (e.g., Confluence, Notion) with:
  - Issue descriptions
  - Steps to reproduce
  - Root causes
  - Fixes implemented
- **Collaborate**: Use **Slack/Discord channels** or **Jira tickets** to coordinate debugging sessions.

---

## **Schema Reference**
Use this **structured schema** to organize debugging data for consistency.

| Field               | Description                                                                 | Example Values                                                                 |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Issue ID**        | Unique identifier (e.g., ticket number)                                      | `DEV-456`, `JIRA-1234`                                                          |
| **Symptom**         | Clear description of the observed behavior                                     | "API returns 500 errors for `/users` endpoint"                                  |
| **Reproduction Steps** | Steps to replicate the issue                                                |                                                                                 |
|                     | 1. Call `/users?limit=1000`                                                   |                                                                                 |
|                     | 2. Wait >3 sec for response                                                 |                                                                                 |
| **Environment**     | OS, Browser, Version, Deployment (dev/stage/prod)                             |                                                                                 |
|                     | - OS: Ubuntu 22.04                                                            |                                                                                 |
|                     | - Browser: Chrome v120                                                           |                                                                                 |
|                     | - App Version: `v1.2.3`                                                       |                                                                                 |
| **Data Collected**  | Logs, traces, screenshots, or dumps                                             |                                                                                 |
|                     | - [Log file](link-to-logs)                                                    |                                                                                 |
|                     | - APM Trace ID: `trace_123xyz`                                                 |                                                                                 |
| **Root Cause**      | Hypothesis + validation                                                     | "DB connection pool exhausted due to unclosed transactions"                   |
| **Fix**             | Implementation details                                                      | "Increased connection pool size to 50"                                          |
| **Verification**    | How the fix was tested                                                       | "Smoke test passed; error rate dropped to 0%"                                  |
| **Owner**           | Team/individual responsible                                                    | "@dev-team", "Alice"                                                             |
| **Status**          | Closed/Reopened/Fixed/Reverted                                                | `Fixed`                                                                         |
| **Timeline**        | When opened/resolved                                                          |                                                                                 |
|                     | - Opened: 2024-05-15 14:30 UTC                                                |                                                                                 |
|                     | - Resolved: 2024-05-15 16:45 UTC                                              |                                                                                 |

---

## **Query Examples**
### **1. Filtering Logs for Errors**
**Tool**: ELK Stack (Kibana Query DSL)
**Query**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1d/d" } } }
      ]
    }
  }
}
```
**Output**: Displays all `ERROR`-level logs from the last day.

---
### **2. Identifying Slow API Endpoints (OpenTelemetry)**
**Tool**: Grafana + OpenTelemetry
**Query**:
```sql
sum by(service_name, endpoint) (
  rate(http_server_duration_seconds_bucket[5m])
  where endpoint = '/users'
  and service_name = 'user-service'
)
```
**Output**: Shows average response time for `/users` endpoint.

---
### **3. Database Query Analysis (PostgreSQL)**
**Tool**: `pgbadger`
**Command**:
```bash
pgbadger -o report.html /var/log/postgresql/postgresql.log
```
**Filter for slow queries** in the generated HTML report.

---
### **4. Network Latency Debugging (Wireshark)**
**Tool**: Wireshark
**Filter**:
```
http.request.method == "POST" && http.host == "api.example.com"
```
**Action**: Inspect TCP handshake, retries, or payload size.

---
### **5. Code Debugging (Python `pdb`)**
**Tool**: Python Debugger
**Steps**:
1. Place `breakpoint()` in suspicious code:
   ```python
   def risky_function():
       breakpoint()  # Pauses execution here
       ...
   ```
2. Run with:
   ```bash
   python -m pdb script.py
   ```
3. Use commands:
   - `n` (next line)
   - `p variable` (print variable)
   - `c` (continue)

---

## **Debugging Templates**
### **1. Bug Report Template**
```markdown
---
**Issue ID**: [JIRA/Ticket #]
**Title**: [Brief description]
**Severity**: [P0-P4]
**Environment**:
- App Version:
- OS:
- Browser:
**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
**Expected Behavior**: [What should happen]
**Actual Behavior**: [What happens instead]
**Logs/Traces**: [Attachments/Links]
**Screenshots**: [Attachments]
**Additional Context**:
- Last working version: [X.Y.Z]
- Recent changes: [Deploy/Config updates]
---
```

### **2. Debugging Cheat Sheet**
| **Issue Type**       | **Quick Checks**                                                                 |
|----------------------|-----------------------------------------------------------------------------------|
| **Frontend Crash**   | - Check browser console (`F12 > Console`)                                         |
|                      | - Validate API responses via Postman                                             |
|                      | - Review bundle size (`npm run analyze`)                                          |
| **Backend Crash**    | - Review server logs (`/var/log/app.log`)                                         |
|                      | - Check CPU/memory usage (`htop`, `top`)                                         |
|                      | - Test with `curl -v`                                                              |
| **Database Issues**  | - Run `EXPLAIN ANALYZE` on slow queries                                           |
|                      | - Check replication lag (`SHOW REPLICATION STATUS`)                              |
|                      | - Validate backups (`pg_dump --list`)                                             |
| **Network Latency**  | - Test ping/TCP connect time (`mtr google.com`)                                  |
|                      | - Inspect DNS resolution (`dig api.example.com`)                                  |
|                      | - Use `tcpdump` to analyze traffic                                               |
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[Observability](Observability.md)** | Collect logs, metrics, and traces to monitor system health.                          | Proactively detect issues before users report them.                         |
| **[Retry & Circuit Breaker](Resilience.md)** | Implement retries and fail-fast mechanisms for unstable dependencies.       | Handle transient failures (e.g., DB timeouts, API outages).              |
| **[Feature Flags](CanaryDeployment.md)** | Gradually roll out changes to a subset of users.                                      | Test fixes in production without affecting all users.                       |
| **[Chaos Engineering](ChaosTesting.md)** | Intentionally inject failures to test resilience.                                      | Validate disaster recovery plans and system robustness.                   |
| **[Postmortem Analysis](IncidentResponse.md)** | Document lessons learned from outages.                                                | Prevent recurrence of similar issues.                                      |
| **[Logging Best Practices](Logging.md)** | Structured logging for easier analysis.                                                | Ship logs with contextual metadata (e.g., user ID, request ID).           |

---

## **Further Reading**
- [Google SRE Book: Debugging](https://sre.google/sre-book/debugging/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [ELK Stack Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [PostgreSQL Performance Tools](https://wiki.postgresql.org/wiki/SlowQueryQuestions)

---
**Last Updated**: [YYYY-MM-DD]
**Contributors**: [@Author1, @Author2]