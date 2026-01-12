---
# **[Pattern] Availability Tuning Reference Guide**

---

## **1. Overview**
The **Availability Tuning** pattern ensures that a system maintains high uptime and resilience under varying workloads, failure conditions, and external disruptions. Unlike generic availability concepts, this pattern provides **targeted tuning mechanisms** for architecture, configuration, and operational practices—balancing cost, scalability, and reliability. It is essential for systems where **downtime is unacceptable**, such as financial services, healthcare applications, or mission-critical platforms.

Key objectives include:
- **Maximizing uptime** by reducing single points of failure (SPOFs).
- **Optimizing resource allocation** to handle peak loads without degradation.
- **Enforcing recovery mechanisms** (e.g., failover, auto-scaling) to mitigate outages.
- **Monitoring and adapting** to dynamic conditions (traffic spikes, dependency failures).

This guide covers **implementation strategies** (e.g., replication, clustering) and **practical configurations** (e.g., Kubernetes readiness probes, database sharding). It avoids vendor-specific details but assumes familiarity with core cloud, database, or distributed systems concepts.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Principles**
| **Concept**               | **Description**                                                                                                                                                                                                 | **Use Case Examples**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Redundancy**            | Duplicating critical components (e.g., nodes, databases) to survive failures.                                                                                                                               | Multi-AZ database deployments, stateless application replicas.                           |
| **Failover**              | Automatically switching to a backup component when a primary fails.                                                                                                                                         | Load balancers routing traffic away from failed hosts, Kubernetes `PodDisruptionBudget`.|
| **Elastic Scaling**       | Dynamically adjusting resources (e.g., CPU, memory) or instances based on demand.                                                                                                                          | Auto-scaling groups for web servers, database read replicas.                           |
| **Graceful Degradation**  | Prioritizing critical functions while degrading non-essential services during overload.                                                                                                                  | Limiting API rate limits, disabling non-critical features under high load.             |
| **State Management**      | Isolating or replicating system state (e.g., databases, caches) to prevent loss.                                                                                                                           | Distributed caches (Redis Cluster), transactional outbox pattern for event sourcing.     |
| **Observability**         | Continuous monitoring of health metrics (latency, error rates) to detect and respond to issues.                                                                                                              | Prometheus + Grafana for SLA tracking, distributed tracing.                             |

---

### **2.2 Implementation Strategies**
#### **A. Infrastructure-Level Tuning**
| **Strategy**               | **Mechanism**                                                                                     | **Configuration Example**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Multi-Region Deployment**| Deploy identical instances across geographic regions to avoid regional outages.                    | AWS Global Accelerator + Route53 failover routing.                                    |
| **Clustered Services**     | Group dependent services (e.g., databases, message brokers) for tightly coupled failover.         | PostgreSQL with logical replication, Kafka with ISR (in-sync replicas).                |
| **Load Balancing**         | Distribute traffic across healthy instances using algorithms (round-robin, least connections).     | NGINX `upstream` configuration, AWS ALB with health checks.                            |
| **Storage Redundancy**     | Replicate data across storage systems (e.g., EBS snapshots, S3 cross-region replication).        | AWS Backup policies, Ceph distributed block storage.                                  |

#### **B. Application-Level Tuning**
| **Strategy**               | **Mechanism**                                                                                     | **Implementation Example**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Stateless Design**       | Avoid storing session data on servers; use external caches (Redis, Memcached).                   | Spring Session with Redis for distributed sessions.                                    |
| **Circuit Breaking**       | Pause requests to failing dependencies to prevent cascading failures.                              | Hystrix or Resilience4j in Java applications.                                         |
| **Retry Policies**         | Exponential backoff for transient failures (e.g., network timeouts).                              | `retry` decorator in Python (Tenacity lib), AWS SQS dead-letter queues.               |
| **Bulkheading**            | Isolate workloads to prevent one component’s failure from affecting others.                        | Kubernetes `ResourceQuotas`, Java `ThreadPoolExecutor` with separate queues.          |

#### **C. Database & Data Tuning**
| **Strategy**               | **Mechanism**                                                                                     | **Configuration Example**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Read Replicas**          | Offload read queries to replicas to reduce primary database load.                                 | MySQL `read_only` slaves, PostgreSQL `pg_pool2` connection pooling.                    |
| **Sharding**               | Split data horizontally across nodes to scale horizontally.                                        | MongoDB sharding by `_id`, Vitess for MySQL.                                           |
| **Connection Pooling**     | Reuse database connections to reduce overhead.                                                    | PgBouncer for PostgreSQL, HikariCP for Java.                                            |
| **Backup & Point-in-Time Recovery** | Schedule regular backups with RTO/RPO goals.                                           | AWS RDS automated backups, cron jobs for PostgreSQL `pg_dump`.                        |

#### **D. Operational Tuning**
| **Strategy**               | **Mechanism**                                                                                     | **Tool/Example**                                                                         |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Chaos Engineering**      | intentionally inject failures to validate resilience.                                             | Gremlin, Chaos Monkey (Netflix).                                                      |
| **Blue-Green Deployments**| Deploy updates to a parallel environment and switch traffic when stable.                           | Kubernetes `Argo Rollouts`, AWS CodeDeploy.                                             |
| **Canary Releases**        | Gradually roll out changes to a subset of users.                                                   | Flagger (Kubernetes), Istio traffic splitting.                                         |
| **Alerting & SLOs**        | Define Service Level Objectives (SLOs) and trigger alerts for violations.                          | SRE Book SLOs, Prometheus alertmanager + Slack.                                        |

---

## **3. Schema Reference**
Below are **scannable tables** for key components in Availability Tuning.

