# **[Pattern] Deployment Migration Reference Guide**

---
## **Overview**
The **Deployment Migration** pattern defines a structured approach to migrating applications, services, or infrastructure from one environment (source) to another (target) with minimal downtime, controlled risk, and full validation. This pattern ensures consistency, traceability, and rollback capability while transitioning workloads across different platforms (e.g., on-premises to cloud, legacy to modernized systems, or between cloud providers).

Key objectives include:
- **Seamless transition**: Minimize user disruption during migration.
- **Validation at scale**: Automate pre/post-migration checks to validate functionality, performance, and data integrity.
- **Disaster recovery (DR)**: Embed automated rollback mechanisms to revert changes quickly if issues arise.
- **Cost efficiency**: Optimize resource allocation and avoid redundant deployments.
- **Compliance**: Ensure data, security, and regulatory standards are maintained post-migration.

This guide covers core concepts, schema references, query examples, and related patterns to implement Deployment Migration effectively.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                                                                                 | **Example Use Case**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Source Environment** | The existing system (e.g., legacy server, on-premises database) that must be migrated from.                                                                                                                                                                   | Migrating from an old monolithic application to Kubernetes.                        |
| **Target Environment** | The new system (e.g., cloud VMs, serverless functions, or a different cloud provider) where the application will reside post-migration.                                                                                                           | Deploying a microservice architecture on AWS Fargate instead of VMs.               |
| **Migration Pipeline** | A series of automated steps (e.g., data export, schema conversion, deployment validation) orchestrated to complete the migration.                                                                                                                   | Using Terraform + Helm + ArgoCD to deploy a Kubernetes application.             |
| **Validation Layer**   | Automated checks (e.g., API tests, synthetic monitoring, data audits) to ensure the target environment behaves identically to the source.                                                                                                                 | Running LoadRunner scripts to validate API response times post-migration.         |
| **Rollback Trigger**   | A predefined condition (e.g., critical failure, performance degradation) that initiates a reversal to the source environment.                                                                                                                             | Reverting to the previous AWS ECS cluster if CI/CD detects a 5xx error spike.     |
| **Cutover Point**      | The scheduled moment when traffic/load is shifted from the source to the target environment.                                                                                                                                                              | Redirecting DNS from `app.olddomain.com` to `app.newdomain.com` at 3 AM UTC.      |
| **Data Synchronization** | Tools (e.g., AWS DMS, Flyway, Liquibase) to ensure source and target data remain consistent during or after migration.                                                                                                                                  | Syncing PostgreSQL data between on-premises and RDS using CDC (Change Data Capture).|
| **Blue-Green Deployment** | Deploying the target concurrently with the source, then switching traffic to the target to reduce downtime.                                                                                                                                           | Running both old and new versions of a web app on separate Kubernetes namespaces.   |
| **Canary Release**     | Gradually shifting a subset of traffic to the target to monitor performance before full migration.                                                                                                                                                     | Routing 5% of user requests to the new API for 24 hours before full cutover.       |

---

## **Schema Reference**
Below are the key schema components for designing a Deployment Migration pipeline. Use this as a reference when architecting your system.

