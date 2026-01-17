# **[Pattern] On-Premises Validation Reference Guide**

---

## **Overview**
The **On-Premises Validation** pattern ensures data integrity, compliance, and security by validating content or operations at the edge (client-side or on-premises infrastructure) before synchronizing changes with a cloud or centralized service. This approach is critical for environments requiring strict data control, offline capabilities, or regulatory adherence (e.g., healthcare, finance, or military systems).

Unlike client-side only validation (which may bypass server-side checks), on-premises validation executes locally but integrates seamlessly with backend systems. It includes:
- **Pre-validation**: Rules enforced before submission (e.g., data formatting, referential integrity).
- **Post-validation**: Confirms consistency after local processing but before synchronization.
- **Conflict resolution**: Handles discrepancies between on-premises and cloud data (e.g., timestamps, versioning).

This pattern minimizes reliance on unstable networks while maintaining data consistency. It’s ideal for hybrid architectures where some workloads must remain on-premises (e.g., legacy systems, air-gapped environments).

---
## **Core Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Use Case Examples**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Validation Rule**    | A business logic rule applied to data at rest or in transit. Rules can be defined as predefined policies (e.g., regex, DDL constraints) or custom scripts (e.g., Python, PowerShell).                          | Enforcing patient privacy in a healthcare EHR system (HIPAA compliance).                                   |
| **Local Repository**   | A database or file store on-premises that holds data during offline operations. Supports CRUD operations with validation before syncing to a remote system.                                                       | A retail POS system validating inventory updates before pushing to ERP.                                     |
| **Sync Engine**        | A service (e.g., Azure Synapse, SFTP, custom ETL) that reconciles on-premises data with cloud storage, applying validation rules during reconciliation.                                                        | Syncing sales orders from a warehouse to a cloud-based inventory system with conflict resolution.         |
| **Conflict Resolution**| Mechanisms to handle discrepancies (e.g., last-write-wins, manual review, or merging). Often involves timestamps, versioning, or user-defined policies.                                                          | Resolving duplicate entries in a distributed order management system.                                      |
| **Offline Quarantine** | A buffer zone for invalid/unconfirmed data that cannot be synced until rules are satisfied. Prevents corrupted data from propagating.                                                                   | Staging raw telemetry data before validating against sensor calibration thresholds.                       |
| **Audit Log**          | Records of validation events (pass/fail) for compliance and debugging. Typically stored separately from operational data.                                                                                   | Logging failed API calls due to invalid credentials in a federated identity system.                        |

---
## **Schema Reference**
Below are common validation schemas for on-premises validation systems. Adjust fields based on your integration (e.g., REST API, database schema, or message queue).

### **1. Validation Rule Schema**
```json
{
  "rule_id": "string (UUID)",  // Unique identifier (e.g., "e93d438f-6f9a-4952-98f8-80230b9e9725")
  "name": "string",            // Human-readable rule name (e.g., "HIPAA_Patient_Age_Validation")
  "type": "enum",              // Validation type: ["regex", "ddl", "custom_script", "api_call"]
  "description": "string",     // Rule purpose (e.g., "Ensure patient age ≥ 18 for prescriptions").
  "scope": ["enum"],           // Applies to: ["patient_records", "order_items", "sensor_data"]
  "criteria": "object",        // Rule-specific parameters (varies by type).
    "regex": {                   // Example for regex validation:
      "pattern": "string",      // e.g., "^[A-Za-z0-9]{8,}$"
      "flags": "string"         // e.g., "i" (case-insensitive).
    },
    "ddl": {                     // Example for database constraint:
      "table": "string",        // e.g., "patients"
      "column": "string",       // e.g., "ssn"
      "constraint": "string"    // e.g., "NOT NULL UNIQUE"
    },
    "custom_script": {          // Example for script-based validation:
      "path": "string",         // Path to script (e.g., "/scripts/validate_inventory.py").
      "args": "object"          // Script arguments (e.g., {"threshold": 100}).
    }
  "severity": "enum",          // Impact level: ["low", "medium", "high"]
  "status": "enum",            // Enabled/disabled: ["active", "inactive", "deprecated"]
  "created_at": "datetime",    // Rule creation timestamp.
  "updated_at": "datetime",    // Last modification timestamp.
  "metadata": "object"         // Custom key-value pairs (e.g., {"compliance": "GDPR"}).
}
```

