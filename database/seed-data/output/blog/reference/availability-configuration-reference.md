# **[Pattern] Availability Configuration Reference Guide**

---

## **1. Overview**
The **Availability Configuration** pattern defines how system components, services, or resources are made accessible to users, clients, or other systems. It ensures that stakeholders—such as developers, DevOps engineers, and infrastructure teams—can define, modify, and enforce availability policies to meet business SLAs, failover needs, and cost optimization goals.

This pattern standardizes how availability is configured in terms of **geographic distribution, redundancy, failover behavior, and regional prioritization**. It supports scenarios like global applications, disaster recovery, and cost-effective scaling by allowing explicit control over where and when resources are available.

Common use cases include:
- **Global applications** requiring low-latency deployment across multiple regions
- **Disaster recovery** with failover to backup regions
- **Cost optimization** by disabling or throttling resources in low-priority regions
- **Multi-tenancy** where availability rules vary per tenant

---

## **2. Key Concepts**

| **Term**                     | **Definition**                                                                                                                                                                                                 |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Availability Zone**        | A logical partitioning within a region that provides physical separation (e.g., power, networking). Ensures resilience within a single region.                                                          |
| **Region**                   | A geographic area (e.g., `us-west-2`, `eu-central-1`) where resources can be deployed. Availability spans multiple regions for global coverage.                                                          |
| **Failover Policy**          | Rules dictating which region takes over primary role if a region fails (e.g., `prefer-primary`, `least-loaded`, `manual`).                                                                              |
| **Availability Group**       | A logical grouping of regions/services with shared availability rules (e.g., a group of 3 regions enforcing active-active failover).                                                                 |
| **Availability Weight**      | A numeric value (0–100) representing the relative importance of a region for failover priorities or traffic routing. Higher values increase likelihood of being selected.                            |
| **Availability Tags**        | Metadata labels (e.g., `environment=prod`, `team=finance`) to categorize resources for conditional availability rules.                                                                                     |
| **Availability Throttling**  | Limits on requests served per region to control costs or manage traffic spikes.                                                                                                                             |
| **Snapshot Retention**       | Duration (e.g., 7 days) for which backups are kept in a region for recovery purposes.                                                                                                                      |
| **Health Check Endpoint**    | URL or script used to proactively monitor availability in a region.                                                                                                                                     |

---

## **3. Schema Reference**

### **3.1 Availability Configuration Schema**
```json
{
  "availability": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "description": "Global availability rules for system components.",
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "Unique identifier for this configuration."
      },
      "name": {
        "type": "string",
        "description": "Human-readable name (e.g., 'Global Customer Portal')."
      },
      "enabled": {
        "type": "boolean",
        "default": true,
        "description": "Whether this configuration is active."
      },
      "regions": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "region": {
              "type": "string",
              "enum": [
                "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", // ... list all eligible regions
                "global"
              ],
              "description": "Target region or 'global' for pan-region coverage."
            },
            "availabilityZone": {
              "type": "string",
              "description": "Specific availability zone within the region (e.g., 'a', 'b')."
            },
            "weight": {
              "type": "integer",
              "minimum": 0,
              "maximum": 100,
              "description": "Priority for failover/traffic distribution."
            },
            "failoverPolicy": {
              "type": "string",
              "enum": ["primary", "secondary", "manual"],
              "description": "Role during failover events."
            },
            "healthCheck": {
              "type": "string",
              "format": "uri",
              "description": "Endpoint for availability checks."
            },
            "throttleRequests": {
              "type": "object",
              "properties": {
                "maxRequestsPerSecond": { "type": "integer" },
                "burstLimit": { "type": "integer" }
              }
            },
            "snapshotRetentionDays": {
              "type": "integer",
              "minimum": 1,
              "description": "Backup retention period in days."
            },
            "tags": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Availability-related metadata."
            }
          },
          "required": ["region"]
        }
      },
      "failoverGroup": {
        "type": "string",
        "description": "Group ID to associate with other configurations for coordinated failover."
      }
    },
    "required": ["regions"]
  }
}
```

---

