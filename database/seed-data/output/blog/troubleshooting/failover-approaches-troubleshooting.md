# **Debugging Failover Approaches: A Troubleshooting Guide**
*For senior backend engineers diagnosing and resolving failover-related system failures*

---

## **1. Introduction**
Failover mechanisms ensure high availability by automatically rerouting traffic from a failed primary component to a standby backup. Failures in failover can lead to cascading outages, degraded performance, or extended downtime.

This guide provides a structured approach to diagnosing failover-related issues, including common failure modes, debugging tools, and preventive measures.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these common failover-related symptoms:

✅ **Primary Node Unresponsive**
   - Is the primary server down? (Check health checks, logs, or monitoring alerts.)
   - Are external dependencies (e.g., databases, APIs) failing?

✅ **Failover Triggered but Failed**
   - Did the failover script/agent execute?
   - Is the standby node taking over, or is it failing silently?
   - Are there error logs indicating the standby node cannot assume the primary role?

✅ **Traffic Not Redirected Properly**
   - Load balancers/DNS not routing to the standby node.
   - Application-level checks not detecting the failure.

✅ **Performance Degradation**
   - Standby node is underperforming (memory, CPU, disk bottlenecks).
   - Database replication lag causing stale data.

✅ **Recurring Failovers (Pinging Pong)**
   - Is the primary node intermittently failing due to network issues?
   - Are health checks too sensitive, causing unnecessary failovers?

✅ **Logs Indicate Failover Attempts**
   - Check application, infrastructure, and monitoring logs for failover-related errors.

---

## **3. Common Issues and Fixes**

### **Issue 1: Failover Script/Orchestrator Fails to Execute**
**Symptoms:**
- Primary node crashes, but failover agent does not trigger.
- No logs indicating a failover attempt.

**Root Causes:**
- **Permissions issue:** The failover user lacks sudo or execution rights.
- **Script misconfiguration:** Failover script is not monitored, or health checks are incorrect.
- **Network isolation:** Agent cannot reach the standby node.

**Debugging Steps & Fixes:**

#### **3.1.1 Verify Script Execution**
```bash
# Test if the failover script runs manually
sudo -u failover_user /path/to/failover_script.sh

# Check for errors
sudo -u failover_user /path/to/failover_script.sh 2>&1 | grep -i "error"
```

**Fix:**
- Ensure the script has execute permissions:
  ```bash
  chmod +x /path/to/failover_script.sh
  ```
- Grant necessary permissions:
  ```bash
  sudo usermod -aG sudo failover_user
  ```

#### **3.1.2 Log Failover Attempts**
Modify the script to log execution attempts:
```bash
#!/bin/bash
LOG_FILE="/var/log/failover.log"

echo "$(date) - Attempting failover" >> "$LOG_FILE"

# Health check
if ! curl -s http://primary-node:8080/health | grep -q "OK"; then
    echo "$(date) - Primary down, initiating failover" >> "$LOG_FILE"

    # Promote standby
    sudo systemctl restart standby-service

    echo "$(date) - Failover initiated" >> "$LOG_FILE"
else
    echo "$(date) - Primary healthy" >> "$LOG_FILE"
fi
```

**Fix:**
- Check logs for missing entries:
  ```bash
  tail -f /var/log/failover.log
  ```

---

### **Issue 2: Standby Node Rejects Primary Promotion**
**Symptoms:**
- Failover script runs, but the standby node fails to take over.
- Logs show `Promotion failed: Lock already held`.

**Root Causes:**
- **Database replication lag:** Standby is not up-to-date.
- **Lock conflict:** Another instance is already primary.
- **Misconfigured failover script:** Incorrect role assignment.

**Debugging Steps & Fixes:**

#### **3.2.1 Check Database Replication Status**
```bash
# For PostgreSQL/MySQL, verify replication lag
psql -U postgres -c "SELECT pg_is_in_recovery() as is_replica;"
# Should return false for standby before promotion.

# Check replication lag (if applicable)
mysql -u root -e "SHOW SLAVE STATUS\G" | grep "Seconds_Behind_Master"
```

