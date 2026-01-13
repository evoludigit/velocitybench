# **[Pattern] Debugging Testing: Reference Guide**

---

## **Overview**
Debugging testing ensures that automated tests are reliable and actionable by detecting edge cases, failed assertions, and environmental discrepancies early. This pattern combines structured debugging practices with testing methodologies to identify root causes efficiently.

Key benefits:
- **Reduces flakiness** by pinpointing unstable test conditions.
- **Improves test maintainability** via clear error logging.
- **Accelerates root-cause analysis** with reproducible test failures.
- **Supports CI/CD stability** by catching intermittent failures.

Debugging testing integrates **assertion analysis**, **environmental validation**, and **log-based diagnostics** to create robust test suites.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                 | **Example Usage**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Assertion Analysis**    | Validates test expectations and suggests corrective actions when assertions fail. | `expect(api.getUser()).toHaveProperty('role', 'admin')` → *Error: User role is `viewer`*. |
| **Environmental Validation** | Checks for test infrastructure discrepancies (e.g., missing dependencies, config errors). | Preflight script: `assert(node_modules_exists('required-lib'), 'Dependency missing.').` |
| **Log-Based Diagnostics** | Parses test logs for performance bottlenecks, race conditions, or silent errors. | Log snippet: `WARN: Database query took 5s (expected <1s).` → Trigger retry/circuit-breaker. |
| **Repro Steps Template**  | Standardized format for documenting test failure conditions.                     | `Steps to Reproduce: \n1. Create user with `role=viewer`.\n2. Navigate to `/admin`.\n3. Assert `403 Forbidden` fails.` |
| **Test Retry Strategy**   | Configurable retry logic for transient failures (e.g., network timeouts).       | `retryPolicy: { attempts: 3, delay: 2000ms }`.                                         |

---

## **Implementation Details**

### **1. Assertion Analysis**
**Purpose**: Differentiate between expected failures (design choices) and unexpected ones (bugs).

**Implementation Steps**:
1. **Tag assertions** with severity (e.g., `expect(user).toBeValid('high-severity')`).
2. **Use descriptive messages** for failures:
   ```javascript
   expect(apiResponse).toMatchObject({
     status: 'success',
     data: { kind: 'user', id: userId }
   }).withMessage(`User ${userId} not found in response.`);
   ```
3. **Group related assertions** into test blocks for granular debugging:
   ```javascript
   describe('User Creation', () => {
     it('should create user with valid credentials', () => {
       // Individual assertions with custom error messages
     });
   });
   ```

**Tools**:
- **Playwright/TestCafe**: Built-in assertion libraries with custom error handlers.
- **Custom wrappers**: Extend `chai.expect` or `jest.expect` for domain-specific validation.

---

### **2. Environmental Validation**
**Purpose**: Ensure tests run in a consistent state by validating preconditions.

**Implementation**:
- **Preflight checks** (run before test suites):
  ```javascript
  // Example: Check database connection
  beforeAll(async () => {
    await db.connect();
    const health = await db.query('SELECT 1');
    if (!health.rows[0]) throw new Error('Database connection failed.');
  });
  ```
- **Mock dependency validation** (for isolated tests):
  ```javascript
  test('User API: Valid credentials', async () => {
    mockAuthService.stub('validate', () => Promise.resolve({ valid: true }));
    // Test logic...
  });
  ```
- **Environment variable checks**:
  ```javascript
  if (!process.env.API_URL) throw new Error('API_URL not configured.');
  ```

**Tools**:
- **Docker Compose**: Spin up isolated test environments.
- **Nock/Supertest**: Mock external APIs for consistency.

---

### **3. Log-Based Diagnostics**
**Purpose**: Extract actionable insights from test logs.

**Implementation**:
- **Structured logging**:
  ```javascript
  console.log({
    event: 'test-failure',
    testId: 'user-login',
    error: 'Invalid credentials',
    stackTrace: error.stack
  });
  ```
- **Log parsing scripts** (Python example):
  ```python
  import re
  def find_timeouts(log):
      return re.findall(r'timeout after (\d+)ms', log)
  ```
- **Alerting thresholds**:
  - Log `WARN` if a test exceeds 95th percentile execution time.
  - Log `ERROR` if a test fails 3+ times in a row.

**Tools**:
- **ELK Stack**: Centralized log analysis.
- **Sentry**: Error tracking for test failures.

---

### **4. Repro Steps Template**
**Purpose**: Standardize failure reporting to reduce debugging time.

**Format**:
```markdown
# [Test Name] Failure
**Steps to Reproduce**:
1. [Action 1]
2. [Action 2]
3. [Assertion that failed]

**Expected**: [Result]
**Actual**: [Result] + [Error log snippet]
**Environment**:
- OS: [Linux/macOS/Windows]
- Node: v[16.13.0]
- Test Framework: Jest/[Framework]
```

**Example**:
```markdown
# "User Profile: Fetch" Failure
**Steps to Reproduce**:
1. Call `GET /api/users/123` with `Authorization: Bearer token`.
2. Assert `status === 200`.

**Expected**: User data with `role: admin`.
**Actual**: `403 Forbidden` + `Logs: "User 123 has no permissions."`
**Environment**:
- Node: v18.12.1
- Framework: Playwright
```

---

### **5. Test Retry Strategy**
**Purpose**: Handle intermittent failures (e.g., race conditions, network issues).

