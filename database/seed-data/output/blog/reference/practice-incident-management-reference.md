# **[Pattern] Incident Management Practices – Reference Guide**

---
## **Overview**
This reference guide outlines **Incident Management Practices**, a structured approach to detecting, responding to, and resolving operational disruptions in IT systems, applications, or services. Leveraging industry standards (ITIL, DevOps, MSP), this pattern ensures **minimized downtime**, **improved reliability**, and **better stakeholder communication**. It integrates **prevention (proactive monitoring), detection (alerting), response (triage), and recovery (post-mortem)**, while aligning with scalable, automated workflows for modern environments.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Incident**           | A disruption in service, degradation, or failure that affects end-users or business operations. | A database outage causing API latency spikes.                              |
| **Severity Level**     | Categorizes incidents by impact (e.g., **P0: Critical**, P1: High, P2: Medium, P3: Low).           | P0: Complete system downtime; P3: Minor UI rendering delay.                 |
| **SLA (Service Level Agreement)** | Time-bound response/recovery targets (e.g., P0: <30 min resolution).                        | Cloud provider guarantees 99.95% uptime with 1-hour recovery objectives.    |
| **Runbook**            | Predefined steps to resolve common incidents without human intervention.                          | Automated failover script for primary database failure.                    |
| **Post-Mortem**        | Structured analysis of root causes, corrective actions, and lessons learned post-resolution.     | Documenting why a misconfigured firewall caused a weekend outage.           |
| **On-Call Rotation**   | Scheduled availability of support teams for incident response (e.g., 24/7 coverage).             | Engineers alternate 12-hour shifts for production monitoring.               |

---

## **Schema Reference**
Below is a **canonical schema** for structuring incident management data in tools (e.g., Jira Service Management, PagerDuty, or custom APIs).

| **Field**              | **Type**       | **Description**                                                                                                                                                                                   | **Example Value**                          |
|------------------------|---------------|--------------------------------------------------------------------------------------------------------------------------------                                                              |--------------------------------------------|
| `incident_id`          | `String`      | Unique identifier for the incident (UUID or auto-incremented).                                                                                                                                     | `"inc-78f3a1b2-4d56-78e9"`                  |
| `title`                | `String`      | Concise description of the issue (max 140 chars).                                                                                                                                                   | `"API Gateway Latency Spikes (P1)"`          |
| `severity`             | `Enum`        | Predefined levels: `P0` (Critical), `P1` (High), `P2` (Medium), `P3` (Low).                                                                                                                   | `"P1"`                                     |
| `status`               | `Enum`        | Lifecycle state: `New`, `Triage`, `In Progress`, `Resolved`, `Verified`, `Closed`.                                                                                                           | `"In Progress"`                            |
| `priority`             | `Number`      | Numerical priority (e.g., `1–5`; lower = higher urgency).                                                                                                                                           | `2` (High)                                  |
| `created_at`           | `Timestamp`   | UTC timestamp of incident detection.                                                                                                                                                             | `"2024-04-20T08:45:00Z"`                   |
| `detected_by`          | `String`      | System/tool that triggered the alert (e.g., Prometheus, ELK Stack).                                                                                                                               | `"Datadog Monitor: API_ResponseTime"`       |
| `affected_systems`     | `Array`       | List of impacted services/applications (e.g., `{ "microservice": "user-auth", "cloud_region": "us-west-2" }`).                                                                               | `[{ "name": "checkout-service", "env": "prod" }]` |
| `root_cause`           | `String`      | Initial hypothesis (updated during triage).                                                                                                                                                       | `"Memory leak in Redis cache cluster."`      |
| `resolution_time_s`    | `Number`      | Time (seconds) from triage start to resolution.                                                                                                                                                   | `1830` (30.5 min)                           |
| `sla_met`              | `Boolean`     | Whether SLA target was met (e.g., `true`/`false` for P0: <30min).                                                                                                                               | `false`                                    |
| `assigned_to`          | `String`      | Engineer/team ID handling the incident.                                                                                                                                                           | `"engineer-456"`                            |
| `escalation_path`      | `Array`       | Hierarchy for escalation (e.g., `[ "oncall-team-lead", "vendor-support" ]`).                                                                                                                   | `[{ "role": "DevOps", "email": "devops@company.com" }]` |
| `post_mortem`          | `Document`    | Structured notes on root cause, fixes, and preventive actions (see below).                                                                                                                      | `{ "root_cause": "DNS misconfiguration", ... }` |
| `related_incidents`    | `Array`       | Links to prior/follow-up incidents (e.g., duplicate or related issues).                                                                                                                      | `[ "inc-123a", "inc-456b" ]`               |

---

