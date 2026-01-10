# **[Pattern] Alerting & On-Call Runbooks Reference Guide**

---

## **Overview**
Effective alerting is critical for maintaining system reliability, but poorly designed alerts only increase on-call fatigue without improving operational efficiency. This **Alerting & On-Call Runbooks** pattern ensures alerts are **actionable, low-noise, and paired with clear runbooks** that guide responders on how to resolve incidents.

This guide covers:
- **Alert design best practices** (clear thresholds, meaningful context, and suppression strategies).
- **Runbook structure** (step-by-step troubleshooting, escalation paths, and post-incident follow-ups).
- **Tooling integration** (connecting alerts to runbooks, automation, and documentation).

By adhering to these principles, teams reduce alert fatigue, shorten mean time to resolution (MTTR), and improve on-call responsiveness.

---

## **Key Concepts**

### **1. Alert Design Principles**
Good alerts follow these rules to minimize noise and maximize relevance:

| **Principle**               | **Description**                                                                                                                                                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Single Responsibility**   | Each alert should monitor **one specific issue** (e.g., "High CPU on pod X," not "System is slow").                                                                                                               |
| **Meaningful Context**     | Include **who/what/where** (e.g., "Pod `web-app-1` on `node-001` exceeded 90% CPU for 5 minutes").                                                                                                           |
| **Adjustable Thresholds**   | Use **dynamic thresholds** (e.g., 95th percentile) instead of static values to account for variability.                                                                                                         |
| **Avoid Alert Storms**      | Implement **alert suppression** (e.g., ignore retries within 10 minutes if the root cause hasn’t changed).                                                                                                    |
| **Severity-Based Escalation** | Align severity (Critical/Warning/Info) with **on-call rotation rules** (e.g., only P1 alerts wake on-call engineers).                                                                                         |
| **Actionable Remediation**  | Every alert should suggest **how to fix it** (e.g., "Scale up pod," "Check disk I/O").                                                                                                                       |
| **Postmortem-Ready**        | Include **temporary vs. permanent fixes** (e.g., "Restart the service vs. upgrade the cluster").                                                                                                                  |

---

### **2. Runbook Structure**
A well-structured runbook reduces cognitive load during incidents. Follow this template:

| **Section**               | **Content**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Title**                 | Clear, concise (e.g., "High Memory Usage in Postgres Cluster").                                                                                                                                            |
| **Trigger Conditions**    | When this alert fires (e.g., "Memory usage > 90% for 15 minutes").                                                                                                                                      |
| **Initial Troubleshooting** | Step-by-step commands/queries (e.g., `kubectl top pods`, `pg_stat_activity`).                                                                                                                              |
| **Root Cause Analysis**   | Likely causes (e.g., query cache miss, disk I/O bottleneck).                                                                                                                                              |
| **Resolutions**           | **Temporary Fix** (e.g., restart pod) + **Permanent Fix** (e.g., optimize queries).                                                                                                                       |
| **Escalation Path**       | Who to call if unresolved (e.g., "Notify SRE after 30 mins").                                                                                                                                             |
| **Post-Incident Actions** | Actions to prevent recurrence (e.g., "Add alert for slow queries > 1s").                                                                                                                                    |
| **Version & Last Updated** | Track changes (e.g., "Updated: 2024-05-15").                                                                                                                                                                |

---

### **3. Tooling Integration**
Automate runbooks and connect them to alerts using:

