**[Pattern] Availability Optimization Reference Guide**

---

### **Overview**
The **Availability Optimization** pattern enhances application resilience by proactively managing system uptime, fault tolerance, and resource allocation. This pattern ensures minimal downtime, reduces latency, and mitigates disruptions during peak loads or failures. It combines **auto-scaling, regional distribution, caching, and failover mechanisms** to maintain high availability. Key use cases include:
- **Global applications** (e.g., SaaS platforms requiring 99.99% uptime)
- **High-traffic services** (e.g., e-commerce during Black Friday)
- **Critical infrastructure** (e.g., healthcare or financial systems)
- **Multi-tenancy architectures** (e.g., cloud services with varying workloads)

---

### **Key Concepts**
Below are foundational components of the Availability Optimization pattern:

| **Concept**               | **Description**                                                                                                                                                                                                 | **Key Metrics**                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **Multi-Region Deployment** | Distributes infrastructure across geographic regions to reduce latency and avoid localized failures. Uses **active-active** or **active-passive** configurations.                                                   | RTO (Recovery Time Objective)        |
| **Auto-Scaling**          | Dynamically adjusts compute/network resources based on demand (e.g., Kubernetes Horizontal Pod Autoscaler, AWS Auto Scaling Groups).                                                                          | CPU Utilization, Request Latency    |
| **Caching Layers**        | Deploys **CDNs, in-memory caches (Redis), or edge caching** to reduce backend load and improve response times.                                                                                                  | Cache Hit Ratio, TTL Efficiency      |
| **Load Balancing**        | Distributes traffic across instances using **round-robin, least connections, or geographic routing** (e.g., AWS ALB, NGINX).                                                                        | Traffic Distribution, Session Persistence |
| **Database Replication**  | Uses **read replicas, sharding, or multi-master setups** to ensure data availability during write failures.                                                                                                   | Replica Lag, Write/Read Throughput   |
| **Circuit Breakers**      | Prevents cascading failures by halting requests to faulty services (e.g., Hystrix, Resilience4j).                                                                                                           | Failure Rate, Recovery Time           |
| **Chaos Engineering**     | Proactively tests resilience by injecting failures (e.g., **Gremlin, Chaos Monkey**).                                                                                                                         | Failure Injection Success Rate       |
| **GeoDNS**                | Routes users to the nearest healthy region based on DNS latency checks.                                                                                                                                           | Geographical Latency, Failover Speed |

---

### **Schema Reference**
Below is a reference schema for configuring Availability Optimization in a microservices architecture:

| **Component**            | **Attributes**                                                                                     | **Options/Example Values**                                                                                     |
|--------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Deployment Strategy**  | RegionCount, FailureDomain, ReplicaCount                                                      | `RegionCount=3`, `FailureDomain=us-west-2a,us-east-1a,eu-central-1a`                                         |
| **Auto-Scaling**         | MinInstances, MaxInstances, ScaleOutPolicy, ScaleInPolicy                                         | `MinInstances=2`, `MaxInstances=20`, `ScaleOutPolicy=Cpu>70%`                                               |
| **Caching Layer**        | CacheType, TTL, MaxMemory                                                                         | `CacheType=Redis`, `TTL=3600s`, `MaxMemory=5GB`                                                              |
| **Load Balancer**        | Algorithm, HealthCheckInterval, SessionSticky                                                    | `Algorithm=LeastConnections`, `HealthCheckInterval=30s`, `SessionSticky=false`                             |
| **Database Replication** | ReplicationFactor, ReadReplicaCount, ShardCount                                                  | `ReplicationFactor=3`, `ReadReplicaCount=2`, `ShardCount=4`                                                  |
| **Circuit Breaker**      | Timeout, ErrorThreshold, HalfOpenCount                                                          | `Timeout=5s`, `ErrorThreshold=50%`, `HalfOpenCount=3`                                                        |
| **Chaos Testing**        | TestFrequency, FailurePatterns                                                                   | `TestFrequency=daily`, `FailurePatterns=NetworkLatency Spike (5s)`                                          |
| **GeoDNS**               | FailoverThreshold, PriorityWeights                                                              | `FailoverThreshold=200ms`, `PriorityWeights=us-west-2:0.6,eu-central-1:0.4`                                 |

---

### **Implementation Details**
#### **1. Multi-Region Deployment**
- **How it works**: Deploy identical instances across regions with **asynchronous replication** for stateful services (e.g., databases) or **synchronous for critical data**.
- **Tools**: AWS Global Accelerator, Google Cloud Load Balancing, Kubernetes Federation.
- **Example**:
  ```yaml
  # Kubernetes Multi-Region Deployment Example
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: app-frontend
    labels:
      app: frontend
  spec:
    replicas: 3
    template:
      spec:
        topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: "topology.kubernetes.io/zone"
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: frontend
  ```

