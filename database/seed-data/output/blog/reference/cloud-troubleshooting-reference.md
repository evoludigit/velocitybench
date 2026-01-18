---
# **[Pattern] Cloud Troubleshooting Reference Guide**

---

## **1. Overview**
This guide provides a structured, systematic approach to diagnosing, resolving, and preventing issues in cloud-based systems. Cloud troubleshooting leverages cloud-specific tools (e.g., logs, metrics, and native monitoring) alongside general troubleshooting principles (e.g., isolation, repro steps). The pattern is designed for **cloud architects, DevOps engineers, and support teams** to quickly identify root causes, mitigate disruptions, and optimize cloud performance.

Key focus areas:
- **Proactive detection** via monitoring and alerts.
- **Isolation of issues** (e.g., service-level vs. infrastructure-level failures).
- **Use of cloud provider tools** (AWS CloudWatch, Azure Monitor, GCP Stackdriver).
- **Log correlation** across services and regions.
- **Documentation of incidents** for future reference.

---

## **2. Key Concepts & Schema Reference**

| **Concept**               | **Definition**                                                                                                                                                                                                       | **Tools/Attributes**                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **Cloud Service Level**   | Categorizes issues by scope: **Infrastructure (e.g., compute, storage, network)**, **Application (e.g., APIs, microservices)**, or **Data (e.g., databases, backups)**.                                          | AWS: Service Quotas, Billing Console<br>Azure: Service Health<br>GCP: Status Dashboard                                               |
| **Log Analysis**          | Parsing cloud logs (CLI, SDKs, or native dashboards) to identify patterns, errors, or anomalies.                                                                                                                 | AWS: CloudWatch Logs Insights<br>Azure: Log Analytics<br>GCP: Logs Explorer                                                   |
| **Metrics & Alerts**      | Real-time monitoring of cloud resources (e.g., CPU, latency, error rates) with configurable thresholds for alerts.                                                                                              | AWS: CloudWatch Alarms<br>Azure: Metrics + Alerts<br>GCP: Metric Explorer + Alerting Policies                                          |
| **Incident Workflow**     | Step-by-step process to escalate, document, and resolve issues (e.g., triage → diagnosis → mitigation → postmortem).                                                                                     | Slack/Teams integration, Jira, PagerDuty                                                                                                |
| **Dependency Mapping**    | Visualizing service dependencies to pinpoint cascading failures or bottlenecks.                                                                                                                              | AWS: CloudFormation/Nested Stacks<br>Azure: Resource Graph<br>GCP: Deployment Manager                                                   |
| **Rollback Strategy**     | Reverting to a stable state (e.g., previous deployment, configuration change, or version) when failures occur.                                                                                                | AWS: CodeDeploy<br>Azure: Deployment Slots<br>GCP: Cloud Run Rollback                                                                     |
| **Cost Anomalies**        | Detecting unexpected spikes in cloud spending (e.g., over-provisioned resources, unused instances).                                                                                                          | AWS: Cost Explorer<br>Azure: Cost Analysis<br>GCP: Billing Reports                                                                           |
| **Security Audits**       | Reviewing cloud configurations for vulnerabilities (e.g., misconfigured IAM, open ports, data leaks).                                                                                                       | AWS: AWS Config + GuardDuty<br>Azure: Defender for Cloud<br>GCP: Security Command Center                                               |

---

## **3. Implementation Steps**

