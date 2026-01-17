```markdown
# **Fraisier: A Multi-Environment Deployment Configuration Pattern for Safe, Scalable Backends**

![Fraisier Pattern Visualization](https://via.placeholder.com/1000x400/2c3e50/ffffff?text=Fraisier+Multi-Environment+Flow)

Deploying backends across **development**, **staging**, and **production** environments is a common challenge—but doing it *correctly* separates the good engineers from the great ones.

Most teams tackle this by throwing together a config file or relying on environment variables. But what happens when:
- Your dev database gets corrupted after a "rebuild" but staging *should* use migrations?
- A bad migration crashes your staging environment, but production isn’t affected?
- Your health checks only work for dev but fail silently in production?

**Fraisier** (French for *"baker’s peel"*—because it layers configurations carefully) is a **practical pattern** for managing environment-specific deployments. It ensures:
- **Dev** can be fast and experimental (reset DBs, no safety checks).
- **Staging** mimics production with controlled migrations.
- **Production** is locked down with airtight safeguards.

By the end of this post, you’ll know:
✅ How to define environments in code
✅ How to safely map Git branches
✅ How to enforce database strategies per environment
✅ How to write health checks that matter

Let’s start by exploring **why** this matters—and then build it step by step.

---

## **The Problem: Environment Drift and Fragile Deployments**

Backends don’t live in a vacuum. Each environment has different needs:

| Environment | Needs | Risks if Wrong |
|-------------|-------|---------------|
| **Dev** | Fast feedback, can reset data | No backups, slow rebuilds |
| **Staging** | Production-like, safe migrations | Broken migrations, manual fixes |
| **Prod** | Zero-downtime, backups, health checks | Accidental rollbacks, data loss |

### **Example: The "Oops" Scenario**
A team runs a `drop-and-recreate` migration in production because they forgot to check the **environment**. Hours later, they’re restoring from backup. Meanwhile, the CI pipeline keeps failing because dev’s "fast path" doesn’t match staging’s "safe path."

### **Why Config Files Alone Fail**
Many teams use a single `config.json` with `NODE_ENV: "dev"`. But:
- **Hardcoded paths** break when containers change.
- **No branch enforcement** means `main` might deploy to staging.
- **No migration strategy differentiation**—why risk production if dev can `truncate` tables?

---

## **The Solution: Fraisier’s Layered Approach**

Fraisier **decouples deployment safety from environment names**. It enforces:

1. **Explicit environment definitions**
2. **Branch-to-environment mapping**
3. **Environment-specific database strategies**
4. **Health check validation**
5. **Isolated state per environment**

### **Core Idea: "Each Environment is a Sandbox"**
Think of it like **different gardening setups**:
- **Dev**: Water daily, plant new seeds, can uproot and replant.
- **Staging**: Use real soil, test watering routines.
- **Production**: Professional-grade irrigation, insurance, and strict pruning rules.

---

## **Implementation Guide**

### **1. Define Environments in Code**
Fraisier starts with **environment-specific configurations**.

#### **Example: `environments.ts` (TypeScript)**
```typescript
// Define environments and their properties
export const Environments = {
  DEV: {
    name: "Development",
    branch: "dev-branch", // Deploy from this branch
    database: {
      strategy: "rebuild", // Drop & recreate DB
      path: "./dev-db.sqlite", // Dev-only DB path
    },
    healthChecks: {
      enabled: true,
      url: "http://localhost:3000/health",
    },
  },
  STAGE: {
    name: "Staging",
    branch: "staging-branch", // Deploy from this branch
    database: {
      strategy: "apply", // Safe migrations only
      path: "./staging-db.sqlite",
    },
    healthChecks: {
      enabled: true,
      url: "https://staging.example.com/health",
    },
    backups: {
      enabled: true,
      schedule: "daily", // Backup staging too
    },
  },
  PROD: {
    name: "Production",
    branch: "main", // Only `main` can deploy here
    database: {
      strategy: "apply", // Critical: safe only
      path: "/data/prod-db.sqlite",
    },
    healthChecks: {
      enabled: true,
      url: "https://api.example.com/health",
      requiredChecks: ["db-ready", "redis-ready"],
    },
    backups: {
      enabled: true,
      schedule: "hourly",
      retention: "30d",
    },
  },
} as const;

