# **Debugging *Zookeeper Cluster Integration Patterns*: A Troubleshooting Guide**

## **Introduction**
Zookeeper is a distributed coordination service that ensures reliable, scalable, and fault-tolerant cluster management. However, when integrating Zookeeper into applications or infrastructure, common issues such as **performance bottlenecks, reliability failures, and scalability problems** can arise.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving Zookeeper-related issues quickly.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms to narrow down the problem:

| **Symptom**                     | **Likely Cause**                          | **Impact**                          |
|----------------------------------|-------------------------------------------|-------------------------------------|
| High latency in leader election | Slow network, oversized cluster, or weak quorum | Increased downtime during failures |
| Frequent connection drops       | Network instability, misconfigured ACLs, or ZK memory pressure | Service interruptions |
| Slow reads/writes to Zookeeper  | High client load, inefficient watchers, or garbage collection pauses | Degraded performance |
| Split-brain scenarios            | Unresponsive nodes, incorrect `tickTime`, or improper `syncLimit` | Data corruption or cluster split |
| Client timeouts (`ConnectionLossException`) | ZK server overload, DNS misconfiguration, or network firewalls | Application crashes |

---

## **2. Common Issues and Fixes**

### **Issue 1: High Latency in Leader Election**
**Symptoms:**
- Slow recovery after a node failure.
- Clients stuck waiting for leader changes.

**Root Causes:**
- Large cluster size (>5 nodes).
- Misconfigured `tickTime` or `electionAlg`.
- Network latency between nodes.

**Fixes:**

#### **A. Optimize Cluster Configuration**
```xml
<!-- Adjust these in zoo.cfg -->
tickTime=2000          # Lower values reduce election time (but risk splits)
electionAlg=3          # Use FastLeaderElection (default) for better performance
syncLimit=5            # Reduce sync delay between nodes
```
**Best Practice:** Keep `tickTime` at least **2x network latency** to avoid splits.

#### **B. Reduce Cluster Size**
- If possible, limit Zookeeper to **3-5 nodes** (odd count recommended).
- Use **non-voting observers** (`follower.readOnly=false`) for read-heavy workloads.

### **Issue 2: Frequent Connection Drops**
**Symptoms:**
- `KeeperException.ConnectionLossException` in clients.
- Logs show `SessionExpired` errors.

**Root Causes:**
- Client sessions timeout (`sessionTimeoutMs` too low).
- ZK server overloaded (high CPU/memory usage).
- Firewall blocking ZK ports (`2181` or `2888`/`3888` for quorum).

**Fixes:**

#### **A. Adjust Client & Server Timeouts**
```java
// In client configuration:
ZooKeeper zk = new ZooKeeper("zk:2181", 5000 * 3, this);
```
- **Recommended:** `sessionTimeoutMs = 3 * tickTime` (default: `12000 = 3 * tickTime=4000`).

#### **B. Monitor Server Health**
Check for high `cpuLoad` or `heapUsage` in ZooKeeper logs:
```bash
# Check ZK metrics (if running in JVM)
jcmd <PID> VM.native_memory
```
- If **OOM occurs**, increase `JVM heap` (`-Xmx`).
- If **CPU bound**, reduce client connections or add replicas.

### **Issue 3: Slow Reads/Writes**
**Symptoms:**
- `OperationTimeoutException` for long-running operations.
- High `znode` churn (frequent watch registrations).

**Root Causes:**
- Too many watchers (`WatchManager` leaks).
- Inefficient bulk operations (`create`, `delete`).
- Garbage collection pauses.

**Fixes:**

#### **A. Optimize Watcher Usage**
```java
// Bad: Unregister watchers manually
zk.unregisterWatch(path, this);

// Good: Let ZK handle cleanup (recommended)
zk.getChildren(path, true, this, null);
```

#### **B. Use Async API for Better Performance**
```java
zk.asyncDelete(path, -1, new AsyncCallback.VoidCallback() { ... }, null);
```
- Async operations **avoid blocking threads**.

#### **C. Tune Garbage Collection**
```bash
# Example JVM args for ZK
-Xms4G -Xmx4G -XX:+UseG1GC -XX:MaxGCPauseMillis=50
```
- Use **G1GC** for large heaps.

