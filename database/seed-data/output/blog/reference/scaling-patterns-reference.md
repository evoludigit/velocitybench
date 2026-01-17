# **[Scaling Patterns] Reference Guide**

## **Overview**
Scaling Patterns define architectural strategies to efficiently handle increased load, data volume, or user demand by distributing resources, optimizing performance, or abstracting complexity. These patterns are categorized into **horizontal scaling** (adding more machines), **vertical scaling** (upgrading resources), **database scaling** (managing data distribution), and **systemic optimizations** (caching, load balancing, and microservices decomposition). Each pattern balances cost, maintainability, and reliability while addressing specific bottlenecks—such as I/O latency, compute saturation, or data consistency. This guide provides structured implementations, schema references, and query examples to apply these patterns in cloud, on-premises, or hybrid environments.

---

## **Pattern Categories & Schema Reference**

| **Pattern**               | **Purpose**                                                                 | **Key Components**                                                                                     | **When to Apply**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Horizontal Scaling**     | Distribute load across multiple identical instances.                          | Load balancer, auto-scaling groups, session affinity policies.                                        | High-traffic web apps, stateless services, or workloads requiring fault tolerance.                   |
| **Database Sharding**      | Split database into smaller, manageable chunks.                              | Shard key (e.g., user_id), shard routers, replica sets.                                              | Read-heavy apps (e.g., social media), or when single DB nodes can’t handle query load.               |
| **Read Replicas**          | Offload read queries from primary DB.                                       | Primary DB + replica nodes, synchronous/asynchronous replication.                                      | Apps with 80%+ read-heavy workloads (e.g., analytics dashboards).                                     |
| **Caching (CDN + Local)**  | Store frequently accessed data in faster storage.                           | Redis/Memcached, CDN edge caches (e.g., CloudFront), cache invalidation strategies.                    | High-latency APIs, static content delivery, or frequent read-heavy operations.                        |
| **Microservices**          | Decompose monolith into independent services.                                | Service mesh (Istio), API gateways, event-driven communication (Kafka).                             | Polyglot persistence, team autonomy, or dynamic scaling per service.                                |
| **Queue-Based Async**      | Decouple producers/consumers using queues.                                   | Message brokers (RabbitMQ, AWS SQS), consumer groups, retries/exponential backoff.                     | Background jobs (e.g., notifications), event sourcing, or batch processing.                          |
| **Database Caching (Proxy)**| Cache query results to reduce DB load.                                      | Proxy layer (e.g., ProxySQL), cache invalidation on writes.                                          | OLTP systems with repetitive queries (e.g., e-commerce product lookups).                             |
| **Partitioning**           | Split data horizontally/vertically.                                        | Range-based (e.g., time-series), hash-based partitioning, partitioning keys.                           | Time-series data (e.g., logs), or datasets with natural groupings.                                   |
| **Load Balancing**         | Distribute traffic across servers.                                          | Round-robin, least connections, weighted LB (Nginx, AWS ALB).                                        | Global apps, multi-region deployments, or handling DDoS attacks.                                      |
| **Vertical Scaling**       | Upgrade single machine resources.                                           | Instance resizing (e.g., AWS m5.4xlarge), right-sizing (CPU/RAM).                                    | Early-stage apps with predictable, moderate scaling needs.                                          |
| **Edge Computing**         | Process data closer to users (e.g., IoT, gaming).                          | Edge servers, serverless functions (AWS Lambda@Edge), low-latency protocols.                         | IoT devices, live streaming, or low-latency trading systems.                                          |
| **Session Affinity**       | Persist user sessions across requests.                                      | Stickiness policies (LB), sticky sessions via cookies/JWT.                                          | Stateful apps (e.g., shopping carts) in horizontally scaled environments.                            |

---

## **Implementation Details**

### **1. Horizontal Scaling**
**Goal:** Handle traffic spikes by adding machines.
**Key Steps:**
1. **Stateless Design:** Store sessions/user data in DB/cache (e.g., Redis).
2. **Load Balancer:** Deploy a balancer (e.g., Nginx, AWS ALB) to distribute requests.
3. **Auto-Scaling:** Configure auto-scaling policies (CPU > 70% → scale out).
4. **Health Checks:** Ensure failed instances are replaced quickly.

**Example Schema (AWS):**
```plaintext
Auto Scaling Group (ASG) →
   → EC2 Instances (t3.medium)
   → ELB (Application Load Balancer)
   → Target Group (check /health)
```

**Query Example (Terraform):**
```hcl
resource "aws_autoscaling_group" "web_servers" {
  launch_template {
    image_id      = "ami-123456"
    instance_type = "t3.medium"
  }
  min_size         = 2
  max_size         = 10
  desired_capacity = 3
  vpc_zone_identifier = ["subnet-12345", "subnet-67890"]
}
```

---

### **2. Database Sharding**
**Goal:** Distribute DB load by splitting data.
**Key Steps:**
1. **Choose Shard Key:** Select a high-cardinality column (e.g., `user_id`).
2. **Router:** Implement a shard router (e.g., Vitess, ProxySQL).
3. **Replication:** Use read replicas per shard for scaling reads.

**Example Schema:**
```plaintext
Primary DB (Shard Router) →
   → Shard 1 (users 1-1M)
   → Shard 2 (users 1M-2M)
   → ...
```

**Query Example (Shard Key Selection):**
```sql
-- Determine optimal shard key distribution
SELECT COUNT(DISTINCT user_id), COUNT(*)
FROM users
GROUP BY user_id;
```

