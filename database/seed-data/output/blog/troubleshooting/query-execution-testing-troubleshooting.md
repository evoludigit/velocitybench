# **Debugging End-to-End Query Testing: A Troubleshooting Guide**
*(Query Execution Testing Pattern)*

End-to-end (E2E) query tests ensure that database queries—from execution to result—integrate correctly across services, APIs, and storage layers. When these tests fail, the root cause is often buried in **orchestration, data state, network latency, or misconfigured test fixtures**. This guide provides a structured approach to diagnosing and resolving query execution issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

| Symptom | Possible Cause |
|---------|----------------|
| **Tests pass in isolation (unit/smoke) but fail in E2E** | Test environment mismatch (e.g., schema, permissions, or data seed differences). |
| **Random failures with "query not found" or "missing columns"** | Flaky test data or schema drift between dev/staging/prod. |
| **Slow failing tests (timeouts, hangs)** | Network latency, unoptimized queries, or deadlocks in test isolation. |
| **Inconsistent test results across runs** | Race conditions, dirty reads, or unsynchronized database state. |
| **Permission errors (e.g., `FORBIDDEN` on query execution)** | Test user lacks required roles or permissions. |
| **Tests pass locally but fail in CI** | Environment variables, connection strings, or test configurations differ between local and remote. |

---

## **2. Common Issues and Fixes**

### **Issue 1: Outdated or Inconsistent Test Data**
**Symptoms:**
- "Column X not found" errors despite schema matching.
- "No rows returned" when expected data exists.

**Root Cause:**
Test fixtures are not refreshed or seeded correctly before each test run.

**Fix:**
- **Ensure deterministic data seeding** using a transactional rollback mechanism.
  ```javascript
  // Example in Node.js with TypeORM (pseudo-code)
  beforeEach(async () => {
    await queryRunner.startTransaction();
    await queryRunner.manager.clear(); // Reset state
    await queryRunner.manager.save(users, testUser); // Seed test data
  });

  afterEach(async () => {
    await queryRunner.rollbackTransaction();
  });
  ```
