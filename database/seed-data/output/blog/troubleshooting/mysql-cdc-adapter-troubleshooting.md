# **Debugging MySQL CDC Adapter: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) allows applications to stream database changes (inserts, updates, deletes) in real time, enabling event-driven architectures. The **MySQL CDC Adapter** captures these changes and forwards them to downstream systems (Kafka, databases, event stores, etc.).

This guide provides a structured approach to diagnosing issues with MySQL CDC adapters, focusing on **quick resolution** without deep dive theory.

---

## **1. Symptom Checklist**
Before debugging, confirm the issue:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **No CDC Events** | No changes appear in downstream systems (e.g., Kafka, Sink DB) | Adapter misconfigured, MySQL replication broken, or connection issues |
| **Partial CDC Events** | Some changes are missed or duplicated | Replay lag, binlog offset mismatch, or consumer lag |
| **Connection Errors** | Adapter logs show connection drops (`Connection refused`, `Network is unreachable`) | MySQL server down, firewall blocking, or wrong credentials |
| **High Latency** | CDC events arrive delayed | Slow network, heavy MySQL load, or inefficient filtering |
| **Adapter Crashes** | Adapter shuts down with errors (`NullPointerException`, `SQLSyntaxError`) | Schema mismatch, malformed binlog data, or Java memory issues |
| **Consumer Lag** | Downstream system can’t keep up with event rate | Slow consumers, incorrect partition assignments |

**Quick Check:**
- Verify MySQL binary logging is enabled (`SHOW VARIABLES LIKE 'log_bin'`).
- Check if the adapter is running (`docker ps`, `systemctl status`).
- Monitor MySQL replication status (`SHOW REPLICA STATUS\G`).
- Review downstream consumer logs (Kafka, Sink DB).

---

## **2. Common Issues & Fixes**

### **2.1 Issue: MySQL Binary Logging Disabled**
**Symptoms:**
- Adapter logs: `Binlog not found`
- MySQL errors: `Log bin already exists`

**Root Cause:**
- `log_bin = OFF` in MySQL config (`my.cnf` or `my.ini`).

**Fix:**
1. Edit MySQL config:
   ```ini
   [mysqld]
   log_bin = /var/log/mysql/mysql-bin.log
   server_id = 1
   binlog_format = ROW
   ```
2. Restart MySQL:
   ```bash
   sudo systemctl restart mysql
   ```
3. Verify:
   ```sql
   SHOW VARIABLES LIKE 'log_bin';
   ```

---

### **2.2 Issue: Incorrect Adapter Configuration**
**Symptoms:**
- Adapter fails to start with `No valid host found`.
- Logs show `HostNotFoundException`.

**Root Cause:**
- Wrong MySQL server address, port, or credentials.

**Fix:**
Ensure correct config (example for **Debezium MySQL Connector**):
```json
{
  "name": "mysql-cdc-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "mysql-server",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "database.server.name": "mysql",
    "database.include.list": "test_db",
    "database.history.kafka.bootstrap.servers": "kafka:9092",
    "database.history.kafka.topic": "schema-changes.test_db"
  }
}
```
**Debugging Steps:**
1. Test MySQL connection manually:
   ```bash
   mysql -h mysql-server -u debezium -p -e "SELECT 1;"
   ```
2. Check adapter logs for connection errors.

---

### **2.3 Issue: Binlog Offset Stuck (Replay Lag)**
**Symptoms:**
- CDC events are duplicated or missed.
- Adapter logs: `Position not found for offset`.

**Root Cause:**
- Adapter restart without proper checkpointing.
- MySQL replication lag.

**Fix:**
1. **For Debezium:**
   - Reset offset manually (if safe):
     ```sql
     DELETE FROM mysql_binlog_events WHERE server_id = 184054;
     ```
   - Or restart the connector (will reprocess from latest checkpoint).

