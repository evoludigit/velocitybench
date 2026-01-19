# **Debugging Databases: A Practical Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **Introduction**
Databases are the backbone of nearly all applications. When they fail, the impact is immediate—slow responses, crashes, or data corruption. This guide provides a structured approach to diagnosing and resolving common database issues efficiently.

---

## **Symptom Checklist**
Before diving into fixes, systematically verify these symptoms:

| **Symptom**                     | **Possible Causes**                          | **Check With**                     |
|----------------------------------|---------------------------------------------|------------------------------------|
| Database connection failures      | Network issues, overloaded DB, misconfig     | `netstat`, `SHOW PROCESSLIST`, logs |
| Slow query performance           | Poor indexing, large tables, missing stats | `EXPLAIN`, `mysqlslow.log`         |
| High CPU/Memory usage            | Full-table scans, long-running queries      | `top`, `htop`, `SHOW FULL PROCESSLIST` |
| Data inconsistency errors        | Transaction corruption, replication lag     | `CHECKSUM TABLE`, `SHOW SLAVE STATUS` |
| Replication failures             | Network issues, binary log corruption       | `SHOW SLAVE STATUS`, binary logs   |
| Storage space exhaustion         | Uncontrolled table growth, backups          | `df -h`, `SHOW TABLE STATUS`       |
| Crashes or segfaults             | Corrupted storage, memory leaks             | Check error logs (`/var/log/mysql/error.log`) |

---

## **Common Issues & Fixes**

### **1. Connection Errors**
**Symptoms:** `connection refused`, `timeout`, or `access denied`.

#### **Common Causes & Fixes**
- **Misconfigured `my.cnf`/`my.ini`**
  - Verify `bind-address` is set to listen on all interfaces if needed.
  - Check `max_connections` isn’t too low for concurrent users.
  - Example fix:
    ```ini
    [mysqld]
    bind-address = 0.0.0.0
    max_connections = 2000
    ```

- **Network Firewall Blocking Port 3306 (MySQL default)**
  - Check AWS Security Groups, `iptables`, or cloud firewall rules.
  - Example (AWS CLI):
    ```sh
    aws ec2 authorize-security-group-ingress \
      --group-id sg-xxxxxx --protocol tcp --port 3306 --cidr 0.0.0.0/0
    ```

- **User/Permission Issues**
  - Verify credentials in application config vs. database grants.
  - Fix with:
    ```sql
    GRANT ALL PRIVILEGES ON db_name.* TO 'user'@'%' IDENTIFIED BY 'password';
    FLUSH PRIVILEGES;
    ```

---

### **2. Slow Queries**
**Symptoms:** High `latency`, `timeout`, or `slow query logs` flooding.

#### **Common Causes & Fixes**
- **Missing Indexes**
  - Use `EXPLAIN` to identify missing keys.
  - Example:
    ```sql
    EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';
    ```
  - Add an index if the scan rate is > 10% of rows:
    ```sql
    ALTER TABLE users ADD INDEX idx_email (email);
    ```

- **Large Table Scans**
  - Partition large tables or split into smaller chunks.
  - Example (PostgreSQL):
    ```sql
    CREATE TABLE logs (
      id SERIAL,
      data JSONB,
      created_at TIMESTAMP
    ) PARTITION BY RANGE (created_at);
    ```

- **Query Optimization**
  - Avoid `SELECT *` and use `LIMIT` for pagination.
  - Example:
    ```sql
    -- Bad: Scans entire table
    SELECT * FROM orders;

    -- Good: Only fetches needed columns
    SELECT id, amount FROM orders WHERE user_id = 1 LIMIT 100;
    ```

---

### **3. High CPU/Memory Usage**
**Symptoms:** Slow performance, OOM killer kills MySQL process.

#### **Common Causes & Fixes**
- **InnoDB Buffer Pool Exhaustion**
  - Increase `innodb_buffer_pool_size` (50% of available RAM).
  - Example:
    ```ini
    [mysqld]
    innodb_buffer_pool_size = 16G
    ```

- **Long-Running Queries**
  - Identify and kill blocking queries:
    ```sql
    SHOW FULL PROCESSLIST WHERE Time > 10;
    KILL 1234; -- Replace with query ID
    ```

- **Memory Leaks**
  - Monitor with `pmap` and restart if needed:
    ```sh
    pmap -x <pid_of_mysql>
    ```

---

### **4. Replication Failures**
**Symptoms:** Slave not syncing with master, lagging replication.

