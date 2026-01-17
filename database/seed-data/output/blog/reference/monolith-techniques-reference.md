# **[Pattern] Monolith Techniques Reference Guide**

---

## **Overview**
The **Monolith Techniques** pattern refers to design approaches for structuring large, domain-focused applications as a single cohesive unit (a "monolith") rather than as microservices, while leveraging best practices to manage complexity, scalability, and maintainability. This pattern is ideal for:
- **Highly interdependent services** (e.g., financial systems, internal tools).
- **Teams with shared domain expertise** leveraging a unified backend.
- **Rapid iteration** in domains where tight coupling is acceptable.

Monoliths excel in simplicity for small-to-medium workloads but require intentional techniques to mitigate scalability bottlenecks. This guide covers architectural patterns, database strategies, deployment techniques, and trade-off considerations.

---

## **Schema Reference**

| **Category**               | **Technique**                     | **Description**                                                                 | **Pros**                                                                 | **Cons**                                                                 |
|----------------------------|-----------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Architecture**           | **Vertical Slice Structure**      | Organize code by user-facing workflows (e.g., checkout flow) rather than layers. | Aligns with developer mental models; easier refactoring.               | Can create duplicate logic if slices overlap.                        |
|                            | **Domain-Driven Design (DDD)**    | Apply bounded contexts to partition the monolith into loosely coupled modules. | Improves cohesion; facilitates gradual decomposition.                   | Requires upfront analysis; may increase complexity.                   |
|                            | **Feature Flags**                | Toggle features at runtime without redeploying.                             | Enables A/B testing and gradual rollouts.                               | Increases deployment complexity.                                       |
| **Database**               | **Single-Column Database**         | Store all data in a single relational database.                              | Simple transactions; ACID compliance.                                  | Scales poorly; risk of performance bottlenecks.                        |
|                            | **Database Sharding**             | Partition data horizontally across identical DB instances.                    | Improves read/write throughput.                                         | Complex sharding keys; eventual consistency issues.                     |
|                            | **Read-Replicas**                | Replicate DB reads to secondary nodes.                                       | Reduces read load on primary.                                           | No write scaling; higher storage costs.                                |
| **Deployment**             | **Blue-Green Deployment**         | Maintain two identical environments; switch traffic to the "green" version. | Zero downtime; easy rollback.                                           | Requires double resources.                                              |
|                            | **Canary Deployments**            | Gradually roll out changes to a subset of users.                           | Reduces risk of widespread failures.                                   | Requires user segmentation and monitoring.                             |
|                            | **Containerization (Docker)**     | Package monolith + dependencies into lightweight containers.                  | Portable; easier scaling (e.g., Kubernetes).                           | Adds operational overhead.                                              |
| **Scaling**                | **Stateless Design**              | Avoid server-side session storage; use distributed caching (e.g., Redis).    | Horizontal scaling via load balancers.                                   | Requires caching layer; increased complexity.                         |
|                            | **Async Processing**              | Offload long-running tasks (e.g., reports) to queues (RabbitMQ, Kafka).   | Prevents blocking requests.                                             | Adds eventual consistency challenges.                                  |
| **Monitoring**             | **Distributed Tracing**           | Track requests across services/microservices (even in a monolith).           | Identifies bottlenecks in complex workflows.                            | Overhead for instrumenting code.                                        |
|                            | **Centralized Logging**           | Aggregate logs from all instances/regions.                                  | Unified visibility for debugging.                                      | Storage costs scale with volume.                                        |

---

## **Implementation Details**

### **1. Vertical Slice Structure**
**Goal:** Align code with user workflows (e.g., "Order Flow," "Inventory Management").
**Example:**
```
src/
├── order-flow/
│   ├── controllers/
│   ├── services/
│   ├── repositories/
│   └── validations/
├── inventory/
│   ├── controllers/
│   └── services/
```

