# **[Pattern] Database Execution Strategy – Reference Guide**
*Optimize and abstract database query execution across diverse relational systems.*

---

## **1. Overview**
The **Database Execution Strategy** pattern abstracts the translation of high-level query plans into database-specific SQL while accommodating dialect variations (e.g., PostgreSQL, MySQL, SQL Server) and engine-specific optimizations. It decouples application logic from database intricacies, ensuring portability and performance consistency.

Key benefits:
- **Dialect Agnosticism**: Uniform interfaces for vendor-specific SQL (e.g., `LIMIT` vs. `TOP`).
- **Optimization Reuse**: Shared execution plans (e.g., indexing strategies) without direct SQL exposure.
- **Feature Leveraging**: Adapts to database-specific capabilities (e.g., window functions, JSON support).
- **Maintainability**: Centralized logic for query translation and execution.

This pattern is critical for multi-database systems, microservices, or applications requiring schema migrations across engines.

---

## **2. Schema Reference**
| **Component**               | **Purpose**                                                                                     | **Example Attributes**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **QueryPlan**               | Abstract representation of a query (logical operators, joins, filters).                      | `plan_type: "SELECT"*, `source_tables: ["users", "orders"]`, `filters: [{"column": "age", "operator": ">", "value": 18}]` |
| **DialectAdapter**          | Translates `QueryPlan` to vendor-specific SQL syntax.                                         | `supports: ["postgres", "mysql"]`, `limit_clause: "LIMIT"`, `join_syntax: "INNER JOIN"` |
| **ExecutionContext**        | Runtime state (e.g., connection pools, transaction isolation).                               | `db_url: "postgres://user:pass@host/db"*, `isolation_level: "READ_COMMITTED"`        |
| **OptimizerRules**          | Rules to tune queries (e.g., "prefer indexing on high-cardinality columns").                 | `rule: "index_ordinality"`, `priority: 10`, `conditions: ["column: 'created_at'"]`    |
| **ResultSet**               | Standardized query results (avoids vendor-specific cursors/response formats).                 | `columns: ["id", "name"]`, `data: [[1, "Alice"], [2, "Bob"]]`, `metadata: {"row_count": 2}` |

---

## **3. Query Examples**
### **3.1 Basic SELECT (Cross-Dialect)**
**Input QueryPlan (Abstract):**
```json
{
  "type": "SELECT",
  "source": "users",
  "columns": ["id", "name", "email"],
  "where": {
    "column": "age",
    "operator": ">",
    "value": 25
  },
  "limit": 10
}
```

**Output SQL (PostgreSQL vs. SQL Server):**
- **PostgreSQL**:
  ```sql
  SELECT id, name, email FROM users WHERE age > 25 LIMIT 10;
  ```
- **SQL Server**:
  ```sql
  SELECT TOP 10 id, name, email FROM users WHERE age > 25;
  ```

**Key Logic:**
The `DialectAdapter` replaces `LIMIT` with `TOP` and adjusts dialect-specific syntax (e.g., `;` vs. `GO`).

---

### **3.2 JOIN Optimization**
**Input QueryPlan (With Join Strategy):**
```json
{
  "type": "SELECT",
  "joins": [
    {
      "table": "orders",
      "join_type": "INNER",
      "condition": { "column": "user_id", "operator": "=", "value": "$user_id" }
    }
  ],
  "columns": ["users.name", "orders.amount"]
}
```
**Optimized Output (PostgreSQL):**
```sql
SELECT
  u.name,
  o.amount
FROM
  users u
INNER JOIN orders o ON u.id = o.user_id;
```
**Implementation Notes:**
- The `OptimizerRules` may enforce `ON u.id = o.user_id` over `WHERE u.id = o.user_id` for better plan generation.
- For MySQL, the adapter replaces `INNER JOIN` with `JOIN` if the dialect lacks strict syntax.

---

### **3.3 Parameterized Queries (Security)**
**Input QueryPlan (With Parameters):**
```json
{
  "type": "UPDATE",
  "table": "users",
  "set": { "last_login": "$now" },
  "where": { "column": "id", "operator": "=", "value": "$user_id" }
}
```
**Output SQL (Parameterized):**
```sql
UPDATE users SET last_login = $1 WHERE id = $2;
-- Parameters: [$now_val, $user_id_val]
```
**Key Logic:**
- The adapter escapes values and binds parameters dynamically (e.g., PostgreSQL uses `$1`, MySQL uses `?`).
- Prevents SQL injection by never interpolating raw input.

---

