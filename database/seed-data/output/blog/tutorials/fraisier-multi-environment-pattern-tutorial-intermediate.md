```markdown
---
title: "Fraisier: Managing Multi-Environment Deployments with Safety and Flexibility"
author: "Jane Doe"
date: "2024-02-15"
tags: ["database design", "API design", "deployment patterns", "backends"]
description: "Explore how to use the Fraisier pattern to handle multi-environment configurations safely while maintaining flexibility for development, staging, and production."
---

# Fraisier: Managing Multi-Environment Deployments with Safety and Flexibility

Deploying services across multiple environments—development, staging, and production—requires careful attention to configuration, database handling, and safety. Each environment has unique requirements:

- **Development** needs fast iteration and the ability to reset data frequently.
- **Staging** should mirror production closely but allow experimental changes.
- **Production** demands safety, backups, and strict health checks before serving live traffic.

Managing these differences manually leads to inconsistencies, deployment failures, or even production outages. The **Fraisier pattern** provides a structured way to define environment-specific configurations, database strategies, and safety mechanisms, ensuring smooth deployments across all stages.

In this post, we’ll explore how the Fraisier pattern solves the challenges of multi-environment deployments. You’ll learn how to configure different branches for each environment, enforce environment-specific database strategies (e.g., `rebuild` for dev vs. `apply` for prod), and integrate health checks and backups. By the end, you’ll have a practical implementation guide to apply to your own services.

---

## The Problem: Why Environment-Specific Configurations Matter

Let’s start with a common pain point: deployments that fail because configuration isn’t aligned with the environment. Imagine this scenario:

1. **Development** works fine with a local SQLite database that resets after every deploy (`rebuild` strategy). This is expected and fast.
2. **Staging** uses PostgreSQL with safe migrations (`apply` strategy) but occasionally deploys incomplete migrations, causing data corruption.
3. **Production** runs the same migrations as staging, but unlike staging, you can’t afford downtime or data loss.

The problem isn’t just inconsistent configurations—it’s a lack of **environment-specific safeguards**. Without explicit rules for each environment, teams often:
- Overlook branch-to-environment mappings (e.g., deploying `main` to dev instead of `dev-branch`).
- Use unsafe database strategies in production (e.g., `rebuild` instead of `apply`).
- Forget to enable health checks or backups for critical environments.

Worse, these issues often surface during production deployments, leading to costly downtime or data loss.

---

## The Solution: The Fraisier Pattern

The Fraisier pattern addresses environment-specific needs by defining **environment configurations** that control:
1. **Branch mappings**: Which Git branch maps to which environment (e.g., `dev` branch → dev environment, `main` branch → staging/prod).
2. **Database strategies**: Whether to use `rebuild` (drop and recreate) or `apply` (safe migrations) for database updates.
3. **Safety mechanisms**: Health checks and backups for production-like environments.
4. **Isolated state**: Separate databases, log directories, and configurations per environment.

### Core Principles
- **Declarative configurations**: Define environment rules once, enforce them everywhere.
- **Safety by design**: Assign stricter rules to production (e.g., no `rebuild`).
- **Flexibility**: Allow development to experiment without constraints.

---

## Implementation Guide: Putting Fraisier into Practice

Let’s walk through a practical implementation for a Node.js service using PostgreSQL. We’ll use a `fraisier-config.js` file to define environment-specific settings and `migration-strategies.js` to handle database updates.

---

### 1. Define Environment Configurations

Store environment-specific settings in a centralized configuration file (e.g., `fraisier-config.js`). This file will map environments to branches, database strategies, and safety options.

#### Example: `fraisier-config.js`
```javascript
const fraisierConfig = {
  // Map branches to environments (Git-based)
  branchMappings: {
    'dev': 'development',
    'staging': 'staging',
    'main': 'production',
  },

  // Environment-specific settings
  environments: {
    development: {
      // Database strategy: "rebuild" (drop and recreate) or "apply" (safe migrations)
      dbStrategy: 'rebuild',
      // Database URL (separate instances per environment)
      dbUrl: 'postgresql://dev-user:password@localhost:5432/dev_db',
      // Path to logs (isolated per environment)
      logsDir: './logs/dev',
      // Health check URL (optional)
      healthCheckUrl: 'http://localhost:3000/health',
      // Enable backups? (Only for staging/production)
      requireBackups: false,
    },
    staging: {
      dbStrategy: 'apply',
      dbUrl: 'postgresql://staging-user:password@staging-db:5432/staging_db',
      logsDir: './logs/staging',
      healthCheckUrl: 'http://staging-server/health',
      requireBackups: true,
    },
    production: {
      dbStrategy: 'apply',
      dbUrl: 'postgresql://prod-user:password@prod-db:5432/prod_db',
      logsDir: './logs/prod',
      healthCheckUrl: 'https://api.example.com/health',
      requireBackups: true,
    },
  },
};

module.exports = fraisierConfig;
```

---

### 2. Integrate Branch Mappings with CI/CD

Ensure your CI/CD pipeline respects branch-to-environment mappings. For example, in a GitHub Actions workflow:

#### Example: `.github/workflows/deploy.yml`
```yaml
name: Deploy

