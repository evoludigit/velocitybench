# **Debugging Failover Setup: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **1. Introduction**
Failover systems ensure high availability (HA) by automatically switching to a backup component (e.g., database, service, or data center) when a primary fails. Misconfigured or failing failover mechanisms can lead to downtime, data inconsistency, or degraded performance.

This guide helps diagnose common failover issues efficiently, focusing on **symptoms, root causes, fixes, debugging tools, and prevention strategies**.

---

## **2. Symptom Checklist**
Use this checklist to quickly identify potential failover failures:

| **Symptom**                          | **Possible Cause**                          | **Action** |
|--------------------------------------|--------------------------------------------|------------|
| Primary node crashes without switching to backup | Failover trigger misconfigured (e.g., health checks too slow) | Check failover scripts, health endpoints, and monitoring |
| Backup node takes too long to activate | Network latency, slow DB replication, or misconfigured failover coordination | Test network, verify replication lag, and adjust failover thresholds |
| Inconsistent data after failover | Asynchronous replication delay or incorrect replication rules | Check replication logs, adjust sync mechanism |
| Failover triggers but application still fails | Application not updated to use backup endpoints | Test failover endpoint routing and DNS/PLUS |
| Backup node becomes primary but performance degrades | Underlying hardware/OS issues not detected by health checks | Add OS-level monitoring (e.g., disk I/O, memory) |
| Failover triggers on false positives (e.g., temporary network blip) | Aggressive health check thresholds | Adjust health check thresholds or add hysteresis |
| Manual failover fails ("command not found" or timeout) | Incorrect failover command execution permissions or dependencies | Check permissions, environment variables, and logs |
| DNS or service discovery fails to update IP on failover | Misconfigured DNS failover or service mesh (e.g., Consul, Kubernetes Endpoints) | Verify DNS TTL, service mesh updates, and load balancer health checks |

---

## **3. Common Issues and Fixes**

### **A. Failover Trigger Not Firing**
**Symptom:** Primary node crashes, but backup does not take over.

#### **Root Causes & Fixes**
1. **Health Check Misconfiguration**
   - Health checks may be too slow (e.g., HTTP endpoint returns `200` even when dead).
   - **Fix:** Use a fast health check (e.g., `/healthz` with a 1-second timeout) and adjust retry logic.
     ```bash
     # Example: Fast health check (Node.js)
     app.use((req, res) => {
       if (process.healthCheck()) res.sendStatus(200);
       else res.sendStatus(503);
     });
     ```

   - **Debug:** Check health check logs:
     ```bash
     # Example: Verify health check in Kubernetes
     kubectl logs <pod> | grep "healthCheck"
     ```

2. **Monitoring System Not Notifying Failover Script**
   - Tools like Prometheus, Nagios, or custom scripts may not trigger failover.
   - **Fix:** Ensure monitoring sends alerts to the failover orchestrator (e.g., via Slack + webhook).
     ```yaml
     # Example: Prometheus alert rule (alertmanager.yml)
     - alert: NodeDown
       expr: up{job="my-app"} == 0
       for: 5s
       labels:
         severity: critical
       annotations:
         summary: "Instances of {{ $labels.instance }} are down"
         command: "/path/to/failover-script.sh"
     ```

3. **Script/Command Not Executed**
   - Failover script may fail silently (e.g., missing permissions, wrong path).
   - **Fix:** Add logging and error handling:
     ```bash
     # Example: Robust failover script (Bash)
     #!/bin/bash
     set -e
     LOG_FILE="/var/log/failover.log"
     exec >> "$LOG_FILE" 2>&1

     # Check if primary is down
     if ! curl -s -o /dev/null -w "%{http_code}" http://primary:8080/healthz | grep -q "5"; then
       echo "Primary is down. Activating backup..."
       systemctl restart my-app-backup.service
     fi
     ```

---

### **B. Slow Failover Activation**
**Symptom:** Backup node activates but takes >30s to respond.

#### **Root Causes & Fixes**
1. **Database Replication Lag**
   - Async replication (e.g., PostgreSQL, MySQL) may not catch up.
   - **Fix:** Use synchronous replication or reduce failover delay:
     ```sql
     -- PostgreSQL: Enable synchronous commit
     ALTER SYSTEM SET synchronous_commit = 'on';
     ```
   - **Debug:** Check replication lag:
     ```bash
     # MySQL replication lag
     mysql -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master"
     ```