**Implementation (Vitess):**
```plaintext
schema "Users" {
  table "users" {
    key: "user_id" (shard_key: "user_id")
    columns: [
      {"name": "name", "type": "STRING"},
      {"name": "email", "type": "STRING"}
    ]
  }
}
```

---

### **3. Caching (CDN + Local)**
**Goal:** Reduce latency by caching responses.
**Key Steps:**
1. **Layered Cache:**
   - **Edge Cache:** CDN (e.g., CloudFront) for static content.
   - **Local Cache:** Redis/Memcached for dynamic data (e.g., API responses).
2. **Cache Invalidation:** Use timestamp-based or event-driven invalidation.

**Example Schema:**
```plaintext
User Request →
   → CDN Cache (TTL: 1h) →
   → Local Cache (Redis, TTL: 5m) →
   → Database (Fallthrough)
```

**Query Example (Redis Cache Key):**
```plaintext
GET "user:123:profile"  # Returns cached JSON
SETEX "user:123:profile" 300 '{"name":"Alice"}'  # TTL=5m
```

**Implementation (CloudFront + Lambda@Edge):**
```plaintext
{
  "CacheBehavior": {
    "TargetOriginId": "s3-origin",
    "PathPattern": "*.jpg",
    "TTL": 3600,
    "LambdaFunctionAssociations": [
      { "LambdaFunctionARN": "arn:aws:lambda:..." }
    ]
  }
}
```

---

### **4. Microservices**
**Goal:** Isolate components for independent scaling.
**Key Steps:**
1. **Decompose:** Split by domain (e.g., `auth-service`, `order-service`).
2. **Service Mesh:** Use Istio/Kong for traffic management.
3. **API Gateway:** Route requests via Kong/Nginx.

**Example Schema:**
```plaintext
Client →
   → API Gateway →
   → Auth Service (K8s Pods) →
   → Order Service (K8s Pods)
```

**Query Example (Docker Compose):**
```yaml
version: "3"
services:
  auth:
    image: auth-service:latest
    ports: ["8080:8080"]
  order:
    image: order-service:latest
    depends_on: ["auth"]
```

---

## **Query Examples by Pattern**

| **Pattern**          | **Example Use Case**                          | **Query/Configuration Snippet**                                                                 |
|----------------------|-----------------------------------------------|------------------------------------------------------------------------------------------------|
| **Auto-Scaling**     | Scale out during Black Friday.                | `aws autoscaling update-policy --group-name web --policy-name "ScaleOnCPU" --scaling-adjustment +3` |
| **Sharding**         | Split users by region.                       | `CREATE TABLE users_shard1 (id INT PRIMARY KEY, ...) PARTITION BY LIST COLUMN (region) VALUES IN ('us', 'eu');` |
| **Read Replicas**    | Offload analytics queries.                   | `ALTER INSTANCE REPLICATE DO_DB 'analytics_db' DO_TABLE users IGNORE_SERVER_IDS 1;` (MySQL)    |
| **Caching**          | Cache API responses.                          | `redis-cli SETEX "product:100" 300 '{"name":"Laptop"}'`                                        |
| **Queue Async**      | Process payments asynchronously.             | `aws sqs send-message --queue-url https://... --message-body '{"payment_id":123}'`               |
| **Load Balancing**   | Distribute traffic globally.                 | `kubectl patch svc myapp --type='json' -p='[{"op": "replace", "path": "/spec/loadBalancerIP", "value": "10.0.0.1"}]'` |
| **Microservices**    | Deploy order service separately.              | `helm install order-service ./order-service-chart`                                                  |

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **Use When**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)** | Separate read/write models for scalability.                                   | High-throughput apps with complex queries (e.g., financial trading).                          |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Store data as a sequence of events.                                          | Audit trails, time-sensitive systems (e.g., blockchain).                                       |
| **[Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)** | Fail fast to avoid cascading failures.                                       | Microservices communicating over HTTP/gRPC.                                                   |
| **[Backend for Frontend (BFF)](https://microservices.io/patterns/data/bff.html)** | Dedicated APIs per client (mobile/web).                                      | Multi-client apps (e.g., mobile + admin dashboards).                                          |
| **[Serverless](https://aws.amazon.com/serverless/)** | Run functions without managing servers.                                     | Sporadic workloads (e.g., file processing, APIs).                                            |
| **[Data Mesh](https://tmr.com/data-mesh/)** | Decentralize data ownership across teams.                                     | Large enterprises with siloed data teams.                                                     |
| **[Polyglot Persistence](https://martinfowler.com/bliki/PolyglotPersistence.html)** | Use different DBs for different needs.                                       | Mixed workloads (e.g., SQL for transactions + NoSQL for logs).                               |

---

## **Best Practices**
1. **Measure Before Scaling:** Use tools like Prometheus/Grafana to identify bottlenecks.
2. **Statelessness:** Prefer stateless designs to simplify scaling.
3. **Monitor Latency:** Track P99/P95 percentiles to detect scaling needs.
4. **Graceful Degradation:** Implement fallback mechanisms (e.g., cache hits before DB).
5. **Cost Efficiency:** Right-size resources (e.g., spot instances for batch jobs).

---
**Next Steps:**
- [Database Sharding Deep Dive](#database-sharding)
- [Serverless Architectures](#serverless-architectures)
- [Observability for Scaling](#observability-guidelines)