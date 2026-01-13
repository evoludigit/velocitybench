# **[Pattern] Environment Management (dev, staging, prod) – Reference Guide**

---

## **Overview**
Environment Management is a standard practice for structuring software development workflows across distinct environments (e.g., **development**, **staging**, and **production**). This pattern ensures code, configurations, and dependencies are isolated from each other, reducing risks (e.g., bugs, downtime) and enabling consistent, predictable deployments. It enforces clear roles (e.g., QA in staging, end-users in prod) and supports collaboration while maintaining security and scalability. Key components include environment-specific configurations, automated testing pipelines, and deployment strategies (e.g., blue-green, canary). Best practices emphasize version control for configs, automated rollback mechanisms, and monitoring to detect discrepancies between environments.

---

## **Schema Reference**
Use the following schema to define environments in your projects.

| **Field**               | **Description**                                                                                     | **Data Type**       | **Example**                          | **Requirements**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------|--------------------------------------|---------------------------------------------------------------------------------|
| **`environment`**       | Unique identifier for the environment (e.g., `dev`, `staging`, `prod`).                             | String              | `dev`                                | Must match predefined values.                                                 |
| **`type`**              | Environment classification (e.g., `development`, `integration`, `production`).                     | String              | `development`                        | Aligns with organizational naming conventions.                                  |
| **`url`**               | Base URL for the environment (e.g., `https://app-dev.example.com`).                                  | URL                 | `https://api-staging.example.io`      | Must be publicly accessible (or documented for internal-only environments).      |
| **`database`**          | Database connection details (e.g., `host`, `port`, `name`).                                         | Object              | `{ host: "db-dev.example.com", port: 5432 }` | Encrypted credentials must use secrets management (e.g., AWS Secrets Manager).   |
| **`features`**          | List of enabled/disabled features per environment (e.g., `{"beta": true}`).                         | Array (Key-Value)   | `["analytics", "payments"]`          | Flags for feature toggles should be version-controlled.                        |
| **`logs`**              | Log aggregation settings (e.g., `Splunk`, `ELK`).                                                 | String              | `Splunk`                             | Logging must respect data privacy (e.g., no production logs in dev).            |
| **`deployment_strategy`** | Strategy for deploying updates (e.g., `rolling`, `blue-green`, `canary`).                          | String              | `blue-green`                         | Must integrate with CI/CD pipelines (e.g., GitHub Actions, Jenkins).            |
| **`synthetic_monitoring`** | Flags for synthetic transactions (e.g., `{"healthcheck": true}`).                                   | Object              | `{ healthcheck: true, login: false }` | Critical paths must be monitored in all environments.                          |
| **`security`**          | Security settings (e.g., `rate_limits`, `waf_rules`).                                              | Object              | `{ rate_limits: { max: 1000 }, waf_rules: ["OWASP"] }` | Prod-specific hardening required.                                           |
| **`dependencies`**      | External services or libraries used (e.g., `{"auth": "aws-cognito"}`).                             | Object              | `{ auth: "okta" }`                   | Version pins to avoid drift.                                                     |
| **`owner`**             | Team or individual responsible for the environment.                                                 | String/Email        | `dev-team@example.com`               | Clear accountability for incident resolution.                                   |
| **`backup_plan`**       | Backup schedule and retention policy (e.g., `{"daily": true, "retention": 30}`).                    | Object              | `{ daily: true, retention: 7 }`      | Prod backups must be immutable and isolated.                                     |
| **`testing`**           | Automated test suites (e.g., `{"unit": true, "e2e": false}`).                                       | Object              | `{ unit: true, integration: true }`  | Staging must replicate prod-like conditions.                                     |

---

## **Implementation Details**
### **1. Environment Naming and Isolation**
- **Naming Convention**: Use lowercase, hyphen-separated names (e.g., `dev`, `staging`, `prod`). Avoid abbreviations like `dev_env`.
- **Isolation**:
  - **Networking**: Deploy environments in separate VPCs/subnets or Kubernetes namespaces.
  - **Data**: Use environment-specific databases/clusters (avoid shared schemas).
  - **Secrets**: Never hardcode credentials. Use tools like **Vault**, **AWS Secrets Manager**, or **HashiCorp Nomad**.

### **2. Configuration Management**
- **File Structure**:
  ```
  /configs/
  ├── dev/
  │   └── settings.json
  ├── staging/
  │   └── settings.json
  └── prod/
      └── settings.json
  ```
- **Tools**:
  - **Terraform/Ansible**: For infrastructure-as-code (IaC) environment provisioning.
  - **GitOps**: Sync configs via Git (e.g., ArgoCD, Flux) to avoid manual changes.

### **3. Deployment Strategies**
| **Strategy**       | **Use Case**                          | **Tools Example**          | **Best Practices**                                                                 |
|--------------------|---------------------------------------|----------------------------|-----------------------------------------------------------------------------------|
| **Rolling**        | Zero-downtime updates for stateless apps. | Kubernetes `RollingUpdate` | Monitor rollback thresholds (e.g., 95% success rate).                             |
| **Blue-Green**     | Instant cutover with zero downtime.    | AWS CodeDeploy, Argo Rollouts | Traffic split testing required.                                                   |
| **Canary**         | Gradual release to a subset of users.   | Istio, Linkerd              | Feature flags for quick rollback.                                                 |
| **Feature Flags**  | Enable/disable features per environment. | LaunchDarkly, Unleash       | Avoid "kill switches" in production.                                             |

