# **Debugging Failover Validation: A Troubleshooting Guide**

## **1. Introduction**
Failover Validation is a critical pattern used to ensure system resilience by verifying that backup systems (failover nodes) can take over seamlessly when the primary node fails. Misconfigurations, network issues, or unhandled dependencies can break this process, leading to downtime.

This guide provides a structured approach to diagnosing, fixing, and preventing Failover Validation failures.

---

## **2. Symptom Checklist**
Before diving into debugging, confirm the issue using these signs:

### **Primary Node Failures**
- [ ] **Primary node crashes unexpectedly** (e.g., OOM, kernel panic, service failure).
- [ ] **Application logs** indicate failover did not trigger (e.g., no health check alerts).
- [ ] **Failover script/logs** show `FAILED` or timeout errors.
- [ ] **Manual failover attempts** hang or reject (e.g., `failover --force` fails).

### **Failover Node Issues**
- [ ] **Backup node fails to boot** (disk, RAM, or service failures).
- [ ] **Health checks** (e.g., `curl http://<backup-node>:<port>/health`) return `5xx` errors.
- [ ] **Traffic redirection fails** (DNS, load balancer, or proxy misrouting).
- [ ] **State synchronization** (e.g., database replication, cache sync) stalls.

### **Network and Dependency Failures**
- [ ] **Network connectivity lost** between primary/backup nodes (ping fails).
- [ ] **DNS propagation delay** causes failover to incorrect endpoint.
- [ ] **External dependencies** (e.g., database, messaging queue) unreachable from backup node.
- [ ] **Clock skew** (>5s) prevents TLS/SSL handshake or database replication.

### **Observation Tools**
- Check **system logs** (`journalctl`, `/var/log/`).
- Monitor **health endpoints** (`/health`, `/status`).
- Verify **network latency** (`ping`, `mtr`, `traceroute`).
- Review **failover controller logs** (e.g., Kubernetes `kube-controller-manager`, Corosync, DRBD).

---

## **3. Common Issues and Fixes**

### **3.1 Primary Node Fails Without Notifying Failover**
**Symptom:**
- Primary node crashes, but backup node is unaware.
- No automated failover occurs.

**Root Causes:**
1. **Health check endpoint flaky** (e.g., HTTP 200 but degraded performance).
2. **Heartbeat timeout misconfigured** (too short/long).
3. **Failover script unresponsive** (blocked on I/O, DB lock).

**Fixes:**
#### **A. Improve Health Checks**
Ensure the endpoint is **always 2xx** when healthy, but log warnings for degraded state.

```bash
# Example health check (Node.js/Express)
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', metrics: { ... } });
});
```

#### **B. Adjust Heartbeat Timeout**
- **Too short?** → False positives.
- **Too long?** → Slow detection.

```ini
# Corosync config (failover_timeout_s = 10s recommended)
quorum {
  quorum_votes 2;
  quorum_policy no-quorum-policy;
  failover_timeout { timeout: 10; }
}
```

#### **C. Debug Failover Script**
Check for deadlocks or blocking calls:

```bash
# Example failover script (Bash)
#!/bin/bash
if ! curl -s http://<primary>:8080/health | grep -q '"status":"healthy"'; then
  echo "Failed health check, triggering failover..."
  systemctl restart <service>
  # Log to verify execution
  echo "$(date) : Failover initiated" >> /var/log/failover.log
else
  echo "Primary healthy, no action."
fi
```

**Debugging:**
```bash
# Check script execution
sudo bash -x /path/to/failover.sh
```

---

### **3.2 Backup Node Fails to Take Over**
**Symptom:**
- Primary fails, but backup node **does not start** or **fails to serve traffic**.

**Root Causes:**
1. **Services not running** (e.g., `systemd` unit failed).
2. **Configuration mismatch** (e.g., different `app.conf`).
3. **Dependencies not synced** (e.g., DB replica lagging).

