**[Pattern] Compliance Troubleshooting – Reference Guide**

---

### **Overview**
Compliance Troubleshooting is a structured approach to identifying and resolving violations, discrepancies, or gaps in regulatory, internal policy, or industry-standard requirements within a system, process, or dataset. This pattern provides a systematic methodology to diagnose compliance issues, trace their root causes, and implement corrective actions while maintaining auditability and traceability. It applies across domains like **finance (SOX, GDPR, PCI-DSS)**, **healthcare (HIPAA, FDA)**, **IT security (NIST, ISO 27001)**, and enterprise governance.

Unlike reactive compliance checks (e.g., scanning for errors post-event), this pattern emphasizes **proactive diagnostics**, leveraging structured workflows, automated validation, and root-cause analysis (RCA) tools. It includes:
- **Automated compliance checks** (via rules engines, APIs, or frameworks).
- **Manual validation** (audits, expert review).
- **Remediation workflows** (escalation, approval, documentation).
- **Traceability** (linking issues to source artifacts, like policies or logs).

This guide covers **key components, schema references, query patterns, and integration with related patterns** to operationalize compliance troubleshooting.

---

## **1. Schema Reference**

| **Component**               | **Description**                                                                                     | **Example Fields**                                                                                     | **Data Type**       | **Notes**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|---------------------|----------------------------------------------------------------------------------------------|
| **Compliance Rule**         | Defines a regulatory or internal policy requirement (e.g., "PCI-DSS Requirement 12.5").             | `rule_id`, `title`, `version`, `scope`, `severity`, `reference_link`                                   | String, Enum        | Pre-configured or dynamically loaded from external sources (e.g., JSON/XML policy files).    |
| **Asset**                   | An entity subject to compliance checks (e.g., database, API, user account).                          | `asset_id`, `name`, `type` (e.g., "Database", "AWS S3"), `owner`, `location`                            | String, Enum        | Tagged for scoping (e.g., `region=us-east-1`).                                              |
| **Control**                 | A mechanism to enforce or validate a rule (e.g., "Encryption at rest", "Access log retention").     | `control_id`, `rule_id`, `implementation_type` (hardened, documented), `status` (active/inactive)     | String, Enum        | Linked to assets (e.g., "Database" → "Encryption control").                                  |
| **Check**                   | A test or query to validate a control (e.g., "Verify S3 bucket encryption").                       | `check_id`, `control_id`, `query`, `frequency` (daily/real-time), `last_run_timestamp`                | String, JSON        | May include SQL, API calls, or custom scripts.                                                |
| **Finding**                 | A recorded violation or discrepancy (e.g., "Bucket [abc123] lacks SSE-KMS encryption").            | `finding_id`, `rule_id`, `asset_id`, `severity` (high/medium/low), `description`, `remediation_steps`   | String, Enum        | Tagged with `status` (new/acknowledged/closed).                                              |
| **RemediationPlan**         | Steps to resolve a finding, including owners and deadlines.                                        | `plan_id`, `finding_id`, `assigned_to`, `due_date`, `status`, `notes`                                  | String, DateTime    | Linked to workflows (e.g., Jira tickets, email alerts).                                      |
| **AuditLogEntry**           | Immutable record of compliance checks/remediations.                                                | `log_id`, `action` (check/remediation), `user`, `timestamp`, `asset_id`, `finding_id` (if applicable)  | String, DateTime    | Used for forensics and compliance reporting.                                                   |
| **PolicyVersion**           | Tracks changes to rules or controls (e.g., "GDPR v2.0").                                           | `version_id`, `effective_date`, `description`, `previous_version_id`                                   | String, DateTime    | Enables regression testing and impact analysis.                                              |

---

## **2. Query Examples**
Compliance troubleshooting involves **querying, analyzing, and acting** on data in the schema above. Below are common query patterns using **SQL-like syntax** (adaptable to tools like PostgreSQL, MongoDB, or custom APIs).

---