### **Issue 4: Split-Brain & Data Corruption**
**Symptoms:**
- Multiple leaders elected simultaneously.
- Inconsistent `znode` data between nodes.

**Root Causes:**
- Incorrect `tickTime` vs. network latency.
- Misconfigured `autoPurgeSnapshots`.
- Disk I/O bottlenecks.

**Fixes:**

#### **A. Ensure Proper `tickTime` & Network Sync**
```xml
# In zoo.cfg
tickTime=2000
initLimit=10       # Allow 5x tickTime for initial sync
syncLimit=5        # Max allowed async reps (prevents splits)
```
**Rule of Thumb:**
- `tickTime >= 2 * networkLatency`
- `initLimit >= 10` (default: `10 * tickTime`)

#### **B. Disable Auto-Purge (if needed)**
```bash
# If snapshots are critical, disable auto-purge:
echo "autoPurgeSnapshots=false" >> conf/zoo.cfg
```

---

## **3. Debugging Tools & Techniques**

### **A. Built-in Monitoring**
- **Zookeeper CLI (`zkCli.sh`)**
  ```bash
  ./bin/zkCli.sh -server localhost:2181
  ls /      # List znodes
  stat /    # Check metadata
  ```
- **JMX Monitoring**
  Exposes metrics like:
  - `zookeeper.server1.znodeCount`
  - `zookeeper.server1.ephemeralCount`
  - `zookeeper.server1.outstandingRequests`

### **B. Log Analysis**
- Check for **errors in `zoo_log`**:
  ```log
  ERROR [SyncRequestProcessor-0:ZooKeeperServer@123] - Unexpected exception
  java.lang.OutOfMemoryError: Java heap space
  ```
- **Enable DEBUG logging** (`-Djava.util.logging.config.file=logging.properties`):
  ```properties
  handlers=java.util.logging.ConsoleHandler
  .level=FINE
  ```

### **C. Network Diagnostics**
- **Check latency between nodes**:
  ```bash
  ping <zk_node_ip>   # Check RTT
  telnet <zk_node> 2181  # Verify port connectivity
  ```
- **Use `nc` for port testing**:
  ```bash
  nc -zv localhost 2181
  ```

### **D. Performance Profiling**
- **JVM Flight Recorder (JFR)**
  ```bash
  jcmd <PID> JFR.start duration=60s filename=zk_profile.jfr
  ```
- **Netdata / Prometheus** for real-time metrics.

---

## **4. Prevention Strategies**

### **A. Cluster Best Practices**
✅ **Keep cluster size odd (3-5 nodes).**
✅ **Use non-voting observers** for read scaling.
✅ **Monitor `znode` churn** (avoid excessive watches).
✅ **Enable `autoPurgeSnapshots`** (unless critical data is stored).

### **B. Configuration Checklist**
```xml
# zoo.cfg recommendations
tickTime=2000
initLimit=10
syncLimit=5
maxClientCnxns=0       # Unlimited (or set high)
autopurge.snapRetainCount=3
autopurge.purgeInterval=1
```

### **C. Disaster Recovery**
- **Backup snapshots manually**:
  ```bash
  cp /var/lib/zookeeper/snapshots/version-2/snapshot /backups/zk_snapshot
  ```
- **Test failover regularly**:
  ```bash
  # Kill a ZK node and verify leader election
  kill -9 $(pgrep -f "QuorumPeerMain")
  ```

---

## **Conclusion**
Zookeeper integration issues often stem from **misconfigured timeouts, network problems, or inefficient client usage**. By following this guide, you can:
✔ **Quickly identify performance bottlenecks** (latency, GC, network).
✔ **Fix reliability issues** (split-brain, connection drops).
✔ **Prevent future problems** with proper monitoring and tuning.

**Next Steps:**
1. **Start with logs** (`zkCli.sh`, JMX).
2. **Adjust timeouts & cluster size** if needed.
3. **Optimize client code** (async ops, watcher cleanup).
4. **Monitor continuously** with Netdata/Prometheus.

For severe issues, consider **hot-swapping a node** or **restarting ZK in safe mode**:
```bash
# Restart in safe mode (prevents leader election)
./bin/zkServer.sh restart -safe
```