| **Tool**               | **Use Case**                                                                                                                                                                                           |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Prometheus Alertmanager** | Group/suppress alerts, route to Slack/PagerDuty.                                                                                                                                                  |
| **PagerDuty/Incident**  | Link alerts to runbooks in the incident timeline.                                                                                                                                                     |
| **GitHub/GitLab**      | Store runbooks as markdown in a repo (e.g., `docs/runbooks/alerts/`.                                                                                                                                   |
| **Terraform/Ansible**  | Automate remediation (e.g., scale pods, restart services).                                                                                                                                           |
| **Confluence/Notion**  | Centralize runbooks with searchability.                                                                                                                                                             |

---

## **Schema Reference**
Below is a **reference schema** for organizing alerts and runbooks.

### **1. Alert Schema**
| Field               | Type       | Required | Description                                                                                                                                                     |
|--------------------|------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `id`               | String     | Yes      | Unique alert identifier (e.g., `cpu-high-pod-web-app-1`).                                                                                                  |
| `name`             | String     | Yes      | Human-readable alert name (e.g., "High CPU on `web-app-1`").                                                                                             |
| `severity`         | Enum       | Yes      | `critical`/`warning`/`info` (maps to on-call escalation).                                                                                                |
| `metric`           | String     | Yes      | Metric being monitored (e.g., `container_cpu_usage_seconds_total`).                                                                                     |
| `threshold`        | Object     | Yes      | `{ value: 90, duration: "5m", operator: "gt" }`.                                                                                                     |
| `suppression`      | Object     | No       | `{ retry: "10m", silence: { start: "2024-05-20T12:00", end: "2024-05-20T14:00" }`.                                                                   |
| `context`          | String     | Yes      | Extra details (e.g., `pod: web-app-1, node: node-001`).                                                                                                  |
| `runbook_url`      | URL        | Yes      | Link to the corresponding runbook (e.g., `https://docs.example.com/runbooks/alerts/cpu-high`).                                                         |
| `automation`       | String     | No       | Ansible/Terraform playbook for remediation (e.g., `restart_pod.yml`).                                                                                   |

---

### **2. Runbook Schema**
| Field               | Type       | Required | Description                                                                                                                                                     |
|--------------------|------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `id`               | String     | Yes      | Unique runbook ID (e.g., `runbook-cpu-high-pod-web-app-1`).                                                                                                 |
| `alert_id`         | String     | Yes      | Links to the alert schema (e.g., `cpu-high-pod-web-app-1`).                                                                                               |
| `title`            | String     | Yes      | Human-readable title.                                                                                                                                     |
| `steps`            | Array      | Yes      | Array of troubleshooting steps (see below).                                                                                                              |
| `escalation`       | Object     | No       | `{ contact: "sre-team", timeout: "30m" }`.                                                                                                               |
| `last_updated`     | Date       | Yes      | When the runbook was last reviewed.                                                                                                                     |
| `version`          | String     | Yes      | Version number (e.g., `v1.2`).                                                                                                                             |

#### **Step Schema (inside `steps` array)**
| Field          | Type    | Required | Description                                                                                     |
|----------------|---------|----------|-------------------------------------------------------------------------------------------------|
| `description`  | String  | Yes      | What the step accomplishes (e.g., "Check disk I/O usage").     |
| `command`      | String  | No       | CLI command (e.g., `kubectl top pod`).                              |
| `query`        | String  | No       | SQL/PromQL query (e.g., `SELECT * FROM pg_stat_activity WHERE state = 'active';`).        |
| `expected_out` | String  | No       | Expected output pattern (regex).                                  |
| `remediation`  | Object  | No       | `{ temp_fix: "restart pod", perm_fix: "upgrade disk" }`.       |

---

## **Query Examples**
### **1. PromQL Alert Rule**
```promql
# Alert when CPU usage exceeds 90% for 5 minutes
alert HighCPUUsage
  IF (sum(container_cpu_usage_seconds_total{namespace="prod", pod=~"web-app-.*"}) by (pod) > 90 * 1000000000 * 0.9 * 5 * 60)
    FOR 5m
    LABELS {severity="critical"}
    ANNOTATIONS {
      runbook_url="https://docs.example.com/runbooks/alerts/cpu-high",
      context="pod={{ $labels.pod }}"
    }
```

### **2. Kubernetes Horizontal Pod Autoscaler (HPA) Configuration**
```yaml
# Auto-scale pods if CPU exceeds 80% for 10 minutes
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```

### **3. Ansible Playbook for Remediation**
```yaml
# Restart a pod if CPU is high (used in `automation` field of alert schema)
---
- name: Restart high-CPU pod
  hosts: localhost
  tasks:
    - name: Get pod name
      command: kubectl get pods -l app=web-app --field-selector=status.containerStatuses[].restartCount>1 -o jsonpath='{.items[0].metadata.name}'
      register: pod_name

    - name: Delete pod to restart it
      command: kubectl delete pod {{ pod_name.stdout }}
```

---

## **Related Patterns**
To complement **Alerting & On-Call Runbooks**, consider these patterns:

| **Pattern**                          | **Description**                                                                                                                                                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Scheduled Maintenance](#)**      | Plan outages to avoid alert storms during known downtimes (e.g., "Ignore alerts during DB backups").                                                                                                        |
| **[Postmortem Template](#)**        | Standardize incident retrospectives with clear action items.                                                                                                                                              |
| **[Observability Stack](#)**        | Combine metrics (Prometheus), logs (Loki/ELK), and traces (Jaeger) for deeper debugging.                                                                                                                   |
| **[On-Call Rotation](#)**            | Define fair escalation policies to avoid alert fatigue.                                                                                                                                                  |
| **[Chaos Engineering](#)**           | Proactively test alerting systems with controlled failures.                                                                                                                                               |

---

## **Next Steps**
1. **Audit existing alerts**: Remove redundant or noisy alerts.
2. **Create runbooks**: Start with high-severity alerts first.
3. **Automate remediation**: Use GitOps (Terraform/Ansible) to reduce manual work.
4. **Review postmortems**: Update runbooks based on incident learnings.

---
**Feedback?** Report issues or suggest improvements in the [GitHub repo](https://github.com/example/patterns).