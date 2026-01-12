---
# **[Pattern] Audit Profiling – Reference Guide**

---

## **Overview**
**Audit Profiling** is a design pattern that systematically collects, analyzes, and categorizes usage patterns, anomalies, and behavioral insights from user interactions, system logs, or API calls. By profiling audit data over time, organizations can detect suspicious activity, enforce compliance, and optimize security policies dynamically.

This pattern is ideal for:
- **Security monitoring** (fraud detection, breach prevention)
- **Access control adaptation** (real-time policy adjustments)
- **Compliance auditing** (GDPR, HIPAA, SOC2)
- **Performance tuning** (identifying inefficient or risky workflows)

Unlike traditional static auditing, **Audit Profiling** enables contextual risk assessment by examining *patterns* (e.g., "Users in Region X never access this feature at night") rather than isolated events.

---

## **Key Concepts**

### **Core Components**
| **Component**          | **Definition**                                                                                     | **Example Use Case**                          |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Audit Stream**       | Continuous flow of raw events (logs, API calls, user actions) from monitored systems.              | REST API request logs from a microservice.    |
| **Profile**            | A structured aggregation of audit events (e.g., "High-risk logins," "Unusual data exports").      | "3 failed logins in 5 minutes → Lock account."|
| **Profile Rules**      | Thresholds or conditions defining what constitutes a "profile" (e.g., "Repeat 404 errors in 1 hour"). | Detect brute-force attacks.                   |
| **Profile Engine**     | Algorithm that processes streams, applies rules, and generates profiles (e.g., ML-based clustering). | Flag abnormal transaction sequences.          |
| **Action Triggers**    | Automated responses to profiles (e.g., alerts, policy changes, user locks).                      | Escalate to SOC team on "Data leakage" profile.|
| **Storage Backend**    | Database or system storing profiles for historical analysis (e.g., time-series DB like InfluxDB).  | Query profiles over 30 days for forensics.    |

---

## **Schema Reference**
Below is the standard schema for **Audit Profiling** data models. Adjust fields as needed for your environment.

### **1. Audit Event Schema**
| **Field**            | **Type**       | **Description**                                                                 | **Example Value**               |
|----------------------|---------------|---------------------------------------------------------------------------------|---------------------------------|
| `event_id`           | String (UUID) | Unique identifier for the event.                                                 | `a1b2c3d4-e5f6-7890-g1h2-34i5j6`|
| `timestamp`          | ISO 8601      | When the event occurred.                                                         | `2023-10-15T14:30:00Z`          |
| `user_id`            | String        | Identifier of the user/actor (if applicable).                                   | `user_4567`                     |
| `system_id`          | String        | Source system generating the event (e.g., `auth-service-v1`).                     | `auth-service-v1`               |
| `action`             | Enum          | Type of action (e.g., `LOGIN`, `DATA_EXPORT`, `API_CALL`).                       | `DATA_EXPORT`                    |
| `resource`           | String        | Target of the action (e.g., `customer_db`, `user_profile_123`).                  | `customer_db`                    |
| `metadata`           | JSON          | Free-form data (IP, success/failure, payload size, etc.).                       | `{"ip": "192.0.2.1", "status": "ERROR"}` |
| `severity`           | Enum          | Predefined risk level (e.g., `INFO`, `WARNING`, `CRITICAL`).                     | `WARNING`                       |

---

### **2. Profile Schema**
| **Field**            | **Type**       | **Description**                                                                 | **Example Value**               |
|----------------------|---------------|---------------------------------------------------------------------------------|---------------------------------|
| `profile_id`         | String (UUID) | Unique identifier for the profile.                                               | `profile_7890`                  |
| `name`               | String        | Human-readable profile name (e.g., `"Unusual Hourly Logins"`).                  | `Unusual Hourly Logins`         |
| `definition`         | JSON          | Rule(s) defining the profile (e.g., `{ "event_type": "LOGIN", "threshold": 5 }`). | `{"event_type": "LOGIN", "time_window": "1h", "threshold": 5}` |
| `first_detected`     | ISO 8601      | When the profile was first triggered.                                           | `2023-10-15T14:31:00Z`          |
| `last_detected`      | ISO 8601      | Most recent trigger time.                                                        | `2023-10-15T14:35:00Z`          |
| `events`             | Array[Event]  | List of audit events contributing to this profile.                               | `[{event_id: "a1b...", ...}]`   |
| `status`             | Enum          | Profile lifecycle (e.g., `ACTIVE`, `RESOLVED`, `RECURRENT`).                     | `ACTIVE`                        |
| `actions_taken`      | Array[String] | List of automated responses (e.g., `["ALERT_SOC", "LOCK_ACCOUNT"]`).           | `["ALERT_SOC"]`                 |
| `metadata`           | JSON          | Additional context (e.g., affected systems, user roles).                         | `{"affected_db": "payments_db"}`|

