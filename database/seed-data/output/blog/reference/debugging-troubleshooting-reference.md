# **[Pattern] Debugging & Troubleshooting Reference Guide**

---

## **Overview**
The **Debugging & Troubleshooting** pattern provides structured methodologies to identify, diagnose, and resolve issues in software systems, hardware, or infrastructure. It follows a **logical, repeatable workflow** to collect symptoms, isolate root causes, apply fixes, and validate resolution. This guide details key concepts, implementation steps, diagnostic tools, and best practices to ensure efficient problem-solving across development, operations, and support teams.

Best suited for:
✔ **Developers** debugging code/logic
✔ **DevOps/SREs** troubleshooting deployments and infrastructure
✔ **QA Testers** resolving flaky tests or integration issues
✔ **Support Engineers** handling user-reported bugs

---

## **Key Concepts & Implementation Details**

### **1. Debugging vs. Troubleshooting**
| Concept          | Focus                     | Scope                          | Deliverable          |
|------------------|---------------------------|--------------------------------|----------------------|
| **Debugging**    | Identifying logical errors in code. | Codebase, runtime execution. | Code fix, unit test. |
| **Troubleshooting** | Diagnosing system failures in production/environment. | Infrastructure, dependencies, configs. | Resolution steps, documentation. |

### **2. Core Workflow Phases**
A standardized approach ensures consistency:
1. **Symptom Collection**
   - Capture user reports, logs, metrics, and environment details.
   - Use structured templates to avoid missing context.
2. **Root Cause Analysis (RCA)**
   - Hypothesize causes via elimination or pattern recognition.
   - Leverage tools like **time-series data (Prometheus/Grafana)**, **debugging profilers**, or **network captures (Wireshark)**.
3. **Fix Application**
   - Test fixes in staged environments (e.g., staging → production).
   - Prioritize non-disruptive solutions (e.g., config changes over code pushes).
4. **Validation & Prevention**
   - Verify resolution with test cases or user confirmations.
   - Implement monitoring/alerts to avoid recurrence (e.g., **SLOs/SLIs**).

---

## **Schema Reference**
Use this structured schema for reproducible troubleshooting records. Store in **Jira, Linear, or a custom database** for traceability.

| **Field**               | **Description**                                                                 | **Example Value**                          | **Tool Support**               |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------------|--------------------------------|
| **Issue ID**            | Unique identifier for tracking.                                               | `TROUBL-045`                               | Jira, GitHub Issues            |
| **Symptoms**            | User-reported behavior vs. expected.                                         | *"API returns 500 for 10% of requests."*   | Comments, tickets              |
| **Repro Steps**         | Sequential actions to trigger the issue.                                     | `1. Login as UserX → 2. Submit Form → 3. Refresh.` | User stories, docs           |
| **Environment**         | OS, browser, OS version, dependencies, etc.                                  | `Windows 11, Chrome 120, Python 3.10`     | System logs, CI/CD artifacts    |
| **Log/Error Snippets**  | Relevant code/log entries (minimal but actionable).                          | `2024-05-20T14:30:00 ERROR: TimeoutExceeded` | CloudWatch, Kibana            |
| **Root Cause Hypothesis** | Initial guess (or multiple) based on data.                           | *"Database connection pool exhausted."*     | Collaboration tools            |
| **Test Fixes**          | Changes applied (config, code, etc.) with rollback plan.                   | `Increased pool size to 50 → reverts to 25 if issues persist.` | Git diffs, config files     |
| **Validation**          | Criteria to confirm resolution.                                              | *"No 500 errors for 48 hours in staging."* | Monitoring dashboards         |
| **Prevention**          | Long-term fixes (e.g., alerts, code reviews).                               | *"Added Slack alert for pool thresholds."*  | Runbooks, wikis               |
| **Time to Resolve (TTR)** | Start to fix duration (metrics for SLA compliance).                         | `3 hours`                                  | Time tracking tools           |
| **Owner**               | Team responsible for follow-up.                                               | `Backend Team → Ops`                       | User management systems       |

---

## **Query Examples**

