# **Debugging On-Premise Strategies: A Troubleshooting Guide**

## **1. Introduction**
On-Premise Strategies refer to deploying and managing applications, databases, and infrastructure within a company’s own data centers rather than relying on cloud providers. This approach offers control, security, and customization but introduces complexity in scaling, maintenance, and troubleshooting.

This guide provides a structured approach to diagnosing and resolving common issues in on-premise environments, ensuring minimal downtime and efficient resolution.

---

## **2. Symptom Checklist**
Before diving into fixes, verify the following symptoms to narrow down the problem:

### **General System Issues**
- [ ] **Performance degradation** (slow response times, high CPU/memory usage)
- [ ] **Service failures** (applications, databases, or APIs crashing or unresponsive)
- [ ] **Network connectivity issues** (latency, timeouts, unreachable services)
- [ ] **Storage problems** (disk full, slow I/O, failed backups)
- [ ] **Authentication failures** (login rejection, permission issues)
- [ ] **Logical errors** (application crashes with no obvious external cause)

### **Database-Specific Issues**
- [ ] **Slow queries** (executing for unusually long time)
- [ ] **Connection pool exhaustion** (database refusing connections)
- [ ] **Transaction timeouts** (long-running transactions blocking others)
- [ ] **Data corruption** (inconsistent records, missing data)

### **Application-Specific Issues**
- [ ] **Crashes on startup** (application fails to initialize)
- [ ] **HTTP 500 errors** (server-side exceptions)
- [ ] **Dependency failures** (external services not responding)
- [ ] **Race conditions** (concurrent access causing unexpected behavior)

### **Infrastructure-Specific Issues**
- [ ] **Virtual machine (VM) crashes** (unexpected reboots, failed migrations)
- [ ] **Load balancer failures** (unable to distribute traffic)
- [ ] **Firewall/NACL misconfigurations** (unexpected network blocks)

---

## **3. Common Issues and Fixes (With Code Examples)**

### **3.1 Performance Degradation (High CPU/Memory Usage)**
**Symptoms:**
- Slow application response times.
- High `top`/`htop` CPU or memory usage.
- Database queries taking longer than expected.

**Root Causes:**
- Memory leaks in applications.
- Inefficient SQL queries (missing indexes, full table scans).
- Lack of resource allocation (under-provisioned servers).
- Too many background processes.

**Debugging Steps:**
1. **Check system metrics:**
   ```bash
   top -d 1  # Monitor CPU/Memory in real-time
   ```
   ```bash
   free -h    # Check memory and swap usage
   ```
   ```bash
   iostat -x 1 # Check disk I/O performance
   ```

2. **Identify CPU hogs:**
   ```bash
   ps aux --sort=-%cpu | head -n 10
   ```

