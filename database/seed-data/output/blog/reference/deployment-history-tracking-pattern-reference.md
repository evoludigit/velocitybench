# **[Pattern] Fraisier: Deployment History & Audit Trail Tracking – Reference Guide**

## **Overview**
Fraisier’s **Deployment History and Audit Trail Tracking** pattern ensures **immutable, tamper-proof records** of all deployment activities—including timestamps, initiators, changes made, and outcomes. This enables:
- **Debugging**: Reconstruct failed deployments by reviewing exact steps, inputs, and system state.
- **Rollback**: Quickly revert to a known-good state using detailed rollback records.
- **Compliance**: Maintain regulatory audit trails for deployments (e.g., SOX, GDPR, HIPAA).
- **Observability**: Track webhook-triggered deployments and state transitions end-to-end.

Unlike generic logging, Fraisier **correlates events** (e.g., webhook → deployment → health check → rollback) into a **single, cohesive audit trail** with versioned diffs between deployments.

---
## **Core Concepts**
| **Concept**               | **Description**                                                                                     | **Example Attributes**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Deployment Record**      | Immutable snapshot of a deployment run, including metadata, status, and outcomes.                   | `id`, `timestamp`, `initiated_by`, `target_env`, `status`, `duration`, `health_check`    |
| **Webhook Event**         | Logs external triggers (e.g., CI/CD pipeline completion, manual buttons) with context.             | `event_id`, `source_system`, `payload`, `deployment_id`                                 |
| **State Transition Event**| Tracks internal system state changes (e.g., "Running" → "Health Check" → "Failed").               | `event_type`, `from_state`, `to_state`, `error_code`, `timestamp`                       |
| **Diff/Comparison**        | Side-by-side diff of config, code, or artifact versions between deployments.                        | `old_version`, `new_version`, `changed_files`, `impact_level` (low/medium/high)       |
| **Rollback Record**        | Records successful/reversed rollbacks, including revert logic and new post-rollback state.         | `rollback_id`, `from_deployment`, `to_version`, `success`, `notes`                     |

---
## **Schema Reference**
Fraisier stores data in **three primary schemas**:

### 1. **Deployment Records**
| Field               | Type          | Description                                                                                     | Example Value                     |
|---------------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `deployment_id`     | UUID          | Unique identifier for the deployment.                                                          | `550e8400-e29b-41d4-a716-446655440000` |
| `timestamp`         | Timestamp     | When the deployment began.                                                                     | `2024-05-15T14:30:00Z`           |
| `initiated_by`      | String        | User/system (e.g., "CI/CD pipeline", "user@example.com").                                      | `"user@example.com"`               |
| `target_env`        | Enum          | Environment (e.g., `dev`, `staging`, `prod`).                                                  | `"prod"`                          |
| `status`            | Enum          | Current lifecycle stage (`pending`, `running`, `health_check`, `success`, `failed`).          | `"success"`                       |
| `duration_seconds`  | Integer       | Deployment runtime in seconds.                                                                  | `45`                              |
| `health_check`      | Object        | Results from post-deployment health checks.                                                    | `{"passed": true, "warnings": []}` |
| `metadata`          | JSON          | Free-form data (e.g., commit hash, artifact URLs).                                             | `{"commit": "abc123", "version": "v1.2.0"}` |
| `webhook_id`        | UUID          | Linked webhook (if triggered).                                                                | `NULL` or `8d342c4d-...`          |

---

### 2. **Webhook Events**
| Field          | Type          | Description                                                                                     | Example Value                     |
|----------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `event_id`     | UUID          | Unique event identifier.                                                                        | `8d342c4d-1e7b-40ee-8e09-8b2f9e293b4c` |
| `timestamp`    | Timestamp     | When the webhook was received.                                                                  | `2024-05-15T14:29:15Z`           |
| `source`       | String        | System triggering the webhook (e.g., "GitHub Actions", "Jenkins").                              | `"GitHub Actions"`                |
| `payload`      | JSON          | Raw webhook data (e.g., commit details).                                                       | `{"repo": "fraisier", "sha": "abc123"}` |
| `deployment_id`| UUID          | Linked deployment (if any).                                                                    | `550e8400-e29b-41d4-a716-446655440000` |

---

