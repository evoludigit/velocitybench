# **Debugging On-Premise Configuration: A Troubleshooting Guide**
*For Senior Backend Engineers & DevOps Teams*

---

## **1. Introduction**
The **On-Premise Configuration** pattern involves running critical infrastructure (databases, APIs, storage, or business logic) within an organization’s private data center rather than relying on cloud providers. While offering control and security, on-premise setups introduce complexity in networking, scaling, and configuration.

This guide focuses on **quick debugging** of common on-premise deployment issues, ensuring minimal downtime and efficient resolution.

---

## **2. Symptom Checklist**
Before diving into fixes, systematically verify the following issues:

| **Category**               | **Symptom**                                                                 | **Likely Cause**                          |
|----------------------------|----------------------------------------------------------------------------|-------------------------------------------|
| **Networking**            | - Inability to connect to internal services.                             | Firewall misconfig, misrouted DNS, MTU issues. |
|                            | - High latency between on-premise and cloud (if hybrid).                 | Poor VPN/bastion host setup.              |
| **Infrastructure**        | - Services fail to start (e.g., databases, APIs).                        | Missing dependencies, incorrect permissions. |
|                            | - Disk space exhaustion (`df -h` shows full disks).                       | Unmonitored log growth or misconfigured storage. |
| **Configuration**         | - Environment variables not loaded.                                       | Incorrect `.env` files or startup scripts. |
|                            | - Database connection failures (`Could not connect to MySQL`).            | Wrong credentials, network policy blocks ports. |
| **Security**              | - Unauthorized access attempts (`failed login attempts`).                  | Weak credentials or exposed admin interfaces. |
|                            | - Performance degradation (high CPU, memory leaks).                      | Misconfigured auto-scaling or resource contention. |
| **Logging/Monitoring**    | - Missing logs or incomplete error messages.                              | Log rotation disabled or parsing failures. |
|                            | - Alerts not triggering (e.g., failed health checks).                     | Misconfigured monitoring (Prometheus, Nagios). |

---

## **3. Common Issues & Fixes**
### **3.1 Networking Problems**
#### **Issue:** *"Services are unreachable internally (ping works, but HTTP fails)"*
**Possible Causes:**
- Firewall blocking ports (e.g., `22`, `3306`).
- Incorrect `iptables`/`nftables` rules.
- MTU issues (fragmented packets).

**Quick Fixes:**
```bash
# Check open ports on a server
sudo ss -tulnp | grep LISTEN

# Temporarily disable firewall for testing (Ubuntu/Debian)
sudo ufw disable

# Check MTU issues (if packets are fragmented)
ping -M do -s 1472 -c 4 <target_ip>
# If fragmented, adjust MTU:
sudo ip link set dev eth0 mtu 1400  # Adjust as needed
```

#### **Issue:** *"VPN connection drops intermittently"*
**Debug Steps:**
1. **Check VPN logs:**
   ```bash
   journalctl -u openvpn --no-pager  # Systemd-based systems
   ```
2. **Verify tunnel stability:**
   ```bash
   ping -I tun0 <destination>
   ```
3. **Increase keepalive:**
   Edit `/etc/openvpn/server.conf`:
   ```
   persist-local-ip
   persist-remote-ip
   ping 30  # Adjust interval
   ping-restart 120  # Restart if idle for 120s
   ```

---

### **3.2 Infrastructure Failures**
#### **Issue:** *"Databases fail to start (`mysqld: Can't find PID file`)"*
**Debug Steps:**
1. **Check for orphaned processes:**
   ```bash
   sudo lsof -i :3306  # Check if another MySQL instance is running
   ```
2. **Force restart:**
   ```bash
   sudo systemctl stop mysql
   sudo rm /var/run/mysqld/mysqld.pid
   sudo systemctl start mysql
   ```
3. **Verify permissions:**
   ```bash
   sudo chown -R mysql:mysql /var/lib/mysql
   ```