### **1. Migration Phases Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `phase`                 | `Enum`         | Migration step (e.g., `PREPARE`, `EXPORT`, `DEPLOY`, `VALIDATE`, `CUTOVER`, `ROLLBACK`).                                                                                                                          | `"DEPLOY"`                                 |
| `status`                | `String`       | Current state of the phase (`PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `ABORTED`).                                                                                                                                      | `"SUCCESS"`                                |
| `start_time`            | `Timestamp`    | When the phase began.                                                                                                                                                                                                      | `"2024-05-15T10:00:00Z"`                   |
| `end_time`              | `Timestamp`    | When the phase completed (null if ongoing).                                                                                                                                                                                  | `"2024-05-15T12:30:00Z"`                   |
| `duration_ms`           | `Integer`      | Phase execution time in milliseconds.                                                                                                                                                                                         | `10800000` (3 hours)                       |
| `source_env`            | `String`       | Identifier for the source environment (e.g., `on-prem-db-1`).                                                                                                                                                                        | `"legacy-mysql-cluster"`                   |
| `target_env`            | `String`       | Identifier for the target environment (e.g., `aws-rds-prod`).                                                                                                                                                                       | `"prod-postgres-cluster"`                  |
| `rollback_plan`         | `JSON`         | Steps to revert the migration (e.g., database rollback scripts, DNS changes).                                                                                                                                                 | `{"type": "database", "command": "reset-to-snapshot"}` |
| `validation_rules`      | `Array[JSON]`  | Criteria to validate post-migration (e.g., API latency < 500ms, data rows = X).                                                                                                                                               | `[{"metric": "latency", "max": 500}]`       |
| `dependencies`          | `Array[String]`| Other phases this phase relies on (e.g., `["EXPORT_DATABASE"]`).                                                                                                                                                                       | `["schema-conversion"]`                   |

---

### **2. Data Export/Import Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `export_job_id`         | `UUID`         | Unique identifier for the export task.                                                                                                                                                                                              | `"550e8400-e29b-41d4-a716-446655440000"`   |
| `source_connection`     | `Object`       | Credentials/endpoint for the source (e.g., `host: "legacy-db.example.com", port: 3306`).                                                                                                                                    | `{"type": "mysql", "host": "old-db.com"}`    |
| `target_connection`     | `Object`       | Credentials/endpoint for the target.                                                                                                                                                                                                  | `{"type": "postgresql", "host": "new-db.example.com"}` |
| `data_format`           | `String`       | Format of the exported data (e.g., `CSV`, `JSON`, `Parquet`).                                                                                                                                                                           | `"Parquet"`                                 |
| `compression`           | `Boolean`      | Whether to compress the export file.                                                                                                                                                                                            | `true`                                      |
| `retries`               | `Integer`      | Max retries for failed export chunks.                                                                                                                                                                                           | `3`                                         |
| `status`                | `String`       | Export status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).                                                                                                                                                                   | `"COMPLETED"`                               |
| `bytes_exported`        | `Integer`      | Total bytes exported (in MB/GB).                                                                                                                                                                                                | `1536` (1.5 GB)                             |
| `errors`                | `Array[String]`| List of error messages (if any).                                                                                                                                                                                                   | `["Chunk 3 failed: Timeout"]`               |

---

### **3. Validation Check Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `check_id`              | `UUID`         | Unique identifier for the validation check.                                                                                                                                                                                    | `"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"`   |
| `check_type`            | `String`       | Type of validation (e.g., `API_RESPONSE`, `DATA_INTEGRITY`, `PERFORMANCE`).                                                                                                                                                     | `"PERFORMANCE"`                             |
| `target_resource`       | `String`       | Fully qualified name of the target (e.g., `api/v1/orders`).                                                                                                                                                                      | `"orders-service:8080"`                     |
| `criteria`              | `JSON`         | Pass/fail conditions (e.g., `"latency_ms": {"max": 300}}`).                                                                                                                                                                      | `{"latency_ms": {"max": 300}, "status_code": 200}` |
| `actual_result`         | `JSON`         | Measured values during the check.                                                                                                                                                                                              | `{"latency_ms": 280, "status_code": 200}`   |
| `passed`                | `Boolean`      | Whether the check met criteria.                                                                                                                                                                                               | `true`                                      |
| `details`               | `String`       | Additional context (e.g., failed request payload).                                                                                                                                                                           | `"Payload: {'order_id': '123'}"`           |

---

### **4. Rollback Schema**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                                     | **Example Value**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|
| `rollback_id`           | `UUID`         | Unique identifier for the rollback action.                                                                                                                                                                                       | `"d2a0e54a-91f6-46e7-b287-f8d478b123ab"`   |
| `trigger`               | `String`       | Reason for rollback (e.g., `VALIDATION_FAILED`, `USER_INITIATED`, `PERFORMANCE_DEGRADATION`).                                                                                                                                | `"VALIDATION_FAILED"`                      |
| `source_environment`    | `String`       | The environment to revert to (e.g., `legacy-ecs`).                                                                                                                                                                           | `"onprem-app-server"`                      |
| `target_environment`    | `String`       | The environment being rolled back from (e.g., `eks-prod`).                                                                                                                                                                        | `"eks-prod-cluster"`                        |
| `steps`                 | `Array[JSON]`  | Ordered list of rollback actions (e.g., `{"type": "stop_service", "resource": "orders-api"}`).                                                                                                                              | `[{"type": "stop_service", "resource": "orders-api"}]` |
| `status`                | `String`       | Rollback state (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).                                                                                                                                                                   | `"COMPLETED"`                               |
| `completion_time`       | `Timestamp`    | When the rollback finished.                                                                                                                                                                                                    | `"2024-05-16T09:15:00Z"`                   |

---

## **Query Examples**
Below are SQL and NoSQL query examples to interact with the Deployment Migration schemas.

---

### **1. List Active Migration Phases**
**Use Case:** Monitor ongoing migrations in real-time.

#### **SQL (PostgreSQL)**
```sql
SELECT
    phase,
    status,
    source_env,
    target_env,
    start_time,
    CASE
        WHEN end_time IS NULL THEN 'Ongoing'
        ELSE format('%s (%.1f hrs)', end_time, EXTRACT(EPOCH FROM (end_time - start_time))/3600)
    END AS duration
FROM migration_phases
WHERE status IN ('IN_PROGRESS', 'PENDING')
ORDER BY start_time DESC;
```

#### **MongoDB**
```javascript
db.migration_phases.aggregate([
  {
    $match: {
      status: { $in: ["IN_PROGRESS", "PENDING"] }
    }
  },
  {
    $addFields: {
      duration: {
        $cond: {
          if: { $isNull: "$end_time" },
          then: "Ongoing",
          else: {
            $concat: [
              { $toString: "$end_time" },
              " (",
              { $divide: [
                { $divide: [
                  { $subtract: ["$end_time", "$start_time"] },
                  1000 * 60 * 60
                ]},
                1
              ]},
              " hrs)"
            ]
          }
        }
      }
    }
  },
  { $sort: { start_time: -1 } }
]);
```

---

### **2. Find Failed Validation Checks**
**Use Case:** Identify post-migration issues requiring manual investigation.

#### **SQL**
```sql
SELECT
    c.check_id,
    c.check_type,
    c.target_resource,
    c.criteria,
    c.actual_result,
    c.passed,
    c.details,
    m.phase,
    m.status AS migration_status
