# **Debugging Pre-Compiled Query Plans: A Troubleshooting Guide**

## **Introduction**
The **Pre-Compiled Query Plans** pattern seeks to optimize database performance by caching query execution plans at schema compile-time (or warm-up phase) to avoid runtime recompilation. This is common in high-throughput systems where repeated queries benefit from plan reuse.

While this pattern improves performance, it can introduce unexpected behavior if misconfigured or deployed on dynamic schemas. This guide helps diagnose and resolve common issues quickly.

---

## **1. Symptom Checklist**
Before diving into fixes, validate the following symptoms:

✅ **First query is significantly slower than subsequent ones** (indicating plan recompilation on cold starts).
✅ **Query performance varies across identical requests** (plan cache misses or invalidations).
✅ **High runtime planning overhead** (visible in query execution logs).
✅ **Unexpected query timeouts or cost estimation differences** (due to stale plans).
✅ **Schema changes cause cascading performance issues** (plans become invalid).

If multiple symptoms appear, the issue likely involves **plan cache misconfiguration, schema drift, or improper invalidation logic**.

---

## **2. Common Issues & Fixes**

### **Issue 1: Missing Query Plan Cache (Cold Start Latency)**
**Symptom:**
- First query execution is 5-10x slower than subsequent runs.
- Plan recompilation is evident in logs (e.g., `Plan Cache Miss`).

**Root Cause:**
- The database is configured to **never cache query plans** (e.g., `max_plan_cache_entries = 0` in PostgreSQL).
- Application-level caching is missing or improperly implemented.

**Fix (PostgreSQL Example):**
```sql
-- Verify current settings
SHOW max_plan_cache_entries;

-- Adjust configuration (if needed)
ALTER SYSTEM SET max_plan_cache_entries = 1000;  -- Default is 1000; adjust based on workload
```
**For Application-Level Caching:**
```java
// Example: Java + Hibernate (if using JPA)
@NamedNativeQuery(
    name = "findExpensiveQuery",
    query = "SELECT * FROM users WHERE status = :status",
    hint = @QueryHint(name = "org.hibernate.hql.bulk.non.query", value = "true")
)
public List<User> findExpensiveQuery(boolean status);
```
**Prevention:** Ensure your ORM (e.g., Hibernate, JDBC `Statement` reuse) or direct SQL clients cache plans.

---

### **Issue 2: Plan Cache Invalidation Due to Schema Changes**
**Symptom:**
- After a `ALTER TABLE` or `CREATE INDEX`, queries regress in performance.
- Logs show **replanning** even for unchanged queries.

**Root Cause:**
- The **plan cache** is not invalidated on schema changes.
- Example: A new index is added, but the database fails to update the plan.

**Fix (PostgreSQL):**
```sql
-- Force plan cache to rebuild (not recommended for production)
RESET ALL;

-- Better: Use `pg_plan_cache_reset()` (if available) or application-level cache invalidation
SELECT pg_plan_cache_reset();  -- Resets query plan cache
```
**Java/Kotlin Fix (Hibernate):**
```kotlin
// Invalidate Hibernate’s second-level cache
sessionFactory.cache().evictAllRegionContents()
```
**Prevention:**
- Use **database-level plan cache invalidation triggers** (e.g., PostgreSQL `pg_class` triggers).
- Implement **application-level cache invalidation** on schema changes.

---

### **Issue 3: Dynamic SQL Preventing Plan Reuse**
**Symptom:**
- Queries with dynamic parameters (`IN` clauses, `WHERE` conditions) repeatedly recompile.
- Logs show `Plan Cache Miss` for identical queries.

**Root Cause:**
- The query **signature includes runtime variables**, making it non-deterministic.
- Example:
  ```sql
  -- Bad: Parameters make the plan unstable
  SELECT * FROM orders WHERE user_id = ? AND status = ?
  ```

**Fix:**
1. **Use Prepared Statements with Placeholders:**
   ```java
   // Java JDBC example
   PreparedStatement stmt = connection.prepareStatement(
       "SELECT * FROM orders WHERE user_id = ? AND status = ?"
   );
   stmt.setInt(1, userId);
   stmt.setString(2, status);
   ResultSet rs = stmt.executeQuery();  // Same plan reused
   ```
2. **For SQL-based ORMs (Hibernate), use `@NamedQuery` with fixed parameters.**

**Prevention:**
- **Standardize query templates** and avoid dynamic SQL where possible.

---

### **Issue 4: Plan Cache Too Small (Memory Pressure)**
**Symptom:**
- Frequent plan cache evictions (`Plan Cache Evict` in logs).
- Performance degrades over time as new plans replace old ones.

**Root Cause:**
- `max_plan_cache_entries` is set too low.
- High query diversity exhausts the cache.

**Fix (PostgreSQL):**
```sql
SHOW max_plan_cache_entries;
ALTER SYSTEM SET max_plan_cache_entries = 10000;  -- Tune based on workload
```
**Monitoring:**
```sql
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;  -- Find expensive queries
```

**Prevention:**
- **Profile query execution** (`pg_stat_statements`) to identify hot queries.
- **Increase cache size** if hot queries are frequently evicted.

---