### **4. Testing and Validation**
- **Dev**: Unit/integration tests (fast feedback loop).
- **Staging**:
  - End-to-end (E2E) tests replicating prod traffic.
  - Load/testing with tools like **Locust** or **JMeter**.
- **Prod**:
  - Canary releases with automated rollback on errors.
  - Post-mortem for failures (e.g., SRE blameless reviews).

### **5. Monitoring and Logging**
| **Component**       | **Dev**               | **Staging**            | **Production**          |
|--------------------|-----------------------|------------------------|-------------------------|
| **Metrics**        | Basic (CPU/memory)     | Extended (latency, errors) | SLOs, alerts (e.g., PagerDuty) |
| **Logs**           | Minimal               | Structured logs (e.g., JSON) | Aggregated (e.g., ELK, Datadog) |
| **Synthetic Checks** | Disabled            | Health checks          | Critical paths + synthetic users |

### **6. Rollback Procedures**
- **Automated**: Triggered by CI/CD pipelines (e.g., failed health checks).
- **Manual**:
  1. Identify the problematic deployment (e.g., via Git commit hash).
  2. Revert to a known-good state (e.g., `git revert` + redeploy).
  3. Isolate the issue (e.g., environment-specific logs).

---

## **Query Examples**
### **1. List Environment Variables**
```bash
# Using Terraform
terraform output -json | jq '.environment_vars'
```
**Output**:
```json
{
  "dev": {
    "DATABASE_URL": "postgres://user:pass@dev-db:5432/dev_db",
    "FEATURE_BETA": "true"
  },
  "staging": {
    "DATABASE_URL": "postgres://user:pass@staging-db:5432/staging_db",
    "FEATURE_BETA": "false"
  }
}
```

### **2. Check Database Connectivity (Python)**
```python
import psycopg2

def test_db(env: str):
    config = {
        "dev": {"host": "dev-db.example.com", "port": 5432},
        "staging": {"host": "staging-db.example.com", "port": 5432},
    }
    try:
        conn = psycopg2.connect(**config[env])
        print(f"✅ {env.upper()} DB connected")
        conn.close()
    except Exception as e:
        print(f"❌ {env.upper()} DB failed: {e}")

test_db("dev")
test_db("staging")
```

### **3. Validate Feature Flags (Shell)**
```bash
#!/bin/bash
ENV=$1
FLAG=$2

case $ENV in
    "dev")
        FLAG_VAL=$(jq -r '.dev.features."'$FLAG'"' configs/settings.json)
        ;;
    "staging")
        FLAG_VAL=$(jq -r '.staging.features."'$FLAG'"' configs/settings.json)
        ;;
    *)
        echo "Error: Invalid env"
        exit 1
        ;;
esac

if [[ "$FLAG_VAL" == "true" ]]; then
    echo "✅ $FLAG is enabled in $ENV"
else
    echo "❌ $FLAG is disabled in $ENV"
fi
```

**Run**:
```bash
./validate_flag.sh staging beta
```

---
## **Best Practices**
1. **Avoid "Works on My Machine"**:
   - Use **Docker** or **Vagrant** to replicate dev environments.
   - Example: `docker-compose -f docker-compose.${ENV}.yml up`.

2. **Environment Parity**:
   - Staging should mimic prod hardware, network, and data volume.
   - Use **feature flags** to disable prod-only features in dev/staging.

3. **Access Control**:
   - **Dev**: Full access (but isolated from prod).
   - **Staging**: Limited to QA/testers.
   - **Prod**: Restricted to ops/security teams.

4. **Backup and Disaster Recovery**:
   - Prod backups must be **immutable** (e.g., AWS S3 Versioning).
   - Test restore procedures quarterly.

5. **Documentation**:
   - Maintain a **README** in each environment’s repo (e.g., `/docs/dev/README.md`).
   - Include:
     - Deployment instructions.
     - Owner contact.
     - Known issues.

---

## **Related Patterns**
1. **[Infrastructure as Code](https://example.com/iac-pattern)**
   - Use Terraform/CloudFormation to provision environments consistently.

2. **[Blue-Green Deployments](https://example.com/blue-green-pattern)**
   - Zero-downtime deployment strategy for critical services.

3. **[Canary Releases](https://example.com/canary-pattern)**
   - Gradual rollouts to minimize risk.

4. **[Feature Flags](https://example.com/feature-flags-pattern)**
   - Toggle features per environment without redeploying.

5. **[Secrets Management](https://example.com/secrets-pattern)**
   - Securely store credentials (e.g., Vault, AWS Secrets Manager).

6. **[Observability](https://example.com/observability-pattern)**
   - Centralized logging/metrics (e.g., Prometheus + Grafana).

7. **[GitOps](https://example.com/gitops-pattern)**
   - Sync environment configs via Git for auditability.