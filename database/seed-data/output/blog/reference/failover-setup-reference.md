# **[Pattern] Failover Setup Reference Guide**

---

## **Overview**
The **Failover Setup** pattern provides a structured approach to ensuring high availability by automatically rerouting traffic from a primary service to a secondary (backup) service when the primary fails. This guide outlines key concepts, implementation details, schema references, query examples, and related patterns for configuring and managing failovers in distributed systems, microservices, or cloud-native deployments.

This pattern is essential for minimizing downtime, improving resilience, and maintaining service continuity during infrastructure failures, network disruptions, or application crashes. It’s commonly used in load balancers, database replication, Kubernetes deployments, and service orchestration frameworks.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**       | **Description**                                                                 |
|---------------------|---------------------------------------------------------------------------------|
| **Primary Service** | The active endpoint being served to clients.                                   |
| **Secondary Service** | A standby service that takes over when the primary fails.                  |
| **Health Check**    | Mechanism to monitor the primary service’s operational status (e.g., HTTP probes, ping checks). |
| **Detection Logic** | Algorithm (e.g., active-active, active-passive) to trigger failover.        |
| **Traffic Routing** | Mechanism (e.g., DNS, load balancer, API gateway) to switch traffic to the secondary. |
| **Synchronization** | Ensures data consistency between primary and secondary (e.g., replication, eventual consistency). |
| **Failback**        | Process to return traffic to the primary when it recovers.                   |

### **2. Failover Strategies**
| **Strategy**        | **Description**                                                                 | **Use Case**                                  |
|---------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Active-Passive**  | Primary handles traffic; secondary is idle until failover occurs.               | Single-writer scenarios, cost-sensitive setups. |
| **Active-Active**   | Both primary and secondary serve traffic; routing logic prioritizes one.       | High-throughput, geographically distributed systems. |
| **Multi-Region**    | Secondary is in a different cloud/geographic region for disaster recovery.      | Global applications with low-latency requirements. |

### **3. Failure Modes Handled**
- **Infrastructure Failures** (e.g., server crash, network partition).
- **Application Failures** (e.g., crashes, timeouts, degraded performance).
- **Configuration Errors** (e.g., misconfigured endpoints).
- **Security Threats** (e.g., DDoS attacks overwhelming the primary).

### **4. Common Tools/Technologies**
| **Category**        | **Tools/Technologies**                                                      |
|---------------------|-----------------------------------------------------------------------------|
| **Load Balancers**  | AWS ALB/NLB, Nginx, HAProxy, Envoy.                                          |
| **Service Meshes**  | Istio, Linkerd (for Kubernetes-based failover).                             |
| **Databases**       | PostgreSQL (replication), MongoDB (sharding/replica sets), DynamoDB (multi-region). |
| **Orchestration**   | Kubernetes (PodDisruptionBudget, Readiness/Liveness Probes), Docker Swarm. |
| **API Gateways**    | Kong, Apigee, AWS API Gateway (with failover policies).                       |
| **Monitoring**      | Prometheus, Datadog, New Relic (for health checks).                          |

---

## **Schema Reference**

### **1. Failover Configuration Schema**
Below is a JSON schema for defining failover rules in a declarative configuration (e.g., Kubernetes `Service`, AWS ALB, or Istio `DestinationRule`).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique identifier for the failover group."
    },
    "primaryService": {
      "type": "object",
      "properties": {
        "endpoint": { "type": "string", "format": "uri" },
        "healthCheck": {
          "type": "object",
          "properties": {
            "path": { "type": "string" },
            "interval": { "type": "integer", "minimum": 1 },
            "timeout": { "type": "integer", "minimum": 1 },
            "healthyThreshold": { "type": "integer", "minimum": 1 },
            "unhealthyThreshold": { "type": "integer", "minimum": 1 }
          },
          "required": ["path", "interval", "healthyThreshold", "unhealthyThreshold"]
        }
      },
      "required": ["endpoint", "healthCheck"]
    },
    "secondaryServices": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "endpoint": { "type": "string", "format": "uri" },
          "weight": { "type": "integer", "minimum": 1, "maximum": 100 }
        },
        "required": ["endpoint", "weight"]
      }
    },
    "strategy": {
      "type": "string",
      "enum": ["ACTIVE_PASSIVE", "ACTIVE_ACTIVE", "MULTI_REGION"],
      "default": "ACTIVE_PASSIVE"
    },
    "synchronization": {
      "type": "object",
      "properties": {
        "replicationLag": { "type": "integer", "description": "Max allowed lag (ms) for data sync." },
        "consistencyModel": {
          "type": "string",
          "enum": ["STRONG", "EVENTUAL"]
        }
      }
    },
    "failbackEnabled": {
      "type": "boolean",
      "default": true
    }
  },
  "required": ["primaryService", "secondaryServices", "strategy"]
}
```

---

### **2. Example Configurations**
#### **Kubernetes Service with Failover**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app-failover
spec:
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 9376
  healthCheckNodePort: 8080  # For NodePort Service
  failover:
    primary:
      endpoint: "http://primary-pod:80"
      healthCheck:
        path: "/health"
        interval: 10
        timeout: 5
        healthyThreshold: 2
        unhealthyThreshold: 3
    secondary:
      - endpoint: "http://secondary-pod:80"
        weight: 50
    strategy: "ACTIVE_ACTIVE"
```

