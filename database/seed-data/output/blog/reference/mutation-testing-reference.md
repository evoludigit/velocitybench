# **[Pattern] Mutation Testing Reference Guide**

---

## **Overview**
**Mutation Testing** is a fault-based software testing technique that validates the effectiveness of test cases by intentionally introducing small, synthetic errors (mutations) into code and verifying whether existing tests can detect them. Unlike traditional coverage-based testing, mutation testing provides a quantitative measure of test suite quality by identifying "killed" (detected) and "survived" (undetected) mutants. This pattern is particularly valuable for verifying the robustness of unit tests, integration tests, and even stored procedures in databases.

Key benefits include:
- Quantifying test suite strength via **mutation score** (percentage of killed mutants).
- Identifying **flawed test cases** that miss critical edge cases.
- Detecting **overconfidence** in test coverage when high coverage doesn’t correlate with high mutant kill rate.
- Supporting **CI/CD pipelines** to ensure test quality is maintained over time.

Mutation testing is widely used in programming languages (e.g., Python with `mutmut`, Java with `PIT`), but this reference focuses on its application to **database systems**, specifically stored procedures.

---

## **Schema Reference**
Below is a conceptual schema for mutation testing in a database context, including entities, attributes, and relationships:

| **Entity**               | **Description**                                                                                     | **Key Attributes**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Mutation Test Suite**  | A collection of tests designed to validate mutation detection and kill rates.                       | `id`, `name`, `database`, `mutation_engine`, `created_at`, `updated_at`                              |
| **Stored Procedure**     | A database function or procedure undergoing mutation testing.                                         | `id`, `name`, `schema`, `language`, `definition`, `last_modified_at`                                  |
| **Mutant**               | A syntactically valid but intentionally flawed version of a stored procedure.                        | `id`, `procedure_id`, `mutation_type`, `mutation_location`, `description`, `survived`, `killed_at`   |
| **Test Case**            | An existing test (unit/integration) that should detect mutations.                                   | `id`, `name`, `type` (unit/integration), `procedure_id`, `assertion`, `execution_status`             |
| **Mutation Engine**      | A tool or service that generates and evaluates mutants.                                             | `name`, `support_language`, `mutation_strategies`, `version`                                           |
| **Mutation Result**      | Outcome of a mutant’s execution (detected or missed by tests).                                        | `id`, `mutant_id`, `test_case_id`, `result` (killed/survived), `timestamp`, `diagnostic_message`     |
| **Mutation Score**       | Metric tracking effectiveness of the test suite.                                                   | `test_suite_id`, `score` (decimal, 0–1), `total_mutants`, `killed_mutants`, `survived_mutants`        |

---
## **Mutation Types for Stored Procedures**
Mutations are categorized by the type of syntactic or logical change introduced. Below are common mutation types applicable to stored procedures:

| **Mutation Type**        | **Description**                                                                                     | **Example (SQL)**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Logical Operator Flip**| Flips logical operators (e.g., `AND` ↔ `OR`, `=` ↔ `!=`).                                            | Original: `SELECT * FROM users WHERE active = true;`
Mutant: `SELECT * FROM users WHERE active != true;`                                                      |
| **Arithmetic Operator Flip** | Replaces arithmetic operators (e.g., `+` ↔ `-`, `*` ↔ `/`).                                          | Original: `amount = price * quantity;`
Mutant: `amount = price / quantity;`                                                                    |
| **Comparison Flip**      | Reverses comparison results (e.g., `>` ↔ `<`, `>=` ↔ `<=`).                                          | Original: `IF (salary > 100000) THEN...`
Mutant: `IF (salary < 100000) THEN...`                                                                  |
| **Statement Deletion**   | Removes or comments out a critical statement (e.g., `WHERE`, `UPDATE`).                              | Original: `UPDATE orders SET status = 'shipped' WHERE shipped_date IS NULL;`
Mutant: `UPDATE orders SET status = 'shipped';` (commented-out `WHERE` clause)                            |
| **Literal Value Change** | Modifies constants (e.g., `1000` → `2000`, `true` → `false`).                                         | Original: `IF (count > 500) THEN...`
Mutant: `IF (count > 2000) THEN...`                                                                        |
| **Function Call Replacement** | Replaces functions with no-ops or synonyms (e.g., `SUM` → `COUNT`).                                  | Original: `total = SUM(sales);`
Mutant: `total = COUNT(sales);`                                                                          |
| **Variable Name Change** | Renames variables to reflect logical errors (e.g., `valid` → `invalid`).                              | Original: `IF (is_valid) THEN...`
Mutant: `IF (is_invalid) THEN...`                                                                        |

