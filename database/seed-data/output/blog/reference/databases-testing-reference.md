# **[Pattern] Databases Testing – Reference Guide**

---

## **Overview**
This guide provides a structured approach to **databases testing**, covering core concepts, implementation best practices, and common reference artifacts. Effective database testing ensures data integrity, performance, and system reliability. This pattern includes test design principles, schema verification, query validation, transaction testing, and scalability checks. It applies to **relational databases (RDBMS)**, **NoSQL**, and hybrid architectures, with examples in SQL, NoSQL queries, and automated tooling. By following this guide, teams can systematically validate database behavior, reduce defects, and align testing with CI/CD pipelines.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                                                                                                                                                                                                                                           | **Example Tools**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Schema Validation**     | Ensures the database schema matches design requirements, including tables, relationships, constraints, and indexes.                                                                                                                                                                                                                                                                                                                  | SQL DDL validation, Liquibase, Flyway, SchemaSpy, PostgreSQL `pg_dump`             |
| **Data Integrity Checks** | Verifies constraints (e.g., `NOT NULL`, `UNIQUE`, `FOREIGN KEY`), referential integrity, and business rules.                                                                                                                                                                                                                                                                                                                           | `CHECK` constraints, foreign key validation, custom stored procedures              |
| **Query Testing**         | Tests SQL/NoSQL queries for correctness, performance (execution plans), and edge cases.                                                                                                                                                                                                                                                                                                                                             | JUnit (H2/Postgres in-memory), pgMustard, MongoDB Aggregation Test Suite            |
| **Transaction Testing**   | Validates ACID properties (Atomicity, Consistency, Isolation, Durability) across multiple operations.                                                                                                                                                                                                                                                                                                                                       | SQL `BEGIN/COMMIT/ROLLBACK`, Testcontainers, H2 embedded DB for unit testing        |
| **Performance Testing**   | Assesses query response times, concurrency, and scalability under load.                                                                                                                                                                                                                                                                                                                                                          | JMeter, Gatling, k6, database benchmarks (e.g., `EXPLAIN ANALYZE`, `EXPLAIN PLAN`) |
| **Backup & Recovery**     | Confirms backup integrity, point-in-time recovery, and disaster recovery procedures.                                                                                                                                                                                                                                                                                                                                                     | `pg_basebackup`, MySQL `mysqldump`, NoSQL exported JSON, Testcontainers snapshots  |
| **Data Migration**        | Validates schema/data changes across versions or environments (e.g., dev → production).                                                                                                                                                                                                                                                                                                                                         | Liquibase changelogs, Flyway SQL migrations, custom scripts                         |
| **Security Testing**      | Checks for SQL injection, unauthorized access, and data leaks (e.g., oversharing in NoSQL).                                                                                                                                                                                                                                                                                                                                              | OWASP ZAP, SQLMap, NoSQLMap, Policy-as-Code (e.g., Open Policy Agent)                |

---

## **Schema Reference**
Below are common database schema elements and their testing considerations.

| **Element**               | **Testing Focus**                                                                                                                                                                                                                                                                 | **Test Case Example**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Table Definition**      | Correct number of columns, data types, default values, and nullable flags.                                                                                                                                                                                           | ```sql SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users'; ``` |
| **Constraints**           | `NOT NULL`, `UNIQUE`, `PRIMARY KEY`, `CHECK` validity, and `FOREIGN KEY` referential integrity.                                                                                                                                                                               | ```sql INSERT INTO users (email) VALUES ('duplicate@example.com') -- Should fail ``` |
| **Indexes**               | Covering indexes, performance impact, and correct usage (e.g., `INCLUDE` clauses).                                                                                                                                                                                                   | ```sql EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 1; ```                |
| **Stored Procedures**     | Correct logic, input/output validation, and transaction handling.                                                                                                                                                                                                              | Call procedure with invalid parameters and verify error handling.                     |
| **Triggers**              | Timing, side effects, and correctness under concurrent operations.                                                                                                                                                                                                              | ```sql BEGIN TRIGGER update_timestamp AFTER UPDATE ON orders FOR EACH ROW BEGIN UPDATE timestamps SET last_updated = NOW(); END; ``` |
| **Views**                 | Query correctness, performance, and dependencies on underlying tables.                                                                                                                                                                                                       | ```sql SELECT * FROM view_name WHERE filter_column = 'value'; -- Verify rows match ``` |
| **Partitioning**          | Partition keys, query performance, and data locality.                                                                                                                                                                                                                           | ```sql CREATE TABLE logs PARTITION BY RANGE (log_date) (PARTITION p2023 VALUES LESS THAN ('2023-01-01')); ``` |
| **NoSQL Structures**      | Schema-less correctness, index design (e.g., MongoDB compound indexes), and query patterns.                                                                                                                                                                                                 | ```json { "_id": ObjectId("..."), "scores": { "math": 90, "science": 85 } } ```    |

---