2. **Network Latency Between Nodes**
   - High latency may cause timeouts in failover coordination.
   - **Fix:** Use a geographically closer backup or increase timeouts:
     ```java
     // Java: Increase connection timeout (Netty)
     Bootstrap b = new Bootstrap()
       .group(group)
       .channel(NioServerSocketChannel.class)
       .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 10000); // 10s timeout
     ```

3. **Load Balancer Not Updating Endpoints**
   - DNS or service mesh (e.g., NGINX, AWS ALB, Istio) may not update routes fast enough.
   - **Fix:** Reduce TTL or use dynamic DNS updates:
     ```bash
     # Example: Update DNS via AWS Route53 (CLI)
     aws route53 change-resource-record-sets \
         --hosted-zone-id Z123456789 \
         --change-batch file://dns-update.json
     ```

---

### **C. Data Inconsistency After Failover**
**Symptom:** Backup node has stale data after failover.

#### **Root Causes & Fixes**
1. **Asynchronous Replication Not Fully Synced**
   - Primary may have committed transactions that haven’t replicated.
   - **Fix:** Use a **quorum-based failover** (e.g., PostgreSQL with `synchronous_commit=remote_apply`).
     ```sql
     -- PostgreSQL: Stronger replication
     ALTER SYSTEM SET wal_level = 'replica';
     ALTER SYSTEM SET synchronous_commit = 'remote_apply';
     ```

2. **Application Not Reading from Backup Correctly**
   - App may still query the old primary endpoint.
   - **Fix:** Update app config to point to backup:
     ```yaml
     # Config (e.g., Kubernetes ConfigMap)
     DB_HOST: backup-db.example.com
     ```

3. **Replication Lag During Failover**
   - Backup may lag behind by >1s, causing inconsistency.
   - **Fix:** Implement **replication lag detection** and delay failover:
     ```python
     # Python: Check replication lag before failover
     def check_replication_lag():
         lag = run_sql("SHOW SLAVE STATUS;")["Seconds_Behind_Master"]
         if lag > 1:
             raise FailoverError("Replication lag too high")
     ```

---

### **D. Manual Failover Fails**
**Symptom:** `failover.sh` or `kube-prometheus operator` fails to activate backup.

#### **Root Causes & Fixes**
1. **Permission Denied**
   - Script lacks sudo or exec rights.
   - **Fix:** Grant execute permissions:
     ```bash
     chmod +x /path/to/failover.sh
     sudo chown root:root /path/to/failover.sh
     ```

2. **Dependencies Missing**
   - Script requires tools (e.g., `curl`, `kubectl`) not installed.
   - **Fix:** Use absolute paths or install dependencies:
     ```bash
     # Ensure kubectl is in PATH
     export PATH=$PATH:/usr/local/bin/kubectl
     ```

3. **Race Condition in Service Orchestration**
   - Kubernetes/Pod may not be ready when failover triggers.
   - **Fix:** Use readiness probes and retries:
     ```yaml
     # Kubernetes Deployment with readiness probe
     readinessProbe:
       httpGet:
         path: /healthz
         port: 8080
       initialDelaySeconds: 5
       periodSeconds: 10
     ```

---

## **4. Debugging Tools and Techniques**

| **Tool/Technique**          | **Use Case**                                  | **Example Command/Config** |
|-----------------------------|-----------------------------------------------|----------------------------|
| **Logging**                 | Track failover script execution.             | `exec >> /var/log/failover.log 2>&1` |
| **Health Checks**           | Verify primary/backup health.                | `curl -w "%{http_code}" http://primary/healthz` |
| **Replication Lag Checks**  | Detect async DB replication issues.          | `SHOW SLAVE STATUS` (MySQL) |
| **Network Traceroute**      | Identify latency between nodes.              | `traceroute backup-db.example.com` |
| **Load Balancer Logs**      | Debug DNS/service mesh failures.             | `kubectl logs -n kube-system <ingress-controller-pod>` |
| **Distributed Tracing**    | Track request flow during failover.          | Jaeger/Zipkin (add to app) |
| **Chaos Engineering**       | Test failover under load.                    | Gremlin/Chaos Mesh (kill primary node) |
| **Metrics Monitoring**      | Detect failover anomalies (e.g., high latency). | Prometheus + Grafana (alert on `failover_duration > 5s`) |

