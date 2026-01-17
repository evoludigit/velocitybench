# **Debugging Failover Configuration: A Troubleshooting Guide**

Failover systems are critical for high availability (HA) and disaster recovery (DR). When failover mechanisms fail, downtime, data loss, or degraded performance can occur. This guide provides a structured approach to diagnosing, resolving, and preventing failover configuration issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

### **Primary Symptoms of Failover Failure**
- **No automatic failover** – Primary node remains down despite secondary nodes being healthy.
- **Unexpected promotions** – Secondary node becomes primary without proper trigger (e.g., heartbeat loss, manual intervention).
- **Delayed failover** – Failover takes longer than expected (e.g., minutes vs. seconds).
- **Inconsistent state** – Replicated data is not synchronized post-failover.
- **Cluster health warnings** – Alerts in monitoring tools (e.g., Prometheus, Nagios, Zabbix) about failover issues.
- **Logs indicating stalls** – Failover logs show no activity despite failures.
- **Manual intervention required** – Admins must manually trigger failover in production.

### **Secondary Symptoms (Related Issues)**
- **Network connectivity drops** – Failover relies on network stability.
- **Resource exhaustion** – CPU, memory, or disk bottlenecks preventing failover.
- **Misconfigured replication** – Database/cluster replication lag.
- **Time synchronization issues** – NTP drift causing heartbeat failures.
- **Permission problems** – Missing IAM roles, SELinux/AppArmor restrictions.

---

## **2. Common Issues & Fixes**

### **2.1 Failover Not Triggering When Expected**
**Symptom:**
- Primary node crashes, but secondary node does not take over.

**Possible Causes & Fixes:**

#### **A. Heartbeat/Quorum Issues (Kubernetes, Pacemaker, Corosync)**
- **Cause:** Heartbeat packets are not being received between nodes.
- **Fix:**
  ```bash
  # Check Corosync/Corosync status (if using Pacemaker/Corosync)
  sudo systemctl status pacemaker corosync
  ```
  - **Logs:**
    ```bash
    journalctl -u corosync -n 50 --no-pager
    ```
  - **Solution:**
    - Verify network connectivity (`ping`, `mtr`, `tcpdump`).
    - Check firewall rules (`sudo iptables -L`, `sudo ufw status`).
    - Adjust `totem` configuration in `/etc/corosync/corosync.conf`:
      ```ini
      totem {
          version: 2
          secauth: on
          cluster_name: mycluster
          token: 3000
          interface {
              ring0_iface: eth0
              ring0_addr: <NODE_IP>
          }
      }
      ```

#### **B. Database Replication Lag (PostgreSQL, MySQL, MongoDB)**
- **Cause:** Replication lag prevents secondary from being promoted.
- **Fix:**
  - **PostgreSQL (pg_basebackup):**
    ```sql
    SELECT pg_is_in_recovery();  -- Check if secondary is syncing
    ```
    ```bash
    sudo pg_isready -U postgres -h <SECONDARY_IP>  # Test connectivity
    ```
  - **MySQL (replication status):**
    ```sql
    SHOW SLAVE STATUS\G  # Check Second_Remote_IO_Running
    ```
  - **Solution:**
    - Increase replication bandwidth (`binlog_row_image=FULL`).
    - Adjust `slave_net_timeout` in MySQL config.
    - Use `pg_rewind` (PostgreSQL) to recover lagged nodes.

#### **C. Stuck in "Standby" Mode (ETCD, ZooKeeper)**
- **Cause:** Leader election timeout or network partition.
- **Fix:**
  - **ETCD:**
    ```bash
    etcdctl endpoint health  # Check cluster health
    etcdctl endpoint status  --write-out=table
    ```
    - **Fix:** Reset leader (`ETCDCTL_API=3 etcdctl endpoint health --write-out=table`).
  - **ZooKeeper:**
    ```bash
    echo stat | nc <ZK_IP> 2181  # Check ZooKeeper state
    ```
    - **Fix:** Adjust `initLimit` and `syncLimit` in `zoo.cfg`.

---

