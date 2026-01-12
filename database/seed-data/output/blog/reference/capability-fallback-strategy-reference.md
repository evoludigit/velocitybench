# **[Pattern] Capability Fallback Strategy Reference Guide**

---

## **1. Overview**
The **Capability Fallback Strategy** pattern addresses scenarios where a database lacks a native feature required for a specific application logic. Instead of rewriting queries or abandoning functionality, this pattern defines a systematic approach to emulate missing capabilities using available constructs. This is particularly useful when working with legacy systems, third-party databases, or older versions of database engines that lack advanced features like window functions, CTEs, or JSON handling.

The pattern follows these principles:
- **Separation of Logic**: Decompose feature requirements into core and fallback implementations.
- **Performance Equivalence**: Ensure fallback methods maintain acceptable query performance.
- **Backward Compatibility**: Allow gradual upgrades by supporting both new and legacy implementations.
- **Clear Documentation**: Explicitly label fallback logic to aid maintenance.

For example, if a database lacks native full-text search capabilities, the fallback might involve string manipulation functions (`LIKE` + `REGEXP`) or pre-computed indexes.

---

## **2. Schema Reference**
The following tables describe key components of the **Capability Fallback Strategy**.

### **2.1 Core Components**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Feature Gap**              | The missing database capability (e.g., `JSON_EXTRACT`, `WITH RECURSIVE`, or `LATERAL JOIN`).                                                                                                                 | `Database does not support `ARRAY_CONTAINS` for PostgreSQL v10.0 or earlier.`                  |
| **Core Implementation**       | The ideal feature (e.g., a window function, JSON parser).                                                                                                                                                   | `WITH cte AS (SELECT ..., ROW_NUMBER() OVER (PARTITION BY category ORDER BY date) as rn)`     |
| **Fallback Logic**            | Alternative query logic to replicate the core functionality using supported constructs.                                                                                                                     | `SELECT *, @row_number:=@row_number+1 AS rn FROM table, (SELECT @row_number:=0) AS init`     |
| **Performance Considerations** | Notes on efficiency (e.g., index usage, temporary tables, or cursor-based approaches).                                                                                                                        | Fallback may require higher memory or slower I/O (e.g., self-joins vs. window functions).     |
| **Migration Path**            | Steps to upgrade once the database supports the core feature (e.g., feature flags, dynamic query switching).                                                                                            | Replace fallback with core logic when `feature_version >= 11.0`.                               |

---

### **2.2 Common Fallback Strategies by Capability**
| **Missing Capability**               | **Fallback Strategy**                                                                                                                                                                                                 | **Trade-offs**                                                                                     |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Window Functions**                  | Self-joins or cumulative counters (e.g., `@rownum:=@rownum+1`).                                                                                                                                                     | Higher CPU usage; may block row locks.                                                              |
| **JSON Support**                      | String manipulation (`SUBSTRING`, `STRPOS`, `SPLIT_PART`) or pre-parsed columns.                                                                                                                                  | No schema enforcement; manual parsing errors risk.                                                   |
| **CTEs (WITH clause)**                | Derived tables or temporary tables.                                                                                                                                                                           | Less readable; requires explicit `JOIN` syntax.                                                      |
| **Recursive Queries**                 | Application-level recursion or iterative cursors.                                                                                                                                                             | Poor scalability for deep hierarchies.                                                              |
| **Full-Text Search**                  | `LIKE` with wildcards (`%word%`) or pre-indexed tokenized columns.                                                                                                                                              | Slower than native `FULLTEXT`; less accurate matching.                                              |
| **LATERAL JOINs**                     | Correlated subqueries or application-side joins.                                                                                                                                                              | Higher overhead; harder to optimize.                                                                |
| **ARRAY Operations**                  | String parsing (`REGEXP_SUBSTR`) or manual iteration (e.g., `UNNEST` in newer versions).                                                                                                                     | Manual cleanup of malformed data.                                                                  |
| **Common Table Expressions (CTEs)**   | Temporary tables or dynamic SQL.                                                                                                                                                                             | Less portable; requires `DROP TABLE` cleanup.                                                       |

