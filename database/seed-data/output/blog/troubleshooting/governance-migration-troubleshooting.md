# **Debugging Governance Migration: A Troubleshooting Guide**

## **1. Introduction**
The **Governance Migration** pattern involves systematically moving governance rules, policies, and access controls from legacy systems to a new architecture (e.g., microservices, cloud-native, or zero-trust environments). Misconfiguration, permission drift, and incomplete rule mapping are common pitfalls.

This guide provides a structured approach to diagnosing and resolving issues during **Governance Migration**, ensuring minimal downtime and enforceable compliance.

---

## **2. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom**                          | **Description**                                                                 | **Severity** |
|--------------------------------------|---------------------------------------------------------------------------------|--------------|
| **Permission Denied Errors**         | Users or services fail to access resources despite correct credentials.           | High         |
| **Rule Mismatch Warnings**           | New governance rules differ from old ones, causing inconsistencies.              | High         |
| **Audit Trail Gaps**                 | Missing or incorrect log entries in governance migrations.                      | Medium       |
| **Performance Degradation**          | Slower policy evaluation or enforcement due to inefficient rule checks.          | Medium       |
| **Unintended Access Grants**         | Users/services gain unexpected privileges after migration.                       | Critical     |
| **Integration Failures**             | Legacy systems reject new governance formats (e.g., JSON vs. XML policies).       | High         |
| **Role/Service Account Leaks**       | Over-privileged accounts remain unrevoked post-migration.                       | Critical     |
| **Compliance Failure Notifications** | Third-party audits flag missing or misapplied governance rules.                 | High         |

---
## **3. Common Issues & Fixes**

### **A. Permission Denied Errors (Most Critical)**
**Symptom:** `AccessDenied` errors during API calls, DB queries, or file operations.

**Root Causes:**
1. **Incorrect Role Mapping** – Legacy roles not fully converted to new IAM roles.
2. **Temporary Cache Issues** – Local auth caches haven’t synced with new policies.
3. **Overlapping Permissions** – Conflicting policies allow unintended access.

**Debugging Steps:**
1. **Check Policy Snapshots**
   Compare old vs. new policies:
   ```bash
   # AWS Example: Compare IAM policies
   aws iam list-policy-versions --policy-arn "old-policy-arn" --query "Versions[?VersionId != '1']"
   ```
   *(Ensure versions match expected governance rules.)*

2. **Test with Minimal Permissions**
   Grant a service account only what it needs:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:GetObject"],
         "Resource": "arn:aws:s3:::bucket/*"
       }
     ]
   }
   ```

3. **Clear Auth Caches**
   If using local caching (e.g., `stash` or `aws-vault`), reset:
   ```bash
   aws-vault logout  # Invalidate cached credentials
   ```

**Fix:**
- **Re-map Legacy Roles** to new IAM roles using a mapping spreadsheet.
- **Use Least Privilege** – Audit tools like `aws iam list-policies` to refine permissions.

---

### **B. Rule Mismatch Warnings**
**Symptom:** "Policy X differs from expected rules" in monitoring dashboards.

**Root Causes:**
1. **Manual Rule Exceptions** – Ad-hoc overrides not documented.
2. **Version Drift** – Old rules not deprecated in favor of new ones.
3. **Misaligned Definitions** – Terms like "admin" mean different things in old vs. new systems.

**Debugging Steps:**
1. **Diff Policy Files**
   ```bash
   diff old-policy.json new-policy.json
   ```
   *(Highlight deviations in RBAC or attribute-based rules.)*

2. **Audit Change Logs**
   ```bash
   # Example: Check Git history for policy changes
   git log --oneline -- policy/
   ```

**Fix:**
- **Standardize Rule Definitions** (e.g., enforce `admin` = `IAMUserRole:Admin`).
- **Automate Policy Syncs** via CI/CD (e.g., Terraform modules for IAM).

---

### **C. Audit Trail Gaps**
**Symptom:** Missing logs for recent governance changes.

**Root Causes:**
1. **Unconfigured Logging** – New systems lack audit hooks.
2. **Log Retention Issues** – Cloud providers truncate old logs.

**Debugging Steps:**
1. **Verify Log Streaming**
   ```bash
   # Check CloudTrail for IAM changes
   aws cloudtrail lookup-events --lookup-attributes '{"AttributeKey": "EventName", "AttributeValue": "CreatePolicyVersion"}'
   ```

2. **Check Retention Policies**
   ```bash
   # AWS S3 bucket lifecycle config
   aws s3api get-bucket-lifecycle --bucket audit-logs-bucket
   ```

**Fix:**
- **Enable Centralized Logging** (e.g., AWS OpenSearch, Datadog).
- **Set Retention Policies** (e.g., 90 days for governance logs).

---

### **D. Performance Degradation in Policy Evaluation**
**Symptom:** Slow access decisions (e.g., 2s+ latency for API gateways).

**Root Causes:**
1. **Complex Ruleset** – Too many nested conditions.
2. **Synchronous Validation** – Policy checks block requests.
3. **Slow Backend Lookups** – Over-reliance on databases for RBAC.

**Debugging Steps:**
1. **Profile Policy Engine**
   ```python
   # Example: Measure time for policy evaluation
   import time
   start = time.time()
   policy.eval(request)  # Your governance engine
   print(f"Latency: {time.time() - start}s")
   ```

2. **Check Database Queries**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM permissions WHERE service = 'api-gateway';
   ```

