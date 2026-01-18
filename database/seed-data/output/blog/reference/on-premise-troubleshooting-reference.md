# **[Pattern] On-Premise Troubleshooting Reference Guide**

---

## **Overview**
The **On-Premise Troubleshooting Pattern** provides a structured methodology for diagnosing and resolving technical issues in environments where systems, applications, or infrastructure reside entirely within an organization’s physical data center or private network. This guide outlines a systematic approach to log collection, analysis, and root-cause identification (RCI) while adhering to on-prem best practices, including compliance, security, and minimal external dependency impacts.

This pattern emphasizes:
- **Localized fault isolation** (avoiding cloud-driven dependencies for diagnostics).
- **Log-centric troubleshooting** (leveraging centralized or federated log management).
- **Resource efficiency** (minimizing performance overhead during diagnostics).
- **Reproducibility** (ensuring troubleshooting steps can be validated across environments).

---

## **Implementation Details**

### **Core Components**
| **Component**               | **Description**                                                                                     | **Key Tools/Artifacts**                                                                       |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Log Collection Layer**    | Gathers system, application, and network logs from distributed on-premise nodes.                 | Splunk, ELK Stack, Graylog, or custom syslog collectors.                                    |
| **Log Storage & Processing**| Stores logs for retention and applies filters, enrichments, and anomaly detection.                | S3-compatible on-prem storage (MinIO), Kafka for log streaming, or Fluentd/Fluent Bit.     |
| **Troubleshooting Workflows**| Defines step-by-step diagnostic procedures (e.g., binary search for failures, impact analysis).    | Playbooks (Ansible, Terraform), custom scripts, or internal wikis.                           |
| **Incident Correlation**    | Links logs from disparate sources (e.g., load balancer, databases, APIs) to pinpoint root causes. | Correlation engines (Splunk Correlation Search, ELK’s Painless scripts).                    |
| **Post-Mortem & Remediation**| Documents findings, implements fixes, and prevents recurrence via automated testing.               | Jira/Confluence tickets, automated test suites (Robot Framework, Selenium).                 |
| **Security & Compliance**   | Ensures troubleshooting adheres to data residency policies and audit requirements.               | SIEM tools (IBM QRadar), on-prem firewall/VPN for secure log access.                        |

---

### **Troubleshooting Workflow Phases**
1. **Preparation**
   - Define **SLOs (Service Level Objectives)** and **RTOs (Recovery Time Objectives)** for troubleshooting.
   - Document **baseline metrics** (CPU, memory, latency) to identify deviations.

2. **Log Collection & Filtering**
   - **Scope**: Limit logs to affected systems (e.g., `hostname = "web-server-01"`).
   - **Filters**: Use regex, timestamps, or severity levels (e.g., `status_code = "500"`).
   - **Example Filter (Splunk)**:
     ```sql
     index=webapp src_host="web-server-01" | stats count by status_code | where count > 100
     ```

3. **Root-Cause Analysis**
   - **Binary Search**: Narrow down failure patterns by eliminating healthy components.
   - **Impact Mapping**: Trace dependencies (e.g., database timeouts → API failures → client errors).
   - **Tools**: Use **Grafana dashboards** for real-time metric correlation with logs.

4. **Validation & Fix Implementation**
   - Reproduce the issue in staging with **scenario isolation** (e.g., containerized test environments).
   - Apply fixes via **infrastructure-as-code (IaC)** (Pulumi, Chef) for consistency.

5. **Post-Mortem & Knowledge Capture**
   - Update **runbooks** with steps, screenshots, and root-cause documentation.
   - Schedule **retrospective meetings** to refine workflows.

---

## **Schema Reference**
Below are key data structures used in on-premise troubleshooting.

| **Entity**               | **Schema**                                                                                     | **Example Field**                     |
|--------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------|
| **Log Record**           | `{ timestamp: ISO8601, source_host: str, level: str, message: str, metadata: dict }`           | `{"timestamp": "2023-10-15T14:30:00Z", "source_host": "db-02", "level": "ERROR", "message": "Connection timeout"}` |
| **Failure Pattern**      | `{ event_id: str, affected_services: list, likelihood: int, severity: str }`                  | `{"event_id": "api-500-error", "affected_services": ["user-service"], "severity": "CRITICAL"}` |
| **Diagnostic Playbook**  | `{ steps: list[dict], duration: int, owner: str }`                                             | `{ "steps": [{"action": "Check disk space", "command": "df -h"}, {"action": "Restart service", "command": "systemctl restart nginx"}], "owner": "devops-team"}` |
| **Impact Graph**         | `{ node: str, dependencies: list[str], health_status: str }`                                   | `{"node": "auth-service", "dependencies": ["user-db", "cache-redis"], "health_status": "DEGRADED"}` |
| **Post-Mortem Report**   | `{ issue: str, root_cause: str, resolution: str, impacted_users: int, metrics: dict }`        | `{"issue": "High latency", "root_cause": "Network latency to S3", "resolution": "Upgrade VPN bandwidth", "metrics": {"p99_latency": 2.5}}` |