### **2.1. Identify Critical Compliance Findings**
**Use Case:** List all high-severity findings requiring immediate attention.
```sql
SELECT
    f.finding_id,
    r.title AS compliance_rule,
    a.name AS asset,
    f.severity,
    f.description,
    rp.assigned_to,
    rp.due_date
FROM
    findings f
JOIN
    rules r ON f.rule_id = r.rule_id
JOIN
    assets a ON f.asset_id = a.asset_id
LEFT JOIN
    remediation_plans rp ON f.finding_id = rp.finding_id
WHERE
    f.severity = 'HIGH'
    AND (rp.status IS NULL OR rp.status = 'open')
ORDER BY
    rp.due_date ASC;
```

**Expected Output:**
| finding_id | compliance_rule         | asset       | severity | description                          | assigned_to | due_date   |
|------------|-------------------------|-------------|----------|--------------------------------------|-------------|------------|
| fdg123     | PCI-DSS 3.4             | `payment_db`| HIGH     | Missing weekly access reviews        | `security@company.com` | 2023-10-15 |

---

### **2.2. Find Orphaned Controls**
**Use Case:** Detect controls lacking active checks or assets.
```sql
SELECT
    c.control_id,
    r.title AS rule,
    c.implementation_type,
    a.name AS asset
FROM
    controls c
JOIN
    rules r ON c.rule_id = r.rule_id
LEFT JOIN
    assets a ON c.asset_id = a.asset_id
WHERE
    a.name IS NULL  -- Orphaned control (no asset)
    OR NOT EXISTS (
        SELECT 1 FROM checks WHERE control_id = c.control_id
    );  -- No active checks
```

**Expected Output:**
| control_id | rule               | implementation_type | asset   |
|------------|--------------------|---------------------|---------|
| cnt456     | SOX 404.1          | Documented          | NULL    |

---

### **2.3. Trace Findings to Policy Versions**
**Use Case:** Audit which policy changes introduced new findings.
```sql
SELECT
    p.version_id,
    p.effective_date,
    f.finding_id,
    r.title AS rule,
    COUNT(DISTINCT f.finding_id) AS finding_count
FROM
    policy_versions p
JOIN
    rules r ON p.version_id = r.version_id  -- Simplified; assume rules are versioned
JOIN
    findings f ON r.rule_id = f.rule_id
WHERE
    p.effective_date > '2023-01-01'
GROUP BY
    p.version_id, r.title
ORDER BY
    finding_count DESC;
```

**Expected Output:**
| version_id | effective_date | rule               | finding_count |
|------------|-----------------|--------------------|---------------|
| ver2.0     | 2023-05-15      | GDPR Article 25     | 4             |

---

### **2.4. Generate Compliance Reports**
**Use Case:** Export a dashboard-ready summary of compliance health.
```sql
SELECT
    r.title AS rule_category,
    COUNT(DISTINCT f.finding_id) AS total_findings,
    SUM(CASE WHEN f.severity = 'HIGH' THEN 1 ELSE 0 END) AS high_risk,
    MAX(a.name) AS example_asset,
    COUNT(DISTINCT CASE WHEN rp.status = 'closed' THEN f.finding_id END) AS resolved
FROM
    findings f
JOIN
    rules r ON f.rule_id = r.rule_id
JOIN
    assets a ON f.asset_id = a.asset_id
LEFT JOIN
    remediation_plans rp ON f.finding_id = rp.finding_id
GROUP BY
    r.title
ORDER BY
    high_risk DESC;
```

**Expected Output:**
| rule_category       | total_findings | high_risk | example_asset | resolved |
|---------------------|----------------|-----------|---------------|----------|
| PCI-DSS 6.1         | 12             | 3         | `credit_card_db` | 5        |

---

