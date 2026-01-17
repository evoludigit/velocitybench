# **[Capacity Planning Patterns] Reference Guide**

---

## **1. Overview**
Capacity planning patterns provide structured approaches to forecast, monitor, and manage system resources (e.g., CPU, memory, storage, network) to ensure optimal performance, reliability, and cost efficiency. These patterns address common challenges like scaling misalignment, unpredictable workloads, and resource under/over-provisioning. They apply across cloud, on-premises, and hybrid environments, supporting both reactive (ad-hoc adjustments) and proactive (predictive optimization) strategies.

Key benefits include:
- **Cost reduction** via right-sizing and auto-scaling.
- **Performance stability** through real-time and forecasted demand analysis.
- **Flexibility** for burst capacity, seasonal spikes, and long-term growth.

Patterns cover:
✅ **Load Modeling** – Quantifying demand patterns.
✅ **Reserve Management** – Static and dynamic allocation strategies.
✅ **Scaling Strategies** – Horizontal/vertical scaling rules.
✅ **Monitoring & Alerting** – Metrics-driven adjustments.
✅ **Cost Optimization** – Right-sizing and cost-efficient scaling.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                                                                                     | **Example Attributes**                                                                                         |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Workload Profile**        | Classifies application behavior (e.g., steady-state, bursty, seasonal) to inform planning.                                                                    | - Pattern Type (e.g., "Seasonal," "Bursty")<br>- Peak-to-Average Ratio<br>- Predictability Score (0–100)     |
| **Resource Allocation**     | Defines static/dynamic allocation rules for compute, storage, and network.                                                                                     | - Minimum/Maximum Units<br>- Auto-Scaling Thresholds (e.g., CPU > 70% for +2 nodes)<br>- Cooldown Periods  |
| **Scaling Trigger**         | Conditions that trigger scaling actions (e.g., request volume, latency spikes, or custom metrics).                                                          | - Metric Name (e.g., "RequestLatencyP99")<br>- Threshold Value (e.g., "500ms")<br>- Predefined Actions       |
| **Cost Model**              | Models cost implications of capacity (e.g., on-demand vs. reserved instances).                                                                                  | - Unit Cost (e.g., "$0.05/hour per vCPU")<br>- Discount Tiers (e.g., 1-year reserved instances)<br>- Pricing Tier (Standard, Premium) |
| **Dependency Graph**        | Maps relationships between services/components to identify cascading effects during scaling.                                                               | - Service A → Service B (e.g., DB → API)<br>- Dependency Weight (e.g., "Critical," "Low")<br>- Failure Impact |
| **Performance SLAs**        | Defines acceptable error rates, latency, and availability targets.                                                                                              | - Error Budget (e.g., 1% daily errors allowed)<br>- Latency Target (e.g., P99 < 300ms)<br>- Uptime SLA (%) |
| **Historical Data**         | Stores load metrics (e.g., requests/second, memory usage) for trend analysis.                                                                                    | - Timestamp<br>- Metric Name<br>- Value<br>- Anomaly Flags (e.g., "Spike Detected")                          |
| **Policy Engine**           | Rules engine to automate decisions (e.g., "If CPU > 80% for 5 mins, scale up by 2 nodes").                                                                     | - IF Condition (e.g., "CPU Utilization > Threshold")<br>- THEN Action (e.g., "Add Capacity")<br>- ELSE Action (e.g., "Notify") |
| **Feedback Loop**           | Mechanism to refine predictions using real-time performance data and user feedback.                                                                           | - Feedback Source (e.g., "Auto," "Manual")<br>- Adjustment Interval (e.g., "Daily")<br>- Confidence Score    |

---

## **3. Query Examples**

### **3.1 Load Profiling Queries**
**Purpose:** Identify workload patterns to inform capacity planning.

#### **Query 1: Identify Seasonal Workloads**
```sql
SELECT
    workload_id,
    DATE_TRUNC('month', timestamp) AS month,
    AVG(requests_per_minute) AS avg_load,
    MAX(requests_per_minute) AS peak_load,
    (MAX(requests_per_minute) / AVG(requests_per_minute)) AS peak_factor
FROM workload_metrics
WHERE service_name = 'ecommerce'
GROUP BY 1, 2
ORDER BY avg_load DESC;
```
**Output Example:**
| `workload_id` | `month`   | `avg_load` | `peak_load` | `peak_factor` |
|---------------|-----------|------------|-------------|---------------|
| 123           | 2023-12   | 1500       | 12,000      | 8.0           |