#### **Issue:** *"APIs crash on startup (`java.lang.OutOfMemoryError`)"*
**Quick Fix:**
- Adjust JVM heap size in `docker-compose.yml` or startup script:
  ```yaml
  environment:
    - JAVA_OPTS="-Xmx2G -Xms512M"
  ```
- Check for memory leaks in logs.

---

### **3.3 Configuration Errors**
#### **Issue:** *"Environment variables not loaded"*
**Debug Steps:**
1. **Verify `.env` file is read:**
   ```bash
   cat /path/to/.env | grep DB_PASSWORD
   ```
2. **Check startup script (e.g., `docker-entrypoint.sh`):**
   ```bash
   cat /docker-entrypoint.sh | grep "set -a"
   ```
   Ensure variables are exported:
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
3. **For Kubernetes, inspect ConfigMaps/Secrets:**
   ```bash
   kubectl get cm <configmap-name> -o yaml
   ```

#### **Issue:** *"Database connection refused (`Connection timed out`)"*
**Debug Steps:**
1. **Check listening interface:**
   ```bash
   sudo netstat -tulnp | grep mysql
   ```
   Ensure it binds to `0.0.0.0` (not `127.0.0.1`).
2. **Verify network policies (Kubernetes):**
   ```yaml
   # Example NetworkPolicy allowing MySQL access
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: allow-mysql
   spec:
     podSelector:
       matchLabels:
         app: mysql
     ingress:
     - ports:
       - port: 3306
         protocol: TCP
   ```

---

### **3.4 Security Issues**
#### **Issue:** *"Brute-force attacks on SSH (`Failed password` logs)"*
**Quick Fixes:**
- Rate-limit SSH:
  ```bash
  sudo apt install fail2ban
  sudo systemctl enable fail2ban
  ```
- Disable password auth (use SSH keys):
  ```bash
  sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  ```

#### **Issue:** *"Exposed admin interfaces (e.g., WordPress, Jenkins) reachable from the internet"*
**Debug Steps:**
1. **Scan for open ports externally:**
   ```bash
   nmap -sV <your-public-ip>
   ```
2. **Restrict access via firewall:**
   ```bash
   sudo iptables -A INPUT -p tcp --dport 8080 -j DROP  # Block Jenkins by default
   sudo iptables -A INPUT -p tcp --dport 8080 -s <trusted-ip> -j ACCEPT
   ```
3. **Use reverse proxies (Nginx/Apache) to authenticate requests.**

---

### **3.5 Logging & Monitoring**
#### **Issue:** *"Critical logs missing"*
**Debug Steps:**
1. **Check log rotations:**
   ```bash
   ls -lh /var/log/ | grep .gz  # Look for compressed logs
   ```
2. **Increase log retention:**
   ```bash
   sudo nano /etc/logrotate.conf
   ```
   Add:
   ```
   /var/log/app.log {
       rotate 7
       daily
       missingok
       notifempty
       compress
       delaycompress
   }
   ```
3. **Centralize logs (ELK Stack):**
   ```bash
   docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.12.0
   docker run -d --name kibana --link elasticsearch:elasticsearch -p 5601:5601 docker.elastic.co/kibana/kibana:8.12.0
   ```

#### **Issue:** *"Monitoring alerts not triggering"*
**Debug Steps:**
1. **Check Prometheus targets:**
   ```bash
   curl http://localhost:9090/targets
   ```
2. **Test alertmanager:**
   ```bash
   curl -X POST http://localhost:9093/api/v2/alerts -d '{"receiver": "default", "alerts": [{"status": "firing", "labels": {"alertname": "HighErrorRate"}}]}'
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Command/Example**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **`tcpdump`**         | Capture network traffic for packets.                                        | `sudo tcpdump -i eth0 port 80 -w capture.pcap` |
| **`strace`**          | Trace system calls for misbehaving processes.                               | `strace -f -o debug.log <pid>`              |
| **`journalctl`**      | Inspect systemd service logs.                                               | `journalctl -u nginx --since "1 hour ago"`  |
| **`netstat`/`ss`**    | Check open ports and connections.                                           | `ss -tulnp`                                 |
| **`dmesg`**           | Kernel-level errors (e.g., disk failures).                                  | `dmesg | grep -i error`                            |
| **`htop`/`glances`**  | Monitor CPU, memory, and disk I/O.                                          | `htop`                                      |
| **`kubectl debug`**   | Debug Kubernetes pods interactively.                                        | `kubectl debug -it <pod-name>`              |
| **`curl`/`wget`**     | Test API endpoints from the command line.                                   | `curl -v http://localhost:8080/health`      |
| **`fail2ban`**        | Block brute-force attempts.                                                 | `sudo systemctl status fail2ban`            |
| **Prometheus/Grafana**| Long-term monitoring and alerting.                                          | Visualize latency spikes.                   |