## **Query Examples**
### **1. Schema Validation Queries**
**Verify Table Existence:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_name = 'users';
```

**Check for Missing Indexes (PostgreSQL):**
```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    indisprimary,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND idx_tup_read > 1000; -- Low scan rate but high reads → potential missing index
```

### **2. Data Integrity Queries**
**Test Foreign Key Referential Integrity:**
```sql
-- Attempt to delete a parent record referenced by a child
DELETE FROM users WHERE id = 1; -- Should fail if orders.user_id = 1 exists
```

**Validate `CHECK` Constraint:**
```sql
INSERT INTO products (price) VALUES (-10); -- Should fail if CHECK (price >= 0)
```

### **3. Query Performance Testing**
**Analyze Execution Plan (PostgreSQL):**
```sql
EXPLAIN ANALYZE
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2023-01-01';
```
**Look for:**
- Full table scans (`Seq Scan`) instead of index seeks (`Index Scan`).
- High cost values (>10% of total).

**NoSQL Query Performance (MongoDB):**
```javascript
// Verify compound index usage
db.orders.explain("executionStats").find({
  user_id: 1,
  status: "paid",
  created_at: { $gte: ISODate("2023-01-01") }
});
```
**Key Metrics:**
- `executionTimeMillis` (slow queries > 500ms).
- `totalDocsExamined` vs. `totalDocsReturned` (wasted reads).

### **4. Transaction Testing**
**Test Atomicity (Rollback on Error):**
```sql
BEGIN;
INSERT INTO accounts (user_id, balance) VALUES (1, 1000);
UPDATE accounts SET balance = balance - 1000 WHERE user_id = 2;
-- Simulate error (e.g., constraint violation)
INSERT INTO accounts (id) VALUES (9999999999); -- Fails if PRIMARY KEY constraint exists
ROLLBACK; -- Verify both inserts are undone
```

### **5. Backup Validation**
**Restore and Verify Backup (PostgreSQL):**
```bash
# Restore from backup
pg_restore -U postgres -d testdb -1 /path/to/backup.dump

