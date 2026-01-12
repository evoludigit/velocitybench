---
# **[Pattern] Availability Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing, analyzing, and resolving availability-related issues in distributed systems, microservices architectures, or cloud-native applications. The **Availability Troubleshooting Pattern** helps identify root causes of downtime, degraded performance, high latency, or unavailability by focusing on system components, dependencies, and operational metrics. It combines **proactive monitoring**, **reactive diagnostics**, and **root-cause analysis (RCA)** to minimize downtime and improve resilience. This pattern is applicable across **on-premises, hybrid, and cloud environments** and leverages observability tools, logging, and metrics to streamline troubleshooting workflows.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
| **Concept**               | **Description**                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **Observability**         | Relies on **metrics, logs, and traces** to detect anomalies in latency, error rates, throughput, and resource utilization.                       |
| **SLOs/SLIs/SLAs**        | Uses **Service Level Objectives (SLOs)**, **Service Level Indicators (SLIs)**, and **Service Level Agreements (SLAs)** to define availability thresholds. |
| **Dependency Mapping**    | Identifies critical dependencies (e.g., databases, APIs, external services) to isolate failures.                                                   |
| **Failure Modes**         | Classifies failures as **transient, intermittent, or permanent** to determine appropriate remediation strategies.                          |
| **Chaos Engineering**     | Proactively tests resilience by injecting failures (e.g., using tools like **Chaos Mesh, Gremlin, or Chaos Monkey**).                          |

---

### **2. Troubleshooting Phases**
The pattern follows a **structured troubleshooting workflow**:

#### **Phase 1: Detection & Alerting**
- **Purpose**: Identify anomalies via **automated alerts** (e.g., Prometheus, Datadog, New Relic).
- **Key Actions**:
  - Check **error rates** (e.g., HTTP 5xx, connection timeouts).
  - Monitor **latency spikes** (e.g., 99th percentile response time).
  - Review **resource saturation** (CPU, memory, disk I/O).
- **Tools**: Alert managers (e.g., **PagerDuty, Opsgenie**), APM tools (e.g., **Dynatrace, ELK Stack**).

#### **Phase 2: Isolation & Diagnosis**
- **Purpose**: Narrow down the scope of the issue.
- **Key Actions**:
  - Use **dependency graphs** (e.g., **Kiali for service meshes, Cloud Map for AWS**) to trace failures.
  - Correlate **logs** (e.g., `error: "connection refused"`) with **traces** (e.g., **Jaeger, Zipkin**).
  - Check **replica health** (e.g., Kubernetes pods, database instances).
- **Commands/Queries**:
  ```sh
  # Example: Check Kubernetes pod health
  kubectl get pods --all-namespaces -o wide | grep -v "Running"

  # Example: Query Prometheus for latency spikes
  prometheus query "http_request_duration_seconds{job='api-service'}" > 5
  ```

#### **Phase 3: Root-Cause Analysis (RCA)**
- **Purpose**: Determine the underlying cause (e.g., misconfiguration, bug, external failure).
- **Key Actions**:
  - Review **relevant metrics** (e.g., high GC pauses in Java apps).
  - Examine **configuration drifts** (e.g., misset `max_connections` in a database).
  - Test **theory of failure** (e.g., simulate load to confirm bottleneck).
- **Templates**:
  - **Bug**: *"Service X fails when Y occurs due to Z."*
  - **Configuration**: *"Parameter A was set to B instead of C, causing D."*
  - **Dependency**: *"External API timeout triggers cascading failures."*

#### **Phase 4: Resolution & Verification**
- **Purpose**: Apply fixes and validate success.
- **Key Actions**:
  - Deploy **patches** (e.g., code changes, config updates).
  - Roll out **rollbacks** (e.g., Kubernetes `Scaledown`, database rollback).
  - Monitor **SLO recovery** (e.g., reduce error rate to <1%).
- **Postmortem**: Document findings in a **blameless format** (e.g., **Google’s Postmortem Template**).

---

### **3. Common Failure Patterns & Mitigations**
| **Failure Type**          | **Symptoms**                          | **Root Causes**                          | **Mitigations**                                                                 |
|---------------------------|---------------------------------------|------------------------------------------|---------------------------------------------------------------------------------|
| **Service Unavailable**   | HTTP 503, connection refused         | CrashLoopBackOff, resource starvation    | Auto-scaling, resource quotas, health checks                                    |
| **Thundering Herd**       | Sudden traffic spike                   | Lack of rate limiting                    | Circuit breakers (e.g., **Hystrix, Resilience4j**), adaptive throttling           |
| **Cascading Failures**    | Dependency timeouts                   | No retries/polling                       | Exponential backoff, bulkheads, dependency isolation                              |
| **Data Corruption**       | Inconsistent reads/writes             | Transaction rollback, network partitions | Idempotency, eventual consistency, strong retry policies                         |
| **Configuration Drift**   | Unexpected behavior                   | Manual overrides, CI/CD misconfigs       | Immutable infrastructure, GitOps (e.g., **ArgoCD**), policy-as-code (e.g., **Open Policy Agent**) |

