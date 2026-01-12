# **Debugging Database Setup: A Troubleshooting Guide for Backend Engineers**

## **Introduction**
A well-structured database setup is critical for any backend system. Common issues—such as connection failures, schema mismatches, performance bottlenecks, and security misconfigurations—can disrupt operations. This guide provides a structured approach to diagnosing and resolving database-related problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, identify the root cause by checking the following symptoms:

### **A. Connection Issues**
- Application fails to connect to the database.
- Timeouts or "Connection refused" errors.
- Unreliable connections (random disconnections).

### **B. Data-related Problems**
- Queries returning incorrect or incomplete results.
- Data corruption or inconsistencies.
- Missing records or duplicate entries.

### **C. Performance Degradation**
- Slow query execution (high response times).
- Long blocking locks or deadlocks.
- High CPU/memory usage in the database.

### **D. Security & Compliance Issues**
- Unauthorized database access attempts.
- Logins failing due to incorrect permissions.
- Database being exposed to external threats.

### **E. Configuration & Schema Issues**
- Migration failures (e.g., schema migration misunderstandings).
- Database version mismatches.
- Missing or incorrect indexes.

### **F. Infrastructure & Dependency Problems**
- Database server crashes or unresponsive.
- Network issues between app and database.
- Storage (disk I/O, disk space) constraints.

**Action:** Cross-reference symptoms with logs, monitoring, and error traces to narrow down the issue.

---

## **2. Common Issues & Fixes (with Code Examples)**

### **A. Database Connection Failures**
#### **Symptom:**
`Could not connect to the database: Connection refused` or `Timeout expired`.

#### **Possible Causes & Fixes:**
1. **Database server not running**
   - Check if the database service is active.
   - **Fix (PostgreSQL Example):**
     ```bash
     sudo systemctl status postgresql  # Linux
     ```
   - Restart if needed:
     ```bash
     sudo systemctl restart postgresql
     ```

2. **Incorrect connection string**
   - Verify `host`, `port`, `username`, and `password` in the app config.
   - **Example (Node.js with `pg`):**
     ```javascript
     const { Pool } = require('pg');
     const pool = new Pool({
       user: 'correct_user',  // Check credentials!
       host: 'localhost',
       database: 'test_db',
       password: 'secure_password',
       port: 5432,
     });
     ```

3. **Firewall blocking the port**
   - Ensure the database port (`3306` for MySQL, `5432` for PostgreSQL) is open.
   - **Fix (Linux iptables):**
     ```bash
     sudo iptables -L  # Check restrictions
     sudo ufw allow 5432/tcp  # Allow PostgreSQL traffic
     ```

4. **Network issues (DNS resolution, VPN, cloud security groups)**
   - Test connectivity from the app server:
     ```bash
     telnet database-host 5432  # Should return connection success
     ```

---

### **B. Schema Mismatch (ORM vs. Database)**
#### **Symptom:**
`Table 'users' does not exist` or `Column 'email' does not exist`.

#### **Possible Causes & Fixes:**
1. **Migrations not applied**
   - If using an ORM (e.g., Sequelize, TypeORM), ensure migrations ran:
     ```javascript
     // Using Sequelize CLI
     npx sequelize-cli db:migrate
     ```
   - **Manual SQL fix:**
     ```sql
     CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       email VARCHAR(255) NOT NULL UNIQUE,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```

2. **Wrong database selected**
   - Check if the app is using the correct database (some ORMs switch databases silently).
   - **Fix:**
     ```javascript
     // Explicitly set DB name in connection
     const pool = new Pool({ database: 'correct_db_name' });
     ```

3. **Schema evolutions in production**
   - Avoid direct SQL changes; use migrations.
   - **Example (Node.js + Knex):**
     ```javascript
     // File: 20240520_create_indexes.js
     exports.up = function(knex) {
       return knex.schema.raw('CREATE INDEX idx_user_email ON users(email)');
     };
     exports.down = function(knex) {
       return knex.schema.raw('DROP INDEX idx_user_email');
     };
     ```

---

### **C. Slow Query Performance**
#### **Symptom:**
Queries taking >1s, high `SELECT *` usage, or frequent timeouts.

#### **Possible Causes & Fixes:**
1. **Missing indexes**
   - **Fix:** Add indexes on frequently queried columns.
     ```sql
     CREATE INDEX idx_user_email ON users(email);
     CREATE INDEX idx_order_date ON orders(purchase_date);
     ```

