# **[Pattern] Security Observability Reference Guide**

---

## **Overview**

**Security Observability** is a proactive approach to detecting, investigating, and responding to security threats by leveraging comprehensive event collection, structured data analysis, and real-time correlation across systems. Unlike traditional security monitoring (e.g., SIEM alerts), observability prioritizes **context-rich visibility** into system behavior, enabling faster threat detection, reduced false positives, and improved incident response. This pattern integrates **telemetry data** (logs, metrics, traces) from security controls (firewalls, IAM, EDR, WAF) and operational systems (servers, containers, cloud infrastructure) into a unified observability platform. Key components include:
- **Centralized collection** of security-relevant events
- **Enrichment** with contextual metadata (user identity, resource state, network flow)
- **Detection rules** (baselines, anomaly scoring, behavioral analysis)
- **Alerting** tied to business impact (e.g., data exfiltration, privilege escalation)
- **Incident lifecycle** automation (containment, remediation, post-mortem)

This guide covers implementation best practices, schema standards, and query techniques to operationalize security observability at scale.

---

## **Implementation Details**

### **1. Core Principles**
| **Principle**               | **Description**                                                                                     | **Example Use Case**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Unified Data Model**      | Standardize event schemas (e.g., OpenTelemetry, Common Event Format) to enable cross-tool analysis. | Correlating EDR logs with cloud trail events. |
| **Retention & Freshness**   | Balance cost vs. compliance (e.g., 30 days for operational, 730+ days for forensics).              | Investigating a supply-chain attack.        |
| **Context over Alert Fatigue** | Prioritize event enrichment (user context, binary analysis) over raw logs.                      | Identifying lateral movement via cross-EC2 traffic. |
| **Proactive Detection**     | Use ML/AI to detect anomalies (e.g., unusual API calls, S3 bucket access patterns).              | Detecting IoT botnets via unencrypted traffic. |

### **2. Key Components**
| **Component**               | **Description**                                                                                     | **Implementation Notes**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **Event Sources**           | Security controls (AWS GuardDuty, CrowdStrike, Splunk SOAR), infrastructure (Kubernetes, cloud logs). | Use **Fluent Bit** for lightweight log forwarding. |
| **Enrichment Pipeline**     | Add metadata (e.g., threat intelligence feeds, user roles, IP reputation).                          | Integrate **Vect** or **OpenSearch** for enrichment. |
| **Detection Layer**         | Rules (SIGMA, PromQL, custom ML) and detection frameworks (Falco, ISH).                              | Leverage **Prometheus Alertmanager** for scaling.  |
| **Incident Management**     | Triage workflows (e.g., Jira, ServiceNow) tied to observability dashboards.                           | Use **Slack/Teams integrations** for alerts.      |

### **3. Schema Reference**
Below is a **standardized schema** for security observability events (adapted from [OpenTelemetry Security Context](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/security.md)).

| **Field**                     | **Type**       | **Description**                                                                                     | **Example Values**                          |
|--------------------------------|----------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------|
| `event.time`                  | `datetime`     | ISO-8601 timestamp of the event.                                                                     | `2023-10-15T14:30:00Z`                      |
| `event.dataset`               | `string`       | Source system (e.g., `aws_cloudtrail`, `crowdstrike`).                                              | `custodian_aws`                             |
| `user.id`                     | `string`       | Unique identifier for the user (e.g., IAM ARN, Active Directory SID).                               | `arn:aws:iam::123456789012:user/admin`      |
| `user.name`                   | `string`       | Display name of the user.                                                                        | `sysadmin_john`                            |
| `user.authentication.method`  | `string`       | MFA, password, SSO, etc.                                                                             | `aws_iam`                                   |
| `process.executable`          | `string`       | Full path to the binary (e.g., `/usr/bin/python3`).                                               | `/opt/venv/bin/python`                      |
| `network.destination.ip`      | `string`       | Comma-separated list of IPs accessed.                                                              | `192.168.1.100,8.8.8.8`                     |
| `network.protocol`            | `string`       | `tcp`, `udp`, `dns`, etc.                                                                           | `https`                                     |
| `resource.cloud.provider`     | `string`       | `aws`, `gcp`, `azure`, etc.                                                                         | `aws`                                       |
| `resource.instance.id`        | `string`       | Unique ID for the affected resource (e.g., EC2 instance ID).                                       | `i-1234567890abcdef0`                       |
| `security.rule`              | `string`       | Detection rule name (e.g., `CrowdStrike_Bruteforce`).                                               | `SIGMA_RDP_BruteForce`                     |
| `security.product`            | `string`       | Security tool generating the event (e.g., `CrowdStrike`, `AWS_KMS`).                                | `AWS_CloudTrail`                            |
| `threat.integrations`         | `array<string>`| Linked threat intelligence feeds (e.g., `MITRE_Tactic`).                                           | `MITRE_T0005`, `ABUSECH_Blacklist`          |

