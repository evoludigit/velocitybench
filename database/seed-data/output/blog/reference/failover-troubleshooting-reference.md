# **[Pattern] Failover Troubleshooting Reference Guide**

---

## **Overview**
The **Failover Troubleshooting** pattern ensures system resilience by diagnosing and resolving failures when a primary component (e.g., a service, database, or node) transitions to a backup (secondary) component. This guide outlines key concepts, diagnostic approaches, and best practices for identifying root causes of failover failures, verifying secondary components, and restoring full functionality. Adaptable to cloud, on-premises, or hybrid architectures, this pattern applies to services like databases (PostgreSQL, Kubernetes), microservices, and distributed systems.

---

## **Key Concepts & Schema Reference**

### **1. Core Components**
| **Component**       | **Description** | **Failure Indicators** |
|---------------------|----------------|-----------------------|
| **Primary Service** | The active instance (e.g., database, API). | Unresponsive, latency spikes, connection timeouts. |
| **Secondary Service** | Standby/backup instance. | Not promoted, data drift, slower performance. |
| **Failover Trigger** | Event causing transition (e.g., health checks, manual intervention). | Misconfigured thresholds, missing alerts. |
| **Failover Agent** | Software/hardware managing switchover (e.g., Kubernetes `Service`/`Pod`, PostgreSQL `pg_promote`). | Agent frozen, misconfigured policies. |
| **Monitoring & Alerts** | Tools tracking health and failover status (e.g., Prometheus, Datadog). | Missing logs, false negatives. |
| **Recovery Process** | Steps to restore primary functionality post-failover. | Manual overrides required, incomplete rollback. |

---

### **2. Failover States & Validation Schema**
| **State**          | **Definition** | **Validation Checks** |
|--------------------|----------------|-----------------------|
| **Healthy (Active)** | Primary is operational. | `Status: Active`, `Latency: < X ms`, `Replication Lag: 0`. |
| **Degraded** | Partial failure (e.g., one node down). | `Component Status: Degraded`, `Alerts: High`. |
| **Failover Initiated** | Transition in progress. | `Primary: Pending`, `Secondary: Promoting`, `Logs: Transition Log`. |
| **Failed Failover** | Switchover aborted/partially completed. | `Primary: Still Active`, `Secondary: Unreachable`, `Agent Logs: Error`. |
| **Post-Failover** | Secondary is now primary. | `New Primary: Active`, `Old Primary: Standby`, `Data Sync: Complete`. |

---

### **3. Troubleshooting Workflow**
1. **Identify Failure**:
   - Check system logs (`journalctl -u <service>`, Kubernetes `kubectl logs`).
   - Review monitoring dashboards (e.g., Grafana alerts).
2. **Verify Failover Trigger**:
   - Confirm the event (e.g., `kubectl get events` for Kubernetes).
   - Audit failover policies (e.g., `configmaps` in Kubernetes, `replication_slots` in PostgreSQL).
3. **Inspect Secondary Component**:
   - **Connectivity**: Test network paths (e.g., `ping`, `telnet`, `nc -zv`).
   - **Data Consistency**: Compare primary/secondary data (e.g., `pg_isready -U user -h secondary-host`).
   - **Agent Status**: Check failover agent health (e.g., `etcdctl endpoint health` for Kubernetes).
4. **Resolve Root Cause**:
   - **Common Causes**:
     - Network partitions (e.g., `iptables` misconfiguration).
     - Corrupted secondary state (e.g., PostgreSQL `pg_ctl promote` failure).
     - Resource exhaustion (e.g., `OOMKilled` in containers).
   - **Mitigations**:
     - Restart failed components (`kubectl rollout restart deployment`).
     - Reinitialize secondary (`pg_basebackup` for PostgreSQL).
5. **Restore Primary**:
   - Promote secondary (e.g., `kubectl patch svc <service> -p '{"spec":{"selector":{"role":"primary"}}'}`).
   - Validate replication (`SELECT * FROM pg_stat_replication;`).
6. **Document & Retest**:
   - Update runbooks with fixes.
   - Simulate failover (`kubectl patch svc --dry-run`).

