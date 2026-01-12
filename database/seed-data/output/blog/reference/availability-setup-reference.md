**[Pattern] Availability Setup Reference Guide**

---

### **Overview**
The **Availability Setup** pattern defines a structured approach to configuring and managing system availability, ensuring resources, services, and infrastructure are optimized for reliability, scalability, and fault tolerance. It extends beyond basic uptime monitoring to encompass proactive configuration of redundancy, failover mechanisms, and performance thresholds. This pattern is critical for cloud-native, distributed, and mission-critical applications, where unplanned downtime can have severe business impacts. It enables teams to define availability zones, replication strategies, traffic routing, and degradation policies—either statically via infrastructure-as-code (IaC) or dynamically via runtime configurations. By separating concerns (e.g., network vs. compute vs. storage) and leveraging declarative definitions, teams can minimize human error and accelerate recovery procedures.

---

### **Key Concepts**
1. **Availability Zone (AZ):** A distinct data center or cluster within a region, isolated from other zones to prevent correlated failures. Configured during infrastructure provisioning.
2. **Replication Strategy:** Defines how data or application instances are duplicated across AZs (e.g., multi-AZ deployments, read replicas).
3. **Traffic Routing:** Controls how requests are distributed across instances, including:
   - **Primary-Secondary:** Active/passive failover.
   - **Active-Active:** Load-balanced traffic across multiple regions.
   - **Geographic Routing:** Prioritizes traffic based on proximity (e.g., latency-based).
4. **Degradation Thresholds:** Rules triggering automatic scaling or failover when SLA metrics (CPU, latency, error rates) exceed predefined limits.
5. **Health Checks:** Endpoint- or application-level checks to determine service readiness, informing routing decisions or failover.
6. **Chaos Engineering:** Optional integration to test failure scenarios (e.g., simulated AZ outages) without impacting production.

---

### **Schema Reference**
Below are key configurations in a cross-platform schema format. Fields are **bold** for required parameters.

| **Entity**            | **Field**                  | **Type**       | **Description**                                                                 | **Example Values**                                                                 |
|-----------------------|----------------------------|----------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **AvailabilityZone**  | `name`                     | `string`       | Unique identifier for the AZ (e.g., `us-west-1a`).                              | `us-west-1a`, `eu-central-1b`                                                       |
|                       | `region`                   | `string`       | Cloud region to which the AZ belongs.                                           | `us-west-1`, `eu-central-1`                                                         |
|                       | `subnet_id`                | `string`       | VPC subnet identifier for network isolation.                                     | `subnet-12345678`                                                                   |
|                       | `is_primary`               | `boolean`      | Marks the AZ for primary traffic (default: `false`).                            | `true`/`false`                                                                    |
|                       | `weight`                   | `integer`      | Traffic distribution weight (0–100).                                             | `50` (50% traffic)                                                                 |
| **Replication**       | `type`                     | `enum`         | Replication mode: `none`, `async`, `sync`, `multi-az`.                          | `async`, `multi-az`                                                                |
|                       | `target_azs`               | `array(string)`| List of AZs for replication targets.                                              | `["us-west-1b", "us-west-1c"]`                                                      |
|                       | `retry_attempts`           | `integer`      | Number of sync retries on failure.                                               | `3`                                                                                 |
|                       | `timeout_seconds`          | `integer`      | Sync timeout in seconds.                                                          | `30`                                                                                 |
| **RoutingPolicy**     | `strategy`                 | `enum`         | Routing mode: `primary-secondary`, `active-active`, `geographic`.              | `active-active`                                                                     |
|                       | `latency_based`            | `boolean`      | Enable latency-based routing.                                                    | `true`/`false`                                                                    |
|                       | `health_check_url`         | `string`       | Endpoint for health checks (e.g., `/api/health`).                                | `/health`                                                                        |
|                       | `check_interval_seconds`   | `integer`      | Frequency of health checks.                                                       | `30`                                                                                 |
| **DegradationRule**   | `metric`                   | `enum`         | Trigger metric: `cpu`, `latency`, `error_rate`, `disk_usage`.                   | `cpu`                                                                               |
|                       | `threshold`                | `float`        | Value at which to trigger actions (e.g., `0.9` for 90% CPU).                     | `0.85` (85%)                                                                         |
|                       | `action`                   | `enum`         | Triggered action: `scale-up`, `failover`, `route-to-backup`.                     | `failover`                                                                          |
|                       | `backoff_seconds`          | `integer`      | Delay before retrying an action.                                                  | `60`                                                                                 |
| **ChaosExperiment**   | `simulate_failure`         | `boolean`      | Enable chaos testing (e.g., AZ outage simulation).                               | `true`                                                                              |
|                       | `duration_minutes`         | `integer`      | Duration of the experiment.                                                       | `5`                                                                                  |

