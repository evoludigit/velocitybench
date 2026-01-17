# **[Pattern] Availability Troubleshooting Reference Guide**

---

## **Overview**
The **Availability Troubleshooting** pattern provides structured methods to identify, diagnose, and resolve issues impacting system uptime, performance, or accessibility. This guide covers systematic approaches for detecting availability disruptions, analyzing root causes, and implementing mitigation strategies. Common failure points include **service unavailability, latency spikes, resource exhaustion, or dependency failures** (e.g., database lockouts, network outages). The pattern prioritizes **observability, automation, and proactive monitoring** to minimize downtime.

Target users include:
- **DevOps/SRE Engineers** (diagnosing infrastructure issues)
- **Site Reliability Engineers** (scaling and failure recovery)
- **Cloud System Administrators** (troubleshooting multi-region deployments)
- **QA/Test Engineers** (validating availability during performance testing)

---

## **Key Concepts & Implementation Details**

### **1. Availability Troubleshooting Phases**
Troubleshooting follows a **structured 5-step workflow**:

| **Phase**               | **Objective**                                                                 | **Key Actions**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Detection**           | Identify availability anomalies (outages, degradation).                     | Review logs, alerts, and monitoring dashboards (e.g., Prometheus, Datadog).   |
| **Classification**      | Categorize the issue (e.g., infrastructure, application, dependency).      | Check cloud provider status pages (AWS, GCP, Azure).                          |
| **Root Cause Analysis** | Determine why the issue occurred (e.g., misconfiguration, external failure). | Analyze traces, metrics, and dependency graphs.                                |
| **Mitigation**          | Apply temporary fixes to restore service.                                    | Rollback deployments, scale resources, or reroute traffic.                     |
| **Resolution**          | Permanently fix the root cause.                                              | Update configurations, patch vulnerabilities, or improve redundancy.            |

---

### **2. Core Components**
| **Component**               | **Description**                                                                 | **Tools/Technologies**                          |
|-----------------------------|-------------------------------------------------------------------------------|-------------------------------------------------|
| **Monitoring**              | Continuously track system health (uptime, latency, error rates).             | Prometheus, New Relic, Grafana, ELK Stack      |
| **Alerting**                | Notify teams of anomalies via SLOs, thresholds, or anomaly detection.         | PagerDuty, Opsgenie, Slack Integrations        |
| **Tracing**                 | Trace requests across services to identify bottlenecks.                       | Jaeger, Zipkin, OpenTelemetry                   |
| **Logging**                 | Centralize logs for real-time debugging.                                     | Splunk, Loki, Fluentd                          |
| **Dependency Mapping**      | Visualize service interdependencies to isolate failures.                     | GraphQL Subscriptions, Topology Maps           |
| **Chaos Engineering**       | Proactively test failure resilience.                                         | Gremlin, Chaos Mesh                            |

---

### **3. Common Availability Issues & Patterns**
| **Issue**                  | **Symptoms**                          | **Troubleshooting Steps**                                                                 |
|----------------------------|---------------------------------------|------------------------------------------------------------------------------------------|
| **Service Unavailability** | HTTP 5xx errors, timeouts, or "Service Unavailable" responses. | Check:
- Application logs for crashes.
- Cloud provider health status.
- Load balancer/proxy metrics (e.g., 5xx rates).
- Dependency service health (e.g., database connectivity). |
| **Latency Spikes**         | Slow responses (>1s), timeouts.         | Investigate:
- Slow database queries (use query profilers).
- Network latency (traceroute, `ping`).
- CPU/memory bottlenecks (e.g., garbage collection pauses). |
| **Resource Exhaustion**    | High CPU, memory, or disk usage.       | Analyze:
- Cloud auto-scaling metrics (e.g., CPU > 80% for 5 mins).
- Memory leaks (heap dumps in Java/Python).
- Disk I/O saturation (check `iostat`). |
| **Dependency Failures**    | External service outages (e.g., payment gateway). | Verify:
- Retry policies in place?
- Circuit breakers (e.g., Hystrix) functioning?
- Fallback mechanisms (e.g., cached responses). |
| **Configuration Drift**    | Unexpected behavior post-deploy.        | Compare:
- Current config vs. git history.
- Environment variables across stages (dev/stage/prod).
- Feature flags enabled in production. |

---

## **Schema Reference**
Below are key data structures used in availability troubleshooting.

### **1. Alert Schema (Prometheus Alertmanager)**
```json
{
  "alerts": [
    {
      "labels": {
        "alertname": "HighErrorRate",
        "severity": "critical",
        "service": "user-service",
        "namespace": "prod"
      },
      "annotations": {
        "summary": "User service errors > 5% for 10 mins",
        "description": "Error rate: {{ $value }}% | Group by: {{ $labels.job }}"
      },
      "startsAt": "2023-10-15T14:30:00Z",
      "endsAt": "2023-10-15T14:40:00Z"
    }
  ]
}
```

### **2. Service Dependency Graph (JSON)**
```json
{
  "services": [
    {
      "name": "frontend",
      "health": "ok",
      "dependencies": [
        { "name": "auth-service", "health": "degraded", "latency": "3.2s" }
      ],
      "metrics": {
        "response_time_p99": 0.8,
        "error_rate": 0.001
      }
    }
  ]
}
```