---

## **5. Prevention Strategies**
### **5.1 Infrastructure**
1. **Automate Deployments:**
   - Use **Terraform** or **Pulumi** for IaC to avoid misconfigurations.
   - Example Terraform snippet for a secure MySQL instance:
     ```hcl
     resource "aws_security_group" "mysql" {
       name        = "mysql-sg"
       description = "Allow MySQL only from bastion host"
       ingress {
         from_port   = 3306
         to_port     = 3306
         protocol    = "tcp"
         cidr_blocks = ["<bastion-ip>/32"]
       }
     }
     ```
2. **Enable Auto-Healing:**
   - Use **Kubernetes Liveness/Readiness Probes** or **systemd restart policies**:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 30
       periodSeconds: 10
     ```

### **5.2 Networking**
1. **Hardened Firewalls:**
   - Restrict ports to necessary IPs only.
   - Example `iptables` rule:
     ```bash
     sudo iptables -A INPUT -p tcp --dport 22 -s <trusted-office-ip> -j ACCEPT
     sudo iptables -A INPUT -p tcp --dport 22 -j DROP
     ```
2. **Network Segmentation:**
   - Use **VLANs** or **CNI plugins (Calico, Cilium)** in Kubernetes to isolate services.

### **5.3 Security**
1. **Least Privilege Access:**
   - Rotate credentials regularly (use **Vault** or **HashiCorp Secret Manager**).
   - Example Vault policy:
     ```hcl
     path "secret/data/db-credentials" {
       capabilities = ["read", "list"]
     }
     ```
2. **Regular Audits:**
   - Schedule **`lynis`** scans:
     ```bash
     sudo apt install lynis
     sudo lynis audit system
     ```
3. **Enable Encryption:**
   - Encrypt disks (**LUKS**) and backups (**`duplicity`**).

### **5.4 Observability**
1. **Centralized Logging:**
   - Deploy **Loki** + **Grafana** for log aggregation.
2. **Synthetic Monitoring:**
   - Use **PagerDuty** or **UptimeRobot** to simulate user requests.
3. **Benchmark Baselines:**
   - Track **95th percentile latency** (e.g., with **Prometheus Histograms**).

---

## **6. Escalation Path**
If issues persist:
1. **Check vendor documentation** (e.g., MySQL bug databases).
2. **Engage SLAs** (if using supported on-premise software).
3. **Reproduce in staging** before applying fixes to production.
4. **Document the fix** in a knowledge base (e.g., Confluence/GitHub Wiki).

---

## **7. Key Takeaways**
| **Action**               | **Goal**                                  | **Tool/Example**                          |
|--------------------------|-------------------------------------------|--------------------------------------------|
| **Isolate the issue**    | Narrow down to networking, config, or infra. | `tcpdump`, `journalctl`                   |
| **Apply minimal fixes**  | Avoid over-engineering.                   | `iptables -A`, `docker-compose down`       |
| **Automate prevention**  | Reduce future occurrences.                | Terraform, Prometheus alerts              |
| **Monitor proactively**  | Catch issues before users notice.         | Grafana dashboards, `fail2ban`            |

---
**Final Note:** On-premise debugging often requires **patience**—sysadmins often need to trace issues from the kernel (`dmesg`) to application logs. **Start broad (`ping`, `netstat`), then narrow down (`strace`, `curl -v`).**