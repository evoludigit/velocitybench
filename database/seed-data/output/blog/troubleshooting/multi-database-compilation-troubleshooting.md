# **Debugging "Multi-Database Compilation" Pattern: A Troubleshooting Guide**

## **1. Introduction**
The **Multi-Database Compilation** pattern enables database-agnostic code generation with optional optimizations for specific databases. While this approach ensures portability, inconsistencies can arise due to schema mismatches, query optimizations, or inefficient compilation strategies.

This guide provides a structured approach to diagnosing and resolving common issues in this pattern.

---

## **2. Symptom Checklist**
Check for the following signs when troubleshooting:

| **Symptom**                          | **Possible Causes** |
|--------------------------------------|----------------------|
| Queries work in one DB but fail in another (syntax errors) | Incorrect SQL dialect handling |
| Performance degrades in some databases | Missing optimization for that DB |
| Schema migrations fail due to conflicting schema versions | Schema drift between databases |
| Compilation time is unnecessarily high | Inefficient templating or query generation |
| Runtime errors related to unsupported features | Missing vendor-specific feature flags |

---

## **3. Common Issues & Fixes**

### **Issue 1: Schema Mismatch Across Databases**
**Symptom:** Queries fail due to schema differences (e.g., column namecase sensitivity, missing constraints).

**Root Cause:**
- Database-specific naming conventions (e.g., MySQL vs. PostgreSQL case sensitivity).
- Missing database-specific schema extensions (e.g., JSON support in PostgreSQL vs. MongoDB).

**Solution:**
Ensure schema generation accounts for database differences:
```typescript
// Example: Dynamic schema generation based on DB type
const generateSchema = (dbType: 'postgres' | 'mysql') => {
  if (dbType === 'postgres') {
    return "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL)";
  } else {
    return "CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL)";
  }
};
```

**Debugging Steps:**
1. Log the exact schema definitions being generated for each database.
2. Compare with actual database schema using:
   ```sql
   -- PostgreSQL
   \d users

   -- MySQL
   SHOW CREATE TABLE users;
   ```

---

### **Issue 2: Incorrect SQL Dialect Handling**
**Symptom:** Queries that work in PostgreSQL fail in MySQL (e.g., `now()` vs. `CURRENT_TIMESTAMP`).

**Root Cause:**
- No database-specific SQL templating.
- Hardcoded functions instead of dynamic replacements.

**Solution:**
Use a dialect-aware query builder:
```typescript
const query = (dbType: string) => {
  const dateFn = dbType === 'mysql' ? 'CURRENT_TIMESTAMP' : 'now()';
  return `SELECT * FROM users WHERE created_at > ${dateFn}`;
};
```

**Debugging Steps:**
1. Print generated SQL before execution (e.g., using a logging middleware).
2. Test with known working queries for each database.

---

### **Issue 3: Performance Degradation in Some Databases**
**Symptom:** Queries are slow in one database but fast in another.

**Root Cause:**
- Missing database-specific optimizations (e.g., index hints in PostgreSQL).
- Overly generic query plans (e.g., always using `LIKE '%pattern%'`).

**Solution:**
Apply database-specific optimizations:
```typescript
const optimizeQuery = (dbType: string) => {
  if (dbType === 'postgres') {
    return "SELECT * FROM users WHERE name ILIKE '%pattern%'"; // Case-insensitive search
  } else if (dbType === 'mysql') {
    return "SELECT * FROM users WHERE name LIKE '%pattern%'"; // Case-sensitive
  }
};
```

**Debugging Steps:**
1. Use `EXPLAIN ANALYZE` to check query execution plans:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE name LIKE '%test%';
   ```
2. Compare execution times across databases.

---

### **Issue 4: Inefficient Compilation**
**Symptom:** Compilation takes too long, especially with complex templates.

**Root Cause:**
- Unoptimized template rendering (e.g., large SQL files).
- Repeated parsing of the same templates.

**Solution:**
- Cache compiled templates per database:
  ```typescript
  const dbTemplateCache = new Map<string, string>();

  const compileTemplate = (dbType: string, template: string) => {
    if (!dbTemplateCache.has(dbType)) {
      const compiled = compileWithDialect(dbType, template);
      dbTemplateCache.set(dbType, compiled);
    }
    return dbTemplateCache.get(dbType);
  };
  ```
- Use a library like `sql-template-string` for efficient templating.

**Debugging Steps:**
1. Profile compilation time using a benchmarking tool.
2. Check for repeated template parsing in logs.

---

## **4. Debugging Tools & Techniques**

### **A. Logging & Profiling**
- **SQL Logging:** Log generated SQL queries before execution.
  ```typescript
  const queryLogger = (sql: string) => console.log(`[SQL] ${sql}`);
  queryLogger(optimizeQuery('mysql'));
  ```
- **Performance Profiling:** Use tools like `console.time()` or integrated profilers (e.g., PostgreSQL’s `pg_stat_statements`).

### **B. Database-Specific Inspection**
- **Schema Comparison:**
  ```bash
  schematool compare --db1=postgres://user:pass@localhost/db1 --db2=mysql://user:pass@localhost/db2
  ```
- **Query Profiling:**
  ```sql
  -- PostgreSQL
  SET log_min_duration_statement = 100;  -- Log queries > 100ms
  ```

### **C. Unit Testing for Multi-DB Compatibility**
- Use a test suite like `jest` with mock databases:
  ```typescript
  test('SELECT should work in PostgreSQL', () => {
    const sql = generateQuery('postgres');
    expect(sql).toContain('now()');
  });
  ```

---

## **5. Prevention Strategies**

### **A. Enforce Database-Aware Code**
- Use feature flags for database-specific syntax:
  ```typescript
  const isPostgres = process.env.DB_TYPE === 'postgres';
  const dateFn = isPostgres ? 'now()' : 'CURRENT_TIMESTAMP';
  ```
- Restrict unsupported features (e.g., window functions in MySQL 5.7).

### **B. Automated Schema Validation**
- Run schema consistency checks before deployment:
  ```bash
  # Example using Flyway/liquibase
  flyway validate --url=jdbc:postgresql://... --user=...
  ```

### **C. Optimize Compilation**
- Precompile templates for each database type.
- Use a build-time compiler (e.g., `sqlx` for Rust, `knex` for JS).

### **D. Monitoring & Alerts**
- Set up alerts for failed queries per database:
  ```sql
  -- PostgreSQL: Track failed queries
  CREATE TABLE query_errors (id SERIAL, query_text TEXT, error_msg TEXT);
  ```

---

## **6. Conclusion**
Debugging **Multi-Database Compilation** requires:
1. **Isolating schema and dialect mismatches** (check logs, `EXPLAIN`).
2. **Optimizing database-specific queries** (caching, indexing).
3. **Preventing future issues** (unit tests, schema validation).

By following this guide, you can systematically resolve inconsistencies and improve compilation efficiency across databases.