### 3. **State Transition Events**
| Field          | Type          | Description                                                                                     | Example Value                     |
|----------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `event_id`     | UUID          | Unique event identifier.                                                                        | `a1b2c3d4-...`                    |
| `deployment_id`| UUID          | Deployment this event belongs to.                                                               | `550e8400-e29b-41d4-a716-446655440000` |
| `timestamp`    | Timestamp     | When the state change occurred.                                                                | `2024-05-15T14:30:05Z`           |
| `from_state`   | Enum          | Previous state (e.g., `pending`, `running`).                                                  | `"running"`                       |
| `to_state`     | Enum          | New state (e.g., `health_check`, `failed`).                                                   | `"health_check"`                  |
| `error_code`   | String        | Error details (if applicable).                                                                | `"ECONNREFUSED"` or `NULL`         |
| `details`      | JSON          | Additional context (e.g., health check logs).                                                 | `{"service": "api", "status": 500}` |

---
### 4. **Rollback Records** *(Subset of `deployment_records` with additional fields)*
| Field          | Type          | Description                                                                                     | Example Value                     |
|----------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `rollback_from` | UUID          | Deployment ID being reverted.                                                                   | `550e8400-e29b-41d4-a716-446655440000` |
| `rollback_to`   | String        | Target version (e.g., `v1.1.0`).                                                                | `"v1.1.0"`                        |
| `success`      | Boolean       | Whether rollback completed successfully.                                                       | `true`                            |
| `rollback_script`| String      | Script or logic used for revert (for audit purposes).                                          | `"/opt/rollback.sh"`              |

---
## **Query Examples**
### **1. List Recent Deployments to Production**
```sql
SELECT deployment_id, timestamp, initiated_by, status, duration_seconds
FROM deployment_records
WHERE target_env = 'prod'
ORDER BY timestamp DESC
LIMIT 10;
```
**Output:**
| `deployment_id`                     | `timestamp`               | `initiated_by`      | `status`     | `duration_seconds` |
|-------------------------------------|---------------------------|---------------------|--------------|-------------------|
| `550e8400-e29b-41d4-a716-446655440000` | `2024-05-15T14:30:00Z`   | `"user@example.com"` | `"success"`   | `45`              |

---

### **2. Trace a Webhook to Its Deployment**
```sql
SELECT d.deployment_id, d.timestamp, d.status, w.source, w.payload
FROM deployment_records d
JOIN webhook_events w ON d.webhook_id = w.event_id
WHERE w.event_id = '8d342c4d-1e7b-40ee-8e09-8b2f9e293b4c';
```
**Output:**
| `deployment_id`                     | `timestamp`               | `status`     | `source`           | `payload`                          |
|-------------------------------------|---------------------------|--------------|--------------------|------------------------------------|
| `550e8400-e29b-41d4-a716-446655440000` | `2024-05-15T14:30:00Z`   | `"success"`   | `"GitHub Actions"` | `{"repo": "fraisier", "sha": "abc123"}` |

---

### **3. Find Failed Deployments with Errors**
```sql
SELECT s.deployment_id, s.from_state, s.to_state, s.error_code, s.timestamp
FROM state_transitions s
JOIN deployment_records d ON s.deployment_id = d.deployment_id
WHERE s.to_state = 'failed'
ORDER BY s.timestamp DESC;
```
**Output:**
| `deployment_id`                     | `from_state` | `to_state` | `error_code`   | `timestamp`               |
|-------------------------------------|--------------|------------|----------------|---------------------------|
| `a1b2c3d4-...`                      | `"running"`  | `"failed"` | `"ECONNREFUSED"` | `2024-05-15T15:10:30Z`  |

---

### **4. Compare Two Deployments for Changes**
```sql
SELECT old_version, new_version, changed_files, impact_level
FROM diff_comparisons
WHERE old_deployment_id = 'a1b2c3d4-...'
  AND new_deployment_id = '550e8400-e29b-41d4-a716-446655440000';
```
**Output:**
| `old_version` | `new_version` | `changed_files`               | `impact_level` |
|---------------|---------------|-------------------------------|----------------|
| `"v1.1.0"`    | `"v1.2.0"`    | `["api/service.py", "config.yml"]` | `"medium"`    |

---
### **5. List Rollbacks for a Specific Deployment**
```sql
SELECT * FROM deployment_records
WHERE rollback_from = '550e8400-e29b-41d4-a716-446655440000';
```
**Output:**
| `deployment_id`                     | `rollback_from`               | `rollback_to` | `success` | `notes`                     |
|-------------------------------------|-------------------------------|---------------|-----------|-----------------------------|
| `9e8d7c6f-...`                      | `"550e8400-e29b-41d4-a716-446655440000"` | `"v1.1.0"` | `true`    | `"Reverted due to API timeout"` |