---
## **Implementation Details**
### **1. Setup**
To implement mutation testing for stored procedures:

1. **Tool Selection**:
   - **PITest** (Java-based, supports database drivers via integration tests).
   - **Infuse** (Python-based, extendable to SQL via CLI).
   - **Custom Scripts**: Automated tools like **SQLUnit** or **dbt** with custom plugins.

2. **Integration**:
   - **CI/CD Pipeline**: Add mutation testing as a post-test step in builds.
   - **Database Connection**: Ensure tools can connect to your database (e.g., PostgreSQL, MySQL) and execute tests.
   - **Test Coverage**: Ensure tests cover critical paths (e.g., 100% branch coverage for stored procedures).

3. **Mutation Engine Configuration**:
   - Specify mutation strategies (e.g., enable/disable specific mutations like `StatementDeletion`).
   - Limit mutants to avoid excessive runtime (e.g., cap at 100 mutants per procedure).

---
### **2. Running Mutation Tests**
Example workflow for a PostgreSQL stored procedure:

```bash
# Example using a hypothetical mutation tool (e.g., "sqlmut"):
sqlmut run \
  --db-url "postgres://user:pass@localhost:5432/mydb" \
  --procedure "sp_calculate_discount" \
  --test-suite "unit_tests" \
  --output-dir "/reports/mutation_results" \
  --max-mutants 50
```

#### **Output Analysis**:
```json
{
  "test_suite": "unit_tests",
  "procedure": "sp_calculate_discount",
  "total_mutants": 47,
  "killed_mutants": 38,
  "survived_mutants": 9,
  "score": 0.8085,
  "diagnostics": [
    {
      "mutant_id": 42,
      "type": "LogicalOperatorFlip",
      "location": "WHERE price > 100",
      "survived": true,
      "test_cases_missed": ["test_high_price_edge_case"]
    }
  ]
}
```

---
### **3. Interpreting Results**
- **Score < 0.8**: Low test quality; review survived mutants and add edge-case tests.
- **Score ≥ 0.8**: High test quality; but ensure tests are not overly simplistic.
- **Survived Mutants**: Investigate why tests missed logical errors (e.g., missing assertions, race conditions).

---
### **4. Optimizing Mutation Testing**
- **Selective Mutations**: Focus on critical procedures/procedures with high business risk.
- **Parallel Execution**: Speed up testing by running mutants concurrently (e.g., using Kubernetes).
- **CI/CD Feedback**: Integrate mutation scores into dashboards (e.g., GitHub Actions, JIRA).

---

## **Query Examples**
### **1. Generating Mutants for a Procedure**
*(Pseudocode for a hypothetical `sqlmut` CLI tool)*

```sql
-- Original stored procedure (example in SQL)
CREATE OR REPLACE PROCEDURE sp_approve_order(
    IN order_id INT,
    OUT status TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM orders WHERE id = order_id AND status = 'pending') THEN
        UPDATE orders SET status = 'approved' WHERE id = order_id;
        status := 'Success';
    ELSE
        status := 'Error: Order not found';
    END IF;
END;
$$;
```

