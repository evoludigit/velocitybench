# **Debugging Database Patterns: A Troubleshooting Guide**

## **Introduction**
Databases are the backbone of modern applications, but poorly designed schemas, query inefficiencies, or misconfigured indexing can lead to performance bottlenecks, data corruption, or availability issues. This guide covers common database troubleshooting scenarios, focusing on **patterns** (such as **Repository, Unit of Work, CQRS, Active Record, and Data Mapper**) and provides actionable fixes.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms align with your issue:

### **Performance-Related Symptoms**
- [ ] Slow queries (taking > 500ms)
- [ ] High CPU/memory usage on DB servers
- [ ] "Timeouts" or "Connection pool exhausted" errors
- [ ] Frequent locks or deadlocks
- [ ] High disk I/O or slow read/write operations

### **Functionality-Related Symptoms**
- [ ] Data inconsistencies (e.g., missing records, duplicate entries)
- [ ] Transactions failing with **constraint violations** (e.g., foreign key errors)
- [ ] ORM-related issues (e.g., lazy loading failures, N+1 queries)
- [ ] Schema migrations breaking production
- [ ] Stale data in read replicas

### **Infrastructure-Related Symptoms**
- [ ] Database crashes or restarts
- [ ] Slow replication lag (in master-slave setups)
- [ ] Network latency between app and DB
- [ ] Authentication/authorization failures

---

## **2. Common Issues & Fixes**

### **2.1 Slow Queries & Performance Bottlenecks**
#### **Common Causes:**
- **Missing Indexes** → Full table scans
- **N+1 Query Problem** → Inefficient ORM usage (e.g., Hibernate/Eager Loading)
- **Large Result Sets** → Fetching all records in bulk
- **Unoptimized Joins** → Cartesians, improper join conditions

#### **Debugging Steps & Fixes**
**A. Identify Slow Queries**
- Use **database slow query logs** (MySQL: `slow_query_log`, PostgreSQL: `pg_stat_statements`)
- Run `EXPLAIN ANALYZE` on suspect queries
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active';
  ```
- Look for `Seq Scan` (full scan) instead of `Index Scan`.

**B. Fix Missing Indexes**
```sql
-- Missing index example (PostgreSQL)
CREATE INDEX idx_users_status ON users(status);
```

**C. Fix N+1 Problem (Hibernate Example)**
❌ **Bad (N+1 queries):**
```java
List<User> users = userRepository.findAll();
for (User user : users) {
    user.getOrders(); // Separate query per user
}
```
✅ **Fixed (Fetch Join or Specifications):**
```java
List<User> users = userRepository.findAllWithOrders(); // Single query
```

**D. Optimize Joins**
❌ **Bad (Cartesian Product Risk):**
```sql
SELECT * FROM users u, orders o; -- Missing JOIN condition!
```
✅ **Fixed:**
```sql
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

---

### **2.2 Data Inconsistencies & Transaction Issues**
#### **Common Causes:**
- **Improper Unit of Work (UoW) handling** → Partial commits
- **Duplicate Constraint Violations** → Missing unique checks
- **Race Conditions** → Unsafe concurrent writes
- **ORM Mismatch** → Detached entities not synced

#### **Debugging Steps & Fixes**
**A. Debug Unit of Work (Database Transactions)**
❌ **Bad (Manual commits):**
```java
userRepository.save(user); // Commit 1
orderRepository.save(order); // Commit 2 → Risk of partial state
```
✅ **Fixed (Transaction Management):**
```java
@Transactional
public void createOrder(User user, Order order) {
    userRepository.save(user);
    orderRepository.save(order); // Both committed or rolled back
}
```

**B. Handle Unique Constraint Errors**
```sql
-- Check for duplicates before insert
IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'user@example.com') {
    INSERT INTO users (email) VALUES ('user@example.com');
}
```
Or use **unique indexes**:
```sql
CREATE UNIQUE INDEX idx_users_email ON users(email);
```

**C. Fix ORM Detached Entity Issues (Hibernate)**
```java
// Detached entities lose changes
User user = userRepository.findById(1);
// Modify user...
// Detach happens here → Changes lost!
userRepository.flush(); // Force sync
```

---

### **2.3 Schema Migration Failures**
#### **Common Causes:**
- **Downtime during migration** → Rolling back
- **Data loss in constraints** → Foreign key errors
- **ORM misalignment** → Generated code vs. DB schema mismatch

