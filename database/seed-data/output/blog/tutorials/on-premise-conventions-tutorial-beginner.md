```markdown
---
title: "On-Premise Conventions: Consistency in Your Local Development & Testing - A Complete Guide"
subtitle: "Why your local databases and APIs should play by the same rules, and how to enforce them"
author: "Alex Chen"
date: "2023-11-07"
tags: ["database design", "API design", "backend patterns", "on-premise", "Docker", "migrations"]
---

# On-Premise Conventions: Consistency in Your Local Development & Testing

**TL;DR:** This guide teaches you how to standardize database and API conventions for your on-premise development environments to reduce inconsistency, simplify debugging, and speed up collaboration. We'll cover why conventions matter, practical patterns to implement them (with code examples), and common pitfalls to avoid.

---

## Introduction

When you're a backend developer working locally, your world is surprisingly complex. You're juggling:
- Databases running in Docker containers or directly on your machine
- APIs that might version differently between environments
- Configuration files that change based on which team member is working
- Tables and endpoints that grow organically without a unified approach

Without **on-premise conventions**, your development becomes a minefield:
- Debugging becomes frustrating because one teammate’s `users` table has a `created_at` column while yours doesn’t
- Testing begins with "It works on my machine" but fails in CI
- Refactoring feels like walking on eggshells because you’re not sure what schema changes are safe

This guide will help you **systematize your local development** by introducing the **On-Premise Conventions** pattern—a set of practical rules and tools to ensure consistency across all on-premise environments. We’ll cover:

1. Why conventions matter for on-premise setups
2. Core conventions to implement (with code examples)
3. How to enforce them in CI/CD and collaboration
4. Common mistakes and how to avoid them

---

## The Problem: Madness Without Conventions

Let’s paint a picture of development hell without conventions:

### Scenario 1: The Schema Drift
- **Alice** adds a `deleted_at` column to her `posts` table using `ALTER TABLE`
- **Bob** clones her repo, runs `npm install`, and `migrate:up`—only to see the error `ERROR: column "deleted_at" does not exist`.
- **Charlie**, working on feature X, doesn’t realize the schema changed and checks in a query that fails because the table structure differs.

### Scenario 2: The API Chaos
- **Team A** deploys an endpoint `/v1/users/{id}` to their on-premise DB
- **Team B**, working in parallel, exposes `/api/users/{id}` with a different query
- When merging, the API schema isn’t documented, and both versions coexist in the codebase.

### Scenario 3: The Debugging Nightmare
- A bug is introduced in `user_service.py` that only manifests when the DB seed script runs
- No one can reproduce it because the seed script depends on a specific PostgreSQL version
- The team starts adding `if __name__ == "__main__"` guards to simulate production inputs, making the codebase harder to maintain.

### The Costs
- **Wasted time**: 30% of debugging time is spent figuring out *why* something is different, not *what’s actually broken* (DevOps Research & Analysis)
- **Broken deployments**: Inconsistent local environments lead to skipped tests or "works on my laptop" bugs in staging.
- **Collaboration friction**: New team members get lost in the "this works here" rabbit hole.

---

## The Solution: On-Premise Conventions

The **On-Premise Conventions** pattern is about **baking consistency into your local workflows**. The core idea is:
> *"All on-premise environments (local dev, testing, CI) should adhere to the same rules for databases, APIs, and configurations."*

This isn’t just about being "consistent"—it’s about **reducing friction** so you can focus on building features, not fighting the environment.

---

### Core Components of the Pattern

#### 1. **Database Conventions**
   - **Schema-first migrations**: Every table must be defined in a migration file before being used.
   - **Versioned migrations**: Migrations include a timestamp, so the order is deterministic.
   - **Seed consistency**: Seeds (test data) must be deterministic and stored in a versioned script.
   - **Transaction isolation**: Use transactions for migrations to avoid partial failures.

#### 2. **API Conventions**
   - **Versioned endpoints**: All APIs must use a versioning scheme (e.g., `/v1/resource`).
   - **Consistent query patterns**: Use standardized query builders (e.g., always `SELECT *` for local testing, but avoid it in production).
   - **Response formats**: Define a standard JSON response shape (e.g., always include `errors`, `data`, and a `timestamp` in every response).

#### 3. **Configuration Conventions**
   - **Environment variables**: Use `.env` files with a standard naming convention (e.g., `DB_HOST=localhost` in dev, `DB_HOST=prod-db` in prod).
   - **Dependency consistency**: Pin all tools (Docker, Python versions, etc.) to `>=0.0.0` in `requirements.txt` or `package.json`.
   - **Tooling**: Enforce linters, formatters, and migrations tools as part of the local setup.

#### 4. **Collaboration Conventions**
   - **Pull request checks**: Reject PRs without passed local tests or a schema migration summary.
   - **Documentation**: Keep a `README.md` with setup instructions, including a "How to debug" section for common issues.
   - **Onboarding**: New hires must run a `setup.sh` script to provision their environment.

---

## Practical Implementation

Let’s dive into how to implement these conventions in your project. We’ll use a **Node.js + PostgreSQL** example, but the concepts apply to Python, Java, or any stack.

---

### 1. Database Setup: Migrations and Seeds

#### **Step 1: Structure Your Migrations**
Store all migrations in a `migrations/` directory, named like `YYYYMMDD_HHMMSS_description.sql`.

```bash
migrations/
├── 20231107_100000_create_users_table.sql
├── 20231107_100100_add_index_to_users_table.sql
└── 20231107_100200_create_posts_table.sql
```

#### **Step 2: Write a Migration Script**
Here’s a sample `20231107_100000_create_users_table.sql` file:

```sql
-- 20231107_100000_create_users_table.sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for faster lookups
CREATE INDEX idx_users_email ON users (email);
```

#### **Step 3: Batch Migrations with a Script**
Write a Node.js script to run migrations in order:

```javascript
// migrations/run.js
const fs = require('fs');
const { Pool } = require('pg');
const path = require('path');