### **Step 1: Triage & Isolation**
1. **Classify the Issue**:
   - *Is it a service disruption (e.g., AWS RDS failure) or a custom app error?*
   - Use provider’s **status page** (e.g., [AWS Health](https://health.aws.amazon.com/)) to check for outages.
2. **Check Logs**:
   - **Example Query (AWS CloudWatch Logs Insights)**:
     ```sql
     filter @type = "ERROR"
     | stats count(*) by @logStream, @message
     | sort @message desc
     ```
   - **Azure Log Analytics**:
     ```kql
     SecurityEvent
     | where EventID == 4625
     | project TimeGenerated, AccountName, Computer
     ```

### **Step 2: Diagnose Root Cause**
#### **A. Performance Bottlenecks**
- **High CPU/Memory (AWS)**: Check `CPUUtilization` or `MemoryUtilization` in CloudWatch.
  ```sql
  stats avg(cpu_usage) by instance_id
  | sort -avg(cpu_usage)
  ```
- **Latency Spikes (GCP)**: Use `latency` metric in Stackdriver.
  ```bash
  gcloud monitoring query-time-series \
    --format=value-only \
    'metric.type="run.googleapis.com/instance/cpu/utilization"'
  ```

#### **B. Dependency Failures**
- **Azure Resource Graph Query**:
  ```kql
  resources
  | where type =~ 'Microsoft.Net/application'
  | project name, resourceGroup
  | join kind=inner (
      alerts
      | where severity == 'Critical'
      ) on $left.name == $right.resourceId
  ```

#### **C. Configuration Drift**
- **AWS Config Compliance Check**:
  ```bash
  aws configservice get-compliance-summary-by-config-rule \
    --resource-type EC2_INSTANCE \
    --config-rule-name "required-tags"
  ```

### **Step 3: Mitigate & Resolve**
| **Scenario**               | **Action Items**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Infrastructure Failure** | - **Restart services**: `az vm restart --resource-group myRG --name myVM` (Azure)<br>- **Scale out**: Increase auto-scaling group (AWS)<br>- **Patch dependencies**: Use provider’s support ticket system.           |
| **Application Crash**      | - **Rollback**: Trigger a previous deployment (e.g., `gcloud run rollback rev-${REVISION_ID}`)<br>- **Restart workloads**: Kubernetes: `kubectl rollout restart deployment <name>`                       |
| **Security Breach**        | - **Isolate compromised resources**: Detach IAM roles, revoke keys.<br>- **Rotate secrets**: Use AWS Secrets Manager/Vault.<br>- **Enable auditing**: Check `audit_log` in GCP.                                |

### **Step 4: Post-Incident Review**
- **Document findings** in a template (example below):
  ```markdown
  ## Incident Summary
  - **Date**: 2023-10-15
  - **Severity**: P1
  - **Root Cause**: Database query timeout due to unoptimized index.
  - **Resolution**: Added index on `user_id` column in DynamoDB.
  - **Prevention**: Scheduled CloudWatch alarm for `ThrottledRequests`.
  ```
- **Update runbooks**: Add steps to the team’s shared knowledge base (e.g., Confluence, Notion).

---

## **4. Query Examples by Cloud Provider**

### **AWS**
| **Use Case**               | **Query/Command**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Find EC2 instances with high CPU** | `aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query "Reservations[*].Instances[*].[InstanceId,State.Name]"` + CloudWatch `cpu_usage > 80%`. |
| **List S3 bucket permissions** | `aws s3api get-bucket-policy --bucket my-bucket`                                                                                                                                                         |
| **Check RDS storage limits**   | `aws rds describe-db-instances --query "DBInstances[?StorageType=='gp2'].StorageInfo"`                                                                                                                   |

### **Azure**
| **Use Case**               | **Query/Command**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **List VMs with failed health checks** | `az vm list --query "[?powerState!='VM deallocated'].{Name:name,ResourceGroup:resourceGroup}" --output table` + `az monitor activity-log list --resource-group <RG> --top 10 --query "[?operationName=='Microsoft.Compute/virtualMachines/restart']"` |
| **Find overly permissive roles** | `az role assignment list --assignee "user@example.com" --scope "/" --output table`                                                                                                                        |
| **Check App Service errors** | `az webapp log tail --name myapp --resource-group myRG`                                                                                                                                                     |

### **Google Cloud Platform (GCP)**
| **Use Case**               | **Query/Command**                                                                                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **List VMs with high disk usage** | `gcloud compute instances list --filter="status=RUNNING" --format="value(name,diskSizeGb)"` + `gcloud compute disks describe <DISK_NAME> --format="json"`                      |
| **Find IAM users with elevated permissions** | `gcloud iam list-roles --enabled` + `gcloud projects get-iam-policy PROJECT_ID`                                                                                                                        |
| **Check Cloud Run service latency** | `gcloud run services describe SERVICE_NAME --format="value(status.latency)"`                                                                                                                            |

---

## **5. Related Patterns**
For a comprehensive troubleshooting workflow, integrate these patterns:
1. **[Observability](https://patterns.dev/observability)**
   - *Link*: Cloud monitoring + logging + tracing (e.g., AWS X-Ray, Azure Application Insights).
2. **[Chaos Engineering](https://patterns.dev/chaos)**
   - *Link*: Proactively test failure scenarios (e.g., Gremlin, Chaos Mesh).
3. **[Infrastructure as Code (IaC)](https://patterns.dev/iac)**
   - *Link*: Reproduce environments using Terraform/ARM/Bicep for consistent troubleshooting.
4. **[Security Hardening](https://patterns.dev/security)**
   - *Link*: Prevent issues via least-privilege IAM, encryption, and regular audits.
5. **[Auto-Remediation](https://patterns.dev/auto-remediate)**
   - *Link*: Automate fixes (e.g., AWS Auto Scaling, Azure Logic Apps).

---
## **6. Best Practices**
- **Proactive Monitoring**: Set up alerts for **SLOs** (e.g., 99.9% uptime) using provider dashboards.
- **Log Retention**: Configure log archiving (e.g., AWS CloudWatch Logs: 30+ days).
- **Cross-Region Failover**: Design for **multi-region deployments** to isolate regional outages.
- **Incident Simulations**: Run **tabletop exercises** with the team to refine response plans.
- **Third-Party Tools**: Supplement native tools with **Splunk, Datadog, or New Relic** for advanced analytics.