# **Debugging Cloud Migration: A Troubleshooting Guide**

## **Introduction**
Migrating workloads to the cloud is a complex process involving infrastructure, applications, data, and networking. Even with careful planning, issues can arise—from connectivity problems to performance bottlenecks, misconfigurations, or data inconsistencies. This guide provides a **structured, actionable approach** to diagnosing and resolving common cloud migration issues.

---

## **Symptom Checklist**
Before diving into fixes, classify the problem using this checklist:

### **Pre-Migration Issues**
| **Symptom**                          | **Possible Cause**                          | **Affected Area**               |
|--------------------------------------|--------------------------------------------|---------------------------------|
| Slow progress in discovery scans     | Network restrictions, permission issues   | **Infrastructure Validation**   |
| Incomplete dependency mapping       | Missing third-party libraries or services  | **Application Assessment**      |
| Unclear migration scope              | Unclear business requirements               | **Planning & Strategy**         |

### **During Migration Issues**
| **Symptom**                          | **Possible Cause**                          | **Affected Area**               |
|--------------------------------------|--------------------------------------------|---------------------------------|
| Failed lift-and-shift attempts       | Incompatible OS/configurations, missing IAM roles | **Infrastructure** |
| High latency in cross-region transfers | Suboptimal networking setup, misconfigured VPC peering | **Networking** |
| Database replication failures        | Network issues, incorrect triggers, or insufficient backup policies | **Data Migration** |
| Application crashes post-migration  | Misconfigured environment variables, missing dependencies | **Application Code** |

### **Post-Migration Issues**
| **Symptom**                          | **Possible Cause**                          | **Affected Area**               |
|--------------------------------------|--------------------------------------------|---------------------------------|
| Slower-than-expected performance     | Underprovisioned instances, inefficient queries | **Compute & Databases** |
| Unauthorized access attempts         | Misconfigured IAM policies, exposed endpoints | **Security** |
| Data inconsistency between old & new systems | Failed sync jobs, corrupted backups | **Data Sync & Validation** |

---
## **Common Issues & Fixes**
### **1. Infrastructure & Networking Problems**
#### **Issue: Failed VM/Container Deployment in Target Cloud**
- **Symptoms:**
  - VMs fail to boot with errors like `InstanceStart.Timeout` (AWS) or `Failed to pull image` (Kubernetes).
  - Containers hang during startup.

- **Root Causes:**
  - Incorrect security group rules (e.g., missing inbound rules for SSH/API ports).
  - Missing IAM roles/permissions for cloud resources.
  - Network interruptions (e.g., VPC peering misconfigurations).

- **Fixes:**
  - **Verify Security Groups/Firewall Rules** (AWS Example):
    ```bash
    # Check security group attached to an instance
    aws ec2 describe-security-groups --group-ids sg-XXXXXX
    ```
    - Ensure **SSH (22), HTTP (80), HTTPS (443)** are open for applicable workloads.

  - **Test IAM Role Permissions** (AWS Example):
    ```bash
    # Check if the role has needed permissions (e.g., EC2FullAccess)
    aws iam get-role-policy --role-name MigrationRole
    ```
    - Compare with required permissions (e.g., `ec2:DescribeInstances`).

  - **Network Connectivity Check**:
    ```bash
    # Ping target VPC from source (if using private subnet)
    ping <target-vpc-ip>
    # Test route tables for correct subnets
    aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-XXXXXX"
    ```

---

#### **Issue: Slow Cross-Region Data Transfer**
- **Symptoms:**
  - Database/backup jobs taking hours longer than expected.
  - API calls between regions have high latency (>500ms).

- **Root Causes:**
  - No **CloudFront CDN** or **global accelerator** in use.
  - Direct peering without **optimized routing** (e.g., AWS Direct Connect with redundant paths).

- **Fixes:**
  - **Enable AWS Direct Connect or VPC Peering with Optimized Routing**:
    ```bash
    # Check peering connections
    aws ec2 describe-vpc-peering-connections
    ```
    - Ensure **transitive peering** is allowed if needed.

  - **Use AWS Global Accelerator** (for low-latency apps):
    ```bash
    # Create a global accelerator
    aws globalaccelerator create-accelerator --name MyAppAccelerator ...
    ```

---

### **2. Application Deployment Failures**
#### **Issue: Application Crashes After Migration**
- **Symptoms:**
  - Logs show `500 errors`, `missing environment variables`, or `connection timeouts`.
  - Containers fail to start due to missing dependencies.

- **Root Causes:**
  - Hardcoded paths/configs (e.g., `/app/config` instead of `/opt/app/config`).
  - Missing **Docker/Kubernetes secrets** or **environment variables**.
  - Database connection strings not updated.

- **Fixes:**
  - **Check Application Logs** (AWS ECS Example):
    ```bash
    aws ecs describe-tasks --cluster my-cluster --tasks <task-id>
    ```
    - Look for `ERROR` entries in logs.

  - **Verify Environment Variables** (Docker/K8s Example):
    ```yaml
    # Kubernetes ConfigMap/Secret fix example
    env:
      - name: DB_HOST
        valueFrom:
          secretKeyRef:
            name: db-secret
            key: host
    ```

  - **Update Connection Strings** (Example in `config.json`):
    ```json
    // Before migration
    "DB_URL": "mysql://user:pass@old-db:3306/db"

    // After migration
    "DB_URL": "mysql://user:pass@new-rds-endpoint:3306/db"
    ```

