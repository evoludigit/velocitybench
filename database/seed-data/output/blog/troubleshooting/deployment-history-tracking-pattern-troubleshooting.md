# **Debugging *Fraisier: Deployment History and Audit Trail Tracking* – A Troubleshooting Guide**
*Ensuring accurate deployment tracking, rollback capability, and audit trails in CI/CD pipelines*

---

## **1. Symptom Checklist**
Before diving into fixes, confirm which symptoms you’re experiencing. Check all that apply:

| **Symptom**                                  | **Severity** | **Diagnosed?** |
|---------------------------------------------|--------------|----------------|
| Cannot trace a bug to a specific deployment  | ⭐⭐⭐⭐⭐      | [ ]            |
| Missing rollback capability after failed deploy | ⭐⭐⭐⭐       | [ ]            |
| No record of who deployed what (user/audit logs) | ⭐⭐⭐⭐ | [ ]           |
| Deployment failures lack clear failure context | ⭐⭐⭐        | [ ]            |
| Manual commit/diff analysis for troubleshooting | ⭐⭐⭐        | [ ]            |
| Inconsistent deployment versions across environments | ⭐⭐⭐        | [ ]            |
| No versioned artifacts stored (e.g., Docker images) | ⭐⭐         | [ ]            |

**Next Steps:**
- If multiple ⭐⭐⭐⭐⭐ symptoms → **Critical: Audit trail and rollback are broken** (Jump to Section 3.1).
- If only some → **Start with diagnostics** (Section 4).

---

## **2. Common Issues & Fixes**

### **2.1 Issue: No Deployment History or Audit Trail**
**Symptoms:**
- No logs show who deployed, when, or which code was released.
- Manual `git log` checks fail to correlate with production changes.

**Root Causes:**
- **Missing CI/CD pipeline metadata** (e.g., no `DEPLOYMENT_ID` or `git SHA` tags).
- **Audit logs not integrated** (e.g., Jenkins/GitLab CI lacks logging).
- **Manual deployments bypass tracking** (e.g., SSH `scp` + `bash` scripts).

