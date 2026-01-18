# **Debugging On-Premise Troubleshooting: A Practical Guide**

On-premise systems require careful maintenance due to their isolated nature, complex dependencies, and lack of centralized monitoring compared to cloud-based solutions. This guide provides a structured approach to diagnosing and resolving issues in on-premise environments efficiently.

---

## **1. Symptom Checklist**

Before diving into fixes, identify the symptoms to narrow down the problem. Common signs of on-premise issues include:

### **Hardware-Related Symptoms**
- [ ] System crashes or unexpected reboots
- [ ] High CPU, memory, or disk usage leading to performance degradation
- [ ] Hardware failures (e.g., failed disks, overheating)
- [ ] Network connectivity issues (e.g., no internet, slow response from on-prem services)
- [ ] Unexpected power loss or UPS (Uninterruptible Power Supply) failures

### **Software-Related Symptoms**
- [ ] Applications crashing or failing to start
- [ ] Logins failing (authentication errors, permissions issues)
- [ ] Database connectivity problems
- [ ] Slow response times in applications
- [ ] Services not starting (e.g., `systemctl status <service>` fails)

### **Network-Related Symptoms**
- [ ] unable to reach internal servers (ping, DNS resolution issues)
- [ ] Firewall or security group blocking traffic
- [ ] VPN or remote access failures

### **Data & Storage Symptoms**
- [ ] Files disappearing or corrupting
- [ ] Disk space running out (`df -h` shows full disks)
- [ ] Backup failures

### **Security-Related Symptoms**
- [ ] Unauthorized access attempts
- [ ] Suspicious processes running (`ps aux | grep -i suspicious`)
- [ ] Antivirus/IDS alerts

If multiple symptoms appear, prioritize based on urgency (e.g., a crashing database server is more critical than a slow application).

---

## **2. Common Issues and Fixes**

### **2.1 System Crashes or Unexpected Reboots**
**Possible Causes:**
- Hardware failure (RAM, CPU, power supply)
- Overheating (check CPU fan speeds)
- Faulty BIOS/UEFI settings
- Kernel panic (check `/var/log/kern.log` or Windows Event Viewer)

**Debugging Steps:**
1. **Check logs:**
   ```bash
   journalctl -xe  # Linux (systemd)
   cat /proc/cpuinfo | grep MHz  # Check overheating
   ```
   - **Windows:** `Event Viewer > Windows Logs > System`

2. **Run hardware diagnostics:**
   - **Linux:** `smartctl -a /dev/sda` (for disk health)
   - **Windows:** `mdsched.exe` (Memory Diagnostic Tool)

3. **Check BIOS settings:**
   - Ensure boot order, boot mode (UEFI/legacy), and memory settings are correct.

4. **Update firmware & drivers:**
   ```bash
   sudo apt update && sudo apt upgrade -y  # Linux
   ```
   - **Windows:** Windows Update > Optional Updates

**Fix:**
- Replace faulty hardware (RAM, CPU, power supply).
- Clean dust from cooling fans.
- Update BIOS if needed.

---

### **2.2 High Resource Usage (CPU, Memory, Disk)**
**Possible Causes:**
- Misbehaving processes (e.g., memory leaks)
- Full disk space
- Too many background services

**Debugging Steps:**
1. **Identify resource hogs:**
   ```bash
   top -c  # Linux (real-time monitoring)
   htop    # Interactive process viewer
   ```
   - **Windows:** `Task Manager > Performance`

2. **Check disk space:**
   ```bash
   df -h  # Linux (shows mounted filesystems)
   ```
   - **Windows:** `Right-click This PC > Properties`

3. **Find large files:**
   ```bash
   sudo du -sh /* | sort -h  # Linux (find large directories)
   ```

**Fix:**
- Kill suspicious processes:
  ```bash
  sudo kill -9 <PID>  # Forcefully terminate a process
  ```
- Free up disk space:
  ```bash
  sudo rm -rf /path/to/unnecessary/files
  ```
- Optimize services (`systemctl list-units --type=service --state=running`).

---

### **2.3 Network Connectivity Issues**
**Possible Causes:**
- Misconfigured routing tables
- Firewall blocking traffic
- DNS resolution failures
- VPN or remote access misconfiguration

**Debugging Steps:**
1. **Test basic connectivity:**
   ```bash
   ping google.com  # Check internet access
   traceroute google.com  # Find where packets drop
   ```
   - **Windows:** `ping`, `tracert`, `nslookup`

2. **Check routing table:**
   ```bash
   route -n  # Linux/Windows (show routing rules)
   ip route   # Linux (alternative)
   ```

3. **Test firewall rules:**
   ```bash
   sudo iptables -L -n -v  # Linux firewall status
   sudo ufw status          # If using UFW
   ```
   - **Windows:** `Windows Defender Firewall with Advanced Security`

4. **Check DNS:**
   ```bash
   cat /etc/resolv.conf  # Linux (DNS settings)
   nslookup google.com   # Test DNS resolution
   ```

**Fix:**
- **Restart networking:**
  ```bash
  sudo systemctl restart networking  # Linux
  netsh int ip reset  # Windows
  ```
- **Adjust firewall rules:**
  ```bash
  sudo ufw allow 80/tcp  # Allow HTTP traffic
  ```
- **Reconfigure VPN:**
  - Check `sudo ipsec status` (Linux) or `rasman` (Windows).

---

### **2.4 Database Connectivity Problems**
**Possible Causes:**
- Database server not running
- Incorrect credentials
- Network issues between app and DB
- Port blocked by firewall

**Debugging Steps:**
1. **Check if the database service is running:**
   ```bash
   sudo systemctl status postgresql  # PostgreSQL
   sudo systemctl status mysql      # MySQL
   ```
   - **Windows:** `Services.msc > Find MySQL/PostgreSQL`