---

## **Query Examples**
### **1. Correlating Logs with High CPU Usage**
**Scenario**: Identify processes causing CPU spikes on a server.
**Query (ELK Stack)**:
```json
GET /logs-_doc/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "host": "server-01" } },
        { "range": { "@timestamp": { "gte": "now-1h", "lte": "now" } } }
      ],
      "filter": [
        { "term": { "log.level": "WARNING" } },
        { "script": { "script": "doc['process_name'].value.contains('postgres') || doc['process_name'].value.contains('java')", "lang": "painless" } }
      ]
    }
  },
  "aggs": {
    "high_cpu_processes": {
      "terms": { "field": "process_name.keyword", "size": 5 }
    }
  }
}
**Output Analysis**:
- Top processes (e.g., `postgres`, `java`) with high CPU usage.
- Cross-reference with **top** command outputs during the same timestamp.

---

### **2. Tracing API Failures to Database Timeouts**
**Scenario**: Diagnose a spike in `502 Bad Gateway` errors for an API.
**Query (Splunk)**:
```sql
index=api_gateway src="api-gateway-01" status=502
| stats count by client_ip, upstream_host, request_method
| join
  [ search index=database_logs status="TIMEOUT" db_host="db-primary" | stats count by client_ip, upstream_host ]
| where match(client_ip, upstream_host)
| table client_ip, upstream_host, count
```
**Output Action**:
- Identify correlated `client_ip`/`upstream_host` pairs.
- Check database logs for `TIMEOUT` events during the same timestamps.

---

### **3. Finding MissingLogs Due to File Permissions**
**Scenario**: Verify log file permissions on all servers.
**Script (Bash)**:
```bash
#!/bin/bash
find /var/log -type f -name "*.log" -not -perm -400 -exec ls -la {} \;
```
**Automation (Ansible)**:
```yaml
- name: Check log file permissions
  ansible.builtin.stat:
    path: "{{ item }}"
  loop: /var/log/*.log
  register: log_permissions
  ignore_errors: yes
- name: Fail if permissions are incorrect
  ansible.builtin.fail:
    msg: "Permission issue detected on {{ item.item }}"
  loop: "{{ log_permissions.results }}"
  when: item.stat.mode & 0500 != 0400
```

---

## **Requirements & Considerations**
| **Requirement**               | **Implementation Guidance**                                                                                     |
|-------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Data Residency**            | Store logs on on-prem storage (e.g., MinIO) or encrypt logs before transferring to external tools (Splunk).   |
| **Security**                  | Restrict log access via **RBAC** (e.g., Splunk access roles) and **VPN** for remote troubleshooting.           |
| **Performance Overhead**      | Use sampling (e.g., 10% of logs) for high-volume systems or compress logs before ingestion.                  |
| **Audit Compliance**          | Retain logs for **mandated periods** (e.g., 7 years for GDPR) and enable **immutable log storage**.           |
| **Tooling Isolation**         | Avoid cloud dependencies; use on-prem alternatives (e.g., **Grafana Cloud → Grafana Enterprise**).           |

---

## **Related Patterns**
1. **[Observability via OpenTelemetry]**
   - *How it relates*: Integrates with on-premise log collection for distributed tracing and metrics correlation.

2. **[Chaos Engineering for Resilience]**
   - *How it relates*: Validates troubleshooting playbooks by intentionally inducing failures in staging environments.

3. **[Infrastructure as Code (IaC)]**
   - *How it relates*: Ensures consistent environments for reproducible troubleshooting (e.g., Terraform modules for log collectors).

4. **[Incident Response Playbooks]**
   - *How it relates*: Provides standardized procedures for common on-premise failures (e.g., disk full, network partition).

5. **[Zero Trust Networking]**
   - *How it relates*: Secures log access by enforcing least-privilege access to troubleshooting tools (e.g., SIEM dashboards).

---
**Note**: For complex troubleshooting, combine this pattern with **[Distributed Tracing]** and **[AIOps Automation]** to reduce manual effort. Always validate fixes in a **staging environment** before applying to production.