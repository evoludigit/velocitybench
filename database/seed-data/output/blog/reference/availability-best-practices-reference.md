---
# **[Pattern] Availability Best Practices – Reference Guide**

---

## **Overview**
This guide outlines **Availability Best Practices**, a pattern designed to ensure systems remain operational, responsive, and resilient under varying loads, failures, or external disruptions. Availability is critical for applications in high-dependence sectors (e.g., finance, healthcare, e-commerce) where downtime directly impacts user experience, revenue, or safety. This pattern combines architectural strategies, operational discipline, and monitoring frameworks to **minimize downtime**, **reduce recovery time**, and **increase system uptime** (measured as **nines of uptime**, e.g., 99.9% = "three nines").

Key principles include:
- **Redundancy**: Deploying multiple copies of services (active-active or active-passive).
- **Fault Isolation**: Preventing a single failure from cascading (e.g., circuit breakers, retries with backoff).
- **Graceful Degradation**: Maintaining core functionality even under partial failures.
- **Scalability**: Dynamically adjusting resources to handle load spikes.
- **Disaster Recovery**: Ensuring rapid recovery from catastrophic failures (e.g., region outages).

This guide assumes familiarity with cloud computing, microservices, and basic DevOps practices. It does **not** cover security availability (see *Security Best Practices* pattern).

---

## **Implementation Details**

### **1. Core Availability Strategies**
| **Strategy**               | **Description**                                                                 | **Tools/Technologies**                          |
|----------------------------|---------------------------------------------------------------------------------|------------------------------------------------|
| **Active-Active Replication** | Multiple instances serve identical traffic; failover is automatic.            | Kubernetes (pod anti-affinity), AWS Multi-AZ  |
| **Active-Passive Replication** | One primary instance; replicas sync data and take over on failure.          | Database replication (PostgreSQL, MongoDB)     |
| **Circuit Breakers**       | Halts requests to failing services to prevent cascading failures.              | Hystrix, Resilience4j, Spring Retry          |
| **Retry with Backoff**     | Automatically retries failed requests with exponential delays.                | AWS SQS (dead-letter queues), gRPC retries    |
| **Load Balancing**         | Distributes traffic across instances to avoid overload.                       | Nginx, AWS ALB, HAProxy                        |
| **Auto-Scaling**           | Dynamically scales resources based on metrics (CPU, memory, request volume).  | Kubernetes HPA, AWS Auto Scaling Groups       |
| **Multi-Region Deployment** | Mirrors services across cloud regions to survive regional outages.            | AWS Global Accelerator, Azure Traffic Manager |
| **Database Sharding**      | Splits data across multiple databases to prevent bottlenecks.                 | Vitess, MongoDB sharding                      |
| **Immutable Infrastructure** | Deploy new instances on failures instead of patching old ones.                | Docker/Kubernetes, Terraform                  |

---

### **2. Key Metrics to Monitor**
| **Metric**               | **Description**                                                                 | **Tools**                          |
|--------------------------|-------------------------------------------------------------------------------|------------------------------------|
| **Uptime Percentage**    | Time the system was operational (e.g., 99.99%).                                | Prometheus, Datadog, New Relic    |
| **Mean Time to Repair (MTTR)** | Average time to restore service post-failure.                                  | SRE best practices documentation  |
| **Error Rate (5xx/4xx)** | Percentage of failed requests (e.g., 5xx errors).                             | CloudWatch, ELK Stack             |
| **Latency (P99/P95)**     | Response time under load (e.g., 99th percentile < 500ms).                     | Grafana, Synthetic Monitoring     |
| **Throughput**           | Requests/second handled by the system.                                        | APM tools (AppDynamics)           |
| **Resource Utilization** | CPU, memory, disk I/O, network bandwidth usage.                              | Kubernetes metrics-server, Cloud Ops |

---

