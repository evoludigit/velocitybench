**[Pattern] Security Migration Reference Guide**
*Version 1.2 | Last Updated: [YYYY-MM-DD]*

---

### **Overview**
The **Security Migration** pattern ensures a secure transition between environments, systems, or applications while minimizing exposure risks. It addresses challenges like credential management, resource synchronization, and compliance validation during transitions (e.g., cloud migration, app refactoring, or infrastructure upgrades). This pattern enforces:
- **Zero-downtime transitions** with phased rollout validation.
- **Encrypted data handling** during transit and storage.
- **Automated audit trails** for compliance (e.g., GDPR, SOC 2).
- **Role-based access control (RBAC)** during transition phases.

Key use cases include:
✔ Migrating workloads from on-premises to cloud.
✔ Upgrading authentication systems (e.g., OAuth 2.0 → OpenID Connect).
✔ Consolidating multiple security tools (e.g., SIEM, IAM) into a unified platform.

---

### **Schema Reference**
Below is a normalized schema for designing a **Security Migration** implementation.

| **Component**               | **Description**                                                                 | **Attributes**                                                                                     | **Data Types**          | **Required** |
|------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|--------------------------|--------------|
| **Migration Project**       | High-level container for migration tasks.                                       | `projectId`, `name`, `startDate`, `endDate`, `status` (planned/active/completed), `complianceStandards` | `string`, `date`, `enum` | ✅ Yes        |
| **Migration Phase**          | Logical segment (e.g., "Data Encryption," "Credential Rotation").                | `phaseId`, `projectId`, `name`, `priority`, `successCriteria`, `estimatedDuration`                  | `string`, `enum`, `int` | ✅ Yes        |
| **Resource Inventory**       | List of assets involved (e.g., databases, APIs, user accounts).                  | `resourceId`, `migrationPhaseId`, `type` (e.g., "DB," "IAMPolicy"), `currentState`, `targetState`  | `string`, `enum`         | ✅ Yes        |
| **Credential**               | Secure storage for keys/tokens during migration.                                 | `credentialId`, `resourceId`, `keyType` (APIKey/PGPKey), `expiryDate`, `status` (active/rotated)    | `string`, `date`, `enum` | ✅ Yes        |
| **Audit Log**                | Immutable record of migration actions for compliance.                          | `logId`, `resourceId`, `action` (e.g., "EncryptData"), `timestamp`, `actor` (user/system), `status` | `string`, `date`, `enum` | ❌ No         |
| **Policy Rule**              | Enforce security rules during migration (e.g., "No data exposure").              | `ruleId`, `migrationPhaseId`, `ruleName`, `severity` (low/medium/high), `triggerCondition`        | `string`, `enum`         | ✅ Yes        |
| **Exception**                | Track deviations from migration plans.                                          | `exceptionId`, `resourceId`, `errorCode`, `description`, `resolutionStatus`                       | `string`, `enum`         | ❌ No         |

---
**Relationships:**
- A `MigrationPhase` contains multiple `ResourceInventory` items.
- Each `ResourceInventory` may reference `Credential` and `AuditLog` entries.
- `PolicyRule` applies to one or more `MigrationPhase` objects.

---
**Example Query (GraphQL):**
```graphql
query GetMigrationPhases($projectId: ID!) {
  migrationProject(id: $projectId) {
    phases {
      id
      name
      resources {
        type
        currentState
        targetState
        credentials {
          keyType
          status
        }
      }
      auditLogs {
        action
        timestamp
      }
    }
  }
}
```

---

### **Implementation Details**

#### **1. Pre-Migration Checklist**
Before migration, validate:
- **Data Classification**: Identify sensitive data (PII, credentials) in `ResourceInventory`.
  *Tooling*: Use DLP (Data Loss Prevention) tools like **Microsoft Purview** or **AWS Macie**.
