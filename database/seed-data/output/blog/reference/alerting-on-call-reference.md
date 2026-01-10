---
# **[Pattern] Alerting & On-Call Management – Reference Guide**
*A standardized approach to proactive incident detection and coordinated response in software systems.*

---

## **1. Overview**
Alerting & On-Call Management is a critical pattern for **detecting, triaging, and resolving incidents** while minimizing downtime and reducing on-call fatigue. This guide outlines best practices for designing scalable alerting systems, structuring on-call rotations, and automating responses. Key goals include:
- **Reducing alert noise** to avoid alert fatigue.
- **Ensuring rapid incident response** with clear escalation paths.
- **Automating routine tasks** to free up human responders.
- **Improving observability** to proactively identify issues before they impact users.

This pattern integrates with **Observability (Logging, Metrics, Tracing)**, **Incident Management**, and **DevOps Collaboration** patterns.

---

## **2. Key Components & Schema Reference**
The pattern consists of **five core components**, detailed in the following schema:

| **Component**               | **Description**                                                                 | **Key Properties**                                                                                     | **Example Tools**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **1. Alert Definition**     | Rules for triggering alerts based on observed system behavior.                 | - **Metric/Log source** (e.g., CPU usage, error rate) <br> - **Threshold** (e.g., >95% latency) <br> - **Severity level** (Critical/Warning/Info) <br> - **Condition duration** (e.g., 5-minute rolling window) | Prometheus AlertManager, Datadog, Splunk ES                                                                 |
| **2. Alert Routing**        | Rules for distributing alerts to the right teams/individuals.                  | - **Recipient groups** (e.g., SREs, Dev Teams) <br> - **Escalation policies** (e.g., after 30 mins) <br> - **On-call schedules** (e.g., rotating shifts) <br> - **Notification channels** (Slack, PagerDuty, Email) | PagerDuty, Opsgenie, VictorOps, Slack/Apple Notifications                                           |
| **3. On-Call Rotation**     | Schedule defining who is on-call when.                                         | - **Rotation type** (e.g., 24/7 shifts, project-based) <br> - **On-call duration** (e.g., 4 hours) <br> - **Recovery time** (e.g., 4 hours off) <br> - **Team assignments** (e.g., SREs, Dev Leads) | VictorOps, Opsgenie, Shift (by Frictionless), Rotating Callout                                       |
| **4. Incident Response**    | Playbook for triaging and resolving incidents.                                | - **Escalation ladder** (e.g., Tier 1 → Tier 2 → Tier 3) <br> - **SLA targets** (e.g., P1 = 15 mins) <br> - **Postmortem template** <br> - **Communication channels** (e.g., Slack #incident-channel) | Jira, Linear, Slack, GatherTown (for remote standups)                                                 |
| **5. Alert Suppression**    | Mechanisms to mute alerts during planned outages or low-priority events.      | - **Suppression duration** (e.g., 60 mins) <br> - **Approval required?** (e.g., for Critical alerts) <br> - **Reason field** (e.g., "Database migration") | Prometheus AlertManager, Datadog Alerts, PagerDuty                                                                 |

---

## **3. Implementation Details**
### **3.1 Alert Definition Best Practices**
- **Avoid alert fatigue**:
  - Use **adaptive thresholds** (e.g., dynamic baselines based on historical data).
  - Group related alerts (e.g., "Database connection pool exhausted" + "High latency").
- **Severity levels**:
  - **Critical**: Immediate action required (e.g., "API 5xx errors > 90%").
  - **Warning**: Monitor but not urgent (e.g., "Disk usage > 80%").
  - **Info**: Non-critical (e.g., "API 4xx errors increased").
- **Condition duration**:
  - Alerts should fire only if a condition persists for **X minutes** (e.g., 5 mins for latency spikes).

**Example Alert Rule (Prometheus):**
```yaml
groups:
- name: high_latency_alerts
  rules:
  - alert: HighAPILatency
    expr: api_request_duration_seconds{quantile="0.95"} > 1.0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High 95th percentile API latency (>1s)"
      description: "Latency exceeded threshold for 5 minutes."
```

---

### **3.2 Alert Routing & Escalation**
- **Recipient groups**:
  - Use **team-based routing** (e.g., "Database Team" for DB-related alerts).
  - Assign **individual on-call contacts** (e.g., `@sre-oncall` for critical alerts).
- **Escalation policies**:
  - Escalate after **X minutes** if no response (e.g., 30 mins for Critical alerts).
  - Use **time-based escalation** (e.g., escalate at 2 AM to avoid weekends).
- **Notification channels**:
  - **Primary**: Slack/PagerDuty (real-time).
  - **Secondary**: Email (for documentation).
  - **Tertiary**: SMS (for emergencies).

**Example Escalation Policy (PagerDuty):**
```
- Alert: "Database Connection Pool Exhausted"
  - Primary: @sre-oncall (Slack)
  - Escalation after 30 mins: @dev-lead-database (PagerDuty SMS)
  - Escalation after 60 mins: #incident-channel (Slack)
```

---

### **3.3 On-Call Rotation Design**
- **Rotation types**:
  - **24/7 shifts**: Single person on-call per shift (good for small teams).
  - **Project-based**: Assign on-call to feature teams (good for large teams).
- **Duration & recovery**:
  - **On-call duration**: 4–8 hours (longer for critical systems).
  - **Recovery time**: Equal to on-call duration (e.g., 4 hours off).
- **Tooling**:
  - Use **calendar sync** (e.g., Google Calendar integration) to avoid double-bookings.
  - Allow **swap requests** for personal events (with approval).

**Example Rotation Schedule (Opsgenie):**
| Time Slot       | On-Call Team          | Primary Contact       | Secondary Contact   |
|-----------------|-----------------------|-----------------------|---------------------|
| 00:00–04:00     | SRE Team A            | @alice_sre            | @bob_sre            |
| 04:00–08:00     | Dev Team B (Backend)  | @charlie_dev          | @dave_dev           |
| ...             | ...                   | ...                   | ...                 |

---

### **3.4 Incident Response Playbook**
- **Incident triage**:
  - **First responder**: Acknowledge the alert within **SLA** (e.g., 5 mins for Critical).
  - **Escalation**: Follow the **escalation ladder** (Tier 1 → Tier 2).
- **Communication**:
  - Use a **dedicated Slack channel** (e.g., `#incident-alerts`) for real-time updates.
  - Publish **incident status pages** (e.g., via Statuspage or PostHog).
- **Postmortem**:
  - **Root cause analysis**: Identify systemic issues.
  - **Action items**: Define fixes and ownership.
  - **Blend into engineering**: Share learnings in team meetings.

**Example Incident Playbook (Slack Template):**
```
🚨 INCIDENT: [API Downtime - Critical]
**Time**: 10:00 AM (UTC)
**Severity**: Critical
**Affected Users**: All customers
**Current Status**: Investigation (Escalated to Tier 2)

**Actions Taken**:
- @alice_sre: Checked logs → DB connection timeout
- @bob_sre: Rebooted DB node (10:05 AM)

**Next Steps**:
- @charlie_dev: Review connection pool limits (Due: 11:00 AM)
- @dave_ops: Monitor DB health for 24h

📄 Postmortem: [Link to Jira ticket]
```

---

### **3.5 Alert Suppression**
- **When to suppress**:
  - Planned outages (e.g., "Deploying v2.0 at 02:00 AM").
  - Low-priority events (e.g., "Disk usage 90%" during a backup).
- **Suppression rules**:
  - **Critical alerts**: Require manual approval.
  - **Warning/Info alerts**: Auto-suppress for predefined durations.
- **Tools**:
  - Use **alertmanager config** (Prometheus) or **suppression policies** (Datadog).

**Example Suppression (Prometheus Alertmanager):**
```yaml
suppress_rules:
- match:
    severity: warning
    alertname: HighDiskUsage
  duration: 1h
  evaluation_interval: 5m
```
**Manual Suppression (PagerDuty):**
```
Reason: "Planned database migration"
Duration: 1 hour
Approver: @dev-lead-database
```

---

## **4. Query Examples**
### **4.1 Querying Alerts (Prometheus/Grafana)**
**Find all active warnings in the last 30 mins:**
```promql
alertmanager_warnings{status="firing"} > 0
```
**List all suppressed alerts:**
```promql
alertmanager_suppressions > 0
```

### **4.2 Querying On-Call Status (PagerDuty API)**
**Check if a user is on-call at a given time:**
```bash
curl -X GET "https://api.pagerduty.com/v2/users/{USER_ID}/on-call-schedules" \
     -H "Authorization: Token TOKEN"
```
**Filter for users on-call in "Database Team":**
```bash
curl -X GET "https://api.pagerduty.com/v2/users?status=on-call&schedule_group=database" \
     -H "Authorization: Token TOKEN"
```

### **4.3 Querying Incident Metrics (Jira API)**
**List open incidents in the last 7 days:**
```bash
curl -X GET "https://your-domain.atlassian.net/rest/api/3/search?jql=project=INCIDENT AND status != Done AND created >= -7d" \
     -H "Authorization: Bearer TOKEN"
```

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **Connection to Alerting & On-Call**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Observability](https://example.com/observability)** | Logging, metrics, and tracing for system visibility.                          | Alerts are triggered by **metrics/logs** from observability tools.                                   |
| **[Incident Management](https://example.com/incident-mgmt)** | Structured process for handling incidents from detection to resolution.       | On-call management and alert routing **feed into incident workflows**.                               |
| **[DevOps Collaboration](https://example.com/devops-collab)** | Cross-team coordination for releases and incidents.                          | On-call schedules **integrate with DevOps tools** (e.g., Jira, Slack).                                |
| **[Chaos Engineering](https://example.com/chaos-engineering)** | Proactively testing system resilience.                                          | Alerting helps **detect chaos experiment failures** and escalate them as incidents.                   |
| **[Configuration as Code](https://example.com/cfg-as-code)** | Managing infrastructure via code.                                              | Alert rules and on-call schedules can be **version-controlled** (e.g., Terraform, Ansible).       |

---

## **6. Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                                                       | **Mitigation**                                                                                         |
|---------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Too many alerts**            | Alert fatigue leads to ignored notifications.                                | - Use **adaptive thresholds**. <br> - **Group related alerts**.                                         |
| **Static on-call schedules**   | Unbalanced workload or missed coverage.                                      | - **Dynamic rotations** (e.g., shift-based). <br> - **Swap requests** for personal time.            |
| **No postmortem process**      | Root causes repeat.                                                          | - **Standardize postmortem templates**. <br> - **Share in team meetings**.                           |
| **Unstructured incident comms**| Miscommunication during crises.                                            | - **Dedicated Slack channels**. <br> - **Incident status pages**.                                      |
| **Over-reliance on automation**| False positives or missed edge cases.                                        | - **Manual review for Critical alerts**. <br> - **Regular alert rule audits**.                       |

---

## **7. Tools & Integrations**
| **Category**          | **Tools**                                                                                     | **Key Features**                                                                                     |
|-----------------------|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Alert Management**  | Prometheus AlertManager, Datadog, Splunk ES, New Relic                                         | - Multi-channel notifications. <br> - Adaptive thresholds. <br> - Suppression rules.                 |
| **On-Call Scheduling**| PagerDuty, Opsgenie, VictorOps, Shift, Rotating Callout                                     | - Calendar sync. <br> - Escalation policies. <br> - Swap request workflows.                         |
| **Incident Tracking** | Jira, Linear, PagerDuty Incidents, Statuspage                                            | - Incident playbooks. <br> - Postmortem templates. <br> - Public status pages.                     |
| **Observability**     | Prometheus, Grafana, Datadog, New Relic, ELK Stack                                         | - Metrics/Logs for alert triggers. <br> - Dashboards for monitoring.                                |
| **Collaboration**     | Slack, Microsoft Teams, GatherTown                                                     | - Real-time incident channels. <br> - Remote standups.                                               |

---
## **8. Further Reading**
- **[SRE Book (Google)](https://sre.google/sre-book/table-of-contents/)** – Chapter on Alerting.
- **[PagerDuty Alerting Best Practices](https://support.pagerduty.com/docs/guidelines/alerting-best-practices)**.
- **[Prometheus Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)**.
- **[Incident Management Guide (Google)](https://cloud.google.com/blog/products/operations/incident-management)**.