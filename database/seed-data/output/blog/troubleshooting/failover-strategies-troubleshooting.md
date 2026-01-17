# **Debugging Failover Strategies: A Troubleshooting Guide**

Failover strategies are critical for maintaining system availability, especially in distributed and high-availability (HA) architectures. When failover mechanisms fail—whether due to misconfiguration, race conditions, or communication issues—systems can degrade into degraded or completely unavailable states. This guide provides a structured approach to diagnosing and resolving common failover-related issues.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **Primary node fails to failover** | No automatic switch to a standby node after primary failure. | Misconfigured health checks, stuck heartbeat, or failed discovery mechanisms. |
| **Secondary node fails to promote** | Standby node does not take over after primary failure. | Locking issues, pending transactions, or misconfigured promotion logic. |
| **Split-brain scenario** | Two nodes both claim primary leadership. | Network partition (e.g., flapping network), conflicting health checks, or race conditions. |
| **Slow failover** | Failover takes longer than expected (e.g., >30 seconds). | Long-running recovery tasks, slow replication sync, or inefficient health checks. |
| **Failback issues** | System fails to revert to primary node after recovery. | Manual intervention not handled, or failback logic has bugs. |
| **Error logs indicate stuck processes** | Logs show stuck `failover_pending`, `promotion_blocked`, or `replication_lag`. | Deadlocks, misconfigured timeouts, or stuck transactions. |
| **Clients disconnected mid-failover** | Clients lose connection during failover transition. | Incomplete state synchronization, abrupt TCP disconnects, or misconfigured load balancers. |
| **Monitoring alerts for unhealthy nodes** | Prometheus/Grafana shows nodes in `UNHEALTHY` state post-failover. | Incorrect health check thresholds, misconfigured liveness probes. |

**Next Steps:**
- Check **system logs** (`/var/log/<service>.log` or `journalctl -u <service>`).
- Verify **health checks** (`curl http://<node>:<health_check_port>/health`).
- Review **failover logs** (e.g., `failover.log`, `replication.log`).
- Monitor **network connectivity** (`ping`, `tcpdump`, `mtr`).

---

## **2. Common Issues & Fixes**
### **Issue 1: Primary Node Not Failing Over**
**Symptoms:**
- Primary node crashes, but standby node does not take over.
- Logs show `No health check response from primary` or `Heartbeat timeout exceeded`.

**Root Causes:**
- **Misconfigured health checks** (wrong endpoint or threshold).
- **Network partition** (primary node unreachable).
- **Heartbeat timeout too long** (standby waits longer than needed).
- **Promotion blocked** (e.g., due to pending operations).

#### **Debugging Steps:**
1. **Check health check endpoint:**
   ```bash
   curl -v http://<primary_node>:<health_check_port>/health
   ```
   - If it fails, verify the endpoint is correct in the failover config.

2. **Review heartbeat logs:**
   ```bash
   grep "heartbeat" /var/log/<service>.log
   ```
   - Look for `timeout` or `no_response` errors.

3. **Adjust heartbeat timeout (if needed):**
   ```yaml
   # Example in Kubernetes Deployment (if using Kubernetes HA)
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
     initialDelaySeconds: 5
     periodSeconds: 10
     failureThreshold: 3
     timeoutSeconds: 5  # Adjust if heartbeats are too slow
   ```

4. **Check network connectivity:**
   ```bash
   ping <primary_node>
   telnet <primary_node> <health_check_port>
   ```
   - If `ping` works but `telnet` fails, check firewall rules (`iptables`, `ufw`).

#### **Fix Example (Manual Promotion Trigger)**
If the system supports manual promotion (e.g., etcd, ZooKeeper), force it:
```bash
# For ZooKeeper (using `zkCli.sh`)
addauth digest admin:password
reconfig - verbose -file /path/to/cluster.config
```

---

### **Issue 2: Split-Brain Scenario (Two Nodes Claim Primary)**
**Symptoms:**
- Two nodes both respond to `/health` as `OK`.
- Clients see inconsistent data.
- Logs show `primary_election_in_progress`.

**Root Causes:**
- **Network flapping** (intermittent connectivity).
- **Incorrect election timeout** (too short → frequent elections; too long → stuck).
- **Misconfigured quorum** (e.g., odd-numbered cluster with even-sized splits).
- **Race condition** in election logic.