FROM validation_checks c
JOIN migration_phases m ON c.migration_id = m.id
WHERE c.passed = FALSE
ORDER BY c.check_id DESC;
```

#### **MongoDB**
```javascript
db.validation_checks.find(
  {
    passed: false
  },
  {
    check_id: 1,
    check_type: 1,
    target_resource: 1,
    criteria: 1,
    actual_result: 1,
    details: 1,
    "migration_id": {
      $elemMatch: {
        "phase": 1,
        "status": 1
      }
    }
  }
).sort({ check_id: -1 });
```

---

### **3. Export Migration Data for Audit**
**Use Case:** Generate a report for compliance or post-mortem analysis.

#### **SQL**
```sql
SELECT
    m.phase,
    m.status,
    m.start_time,
    m.end_time,
    m.duration_ms,
    m.rollback_plan,
    COUNT(DISTINCT v.check_id) AS validation_checks_run,
    SUM(CASE WHEN v.passed = FALSE THEN 1 ELSE 0 END) AS failed_checks,
    COUNT(DISTINCT e.export_job_id) AS exports_completed
FROM migration_phases m
LEFT JOIN validation_checks v ON m.id = v.migration_id
LEFT JOIN export_jobs e ON m.id = e.migration_id
WHERE m.migration_id = '123e4567-e89b-12d3-a456-426614174000'
GROUP BY m.id;
```

#### **MongoDB**
```javascript
db.migration_phases.aggregate([
  {
    $match: {
      id: ObjectId("123e4567e89b12d3a456426614174000")
    }
  },
  {
    $lookup: {
      from: "validation_checks",
      localField: "id",
      foreignField: "migration_id",
      as: "validation_checks"
    }
  },
  {
    $lookup: {
      from: "export_jobs",
      localField: "id",
      foreignField: "migration_id",
      as: "exports"
    }
  },
  {
    $project: {
      phase: 1,
      status: 1,
      start_time: 1,
      end_time: 1,
      duration_ms: 1,
      rollback_plan: 1,
      validation_checks_run: { $size: "$validation_checks" },
      failed_checks: {
        $size: {
          $filter: {
            input: "$validation_checks",
            as: "vc",
            cond: { $eq: ["$$vc.passed", false] }
          }
        }
      },
      exports_completed: { $size: "$exports" }
    }
  }
]);
```

---

## **Related Patterns**
Deployment Migration often integrates with or is influenced by the following patterns:

1. **Blue-Green Deployment**
   - **Relation**: Deployment Migration can use Blue-Green to minimize downtime during cutover by running both environments in parallel.
   - **When to Use**: Critical applications where zero downtime is required (e.g., e-commerce, banking).
   - **Tools**: Kubernetes Ingress routing, AWS CodeDeploy, NGINX.

2. **Canary Releases**
   - **Relation**: Migration can include a Canary phase to gradually shift traffic to the target environment for validation.
   - **When to Use**: High-traffic services where risks must be mitigated (e.g., SaaS platforms).
   - **Tools**: Istio, AWS CodeDeploy, Linkerd.

3. **Feature Flags**
   - **Relation**: Use feature flags to control feature rollouts post-migration, allowing gradual user exposure.
   - **When to Use**: Complex applications with interconnected services.
   - **Tools**: LaunchDarkly, Unleash, Flagsmith.

4. **Infrastructure as Code (IaC)**
   - **Relation**: Define migration steps (e.g., VPC peering, RDS replication) as code for reproducibility.
   - **When to Use**: Cloud migrations or multi-environment deployments.
   - **Tools**: Terraform, Pulumi, AWS CDK.

5. **Database Migration**
   - **Relation**: Core to Deployment Migration for applications with persistent data (e.g., schema changes, CDC).
   - **When to Use**: Any migration involving databases (SQL/NoSQL).
   - **Tools**: Flyway, Liquibase, AWS Database Migration Service (DMS), Flyway.

6. **Chaos Engineering**
   - **Relation**: Validate resilience of the target environment by injecting failures during migration.
   - **When to Use**: High-availability systems where downtime is unacceptable.
   - **Tools**: Gremlin, Chaos Monkey, LitmusChaos.

7. **Observability-Driven Migration**
   - **Relation**: Use metrics, logs, and traces to monitor migration health in real-time.
   - **When to Use**: Large-scale migrations (e.g., monolith to microservices).
   - **Tools**: Prometheus, Grafana, OpenTelemetry, Datadog.

8. **GitOps**
   - **Relation**: Automate migration pipelines using Git as the single source of truth.
   - **When to Use**: Teams practicing DevOps