### **Post-Mortem Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                           | **Example**                                  |
|-------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| `summary`               | `String`      | Brief recap of the incident (1–2 sentences).                                                                                                                            | `"Redis cluster failover triggered cascading outages in checkout flow."` |
| `root_cause`            | `Array`       | Detailed analysis of causes (e.g., `[ { "type": "config", "description": "DNS TTL too high" } ]`).                                                                 | `[{ "type": "human_error", "description": "Deployed without rollback plan" }]` |
| `short_term_fixes`      | `Array`       | Immediate fixes applied (e.g., `[ "Increased Redis replicas", "Added circuit breaker" ]`).                                                                       | `[ "Enabled auto-healing for Redis pods" ]`   |
| `long_term_actions`     | `Array`       | Preventive measures (e.g., `[ { "task": "Upgrade DNS provider", "owner": "network-team", "status": "Scheduled" } ]`).         | `[{ "task": "Implement chaos engineering tests", "status": "In Progress" }]` |
| `impact_analysis`       | `Document`    | Metrics on business/product impact (e.g., `$loss`, user count affected).                                                                                                | `{ "revenue_loss": "$12K", "users_affected": 5000 }` |
| `lessons_learned`       | `Array`       | Key takeaways (e.g., `[ "Automate a health check for DNS records" ]`).                                                                                               | `[ "On-call rotation needs 24/7 coverage" ]`  |

---

## **Implementation Details**
### **1. Detection & Alerting**
- **Tools**: Use **monitoring stacks** (Prometheus + Grafana, Datadog, New Relic) with thresholds for:
  - **Latency**: P99 > 500ms (API calls).
  - **Error Rates**: >1% HTTP 5xx responses.
  - **Resource Limits**: CPU > 90% for 5 mins.
- **Alert Channels**: Route alerts to:
  - **Primary**: PagerDuty/Slack (for on-call teams).
  - **Secondary**: Email digests for non-critical incidents.

**Example Alert Rule (Prometheus):**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
  / sum(rate(http_requests_total[5m]))
  > 0.01
```

---

### **2. Triage & Escalation**
- **Initial Response**:
  - Assign a **single owner** via tooling (e.g., Jira automation).
  - Classify severity based on **impact + SLA** (e.g., revenue loss vs. user-facing bug).
  - Trigger **runbooks** if incident matches a known pattern (e.g., "Database Replica Lag").
- **Escalation Path**:
  - If unresolved in **SLA time**, escalate to **on-call manager** → **vendor support** → **executive alert** (for P0).
  - Document **escalation reasons** (e.g., "No response from SRE team after 15 mins").

**Query Example (Jira API):**
```bash
GET /rest/api/3/search
  ?jql=project=INCIDENT AND status="In Progress" AND priority="High" ORDER BY created DESC
```

---

### **3. Resolution & Post-Mortem**
- **Resolution**:
  - Apply **runbook steps** or **manual fixes** (e.g., restart service, rollback deployment).
  - Verify fix via **automated health checks** (e.g., API endpoint ping).
- **Post-Mortem**:
  - Hold a **15–30 min meeting** within **24 hours** of resolution.
  - Use a **template** (e.g., GitHub issue or Confluence page) to document findings.
  - **Attach evidence**: Logs, screenshots, or replay videos (e.g., via tools like **Datadog Synthetic Monitors**).

**Post-Mortem Template Snippet:**
```markdown
### **Incident Summary**
- **Time**: 2024-04-20 09:00–11:30 UTC
- **Impact**: 3000 users affected; $8K revenue lost.

### **Root Cause**
1. **Primary**: Misconfigured load balancer (TTL=300s) caused DNS propagation delay.
2. **Secondary**: Lack of health checks in Kubernetes deployment.

### **Actions Taken**
- [x] Increased TTL to 60s.
- [x] Added liveness probes to PodSpec.
- [ ] Audit DNS configuration for all services.

### **Owner**: @engineer-456
```

---

### **4. Reporting & Continuous Improvement**
- **Metrics to Track**:
  | **Metric**               | **Tool**               | **Frequency**  | **Example Goal**          |
  |--------------------------|------------------------|----------------|---------------------------|
| Incident MTTR (Mean Time to Resolution) | Prometheus/Grafana      | Monthly        | <20 mins for P1 incidents |
| SLA Compliance Rate       | Custom Dashboards       | Weekly         | 95%+ for P0/P1           |
| Post-Mortem Completion %  | Jira/Confluence        | Quarterly      | 100% of incidents        |
| On-Call Satisfaction      | Survey (e.g., Typeform) | Biannual       | 90% "Satisfied"           |
- **Automate Reports**:
  - Use **Prometheus + Alertmanager** to track MTTR.
  - Export Jira incident data to **DataDog** for trend analysis.

**Query for MTTR (GraphQL Example):**
```graphql
query IncidentMTTR {
  incidents(
    filter: { status: "Closed", severity: ["P0", "P1"] }
  ) {
    edges {
      node {
        resolutionTime
      }
    }
  }
}
```

---

## **Query Examples**
### **1. Find Unresolved Incidents (CLI)**
```bash
# Using Jira REST API
curl -X GET \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  "https://your-domain.atlassian.net/rest/api/3/search?jql=status!=Closed&maxResults=100"
```

### **2. Export Post-Mortems to CSV (Python)**
```python
import requests

# Fetch post-mortem data from API
response = requests.get(
    "https://api.yourcompany.com/incidents?status=closed&include=post_mortem"
)
incidents = response.json()["data"]

