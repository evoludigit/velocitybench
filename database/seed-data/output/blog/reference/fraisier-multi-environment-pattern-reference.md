# **[Pattern] Fraisier: Multi-Environment Deployment Configuration Reference Guide**

---

## **1. Overview**
Fraisier is a deployment pattern for microservices that ensures **environment-parallelism** (dev, staging, prod) with **operational isolation**. By enforcing distinct configurations, Git branches, database strategies, and health checks per environment, Fraisier minimizes cross-environment contamination and enables controlled, safe deployments.

Key benefits:
- **Separate storage & state**: Each environment uses its own database and log directories.
- **Safe migrations**: Production uses a "slow" (`apply`) migration strategy, while dev uses a "fast" (`rebuild`) approach.
- **Branch isolation**: Git branches are mapped to environments, preventing accidental deployments.
- **Enforced consistency**: Health checks validate deployments before promoting changes.

Suitable for services where **development, staging, and production** must operate independently for security, testing, or compliance reasons.

---

## **2. Schema Reference**

| **Component**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                                  |
|-----------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| **Environment**             | Enum          | Defines supported environments (`dev`, `staging`, `prod`).                                                                                                                                                     | `dev`, `staging`, `prod`                            |
| **Branch Mapping**          | Map           | Git branch → Environment mapping (e.g., `dev-branch` → `dev`).                                                                                                                                                  | `{ "dev-branch" : "dev", "staging-branch" : "staging" }` |
| **Database Strategy**       | Enum          | Controls migration behavior:                                                                                                                                                                               |                                         `rebuild`, `apply`, `noop` |
| - `rebuild`                 |               | Drops & recreates the database (fast but destructive).                                                                                                                                                       | Used in `dev`                                       |
| - `apply`                   |               | Applies incremental migrations (slow but safe).                                                                                                                                                            | Used in `prod`                                      |
| - `noop`                    |               | Skips migrations (for read-only environments).                                                                                                                                                             | Used in `staging` (if no changes)                   |
| **Health Check**            | Config Object | Endpoint & success criteria to verify deployment.                                                                                                                                                          | `{ "endpoint": "/health", "status": "200" }`         |
| **Backup Policy**           | Boolean       | Enables automatic backups before production deployments.                                                                                                                                                     | `true` (prod), `false` (dev/staging)                |
| **Log Directory**           | Path          | Isolated log storage per environment (e.g., `/var/log/fraisier/dev`).                                                                                                                                        | `/data/logs/{env}`                                  |
| **Database Directory**      | Path          | Isolated DB storage per environment (e.g., `/var/lib/fraisier/prod`).                                                                                                                                      | `/data/db/{env}`                                    |

---

## **3. Implementation Details**

### **3.1 Environment Definition**
Each environment is configured via a **YAML/JSON manifest** (e.g., `fraisier.yaml`):
```yaml
environments:
  dev:
    branch: "dev-branch"
    db_strategy: "rebuild"
    health_check: { endpoint: "/health", status: 200 }
    backup: false
  prod:
    branch: "main"
    db_strategy: "apply"
    health_check: { endpoint: "/health", status: 200 }
    backup: true
```

**Key Rules:**
- `prod` cannot use `rebuild` (enforced by tooling).
- `dev` must use a `rebuild`-compatible DB (e.g., SQLite in-memory).

---

### **3.2 Branch Mapping**
Fraisier enforces **one-to-one branch-to-environment mapping**:
- Commit to `dev-branch` → deploys to `dev` environment.
- Merge to `main` → triggers `prod` deployment (with backup).

**Query Example (CLI):**
```sh
$ fraisier env list
+--------+-----------+
| Branch | Environment |
+--------+-----------+
| dev    | dev        |
| main   | prod       |
+--------+-----------+
```

---

### **3.3 Database Strategy**
| **Strategy** | **Use Case**               | **DB Actions**                          | **Rollback Risk** |
|--------------|---------------------------|----------------------------------------|-------------------|
| `rebuild`    | Development               | Drop + recreate DB                      | High              |
| `apply`      | Production                | Apply migrations incrementally         | Low               |
| `noop`       | Staging (no changes)      | Skip migrations                         | None              |

**Migration Example (Flyway):**
```yaml
# In fraisier.yaml:
flyway:
  strategy: "apply"  # For prod
  locations: ["classpath:db/migration"]
```

---

### **3.4 Health Checks**
Validates deployment success before promoting.
- **Triggered** after DB migration.
- **Fails safe**: Deployments stuck in `pending` if health check fails.

**Example Check (HTTP):**
```yaml
health_check:
  endpoint: "/ready"
  status: 200
  timeout: 10s
```

**Query Example (API):**
```http
GET /api/env/dev/health
{
  "status": "healthy",
  "last_checked": "2023-10-01T12:00:00Z"
}
```

---

### **3.5 Backups**
Automatic backups for `prod`:
- **Trigger**: Before `apply` migrations.
- **Storage**: S3, local, or encrypted backup DB.
- **Retention**: 7 days (configurable).

**Backup Policy Example:**
```yaml
backup:
  enabled: true
  destination: "s3://fraisier-backups/prod"
  schedule: "daily-at-2am"
```

---

## **4. Query Examples**

### **4.1 List Environments**
```sh
$ fraisier env list --format table
+--------+-----------+-----------+--------------+
| Name   | Branch    | DB Strategy | Health Check |
+--------+-----------+--------------+--------------+
| dev    | dev-branch| rebuild     | /health      |
| staging| staging   | noop        | /ready       |
| prod   | main      | apply       | /ready       |
+--------+-----------+--------------+--------------+
```

---

### **4.2 Deploy to Environment**
```sh
# Deploy dev branch to staging (simulated)
$ fraisier deploy --env staging --branch staging
✅ Migration: noop (no changes)
✅ Health check: /ready (200)
```

---

### **4.3 Check Backup Status**
```sh
$ fraisier backup status prod
{
  "status": "completed",
  "last_backup": "2023-10-01T02:00:00Z",
  "location": "s3://fraisier-backups/prod/2023-10-01.sql"
}
```

---

## **5. Related Patterns**

| **Pattern**               | **Purpose**                                                                 | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Canary Deployments**    | Gradually roll out changes to a subset of users.                            | High-traffic services                    |
| **Blue-Green Deployments**| Instant cutover between two identical environments.                         | Zero-downtime updates                    |
| **Feature Flags**         | Toggle features without redeploying.                                       | Experimental features                    |
| **Infrastructure as Code**| Manage deployments via scripts (Terraform, Ansible).                       | Multi-cloud environments                 |
| **GitOps (ArgoCD/Flux)**  | Sync Kubernetes manifests with Git.                                         | Kubernetes-native deployments            |

---

## **6. Best Practices**
1. **Dev = Fast Feedback**: Use `rebuild` for dev to avoid migration drift.
2. **Staging = Production-Like**: Use `apply` migrations in staging.
3. **Backup Prod**: Always enable backups for production.
4. **Health Checks First**: Fail fast if deployments are unhealthy.
5. **Isolate Logs/DBs**: Never share storage between environments.

---
**See also:**
- [Fraisier Git Integration Guide](link)
- [Database Migration Strategies](link)