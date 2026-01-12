**[Pattern] Availability Approaches Reference Guide**
*Ensure resilient system performance and efficient resource utilization under varying workloads and failure conditions.*

---

### **1. Overview**
The **Availability Approaches** pattern provides strategies to design, implement, or enhance systems to maximize uptime, recover from failures, and handle load spikes. Availability is a critical non-functional requirement (NFR) for systems spanning from user-facing applications to distributed microservices. This pattern categorizes availability techniques into **preventive**, **reactive**, and **adaptive** approaches, balancing cost, complexity, and business impact.

Key considerations include:
- **Redundancy**: Deploying duplicate components (e.g., failover instances, data replicas).
- **Resilience**: Graceful degradation under partial failures (e.g., circuit breakers, retries).
- **Scalability**: Dynamically adjusting resources based on demand (e.g., auto-scaling, load balancing).
- **Monitoring & Recovery**: Proactively detecting and mitigating issues (e.g., health checks, automated rollbacks).

Use this guide to evaluate trade-offs for your system’s specific SLOs (Service Level Objectives), latency requirements, and budget constraints.

---

### **2. Schema Reference**
Below is a structured breakdown of availability approaches, grouped by strategy. Use this as a decision matrix when designing or assessing systems.

| **Category**       | **Approach**               | **Description**                                                                                     | **Pros**                                                                                     | **Cons**                                                                                     | **Use Case Examples**                                                                 |
|--------------------|----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Preventive**     | **Redundancy (N+1)**       | Deploy *N* active instances + *1* backup (e.g., database replicas, load balancer backups).         | High availability; seamless failover.                                                      | Higher operational cost; potential data inconsistencies.                                | Global distributed databases (e.g., multi-region PostgreSQL clusters).                     |
|                    | **Multi-Region Deployment** | Deploy critical services across geographically dispersed regions.                                   | Mitigates regional outages (e.g., cloud provider failures, natural disasters).               | Latency spikes for cross-region traffic; higher data synchronization costs.            | E-commerce platforms (e.g., Amazon, Walmart).                                               |
|                    | **Caching (Layered)**      | Cache frequent/expensive queries (e.g., Redis, CDN) to reduce backend load.                           | Improves response time; reduces database queries.                                          | Stale data risk; cache invalidation overhead.                                               | High-traffic APIs (e.g., Twitter, Slack).                                                    |
| **Reactive**       | **Circuit Breaker**        | Halts requests to a failing dependency after *N* consecutive failures (e.g., Hystrix, Resilience4j). | Prevents cascading failures; improves system stability.                                     | Introduces latency during degradation.                                                     | Microservices with third-party APIs (e.g., payment gateways).                                |
|                    | **Retry with Backoff**     | Retry failed requests with exponential backoff (e.g., AWS SDK retries).                             | Handles transient errors (e.g., network blips).                                            | Risk of retry storms; possible data corruption if not idempotent.                          | Batch processing pipelines (e.g., ETL jobs).                                                 |
|                    | **Bulkheads**              | Isolate components to prevent a single failure from impacting others (e.g., thread pools).           | Limits blast radius of failures.                                                            | Complexity in resource management.                                                          | High-throughput systems (e.g., trading platforms).                                          |
| **Adaptive**       | **Auto-Scaling**           | Dynamically adjusts resource allocation (e.g., AWS Auto Scaling, Kubernetes HPA).                  | Scales with demand; cost-efficient for variable workloads.                                  | Cold starts; scaling delay overhead.                                                        | Web applications with unpredictable traffic (e.g., Black Friday sales).                      |
|                    | **Load Balancing**         | Distributes traffic across instances (e.g., round-robin, least connections).                         | Even resource utilization; improved fault tolerance.                                        | Single point of failure (if load balancer fails).                                           | Global scale APIs (e.g., Netflix, Uber).                                                     |
|                    | **Chaos Engineering**      | Proactively injects failures to test resilience (e.g., Gremlin, Chaos Monkey).                     | Uncovers weaknesses; improves operational confidence.                                      | Requires discipline; potential disruption if not controlled.                                | Large-scale distributed systems (e.g., Netflix, Stripe).                                    |
| **Hybrid**         | **Multi-Channel Failover** | Uses a secondary channel (e.g., backup database, fallback service) if primary fails.               | High availability with minimal downtime.                                                   | Complexity in synchronization.                                                              | Critical infrastructure (e.g., banking systems).                                           |
|                    | **Blue-Green Deployment**  | Instantly switches traffic from "Blue" (active) to "Green" (new version) environment.               | Zero-downtime deployments; quick rollback.                                                  | Requires double resources during deployment.                                               | High-availability web apps (e.g., LinkedIn, Airbnb).                                        |
|                    | **Database Sharding**      | Splits data across multiple servers (e.g., horizontal partitioning).                                 | Scales read/write capacity; improves performance.                                           | Complex join operations; requires application changes.                                      | Social media platforms (e.g., Facebook, Reddit).                                            |

---

### **3. Query Examples**
Below are example queries and configurations for common scenarios implementing availability approaches.

