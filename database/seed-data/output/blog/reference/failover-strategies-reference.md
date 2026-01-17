# **[Pattern] Failover Strategies – Reference Guide**

---

## **Overview**
Failover strategies define automated or manual mechanisms to ensure continuity of service when a system component (e.g., server, database, or service) fails. Effective failover minimizes downtime, improves resilience, and maintains application availability. This guide covers **key concepts**, implementation details, schema references, and practical examples for common failover strategies, including **active-passive**, **active-active**, and **hot/cold standby**.

---

## **1. Key Concepts**
| Term               | Definition                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Primary Node**   | The active component processing requests.                                                     |
| **Secondary Node** | A backup component ready to take over if the primary fails.                                    |
| **Failover**       | The process of switching from a failed primary node to a secondary node.                      |
| **Failback**       | Reverting to the original primary node after recovery.                                         |
| **Fallback**       | Graceful degradation (e.g., routing traffic to a less-capable service).                       |
| **Tolerance**      | The system’s ability to withstand failures without service interruption.                      |
| **Latency**        | Delay introduced during failover (critical for low-latency systems).                          |
| **Synchronization**| Ensuring secondary nodes have near-real-time data consistency with the primary.               |

---

## **2. Schema Reference**
### **Failover Strategies Classification**
| **Strategy**       | **Primary Use Case**                          | **Sync State**               | **Recovery Time** | **Implementation Complexity** | **Cost**          |
|--------------------|---------------------------------------------|-----------------------------|--------------------|-------------------------------|-------------------|
| **Active-Passive** | High availability for single critical node   | Synchronous/Asynchronous    | Low (seconds)      | Low-Medium                     | Low-Medium        |
| **Active-Active**  | Scalable multi-region deployments           | Synchronous (or eventual)   | Medium (seconds)   | High                         | High              |
| **Hot Standby**    | Near-instant failover (e.g., databases)      | Synchronous                 | Low (sub-second)   | Medium-High                   | Medium-High       |
| **Warm Standby**   | Delayed failover (e.g., backups)             | Asynchronous                | High (minutes)     | Low                          | Low               |
| **Cold Standby**   | Disaster recovery (offline backups)         | None                        | Very High (hours)  | Low                          | Very Low          |
| **Circuit Breaker**| Prevent cascading failures (microservices)   | N/A                         | Low (milliseconds)| Low                          | Low               |

---

## **3. Implementation Details**

### **3.1 Active-Passive Failover**
- **Description**: A primary node handles traffic; secondary nodes remain idle but synchronized.
- **Use Cases**: Database replication (e.g., PostgreSQL streaming), load balancers with backups.
- **Mechanism**:
  1. **Monitoring**: Health checks (e.g., `ping`, HTTP 200/5xx) detect failures.
  2. **Trigger**: Failover occurs when primary health degrades below a threshold.
  3. **Promotion**: Secondary node assumes primary role; clients updated via DNS or sticky sessions.
- **Pros**: Simple, low cost.
- **Cons**: Secondary nodes underutilized; potential synchronization lag.
- **Example Tools**: HAProxy, MySQL Master-Slave, Kubernetes `PodDisruptionBudget`.

#### **Example Workflow (PostgreSQL Streaming Replication)**
```mermaid
graph LR
  A[Primary DB] -- "SQL Writes" --> B[WAL Archiving]
  B --> C[Secondary DB]
  C -- "Lag Check" -->|>20s| D[Failover Trigger]
  D --> E[Promote Secondary to Primary]
  E --> F[Client DNS Update]
```

---

### **3.2 Active-Active Failover**
- **Description**: Multiple nodes handle traffic simultaneously; failover involves rerouting traffic dynamically.
- **Use Cases**: Multi-region apps (e.g., AWS Global Accelerator), cloud-native services.
- **Mechanism**:
  1. **Synchronization**: Use **conflict-free replicated data types (CRDTs)** or **operational transformation** for eventual consistency.
  2. **Routing**: Load balancers (e.g., AWS ALB, Nginx) distribute traffic based on health checks.
  3. **Conflict Resolution**: Last-write-wins (LWW) or application-specific logic.
- **Pros**: High scalability, no single point of failure.
- **Cons**: Complex consistency modeling; higher latency for synchronous sync.
- **Example Tools**: Kubernetes `Service` with multiple endpoints, etcd for distributed coordination.

#### **Example Workflow (Kubernetes Headless Service)**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  clusterIP: None
  ports:
  - port: 80
    name: http
  selector:
    app: my-app
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-primary
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
      tier: primary
  template:
    metadata:
      labels:
        app: my-app
        tier: primary
    spec:
      containers:
      - name: app
        image: my-app:latest
        ports:
        - containerPort: 80
---
# Failover triggered if `tier: primary` pods crash
```

---

### **3.3 Hot/Warm/Cold Standby**
| **Type**      | **Synchronization**       | **Recovery Time** | **Use Case**                          |
|---------------|----------------------------|--------------------|---------------------------------------|
| **Hot Standby** | Synchronous (e.g., DB replication) | <1s               | Critical systems (e.g., databases)    |
| **Warm Standby**| Asynchronous (e.g., periodic backups) | Minutes     | Non-critical backups                    |
| **Cold Standby** | Offline (e.g., nightly snapshots)       | Hours             | Disaster recovery                     |

**Example (MySQL Hot Standby)**:
```sql
-- On Primary:
CHANGE MASTER TO
  MASTER_HOST='secondary-host',
  MASTER_USER='repl_user',
  MASTER_PASSWORD='password';