### **3. Incident Report Template**
```json
{
  "name": "Database Connection Pool Exhaustion",
  "timestamp": "2023-10-15T15:00:00Z",
  "impact": {
    "services": ["checkout-service"],
    "duration": "PT10M"
  },
  "root_cause": {
    "type": "Configuration",
    "description": "Connection pool size (20) < concurrent users (50)."
  },
  "mitigation": "Increased pool size to 100.",
  "resolution": "Automated scaling via Kubernetes HPA.",
  "affected_teams": ["backend", "devops"]
}
```

---

## **Query Examples**

### **1. Detecting High-Error Rates (PromQL)**
```promql
# Errors per second for a service
rate(http_requests_total{job="user-service",status=~"5.."}[1m]) > 0.5
```
**Output:**
Alerts if errors exceed 0.5/sec for `user-service`.

---

### **2. Identifying Slow API Endpoints (Grafana Dashboard)**
```promql
# P99 latency for `/checkout` endpoint
histogram_quantile(0.99, sum(rate(http_request_size_bytes_sum[5m])) by (le, endpoint))
```
**Output:**
Displays latency percentiles for `/checkout` (e.g., 1.2s P99).

---

### **3. Finding Orphaned Pods (Kubernetes)**
```bash
kubectl get pods --all-namespaces --field-selector=status.phase==Pending
```
**Output:**
Lists pods stuck in `Pending` state (e.g., due to resource quotas).

---

### **4. Tracing a Failed Request (Jaeger Query)**
```bash
# Trace ID from logs
curl \
  -s \
  -X POST \
  "http://jaeger-query:16686/search?service=user-service&traceID=1234abcd" \
  -H "Content-Type: application/json"
```
**Output:**
JSON graph of the failed request flow.

---

### **5. Checking Cloud Provider Status (AWS CLI)**
```bash
aws health service-events list-service-impacts --service-code aws:ec2 --max-items 1
```
**Output:**
AWS health dashboard updates (e.g., region outage).

---

## **Related Patterns**
To complement **Availability Troubleshooting**, consider integrating the following patterns:

| **Pattern**               | **Purpose**                                                                 | **Connection to Availability Troubleshooting**                          |
|---------------------------|----------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **[Observability Stack]** | Centralize logs, metrics, and traces for diagnostic clarity.             | Provides data for **Detection** and **Root Cause Analysis**.             |
| **[Circuit Breaker]**     | Prevent cascading failures by isolating unhealthy dependencies.            | Mitigates **Dependency Failures** during outages.                        |
| **[Chaos Engineering]**   | Proactively test resilience to failures.                                   | Reduces likelihood of unplanned outages by exposing weaknesses.         |
| **[Auto-Scaling]**        | Dynamically adjust resources to handle load spikes.                       | Helps prevent **Resource Exhaustion** during traffic surges.             |
| **[Feature Flags]**       | Gradually roll out changes without affecting all users.                   | Reduces blast radius of **Configuration Drift** issues.                  |
| **[Blame the Cloud]**     | Distinguish between customer and provider issues.                         | Isolates **Infrastructure vs. Application** failures.                    |
| **[Golden Signals]**      | Focus on latency, traffic, errors, and saturation for availability.      | Guides **Classification** and **Root Cause Analysis**.                     |

---
## **Best Practices**
1. **Automate Detection**:
   - Use SLOs (Service Level Objectives) to define acceptable error budgets.
   - Example: "99.9% availability" → Alert at 0.1% errors.

2. **Reduce Mean Time to Detect (MTTD)**:
   - Implement real-time anomaly detection (e.g., Prometheus Alertmanager + ML models).

3. **Document Failures**:
   - Maintain an **Incident Wiki** with root causes and fixes for recurring issues.

4. **Chaos Testing**:
   - Run **Chaos Experiments** (e.g., kill 50% of pods) to validate resilience.

5. **Dependency Resilience**:
   - Use **retries with backoff** and **circuit breakers** for external APIs.

6. **Postmortems**:
   - Conduct retrospectives to identify systemic issues (e.g., missing alerts).

---
## **Troubleshooting Checklist**
| **Step**               | **Action Items**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Is the issue affecting all users?** | Check:
- Regional deployments (multi-region vs. single-region).
- User segments (e.g., logged-in vs. anonymous). |
| **Is the problem infrastructure or application?** | Compare:
- Cloud provider status pages.
- Local vs. remote logs. |
| **Are dependencies healthy?** | Verify:
- Database connections.
- External API responses. |
| **Is the issue reproducible?** | Test:
- Recreate steps in staging.
- Use feature flags to isolate changes. |
| **Has this happened before?** | Review:
- Past incident logs.
- Blame-the-Cloud analysis. |

---
## **Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **SLO**                | Service Level Objective (e.g., "99.9% uptime").                               |
| **SLA**                | Service Level Agreement (contractual uptime guarantee).                        |
| **MTTR**               | Mean Time to Recovery (time to fix an issue).                                 |
| **MTTD**               | Mean Time to Detect (time to identify an issue).                              |
| **Circuit Breaker**    | Pattern to stop cascading failures (e.g., Hystrix).                          |
| **Golden Signals**     | Latency, Traffic, Errors, Saturation (Google’s observability focus).          |
| **Blame the Cloud**    | Technique to determine if an issue is customer vs. provider responsibility.    |

---
**End of Reference Guide** (Word count: ~1,050)