### **3. Step-by-Step Implementation**
#### **Phase 1: Design for Resilience**
1. **Identify Single Points of Failure (SPOFs)**
   - Use dependency graphs (e.g., [Dependabot](https://dependabot.com/)) to map critical components.
   - Example: A single database or monolithic service acting as an SPOF.

2. **Choose Replication Strategy**
   - **Stateless services**: Deploy behind a load balancer with auto-scaling.
   - **Stateful services** (e.g., databases): Use active-active replication (e.g., PostgreSQL streaming replication).
   - **Stateful services with no native HA**: Use a managed service (e.g., AWS RDS Proxy) or implement client-side caching.

3. **Implement Circuit Breakers**
   - Add circuit breakers to client libraries (e.g., Feign clients in Spring Boot).
   - Example:
     ```java
     @Retry(name = "databaseRetry", maxAttempts = 3)
     @CircuitBreaker(name = "databaseCircuit", fallbackMethod = "fallback")
     public User getUser(long id) { ... }
     ```

#### **Phase 2: Deploy Redundancy**
- **For stateless apps**:
  ```yaml
  # Kubernetes Deployment (3 replicas)
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: my-app
  spec:
    replicas: 3
    template:
      spec:
        containers:
        - name: my-app
          image: my-app:latest
  ```
- **For databases**:
  Use managed HA solutions (e.g., AWS Aurora Serverless) or manual replication:
  ```sql
  -- PostgreSQL streaming replication example
  wal_level = replica
  max_wal_senders = 10
  hot_standby = on
  ```

#### **Phase 3: Configure Auto-Scaling**
- **Horizontal Pod Autoscaler (Kubernetes)**:
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: my-app-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: my-app
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  ```
- **AWS Auto Scaling**:
  Configure triggers for CPU > 70% or request count > 1000/s.

#### **Phase 4: Test Resilience**
- **Chaos Engineering**: Use tools like [Gremlin](https://www.gremlin.com/) or [Chaos Mesh](https://chaos-mesh.org/) to simulate:
  - Node failures.
  - Network partitions.
  - Database outages.
- **Load Testing**:
  Use [Locust](https://locust.io/) or [k6](https://k6.io/) to simulate traffic spikes:
  ```python
  # Locust example
  class MyUserBehavior(Behavior):
      def on_start(self):
          self.user = User.on(self.client).create()

      def create_item(self):
          self.user.items.create(data={"name": "Test"})
  ```

#### **Phase 5: Monitor and Iterate**
- **Set Up Alerts**:
  Example Prometheus alert rule:
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.instance }}"
  ```
- **Post-Mortem Analysis**:
  Document failures in a database (e.g., [Blameless Postmortems](https://www.golang.org/doc/faq#c_who_made_the_deployment)) and track root causes.

---

### **4. Common Pitfalls and Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| **Over-replication**                  | Limit replicas to necessary instances (e.g., 3 for 99.99% uptime).         |
| **Thundering Herd Problem**          | Use bulkheads or priority queues (e.g., AWS SQS FIFO).                     |
| **Unbounded Retries**                | Implement exponential backoff + jitter (e.g., `retry: 3 * 2^x`).             |
| **Cold Starts (Serverless)**         | Use provisioned concurrency (AWS Lambda) or keep warm instances.           |
| **Data Consistency Lag**             | Accept eventual consistency (e.g., CQRS pattern) or use strong sync tools.  |
| **Vendor Lock-in**                   | Abstract cloud providers behind APIs (e.g., Terraform modules).            |

---

## **Schema Reference**
Below is a reference schema for an **Availability Checklist** (for CI/CD integration):

| **Category**               | **Check**                                               | **Status**       | **Notes**                          |
|----------------------------|--------------------------------------------------------|------------------|------------------------------------|
| **Redundancy**             | Deployment has ≥3 replicas.                             | [ ]               |                                     |
| **Replication**            | Database replication enabled (RPO/RTO documented).     | [ ]               |                                     |
| **Circuit Breakers**        | Critical APIs have circuit breakers.                  | [ ]               |                                     |
| **Auto-Scaling**           | Scaling rules configured for CPU/memory.               | [ ]               |                                     |
| **Chaos Testing**          | Recent chaos engineering run (document link).          | [ ]               |                                     |
| **Backup Policy**          | Automated backups (frequency: daily/weekly).           | [ ]               |                                     |
| **Disaster Recovery**       | Multi-region deployment tested.                        | [ ]               |                                     |
| **Monitoring Alerts**       | Critical errors alert team (SLOs defined).            | [ ]               |                                     |

---

## **Query Examples**
### **1. Query Prometheus for 5xx Errors**
```promql
rate(http_requests_total{status=~"5.."}[5m]) > 0
```
**Explanation**: Finds requests with 5xx errors over the last 5 minutes.

### **2. Kubernetes Pod Readiness Check**
```sh
kubectl get pods --field-selector=status.phase=Running
```
**Explanation**: Lists running pods (ensures readiness probes are working).

### **3. AWS CloudWatch Metric for Latency (P99)**
```json
{
  "MetricName": "Duration",
  "Dimensions": [
    {"Name": "API", "Value": "GetUser"},
    {"Name": "Namespace", "Value": "AWS/ApiGateway"}
  ],
  "Namespace": "AWS/ApiGateway",
  "Statistic": "p99",
  "Period": 60
}
```
**Explanation**: Queries 99th percentile latency for a specific API.

---

## **Related Patterns**
1. **Resilience with Circuit Breakers**
   - *When to use*: When a service dependency is unreliable.
   - *Key difference*: Focuses on *temporary* failure handling (vs. Availability Best Practices’ holistic uptime).

2. **Chaos Engineering**
   - *When to use*: After initial deployment to proactively test resilience.
   - *Key difference*: Active failure introduction (vs. Availability’s passive monitoring).

3. **Disaster Recovery (DR) Planning**
   - *When to use*: For catastrophic failures (e.g., region outages).
   - *Key difference*: Long-term recovery planning (vs. real-time availability).

4. **Auto-Scaling Best Practices**
   - *When to use*: To dynamically adjust resources under load.
   - *Key difference*: Focuses on *resource efficiency* (vs. Availability’s uptime guarantees).

5. **Site Reliability Engineering (SRE) Principles**
   - *When to use*: For organizational reliability culture.
   - *Key difference*: Framework for balancing reliability and velocity (vs. technical implementation).

---
## **Further Reading**
- [Google’s SRE Book (Chapter 4: Reliability)](https://sre.google/sre-book/table-of-contents/)
- [AWS Well-Architected Framework: Reliability Pillars](https://aws.amazon.com/architecture/well-architected/)
- [Kubernetes Best Practices for High Availability](https://kubernetes.io/docs/tutorials/clusters/administration/ha/)