### **3.4 Window Functions (Dialect-Specific)**
**Input QueryPlan (With Window Logic):**
```json
{
  "type": "SELECT",
  "source": "sales",
  "columns": [
    "product_id",
    "amount",
    {
      "column": "rank",
      "type": "window",
      "partition_by": ["product_id"],
      "order_by": ["amount", "desc"]
    }
  ]
}
```
**Output SQL (PostgreSQL vs. SQL Server):**
- **PostgreSQL**:
  ```sql
  SELECT
    product_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY amount DESC) AS rank
  FROM sales;
  ```
- **SQL Server**:
  ```sql
  SELECT
    product_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY amount DESC) AS rank
  FROM sales;
  ```
**Note:** Some dialects (e.g., older MySQL) may lack window functions, requiring fallback to subqueries.

---

### **3.5 Transaction Management**
**Input Context (ExecutionContext):**
```json
{
  "db_url": "postgres://...",
  "isolation_level": "SERIALIZABLE",
  "transaction_mode": "BEGIN/COMMIT" // or "SAVEPOINT"
}
```
**Generated Transaction Blocks:**
```sql
-- PostgreSQL
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- [Query Execution]
COMMIT;
```
**Key Logic:**
- The `ExecutionContext` dictates transaction boundaries and isolation levels.
- Supports distributed transactions via `XA` where applicable.

---

## **4. Implementation Details**
### **4.1 Key Components**
| **Component**       | **Description**                                                                                     | **Example Implementation**                                                                 |
|---------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **QueryPlanParser** | Converts business logic (e.g., ORM-like APIs) into `QueryPlan` objects.                          | `QueryPlan.from_orm_query(orm_query)`                                                           |
| **DialectRegistry** | Registry of `DialectAdapter` implementations (singleton per database type).                     | `registry = { "postgres": PostgresAdapter(), "mysql": MysqlAdapter() }`                       |
| **Optimizer**       | Applies `OptimizerRules` to `QueryPlan` before translation.                                       | `plan = optimizer.apply_rules(plan)`                                                           |
| **Executor**        | Executes translated SQL with connection pooling and retries.                                       | ```javascript
          async execute(plan: QueryPlan, context: ExecutionContext) {
            const adapter = registry.get(context.db_type);
            const sql = adapter.translate(plan);
            const conn = await pool.get();
            const result = await conn.query(sql);
            return adapter.format_results(result);
          }
        ```                                                                                              |

---

### **4.2 Handling Dialect Quirks**
| **Scenario**                | **Pattern Solution**                                                                                     | **Example**                                                                                     |
|-----------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Date Functions**          | Abstract `DATE_FORMAT`, `TO_DATE` into `format_function` in `QueryPlan`.                               | `QueryPlan` includes `function: "date_format", args: ["created_at", "YYYY-MM-DD"]`           |
| **NULL Handling**           | Standardize `IS NULL`/`IS NOT NULL` across dialects.                                                   | Adapter ensures consistent `ISNULL`/`COALESCE` usage.                                             |
| **Case Sensitivity**        | Use `COLLATE` or dialect-specific collation rules in `DialectAdapter`.                                | `SELECT name COLLATE utf8mb4_general_ci FROM users` (MySQL)                                     |
| **JSON Support**            | Map JSON operations (e.g., `->`, `#>>`) to vendor-specific syntax.                                    | `QueryPlan` may include `json_path: "$.metadata.tags"` with adapter-specific `->` or `JSON_EXTRACT`. |

---

### **4.3 Performance Considerations**
- **Plan Caching**: Cache compiled `QueryPlan` → SQL mappings for identical queries.
- **Bulk Execution**: Support `BATCH` operations (e.g., `INSERT ... VALUES (a1), (a2)`).
- **Query Profiler**: Log execution plans for optimization (e.g., `EXPLAIN ANALYZE` in PostgreSQL).

**Example Caching:**
```javascript
const cache = new LRUCache(1000); // Cache 1k plans
const sql = cache.get(plan.id) || registry.translate(plan);
cache.set(plan.id, sql);
```

---

## **5. Query Examples (Code Snippets)**
### **5.1 Python (Using Abstracted ORM)**
```python
from database_execution import QueryPlan, PostgreSQLDialect

# Define a plan
plan = QueryPlan(
    type="SELECT",
    source="products",
    columns=["id", "name"],
    where={"column": "price", "operator": ">", "value": 100}
)

# Execute with dialect adapter
adapter = PostgreSQLDialect()
sql = adapter.translate(plan)
print(sql)  # SELECT id, name FROM products WHERE price > 100
```

