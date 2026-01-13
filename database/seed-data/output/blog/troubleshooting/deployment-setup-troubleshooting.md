# **Debugging Deployment Setup: A Troubleshooting Guide**

## **1. Introduction**
Deployment Setup refers to the process of configuring, testing, and validating environments (e.g., staging, production) before launching applications. Issues in this phase can lead to downtime, misconfigurations, or failed deployments. This guide focuses on common **Deployment Setup** problems, their root causes, and actionable fixes.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

✅ **Deployment Fails Silently** – No logs, errors, or rollback.
✅ **Environment Mismatch** – Staging behaves differently than production.
✅ **Resource Limits Exceeded** – OOM errors, disk full, or CPU throttling.
✅ **Missing Dependencies** – Libraries, configs, or DB schemas not present.
✅ **Permission Denied** – API keys, IAM roles, or file access issues.
✅ **Slow Rollout** – Slow startup, high latency, or timeouts.
✅ **Unreliable Rollback** – Failed rollbacks or orphaned deployments.
✅ **Logging/Monitoring Gaps** – Missing telemetry or failed metrics collection.
✅ **CI/CD Pipeline Errors** – Build failures, failed linting, or missing tests.
✅ **Network/Connectivity Issues** – Firewall blocks, DNS failures, or proxy misconfigurations.

---

## **3. Common Issues & Fixes**

### **3.1 Deployment Fails Without Logs**
**Root Cause:** Missing logging, improper error handling, or corrupted deployment artifacts.

#### **Debugging Steps:**
1. **Check CI/CD Logs**
   - Look for build errors in GitHub Actions, GitLab CI, or Jenkins.
   - Example GitHub Actions error:
     ```yaml
     steps:
       - name: Build Docker Image
         run: docker build -t my-app .
     ```
     - If failing, check `docker build` logs:
       ```sh
       docker build --no-cache -t my-app .
       ```

2. **Enable Debug Logging in Deployment Scripts**
   ```bash
   # Example: Kubernetes deployment with verbose logs
   kubectl apply -f deployment.yaml --field-manager=kustomize --dry-run=client -o yaml | grep -i error
   ```

3. **Inspect Artifact Integrity**
   ```bash
   # Verify Docker image layers
   docker history my-app | grep "Open in another window"

   # Check file checksums
   sha256sum app.jar
   ```

---

### **3.2 Environment Mismatch (Staging vs. Production)**
**Root Cause:** Missing `.env` variables, differing config files, or untested environment variables.

#### **Debugging Steps:**
1. **Compare Config Files**
   ```bash
   # Diff prod vs. staging configs
   diff staging/config.json production/config.json
   ```

2. **Use Environment-Aware Configs**
   ```bash
   # Example: Deploy with env-specific configs
   if [ "$DEPLOY_ENV" == "production" ]; then
     cp config-prod.json config.json
   else
     cp config-dev.json config.json
   fi
   ```

3. **Validate with Linting**
   ```yaml
   # Example: Schematize configs (using JSON Schema)
   schema.yml:
     type: object
     properties:
       DB_URL:
         type: string
   ```
   ```sh
   jsonschema -i config.json schema.yml
   ```

---

### **3.3 Resource Limits Exceeded (OOM, Disk Full)**
**Root Cause:** Misconfigured `limits` in Kubernetes, Docker, or misbehaving services.

#### **Debugging Steps:**
1. **Check Kubernetes Resource Limits**
   ```yaml
   # Example: Adjust pod limits
   resources:
     limits:
       cpu: "1"
       memory: "512Mi"
     requests:
       cpu: "500m"
       memory: "256Mi"
   ```

2. **Monitor Resource Usage**
   ```sh
   kubectl top pods --all-namespaces
   kubectl describe pod <pod-name> | grep Limits
   ```

3. **Optimize Docker Containers**
   ```sh
   docker stats --no-stream | grep -i "cpu%|mem%"
   ```

---

### **3.4 Missing Dependencies**
**Root Cause:** Incorrect `requirements.txt`, missing Docker layers, or stale DB migrations.

#### **Debugging Steps:**
1. **Reinstall Python Dependencies**
   ```sh
   pip freeze > requirements.txt
   pip install -r requirements.txt
   ```

2. **Check Docker Layer Cache**
   ```sh
   docker system df  # Check disk usage
   docker builder prune -a  # Clean cache
   ```

3. **Compare DB Schemas**
   ```sql
   -- Check for missing tables
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   ```

---

### **3.5 Permission Denied (API Keys, IAM Roles)**
**Root Cause:** Incorrect permissions, expired keys, or misconfigured RBAC.