---
## **5. Prevention Strategies**

### **A. Configuration Best Practices**
1. **Health Checks**
   - Use **short-lived, fast checks** (e.g., `/healthz` with 1s timeout).
   - Example: [Health Check Best Practices (AWS)](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/configuring-health.html).

2. **Replication**
   - Prefer **synchronous replication** (e.g., PostgreSQL `synchronous_commit=on`).
   - For async, **monitor lag** and delay failover if lag > X ms.

3. **Failover Orchestration**
   - Use **idempotent failover scripts** (can run multiple times safely).
   - Example:
     ```bash
     # Idempotent failover (Bash)
     if ! systemctl is-active --quiet my-app-backup; then
       systemctl start my-app-backup
     fi
     ```

### **B. Testing Failover**
1. **Chaos Testing**
   - Periodically **kill the primary** and verify backup activates:
     ```bash
     # Kill primary pod (Kubernetes)
     kubectl delete pod primary-app-1
     ```
   - Use tools like:
     - [Gremlin](https://www.gremlin.com/) (for cloud environments).
     - [Chaos Mesh](https://chaos-mesh.org/) (Kubernetes-native).

2. **Load Testing**
   - Simulate **high traffic** before failover:
     ```bash
     # Locust load test
     locust -f load_test.py --host=http://primary:8080 --headless -u 1000 -r 100
     ```

### **C. Monitoring and Alerts**
1. **Failover Metrics**
   - Track:
     - `failover_duration` (time to switch).
     - `replication_lag` (DB sync delay).
     - `health_check_failures` (primary/backup issues).
   - Example Prometheus alert:
     ```yaml
     - alert: HighReplicationLag
       expr: mysql_replication_lag > 1000
       for: 1m
       labels:
         severity: warning
     ```

2. **Automated Rollback**
   - If backup fails, **auto-roll back to primary** after 30s:
     ```bash
     # Example: Failover with timeout (Bash)
     if ! start_backup; then
       echo "Backup failed. Retrying primary..."
       systemctl restart my-app-primary.service
     fi
     ```

### **D. Documentation**
1. **Runbook**
   - Document **failover steps**, **dependencies**, and **known issues**.
   - Example:
     ```
     FAILOVER PROCEDURE:
     1. Check DB replication lag: `SHOW SLAVE STATUS`
     2. Run: `/opt/failover.sh --backup=backup-db.example.com`
     3. Verify: `kubectl get pods -l app=my-app`
     ```

2. **Post-Failover Checks**
   - List of **verification commands** to run after failover:
     ```bash
     # Post-failover checks
     curl http://backup:8080/healthz
     pg_isready -h backup-db
     kubectl describe pod backup-app-1
     ```

---

## **6. Quick Resolution Cheat Sheet**
| **Issue**                     | **Immediate Fix**                          | **Long-Term Fix**                     |
|-------------------------------|--------------------------------------------|---------------------------------------|
| Failover trigger not firing   | Check health check logs                     | Reduce health check timeout           |
| Slow DB replication           | Promote secondary ASAP                     | Switch to synchronous replication     |
| DNS not updating               | Manually update DNS (TTL=0)                | Use dynamic DNS (Route53, Cloudflare)  |
| Application still using primary| Update app config to backup endpoint      | Use service mesh (Istio, Linkerd)     |
| Failover script fails         | Run manually to debug (`sudo /path/to/script.sh`) | Add error logging and retries     |

---

## **7. Conclusion**
Failover debugging requires a **systematic approach**:
1. **Identify symptoms** (logs, metrics, application behavior).
2. **Check dependencies** (health checks, replication, networking).
3. **Test fixes incrementally** (e.g., reduce TTL, restart services).
4. **Prevent recurrence** (chaos testing, idempotent scripts, monitoring).

By following this guide, you can **resolve failover issues in minutes** rather than hours. Always **document lessons learned** to improve future failover reliability.

---
**Further Reading:**
- [PostgreSQL Replication Tuning](https://www.postgresql.org/docs/current/wal-shipping.html)
- [Kubernetes Failover with PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb/)
- [Chaos Engineering Handbook](https://www.chaosengineering.io/handbook/)