2. **Inefficient queries (e.g., `SELECT *` with large tables)**
   - **Fix:** Optimize queries.
     ```javascript
     // Bad: Fetches all columns
     db.query('SELECT * FROM users WHERE id = ?', [userId]);

     // Good: Select only needed fields
     db.query('SELECT id, email FROM users WHERE id = ?', [userId]);
     ```

3. **No query caching**
   - **Fix:** Implement caching (Redis, Memcached).
     ```javascript
     const { createClient } = require('redis');
     const redis = createClient();
     await redis.connect();
     const cachedData = await redis.get(`user:${userId}`);
     if (!cachedData) {
       const dbData = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
       await redis.set(`user:${userId}`, JSON.stringify(dbData), 'EX', 3600);
     }
     ```

4. **Lock contention**
   - **Fix:** Avoid long-running transactions.
     ```sql
     -- Bad: Holds lock too long
     BEGIN;
     INSERT INTO accounts (user_id, balance) VALUES (1, 1000);
     UPDATE transactions SET status = 'processed' WHERE id = 100;
     COMMIT;

     -- Good: Keep transactions short
     BEGIN;
     UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
     INSERT INTO transactions (...) VALUES (...);
     COMMIT;
     ```

---

### **D. Security Vulnerabilities**
#### **Symptom:**
`User lacks permission` or `Database exposed to unauthorized access`.

#### **Possible Causes & Fixes:**
1. **Overprivileged database users**
   - **Fix:** Use least-privilege principle.
     ```sql
     -- Grant only necessary permissions (PostgreSQL)
     GRANT SELECT, INSERT ON users TO app_user;
     REVOKE ALL ON orders FROM app_user;
     ```

2. **Hardcoded credentials in code**
   - **Fix:** Use environment variables (never commit secrets).
     ```javascript
     // .env
     DB_PASSWORD=your_secure_password

     // app.js
     const password = process.env.DB_PASSWORD;
     ```

3. **No TLS/SSL encryption**
   - **Fix:** Enable SSL for database connections.
     ```javascript
     const pool = new Pool({
       ssl: { rejectUnauthorized: false }, // Adjust in production
       // OR for strict validation:
       ssl: { rejectUnauthorized: true, ca: fs.readFileSync('/path/to/ca.pem') }
     });
     ```

4. **Exposed database on the internet**
   - **Fix:** Restrict access via security groups (AWS), firewall rules, or VPNs.

---

### **E. Migration Failures**
#### **Symptom:**
`Migration failed: Error code: 1050 'Table already exists'`.

#### **Possible Causes & Fixes:**
1. **Race condition in deployments**
   - **Fix:** Ensure database is locked during migrations.
     ```bash
     # Using Node.js + Knex
     npx knex migrate:lock
     npx knex migrate:latest
     npx knex migrate:unlock
     ```

2. **Manual schema changes in production**
   - **Fix:** Rollback manual changes and re-run migrations.
     ```bash
     npx knex migrate:rollback --step 1
     npx knex migrate:latest
     ```

3. **Migrations not idempotent**
   - **Fix:** Design migrations to be reversible.
     ```javascript
     exports.down = function(knex) {
       return knex.schema.table('users', (table) => {
         table.dropColumn('last_login_at');
       });
     };
     ```

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Logging Tools**
- **Database Logs:**
  - PostgreSQL: `/var/log/postgresql/postgresql-14-main.log`
  - MySQL: `/var/log/mysql/error.log`
  - **Enable slow query logging:**
    ```sql
    -- MySQL
    SET GLOBAL slow_query_log = 'ON';
    SET GLOBAL long_query_time = 1;  -- Log queries >1s
    ```

- **Application Logging:**
  - Use structured logging (Winston, Pino) to correlate app errors with DB issues.
    ```javascript
    const winston = require('winston');
    const logger = winston.createLogger({
      transports: [new winston.transports.Console()],
      format: winston.format.json()
    });
    logger.info('Query executed', { query: 'SELECT * FROM users' });
    ```