#### **Debugging Steps:**
1. **Check network stability:**
   ```bash
   mtr <primary_node>  # Test latency/jitter
   tcpdump -i eth0 port <health_check_port>  # Capture network packets
   ```
   - If packets are lost, investigate network hardware or MTU issues.

2. **Review election logs:**
   ```bash
   grep "election" /var/log/<service>.log
   ```
   - Look for `split_vote` or `no_quorum` errors.

3. **Adjust election timeout:**
   ```yaml
   # Example in Consul config
   leave_on_terminate = true
   election_timeout = "20s"  # Increase if elections are too frequent
   ```

4. **Verify quorum settings:**
   - Ensure the cluster size is odd (e.g., 3, 5, 7 nodes).
   - If using Raft/Consul, check `raft_protocol` for split-brain protection.

#### **Fix Example (Force Quorum Recovery)**
For etcd:
```bash
ETCDCTL_API=3 etcdctl endpoint health --write-out=table
```
If quorum is lost, manually promote a healthy node:
```bash
ETCDCTL_API=3 etcdctl member add --ascii <node_id> <ip>:<port> --name=<node_name>
```

---

### **Issue 3: Slow Failover (30+ Seconds)**
**Symptoms:**
- Failover takes longer than expected (e.g., 30s vs. 5s).
- Logs show `replication_lag` or `sync_in_progress`.

**Root Causes:**
- **Slow replication** (e.g., network latency, disk I/O).
- **Long-running transactions** (e.g., large writes before failover).
- **Misconfigured sync timeout** (standby waits too long to catch up).

#### **Debugging Steps:**
1. **Check replication lag:**
   ```bash
   # For PostgreSQL
   SELECT pg_is_in_recovery(), pg_last_xact_replay_timestamp();

   # For etcd
   ETCDCTL_API=3 etcdctl endpoint status --write-out=table
   ```
   - High lag indicates replication bottlenecks.

2. **Review failover logs:**
   ```bash
   grep "sync" /var/log/<service>.log
   ```
   - Look for `replication_delay` or `sync_timeout`.

3. **Adjust sync timeout (if needed):**
   ```yaml
   # Example in etcd config
   cluster-advertise-client-urls = "http://0.0.0.0:2379"
   quota-backend-bytes = 8589934592  # Reduce if replication is slow
   ```

#### **Fix Example (Force Sync on Standby)**
For PostgreSQL:
```sql
-- Run this on the standby before failover
SELECT pg_rewind take backup;
pg_rewind (slave_connection_string, target_connection_string, options);
```

---

### **Issue 4: Failback Fails (Primary Not Recovered)**
**Symptoms:**
- Primary node recovers, but system stays in degraded mode.
- Logs show `failback_blocked` or `primary_not_resumed`.

**Root Causes:**
- **Manual intervention required** (e.g., `STOLEN` flag in ZooKeeper).
- **State not synced** (standby has newer data).
- **Misconfigured failback logic**.

#### **Debugging Steps:**
1. **Check failback logs:**
   ```bash
   grep "failback" /var/log/<service>.log
   ```
   - Look for `state_not_synced` or `manual_required`.

2. **Verify primary node status:**
   ```bash
   ETCDCTL_API=3 etcdctl endpoint status --write-out=table
   ```
   - If primary is `healthy`, check if clients are still routing to standby.

3. **Force failback (if supported):**
   ```bash
   # For Consul
   consul operator failover <node_id>
   ```

#### **Fix Example (Reset ZooKeeper State)**
If a node was forcibly removed, reset its state:
```bash
# List nodes
zkCli.sh ls /

# Remove stale node (if needed)
zkCli.sh rmr /zk_nodes/mynode
```

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Purpose** | **Example Command** |
|----------|------------|---------------------|
| **`journalctl`** | View systemd logs. | `journalctl -u <service> -f` |
| **`tcpdump`** | Capture network traffic. | `tcpdump -i eth0 port 2379` |
| **`mtr`** | Test network latency. | `mtr <cluster_node>` |
| **`ethtool`** | Check network interface status. | `ethtool -S eth0` |
| **Prometheus + Grafana** | Monitor failover metrics. | Query `up{job="failover"}` |
| **`strace`** | Debug process-level issues. | `strace -f -e trace=open,read,write /path/to/service` |
| **`iperf3`** | Test network throughput. | `iperf3 -c <node_ip> -t 30` |
| **`pg_isready` (PostgreSQL)** | Check PostgreSQL connectivity. | `pg_isready -U postgres -h <standby_ip>` |
| **`etcdctl` (etcd)** | Inspect etcd cluster state. | `ETCDCTL_API=3 etcdctl endpoint health` |

