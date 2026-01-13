# **Debugging Deployment Conventions: A Troubleshooting Guide**

## **1. Introduction**
**Deployment Conventions** ensure consistency in how applications are packaged, deployed, and scaled across environments. Misconfigurations, unclear conventions, or mismatched deployments can lead to inconsistencies, downtime, or failed rollouts. This guide provides a structured approach to diagnosing and resolving common issues related to deployment conventions.

---

## **2. Symptom Checklist**
Before diving into fixes, identify the symptoms:

✅ **Environment Mismatches**
   - Deployments work in staging but fail in production.
   - Configuration files differ between environments (e.g., `config.local` vs `config.prod`).

✅ **Deployment Rollback Failures**
   - Rollback fails with errors like **"Resource not found"** or **"Permission denied."**
   - Previous versions are corrupted or missing.

✅ **Inconsistent Service Behavior**
   - Some services work in one region but fail in another.
   - Database schemas or environment variables mismatch.

✅ **Slow or Blocked Deployments**
   - CI/CD pipelines stuck at build/package steps.
   - Artifact storage (e.g., Docker images, JARs) unreachable.

✅ **Post-Deployment Issues**
   - Services crash after deployment (e.g., `500 Internal Server Error`).
   - Logs show `config not found` or `missing dependency`.

---
## **3. Common Issues & Fixes**
### **3.1 Environment-Specific Configuration Mismatches**
**Symptom:** App behaves differently across envs (e.g., `DEBUG=true` in prod).

**Root Cause:**
- Missing or incorrect environment variables.
- Hardcoded paths or configs not following the 12-factor app principle.

**Fix:**
- **Use Config Files & Environment Variables**
  ```bash
  # Example: .env files with environment-specific overrides
  # .env.prod
  NODE_ENV=production
  DATABASE_URL=prod-db-url

  # .env.staging
  NODE_ENV=development
  DATABASE_URL=staging-db-url
  ```
- **Validate Config at Startup**
  ```python
  # Python example (using python-dotenv)
  import os
  from dotenv import load_dotenv

  load_dotenv(".env." + os.getenv("ENVIRONMENT", "local"))
  if not os.getenv("DATABASE_URL"):
      raise ValueError("Missing DATABASE_URL!")
  ```

---

### **3.2 Failed Rollbacks Due to Artifact Corruption**
**Symptom:** Rollback fails with `404 Not Found` for old versions.

**Root Cause:**
- Artifacts not properly versioned or stored.
- CI/CD pipeline doesn’t preserve old builds.

**Fix:**
- **Enable Versioned Artifact Storage**
  ```yaml
  # GitHub Actions example
  steps:
    - uses: actions/upload-artifact@v3
      with:
        name: app-build-${{ github.sha }}
        path: dist/
        retention-days: 7
  ```
- **Use Immutable Deployments (GitOps Approach)**
  ```bash
  # Helm example (immutable releases)
  helm upgrade --install my-app ./chart --wait --timeout 5m
  ```

---

### **3.3 Inconsistent Service Scaling (Kubernetes Example)**
**Symptom:** Services crash when scaled up/down.

**Root Cause:**
- Resource limits too low (`requests/limits` misconfigured).
- Liveness/Readiness probes failing.

**Fix:**
```yaml
# Fix resource limits in deployment.yaml
resources:
  requests:
    cpu: "100m"
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"

# Adjust liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

### **3.4 CI/CD Pipeline Stuck at Build Step**
**Symptom:** Pipeline hangs at `mvn package` or `docker build`.

**Root Cause:**
- Missing dependencies.
- Dockerfile errors (e.g., incorrect `FROM` image).
- Permissions issues.

**Fix:**
- **Debug Docker Builds**
  ```bash
  docker build --no-cache -t myapp .
  docker history myapp  # Check for layer failures
  ```
- **Add Build-Time Checks**
  ```dockerfile
  # Example: Fail if required files are missing
  RUN ls /app/config.json || { echo "Config missing!" && exit 1; }
  ```

---

### **3.5 Database Schema Migrations Fail**
**Symptom:** App crashes with `ColumnNotFoundError`.

**Root Cause:**
- Migrations not applied or rolled back.
- Schema drift between environments.

**Fix:**
- **Use Database Migration Tools (Flyway/Liquibase)**
  ```sql
  -- Flyway example (apply migrations)
  SELECT * FROM flyway_schema_history;
  ```
- **Enforce Schema Validation**
  ```python
  # Python SQLAlchemy example
  from sqlalchemy import inspect
  inspector = inspect(engine)
  if "user_table" not in inspector.get_table_names():
      raise RuntimeError("Missing required table!")
  ```

---

## **4. Debugging Tools & Techniques**
| **Issue**               | **Debugging Tool/Technique**                     | **Example Command/Output**                     |
|-------------------------|-------------------------------------------------|-----------------------------------------------|
| **Config Issues**       | `env` / `set` (Linux/macOS)                     | `set | grep DB_` (list DB env vars)                |
| **Kubernetes Debugging**| `kubectl logs -f <pod>` / `kubectl describe pod` | `kubectl logs deployment/myapp -c web`       |
| **Docker Issues**       | `docker inspect <container>`                   | `docker inspect --format='{{.State.Health.Status}}' myapp` |
| **CI/CD Pipeline Stalls**| GitHub Actions Artifacts / Logs                | `<pipeline_url>/actions` (check logs)        |
| **Database Schema**     | `psql -U user -d db -c "\dt"` (PostgreSQL)      | `list_tables()` (MySQL)                       |

**Pro Tip:**
- Use **structured logging** (JSON) for easier filtering:
  ```javascript
  console.log(JSON.stringify({ level: "error", message: "DB connect failed" }));
  ```

---

## **5. Prevention Strategies**
### **5.1 Standardize Deployment Artifacts**
- Use **signed containers** (e.g., Docker Content Trust).
- Enforce **immutable tags** (e.g., `sha256` instead of `latest`).

### **5.2 Implement Environment Validation**
- **Preflight Checks:** Run scripts to validate env vars, configs, and dependencies before deployment.
  ```bash
  # Example: validate required env vars
  grep -q "^DATABASE_URL=" .env || { echo "Missing DB config!" && exit 1; }
  ```

### **5.3 Automate Rollback Testing**
- **Chaos Engineering:** Simulate rollbacks in staging.
  ```bash
  # Helm example: test rollback
  helm rollback myapp 1 --dry-run
  ```

### **5.4 Enforce Documentation & Compliance**
- **Document Deployment Steps:** Use tools like [Conventional Commits](https://www.conventionalcommits.org/).
- **Audit Trails:** Track deployments with Git tags or Jira tickets.

---

## **6. Summary Checklist for Quick Fixes**
| **Action**                  | **Tool/Command**                          |
|-----------------------------|-------------------------------------------|
| Check env vars              | `env` / `kubectl get env`                |
| Validate configs             | `.env` parsing scripts                    |
| Debug Kubernetes             | `kubectl logs`, `describe pod`            |
| Fix Docker builds           | `--no-cache`, `docker history`            |
| Rollback failed deploys     | Helm/Git version control                 |

---
**Final Note:**
Deployment conventions are only as strong as their weakest link. Use **automated validation**, **immutable deployments**, and **structured logging** to minimize outages.

---
**Need more help?**
- **Kubernetes?** Check [`kubectl debug`](https://kubernetes.io/docs/tasks/debug/debug-application/debugging-container/).
- **Docker?** Run `docker events` to monitor builds.
- **CI/CD?** Audit logs in Jenkins/GitHub Actions.

---
*This guide targets production-grade debugging—apply with caution!* 🚀