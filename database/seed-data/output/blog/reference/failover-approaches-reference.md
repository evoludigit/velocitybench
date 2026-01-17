---
# **[Pattern] Failover Approaches – Reference Guide**

---

## **Overview**
**Failover Approaches** is a **resilience pattern** that ensures uninterrupted service delivery by automatically redirecting requests to a backup component when the primary component fails. This pattern is critical for high-availability systems, where downtime can result in lost revenue, degraded user experience, or data loss.

Failover can be **active-active** (both primary and backup systems process requests concurrently) or **active-passive** (only the primary system processes requests until failure). Implementations vary by infrastructure (e.g., cloud, on-premises, service meshes) and application type (e.g., stateless vs. stateful services). This guide covers **key concepts, implementation strategies, configuration options, and trade-offs** for different failover approaches.

---

## **1. Key Concepts**
| **Term**               | **Definition**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|
| **Primary Component**  | The active system processing user requests.                                                        |
| **Backup Component**   | A standby system ready to take over if the primary fails.                                         |
| **Failover Trigger**   | Event that initiates failover (e.g., health check failure, threshold breach, manual intervention). |
| **Failover Detection** | Mechanism to detect primary system failure (e.g., heartbeats, ping checks, circuit breakers).    |
| **Failback**           | Process of reverting to the primary component after it recovers (optional).                       |
| **Latency Spike**      | Temporary increase in response time during failover due to backup system initialization.          |
| **Data Synchronization**| Ensuring backup systems have up-to-date data (e.g., via replication, change logs).               |

---

## **2. Failover Approaches & Implementation Details**
Failover approaches are categorized by **topology** and **trigger mechanism**:

| **Approach**               | **Description**                                                                                     | **Use Case**                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Active-Passive**         | Only the primary processes requests; backup remains idle until failover.                           | Cost-effective for low-traffic or rare failure scenarios (e.g., databases, monolithic apps).   |
| **Active-Active**          | Both primary and backup process requests simultaneously; load balancer routes traffic.             | High-traffic systems requiring zero downtime (e.g., microservices, cloud-native apps).           |
| **Manual Failover**        | Admin-initiated failover (e.g., scheduled maintenance).                                            | Controlled environments where automation is risky (e.g., critical infrastructure).                |
| **Automatic Failover**     | Triggered by health checks, thresholds, or circuit breakers.                                      | Self-healing systems (e.g., Kubernetes pods, AWS Auto Scaling).                                  |
| **Geographic Failover**    | Backup in a different region/cloud to mitigate regional outages.                                    | Global applications (e.g., SaaS platforms).                                                    |
| **Service Mesh Failover**  | Failover managed by a service mesh (e.g., Istio, Linkerd) via sidecar proxies.                    | Microservices architectures with dynamic routing.                                               |

---

## **3. Schema Reference**
### **3.1 Failover Configuration Schema**
```json
{
  "failoverApproach": {
    "type": "object",
    "properties": {
      "topology": {
        "type": "string",
        "enum": ["active-passive", "active-active", "manual", "automatic"],
        "description": "Failover topology strategy."
      },
      "trigger": {
        "type": "object",
        "properties": {
          "healthCheck": {
            "type": "object",
            "properties": {
              "interval": { "type": "number", "unit": "seconds" },
              "timeout": { "type": "number", "unit": "seconds" },
              "threshold": { "type": "number", "minimum": 1 }
            }
          },
          "threshold": {
            "type": "object",
            "properties": {
              "metric": { "type": "string", "example": "error_rate" },
              "value": { "type": "number" }
            }
          },
          "manual": {
            "type": "boolean",
            "description": "Whether failover requires admin intervention."
          }
        }
      },
      "backupSystem": {
        "type": "object",
        "properties": {
          "endpoint": { "type": "string", "format": "uri" },
          "syncMethod": {
            "type": "string",
            "enum": ["replication", "change_log", "snapshots"]
          }
        }
      },
      "failback": {
        "type": "boolean",
        "description": "Enable automatic failback to primary after recovery."
      },
      "geographicLocation": {
        "type": "string",
        "description": "Region/cloud for backup (e.g., `us-west-2` or `aws`)."
      }
    }
  }
}
```

---

## **4. Query Examples**
### **4.1 Detecting Failover Trigger (Health Check)**
```python
# Pseudocode for health check (e.g., using Prometheus)
def check_health():
    response = request.get("http://primary-service:8080/health")
    if response.status_code != 200:
        trigger_failover("primary-service", "backup-service")
```

### **4.2 Active-Active Load Balancing (AWS ALB Example)**
```yaml
# AWS Application Load Balancer (ALB) config for active-active
Resources:
  PrimaryTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Targets:
        - Id: primary-instance-id
          Port: 80
  BackupTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Targets:
        - Id: backup-instance-id
          Port: 80
  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref PrimaryTargetGroup
          Weight: 100
        - Type: forward
          TargetGroupArn: !Ref BackupTargetGroup
          Weight: 0  # Weight 0 disables until failover
```

### **4.3 Circuit Breaker (Resilience4j Example)**
```java
// Circuit Breaker configuration (Resilience4j)
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)  // Failover if 50% failures
    .slowCallRateThreshold(70)  // Failover if 70% slow responses
    .slowCallDurationThreshold(Duration.ofSeconds(2))
    .permittedNumberOfCallsInHalfOpenState(3)
    .recordExceptions(TimeoutException.class, ServiceUnavailableException.class)
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("serviceA", config);
```

### **4.4 Geographic Failover (Terraform Example)**
```hcl
# Terraform: Multi-region deployment
resource "aws_instance" "primary" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  availability_zone = "us-east-1a"
}

resource "aws_instance" "backup" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  availability_zone = "eu-west-1a"  # Backup in Europe
}
```

---

## **5. Trade-offs**
| **Approach**       | **Pros**                                                                 | **Cons**                                                                 |
|--------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Active-Passive** | Lower cost, simpler synchronization.                                     | Higher latency during failover, no redundancy during primary uptime.  |
| **Active-Active**  | Zero downtime, horizontal scaling.                                        | Higher cost, complex data consistency.                                  |
| **Manual Failover**| Full control, no unintended outages.                                     | Downtime during failover, requires admin intervention.                  |
| **Automatic**      | Self-healing, reduces MTTR.                                               | Risk of cascading failures if triggers are misconfigured.               |
| **Geographic**     | Mitigates regional outages.                                               | Higher latency, cross-region data sync overhead.                         |

---

## **6. Related Patterns**
1. **Circuit Breaker** – Prevents cascading failures by stopping requests to a failing service.
2. **Retry with Backoff** – Resolves transient failures (e.g., network blips) before initiating failover.
3. **Bulkhead** – Isolates failures in one component from affecting others (e.g., thread pools).
4. **Rate Limiting** – Prevents backup overload during failover.
5. **Multi-Region Deployment** – Complements geographic failover for global resilience.
6. **Chaos Engineering** – Proactively tests failover mechanisms (e.g., using Netflix Chaos Monkey).

---
## **7. Best Practices**
- **Minimize Failover Latency**: Use fast detection (e.g., heartbeats) and low-latency sync (e.g., change logs).
- **Test Failover**: Simulate failures in staging (e.g., kill primary pods in Kubernetes).
- **Monitor Failbacks**: Ensure primary recovers and traffic reroutes back smoothly.
- **Document Procedures**: Define manual failover steps for critical systems.
- **Avoid Split-Brain**: For active-active, use consensus protocols (e.g., Raft, Paxos) to prevent conflicting states.