### **3.1 Availability Schema: Key Metrics**
| **Metric**               | **Description**                                                                                     | **Target Threshold**               | **Tools to Measure**                     |
|--------------------------|---------------------------------------------------------------------------------------------------|------------------------------------|-----------------------------------------|
| **Availability (Uptime)**| % of time the system is operational.                                                                 | 99.9% (SLA), 99.99% (critical)      | UptimeRobot, Datadog, New Relic         |
| **RTO (Recovery Time Objective)** | Max allowed time to restore service.                                                                 | 5–30 mins (depends on SLO)          | Incident reports, Chaos Engineering logs |
| **RPO (Recovery Point Objective)** | Max data loss acceptable during outage.                                                              | 0–15 mins (transactional systems)   | Backup retention policies               |
| **Error Budgets**        | % of failures allowed per SLO (e.g., 0.1% for 99.9% availability).                                    | Calculated from SLO                 | Prometheus + Grafana                    |
| **Throughput**           | Requests/second handled without degradation.                                                          | Varies by system                  | APM tools (AppDynamics), custom scripts |
| **Latency P99**          | 99th percentile request latency (identifies outliers).                                                 | <100ms (ideal), <1s (acceptable)    | AWS CloudWatch, Datadog RUM              |

---

### **3.2 Failure Mode Schema**
| **Failure Type**          | **Cause**                                                                                          | **Mitigation Strategy**                                                                 | **Example Fix**                          |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|------------------------------------------|
| **Node Failure**          | Host hardware failure, OS crash.                                                                   | Replication, auto-recovery.                                                          | Kubernetes `SelfHealing` (restart pods)  |
| **Dependency Failure**    | Third-party service downtime (e.g., payment gateway).                                              | Circuit breakers, fallback logic.                                                    | Resilience4j timeout + mock response    |
| **Configuration Drift**   | Misconfigured deployments (e.g., wrong env vars).                                                  | Infrastructure-as-code (IaC), canary releases.                                       | Terraform + GitOps (ArgoCD)              |
| **Traffic Spikes**        | Unexpected load (e.g., viral campaign).                                                            | Auto-scaling, rate limiting.                                                         | Kubernetes HPA, NGINX `limit_req`        |
| **Data Corruption**       | Disk failures, transaction rollbacks.                                                              | Checksums, WAL (Write-Ahead Logging), backups.                                      | PostgreSQL `pg_basebackup`, S3 versioning |
| **Security Breach**       | DDoS, credential leaks.                                                                           | WAF, rate limiting, zero-trust models.                                               | AWS Shield, Cloudflare Rate Limiting     |

---

## **4. Query Examples**

### **4.1 PromQL for Availability Metrics**
Monitor **service availability** using Prometheus:
```promql
# % of 5xx errors (unavailable requests)
1 - (sum(rate(http_requests_total{status=~"2.."}[5m])) / sum(rate(http_requests_total[5m])))

# Kubernetes pod availability (ready:1/1)
sum(kube_pod_status_ready{namespace="my-app"}) by (pod) == 1
```

### **4.2 Kubernetes Readiness Probe**
Ensure pods are **only traffic when healthy**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
```

### **4.3 Database Read Replica Setup (PostgreSQL)**
```sql
-- Create a standby node (logical replication)
SELECT pg_create_physical_replica('standby',
  'primary_host:5432',
  'standby_dir', 'wal_location',
  FALSE, -- synchronous
  'recovery_target_time = "2023-01-01 00:00:00"');
```

### **4.4 Auto-Scaling Group (AWS CLI)**
Configure an **ASG** to scale based on CPU:
```bash
aws autoscaling create-scaling-policy \
  --policy-name CPUScaleUp \
  --scaling-adjustment 1 \
  --auto-scaling-group-name MyAppASG \
  --adjustment-type ChangeInCapacity \
  --cooldown 300
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Combine**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[Resilience](https://www.patterns.dev/patterns/resilience)** | Handles transient failures gracefully.                                                            | Use **Circuit Breaking** + **Retry Policies** in Availability Tuning.              |
| **[Caching](https://www.patterns.dev/patterns/caching)**       | Reduces load on databases/APIs.                                                                 | Pair with **Read Replicas** to offload queries.                                     |
| **[Circuits & Fuses](https://www.patterns.dev/patterns/circuit-breaker)** | Prevents cascading failures.                                                                      | Critical for **Dependency Failures** in Availability Tuning.                         |
| **[Observer](https://www.patterns.dev/patterns/observer)**  | Notifies systems of state changes (e.g., failover triggers).                                       | Use for **Alerting & Recovery** mechanisms.                                         |
| **[Idempotency](https://www.patterns.dev/patterns/idempotency)** | Ensures repeated operations are safe (e.g., retries).                                             | Critical for **State Management** during outages.                                    |

---

## **6. Troubleshooting Checklist**
1. **Isolate the Failure**:
   - Check `kubectl get pods --all-namespaces` (K8s) or CloudWatch metrics.
   - Verify logs with `journalctl` (Linux) or ELK stack.
2. **Validate Redundancy**:
   - Test failover manually (e.g., kill primary pod in K8s).
   - Confirm read replicas are synchronized (`pg_isready -h replica`).
3. **Review Alerts**:
   - Are error budgets exceeded? Check SLO dashboards.
   - Are alerts silenced incorrectly? Audit `alertmanager` configs.
4. **Load Testing**:
   - Simulate traffic spikes with **Locust** or **JMeter**.
   - Monitor `RPS` (requests per second) vs. `latency P99`.
5. **Dependency Health**:
   - Test circuit breakers with `resilience4j` or `Hystrix`.
   - Verify third-party SLAs (e.g., payment gateways).

---
**Note**: Adjust thresholds (e.g., 99.9% availability) based on your **SLOs** and **cost constraints**. Always validate tuning changes in a **staging environment**.