# **Debugging Database Compatibility Testing: A Troubleshooting Guide**

## **Introduction**
Database compatibility testing ensures your application behaves consistently across different database systems (e.g., PostgreSQL, MySQL, SQL Server, Oracle). This guide provides a structured approach to diagnosing and resolving issues when testing multiple database targets.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

### **General Issues**
- [ ] SQL syntax errors persist across databases (e.g., `LIMIT` vs `FETCH FIRST`).
- [ ] Schema migrations fail with database-specific errors.
- [ ] Query performance varies drastically between databases.
- [ ] ORM (e.g., Hibernate, SQLAlchemy) behaves differently across targets.
- [ ] Transactions fail due to isolation level mismatches.
- [ ] Connection pooling issues (different drivers behave differently).
- [ ] Timezone or datetime handling discrepancies.
- [ ] Missing database-specific functions or extensions.

### **Test-Specific Issues**
- [ ] Tests pass in one database but fail in another.
- [ ] Test execution slows down significantly across certain databases.
- [ ] Dependency conflicts (e.g., `pg_query` for PostgreSQL may not work in MySQL).
- [ ] Fixture setup fails due to unsupported data types.

---

## **2. Common Issues and Fixes**
### **Issue 1: SQL Syntax Variations**
**Symptoms:**
- `LIMIT` fails in SQL Server (`OFFSET-FETCH` required).
- `DATEADD` vs `INTERVAL` syntax differences.
- `COALESCE` vs `ISNULL` behavior.

**Solution:**
Use **database-agnostic queries** with conditional logic.

```sql
-- Instead of hardcoding LIMIT, use a parameterized approach
SELECT * FROM users
-- PostgreSQL/MySQL: WHERE created_at > :offset LIMIT :limit
-- SQL Server: WHERE created_at > :offset OFFSET 0 ROWS FETCH NEXT :limit ROWS ONLY
```

**Programmatic Fix (Java Example):**
```java
StringBuilder query = new StringBuilder("SELECT * FROM users WHERE created_at > ?");
if (isPostgres()) {
    query.append(" LIMIT ?");
} else if (isSqlServer()) {
    query.append(" OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY");
}
```

**Alternative:** Use a **SQL templating library** (e.g., JDBC’s `Statement` with dynamic SQL generation).

---

### **Issue 2: Schema Migrations Fail**
**Symptoms:**
- `CREATE TABLE` fails with unsupported data types.
- `ALTER TABLE` syntax differs (e.g., MySQL vs PostgreSQL).

**Solution:**
Validate migrations against **database-specific constraints** before running.

**Example Fix (Liquibase XML):**
```xml
<changeSet id="1" author="dev">
    <createTable tableName="users">
        <column name="id" type="bigserial"> <!-- PostgreSQL -->
            <constraints primaryKey="true" nullable="false"/>
        </column>
        <!-- MySQL alternative: <column name="id" type="int(11)" autoIncrement="true"/> -->
    </createTable>
</changeSet>
```

**Automated Check:** Use **Flyway/DbUp** with database-specific metadata files.

---

### **Issue 3: ORM Inconsistencies**
**Symptoms:**
- `Session.save()` behaves differently (e.g., auto-increment handling).
- `@Query` annotations fail due to dialect mismatches.

**Solution:**
Configure ORM per-database via **Hibernate dialect settings**.

**Java Example (Spring Boot):**
```properties
# application-dev.properties (PostgreSQL)
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

# application-mysql.properties
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQL57Dialect
```

**Alternative:** Use **custom SQL templates** for critical operations.

---

### **Issue 4: Connection Pooling Issues**
**Symptoms:**
- `Too many connections` errors in production.
- Driver-specific timeouts (`org.postgresql.util.PSQLException` in PostgreSQL).

**Solution:**
Adjust pool settings per database.