---

## **Query Examples**

### **1. Kubernetes Failover Debugging**
```bash
# Check failover events (Pod evictions)
kubectl get events --sort-by='.metadata.creationTimestamp' -A

# Verify Service selector (ensure 'role=primary' is active)
kubectl describe svc <service-name> | grep -i selector

# Inspect Pod readiness
kubectl get pods -l app=<app-name> --show-labels
```

### **2. PostgreSQL Failover Checks**
```sql
-- Check replication status
SELECT * FROM pg_stat_replication;

-- Verify primary connection
pg_isready -U replica_user -h primary-host;

-- Restart replication (if lagged)
SELECT pg_promote();
```

### **3. Monitoring Alerts (Prometheus)**
```promql
# Alert for failover timeout (e.g., >30s)
up{job="postgres"} == 0 or on() (up{job="postgres"} - up{job="postgres-replica"}) == 1
```

### **4. Network Troubleshooting**
```bash
# Test connectivity between nodes
ping <primary-ip>
telnet <primary-ip> 5432  # For PostgreSQL port

# Check firewall rules
sudo iptables -L -n
```

---

## **Implementation Best Practices**
1. **Automate Validation**:
   - Use **liveness/readiness probes** in Kubernetes (`initialDelaySeconds: 30`, `failureThreshold: 3`).
   - Implement **health checks** in application code (e.g., `/health` endpoint).
2. **Log Correlate Failovers**:
   - Tag logs with `failover_id` for traceability.
   - Example: `logging: { driver: "json-file", format: "{ 'failover_id': '${FAILOVER_ID}', 'message': '%{message}' }" }`.
3. **Test Failovers Regularly**:
   - Schedule **chaos engineering** (e.g., using **Chaos Mesh** in Kubernetes).
   - Example: `chaos mesh apply -f kill-pod.yaml --namespace=production`.
4. **Document Runbooks**:
   - Include **step-by-step failover commands** and **known issues**.
   - Example:
     ```markdown
     ### PostgreSQL Failover Runbook
     1. `sudo su - postgres`
     2. `pg_ctl promote`
     3. `systemctl restart postgresql`
     ```
5. **Optimize Recovery Time**:
   - **Minimize replication lag** (tune `wal_level`, `synchronous_commit` in PostgreSQL).
   - **Use geo-redundancy** for cloud failovers (e.g., AWS Multi-AZ, GCP Regional Persistent Disk).

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Integration Points**                     |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **[Circuit Breaker](https://example.com/circuit-breaker)** | Prevent cascading failures during recovery.                                | `failover_timeout` in `Hystrix`/`Resilience4j`. |
| **[Blue-Green Deployment](https://example.com/blue-green)** | Zero-downtime failover for application updates.                            | Kubernetes `Service` with `externalName`. |
| **[Multi-Region Replication](https://example.com/multi-region)** | Global failover resilience.                                                  | AWS Global Accelerator, Kafka MirrorMaker. |
| **[Chaos Engineering](https://example.com/chaos)**            | Proactively test failover resilience.                                        | Chaos Mesh, Gremlin.                      |
| **[Idempotent Operations](https://example.com/idempotent)**   | Ensure safe failover rollback.                                              | Database transactions, AWS Step Functions. |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|--------------------------------------------------------------------------------|
| **Overlapping failover windows**      | Use **canary failovers** (gradual rollout).                                    |
| **Data drift between primary/secondary** | Enable **continuous replication** (e.g., PostgreSQL `logical replication`).  |
| **Failover agent race conditions**    | Implement **locking mechanisms** (e.g., `etcd` for Kubernetes).              |
| **Undetected secondary failures**     | Add **heartbeat checks** (e.g., Heartbeat service in Linux HA).               |
| **Manual intervention required**      | Automate with **Terraform/Ansible** playbooks.                                |

---
**See Also**:
- [Kubernetes Failover Docs](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-control-plane)
- [PostgreSQL High Availability Guide](https://www.postgresql.org/docs/current/high-availability.html)