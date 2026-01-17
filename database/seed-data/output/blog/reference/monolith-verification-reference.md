# **[Pattern] Monolith Verification Reference Guide**

---

## **Overview**
The **Monolith Verification Pattern** ensures consistency, completeness, and correctness of large, tightly coupled codebases (monoliths) by systematically validating business logic, data integrity, and system behavior. Unlike traditional unit or integration testing, this pattern focuses on **end-to-end verification of critical workflows**, simulating real-world usage while minimizing risk in progressive refactoring. It bridges the gap between isolated tests and full-scale deployment, helping teams safely migrate monoliths to microservices or cloud-native architectures.

---

## **Key Concepts**
| **Term**               | **Description**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Monolith Scope**     | The bounded context of application logic to be verified (e.g., user registration, order processing).                                                                                                               |
| **Verification Rule** | A contract defining expected inputs, outputs, and edge cases for a workflow (e.g., "Order total must match line items").                                                                                       |
| **Mocked Dependencies**| Stubs/sandboxes for external systems (databases, APIs) to isolate verification from live infrastructure.                                                                                                          |
| **Verification Suite**| A collection of rules + predefined test data to validate a monolith’s behavior under varied conditions (e.g., happy path, error cases, concurrency).                                                      |
| **Verification Report**| A structured output (e.g., JSON, HTML) summarizing pass/fail outcomes, discrepancies, and suggested fixes.                                                                                                      |
| **Canary Rule**        | A subset of verification rules executed in production-like environments (e.g., staging) to detect latent issues before full rollout.                                                                           |

---

## **Implementation Details**

### **1. Schema Reference**
#### **Verification Rule Schema**
| Field               | Type           | Description                                                                                                                                                                                                                                                                 | Example Value                                                                                     |
|---------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `id`                | String (UUID)  | Unique identifier for the rule.                                                                                                                                                                                                                          | `"550e8400-e29b-41d4-a716-446655440000"`                                                             |
| `description`       | String         | Human-readable purpose of the rule.                                                                                                                                                                                                                          | `"Ensure order status transitions correctly from 'created' to 'shipped'."`                        |
| `scope`             | String         | System boundary (e.g., `auth-service`, `inventory-service`).                                                                                                                                                                                   | `"order-processing"`                                                                              |
| `preconditions`     | Array[Object]  | Inputs/data required for the rule.                                                                                                                                                                                                               | `[{"key": "userId", "type": "string", "value": "u123"}]`                                          |
| `steps`             | Array[Object]  | Sequential actions to trigger verification (e.g., API calls, database queries).                                                                                                                                                                      | `[{"method": "POST", "endpoint": "/orders", "payload": {...}}]`                                     |
| `assertions`        | Array[Object]  | Expected outcomes (e.g., response status, field values).                                                                                                                                                                                          | `[{"type": "statusCode", "expected": 201}, {"type": "field", "key": "status", "expected": "created"}]` |
| `errorHandling`     | String         | How to handle failures (e.g., `skip`, `fail`, `retry`).                                                                                                                                                                                           | `"fail"`                                                                                          |
| `tags`              | Array[String]  | Labels for categorization (e.g., `security`, `performance`).                                                                                                                                                                                      | `["critical-path", "end-to-end"]`                                                                |
| `priority`          | String         | Severity level (`low`, `medium`, `high`).                                                                                                                                                                                                         | `"high"`                                                                                          |

---
#### **Verification Suite Schema**
| Field          | Type           | Description                                                                                                                                                                                                           | Example Value                                                                                     |
|----------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `name`         | String         | Human-readable suite name (e.g., "Payment Workflow").                                                                                                                                                                | `"Checkout Process"`                                                                              |
| `rules`        | Array[Object]  | List of `VerificationRule` objects.                                                                                                                                                                                 | `[{...}, {...}]`                                                                                   |
| `environment`  | String         | Target environment (e.g., `staging`, `prod`).                                                                                                                                                                       | `"staging"`                                                                                       |
| `dependencies` | Array[String]  | External services required (e.g., `payment-gateway`, `logging-service`).                                                                                                                                            | `["datastore", "cache"]`                                                                          |
| `mockData`     | Object         | Predefined test data if applicable.                                                                                                                                                                                      | `{ "users": [...], "products": [...] }`                                                           |
| `excludedTags` | Array[String]  | Rules to skip (e.g., `["performance"]`).                                                                                                                                                                            | `[]`                                                                                               |

---