- **Dependency Mapping**: Document indirect dependencies (e.g., 3rd-party APIs called during migration).
  *Tooling*: **Dependency Track**, **Nessus**.
- **Compliance Gaps**: Align phases with standards (e.g., HIPAA requires 24/7 monitoring during migration).
  *Tooling*: **OpenPolicyAgent (OPA)** for policy-as-code.

**Example Schema Update:**
```json
{
  "resourceId": "db-123",
  "type": "Database",
  "currentState": { "encryption": "AES-256", "compliance": ["GDPR"] },
  "targetState": { "encryption": "AWS KMS", "compliance": ["GDPR", "SOC2"] }
}
```

---

#### **2. Phase-Specific Implementation**
| **Phase**               | **Key Activities**                                                                 | **Security Controls**                                                                           | **Validation**                                                                 |
|-------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Discovery**           | Inventory resources; classify data.                                                | Encrypt inventories with **PGP** at rest.                                                      | Compare against **NIST SP 800-53** controls.                                   |
| **Preparation**         | Rotate credentials; configure hybrid access.                                       | Use **short-lived tokens** (JWT with 15-min expiry) for migration scripts.                     | Test with **Chaos Engineering** (e.g., failover scenarios).                     |
| **Execution**           | Deploy changes in phases (e.g., 20% traffic to new system).                         | Enable **WAF rules** during cutover to block anomalous traffic.                                | Monitor with **SIEM** (e.g., Splunk) for anomalies.                            |
| **Post-Migration**      | Validate data integrity; rotate legacy credentials.                                | Log all access with **IMDSv2** (for AWS) or **Azure AD Audit Logs**.                          | Run **penetration tests** (e.g., Burp Suite) on the new environment.          |
| **Rollback**            | Revert to pre-migration state if issues arise.                                      | Maintain **immutable snapshots** of pre-migration data.                                        | Automate rollback with **Terraform State Versioning**.                         |

---

#### **3. Credential Management**
- **Secret Rotation**: Automate rotation every **7–30 days** using secrets managers like:
  - **AWS Secrets Manager** (integrates with IAM).
  - **HashiCorp Vault** (dynamic secrets).
  - **Azure Key Vault** (for hybrid clouds).
- **Encryption**:
  - Transit: **TLS 1.2+** for all API calls during migration.
  - At Rest: **AWS KMS**, **Google Cloud KMS**, or **Azure Disk Encryption**.
- **Access Control**:
  -scope credentials to **least privilege** (e.g., IAM roles with temporary access).
  -Use **RBAC** to limit phase-specific access (e.g., "Only DevOps can trigger Phase 2").

**Example Policy Rule (OPA):**
```rego
package migration

default allow = false

allow {
  input.actor.role == "DevOps"
  input.phase == "Preparation"
  input.resource.type == "Database"
}
```

---

#### **4. Compliance Automation**
- **GDPR**: Anonymize PII during migration using **tokenization** (e.g., **AWS Glue DataBrew**).
- **PCI DSS**: Isolate credit card data in a **PCI-compliant subnet** during transition.
- **Audit Logging**:
  - Capture all changes in **immutable logs** (e.g., **AWS CloudTrail** + **S3 Object Lock**).
  - Retain logs for **7 years** (GDPR requirement).

**Compliance Checklist Template:**
| **Standard** | **Requirement**                          | **Implementation**                          | **Tool**               |
|--------------|------------------------------------------|---------------------------------------------|------------------------|
| **SOX**      | Logging for financial transactions      | Enable **AWS Config Rules** for SOX controls | AWS Config             |
| **ISO 27001**| Risk assessment documentation           | Use **RiskLens** for automated risk scoring | RiskLens               |
| **HIPAA**    | Encryption of ePHI                       | Enable **AWS KMS CMKs** for PHI data         | AWS KMS                |

---

#### **5. Rollback Strategy**
- **Automated Snapshots**: Take pre-migration backups with **checksum validation**.
  - *Tools*: **Velero** (Kubernetes), **AWS Backup**.
