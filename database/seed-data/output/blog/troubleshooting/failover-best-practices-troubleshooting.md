# **Debugging Failover Best Practices: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **1. Introduction**
Failover ensures high availability (HA) by automatically switching to a standby system when the primary fails. Poor failover implementation can lead to downtime, data inconsistency, or cascading failures. This guide helps diagnose and resolve common failover issues efficiently.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom**                          | **How to Detect**                                                                 | **Severity** |
|---------------------------------------|-----------------------------------------------------------------------------------|--------------|
| Primary node crashes repeatedly       | Check logs (`journalctl`, `docker logs`, `k8s events`), monitor alerts (Prometheus), or observe API health checks. | High |
| Failover triggers but service unavailability | Verify failover logs, test failover manually, and check if standby was promoted successfully. | Critical |
| Data inconsistency between nodes      | Run checksum comparisons (`md5sum`), validate transactions (e.g., `pg_isready` in PostgreSQL), or use distributed logs (ZooKeeper, etcd). | Critical |
| Slow failover response               | Measure failover latency (metrics: `failover_duration_seconds`), check network latency (`ping`, `mtr`), and resource contention (`top`, `htop`). | Medium |
| Standby node fails to take over       | Check resource constraints (CPU/memory), misconfigured health checks, or permission issues. | High |
| Circular failovers (ping-pong effect)| Examine failover triggers (e.g., heartbeat timeouts), disk errors (`dmesg`), or misconfigured quorum. | Critical |

---

## **3. Common Issues and Fixes**

### **A. Primary Node Crashes Repeatedly**
**Cause:** Hardware failure, misconfigured resource limits, or OS-level issues.
**Debugging Steps:**
1. **Check logs:**
   ```bash
   # For Docker/Kubernetes:
   docker logs <container>
   kubectl logs <pod> --previous

   # For systemd services:
   journalctl -u <service> --no-pager -n 50
   ```
2. **Identify hardware issues:**
   ```bash
   dmesg | grep -i error  # Check kernel logs for disk/CPU failures
   smartctl -a /dev/sdX # Verify disk health
   ```
3. **Review resource constraints:**
   ```bash
   # Check CPU/memory usage on primary:
   top -c -n 1
   ```
   - If the primary is OOM-killed, adjust `ulimit` or resource quotas in Kubernetes.

**Fix:**
- Replace failing hardware.
- Scale up primary node or optimize resource usage.
- Configure graceful degradation (e.g., `max_connections` in databases).

---

### **B. Failover Triggers but Service Unavailable**
**Cause:** Standby was not promoted correctly, or health checks failed.
**Debugging Steps:**
1. **Verify failover logs:**
   ```bash
   # Example for HAProxy (if using it for failover):
   grep -i failover /var/log/haproxy.log

   # For database failovers (e.g., PostgreSQL):
   psql -c "SELECT pg_is_in_recovery();"
   ```
2. **Check health check failures:**
   ```bash
   # Simulate a health check (replace with your endpoint):
   curl -v http://<primary-ip>:<port>/health
   ```
   - If standby reports `unhealthy`, check:
     - Network connectivity (`telnet <primary-ip> <port>`).
     - Missing dependencies (e.g., database replication lag).

**Fix:**
- **Manual promotion (if automated failover failed):**
  ```sql
  -- PostgreSQL example:
  SELECT pg_promote();
  ```
- **Adjust health check thresholds:**
  ```yaml
  # Example for Kubernetes liveness probe:
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    failureThreshold: 5
  ```
- **Restart failover controller (e.g., Keepalived):**
  ```bash
  systemctl restart keepalived
  ```

---

### **C. Data Inconsistency Between Nodes**
**Cause:** Replication lag, failed sync, or manual intervention.
**Debugging Steps:**
1. **Compare data integrity:**
   ```bash
   # Example for filesystems (compare checksums):
   md5sum /path/to/data_primary > primary.md5
   md5sum /path/to/data_standby > standby.md5
   diff primary.md5 standby.md5

   # For databases (e.g., PostgreSQL):
   SELECT pg_size_pretty(pg_database_size('db_name'));
   ```