### **2. Query Examples**
#### **Query Verification Rules**
```sql
-- Schema (PostgreSQL example)
CREATE TABLE verification_rules (
    id UUID PRIMARY KEY,
    description TEXT,
    scope TEXT,
    preconditions JSONB,
    steps JSONB,
    assertions JSONB,
    error_handling TEXT,
    tags TEXT[],
    priority TEXT
);

-- Insert a rule for order validation
INSERT INTO verification_rules (
    id, description, scope, preconditions, steps, assertions, error_handling, tags, priority
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'Order total must equal sum of line items',
    'order-service',
    '["{"userId": "u123", "items": [{"productId": "p1", "quantity": 2}]}"]',
    '[
        {"method": "POST", "endpoint": "/orders", "payload": {"userId": "u123", "items": [{"productId": "p1", "quantity": 2}]}}
    ]',
    '[{"type": "calculation", "key": "total", "expected": 99.99}]',
    'fail',
    ['financial', 'critical-path'],
    'high'
);
```

#### **Query Verification Suite**
```python
# Example in Python (using `verification_suite` schema)
suite = {
    "name": "Payment Processing",
    "rules": [
        {
            "id": "rule1",
            "preconditions": {"amount": 100, "currency": "USD"},
            "steps": [
                {"method": "POST", "endpoint": "/payments", "payload": {"amount": 100}},
                {"method": "GET", "endpoint": "/payments/u123"}
            ],
            "assertions": [
                {"type": "statusCode", "expected": 200},
                {"type": "field", "key": "status", "expected": "completed"}
            ]
        }
    ],
    "environment": "staging"
}
```

#### **Example API Request (Postman/Newman)**
```http
POST /api/verification/suites
Headers:
  Content-Type: application/json

Body (JSON):
{
  "name": "User Authentication",
  "rules": [
    {
      "id": "auth-login",
      "steps": [
        {"method": "POST", "endpoint": "/auth/login", "payload": {"email": "test@example.com", "password": "secure123"}}
      ],
      "assertions": [
        {"type": "statusCode", "expected": 200},
        {"type": "tokenExists": true}
      ]
    }
  ]
}
```

---

### **3. Mocking Dependencies**
Use tools like:
- **Mock Service Worker (MSW)**: Intercept HTTP requests.
  ```javascript
  // Example: Mocking a database query
  import { setupWorker, rest } from 'msw';

  const worker = setupWorker(
    rest.get('/api/inventory/:id', (req, res, ctx) => {
      return res(ctx.status(200), ctx.json({ id: 'p1', stock: 5 }));
    })
  );
  ```
- **Testcontainers**: Spin up ephemeral databases (e.g., PostgreSQL).
  ```java
  // Java example
  PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13");
  postgres.start();
  ```
- **Custom Sandboxes**: Lightweight in-memory databases (e.g., SQLite for local testing).

---

### **4. Execution Workflow**
1. **Parse Suite**: Load `verification_suite` from config/database.
2. **Resolve Dependencies**: Use mocks/stubs for external systems.
3. **Execute Steps**:
   - For each rule, invoke steps in sequence (e.g., API calls, database ops).
   - Capture responses/errors.
4. **Validate Assertions**:
   - Compare outputs against `assertions`.
   - Log violations (e.g., `"Order total (99.99) ≠ expected (100.00)"`).
5. **Generate Report**:
   ```json
   {
     "suite": "Checkout Process",
     "environment": "staging",
     "status": "partial",
     "results": [
       {
         "rule": "order-creation",
         "status": "pass",
         "timestamp": "2023-10-01T12:00:00Z"
       },
       {
         "rule": "payment-validation",
         "status": "fail",
         "error": "Token expired",
         "details": {...}
       }
     ]
   }
   ```

---

### **5. Automation Pipeline**
Integrate with **CI/CD** (e.g., GitHub Actions, Jenkins):
```yaml
# GitHub Actions example
name: Monolith Verification
on: [push]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Verification Suite
        run: |
          npm install -g verification-cli
          verification-cli --suite "payment-processing" --env staging
      - name: Report Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: verification-report
          path: reports/*.json
```

---

## **Query Examples: Edge Cases**
| **Scenario**               | **Verification Rule Example**                                                                                                                                                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Concurrency Conflict**   | `assertions: [{"type": "atomic", "operation": "priceUpdate", "expected": "success"}]` (Ensures no race conditions during parallel updates).                                                                    |
| **Rate Limiting**          | `steps: [{"method": "POST", "endpoint": "/api/rate-limited", "delay": 1000}]` (Simulates throttling).                                                                                                               |
| **Data Migration**         | `preconditions: {"oldSchema": true}`, `assertions: [{"type": "schemaValidation", "expected": "newSchema"}]` (Validates post-migration state).                                                                     |
| **Third-Party API Failure**| `mockData: {"error": "Service Unavailable"}`, `assertions: [{"type": "fallback", "expected": true}]` (Tests graceful degradation).                                                                                   |
| **Security Validation**    | `tags: ["security"]`, `assertions: [{"type": "sqliCheck", "expected": false}]` (Detects SQL injection attempts).                                                                                                    |

---