**Fixes:**
#### **A. Verify Backup Node Boot**
Check system services:
```bash
systemctl list-units --failed   # List failed services
journalctl -xe                  # Check boot logs
```

#### **B. Compare Configurations**
Ensure **primary/backup env vars, configs, and DB schemas match**:
```bash
# Compare app config
diff <(cat /etc/app/config.json) <(cat /etc/app/config_backup.json)
```

#### **C. Sync Dependencies**
For databases (e.g., PostgreSQL):
```bash
# Check replication lag
psql -c "SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp()"
# Fix if lagged: Adjust `max_replication_slots` in postgresql.conf
```

For caching (Redis):
```bash
# Ensure slave-of is set correctly
redis-cli info replication | grep 'master_host'
```

---

### **3.3 DNS or Load Balancer Misrouting**
**Symptom:**
- Failover happens, but **DNS/LB sends traffic to old node**.

**Root Causes:**
1. **DNS TTL too long** (caches stale records).
2. **LB health checks misconfigured** (fails to detect failover).
3. **Manual override in LB** (e.g., AWS ALB stuck on old IP).

**Fixes:**
#### **A. Reduce DNS TTL**
Set TTL to **30s–60s** for failover zones:
```bash
# Example BIND zone config
$TTL 60
@       IN  SOA  ns1.example.com. admin.example.com. (
    2024010101 ; Serial
    3600       ; Refresh
    1800       ; Retry
    604800     ; Expire
    300        ; Minimum TTL
)
```

#### **B. Configure LB Health Checks**
Example (AWS ALB):
- **Health check path:** `/health`
- **Interval:** `30s`
- **Timeout:** `5s`
- **Unhealthy threshold:** `2`

#### **C. Force LB Sync**
If LB has stale data:
```bash
# AWS ALB: Manual sync (via Console → Target Groups → "Sync")
# NGINX: Reload config
nginx -s reload
```

---

### **3.4 State Mismatch After Failover**
**Symptom:**
- Backup node starts, but **data inconsistent** (e.g., cached vs. DB mismatch).

**Root Causes:**
1. **Incomplete DB replication**.
2. **Cache stale** (Redis/Memcached not flushed).
3. **Transactions lost** (no write-ahead log sync).

**Fixes:**
#### **A. Force DB Sync**
For PostgreSQL:
```sql
SELECT pg_suspend_backend();
-- Wait for replication to catch up
SELECT pg_resume_backend();
```

For MySQL:
```sql
FLUSH TABLES WITH READ LOCK;
-- Apply pending changes
UNLOCK TABLES;
```

#### **B. Clear Cache**
```bash
# Redis: Flush all
redis-cli FLUSHALL
# Or sync from primary (if possible)
redis-cli REPLICATE
```

#### **C. Enable Write-Ahead Logging**
Ensure your app **flushes changes to DB before acknowledging success**.

```python
# Example (Flask/SQLAlchemy)
@app.route('/update', methods=['POST'])
def update():
    db.session.commit()  # Force write to DB
    return "Success"
```

---

## **4. Debugging Tools and Techniques**

| **Tool/Technique**          | **Purpose**                                                                 | **Example Command/Usage**                          |
|-----------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **`journalctl`**            | Check system logs (systemd services).                                       | `journalctl -u nginx -xe`                         |
| **`curl`/`wget`**           | Test health endpoints.                                                     | `curl -v http://<node>:8080/health`              |
| **`netstat`/`ss`**          | Check network connections (listening ports).                               | `ss -tulnp`                                      |
| **`mtr`**                   | Diagnose network latency/hops.                                              | `mtr <primary-node>`                             |
| **`ping`/`traceroute`**     | Verify network reachability.                                               | `traceroute <backup-node>`                       |
| **`strace`**                | Debug system calls in failover scripts.                                    | `strace -f /usr/local/bin/failover.sh`           |
| **`tcpdump`**               | Capture network traffic (failover protocol).                                | `tcpdump -i any port 6666` (Corosync default)    |
| **Database Replication Logs** | Check DB sync status.                                                       | `tail -f /var/log/postgresql/postgresql.log`    |
| **Prometheus/Grafana**      | Monitor failover metrics (latency, errors).                                | Query: `up{job="app"} == 0`                     |
| **Chaos Engineering Tools** | Simulate failures (e.g., kill primary node).                               | `chaos-mesh run kill -n <namespace> -p 50%`      |