### **3.2 Example Configuration**
```json
{
  "availability": {
    "name": "Multi-Region Order Processing",
    "enabled": true,
    "regions": [
      {
        "region": "us-east-1",
        "weight": 80,
        "failoverPolicy": "primary",
        "healthCheck": "https://apiorders.us-east-1.example.com/health",
        "snapshotRetentionDays": 7,
        "tags": ["prod", "finance"]
      },
      {
        "region": "eu-west-1",
        "weight": 50,
        "failoverPolicy": "secondary",
        "throttleRequests": { "maxRequestsPerSecond": 5000 }
      },
      {
        "region": "ap-southeast-1",
        "weight": 30,
        "failoverPolicy": "secondary"
      }
    ],
    "failoverGroup": "finance-payment"
  }
}
```

---

## **4. Query Examples**

### **4.1 Query for Primary Regions**
**Use Case:** Identify all regions marked as primary for failover.
**Query (CLI/REST API):**
```sh
# Using a hypothetical CLI tool
avail query --filter "regions.failoverPolicy=primary" --output json
```

**Output:**
```json
[
  {
    "region": "us-east-1",
    "name": "Primary US Region",
    "failoverPolicy": "primary"
  },
  {
    "region": "eu-west-1",
    "name": "Primary EU Region",
    "failoverPolicy": "primary"
  }
]
```

---
### **4.2 Query for Regions with High Throttling**
**Use Case:** Check regions enforcing request limits.
**Query:**
```sh
avail query --filter "regions.throttleRequests.maxRequestsPerSecond < 10000" --sort weight:desc
```

---

### **4.3 Update Throttling in a Region**
**Use Case:** Adjust request limits in `ap-southeast-1`.
**Command:**
```sh
avail update --id "order-processing" --patch '{
  "regions[0].throttleRequests": {
    "maxRequestsPerSecond": 3000,
    "burstLimit": 10000
  }
}'
```

---
### **4.4 Simulate Failover**
**Use Case:** Test failover by marking `us-east-1` as unavailable.
**Command:**
```sh
avail failover --id "order-processing" --region us-east-1 --action "degrade"
```
**Output:**
```
Region us-east-1 degraded. Traffic rerouted to eu-west-1 (weight=50).
```

---

## **5. Implementation Considerations**

### **5.1 Supported Region List**
Ensure your system supports these common regions (expand as needed):
```json
[
  "us-east-1", "us-east-2", "us-west-1", "us-west-2",
  "eu-west-1", "eu-west-2", "eu-central-1",
  "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
  "global"
]
```

### **5.2 Health Check Best Practices**
- Use **Liveness Probes**: Health checks should return fast (e.g., under 2s).
- **Retry Logic**: Configure retries for transient failures (e.g., 3 retries with 5s backoff).
- **Notices**: Alert on degraded health (e.g., via Slack/PagerDuty).

### **5.3 Failover Testing**
- **Chaos Testing**: Simulate region outages using tools like [Chaos Mesh](https://chaos-mesh.org/).
- **Blue-Green Deployments**: Test failover after deploying new versions.

---

## **6. Error Handling**
| **Error Code** | **Description**                                                                 | **Resolution**                                                                 |
|----------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `INVALID_REGION` | Specified region is not supported.                                              | Use `avail list-regions` to check valid regions.                            |
| `WEIGHT_CONFLICT` | Total weight across regions exceeds 100.                                       | Redistribute weights (e.g., `weight: 50, 30, 20` instead of `40, 40, 30`). |
| `UNAUTHORIZED`  | Insufficient permissions to modify availability.                                | Grant permissions via IAM/role policies.                                    |

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Relationship**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Regional Load Balancing](#)** | Distributes traffic across regions for performance.                       | Complements `Availability Configuration` by applying traffic rules post-availability. |
| **[Circuit Breaker](#)**   | Prevents cascading failures during outages.                                | Works with failover policies to isolate failures.                              |
| **[Multi-Region Database Replication](#)** | Keeps replicas synchronized across regions. | Required for active-active failover scenarios defined in availability groups.  |
| **[Tag-Based Routing](#)** | Routes traffic based on metadata tags.                                     | Extends availability rules with additional filtering (e.g., `team=marketing`). |

---

## **8. Versioning**
- **Schema Version**: `v1.2` (Last updated: 2024-01-15)
- **Breaking Changes**:
  - `v1.1`: Added `snapshotRetentionDays` field.
  - `v1.0`: Initial release.

---
**References:**
- [AWS Availability Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)
- [Global Load Balancer Design Patterns](https://www.oreilly.com/library/view/global-load-balancing/9781492042845/)