2. **For Custom Adapters:**
   - Ensure binlog position is tracked (e.g., `BINLOG_PLAYBACK`).
   - Check MySQL replication status:
     ```sql
     SHOW SLAVE STATUS\G
     ```
     - If `Seconds_Behind_Master` is high, wait or optimize MySQL.

---

### **2.4 Issue: Schema Mismatch (Column/Table Changes)**
**Symptoms:**
- Adapter fails with `Schema evolution error`.
- Downstream system rejects events.

**Root Cause:**
- Table structure changed (DDL operations without CDC awareness).

**Fix:**
1. **For Debezium:**
   - Enable schema evolution:
     ```json
     "transforms": "unwrap",
     "transforms.unwrap.type": "io.debezium.transforms.ByLogSequencePositionUnwrap"
     ```
   - Or ignore changes (not recommended):
     ```json
     "transforms": "filter",
     "transforms.filter.type": "io.debezium.transforms.ignore.value",
     "transforms.filter.ignore.type": "RECORD"
     ```

2. **For Custom Adapters:**
   - Rebuild mapping logic to handle schema changes.
   - Example (Pseudo-code for tracking schema):
     ```java
     if (change.isDDL()) {
         updateSchemaRegistry(changedTable);
     }
     ```

---

### **2.5 Issue: Network/Connection Timeouts**
**Symptoms:**
- Adapter logs: `Connection reset`, `Socket timeout`.
- Downstream system drops events.

**Root Cause:**
- MySQL firewall blocking ports.
- Network latency or MTU issues.

**Fix:**
1. **Check Firewall:**
   ```bash
   sudo ufw status  # Linux
   iptables -L      # Check MySQL ports (3306, 6603 for Debezium)
   ```
   - Allow MySQL ports:
     ```bash
     ufw allow 3306/tcp
     ```

2. **Tune Network:**
   - Increase MySQL connection timeout:
     ```ini
     [mysqld]
     wait_timeout = 600
     interactive_timeout = 600
     ```
   - For Docker/Kubernetes, ensure proper DNS resolution.

3. **Monitor Network:**
   ```bash
   ping mysql-server
   telnet mysql-server 3306
   ```

---

### **2.6 Issue: Adapter Crash (OOM, Thread Leaks)**
**Symptoms:**
- Adapter restarts frequently.
- Logs: `OutOfMemoryError`, `Too many open files`.

**Root Cause:**
- High memory usage (unbounded CDC batch size).
- Thread leaks (e.g., unclosed connections).

**Fix:**
1. **Increase Heap Space (Debezium):**
   ```bash
   export JAVA_OPTS="-Xms2G -Xmx2G"  # Increase JVM memory
   ```

2. **Optimize Batch Processing:**
   ```json
   "offset.flush.interval.ms": "60000",
   "max.queue.size": "10000"
   ```
   - Avoid large batches that cause memory spikes.

3. **Monitor JVM:**
   ```bash
   jcmd <pid> VM.native_memory
   ```

---

## **3. Debugging Tools & Techniques**

### **3.1 MySQL-Specific Tools**
| Tool | Purpose | Command/Usage |
|------|---------|--------------|
| `SHOW BINARY LOGS` | List available binlogs | ```sql SHOW BINARY LOGS;``` |
| `SHOW MASTER STATUS` | Get current binlog position | ```sql SHOW MASTER STATUS\G``` |
| `mysqlbinlog` | Inspect binlog files | ```bash mysqlbinlog /var/log/mysql/mysql-bin.000001``` |
| `pt-table-checksum` | Verify CDC consistency | ```bash pt-table-checksum -u user -p'pass' --replicate --checksum-interval 100``` |

### **3.2 Adapter Debugging**
| Tool | Purpose | Example |
|------|---------|---------|
| **Debezium CLI** | Check connector status | ```bash curl http://localhost:8083/connectors/mysql-cdc/status``` |
| **Kafka Consumer** | Verify events | ```bash kafka-console-consumer --bootstrap-server kafka:9092 --topic test_db.test_table --from-beginning``` |
| **JMX Monitoring** | Track adapter metrics | ```bash jconsole <adapter-pid>``` |
| **Log4j2 Filtering** | Reduce noise | ```xml <Loggers> <Logger name="io.debezium" level="DEBUG"/> </Loggers>``` |

