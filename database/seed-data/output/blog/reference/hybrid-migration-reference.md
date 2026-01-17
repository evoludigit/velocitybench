---
# **[Pattern] Hybrid Migration Reference Guide**

---

## **Overview**
The **Hybrid Migration** pattern enables a phased, incremental transition of systems or data between environments (e.g., on-premises to cloud, legacy to modern platforms) while maintaining operational continuity. Unlike full cutovers, hybrid migration splits workloads across old and new systems, reducing risk by mitigating downtime, data loss, and performance degradation. This pattern is ideal for large organizations with complex dependencies, high availability requirements, or critical systems where gradual testing is necessary.

The pattern relies on **dual-write, synchronization, and selective cutover** strategies, where:
- Existing systems remain active (**"Source" environment**).
- New systems (**"Target" environment**) handle non-critical or test workloads.
- Over time, workloads are migrated incrementally, with validation at each step.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Use Case**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Source System**      | Legacy or current environment being migrated from.                                               | On-premises databases, legacy apps, or monolithic systems.                                     |
| **Target System**      | New environment (cloud, microservices, modern tech stack).                                        | AWS/Azure databases, Kubernetes deployments, or NoSQL stores.                                  |
| **Synchronization**    | Mechanisms to keep source/target data in sync (CDC, ETL, APIs).                                  | Avoiding stale data during migration.                                                          |
| **Dual-Write**         | Writing data to both source and target simultaneously.                                           | Ensuring consistency during migration phases.                                                 |
| **Selective Cutover**  | Gradually shifting workloads from source to target.                                              | Reducing risk by validating each component before full transition.                              |
| **Validation Phase**   | Testing migrated data/workloads for consistency, performance, and functionality.                | Detecting issues before full cutover.                                                         |

---

## **Schema Reference**
Below are common data schemas for hybrid migration scenarios.

### **1. Schema for Change Data Capture (CDC) Pipeline**
| Field               | Type    | Description                                                                                     | Example Values                     |
|---------------------|---------|-------------------------------------------------------------------------------------------------|------------------------------------|
| `source_id`         | UUID    | Unique identifier for the source system record.                                                 | `550e8400-e29b-41d4-a716-446655440000` |
| `target_id`         | UUID    | Unique identifier for the target system record (after sync).                                    | `660e8400-e29b-41d4-a716-446655440001` |
| `operation`         | String  | Type of change (`INSERT`, `UPDATE`, `DELETE`, `SYNC`).                                          | `INSERT`                           |
| `timestamp`         | Datetime| When the change occurred in the source system.                                                 | `2024-05-20T10:00:00Z`             |
| `data_payload`      | JSON    | Serialized record data (source and/or target format).                                           | `{"name": "Test", "value": 123}`   |
| `status`            | String  | Migration status (`PENDING`, `SYNCED`, `FAILED`, `COMPLETED`).                                  | `SYNCED`                           |
| `error`             | String  | Error details (if `status=FAILED`).                                                            | `{"code": "400", "message": "Schema mismatch"}` |

---

### **2. Schema for Workload Migration Tracking**
| Field               | Type    | Description                                                                                     | Example Values                     |
|---------------------|---------|-------------------------------------------------------------------------------------------------|------------------------------------|
| `workload_id`       | UUID    | Unique identifier for a migrated workload (e.g., API endpoint, microservice).                  | `770e8400-e29b-41d4-a716-446655440002` |
| `source_system`     | String  | Name of the source system (e.g., `legacy_db`, `monolith_app`).                               | `legacy_db`                        |
| `target_system`     | String  | Name of the target system (e.g., `cloud_db`, `k8s_api`).                                       | `cloud_db`                         |
| `migration_status`  | String  | Status (`PLANNED`, `IN_PROGRESS`, `TESTING`, `LIVE`, `FAILED`).                                | `TESTING`                          |
| `start_time`        | Datetime| When migration began.                                                                          | `2024-05-21T09:00:00Z`             |
| `end_time`          | Datetime| When migration completed (nullable).                                                            | `2024-05-21T12:00:00Z`             |
| `metrics`           | JSON    | Performance/data consistency metrics (e.g., latency, record count).                            | `{"latency_ms": 150, "records": 10000}` |
| `notes`             | String  | Observations or issues encountered.                                                              | `"Latency spike at 11:30 AM"`      |

---

## **Implementation Details**
### **1. Phases of Hybrid Migration**
1. **Assessment**
   - Audit source/target systems for compatibility (schema, dependencies, performance).
   - Define migration scope (e.g., "User profiles only").

2. **Data Synchronization Setup**
   - Configure CDC (e.g., Debezium, AWS DMS) or periodic ETL jobs.
   - Validate schema reconciliation (e.g., align SQL types with NoSQL documents).

3. **Dual-Write Deployment**
   - Implement logic to write to both systems during the overlap period.
   - Example: In an e-commerce app, user orders are logged to both the legacy DB and the new cloud DB.

4. **Selective Cutover**
   - Migrate non-critical workloads first (e.g., analytics reports).
   - Monitor for errors and revert if needed.

5. **Full Cutover**
   - Once validated, redirect all traffic to the target system.
   - Decommission the source system (with a backup).

---

### **2. Tools & Technologies**
| **Category**               | **Tools/Technologies**                                                                 | **Purpose**                                                                                     |
|----------------------------|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **ETL/CDC**                | Apache Kafka, AWS Database Migration Service, Debezium                                   | Real-time or batch data sync between systems.                                                  |
| **Orchestration**          | Terraform, Ansible, AWS Step Functions                                                   | Manage infrastructure and migration workflows.                                                |
| **Validation**             | Great Expectations, dbt, custom scripts                                                  | Ensure data consistency after migration.                                                      |
| **Monitoring**             | Prometheus, Grafana, Datadog                                                           | Track performance and sync health during migration.                                           |
| **Database**               | PostgreSQL (Fork), MySQL (Replication), MongoDB (Change Streams)                        | Sync relational or document databases.                                                         |
| **API Gateways**           | Kong, Apigee, AWS API Gateway                                                            | Route requests to source/target systems during overlap.                                         |