# Verify table counts
SELECT COUNT(*) FROM users; -- Should match production data
```

### **6. Security Testing**
**SQL Injection Test (Parameterized Query vs. Concatenation):**
✅ **Safe:**
```sql
PREPARE safe_query (INT) AS SELECT * FROM users WHERE id = $1;
EXECUTE safe_query(1);
```
❌ **Vulnerable:**
```sql
-- Concatenating user input leads to SQL injection
EXECUTE 'SELECT * FROM users WHERE id = ''' || user_input || '''';
```

**NoSQL Injection Test (MongoDB):**
```javascript
// Safe: Use $where for complex queries (but risky if user-controlled)
// OR avoid $where and use aggregation pipelines
db.users.find({ $where: "this.email == 'admin@example.com'" });
```

---

## **Implementation Checklist**
| **Step**               | **Action Items**                                                                                                                                                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Schema Design**    | - Document schema in **ER diagrams** (e.g., Lucidchart, draw.io).<br>- Use version control for DDL (Liquibase, Flyway).                                                                                                                              |
| **2. Test Environment** | - Use **containers** (Docker, Testcontainers) for isolated testing.<br>- Seed test data with **fixture generators** (e.g., Faker, Testcontainers Java).                                                                                              |
| **3. Schema Validation**| - Automate schema checks in CI (e.g., `pg_schema_check`, `pg_tap`).<br>- Validate constraints with **unit tests** (JUnit, pytest).                                                                                                                    |
| **4. Query Testing**    | - Test **edge cases** (nulls, empty results, large datasets).<br>- Use **property-based testing** (Hypothesis for SQL).                                                                                                                             |
| **5. Performance**      | - Baseline queries with `EXPLAIN ANALYZE`.<br>- Load test with **JMeter** or **k6**.                                                                                                                                                                        |
| **6. Transaction Safety**| - Test **ACID violations** (e.g., deadlocks, phantom reads).<br>- Use **transaction logs** (e.g., PostgreSQL `pgBadger`) for auditing.                                                                                                                    |
| **7. Backup Testing**   | - Automate backup/restore in CI.<br>- Test **point-in-time recovery** (e.g., PostgreSQL `pg_archivecleanup`).                                                                                                                                            |
| **8. Security**         | - Scan for **SQL/NoSQL injection** (e.g., OWASP ZAP).<br>- Enforce **least privilege** (e.g., role-based access).                                                                                                                                          |
| **9. Migration Testing**| - Test **zero-downtime migrations** (e.g., Flyway `out-of-order` migrations).<br>- Validate data consistency post-migration.                                                                                                                          |
| **10. Monitoring**      | - Set up **alerts** for schema drifts (e.g., Great Expectations).<br>- Monitor **query performance** (e.g., Datadog, Prometheus).                                                                                                                 |

---

## **Query Examples by Database**
### **PostgreSQL**
```sql
-- Test window functions
SELECT
  user_id,
  SUM(amount) OVER (PARTITION BY user_id) AS total_spent,
  RANK() OVER (ORDER BY SUM(amount) DESC) AS spending_rank
FROM purchases;
```

### **MySQL**
```sql
-- Test stored procedure
CALL validate_order(12345, 100.00); -- Should update order_status if valid
```

### **MongoDB**
```javascript
// Test aggregation pipeline
db.orders.aggregate([
  { $match: { status: "paid" } },
  { $group: { _id: "$user_id", total: { $sum: "$amount" } } },
  { $sort: { total: -1 } }
]);
```

### **SQLite**
```sql
-- Test foreign key cascade
INSERT INTO orders (user_id, total)
VALUES (1, 50.00); -- Should cascade delete from users if ON DELETE CASCADE
```

---

## **Automation Tools**
| **Tool**                | **Purpose**                                                                                                                                                                                                                     | **Example Use Case**                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Liquibase/Flyway**    | Schema versioning and migration testing.                                                                                                                                                                           | Automate schema changes in CI/CD with rollback support.                            |
| **Testcontainers**      | Spin up isolated DB instances for testing.                                                                                                                                                                           | Run PostgreSQL in-memory for unit tests.                                             |
| **JUnit + H2**          | Embedded database for unit testing.                                                                                                                                                                                 | Test SQL queries without a full DB setup.                                            |
| **pgMustard**           | PostgreSQL test utilities (e.g., schema validation).                                                                                                                                                                    | Validate schema changes against a baseline.                                           |
| **MongoDB Aggregation Test Suite** | Test NoSQL query correctness.                                                                                                                                                                                   | Verify aggregation pipelines return expected results.                                |
| **Great Expectations**  | Data validation and testing.                                                                                                                                                                                       | Check for expected data distributions (e.g., no null emails).                       |
| **k6/JMeter**           | Database load testing.                                                                                                                                                                                             | Simulate 10K concurrent users for performance.                                       |
| **SQLMap**              | SQL injection testing.                                                                                                                                                                                           | Scan for vulnerable endpoints.                                                       |

---

## **Related Patterns**
1. **[Data Migration Testing]**
   - Focuses on validating schema/data changes across environments (e.g., Flyway changelogs, custom scripts).
   - *Related Artifacts:* Migration checklists, rollback procedures.

2. **[Performance Optimization]**
   - Complements this pattern by analyzing slow queries and indexing strategies.
   - *Related Artifacts:* Query execution plans, `EXPLAIN ANALYZE` reports.

3. **[CI/CD for Databases]**
   - Integrates database testing into pipelines (e.g., schema validation pre-deploy).
   - *Related Artifacts:* GitHub Actions workflows, Jenkins plugins for Liquibase.

4. **[Observability for Databases]**
   - Monitors database health (e.g., Prometheus metrics, APM tools).
   - *Related Artifacts:* Alerting rules for slow queries, deadlocks.

5. **[Data Governance]**
   - Ensures compliance with data policies (e.g., GDPR, PII handling).
   - *Related Artifacts:* Data classification, access logs.

6. **[Chaos Engineering for Databases]**
   - Tests resilience to failures (e.g., node kills in NoSQL clusters).
   - *Related Artifacts:* Failure injection scripts, recovery playbooks.

7. **[NoSQL Testing]**
   - Extends this pattern to schema-less databases (e.g., MongoDB, Cassandra).
   - *Related Artifacts:* Query pattern testing, data model validation.

---
## **Glossary**
| **Term**               | **Definition**                                                                                                                                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **ACID**               | Atomicity, Consistency, Isolation, Durability – properties of reliable transactions.                                                                                                                     |
| **Constraint**         | Rule enforcing data integrity (e.g., `NOT NULL`, `FOREIGN KEY`).                                                                                                                                           |
| **Coverage**           | Percentage of database elements tested (e.g., 80% of tables, 100% of queries).                                                                                                                              |
| **Deadlock**           | Transactional conflict where two processes wait indefinitely for each other’s locks.                                                                                                                       |
| **Index**              | Data structure improving query performance (e.g., B-tree, hash).                                                                                                                                           |
| **Partitioning**       | Dividing large tables into smaller, manageable chunks.                                                                                                                                                     |
| **Race Condition**     | Undesired behavior due to concurrent access (e.g., double-spending in payments).                                                                                                                          |
| **Schema Drift**       | Unintentional changes to the database schema (e.g., adding a column without documentation).                                                                                                               |
| **Stored Procedure**   | Precompiled SQL code stored on the database server.                                                                                                                                                        |
| **Transaction Log**    | Record of all database changes for recovery.                                                                                                                                                               |
| **View**               | Virtual table defined by a SQL query.                                                                                                                                                                     |

---
## **Further Reading**
- **[PostgreSQL Official Docs: Testing](https://www.postgresql.org/docs/current/testing.html)**
- **[MongoDB Aggregation Test Suite](https://github.com/mongodb-labs/mongo-testdata)**
- **[OWASP Database Testing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Database_Testing_Cheat_Sheet.html)**
- **[Testcontainers Documentation](https://www.testcontainers.org/)**
- **[Great Expectations Data Validation](https://docs.greatexpectations.io/)**