### **2.5. Simulate a Compliance Audit Walkthrough**
**Use Case:** Recreate an auditor’s workflow to validate controls.
```sql
-- Step 1: List all controls with their check status
SELECT
    c.control_id,
    r.title AS rule,
    a.name AS asset,
    STRING_AGG(check.status, ', ') AS check_statuses  -- Aggregate check results
FROM
    controls c
JOIN
    rules r ON c.rule_id = r.rule_id
JOIN
    assets a ON c.asset_id = a.asset_id
JOIN
    checks chk ON c.control_id = chk.control_id
GROUP BY
    c.control_id, r.title, a.name
HAVING
    STRING_AGG(check.status, ', ') LIKE '%FAILED%';  -- Controls with failed checks

-- Step 2: Drill into findings for failed checks
SELECT
    f.finding_id,
    f.description,
    chk.query AS validation_query
FROM
    findings f
JOIN
    checks chk ON f.asset_id = chk.asset_id
WHERE
    f.finding_id IN (
        SELECT finding_id FROM findings WHERE rule_id IN (
            SELECT rule_id FROM controls WHERE control_id IN (
                SELECT control_id FROM checks WHERE status = 'FAILED'
            )
        )
    );
```

---

## **3. Implementation Steps**
Deploy the **Compliance Troubleshooting pattern** in the following phases:

### **3.1. Define Compliance Rules and Assets**
1. **Ingest policies** from external sources (e.g., NIST CSF, ISO 27001) or internal documents.
   - Use a **policy-as-code** approach (e.g., YAML/JSON templates for rules).
   - Example rule template:
     ```yaml
     rule_id: r001
     title: "Data Retention for PII"
     version: "1.0"
     scope: ["databases", "s3_buckets"]
     description: "Sensitive data must be retained for 7 years."
     severity: MEDIUM
     controls:
       - implementation_type: "Automated (TTL)"
         check:
           type: "sql_query"
           query: "SELECT * FROM user_data WHERE created_at < CURRENT_DATE - INTERVAL '7 years';"
     ```

2. **Categorize assets** (e.g., databases, APIs, user accounts) and link them to rules via controls.

---

### **3.2. Automate Checks**
- **Embed checks** in existing workflows:
  - **Databases:** Use tools like **SQLAnarchy** or custom procedures to run validation queries.
  - **Cloud Services:** Leverage native APIs (e.g., AWS Config, GCP Security Command Center) or third-party tools (e.g., Prisma Cloud).
  - **Applications:** Integrate with CI/CD pipelines (e.g., GitLab CI, ArgoCD) to run checks on deployments.
- **Schedule checks** based on rule frequency (e.g., daily for critical controls, real-time for security events).

**Example Check Payload (API Format):**
```json
{
  "check_id": "chk001",
  "control_id": "cnt123",
  "asset_id": "asset456",
  "query": "SELECT COUNT(*) FROM user_roles WHERE role = 'admin' AND last_login > '2023-01-01';",
  "expected_result": "0",  -- No recent admin logins expected
  "status": "pending",
  "last_run": "2023-10-10T14:30:00Z"
}
```

---

### **3.3. Process Findings**
- **Automate triage**:
  - Escalate high-severity findings to **Slack/MS Teams** or **ticketing systems** (e.g., Jira, ServiceNow).
  - Example alert:
    ```json
    {
      "alert_type": "compliance_violation",
      "message": "High-severity finding in rule PCI-DSS 3.4 for asset `payment_db`.",
      "finding_id": "fdg789",
      "remediation_deadline": "2023-10-15"
    }
    ```
- **Manual validation**: Assign findings to compliance officers for review (e.g., via a **risk assessment portal**).

---

### **3.4. Remediate and Document**
- **Standardize remediation steps** per rule (e.g., "Apply encryption to S3 bucket").
- **Link remediation actions** to findings and audit logs:
  ```sql
  INSERT INTO audit_log_entries (
      action,
      user,
      timestamp,
      asset_id,
      finding_id,
      details
  ) VALUES (
      'remediation',
      'admin_user',
      NOW(),
      'asset456',
      'fdg789',
      'S3 bucket [bucket123] encrypted with SSE-KMS. Tested at 2023-10-12.'
  );
  ```
- **Close findings** only after verification (e.g., re-running checks).

---

