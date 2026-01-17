# **Debugging *Fraisier: Multi-Environment Deployment Configuration* – A Troubleshooting Guide**

## **Introduction**
The *Fraisier* pattern ensures consistent, environment-specific deployments across **development, staging, and production**. Misconfigurations here can lead to **data corruption, accidental dumps, or inconsistent behavior** between environments. This guide helps diagnose and resolve common deployment issues efficiently.

---

## **🔍 Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom** | **Possible Cause** |
|-------------|------------------|
| Dev and Prod use different deployment scripts | Config files not environment-aware |
| Database errors (missing tables, schema mismatches) | Incorrect `migrate` commands by environment |
| Staging/Prod missing backups before deploy | Missing `backup_before_deploy` step |
| Inconsistent health checks across environments | Health probe endpoints not standardized |
| Slow deployments in Prod but fast in Dev | Missing tuning (e.g., connection pooling, async tasks) |
| Failed deployments with no rollback | Missing `rollback` strategy |

---
## **🐛 Common Issues & Fixes**

### **1. Inconsistent Deployment Scripts**
**Symptom:**
```bash
# Dev: Uses `npm run dev:deploy`
# Prod: Uses `npm run prod:deploy`
```
**Root Cause:** Hardcoded or environment-unspecific scripts.

**Fix:** Use **environment variables** (`NODE_ENV`, `ENVIRONMENT`) or **CI/CD templates** to enforce consistency.

#### **Example: Standardized Script in `package.json`**
```json
"scripts": {
  "deploy": {
    "dev": "node deploy.js --env=dev",
    "staging": "node deploy.js --env=staging",
    "prod": "node deploy.js --env=prod --dry-run=false"
  }
}
```
**Check:**
```bash
# Run with correct env flag
npm run deploy:prod
```

---

### **2. Accidental Database Drops**
**Symptom:**
```sql
# Error: "ERROR: database 'prod_db' does not exist"
```
**Root Cause:** `migrate --drop` used in Prod by mistake.

**Fix:** **Enforce strict migration rules** with environment checks.

#### **Example: Safe Migration Script**
```javascript
const { Migrator } = require('knex');

const migrator = new Migrator({
  client: 'pg',
  connection: process.env.DB_URL,
});

// Prevent accidental drops in Prod
if (process.env.ENVIRONMENT === 'production') {
  console.error('⚠️ Migration drop disabled in Prod!');
  process.exit(1);
}

// Run safe migrations
migrator
  .latest()
  .catch(console.error);
```
**Prevention:**
- **Use `--force=false` in Prod** (Knex, Prisma, etc.).
- **Lock migration scripts** in `git`.

---

### **3. Missing Backups Before Deploy**
**Symptom:**
```sql
# Prod DB has no recent backup before deployment
```
**Root Cause:** Backup step skipped during CI/CD.

**Fix:** **Automate backups** with environment checks.

#### **Example: Backup Script (PostgreSQL)**
```bash
#!/bin/bash
DB_USER=postgres
DB_NAME=prod_db
BACKUP_DIR=/backups

if [[ "$ENVIRONMENT" == "production" ]]; then
  pg_dump -U $DB_USER $DB_NAME -Fc -f "$BACKUP_DIR/$(date +%Y-%m-%d).sql.gz"
  echo "🔄 Backup created: $BACKUP_DIR/*.sql.gz"
fi
```
**Integration:**
```yaml
# .github/workflows/deploy.yml
steps:
  - run: ./backup_prod_db.sh
  - run: ./deploy_prod.sh
```

---

### **4. Missing or Inconsistent Health Checks**
**Symptom:**
```http
# Dev: 200 OK (health endpoint)
# Prod: 503 Service Unavailable (missing endpoint)
```
**Root Cause:** Health checks defined only in Dev.

**Fix:** **Standardize health checks** across all environments.

#### **Example: Express.js Health Endpoint**
```javascript
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', env: process.env.ENVIRONMENT });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🏥 Health check on port ${PORT}`));
```
**CI/CD Check:**
```yaml
# Ensure health check passes before deploy
- name: Health check
  run: curl -f http://localhost:3000/health || exit 1
```

---

### **5. Slow Deployments in Production**
**Symptom:**
```bash
# Dev: 10s deploy
# Prod: 5 minutes (timeouts, DB locks)
```
**Root Cause:** Missing Prod-specific optimizations.

**Fix:** **Enable async tasks & connection pooling**.

#### **Example: Optimized Deployment**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DB_URL,
  max: 20, // Adjust based on Prod load
  idleTimeoutMillis: 30000,
});

// Use async batches for migrations
async function deploy() {
  await pool.query('BEGIN');
  try {
    await pool.query('ALTER TABLE users ADD COLUMN is_active BOOLEAN');
    await pool.commit();
  } catch (err) {
    await pool.rollback();
    throw err;
  }
}
```

---

## **🛠 Debugging Tools & Techniques**
| **Tool** | **Purpose** |
|----------|------------|
| **Environment Variables Inspector** | `env` (Node.js), `printenv` (Linux) |
| **Database Diff Tool** | `pg_dump` vs. `pg_restore` (PostgreSQL) |
| **CI/CD Logs** | Check deployment pipeline (`github actions`, `jenkins`) |
| **Health Check Proxy** | `healthchecks.io` for external monitoring |
| **Git Bisect** | Find when deployments broke (`git bisect`) |

**Example Debug Workflow:**
1. Check logs:
   ```bash
   journalctl -u fraisier-deploy --no-pager -n 50
   ```
2. Verify DB state:
   ```sql
   SELECT COUNT(*) FROM users; -- Compare Dev vs. Prod
   ```
3. Test health endpoint:
   ```bash
   curl -v http://prod.example.com/health
   ```

---

## **🛡 Prevention Strategies**
1. **Enforce Environment Variables**
   - Use `.env.example` with `ENVIRONMENT=dev/staging/prod`.
   - Validate with `dotenv-safe`.

2. **Lock Critical Configs**
   - Exclude `config/dev.json` from deployment.
   - Use `NODE_ENV=production` in Prod.

3. **Automated Backups**
   - Schedule `pg_dump` (PostgreSQL) or `mysqldump` (MySQL) pre-deploy.

4. **Canary Deployments**
   - Use **blue-green** or **feature flags** for safe rollouts.

5. **Post-Mortem Reports**
   - Document every failed deploy in a shared doc.

---
## **Final Checklist Before Deploying**
| **Action** | **Yes/No** |
|------------|-----------|
| ✅ Scripts match all environments | |
| ✅ Backup created & verified | |
| ✅ Health endpoint tested | |
| ✅ Rollback strategy documented | |
| ✅ Environment variables validated | |

---
### **Conclusion**
By following this guide, you can **systematically diagnose and fix** common *Fraisier* deployment issues. **Standardization, automation, and environment checks** are key to avoiding production blunders.

**Need a deeper dive?** Check:
- [Knex.js Migration Best Practices](https://knexjs.org/guide/migrations.html)
- [12-Factor App Config](https://12factor.net/config)

🚀 **Deploy confidently!**