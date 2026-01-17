# **Debugging *On-Premise Setup*: A Troubleshooting Guide**

## **Introduction**
Deploying applications and services on-premises requires careful configuration of infrastructure, networking, security, and application layers. Unlike cloud-based setups, on-premise environments introduce complexities like hardware dependencies, localized network constraints, and legacy system integrations.

This guide provides a **structured debugging approach** for common issues in on-premise deployments. We’ll cover **symptom identification, root-cause analysis, code-based fixes, debugging tools, and preventive measures** to minimize downtime and improve reliability.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically verify the following symptoms:

| **Category**          | **Symptoms**                                                                 | **Likely Causes**                          |
|-----------------------|------------------------------------------------------------------------------|--------------------------------------------|
| **Application Failures** | App crashes, timeouts, or unresponsive behavior                             | Misconfigured dependencies, insufficient resources, or corrupt data |
| **Network Issues**     | Connectivity drops, high latency, or unreachable services                   | Firewall blocking ports, incorrect routes, or DNS misconfiguration |
| **Storage Problems**   | Slow I/O, disk failures, or application data corruption                     | Underpowered storage, improper backup policies, or permissions issues |
| **Security Breaches**  | Unauthorized access, failed authentication, or logs indicating brute-force attempts | Weak credentials, misconfigured ACLs, or missing patches |
| **Hardware Failures**  | Overheating, fan failures, or sudden power cuts                              | Poor ventilation, faulty components, or unstable power supply |
| **Database Issues**    | Query timeouts, connection leaks, or corruption                             | Insufficient indexing, improper transaction handling, or disk space issues |
| **Logging & Monitoring** | Missing logs, alert fatigue, or delayed notifications                      | Misconfigured log rotation, monitoring probes not reaching endpoints |

---
**Action Step:**
If multiple symptoms appear simultaneously, **prioritize failures that impact critical services first** (e.g., authentication, database, or API endpoints).

---

## **2. Common Issues & Fixes**

### **A. Application Crashes & Timeouts**
**Symptom:** The application fails silently or throws generic errors like `500 Internal Server Error`, with no stack traces.

#### **Root Causes & Fixes**
1. **Insufficient Memory/CPU**
   - **Check:** Use `top`, `htop`, or OS-level tools to monitor resource usage.
   - **Fix:** Scale horizontally (add more nodes) or optimize code.
   - **Example (Java):**
     ```java
     // Check heap usage in a JVM
     Runtime runtime = Runtime.getRuntime();
     long usedMemory = runtime.totalMemory() - runtime.freeMemory();

     if (usedMemory > (runtime.maxMemory() * 0.9)) {
         System.err.println("High memory usage detected! Consider scaling or tuning GC.");
     }
     ```

2. **Uncaught Exceptions**
   - **Check:** Review server logs (`/var/log/[app-name]/`) or add structured logging.
   - **Fix:** Implement global exception handling (e.g., Spring `@ControllerAdvice`).
   - **Example (Python - Flask):**
     ```python
     from flask import Flask, jsonify
     app = Flask(__name__)

     @app.errorhandler(Exception)
     def handle_exception(e):
         return jsonify({"error": str(e)}), 500
     ```

3. **Database Connection Timeouts**
   - **Check:** Use `pg_stat_activity` (PostgreSQL) or `show processlist` (MySQL) to identify idle connections.
   - **Fix:** Implement connection pooling (e.g., HikariCP, PgBouncer) and set `timeout` values.
   - **Example (Java HikariCP):**
     ```java
     Properties props = new Properties();
     props.setProperty("connectionTimeout", "30000"); // 30s timeout
     HikariConfig config = new HikariConfig(props);
     ```

---

### **B. Network-Related Issues**
**Symptom:** Services cannot communicate with each other or external APIs.