### **3.5. Review and Improve**
- **Quarterly policy reviews**: Update rules based on regulatory changes (e.g., GDPR updates).
- **Analyze trends**: Use queries like the ones above to identify recurring compliance gaps.
- **Feedback loop**: Allow compliance teams to suggest rule improvements or new checks.

---

## **4. Tools and Integrations**
| **Tool Category**       | **Examples**                                                                 | **Use Case**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Rule Management**     | [Open Policy Agent (OPA)](https://www.openpolicyagent.org/), [PolicyHub](https://www.policydb.com/) | Define and version compliance rules.                                        |
| **Compliance Checkers** | [Trivy](https://aquasecurity.github.io/trivy/), [Checkmarx](https://checkmarx.com/) | Scan for vulnerabilities or configuration drift.                            |
| **Audit Logging**       | [ELK Stack](https://www.elastic.co/elk-stack), [Splunk](https://www.splunk.com/) | Centralize and analyze compliance events.                                   |
| **Workflow Orchestration** | [Airflow](https://airflow.apache.org/), [Temporal](https://temporal.io/)     | Schedule checks and remediations.                                           |
| **Ticketing**           | [Jira](https://www.atlassian.com/software/jira), [ServiceNow](https://www.servicenow.com/) | Track remediation tasks.                                                     |
| **Cloud Security**      | [AWS Config](https://aws.amazon.com/config/), [GCP Security Command Center](https://cloud.google.com/security-command-center) | Monitor cloud compliance.                                                     |
| **APIs**                | [ComplianceAsCode](https://www.complianceascode.org/), Custom REST APIs   | Trigger checks via CI/CD or event-driven workflows.                          |

---

## **5. Related Patterns**
Compliance Troubleshooting integrates with other patterns to create a **holistic compliance ecosystem**:

| **Pattern**                  | **Description**                                                                 | **Integration Point**                                                                 |
|------------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **[Policy as Code](https://www.complianceascode.org/)** | Define policies in machine-readable formats (e.g., Open Policy Agent).       | Use the same rule schema to generate compliance checks.                                |
| **[Observability for Security](https://cloud.google.com/blog/products/observability)** | Centralize logs, metrics, and traces for compliance events.                      | Feed audit logs from Compliance Troubleshooting into observability tools (e.g., Prometheus, Grafana). |
| **[Chaos Engineering](https://chaoss.com/)**               | Test system resilience to compliance breaches (e.g., simulate data leaks).     | Inject "compliance failures" into chaos experiments to validate recovery processes.    |
| **[FinOps Governance](https://finops.org/)**               | Align compliance with cost optimization (e.g., right-sizing assets for GDPR).  | Tag assets with compliance tags (e.g., `sensitive_data=true`) for FinOps queries.     |
| **[Security Personnel Onboarding](https://securitypersonnel.io/)** | Streamline access provisioning to comply with least-privilege principles.   | Automatically flag findings like "excessive user permissions" during onboarding.      |
| **[Configuration Management](https://en.wikipedia.org/wiki/Configuration_management)** | Ensure consistent system states for compliance.                              | Validate asset configurations against compliance rules (e.g., "all EC2 instances must have encryption enabled"). |

---

## **6. Best Practices**
1. **Start small**: Pilot with 1–2 high-impact rules (e.g., PCI-DSS encryption) before scaling.
2. **Automate where possible**: Manual checks increase human error and lag time.
3. **Document everything**: Use the `AuditLogEntry` table to maintain a trail of all actions.
4. **Train teams**: Compliance is a shared responsibility—train developers, ops, and legal teams on their roles.
5. **Plan for exceptions**: Allow "justifications" for temporary rule deviations (e.g., `finding_status = 'acknowledged'`) with clear deadlines.
6. **Leverage existing tools**: Integrate with your **SIEM** (e.g., Splunk), **ITSM** (e.g., ServiceNow), or **CSPM** (e.g., Prisma Cloud) to reduce duplication.

---

## **7. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│             │    │             │    │                 │    │             │
│  **Compliance**│    │ **Audit**  │    │ **Remediation**│    │ **Rule**    │