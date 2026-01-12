**[Pattern] Availability Strategies Reference Guide**
*Efficiently design systems to handle varying availability demands while ensuring resilience, scalability, and cost-efficiency.*

---

### **1. Overview**
The **Availability Strategies** pattern addresses trade-offs between system uptime, cost, and flexibility by enabling dynamic adjustments to availability based on workload, budget, or user needs. It is essential for cloud-native and microservices architectures where resources must scale elastically while minimizing downtime and operational overhead.

This pattern defines strategies to:
- **Control availability zones (AZs)** – Distribute workloads across multiple AZs to mitigate failures.
- **Adjust replication factors** – Scale read/write replicas based on traffic patterns.
- **Use caching layers** – Offload read-heavy workloads to reduce core service load.
- **Implement multi-region deployments** – Improve latency and resilience for globally distributed users.
- **Apply auto-scaling policies** – Scale compute/DB resources dynamically based on demand.

Key use cases include:
- **Seasonal traffic spikes** (e.g., Black Friday sales).
- **Cost optimization** (e.g., reducing high-availability overhead during low-usage periods).
- **Regulatory compliance** (e.g., GDPR, HIPAA requiring multi-region data residency).
- **Disaster recovery** (e.g., ransomware mitigation via immutable backups).

---

### **2. Schema Reference**
Below is a structured breakdown of availability strategies, their components, and trade-offs.

| **Strategy**               | **Purpose**                                                                                     | **Components**                                                                                                                                                                                                 | **Trade-offs**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Multi-AZ Deployment**     | Ensures high availability by replicating workloads across AZs.                                  | - **Primary AZ** (active writer).
- **Secondary AZ(s)** (read replicas or failovers).
- **Automatic failover** (e.g., Kubernetes Operator, AWS Multi-AZ RDS).
- **Cross-AZ load balancer** (e.g., Application Load Balancer).
- **Monitoring** (e.g., Prometheus + Alertmanager for AZ health). | - **Cost**: Higher operational complexity.
- **Latency**: Cross-AZ traffic may introduce delays.
- **Data consistency**: Asynchronous replication can cause temporary inconsistencies.                                  |
| **Replication Factor**      | Scales read capacity by adding replicas.                                                        | - **Primary node** (handles writes).
- **N secondary nodes** (e.g., `N=3` for fault tolerance).
- **Replication lag monitoring** (e.g., Kafka lag metrics).                                                                                                                                                | - **Cost**: More replicas = higher storage/network costs.
- **Consistency**: Strong vs. eventual consistency trade-offs (e.g., Raft vs. Paxos).
- **Overhead**: Synchronizing replicas increases CPU/network load.                                                                                                                      |
| **Caching Layer**          | Reduces load on primary databases by caching frequent queries.                                  | - **Cache tier** (e.g., Redis, Memcached).
- **Cache invalidation strategy** (TTL, write-through, write-behind).
- **Cache-aside pattern** (e.g., invalidation on write).
- **Sticky sessions** (if cache is per-user).                                                                                                                                                           | - **Stale data risk**: Inconsistencies if cache is not synced.
- **Memory overhead**: Caching adds latency and requires maintenance.
- **Not suitable for writes**: Write-heavy workloads may bypass cache.                                                                                                                                     |
| **Multi-Region Deployment** | Improves latency and compliance by deploying to multiple geographic regions.                     | - **Regional data centers** (e.g., AWS us-east-1, eu-west-1).
- **Active-active or active-passive sync**.
- **DNS-based routing** (e.g., Cloudflare Workers, AWS Route 53 latency-based routing).
- **Data encryption in transit** (TLS).                                                                                                                                                                | - **Cost**: Higher bandwidth/storage costs for sync.
- **Complexity**: Cross-region failover and conflict resolution.
- **Regulatory hurdles**: Data sovereignty laws may restrict replication.                                                                                                                                   |
| **Auto-Scaling**            | Dynamically adjusts resources based on demand.                                                  | - **Horizontal scaling** (e.g., Kubernetes HPA, AWS Auto Scaling).
- **Vertical scaling** (e.g., DB instance resize).
- **Scaling policies** (CPU/memory thresholds, custom metrics).
- **Warm-up routines** (pre-warming for sudden spikes).                                                                                                                                                     | - **Cold starts**: Delayed scaling can cause latency.
- **Cost spikes**: Over-scaling may incur unnecessary charges.
- **State management**: Stateless services scale easier than stateful ones.                                                                                                                                   |
| **Immutable Backups**       | Protects against corruption/ransomware by maintaining append-only backups.                         | - **Point-in-time snapshots** (e.g., PostgreSQL WAL archiving).
- **Immutable storage** (e.g., AWS S3 Object Lock).
- **Offsite replication** (e.g., cross-region backups).
- **Versioned backups** (e.g., time-based retention).                                                                                                                                                         | - **Storage costs**: Immutable backups grow over time.
- **Recovery time**: Restoring from backups is slower than failover.
- **Performance overhead**: Frequent snapshots may impact write throughput.                                                                                                                                        |

---

### **3. Query Examples**
Below are query patterns to implement or validate availability strategies in your infrastructure.