#### **AWS ALB Failover Policy**
```json
{
  "Listeners": [
    {
      "Port": 80,
      "Protocol": "HTTP",
      "DefaultActions": [
        {
          "Type": "forward",
          "TargetGroupArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/primary-tg/1234567890abcdef",
          "ForwardConfig": {
            "TargetGroups": [
              {
                "TargetGroupArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/secondary-tg/0987654321fedcba",
                "Weight": 50
              }
            ]
          }
        }
      ]
    }
  ],
  "FailoverGroups": [
    {
      "PrimaryTargetGroupArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/primary-tg/1234567890abcdef",
      "SecondaryTargetGroupArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/secondary-tg/0987654321fedcba",
      "HealthCheckPath": "/health",
      "FailoverThreshold": 3
    }
  ]
}
```

---

## **Query Examples**

### **1. Detecting Failover Trigger**
**Scenario**: Query the health status of the primary service to determine if failover is needed.

**SQL (PostgreSQL Example)**:
```sql
SELECT
  service_name,
  last_health_check,
  status,
  case when status = 'UNHEALTHY' then true else false end as failover_needed
FROM service_health_monitor
WHERE service_name = 'primary-app'
  AND last_health_check > now() - interval '5 minutes';
```

**API (gRPC Example)**:
```protobuf
rpc CheckServiceHealth(CheckHealthRequest) returns (HealthResponse) {
  message CheckHealthRequest {
    string service_name = 1;
  }
  message HealthResponse {
    bool is_healthy = 1;
    string last_check_timestamp = 2;
  }
}
```

### **2. Routing Traffic to Secondary**
**Scenario**: Update DNS records or load balancer rules to route traffic to the secondary.

**DNS (PowerDNS API)**:
```bash
curl -X PUT "http://localhost:8081/api/v1/servers/1/records/myapp.example.com/AAAA" \
  -H "Content-Type: application/json" \
  -d '{"content": "2001:db8::secondary", "ttl": 300, "type": "AAAA"}'
```

**Terraform (AWS Load Balancer Update)**:
```hcl
resource "aws_lb_target_group" "secondary_tg" {
  name        = "secondary-app-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "instance"

  health_check {
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_listener_rule" "failover_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.secondary_tg.arn
  }

  condition {
    path_pattern {
      values = ["/failover-trigger"]
    }
  }
}
```

### **3. Failback Automation**
**Scenario**: Automatically return traffic to the primary once it recovers.

**Python (Using `requests` and `boto3`)**:
```python
import requests
import boto3

def monitor_and_failback():
    lb_client = boto3.client('elbv2')
    primary_target_group = "arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/primary-tg/1234567890abcdef"

    while True:
        response = requests.get("http://primary-app:80/health")
        if response.status_code == 200:
            # Update ALB to redirect to primary
            lb_client.modify_load_balancer_attributes(
                LoadBalancerArn="arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/my-app/1234567890abcdef",
                Attributes=[
                    {
                        "Key": "load_balancer.attributes.action_on.unhealthy=ALERT",
                        "Value": "true"
                    },
                    {
                        "Key": "load_balancer.attributes.target_group.arn",
                        "Value": primary_target_group
                    }
                ]
            )
            break
        time.sleep(5)  # Retry every 5 seconds
```

---

## **Related Patterns**
1. **Circuit Breaker**
   - Complements failover by temporarily stopping requests to a failing service to prevent cascading failures.
   - *Tools*: Hystrix, Resilience4j, Istio Circuit Breaker.

2. **Bulkhead**
   - Isolates failure domains to prevent one service’s failure from affecting others.
   - *Use Case*: Throttle requests to the secondary during failover.

3. **Retry with Backoff**
   - Automatically retries failed requests with exponential backoff before triggering failover.
   - *Tools*: Spring Retry, AWS Step Functions.

4. **Multi-Region Data Replication**
   - Ensures data consistency across regions for global failover.
   - *Tools*: AWS Global Accelerator, MongoDB Global Cluster.

5. **Chaos Engineering**
   - Proactively tests failover mechanisms by injecting failures.
   - *Tools*: Gremlin, Chaos Mesh.

6. **Service Mesh (Istio/Linkerd)**
   - Provides built-in failover, traffic shifting, and observability.
   - *Example*: Istio `VirtualService` for canary failover.

7. **Database Replication**
   - Synchronizes data between primary and secondary databases.
   - *Tools*: PostgreSQL Streaming Replication, Cassandra Multi-DC.

8. **Blue-Green Deployment**
   - Deploys a secondary version in parallel and switches traffic once validated.
   - *Use Case*: Zero-downtime releases.

---

## **Best Practices**
1. **Monitor Failover Events**: Log and alert on failover triggers (e.g., Prometheus + Alertmanager).
2. **Test Failover Regularly**: Simulate failures using chaos engineering tools.
3. **Minimize Latency**: Place secondaries close to primaries (e.g., same region or edge locations).
4. **Avoid Split-Brain**: Use quorum-based consensus (e.g., Raft) for distributed systems.
5. **Document Recovery Procedures**: Define steps for manual failback if automation fails.
6. **Use Idempotency**: Ensure failover operations can be safely repeated (e.g., DNS updates).
7. **Load Test**: Validate failover under heavy traffic using tools like Locust or JMeter.