---

## **3. Query Examples**
The following examples demonstrate the **Capability Fallback Strategy** for common scenarios.

---

### **3.1 Fallback for Window Functions (e.g., `ROW_NUMBER`)**
**Missing Capability**: Database lacks `ROW_NUMBER() OVER (PARTITION BY ...)`.
**Core Implementation (PostgreSQL+)**:
```sql
WITH ranked_sales AS (
    SELECT
        product_id,
        sale_date,
        sale_amount,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY sale_date DESC) as rank
    FROM sales
)
SELECT * FROM ranked_sales WHERE rank <= 3;
```

**Fallback (Legacy MySQL < 8.0)**:
```sql
SELECT
    s1.product_id,
    s1.sale_date,
    s1.sale_amount,
    @rownum := CASE WHEN @product_id = s1.product_id THEN @rownum + 1 ELSE 1 END as rank,
    @product_id := s1.product_id
FROM
    sales s1,
    (SELECT @rownum := 0, @product_id := NULL) init
WHERE
    @rownum <= 3
ORDER BY
    s1.product_id, s1.sale_date DESC;
```

---

### **3.2 Fallback for JSON Extraction**
**Missing Capability**: Database lacks `JSON_EXTRACT` (e.g., MySQL < 8.0).
**Core Implementation (MySQL 8.0+)**:
```sql
SELECT
    user_id,
    JSON_EXTRACT(data, '$.address.city') as city
FROM users;
```

**Fallback (Legacy MySQL)**:
```sql
SELECT
    user_id,
    SUBSTRING_INDEX(
        SUBSTRING_INDEX(
            data,
            'city": "', 1
        ),
        '",',
        1
    ) as city
FROM users;
```

**Alternative (Pre-Parsed Column)**:
```sql
-- Pre-compute and store JSON fields as columns
ALTER TABLE users ADD COLUMN city VARCHAR(100);
UPDATE users
SET city = JSON_EXTRACT(data, '$.address.city'); -- Only do this if JSON support is added later
```

---

### **3.3 Fallback for Recursive Queries**
**Missing Capability**: Database lacks `WITH RECURSIVE` (e.g., Oracle 11g).
**Core Implementation (PostgreSQL/Oracle 12+)**:
```sql
WITH RECURSIVE org_hierarchy AS (
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    SELECT e.id, e.name, e.manager_id, oh.level + 1
    FROM employees e
    JOIN org_hierarchy oh ON e.manager_id = oh.id
)
SELECT * FROM org_hierarchy;
```

**Fallback (Oracle 11g)**:
```sql
-- Application-side recursion (pseudo-code)
DECLARE
    TYPE emp_rec IS RECORD (id NUMBER, name VARCHAR2(100), level NUMBER);
    emp_list emp_rec;
BEGIN
    -- Base case: root employees
    FOR root IN (SELECT id, name FROM employees WHERE manager_id IS NULL) LOOP
        INSERT INTO result_values VALUES (root);
        -- Recursive call (simplified)
        CALL process_subordinates(root.id, level + 1);
    END LOOP;
END;
/
```

**Alternative (Cursor-Based)**:
```sql
-- PL/SQL cursor for recursion
DECLARE
    emp_id NUMBER;
    level NUMBER := 1;
BEGIN
    -- Start with root employees
    FOR emp_cursor IN (SELECT id FROM employees WHERE manager_id IS NULL) LOOP
        emp_id := emp_cursor.id;
        -- Use a context variable to track level
        -- (MySQL/non-PL/SQL: Use application logic)
    END LOOP;
END;
/
```

---

### **3.4 Fallback for Full-Text Search**
**Missing Capability**: Database lacks `FULLTEXT` index (e.g., SQLite).
**Core Implementation (PostgreSQL/MySQL)**:
```sql
CREATE FULLTEXT INDEX idx_search ON articles (content);
SELECT * FROM articles WHERE MATCH(content) AGAINST('database patterns');
```