async function runMigrations() {
    const pool = new Pool({ connectionString: process.env.DATABASE_URL });

    try {
        const files = fs.readdirSync(path.join(__dirname))
            .filter(file => file.endsWith('.sql'))
            .sort((a, b) => {
                const dateA = a.match(/^\d+/)[0];
                const dateB = b.match(/^\d+/)[0];
                return dateA - dateB;
            });

        for (const file of files) {
            const sql = fs.readFileSync(path.join(__dirname, file), 'utf8');
            console.log(`Running ${file}...`);
            await pool.query(sql);
        }
        console.log('Migrations completed!');
    } catch (err) {
        console.error('Migration failed:', err);
    } finally {
        await pool.end();
    }
}

runMigrations();
```

#### **Step 4: Seed Your Database Deterministically**
Create a `seeds/` directory with a `users_seed.sql` file:

```sql
-- seeds/users_seed.sql
INSERT INTO users (username, email, password_hash)
VALUES
    ('admin', 'admin@example.com', '$2a$10$N9qo8uLOwv1Z5J3zUeZWwO...'),  -- bcrypt hash
    ('test_user', 'test@example.com', '$2a$10$xOoQqWwL...');
```

Then write a script to run it:

```javascript
// seeds/run.js
const fs = require('fs');
const { Pool } = require('pg');
const path = require('path');

async function seedDatabase() {
    const pool = new Pool({ connectionString: process.env.DATABASE_URL });

    try {
        const files = fs.readdirSync(path.join(__dirname))
            .filter(file => file.endsWith('.sql'));

        for (const file of files) {
            const sql = fs.readFileSync(path.join(__dirname, file), 'utf8');
            console.log(`Seeding ${file}...`);
            await pool.query(sql);
        }
        console.log('Database seeded!');
    } catch (err) {
        console.error('Seeding failed:', err);
    } finally {
        await pool.end();
    }
}

seedDatabase();
```

#### **Step 5: Add to `package.json` Scripts**
```json
{
  "scripts": {
    "migrate": "node migrations/run.js",
    "seed": "node seeds/run.js"
  }
}
```

**Run them!**
```bash
npm run migrate
npm run seed
```

---

### 2. API Conventions: Versioned Endpoints and Responses

#### **Step 1: Enforce Versioned Endpoints**
Always prefix endpoints with `/v1/` for local development. Example:

```javascript
// In your Express app (or FastAPI, Flask, etc.)
app.use('/v1/users', require('./routes/users'));
app.use('/v1/posts', require('./routes/posts'));
```

Then, in your routes:

```javascript
// routes/users.js
const express = require('express');
const router = express.Router();

router.get('/', async (req, res) => {
    try {
        // Fetch users and return a consistent response
        const users = await db.query('SELECT * FROM users ORDER BY created_at DESC');
        res.json({
            status: 'success',
            data: users.rows,
            errors: null,
            timestamp: new Date().toISOString()
        });
    } catch (err) {
        res.status(500).json({
            status: 'error',
            data: null,
            errors: err.message,
            timestamp: new Date().toISOString()
        });
    }
});

module.exports = router;
```

#### **Step 2: Add a Response Wrapper Utility**
Create a helper function to standardize responses:

```javascript
// utils/apiResponse.js
function createResponse(status, data = {}, errors = null) {
    return {
        status: status,
        data: data,
        errors: errors,
        timestamp: new Date().toISOString()
    };
}