#### **3.1. Check Multi-AZ Deployment Health**
```sql
-- PostgreSQL (using pg_available_extensions or custom AZ monitoring)
SELECT
    availability_zone,
    COUNT(*) as running_instances,
    pg_is_in_recovery() as recovery_status
FROM pg_stat_replication
GROUP BY availability_zone;
```
**Expected Output**:
```
| availability_zone | running_instances | recovery_status |
|-------------------|-------------------|------------------|
| us-east-1a        | 3                 | false            |
| us-east-1b        | 2                 | true             |  -- Indicates failover in progress
```

#### **3.2. Monitor Replication Lag**
```bash
# Kafka consumer lag (check replication delay)
kafka-consumer-groups --bootstrap-server broker1:9092 --describe --group my-group
```
**Expected Output**:
```
GROUP           TOPIC              PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
my-group        orders             0          10000           10050            50
```

#### **3.3. Validate Cache Hit Ratio**
```sql
-- Redis cache statistics
INFO stats | grep "keyspace_hits"
```
**Expected Output**:
```
keyspace_hits:1000000
keyspace_misses:50000
hit_ratio:99.95%  -- (1000000 / (1000000 + 50000))
```

#### **3.4. Test Multi-Region Failover**
```bash
# AWS CLI: Simulate AZ failure and verify failover
aws rds modify-db-instance --db-instance-identifier my-db --availability-zone us-east-1b --apply-immediately
# Monitor primary region for failover:
kubectl get pods -n my-namespace -o wide | grep "primary"
```
**Expected Output**:
```
my-pod-1   Running   0   5m   us-east-1a   Node1
my-pod-2   Running   0   3m   us-east-1b   Node2  -- Now primary
```

#### **3.5. Scale Resources Based on Load**
```yaml
# Kubernetes Horizontal Pod Autoscaler (HPA) YAML
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: External
    external:
      metric:
        name: requests_per_second
        selector:
          matchLabels:
            app: web-app
      target:
        type: AverageValue
        averageValue: 1000
```

---

### **4. Implementation Checklist**
| **Step**                          | **Action Items**                                                                                                                                                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Assess Requirements**           | - Define SLAs (e.g., 99.95% uptime).
- Identify critical vs. non-critical workloads.
- Budget for multi-AZ/region costs.                                                                                                                                                                         |
| **Choose Strategy**               | - Use **Multi-AZ** for single-region resilience.
- Use **Multi-Region** for global users or compliance.
- Use **Caching** for read-heavy apps.
- Use **Auto-Scaling** for unpredictable traffic.                                                                                                                                                          |
| **Configure Replication**         | - Set up synchronous (strong consistency) or asynchronous (performance) replication.
- Test failover procedures (e.g., chaos engineering).                                                                                                                                                              |
| **Monitor and Alert**             | - Implement APM tools (e.g., Datadog, New Relic).
- Set up alerts for replication lag, cache misses, or AZ failures.                                                                                                                                               |
| **Test Failover**                 | - Simulate AZ/region outages (e.g., AWS Failure Predictor).
- Validate backup restoration.                                                                                                                                                                                 |
| **Optimize Costs**                | - Downscale during off-peak hours.
- Use spot instances for non-critical workloads.                                                                                                                                                                |
| **Document Runbook**              | - Create recovery procedures for each strategy.
- Train DevOps/SRE teams on rollback.                                                                                                                                                                           |

---

### **5. Related Patterns**
To complement **Availability Strategies**, consider integrating these patterns:

| **Pattern**                     | **Purpose**                                                                                     | **When to Use**                                                                                                                                                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Circuit Breaker]**           | Prevents cascading failures by halting requests to failing services.                           | Highly interconnected microservices (e.g., payment processing).                                                                                                                                               |
| **[Bulkhead]**                  | Isolates resource contention (e.g., DB connections) per tenant/region.                         | Multi-tenant SaaS apps with unpredictable spikes.                                                                                                                                                             |
| **[Retry with Backoff]**        | Mitigates transient failures in distributed systems.                                             | APIs calling external services (e.g., payment gateways).                                                                                                                                                     |
| **[Idempotency]**                | Ensures safe retries for duplicate requests (e.g., payments, orders).                          | Event-driven architectures (e.g., Kafka consumers).                                                                                                                                                          |
| **[Chaos Engineering]**          | Proactively tests resilience by injecting failures.                                            | Critical production systems (e.g., financial services).                                                                                                                                                      |
| **[Rate Limiting]**              | Prevents abuse and managed resource exhaustion.                                                | Public APIs or shared infrastructure.                                                                                                                                                                      |
| **[Saga Pattern]**              | Manages distributed transactions via compensating actions.                                       | Microservices with ACID requirements (e.g., order fulfillment).                                                                                                                                            |
| **[Database Sharding]**          | Horizontally partitions data for scalability.                                                   | High-write throughput apps (e.g., IoT sensor data).                                                                                                                                                           |

---
**References**:
- AWS Well-Architected Framework: [Resilience Pillars](https://aws.amazon.com/architecture/well-architected/)
- Kubernetes Best Practices: [Scaling](https://kubernetes.io/docs/concepts/scheduling-eviction/scaling/)
- Designing Data-Intensive Applications (DDIA) – Chapter 6 (Replication).