#### **Debugging Steps & Fixes**
**A. Safe Migrations (PostgreSQL Example)**
```sql
-- Use transactions for safety
BEGIN;
-- Drop old column first
ALTER TABLE users DROP COLUMN old_column;
-- Add new column
ALTER TABLE users ADD COLUMN new_column VARCHAR(255);
COMMIT;
```
**B. Check ORM State (Spring + Flyway)**
```java
@Bean
public DataSource dataSource(DataSource existingDataSource) {
    return new FlywayDataSourceDecorator(existingDataSource);
}
```
**C. Rollback Plan**
- If migration fails, **stop new versions** before reverting.
- Use **backup DB** before migrations.

---

### **2.4 Connection Pool Exhaustion**
#### **Common Causes:**
- **Leaked connections** → Not closed properly
- **Too few pool size** → Underload
- **Long transactions** → Blocking connections

#### **Debugging & Fixes**
**A. Check Connection Leaks (HikariCP Example)**
```java
// Always close connections in finally
try (Connection conn = dataSource.getConnection()) {
    // Use conn...
} // Auto-closes
```
**B. Adjust Pool Settings**
```xml
<!-- Spring Boot HikariCP config -->
<property name="hikari.data-source.max-pool-size" value="10" />
<property name="hikari.data-source.max-lifetime" value="30000" /> <!-- 30 sec -->
```

---

## **3. Debugging Tools & Techniques**
| **Tool/Technique**       | **Purpose**                          | **Example**                          |
|--------------------------|---------------------------------------|---------------------------------------|
| **Database Profiler**    | Log query execution details           | MySQL `slow_query_log`, PgBadger      |
| **ORM Debugging**        | Track entity state (Hibernate/JPA)    | `sessionFactory.openSession()`        |
| **Explain Analyze**      | Optimize slow queries                 | `EXPLAIN ANALYZE SELECT ...`          |
| **Transaction Logs**     | Debug rollbacks/failures              | `spring.jpa.show-sql=true` (logback)  |
| **Load Testing**         | Stress-test DB under load             | JMeter, Gatling                       |
| **Schema Comparison**    | Detect drift between DB & ORM         | Liquibase, Flyway diff                |

---

## **4. Prevention Strategies**
### **Best Practices for Database Patterns**
✅ **Repository Pattern**
- Use **pagination** (`Pageable` in Spring Data JPA)
- Avoid raw SQL unless necessary
- Implement **soft deletes** for auditability

```java
public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT u FROM User u WHERE u.status = :status")
    Page<User> findActiveUsers(@Param("status") String status, Pageable pageable);
}
```

✅ **Unit of Work (UoW)**
- **Always use `@Transactional`** for multi-step ops
- **Keep transactions short** to reduce locks

```java
@Transactional(isolation = Isolation.READ_COMMITTED)
public void transferFunds(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepo.findById(fromId).orElseThrow(...);
    Account to = accountRepo.findById(toId).orElseThrow(...);
    from.withdraw(amount);
    to.deposit(amount);
}
```

✅ **CQRS (Separate Reads/Writes)**
- Use **Materialized Views** for reads
- **Event Sourcing** for audit logs

```java
// Write-side (command)
@EventSourcingHandler
public void on(OrderPlacedEvent event) {
    orderRepo.save(new Order(event.getOrderId(), event.getAmount()));
}

// Read-side (query)
@QueryHandler
public OrderQueryHandler() {
    // Pre-aggregate data
}
```

✅ **Data Mapper (Domain-Driven Design)**
- **Avoid ORM entanglement** (e.g., don’t mix DTOs with entities)
- **Use DTOs for API responses**

```java
public UserDTO toDto(User user) {
    return UserDTO.builder()
        .id(user.getId())
        .email(user.getEmail())
        .name(user.getName())
        .build();
}
```

---

## **5. Final Checklist for Fast Debugging**
1. **Check logs first** (DB, app, ORM logs).
2. **Reproduce in staging** (avoid production guesswork).
3. **Use `EXPLAIN ANALYZE`** if queries are slow.
4. **Enable transaction logging** (`spring.jpa.show-sql=true`).
5. **Test migrations in a backup DB** before production.
6. **Monitor connection pools** (HikariCP metrics).
7. **Review recent code changes** (new queries, ignored indexes).

---
**Next Steps:**
- **If performance issues persist**, consider **sharding** or **read replicas**.
- **For schema-related bugs**, audit **migration scripts** and **ORM mappings**.
- **For connection leaks**, use **connection pooling monitoring tools** (Prometheus + Grafana).

By following this guide, you should be able to **quickly isolate and resolve** 90% of database-related issues. Happy debugging! 🚀