**Pro Tip:**
- Use **`failsafe`** mode in some systems (e.g., Kubernetes) to bypass failover rules temporarily:
  ```yaml
  # Kubernetes Deployment override
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: myapp
  spec:
    template:
      spec:
        containers:
        - name: myapp
          env:
          - name: FAILSAFE_ENABLED
            value: "true"
  ```

---

## **4. Prevention Strategies**
### **A. Configuration Best Practices**
1. **Set Realistic Timeouts:**
   - Heartbeat: **5-10s** (adjust based on network latency).
   - Election timeout: **2x heartbeat interval** (e.g., 20s).
   - Replication sync timeout: **3x replication lag threshold**.

2. **Use Odd-Numbered Clusters:**
   - Avoid split-brain by ensuring a quorum exists (e.g., 3, 5, 7 nodes).

3. **Enable Automatic Discovery:**
   - Use DNS SRV records or service discovery (Consul, Kubernetes Endpoints).

4. **Monitor Health Checks:**
   - Promote health checks to **`/ready`** (liveness) and **`/health`** (readiness).

5. **Test Failover Regularly:**
   - Use chaos engineering tools like **Gremlin** or **Chaos Mesh** to simulate node failures.

### **B. Code-Level Preventions**
- **Idempotent Failover Logic:**
  ```python
  # Example: Safe failover in Python (etcd client)
  import etcd

  client = etcd.Client(host='<primary_ip>')
  try:
      client.add('/health', value='ok', dir=True)  # Create if not exists
  except etcd.EtcdkeyExistsError:
      pass  # Already exists, no action needed
  ```
- **Circuit Breakers:**
  - Use **Hystrix** or **Resilience4j** to prevent cascading failures during failover.

- **Transactional Failover:**
  - Ensure no partial writes during failover (e.g., PostgreSQL’s `pg_rewind`).

### **C. Network & Infrastructure**
1. **Bond Interfaces (Multi-NIC Setup):**
   ```bash
   # Example bonding (Linux)
   cat > /etc/network/interfaces.d/eth0 <<EOF
   auto bond0
   iface bond0 inet manual
      bond-slaves eth0 eth1
      bond-mode active-backup
   EOF
   ```
2. **Use VPN for Redundancy:**
   - Deploy a **WireGuard** or **OpenVPN** overlay network between nodes.
3. **Check MTU Settings:**
   - Ensure MTU is consistent (`ip link set dev eth0 mtu 1500`).

### **D. Observability**
1. **Custom Metrics:**
   - Track `failover_latency`, `election_attempts`, `replication_lag`.
2. **Alerts:**
   - Alert on:
     - `failover_attempts > 3` (within 5 mins).
     - `health_check_failure_rate > 5%`.
3. **Distributed Tracing:**
   - Use **Jaeger** or **Zipkin** to trace requests across failover events.

---

## **5. Quick Reference Cheat Sheet**
| **Scenario** | **Immediate Fix** | **Long-Term Fix** |
|--------------|------------------|------------------|
| **Primary stuck** | Manually promote standby (`ETCDCTL_API=3 etcdctl member promote <id>`) | Increase heartbeat timeout |
| **Split-brain** | Force quorum recovery (`ETCDCTL_API=3 etcdctl member remove <rogue_node>`) | Use even-numbered cluster + split-brain mode |
| **Slow failover** | Kill stuck process (`pkill -f "replication_sync"`) | Optimize disk I/O, reduce replication lag |
| **Failback fails** | Reset node state (`zkCli.sh rmr /zk_nodes/<node>`) | Implement automatic failback logic |
| **Network flapping** | Run `tcpdump` to identify packet loss | Use bonding or VPN for redundancy |

---

## **6. Final Checklist Before Deploying Fixes**
1. [ ] **Test in staging** (simulate failover with `kill -9`).
2. [ ] **Backup data** before manual interventions.
3. [ ] **Monitor metrics** post-fix (Prometheus/Grafana).
4. [ ] **Review logs** for lingering issues.
5. [ ] **Document changes** for future troubleshooting.

---
**Debugging failover issues is often about eliminating the "blame it on the network" excuse first.** Start with **logs → network → configuration**, then refine with **metrics and tests**. If the system is complex, consider **chaos engineering** to proactively find weak points.

Would you like a deep dive into a specific failover implementation (e.g., PostgreSQL, etcd, Kubernetes)?