**Mutant Generated**:
```sql
-- Mutant: StatementDeletion (removed UPDATE)
CREATE OR REPLACE PROCEDURE sp_approve_order_mutant(
    IN order_id INT,
    OUT status TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM orders WHERE id = order_id AND status = 'pending') THEN
        -- UPDATED COMMENTED OUT
        -- UPDATE orders SET status = 'approved' WHERE id = order_id;
        status := 'Success';
    ELSE
        status := 'Error: Order not found';
    END IF;
END;
$$;
```

---
### **2. Evaluating a Mutant**
```sql
-- Test case (unit test) to validate sp_approve_order
DO $$
DECLARE
    test_order_id INT := 123;
BEGIN
    INSERT INTO orders (id, status) VALUES (test_order_id, 'pending');
    CALL sp_approve_order(test_order_id, status);
    RAISE NOTICE 'Result: %', status;
    IF status != 'Success' THEN
        RAISE EXCEPTION 'Test failed';
    END IF;
END $$;
```

**Mutant Evaluation**:
- Original test passes (status = 'Success').
- Mutant survives (no `UPDATE` → status remains `'Error: Order not found'`).
- **Result**: Test missed the missing `UPDATE` statement.

---
### **3. Viewing Mutation Results in a Database**
Store results in a `mutation_results` table:
```sql
CREATE TABLE mutation_results (
    id SERIAL PRIMARY KEY,
    mutant_id INT,
    test_case_id INT,
    result VARCHAR(20) CHECK (result IN ('killed', 'survived')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    diagnostic_message TEXT
);
```

**Insert Result**:
```sql
INSERT INTO mutation_results (mutant_id, test_case_id, result, diagnostic_message)
VALUES (42, 1, 'survived', 'Test did not detect missing UPDATE statement');
```

**Query Survived Mutants**:
```sql
SELECT m.mutation_type, m.description, tr.diagnostic_message, t.name AS test_case
FROM mutation_mutants m
JOIN mutation_results tr ON m.id = tr.mutant_id
JOIN test_cases t ON tr.test_case_id = t.id
WHERE tr.result = 'survived'
ORDER BY tr.timestamp DESC;
```

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Synergy with Mutation Testing**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Test-Driven Development (TDD)** | Writing tests before implementation to ensure coverage.                                             | Mutation testing validates that TDD tests are robust.                                               |
| **Parameterized Testing** | Reusing test logic with different inputs.                                                           | Helps detect mutants that affect specific parameter combinations.                                  |
| **Behavior-Driven Development (BDD)** | Tests written in plain language (e.g., Gherkin).                                                    | Mutation testing ensures BDD scenarios catch edge cases.                                            |
| **Continuous Integration (CI)** | Automated testing in CI pipelines.                                                                  | Mutation testing as a CI step ensures test quality is maintained.                                   |
| **Database Testing (e.g., SQLUnit)** | Unit testing for SQL queries/procedures.                                                          | Mutation testing validates SQLUnit tests for stored procedures.                                     |
| **Chaos Engineering**     | Introducing failures to test resilience.                                                           | Mutation testing introduces *controlled* failures to validate tests against defects.               |

---
## **Best Practices**
1. **Start Small**: Mutate only high-risk procedures initially.
2. **Combine with Coverage**: Ensure mutation testing follows 100% branch coverage.
3. **Focus on Survived Mutants**: Fix tests that miss critical defects.
4. **Automate Feedback**: Integrate mutation scores into code reviews.
5. **Limit Mutants**: Use `--max-mutants` to avoid excessive runtime.

---
## **Limitations**
- **Performance Overhead**: Mutation testing is computationally intensive.
- **False Positives**: Some mutants may not be syntactically valid or relevant.
- **Tooling Gaps**: Limited native support for mutation testing in databases vs. programming languages.

---
## **Further Reading**
- [PITest Documentation](https://pitest.org/)
- [Mutation Testing in Practice (Journal Paper)](https://dl.acm.org/doi/10.1145/3304731.3304748)
- [SQLUnit for Database Testing](http://sqlunit.github.io/)
- [Infuse Mutation Testing](https://infuse.readthedocs.io/)