**Fix:**
- Ensure replication is healthy before failover.
- If lag exists, pause replication temporarily:
  ```bash
  # For MySQL
  mysql -u root -e "STOP SLAVE;"

  # For PostgreSQL (if using logical replication)
  pg_ctl stop -D /var/lib/postgresql/standby_data
  ```

#### **3.2.2 Verify Role Assignment**
```bash
# Check if the standby is correctly identified
psql -U postgres -c "SELECT pg_is_in_recovery() as is_replica;"
# Should return true for standby.

# If not, manually assign role (example for PostgreSQL)
sed -i 's/primary_slot_name=.*/primary_slot_name=my_slot/' /etc/postgresql/postgresql.conf
systemctl restart postgres
```

**Fix:**
- Ensure the failover script correctly checks and updates roles:
  ```bash
  # Example: Force role change (PostgreSQL)
  sudo -u postgres psql -c "ALTER SYSTEM SET wal_level = replica;"
  sudo systemctl restart postgres
  ```

---

### **Issue 3: Load Balancer/DNS Not Redirecting Traffic**
**Symptoms:**
- Failover completes, but users still hit the failed primary.
- No traffic reaches the standby node.

**Root Causes:**
- **Hairpin routing issue:** Load balancer stuck on primary.
- **DNS TTL too high:** Cached DNS records override new endpoints.
- **Health check misconfiguration:** LB considers standby unhealthy.

**Debugging Steps & Fixes:**

#### **3.3.1 Check Load Balancer Health Checks**
```bash
# Example: Check Nginx health checks
nginx -T | grep "server"
# Verify health check URL is correct (e.g., /health).

# Test manually
curl -v http://standby-node:8080/health
```

**Fix:**
- If health check fails, adjust in LB config (e.g., AWS ALB, Nginx):
  ```nginx
  upstream backend {
      server primary-node:8080 max_fails=3 fail_timeout=30s;
      server standby-node:8080 max_fails=3 fail_timeout=30s;
      health_check path=/health interval=5s;
  }
  ```

#### **3.3.2 Verify DNS Propagation**
```bash
# Check current DNS record
dig +short failover-service.example.com

# Test standby node resolution
dig +short standby-node.example.com

# Force refresh (if using local DNS cache)
echo "flush" | nslookup
```

**Fix:**
- Reduce TTL or use a dynamic DNS provider.
- Force manual DNS update:
  ```bash
  dig +short failover-service.example.com +nocmd > /etc/hosts
  ```

---

### **Issue 4: Recurring Failovers (Thundering Herd)**
**Symptoms:**
- Primary node crashes, standby takes over, then primary recovers but traffic shifts back.
- High latency spikes during failover cycles.

**Root Causes:**
- **Sensitive health checks:** Node considered healthy when still recovering.
- **Race condition in failover:** Multiple nodes competing for primary role.
- **Resource starvation:** Primary node crashes due to high load.

**Debugging Steps & Fixes:**

#### **3.4.1 Adjust Health Check Thresholds**
```bash
# Example: Increase failover delay in Kubernetes
kubectl edit svc my-service
# Set `readinessProbe.failureThreshold: 5`
```

**Fix:**
- Implement **graceful degradation**:
  ```bash
  # Example: Node reports degraded state before failing
  if [[ $(free -m | awk '/Mem:/ {print $3}') -lt 1024 ]]; then
      echo "Low memory, marking as degraded" > /var/status
  fi
  ```

#### **3.4.2 Prevent Race Conditions**
- Use **leader election** (e.g., ZooKeeper, Consul) to ensure only one node promotes.
- Example with Consul:
  ```bash
  consul lock -name=primary-lock -key=my-service
  ```

---

## **4. Debugging Tools and Techniques**