2. **Check replication status:**
   ```sql
   -- PostgreSQL replication lag:
   SELECT pg_stat_replication;
   ```
   - If `replay_lag` is high, increase WAL archiving or reduce client load.

**Fix:**
- **Force sync (if replication is stalled):**
  ```sql
  -- PostgreSQL: Trigger resync
  SELECT pg_switch_wal();
  ```
- **Restore from backup (last resort):**
  ```bash
  # Example for etcd (if corrupted):
  etcdctl snapshot save snapshot.db
  etcdctl snapshot restore snapshot.db
  ```

---

### **D. Slow Failover Response**
**Cause:** Network latency, misconfigured timeouts, or resource contention.
**Debugging Steps:**
1. **Measure network latency:**
   ```bash
   ping <standby-ip>  # Check RTT
   mtr <primary-ip>   # Trace route + latency
   ```
2. **Review failover metrics:**
   ```bash
   # Prometheus query for failover duration:
   histogram_quantile(0.95, sum(rate(failover_duration_seconds_bucket[5m])) by (le))
   ```
3. **Check system load:**
   ```bash
   sar -u 1  # CPU usage over time
   ```

**Fix:**
- **Reduce failover timeout:**
  ```yaml
  # Example for HAProxy:
  failover_sla_active 10000  # 10s timeout
  ```
- **Optimize network paths:**
  - Use bonded interfaces or VLANs for failover traffic.
  - Reduce DNS lookup times (e.g., use `failover-ip` with cloud provider load balancers).
- **Scale resources for standby:**
  ```bash
  # Kubernetes: Pre-warm standby pods
  kubectl scale deployment <app> --replicas=2
  ```

---

### **E. Circular Failovers (Ping-Pong Effect)**
**Cause:** Misconfigured quorum, split-brain scenarios, or flaky hardware.
**Debugging Steps:**
1. **Check cluster quorum:**
   ```bash
   # ZooKeeper example:
   echo stat | nc localhost 2181
   ```
2. **Review heartbeat logs:**
   ```bash
   grep -i "split brain" /var/log/keepalived.log
   ```
3. **Simulate network partitions:**
   ```bash
   # Test with `tcpdump` or `iptables` to force splits:
   tcpdump -i any host <primary-ip> -w split_test.pcap
   ```

**Fix:**
- **Enforce strict quorum:**
  ```ini
  # Keepalived config (minimum 2 nodes for quorum):
  VRRP_Script_check {
      script "check_ping"
      interval 3
      weight 2
  }
  ```
- **Use external monitoring (e.g., Consul) to detect splits:**
  ```bash
  consul members  # Verify node connectivity
  ```
- **Replace faulty hardware causing flakiness.**

---

## **4. Debugging Tools and Techniques**
| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|-------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Prometheus + Grafana** | Track failover latency, errors, and node health.                          | `failover_duration_seconds` metric          |
| **cAdvisor**            | Monitor Kubernetes pod resource usage during failover.                     | `kubectl top pods`                          |
| **Wireshark/tcpdump**   | Analyze network traffic (e.g., replication lag, heartbeat messages).        | `tcpdump -i eth0 port 5432` (PostgreSQL)    |
| **ethtool**             | Check network interface issues (duplex, speed).                            | `ethtool -S eth0`                           |
| **systemd-analyze**     | Identify slow boot or startup failures post-failover.                      | `systemd-analyze blame`                     |
| **PostgreSQL `pgBadger`** | Log analysis for replication issues.                                    | `pgbadger -f postgres.log`                  |
| **Kubernetes `kubectl`** | Debug pod failover in orchestrated environments.                          | `kubectl describe pod <pod-name>`          |