on:
  push:
    branches: [dev, staging, main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set environment
        id: env
        run: |
          if [ "${{ github.ref }}" == "refs/heads/dev" ]; then
            echo "ENVIRONMENT=development" >> $GITHUB_OUTPUT
          elif [ "${{ github.ref }}" == "refs/heads/staging" ]; then
            echo "ENVIRONMENT=staging" >> $GITHUB_OUTPUT
          else
            echo "ENVIRONMENT=production" >> $GITHUB_OUTPUT
          fi
      - name: Deploy
        env:
          FRAISIER_ENV: ${{ steps.env.outputs.ENVIRONMENT }}
        run: |
          npm run deploy -- --env=$FRAISIER_ENV
```

---

### 3. Implement Database Strategies

Use a library like [`knex.js`](https://knexjs.org/) or [`sequelize`](https://sequelize.org/) to handle migrations based on the environment’s strategy. Below is an example using Knex with a `migration-strategies.js` helper:

#### Example: `migration-strategies.js`
```javascript
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const execAsync = promisify(exec);

const fraisierConfig = require('./fraisier-config');

async function migrate(environment) {
  const config = fraisierConfig.environments[environment];
  if (!config) throw new Error(`Environment ${environment} not configured`);

  const knexConfig = {
    client: 'pg',
    connection: config.dbUrl,
    migrations: {
      directory: './migrations',
    },
  };

  const knex = require('knex')(knexConfig);

  try {
    if (config.dbStrategy === 'rebuild') {
      // Drop and recreate the database (dev-only)
      await knex.raw('DROP DATABASE IF EXISTS ' + knexConfig.connection.database);
      await knex.raw(`CREATE DATABASE ${knexConfig.connection.database}`);
      await knex.migrate.latest();
      console.log(`Database rebuilt and migrations applied for ${environment}`);
    } else if (config.dbStrategy === 'apply') {
      // Apply migrations safely (staging/prod)
      await knex.migrate.latest();
      console.log(`Migrations applied for ${environment}`);
    }
  } catch (error) {
    console.error(`Migration failed for ${environment}:`, error);
    throw error;
  } finally {
    await knex.destroy();
  }
}

module.exports = { migrate };
```

---

### 4. Add Health Checks

Health checks verify that the service is running correctly after deployment. Example with Express:

#### Example: `server.js`
```javascript
const express = require('express');
const { migrate } = require('./migration-strategies');
const fraisierConfig = require('./fraisier-config');

const app = express();
const env = process.env.FRAISIER_ENV || 'development';

// Start health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// Initialize database based on environment
async function bootstrap() {
  try {
    await migrate(env);
    const port = env === 'development' ? 3000 : 8080;
    app.listen(port, () => {
      console.log(`Server running in ${env} mode on port ${port}`);
    });
  } catch (error) {
    console.error('Failed to bootstrap:', error);
    process.exit(1);
  }
}

bootstrap();
```

---

### 5. Enable Backups for Production-like Environments

For staging and production, enforce backups before deployments. Use a script like this to backup PostgreSQL:

#### Example: `backup-db.sh`
```bash
#!/bin/bash

ENV=$1
DB_URL=$2

if [ -z "$ENV" ] || [ -z "$DB_URL" ]; then
  echo "Usage: $0 <environment> <db-url>"
  exit 1
fi

# Extract database name from URL
DB_NAME=$(echo "$DB_URL" | sed -E 's/.*postgresql:\/\/[^:]+\:[^@]*@[^:]+:([0-9]+)\/([^\?]+).*/\2/')

# Create a timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/${ENV}"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Run pg_dump with compression
pg_dump -h "$(echo "$DB_URL" | cut -d'/' -f3 | cut -d':' -f1)" \
        -p "$(echo "$DB_URL" | cut -d'/' -f3 | cut -d':' -f2)" \
        -U "$(echo "$DB_URL" | cut -d'/' -f2 | cut -d':' -f1)" \
        -d "$DB_NAME" \
        -Fc | gzip > "$BACKUP_FILE"

echo "Backup created: $BACKUP_FILE"
```

Add this to your deployment script for staging/production:
```bash
if [ "$FRAISIER_ENV" = "staging" ] || [ "$FRAISIER_ENV" = "production" ]; then
  ./backup-db.sh "$FRAISIER_ENV" "$(jq -r ".environments[$FRAISIER_ENV].dbUrl" fraisier-config.js)"
fi
```

---

## Common Mistakes to Avoid

1. **Ignoring branch-to-environment mappings**:
   - Always enforce mappings (e.g., `dev` branch → dev environment). Avoid deploying `main` to dev by accident.

2. **Using `rebuild` in non-dev environments**:
   - `rebuild` is for development only. Staging/production should always use `apply` to avoid data loss.

3. **Skipping health checks**:
   - Health checks are non-negotiable for staging/production. They catch issues early.

4. **Not isolating environments**:
   - Use separate databases, log directories, and configurations per environment. Never share resources between dev/staging/prod.

5. **Forgetting backups**:
   - Always backup staging/production before deployments. Use automated scripts to avoid human error.

6. **Overcomplicating configurations**:
   - Start simple (e.g., `fraisier-config.js`). Add complexity only as needed (e.g., environment variables for secrets).

---

## Key Takeaways

- **Define environment-specific rules**: Use `fraisier-config.js` to map branches, database strategies, and safety options.
- **Enforce database strategies**:
  - `rebuild` for development (fast iterators).
  - `apply` for staging/production (safe migrations).
- **Integrate with CI/CD**: Use Git branch mappings to automate deployments.
- **Add health checks**: Verify deployments succeeded before traffic hits your service.
- **Backup critical environments**: Always back up staging/production before deployments.
- **Isolate resources**: Use separate databases, logs, and configs per environment.

---

## Conclusion

The Fraisier pattern provides a structured way to handle multi-environment deployments safely and flexibly. By defining environment-specific configurations, database strategies, and safety mechanisms upfront, you reduce risks like data loss, failed deployments, and inconsistencies.

Start small: define your `fraisier-config.js`, enforce branch mappings in CI/CD, and add health checks. Gradually introduce database isolation and backups as your needs grow. The goal isn’t perfection—it’s reducing friction and preventing disasters.

Try Fraisier in your next project. Your future self (especially in production) will thank you.

---
```