#### **3.1. Auto-Scaling (AWS CLI)**
```bash
# Enable Auto Scaling for an EC2 instance
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name "my-app-asg" \
  --launch-template LaunchTemplateName=my-launch-template \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2 \
  --vpc-zone-identifier "subnet-1234,subnet-5678"
```

#### **3.2. Circuit Breaker (Python with Resilience4j)**
```python
from resilience4j.circuitbreaker import CircuitBreakerConfig

config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50)  # Fail after 50% failures
    .waitDurationInOpenState(Duration.ofSeconds(10))
    .slidingWindowSize(10)      # Last 10 calls
    .permittedNumberOfCallsInHalfOpenState(2)
    .recordExceptions(
        TimeoutException.class,
        SocketTimeoutException.class
    )
    .build()

circuitBreaker = CircuitBreaker.of("my-service", config);
```

#### **3.3. Redis Caching (Node.js)**
```javascript
const redis = require("redis");
const client = redis.createClient();

client.on("error", (err) => console.log("Redis Client Error", err));

// Cache a value for 1 hour
async function setWithTTL(key, value, ttl) {
  await client.set(key, value, "EX", ttl);
}

// Get cached value
async function get(key) {
  return await client.get(key);
}
```

#### **3.4. Multi-Region Failover (Terraform)**
```hcl
resource "aws_db_instance" "primary" {
  identifier         = "primary-db"
  engine             = "postgres"
  instance_class     = "db.t3.medium"
  allocated_storage  = 20
  region             = "us-east-1"
}

resource "aws_db_instance" "backup" {
  identifier         = "backup-db"
  engine             = "postgres"
  instance_class     = "db.t3.medium"
  allocated_storage  = 20
  region             = "eu-west-1"
  # Configure read replica or logical replication for failover
}
```

#### **3.5. Chaos Engineering (Gremlin Command)**
```bash
# Inject latency on a target endpoint (1000ms delay)
gremlin inject-latency --target http://api.example.com/orders \
  --latency 1000ms \
  --concurrency 50 \
  --duration 1m
```

---

### **4. Implementation Considerations**
#### **4.1. Trade-Offs**
| **Decision Point**               | **Option A**                          | **Option B**                          | **Recommendation**                          |
|----------------------------------|---------------------------------------|---------------------------------------|---------------------------------------------|
| **Cost vs. Availability**        | Redundancy (N+1)                      | Auto-scaling                          | Use **auto-scaling** for variable workloads; **N+1** for critical systems. |
| **Latency vs. Consistency**      | Strong consistency (e.g., synchronous replication) | Eventual consistency (e.g., Kafka) | Prefer **eventual consistency** for global systems; use **strong consistency** for financial data. |
| **Complexity vs. Resilience**    | Circuit breakers + retries           | Bulkheads                            | Combine both for **defense in depth**.       |
| **Deployments**                  | Blue-Green                          | Canary Releases                       | Use **Blue-Green** for zero-downtime; **Canary** for gradual rollouts. |

#### **4.2. Anti-Patterns to Avoid**
1. **Over-Redundancy**: Deploying *N* copies without measuring cost vs. gain (e.g., 10 database replicas for a low-traffic app).
2. **Ignoring Monitoring**: Assuming availability without metrics (e.g., no uptime alerts, no latency tracking).
3. **Brittle Retries**: Retrying non-idempotent operations (e.g., `DELETE` requests) without deduplication.
4. **Chaos Without Goals**: Running chaos experiments without defining success criteria (e.g., "break anything").
5. **Static Scaling**: Using fixed scalers instead of dynamic ones (e.g., scaling to 100 instances at 3 AM).

---

### **5. Related Patterns**
Consume these patterns in conjunction with **Availability Approaches** to build robust systems:

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)** | Separates read and write operations for scalability and performance.          | High-scale read-heavy systems (e.g., analytics dashboards).                     |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manages distributed transactions via compensating actions.                   | Microservices with ACID requirements.                                           |
| **[Rate Limiting](https://en.wikipedia.org/wiki/Token_bucket)** | Controls request volume to prevent abuse or overload.                        | Public APIs, payment gateways.                                                   |
| **[Idempotency](https://martinfowler.com/articles/patterns-of-distributed-systems/idempotency.html)** | Ensures repeated requests have the same effect as a single request.           | Payment processing, order management.                                           |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Stores state changes as a sequence of events.                                | Audit trails, time-sensitive systems.                                           |
| **[Chaos Mesh](https://chaos-mesh.org/)**                     | Open-source chaos engineering platform for Kubernetes.                         | Kubernetes-based distributed systems.                                           |

---

### **6. Further Reading**
- **[AWS Well-Architected Framework: Reliability](https://aws.amazon.com/architecture/well-architected/)**
- **[Google SRE Book (Chapter 5: Measurement)](https://sre.google/sre-book/table-of-contents/)**
- **[Resilience Patterns (Resilience4j Documentation)](https://resilience4j.readme.io/docs)**
- **[Chaos Engineering Handbook](https://www.oreilly.com/library/view/chaos-engineering-handbook/9781492049461/)**