### **Issue 5: ORM-Specific Plan Cache Issues (Hibernate, JPA)**
**Symptom:**
- Hibernate/JPA queries are slower after application restarts.
- Logs show `HHH000346: Plan Cache miss` (Hibernate 6+).

**Root Cause:**
- Hibernate’s **second-level query cache** is misconfigured.
- **Native SQL plans are not cached** due to incorrect hints.

**Fix (Hibernate):**
```xml
<!-- Enable query plan caching in hibernate.properties -->
hibernate.cache.query.cache_region = org.hibernate.cache.internal.NoCache
hibernate.cache.use_second_level_cache = true
hibernate.generate_statistics = true
```
**Java Configuration:**
```java
// Force plan reuse via annotation
@Entity
@DynamicUpdate
@Table(name = "users")
public class User {
    @QueryHints({@QueryHint(name = "org.hibernate.hql.bulk.non.query", value = "true")})
    public List<User> findByStatus(String status) {
        return em.createQuery("FROM User u WHERE u.status = :status", User.class)
                .setParameter("status", status)
                .getResultList();
    }
}
```
**Prevention:**
- **Enable Hibernate statistics** to track cache hits/misses.
- **Use `@NamedNativeQuery` for repeated queries.**

---

## **3. Debugging Tools & Techniques**
### **A. Database-Specific Tools**
| Database      | Tool/Command | Usage |
|--------------|-------------|-------|
| **PostgreSQL** | `pg_stat_statements` | `SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC;` |
| **PostgreSQL** | `pg_plan_cache` | `SELECT * FROM pg_plan_cache;` |
| **MySQL**     | `SHOW PROFILE` | `SET SESSION profiling = 1;` |
| **Oracle**    | `v$sql_plan` | `SELECT * FROM v$sql_plan WHERE sql_id = '...';` |
| **SQL Server**| `sp_configure` | `EXEC sp_configure 'show advanced options', 1;` |

### **B. Application-Level Debugging**
- **Enable SQL Logging:**
  - **Java (Spring Boot):** `spring.jpa.show-sql=true`
  - **Python (SQLAlchemy):** `engine.echo = True`
- **Use AOP for Query Timing:**
  ```java
  @Around("execution(* com.example.repository.*.*(..))")
  public Object logQueryTime(ProceedingJoinPoint pjp) throws Throwable {
      long start = System.currentTimeMillis();
      Object result = pjp.proceed();
      long duration = System.currentTimeMillis() - start;
      System.out.println(pjp.getSignature() + " took " + duration + "ms");
      return result;
  }
  ```
- **Query Profiling Tools:**
  - **P6Spy** (Java)
  - **SQLProfiling** (Python)
  - **Slow Query Logs** (MySQL, PostgreSQL)

### **C. Plan Inspection**
- **PostgreSQL:**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE id = 1;
  ```
- **MySQL:**
  ```sql
  EXPLAIN FORMAT=JSON SELECT * FROM users WHERE id = 1;
  ```

---

## **4. Prevention Strategies**
### **A. Database Configuration**
- Set **optimal plan cache size** (`max_plan_cache_entries`).
- Enable **query logging** (`log_min_duration_statement` in PostgreSQL).
- Use **partitioned plans** for large tables.

### **B. Application-Level Best Practices**
| Practice | Implementation |
|----------|----------------|
| **Reuse Prepared Statements** | Use `PreparedStatement` in JDBC, `@NamedQuery` in JPA. |
| **Schema Change Handling** | Invalidate caches on `ALTER TABLE`/`CREATE INDEX`. |
| **Dynamic SQL Minimization** | Avoid `WHERE` conditions with runtime variables. |
| **Connection Pooling** | Use `HikariCP`, `Tomcat JDBC Pool` to reuse connections. |
| **Query Batch Processing** | Use `JdbcTemplate.batchUpdate()` for bulk operations. |

### **C. Monitoring & Alerting**
- **Set up alerts** for:
  - High plan cache miss ratios.
  - Sudden query timeouts.
  - Schema change spikes.
- **Use APM tools** (New Relic, Datadog) to track query performance.

---

## **5. Final Checklist for Resolution**
| Step | Action |
|------|--------|
| 1 | Check `SHOW max_plan_cache_entries;` (PostgreSQL) or equivalent. |
| 2 | Verify if queries use `PreparedStatement` or `@NamedQuery`. |
| 3 | Inspect logs for `Plan Cache Miss` or `Replanning`. |
| 4 | Profile slow queries (`EXPLAIN ANALYZE`). |
| 5 | Invalidate cache if schema changed (`RESET ALL` or app-level cache reset). |
| 6 | Adjust `max_plan_cache_entries` if cache pressure is high. |
| 7 | Enable ORM statistics (Hibernate) to debug cache hits/misses. |

---

## **Conclusion**
The **Pre-Compiled Query Plans** pattern is powerful but requires careful tuning. Most issues stem from:
❌ **Missing plan caching** (first-query penalty).
❌ **Schema drift invalidating plans**.
❌ **Dynamic SQL breaking plan reuse**.

By following this guide, you should be able to:
✅ **Identify** performance bottlenecks.
✅ **Fix** caching misconfigurations.
✅ **Prevent** future regressions.

**Final Tip:** Always **benchmark before/after changes**—performance tuning is iterative. 🚀