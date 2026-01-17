# **[Pattern] Cost Monitoring Patterns – Reference Guide**

---

## **Overview**
Effective **Cost Monitoring** ensures cost efficiency, budget adherence, and proactive anomaly detection in cloud and on-premises environments. This guide outlines **best-practice patterns** for monitoring costs, categorizing them by scope (global, per-service, per-resource, or anomaly-based) and application (financial forecasting, alerting, or cost optimization).

Use these patterns to:
- Track spending trends over time.
- Set alerts for budget overruns.
- Identify cost-saving opportunities.
- Assess ROI of cloud investments.

---

## **Implementation Details**

### **1. Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Cost Monitoring**    | Continuous tracking of expenditure against predefined budgets, thresholds, or historical trends.                                                                                                               |
| **Budget**             | A financial limit set for a department, project, or resource type (e.g., "EC2 spend ≤ $5,000/month").                                                                                              |
| **Cost Anomaly**       | Unexpected spikes or deviations in spending (e.g., a 300% increase in database queries).                                                                                                                      |
| **Tag-Based Filtering**| Cost segmentation using resource tags (e.g., `Environment=Dev`, `Owner=TeamA`) for granular analysis.                                                                                                      |
| **Cost Allocation**    | Assigning costs to business units, projects, or departments via tags or organizational structures.                                                                                                          |
| **Forecasting**        | Predicting future spend based on historical trends, usage patterns, or planned scaling.                                                                                                                     |
| **Cost Optimization**  | Identifying underutilized resources, right-sizing recommendations, or idle resources to reduce waste.                                                                                                     |

---

### **2. Pattern Categories**
Cost Monitoring Patterns are grouped by **scope** and **use case**:

| **Scope**          | **Pattern**                          | **Purpose**                                                                                                                                                     |
|--------------------|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Global**         | **Budget Tracking**                  | Monitor total spend across accounts/projects against predefined budgets.                                                                                         |
| **Service-Level**  | **Service-Specific Cost Alerts**     | Alert on abnormal usage (e.g., "Lambda invocations spiked by 50%").                                                                                           |
| **Resource-Level** | **Tag-Based Cost Analysis**           | Analyze costs by environment, team, or project via resource tags.                                                                                                |
| **Anomaly-Based**  | **Anomaly Detection & Root Cause**    | Use ML or statistical methods to flag irregular spending patterns.                                                                                             |
| **Forecasting**    | **Spend Forecasting**                | Predict future costs 30/60/90 days ahead for budget planning.                                                                                                 |
| **Optimization**   | **Cost Savings Recommendations**      | Suggest actions like stopping idle VMs, using spot instances, or right-sizing storage.                                                                          |

---

## **Schema Reference**
Below are the **core schemas** for implementing Cost Monitoring:

### **1. Budget Definition Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BudgetDefinition",
  "type": "object",
  "properties": {
    "budget_id": { "type": "string", "format": "uuid" },
    "name": { "type": "string", "example": "Dev Team Budget" },
    "amount": { "type": "number", "minimum": 0 },
    "currency": { "type": "string", "enum": ["USD", "EUR", "GBP"] },
    "start_date": { "type": "string", "format": "date" },
    "end_date": { "type": "string", "format": "date" },
    "account_ids": { "type": ["array", "null"], "items": { "type": "string" } },
    "service_filters": { "type": ["array", "null"], "items": { "type": "string" } },
    "tags": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    },
    "alert_thresholds": {
      "type": "object",
      "properties": {
        "warning": { "type": "number", "minimum": 0 },
        "critical": { "type": "number", "minimum": 0 }
      },
      "required": ["warning", "critical"]
    }
  },
  "required": ["budget_id", "name", "amount", "currency", "start_date", "end_date"]
}
```

### **2. Cost Anomaly Detection Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CostAnomaly",
  "type": "object",
  "properties": {
    "anomaly_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" },
    "resource_id": { "type": "string" },
    "service": { "type": "string" },
    "actual_cost": { "type": "number" },
    "expected_cost": { "type": "number" },
    "deviation_percentage": { "type": "number" },
    "severity": { "type": "string", "enum": ["low", "medium", "high", "critical"] },
    "root_cause": { "type": "string", "nullable": true },
    "tags": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    }
  },
  "required": ["anomaly_id", "timestamp", "resource_id", "service", "actual_cost", "deviation_percentage"]
}
```

