# **Debugging On-Premise Deployment: A Troubleshooting Guide**

## **Introduction**
The **"On-Premise"** deployment pattern involves hosting applications, databases, and infrastructure within a private, controlled environment (e.g., a company data center) rather than relying on cloud providers. While this offers enhanced security and control, it introduces challenges such as network isolation, dependency management, and performance tuning.

This guide provides a structured approach to diagnosing and resolving common issues in on-premise deployments, ensuring minimal downtime and efficient troubleshooting.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically verify these symptoms to narrow down the problem:

| **Symptom**                     | **Possible Causes**                          | **Quick Check** |
|----------------------------------|---------------------------------------------|------------------|
| **Application crashes on startup** | Misconfigured dependencies, corrupted logs, or resource constraints | Check logs (`journalctl`, `tail -f /var/log/`) |
| **Slow response times**          | Network latency, CPU/memory bottlenecks, or database issues | Monitorwith `htop`, `netstat`, or `ping` |
| **Connection failures (DB/API)** | Firewall blocking ports, incorrect bindings, or misconfigured VPNs | Test `telnet` or `nc` to verify ports |
| **Failed dependency installations** | Permission issues, repository corruption, or incorrect versions | Verify `yum`, `apt`, or `pip` logs |
| **Log flooding or corruption**   | Improper log rotation or permission issues | Check `/etc/logrotate.conf` or `rsyslog` config |
| **Database lockouts/timeout**    | Overloaded queries, misconfigured `postgresql.conf`, or replication lag | Run `pgBadger` or `EXPLAIN ANALYZE` |
| **Container/VM unresponsive**    | Resource starvation, network misconfig, or disk I/O issues | Check `docker stats`, `virsh dominfo`, or `df -h` |
| **Authentication failures**      | LDAP/Kerberos misconfig, expired certs, or SELinux blocking access | Test with `kinit` or `ldapsearch` |

---

## **2. Common Issues & Fixes**

### **2.1 Application Crashes on Startup**
**Symptoms:**
- App logs show `Segmentation Fault`, `Permission Denied`, or `Missing Dependency`.
- The service fails to start (`systemctl status` shows `failed`).

**Possible Causes & Fixes:**

#### **A. Missing Dependencies**
- **Check:** `ldd <binary>` (for shared libs) or `dpkg -l | grep <missing_pkg>`.
- **Fix:**
  ```bash
  sudo yum install -y libxyz-devel  # RHEL/CentOS
  sudo apt-get install --fix-missing  # Debian/Ubuntu
  ```

#### **B. Corrupted or Misconfigured Logs**
- **Check:** `journalctl -xe` or `/var/log/<app>/*.log`.
- **Fix:** Rotate logs or reset permissions:
  ```bash
  sudo chown -R appuser:appgroup /var/log/<app>
  sudo logrotate -f /etc/logrotate.conf
  ```

#### **C. Port/Resource Conflicts**
- **Check:** `ss -tulnp | grep <port>` or `docker ps -a`.
- **Fix:** Kill conflicting processes or change the app’s bind port.

---

### **2.2 Slow Performance**
**Symptoms:**
- High CPU (`top`/`htop`), slow DB queries, or network timeouts.

**Possible Causes & Fixes:**

#### **A. Database Bottlenecks**
- **Check:** `pg_stat_activity` (PostgreSQL) or `SHOW STATUS LIKE 'Slow_Queries';` (MySQL).
- **Fix:** Optimize slow queries with `EXPLAIN ANALYZE` and adjust `innodb_buffer_pool_size`:
  ```ini
  # my.cnf (MySQL)
  innodb_buffer_pool_size = 2G
  slow_query_log = 1
  slow_query_log_file = /var/log/mysql/slow.log
  ```

#### **B. High Network Latency**
- **Check:** `ping <target>`, `mtr <target>`, or `tcpdump`.
- **Fix:** Adjust MTU (`/etc/sysctl.conf`), enable TCP BBR (`sysctl -w net.ipv4.tcp_congestion_control=bbr`), or optimize VPN tunnels.

---

### **2.3 Connection Failures (DB/API)**
**Symptoms:**
- `Connection refused` or `ETIMEDOUT` when accessing services.

**Possible Causes & Fixes:**

#### **A. Firewall Blocking Ports**
- **Check:** `sudo iptables -L -n` or `sudo ufw status`.
- **Fix:** Open required ports:
  ```bash
  sudo iptables -A INPUT -p tcp --dport 5432 -j ACCEPT  # PostgreSQL
  sudo ufw allow 3306/tcp  # MySQL
  ```

#### **B. Misconfigured Bindings**
- **Check:** `netstat -tulnp` or `docker inspect <container>`.
- **Fix:** Ensure the app binds to `0.0.0.0` (not `127.0.0.1`) and the port is exposed:
  ```yaml
  # Docker Compose example
  services:
    db:
      ports:
        - "5432:5432"
      command: -c "listen_addresses='*'"
  ```

#### **C. VPN/Network Misconfiguration**
- **Check:** `ip route` and verify VPN tunnels (`sudo ipsec status` for IPsec).
- **Fix:** Adjust routes or reconfigure VPN:
  ```bash
  sudo ip route add <remote_subnet> via <gateway>
  ```

---

### **2.4 Dependency Installation Failures**
**Symptoms:**
- `E: Could not open lock` (APT) or `yum failed to fetch`.