---
### **2. Local Repository Schema (Example: SQL Table)**
| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|
| `record_id`        | UUID           | Unique identifier for the record.                                                                                                                                                                             | `550e8400-e29b-41d4-a716-446655440000` |
| `entity_type`      | VARCHAR(50)    | Type of entity (e.g., "patient", "order", "sensor_reading").                                                                                                                                             | `patient`                       |
| `data`             | JSON           | Serialized payload (e.g., PII, metadata).                                                                                                                                                                   | `{"name": "J. Doe", "age": 45}` |
| `validation_status`| VARCHAR(20)    | Current status: "pending", "valid", "invalid", "quarantined".                                                                                                                                           | `valid`                         |
| `errors`           | JSON           | List of validation failures (if any).                                                                                                                                                                      | `[{"rule": "HIPAA_Patient_Age", "message": "Age < 18"}]` |
| `version`          | INTEGER        | Optimistic concurrency control (prevents overwrite conflicts).                                                                                                                                              | `3`                             |
| `sync_timestamp`   | DATETIME       | When the record was last synced to cloud.                                                                                                                                                                   | `2023-10-01T12:00:00Z`          |
| `on_premises_id`   | VARCHAR(100)   | Local-only identifier (if applicable).                                                                                                                                                                    | `warehouse_order#42`            |
| `quarantine_reason`| VARCHAR(255)   | Reason for quarantine (if applicable).                                                                                                                                                                 | `pending_manager_approval`      |

---
### **3. Sync Conflict Resolution Schema**
| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `conflict_id`      | UUID           | Unique identifier for the conflict.                                                                                                                                                                       | `a1b2c3d4-5678-90ef-ghij-klmnopqrstuv` |
| `local_record`     | JSON           | Version of the record from on-premises.                                                                                                                                                                     | `{...}`                          |
| `remote_record`    | JSON           | Version of the record from cloud.                                                                                                                                                                        | `{...}`                          |
| `resolution_method`| VARCHAR(50)    | How to resolve: "local_wins", "remote_wins", "manual", "merge", or "custom_script".                                                                                                                   | `manual`                        |
| `resolved_by`      | VARCHAR(100)   | User or system account that resolved it.                                                                                                                                                                   | `admin_user`                     |
| `resolution_time`  | DATETIME       | When the conflict was resolved.                                                                                                                                                                           | `2023-10-01T14:30:00Z`          |
| `notes`            | TEXT           | Context for the resolution.                                                                                                                                                                                | `"User override due to urgent order."` |

---

## **Query Examples**
### **1. List All Invalid Records**
**SQL (PostgreSQL):**
```sql
SELECT
  record_id,
  entity_type,
  data,
  errors,
  quarantine_reason
FROM local_repository
WHERE validation_status = 'invalid'
ORDER BY errors->>'message' ASC;
```

**NoSQL (MongoDB):**
```javascript
db.localRepository.find({
  validation_status: "invalid"
}).sort({ "errors.message": 1 });
```

---
### **2. Apply a Validation Rule to New Data**
**Python (Custom Script Example):**
```python
import re

def validate_ssn(ssn: str) -> bool:
    """Regex rule for US SSN format: XXX-XX-XXXX."""
    return bool(re.match(r"^\d{3}-\d{2}-\d{4}$", ssn))

# Example usage:
data = {"ssn": "123-45-6789"}
if not validate_ssn(data["ssn"]):
    raise ValueError("Invalid SSN format.")
```

**REST API (Validation Endpoint):**
```http
POST /api/validate/patients HTTP/1.1
Content-Type: application/json

{
  "data": {
    "ssn": "987-65-4321",
    "name": "A. Smith"
  },
  "rules": ["HIPAA_SSN_REGEX"]
}
```

**Response (Success):**
```json
{
  "status": "valid",
  "metadata": {
    "rule_applied": "HIPAA_SSN_REGEX"
  }
}
```

**Response (Failure):**
```json
{
  "status": "invalid",
  "errors": [
    {
      "rule_id": "HIPAA_SSN_REGEX",
      "message": "SSN must match XXX-XX-XXXX format."
    }
  ]
}
```

---
### **3. Sync Conflicts Resolution (Example: Last-Write-Wins)**
**Pseudocode (Sync Engine Logic):**
```python
def resolve_conflict(local_record, remote_record):
    if local_record["sync_timestamp"] > remote_record["sync_timestamp"]:
        return local_record  # Local wins
    elif remote_record["version"] > local_record["version"]:
        return remote_record  # Remote wins
    else:
        return merge_records(local_record, remote_record)  # Fallback to merge
```

---
### **4. Audit Log Query**
**SQL:**
```sql
SELECT
  rule_id,
  entity_type,
  record_id,
  timestamp,
  status,
  user_agent,
  decision
FROM validation_audit_log
WHERE rule_id = 'e93d438f-6f9a-4952-98f8-80230b9e9725'
ORDER BY timestamp DESC
LIMIT 50;
```

**Output:**
| `rule_id`               | `entity_type` | `record_id`               | `timestamp`               | `status` | `user_agent`       | `decision` |
|-------------------------|----------------|----------------------------|----------------------------|-----------|--------------------|------------|
| e93d438f-6f9a-4952-98f8 | patient        | 550e8400-e29b-41d4-a716... | 2023-10-01T10:00:00Z      | failed    | `offline_client/1.0` | rejected   |