**Key Rules:**
- Each slice owns its database schema (e.g., `orders`, `inventory` tables).
- Slices communicate via API calls or shared libraries (avoid tight coupling).
- **Trade-off:** Duplicated code may emerge if slices share domain logic (mitigate via DDD).

---

### **2. Database Strategies**
#### **Single Database (Default)**
- **When to use:** Small-to-medium workloads (<1M daily requests).
- **Optimizations:**
  - **Indexing:** Add indexes for frequent query columns (e.g., `WHERE user_id`).
  - **Query Optimization:** Use `EXPLAIN ANALYZE` to identify slow queries.
  - **Connection Pooling:** Configure `pgbouncer` (PostgreSQL) or `ProxySQL` (MySQL).

#### **Sharding**
- **When to use:** High write throughput (e.g., social media feeds).
- **Implementation:**
  - **Range-based sharding:** Split by `user_id` ranges (e.g., `users 1-100000` on `db1`).
  - **Hash-based sharding:** Distribute data evenly (e.g., `SHARDING_KEY = HASH(user_id)`).
  - **Tools:** Use [Vitess](https://vitess.io/) (YouTube-scale) or custom proxy (e.g., [ProxySQL](https://proxysql.com/)).

**Example Shard Key Design:**
```sql
-- User table sharded by region
CREATE TABLE users (
  id BIGINT PRIMARY KEY,
  region VARCHAR(2) NOT NULL,
  username VARCHAR(50),
  -- other columns
) PARTITION BY LIST COLUMN (region);
```

#### **Read-Replicas**
- **Setup:**
  1. Replicate primary DB to N replicas.
  2. Route read queries to replicas via a load balancer (e.g., `HAProxy`).
  - **Tools:** PostgreSQL logical replication, MySQL replication.

---

### **3. Deployment Techniques**
#### **Blue-Green Deployment**
**Workflow:**
1. Deploy new version to "green" environment.
2. Validate with canary users.
3. Switch traffic from "blue" to "green" via DNS/load balancer.
4. Roll back to "blue" if issues arise.

**Tools:**
- **Kubernetes:** Use `Deployment` + `Service` with `sessionAffinity: None`.
- **Cloud:** AWS CodeDeploy, Azure Traffic Manager.

#### **Canary Deployments**
**Example (AWS):**
1. Deploy new version to a small AWS Auto Scaling group.
2. Route 5% of traffic via ALB weight-based routing.
3. Monitor metrics (e.g., error rate) for 15 minutes.
4. Fully roll out if stable.

**Tools:**
- **Istio:** Traffic splitting with `VirtualService`.
- **Istio Example:**
  ```yaml
  apiVersion: networking.istio.io/v1alpha3
  kind: VirtualService
  metadata:
    name: monolith
  spec:
    hosts:
    - monolith.example.com
    http:
    - route:
      - destination:
          host: monolith.example.com
          subset: v1
        weight: 95
      - destination:
          host: monolith.example.com
          subset: v2
        weight: 5
  ```

---

### **4. Scaling Strategies**
#### **Statelessness**
- **Key Principles:**
  - Store sessions in Redis/Memcached.
  - Use JWT for authentication (stateless tokens).
  - Avoid server-side caches (e.g., `memcached` for app data).
- **Example (Python Flask + Redis):**
  ```python
  from flask import Flask
  import redis

  app = Flask(__name__)
  redis_client = redis.StrictRedis(host='redis', port=6379)

  @app.route('/set_session')
  def set_session():
      redis_client.set("user:123:session", "{"key": "value"}")
      return "OK"
  ```

#### **Async Processing**
- **Use Case:** Background tasks (e.g., generating PDFs, sending emails).
- **Tools:**
  - **Job Queues:** RabbitMQ, SQS, or Kafka.
  - **Workflow:** Decouple producers/consumers.
- **Example (Python + Celery):**
  ```python
  from celery import Celery
  app = Celery('tasks', broker='redis://redis:6379/0')

  @app.task
  def generate_pdf(user_id):
      # Long-running task
      pass
  ```

---

### **5. Monitoring**
#### **Distributed Tracing**
- **Tools:** OpenTelemetry, Jaeger, or Datadog APM.
- **Implementation:**
  1. Instrument code with trace IDs (e.g., `UUID`).
  2. Propagate traces via HTTP headers (`traceparent`).
- **Example (Python):**
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)

  def order_flow():
      with tracer.start_as_current_span("order_flow"):
          # Business logic
          pass
  ```

#### **Centralized Logging**
- **Tools:** ELK Stack (Elasticsearch, Logstash, Kibana), Splunk, or Loki.
- **Best Practices:**
  - Structured logging (e.g., JSON).
  - Correlate logs with traces (via `trace_id`).

---
## **Query Examples**
### **1. Vertical Slice Query (Order Flow)**
**Goal:** Fetch order details with related line items.
```sql
-- Postgres JSONB example for flexible schema
SELECT
  o.*,
  jsonb_agg(
    jsonb_build_object(
      'id', li.id,
      'product', li.product_name,
      'quantity', li.quantity
    )
  ) AS line_items