### **4.1 Monitoring and Logging**
| Tool               | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Prometheus + Grafana** | Track failover metrics (latency, error rates, node health).           |
| **ELK Stack (Elasticsearch, Logstash, Kibana)** | Aggregate logs for failover events.       |
| **Datadog/New Relic** | APM for real-time failover detection.                                  |
| **journalctl**      | Check systemd service logs.                                             |
| **tcpdump/wireshark** | Inspect network traffic during failover.                                |

**Example Prometheus Query:**
```promql
# Detect failover events (if logging to Prometheus)
count_over_time({job="failover-service"}[5m]) > 0
```

---

### **4.2 Health Check Automation**
- **Synthetic Transactions:** Use tools like **New Relic Synthetics** or **Locust** to simulate failover scenarios.
- **Chaos Engineering:** Test failover with tools like **Gremlin** or **Chaos Monkey**.

**Example Locust Test:**
```python
from locust import HttpUser, task

class FailoverUser(HttpUser):
    @task
    def check_primary(self):
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                print("Primary failed, expecting failover...")
```

---

### **4.3 Infrastructure Diagnostics**
| Component          | Diagnostic Command                                  |
|--------------------|-----------------------------------------------------|
| **Database Replication** | `mysql slave status` / `pg_is_in_recovery()`      |
| **Network Connectivity** | `ping`, `mtr`, `telnet`                             |
| **Process Health**      | `systemctl status`, `ps aux | grep <service>`    |
| **Disk I/O**           | `iostat -x 1`, `dmesg | grep -i error`         |

**Example Disk Check:**
```bash
# Check for disk errors
dmesg | grep -i error
# Check I/O latency
iostat -x 1
```

---

## **5. Prevention Strategies**

### **5.1 Design for Resilience**
✔ **Multi-Region Deployments:** Use global load balancers (AWS Global Accelerator, Cloudflare).
✔ **Automated Scaling:** Auto-scale standby nodes during traffic spikes.
✔ **Chaos Testing:** Regularly simulate failures (e.g., kill primary node).

### **5.2 Failover Script Best Practices**
```bash
#!/bin/bash
set -e  # Exit on error
LOG="/var/log/failover.log"

# 1. Check primary health (adjust threshold)
if ! curl -s http://primary-node:8080/health | grep -q "OK"; then
    echo "$(date) - PRIMARY DOWN. Initiating failover." >> "$LOG"

    # 2. Promote standby (idempotent operation)
    if ! sudo systemctl is-active --quiet standby-service; then
        sudo systemctl start standby-service
    fi

    # 3. Update external services (DNS/LB)
    sudo sed -i "s/primary-node/standby-node/" /etc/nginx/nginx.conf
    sudo systemctl reload nginx

    echo "$(date) - FAILOVER COMPLETED." >> "$LOG"
else
    echo "$(date) - PRIMARY HEALTHY." >> "$LOG"
fi
```

### **5.3 Monitoring Failover Health**
- **Alert on failover events:**
  ```yaml
  # Example Alertmanager config
  - alert: FailoverTriggered
    expr: failover_triggered{status="activated"} == 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Failover triggered on {{ $labels.instance }}"
  ```
- **Track failover downtime:**
  ```bash
  # Use Prometheus record failover duration
  record: job:failover_duration:sum:rate5m
  ```

### **5.4 Disaster Recovery Plan**
- **Regular backups:** Test failover from a known good backup.
- **Document rollback procedures:** Steps to revert to primary if standby fails.
- **Post-mortem reviews:** Analyze failover incidents for root causes.

---

## **6. Conclusion**
Failover debugging requires a structured approach:
1. **Verify symptoms** (primary down? standby unreachable?).
2. **Check logs and metrics** (Prometheus, ELK, system logs).
3. **Test fixes incrementally** (health checks, DB replication, LB config).
4. **Prevent recurrences** (chaos testing, automated scaling, monitoring).

By following this guide, you can quickly isolate and resolve failover failures while ensuring future resilience.

---
**Next Steps:**
- Run a **failover simulation** in staging.
- Set up **automated alerts** for failover events.
- Review **database replication lag** as a common failure point.