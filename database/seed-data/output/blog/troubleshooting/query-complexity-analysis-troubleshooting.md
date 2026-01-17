---
# **Debugging Query Complexity Analysis: A Troubleshooting Guide**

## **1. Introduction**
The **Query Complexity Analysis** pattern helps identify and mitigate performance bottlenecks by analyzing the complexity of SQL `WHERE` clauses (e.g., nested conditions, subqueries, and inefficient joins). If this analysis fails or produces inaccurate results, queries may still execute poorly, leading to degraded application performance.

This guide provides a structured approach to diagnosing and resolving issues with Query Complexity Analysis, including common pitfalls, debugging techniques, and prevention strategies.

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

✅ **Analysis fails silently** – The system doesn’t flag complex queries despite known inefficiencies.
✅ **False positives/negatives** – Some truly complex queries are ignored, while others are flagged incorrectly.
✅ **Performance degradation** – Queries that should be optimized are not detected by the analyzer.
✅ **Dependency issues** – The analyzer relies on external tools (e.g., `pg_stat_statements`, query parsers) that may not be properly configured.
✅ **Dynamic SQL issues** – The analyzer struggles with dynamically generated queries (e.g., ORM-generated SQL).
✅ **Large query parsing delays** – Complex queries take too long to analyze, causing latency spikes.

If multiple symptoms apply, proceed with debugging.

---

## **3. Common Issues & Fixes**

### **3.1 Issue: The Analyzer Skips Dynamic SQL**
**Symptom:**
- ORM-generated queries (e.g., Hibernate, Django ORM) are not analyzed, even though they contain complex conditions.
- Raw SQL with dynamic parameters is ignored.

**Root Cause:**
- The analyzer relies on static SQL parsing, but dynamic SQL is constructed at runtime.
- Some ORMs inject query complexity (e.g., nested `IN` clauses, `JOIN` explosion) that the analyzer cannot detect.

**Fix:**
- **For ORMs:**
  Modify the ORM to log raw SQL queries before execution and feed them into the analyzer:
  ```java
  // Hibernate (Java) Example: Log SQL before execution
  @Override
  public Query appendWhereCondition(Query query, String condition) {
      String rawSql = query.getQueryString(); // Log or analyze raw SQL
      complexityAnalyzer.analyze(rawSql);     // Pass to analyzer
      return query;
  }
  ```

- **For Dynamic SQL:**
  Use a **query interceptor** (PostgreSQL) or application-level profiler to capture and analyze raw SQL:
  ```sql
  -- PostgreSQL: Enable query logging
  SET log_statement = 'all';  -- Logs raw SQL
  ```

---

### **3.2 Issue: False Positives (Incorrectly Flagged Queries)**
**Symptom:**
- Simple queries (e.g., `WHERE id = 5`) are flagged as complex.
- The analyzer misidentifies legitimate conditions as inefficient.

**Root Cause:**
- The analyzer lacks precision in distinguishing between **complex logic** and **simple filtering**.
- Thresholds for "complexity" are set too low.

**Fix:**
- **Adjust complexity thresholds** (e.g., only flag queries with `NESTED LOOPS` or `SEQ SCAN` patterns).
  ```python
  # Example: Python-based analyzer (pseudo-code)
  def is_query_complex(sql):
      has_nested_where = 'WHERE (' in sql and sql.count('WHERE') > 1
      has_subquery = 'SELECT ... IN (' in sql
      return has_nested_where or has_subquery
  ```
- **Whitelist simple queries** that meet business logic requirements:
  ```sql
  -- Example: Allow simple ID-based queries
  IF query LIKE '%WHERE id = %' AND NOT query LIKE '%OR%' THEN
      EXCLUDE_FROM_ANALYSIS;
  ```

---

### **3.3 Issue: Analysis Too Slow for Production Traffic**
**Symptom:**
- The analyzer introduces latency by processing every query, slowing down response times.
- Large batch queries (e.g., `SELECT * FROM huge_table`) take too long to analyze.

**Root Cause:**
- The analyzer runs synchronously and lacks optimizations for high-load environments.
- String parsing of SQL is inefficient for large datasets.

**Fix:**
- **Implement asynchronous analysis** (e.g., queue queries for later review):
  ```java
  // Spring Boot Example: Async Query Analysis
  @Async
  public void analyzeQueryAsync(String query) {
      if (query.contains("complex_pattern")) {
          queryComplexityRepository.save(query); // Log for later review
      }
  }
  ```
- **Sample queries only** (skip analysis for known simple patterns):
  ```sql
  -- Example: Skip analysis for common CRUD queries
  IF query IN ('SELECT * FROM users WHERE id = ?', 'DELETE FROM logs') THEN
      SKIP_ANALYSIS;
  ```

---

### **3.4 Issue: Subquery and Join Complexity Not Detected**
**Symptom:**
- Queries with `JOIN`, `EXISTS`, or correlated subqueries are not flagged.
- The analyzer fails to recognize `IN` clauses with large subqueries.

**Root Cause:**
- The analyzer uses basic regex or shallow parsing instead of a full SQL parser.
- Correlated subqueries (e.g., `WHERE EXISTS (SELECT ... FROM ... WHERE ...)`) are hard to detect.