FROM orders o
JOIN line_items li ON o.id = li.order_id
WHERE o.user_id = 123
GROUP BY o.id;
```

### **2. Sharded Database Query (User Lookup)**
**Target:** Find users by region (sharded table).
```sql
-- Route to shard by region (via proxy)
SELECT * FROM users WHERE region = 'us' AND username = 'jdoe';
-- Proxy SQL rule:
-- SELECT * FROM users WHERE region = 'us' AND username = 'jdoe'
-- --> ROUTE TO db_us;
```

### **3. Async Task Trigger (PDF Generation)**
**Producer (Monolith):**
```python
from celery import chain

def create_invoice(user_id):
    return chain(
        generate_pdf.s(user_id),
        send_email.s(user_id)
    )()
```

**Consumer (Worker):**
```python
@app.task
def generate_pdf(user_id):
    # Download template, render PDF, save to S3
    pass
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Pair With Monolith**                          |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------|
| **Layered Architecture**  | Separate UI, business logic, and data layers.                                | Use alongside Vertical Slices for clarity.            |
| **CQRS**                  | Separate read (queries) and write (commands) models.                          | Pair with monolith for analytics-heavy workloads.      |
| **Event Sourcing**        | Store state changes as a sequence of events.                                  | Combine with monolith for audit trails.                |
| **Microservices**         | Decompose monolith into independent services over time.                       | Gradually migrate from monolith as scale demands it. |
| **Serverless**            | Run monolith functions as FaaS (e.g., AWS Lambda).                          | Ideal for sporadic workloads (e.g., cron jobs).      |

---

## **Anti-Patterns to Avoid**
1. **God Object Monolith:** Avoid a single class handling everything (violates SRP).
   - *Fix:* Apply DDD to split into bounded contexts.
2. **Ignoring Database Scaling:** Assuming a single DB will always work.
   - *Fix:* Monitor query performance; shard proactively.
3. **Over-Engineering for Scale:** Adding Kubernetes before needing it.
   - *Fix:* Start with containers (Docker); scale horizontally later.
4. **Tight Coupling:** Sharing libraries directly between slices.
   - *Fix:* Use interfaces or API contracts.

---
## **Tools & Libraries**
| **Category**       | **Tools**                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **ORM**            | SQLAlchemy, Django ORM, TypeORM                                          |
| **Task Queues**    | RabbitMQ, Celery, AWS SQS                                                 |
| **Caching**        | Redis, Memcached                                                          |
| **Tracing**        | OpenTelemetry, Jaeger, Datadog                                            |
| **Deployment**     | Kubernetes, Docker, AWS CodeDeploy                                        |
| **Monitoring**     | Prometheus + Grafana, ELK Stack                                         |

---
**Key Takeaway:** Monoliths thrive when domain complexity is low-to-moderate. Leverage **vertical slices**, **sharding**, and **async processing** to mitigate scaling limits. Transition to microservices only when decomposition aligns with business boundaries.