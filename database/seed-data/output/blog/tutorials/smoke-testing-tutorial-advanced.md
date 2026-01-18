```markdown
---
title: "Smoke Testing: Quick Sanity Checks for Suspiciously Fast Deployments"
date: "2024-05-15"
author: "Alexandra Carter"
tags: ["database design", "testing", "CI/CD", "backend engineering", "pattern"]
---

# Smoke Testing: Quick Sanity Checks for Suspiciously Fast Deployments

*"It works on my machine!"* is a phrase we’ve all heard. But in high-velocity software environments—especially when deploying to production with alarming frequency—this old adage can mean the difference between a seamless user experience and a cascade of embarrassing outages. **Smoke testing** is the unsung hero of *pre-deployment sanity checks*. It’s not about exhaustive validation; it’s about catching the obvious before it becomes the headline of your company’s Slack channel.

Smoke testing is a lightweight, high-impact pattern designed to verify that your system is “breathing” after a deployment. Think of it as a quick health scan—a **pre-flight checklist** for your application infrastructure. The name comes from the idea of passing a “smoke test,” where if smoke (read: errors) is detected, the system is immediately flagged as unhealthy. While it might sound simplistic, integrating smoke tests into your CI/CD pipeline can save you from hours of debugging by catching critical issues early—before they reach production.

In this post, we’ll explore when smoke testing is useful, how to implement it effectively, and the pitfalls to avoid. We’ll dive into code examples that illustrate both API-level and database-level smoke checks, covering microservices, monoliths, and everything in between. Let’s get started.

---

# The Problem: Why Smoke Testing Matters

Imagine this scenario:
You’ve just released a critical feature update to your SaaS platform. The CI/CD pipeline ran green, the unit tests passed, and your feature branch merged without incident. But two hours later, your support team is flooded with reports: users can’t log in, orders aren’t processing, and the dashboard is returning 500 errors. What went wrong?

In many cases, the issue isn’t a bug in your new feature—it’s a **configuration drift**, a **database migration failure**, or a **dependency breaking change** that wasn’t caught during testing. These are often “obvious” problems that slip through the cracks because:
- **Unit tests** focus on logic, not infrastructure.
- **Integration tests** may be too slow or flaky to run post-deployment.
- **Manual QA** is skipped when deployments are rushed.
- **Environment parity** isn’t maintained between staging and production.

Smoke tests are designed to fill this gap. They’re not a replacement for thorough testing—they’re a **last-line defense** that ensures your system isn’t in a broken state before users do. The key is to keep them **fast, deterministic, and focused on critical paths**. A good smoke test should answer:
- *Is the database reachable?*
- *Are core dependencies responding?*
- *Are authentication/authorization working?*
- *Are high-traffic APIs returning valid responses?*

---

# The Solution: What Is a Smoke Test?

A smoke test is a **subset of critical checks** run immediately after a deployment to verify the system is operational. It’s not about testing new features—it’s about ensuring the system can *breathe*. Here’s how it works:

1. **Triggers**: Smoke tests run as part of your CI/CD pipeline (e.g., after a rollout or redeploy).
2. **Scope**: They focus on **baseline functionality**—the things your users depend on daily.
3. **Speed**: Designed to complete in **seconds**, not minutes.
4. **Automation**: Written as code and executed programmatically.
5. **Failure Handling**: Fails fast if critical issues are detected, triggering rollback or alerts.

### Smoke Tests vs. Other Testing Types

| **Test Type**       | **Scope**                          | **Goal**                                  | **Execution Time** | **Example Checks**                     |
|---------------------|------------------------------------|------------------------------------------|--------------------|----------------------------------------|
| **Unit Test**       | Individual functions/classes       | Verify logic correctness                 | Milliseconds       | `isUserValid()` returns `false` for invalid input |
| **Integration Test**| Modules/service interactions       | Test API/database contracts              | Seconds            | User login API returns `200 OK` with token |
| **Smoke Test**      | System-wide health                  | Validate post-deployment baseline        | <10 seconds        | Database connection alive, `/health` endpoint returns `200` |
| **E2E Test**        | Full user journey                  | Simulate real-world scenarios            | Minutes            | User completes checkout flow           |
| **Load Test**       | Performance under load             | Ensure scalability                        | Minutes/Hours      | System handles 10K RPS with <500ms latency |

Smoke tests are **not** a replacement for integration or E2E tests. Instead, they act as a **bridge** between your CI/CD pipeline and production, ensuring that the system is in a known good state before users interact with it.

---

# Implementation Guide: Building Smoke Tests

Smoke tests can be implemented at multiple levels, depending on your architecture. Below are practical examples for **API-based systems**, **database-centric applications**, and **microservices**.

---

## 1. API-Level Smoke Tests

For APIs, smoke tests typically involve:
- Verifying endpoint availability.
- Testing basic authentication/authorization.
- Validating response formats.
- Checking for critical business logic paths.

### Example: Express.js API Smoke Test

Here’s a Node.js example using `axios` and `chai` to test a RESTful API:

```javascript
// smoke-test.js
const axios = require('axios');
const chai = require('chai');
const expect = chai.expect;

