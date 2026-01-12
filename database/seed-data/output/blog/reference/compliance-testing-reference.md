# **[Pattern] Compliance Testing Reference Guide**

---

## **Overview**
The **Compliance Testing** pattern ensures that systems, applications, or services adhere to regulatory, industry-specific, or organizational standards. This reference guide outlines how to design, implement, and execute compliance tests to validate adherence to policies, laws (e.g., GDPR, HIPAA), or internal guidelines.

Compliance testing involves:
- **Automated validation** of configurations, data handling, and access controls.
- **Manual audits** to verify compliance in non-automatable areas (e.g., process documentation).
- **Integration with monitoring tools** to detect deviations in real time.
- **Reporting** to meet regulatory requirements (e.g., SOX, PCI-DSS).

This pattern is critical for **financial services, healthcare, data privacy, and supply chain management** industries, where non-compliance can lead to legal penalties, reputational damage, or operational disruption.

---

## **Schema Reference**

| **Component**          | **Description**                                                                                                                                                                                                 | **Example Fields/Parameters**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Compliance Rule**    | Defines a regulatory, industry, or organizational requirement (e.g., "User data must be encrypted at rest").                                                                                        | - Rule ID (e.g., `GDPR-ART25`)<br>- Rule name (e.g., "Encryption Standard")<br>- Severity (High/Medium/Low)<br>- Scope (Global/Region/Department)<br>- Compliance framework (GDPR, HIPAA, ISO 27001) |
| **Test Case**          | A specific validation check aligned to a compliance rule (e.g., "Verify database fields marked as PII are encrypted").                                                              | - Test ID (e.g., `GDPR-ART25-001`)<br>- Rule ID (FK)<br>- Test name<br>- Expected outcome (Pass/Fail)<br>- Automated/Manual flag<br>- Frequency (One-time/Scheduled/On-demand) |
| **Test Asset**         | System, data, or process under test (e.g., "Payment processing API," "Employee access logs").                                                                                                         | - Asset name (e.g., "API_v1.2")<br>- Asset type (Application, Database, Network)<br>- Owner (Team/Department)<br>- Last audited date |
| **Test Result**        | Outcome of executing a test case (e.g., "Failed: API logs contain unencrypted PII").                                                                                                                   | - Result date<br>- Test case ID (FK)<br>- Status (Pass/Failed/Not Applicable)<br>- Remediation steps<br>- Assigned to (Team/Individual)<br>- Resolution date |
| **Audit Trail**        | Log of changes to compliance rules, test cases, or results (for traceability).                                                                                                                      | - Action (Create/Update/Delete)<br>- User ID<br>- Timestamp<br>- Entity affected (Rule/Test Result)<br>- Old/new values |
| **Remediation Plan**   | Steps to address failed tests (e.g., "Update database encryption keys").                                                                                                                               | - Issue description<br>- Root cause<br>- Assignee<br>- Deadline<br>- Status (Open/In Progress/Resolved) |
| **Compliance Dashboard** | Visual summary of test coverage, pass/fail rates, and trend analysis.                                                                                                                                | - Time range (Last 30 days/Quarter)<br>- Filter by framework/team<br>- Export options (PDF/CSV) |

---

## **Implementation Details**

### **1. Key Concepts**
- **Regulatory vs. Internal Compliance**:
  - *Regulatory* (e.g., GDPR, SOX) requires strict adherence to laws with legal consequences for failure.
  - *Internal* (e.g., company security policies) may have softer enforcement but align with industry best practices.
- **Automated vs. Manual Testing**:
  - **Automated**: Scripted checks (e.g., scanning for unencrypted fields via CI/CD pipelines).
  - **Manual**: Human review (e.g., auditing access logs for unauthorized users).
- **Continuous vs. Static Testing**:
  - **Continuous**: Real-time monitoring (e.g., SIEM tools flagging policy violations).
  - **Static**: Periodic snapshots (e.g., quarterly GDPR audits).

### **2. Workflow Steps**
1. **Define Compliance Rules**
   - Map requirements from frameworks (e.g., GDPR’s "Right to Erasure") to internal rules.
   - Use a **rule engine** (e.g., Apache Drools) or **configuration management tools** (e.g., Ansible, Chef) to enforce rules.
   - *Example*: Rule `GDPR-ART25-001` → "All PII fields must be redacted within 72 hours of request."

2. **Design Test Cases**
   - For each rule, create **atomic test cases** (single verification point).
   - Example workflow:
     ```
     Rule: GDPR-ART25-001
     → Test Case 1: Verify PII fields are encrypted at rest.
     → Test Case 2: Audit database queries for unauthorized PII access.
     ```

3. **Select Test Assets**
   - Prioritize critical assets (e.g., payment systems, HR databases).
   - Use **asset inventories** (e.g., Microsoft Sentinel, ServiceNow) to track coverage.

4. **Execute Tests**
   - **Automated**:
     - Integrate with **CI/CD pipelines** (e.g., Jenkins, GitLab CI) to run tests on code/deploy changes.
     - Use **open-source tools** like OWASP ZAP (for web app vulnerabilities) or **commercial solutions** (e.g., Qualys, Tenable).
     - *Example Query* (Python + boto3 for AWS compliance):
       ```python
       import boto3
       ec2 = boto3.client('ec2')
       response = ec2.describe_instances()
       for instance in response['Reservations']:
           if 't3.micro' in str(instance['Instances'][0]['InstanceType']):
               print(f"Risk: Small instance ({instance['Instances'][0]['InstanceId']}) may not meet PCI-DSS storage requirements.")
       ```
   - **Manual**:
     - Conduct **walkthroughs** (e.g., reviewing role-based access controls).
     - Document findings in tools like **Jira** or **ServiceNow**.

