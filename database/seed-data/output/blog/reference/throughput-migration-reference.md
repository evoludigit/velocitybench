## **[Pattern] Throughput Migration Reference Guide**

---

### **1. Overview**

The **Throughput Migration** pattern addresses the challenge of migrating workloads from a legacy system to a new architecture while minimizing downtime and ensuring sustained performance. This pattern focuses on gradually shifting traffic from the old system to the new one by routing requests through a migration proxy, allowing the new system to handle increasing loads until the legacy system can be fully decommissioned.

Throughput Migration is ideal for high-availability systems where downtime is unacceptable, such as databases, microservices, or monolithic applications. The pattern ensures smooth transition by:
- **Gradually offloading traffic** to the new system.
- **Monitoring performance** to detect bottlenecks.
- **Failing over gracefully** if issues arise.

By decoupling the migration process from sudden traffic shifts, this pattern reduces risks associated with abrupt system changes.

---

### **2. Key Concepts**

| **Term**               | **Definition**                                                                                     | **Purpose**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Legacy System**      | The existing system being migrated out.                                                           | Provides initial service while the new system scales.                                          |
| **New System**         | The target system replacing the legacy one.                                                        | Handles increased traffic and supports future growth.                                          |
| **Migration Proxy**    | A routing layer (e.g., load balancer, API gateway) that distributes traffic between old and new. | Gradually shifts traffic while monitoring performance.                                           |
| **Migration Criteria** | Defined thresholds (e.g., response time, error rate) to determine full handover.                  | Ensures stability before fully decommissioning the legacy system.                                |
| **Rollback Plan**      | A pre-defined script to revert traffic to the legacy system if issues arise.                       | Mitigates downtime and data loss during migration.                                              |

---

### **3. Schema Reference**

The throughput migration pattern involves three core components:

#### **3.1 Migration Proxy Schema**
| **Field**          | **Type**   | **Description**                                                                                     | **Example**                     |
|--------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `service_name`     | String     | Name of the legacy/new service (e.g., `order-service`).                                            | `e-commerce-api`                |
| `legacy_endpoint`  | String     | Legacy system’s API/endpoint URL.                                                                   | `http://legacy-api.example.com` |
| `new_endpoint`     | String     | New system’s API/endpoint URL.                                                                      | `http://new-api.example.com`    |
| `traffic_ratio`    | Integer    | Percentage of traffic (0-100) routed to the new system.                                             | `30` (30% new, 70% legacy)      |
| `migration_stride` | Integer    | Incremental traffic shift (e.g., 5% per hour).                                                     | `5`                              |
| `health_check_url` | String     | Endpoint to validate system health.                                                                 | `/health`                        |
| `timeout_ms`       | Integer    | Max allowed response time for requests.                                                           | `5000`                           |

---

#### **3.2 Migration State Schema**
| **Field**               | **Type**   | **Description**                                                                                     | **Example**                     |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `status`                | String     | Current migration phase (`ACTIVE`, `ROLLOUT`, `FAILBACK`, `COMPLETE`).                               | `ROLLOUT`                       |
| `legacy_traffic`        | Integer    | Remaining traffic (%) on legacy system.                                                             | `20`                            |
| `new_traffic`           | Integer    | Current traffic (%) on new system.                                                                 | `80`                            |
| `last_updated`          | Timestamp  | Last time the migration state was updated.                                                          | `2023-10-15T14:30:00Z`          |
| `error_threshold`       | Float      | Max allowed error rate (e.g., 1%).                                                                  | `0.01`                          |

---

#### **3.3 Monitoring Metrics Schema**
| **Metric**               | **Unit**    | **Description**                                                                                     | **Threshold**                   |
|--------------------------|-------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `latency_p99`            | Milliseconds| 99th percentile response time.                                                                     | `< 500`                          |
| `error_rate`             | Percentage  | % of failed requests.                                                                              | `< 0.1`                          |
| `throughput`             | Requests/sec| Requests handled per second.                                                                          | `> 1000`                         |
| `legacy_failure_rate`    | Percentage  | % of failures routed to legacy system.                                                             | `< 0.05`                         |

---

### **4. Implementation Steps**

#### **4.1 Prerequisites**
- **Legacy System**: Must support read-only operations (if applicable).
- **New System**: Must be deployed and stable under load.
- **Migration Proxy**: Load balancer (e.g., Nginx, AWS ALB) or API gateway (e.g., Kong, Apigee).

#### **4.2 Setup Migration Proxy**
1. **Configure Routing Rules**:
   - Define weighted traffic distribution (e.g., 70% legacy, 30% new).
   - Example (Nginx):
     ```nginx
     upstream legacy_api { server legacy-api.example.com; }
     upstream new_api { server new-api.example.com; }
     server {
         location / {
             proxy_pass http://legacy_api;
             proxy_pass_request_headers on;
             weight 70; # Legacy gets 70% traffic
         }
         location /new {
             proxy_pass http://new_api;
             proxy_pass_request_headers on;
             weight 30; # New gets 30% traffic
         }
     }
     ```
   - **Note**: Use path-based or header-based routing for separation.

