---
# **[Database Replication Strategies] Reference Guide**
*Ensure high availability, disaster recovery, and scalability via synchronous or asynchronous data replication across database servers.*

---

## **1. Overview**
Database replication synchronizes data changes from a **primary (master) server** to **secondary (standby/replica) servers**, enabling:
- **High Availability (HA)**: Automatic failover to replicas during primary downtime.
- **Disaster Recovery (DR)**: Geo-redundancy for regional outages.
- **Read Scaling**: Offload read queries from the primary to replicas.
- **Load Balancing**: Distribute read traffic across multiple replicas.

Replication latency, failover complexity, and durability depend on the replication strategy (e.g., **synchronous**, **asynchronous**, or **logical**). Common implementation techniques include:
- **Streaming Replication (PostgreSQL)**: Real-time WAL (Write-Ahead Log) forwarding.
- **Binary Log Replication (MySQL)**: Binlog-based change propagation.
- **Trigger-Based Replication**: Row-level events for custom logic.

**Trade-offs**:
| **Metric**          | **Synchronous Replica** | **Asynchronous Replica** |
|----------------------|-------------------------|--------------------------|
| **Durability**       | High (acknowledged writes)| Lower (potential data loss)|
| **Latency**          | Higher                  | Lower                    |
| **Failover Complexity** | Moderate (quorums)   | Simpler (no consensus)    |

---

## **2. Schema Reference**
| **Component**          | **Description**                                                                 | **Key Properties**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Primary (Master)**   | Source of truth; accepts writes.                                               | - Configurable `synchronous_standby_names` (PostgreSQL) or `binlog_format=ROW`. |
| **Replica (Standby)**  | Synchronized read/write-target (synchronous) or read-only replica.          | - Promoted via `pg_promote` (PostgreSQL) or `CHANGE MASTER TO`.                 |
| **Replication Process**| Mechanism to propagate writes to replicas.                                    | - **PostgreSQL**: Streaming via `wal_level=replica` + `hot_standby=on`.        |
|                        |                                                                               | - **MySQL**: Binlog replication with `slave/debian-sys-maint` user.            |
| **Replication Lag**    | Time delay between primary and replica writes.                                | - Monitor with `pg_stat_replication` (PostgreSQL) or `SHOW SLAVE STATUS`.       |
| **Failover Mechanism** | Process to switch primary role to a replica during outage.                    | - **Manual**: Promote replica (`pg_ctl promote`).                                 |
|                        |                                                                               | - **Automated (e.g., Patroni, MHA)**: Uses quorum for leader election.           |

---

## **3. Key Implementation Details**
### **3.1 Replication Modes**
| **Mode**               | **Description**                                                                 | **Use Case**                                                                 |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Synchronous**        | Primary waits for acknowledgment from all replicas before confirming writes. | Critical applications requiring zero data loss (e.g., financial systems).   |
| **Asynchronous**       | Primary sends writes to replicas without waiting for confirmation.            | High-traffic apps where slight lag is acceptable.                          |
| **Semi-Synchronous**   | Hybrid: Primary waits for *some* replicas (e.g., 1/3 majority).               | Balances durability and performance.                                       |

### **3.2 Replication Lag Mitigation**
- **Increase Replica Resources**: More CPU/RAM reduces lag.
- **Compress Replication Streams**: Use `pg_bouncer` or `binlog_compression`.
- **Scheduled Snapshots**: For bulk historical syncs (e.g., `pg_basebackup`).
- **Logical Decoding**: Apply changes via logical replication (PostgreSQL) or CDC tools (e.g., Debezium).

### **3.3 Failover Workflow**
1. **Detect Outage**: Use tools like `patroni`, `Kubernetes operator`, or manual `pg_isready`.
2. **Promote Replica**:
   ```bash
   # PostgreSQL (manual)
   sudo pg_ctl promote /path/to/replica_data
   ```
   ```sql
   -- MySQL (promote standby as master)
   CHANGE MASTER TO MASTER_HOST='localhost', MASTER_USER='replicator', MASTER_AUTO_POSITION=1;
   ```
3. **Update DNS/API Load Balancers**: Point traffic to new primary.
4. **Resync Remaining Replicas**: Resume replication from promoted server.

### **3.4 Recovery Point Objective (RPO)**
- **RPO**: Max acceptable data loss (e.g., 5 minutes).
  - **Synchronous replication** → Near-zero RPO.
  - **Asynchronous replication** → RPO = replication lag.

---

## **4. Query Examples**
### **4.1 Check Replication Status (PostgreSQL)**
```sql
-- List replication slots and lag
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  sent_location,
  write_location,
  flush_location,
  replay_location,
  EXTRACT(EPOCH FROM (now() - pg_wal_lsn_diff(replay_location, sent_location)/32768)) AS lag_seconds
FROM pg_stat_replication;
```