---

## **Query Examples**

### **1. Check Remaining Budget (SQL-like Pseudocode)**
```sql
SELECT
  b.budget_id,
  b.name,
  b.amount,
  SUM(c.cost) AS spent,
  (b.amount - SUM(c.cost)) AS remaining
FROM Budgets b
JOIN CostEvents c ON b.budget_id = c.budget_id
  AND c.timestamp BETWEEN b.start_date AND CURRENT_DATE()
WHERE b.account_ids = ['acc-12345']
GROUP BY b.budget_id;
```

### **2. Find Anomalous Spend (Python Pseudocode)**
```python
from datetime import datetime, timedelta

# Detect anomalies > 20% deviation from 7-day average
def find_anomalies(cost_data, threshold=0.2):
    anomalies = []
    for resource in cost_data:
        daily_costs = [entry['cost'] for entry in cost_data[resource]
                      if entry['timestamp'].date() >= datetime.now() - timedelta(days=7)]
        avg_cost = sum(daily_costs) / len(daily_costs)
        for entry in cost_data[resource]:
            deviation = abs(entry['cost'] - avg_cost) / avg_cost
            if deviation > threshold:
                anomalies.append({
                    "resource": resource,
                    "timestamp": entry['timestamp'],
                    "actual": entry['cost'],
                    "expected": avg_cost,
                    "deviation": deviation
                })
    return anomalies
```

### **3. Tag-Based Cost Breakdown (AWS CLI Example)**
```bash
aws cost-explorer get-cost-and-usage --time-period Start=2023-01-01,End=2023-01-31 \
  --filters "Tags.Key=Environment,Tags.Value=Production" \
  --granularity MONTHLY
```

---

## **Related Patterns**
To complement **Cost Monitoring Patterns**, consider integrating:

| **Related Pattern**            | **Purpose**                                                                                                                                                         | **Where to Use**                                                                                     |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Cost Allocation Strategy]**  | Assign costs to business units/departments for accountability.                                                                                                     | Multi-team environments, shared infrastructure.                                                    |
| **[Reserved Instance Planning]**| Optimize long-term savings by forecasting reserved instance usage.                                                                                                | Cloud-native teams with predictable workloads.                                                      |
| **[Right-Sizing Recommendations]**| Automatically adjust resource sizes (e.g., EC2, RDS) to reduce over-provisioning.                                                                | DevOps/SRE teams managing auto-scaling groups.                                                     |
| **[FinOps Governance]**         | Enforce cost policies (e.g., "No unused spot instances") via automation.                                                                                          | Finance/DevOps collaboration for policy enforcement.                                                  |
| **[Multi-Cloud Cost Comparison]**| Compare costs across AWS, Azure, and GCP for vendor agility.                                                                                                      | Cloud strategy teams evaluating hybrid/multi-cloud setups.                                           |

---

## **Best Practices**
1. **Tag Resources Consistently**
   Use standardized tags (e.g., `CostCenter`, `Owner`, `Project`) for accurate cost allocation.

2. **Set Up Alerts Proactively**
   Configure alerts at **70% and 100%** of budget limits to avoid surprises.

3. **Automate Anomaly Investigation**
   Use tools like **Amazon Cost Anomaly Detection** or **Google Cloud’s Cost Insights** for ML-driven insights.

4. **Forecast with Historical Data**
   Leverage **time-series forecasting** (e.g., ARIMA models) to predict seasonal spend spikes.

5. **Optimize Continuously**
   Schedule **quarterly cost reviews** to right-size resources and eliminate waste.

---
**Next Steps**:
- [ ] Implement **Budget Tracking** for your cloud accounts.
- [ ] Set up **anomaly detection** for critical services.
- [ ] Use **tag-based analysis** to identify cost drains.