2. **Enable Health Checks**:
   - Verify endpoints return `200 OK` before heavy traffic is shifted.
   - Example (AWS ALB):
     ```yaml
     HealthCheck:
       Path: /health
       Interval: 30s
       Timeout: 5s
       HealthyThreshold: 2
       UnhealthyThreshold: 3
     ```

#### **4.3 Gradual Traffic Shift**
1. **Incrementally Increase Traffic**:
   - Adjust weights in the proxy (e.g., +5% every hour).
   - Example script (Python):
     ```python
     def update_traffic_ratio(current_ratio: int, increment: int = 5) -> int:
         new_ratio = min(100, current_ratio + increment)
         print(f"Updating traffic ratio to {new_ratio}% on new system.")
         # Call proxy API to update weights.
         return new_ratio
     ```

2. **Monitor Key Metrics**:
   - Use tools like Prometheus + Grafana or CloudWatch.
   - Alert on anomalies (e.g., `error_rate > 0.01`).

3. **Automate Failover**:
   - If `latency_p99 > 500ms` for 5 minutes, shift 100% traffic back to legacy.
   - Example failover logic:
     ```pseudo
     if (error_rate > threshold AND latency_p99 > timeout):
         revert_traffic_ratio(new_traffic, legacy_traffic + new_traffic)
         log("Migration paused due to degraded performance.")
     ```

#### **4.4 Full Handover**
1. **Verify Stability**:
   - Ensure `new_traffic = 100%` for at least 24 hours.
   - Confirm no regressions in performance.

2. **Decommission Legacy System**:
   - Shut down legacy infrastructure after validating no remaining dependencies.
   - Update DNS records to point exclusively to the new system.

---

### **5. Query Examples**

#### **5.1 Check Current Migration State**
```sql
-- SQL (e.g., PostgreSQL)
SELECT * FROM migration_status
WHERE service_name = 'e-commerce-api';
```
**Expected Output**:
```
status     | legacy_traffic | new_traffic
-----------+----------------+-------------
ROLLOUT    | 20             | 80
```

#### **5.2 Monitor Latency During Rollout**
```bash
# PromQL query (Prometheus)
avg_by_instance(
  rate(http_request_duration_seconds_bucket{service="e-commerce-api"}[5m])
)[5m]
```
**Output**:
```
# HELP http_request_duration_seconds_bucket A histogram of the response latencies.
# TYPE http_request_duration_seconds_bucket histogram
http_request_duration_seconds_bucket{le="0.5", service="e-commerce-api"} 1000
http_request_duration_seconds_bucket{le="1.0", service="e-commerce-api"} 2000
```

#### **5.3 Rollback Traffic Due to Error Spike**
```bash
# Curling API to revert weights (example)
curl -X PUT "http://migration-proxy/api/v1/weights" \
  -H "Content-Type: application/json" \
  -d '{"service": "e-commerce-api", "legacy_weight": 100, "new_weight": 0}'
```

---

### **6. Best Practices**

1. **Start with Non-Critical Traffic**:
   - Test migration on low-priority endpoints first (e.g., reports).

2. **Use Canary Releases**:
   - Route a small percentage (e.g., 1%) to new system before full rollout.

3. **Document Rollback Steps**:
   - Include commands to revert changes in the deployment documentation.

4. **Test Failover Scenarios**:
   - Simulate outages to validate failover mechanisms.

5. **Optimize New System**:
   - Tune database indexes, caching layers, and scaling policies before migration.

---

### **7. Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Blue-Green Deployment** | Instantly switches traffic to a new system after validation.                                       | Low-risk, zero-downtime deployments with identical environments.                                    |
| **Feature Flags**         | Gradually enables features in the new system without traffic redirection.                          | Phased feature rollouts with A/B testing.                                                          |
| **Database Migration**    | Syncs data between legacy and new systems during migration.                                        | Critical data consistency requirements.                                                            |
| **Circuit Breaker**       | Stops routing traffic to a failing system to prevent cascading failures.                           | Resilient architectures with microservices.                                                         |

---

### **8. Common Pitfalls & Mitigations**

| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| Unplanned Downtime                   | Use automated failback and monitor `error_rate` thresholds.                                        |
| Data Inconsency                      | Implement bidirectional sync for critical data (e.g., CDC tools like Debezium).                  |
| Performance Regression                | Test new system under peak loads before full handover.                                            |
| Proxy Misconfiguration                | Validate routing rules with `curl` or load testing (e.g., Locust).                                |
| Rollback Complexity                    | Document steps in Infrastructure-as-Code (e.g., Terraform) for reproducibility.                  |

---
**References**:
- [AWS Migration Hub](https://aws.amazon.com/migration/migration-hub/)
- *Site Reliability Engineering* by Google (Chapter 8: Release Management)
- [Kubernetes Canary Deployments Guide](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#canary-deployments)