**Interpretation:** A peak factor of **8x** suggests high variability, requiring dynamic scaling.

---

#### **Query 2: Detect Anomalous Spikes**
```sql
SELECT
    timestamp,
    metric_name,
    value,
    CASE
        WHEN value > (AVG(value) OVER (PARTITION BY metric_name ORDER BY timestamp ROWS BETWEEN 7 PRECEDING AND CURRENT ROW)) * 1.5
        THEN 'Spike'
        ELSE 'Normal'
    END AS anomaly_status
FROM system_metrics
WHERE metric_name IN ('cpu_usage', 'memory_usage')
ORDER BY timestamp DESC
LIMIT 50;
```
**Output:**
| `timestamp`      | `metric_name` | `value` | `anomaly_status` |
|------------------|---------------|---------|------------------|
| 2023-10-15 14:30 | cpu_usage     | 95%     | Spike            |

**Action:** Investigate root cause (e.g., failed batch job) and adjust reserves.

---

### **3.2 Scaling Policy Queries**
**Purpose:** Validate scaling rules before deployment.

#### **Query 3: Simulate Auto-Scaling Impact**
```sql
WITH simulated_load AS (
    SELECT
        timestamp,
        predicted_requests,
        current_capacity,
        CASE
            WHEN predicted_requests > (current_capacity * 1.2)
            THEN current_capacity * 1.2  -- Scale up by 20%
            ELSE current_capacity * 0.8   -- Scale down by 20%
        END AS adjusted_capacity
    FROM load_forecast
    WHERE service_name = 'dashboard'
)
SELECT
    timestamp,
    predicted_requests,
    current_capacity,
    adjusted_capacity,
    adjusted_capacity - current_capacity AS capacity_delta
FROM simulated_load
ORDER BY timestamp;
```
**Output:**
| `timestamp`      | `predicted_requests` | `current_capacity` | `adjusted_capacity` | `capacity_delta` |
|------------------|----------------------|--------------------|---------------------|------------------|
| 2023-11-01       | 5,000                | 4,000              | 4,800               | +800             |

**Result:** Projected **+20% capacity** to handle Q1 traffic.

---

#### **Query 4: Cost vs. Performance Tradeoff**
```sql
SELECT
    scaling_strategy,
    avg_latency_ms,
    cost_per_month,
    (avg_latency_ms / 100) * cost_per_month AS latency_cost_ratio
FROM (
    SELECT
        CASE
            WHEN is_auto_scaling = TRUE THEN 'Auto-Scaling'
            ELSE 'Reserved Instances'
        END AS scaling_strategy,
        P99_latency_ms,
        SUM(unit_cost * hours_used) AS cost_per_month
    FROM capacity_metrics
    GROUP BY 1
)
ORDER BY latency_cost_ratio DESC;
```
**Output:**
| `scaling_strategy` | `avg_latency_ms` | `cost_per_month` | `latency_cost_ratio` |
|--------------------|------------------|-------------------|----------------------|
| Reserved Instances | 250              | $1,200            | 3.0                  |
| Auto-Scaling       | 300              | $1,500            | 4.5                  |

**Insight:** **Reserved Instances** offer **lower latency-cost tradeoff**.

---

### **3.3 Dependency Analysis Queries**
**Purpose:** Ensure scaling actions don’t break critical dependencies.

#### **Query 5: Identify High-Dependency Services**
```sql
SELECT
    dependent_service,
    service_name,
    dependency_weight,
    COUNT(DISTINCT failure_scenario) AS failure_scenarios
FROM service_dependencies
WHERE dependency_weight > 0.7  -- Critical dependencies only
GROUP BY 1, 2, 3
ORDER BY failure_scenarios DESC;
```
**Output:**
| `dependent_service` | `service_name` | `dependency_weight` | `failure_scenarios` |
|----------------------|----------------|---------------------|---------------------|
| payment_gateway      | checkout_service | 0.9                 | 3                   |

**Action:** **Coordinate scaling** of `payment_gateway` with `checkout_service` to avoid cascading failures.

---

## **4. Implementation Patterns by Use Case**