---

### **3. Profile Rule Schema**
| **Field**            | **Type**       | **Description**                                                                 | **Example**                     |
|----------------------|---------------|---------------------------------------------------------------------------------|---------------------------------|
| `rule_id`            | String        | Unique identifier for the rule.                                                  | `rule_login_frequency`          |
| `event_type`         | String        | Filter by audit event type (e.g., `LOGIN`).                                      | `LOGIN`                         |
| `threshold`          | Integer       | Number of events to trigger the profile (e.g., 5 logins).                       | `5`                             |
| `time_window`        | Duration      | Time span for counting events (e.g., `1h`, `24h`).                               | `1h`                            |
| `severity`           | Enum          | Rule-specific severity (e.g., `MEDIUM`, `HIGH`).                                | `HIGH`                          |
| `conditions`         | JSON          | Optional filters (e.g., `{ "user_role": "ADMIN" }`).                             | `{"user_role": "ADMIN"}`        |

---

## **Implementation Steps**
### **1. Ingest Audit Data**
- **Sources:** Logs (ELK, Splunk), APIs, database triggers, or SIEM tools (e.g., Splunk, Datadog).
- **Format:** Stream events in real-time (e.g., Kafka, AWS Kinesis) or batch-process logs.
- **Tools:** Apache Flume, Logstash, or custom scripts.

**Example Ingestion Pipeline:**
```plaintext
[Database Trigger] → [Kafka Topic: `audit-events`] → [Profile Engine]
```

---

### **2. Define Profiles and Rules**
- **Static Rules:** Hardcoded thresholds (e.g., "Block >3 failed logins in 10 mins").
- **Dynamic Rules:** Use machine learning to adjust thresholds over time (e.g., "Detect 2 standard deviations from normal login times").

**Example Rule (YAML):**
```yaml
profile: "Brute Force Attempt"
rule_id: "too_many_failed_logins"
event_type: "LOGIN"
threshold: 3
time_window: "10m"
conditions:
  result: "FAILED"
```

---