### **1. Log Analysis (CloudTrail/ELK/Kibana)**
```sql
-- Example: Find API errors in the last hour
GET /api/v1/logs
{
  "filter": {
    "status": ["5xx"],
    "timestamp": {"gte": "now-1h", "lte": "now"}
  },
  "sort": ["timestamp:desc"]
}
```
**Output:**
| Timestamp          | Service | Error Code | Request Path |
|--------------------|---------|------------|--------------|
| 2024-05-20T14:35   | UserAPI | 504        | `/users/profile` |

---
### **2. Database Query (PostgreSQL)**
```sql
-- Identify slow queries causing timeouts
SELECT query, execution_time, count
FROM slow_queries
WHERE execution_time > 5000  -- 5 seconds
ORDER BY execution_time DESC;
```
**Output:**
| Query                          | Execution Time | Count |
|--------------------------------|----------------|-------|
| `UPDATE transactions SET ...` | 8,423 ms       | 12    |

---
### **3. Network Troubleshooting (Wireshark)**
```bash
# Capture HTTP traffic to a failing endpoint
tshark -i eth0 -f "host example.com and port 80" -a duration:60 -w capture.pcap
```
**Key observations:**
- Latency spikes during `POST /api/data?size=1000`.
- TLS handshake failures (`SSL_HANDSHAKE_FAILURE`).

---

### **4. Monitoring Alerts (Prometheus/Grafana)**
```promql
# Alert on high error rates in a microservice
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
```
**Trigger:** Fire alert if >5% errors in the last 5 minutes.

---

## **Tooling & Integrations**
| **Category**       | **Tools**                                                                 | **Use Case**                                  |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| **Logging**        | ELK Stack (Elasticsearch, Logstash, Kibana), CloudWatch, Datadog        | Correlate logs across services.               |
| **APM**            | New Relic, Dynatrace, OpenTelemetry                                        | Trace requests end-to-end.                     |
| **Profiling**      | pprof (Go), Python cProfile, Java VisualVM                                 | Identify CPU/memory bottlenecks.              |
| **Network**        | Wireshark, tcpdump, ngrep                                               | Analyze packet-level issues.                  |
| **CI/CD**          | GitHub Actions, Jenkins, CircleCI                                         | Auto-trigger tests on bug reports.            |
| **Collaboration**  | Slack, Jira, Linear                                                     | Track issues in real-time.                    |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Ignoring "It works on my machine"** | Reproduce in a staging environment matching production (e.g., same DB version). |
| **Overlooking dependencies**           | Check version mismatches (e.g., `npm audit`, `docker inspect`).                |
| **Guessing root cause**               | Use structured RCA (e.g., **Fishbone Diagram** or **5 Whys**).                  |
| **Fixing without validation**         | Test fixes in **canary deployments** before full rollout.                      |
| **Silent failures**                   | Implement **circuit breakers** (e.g., Hystrix) and **retries with backoff**.    |

---

## **Related Patterns**
1. **[Observability Pattern](https://example.com/observability)**
   - *Why?* Debugging requires metrics, logs, and traces. This pattern provides the infrastructure for monitoring.
2. **[Rollback Strategy Pattern](https://example.com/rollback)**
   - *Why?* Critical for safely undoing fixes that introduce new issues.
3. **[Containerization Pattern](https://example.com/containerization)**
   - *Why?* Isolates environments for reproducible debugging (e.g., Docker/Kubernetes).
4. **[Chaos Engineering](https://example.com/chaos)**
   - *Why?* Proactively tests failure modes to improve troubleshooting resilience.
5. **[Incident Management](https://example.com/incident-management)**
   - *Why?* Structured response to outages post-diagnosis.

---
## **Further Reading**
- [Google’s SRE Book (Chapter 5: Debugging)](https://sre.google/sre-book/)
- [Postmortem Examples from GitLab](https://about.gitlab.com/handbook/engineering/infrastructure/postmortems/)
- [ELK Stack Guide for Debugging](https://www.elastic.co/guide/en/elastic-stack-get-started/current/get-started.html)