- **Canary Analysis**: Monitor post-migration metrics (e.g., latency, error rates) for **14 days**.
  - *Tool*: **Prometheus + Grafana**.
- **Emergency Rollback Playbook**:
  1. Trigger rollback via **SNS/CloudWatch Alarm**.
  2. Restore from snapshot using **Terraform**.
  3. Re-rotate credentials (use **AWS Secrets Manager** for automated reissuance).

---
**Example Rollback Command (Terraform):**
```hcl
module "rollback_db" {
  source = "git::https://github.com/terraform-aws-modules/rds/aws//modules/snapshot"
  snapshot_identifier = "pre-migration-snapshot-${var.env}"
  rollback_to = "pre-migration-state"
}
```

---

### **Query Examples**
#### **1. List All Migration Phases with Resource Status**
```sql
SELECT
    p.phase_id,
    p.name,
    r.resource_id,
    r.type,
    r.current_state,
    r.target_state,
    COUNT(a.action) AS audit_logs_count
FROM migration_phase p
JOIN resource_inventory r ON p.phase_id = r.migration_phase_id
LEFT JOIN audit_log a ON r.resource_id = a.resource_id
WHERE p.project_id = 'migration-2024'
GROUP BY p.phase_id, r.resource_id;
```

#### **2. Find Unencrypted Resources (Compliance Violation)**
```graphql
query FindUnencryptedResources {
  migrationProject(id: "migration-2024") {
    phases {
      resources {
        resourceId
        type
        currentState {
          encryption
        }
        targetState {
          encryption
        }
      }
    }
  }
}
```

#### **3. Generate Report for SOC 2 Audit**
```python
# Pseudocode using Python + SQLAlchemy
from sqlalchemy import text

def generate_soc2_report(engine):
    query = """
    SELECT
        r.resource_id,
        r.type,
        COUNT(DISTINCT a.actor) AS access_count,
        MAX(a.timestamp) AS last_access
    FROM resource_inventory r
    JOIN audit_log a ON r.resource_id = a.resource_id
    WHERE a.action IN ('Read', 'Write')
      AND a.timestamp > DATE_SUB(CURRENT_DATE, INTERVAL 90 DAY)
    GROUP BY r.resource_id, r.type
    HAVING access_count > 1000
    ORDER BY access_count DESC;
    """
    with engine.connect() as conn:
        return conn.execute(text(query)).fetchall()
```

---