---

## **Query Examples**
### **1. Query CDC Pipeline Status (SQL)**
```sql
SELECT
    source_id,
    target_id,
    operation,
    timestamp,
    CASE
        WHEN status = 'SYNCED' THEN '✅ Success'
        WHEN status = 'FAILED' THEN '❌ Error: ' || error
        ELSE 'In Progress'
    END AS sync_status
FROM cdc_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;
```

### **2. Check Workload Migration Progress (PostgreSQL)**
```sql
SELECT
    workload_id,
    source_system,
    target_system,
    migration_status,
    COUNT(*) AS record_count
FROM workload_migration
JOIN workload_metrics USING (workload_id)
WHERE migration_status IN ('TESTING', 'LIVE')
GROUP BY workload_id
ORDER BY record_count DESC;
```

### **3. Compare Source vs. Target Data (Python Example)**
```python
import pandas as pd

# Load source and target data
source_df = pd.read_sql("SELECT * FROM legacy_users", legacy_conn)
target_df = pd.read_sql("SELECT * FROM cloud_users", target_conn)

# Check for discrepancies
discrepancies = pd.merge(
    source_df,
    target_df,
    how='outer',
    indicator=True,
    suffixes=('_src', '_tgt')
).query("_indicator == 'left_only' or _indicator == 'right_only'")

print(discrepancies)
```

### **4. Filter Failed Syncs (NoSQL - MongoDB)**
```javascript
db.cdc_logs.aggregate([
  {
    $match: {
      status: "FAILED",
      timestamp: { $gte: ISODate("2024-05-20") }
    }
  },
  {
    $project: {
      source_id: 1,
      error: 1,
      operation: 1,
      _id: 0
    }
  }
])
```

---

## **Validation Strategies**
1. **Data Consistency Checks**
   - Compare record counts, checksums, or hashes between source/target.
   - Example: Use `pg_checksums` for PostgreSQL or `md5` hashes in scripts.

2. **Functional Testing**
   - Verify migrated workloads (e.g., API endpoints, reports) produce identical results.
   - Example: Automated test suite comparing output from source vs. target.

3. **Performance Benchmarking**
   - Measure latency, throughput, and resource usage (CPU, memory) during migration.
   - Tools: `ab` (Apache Benchmark), `k6`, or cloud-native metrics (AWS CloudWatch).

4. **Rollback Plan**
   - Document steps to revert to the source system if issues arise.
   - Example: Temporarily block traffic to the target system.

---

## **Error Handling**
| **Issue**                     | **Root Cause**                          | **Solution**                                                                                     |
|--------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **Data Drift**                 | Source/target schemas diverge.           | Use schema validation tools (e.g., Great Expectations) or CDC hooks.                          |
| **Sync Lag**                   | Slow CDC pipeline or high load.         | Optimize pipeline (e.g., batch size, parallel processing) or scale resources.                   |
| **Dependency Failures**        | Target system lacks required services.  | Deploy dependencies incrementally (e.g., Kubernetes sidecars).                                 |
| **Downtime During Cutover**    | Traffic shift causes instability.       | Use blue-green deployment with DNS failover or feature flags.                                  |
| **Permission Errors**          | IAM/DB roles misconfigured.             | Audit permissions and grant least-privilege access.                                             |

---

## **Related Patterns**
1. **[Blue-Green Deployment](https://docs.google.com/document/d/1...)
   - **Relation**: Like hybrid migration, blue-green uses parallel environments but focuses on application deployments, not data sync.
   - **Use When**: Migrating entire apps without data overlap.

2. **[Canary Release](https://docs.google.com/document/d/1...)
   - **Relation**: Gradually shifts traffic to the target, but typically for feature flags, not full system migration.
   - **Use When**: Testing new versions of apps/services.

3. **[Event Sourcing](https://docs.google.com/document/d/1...)
   - **Relation**: Enables CDC by treating domain events as immutable logs; compatible with hybrid migration.
   - **Use When**: Building real-time systems with audit logs.

4. **[Feature Toggle (Feature Flag)](https://www.thoughtworks.com/insights/blog/feature-flags)
   - **Relation**: Used alongside hybrid migration to expose target system features incrementally.
   - **Use When**: Phased rollouts of new functionality.

5. **[Database Replication](https://www.postgresql.org/docs/current/sql-alterreplicaidentity.html)
   - **Relation**: Underpins CDC but may lack transformative capabilities (e.g., schema changes).
   - **Use When**: Near-real-time sync without application logic.

---
## **Best Practices**
- **Start Small**: Migrate a non-critical subset first (e.g., user profiles before orders).
- **Automate Validation**: Use scripts or tools to compare source/target data automatically.
- **Monitor Closely**: Set up alerts for sync failures or performance degradation.
- **Communicate Risks**: Document potential downtime or data inconsistencies to stakeholders.
- **Document Rollback**: Ensure the team knows how to revert if needed.

---
## **Example Workflow**
1. **Week 1-2**: Set up CDC from `legacy_db` to `cloud_db` (Debezium + Kafka).
2. **Week 3**: Migrate `user_service` to target; validate with 10% traffic.
3. **Week 4**: Migrate `analytics_reports`; monitor data drift.
4. **Week 5**: Full cutover for `user_service`; decommission `legacy_db` (backup first).
5. **Week 6**: Repeat for remaining systems.

---
**End of Guide**