**Possible Causes & Fixes:**

#### **A. Repository Issues**
- **Check:** `apt-mirror` or `yum repolist`.
- **Fix:** Update repos and clean caches:
  ```bash
  sudo apt update && sudo apt upgrade
  sudo yum clean all && sudo yum makecache
  ```

#### **B. Permission Errors**
- **Check:** `ls -la /var/lib/apt/lists` or `/etc/yum.repos.d/`.
- **Fix:** Fix SELinux (`setenforce 0`) or ownership:
  ```bash
  sudo chown -R root:root /var/lib/apt
  sudo restorecon -Rv /var/lib/apt
  ```

---

### **2.5 Log Corruption**
**Symptoms:**
- Logs fill up disk space, or critical logs are missing.

**Possible Causes & Fixes:**

#### **A. Misconfigured Log Rotation**
- **Check:** `/etc/logrotate.conf` or `/etc/logrotate.d/<app>`.
- **Fix:** Adjust rotation settings:
  ```config
  /var/log/<app>/*.log {
      daily
      missingok
      rotate 7
      compress
      delaycompress
      notifempty
      create 640 appuser appgroup
  }
  ```

#### **B. Disk Full**
- **Check:** `df -h`.
- **Fix:** Free up space or adjust log retention:
  ```bash
  sudo journalctl --vacuum-size=100M  # Systemd logs
  sudo truncate -s 0 /var/log/syslog
  ```

---

## **3. Debugging Tools & Techniques**
### **3.1 Network Diagnostics**
| **Tool**          | **Use Case**                          | **Example Command** |
|-------------------|---------------------------------------|---------------------|
| `ping`            | Check basic connectivity               | `ping google.com`   |
| `mtr`             | Trace route + latency analysis         | `mtr google.com`     |
| `tcpdump`         | Capture network traffic                | `tcpdump -i eth0 port 5432` |
| `netstat`/`ss`    | Check listening ports                  | `ss -tulnp`          |
| `curl`/`wget`     | Test API endpoints                     | `curl -v http://localhost:8080/api` |

### **3.2 System Monitoring**
| **Tool**          | **Use Case**                          | **Example Command** |
|-------------------|---------------------------------------|---------------------|
| `htop`            | Real-time CPU/memory usage            | `htop`              |
| `iotop`           | Disk I/O bottlenecks                  | `sudo iotop`        |
| `dstat`           | Comprehensive system stats            | `dstat -cdngy`      |
| `strace`          | Debug syscalls (e.g., failed app start)| `strace -f ./app`   |

### **3.3 Database Debugging**
| **Tool**          | **Use Case**                          | **Example Command** |
|-------------------|---------------------------------------|---------------------|
| `pgBadger`        | PostgreSQL log analysis               | `pgbadger /var/log/postgresql/postgresql.log` |
| `EXPLAIN ANALYZE` | Optimize slow queries                 | `EXPLAIN ANALYZE SELECT * FROM users;` |
| `pg_top`          | Monitor active PostgreSQL sessions    | `pg_top`            |

### **3.4 Container/VM Debugging**
| **Tool**          | **Use Case**                          | **Example Command** |
|-------------------|---------------------------------------|---------------------|
| `docker exec`     | Shell into a container                | `docker exec -it cont_name bash` |
| `virsh console`   | Debug VMs                             | `virsh console vm_name` |
| `kubectl logs`    | Check Kubernetes pod logs             | `kubectl logs <pod>` |

---

## **4. Prevention Strategies**
### **4.1 Pre-Deployment Checks**
- **Dependency Validation:**
  Run `apt-cache policy` or `yum list installed` to ensure versions match requirements.
- **Network Testing:**
  Use `tcpdump` to verify ports are open before deployment.
- **Log Config:**
  Always set up log rotation and monitoring (`logrotate`, `syslog-ng`).

### **4.2 Automated Monitoring**
- **Install:**
  - **Prometheus + Grafana** for metrics.
  - **ELK Stack** (Elasticsearch, Logstash, Kibana) for logs.
  - **Nagios/Zabbix** for alerts.
- **Example Prometheus Alert:**
  ```yaml
  - alert: HighCPU
    expr: node_cpu_seconds_total{mode="user"} > 0.9 * 100
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High CPU on {{ $labels.instance }}"
  ```

### **4.3 Disaster Recovery Plan**
- **Backup Strategy:**
  - Database: `pg_dump` (PostgreSQL) or `mysqldump` (MySQL) with retention.
  - File System: `rsync` to a distant server or cloud storage.
- **Test Failover:**
  Simulate network partitions or VM failures to validate recovery.

### **4.4 Documentation & Runbooks**
- Maintain a **Troubleshooting Playbook** for common issues (e.g., "How to fix MySQL replication lag").
- Use **Ansible/Terraform** to ensure environment consistency.

---

## **5. Conclusion**
Debugging on-premise deployments requires a methodical approach:
1. **Isolate symptoms** using logs, metrics, and network tools.
2. **Apply fixes systematically** (dependencies → configs → permissions).
3. **Prevent recurrence** with monitoring, automation, and documentation.

For faster resolution, always:
✅ **Check logs first** (`journalctl`, `/var/log/`).
✅ **Verify network connectivity** (`ping`, `telnet`, `tcpdump`).
✅ **Test changes in staging** before production.

By following this guide, you can minimize downtime and ensure stable on-premise operations.