#### **Common Causes & Fixes**
- **Binary Log Corruption**
  - Reset replication using `MASTER_POSITION`.
  - Example:
    ```sql
    STOP SLAVE;
    RESET SLAVE ALL;
    START SLAVE;
    ```

- **Network Issues**
  - Use `SHOW SLAVE STATUS` to check `Last_Error`.
  - Example fix:
    ```sql
    CHANGE MASTER TO
      MASTER_HOST='master_ip',
      MASTER_USER='repl_user',
      MASTER_PASSWORD='password',
      MASTER_PORT=3306,
      MASTER_LOG_FILE='mysql-bin.000123',
      MASTER_LOG_POS=1234;
    ```

- **Slave Not Keeping Up**
  - Add `slave-net-timeout` to handle slow connections:
    ```ini
    [mysqld]
    slave-net-timeout = 60
    ```

---

### **5. Storage Issues**
**Symptoms:** `Disk full`, `Table corruption`, slow storage I/O.

#### **Common Causes & Fixes**
- **Excessive Log/Backup Space**
  - Clean up old binary logs:
    ```sh
    mysql -e "PURGE BINARY LOGS BEFORE NOW() - INTERVAL 7 DAY"
    ```

- **Corrupted Tables**
  - Repair with:
    ```sql
    CHECK TABLE corrupted_table;
    REPAIR TABLE corrupted_table;
    ```

- **Slow SSD/HDD**
  - Use `dd` to benchmark:
    ```sh
    dd if=/dev/zero of=tempfile bs=1M count=1000 oflag=direct
    ```
  - If slow, consider NVMe or cloud storage (EBS/GCE Persistent Disk).

---

## **Debugging Tools & Techniques**

| **Tool/Technique**         | **Purpose**                          | **Usage Example**                     |
|----------------------------|--------------------------------------|----------------------------------------|
| **`mysqladmin processlist`** | View running queries.               | `mysqladmin -u root -p processlist`    |
| **`pt-query-digest`**      | Analyze slow query logs.            | `pt-query-digest /var/log/mysql/mysql-slow.log` |
| **`percona-toolkit`**      | Check replication, locks, etc.       | `pt-table-checksum db_name.table`      |
| **`pg_top` (PostgreSQL)**   | Monitor PostgreSQL processes.        | `pg_top`                              |
| **`traceroute`**           | Diagnose network latency.            | `traceroute db-server`                |
| **`vmstat`/`iostat`**      | Check I/O & CPU usage.               | `iostat -x 1`                          |

---

## **Prevention Strategies**

1. **Monitoring**
   - Use tools like **Prometheus + Grafana** for metrics.
   - Example MySQL exporter: [prometheus/mysqld-exporter](https://github.com/prometheus/mysqld-exporter).

2. **Logging & Alerts**
   - Enable slow query logs:
     ```ini
     [mysqld]
     slow_query_log = 1
     slow_query_log_file = /var/log/mysql/mysql-slow.log
     long_query_time = 2
     ```
   - Set up alerts for high CPU/memory (e.g., via **Datadog** or **New Relic**).

3. **Backup Strategy**
   - Use **LVM snapshots** or **Percona XtraBackup** for hot backups.
   - Example (MySQL):
     ```sh
     xtrabackup --backup --target-dir=/backup/mysql
     ```

4. **Scaling**
   - **Read Replicas** for read-heavy workloads.
   - **Sharding** for horizontal scaling.
   - Example (PostgreSQL):
     ```sql
     CREATE TABLE users (
       id SERIAL,
       name VARCHAR(100)
     ) PARTITION BY LIST (id % 4);
     ```

5. **Regular Maintenance**
   - **Optimize tables** weekly:
     ```sql
     OPTIMIZE TABLE large_table;
     ```
   - **Update MySQL/PostgreSQL** (patch security vulnerabilities).

---

## **Final Checklist for Quick Resolution**
When troubleshooting:
1. **Check logs first** (`/var/log/mysql/error.log`, `/var/log/syslog`).
2. **Isolate the issue** (connection, query, replication, storage).
3. **Apply fixes incrementally** (don’t restart DB unnecessarily).
4. **Test changes** in staging before production.
5. **Document the fix** and its impact.

---
**Key Takeaway:** Database issues often stem from misconfigurations or unoptimized queries. **Start with logs, query analysis, and resource checks**—don’t guess. Use monitoring to prevent outages before they happen.

Would you like a deeper dive into any specific area (e.g., PostgreSQL-specific issues, Kubernetes DB deployments)?