### **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Zero Trust Architecture](https://docs.microsoft.com/en-us/azure/architecture/framework/security/zero-trust)** | Assume breach; verify every access request.                                   | Post-migration to enforce continuous authentication.                          |
| **[Encrypted Secrets Store](https://learn.microsoft.com/en-us/azure/azure-app-configuration/secrets-overview)** | Centralized encryption management.                                             | If migrating secrets across multiple clouds (e.g., AWS → Azure).               |
| **[Chaos Engineering](https://principlesofchaos.org/)**                      | Test system resilience under failure conditions.                               | During Phase 3 (Execution) to validate rollback.                               |
| **[Immutable Infrastructure](https://www.immutable-infra.com/)**            | Treat infrastructure as ephemeral and reproducible.                           | For cloud-native migrations (e.g., Kubernetes → EKS).                          |
| **[Policy as Code](https://www.openpolicyagent.org/)**                     | Enforce security policies via code (e.g., Rego).                              | To automate compliance checks during migration phases.                        |

---

### **Tools & Integrations**
| **Category**       | **Tools**                                                                                     | **Use Case**                                                                 |
|--------------------|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Secrets Mgmt**   | AWS Secrets Manager, HashiCorp Vault, Azure Key Vault                                   | Credential rotation and access control during migration.                     |
| **Compliance**     | OpenPolicyAgent (OPA), Drata, Prisma Cloud                                             | Automate policy enforcement and audit logging.                              |
| **Discovery**      | Nessus, Black Duck, AWS Config                                                        | Inventory resources and detect vulnerabilities pre-migration.             |
| **Orchestration**  | Terraform, Ansible, AWS Step Functions                                                | Automate phased rollouts and rollbacks.                                    |
| **Monitoring**     | Prometheus, Datadog, AWS CloudWatch                                                    | Track performance and security metrics post-migration.                      |
| **Chaos Testing**  | Gremlin, Chaos Mesh                                                                     | Simulate failures to validate recovery processes.                            |

---
### **Troubleshooting**
| **Issue**                          | **Root Cause**                                   | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------------|--------------------------------------------------------------------------------|
| **Unauthorized Access**             | RBAC misconfiguration                          | Run `terraform validate`; audit IAM policies with **AWS IAM Access Analyzer**. |
| **Data Corruption**                 | Failed encryption during transit               | Use **checksum validation** (e.g., `md5sum`) for backups.                     |
| **Phase Delay**                     | Compliance review bottlenecks                  | Automate reviews with **GitHub Actions** or **Jira Integrations**.           |
| **Credential Leak**                 | Stored in plaintext                             | Enforce **Vault integration** for all secrets.                                |
| **Rollback Failure**                | Outdated snapshots                             | Schedule **daily snapshots** with retention policies (e.g., 30-day window).    |

---
### **Best Practices**
1. **Start Small**: Pilot with a non-critical system before full migration.
2. **Document Everything**:
   - Use **Confluence** or **Notion** for migration playbooks.
   - Tag all resources with **`migration-phase: [name]`** for easy filtering.
3. **Automate as Early as Possible**:
   - Use **Terraform** for infrastructure-as-code (IaC) to avoid manual errors.
   - Deploy **monitoring dashboards** (e.g., Grafana) for real-time visibility.
4. **Train Teams**:
   - Conduct **phishing simulations** to test user awareness.
   - Run **tabletop exercises** for rollback scenarios.
5. **Post-Mortem**:
   - After migration, deprecate legacy systems **only after 30 days** (to allow rollback).

---
### **Example Migration Timeline**
| **Week** | **Phase**               | **Tasks**                                                                                                                                 | **Owner**       |
|----------|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|-----------------|
| 1        | Discovery               | Run Nessus scan; classify data in AWS Glue.                                                                                             | Security Team   |
| 2        | Preparation             | Rotate DB credentials; configure WAF rules.                                                                                            | DevOps          |
| 3        | Execution (Phase 1)     | Migrate 20% of traffic to new system; monitor with Datadog.                                                                               | Cloud Engineers |
| 4        | Execution (Phase 2)     | Cut over remaining 80% traffic; validate with chaos tests.                                                                              | QA Team         |
| 5        | Post-Migration          | Run penetration test; decommission legacy system.                                                                                     | Security Team   |
| 6        | Audit                   | Submit SOC 2 report; perform user training refresh.                                                                                     | Compliance Team |

---
### **Key Metrics to Track**
| **Metric**                  | **Tool**               | **Target**                          |
|-----------------------------|------------------------|-------------------------------------|
| Migration Phase Duration    | Jira + Confluence      | ≤ 8 weeks for critical systems     |
| Unauthorized Access Attempts| SIEM (Splunk)          | < 0.1% of total access attempts     |
| Data Integrity Violations    | checksum validation    | 0%                                  |
| Rollback Success Rate       | Terraform + CloudWatch | 100% for critical phases           |
| Compliance Pass Rate        | OPA + Drata            | 100% for all phases                |

---
**References**:
- [NIST SP 800-53 Migration Guide](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [AWS Well-Architected Migration Framework](https://aws.amazon.com/architecture/well-architected/)
- [Open Policy Agent (OPA) Documentation](https://www.openpolicyagent.org/docs/latest/)