---
**Example Event JSON:**
```json
{
  "event": {
    "time": "2023-10-15T14:30:00Z",
    "dataset": "aws_cloudtrail",
    "id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
    "action": "PutObject"
  },
  "user": {
    "id": "arn:aws:iam::123456789012:user/devops",
    "name": "devops_alice",
    "authentication.method": "aws_iam"
  },
  "resource": {
    "cloud.provider": "aws",
    "type": "s3_bucket",
    "instance.id": "bucket-name",
    "bucket.arn": "arn:aws:s3:::bucket-name"
  },
  "network": {
    "source.ip": "192.168.1.50",
    "destination.ip": "s3.amazonaws.com",
    "protocol": "https"
  },
  "security": {
    "rule": "S3_Inappropriate_CrossRegionAccess",
    "product": "AWS_CloudTrail"
  }
}
```

---

## **Query Examples**
### **1. Detect Unauthorized API Calls (CloudTrail)**
**Objective**: Find API calls from IAM users outside their usual regions.
**Query (OpenSearch/Kibana)**:
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event.dataset": "aws_cloudtrail" } },
        {
          "bool": {
            "should": [
              { "term": { "event.action": "PutObject" } },
              { "term": { "event.action": "ListBuckets" } }
            ]
          }
        }
      ],
      "filter": [
        {
          "script": {
            "script": {
              "source": """
                // Calculate distance between user's home region and event region
                String userRegion = ctx.user.homeRegion;
                String eventRegion = ctx.event.region;
                int distance = Math.abs(userRegion.hashCode() - eventRegion.hashCode());
                return distance > 50; // Threshold for "unusual"
              """
            }
          }
        }
      ]
    }
  }
}
```

### **2. Correlate EDR Alerts with Cloud Logs (Falco/CrowdStrike)**
**Objective**: Match CrowdStrike indicators of compromise (IOCs) in EDR alerts to cloud resource access.
**Query (Grafana/Loki)**:
```logql
# CrowdStrike IOCs in logs
crowdstrike_alerts
| json
| where severity = "High"
| label_map
| line_format "{{.actor}} accessed {{.resource}} via {{.protocol}}"

# CloudTrail access events for the same actor/resource
aws_cloudtrail_events
| filter user.id = "{{.actor}}"
| filter resource.instance.id = "{{.resource}}"
| table(user.id, event.time, event.action)
```
**Output**:
```
actor=admin_john resource=s3://bucket-name
time=2023-10-15T14:30:00Z action=PutObject
```

### **3. Detect Lateral Movement (Kubernetes Audit Logs)**
**Objective**: Flag pods executing `ssh` or `rclone` commands to other nodes.
**Query (PromQL)**:
```promql
# Pods with lateral movement indicators
sum by (pod, namespace) (
  rate(kubernetes_pod_container_log_bytes_total{job="kube-audit-logging"}[5m])
  unless on(pod, namespace)
  rate(kubernetes_pod_container_log_bytes_total{job="kube-audit-logging", log="authentication,request"})
)
|> match("ssh|rclone|nc")
|> count by (pod)
```
**Alert Condition**: Trigger if `count > 0` for pods in `db-*` namespaces.

### **4. Anomaly Detection (Metrics + ML)**
**Objective**: Detect unexpected increases in failed login attempts.
**Query (Prometheus)**:
```promql
# Failed logins per user (adapted for your IDS)
rate(aws_guardduty_failed_logins_total{method="SSH"}[1h])
/ on(user_id) count(aws_guardduty_failed_logins_total{method="SSH"})
> 5  # Threshold: 5x baseline
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                          |
|----------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **[Centralized Log Management]** | Aggregate logs from diverse sources (e.g., Loki, OpenSearch) for security analysis.                 | Require scalable log retention.         |
| **[Threat Detection with ML]**    | Use anomaly detection (e.g., Prometheus Anomaly Detection, Datadog ML) for zero-day threats.       | High-volume environments.               |
| **[Incident Response Automation]** | Automate containment (e.g., terminate pods, revoke IAM policies) via observability data.          | Critical infrastructure.                |
| **[Security Posture Management]** | Continuously audit compliance (CIS, CISOs) using observability metrics.                            | Regulated industries (HIPAA, GDPR).     |
| **[Chaos Engineering for Security]** | Inject failures (e.g., fake exfiltration) to test observability and detection capabilities.      | Security maturity model (SMM).          |

---

## **Further Reading**
- [OpenTelemetry Security Context](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/security.md)
- [MITRE ATT&CK for Cloud](https://attack.mitre.org/extensions/cloud/)
- [SIGMA Rules Repository](https://github.com/SigmaHQ/sigma)
- [AWS Security Lake](https://aws.amazon.com/securitylake/) (Centralized SIEM)

---
**Last Updated**: [Insert Date]
**Contributors**: [List Maintainers]