---

### **Query Examples**
Below are examples for common use cases, assuming a REST API (`/api/availability`) or CLI tool.

#### **1. Define Multi-AZ Deployment**
```bash
# Terraform (IaC)
resource "aws_availability_zone" "example" {
  name       = "us-west-1a"
  region     = "us-west-1"
  subnet_id  = "subnet-12345678"
  is_primary = true
}

resource "aws_replication" "example" {
  type          = "multi-az"
  target_azs    = ["us-west-1b", "us-west-1c"]
  retry_attempts = 3
}
```

#### **2. Configure Active-Active Routing**
```bash
# API Request (POST `/api/availability/policies`)
{
  "strategy": "active-active",
  "latency_based": true,
  "health_check_url": "/health",
  "check_interval_seconds": 30,
  "azs": [
    {"name": "us-west-1a", "weight": 50},
    {"name": "us-west-1b", "weight": 50}
  ]
}
```

#### **3. Set Degradation Thresholds**
```bash
# API Request (POST `/api/availability/degradation`)
{
  "metric": "cpu",
  "threshold": 0.85,
  "action": "scale-up",
  "backoff_seconds": 60
}
```

#### **4. Simulate AZ Failure (Chaos Testing)**
```bash
# API Request (POST `/api/availability/chaos`)
{
  "simulate_failure": true,
  "duration_minutes": 5,
  "target_az": "us-west-1a"
}
```

#### **5. Query Current Availability Status**
```bash
# API Request (GET `/api/availability/status`)
# Response:
{
  "status": "healthy",
  "azs": [
    {"name": "us-west-1a", "status": "operational"},
    {"name": "us-west-1b", "status": "degraded"}
  ],
  "routing": {"strategy": "active-active", "current_primary": "us-west-1a"}
}
```

---

### **Implementation Best Practices**
1. **Isolation by Default:**
   - Configure AZs with distinct subnets, security groups, and IAM roles to limit blast radii.
   - Example: Use separate VPCs for production vs. staging.

2. **Gradual Rollouts:**
   - Start with single-AZ deployments, then expand to multi-AZ as needed. Monitor failure rates before enabling failover.

3. **Observability:**
   - Integrate with monitoring tools (e.g., Prometheus, CloudWatch) to alert on AZ health or routing anomalies.

4. **Idempotency:**
   - Ensure IaC templates (e.g., Terraform, CloudFormation) are idempotent to avoid drift during updates.

5. **Document Recovery Procedures:**
   - Define runbooks for manual failover in cases where automated actions fail (e.g., network partitions).

6. **Cost-Aware Design:**
   - Balance redundancy with cost by:
     - Using spot instances for non-critical workloads.
     - Prioritizing replication for stateful services (e.g., databases) over stateless ones (e.g., APIs).

---

### **Related Patterns**
1. **[Fault Tolerance](link)**:
   - Complements Availability Setup by defining how systems recover from failures (e.g., circuit breakers, retries).

2. **[Canary Deployments](link)**:
   - Useful for testing availability changes in a controlled environment before full rollout.

3. **[Auto Scaling](link)**:
   - Works alongside Availability Setup to dynamically adjust capacity based on load or AZ failures.

4. **[Multi-Region Disaster Recovery](link)**:
   - Extends Availability Setup to global scale, with cross-region replication and traffic steering.

5. **[Infrastructure as Code (IaC)](link)**:
   - Required to version-control and replicate availability configurations across environments.

---

### **Example Workflow**
1. **Design Phase:**
   - Define AZs and replication strategies in Terraform/CloudFormation.
   - Set degradation thresholds for CPU/memory in the routing policy.

2. **Deployment Phase:**
   - Deploy applications with multi-AZ support.
   - Configure load balancers to distribute traffic based on AZ health.

3. **Runtime Phase:**
   - Monitor via API or dashboard (e.g., AWS Console, Datadog).
   - Trigger chaos experiments to validate failover (e.g., simulate `us-west-1a` outage).

4. **Recovery Phase:**
   - If an AZ fails, the routing policy automatically redirects traffic.
   - Use recovery runbooks if manual intervention is required.

---
**Note:** Adjust examples based on your specific cloud provider (AWS, GCP, Azure) or infrastructure stack. For provider-specific details, consult the platform’s documentation (e.g., [AWS Availability Zones](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html)).