- **Use a database reset tool** like [TestContainers](https://www.testcontainers.org/) for ephemeral DB instances.

---

### **Issue 2: Schema Migrations Not Applied in Test Environment**
**Symptoms:**
- "Table doesn’t exist" errors.
- Column definitions mismatch between prod and test.

**Root Cause:**
Migrations are applied only to production or dev environments but not test containers.

**Fix:**
- **Run migrations in a `beforeAll` hook** for the test suite.
  ```javascript
  // Example with TypeORM
  beforeAll(async () => {
    await connection.runMigrations(); // Apply pending migrations
  });
  ```
- **Use a dedicated test DB** (e.g., PostgreSQL via Docker) with migrations applied via CI/CD.

---

### **Issue 3: Slow Query Execution (Timeouts)**
**Symptoms:**
- Tests hang or fail with "Operation timed out."
- Slower than acceptable in CI but passes locally.

**Root Cause:**
- Unindexed queries in test data.
- Too many rows in test fixtures.
- Network latency between test runner and DB.

**Fix:**
- **Add test-specific indexes** to speed up query execution.
  ```sql
  CREATE INDEX idx_test_users_email ON test_users(email) WHERE test_flag = TRUE;
  ```
- **Limit test data volume** using `WHERE` clauses in seeds.
- **Use a lightweight test DB** (e.g., SQLite for unit tests, PostgreSQL for E2E).

---

### **Issue 4: Permission or Role Mismatch**
**Symptoms:**
- "Permission denied" or "Insufficient privileges" errors.
- Works locally but fails in CI.

**Root Cause:**
Test database user lacks required roles (e.g., `USAGE`, `INSERT`).

**Fix:**
- **Grant necessary permissions** via test initialization script.
  ```sql
  -- Example for PostgreSQL
  GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;
  GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO test_user;
  ```
- **Use environment variables** to override DB roles in tests.
  ```javascript
  const testUser = process.env.TEST_DB_USER || "default_test_user";
  ```

---

### **Issue 5: Race Conditions in Test Isolation**
**Symptoms:**
- Inconsistent test results across runs.
- "Duplicate key" errors due to unsynchronized state.

**Root Cause:**
- Tests run concurrently without transaction isolation.
- Shared database state between test runs.

**Fix:**
- **Isolate tests with transactions** (roll back after each test).
  ```javascript
  it("should handle transaction race conditions", async () => {
    await queryRunner.startTransaction();
    try {
      await testFunction(); // Test logic
      await queryRunner.commitTransaction();
    } catch (error) {
      await queryRunner.rollbackTransaction();
      throw error;
    }
  });
  ```
- **Use a new test DB instance per test suite** (TestContainers).

---

## **3. Debugging Tools and Techniques**

### **Tool 1: Database Logging**
- **Enable slow query logs** in your database (PostgreSQL example):
  ```sql
  ALTER SYSTEM SET log_min_duration_statement = '100'; -- Log queries >100ms
  ```
- **Use tools like:**
  - **PostgreSQL:** `pgBadger` or `pgAudit`.
  - **MySQL:** `mysqld --general-log=1`.
  - **MongoDB:** `$log` command or MongoDB Atlas logs.

### **Tool 2: Query Performance Profiling**
- **Capture slow queries in tests** using a wrapper:
  ```javascript
  const originalExecute = db.query;
  const slowQueryTimeout = 500; // ms

  db.query = async (query, params) => {
    const start = Date.now();
    const result = await originalExecute(query, params);
    if (Date.now() - start > slowQueryTimeout) {
      console.warn(`Slow query: ${query} (${Date.now() - start}ms)`);
    }
    return result;
  };
  ```

### **Tool 3: Test Data Validation**
- **Verify test data integrity** with checksums or schema checks:
  ```javascript
  async function validateTestData() {
    const rows = await db.query("SELECT COUNT(*) FROM users");
    if (rows[0].count !== 100) {
      throw new Error("Test data seed failed: incorrect row count");
    }
  }
  ```

### **Tool 4: Network Diagnostics**
- **Check DB connection latency** with `ping` or `telnet`:
  ```bash
  telnet db-host 5432  # Test PostgreSQL connection
  ```
- **Use `curl` to verify API endpoints**:
  ```bash
  curl -v http://api-server:3000/health
  ```

---

## **4. Prevention Strategies**
1. **Standardize Test Environments**
   - Use **Dockerized databases** (e.g., TestContainers) to ensure consistency.
   - Store test configurations in `.env` files (e.g., `DB_TEST_USER`, `DB_TEST_PASSWORD`).

2. **Automate Schema Validation**
   - Run `schema:check` migrations before tests.
   - Use tools like [SchemaSpy](https://github.com/schema-spy/schema-spy) to compare schemas.

3. **Isolate Test Data**
   - Seed test data in a **transaction** and roll back after each test suite.
   - Use **unique prefixes** for test tables (e.g., `test_users_123`).

4. **Monitor Test Flakiness**
   - Log test failures with **stack traces + DB state snapshots**.
   - Use **retries with jitter** for flaky tests (e.g., `jest-retry`).

5. **CI/CD Best Practices**
   - **Cache test databases** in CI to avoid rebuilds.
   - **Run migrations in CI** before test execution.

---

## **5. Step-by-Step Debugging Workflow**
1. **Reproduce the Failure**
   - Run the failing test in isolation: `npm test -- -t "failing-test"`.
   - Check CI logs for environment differences.

2. **Inspect Database State**
   - Connect to the test DB and run:
     ```sql
     SELECT * FROM test_table LIMIT 10; -- Verify seeded data
     EXPLAIN ANALYZE SELECT ...; -- Check query execution plan
     ```

3. **Enable Debug Logging**
   - Temporarily add `console.log` or `debug` statements in test code.
   - Enable database `log_statement`:
     ```sql
     SET log_statement = 'all'; -- PostgreSQL
     ```

4. **Compare with a Working Run**
   - Run a passing test and compare:
     - Query execution times.
     - Network latency (`ping`, `curl`).
     - Database roles (`GRANT` checks).

5. **Fix and Validate**
   - Apply fixes (e.g., schema sync, data seeding).
   - Re-run the test in isolation, then in the full suite.

---

## **Final Checklist Before Commits**
✅ Test data is seeded deterministically.
✅ Schema matches between dev/test/prod.
✅ Database user has correct permissions.
✅ Slow queries are optimized or ignored in tests.
✅ CI environment matches local (network, DB version).

---
**Key Takeaway:** End-to-end query test failures are rarely about the query itself—they’re usually about **environment divergence, data inconsistency, or orchestration issues**. By systematically isolating components (DB state, permissions, network) and using targeted debugging tools, you can resolve most issues within 1–2 hours.