### **3. Process and Store Profiles**
- **Engine Options:**
  - **Rule-Based:** Use tools like [Prometheus Alertmanager](https://prometheus.io/docs/alerting/alertmanager/) or custom scripts (Python, Go).
  - **ML-Based:** Libraries like [Scikit-learn](https://scikit-learn.org/) for anomaly detection.
- **Storage:** Time-series databases (InfluxDB) or document stores (MongoDB, Elasticsearch).

**Pseudocode for Rule Engine:**
```python
from datetime import datetime, timedelta

def check_profile(events, rule):
    window_start = datetime.now() - timedelta(minutes=rule["time_window"])
    rule_events = [
        e for e in events
        if e["timestamp"] >= window_start
        and e["action"] == rule["event_type"]
        and e["metadata"]["result"] == rule.get("result", "SUCCESS")
    ]
    return len(rule_events) >= rule["threshold"]
```

---

### **4. Trigger Actions**
- **Automated Responses:**
  - Alerts (Slack, PagerDuty, Email).
  - Policy changes (e.g., temporarily disable a user’s API keys).
  - Forensic investigations (flag events for review).
- **Tools:** SIEM correlation (Splunk, Wazuh), orchestration (Ansible, Terraform).

**Example Action (Terraform):**
```hcl
resource "aws_iam_user_policy_attachment" "restrict_user" {
  user       = "user_${var.user_id}"
  policy_arn = "arn:aws:iam::aws:policy/AWSSupportAccess"
  count      = var.profile == "DATA_LEAK_RISK" ? 1 : 0
}
```

---

### **5. Monitor and Iterate**
- **Dashboarding:** Visualize profiles with Grafana or Kibana.
- **Feedback Loop:** Adjust rules based on false positives/negatives (e.g., "Reduce threshold for `DATA_EXPORT` if most are legitimate").
- **Compliance Reporting:** Export profiles to meet audit requirements (e.g., CSV for SOC2 evidence).

---

## **Query Examples**
### **1. Find Active High-Risk Profiles**
```sql
-- SQL (PostgreSQL)
SELECT profile_id, name, COUNT(*) as event_count
FROM profiles
WHERE status = 'ACTIVE'
  AND severity = 'HIGH'
GROUP BY profile_id, name;
```

**Output:**
```
profile_id    | name                  | event_count
--------------+----------------------+------------
profile_7890  | Brute Force Attempt  | 12
profile_1234  | Data Leak Risk       | 5
```

---

### **2. List Events for a Profile**
```python
# Python (using PyMongo)
db.profiles.find_one({"profile_id": "profile_7890"})
# Output:
{
  "events": [
    {"event_id": "a1b2...", "timestamp": "2023-10-15T14:31:00Z", "action": "LOGIN"},
    {"event_id": "b2c3...", "timestamp": "2023-10-15T14:32:00Z", "action": "LOGIN"}
  ]
}
```

---

### **3. Detect Anomalies with ML (Python Example)**
```python
from sklearn.ensemble import IsolationForest

# Load historical data (e.g., login times)
X = [[event["metadata"]["login_time"]] for event in audit_events]

# Train model
model = IsolationForest(contamination=0.01)
model.fit(X)

# Predict anomalies
anomalies = model.predict(X)
print("Anomalous logins:", anomalies[anomalies == -1])
```

---

## **Performance Considerations**
| **Aspect**            | **Recommendation**                                                                 |
|-----------------------|-----------------------------------------------------------------------------------|
| **Real-Time Processing** | Use streaming (Kafka + Flink) for low-latency profiling.                          |
| **Rule Complexity**   | Start with simple rules; add ML later if needed.                                   |
| **Storage Scalability** | Partition profiles by time (e.g., monthly folders in S3).                          |
| **False Positives**   | Implement "whitelisting" for known benign patterns.                              |
| **Cost**              | Avoid over-collecting; sample logs if monitoring large-scale systems.             |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use Together**                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **[SIEM Integration](https://example.com/siem)** | Combine Audit Profiling with Security Information and Event Management.     | For centralized threat detection.                |
| **[Rate Limiting](https://example.com/rate-limiting)** | Use profiles to dynamically adjust rate limits (e.g., block IPs after 3 failures). | Prevent DDoS attacks.                             |
| **[Context-Aware Auth](https://example.com/auth-context)** | Augment MFA with profile data (e.g., require SMS for "Unusual Location" profiles). | Enhance user experience while improving security. |
| **[Compliance Monitoring](https://example.com/compliance)** | Export profile data to compliance reports (e.g., GDPR Article 30).           | Meet regulatory requirements.                    |
| **[Behavioral Analytics](https://example.com/behavioral)** | Use ML to detect subtle patterns (e.g., insider threats).                   | For advanced fraud detection.                    |

---

## **Example Architecture**
```plaintext
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Database   │    │    API      │    │  Audit Stream   │    │  Profile    │
│  (Source)   ├─▶▶│  Gateway    ├─▶▶│  (Kafka/ELK)    ├─▶▶│  Engine      │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
                                           ▲                  ▲
                                           │                  │
                                  ┌───────┴───────┐    ┌───────┴───────┐
                                  │    Rules     │    │   Storage    │
                                  │  Database    │    │ (InfluxDB/    │
                                  └──────────────┘    │  MongoDB)     │
                                                        └──────────────┘
```

---

## **Troubleshooting**
| **Issue**                     | **Diagnosis**                          | **Solution**                                  |
|--------------------------------|----------------------------------------|-----------------------------------------------|
| High false positives           | Rules too broad (e.g., low threshold). | Tighten conditions or use ML to learn normal behavior. |
| Profile engine slow            | Complex rules or large datasets.       | Optimize queries; consider sampling.           |
| Data missing from profiles     | Ingestion pipeline failure.             | Check Kafka/S3 logs; validate schema.         |
| Alert fatigue                  | Too many low-severity profiles.        | Prioritize profiles by impact.                |

---

## **Further Reading**
- [CIS Controls v8: Audit Logging and Monitoring](https://www.cisecurity.org/controls/)
- [NIST SP 800-53: Audit and Accountability](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [Prometheus Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)