#### **2. Auto-Scaling**
- **Vertical Scaling**: Increase instance size (manual or scheduled).
- **Horizontal Scaling**: Add/remove pods/containers (e.g., Kubernetes HPA).
- **Example Query (AWS CLI)**:
  ```bash
  # Scale out based on CPU usage
  aws application-autoscaling register-scalable-target \
    --service-namespace "ec2" \
    --resource-id "auto-scaling-group/asg-12345678" \
    --scalable-dimension "ec2:auto-scaling-group:DesiredCapacity" \
    --min-capacity 2 \
    --max-capacity 20

  # Configure scaling policy
  aws application-autoscaling put-scaling-policy \
    --policy-name "CPUScaleOut" \
    --service-namespace "ec2" \
    --resource-id "auto-scaling-group/asg-12345678" \
    --scalable-dimension "ec2:auto-scaling-group:DesiredCapacity" \
    --policy-type "TargetTrackingScaling" \
    --target-tracking-scaling-policy-configuration '{
      "TargetValue": 70.0,
      "ScaleInCooldown": 300,
      "ScaleOutCooldown": 60,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ASGAverageCPUUtilization"
      }
    }'
  ```

#### **3. Caching Strategies**
- **Edge Caching**: Use **Cloudflare, Akamai, or Fastly** to cache static assets.
- **In-Memory Caching**: Deploy **Redis/Memcached** clusters.
- **Database Query Caching**: Cache frequent SQL queries (e.g., PostgreSQL `pg_cache`).
- **Example (Redis with Node.js)**:
  ```javascript
  const redis = require("redis");
  const client = redis.createClient();

  async function getUserCache(userId) {
    const data = await client.get(`user:${userId}`);
    if (data) return JSON.parse(data);
    // Fallback to DB if cache miss
    const dbData = await db.query("SELECT * FROM users WHERE id = ?", [userId]);
    client.set(`user:${userId}`, JSON.stringify(dbData), "EX", 3600); // Cache for 1h
    return dbData;
  }
  ```

#### **4. Load Balancing**
- **Global Load Balancers**: Route users to the nearest healthy region.
- **Local Load Balancers**: Distribute traffic within a region (e.g., AWS ALB, NGINX).
- **Example (Terraform for AWS ALB)**:
  ```hcl
  resource "aws_lb" "frontend" {
    name               = "frontend-alb"
    internal           = false
    load_balancer_type = "application"
    security_groups    = [aws_security_group.alb.id]
    subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]

    enable_deletion_protection = false
  }

  resource "aws_lb_target_group" "app" {
    name     = "app-target-group"
    port     = 80
    protocol = "HTTP"
    vpc_id   = aws_vpc.main.id
  }

  resource "aws_lb_listener" "frontend" {
    load_balancer_arn = aws_lb.frontend.arn
    port              = 80
    protocol          = "HTTP"

    default_action {
      type             = "forward"
      target_group_arn = aws_lb_target_group.app.arn
    }
  }
  ```

#### **5. Database Replication**
- **Read Replicas**: Offload read queries (e.g., PostgreSQL `pg_basebackup`).
- **Sharding**: Split data horizontally (e.g., MongoDB sharding, Vitess).
- **Example (PostgreSQL Read Replica)**:
  ```sql
  -- Configure primary server (postgresql.conf)
  wal_level = replica
  max_wal_senders = 10
  hot_standby = on

  -- Replica setup (on replica server)
  recovery_target_timeline = 'latest'
  primary_conninfo = 'host=primary-server port=5432 user=replicator password=secret'
  ```

#### **6. Circuit Breakers**
- **Implementation**: Use libraries like **Resilience4j** (Java) or **Hystrix** (deprecated but still used).
- **Example (Resilience4j)**:
  ```java
  CircuitBreakerConfig config = CircuitBreakerConfig.custom()
      .failureRateThreshold(50)
      .waitDurationInOpenState(Duration.ofSeconds(5))
      .slidingWindowSize(2)
      .permittedNumberOfCallsInHalfOpenState(3)
      .build();

  CircuitBreaker circuitBreaker = CircuitBreaker.of("example", config);

  // Execute with fallback
  Supplier<String> service = CircuitBreaker.decorateSupplier(
      circuitBreaker,
      () -> callExternalService()
  ).onFailure(fail -> "Fallback response");

  String result = service.get();
  ```

#### **7. Chaos Engineering**
- **Testing Failures**:
  - **Network Latency**: Simulate 100ms delay between regions.
  - **Instance Kill**: Randomly terminate pods (e.g., Chaos Mesh).
- **Example (Chaos Mesh)**:
  ```yaml
  apiVersion: chaos-mesh.org/v1alpha1
  kind: NetworkChaos
  metadata:
    name: network-latency
  spec:
    action: delay
    mode: one
    selector:
      namespaces:
        - default
      labelSelectors:
        app: frontend
    delay:
      latency: "100ms"
      jitter: "50ms"
  ```