**Fix:**
- **Optimize Rules** – Simplify conditions (e.g., flatten nested `if-else`).
- **Cache Results** – Use Redis for frequent policy lookups.

---

### **E. Unintended Access Grants**
**Symptom:** Users/services suddenly gain excessive permissions.

**Root Causes:**
1. **Overly Broad Policies** – Wildcard resources (`*`) in IAM.
2. **Automated Rollouts** – CI/CD pipelines misapplied rules.
3. **Human Error** – Manual policy edits not reviewed.

**Debugging Steps:**
1. **Scan for Over-Permissive Policies**
   ```bash
   # AWS IAM policy scanner
   aws iam get-policy-version --policy-arn "arn:aws:iam::123456789012:policy/old-policy"
   ```
   *(Look for `"*": "*"` patterns.)*

2. **Check Last Modified Dates**
   ```bash
   aws iam list-policy-versions --policy-arn "arn:aws:iam::123456789012:policy/old-policy" --query "Versions[].LastUpdatedDate"
   ```

**Fix:**
- **Enforce Policy-as-Code** (e.g., OPA/Gatekeeper for Kubernetes).
- **Use Automated Reviews** (e.g., AWS IAM Access Analyzer).

---

## **4. Debugging Tools & Techniques**

### **A. Automated Scanning Tools**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|------------------------------------------------------------------------------|-----------------------------------------------|
| **AWS IAM Policy Simulator** | Test if a policy allows unintended access.                                | `aws iam simulate-principal-policy`         |
| **OPA/Gatekeeper**     | Runtime policy enforcement in Kubernetes.                                    | `gatekeeper audit all`                       |
| **Open Policy Agent (OPA)** | Evaluate policies against inputs.                                           | `opa eval -m policy.rego --input file.json`  |
| **AWS Config**         | Continuously assess IAM policies for compliance.                             | `aws configrule create --name "deny-public-s3"` |
| **Chef/Ansible Inspec** | Validate governance rules on servers.                                        | `inspec exec compliance_suite.rb`           |

### **B. Log & Metric Analysis**
1. **CloudTrail + CloudWatch** – Track IAM changes.
   ```bash
   aws logs filter-log-events --log-group-name "/aws/cloudtrail/management" --log-stream-name "*"
   ```
2. **Prometheus + Grafana** – Monitor policy evaluation latency.
   ```yaml
   # Example: Alert on slow policy checks
   - alert: HighPolicyLatency
     expr: rate(policy_evaluation_seconds{status="error"}[1m]) > 0.1
     for: 5m
   ```

### **C. Unit Testing for Governance**
```python
# Example: Unit test policy decision
def test_service_can_read_db(request, policy):
    assert policy.allow(request, {"action": "read", "resource": "db:user1"}) == True
```

---

## **5. Prevention Strategies**

### **A. Pre-Migration Checklist**
- [ ] **Audit Old Rules** – Map every legacy policy to a new format.
- [ ] **Simulate Failures** – Test rollback plans.
- [ ] **Document Assumptions** – Record unspoken governance rules.
- [ ] **Phased Rollout** – Migrate non-critical services first.

### **B. Post-Migration Best Practices**
- **Tag All Resources** – Enable granular access control.
  ```bash
  aws ec2 create-tags --resources "i-123456" --tags "Key=governance,Value=critical"
  ```
- **Automate Reviews** – Use tools like **Open Policy Agent (OPA)** for real-time checks.
- **Enforce Least Privilege** – Regularly audit and revoke unused permissions.
- **Monitor Drift** – Set up alerts for unauthorized changes.

### **C. Backup & Rollback Plan**
```bash
# Example: Store old policies in version control
git add old-policy.json
git commit -m "Backup pre-migration governance rules"
```

---

## **6. Summary of Key Actions**
| **Issue**               | **Immediate Fix**                          | **Long-Term Solution**                     |
|-------------------------|--------------------------------------------|-------------------------------------------|
| Permission Denied       | Revoke/reapply roles via CLI.              | Auto-generate IAM roles from Git.         |
| Rule Mismatch           | Audit policy diffs.                        | Use OPA for dynamic policy enforcement.   |
| Audit Trail Gaps        | Enable CloudTrail + OpenSearch.            | Set log retention policies.                |
| Performance Lag         | Cache policy results.                      | Optimize ruleset complexity.              |
| Unintended Access       | Run IAM Access Analyzer.                   | Enforce least privilege via CI/CD.        |

---
## **7. Final Notes**
Governance Migration is **not just technical**—it requires governance ownership across teams. Use **automation** to reduce human error, **testing** to catch edge cases, and **monitoring** to Detect drift early.

For severe issues, **rollback to a known-good state** before debugging further. Always document changes in a **governance runbook** for future reference.

---
**Need deeper help?** Check:
- [AWS IAM Best Practices](https://aws.amazon.com/blogs/mt/)
- [Open Policy Agent Docs](https://www.openpolicyagent.org/docs/latest/)