### **2.2 Failover Takes Too Long**
**Symptom:**
- Failover completes in **minutes instead of seconds**.

**Possible Causes & Fixes:**

#### **A. Slow Leader Election (Consul, Kafka)**
- **Cause:** Too many nodes or slow network.
- **Fix:**
  - **Consul:**
    ```bash
    consul members  # Check cluster health
    ```
    - Increase `consul.raft.heartbeat_interval` (if using Raft mode).
  - **Kafka:**
    ```bash
    kafka-leader-election.sh --bootstrap-server <BROKER>:9092 --topic __consumer_offsets --partition 0 --election-type IMPERATIVE
    ```
    - Tune `unclean.leader.election.enable=false` (disables unsafe leadership).

#### **B. Replication Lag (NoSQL Databases)**
- **Cause:** Network latency or disk I/O bottlenecks.
- **Fix:**
  - **MongoDB:**
    ```bash
    mongostat --host <SECONDARY_IP>  # Check replication lag
    ```
    - Increase `replSetSyncTimeout` or use chunked replication.
  - **Cassandra:**
    ```bash
    nodetool status  # Check replication status
    ```
    - Adjust `replication_factor` and `hinted_handoff_enabled`.

---

### **2.3 Failover to Wrong Node**
**Symptom:**
- A **non-primary node** becomes primary unexpectedly.

**Possible Causes & Fixes:**

#### **A. Misconfigured Priority (Pacemaker, Kubernetes)**
- **Cause:** Incorrect resource priority settings.
- **Fix:**
  - **Pacemaker CRMshell:**
    ```bash
    crm configure show
    ```
    - Check `prefer-api` and `score` attributes.
    - Adjust with:
      ```bash
      crm configure resource failover fencing prop priority=100
      ```

#### **B. Managed Service Failover (AWS RDS, GCP Cloud SQL)**
- **Cause:** Multi-AZ failover is disabled or misconfigured.
- **Fix:**
  - **AWS RDS:**
    ```bash
    aws rds describe-db-instances --db-instance-identifier <INSTANCE>
    ```
    - Ensure `MultiAZ` is `true`.
    - Enable failover monitoring (`rds-monitor`).
  - **GCP Cloud SQL:**
    ```bash
    gcloud sql instances describe <INSTANCE> --format=json
    ```
    - Set `availability_type: REGIONAL`.

---

### **2.4 Data Inconsistency Post-Failover**
**Symptom:**
- Primary node has newer data than secondary after failover.

**Possible Causes & Fixes:**

#### **A. Unsafe Failover (Kafka, ZooKeeper)**
- **Cause:** `unclean.leader.election.enable=true` (Kafka).
- **Fix:**
  - **Kafka:**
    ```bash
    sed -i 's/unclean.leader.election.enable=true/unclean.leader.election.enable=false/' server.properties
    kafka-server-start.sh --config server.properties
    ```
  - **ZooKeeper:**
    - Enable `4lw.commands.whitelist` to prevent unsafe operations.

#### **B. Replication Lag (PostgreSQL, MySQL)**
- **Cause:** Secondary node was not fully synced before promotion.
- **Fix:**
  - **PostgreSQL:**
    ```bash
    pg_rewind /var/lib/postgresql/data/ /var/lib/postgresql/data/backup/
    ```
  - **MySQL:**
    ```sql
    RESET SLAVE ALL;
    CHANGE MASTER TO MASTER_USE_GTID=current_pos;
    ```

---

## **3. Debugging Tools & Techniques**
### **3.1 Monitoring & Logging**
| Tool | Purpose | Example Command |
|------|---------|----------------|
| **Corosync/Corosync Logs** | Pacemaker failover logs | `journalctl -u corosync` |
| **Prometheus + Grafana** | Cluster health metrics | `prometheus-node-exporter` |
| **ETCD Debugging** | Leader election issues | `ETCDCTL_API=3 etcdctl endpoint health` |
| **ZooKeeper Snake Plot** | Network latency analysis | `zkCli.sh` + `mvn exec:java -Dexec.mainClass=org.apache.zookeeper.server.quorum.Snake` |
| **PostgreSQL pgBadger** | Replication lag analysis | `pgBadger -f postgresql.log` |
| **MySQL pt-table-checksum** | Data consistency checks | `pt-table-checksum -u root -p'password' -n 2 --replicate` |