#### **Root Causes & Fixes**
1. **Firewall Blocking Traffic**
   - **Check:** Verify open ports (`netstat -tuln`, `ss -tuln`) and firewall rules (`iptables`, `ufw`).
   - **Fix:** Ensure allowed ports (e.g., 80, 443, custom app ports) are open.
   - **Example (Linux Firewall):**
     ```bash
     sudo ufw allow 80/tcp   # Allow HTTP
     sudo ufw allow 3306/tcp # Allow MySQL (if needed)
     ```

2. **DNS Resolution Failures**
   - **Check:** Test DNS from the server (`nslookup google.com`, `dig google.com`).
   - **Fix:** Configure `/etc/resolv.conf` with correct DNS servers (e.g., Google: `8.8.8.8`).
   - **Example:**
     ```
     nameserver 8.8.8.8
     nameserver 8.8.4.4
     ```

3. **Subnet Mismatch**
   - **Check:** Verify IP ranges (`ip a`, `ifconfig`) and ensure they don’t overlap with other networks.
   - **Fix:** Adjust VLANs or subnet masks if needed.

---

### **C. Storage & Database Corruption**
**Symptom:** Applications report `Disk Full`, `Table Locked`, or `Permission Denied`.

#### **Root Causes & Fixes**
1. **Disk Space Issues**
   - **Check:** Run `df -h` and `du -sh /var` to identify large directories.
   - **Fix:** Clean up logs (`logrotate`), delete old backups, or expand storage.
   - **Example (Log Rotation - `/etc/logrotate.conf`):**
     ```
     /var/log/app/*.log {
         daily
         missingok
         rotate 7
         compress
         delaycompress
     }
     ```

2. **Database Indexing Problems**
   - **Check:** Run `EXPLAIN` on slow queries (PostgreSQL/MySQL).
   - **Fix:** Add missing indexes or optimize queries.
   - **Example (MySQL):**
     ```sql
     CREATE INDEX idx_user_name ON users(last_name);
     ```

3. **Permission Issues**
   - **Check:** Verify file ownership (`ls -l /var/log/app`) and SELinux/AppArmor settings.
   - **Fix:** Adjust permissions (`chown`, `chmod`) or disable unnecessary restrictions.
   - **Example:**
     ```bash
     sudo chown -R app_user:app_group /var/data
     sudo chmod 750 /var/data
     ```

---

### **D. Security Vulnerabilities**
**Symptom:** Failed login attempts, unauthorized access, or brute-force detection.

#### **Root Causes & Fixes**
1. **Weak Credentials**
   - **Check:** Audit `/var/log/auth.log` for repeated failed attempts.
   - **Fix:** Enforce strong passwords and **fail2ban** to block IPs.
   - **Example (Fail2Ban):**
     ```ini
     # /etc/fail2ban/jail.local
     [sshd]
     enabled = true
     bantime = 1h
     findtime = 10m
     maxretry = 3
     ```

2. **Misconfigured ACLs**
   - **Check:** Verify `/etc/sudoers`, `/etc/passwd`, and application role-based access.
   - **Fix:** Restrict permissions to least privilege.
   - **Example (Linux Sudoers):**
     ```
     app_user ALL = NOPASSWD: /usr/bin/backup_script.sh
     ```

---

### **E. Hardware Failures**
**Symptom:** Server crashes, overheating, or sudden reboots.

#### **Root Causes & Fixes**
1. **Overheating**
   - **Check:** Monitor temps (`sensors`, `lm_sensors`).
   - **Fix:** Clean dust, replace thermal paste, or upgrade cooling.
   - **Example:**
     ```bash
     sudo apt install lm-sensors
     sensors
     ```

