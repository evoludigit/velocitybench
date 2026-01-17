```markdown
---
title: "Fraisier Pattern: Building a Deployment History and Audit Trail for Your APIs"
date: 2023-11-15
tags: ["backend", "database", "patterns", "api-design", "deployment", "audit"]
description: "Learn how to implement the Fraisier pattern to track every deployment in your system like a flight recorder. Essential for debugging, compliance, and reliability."
---

# **Fraisier Pattern: Deployment History and Audit Trail for Your APIs**

## **Introduction**

Have you ever pulled a deployment, only to realize later that a critical bug was introduced? Or had to debug why a deployment failed without knowing what changed? If so, you’ve experienced the pain of a **lack of deployment history**.

The **Fraisier pattern** (named after the French word for "baker," symbolizing the meticulous tracking of every step) ensures every deployment is recorded with precision. It acts like a **flight recorder for deployments**, capturing:
- What was deployed
- When it happened
- Who did it
- Why it happened
- And most importantly—**what went wrong (or right)**

This pattern is essential for **debugging, compliance, and reliability**. In this post, we’ll explore:
✅ How to structure a **complete deployment audit trail**
✅ Real-world examples in **backend APIs**
✅ Tradeoffs and optimizations
✅ Common mistakes to avoid

---

## **The Problem: Why Deployment History Matters**

Without a proper audit trail, deployments become a **black box**. Here’s why tracking them is critical:

### **1. Debugging Failed Deployments**
- **Problem:** A deployment fails, but logs are scattered across services. Did it break after a config change? A dependency update? You don’t know.
- **Example:** A CI/CD pipeline fails, but the only log is:

```json
{
  "timestamp": "2023-11-15 14:30:00",
  "status": "failed",
  "message": "Deployment failed"
}
```
❌ **No context!** You don’t know if it was a **code error, environment misconfiguration, or a race condition**.

### **2. Rolling Back to a Known Good Version**
- **Problem:** A production bug appears after a deployment. But how do you revert **exactly** to the previous working state?
- **Example:** You deploy `v2.1`, but users report a crash. Did `v2.1` introduce a breaking change? Without history, you might **guess-and-check** instead of knowing the exact change.

### **3. Compliance and Auditing**
- **Problem:** Regulators may require proof that deployments followed a specific process. Without logs, you can’t prove:
  - Who approved the deployment?
  - Was a manual override used?
  - Were pre-deployment checks performed?

### **4. Understanding Regregressions**
- **Problem:** A new feature works in staging but fails in production. Why?
- **Example:** A database schema change works locally but breaks in production because of **data schema drift**. Without history, you can’t compare `v1.0` vs. `v2.0` schemas.

### **5. Team Accountability**
- **Problem:** Someone deployed without proper approval. Without logs, it’s hard to trace **who did it** and **why**.

---
## **The Solution: The Fraisier Pattern**

The **Fraisier pattern** solves these problems by maintaining a **complete audit trail** of every deployment. It consists of **five key components**:

| Component               | Purpose                                                                 |
|-------------------------|--------------------------------------------------------------------------|
| **Deployment Records**  | Core facts: timestamp, who, what, why, status                          |
| **Webhook Events**      | Trace how a deployment was triggered (e.g., CI/CD webhook → deployment) |
| **Status Change Events**| Track transitions (e.g., `running` → `health_check` → `success/failed`)  |
| **Change Diffs**        | Store what changed between deployments (code, config, DB schema)       |
| **Rollback Records**    | Log rollbacks and recovery actions                                      |

Let’s break this down with **practical examples**.

---

## **Implementation Guide**

### **1. Database Schema (PostgreSQL Example)**

We’ll use a **relational database** (PostgreSQL) to store deployment history. Here’s the structure:

#### **Core Tables**
```sql
-- Tracks each deployment (like a flight log)
CREATE TABLE deployments (
  id SERIAL PRIMARY KEY,
  version VARCHAR(50) NOT NULL,      -- e.g., "v2.1.0"
  environment VARCHAR(20) NOT NULL, -- "staging", "production"
  deployed_by VARCHAR(100) NOT NULL, -- Who triggered it (user/role)
  reason VARCHAR(255),              -- Why was it deployed? ("Bug fix", "Feature X")
  status VARCHAR(20) NOT NULL,      -- "pending", "running", "success", "failed"
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP,
  duration_ms INTEGER,              -- How long it took
  metadata JSONB,                   -- Additional details (e.g., CI/CD pipeline ID)
  CHECK (status IN ('pending', 'running', 'success', 'failed'))
);