---
## **Implementation Steps**
1. **Define Rules**:
   - Use a rule engine (e.g., Drools, OpenPolicyAgent) or custom scripts to enforce validation logic.
   - Store rules in a centralized repository (e.g., database, YAML files).

2. **Set Up Local Repository**:
   - Choose a data store (SQL, NoSQL, or file-based) supporting CRUD and validation hooks.
   - Example: PostgreSQL with triggers for automatic validation.

3. **Integrate Validation**:
   - **Pre-validation**: Run rules before saving data locally (e.g., API middleware, database triggers).
   - **Post-validation**: Apply rules before syncing (e.g., during ETL, API calls).

4. **Handle Synchronization**:
   - Use a sync engine (e.g., Azure Synapse, custom script) to reconcile on-premises and cloud data.
   - Implement conflict resolution (e.g., timestamps, manual review).

5. **Audit and Monitoring**:
   - Log all validation events (success/failure) for compliance and debugging.
   - Set up alerts for repeated failures (e.g., Slack notifications).

---
## **Best Practices**
- **Idempotency**: Design sync operations to be idempotent to avoid duplicate processing.
- **Performance**: Cache validation results for repeated checks (e.g., Redis).
- **Security**:
  - Encrypt sensitive data (e.g., PII) at rest and in transit.
  - Use role-based access control (RBAC) for validation rules.
- **Scalability**: Partition validation rules by entity type (e.g., "patients" vs. "orders").
- **Documentation**: Maintain a live inventory of rules and their compliance requirements.

---
## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **[Event-Driven Validation](link)** | Validates data in response to events (e.g., Kafka streams) rather than on demand.                                                                                                                           | Real-time systems (e.g., fraud detection, IoT sensor data).                                           |
| **[Canary Validation](link)**    | Gradually rolls out validation rules to a subset of users/data to test impact.                                                                                                                                    | High-risk environments (e.g., financial transactions).                                                 |
| **[Query-Time Validation](link)** | Validates queries against a database schema or rules before execution.                                                                                                                                      | OLTP systems where ad-hoc queries are common (e.g., BI tools).                                        |
| **[Hybrid Sync](link)**          | Combines on-premises validation with cloud-based validation for critical data.                                                                                                                                | Enterprises with strict latency requirements (e.g., trading platforms).                               |
| **[Immutable Audit Logs](link)** | Stores validation logs in a write-once, append-only format for tamper-proof compliance.                                                                                                                   | Regulated industries (e.g., healthcare, government).                                                    |

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                                                 | **Solution**                                                                                          |
|------------------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| Validation failures during sync     | Missing or outdated rules on cloud side.                                   | Sync rule definitions alongside data.                                                                |
| Performance bottlenecks             | Complex validation rules or large datasets.                               | Partition data, optimize queries, or use caching.                                                   |
| Stale data conflicts                | Network latency or delayed syncs.                                          | Implement time-based conflict resolution (e.g., "last write within 5 mins wins").                     |
| Audit log corruption                | Disk failures or permission issues.                                        | Use immutable storage (e.g., AWS S3, blockchain) for logs.                                           |
| Rule conflicts                      | Overlapping or contradictory rules.                                        | Prioritize rules (e.g., "HIPAA > internal_policy") or use rule chaining.                            |

---
## **Tools and Libraries**
| **Category**               | **Tools/Libraries**                                                                 | **Language/Platform**               |
|----------------------------|------------------------------------------------------------------------------------|-------------------------------------|
| **Rule Engines**           | [OpenPolicyAgent (OPA)](https://www.openpolicyagent.org/), [Drools](https://www.drools.org/) | Go, Java                           |
| **Validation Frameworks**   | [Pydantic](https://pydantic-docs.helpmanual.io/), [Zod](https://github.com/colinhacks/zod) | Python, TypeScript                  |
| **Sync Engines**           | [Azure Synapse](https://azure.microsoft.com/products/synapse/), [Debezium](https://debezium.io/) | SQL, Kafka                         |
| **Audit Logging**          | [ELK Stack](https://www.elastic.co/elk-stack), [Fluentd](https://www.fluentd.org/) | Multi-platform                     |
| **Conflict Resolution**    | [PostgreSQL `ON CONFLICT`](https://www.postgresql.org/docs/current/sql-insert.html), [Apache Kafka Streams](https://kafka.apache.org/documentation/streams/) | SQL, Java/Scala                     |

---
## **Further Reading**
- [CQRS and Event Sourcing for Validation](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)
- [GDPR Compliance Checklist for On-Premises Data](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
- [Designing Data-Intensive Applications (Validation Chapter)](https://dataintensive.net/)