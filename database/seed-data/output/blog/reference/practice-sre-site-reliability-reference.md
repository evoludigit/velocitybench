# **[Pattern] Site Reliability Engineering (SRE) Practices – Reference Guide**

---

## **Overview**
Site Reliability Engineering (SRE) is a discipline that combines aspects of software engineering and IT operations to ensure scalable, reliable, and efficient systems. This pattern outlines best practices for **SRE site reliability**, covering key principles, metrics, incident response, and operational automation. The guide focuses on **resilience, observability, and measurable reliability goals**—key tenets of SRE—to minimize downtime and improve system stability.

SRE Practices are rooted in **Google’s Site Reliability Engineering (SRE) book** and adapted for cloud-native, microservices, and DevOps environments. Core goals include balancing reliability with scalability while reducing manual intervention. This guide provides actionable strategies for defining **Service Level Objectives (SLOs)**, **Error Budgets**, and **Blameless Postmortems** to build robust, self-healing systems.

---

## **Schema Reference**
Below are key components of SRE Practices, structured as a reference schema for implementation:

| **Component**               | **Description**                                                                                                                           | **Key Attributes**                                                                                                                                                     | **Example Format/Tool**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Service Level Objectives (SLOs)** | Defines expected availability (e.g., "99.9%" uptime) for a service. Serves as the reliability target.                         | - **Target:** % availability (e.g., 99.99%)<br>- **Baseline:** Current availability<br>- **Error Budget:** Tolerable downtime (%)<br>- **Measurement Window:** Timeframe (e.g., monthly) | `SLO: 99.95% availability for `/api/v1` over 30-day rolling window.` |
| **Error Budget**            | Quantifies allowed failures within an SLO (e.g., 0.05% of time can be "downtime"). Balances reliability with innovation.          | - **Exhausted?** (Bool)<br>- **Remaining:** % remaining budget<br>- **Rollback Threshold:** % trigger rollback<br>- **Notification Triggers:** Alerts at X% exhaustion | Alert: `"Error budget exhausted: 0/0% remaining for `auth-service`."`                                     |
| **Postmortem**              | Structured analysis of incidents to identify root causes and prevent recurrence. Adheres to **blameless culture**.               | - **Incident Description:** What happened?<br>- **Timeline:** Event sequence<br>- **Root Cause:** Technical + systemic<br>- **Corrective Actions:** Fixes/Process Changes<br>- **Ownership:** Team accountable for follow-ups | Template: [Google’s Postmortem Guide](https://cloud.google.com/blog/products/devops-sre/running-effective-postmortems) |
| **Observability Stack**     | Tools for monitoring, logging, and tracing to detect issues proactively.                                                           | - **Metrics:** Latency, error rates, throughput<br>- **Logs:** Structured + unstructured data<br>- **Traces:** Request flow analysis<br>- **Alerts:** Anomaly detection | Stack: **Prometheus (metrics) + Loki (logs) + Jaeger (traces) + Alertmanager**                          |
| **Automated Incident Response** | Playbooks or scripts to remediate incidents without manual intervention (e.g., auto-restart failed pods).                     | - **Detection Rule:** Trigger condition (e.g., `HTTP 5xx > 1%`)<br>- **Remediation Steps:** Sequence of actions<br>- **Fallback:** Manual override<br>- **Rollback:** Revert to stable state | Example: `Kubernetes Horizontal Pod Autoscaler (HPA) + Chaos Mesh for chaos engineering.`                 |
| **Chaos Engineering**       | Proactively testing system resilience by injecting failures (e.g., killing pods, network latency).                                | - **Scenarios:** Failure modes (e.g., `pod deletion`, `disk failure`)<br>- **Risk Assessment:** Impact analysis<br>- **Consent:** Run in non-production first | Tools: **Chaos Mesh, Gremlin, Netflix Simian Army**                                                        |
| **On-Call Rotation**        | Structured scheduling to distribute incident response duty and ensure coverage.                                                    | - **Rotation Schedule:** Frequency (e.g., 4-hour shifts)<br>- **Escalation Path:** Tiered ownership<br>- **Slack/Opsgenie Integration:** Alert routing | Example: **PagerDuty + OnCall rotation policy**                                                          |
| **Degradation Strategies**  | Graceful handling of failures (e.g., circuit breakers, rate limiting, fallback services).                                        | - **Circuit Breaker:** Trip threshold<br>- **Retry Policy:** Exponential backoff<br>- **Fallback:** Static response/page<br>- **Caching:** Reduce load | Implementations: **Hystrix (Netflix), Resilience4j**                                                     |
| **Capacity Planning**       | Forecasting resource needs to avoid bottlenecks (e.g., scaling pods, database sharding).                                        | - **Trend Analysis:** Historical usage<br>- **Growth Projections:** User/metric-based<br>- **Autoscaling:** Horizontal/vertical<br>- **Reserve Capacity:** Buffer | Tools: **Datadog Capacity Planning, GKE Cluster Autoscaler**                                              |
| **Documentation Standards** | Centralized, up-to-date runbooks, architecture diagrams, and SLO definitions for all services.                               | - **Runbooks:** Step-by-step troubleshooting<br>- **Architecture Diagrams:** Service dependencies<br>- **SLO Definitions:** Publicly accessible<br>- **Ownership:** Team maintenance | **Confluence + Notion + Diagrams.net**                                                                     |

---

## **Query Examples**

### **1. Checking SLO Health**
**Context:** Verify if a service’s error budget is at risk.
**Query (PromQL):**
```promql
# Check if error budget is exhausted (99.9% SLO, 0.1% error budget)
rate(http_requests_total{status=~"5.."}[1h]) * 100 * 24 * 30 > 0.1
```
**Expected Output:**
```
false  # Error budget not exhausted (0.08% used)
```
**Action:** If `true`, trigger an alert (e.g., Slack message).

---

### **2. Detecting Degraded Performance (Latency Spikes)**
**Context:** Alert on API latency exceeding thresholds.
**Query (Grafana Dashboard Alert):**
```promql
# Average latency > 500ms for `/api/auth`
avg_over_time(http_request_duration_seconds{path="/api/auth"}[5m]) > 0.5
```
**Conditions:**
- **Firing:** Latency > 500ms for 5 consecutive minutes.
- **Resolution:** Latency < 300ms for 15 minutes.
**Tools:** Integrate with **PagerDuty** or **Opsgenie**.

---

### **3. Pod Failure Detection (Kubernetes)**
**Context:** Automatically restart failed pods in a deployment.
**Kubernetes CRD (Chaos Mesh):**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure-test
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-service
  duration: "10s"
  schedule: "*/5 * * * *"  # Every 5 minutes
```
**Remediation Script (Python + K8s API):**
```python
from kubernetes import client, config
config.load_kube_config()

v1 = client.CoreV1Api()
pods = v1.list_namespaced_pod(namespace="default", label_selector="app=my-service")
for pod in pods.items:
    if pod.status.phase == "Pending":
        v1.replace_namespaced_pod_status(pod.metadata.name, pod.metadata.namespace, body=pod)
```

---

### **4. Postmortem Root Cause Analysis (RCA)**
**Template Query for Logs (ELK):**
```kibana
# Filter logs for "Critical" errors during outage (timestamp: 2023-10-01T00:00:00 to 2023-10-01T01:00:00)
service:auth-service AND level:ERROR AND message:"Critical"
```
**Key Fields to Extract:**
- `timestamp`, `service`, `error_code`, `user_id` (if applicable), `stack_trace`.
**Tools:** **ELK Stack, Datadog, Splunk**.

---

### **5. Error Budget Exhaustion Alert (SLO Tracking)**
**Script (Python + Prometheus API):**
```python
import requests
import prometheus_api_client

prom = prometheus_api_client.PrometheusConnect(
    url="http://prometheus-server:9090",
    disable_ssl=True
)

# Fetch current error budget usage for `serviceA`
result = prom.custom_query(
    "rate(http_errors_total[5m]) * 100 / (99.99 * 24 * 30)"
)
budget_used = result[0].value[1]  # Percentage used

if budget_used >= 99.9:  # Exhausted
    print("ALERT: Error budget exhausted for serviceA!")
    # Trigger Slack notification
    requests.post(
        "https://hooks.slack.com/services/XXX",
        json={"text": "SLO Alert: serviceA error budget exhausted"}
    )
```

---

## **Related Patterns**
To complement **SRE Site Reliability Practices**, consider integrating or referencing these patterns:

| **Pattern**                          | **Description**                                                                                                                                 | **Connection to SRE**                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **[Observability Stack](link)**       | Centralized monitoring, logging, and tracing for real-time issue detection.                                                          | **Core to SRE:** Observability enables proactive reliability monitoring and incident detection.           |
| **[Chaos Engineering](link)**         | Deliberately injecting failures to test resilience.                                                                                     | **Complements SRE:** Validates reliability assumptions and error budgets in a controlled manner.          |
| **[Site Reliability Metrics](link)** | Defining metrics like **Mean Time to Detect (MTTD)** and **Mean Time to Resolve (MTTR)**.                                             | **Critical for SLOs:** Quantifies reliability and informs error budget calculations.                        |
| **[Incident Management](link)**      | Structured response to incidents with runbooks and postmortems.                                                                          | **Essential for SRE:** Blameless postmortems and error budget tracking are foundational to continuous improvement. |
| **[Automated Remediation](link)**     | Self-healing systems via scripts/playbooks (e.g., auto-scaling, rollbacks).                                                       | **Key to SRE:** Reduces manual intervention and aligns with the "reliability via automation" principle.   |
| **[Capacity Planning](link)**         | Scaling infrastructure based on demand to avoid bottlenecks.                                                                          | **Linked to SLOs:** Prevents degradation from resource constraints, preserving error budgets.              |
| **[Blameless Culture](link)**         | Encouraging psychological safety to improve incident reporting.                                                                        | **Cultural Pillar:** Enables honest postmortems and systemic fix prioritization.                         |
| **[GitOps](link)**                    | Managing infrastructure as code (IaC) via Git for auditability and rollback capability.                                               | **Supports SRE:** Facilitates quick, safe rollbacks during incidents.                                      |

---

## **Key Takeaways**
1. **Define SLOs Early:** Align SLOs with business needs and track error budgets religiously.
2. **Automate Everything:** From incident detection to remediation, reduce human error.
3. **Embrace Failure:** Use chaos engineering to proactively test resilience.
4. **Document Postmortems:** Blameless analysis leads to systemic improvements.
5. **Observability First:** Without logs/metrics/traces, you’re flying blind.
6. **Rotate On-Call Fairly:** Sustainable reliability requires balanced workload distribution.

---
**Further Reading:**
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Kubernetes SRE Practices](https://kubernetes.io/docs/concepts/sre/)
- [Chaos Engineering Research](https://www.netflix.com/blog/post/chaos-engineering)