-- Tracks status changes (e.g., "running" → "health_check")
CREATE TABLE deployment_status_changes (
  id SERIAL PRIMARY KEY,
  deployment_id INTEGER REFERENCES deployments(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL,       -- Current status
  changed_at TIMESTAMP NOT NULL,
  details VARCHAR(255)              -- Extra info (e.g., "Health check failed")
);

-- Stores webhook events (e.g., GitHub -> deployment trigger)
CREATE TABLE webhook_events (
  id SERIAL PRIMARY KEY,
  event_type VARCHAR(50) NOT NULL,    -- "push", "merge_request", "api_deploy"
  source_system VARCHAR(50),         -- "github", "jenkins", "manual"
  payload JSONB,                     -- Raw event data
  triggered_deployment_id INTEGER REFERENCES deployments(id),
  occurred_at TIMESTAMP NOT NULL
);

-- Diffs between deployments (what changed?)
CREATE TABLE deployment_diffs (
  id SERIAL PRIMARY KEY,
  previous_version VARCHAR(50),
  current_version VARCHAR(50),
  changes JSONB NOT NULL,            -- Structured diff (e.g., ["added_file": "src/api.js"])
  created_at TIMESTAMP NOT NULL
);

-- Rollback records (if we revert a deployment)
CREATE TABLE deployments_rollback (
  id SERIAL PRIMARY KEY,
  deployment_id INTEGER REFERENCES deployments(id),
  rolled_back_to_version VARCHAR(50),
  rolled_back_by VARCHAR(100),
  reason VARCHAR(255),
  status VARCHAR(20) NOT NULL,       -- "pending", "success", "failed"
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP
);
```

---

### **2. Sample Data Insertions**

#### **Example 1: Recording a Deployment**
```sql
-- Insert a deployment record
INSERT INTO deployments (
  version, environment, deployed_by, reason, status, started_at
) VALUES (
  'v2.1.0',
  'production',
  'devops-team@example.com',
  'Fix bug in user auth',
  'running',
  NOW()
);

-- Later, update status and duration
UPDATE deployments
SET status = 'success', completed_at = NOW(), duration_ms = 45000
WHERE id = 1;  -- Assuming last deployment ID was 1
```

#### **Example 2: Tracking Status Changes**
```sql
-- Log status changes (e.g., "running" → "health_check")
INSERT INTO deployment_status_changes (
  deployment_id, status, changed_at, details
) VALUES (
  1, 'health_check', NOW(), 'Running health checks...'
);

-- If health check fails:
INSERT INTO deployment_status_changes (
  deployment_id, status, changed_at, details
) VALUES (
  1, 'failed', NOW(), 'Health check failed: Database timeout'
);
```

#### **Example 3: Recording a Webhook Event**
```sql
-- GitHub webhook triggered deployment
INSERT INTO webhook_events (
  event_type, source_system, payload, triggered_deployment_id, occurred_at
) VALUES (
  'merge_request_merged',
  'github',
  '{"branch": "main", "sha": "abc123"}',
  1,
  NOW()
);
```

#### **Example 4: Storing Deployment Diffs**
```sql
-- Compare v1.0 → v2.0 changes
INSERT INTO deployment_diffs (
  previous_version, current_version, changes, created_at
) VALUES (
  'v1.0',
  'v2.0',
  '[
    {"type": "added", "path": "src/api/routes.js"},
    {"type": "modified", "path": "config/database.yml", "changes": ["updated connection pool"]}
  ]',
  NOW()
);
```

#### **Example 5: Logging a Rollback**
```sql
-- If v2.1.0 fails, roll back to v2.0.0
INSERT INTO deployments_rollback (
  deployment_id, rolled_back_to_version, rolled_back_by, status, started_at
) VALUES (
  1, 'v2.0.0', 'devops-team@example.com', 'success', NOW()
);
```

---

### **3. API Endpoints (Node.js + Express Example)**

To interact with this database, we’ll build a simple **REST API**:

#### **Endpoint 1: Record a Deployment**
```javascript
const express = require('express');
const { Pool } = require('pg');
const app = express();
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// POST /deployments
app.post('/deployments', async (req, res) => {
  const { version, environment, deployed_by, reason } = req.body;

  try {
    const result = await pool.query(
      `INSERT INTO deployments
       (version, environment, deployed_by, reason, status, started_at)
       VALUES ($1, $2, $3, $4, 'running', NOW())
       RETURNING id`,
      [version, environment, deployed_by, reason]
    );

    const deploymentId = result.rows[0].id;
    res.status(201).json({ id: deploymentId });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to record deployment' });
  }
});
```

#### **Endpoint 2: Update Deployment Status**
```javascript
// PATCH /deployments/:id/status
app.patch('/deployments/:id/status', async (req, res) => {
  const { id } = req.params;
  const { status, duration_ms, completed_at } = req.body;

  try {
    await pool.query(
      `UPDATE deployments
       SET status = $1, duration_ms = $2, completed_at = $3
       WHERE id = $4`,
      [status, duration_ms, completed_at, id]
    );

    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to update status' });
  }
});
```

#### **Endpoint 3: Get Deployment History**
```javascript
// GET /deployments?environment=production
app.get('/deployments', async (req, res) => {
  const { environment } = req.query;

  try {
    const query = environment
      ? `SELECT * FROM deployments WHERE environment = $1 ORDER BY started_at DESC`
      : `SELECT * FROM deployments ORDER BY started_at DESC`;

    const { rows } = await pool.query(query, [environment]);
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch deployments' });
  }
});
```

---

### **4. Querying Deployment History (Example Reports)**

#### **Example Report: Failed Deployments in Production**
```sql
SELECT
  d.id,
  d.version,
  d.status,
  d.started_at,
  d.duration_ms,
  d.reason,
  jsonb_pretty(d.metadata) AS metadata,
  ARRAY_AGG(dsc.status ORDER BY dsc.changed_at) AS status_history
