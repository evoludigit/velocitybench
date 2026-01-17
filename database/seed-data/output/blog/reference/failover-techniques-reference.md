# **[Pattern] Failover Techniques Reference Guide**

---

## **Overview**
The **Failover Techniques** pattern defines mechanisms to ensure high availability by automatically rerouting system traffic to a backup (or secondary) component when a primary component fails or becomes unresponsive. Failover can be manual or automated, synchronous or asynchronous, and may involve hardware, software, or network-level redundancy.

This pattern is critical in distributed systems, cloud architectures, and mission-critical applications where uptime is paramount. Failover techniques balance **resilience**, **performance overhead**, and **recovery time objective (RTO)** while mitigating cascading failures.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary Node**       | The active component handling user requests.                                                                                                                                                                   |
| **Backup Node**        | A standby component ready to take over if the primary fails.                                                                                                                                                       |
| **Failover Trigger**   | Event that initiates failover (e.g., node downtime, latency spike, or health check failure).                                                                                                                  |
| **Synchronous Failover**| Failover occurs **during** a transaction (strong consistency, higher latency).                                                                                                                              |
| **Asynchronous Failover**| Failover occurs **after** a transaction completes (eventual consistency, lower latency).                                                                                                                      |
| **Active-Passive**     | Only one node (backup) is active at a time; backup stays dormant until failover.                                                                                                                               |
| **Active-Active**      | Multiple nodes handle requests simultaneously; failover routes traffic dynamically.                                                                                                                          |
| **Checkpointing**      | Periodically saving system state to ensure recoverability during failover.                                                                                                                                    |
| **Heartbeat**          | Regular communication between nodes to detect failures (e.g., TCP keepalives).                                                                                                                                  |
| **Replication Lag**    | Delay between primary and backup synchronization (affects RTO).                                                                                                                                               |
| **Circuit Breaker**    | Prevents cascading failures by halting requests to a failing service.                                                                                                                                            |
| **Load Balancer**      | Routes traffic to active nodes; can detect failures via health checks.                                                                                                                                          |

---

## **Implementation Schema**

### **1. Failover Architecture Types**
| **Schema**          | **Description**                                                                                                                                                                                                 |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Active-Passive**   | ![Diagram: A → [Primary] → User; [Backup] idle]                                                                                                                                                        |
| **Active-Active**    | ![Diagram: User → [Primary & Backup] parallel]                                                                                                                                                             |
| **Hot Standby**      | Backup is fully synchronized; immediate failover.                                                                                                                                                           |
| **Warm Standby**     | Backup is partially synchronized; delayed failover (~seconds).                                                                                                                                              |
| **Cold Standby**     | Backup is unsynchronized; failover requires recovery (~minutes).                                                                                                                                              |

### **2. Failover Mechanisms**
| **Mechanism**        | **Use Case**                                                                                     | **Pros**                                      | **Cons**                                      |
|----------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Heartbeat**        | Detect node failures via periodic probes.                                                          | Low overhead, real-time detection.            | False positives if network unstable.         |
| **Health Checks**    | Active probes (e.g., HTTP `200 OK`, database ping).                                               | Configurable thresholds.                      | Kills good nodes during traffic spikes.       |
| **Replication**      | Synchronize data between primary and backup (e.g., Kafka, Raft).                                 | Strong consistency.                           | High write latency.                          |
| **Circuit Breaker**  | Stop calls to a failing service (e.g., Hystrix).                                                   | Prevents cascading failures.                   | Degrades user experience.                    |
| **DNS Failover**     | Redirect traffic via DNS TTL updates (e.g., AWS Route 53).                                        | Simple, no app changes.                       | Slow (TTL-based).                            |
| **Load Balancer**    | Detects unhealthy nodes and routes traffic (e.g., Nginx, AWS ALB).                               | Granular control, health checks.               | Single point of failure.                     |
| **Client-Side**      | Clients retry failed requests to another node.                                                    | No server-side dependency.                    | Complex client logic.                        |