**Java Example (HikariCP):**
```java
HikariConfig config = new HikariConfig();
if (dbType == DB_TYPE.POSTGRES) {
    config.setMaximumPoolSize(20); // PostgreSQL prefers fewer connections
}
else if (dbType == DB_TYPE.MYSQL) {
    config.setMaximumPoolSize(50); // MySQL scales better
}
```

**Validation:** Test with **JMeter** to simulate load.

---

### **Issue 5: Timezone/Datetime Mismatches**
**Symptoms:**
- `TIMESTAMP` queries return incorrect results.
- `UTC` vs `LOCAL` timezone handling differs.

**Solution:**
Standardize on **UTC** and avoid `CURRENT_TIMESTAMP`.

```sql
-- Force UTC in PostgreSQL
SELECT NOW() AT TIME ZONE 'UTC' AS utc_time;

-- MySQL equivalent (if needed)
SELECT CONVERT_TZ(NOW(), @@session.time_zone, '+00:00') AS utc_time;
```

**Programmatic Fix (Java):**
```java
// Always use Instant or OffsetDateTime
LocalDateTime now = LocalDateTime.now(ZoneOffset.UTC);
```

---

### **Issue 6: Missing Database Functions**
**Symptoms:**
- `pg_is_visible()` fails in MySQL.
- `JSONB` operations don’t work in older MySQL versions.

**Solution:**
Use **feature detection** or fallback logic.

```java
public boolean isPostgres() {
    return "PostgreSQL".equalsIgnoreCase(getDatabaseProductName());
}

public void safeJsonQuery() {
    if (isPostgres()) {
        // Query with JSONB ops
    } else {
        // Fallback to JSON functions
    }
}
```

---

## **3. Debugging Tools & Techniques**
### **A. Database-Specific Logging**
Enable detailed logs for each database type:
- **PostgreSQL:** `log_statement = all` in `postgresql.conf`
- **MySQL:** `general_log = 1` in `my.ini`
- **SQL Server:** `SET STATISTICS TIME, IO ON`

### **B. Query Profiling**
- **PostgreSQL `EXPLAIN ANALYZE`**
- **MySQL `EXPLAIN`**
- **SQL Server `SET SHOWPLAN_TEXT ON`**

### **C. Test Containers**
Spin up databases in **Docker** for isolated testing:
```bash
docker-compose up -d postgres mysql
```

### **D. Schema Validation**
Compare schemas with:
- **`pg_dump` vs `mysqldump`** (for comparison)
- **Liquibase Diff Tool**

---

## **4. Prevention Strategies**
### **A. Database Abstraction Layer**
Use a **wrapper** to mask differences:
```java
public interface DatabaseAdapter {
    long getAutoIncrementId();
    String getLimitClause(int limit, int offset);
}
```

### **B. CI/CD Integration**
- **Test on all supported databases** in CI (GitHub Actions, GitLab CI).
- **Fail early** if syntax issues are detected.

### **C. Documentation & Cheat Sheets**
Maintain a **database compatibility matrix** for:
- Supported SQL features
- Dialect-specific quirks

### **D. Version Control for Migrations**
- Track migrations per database (e.g., `migrations/postgres/`, `migrations/mysql/`).
- Use **branch-per-database** strategy for critical fixes.

### **E. Automated Syntax Checking**
- **Pre-commit hooks** to validate SQL (e.g., `sqlfluff`).
- **Static analysis** for ORM annotations.

---

## **Conclusion**
Database compatibility testing requires **awareness of differences** and **defensive programming**. By systematically addressing SQL syntax, ORM behavior, and connection issues, you can ensure smooth cross-database deployments. Always **test early**, **profile queries**, and **document pitfalls**.

**Final Checklist Before Deployment:**
✅ All SQL tested on target databases.
✅ ORM configurations validated.
✅ Connection pool tuned per database.
✅ Timezone/date handling standardized.
✅ Migration scripts pre-validated.

---
**Next Steps:**
- Review [this database compatibility guide](https://vladmihalcea.com/postgresql-vs-mysql-vs-sql-server-comparison/) for deeper insights.
- Automate cross-database testing with **TestContainers** and **JUnit 5**.