**Advanced Techniques:**
- **Chaos Engineering:** Use tools like [Chaos Mesh](https://chaos-mesh.org/) to test failover under stress.
- **Distributed Tracing:** Add OpenTelemetry to trace requests across primary/standby nodes.
- **Golden Images:** Maintain consistent AMIs/containers for failover nodes.

---

## **5. Prevention Strategies**
### **A. Design-Time Best Practices**
1. **Multi-AZ Deployments:**
   - Deploy primary/standby in separate availability zones (AWS, GCP, Azure).
   - Use cloud provider failover services (e.g., RDS Multi-AZ, Kubernetes Multi-Cluster).
2. **Automated Health Checks:**
   - Implement end-to-end health checks (e.g., `/health` endpoints).
   - Use liveness probes in Kubernetes:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 10
       failureThreshold: 3
     ```
3. **Replication Tuning:**
   - Database: Adjust `max_replication_slots` (PostgreSQL), `binlog_group_size` (MySQL).
   - Example for PostgreSQL:
     ```sql
     ALTER SYSTEM SET max_replication_slots = 10;
     ```
4. **Resource Isolation:**
   - Use cgroups or Kubernetes resource limits to prevent resource starvation during failover.

### **B. Operational Best Practices**
1. **Regular Failover Drills:**
   - Simulate failovers weekly (e.g., `kubectl delete svc <primary>` in Kubernetes).
2. **Monitoring Alerts:**
   - Set up alerts for:
     - Failover duration > 5s (adjust threshold).
     - Replication lag > 1 minute.
     - Node CPU > 90% for 5 minutes.
   - Example Prometheus alert:
     ```yaml
     - alert: HighReplicationLag
       expr: pg_stat_replication_replay_lag > 60
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "PostgreSQL replication lag is high"
     ```
3. **Backups and Snapshots:**
   - Schedule regular backups (e.g., `pg_dump` for PostgreSQL).
   - Test restore procedures quarterly.
4. **Documentation:**
   - Maintain a runbook for failover steps (e.g., "How to manually promote standby").

### **C. Incident Response Plan**
1. **Escalation Path:**
   - Define SLOs (e.g., "RTO < 2 minutes").
   - Assign on-call engineers with failover permissions.
2. **Post-Mortem:**
   - After a failover incident, document:
     - Root cause (e.g., "Hardware failure in AZ-B").
     - Time to recovery (TTM).
     - Actions to prevent recurrence (e.g., add redundancy to disks).
3. **Blame-Free Post-Mortems:**
   - Focus on system design gaps, not individual errors.

---

## **6. Example Debugging Workflow**
**Scenario:** Primary database node crashes, and failover to standby takes 10+ minutes.

1. **Check Symptoms:**
   - `pg_stat_replication` shows `replay_lag` = 600s.
   - `kubectl get pods` shows standby pod restarting.
2. **Drill Down:**
   - `journalctl -u postgres` reveals OOM killer terminating the standby.
   - `top` shows CPU throttling on standby node.
3. **Fix:**
   - Adjust Kubernetes resource requests:
     ```yaml
     resources:
       requests:
         memory: "4Gi"
         cpu: "2"
       limits:
         memory: "8Gi"
     ```
   - Restart standby:
     ```bash
     kubectl rollout restart deployment <postgres-deployment>
     ```
4. **Verify:**
   - Monitor `failover_duration_seconds` in Prometheus (now ~30s).
   - Check `pg_is_in_recovery` → `false` (standby promoted successfully).

---

## **7. Key Takeaways**
| **Issue**               | **Quick Fix**                          | **Prevention**                              |
|--------------------------|-----------------------------------------|---------------------------------------------|
| Primary crashes          | Replace hardware, adjust resources     | Hardware RAID, automated backups            |
| Slow failover            | Reduce timeouts, optimize network      | Bonded interfaces, pre-warm standby          |
| Data inconsistency       | Force sync, restore from backup        | Regular sync checks (`pg_stat_replication`)  |
| Circular failovers       | Enforce quorum, replace flaky nodes     | External monitoring (e.g., Consul)          |
| Standby fails to promote | Check health checks, permissions        | End-to-end health probes                    |

---
**Final Notes:**
- **Automate everything.** Script failover recovery steps (e.g., Ansible, Bash).
- **Test failover monthly.** Use chaos tools to ensure resilience.
- **Monitor proactively.** Failures often precede crashes (e.g., increasing latency).

By following this guide, you can diagnose and resolve failover issues efficiently, minimizing downtime and ensuring high availability.