---

## **Implementation Notes**
### **1. Data Lifecycle**
- **Retention**: Audit logs are **immutable** and retained for **7+ years** (adjustable).
- **Versioning**: Each deployment record is versioned; diffs are computed on-demand.
- **Indexing**: Critical fields (`deployment_id`, `target_env`, `timestamp`) are indexed for performance.

### **2. Integrations**
- **CI/CD**: Hook Fraisier into pipelines (e.g., GitHub Actions, Jenkins) via webhooks.
- **Infrastructure**: Embed Fraisier agents in Kubernetes, Terraform, or serverless deployments.
- **Databases**: Store raw logs in **time-series databases** (e.g., InfluxDB) for analytics.

### **3. Example Workflow: Debugging a Failed Deployment**
1. **Identify the failed deployment**:
   ```sql
   SELECT * FROM deployment_records WHERE status = 'failed';
   ```
2. **Check webhook context**:
   ```sql
   SELECT * FROM webhook_events WHERE deployment_id = 'failed_id';
   ```
3. **Review state transitions**:
   ```sql
   SELECT * FROM state_transitions WHERE deployment_id = 'failed_id';
   ```
4. **Compare with previous deployment**:
   ```sql
   SELECT * FROM diff_comparisons
   WHERE old_deployment_id = 'previous_id'
     AND new_deployment_id = 'failed_id';
   ```
5. **Roll back if needed**:
   ```sql
   -- Trigger a rollback via API
   POST /api/v1/deployments/rollback
   { "deployment_id": "failed_id", "target_version": "v1.1.0" }
   ```

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                   | **Use Case**                                  |
|--------------------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)** | Store state changes as an append-only log of events.                                             | Audit trail for stateful systems.            |
| **[Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)** | Deploy to a separate environment before switching traffic.                                       | Zero-downtime rollbacks.                     |
| **[Canary Releases](https://martinfowler.com/bliki/CanaryRelease.html)**         | Gradually roll out to a subset of users.                                                        | Controlled risk exposure.                    |
| **[GitOps](https://www.gitops.tech/)** | Manage infrastructure as code via Git repositories.                                              | Declarative deployments with version control. |

---
## **Tools & Libraries**
| **Component**               | **Tools/Libraries**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------|
| **Storage**                 | PostgreSQL (for structured data), InfluxDB (for time-series logs).                   |
| **Orchestration**           | Kubernetes Operators, Terraform Cloud, ArgoCD.                                       |
| **Webhook Handling**        | Nginx, Apache, oder AWS API Gateway.                                                  |
| **Diffing**                 | Python `diff-match-patch`, `go-diff`.                                                  |
| **Audit Visualization**     | Grafana, ELK Stack (Elasticsearch, Logstash, Kibana), or custom dashboards.         |

---
## **Best Practices**
1. **Minimize Sensitive Data**: Exclude secrets (e.g., API keys) from logs via redaction.
2. **Performance**: Cache frequent queries (e.g., "last 100 deployments") to avoid full table scans.
3. **Alerting**: Set up alerts for failed deployments or rollbacks via Slack/PagerDuty.
4. **Backup**: Regularly back up audit logs to S3/Glacier for disaster recovery.
5. **Compliance Labels**: Tag deployments with regulatory flags (e.g., `"compliance": "HIPAA"`).

---
## **Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Immutable Log**      | A log that cannot be altered after creation.                                   |
| **State Transition**   | Movement between predefined states (e.g., `running` → `health_check`).         |
| **Diff**               | A comparison of two versions showing changes (added/removed/modified).        |
| **Rollback Record**    | A snapshot of a deployment’s state before and after reverting to a prior version. |

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| **Slow queries on large datasets**  | Add indexes on `timestamp`, `target_env`, and `status`.                     |
| **Missing webhook events**          | Verify webhook payload format matches Fraisier’s schema.                    |
| **Failed health checks**            | Check `state_transitions` for `error_code` and review `health_check` details. |
| **Rollback partially succeeds**     | Audit `rollback_records` for `success` flags and missing steps.            |

---
**End of Reference Guide** (≈1,000 words)