const API_BASE_URL = process.env.API_URL || 'http://localhost:3000';

describe('API Smoke Tests', () => {
  // Test database connection via health endpoint
  it('should return 200 OK for /health', async () => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    expect(response.status).to.equal(200);
    expect(response.data).to.have.property('status', 'healthy');
  });

  // Test authentication endpoint
  it('should return 401 for unauthorized login', async () => {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      email: 'invalid@example.com',
      password: 'wrongpass',
    });
    expect(response.status).to.equal(401);
    expect(response.data).to.have.property('error', 'Invalid credentials');
  });

  // Test a critical business endpoint
  it('should return 200 OK for /users/me (authenticated)', async () => {
    // First, login to get a token
    const loginResponse = await axios.post(`${API_BASE_URL}/auth/login`, {
      email: 'test@example.com',
      password: 'password123',
    });
    const token = loginResponse.data.token;

    // Use token for subsequent requests
    const response = await axios.get(`${API_BASE_URL}/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.status).to.equal(200);
    expect(response.data).to.have.property('email', 'test@example.com');
  });

  // Test rate limiting (optional, but useful for APIs)
  it('should enforce rate limits', async () => {
    for (let i = 0; i < 100; i++) {
      const response = await axios.get(`${API_BASE_URL}/public-endpoint`);
      expect(response.status).not.to.equal(429);
    }

    const rateLimitedResponse = await axios.get(`${API_BASE_URL}/public-endpoint`);
    expect(rateLimitedResponse.status).to.equal(429);
  });
});

// Run tests (e.g., via GitHub Actions or CI/CD script)
if (require.main === module) {
  const start = Date.now();
  const { failures } = require('mocha').run();
  console.log(`Smoke tests completed in ${Date.now() - start}ms`);
  process.exit(failures > 0 ? 1 : 0);
}
```

### Key Considerations:
- **Environment Variables**: Use `process.env` to configure the API URL dynamically.
- **Authentication**: If your API requires auth, include a test user credentials (or use a test token).
- **Parallelization**: Run tests concurrently to reduce execution time.
- **Idempotency**: Ensure tests don’t modify state (e.g., avoid `POST` requests unless they’re safe).

---

## 2. Database-Level Smoke Tests

Databases are a common source of post-deployment failures. Smoke tests for databases should verify:
- Connectivity.
- Schema integrity.
- Basic queries.
- Transactional consistency.

### Example: PostgreSQL Smoke Test with `pg` and `pg-memcheck`

```sql
-- pre-deploy.sql (run as part of your CI/CD pipeline)
-- Check database connectivity
SELECT
  version(),
  pg_is_in_recovery(),
  pg_size_pretty(pg_database_size(current_database()))
  AS database_size;
```

```javascript
// db-smoke-test.js
const { Pool } = require('pg');
const assert = require('assert');

const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'test_db',
  password: process.env.DB_PASSWORD || 'password',
  port: process.env.DB_PORT || 5432,
});

describe('Database Smoke Tests', () => {
  it('should connect to the database', async () => {
    const client = await pool.connect();
    assert.ok(client, 'Database connection failed');
    client.release();
  });

  it('should verify schema integrity', async () => {
    const query = `
      SELECT COUNT(*) FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name IN ('users', 'orders');
    `;
    const { rows } = await pool.query(query);
    assert.equal(rows[0].count, 2, 'Critical tables missing');
  });

  it('should execute a basic query', async () => {
    const query = 'SELECT 1 + 1 AS sum';
    const { rows } = await pool.query(query);
    assert.deepEqual(rows, [{ sum: 2 }], 'Simple query failed');
  });

  it('should handle transactions', async () => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('INSERT INTO users (id, email) VALUES (999, \'smoke-test@example.com\')');
      await client.query('COMMIT');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  });
});

// Run tests
const start = Date.now();
const { failures } = require('mocha').run();
console.log(`Database smoke tests completed in ${Date.now() - start}ms`);
process.exit(failures > 0 ? 1 : 0);
```

### Key Considerations:
- **Test Database**: Use a staging-like database for smoke tests to avoid production contamination.
- **Schema Checks**: Focus on tables/columns critical to core functionality.
- **Transactions**: Test that your DB supports transactions (critical for data integrity).
- **Performance**: Avoid large queries or complex joins—keep tests fast.

---

## 3. Microservices Smoke Tests

For microservices architectures, smoke tests should:
- Verify inter-service communication.
- Test circuit breakers (e.g., Resilience4j, Hystrix).
- Ensure service discovery works.

### Example: Spring Boot Smoke Test with `@SpringBootTest`

```java
// SmokeTest.java (Spring Boot)
package com.example.smoketest;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class SmokeTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void contextLoads() {
        // Test that the application context loads (implicitly tests DB connection, etc.)
    }

    @Test
    void healthEndpointReturnsOk() {
        ResponseEntity<String> response = restTemplate.getForEntity("/actuator/health", String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"status\":\"UP\"");
    }

    @Test
    void userServiceReturnsValidUser() {
        ResponseEntity<String> response = restTemplate.getForEntity("/api/users/1", String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).contains("\"email\":\"test@example.com\"");
    }

    @Test
    void serviceDiscoveryWorks() {
        ResponseEntity<String> response = restTemplate.getForEntity("/config/version", String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
    }
}
```

### Key Considerations:
- **Port Binding**: Use `RANDOM_PORT` to avoid conflicts.
- **Actuator Endpoints**: Leverage Spring Actuator’s `/health` for quick checks.
- **Mock External Services**: If testing inter-service calls, mock slow dependencies (e.g., with WireMock).
- **Circuit Breaker Checks**: Test that retries and fallbacks work as expected.

---

## 3. Automating Smoke Tests in CI/CD

Smoke tests should be **automated and integrated into your deployment pipeline**. Here’s how to do it in popular platforms:

### GitHub Actions Example

```yaml
# .github/workflows/smoke-test.yml
name: Smoke Test

on:
  workflow_run:
    workflows: ["Deploy to Staging"]
    branches: [main]
    types:
      - completed

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run smoke tests
        run: npm run smoke-test
        env:
          API_URL: ${{ secrets.STAGING_API_URL }}
          DB_HOST: ${{ secrets.STAGING_DB_HOST }}
          DB_USER: ${{ secrets.STAGING_DB_USER }}

      - name: Notify on failure
        if: failure()
        uses: rtCamp/action-slack-notify@v2
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
          SLACK_COLOR: danger
          SLACK_TITLE: "Smoke Test Failed"
          SLACK_MESSAGE: "Deployment smoke test failed. Check logs."
```

### Key CI/CD Considerations:
- **Trigger**: Run after deployment (not before).
- **Environment**: Use staging/pre-prod environments for smoke tests.
- **Notifications**: Alert teams if smoke tests fail (e.g., Slack, PagerDuty).
- **Rollback**: Fail the pipeline if critical smoke tests fail (this can trigger a rollback).

---

# Common Mistakes to Avoid

While smoke testing is straightforward, there are pitfalls that can reduce its effectiveness:

1. **Overengineering Smoke Tests**
   - *Mistake*: Writing complex, slow smoke tests that resemble integration tests.
   - *Fix*: Keep them simple and focused on critical paths. Example: A smoke test shouldn’t test “user can checkout with 100 items”—it should test “`/checkout` endpoint returns `200`.”

2. **Ignoring False Positives/Negatives**
   - *Mistake*: Not handling flaky tests (e.g., timing out on slow DB connections).
   - *Fix*: Add retries for transient failures (e.g., 3 retries with 500ms delay).
   ```javascript
   async function retryWithTimeout(fn, retries = 3, timeoutMs = 500) {
     for (let i = 0; i < retries; i++) {
       try {
         return await fn();
       } catch (err) {
         if (i === retries - 1) throw err;
         await new Promise(res => setTimeout(res, timeoutMs));
       }
     }
   }
   ```

3. **Not Testing Database-Level Issues**
   - *Mistake*: Assuming the app layer will catch DB problems.
   - *Fix*: Always test DB connectivity, schema, and basic queries.

4. **Skipping Smoke Tests for “Quick” Deployments**
   - *Mistake*: Bypassing smoke tests to speed up deployments.
   - *Fix*: Treat smoke tests as a non-negotiable step. If they’re too slow, optimize them (parallelize tests, reduce scope).

5. **Not Documenting Smoke Test Scope**
   - *Mistake*: Smoke tests become “mystery meat” with undefined coverage.
   - *Fix*: Document which endpoints/tables are tested. Example:
     ```
     Smoke Test Coverage:
     - API: /health, /auth/login, /users/me
     - Database: users table exists, basic queries work
     - Dependencies: Redis connection alive
     ```

6. **Testing Only Happy Paths**
   - *Mistake*: Smoke tests only verify success cases.
   - *Fix*: Include basic error cases (e.g., `404` for missing resources, `401` for unauthorized access).

---

# Key Takeaways

Here’s a checklist for implementing smoke tests effectively:

- **Scope**: Focus on **critical paths** (auth, core APIs, DB connectivity). Avoid testing new features.
- **Speed**: Design tests to complete in **under 10 seconds**. Use parallelization if needed.
- **Automation**: Integrate smoke tests into **CI/CD pipelines** as a final validation step.
- **Determinism**: Avoid flaky tests. Use retries for transient failures.
- **Database**: Always test **connectivity, schema, and basic queries**.
- **Dependencies**: Verify **external services** (Redis, message queues) are reachable.
- **Notifications**: Fail fast and alert teams if smoke tests fail.
- **Documentation**: Maintain a list of **what is tested** and **what is not**.
- **Review**: Periodically review smoke tests to ensure they cover **new critical paths**.

---

# Conclusion: Why Smoke Testing Should Be Your Default

In fast-moving software environments, deployments happen at the speed of thought. But speed doesn’t excuse sloppiness. Smoke tests are the **invisible safety net** that catches the obvious before it becomes the obvious problem. They’re not about perfection—they’re about **redu