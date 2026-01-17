# **Debugging Multi-Database Testing: A Troubleshooting Guide**

## **1. Introduction**
The **Multi-Database Testing** pattern ensures your application interacts correctly with multiple database backends (e.g., PostgreSQL, MySQL, MongoDB, Firebase). This guide will help you diagnose and resolve common issues when testing across different databases.

---

## **2. Symptom Checklist**
Before diving into debugging, verify if your issue aligns with these symptoms:

| Symptom | Description |
|---------|-------------|
| **Connection Failures** | Tests fail with connection timeouts or authentication errors. |
| **Schema Mismatch Errors** | Different databases interpret SQL syntax differently. |
| **Transaction Isolation Issues** | Transactions behave unexpectedly in embedded vs. standalone databases. |
| **Query Performance Differences** | Some queries run fast in one DB but slow in another. |
| **Schema Migration Failures** | Migration scripts fail due to vendor-specific syntax. |
| **Test Flakiness** | Random failures appear when switching between databases. |
| **Schema Validation Errors** | ORM (e.g., Hibernate, Prisma) rejects schema definitions. |
| **Data Consistency Issues** | Read/write operations produce unexpected results. |

---

## **3. Common Issues and Fixes**

### **3.1 Connection Failures**
**Symptom:** Tests fail with `Connection refused`, `Authentication failed`, or `Network timeout`.
**Root Causes:**
- Incorrect credentials or URLs.
- Missing JDBC/ODBC drivers.
- Firewall/network blocking access.

#### **Fixes:**
**Java (JDBC) Example:**
```java
// Correct connection setup (PostgreSQL example)
String jdbcUrl = "jdbc:postgresql://localhost:5432/testdb?sslmode=require";
Connection conn = DriverManager.getConnection(jdbcUrl, "user", "password");
```
**Dockerized MySQL (Testcontainers):**
```java
MySqlContainer<?> mysql = new MySqlContainer<>("mysql:8.0");
mysql.start();

// Use JDBC URL from container
String jdbcUrl = mysql.getJdbcUrl() + "&useSSL=false";
```

**Debugging Steps:**
- Verify credentials in `application-test.properties`.
- Check if the database is running (`docker ps`, `pg_isready -U postgres`).
- Use `telnet` or `nc -zv localhost 5432` to test connectivity.

---

### **3.2 Schema Mismatch Errors**
**Symptom:** SQL queries fail due to vendor-specific syntax (e.g., `LIMIT` vs. `FETCH`).
**Root Causes:**
- ORM mapping conflicts.
- Raw SQL queries using non-portable syntax.

#### **Fixes:**
**ORM-Specific Solutions:**
- **Hibernate:** Use `hibernate.dialect` to specify the DB dialect.
  ```properties
  spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
  ```
- **Prisma:** Define schema per database:
  ```prisma
  datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")
  }
  ```

**Portable SQL Alternative:**
```sql
-- Replace LIMIT in MySQL with FETCH in PostgreSQL
SELECT * FROM users
WHERE id < (SELECT MAX(id) FROM users) LIMIT 10;  -- MySQL
SELECT * FROM users
ORDER BY id DESC
FETCH FIRST 10 ROWS ONLY;  -- PostgreSQL
```

**Debugging Steps:**
- Check ORM logs for unsupported SQL.
- Use `EXPLAIN ANALYZE` to inspect query execution.

---

### **3.3 Transaction Isolation Issues**
**Symptom:** Dirty reads or phantom reads occur inconsistently.
**Root Causes:**
- DBMS-specific isolation levels.
- Test isolation not set correctly.

#### **Fixes:**
**Test Configuration (Spring Boot):**
```java
@SpringBootTest
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_EACH_TEST_METHOD)
public class MultiDBTest {
    @Autowired
    private DataSource dataSource;

    @BeforeEach
    void setUp() {
        // Force READ_COMMITTED isolation (works across DBs)
        Connection conn = dataSource.getConnection();
        conn.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);
    }
}
```

**Debugging Steps:**
- Check `SET TRANSACTION ISOLATION LEVEL` in logs.
- Use `READ_COMMITTED` (default in most DBs) for consistency.

---

### **3.4 Query Performance Differences**
**Symptom:** A query is fast in PostgreSQL but slow in MongoDB.
**Root Causes:**
- Indexing strategies differ.
- Join semantics vary (NoSQL vs. SQL).

#### **Fixes:**
- **SQL Databases:** Add proper indexes:
  ```sql
  CREATE INDEX idx_user_name ON users (name);
  ```
- **MongoDB:** Use `.explain()` to analyze query plans:
  ```javascript
  db.users.find({ name: "John" }).explain("executionStats");
  ```

**Debugging Steps:**
- Compare execution plans (`EXPLAIN` in SQL, `.explain()` in MongoDB).
- Profile queries with tools like **PostgreSQL pgBadger** or **MongoDB Atlas Query Profiler**.