### **5.2 JavaScript (Node.js Example)**
```javascript
const { QueryPlan, MySQLDialect } = require("db-execution-strategy");

// Create a join plan
const plan = new QueryPlan({
  type: "SELECT",
  joins: [{
    table: "orders",
    join_type: "INNER",
    condition: { column: "user_id", operator: "=", value: "$user_id" }
  }],
  columns: ["users.name", "orders.amount"]
});

// Execute
const adapter = new MySQLDialect();
const { sql, params } = adapter.translate(plan);
console.log(sql); // "SELECT users.name, orders.amount FROM users INNER JOIN orders ON users.id = orders.user_id WHERE users.id = ?"
```

---

## **6. Error Handling & Edge Cases**
| **Scenario**               | **Solution**                                                                                     | **Example**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Unsupported Dialect**    | Throw `UnsupportedDialectError` with fallback options (e.g., "Use PostgreSQL adapter").        | `if (!registry.has(dialect)) throw new UnsupportedDialectError(dialect);`                      |
| **Syntax Conflicts**       | Log warnings and auto-correct minor issues (e.g., `LIMIT` → `FETCH FIRST`).                   | `adapter.warn("MySQL lacks LIMIT; using FETCH FIRST")`                                          |
| **Operation Timeout**      | Retry with exponential backoff (configurable in `ExecutionContext`).                             | `await retryWithBackoff(() => conn.query(sql), { max_retries: 3 });`                           |
| **Schema Mismatch**        | Validate `QueryPlan` against schema before execution.                                            | `if (!schema.has_column(source, column)) throw new SchemaError(...);`                         |

---

## **7. Related Patterns**
| **Pattern**                | **Relationship**                                                                                     | **When to Use Together**                                                                       |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Repository Pattern**     | `Database Execution Strategy` powers the query layer of repositories.                              | Use when repositories abstract data access but need database-agnostic execution.               |
| **Command Query Responsibility Segregation (CQRS)** | Strategy handles read models (queries) while CQRS separates read/write concerns.            | Ideal for high-scale apps with complex query patterns.                                         |
| **Data Mapper**            | The strategy translates between domain models and database execution.                              | Combine when domain objects map to relational tables but queries are complex.                   |
| **Active Record**          | Less common; strategy can augment Active Record’s simplicity with vendor-specific optimizations. | Use for legacy systems where Active Record is already in use but needs portability.           |
| **Connection Pooling**     | The strategy’s `ExecutionContext` manages pooled connections.                                     | Always pair for optimal performance.                                                            |
| **Query Object Pattern**   | `QueryPlan` objects align with query objects for declarative queries.                             | Use when building query DSLs (e.g., `Users.where(age > 25).limit(10)`).                         |

---

## **8. Anti-Patterns to Avoid**
1. **Hardcoding SQL**:
   Bypassing the strategy to write raw SQL defeats abstraction and reduces portability.
   ❌ `conn.query("SELECT * FROM users WHERE age > 25");` (Bad)
   ✅ `plan = QueryPlan(...); adapter.translate(plan).exec();` (Good)

2. **Ignoring Dialect Quirks**:
   Assumptions about SQL syntax (e.g., `LIMIT` everywhere) cause runtime failures.
   ✅ Validate dialect support before translation.

3. **Over-Optimizing Plans**:
   Prematurely tuning plans for a single database without measuring impact across dialects.
   ✅ Profile and iterate across all supported databases.

4. **Tight Coupling to ORMs**:
   Let the strategy layer sit between ORM and database, allowing ORM swaps without migration.
   ❌ ORM → Database (Direct)
   ✅ ORM → Strategy → Database

---

## **9. Migration Checklist**
| **Step**                   | **Action**                                                                                           | **Tools/Libraries**                                                                             |
|----------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Feature Matrix**         | Document supported features per dialect (e.g., window functions, CTEs).                            | Spreadsheet or tool like [DbSchema](https://www.dbschema.com/).                               |
| **Test Suite**             | Write integration tests for all query types across dialects.                                         | Jest + PostgreSQL/MySQL test containers.                                                      |
| **Fallback Logic**         | Implement graceful degradation (e.g., subqueries for unsupported features).                          | Custom `DialectAdapter` for legacy databases.                                                 |
| **Performance Baseline**   | Benchmark query execution time pre/post strategy implementation.                                     | `pg_stat_statements` (PostgreSQL), `mysql slow query log`.                                      |
| **Monitoring**             | Track translated SQL and execution plans in production.                                             | ELK Stack, Datadog, or custom logging with `ExecutionContext`.                                |

---
**Final Note:** The **Database Execution Strategy** pattern is most valuable in greenfield projects or migrations where database independence is a priority. For simple CRUD apps, a lighter ORM (e.g., SQLAlchemy, TypeORM) may suffice. Always align its complexity with your system’s needs.