#### **8. GeoDNS**
- **Providers**: AWS Route 53, Cloudflare, Google Cloud DNS.
- **Example (AWS Route 53 Latency-Based Routing)**:
  ```json
  {
    "Comment": "Route traffic to nearest region",
    "HostedZoneId": "Z1234567890",
    "RecordSets": [
      {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 300,
        "SetIdentifier": "latency-us",
        "GeoLocation": {
          "ContinentCode": "NA"
        },
        "AliasTarget": {
          "HostedZoneId": "Z1111111111",
          "DNSName": "d1111111111.us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": false
        }
      },
      {
        "Name": "app.example.com",
        "Type": "A",
        "TTL": 300,
        "SetIdentifier": "latency-eu",
        "GeoLocation": {
          "ContinentCode": "EU"
        },
        "AliasTarget": {
          "HostedZoneId": "Z2222222222",
          "DNSName": "d2222222222.eu-west-1.elb.amazonaws.com",
          "EvaluateTargetHealth": false
        }
      }
    ]
  }
  ```

---

### **Query Examples**
#### **1. Check Auto-Scaling Group Health (AWS CLI)**
```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "my-asg" \
  --query "AutoScalingGroups[0].Instances[?HealthStatus=='healthy'].InstanceId"
```

#### **2. Monitor Redis Cache Hit Ratio**
```bash
redis-cli --stat | grep "keyspace_hits" "keyspace_misses" | awk '{print "Hit Ratio: " ($1/($1+$2))*100 "%"}'
```

#### **3. Test Load Balancer Health (kubectl)**
```bash
kubectl get endpoints frontend-service -o yaml | grep "endpoints:"
kubectl describe service frontend-service | grep "sessionaffinity"
```

#### **4. Query PostgreSQL Replica Lag**
```sql
SELECT
  pg_stat_replication.pid,
  pg_stat_replication.usename,
  pg_stat_replication.state,
  EXTRACT(EPOCH FROM (now() - pg_stat_replication.replay_lag)) AS lag_seconds
FROM pg_stat_replication;
```

#### **5. Check Circuit Breaker Metrics (Resilience4j)**
```bash
# Prometheus query for circuit breaker failures
sum(rate(resilience4j_circuitbreaker_calls_total{name="example"}[1m]))
by (state) > 0
```

---

### **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|---------------------------------------|---------------------------------------------------------------------------------------------------|
| **Thundering Herd Problem**           | Use **queue-based scaling** (e.g., AWS SQS) to limit concurrent requests during failover.          |
| **Cache Invalidation Stampedes**      | Implement **TTL-based invalidation** or **event-driven updates** (e.g., Redis Pub/Sub).           |
| **Over-Provisioning Costs**           | Set **cost-based scaling policies** (e.g., AWS Cost Explorer + Auto Scaling).                     |
| **Cross-Region Latency**              | Use **synchronous replication** for critical data (e.g., PostgreSQL streaming replication).       |
| **Chaos Testing Overload**            | **Rate-limit chaos experiments** (e.g., Chaos Mesh `podChaos` with `delete` action).               |

---

### **Related Patterns**
1. **[Resilience Pattern](https://www.enterpriseintegrationpatterns.com/patterns/data/Resilience.html)**
   - Focuses on graceful degradation under failure (e.g., circuit breakers, retries).
   - *Use case*: Combine with Availability Optimization for **fault-tolerant microservices**.

2. **[CQRS Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)**
   - Separates read/write operations to optimize performance.
   - *Use case*: Pair with **read replicas** for high-availability reads.

3. **[Saga Pattern](https://microservices.io/patterns/data/saga.html)**
   - Manages distributed transactions across services.
   - *Use case*: Ensure **atomicity** during multi-region transactions.

4. **[Multi-Cluster Kubernetes](https://kubernetes.io/docs/concepts/cluster-administration/cluster-management/)**
   - Deploys Kubernetes clusters across regions for high availability.
   - *Use case*: Use with **Federation V2** for global workloads.

5. **[Event-Driven Architecture](https://www.event-driven.org/)**
   - Uses events (e.g., Kafka, NATS) to decouple services.
   - *Use case*: Enable **asynchronous failover** and scaling.

---
### **Further Reading**
- **[AWS Well-Architected Framework: Reliability](https://aws.amazon.com/architecture/well-architected/)**
- **[Google SRE Book: Site Reliability Engineering](https://sre.google/sre-book/)**
- **[Chaos Engineering: How Netflix Stays in Sync](https://netflixtechblog.com/chaos-engineering-at-netflix-df0d370e5acy)**
- **[Kubernetes Best Practices for High Availability](https://kubernetes.io/docs/concepts/architecture/high-availability/)**