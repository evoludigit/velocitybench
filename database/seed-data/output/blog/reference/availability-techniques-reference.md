# **[Pattern] Availability Techniques Reference Guide**

---

## **Overview**
The **Availability Techniques** pattern ensures systems remain operational and accessible during demand surges, failures, or planned maintenance. This guide outlines key techniques—including **scaling, redundancy, load balancing, caching, and failover mechanisms**—to maintain high availability (HA) for applications, APIs, and infrastructure. Proper application of these techniques mitigates downtime, optimizes resource usage, and aligns with [N+1 redundancy](https://en.wikipedia.org/wiki/Redundancy_(computing)#N-plus-one_approach) principles.

Availability is measured via **uptime (e.g., 99.99% SLA)**, **latency thresholds**, and **throughput capacity**. Techniques may be combined (e.g., **auto-scaling + caching**) or applied selectively based on system constraints (cost, complexity, and failure recovery time objectives).

---

## **Key Concepts & Schema Reference**

### **Core Availability Techniques**
| **Technique**          | **Definition**                                                                 | **Use Case**                                                                 | **Implementation Options**                                                                 |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Horizontal Scaling** | Adding more instances to distribute load (stateless preferred).                | Web servers, microservices, databases (read replicas).                       | Kubernetes Horizontal Pod Autoscaler, AWS Auto Scaling Groups.                       |
| **Vertical Scaling**   | Upgrading instance resources (CPU, RAM).                                      | Monolithic apps with tight resource coupling.                               | AWS Instance Type Resizing, Azure VM Scale Sets.                                        |
| **Load Balancing**     | Distributing traffic across instances using algorithms (round-robin, least connections). | Fronting web apps, APIs, or database read replicas.                          | Nginx, AWS ALB/ELB, HAProxy, GCP Load Balancer.                                          |
| **Caching**            | Storing frequently accessed data in fast memory (e.g., Redis, Memcached).   | Database queries, API responses, static assets.                             | Layer-level caching (CDN for assets, app cache for DB queries), query caching.           |
| **Redundancy**         | Deploying duplicate systems to tolerate failures (active-active or active-passive). | Critical databases, storage (e.g., S3 cross-region replication).          | Multi-AZ deployments, Kubernetes PodDisruptionBudgets, database replication.           |
| **Failover**           | Automatically switching to a backup system upon failure.                       | Databases (Postgres streaming replication), stateful services.                | Manual failover (e.g., AWS Database Failover) or automated (e.g., Kubernetes StatefulSets). |
| **Graceful Degradation**| Maintaining core functionality while non-critical features are disabled.      | High-traffic APIs during resource constraints.                             | Circuit breakers (e.g., Hystrix), feature flags.                                       |
| **Multi-Region Deployment** | Deploying systems across geographic regions to reduce latency and recover from regional outages. | Global SaaS applications, compliance requirements.                     | AWS Global Accelerator, Kubernetes Federation, GCP Multi-Region Clusters.            |

---

### **Schema Reference: Key Components**
| **Component**               | **Attributes**                                                                 | **Example Values**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Scaling Policy**          | `targetCPUUtilizationPercentage`, `minInstances`, `maxInstances`, `cooldownPeriod` | `{"min": 2, "max": 10, "cpuThreshold": 70, "cooldown": 300}`                   |
| **Load Balancer**           | `algorithm` (round-robin/least-conn), `healthCheckInterval`, `healthyThreshold` | `{"algorithm": "least-conn", "interval": 30, "threshold": 2}`                   |
| **Cache Configuration**     | `ttl` (time-to-live), `maxMemory`, `evictionPolicy`                          | `{"ttl": 3600, "maxMemory": "100mb", "policy": "lru"}`                         |
| **Failover Strategy**       | `primaryRegion`, `backupRegion`, `autofailover`                              | `{"primary": "us-west-2", "backup": "eu-west-1", "autofailover": true}`         |
| **Redundancy Rule**         | `n` (number of replicas), `deploymentType` (active-active/active-passive)    | `{"n": 3, "type": "active-active"}`                                               |

---

## **Implementation Examples**

### **1. Auto-scaling a Web Application**
**Scenario**: A Flask app hosted on AWS ECS needs to handle traffic spikes during a product launch.

**Implementation Steps**:
1. **Configure Auto Scaling Group (ASG)**:
   ```yaml
   # AWS CloudFormation (simplified)
   Resources:
     WebAppASG:
       Type: AWS::AutoScaling::AutoScalingGroup
       Properties:
         LaunchConfigurationName: !Ref WebAppLaunchConfig
         MinSize: 2
         MaxSize: 10
         TargetGroupARNs:
           - !Ref ALBTargetGroup
         ScalingPolicies:
           - PolicyName: CPUScaleOut
             AdjustmentType: ChangeInCapacity
             AutoScalingGroupName: !Ref WebAppASG
             Cooldown: 300
             ScalingAdjustment: 1
   ```
2. **Set Up CloudWatch Metric Alarms** (trigger scaling):
   ```json
   // CloudWatch Alarm for CPU > 70%
   {
     "MetricName": "CPUUtilization",
     "Namespace": "AWS/ECS",
     "Statistic": "Average",
     "Period": 60,
     "EvaluationPeriods": 2,
     "Threshold": 70,
     "ComparisonOperator": "GreaterThanThreshold"
   }
   ```

**Tools**: AWS CLI, CloudFormation, Terraform.

---

### **2. Database Read Replicas with Failover**
**Scenario**: PostgreSQL database needs high availability with manual failover.

**Implementation**:
1. **Set Up Replication**:
   ```sql
   -- Primary database (postgres.conf)
   wal_level = replica
   max_wal_senders = 3
   hot_standby = on

   -- Standby node (recovery.conf)
   standby_mode = 'on'
   primary_conninfo = 'host=primary-db port=5432 user=repl user=postgres password=xxx'
   trigger_file = '/tmp/postgresql.trigger'
   ```
2. **Configure Failover Script** (e.g., `promote_standby.sh`):
   ```bash
   #!/bin/bash
   pg_ctl promote -D /var/lib/postgresql/data
   sed -i 's/primary_conninfo.*/primary_conninfo = ''''/g' /etc/postgresql/recovery.conf
   ```
3. **Orchestrate with Kubernetes StatefulSets**:
   ```yaml
   # Kubernetes StatefulSet with Pod Management Policy=Parallel
   spec:
     podManagementPolicy: Parallel
     replicas: 3
     template:
       spec:
         affinity:
           podAntiAffinity:
             requiredDuringSchedulingIgnoredDuringExecution:
               - labelSelector:
                   matchExpressions:
                     - key: app
                       operator: In
                       values: ["postgres"]
                 topologyKey: "kubernetes.io/hostname"
   ```

**Tools**: `pg_basebackup`, `patroni`, Kubernetes Operators.

---

### **3. Caching API Responses with Redis**
**Scenario**: Reduce database load for a high-traffic REST API.

**Implementation**:
1. **Cache API Responses**:
   ```python
   # Python (FastAPI + Redis example)
   from fastapi import FastAPI
   import redis
   import json

   app = FastAPI()
   cache = redis.Redis(host='redis', port=6379, db=0)

   @app.get("/items/{item_id}")
   async def read_item(item_id: int):
       cache_key = f"item:{item_id}"
       cached_data = cache.get(cache_key)
       if cached_data:
           return json.loads(cached_data)
       # Fetch from DB, then cache
       db_data = fetch_from_db(item_id)
       cache.setex(cache_key, 300, json.dumps(db_data))  # Cache for 5 mins
       return db_data
   ```
2. **Redis Cluster Setup** (for high availability):
   ```bash
   redis-cli --cluster create \
     redis1:6379 redis2:6379 redis3:6379 \
     --cluster-replicas 1
   ```

**Tools**: Redis, Python `redis-py`, or Node.js `ioredis`.

---

### **4. Multi-Region Deployments with Kubernetes**
**Scenario**: Deploy a global application with low-latency access.

**Implementation**:
1. **Configure Clusters**:
   ```yaml
   # terraform-aws-modules/eks/aws/variables.tf
   variables {
     cluster_name = "global-app"
     clusters = {
       us-west-2 = { name = "us-west-2-cluster" }
       eu-west-1 = { name = "eu-west-1-cluster" }
     }
   }
   ```
2. **Use GCP Global Load Balancer**:
   ```yaml
   # Kubernetes Ingress (GKE)
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     annotations:
       networking.gke.io/managed-certificates: "global-cert"
       networking.gke.io/v1beta1.FrontendConfig: "global-fc"
   spec:
     backend:
       serviceName: my-service
       servicePort: 80
   ```
3. **Service Mesh (Istio) for Traffic Routing**:
   ```yaml
   # Istio VirtualService (traffic split)
   apiVersion: networking.istio.io/v1alpha3
   kind: VirtualService
   metadata:
     name: my-service
   spec:
     hosts:
     - "my-app.example.com"
     http:
     - route:
       - destination:
           host: my-service.us-west-2.svc.cluster.local
           subset: v1
         weight: 60
       - destination:
           host: my-service.eu-west-1.svc.cluster.local
           subset: v1
         weight: 40
   ```

**Tools**: Kubernetes Federation, AWS Global Accelerator, Istio.

---

## **Query Examples**

### **1. Check Auto Scaling Group Events (AWS CLI)**
```bash
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name "WebAppASG" \
  --output text --query "Activities[?ActivityType=='AddInstanceInService'].{Time:Timestamp,Instance:InstanceId}"
```

### **2. Validate Redis Cache Hit/Miss Ratio (Redis CLI)**
```bash
redis-cli --stat
# Look for:
# keyspace_hits:12345 keyspace_misses:456
# Hit ratio: (keyspace_hits / (keyspace_hits + keyspace_misses)) * 100
```

### **3. Query Kubernetes Pod Disruption Budgets (Kubectl)**
```bash
kubectl get poddisruptionbudget -o yaml
# Example output:
# apiVersion: policy/v1
# metadata:
#   name: postgres-pdb
# spec:
#   minAvailable: 2  # Ensures 2 PostgreSQL pods always run
#   selector:
#     matchLabels:
#       app: postgres
```

---

## **Related Patterns**
To complement **Availability Techniques**, consider integrating the following patterns:

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.ioPatterns/circuit-breaker.html)** | Prevents cascading failures by stopping requests to a failing service.       | Microservices communicating over networks (e.g., Hystrix, Resilience4j).       |
| **[Bulkhead](https://microservices.ioPatterns/bulkhead.html)**               | Limits concurrent executions to prevent resource exhaustion.               | CPU-intensive tasks (e.g., batch processing).                                   |
| **[Retry with Backoff](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)** | Retries failed operations with exponential backoff.                       | Idempotent APIs (e.g., database writes).                                       |
| **[ lazy initialization](https://martinfowler.com/eaaCatalog/lazyInit.html)** | Delays initialization of expensive resources until needed.                 | Startup-heavy services (e.g., caching layers).                                |
| **[Rate Limiting](https://learn.microsoft.com/en-us/azure/architecture/patterns/rate-limiting)** | Controls request volume to prevent abuse or overload.                     | Public APIs, payment systems.                                                  |
| **[Idempotency Key](https://microservices.ioPatterns/idempotency-key.html)** | Ensures duplicate requests don’t cause side effects.                      | Payment processing, order management.                                         |

---

## **Best Practices**
1. **Monitor proactively**: Use tools like **Prometheus + Grafana** or **AWS CloudWatch** to track:
   - Scaling events.
   - Cache hit ratios.
   - Failover times.
2. **Test failure scenarios**: Simulate region outages (Chaos Engineering with **Gremlin** or **Chaos Mesh**).
3. **Document runbooks**: Create step-by-step guides for manual failover (e.g., [AWS Failover Runbook](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.GloballyDistributedApplications.html)).
4. **Cost vs. availability tradeoff**: Balance redundancy (e.g., 3-AZ deployments) with budget constraints.
5. **Statelessness**: Prefer stateless architectures for easier scaling (e.g., use sessions in a database or Redis).

---
**References**:
- [AWS Well-Architected High Availability Pillar](https://aws.amazon.com/architecture/well-architected/)
- [Kubernetes Best Practices for High Availability](https://kubernetes.io/docs/concepts/architecture/high-availability/)
- [Redis High Availability](https://redis.io/topics/high-availability)