**Fix:**
- **Use a proper SQL parser** (e.g., [ANTLR](https://www.antlr.org/), [SQLParser](https://github.com/antlr/sqlparser)):
  ```java
  // ANTLR Example: SQL Parsing
  SQLParser parser = new SQLParser(new CharStream(sql));
  ParseTree tree = parser.sqlStatement();
  if (tree.hasComplexJoins()) {
      flagAsComplex();
  }
  ```
- **Manual pattern matching for subqueries**:
  ```python
  def detect_subqueries(query):
      if "SELECT ... FROM" in query and "WHERE" in query:
          return True  # Simple heuristic for subqueries
  ```

---

### **3.5 Issue: Database-Specific Query Patterns Not Handled**
**Symptom:**
- The analyzer works for PostgreSQL but fails on MySQL/MongoDB.
- Database-specific optimizations (e.g., MongoDB `$lookup`) are not recognized.

**Root Cause:**
- No database-agnostic or database-specific SQL parsing logic.
- Some databases (e.g., MongoDB) use JSON-like queries instead of SQL.

**Fix:**
- **Create database-specific analyzers**:
  ```java
  // Example: MySQL vs. PostgreSQL handling
  if (isPostgres) {
      detectComplexWhereConditions();
  } else if (isMySQL) {
      detectJoinExplosion();
  }
  ```
- **For NoSQL:**
  Use a schema-aware analyzer (e.g., check for `$lookup` in MongoDB):
  ```javascript
  // MongoDB Example: Detect complex aggregations
  if (query.aggPipeline.some(p => p.$lookup)) {
      logComplexAggregation(query);
  }
  ```

---

## **4. Debugging Tools & Techniques**

### **4.1 Logging & Instrumentation**
- **Log raw SQL queries** before analysis:
  ```java
  log.debug("Analyzing query: {}", sql);
  ```
- **Track analysis duration** to identify slow queries:
  ```python
  start_time = time.time()
  analyze_query(query)
  duration = time.time() - start_time
  if duration > 1000:  # 1 second threshold
      warn("Slow analysis detected!")
  ```

### **4.2 Query Profiling Tools**
| Tool | Purpose | Example Command |
|------|---------|-----------------|
| **PostgreSQL `pg_stat_statements`** | Tracks slow queries | `CREATE EXTENSION pg_stat_statements;` |
| **MySQL Slow Query Log** | Logs slow queries | `slow_query_log = 1` in `my.cnf` |
| **MongoDB `explain()`** | Analyzes query execution | `db.collection.find().explain("executionStats")` |
| **OR Tools (e.g., DBeaver, DataGrip)** | Visualizes query plans | Right-click → "Query Plan" |

### **4.3 SQL Parsing & Validation**
- Use **SQLLint** or **SQLParser** to validate query structures:
  ```bash
  sql-lint --format=ansi my_query.sql
  ```
- **Test with known complex queries**:
  ```sql
  -- Test case: Nested OR conditions
  SELECT * FROM users WHERE (age > 30 AND (status = 'active' OR status = 'pending'));
  ```

### **4.4 Unit Testing the Analyzer**
- Write unit tests to verify edge cases:
  ```java
  @Test
  public void testNestedWhereConditions() {
      String query = "SELECT * FROM users WHERE (name = 'Alice' OR (age > 20 AND status = 'active'))";
      assertTrue(queryComplexityAnalyzer.isComplex(query));
  }
  ```

---

## **5. Prevention Strategies**

### **5.1 Early Adoption of Analysis**
- **Integrate analysis into CI/CD** to catch complex queries early:
  ```yaml
  # GitHub Actions Example
  - name: Run Query Complexity Check
    run: ./query-complexity-analyzer.sh ./migrations/*.sql
  ```

### **5.2 Educate Developers**
- **Document query patterns** that lead to complexity:
  ```markdown
  # ❌ Avoid:
  SELECT * FROM users WHERE (status = 'active' AND (
      (created_at > '2023-01-01' OR created_at < '2023-01-31')
  ));

  # ✅ Use Instead:
  SELECT * FROM users WHERE status = 'active'
  AND (created_at BETWEEN '2023-01-01' AND '2023-01-31');
  ```

### **5.3 Automated Refactoring Suggestions**
- **Use linters** to suggest optimizations:
  ```python
  # Example: Suggest query rewrite
  if query_contains_nested_or:
      print("⚠ Consider using IN() instead of nested OR conditions.")
  ```

### **5.4 Database-Level Optimizations**
- **Use query hints** for known complex queries:
  ```sql
  -- PostgreSQL: Force index usage
  SELECT /*+ IndexScan(users_pkey) */ * FROM users WHERE id = 5;
  ```
- **Partition large tables** to reduce scan complexity:
  ```sql
  CREATE TABLE users (
      id SERIAL,
      -- other columns
  ) PARTITION BY RANGE (created_at);
  ```

### **5.5 Benchmarking & Monitoring**
- **Set up alerts** for queries exceeding complexity thresholds:
  ```bash
  # Prometheus Alert Rule Example
  ALERT HighQueryComplexity
    IF query_complexity_score > 0.9
    FOR 5m
    LABELS {severity="critical"}
  ```

---

## **6. Conclusion**
Query Complexity Analysis is critical for maintaining database performance, but it can fail due to dynamic SQL, false positives, or inefficient parsing. By following this guide, you can:

✔ **Debug** analyzer issues (dynamic SQL, false positives, slow processing).
✔ **Use tools** like `pg_stat_statements` and SQL parsers for deeper insights.
✔ **Prevent** complexity issues via CI/CD, developer education, and automated refactoring.

**Final Checklist Before Deployment:**
- [ ] Test with dynamic SQL (ORM-generated queries).
- [ ] Verify thresholds for "complexity" are realistic.
- [ ] Benchmark analysis performance under load.
- [ ] Document known false positives/negatives.

By proactively addressing these challenges, you ensure that Query Complexity Analysis delivers real-world value instead of becoming a bottleneck itself.