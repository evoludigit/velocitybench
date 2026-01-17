# **Fraisier: Environment-Specific Deployment Patterns for Backend Services**

Deploying backend services across multiple environments—development, staging, and production—is a fundamental challenge in modern software engineering. Each environment has unique requirements: **development needs fast iteration, staging requires production-like safety, and production demands zero-downtime reliability**.

Yet, many teams struggle with **configuration sprawl**, **migration safety**, and **state management** across environments. Services often share the same database or rely on monolithic deployment configurations, leading to accidental outages, inconsistent test data, and brittle migrations.

In this post, we’ll explore the **Fraisier pattern**, a structured approach to managing environment-specific configurations, database strategies, and deployment safeguards. By the end, you’ll understand how to implement **safe, isolated, and flexible** deployments for each environment—without reinventing the wheel.

---

## **The Problem: Why Environment Configurations Fail**

Development, staging, and production environments differ in **critical ways**, but many teams treat them as if they were the same:

| **Requirement**          | **Development**               | **Staging**                     | **Production**                  |
|--------------------------|-------------------------------|---------------------------------|----------------------------------|
| **Database Strategy**    | Fast resets (`DROP` + rebuild) | Safe migrations (`ALTER` only)  | Safe migrations + backups        |
| **Test Data**            | Mock data, ephemeral           | Production-like seed data       | Live, real-world data            |
| **Deployment Safety**    | Can roll back instantly        | Requires verification           | Zero-downtime, rollback-ready    |
| **Health Checks**        | Minimal, largely ignored       | Critical for pre-prod validation | Mandatory, strict SLAs            |
| **Branch Management**    | Any branch allowed            | Limited to pre-release branches | Only stable release branches     |

### **Common Anti-Patterns**
1. **Shared Database for All Environments**
   ```bash
   # Example: Accidental production writes in dev
   docker-compose -f docker-compose.dev.yml up
   # Later...
   ./migrate --env=prod  # Oops, ran on dev DB!
   ```
   → **Result:** Data corruption, security breaches.

2. **One-Size-Fits-All Migrations**
   ```sql
   -- Dev: DROP TABLE users; CREATE TABLE users (id SERIAL, name TEXT);
   -- Prod: ALTER TABLE users ADD COLUMN updated_at TIMESTAMP;
   ```
   → **Result:** Broken prod deployments when dev scripts run in production.

3. **No Isolation Between Environments**
   ```yaml
   # config.yaml (monolithic)
   database:
     url: "postgres://user:pass@db:5432/mydb"
     migrations: ["up", "down"]
   ```
   → **Result:** Accidental `migrate --force` in production.

4. **Manual Environment Switching**
   ```bash
   export ENV=dev
   ./run.sh
   # Later...
   export ENV=prod
   ./run.sh  # Did the team remember to change everything?
   ```
   → **Result:** Human error, inconsistent states.

---

## **The Solution: Fraisier – Environment-Specific Deployment Patterns**

Fraisier is a **configuration and deployment pattern** that ensures:
✅ **Isolated state** per environment (databases, logs, storage)
✅ **Environment-aware migrations** (safe for prod, fast for dev)
✅ **Branch-to-environment mapping** (automated safety gates)
✅ **Health checks and backups** (prod-only safeguards)

The core idea is to **externalize environment-specific logic** while keeping the service code dry. This allows:

- **Dev:** Reset databases on deploy (`DROP` + rebuild).
- **Staging:** Apply safe migrations (`ALTER` only).
- **Prod:** Strict migration controls + backups before changes.

---

## **Implementation Guide: Fraisier in Practice**

Let’s build a **real-world example** using Go, PostgreSQL, and Docker, but the pattern applies to any language (Node.js, Python, Java, etc.).

---

### **1. Environment Definition (Configuration)**
Each environment has its own **configuration profile** stored in a central config service (e.g., `config.yaml`).