## **Related Patterns**
| **Pattern**                     | **Relation to Monolith Verification**                                                                                                                                                                                                 |
|----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Strangler Pattern**            | Use verification to validate slices of the monolith before extracting them into microservices.                                                                                                                               |
| **Feature Flags**                | Deploy verification rules as feature flags to test canary releases without affecting all users.                                                                                                                          |
| **Contract Testing**             | Integrate with **OpenAPI/Swagger** contracts to verify API compliance between monolith and dependent services.                                                                                                       |
| **Chaos Engineering**            | Combine with chaos experiments (e.g., network partitions) to test resilience.                                                                                                                                              |
| **Canary Rollouts**              | Run verification suites on a subset of traffic before full deployment.                                                                                                                                                      |
| **Database Migration Validation**| Extend verification to include schema changes and data consistency checks.                                                                                                                                                   |
| **Performance Testing**          | Supplement with load testing to ensure verification rules scale under stress.                                                                                                                                               |

---
## **Best Practices**
1. **Prioritize Critical Paths**: Focus verification on high-risk workflows (e.g., payments, authentication).
2. **Isolate Mocks**: Use separate mock configurations per environment (dev/staging/prod).
3. **Automate Reporting**: Integrate with tools like **Jira**, **Slack**, or **PagerDuty** for alerts.
4. **Incremental Refinement**: Start with a small suite, then expand coverage over time.
5. **Document Assumptions**: Clearly note mocked behaviors (e.g., "Database returns hardcoded stock levels").
6. **Reuse Rules**: Share verification rules across teams via a **rule registry** (e.g., Git repo or database).
7. **Monitor False Positives**: Tune assertions to minimize noise (e.g., ignore minor timing variations).

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                                                                                                                                                 |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Postman/Newman**     | Execute verification suites via API collections.                                                                                                                                                              |
| **Pytest/Bdd**         | Framework for writing verification rules in Python (e.g., using `pyyaml` for schema definition).                                                                                                          |
| **Cypress**            | Frontend verification (e.g., UI workflows in monoliths).                                                                                                                                                  |
| **K6**                 | Load-test verification suites under concurrent load.                                                                                                                                                            |
| **Duct Tape Data**     | Schema validation for mock data.                                                                                                                                                                             |
| **AWS Step Functions** | Orchestrate complex verification workflows (e.g., cross-service validation).                                                                                                                            |

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                                                                                                                                                 |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Rule Fails Intermittently**       | Add retry logic with exponential backoff or check for flaky dependencies.                                                                                                                              |
| **Mock Misconfiguration**           | Validate mock responses against production API specs.                                                                                                                                                  |
| **Performance Bottlenecks**         | Parallelize rule execution or optimize mock responses.                                                                                                                                                      |
| **False Negatives**                 | Increase assertion strictness or add logging for edge cases.                                                                                                                                             |
| **Dependency Changes**              | Update mocked behaviors to reflect real-world changes.                                                                                                                                                     |

---
## **Example: Full Verification Suite for E-Commerce**
```yaml
# verification_suite.yaml
name: E-Commerce Checkout
environment: staging
rules:
  - id: order-creation
    scope: order-service
    preconditions: {userId: "u123", items: [{"productId": "p1", "quantity": 1}]}
    steps:
      - method: POST
        endpoint: /orders
        payload: {userId: "u123", items: [{"productId": "p1", "quantity": 1}]}
    assertions:
      - type: statusCode
        expected: 201
      - type: field
        key: status
        expected: created
    tags: [critical-path]

  - id: inventory-deduction
    scope: inventory-service
    preconditions: {orderId: "o456", productId: "p1"}
    steps:
      - method: PUT
        endpoint: /inventory/products/p1
        payload: {stock: 4}  # Expected: 5 → 4
    assertions:
      - type: statusCode
        expected: 200
      - type: calculation
        key: stock
        expected: 4
    dependencies: [datastore]

  - id: payment-processing
    scope: payment-service
    preconditions: {orderId: "o456", amount: 99.99}
    steps:
      - method: POST
        endpoint: /payments
        payload: {orderId: "o456", amount: 99.99}
    assertions:
      - type: statusCode
        expected: 200
      - type: field
        key: status
        expected: completed
    tags: [financial]
```
---
**Run with CLI**:
```bash
verification-cli --file verification_suite.yaml --output report.json
```

---
**Output (`report.json`)**:
```json
{
  "suite": "E-Commerce Checkout",
  "summary": {
    "totalRules": 3,
    "passed": 2,
    "failed": 1,
    "skipped": 0
  },
  "results": [
    {
      "rule": "order-creation",
      "status": "pass"
    },
    {
      "rule": "inventory-deduction",
      "status": "fail",
      "error": "Stock mismatch: expected 4, got 5 (race condition detected)"
    },
    {
      "rule": "payment-processing",
      "status": "pass"
    }
  ]
}
```