---
**[Pattern] Availability Profiling Reference Guide**

---

### **1. Overview**
**Availability Profiling** is a reliability pattern for predicting and optimizing system uptime by analyzing historical availability data, workload patterns, and external factors (e.g., traffic spikes, geographic events). By creating **profiles** (e.g., "High-Traffic Peak Hours," "Geopolitical Outages"), teams can proactively allocate resources, test failover mechanisms, and reduce unplanned downtime. This pattern is critical for **SLO-driven systems**, multi-region deployments, and cost-sensitive cloud architectures.

**Core Goal:** *Minimize planned/unplanned outages via data-informed availability planning.*
**Use Cases:**
- Predictive capacity scaling (e.g., Kubernetes HPA tuning).
- Failover testing (e.g., chaos engineering with synthetic traffic).
- Disaster recovery (DR) scenario simulation.
- Cost optimization (e.g., pausing non-critical regions during predicted downtimes).

---

### **2. Schema Reference**

| **Component**          | **Description**                                                                 | **Fields**                                                                                                                                 |
|------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **Availability Profile** | A named configuration defining expected availability characteristics.           | `id` (str), `name` (str), `description` (str), `start_time` (datetime), `end_time` (datetime), `timezone` (str), `reliability_sla` (float 0–1) |
| **Profile Rule**       | Conditions/triggers for profiling events (e.g., "if regional outage > 5min"). | `profile_id` (ref), `event_type` (str: "traffic_spike", "outage", "maintenance"), `threshold` (float), `metric` (str: "latency", "error_rate"), `action` (str: "scale_up", "failover") |
| **Historical Event**   | Past availability incidents used for profiling.                                 | `id` (str), `profile_id` (ref), `timestamp` (datetime), `duration` (timedelta), `severity` (str: "minor", "major"), `root_cause` (str)        |
| **Predictive Model**   | ML-based forecasts (optional).                                                  | `profile_id` (ref), `model_type` (str: "time_series", "anomaly_detection"), `accuracy` (float), `last_updated` (datetime)                     |

**Example Profile:**
```json
{
  "id": "prod-traffic-peak",
  "name": "Production Traffic Peak (US)",
  "start_time": "2024-01-01T08:00:00",
  "end_time": "2024-01-01T20:00:00",
  "timezone": "America/New_York",
  "rules": [
    {
      "event_type": "traffic_spike",
      "threshold": 1.5,
      "metric": "requests_per_sec",
      "action": "scale_up_by 50%"
    }
  ]
}
```

---

### **3. Implementation Details**

#### **3.1 Key Concepts**
- **Signal Sources:**
  - **Observability Data:** APM (e.g., OpenTelemetry), monitoring (e.g., Prometheus), logs (e.g., ELK).
  - **External APIs:** Weather forecasts (for outage risks), DDoS threat feeds.
  - **Human Input:** Scheduled maintenance windows (e.g., CI/CD pipelines).

- **Profile Lifecycle:**
  1. **Discovery:** Collect historical events (e.g., "Region A had 3/5 major outages in Q1").
  2. **Definition:** Define rules (e.g., "If `error_rate > 0.1` for 30s, trigger failover").
  3. **Validation:** Test profiles via synthetic traffic (e.g., Locust/Chaos Mesh).
  4. **Execution:** Automate actions (e.g., Terraform cloud region swaps).

- **Tooling Integration:**
  - **Observability:** Correlate profiles with metrics (e.g., `rate(http_errors_total{status=5xx}) > 0`).
  - **Orchestration:** Annotate Kubernetes pods with `availabilityProfile: prod-traffic-peak` for dynamic scaling.
  - **Incident Management:** Link profiles to PagerDuty alerts (e.g., `{"profile": "prod-traffic-peak", "severity": "critical"}`).

#### **3.2 Critical Considerations**
- **False Positives/Negatives:**
  - Use **confidence thresholds** (e.g., `accuracy > 0.85` for automated actions).
  - Combine multiple signals (e.g., "high traffic + low CPU utilization" suggests a bug, not a spike).
- **Regional Bias:**
  - Profile by **geographic SLOs** (e.g., "Asia-Pacific tier_2 availability = 99.9%").
- **Cost Trade-offs:**
  - Balance over-provisioning (e.g., keeping all regions online during "false positives") vs. under-provisioning (e.g., missing a real outage).

#### **3.3 Example Architecture**
```
[Observability Data]
       ↓ (Prometheus/Grafana)
[Availability Profiles Service]
       ↓ (REST/gRPC)
[Orchestrator] ←→ [Kubernetes/HPC]
       ↓
[SLO Dashboard]
```

---

### **4. Query Examples**

#### **4.1 Query Historical Events (PromQL)**
```promql
# Find outages where duration > 10min
histogram_quantile(0.95, sum by (service) (
  rate(http_request_duration_seconds_bucket[5m])
)) > 600
```
**Output:** Alerts for prolonged latency spikes, flagged for profile refinement.

#### **4.2 Validate Profiles (Terraform)**
```hcl
resource "aws_autoscaling_group" "prod-app" {
  availability_zones = ["us-east-1a", "us-east-1b"]
  tag {
    key                 = "availability_profile"
    value               = "prod-traffic-peak"
    propagate_at_launch = true
  }
}
```
**Result:** ASG scales based on linked profile rules.

#### **4.3 Export Profiles (CLI)**
```bash
# List profiles via custom API
curl -X GET http://localhost:8080/api/profiles \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | select(.name == "prod-traffic-peak")'
```
**Output:**
```json
{
  "id": "prod-traffic-peak",
  "rules": [...],
  "last_updated": "2023-11-15T14:30:00Z"
}
```

---

### **5. Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use Together**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Chaos Engineering**     | Profiles inform targeted chaos experiments (e.g., "Test failover during `prod-traffic-peak`"). | Reduce blind spots in availability assumptions.                                         |
| **Multi-Region Deployment** | Profiles guide region-specific scaling/pausing (e.g., "Pause `eu-west-1` during US peak"). | Optimize cost for global workloads.                                                     |
| **SLO-Driven Design**     | Profiles align with SLOs (e.g., "99.9% availability for `ecommerce` profile").    | Avoid ad-hoc reliability trade-offs.                                                     |
| **Circuit Breaker**       | Profiles trigger circuit breakers (e.g., "Trip breaker if `prod-traffic-peak` fails 3x"). | Prevent cascading failures during known high-load periods.                                 |
| **Canary Deployments**    | Test profiles in canary waves (e.g., "Deploy to 10% traffic first during `dev-traffic-spike`"). | Mitigate risk in profile-driven changes.                                                 |

---
**References:**
- [Google SRE Book: SLIs/SLOs/Error Budgets](https://sre.google/sre-book/)
- [Chaos Engineering: "Antifragile Systems"](https://www.chaosengineering.io/)
- [Kubernetes HPA with Custom Metrics](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#support-for-custom-metrics)