### **B. Query Profiling**
- **PostgreSQL `EXPLAIN ANALYZE`:**
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
  ```
  - Look for `Seq Scan` (slow) vs. `Index Scan` (fast).

- **MySQL `EXPLAIN`:**
  ```sql
  EXPLAIN SELECT * FROM orders WHERE user_id = 1;
  ```

### **C. Network & Connection Debugging**
- **`ping` and `telnet` for connectivity:**
  ```bash
  ping database-server
  telnet database-host 5432
  ```
- **`netstat` to check active connections:**
  ```bash
  netstat -tulnp | grep mysql  # MySQL connections
  ```

### **D. Monitoring & Alerting**
- **Tools:**
  - **Prometheus + Grafana:** Track DB metrics (latency, errors, connections).
  - **Datadog/New Relic:** APM for database queries.
  - **pgBadger (PostgreSQL):** Analyze slow queries from logs.

- **Example Prometheus metrics (PostgreSQL):**
  ```promql
  rate(pg_up{job="postgres"}[1m])  # Database uptime
  histogram_quantile(0.95, sum(rate(pg_stat_activity_query_time_sum[5m])) by (le))  # 95th percentile query latency
  ```

### **E. Reproducible Test Environments**
- **Use Docker for local DB testing:**
  ```dockerfile
  # docker-compose.yml
  version: '3'
  services:
    postgres:
      image: postgres:14
      environment:
        POSTGRES_USER: testuser
        POSTGRES_PASSWORD: testpass
      ports:
        - "5432:5432"
  ```
- **Test migrations locally before production:**
  ```bash
  docker-compose up -d
  npx knex migrate:latest
  ```

---

## **4. Prevention Strategies**
### **A. Infrastructure Best Practices**
1. **Database Backups:**
   - Automate backups (e.g., `pg_dump` for PostgreSQL).
     ```bash
     pg_dump -U postgres -d mydb -f backup.sql
     ```
   - Test restores periodically.

2. **High Availability (HA):**
   - Use read replicas for scaling reads.
   - Set up failover with tools like **Patroni (PostgreSQL)** or **MySQL InnoDB Cluster**.

3. **Resource Limits:**
   - Monitor disk space, CPU, and RAM.
   - Set alerts for 90%+ usage.

### **B. Code & Schema Management**
1. **Version-Control Migrations:**
   - Store migration files in Git (never modify them manually in production).
   - Example structure:
     ```
     migrations/
       ├── 20240515_create_users.js
       ├── 20240516_add_email_index.js
     ```

2. **ORM Best Practices:**
   - Avoid `SELECT *`; specify columns.
   - Use transactions for critical operations:
     ```javascript
     await db.tx(async (trx) => {
       await trx('users').update({ balance: trx('users').select('balance').where({ id: userId }).plus(100) });
       await trx('transactions').insert({ user_id: userId, amount: 100 });
     });
     ```

3. **Security Hardening:**
   - Rotate database passwords regularly.
   - Use **database-specific tools** (e.g., **PostgreSQL Row-Level Security (RLS)**).

### **C. CI/CD & Deployment**
1. **Test Migrations in Staging:**
   - Always run migrations in a staging environment before production.

2. **Blue-Green Deployments for DB Schema:**
   - Avoid downtime by testing changes in a parallel environment.

3. **Rollback Plan:**
   - Document how to revert migrations if they fail.

### **D. Monitoring & Alerts**
1. **Set Up Dashboards:**
   - Track:
     - Query execution time.
     - Connection pool usage.
     - Error rates.

2. **Alert on Anomalies:**
   - Example (Prometheus alert rule):
     ```yaml
     - alert: HighDatabaseLatency
       expr: histogram_quantile(0.95, rate(pg_stat_activity_query_time_sum[5m])) > 1
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High database latency ({{ $value }}s)"
     ```

---

## **5. Checklist for Quick Resolution**
| **Issue**               | **Immediate Actions**                                                                 | **Long-Term Fix**                          |
|-------------------------|--------------------------------------------------------------------------------------|--------------------------------------------|
| Connection refused      | Check DB service status, firewall, network.                                          | Use proper logging for connection attempts. |
| Missing table           | Run pending migrations.                                                              | Enforce migration discipline.              |
| Slow queries            | Analyze with `EXPLAIN`, add indexes.                                                 | Implement query caching.                   |
| Permission denied       | Grant required permissions (least privilege).                                        | Use DB roles for different apps.           |
| Migration failure       | Rollback and re-run migrations.                                                      | Test migrations in staging.                |
| Security breach         | Restrict access, rotate credentials, audit logs.                                      | Enforce TLS, use secrets manager.          |
| High CPU/memory         | Check for runaway queries, optimize indexes.                                         | Set up auto-scaling for DB.                |

---

## **Conclusion**
Debugging database issues requires a structured approach: **identify symptoms → isolate the root cause → apply fixes → prevent recurrence**. Use logging, profiling, and monitoring tools to streamline troubleshooting. For production systems, automation (backups, HA, CI/CD) is key to resilience.

**Final Tip:** Always test changes in a staging environment before applying them to production. When in doubt, check the database logs first.