**Implementation**:
- **Fixed retry count**:
  ```javascript
  test('API call with retry', async () => {
    await retryUntil(() => apiCall(), { maxAttempts: 3, delay: 1000 });
  }, 3000);
  ```
- **Exponential backoff**:
  ```javascript
  const retries = async (fn, maxRetries = 3) => {
    for (let i = 0; i < maxRetries; i++) {
      try { return await fn(); }
      catch (e) { await delay(1000 * 2 ** i); }
    }
    throw new Error('Max retries exceeded.');
  };
  ```

**Tools**:
- **Jest Retry**: Built-in retry mechanism.
- **Pytest-retries**: Retry plugin for Python tests.

---

## **Schema Reference**
| **Component**               | **Schema**                                                                 | **Purpose**                                  |
|-----------------------------|----------------------------------------------------------------------------|---------------------------------------------|
| **Assertion**               | `{ condition: boolean, message: string, severity: 'low|medium|high' }` | Defines test expectations with context.      |
| **Preflight Check**         | `{ type: 'db|env|api', check: function, required: boolean }` | Validates test environment prerequisites.  |
| **Log Entry**               | `{ timestamp: Date, level: 'info|warn|error', details: object }` | Structured test execution logs.            |
| **Retry Policy**            | `{ attempts: number, delay: number, maxDelay: number }` | Configures retry logic for flaky tests.     |
| **Failure Report**          | `{ testId: string, steps: Array<string>, actual: any, expected: any }`  | Standardized failure documentation.        |

---
## **Query Examples**

### **1. Assertion Analysis Query**
**Scenario**: Find all test failures with `high-severity` assertions.

**SQL (for test databases)**:
```sql
SELECT *
FROM test_results
WHERE assertion_severity = 'high'
  AND status = 'failed'
ORDER BY failure_time DESC;
```

**Jest Command**:
```bash
jest --findRelatedTests --testResultsFile=jest-junit.xml \
  | xargs grep -l "high-severity"  # Filter high-severity logs
```

---

### **2. Environmental Validation Query**
**Scenario**: Identify tests failing due to missing dependencies.

**Example Query (Log Analysis)**:
```bash
grep "Dependency missing" test-logs-*.txt | \
  awk '{print $NF}' | sort | uniq -c
```

**Output**:
```
   5 node_modules/webdriverio/dist/
   3 @types/chai
```

---

### **3. Log-Based Diagnostics Query**
**Scenario**: Detect tests exceeding timeout thresholds.

**Python Script**:
```python
from elasticsearch import Elasticsearch
es = Elasticsearch()

def find_timeouts():
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"event": "test-failure"}},
                    {"range": {"execution_time": {"gt": 5000}}}  # >5s
                ]
            }
        }
    }
    return es.search(index="test-logs", body=query)
```

---

### **4. Repro Steps Extraction**
**Scenario**: Parse failure reports for common patterns.

**Bash Command**:
```bash
grep -E -A 5 "Steps to Reproduce" failure-reports/ | \
  grep -oP '(?<=1\. ).*(?=\n2\.)' >> common_steps.txt
```

**Output** (`common_steps.txt`):
```
Create user with role=viewer.
Navigate to /admin.
Assert 403 forbidden status.
```

---

### **5. Retry Strategy Optimization**
**Scenario**: Analyze which tests benefit from retry policies.

**Jest Stats**:
```bash
jest --updateSnapshot --runInBand --passWithNoTests | \
  awk '/Passed/,/Failed/ {print}' > test_stats.txt
```
**Filter retries needed**:
```bash
grep -E "Failed:.+Passed:.+" test_stats.txt | \
  awk '{if ($2 > $4) print $1}'  # Tests where failures > passes
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------|
| **Test Pyramid**          | Structures tests by level (unit > integration > E2E) to optimize debugging.     | When balancing test speed and coverage.        |
| **Property-Based Testing** | Generates random inputs to find edge cases (e.g., QuickCheck).               | Debugging assertions that fail unpredictably.    |
| **Test Containers**       | Uses disposable containers (Docker) for isolated test environments.          | When environment inconsistencies cause failures.|
| **Canary Testing**        | Gradually rolls out test changes to catch regressions early.                  | For large test suites with high churn.          |
| **Observability Testing** | Integrates metrics (APM) to debug performance bottlenecks.                    | When tests are slow or intermittent.           |

---

## **Best Practices**
1. **Tag failures**: Label test failures by type (e.g., `env-issue`, `assertion-error`).
2. **Automate repro steps**: Generate repro templates from test failures.
3. **Isolate flaky tests**: Use statistical methods (e.g., [Flaky Test Finder](https://github.com/google/flaky-test-finder)) to identify intermittent failures.
4. **Correlate logs**: Link test failures to application logs (e.g., via correlation IDs).
5. **Document edge cases**: Update tests with known failure conditions (e.g., "Fails on IE11").

---
## **Anti-Patterns**
- **Broad assertions**: Avoid `expect(obj).toBeDefined()`; use `expect(obj).toHaveProperty('key')`.
- **Ignoring preflight checks**: Skipping `beforeAll` validations risks undetected environment issues.
- **Silent retries**: Retry without logging increases debug time (always log retry attempts).
- **Over-retrying**: Retrying too many times masks root causes (e.g., 10 retries for a `500` error).
- **Generic failure messages**: Replace `AssertionError` with `InvalidUserRoleError` for actionable debugging.