5. **Record Results**
   - Log outcomes in a **centralized compliance database** (e.g., Postgres, Snowflake).
   - *Example Table Schema*:
     ```sql
     CREATE TABLE test_results (
         result_id SERIAL PRIMARY KEY,
         test_case_id INT REFERENCES test_cases(test_id),
         status VARCHAR(20), -- 'PASS', 'FAIL', 'NA'
         details TEXT,
         executed_at TIMESTAMP,
         remediation_steps JSONB,
         resolved_at TIMESTAMP,
         resolved_by VARCHAR(100)
     );
     ```

6. **Trigger Remediation**
   - Failed tests should auto-generate **tickets** (e.g., Jira) or **incidents** (e.g., PagerDuty).
   - Example Slack alert:
     ```
     ⚠️  **Compliance Alert** (GDPR-ART25-001 Failed)
     - Test Case: PII field 'ssn' not encrypted in DB 'users_prod'.
     - Remediation: Run `update_users_encryption.sh` by EOD.
     - Assigned To: @db-team
     ```

7. **Generate Reports**
   - Use **BI tools** (e.g., Tableau, Power BI) or **compliance-specific dashboards** (e.g., OpenCompliance).
   - *Key Metrics*:
     - % of assets tested vs. total.
     - Time to remediate failed tests (SLA compliance).

8. **Continuous Improvement**
   - Review **false positives/negatives** to refine test cases.
   - Update rules based on **framework updates** (e.g., GDPR amendments).

---

## **Query Examples**

### **1. Find All Failed Tests for a Specific Rule**
```sql
SELECT tr.result_id, tc.test_name, tr.details, tr.executed_at
FROM test_results tr
JOIN test_cases tc ON tr.test_case_id = tc.test_id
WHERE tc.rule_id = 'GDPR-ART25-001'
  AND tr.status = 'FAIL'
ORDER BY tr.executed_at DESC;
```

### **2. Audit Compliance Coverage by Asset Type**
```python
# Using pandas + SQLAlchemy (example for a healthcare asset audit)
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@db/compliance_db')
query = """
SELECT
    ta.asset_name,
    COUNT(tr.result_id) AS test_count,
    SUM(CASE WHEN tr.status = 'PASS' THEN 1 ELSE 0 END) AS passes,
    SUM(CASE WHEN tr.status = 'FAIL' THEN 1 ELSE 0 END) AS fails
FROM test_assets ta
LEFT JOIN test_results tr ON ta.asset_id = tr.asset_id
GROUP BY ta.asset_name
HAVING ta.asset_type = 'EHR';
"""
df = pd.read_sql(query, engine)
print(df[df['fails'] > 0])  # High-risk assets
```

### **3. Identify Assets Without Recent Testing**
```sql
SELECT ta.asset_name, ta.asset_type, MAX(tr.executed_at) AS last_tested
FROM test_assets ta
LEFT JOIN test_results tr ON ta.asset_id = tr.asset_id
GROUP BY ta.asset_name, ta.asset_type
HAVING last_tested < CURRENT_DATE - INTERVAL '30 days';
```

### **4. Generate a Compliance Heatmap (Simulated)**
*Input:* List of test results for a quarter.
*Output:* A table ranking teams by compliance performance.
```python
# Simulate heatmap in Python
results = {
    "QA Team": {"pass": 85, "fail": 15},
    "Security Team": {"pass": 98, "fail": 2},
    "DevOps": {"pass": 70, "fail": 30}
}
heatmap = pd.DataFrame([results]).T
heatmap['status'] = heatmap['fail'].apply(lambda x: '⚠️ Critical' if x > 20 else '✅ Good')
print(heatmap)
```

---

## **Related Patterns**
1. **[Policy as Code](https://www.policy-as-code.org/)**
   - *Connection*: Compliance testing relies on policy-as-code tools (e.g., Open Policy Agent) to automate rule enforcement and validation.

2. **[Configuration Management](https://en.wikipedia.org/wiki/Configuration_management)**
   - *Connection*: Use tools like **Puppet, Ansible, or Terraform** to ensure systems are configured according to compliance requirements before testing.

3. **[Observability](https://www.datadoghq.com/blog/observability-vs-monitoring/)**
   - *Connection*: Comprehensive logging and monitoring (e.g., Prometheus, Grafana) are critical for detecting compliance violations in real time.

4. **[Chaos Engineering](https://principlesofchaos.org/)**
   - *Connection*: Chaos testing (e.g., Gremlin) can inadvertently expose compliance gaps by stress-testing resilience.

5. **[Data Masking/Redaction](https://www.veracode.com/blog/security/data-masking-vs-data-redaction)**
   - *Connection*: Compliance testing often requires verifying that sensitive data is masked or redaction is applied correctly (e.g., GDPR’s "Right to Erasure").

6. **[Audit Logging](https://www.auditing.com/audit-logging/)**
   - *Connection*: Compliance testing depends on robust audit trails to track access and changes to sensitive systems.

7. **[Secret Management](https://medium.com/faun/secret-management-is-a-mess-let-s-fix-it-258f843f4d36)**
   - *Connection*: Compliance tests must validate that secrets (e.g., API keys) are stored securely and rotated as required (e.g., PCI DSS 3.2.6).

---
**Note**: For industry-specific compliance (e.g., **HIPAA, SOC 2, PCI DSS**), consult official frameworks for rule details. Always align testing with the **latest versions** of compliance standards.