---
#### **Fixes**
##### **Option A: Instrument CI/CD Pipeline (GitLab CI Example)**
Add metadata to your `.gitlab-ci.yml`:
```yaml
stages:
  - deploy

deploy_prod:
  stage: deploy
  script:
    - echo "DEPLOYMENT_ID=$(date +%s%N)-$CI_COMMIT_SHA" > /tmp/deployment_id
    - # Deploy logic (e.g., AWS CLI, Helm)
    - aws cloudformation deploy --stack-name my-app --template ./template.yaml
    - # Log audit trail to DB/Elasticsearch
    - curl -X POST -H "Content-Type: application/json" \
        -d '{"action":"deploy","env":"prod","sha":"'$CI_COMMIT_SHA'", \
        "user":"'$GITLAB_USER_LOGIN'", \
        "timestamp":"$(date -u +'%Y-%m-%dT%H:%M:%SZ')"}' \
        http://audit-logger-service:8080/api/v1/audit
  tags:
    - deployment-tracker
```
**Key Changes:**
- Append `DEPLOYMENT_ID` to trace deployments.
- Log to a centralized audit service (e.g., [OpenTelemetry](https://opentelemetry.io/) or a simple DB).

##### **Option B: Post-Deployment Hook (Terraform Example)**
Use `terraform_remote_state` + CloudWatch Logs:
```hcl
terraform {
  backend "s3" {
    bucket = "my-state-bucket"
    key    = "prod/app/${var.env}.tfstate"
    region = "us-east-1"
  }
}

resource "aws_cloudwatch_log_group" "audit" {
  name = "/aws/terraform/audit/${var.env}"
}

# Log deployment metadata on apply
provider "null" {
  experiments = [ "terraform_3_0" ]
}

resource "null_resource" "audit_log" {
  triggers = {
    sha = git_sha1(file("README.md"))  # Or use var.commit_sha
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws logs put-log-events \\
        --log-group-name ${aws_cloudwatch_log_group.audit.name} \\
        --log-stream-name "audit-${var.env}" \\
        --log-events '[{"timestamp":$(date +%s000), "message":"Deployed ${var.commit_sha} by $USER"}]'
    EOT
    interpreter = ["bash", "-c"]
  }
}
```

---

### **2.2 Issue: Rollback Fails or is Unreliable**
**Symptoms:**
- Rollback deploys to an *unknown* state.
- Manual `git checkout` + redeploy doesn’t match expectations.

**Root Causes:**
- No **versioned artifacts** (e.g., Docker images without tags).
- **Stateful rollbacks** (e.g., databases retain old data).
- **"Atomic" deployments aren’t enforced** (partial rollback).

---
#### **Fixes**
##### **Option A: Versioned Artifacts (Docker + AWS ECR)**
Tag images with `DEPLOYMENT_ID`:
```bash
# Build and push with metadata
DOCKER_IMAGE=my-app:deployment-$(date +%s%N)-$CI_COMMIT_SHA
docker build -t $DOCKER_IMAGE .
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag $DOCKER_IMAGE:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:$DOCKER_IMAGE
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:$DOCKER_IMAGE
```
**Rollback Script:**
```bash
#!/bin/bash
DEPLOYMENT_ID="$(aws ecs list-tasks --cluster my-cluster --desired-status STOPPED | jq -r '.taskArns[] | split(":")[2]')"
# Revert to previous tag (e.g., from audit log)
PREVIOUS_TAG=$(aws ecr describe-images --repository-name my-app | jq -r '.imageDetails[0].imageTags[0]')
aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment
```

##### **Option B: Database Rollback (PostgreSQL Example)**
Use `pg_dump` + versioned backups:
```sql
-- Pre-deploy: Create a transactional backup
SELECT pg_create_restore_point('before-deploy-$(date +%s)');

-- Post-deploy failure: Rollback
SELECT pg_restore_point('before-deploy-1234567890');
```

---

### **2.3 Issue: Failed Deployments Lack Context**
**Symptoms:**
- Deployment fails with no metadata (e.g., "500 Internal Error" in logs).
- No way to correlate failures with specific code changes.

**Root Causes:**
- **No structured logs** (e.g., plaintext error messages).
- **Missing CI/CD artifacts** (e.g., no stack traces in build logs).
- **Environment mismatch** (dev vs. prod configs).

---
#### **Fixes**
##### **Option A: Structured Logging (JSON + OpenTelemetry)**
Add to your app (Python example):
```python
import logging
from opentelemetry import trace

logger = logging.getLogger("app")
trace.set_tracer_provider(trace.get_tracer_provider())

def deploy_hook():
    tracer = trace.get_tracer(__name__)
    ctx = trace.set_span_in_context(tracer.start_span("deploy_hook"))
    try:
        logger.info(
            {"event": "deploy_start", "commit": "abc123", "env": "prod"},
            extra={"span": tracer.current_span()}
        )
        # Your deploy logic
    except Exception as e:
        logger.error(
            {"error": str(e), "deploy_id": "dep-abc123"},
            exc_info=True,
            extra={"span": tracer.current_span()}
        )
        raise
```

##### **Option B: CI/CD Artifact Storage (GitLab CI)**
Upload logs + binaries:
```yaml
deploy:
  script:
    - ./deploy.sh
  artifacts:
    when: always
    paths:
      - logs/
      - /tmp/deploy-metadata.json
    expire_in: 1 week
```

---

## **3. Debugging Tools & Techniques**

### **3.1 Audit Trail Debugging**
| **Tool**               | **Use Case**                                  | **Command/Setup**                          |
|------------------------|-----------------------------------------------|---------------------------------------------|
| **JFrog Artifactory**  | Track Docker images + dependencies            | `jf rt config` (CLI)                        |
| **GitHub Audit Logs**  | User activity (deploys, PRs)                  | `gh api repos/{owner}/{repo}/audit-log`    |
| **ELK Stack**          | Centralized logs (e.g., Kibana for audit logs)| Docker: `docker-compose -f elasticsearch.yml up` |
| **Terraform Cloud**    | Versioned state + change history              | `terraform login` + `terraform workspace show` |

**Example Query (Elasticsearch):**
```json
GET /audit_logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "env": "prod" } },
        { "range": { "timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```

### **3.2 Rollback Debugging**
1. **Docker:**
   ```bash
   # List images with tags
   docker images | grep my-app
   # Rollback to previous tag
   docker service update --image my-app:v1.2.0 my-service
   ```
2. **Kubernetes:**
   ```bash
   # Check rollback history
   kubectl rollout history deployment/my-app
   # Rollback to revision 2
   kubectl rollout undo deployment/my-app --to-revision=2
   ```
3. **Database:**
   ```sql
   -- Find last successful backup (PostgreSQL)
   SELECT pg_backup_restore_point_information('last_backup');
   ```

---

## **4. Prevention Strategies**
### **4.1 Design-Time Fixes**
- **Enforce deployment metadata**:
  - Add `DEPLOYMENT_ID` to all deployments (CI/CD + manual).
  - Store in database (e.g., `deployments` table with `sha`, `user`, `env`, `status`).
- **Version all artifacts**:
  - Docker: `latest` = `deployment-<id>-<sha>`.
  - Helm: `chart.version` + `appVersion`.
- **Atomic deployments**:
  - Use **blue-green** or **canary** (e.g., Argo Rollouts).
  - Example (Terraform):
    ```hcl
    resource "aws_lb_listener_rule" "canary" {
      listener_arn = aws_lb_listener.main.arn
      priority     = 100

      action {
        type             = "forward"
        target_group_arn = aws_lb_target_group.canary.arn
      }

      condition {
        path_pattern {
          values = ["/canary/*"]
        }
      }
    }
    ```

### **4.2 Runtime Safeguards**
- **Automated rollback triggers**:
  - CloudWatch Alarms → Lambda → `kubectl rollout undo`.
  - Example (AWS Lambda):
    ```python
    import boto3

    def lambda_handler(event, context):
        cloudwatch = boto3.client('cloudwatch')
        if event[' detail']['alarmName'] == 'HighErrorRate':
            client = boto3.client('eks')
            response = client.update_service(
                name='my-service',
                clusterName='my-cluster',
                revision='PREVIOUS'
            )
    ```
- **Immutable infrastructure**:
  - Use **Terraform/CloudFormation snapshots** for rollback.
  - Example (Terraform):
    ```hcl
    resource "null_resource" "backup_snapshot" {
      provisioner "local-exec" {
        command = "aws rds create-db-snapshot --db-instance-identifier my-db --snapshot-identifier manual-snap-$(date +%s)"
      }
    }
    ```

### **4.3 Observability**
- **Dashboards**:
  - Grafana: Deployment latency vs. error rate.
  - Example (Prometheus + Grafana):
    ```yaml
    # prometheus.yml
    scrape_configs:
      - job_name: 'deployments'
        static_configs:
          - targets: ['audit-logger:8080']
    ```
- **Alerts**:
  - "Deployments exceeding 5 minutes" → PagerDuty.
  - Example (Terraform + Datadog):
    ```hcl
    resource "datadog_monitor" "long_deploy" {
      name    = "Deployments > 5m"
      type    = "metric alert"
      query   = "avg:aws.ecs.task.duration{env:prod} > 300"
      message = "Rollback required!"
    }
    ```

---

## **5. Quick Reference Cheat Sheet**
| **Problem**               | **Immediate Fix**                          | **Long-Term Fix**                          |
|---------------------------|--------------------------------------------|--------------------------------------------|
| Missing audit logs        | Query CI/CD logs + DB audit tables          | Add `audit-logger` middleware              |
| No rollback capability    | Manual `git checkout` + redeploy           | Versioned artifacts + atomic deployments   |
| Failed deployments        | Check CI logs + console output             | Structured logging + OpenTelemetry        |
| Environment mismatch     | Compare `terraform plan` outputs           | Infrastructure-as-code (IaC) validation     |

---

## **6. Next Steps**
1. **For critical outages**:
   - Run `find /var/log -name "*deployment*"` (Linux) or `Get-AzLog -ResourceGroupName my-rg`.
   - Check CI/CD pipeline logs (e.g., GitLab: `Settings > CI/CD > Jobs`).
2. **For recurring issues**:
   - Add automated tests for deployment tracking (e.g., GitHub Actions linting).
   - Implement a **post-mortem template** for failed deployments.

---
**Final Note**: *Fraisier’s strength lies in its simplicity—prioritize metadata consistency over complexity. Start with CI/CD logs, then layer in audit tools.*