```yaml
# config.yaml
environments:
  dev:
    database:
      url: "postgres://devuser:devpass@localhost:5432/dev_mydb"
      strategy: "rebuild"  # DROP + recreate tables
      migrations:
        up: "up-dev.sql"
        down: "down-dev.sql"
    git:
      branch: "main"  # Default, but branch mapping applies
    health:
      enabled: false
    backups:
      enabled: false

  staging:
    database:
      url: "postgres://staginguser:stagingpass@localhost:5432/staging_mydb"
      strategy: "apply"   # Safe ALTER-only migrations
      migrations:
        up: "up-staging.sql"
        down: "down-staging.sql"
    git:
      allowed_branches: ["release/*"]
    health:
      enabled: true
      check_endpoint: "/healthz"
    backups:
      enabled: true
      schedule: "0 3 * * *"  # Nightly backups

  prod:
    database:
      url: "postgres://produser:prodpass@db.cluster-123.rds.amazonaws.com:5432/prod_mydb"
      strategy: "apply"   # Strict migration control
      migrations:
        up: "up-prod.sql"
        down: "down-prod.sql"
    git:
      allowed_branches: ["main", "release/*"]
    health:
      enabled: true
      check_endpoint: "/healthz"
    backups:
      enabled: true
      schedule: "0 2 * * *"  # Hourly backups
```

---

### **2. Branch Mapping (Git Safety Gates)**
Only **specific branches** can deploy to **specific environments**.

```go
// env/env.go
package env

import (
	"errors"
	"fmt"
)

type Environment string

const (
	Dev    Environment = "dev"
	Staging Environment = "staging"
	Prod   Environment = "prod"
)

func IsBranchAllowedForEnv(env Environment, branch string) bool {
	allowedBranches := map[Environment][]string{
		Dev:    {"main", "develop", "feature/*"},
		Staging: {"release/*"},
		Prod:   {"main", "release/*"},
	}

	for allowedBranch := range allowedBranches[env] {
		if matchesPattern(allowedBranch, branch) {
			return true
		}
	}
	return false
}

func matchesPattern(pattern, branch string) bool {
	// Simple glob-like matching (use github.com/bmatcuk/doublestar for full globs)
	if pattern == "*" {
		return true
	}
	return branch == pattern || strings.HasPrefix(branch, pattern+"/")
}
```

**Usage:**
```go
if !env.IsBranchAllowedForEnv(Prod, "dev-feature") {
	panic("Production deploy from dev-feature branch rejected!")
}
```

---

### **3. Database Strategy (Safe Migrations)**
Different environments **cannot use the same migration script**. Instead, we **generate environment-specific SQL**.

```go
// migrations/migrator.go
package migrations

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
)

type Migrator struct {
	env       env.Environment
	db        *sql.DB
	migrationDir string
}

func NewMigrator(env env.Environment, db *sql.DB, migrationsDir string) (*Migrator, error) {
	return &Migrator{
		env:           env,
		db:            db,
		migrationDir: migrationsDir,
	}, nil
}

func (m *Migrator) Up() error {
	var scriptPath string
	switch m.env {
	case env.Dev:
		scriptPath = filepath.Join(m.migrationDir, "up-dev.sql")
	case env.Staging, env.Prod:
		scriptPath = filepath.Join(m.migrationDir, "up.sql")
	default:
		return fmt.Errorf("unsupported environment: %v", m.env)
	}

	return applySQLScript(m.db, scriptPath)
}

func (m *Migrator) Down() error {
	var scriptPath string
	switch m.env {
	case env.Dev:
		scriptPath = filepath.Join(m.migrationDir, "down-dev.sql")
	case env.Staging, env.Prod:
		scriptPath = filepath.Join(m.migrationDir, "down.sql")
	default:
		return fmt.Errorf("unsupported environment: %v", m.env)
	}

	return applySQLScript(m.db, scriptPath)
}

func applySQLScript(db *sql.DB, path string) error {
	sql, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	_, err = db.Exec(string(sql))
	return err
}
```

**Example SQL (`up-dev.sql` vs `up.sql`):**
```sql
-- up-dev.sql (for dev)
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- up.sql (for staging/prod – safe migrations)
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
```

---

### **4. Health Checks (Prod-Only Validation)**
Production environments **must verify** deployment success before traffic is routed.

```go
// health/health.go
package health

import (
	"net/http"
)

func RegisterHealthCheck(mux *http.ServeMux, env env.Environment) {
	if env != env.Prod {
		return // Health checks only in prod
	}

	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if checkDatabaseHealth() && checkDependencies() {
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("healthy"))
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
			w.Write([]byte("unhealthy"))
		}
	})
}

func checkDatabaseHealth() bool {
	// Implement DB connection/read test
	return true
}

func checkDependencies() bool {
	// Test Redis, Kafka, etc.
	return true
}
```