### **3. Failover Workflow**
1. **Monitor**: Detect failure via heartbeats/health checks.
2. **Notify**: Alert backup node or orchestration layer (e.g., Kubernetes, Consul).
3. **Promote**: Backup becomes primary (synchronous/asynchronous).
4. **Synchronize**: Resync data if replication lag exists.
5. **Route**: Update DNS/load balancer to direct traffic to new primary.
6. **Recover**: Fix primary; demote backup (if applicable).

---

## **Query Examples**

### **1. Detecting Failures (Pseudocode)**
```python
# Heartbeat-based failure detection (Active-Passive)
def detect_failure(primary_node):
    if not primary_node.heartbeat_received(timeout=5s):
        return True  # Failover trigger
    return False
```

```bash
# Health check via HTTP (Load Balancer)
curl -I http://<primary-node>:8080/health | grep "200 OK"
```

### **2. Automated Failover (Kubernetes Example)**
```yaml
# Deployment with readiness probes (Active-Active)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: web-app
        image: web-app:v1
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

```bash
# Kubernetes failover trigger (manual)
kubectl patch deployment web-app -p '{"spec":{"template":{"spec":{"containers":[{"name":"web-app","readinessProbe":null}]}}}}'
```

### **3. Database Failover (PostgreSQL Example)**
```sql
-- Create standby (replication)
SELECT pg_create_standby_control_file();
```

```bash
# Promote standby to primary
sudo -u postgres pg_ctl promote -D /var/lib/postgresql/data
```

### **4. DNS Failover (AWS Route 53)**
```json
# Failover record set (Weighted Routing)
{
  "Comment": "Web App Failover",
  "SetIdentifier": "web-app-failover",
  "HealthCheckId": "ABC123",
  "Failover": "PRIMARY",
  "Weight": 100,
  "Records": [
    {"Type": "A", "Value": "10.0.0.1"}
  ]
}
```

```bash
# Update failover weight (e.g., on primary failure)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://failover-update.json
```

---

## **Failure Scenarios & Mitigations**

| **Scenario**               | **Root Cause**                          | **Mitigation**                                                                                     |
|----------------------------|----------------------------------------|---------------------------------------------------------------------------------------------------|
| **Primary Node Crash**    | Hardware failure, OS crash.            | Use active-active or hot standby; checkpointing.                                                 |
| **Network Partition**      | Split-brain (both nodes think they’re primary). | Quorum-based consensus (e.g., Raft, ZooKeeper).                                                  |
| **Replication Lag**        | Backup can’t keep up with writes.       | Asynchronous failover; increase backup resources.                                                 |
| **Misconfigured Health Check** | False positive (e.g., high CPU load). | Adjust thresholds; use multiple health checks.                                                    |
| **Cascading Failures**     | Failover triggers dependent service outage. | Circuit breakers; gradual failover.                                                              |
| **DNS Propagation Delay**  | Slow DNS TTL updates.                   | Use health checks in load balancer; shorten TTL dynamically.                                       |

---

## **Best Practices**

1. **Minimize Replication Lag**:
   - Use synchronous replication for critical data (e.g., financial transactions).
   - Accept eventual consistency for non-critical data (e.g., logging).

2. **Test Failover Regularly**:
   - Simulate node failures in staging.
   - Measure **RTO** (Recovery Time Objective) and **RPO** (Recovery Point Objective).

3. **Avoid Split-Brain**:
   - Implement quorum-based failover (e.g., 2/3 node majority for promotion).
   - Use strong consistency protocols (e.g., Paxos, Raft) for distributed systems.

4. **Monitor Failover Health**:
   - Track failover events (e.g., Prometheus + Grafana).
   - Alert on prolonged failover durations.

5. **Hybrid Approaches**:
   - Combine active-active (for low latency) with active-passive (for critical writes).
   - Example: Read-heavy workloads (active-active) + write-heavy (active-passive).

6. **Graceful Degradation**:
   - Provide fallback UI/messages during failover (e.g., "Service unavailable; retry in 5s").
   - Degrade non-critical features first (e.g., analytics vs. core transactions).

7. **Automate Recovery**:
   - Use infrastructure-as-code (Terraform, Ansible) to restore primary.
   - Example: Kubernetes `Job` to heal failed pods.

---

## **Related Patterns**

| **Pattern**               | **Connection to Failover**                                                                                     | **Reference**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures during failover.                                                               | [Circuit Breaker Pattern](link-to-circuit-breaker-guide).                                        |
| **Bulkhead**              | Isolates failover impact to specific service instances.                                                    | [Bulkhead Pattern](link-to-bulkhead-guide).                                                      |
| **Retry with Backoff**    | Clients retry failed requests after failover.                                                             | [Exponential Backoff](link-to-retry-guide).                                                      |
| **Idempotency**           | Ensures safe retries after failover (e.g., `PUT` instead of `POST`).                                      | [Idempotency Pattern](link-to-idempotency-guide).                                                |
| **Saga Pattern**          | Manages distributed transactions across services during failover.                                         | [Saga Pattern](link-to-saga-guide).                                                              |
| **Multi-Region Deployment** | Reduces failover impact by spreading nodes across regions.                                                | [Multi-Region Architecture](link-to-multi-region-guide).                                          |
| **Chaos Engineering**     | Tests failover resilience by injecting failures (e.g., Netflix Chaos Monkey).                              | [Chaos Engineering](link-to-chaos-engineering-guide).                                            |
| **Database Sharding**     | Distributes failover load across shards.                                                                  | [Sharding Pattern](link-to-sharding-guide).                                                       |

---

## **Tools & Frameworks**
| **Category**       | **Tools/Frameworks**                                                                                     | **Notes**                                                                                         |
|--------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Orchestration**  | Kubernetes, Docker Swarm, Nomad                                                                    | Auto-healing, self-healing deployments.                                                            |
| **Service Mesh**   | Istio, Linkerd                                                                                          | Automatic failover routing; mutual TLS.                                                           |
| **Database**       | PostgreSQL (Stream Replication), MongoDB (Replica Sets), Cassandra (Multi-DC)                          | Tunable consistency levels.                                                                      |
| **Caching**        | Redis Cluster, Memcached                                                                               | Failover via sentinels; automatic re-sync.                                                       |
| **API Gateway**    | Kong, AWS API Gateway, Traefik                                                                         | Health checks + dynamic routing.                                                                  |
| **Monitoring**     | Prometheus (Alertmanager), Datadog, New Relic                                                           | Failover event tracking.                                                                          |
| **DNS**            | AWS Route 53 (Latency-Based Routing), Cloudflare (Failover DNS)                                       | Sub-10s failover.                                                                                 |

---

## **Anti-Patterns to Avoid**

| **Anti-Pattern**          | **Why It’s Bad**                                                                                     | **Fix**                                                                                            |
|---------------------------|-------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Single Point of Failure (SPOF)** | Failover depends on one component (e.g., monolithic DB).                                              | Replicate critical components.                                                                   |
| **No Health Checks**      | Failover only detected post-failure.                                                                  | Implement liveness/readiness probes.                                                               |
| **Synchronous Failover for High Latency** | Blocks transactions during failover.                                                                  | Use asynchronous failover; batch writes.                                                          |
| **Manual Failover**       | Human error; slow recovery.                                                                           | Automate with orchestration tools.                                                               |
| **Ignoring Replication Lag** | Backup falls behind; data loss.                                                                        | Monitor lag; scale backup resources.                                                               |
| **Overloading Backup**    | Backup fails during failover.                                                                          | Test failover under load; use warm/cold standby tradeoffs.                                        |
| **No Fallback UI**        | Users see errors during failover.                                                                | Provide degraded-mode UI.                                                                         |

---
**Last Updated:** [MM/DD/YYYY]
**Version:** 1.2