| **Use Case**               | **Recommended Patterns**                                                                                     | **Key Attributes to Configure**                                                                 |
|----------------------------|------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Seasonal Workloads**     | - **Reserved Capacity for Base Load**<br>- **Auto-Scaling for Peaks**                                       | - Peak window (e.g., "Q4: Nov–Dec")<br>- Reserve ratio (e.g., 60% of base load)<br>- Scale-up threshold (e.g., CPU > 85%) |
| **Bursty Traffic**         | - **Event-Driven Scaling** (e.g., AWS Auto Scaling, Kubernetes HPA)<br>- **Queue-Based Backpressure**         | - Trigger metric (e.g., `requests_in_flight`)<br>- Cooldown period (e.g., 5 mins)<br>- Max instances (e.g., 100) |
| **Multi-Region Failover**  | - **Active-Active with Traffic Mirroring**<br>- **Predictive Failover** (using anomaly detection)         | - Regional latency SLA (e.g., < 200ms)<br>- Failover threshold (e.g., "3 consecutive region failures")<br>- Capacity mirror ratio (e.g., 0.8) |
| **Cost Optimization**      | - **Spot Instances for Tolerable Failures**<br>- **Right-Sizing with ML Forecasting**                     | - Spot bid percentage (e.g., 70% of on-demand)<br>- Forecast horizon (e.g., 7 days)<br>- Tolerable RTO (e.g., 15 mins) |
| **Legacy System Upgrade**  | - **Phased Migration with Shadow Traffic**<br>- **Capacity Bridge** (dual-write during transition)        | - Migration window (e.g., "2 weeks")<br>- Shadow traffic ratio (e.g., 10%)<br>- Cutover trigger (e.g., "99.9% data sync") |

---

## **5. Best Practices**
1. **Start with Historical Data:**
   - Use at least **3–6 months of metrics** to identify patterns.
   - Example tools: **Prometheus**, **CloudWatch**, or **Datadog**.

2. **Define SLAs First:**
   - Align capacity planning with **business KPIs** (e.g., "99.9% uptime for payments").
   - Example SLA template:
     ```
     SLA: Uptime > 99.95%
     Latency P99 < 300ms
     Error Budget: 0.05% daily failures
     ```

3. **Automate Scaling Actions:**
   - Use **infrastructure-as-code (IaC)** (e.g., Terraform, CloudFormation) to deploy scaling policies.
   - Example Terraform snippet for AWS Auto Scaling:
     ```hcl
     resource "aws_autoscaling_policy" "scale_on_cpu" {
       name                   = "scale-on-cpu"
       policy_type            = "TargetTrackingScaling"
       autoscaling_group_name = aws_autoscaling_group.app.name
       target_tracking_configuration {
         predefined_metric_specification {
           predefined_metric_type = "ASGAverageCPUUtilization"
         }
         target_value = 70.0
       }
     }
     ```

4. **Monitor Dependency Impacts:**
   - Use **distributed tracing** (e.g., Jaeger, OpenTelemetry) to track request flows.
   - Example query to map dependencies:
     ```sql
     SELECT
         service_a,
         service_b,
         COUNT(*) AS call_count,
         AVG(latency_ms) AS avg_latency
     FROM trace_events
     WHERE trace_id IN (
         SELECT trace_id FROM service_dependencies
         WHERE service_a = 'api-gateway' AND service_b = 'db-service'
     )
     GROUP BY 1, 2;
     ```

5. **Iterate with Feedback Loops:**
   - Implement **post-mortem reviews** for outages and **A/B test scaling policies**.
   - Example feedback loop workflow:
     ```
     1. Deploy new scaling policy.
     2. Monitor P99 latency and error rates.
     3. If P99 > 500ms, roll back and adjust thresholds.
     ```

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Chaos Engineering](https://chaosengineering.io/)** | Deliberately introduces failures to test resilience.                                                                                         | Validating capacity planning under worst-case scenarios (e.g., region outage).                     |
| **[Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)** | Stops cascading failures by halting calls to unhealthy services.                                                                          | When dependencies are critical (e.g., payment processing).                                         |
| **[Multi-Region Deployment](https://aws.amazon.com/architecture/multi-region/)** | Distributes workloads across regions for high availability.                                                                               | Global applications with strict uptime requirements (e.g., SaaS).                                  |
| **[Canary Releases](https://www.deploygate.com/blog/canary-deployment)** | Gradually rolls out changes to a subset of users.                                                                                            | Testing new scaling configurations without full risk exposure.                                      |
| **[Cost as a Service](https://www.gartner.com/smarterwithgartner/cost-as-a-service)** | Treats infrastructure costs as variable expenses.                                                                                          | Startups or variable workloads where predictability is low.                                         |

---
### **Further Reading**
- **[AWS Well-Architected Framework: Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/overview.html)**
- **[Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/table-of-contents/)**
- **[Kubernetes Horizontal Pod Autoscaler (HPA) Docs](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscaler/)**