**Fallback (SQLite)**:
```sql
-- Pre-tokenize content (e.g., during ETL)
ALTER TABLE articles ADD COLUMN search_tokens TEXT;
UPDATE articles SET search_tokens = (
    SELECT GROUP_CONCAT(token)
    FROM (
        SELECT TRIM(REGEXP_SUBSTR(content, '[a-zA-Z]+', 1, REVERSE(LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) + 1)) as token
        FROM articles
    ) AS tokens
    GROUP BY id
);

-- Query using LIKE (inefficient for large datasets)
SELECT * FROM articles
WHERE search_tokens LIKE '%database%'
AND search_tokens LIKE '%fallback%';
```

---

## **4. Implementation Guidelines**
### **4.1 Design Considerations**
1. **Hybrid Schemas**:
   - Store fallback logic in separate tables or views (e.g., `v_legacy_ranking`).
   - Use feature flags to switch between core and fallback:
     ```sql
     SELECT CASE WHEN DATABASE_VERSION >= '11.0' THEN core_logic() ELSE fallback_logic() END;
     ```

2. **Performance Tuning**:
   - **Indexing**: Ensure fallback queries use indexes (e.g., `LIKE` with `LIKE 'prefix%'`).
   - **Batch Processing**: For array/JSON fallbacks, process in chunks to avoid memory overload.
   - **Avoid Cursors**:Cursor-based fallbacks (e.g., recursive queries) can block locks; prefer application-level recursion.

3. **Data Consistency**:
   - Validate fallback output against core logic during upgrades.
   - Use triggers or application checks to enforce constraints (e.g., `UNIQUE` on fallback-generated keys).

4. **Documentation**:
   - Label fallback queries with comments:
     ```sql
     -- [FALLBACK] Window function emulation for MySQL < 8.0
     -- Upgrade path: Replace with ROW_NUMBER() when supported.
     ```

---

### **4.2 Migration Checklist**
1. **Audit Feature Usage**:
   - Query execution plans to identify queries using unsupported features.
   - Example (PostgreSQL):
     ```sql
     SELECT query, query_planner_tree
     FROM pg_stat_statements
     WHERE query LIKE '%ROW_NUMBER%';
     ```

2. **Test Fallbacks**:
   - Compare fallback results against core logic using a small dataset:
     ```sql
     -- Verify fallback matches core logic for 100 records
     WITH core AS (SELECT ... FROM core_implementation LIMIT 100),
          fallback AS (SELECT ... FROM fallback_logic LIMIT 100)
     SELECT * FROM core INTERSECT SELECT * FROM fallback;
     ```

3. **Performance Benchmark**:
   - Measure query time and resource usage (e.g., `EXPLAIN ANALYZE`):
     ```sql
     EXPLAIN ANALYZE SELECT ... FROM fallback_logic;
     ```

4. **Rolling Upgrade**:
   - Gradually switch from fallback to core logic using a percentage-based flag:
     ```sql
     SET SESSION use_fallback = FALSE; -- Toggle at deployment time
     ```

---

## **5. Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                     | **When to Combine**                                                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **[Feature Toggle][1]**               | Dynamically enable/disable features at runtime.                                                                                                                  | Use with **Capability Fallback** to switch between core/fallback logic.                                  |
| **[Schema Migration][2]**             | Gradually update schemas without downtime.                                                                                                                   | Apply alongside fallbacks to maintain compatibility during upgrades.                                    |
| **[Polymorphic Query][3]**           | Handle multiple data formats/versions in a single query.                                                                                                       | Extend fallbacks to support multiple legacy formats.                                                    |
| **[Materialized View][4]**            | Pre-compute expensive queries for faster access.                                                                                                              | Use pre-computed fallback results (e.g., tokenized search terms) to improve performance.              |
| **[Sharding][5]**                     | Split data across multiple database instances.                                                                                                                | Fallback logic can be shard-specific (e.g., regional `LIKE` queries).                                 |
| **[Two-Phase Commit][6]**              | Ensure consistency across distributed transactions.                                                                                                           | Use with fallbacks in multi-database setups (e.g., MySQL fallback on PostgreSQL primary).               |