2. **Failing Disk**
   - **Check:** Run `smartctl -a /dev/sda` (SMART tests).
   - **Fix:** Replace disk immediately if bad sectors are detected.

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                     |
|------------------------|-----------------------------------------------|------------------------------------------|
| `tcpdump`              | Capture network traffic                      | `tcpdump -i eth0 port 80 -w capture.pcap` |
| `strace`               | Trace system calls (e.g., why a process hangs)| `strace -p PID`                          |
| `journalctl`           | Check systemd logs                           | `journalctl -u nginx --no-pager`         |
| `netstat` / `ss`       | Check network connections                    | `ss -tulnp`                              |
| `top` / `htop`         | Monitor CPU/Memory usage                      | `htop`                                   |
| `pgBadger` / `MySQLTuner` | Analyze DB query patterns               | `pgBadger /var/log/postgresql/postgresql.log` |
| `fail2ban`             | Automate IP blocking                         | `sudo systemctl status fail2ban`         |
| **Logging Aggregators** | Centralize logs (ELK Stack, Loki)            | `filebeat -e`                            |

---
**Pro Tip:**
- Use **logging libraries** (e.g., Log4j, Winston.js) for structured logs.
- Set up **alerting** (Prometheus + Alertmanager) for critical thresholds.

---

## **4. Prevention Strategies**
To minimize on-premise debugging efforts, adopt these **best practices**:

### **A. Infrastructure as Code (IaC)**
- Use **Ansible, Terraform, or Puppet** to standardize deployments.
- Example (Terraform):
  ```hcl
  resource "aws_instance" "web" {
    ami           = "ami-0abcdef1234567890"
    instance_type = "t3.medium"
    tags = {
      Name = "MyApp-Server"
    }
  }
  ```

### **B. Automated Backups**
- Schedule **daily snapshots** (e.g., `rsync`, `BorgBackup`).
- Example (Bash Cron Job):
  ```bash
  0 3 * * * /usr/bin/rsync -avz /var/www/ backup-server:/backups/www/
  ```

### **C. Monitoring & Alerts**
- Deploy **Prometheus + Grafana** for metrics.
- Set alerts for:
  - High CPU (>80%)
  - Disk usage (>90%)
  - Failed logins (3+ attempts)

### **D. Disaster Recovery (DR) Plan**
- **RTO (Recovery Time Objective):** Aim for <2 hours for critical services.
- **RPO (Recovery Point Objective):** Backups every 15 minutes.

### **E. Regular Maintenance**
- **Patch Management:** Use `apt upgrade`, `yum update`, or **Red Hat Subscription Manager**.
- **Hardware Checks:** Replace failing disks before they crash.

---

## **5. Step-by-Step Debugging Workflow**
1. **Reproduce the Issue:**
   - Is it consistent? Does it happen under load?
   - Check logs (`journalctl`, application logs).

2. **Isolate the Problem:**
   - Is it network-related? (Test with `ping`, `curl`.)
   - Is it application-specific? (Check stack traces.)

3. **Apply Fixes:**
   - Start with **low-risk changes** (e.g., log adjustments before code deployments).

4. **Validate:**
   - Monitor metrics after changes.
   - Re-run tests (unit, integration, load).

5. **Document:**
   - Update runbooks with fixes for future reference.

---

## **6. When to Escalate**
- **Escalate if:**
  - Hardware failure (e.g., motherboard crash).
  - Data corruption (requiring forensic analysis).
  - Security breach (e.g., unauthorized access).

---

## **Final Checklist for On-Premise Stability**
| **Area**          | **Action**                                  |
|-------------------|--------------------------------------------|
| **Network**       | Verify firewalls, VPNs, and routing.       |
| **Storage**       | Monitor disk health (`smartctl`), backups. |
| **Application**   | Check logs, CPU/memory, database queries.  |
| **Security**      | Audit permissions, fail2ban, password policies. |
| **Hardware**      | Replace failing components proactively.   |

---

## **Conclusion**
On-premise debugging requires **methodical troubleshooting**, leveraging logs, monitoring tools, and infrastructure best practices. By following this guide, you can **reduce downtime, improve reliability, and prevent recurring issues**.

**Key Takeaways:**
✅ **Log everything** – Structured logs save time.
✅ **Automate backups & monitoring** – Proactive > reactive.
✅ **Isolate issues quickly** – Use `strace`, `tcpdump`, and metrics.
✅ **Document fixes** – Maintain a knowledge base for the team.

Happy debugging! 🚀