---

### **3. Data Migration Issues**
#### **Issue: Incomplete or Corrupted Database Migration**
- **Symptoms:**
  - `COUNT(*)` mismatch between source and target.
  - Failed `aws rds export` jobs.

- **Root Causes:**
  - **Network timeouts** during large exports.
  - **Triggers/constraints** not disabled during migration.
  - **Incorrect backup policies** (e.g., no point-in-time recovery enabled).

- **Fixes:**
  - **Enable Binary Logging (MySQL Example)**:
    ```sql
    # Before migration, enable binary log
    SET GLOBAL binlog_format = 'ROW';
    SET GLOBAL log_bin = ON;
    ```
    - Restore using `mysqlbinlog` in AWS RDS.

  - **Use AWS DMS (Database Migration Service)**:
    ```bash
    # Start a DMS replication task
    aws dms start-replication-task --replication-task-identifier my-task
    ```

  - **Validate Data Consistency**:
    ```sql
    -- Compare row counts (PostgreSQL example)
    SELECT COUNT(*) FROM source_table;
    SELECT COUNT(*) FROM target_table;
    ```

---

## **Debugging Tools & Techniques**
### **1. Infrastructure Validation**
| **Tool**               | **Use Case**                                  | **Command/Example**                          |
|------------------------|-----------------------------------------------|----------------------------------------------|
| **Terraform/Terragrunt** | Detect drifting resources (e.g., `terraform plan`). | `terraform plan -out=tfplan -target=aws_instance.app` |
| **AWS Config**         | Audit compliance (e.g., missing security groups). | `aws configservice get-configuration-recorder-status` |
| **VPC Flow Logs**      | Troubleshoot network latency/blocks.          | `aws ec2 describe-flow-logs`                  |

### **2. Application Troubleshooting**
| **Tool**               | **Use Case**                                  | **Example**                                  |
|------------------------|-----------------------------------------------|----------------------------------------------|
| **AWS X-Ray**          | Trace API calls across services.              | Enable in CloudFormation template.           |
| **Kubernetes `kubectl`** | Check pod events/logs.                        | `kubectl get events -A`                      |
| **Prometheus/Grafana** | Monitor application metrics (e.g., latency).  | `curl http://<prometheus-server>:9090`       |

### **3. Data Validation Techniques**
| **Technique**          | **Use Case**                                  | **Example**                                  |
|------------------------|-----------------------------------------------|----------------------------------------------|
| **Checksum Verification** | Detect corrupted backups.                     | `sha256sum backup.sql.gz`                    |
| **AWS DMS Replication Instance** | Monitor DMS tasks in real-time. | `aws dms describe-replication-tasks`          |
| **Custom Validation Scripts** | Compare schema/data between systems. | Python script with `pandas` to compare tables. |

---

## **Prevention Strategies**
### **1. Pre-Migration Checklist**
✅ **Environment Parity:**
   - Test **lift-and-shift** in a staging environment first.
   - Use **containerization** (Docker/K8s) to reduce OS-specific issues.

✅ **Networking Best Practices:**
   - Enable **VPC Flow Logs** during migration.
   - Use **private subnets** for database layers.

✅ **Security Hardening:**
   - Restrict **IAM roles** to least privilege.
   - Enable **AWS GuardDuty** for anomaly detection.

### **2. Post-Migration Optimization**
🔹 **Right-Size Resources:**
   - Use **AWS Compute Optimizer** to suggest instance types.
   ```bash
   aws compute-optimizer recommend-instances --instance-type t3.medium
   ```

🔹 **Enable Auto-Scaling:**
   - Configure **Kubernetes HPA (Horizontal Pod Autoscaler)** or **AWS Auto Scaling Groups**.

🔹 **Monitor & Alert:**
   - Set up **CloudWatch Alarms** for:
     - High CPU/memory usage.
     - Failed API calls.
     - Unusual outbound traffic.

### **3. Documentation & Rollback Plan**
- **Document:**
  - **Pre-migration** (source DB schemas, app versions).
  - **Post-migration** (new architecture diagrams).
- **Rollback Strategy:**
  - Keep **source system operational** until validation is complete.
  - Use **AWS Backup** for automated failover.

---
## **Conclusion**
Cloud migration is rarely seamless, but a **structured debugging approach** minimizes downtime. Focus on:
1. **Networking & IAM** (most common blockers).
2. **Application config** (environment variables, dependencies).
3. **Data validation** (counts, checksums, DMS tasks).

**Pro Tip:** Automate checks where possible (e.g., Terraform drift detection, CI/CD pipeline validations).

---
**Need help?** Refer to:
- [AWS Migration Hub](https://aws.amazon.com/migration/)
- [Google Cloud Migration Docs](https://cloud.google.com/migration)
- [Azure Migrate](https://azure.microsoft.com/en-us/solutions/migrate/)