# **Debugging Failover: A Troubleshooting Guide**
*For Senior Backend Engineers*

This guide covers systematic failover troubleshooting, focusing on **identifying, diagnosing, and resolving failures** in high-availability (HA) systems. Failovers—whether manual or automatic—can fail due to misconfigurations, dependency issues, or race conditions. This guide ensures rapid diagnosis and recovery.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the following symptoms:

| **Symptom Category**       | **Possible Indicators**                                                                 | **How to Verify**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Primary Node Failure**   | API calls time out, errors like `Service Unavailable` (503), or circuit breakers tripping. | Check health checks (`/health`), logs, and monitoring dashboards.                |
| **Failover Triggered**     | Unexpected node promotion (e.g., Kubernetes selects a new leader, ZooKeeper election). | Audit logs (`kube-apiserver`, `ZooKeeper`, or custom failover logs).               |
| **Data Inconsistency**     | Transactions fail with `duplicate entry` or stale reads.                              | Compare DB replicas (`SELECT @@hostname;`) or use tools like [Percona Toolkit](https://www.percona.com/doc/percona-toolkit/). |
| **Network Partition**      | Slow responses, TCP timeouts, or `Connection refused`.                                | Test connectivity (`ping`, `traceroute`, `telnet <port>`).                       |
| **Misconfigured Policies** | Failover fails silently or rolls back incorrectly.                                    | Review failover scripts/configs (e.g., Ansible, Kubernetes `PodDisruptionBudget`). |
| **External Dependency Fail** | Cloud provider outage, DNS failure, or database connection pool exhaustion.          | Check cloud provider status pages (`aws-status`, `azure-status`).                |

---

## **2. Common Issues & Fixes**
### **2.1. Failover Not Triggering**
**Symptoms:**
- Primary node fails, but no backup is promoted.
- Logs show no failover event (e.g., no entries in `failover.log`).

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     | **Example Code Snippet**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Health check threshold misconfigured** | Ensure `max-failures` and `period` in health checks are set correctly.               | **Kubernetes Liveness Probe:**<br>`livenessProbe:<br>httpGet:<br>path: /health<br>port: 8080<br>failureThreshold: 3` |
| **No failover script executed**    | Verify cron jobs (`cron`/`systemd`) or Kubernetes `Job` for failover scripts run.         | **Bash Failover Script:**<br>`#!/bin/bash`<br>`if ! curl -s http://primary:8080/health | grep -q "OK"; then<br>`    kubeectl patch svc primary -p '{"spec":{"selector":{"role":"backup"}}'`;<br>`fi` |
| **ZooKeeper/Kafka leader election stuck** | Check for quorum loss or election timeouts.              | **ZooKeeper Debug:**<br>`zkCli.sh -server localhost:2181 ls /<br>echo stat | grep "mode"`<br>If stuck, restart a follower: `zkServer.sh restart` |

---

### **2.2. Failover Partially Successful**
**Symptoms:**
- Backup node takes over but **data is inconsistent** (e.g., missing transactions).
- Some services fail to start (e.g., DB replicas lag).

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     | **Example Code Snippet**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Replica lag in DB (e.g., MySQL, MongoDB)** | Check replication status and increase `binlog` retention.                  | **MySQL Check Replication:**<br>`SHOW SLAVE STATUS\G;<br>SET GLOBAL sql_slave_skip_counter = 1;` (if needed)<br>**MongoDB ReplayOps:**<br>`mongos --replSetConfigFile rs.conf.js --oplogReplay` |
| **Application not synchronized**  | Ensure stateful services (e.g., Redis Sentinel) flush cache before failover.           | **Redis Sentinel Failover:**<br>`sentinel failover <master-id>`<br>Check logs for `role change`. |
| **Network split-brain**            | Use `split-brain` prevention (e.g., Kafka `unclean.leader.election.enable=false`).      | **Kafka Config (`server.properties`):**<br>`unclean.leader.election.enable=false` |

---

### **2.3. Failover Rolls Back Unexpectedly**
**Symptoms:**
- Backup node fails, and primary is restored automatically.
- Logs show `failback` events without manual intervention.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     | **Example Code Snippet**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Health check false positive**    | Adjust thresholds or add custom metrics (e.g., `Prometheus` alerts).             | **Prometheus Alert Rule:**<br>`alert: HighLatency<br>expr: http_request_duration_seconds{quantile="0.99"} > 2<br>for: 5m<br>labels:`<br>severity: warning` |
| **Manual rollback trigger**        | Check for admin scripts (e.g., `kubectl rollout undo`).                                  | **Prevent Unauthorized Rollbacks:**<br>Add RBAC restrictions:<br>`apiVersion: rbac.authorization.k8s.io/v1<br>kind: Role<br>metadata: name: failover-admin<br>rules:<br>- apiGroups: ["apps"]<br> resources: ["deployments"]<br> verbs: ["get", "patch"]` |
| **Circuit breaker tripping**      | Reset circuit breakers manually or adjust thresholds.                                      | **Resilio (Java):**<br>`CircuitBreaker.reset();` (Hystrix/Resilience4j)               |

---

### **2.4. Data Loss During Failover**
**Symptoms:**
- Transactions are lost after failover.
- `PRIMARY_HAS_BEEN_RESTORED` errors in MySQL.

**Root Causes & Fixes:**
| **Cause**                          | **Fix**                                                                                     | **Example Code Snippet**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **In-flight transactions not committed** | Enable `binlog` transactions (MySQL) or use WAL (PostgreSQL).               | **MySQL Config (`my.cnf`):**<br>`[mysqld]<br>binlog_format=ROW<br>binlog_row_image=FULL` |
| **Async replica lag**              | Use synchronous replication or `GROUP_REPLICATION` (MySQL).                             | **MySQL GROUP_REPLICATION:**<br>`CHANGE MASTER TO MASTER_HOST='backup';<br>START GROUP_REPLICATION;` |
| **Cassandra hinted handoff failures** | Check `nodetool status` for `UN` (down) nodes.                                           | **Cassandra Repair:**<br>`nodetool repair`<br>`nodetool cleanup` (if needed)          |

---

## **3. Debugging Tools & Techniques**
### **3.1. Log Analysis**
- **Key Logs to Check:**
  - **Kubernetes:** `kubelet`, `kube-controller-manager`, `etcd`
  - **Databases:** `mysql`, `postgresql`, `cassandra`
  - **Orchestration:** `ZooKeeper`, `Consul`, `etcd`
  - **Failover Scripts:** Custom scripts, Ansible Playbooks.

- **Tools:**
  - **ELK Stack** (Elasticsearch + Logstash + Kibana) for centralized logging.
  - **Fluentd** for real-time log forwarding.
  - **Grep/Firehydrant** for ad-hoc log searches:
    ```bash
    # Find failover-related errors in logs
    grep -r "failover|rollback" /var/log/
    ```

### **3.2. Network Diagnostics**
| **Tool**       | **Command**                                                                 | **Purpose**                          |
|----------------|-----------------------------------------------------------------------------|--------------------------------------|
| `ping`         | `ping primary-node`                                                       | Check ICMP reachability.            |
| `telnet`       | `telnet primary 3306`                                                    | Test TCP connectivity to DB port.   |
| `mtr`          | `mtr --report google.com`                                                 | Trace route + packet loss.           |
| `nc -zv`       | `nc -zv backup-node 8080`                                                 | Check if port is open.              |
| `dig`          | `dig @8.8.8.8 failover.example.com`                                        | Verify DNS resolution.               |

### **3.3. Performance Profiling**
- **Database:**
  - **MySQL:** `SHOW PROCESSLIST;`, `pt-query-digest`.
  - **PostgreSQL:** `pg_stat_activity`, `EXPLAIN ANALYZE`.
- **Application:**
  - **Java:** Async Profiler, YourKit.
  - **Go:** `pprof` (built-in).
  - **Python:** `cProfile`.

### **3.4. Chaotic Testing (Prevent Failovers)**
- **Tools:**
  - **Chaos Mesh** (Kubernetes-native chaos engineering).
  - **Gremlin** (manually inject failures).
  - **Killing Pods:**
    ```bash
    # Simulate node failure
    kubectl delete pod -n failover-test primary-pod --grace-period=0 --force
    ```

### **3.5. Metrics & Alerts**
- **Essential Metrics:**
  - **Replication Lag** (DB `Seconds_Behind_Master`).
  - **Leader Election Time** (ZooKeeper/Kafka).
  - **Circuit Breaker State** (Hystrix/Resilience4j).
- **Alerting Rules (Prometheus):**
  ```yaml
  # Alert if replication lag > 10s
  alert: HighReplicationLag
  expr: mysql_replication_lag_seconds > 10
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "MySQL replica {{ $labels.instance }} is lagging by {{ $value }}s"
  ```

---

## **4. Prevention Strategies**
### **4.1. Design-Time Mitigations**
| **Strategy**                          | **Implementation**                                                                 | **Tools/Examples**                                                                 |
|---------------------------------------|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Multi-AZ Deployments**              | Deploy primary and backup in different availability zones.                         | AWS: `us-west-2a` (primary), `us-west-2b` (backup).                              |
| **Active-Active vs. Active-Passive**  | Use active-active for low-latency apps (e.g., Kafka, Redis Cluster).              | **Kafka:** Enable `min.insync.replicas=2`.                                         |
| **Automated Promotions**              | Use built-in failover (e.g., PostgreSQL `pg_ctl promote`).                          | **PostgreSQL:**<br>`pg_ctl promote -D /var/lib/postgresql/data`                     |
| **Graceful Degradation**              | Stagger failover steps (e.g., shut down services before promoting).               | **Kubernetes:**<br>`kubectl scale deployment --replicas=0 primary` (drain first). |

### **4.2. Runtime Safeguards**
| **Strategy**                          | **Implementation**                                                                 | **Example**                                                                         |
|---------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Health Check Throttling**           | Avoid rapid failovers by introducing delays.                                         | **Custom Health Check:**<br>`if (retry_count > 3) { sleep(60); }`                  |
| **Write-Ahead Logging (WAL)**         | Ensure no data loss during crashes (e.g., PostgreSQL `fsync`).                      | **PostgreSQL Config (`postgresql.conf`):**<br>`fsync = on`<br>`sync_interval = 1s`  |
| **Automated Rollback Testing**        | Simulate rollbacks in staging before production.                                     | **Terraform Plan:**<br>`terraform plan -out=tf.plan`<br>`terraform apply -auto-approve -input=false tf.plan` |
| **Immutable Infrastructure**           | Treat failover as a redeploy (e.g., Kubernetes `Deployment` instead of `StatefulSet`). | **Kubernetes:**<br>Use `Deployment` + `PodDisruptionBudget` instead of `StatefulSet`. |

### **4.3. Post-Failover Checks**
1. **Verify Data Consistency:**
   ```sql
   -- MySQL: Compare row counts
   SELECT COUNT(*) FROM table1;
   -- Compare across replicas
   ```
2. **Test Transactions:**
   - Run a write-heavy load (e.g., `wrk`) and check for duplicates.
3. **Monitor Metrics:**
   - Ensure replication lag is <1s (adjust thresholds if needed).
4. **Update Configs:**
   - If failover was manual, document the steps for future use.

---

## **5. Quick Reference Cheat Sheet**
| **Scenario**               | **Immediate Action**                          | **Long-Term Fix**                          |
|----------------------------|-----------------------------------------------|--------------------------------------------|
| **Primary Node Down**      | Promote backup (if auto-failover not working). | Increase health check `failureThreshold`.  |
| **Data Inconsistency**     | Restore from backup (last known good state). | Enable binary logging (`binlog`) in DB.    |
| **Network Partition**      | Isolate faulty nodes; retry later.           | Use VPC peering or transit gateways.       |
| **Slow Failover**          | Check ZooKeeper/Kafka election logs.         | Increase `election.algorithms.timeout.ms`. |
| **Rollback Happens**       | Manually inspect DB for corruption.          | Add RBAC to prevent unauthorized rollbacks.|

---

## **6. Final Checklist Before Production**
✅ **Failover Tested in Staging:**
- Simulate node failures, network splits, and DB outages.
- Verify metrics/alerts trigger correctly.

✅ **Rollback Plan Documented:**
- Steps to revert failover (e.g., `kubectl rollout undo`).
- Contact list for on-call engineers.

✅ **Monitoring in Place:**
- Prometheus/Grafana dashboards for replication lag.
- SLOs for RTO (Recovery Time Objective) and RPO (Recovery Point Objective).

✅ **Automation Scripts Idempotent:**
- Failover scripts should handle retries and idempotency.

---
**Next Steps:**
1. **For Immediate Issues:** Use the symptom checklist to narrow down the root cause.
2. **For Recurring Issues:** Audit configs and monitoring thresholds.
3. **For Prevention:** Implement the prevention strategies above.