---

## **Schema Reference**
Below is a structured schema for tracking availability incidents. Use this template in **Jira, Confluence, or a custom tool**.

| **Field**               | **Type**       | **Description**                                                                                     | **Example Values**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `IncidentID`            | String         | Unique identifier for the incident.                                                                | `AV-2024-0042`                              |
| `DetectionTime`         | Timestamp      | When the issue was first detected.                                                                  | `2024-05-15T14:30:00Z`                     |
| `Severity`              | Enum           | Critical/High/Medium/Low based on impact.                                                            | `High`                                      |
| `AffectedComponent`     | String[]       | Services, databases, or endpoints impacted.                                                        | `["api-service", "redis-cache"]`            |
| `RootCause`             | String         | Categorized cause (e.g., `Configuration`, `Dependency`, `Bug`).                                    | `Dependency: Database connection timeout`   |
| `MetricsAffected`       | Object[]       | Key metrics violating SLOs (e.g., `error_rate`, `latency`).                                      | `{ "metric": "http_errors", "threshold": 1 }`|
| `Dependencies`          | String[]       | External systems failing (e.g., payment gateway, CDN).                                            | `["stripe-api", "cloudflare"]`              |
| `ResolutionTime`        | Timestamp      | When the issue was resolved.                                                                      | `2024-05-15T14:45:00Z`                     |
| `MTTR`                  | Duration       | Mean Time to Recovery (calculated from detection to resolution).                                  | `PT15M` (15 minutes)                        |
| `PostmortemLink`        | URL            | Link to the documented analysis.                                                                  | `https://confluence.example.com/docs/av-2024-0042` |
| `AffectedUsers`         | Integer        | Estimated number of users impacted.                                                                 | `5000`                                      |

---

## **Query Examples**
### **1. Detecting High Error Rates (Prometheus)**
```promql
# Alert if error rate exceeds 1% in the last 5 minutes
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
  > (0.01 * sum(rate(http_requests_total[5m])) by (service))
```

### **2. Identifying Slow Endpoints (Metrics + Logs)**
```bash
# Filter slow API responses (latency > 1s) in logs
grep "duration_ms>" /var/log/api-service.log | awk '{if ($3 > 1000) print $0}'
```

### **3. Kubernetes Pod Crashes (CLI)**
```sh
# List crashing pods with crash loop backoff
kubectl get pods --field-selector=status.phase=CrashLoopBackOff -A
```

### **4. Database Connection Pool Exhaustion (PostgreSQL)**
```sql
# Check active connections in PostgreSQL
SELECT usename, count(*) as connections
FROM pg_stat_activity
GROUP BY usename
ORDER BY count(*) DESC;
```

### **5. External API Latency (cURL + jq)**
```bash
# Measure latency to an external API
time curl -s -o /dev/null -w "API Latency: %{time_total}s\n" https://api.example.com/health
```

---

## **Related Patterns**
To complement **Availability Troubleshooting**, leverage these patterns:

| **Pattern**                          | **Purpose**                                                                 | **Tools/Frameworks**                          |
|--------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **[Resilience Testing]**             | Proactively test system resilience with chaos experiments.                  | Chaos Mesh, Gremlin, Fault Injection Simulator |
| **[Distributed Tracing]**            | Trace requests across microservices to identify latency bottlenecks.       | Jaeger, Zipkin, OpenTelemetry               |
| **[Circuit Breaker]**                | Prevent cascading failures by limiting calls to unstable services.         | Hystrix, Resilience4j, Envoy               |
| **[Auto-Scaling]**                   | Dynamically adjust resources based on load.                                  | Kubernetes HPA, AWS Auto Scaling            |
| **[Chaos Engineering]**               | Deliberately introduce failures to improve fault tolerance.                 | Chaos Monkey, Chaos Gorilla                 |
| **[Service Mesh Observability]**     | Centralized monitoring of service-to-service traffic.                       | Istio, Linkerd, Consul                       |
| **[Golden Signals]**                 | Focus on **latency, traffic, errors, saturation** for observability.       | SRE Book (Google)                            |

---

## **Best Practices**
1. **Automate Alerting**: Define **SLO-based alerts** (e.g., error budget alerts).
2. **Centralize Logs**: Use **ELK Stack, Loki, or Datadog** for cross-service log analysis.
3. **Document Failures**: Maintain a **blameless postmortem repository** (e.g., GitHub Wiki).
4. **Simulate Failures**: Run **chaos experiments** during non-peak hours.
5. **Review Dependencies**: Regularly audit **external API contracts** and SLAs.
6. **Capacity Planning**: Use **forecasting tools** (e.g., **Prometheus Forecast**) to anticipate scaling needs.

---
**Last Updated**: `[Insert Date]`
**Version**: `1.2`