import csv
with open("post_mortems.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Incident", "Root Cause", "Fix"])
    for incident in incidents:
        writer.writerow([incident["id"], incident["post_mortem"]["root_cause"], incident["post_mortem"]["short_term_fixes"]])
```

### **3. Slack Alert for High-Severity Incidents (Webhook)**
```json
{
  "text": ":rotating_light: **INCIDENT ALERT** :rotating_light:\n\n*Title*: {{incident.title}}\n*Severity*: {{incident.severity}}\n*Status*: {{incident.status}}\n*Assigned To*: {{incident.assigned_to}}\n\n[View in Jira]({{incident.link}})",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Escalation Required*\nIf unresolved in 15 mins, ping @engineering-manager."
      }
    }
  ]
}
```

---

## **Automation Scenarios**
| **Scenario**                          | **Tool**               | **Automation Example**                                                                 |
|----------------------------------------|------------------------|---------------------------------------------------------------------------------------|
| Auto-assign incidents to on-call team | **PagerDuty + Jira**   | Trigger Jira automation when PagerDuty on-call user changes.                          |
| Rollback deployments on failure        | **GitLab CI**          | Use `job:rollback` template if pipeline fails post-deployment.                          |
| Escalate to vendor if unresponsive    | **Slack + Zapier**     | Zapier webhook to Slack: `@channel If vendor (e.g., AWS) response > 60 mins, notify.` |
| Generate post-mortem drafts            | **GitHub Actions**     | Run a script to extract logs and auto-fill Confluence template on incident closure.    |

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **[Observability Stack]**             | Centralized logging, metrics, and tracing (e.g., ELK + OpenTelemetry).                                                                                                                                     | When you need to **debug incidents** at scale.                                    |
| **[Chaos Engineering]**               | Deliberately inject failures to test resilience (e.g., Gremlin, Chaos Monkey).                                                                                                                        | To **proactively identify single points of failure**.                             |
| **[Blameless Post-Mortems]**          | Focus on **systems and processes**, not individuals, to encourage psychological safety.                                                                                                               | After **high-impact incidents** to drive culture change.                          |
| **[SRE Metrics]**                     | Define SLIs, SLOs, and error budgets for service reliability.                                                                                                                                        | To **quantify reliability goals** and set service targets.                          |
| **[Incident Playbooks]**              | Pre-built runbooks for common issues (e.g., "Database Crash", "API Gateway Failure").                                                                                                                  | To **standardize responses** to frequent incidents.                               |
| **[Incident Communication Plan]**     | Structured messaging (e.g., RFC 8572) for internal/external updates.                                                                                                                                   | To **keep stakeholders informed transparently**.                                 |

---

## **Tools & Integrations**
| **Category**          | **Tools**                                                                                     | **Key Features**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Ticketing**         | Jira Service Management, Zendesk, Freshservice                                                     | Workflow automation, SLAs, and post-incident analysis.                                             |
| **Alerting**          | PagerDuty, Opsgenie, Alertmanager (Prometheus)                                                  | On-call scheduling, escalation policies, and multi-channel alerts (email/SMS).                     |
| **Monitoring**        | Datadog, New Relic, Prometheus + Grafana                                                         | Custom dashboards, anomaly detection, and alerting thresholds.                                       |
| **Logging**           | ELK Stack (Elasticsearch, Logstash, Kibana), Loki (Grafana)                                       | Centralized logs, correlation IDs, and search capabilities.                                        |
| **Infrastructure**    | Terraform, Ansible, Kubernetes (with Prometheus Operators)                                      | Automate incident recovery (e.g., self-healing clusters).                                           |
| **Collaboration**     | Slack, Microsoft Teams, Confluence (for post-mortems)                                           | Real-time communication and historical documentation.                                              |
| **Chaos Testing**     | Gremlin, Chaos Mesh, LitmusChaos                                                               | Proactively test failure scenarios.                                                               |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                                                                                      |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Overloading on-call teams**        | Implement **on-call rotation** with clear escalation paths and limit P0/P1 incidents to 1–2 concurrent.                                               |
| **Lack of post-mortem discipline**    | Enforce **24-hour deadlines** for post-mortems via tooling (e.g., Jira due dates).                                                          |
| **Ignoring low-severity incidents**  | Treat **P2/P3 incidents** as learning opportunities via **retrospective meetings**.                                                                      |
| **Alert fatigue**                    | Use **alert clustering** (e.g., suppress 5xx errors for 5 mins if they spike) and **adaptive thresholds**.                                          |
| **Long MTTR due to manual steps**    | **Automate runbooks** where possible (e.g., Kubernetes rollbacks).                                                                                          |
| **Poor documentation**               | Maintain a **shared wiki** (Confluence/Notion) with incident templates, runbooks, and contact lists.                                                |

---

## **Example Workflow: Database Crash**
1. **Detection** (08:45 AM):
   - **Alert**: Prometheus alerts on `redis_memory_used > 90%`.
   - **Channel**: Slack `@engineering-alerts` + PagerDuty page to on-call SRE.