**Advanced Debugging:**
- **Enable debug logs** in failover controllers (e.g., Corosync, Kubernetes).
- **Use `strace` on failover scripts** to find blocking calls:
  ```bash
  strace -f -s 99 /usr/bin/failover_script.sh
  ```
- **Enable packet capture** for custom failover protocols:
  ```bash
  tcpdump -i eth0 -w failover.pcap 'port 5432'  # PostgreSQL replication
  ```

---

## **5. Prevention Strategies**

### **5.1 Configuration Checks**
- **Automate config validation** before deploy:
  ```bash
  # Example: Compare configs with Ansible
  ansible-playbook -i hosts validate-config.yml
  ```
- **Use Infrastructure as Code (IaC)** (Terraform, CloudFormation) to ensure consistency.

### **5.2 Monitoring and Alerts**
- **Set up alerts** for:
  - **Health checks failing** (e.g., Prometheus alert: `health_check_failures > 0`).
  - **Replication lag** (e.g., `pg_last_xact_replay_timestamp` too old).
  - **Network partitions** (e.g., `ping_failure > 3`).

```yaml
# Example Prometheus Alert (failover_health.yaml)
- alert: FailoverHealthCheckFailed
  expr: up{job="app", service="failover"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Failover health check failed for {{ $labels.instance }}"
```

### **5.3 Testing Failovers**
- **Simulate failures** in staging:
  ```bash
  # Kill primary node gracefully
  sudo systemctl stop <primary-service>
  ```
- **Use chaos engineering tools**:
  ```bash
  chaos-mesh run kill -n kube-system -p 100% --duration 30s
  ```
- **Automated failover tests** (e.g., with `pytest` for services):
  ```python
  def test_failover_recovery():
      # 1. Kill primary
      kill_primary()
      # 2. Wait for backup to take over
      assert backup_node_is_healthy(timeout=30)
  ```

### **5.4 Automate Recovery**
- **Self-healing scripts**:
  ```bash
  # Example: Auto-restart failed services
  while true; do
      if ! curl -s http://localhost:8080/health | grep -q 'healthy'; then
          sudo systemctl restart app
      fi
      sleep 10
  done
  ```
- **Kubernetes Readiness/Liveness Probes**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  ```

### **5.5 Documentation and Runbooks**
- **Document failover steps** (e.g., GitHub Wiki).
- **Maintain a runbook** for emergency recovery:
  ```
  === FAILOVER EMERGENCY RUNBOOK ===
  1. Verify primary is dead: `curl -v http://primary:8080/health`
  2. Promote backup:
     - Run: `sudo systemctl start app@backup`
  3. Check replication:
     - For DB: `pg_is_in_recovery`
  4. DNS/LB update:
     - AWS Route53: Change alias to backup-node.
  ```

---

## **6. Conclusion**
Failover Validation failures are often caused by **misconfigured dependencies, flaky health checks, or untimely state sync**. The key steps in debugging are:
1. **Confirm symptoms** (check logs, health endpoints).
2. **Isolate the failure** (primary? backup? network?).
3. **Fix root cause** (config, script, or dependency).
4. **Test recovery** before production.

**Prevent future issues** by:
✅ Automating config validation.
✅ Setting up alerts for failover health.
✅ Regularly testing failovers in staging.
✅ Documenting emergency procedures.

By following this guide, you can quickly diagnose and resolve Failover Validation failures with minimal downtime.