---

### **5. Backups (Prod Safety Net)**
Production databases **must be backed up before changes**.

```bash
# Example: Pre-migration backup (run in a CI/CD pipeline)
#!/bin/bash
ENV=prod
DB_URL="postgres://produser:prodpass@db.cluster-123.rds.amazonaws.com:5432/prod_mydb"

# Trigger backup
pg_dump -h $(echo $DB_URL | cut -d'/' -f3) \
        -U $(echo $DB_URL | cut -d'/' -f4 | cut -d':' -f1) \
        -d $(echo $DB_URL | cut -d'/' -f6) |
    gzip > "prod_backup_$(date +%Y%m%d).sql.gz"

# Store backup in S3/backup service
aws s3 cp prod_backup_*.sql.gz s3://my-backups/prod/
```

---

## **Deployment Workflow (Docker + CI/CD)**
Here’s how we **deploy** using a **Fraisier-compliant** Docker setup.

### **1. Docker Compose per Environment**
```yaml
# docker-compose.dev.yml
version: "3.8"
services:
  app:
    build: .
    environment:
      - ENV=dev
      - DATABASE_URL=postgres://devuser:devpass@db:5432/dev_mydb
    depends_on:
      - db
    command: ["sh", "-c", "migrate && ./app"]
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: devuser
      POSTGRES_PASSWORD: devpass
      POSTGRES_DB: dev_mydb
    volumes:
      - dev_db_data:/var/lib/postgresql/data
    command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]

volumes:
  dev_db_data:
```

```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  app:
    build: .
    environment:
      - ENV=prod
      - DATABASE_URL=postgres://produser:prodpass@db:5432/prod_mydb
    depends_on:
      - db
    command: ["sh", "-c", "migrate && ./app"]
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: produser
      POSTGRES_PASSWORD: prodpass
      POSTGRES_DB: prod_mydb
    volumes:
      - prod_db_data:/var/lib/postgresql/data
    command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]

volumes:
  prod_db_data:
```

### **2. CI/CD Pipeline (GitHub Actions Example)**
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: ["main", "release/*"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: go test ./...
  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose -f docker-compose.dev.yml up -d
  deploy-staging:
    needs: test
    if: startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ./validate-branch-allowed prod release/*
      - run: docker-compose -f docker-compose.staging.yml up -d
  deploy-prod:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/v*')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: ./validate-branch-allowed prod main
      - run: ./run-backup.sh prod
      - run: docker-compose -f docker-compose.prod.yml up -d
```

---

## **Common Mistakes to Avoid**

1. **Not Using Environment-Specific Migrations**
   → Mixing `DROP` and `ALTER` in the same script causes prod outages.

2. **Skipping Health Checks in Production**
   → Assume everything works—verify with `/healthz`.

3. **Overcommitting to "Shared DB" for Testing**
   → Dev and staging **must** have their own databases.

4. **No Backup Strategy**
   → Always back up prod before migrations.

5. **Manual Environment Switching**
   → Use **configuration files** or **environment variables** consistently.

6. **Ignoring Branch Policies**
   → Never allow `main` to deploy to staging unless it’s a release.

---

## **Key Takeaways**
✅ **Environment isolation** → Dev, staging, prod **must** have separate databases/logs.
✅ **Environment-specific migrations** → Dev = `DROP`, Prod = `ALTER` only.
✅ **Branch-to-environment mapping** → Restrict deployments with safety gates.
✅ **Health checks in production** → Only route traffic after `/healthz` passes.
✅ **Backups before changes** → Prod migrations **must** be backed up first.

---

## **Conclusion: Safe Deployments Start with Fraisier**

Managing multiple environments effectively is **not about tools—it’s about discipline**. The **Fraisier pattern** ensures:
- **Dev:** Fast iteration with safe resets.
- **Staging:** Production-like testing with controlled migrations.
- **Prod:** Zero-downtime, backed-up, and verified deployments.

By **externalizing environment-specific logic** and enforcing **strict safety rules**, you reduce risk and avoid costly outages.

**Next Steps:**
1. Audit your current deployments—are environments properly isolated?
2. Implement **branch-to-environment mapping** in your CI/CD.
3. Start **staging like production**—test migrations there first.

Would you like a deeper dive into **database replication strategies** for multi-env setups? Let me know in the comments! 🚀