#### **Debugging Steps:**
1. **Check Kubernetes RBAC**
   ```yaml
   # Example: Fix a role binding
   apiVersion: rbac.authorization.k8s.io/v1
   kind: RoleBinding
   metadata:
     name: default-allow
   subjects:
   - kind: User
     name: system:serviceaccount:default:default
   roleRef:
     kind: ClusterRole
     name: edit
   ```

2. **Verify AWS IAM Policies**
   ```sh
   aws iam list-attached-user-policies --user-name my-user
   ```

3. **Check File Permissions**
   ```sh
   ls -la /path/to/config  # Ensure correct permissions
   chmod 644 config.json
   ```

---

### **3.6 Slow Rollout (High Latency, Timeouts)**
**Root Cause:** Cold starts, inefficient networking, or unoptimized database queries.

#### **Debugging Steps:**
1. **Check Docker Build Time**
   ```sh
   time docker build -t my-app .
   ```

2. **Optimize Kubernetes Scaling**
   ```yaml
   # Example: Use Horizontal Pod Autoscaler (HPA)
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: my-app-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: my-app
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

3. **Profile Slow DB Queries (PostgreSQL Example)**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active';
   ```

---

### **3.7 Failed Rollbacks**
**Root Cause:** Orphaned resources, broken health checks, or incomplete rollback scripts.

#### **Debugging Steps:**
1. **Check Kubernetes Rollback**
   ```sh
   kubectl rollout undo deployment/my-app --to-revision=2
   kubectl rollout status deployment/my-app
   ```

2. **Verify Health Checks**
   ```yaml
   # Example: Fix liveness probe
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
     initialDelaySeconds: 5
     periodSeconds: 10
   ```

3. **Clean Up Orphaned Resources**
   ```sh
   kubectl get all --all-namespaces | grep "Completed"
   kubectl delete pod --all --force
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example Command/Setup** |
|--------------------------|---------------------------------------|---------------------------|
| **kubectl**              | Debug Kubernetes deployments          | `kubectl logs -f <pod>`   |
| **Docker Diagnostics**   | Check container health               | `docker inspect <container>` |
| **Prometheus/Grafana**   | Monitor resource usage                | `kubectl port-forward svc/prometheus 9090` |
| **JTidy (Java)**         | Analyze slow GC pauses                | `java -XX:+PrintGCDetails -XX:+PrintGCDateStamps` |
| **Terraform Apply --var-file** | Compare TF state vs. live env | `terraform apply -var-file=staging.tfvars` |
| **Traceroute/Ping**     | Network latency issues                | `traceroute 8.8.8.8`      |
| **strace/ltrace**        | System call debugging                 | `strace -p <PID>`         |
| **AWS CloudTrail**       | Track IAM/API changes                 | `aws cloudtrail lookup-events` |
| **Git Bisect**           | Find broken commits                   | `git bisect start HEAD~5 HEAD` |

---

## **5. Prevention Strategies**

### **5.1 Pre-Deployment Checklist**
✔ **Run `docker build --no-cache`** (avoids stale layers)
✔ **Validate configs with schematization** (e.g., JSON Schema)
✔ **Test rollbacks manually** (e.g., `kubectl rollout undo`)
✔ **Enable audit logging** (Kubernetes, AWS, databases)
✔ **Use canary deployments** for risky updates

### **5.2 CI/CD Best Practices**
🔹 **Fail Fast** – Reject builds with missing tests or lint errors.
🔹 **Immutable Deployments** – Never modify running containers.
🔹 **Blue-Green or Canary Deployments** – Reduce risk of failed rollouts.
🔹 **Automated Rollback Triggers** – Rollback on error spikes.

### **5.3 Monitoring & Observability**
📊 **Centralized Logging** (ELK, Loki)
📈 **Metrics Collection** (Prometheus, Datadog)
🔍 **Distributed Tracing** (Jaeger, OpenTelemetry)

### **5.4 Documentation & Runbooks**
📝 **Document deployment steps** (e.g., Ansible playbooks, Terraform modules).
📝 **Maintain a troubleshooting runbook** (e.g., "How to fix OOM in Kubernetes").

---

## **6. Conclusion**
Deployment Setup issues are often traceable to **environment mismatches, misconfigurations, or missing dependencies**. By following this guide, you can:
✅ **Quickly identify root causes** using logs and diagnostics.
✅ **Apply fixes with minimal downtime** (e.g., adjusting resource limits).
✅ **Prevent future issues** with automation and observability.

**Next Steps:**
- **Automate rollback tests** in CI.
- **Set up alerts** for resource anomalies.
- **Document critical deployment steps** for the team.

---
**Need deeper debugging?** Check:
- Kubernetes: [`kubectl debug`](https://kubernetes.io/docs/tasks/debug/)
- Docker: [`docker events`](https://docs.docker.com/engine/cli/commandline/events/)
- AWS: [CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)