[1]: [Feature Toggle Pattern](https://martinfowler.com/bliki/FeatureToggle.html)
[2]: [Schema Migration Strategy](https://martinfowler.com/eaaCatalog/schemaMigration.html)
[3]: [Polymorphic Query Pattern](https://wiki.postgresql.org/wiki/Polymorphic_Query)
[4]: [Materialized View](https://www.postgresql.org/docs/current/sql-creatematerializedview.html)
[5]: [Database Sharding](https://www.percona.com/blog/2014/12/19/sharding-in-database-world/)
[6]: [Two-Phase Commit](https://en.wikipedia.org/wiki/Two-phase_commit_protocol)

---

## **6. Anti-Patterns**
- **Hardcoding Fallbacks**: Avoid permanent hacks (e.g., `SELECT 1` instead of a window function). Always document the root cause.
- **Performance Ignored**: Fallback queries must be reviewed for efficiency; ignore at your peril.
- **Over-Fallback**: Don’t replace all features with fallbacks. Use this pattern **only** for critical gaps.
- **Lack of Monitoring**: Fallback queries should be logged and monitored for regressions (e.g., slower than core logic).

---

## **7. Tools and Libraries**
| **Tool**               | **Purpose**                                                                                                                                 | **Example Use Case**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **dbdeploy**           | Schema versioning and fallback management.                                                                                                  | Automate fallback activation during rollbacks.                                                          |
| **Flyway/Sliql**       | Database migrations with fallback logic.                                                                                                   | Conditional migrations based on database version.                                                     |
| **JOOQ**               | SQL generation with fallback support (e.g., conditional joins).                                                                          | Generate fallback queries for unsupported features in Java.                                             |
| **pgBadger**           | Query analysis in PostgreSQL.                                                                                                             | Identify fallback queries causing performance bottlenecks.                                             |
| **Custom ETL Jobs**    | Pre-process data to support fallbacks (e.g., tokenization).                                                                              | Batch-process JSON data into flat tables for legacy queries.                                           |

---

## **8. Example: Full Workflow**
**Scenario**: Upgrade a MySQL 5.7 database to 8.0, but `JSON_EXTRACT` is not yet supported.
**Steps**:
1. **Audit**:
   ```sql
   -- Check for JSON queries
   SELECT query FROM information_schema.routines
   WHERE routine_definition LIKE '%JSON%';
   ```
2. **Implement Fallback**:
   Replace:
   ```sql
   SELECT JSON_EXTRACT(config, '$.theme.color') FROM settings;
   ```
   With:
   ```sql
   SELECT SUBSTRING_INDEX(
       SUBSTRING_INDEX(config, 'theme":{"color":"', -1),
       '",', 1
   ) FROM settings;
   ```
3. **Test**:
   ```sql
   -- Compare results with a sample dataset
   SELECT fallback_logic() = core_logic() FROM (SELECT 1) AS dummy;
   ```
4. **Document**:
   ```sql
   -- Add comment to the table
   ALTER TABLE settings COMMENT = 'FALLBACK: JSON_EXTRACT not supported in 5.7';
   ```
5. **Upgrade**:
   - After upgrading to 8.0, update the query:
     ```sql
     -- Replace with new logic
     ALTER TABLE settings MODIFY COMMENT = 'JSON_EXTRACT supported';
     ```

---

## **9. References**
- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current window-functions.html)
- [MySQL JSON Functions](https://dev.mysql.com/doc/refman/8.0/en/json-functions.html)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [Database Versioning Strategies](https://www.databasesoup.com/2011/11/version-control-for-database-schemas/)
- [Legacy Database Upgrades](https://www.percona.com/blog/2017/01/11/upgrading-from-mysql-5-6-to-mysql-5-7/)