module.exports = createResponse;
```

Now use it in your routes:

```javascript
// routes/users.js (updated)
router.get('/', async (req, res) => {
    try {
        const users = await db.query('SELECT * FROM users ORDER BY created_at DESC');
        res.json(createResponse('success', users.rows));
    } catch (err) {
        res.status(500).json(createResponse('error', null, err.message));
    }
});
```

---

### 3. Configuration Conventions: `.env` and Docker

#### **Step 1: Standard `.env` File**
Create a `.env.template` file and distribute it to all developers:

```env
# .env.template
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dev_db
DB_USER=dev_user
DB_PASSWORD=dev_pass
DB_SSL=false

APP_PORT=3000
NODE_ENV=development
```

#### **Step 2: Use Docker Compose for Development**
Create a `docker-compose.yml` file to spin up a consistent PostgreSQL instance:

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

#### **Step 3: Add a `setup.sh` Script**
Create a script to automate setup:

```bash
#!/bin/bash
# setup.sh
set -e

# Create .env file from template
cp .env.template .env

# Start PostgreSQL with Docker
echo "Starting PostgreSQL..."
docker-compose up -d

# Wait for DB to be ready
echo "Waiting for DB to start..."
until docker-compose exec db pg_isready -U ${DB_USER}; do
  sleep 1
done

# Run migrations
echo "Running migrations..."
npm run migrate

# Seed the DB
echo "Seeding database..."
npm run seed

echo "Setup complete!"
```

Make it executable:
```bash
chmod +x setup.sh
```

**Run it!**
```bash
./setup.sh
```

---

### 4. Enforce Conventions in CI/CD

Add a GitHub Actions workflow to ensure consistency:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm install

      - name: Run migrations
        env:
          DATABASE_URL: "postgresql://test_user:test_pass@localhost:5432/test_db"
        run: |
          npm run migrate
          npm test
```

---

## Common Mistakes to Avoid

1. **Skipping the `.env.template`**
   - *Mistake*: Commit only `.env` files with real credentials.
   - *Fix*: Always provide a `.env.template` and document how to create `.env` for local dev.

2. **Not Versioning Migrations**
   - *Mistake*: Manually running `ALTER TABLE` or using tools without version control.
   - *Fix*: Never touch the DB directly. Always use versioned migration files.

3. **Ignoring Schema Drift**
   - *Mistake*: Adding a column to the DB directly without a migration.
   - *Fix*: Use tools like Prisma (for TypeScript) or Flyway that track schema changes.

4. **Hardcoding API Versions**
   - *Mistake*: Using `/users` instead of `/v1/users` for local dev.
   - *Fix*: Version all endpoints locally and ensure the version is in the response headers.

5. **No CI/Docker Setup**
   - *Mistake*: "It works on my machine" because you use a different PostgreSQL version or Docker image.
   - *Fix*: Use Docker for all local development and enforce it in CI.

6. **Inconsistent Test Data**
   - *Mistake*: Using `INSERT` statements directly in tests instead of seeded data.
   - *Fix*: Seed your DB *before* running any tests, and document the expected state.

7. **Not Documenting Conventions**
   - *Mistake*: Assuming everyone knows how to set up the environment.
   - *Fix*: Add a `CONTRIBUTING.md` or `DEV_SETUP.md` file with step-by-step instructions.

---

## Key Takeaways

✅ **Database Conventions**
- Use **versioned migrations** to track schema changes.
- **Seed your DB deterministically** and version the seed scripts.
- **Never** alter tables directly; always use migrations.

✅ **API Conventions**
- **Version all endpoints** locally (`/v1/resource`).
- **Standardize responses** with a wrapper (e.g., `status`, `data`, `errors`).
- **Use consistent query patterns** (e.g., always `SELECT *` in local tests).

✅ **Configuration Conventions**
- Use `.env.template` for all local dev environments.
- **Pin all tools** (Docker images, Node.js versions, etc.).
- **Automate setup** with scripts like `setup.sh`.

✅ **Collaboration Conventions**
- **Enforce local tests** in CI before merging PRs.
- **Document everything** (setup, debugging, schema).
- **Use Docker** for consistent local environments.

✅ **Tooling**
- Add linters, formatters, and migration tools to `package.json` scripts.
- Use Git hooks to prevent broken migrations or syntax errors.

---

## Conclusion

The **On-Premise Conventions** pattern is about **taking control of your local environment** so you can focus on building features, not fixing environment inconsistencies.

### Recap of What We Built:
1. **Database**: Versioned migrations and deterministic seeds.
2. **API**: Versioned endpoints and consistent response shapes.
3. **Configuration**: Standardized `.env` files and Docker-based setups.
4. **Collaboration**: CI checks and documentation to enforce conventions.

### Next Steps:
- **Adopt incrementally**: Start with migrations and seeds, then add API conventions.
- **Document**: Add a `CONTRIBUTING.md` to your repo.
- **Iterate**: Review PRs for consistency and fix issues as they arise.