### **4.2 Verify Replication Status (MySQL)**
```sql
SHOW SLAVE STATUS\G
-- Key fields:
--   Seconds_Behind_Master: Replication lag (seconds).
--   Slave_IO_Running: 'Yes' if catching up.
```

### **4.3 Promote a Replica (PostgreSQL)**
```bash
# Stop replica (if running)
sudo systemctl stop postgresql@replica
# Promote to primary
sudo pg_ctl promote -D /var/lib/postgresql/data/replica
# Start replica as new primary
sudo systemctl start postgresql@replica
```

### **4.4 Configure Synchronous Replication (PostgreSQL)**
Edit `postgresql.conf` (primary):
```ini
synchronous_commit = on
synchronous_standby_names = '*'
hot_standby = on
wal_level = replica
```

---

## **5. Components/Solutions**
### **5.1 Primary (Master) Server**
- **Role**: Accepts writes, propagates changes to replicas.
- **Tools**:
  - **PostgreSQL**: `wal_level=replica` + `pg_hba.conf` for replica authentication.
  - **MySQL**: `binlog_format=ROW` + `server_id` for unique identification.

### **5.2 Replica (Standby) Server**
- **Role**: Read-only by default (unless promoted); used for failover/read scaling.
- **Tools**:
  - **PostgreSQL**: `primary_conninfo` in `postgresql.conf` to connect to primary.
  - **MySQL**: `CHANGE MASTER TO MASTER_HOST=...` to subscribe to binlog.

### **5.3 Replication Process**
| **Database**       | **Method**                          | **Config Example**                                  |
|--------------------|-------------------------------------|-----------------------------------------------------|
| **PostgreSQL**     | Streaming Replication               | `pg_basebackup --wal-level=replica` + `start_replication`. |
| **MySQL**          | Binlog Replication                 | `mysqlbinlog /var/log/mysql/master-bin.000001`.    |
| **Logical Replication (PostgreSQL)** | Pub/Sub via `pg_repack` or CDC tools | `CREATE PUBLICATION mypub FOR TABLE users;`          |

---

## **6. Example Architecture**
```
[Application Layer]
   │
   ├───[Primary (PostgreSQL)]───────┬─────────────▶ [Read Scaling: Replica 1,2]
   │                                  │
   └───────────[Binlog (MySQL)]──────┘
   │
   └───────────[Failover: Promote Replica → New Primary]
```

---

## **7. Related Patterns**
1. **[Sharding]** – Horizontal partitioning for horizontal scalability (complements replication for read/write separation).
2. **[Connection Pooling]** – Manage replica load (e.g., PgBouncer, ProxySQL).
3. **[Backup and Restore]** – Point-in-time recovery (PITR) using WAL archiving (PostgreSQL) or `mysqlbinlog` (MySQL).
4. **[Multi-Region Deployment]** – Replicate across regions with tools like **Citus** (PostgreSQL) or **GTID-based replication** (MySQL).
5. **[Automated Failover]** – Use managed services (AWS RDS, Google Cloud SQL) or tools like **Patroni**, **MHA**, or **Kubernetes Operators**.

---
## **8. Best Practices**
- **Monitor Replication Lag**: Set up alerts for `lag_seconds > 60`.
- **Test Failover Regularly**: Simulate primary outages with `pg_ctl stop` or `mysqld_safe --skip-networking`.
- **Limit Replica Write Conflicts**: Use **application-level locking** or **row-level filters** (`WHERE id IN (...)`).
- **Secure Replication**: Restrict replica access with:
  ```ini
  # PostgreSQL pg_hba.conf
  host    replication     repl_user     replica_server_ip/32   md5 "password"
  ```
- **Avoid Over-Replication**: Scale reads via **read replicas** (not primary replicas).

---
## **9. Troubleshooting**
| **Issue**               | **PostgreSQL Fix**                          | **MySQL Fix**                                  |
|-------------------------|--------------------------------------------|-----------------------------------------------|
| **Replication Lag**     | Increase `max_wal_senders` or replica CPU. | Tune `relay-log` or `binlog_row_image=FULL`. |
| **Failed Sync**         | Check `pg_last_wal_receive_lsn` vs `pg_last_wal_replay_lsn`. | Run `STOP SLAVE; START SLAVE;` in MySQL. |
| **Promotion Fail**      | Verify `pg_control` file on replica.       | Check `GRANT RELOAD` privileges.              |

---
## **10. References**
- [PostgreSQL Documentation: Replication](https://www.postgresql.org/docs/current/warm-standby.html)
- [MySQL Documentation: Replication](https://dev.mysql.com/doc/refman/8.0/en/replication.html)
- [Debezium: Change Data Capture](https://debezium.io/) (for logical replication)
- [Citus Data: Distributed PostgreSQL](https://www.citusdata.com/) (for sharding + replication)