-- On Secondary:
START SLAVE;
```

---

### **3.4 Circuit Breaker Pattern**
- **Description**: Prevents cascading failures by stopping requests to a failing service after `N` retries or failures.
- **Use Cases**: Microservices, external APIs (e.g., payment gateways).
- **Mechanism**:
  1. **State Tracking**: `Closed` (normal), `Open` (failed), `Half-Open` (testing recovery).
  2. **Thresholds**:
     - `Failure Ratio` (e.g., >50% failures → `Open`).
     - `Timeout` (e.g., 30s in `Half-Open`).
  3. **Fallback**: Return cached data or degrade gracefully.
- **Tools**: Hystrix, Resilience4j, AWS Step Functions.

#### **Code Example (Resilience4j)**
```java
CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("paymentService");
circuitBreaker.executeSupplier(() -> {
    return paymentGateway.processPayment();
}, (FailureReason reason) -> {
    return fallbackPaymentService.process();
});
```

---

## **4. Query Examples**
### **4.1 Failover Health Check (Bash)**
```bash
#!/bin/bash
# Check PostgreSQL primary/secondary health (Active-Passive)
PRIMARY_HOST="primary-db.example.com"
SECONDARY_HOST="secondary-db.example.com"

# Test primary
if ! pg_isready -h "$PRIMARY_HOST"; then
  echo "Primary down. Triggering failover..."
  # Promote secondary (simplified; use pg_promote in production)
  sudo systemctl restart postgresql-secondary
fi
```

### **4.2 Kubernetes Failover Monitoring (Helm)**
```yaml
# Chart values.yaml for Prometheus alert
alerts:
  postgresql-failover:
    rules:
    - alert: "PostgresPrimaryDown"
      expr: up{job="postgresql-exporter"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "PostgreSQL primary failed over to {{ $labels.instance }}"
```

### **4.3 SQL Query: Detect Failover Lag (PostgreSQL)**
```sql
-- Check replication lag (Active-Passive)
SELECT
  pg_is_in_recovery() AS is_standby,
  pg_last_xact_replay_timestamp() AS last_replay_time,
  EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
FROM pg_stat_replication;
```

---

## **5. Failure Scenarios & Mitigations**
| **Scenario**               | **Impact**                          | **Mitigation**                                  |
|----------------------------|-------------------------------------|-------------------------------------------------|
| Network Partition          | Split-brain (active-active)         | Quorum-based consensus (e.g., etcd)              |
| Primary Node Crash         | Downtime (active-passive)           | Automated promotion (e.g., Keepalived)          |
| Database Corruption        | Data loss                           | Regular backups + point-in-time recovery (PITR)  |
| Configuration Drift        | Inconsistent failover behavior      | Infrastructure as Code (IaC) + drift detection  |
| Thundering Herd Problem    | Overwhelming failover traffic       | Rate limiting + phased rollouts                 |

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Bulkhead Pattern**      | Isolate failures to prevent cascading (e.g., thread pools for external calls).  | High-throughput systems.                         |
| **Retry with Backoff**    | Exponential backoff for transient failures (e.g., network retries).           | Temporary failures (e.g., 5xx errors).           |
| **Circuit Breaker**       | Stop cascading failures to dependent services.                                  | Microservices architectures.                    |
| **Bulkheads**             | Segregate resources to limit failure impact.                                  | Shared databases or APIs.                       |
| **Saga Pattern**          | Manage distributed transactions across services.                              | Microservices with ACID requirements.           |
| **Database Sharding**     | Split data across nodes for scalability.                                      | High-write workloads.                           |

---

## **7. Best Practices**
1. **Automate Failover**: Use tools like **Kubernetes**, **Consul**, or **Ansible** for orchestration.
2. **Monitor Lag**: Track replication lag (e.g., PostgreSQL `pg_stat_replication`).
3. **Test Failovers**: Simulate failures in staging (e.g., kill primary node).
4. **Minimize Downtime**:
   - **Synchronous replication** for <1s failover (hot standby).
   - **Asynchronous** for higher availability (accept minor lag).
5. **Document Recovery Procedures**: Include manual failback steps.
6. **Chaos Engineering**: Use tools like **Gremlin** or **Chaos Mesh** to test resilience.

---
## **8. Tools & Libraries**
| **Category**       | **Tools**                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **Databases**      | PostgreSQL (pg_standby), MySQL (InnoDB Cluster), MongoDB (Replica Sets)   |
| **Orchestration**  | Kubernetes, Docker Swarm, Nomad                                          |
| **Load Balancing** | HAProxy, Nginx, AWS ALB, Traefik                                         |
| **Service Mesh**   | Istio, Linkerd (for active-active traffic shifting)                      |
| **Monitoring**     | Prometheus + Grafana, Datadog, New Relic                                 |
| **Circuit Breaker**| Resilience4j, Hystrix, AWS App Mesh                                        |

---
## **9. Common Pitfalls**
- **Data Inconsency**: Avoid eventual consistency in critical paths.
- **Overhead**: Synchronous replication adds latency.
- **Zombie Processes**: Failed nodes may linger; use **health checks + liveness probes**.
- **Cascading Failures**: Isolate services (e.g., bulkheads).
- **False Positives**: Misconfigured health checks may trigger unnecessary failovers.