---

### **3.5 Schema Migration Failures**
**Symptom:** Migrations fail with syntax errors (e.g., `ALTER TABLE` in SQL vs. schema.json in NoSQL).
**Root Causes:**
- Hardcoded SQL in migrations.
- Tool-specific migration files (Flyway vs. Liquibase).

#### **Fixes:**
**Flyway Approach (Vendor-Agnostic):**
```properties
# flyway.conf
defaults:
  locations:
    - classpath:/db/migration
    - filesystem:/custom/migrations
```
**Liquibase XML Example:**
```xml
<changeSet id="add-column" author="me">
    <addColumn tableName="users">
        <column name="email" type="varchar(255)">
            <constraints nullable="true"/>
        </column>
    </addColumn>
</changeSet>
```

**Debugging Steps:**
- Check migration logs for SQL parsing errors.
- Test migrations in each DB separately.

---

### **3.6 Test Flakiness**
**Symptom:** Random test failures when switching databases.
**Root Causes:**
- Race conditions in concurrent transactions.
- Non-deterministic seeding.

#### **Fixes:**
**Deterministic Test Setup (Testcontainers):**
```java
// Use fixed seeds in Docker images
MySqlContainer<?> mysql = new MySqlContainer<>("mysql:8.0")
    .withDatabaseName("testdb")
    .withUsername("user")
    .withPassword("pass")
    .withInitScript("set.sql");  // Pre-populate with known data
```

**Spring Test Isolation:**
```java
@SpringBootTest
@ActiveProfiles("test")
@TransactionConfiguration(defaultTimeout = 10, transactionManagerRef = "transactionManager")
public class FlakyTest {
    @Autowired
    private EntityManager entityManager;

    @BeforeEach
    void resetState() {
        entityManager.createNativeQuery("TRUNCATE users RESTART IDENTITY CASCADE")
                   .executeUpdate();
    }
}
```

**Debugging Steps:**
- Run tests in isolation (`mvn test -Dtest=SingleTestClass`).
- Enable debug logging for transactions.

---

## **4. Debugging Tools & Techniques**
| Tool/Technique | Purpose |
|----------------|---------|
| **Testcontainers** | Spin up real DBs in Docker for isolated testing. |
| **SQLErrorSimulator** | Inject SQL errors to test error handling. |
| **Database Logging** | Enable `log4j2.xml` for JDBC logs. |
| **Schema Comparators** | Check schema drift (e.g., **SchemaCrawler**). |
| **Query Profilers** | Monitor slow queries (e.g., **pgBadger**, **MongoDB Dev Tools**). |
| **Mocking Frameworks** | Use **Mockito** for DB interactions in unit tests. |

**Example: JDBC Logging (log4j2.xml)**
```xml
<Configuration>
    <Appenders>
        <Console name="Console" target="SYSTEM_OUT">
            <PatternLayout pattern="%d{HH:mm:ss.SSS} [%t] %-5level %logger{36} - %msg%n" />
        </Console>
    </Appenders>
    <Loggers>
        <Logger name="org.hibernate.SQL" level="debug" />
        <Logger name="org.hibernate.type.descriptor.sql.BasicBinder" level="trace" />
    </Loggers>
</Configuration>
```

---

## **5. Prevention Strategies**
1. **Standardize Database Configs**
   - Use environment variables for DB URLs/credentials.
   - Example:
     ```properties
     spring.datasource.url=${DB_URL:jdbc:postgresql://localhost:5432/mydb}
     ```

2. **Adopt ORM with Cross-DB Support**
   - **Hibernate** (with proper dialects).
   - **JOOQ** (type-safe SQL for multiple DBs).

3. **Schema Validation in CI**
   - Use **SchemaCrawler** to detect schema drift.
   - Fail builds if schemas diverge.

4. **Test in Production-Like Environments**
   - Use **Testcontainers** for Dockerized DBs in CI.

5. **Isolate Tests by Database**
   - Run SQL DB tests separately from NoSQL tests.

6. **Document Known Issues**
   - Maintain a **DB Compatibility Matrix** (e.g., PostgreSQL vs. MySQL quirks).

---

## **6. Conclusion**
Multi-database testing requires careful handling of connections, schema differences, and transaction behaviors. By following this guide, you can:
✅ Debug connection issues with Testcontainers.
✅ Avoid flaky tests with deterministic setups.
✅ Optimize queries with profiling tools.
✅ Prevent regressions with schema validation.

**Final Tip:** Start with **one database at a time**, then gradually expand to multi-database setups. Use **rolled-back transactions** in tests to ensure isolation.

---
**Need help?** Check:
- [Testcontainers Wiki](https://github.com/testcontainers/testcontainers-java/wiki)
- [Hibernate Dialects](https://www.hibernate.org/orm/dialects/)
- [PostgreSQL vs. MySQL Differences](https://www.percona.com/blog/2016/02/02/postgresql-vs-mysql/)