### **3.2 Network Diagnostics**
| Tool | Purpose | Example Command |
|------|---------|----------------|
| **Ping & MTR** | Network latency | `mtr <NODE_IP>` |
| **TCPDUMP** | Packet inspection | `tcpdump -i eth0 port 2281` (Corosync) |
| **Wireshark** | Advanced network analysis | Filter for `corosync` or `raft` traffic |
| **Netdata** | Real-time cluster monitoring | `sudo netdata` |
| **NTP Sync Check** | Heartbeat clock drift | `ntpq -p` |

### **3.3 Database-Specific Debugging**
| Database | Command | Purpose |
|----------|---------|---------|
| **PostgreSQL** | `SELECT pg_is_in_recovery();` | Check sync status |
| **MySQL** | `SHOW SLAVE STATUS\G` | Replication lag |
| **MongoDB** | `db.serverStatus().repl` | Replica set health |
| **Cassandra** | `nodetool status` | Ring consistency |
| **ETCD** | `etcdctl endpoint health` | Cluster leadership |

---

## **4. Prevention Strategies**
### **4.1 Configuration Best Practices**
✅ **Always test failover in staging** before production deployment.
✅ **Set appropriate timeouts** (`totem.consensus=5000`, `pg_basebackup_timeout=60s`).
✅ **Monitor replication lag** (alert if >10s in PostgreSQL).
✅ **Use network bonding** (`bonding-driver`) for high availability.
✅ **Enable encryption** (`ssl=on` in PostgreSQL, `tls` in Kafka).

### **4.2 Automated Failover Testing**
```bash
# Pacemaker failover test
sudo crm_resource --test --failover --mode manual ip_resource

# Kubernetes failover simulation
kubectl delete pod -n <namespace> <pod-name> --grace-period=0 --force
```

### **4.3 Disaster Recovery (DR) Plan**
| Component | DR Strategy |
|-----------|------------|
| **SQL Databases** | Regular backups + `pg_rewind` |
| **NoSQL (Cassandra, MongoDB)** | Cross-DC replication |
| **Kubernetes** | Multi-zone `NodeAffinity` |
| **ETCD/ZooKeeper** | Persistent storage + snapshots |
| **Pacemaker/Corosync** | Regular `crm_resource --test` |

### **4.4 Alerting & Incident Response**
- **Set up alerts** for:
  - `failover_delay > 30s`
  - `replication_lag > 5s`
  - `heartbeat_loss > 30s`
- **Use tools:**
  - **Prometheus + Alertmanager**
  - **Datadog + PagerDuty**
  - **AWS CloudWatch Alerts**

---

## **5. Summary Checklist for Quick Resolution**
| Step | Action |
|------|--------|
| **1. Check logs** | `journalctl -u corosync`, `pgBadger`, `zkCli.sh` |
| **2. Verify network** | `mtr <NODE_IP>`, `tcpdump` |
| **3. Test failover manually** | `crm failover` (Pacemaker) |
| **4. Adjust timeouts** | `totem.consensus`, `pg_basebackup_timeout` |
| **5. Restart services** | `systemctl restart corosync` |
| **6. Re-sync data** | `pg_rewind`, `mysqlbinlog` |
| **7. Run DR drills** | Simulate node failures |

---
### **Final Notes**
- **Failover is not instantaneous** – Acceptable delay depends on use case (e.g., seconds for DBs, minutes for backups).
- **Always document failover procedures** – Include steps for manual intervention.
- **Automate recovery** – Use tools like **Ansible** or **Terraform** for consistent failover testing.

By following this guide, you should be able to **diagnose, fix, and prevent** failover issues efficiently. If problems persist, consider **isolation testing** (e.g., single-node vs. multi-node) to narrow down the root cause.