FROM deployments d
LEFT JOIN deployment_status_changes dsc ON d.id = dsc.deployment_id
WHERE d.environment = 'production' AND d.status = 'failed'
GROUP BY d.id
ORDER BY d.started_at DESC;
```

#### **Example Report: Rollback History**
```sql
SELECT
  d.id AS deployment_id,
  d.version,
  r.rolled_back_to_version,
  r.rolled_back_by,
  r.reason,
  r.started_at
FROM deployments d
JOIN deployments_rollback r ON d.id = r.deployment_id
ORDER BY r.started_at DESC;
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Not Recording Pre-Deployment State**
- **Problem:** You only log **after** deployment. But if something fails in deployment, you don’t know the **initial state**.
- **Fix:** Record the **environment snapshot** (e.g., DB schema, config) **before** deployment starts.

### **❌ Mistake 2: Over-Reliance on External Logging**
- **Problem:** Relying only on **CI/CD logs** (e.g., Jenkins, GitHub Actions) means you lose control if the external system fails.
- **Fix:** **Self-host your audit logs** (e.g., in your database) so you’re not dependent on third-party tools.

### **❌ Mistake 3: Ignoring Webhook Events**
- **Problem:** Without tracking **how** a deployment was triggered (e.g., "merge request merged" → "deployment"), you can’t debug **"why did this deploy at this time?"**.
- **Fix:** Log **every event** that leads to a deployment.

### **❌ Mistake 4: Not Storing Diffs Between Versions**
- **Problem:** If a bug appears, you can’t quickly see **what changed** between versions.
- **Fix:** Store **structured diffs** (e.g., Git commits, config changes, DB schema changes).

### **❌ Mistake 5: Forgetting to Log Rollbacks**
- **Problem:** If you roll back, you lose the **history of why** and **what was reverted**.
- **Fix:** Always log **rollback records** with details.

---

## **Key Takeaways**

✅ **Deployment history is like a flight recorder**—it helps you **debug incidents, prove compliance, and recover quickly**.

✅ **Core components of Fraisier:**
- **Deployment Records** (who, what, when, why)
- **Status Changes** (real-time deployment lifecycle)
- **Webhook Events** (how deployments were triggered)
- **Diffs** (what changed between versions)
- **Rollback Records** (recovery history)

✅ **Database structure:**
- Use a **relational database** (PostgreSQL, MySQL) for structured logs.
- Store **JSONB** for flexible metadata (e.g., CI/CD pipeline details).

✅ **API design:**
- Provide **CRUD endpoints** for deployments.
- Support **filtering by environment, status, time range**.

✅ **Common pitfalls:**
- Don’t **only** rely on external logs (self-host your audit trail).
- Always **store diffs** between versions.
- Log **every event** that leads to a deployment.

---

## **Conclusion**

The **Fraisier pattern** ensures your deployments are **transparent, debuggable, and recoverable**. By maintaining a **complete audit trail**, you:
- **Debug failures faster** (know exactly what went wrong).
- **Roll back safely** (track changes between versions).
- **Prove compliance** (show who did what and when).

### **Next Steps**
1. **Start small:** Begin logging just **deployment records** and **status changes**.
2. **Expand gradually:** Add **webhook events**, **diffs**, and **rollback logs**.
3. **Automate:** Integrate with your **CI/CD pipeline** to auto-log deployments.

Would you like a **Terraform/CloudFormation template** to set up this database in AWS/GCP? Or a **Go/Python example** for server-side logging? Let me know in the comments!

---
```