export type Environment = keyof typeof Environments;
```

#### **Key Insights**
- **`branch`** ensures only allowed branches deploy.
- **`strategy`** (`rebuild` vs. `apply`) controls DB behavior.
- **`healthChecks`** validates deployments.

---

### **2. Branch-to-Environment Mapping**
Prevent `dev-branch` from deploying to staging by enforcing **Git branch rules**.

#### **Example: `.github/workflows/deploy.yml` (GitHub Actions)**
```yaml
name: Deploy
on:
  push:
    branches:
      - "dev-branch"  # Only deploy dev branch to DEV
      - "staging-branch"  # Only deploy staging branch to STAGE
      - "main"  # Only `main` can deploy to PROD

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to ${{ env.ENV }}
        run: |
          if [ "${{ env.ENV }}" = "dev" ]; then
            npm run migrate:rebuild
          elif [ "${{ env.ENV }}" = "prod" ]; then
            npm run migrate:apply --check  # Dry run first
          fi
```

---

### **3. Environment-Specific Database Strategies**
**`rebuild`** (Dev/Staging) vs. **`apply`** (Prod) play differently:

#### **Example: `migrations.ts` (SQL + TypeScript)**
```typescript
// Example migration logic
export async function runMigration(strategy: "rebuild" | "apply") {
  if (strategy === "rebuild") {
    console.log("⚠️ Dev/Staging: Rebuilding database...");
    await execute("DROP TABLE IF EXISTS users");
    await execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)");
    await seedUsers();
    return;
  }

  // Safe migrations (prod)
  await execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP");
}
```

#### **When to Use Which?**
| Strategy | When to Use | Risks |
|----------|------------|-------|
| `rebuild` | Dev/Staging | Data loss, slower |
| `apply` | Production | Risky migrations |

---

### **4. Health Checks for Confidence**
Ensure deployments work before exposing them.

#### **Example: `health.ts` (Express)**
```typescript
import express from "express";
const app = express();

// Health check endpoint
app.get("/health", (req, res) => {
  const dbReady = checkDatabase();
  const redisReady = checkRedis();

  if (!dbReady || !redisReady) {
    return res.status(503).json({ status: "unhealthy", checks: { db: dbReady, redis: redisReady } });
  }

  res.json({ status: "healthy" });
});

// Run checks on startup
app.listen(3000, () => {
  setTimeout(() => {
    console.log("Health check running at http://localhost:3000/health");
  }, 2000);
});
```

#### **Enforce in CI**
```yaml
# Verify health check before deploying
- name: Check health
  run: |
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health)
    if [ "$response" -ne 200 ]; then
      echo "Health check failed! Exiting."
      exit 1
    fi
```

---

### **5. Isolated State (Databases & Logs)**
Never share:
- **Database files** (`dev-db.sqlite`, `prod-db.sqlite`)
- **Log directories** (`/var/log/example-dev`, `/var/log/example-prod`)

#### **Example: Docker Compose**
```yaml
version: "3.8"
services:
  db-dev:
    image: postgres
    volumes:
      - ./dev-db:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: "example-dev"

  db-prod:
    image: postgres
    volumes:
      - ./prod-db:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: "example-prod"
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: No Branch Enforcement**
*"We’ll just deploy `main` to staging too."*
→ **Fix:** Use `.gitignore` + CI checks.

### **❌ Mistake 2: Same Migration Strategy Everywhere**
*"Why not just `apply` everywhere?"*
→ **Fix:** `rebuild` is fine for non-production.

### **❌ Mistake 3: No Health Checks in Prod**
*"If it works in staging, it’ll work in prod."*
→ **Fix:** Always validate.

### **❌ Mistake 4: Shared DB Across Environments**
*"The staging DB is the same as prod, just with a different name."*
→ **Fix:** **Never** share databases.

---

## **Key Takeaways**
- **Environments ≠ Environment Variables**: Define them explicitly.
- **Branch Control**: Only allow `main` to `prod`, `dev-branch` to `dev`.
- **Database Safety**: Use `rebuild` for dev, `apply` for prod.
- **Health Checks**: Validate before exposing.
- **Isolation**: Never share DBs or logs.

---

## **Conclusion: Deploy with Confidence**

Fraisier isn’t about magic—it’s about **enforcing rules explicitly** so deployments stay safe.

### **Next Steps**
1. Start with **environments.ts** to define your setup.
2. Add **branch checks** in CI.
3. Use **`rebuild`/`apply`** per environment.
4. **Health checks** before production.

By treating each environment as a **controlled experiment**, you’ll avoid the "oops" of environment drift.

Now go build something **both fast and safe**!

---
**Further Reading**:
- [Database Migration Strategies](https://kennethreitz.org/essays/2014/01/12/on-database-migrations.html)
- [GitOps for Environments](https://www.gitops.tech/)
```