### **3.3 Performance Profiling**
- **MySQL:**
  ```sql
  SELECT * FROM performance_schema.setup_consumers;
  SET GLOBAL slow_query_log = 'ON';
  ```
- **Adapter:**
  Use **VisualVM** or **JFR** to profile JVM bottlenecks.

---

## **4. Prevention Strategies**

### **4.1 Configuration Best Practices**
| Setting | Recommended Value | Notes |
|---------|------------------|-------|
| `log_bin` | `ON` | Must be enabled for CDC |
| `binlog_format` | `ROW` | Best for CDC (changeset format) |
| `max_binlog_size` | `100M` | Prevents too-large binlogs |
| `binlog_checksum` | `NONE/CRC32` | `CRC32` detects corruption |
| **Debezium:**
- `database.history.kafka.bootstrap.servers` | Highly available Kafka | Avoid single points of failure |
- `transforms` | `unwrap`, `route` | Reduce payload size |

### **4.2 Monitoring & Alerts**
- **MySQL:**
  - Monitor `Bytes_read`, `Binlog_cache_size`.
  - Alert on `Seconds_Behind_Master > 10`.
- **Adapter:**
  - Track `records_lag`, `batch.latency`.
  - Set up alerts for `5xx` errors in logs.

**Example Prometheus Alert:**
```yaml
- alert: DebeziumConnectorError
  expr: rate(debezium_connectors_errors_total[5m]) > 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Debezium connector failed: {{ $labels.connector }}"
```

### **4.3 Testing & Validation**
- **Unit Tests:**
  Mock MySQL responses:
  ```java
  @Test
  public void testBinlogEventParsing() {
      String binlogEvent = "[...binary data...]";
      assertEquals("INSERT", EventParser.parseType(binlogEvent));
  }
  ```
- **Integration Tests:**
  Use **Testcontainers** for MySQL:
  ```java
  MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0");
  mysql.start();
  // Test CDC with embedded MySQL
  ```

- **Chaos Engineering:**
  Simulate failures (kill adapter, network drops) to test recovery.

---

## **5. Final Checklist for Quick Resolution**
| Step | Action | Expected Outcome |
|------|--------|------------------|
| 1 | Verify MySQL binary logging | `log_bin = ON` |
| 2 | Check adapter config | Correct host/port/credentials |
| 3 | Monitor binlog position | `SHOW MASTER STATUS` |
| 4 | Test connection manually | `mysql -h host -u user -p` |
| 5 | Review logs for errors | No `NullPointer`, `Connection` errors |
| 6 | Check downstream consumer | Events appear in Kafka/Sink DB |
| 7 | Optimize batch size | Adjust `max.queue.size` if OOM |
| 8 | Set up alerts | Prometheus/Grafana monitoring |

---

## **Conclusion**
Debugging MySQL CDC adapters requires a **structured approach**:
1. **Isolate symptoms** (no events? timeouts? crashes?).
2. **Check fundamentals** (binlog, config, network).
3. **Use tools** (`SHOW BINARY LOGS`, `mysqlbinlog`, JMX).
4. **Prevent future issues** (monitoring, testing, alerts).

For **quick fixes**, focus on:
- Binary logging (`log_bin = ON`).
- Network connectivity (`telnet`, `ufw`).
- Adapter config (Debezium/Kafka settings).

For **deep issues**, enable **debug logs** and profile with **VisualVM/JFR**. Always **validate changes** before production deployment.

---
**Troubleshooting template for future issues:**
```plaintext
[Issue] [Symptom] -> [Root Cause] -> [Fix] -> [Verification]
Example:
[No Events] -> Binlog disabled -> Enable `log_bin` -> `SHOW VARIABLES LIKE 'log_bin'`
```