3. **Database bottleneck analysis:**
   ```sql
   -- Check slow queries in PostgreSQL
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

4. **Optimize queries (example: adding an index):**
   ```sql
   CREATE INDEX idx_customer_email ON customers(email);
   ```

5. **Adjust resource limits (if using containers/Kubernetes):**
   ```yaml
   # Example resource limits in Kubernetes
   resources:
     limits:
       cpu: "2"
       memory: "4Gi"
     requests:
       cpu: "1"
       memory: "2Gi"
   ```

**Preventive Fix:**
- Implement **auto-scaling** (if possible).
- Use **application performance monitoring (APM)** tools like New Relic or Datadog.

---

### **3.2 Service Failures (Applications/Cron Jobs Crashing)**
**Symptoms:**
- Application logs show `Segmentation Fault`, `OutOfMemoryError`, or `Timeout`.
- Cron jobs failing without clear error messages.

**Root Causes:**
- Unhandled exceptions in code.
- Infinite loops or blocking calls.
- Resource starvation (e.g., too many open files).

**Debugging Steps:**

1. **Check logs for errors:**
   ```bash
   tail -f /var/log/<app_name>.log
   ```

2. **Use `strace` to debug crashes:**
   ```bash
   strace -f -e openat,execve ./your_application 2>&1 | grep -i "error\|segfault\|oom"
   ```

3. **Enable verbose logging (example in Java):**
   ```java
   public class DebugExample {
       public static void main(String[] args) {
           System.setProperty("java.util.logging.config.file", "logging.properties");
           Logger.getLogger("com.yourpackage").setLevel(Level.FINEST);
           // Your code...
       }
   }
   ```

4. **Fix common crashes (e.g., Java `OutOfMemoryError`):**
   ```bash
   # Increase JVM heap (adjust as needed)
   java -Xms2g -Xmx4g -jar your_app.jar
   ```

5. **For cron job failures:**
   ```bash
   crontab -l | grep your_script
   ```
   ```bash
   # Redirect logs to a file
   * * * * * /path/to/script.sh >> /tmp/cron.log 2>&1
   ```

**Preventive Fix:**
- **Unit & integration testing** for edge cases.
- **Graceful shutdown handling** in applications.

---

### **3.3 Network Connectivity Issues (Latency/Timeouts)**
**Symptoms:**
- Services taking ~1-2 seconds longer than usual.
- `curl` failing with `Connection timed out`.
- DNS resolution issues.

**Root Causes:**
- Overloaded network interfaces.
- Misconfigured load balancers.
- DNS cache staleness.
- Firewall blocking traffic.

**Debugging Steps:**

1. **Check network latency:**
   ```bash
   ping <hostname>  # Check basic connectivity
   mtr <hostname>   # Advanced troubleshooting (TCP & UDP)
   ```

2. **Trace network path:**
   ```bash
   traceroute <hostname>
   ```

3. **Check firewall rules:**
   ```bash
   sudo iptables -L -n -v  # Linux firewall rules
   sudo ufw status          # UFW status
   ```

4. **Test connectivity to a specific port:**
   ```bash
   telnet <hostname> <port>
   nc -zv <hostname> <port>  # Netcat test
   ```

5. **Fix common issues:**
   - **DNS issues:** Flush cache (`sudo systemd-resolvconf -f`).
   - **Load balancer misconfig:** Verify health checks and routing tables.
   - **Firewall rule:** Allow necessary ports:
     ```bash
     sudo iptables -A INPUT -p tcp --dport <port> -j ACCEPT
     ```

**Preventive Fix:**
- **Monitor network health** with tools like Nagios.
- **Use VPNs** for secure remote access.

---

### **3.4 Storage Problems (Disk Full, Slow I/O)**
**Symptoms:**
- `df -h` shows disk at 95%+ capacity.
- Applications failing with `No space left on device`.
- Database writes slowing down.

**Root Causes:**
- Log files growing uncontrollably.
- Temporary files not being cleaned up.
- Under-provisioned storage.

**Debugging Steps:**

1. **Check disk usage:**
   ```bash
   df -h            # Check overall disk space
   du -sh /var/log  # Check log directory size
   ```

2. **Find large files:**
   ```bash
   find /var/log -type f -exec du -h {} + | sort -rh | head -n 10
   ```

3. **Cleanup logs (example for rotating logs):**
   ```bash
   journalctl --vacuum-size=100M  # Rotate systemd logs
   ```

4. **Fix permissions (if disk is full due to permissions):**
   ```bash
   sudo chown -R user:group /path/to/directory
   ```

5. **Optimize database storage:**
   - Run `VACUUM` in PostgreSQL.
   - Archive old data.

**Preventive Fix:**
- **Enable log rotation** (`logrotate` in Linux).
- **Set up alerts** for disk space thresholds.

---

### **3.5 Authentication Failures**
**Symptoms:**
- Users unable to log in.
- `403 Forbidden` or `401 Unauthorized`.
- LDAP/Active Directory sync issues.

**Root Causes:**
- Incorrect credentials in config files.
- Expired SSL certificates.
- Misconfigured LDAP bindings.

**Debugging Steps:**

1. **Check auth logs:**
   ```bash
   tail -f /var/log/auth.log
   ```

2. **Test LDAP connection (example):**
   ```bash
   ldapsearch -x -H ldap://ldap-server -b "dc=example,dc=com" -D "admin" -W
   ```

3. **Verify SSL certificates:**
   ```bash
   openssl s_client -connect your-server:443 -showcerts
   ```

4. **Fix common issues:**
   - **Reset passwords** in LDAP.
   - **Update auth configs** (e.g., `nginx`, `apache`):
     ```nginx
     auth_basic_user_file /etc/nginx/.htpasswd;
     ```

**Preventive Fix:**
- **Automate certificate renewal** (Let’s Encrypt + Certbot).
- **Use MFA** for admin access.

---

## **4. Debugging Tools and Techniques**

| **Tool**               | **Use Case**                          | **Example Command/Usage**                     |
|------------------------|---------------------------------------|---------------------------------------------|
| **top/htop**           | Check CPU/Memory usage                | `htop`                                       |
| **strace**             | Trace system calls for crashes        | `strace -f ./app`                            |
| **netstat/ss**         | Check network connections             | `ss -tulnp`                                  |
| **mtr**                | Advanced network troubleshooting      | `mtr google.com`                             |
| **tcpdump**            | Capture network packets               | `tcpdump -i eth0 port 80`                    |
| **journalctl**         | View systemd logs                      | `journalctl -xe`                             |
| **dig/nslookup**       | Test DNS resolution                   | `dig example.com`                            |
| **pg_stat_statements** | Analyze slow SQL queries (PostgreSQL) | `SELECT query, calls FROM pg_stat_statements;` |
| **New Relic/Datadog**  | APM for performance monitoring        | N/A (requires installation)                 |

### **Advanced Techniques:**
- **Kernel-level debugging:** Use `perf` for CPU profiling.
  ```bash
  perf top
  ```
- **Container debugging:** Inspect Kubernetes pods:
  ```bash
  kubectl describe pod <pod-name>
  kubectl logs <pod-name>
  ```
- **Database profiling:** Enable slow query logs in MySQL:
  ```sql
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 1;
  ```

---

## **5. Prevention Strategies**

### **5.1 Proactive Monitoring**
- **Set up alerts** for:
  - High CPU/Memory usage.
  - Disk space thresholds.
  - Failed authentication attempts.
- **Use tools:**
  - Prometheus + Grafana (metrics).
  - Nagios/Zabbix (alerts).

### **5.2 Infrastructure Best Practices**
- **Automate backups** (e.g., `rsync`, `BorgBackup`).
- **Use configuration management** (Ansible, Puppet, Chef).
- **Implement CI/CD** for rapid deployments.

### **5.3 Code & Security Hardening**
- **Write unit tests** (JUnit, pytest).
- **Enforce static code analysis** (SonarQube).
- **Regularly update dependencies** (`npm audit`, `yum update`).
- **Scan for vulnerabilities** (OWASP ZAP, Nessus).

### **5.4 Documentation & Runbooks**
- Maintain an **on-call rotation** for critical systems.
- Document **troubleshooting steps** for common issues.
- **Postmortems** after incidents to identify root causes.

---

## **6. Conclusion**
On-premise debugging requires a mix of **system-level monitoring**, **log analysis**, and **proactive maintenance**. By following this guide, you should be able to:
✅ Quickly identify root causes of failures.
✅ Apply targeted fixes (with code examples).
✅ Prevent future issues with monitoring and automation.

**Final Checklist Before Troubleshooting:**
- [ ] Verify logs (`/var/log/`).
- [ ] Check system metrics (`top`, `df`, `netstat`).
- [ ] Test connectivity (`ping`, `telnet`, `mtr`).
- [ ] Review recent changes (deploys, config updates).

---
**Need further help?** Refer to the specific tool’s documentation or escalate to cloud providers if hybrid setups are involved.