2. **Test connection manually:**
   ```bash
   mysql -u root -p -h localhost  # MySQL
   psql -U postgres -h localhost  # PostgreSQL
   ```

3. **Check logs:**
   ```bash
   sudo journalctl -u postgresql  # PostgreSQL logs
   sudo tail -f /var/log/mysql/error.log  # MySQL logs
   ```

**Fix:**
- **Restart the database:**
  ```bash
  sudo systemctl restart postgresql
  ```
- **Verify credentials in config files (`/etc/mysql/my.cnf`, `/etc/postgresql/main.conf`).**
- **Check firewall port (default: MySQL=3306, PostgreSQL=5432):**
  ```bash
  sudo ufw allow 3306/tcp
  ```

---

### **2.5 Failed Backups**
**Possible Causes:**
- Insufficient disk space
- Permissions issues
- Backup script errors
- Corrupted backup files

**Debugging Steps:**
1. **Check space before backup:**
   ```bash
   df -h /backup/directory
   ```
2. **Test backup script manually:**
   ```bash
   sudo ./backup_script.sh  # Run manually
   tail -f /var/log/backup.log  # Check logs
   ```
3. **Verify permissions:**
   ```bash
   ls -la /backup/directory  # Ensure backup user has write access
   ```

**Fix:**
- **Increase disk space:**
  ```bash
  sudo growpart /dev/sdb 1  # Extend partition (Linux)
  sudo resize2fs /dev/sdb1  # Resize filesystem
  ```
- **Fix permissions:**
  ```bash
  sudo chown -R backupuser:/backup/directory
  ```
- **Restore from a known good backup if files are corrupted.**

---

## **3. Debugging Tools and Techniques**

### **3.1 Logging & Log Analysis**
- **Linux:**
  - `journalctl` (systemd logs)
  - `tail -f /var/log/syslog`
  - `grep "error" /var/log/apache2/error.log` (for web servers)
- **Windows:**
  - Event Viewer (`eventvwr.msc`)
  - Application Logs (check IIS, SQL Server logs)
- **Logging Frameworks:**
  - **ELK Stack (Elasticsearch, Logstash, Kibana)** for centralized logging.
  - **Splunk** for advanced log monitoring.

### **3.2 Remote Debugging Tools**
- **SSH (Linux/Unix):** `ssh user@server_ip`
- **PowerShell Remoting (Windows):** `Enable-PSRemoting`
- **RDP (Remote Desktop):** `mstsc` (Windows)
- **VNC/TightVNC:** For GUI access to Linux servers.

### **3.3 Network Diagnostics**
- **`tcpdump` (Linux):** Capture network traffic:
  ```bash
  sudo tcpdump -i eth0 -w capture.pcap
  ```
- **Wireshark:** GUI alternative to `tcpdump`.
- **`mtr` (Linux):** Combine `ping` + `traceroute`:
  ```bash
  mtr google.com
  ```

### **3.4 Performance Monitoring**
- **Linux:**
  - `htop` (interactive process viewer)
  - `vmstat 1` (system metrics)
  - `iostat -x 1` (disk I/O)
- **Windows:**
  - **Performance Monitor** (`perfmon`)
  - **Resource Monitor** (`resmon`)

### **3.5 Automated Tools**
- **Nagios/Zabbix:** Monitoring infrastructure.
- **New Relic/DataDog:** APM (Application Performance Monitoring).
- **fail2ban:** Block brute-force attacks (`sudo apt install fail2ban`).

---

## **4. Prevention Strategies**

### **4.1 Proactive Monitoring**
- **Set up alerts** for:
  - Disk space (`df -h | awk '$5 >= 90 {print $NF}'`)
  - High CPU/memory usage (`top -c`)
  - Failed services (`systemctl is-active <service>`)
- **Use tools like:**
  - **Prometheus + Grafana** (custom metrics)
  - **Netdata** (real-time monitoring)

### **4.2 Regular Maintenance**
- **Update OS & applications:**
  ```bash
  sudo apt update && sudo apt upgrade -y  # Linux
  windows update  # Windows
  ```
- **Patch security vulnerabilities:**
  - Use **OpenSCAP** (Linux) or **WSUS** (Windows).
- **Rotate credentials** (database, admin accounts).

### **4.3 Backup & Disaster Recovery**
- **Automate backups:**
  - **Linux:** `rsync`, `tar`, `BorgBackup`
  - **Windows:** Windows Server Backup, Veeam
- **Test backups regularly.**
- **Implement 3-2-1 rule:**
  - 3 copies of data
  - 2 different media types
  - 1 offsite backup

### **4.4 Hardening Security**
- **Enable firewalls:**
  ```bash
  sudo ufw enable  # Linux
  Windows Defender Firewall  # Windows
  ```
- **Restrict SSH access:**
  ```bash
  sudo nano /etc/ssh/sshd_config
  PermitRootLogin no
  PasswordAuthentication no  # Use SSH keys only
  ```
- **Disable unused services:**
  ```bash
  sudo systemctl list-units --type=service --state=inactive
  ```

### **4.5 Documentation & Runbooks**
- **Keep an updated `runbook`** for common issues.
- **Document:**
  - Server configurations (`/etc/hosts`, firewall rules).
  - Backup procedures.
  - Contact info for vendors (hardware, software support).

---

## **Final Checklist Before Leaving a Problem**
1. **Root cause identified?**
2. **Log evidence preserved?**
3. **Fix applied and tested?**
4. **Preventive measures in place?**
5. **Documentation updated?**

By following this structured approach, you can efficiently diagnose and resolve on-premise issues while reducing future incidents.