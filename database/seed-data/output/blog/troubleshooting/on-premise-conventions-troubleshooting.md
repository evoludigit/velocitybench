# **Debugging *On-Premise Conventions* Pattern: A Troubleshooting Guide**

## **1. Introduction**
The *On-Premise Conventions* pattern ensures standardized configurations, security policies, and operational practices within a private cloud or on-premise infrastructure. Common issues arise from misconfigurations, compliance gaps, or inadequate monitoring. This guide provides a structured approach to diagnosing and resolving problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, verify the following symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Unized Compliance Checks** | Security scans (e.g., CIS benchmarks) fail due to misconfigured services (e.g., SSH, databases). | Risk of vulnerabilities, regulatory penalties. |
| **Performance Degradation** | High latency or resource contention in critical systems (e.g., storage, networking). | Downtime, inefficient operations. |
| **Authentication Failures** | Users/staff cannot access systems due to expired certificates or misconfigured LDAP/Kerberos. | Productivity loss, security risks. |
| **Patch Management Failures** | Failed OS/patch deployments due to conflicting policies or missing pre/post-scripts. | Exposed systems, compliance violations. |
| **Backup Failures** | Retention policies aren’t enforced; backups are incomplete or corrupted. | Data loss, recovery failures. |
| **Network misconfigurations** | Overly restrictive firewall rules or VPN failures due to overly strict conventions. | Remote access issues, service outages. |
| **Logging/Governance Gaps** | Audit logs are incomplete or unstructured, making forensics difficult. | Regulatory non-compliance, difficult incident response. |

---

## **3. Common Issues and Fixes**

### **3.1 Compliance Violations (CIS Benchmarks, PCI DSS, etc.)**
**Symptom:** Security tools (e.g., OpenSCAP, Nessus) flag misconfigurations.
**Common Causes:**
- SSH enabled root login (`PermitRootLogin` set to `yes`).
- Outdated OS/patches.
- Unencrypted storage (e.g., `ext4` without LUKS).

**Fixes:**
#### **A. Enforce SSH Hardening**
```bash
# Disable root login (edit /etc/ssh/sshd_config)
sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

#### **B. Apply CIS Benchmark Fixes**
Use tools like **OpenSCAP** to auto-apply benchmarks:
```bash
# Install OpenSCAP
sudo yum install -y scap-security-guide scap-workbench

# Apply CIS CentOS 7 Level 1
sudo scap-workbench --profile scap_ssg_rule_centos7-docker_level1.xml \
    --rules scap_ssg_rule_centos7-docker_level1.rules \
    --output openscap_result.xml

# Verify fixes
sudo scap-workbench --profile scap_ssg_rule_centos7-docker_level1.xml \
    --rules scap_ssg_rule_centos7-docker_level1.rules \
    --input openscap_result.xml --rules scap_ssg_rule_centos7-docker_level1.rules
```

---

### **3.2 Performance Bottlenecks (Storage, Network, CPU)**
**Symptom:** High disk I/O, network latency, or CPU throttling.
**Common Causes:**
- Inadequate swap space.
- Over-provisioned VMs with high RAM/CPU usage.
- Misconfigured NFS/iSCSI shares (e.g., incorrect `rw`/`ro` permissions).

**Fixes:**
#### **A. Optimize Disk I/O**
Check disk usage:
```bash
df -h
iostat -x 1
```
Fix high I/O:
```bash
# Increase swap (if safe)
sudo swapoff -a
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
```
#### **B. Adjust NFS Permissions**
```bash
# Check mounts
sudo mount | grep nfs

# Fix permissions (example: enforce read-only)
sudo mount -o remount,ro /path/to/nfs/mount
```

---

### **3.3 Authentication Failures (LDAP, Kerberos, Certificates)**
**Symptom:** Users cannot log in via Active Directory or Kerberos.
**Common Causes:**
- Expired Kerberos tickets (`kinit` fails).
- Misconfigured `nsswitch.conf` for LDAP.
- SSL certificate mismatches in reverse proxy (e.g., Nginx).

**Fixes:**
#### **A. Renew Kerberos Tickets**
```bash
# Check ticket status
klist

# Renew ticket (if expired)
kinit user@DOMAIN.COM
```

#### **B. Verify LDAP Bindings**
```bash
# Test LDAP connection
ldapsearch -x -H ldap://AD_SERVER -b "dc=example,dc=com" -D "CN=Admin,CN=Users,DC=example,DC=com" -W
```
Fix `/etc/nsswitch.conf`:
```ini
passwd:         files ldap
shadow:         files ldap
group:          files ldap
```

#### **C. Fix Reverse Proxy SSL**
```nginx
# Ensure cert paths are correct in Nginx
server {
    listen 443 ssl;
    server_name example.com;
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
}
```

---

### **3.4 Patch Management Failures**
**Symptom:** Failed OS patches or agent updates (e.g., Puppet/Chef).
**Common Causes:**
- Missing pre-post scripts.
- Conflicting policies in configuration management tools.

**Fixes:**
#### **A. Debug Failed Patches**
```bash
# Check yum/dnf logs
sudo journalctl -u yum-interval-sync --no-pager

# Retry patch (CentOS/RHEL)
sudo yum update --skip-broken -y
```

#### **B. Fix Puppet/Chef Agent**
```bash
# Restart Puppet agent
sudo systemctl restart puppet
sudo puppet agent --test

# Clear cache (Chef)
sudo chef-client --debug --no-merge --local-mode
```

---

## **4. Debugging Tools and Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|------------|---------------------|
| **OpenSCAP** | CIS compliance checks | `oscap benchmark apply --profile centos7-docker-level1` |
| **Nagios/Zabbix** | Monitoring misconfigurations | `nagios-check_ssh` |
| **Wireshark** | Network protocol issues | `tcpdump -i eth0 -w capture.pcap` |
| **SSH Key Audit** | Check for weak keys | `ssh-keygen -l -f ~/.ssh/id_rsa` |
| **Auditd** | Log policy violations | `sudo ausearch -m AVC` |

**Techniques:**
- **Binary Search Debugging:** Isolate affected systems, check if issues occur in a subset.
- **Rolling Restarts:** Apply fixes incrementally (e.g., restart one server at a time).
- **Reproduce in Test Env:** Deploy misconfigurations in a staging server to diagnose.

---

## **5. Prevention Strategies**
### **5.1 Automate Compliance Checks**
- Use **Ansible Playbooks** or **Terraform** to enforce conventions.
  ```yaml
  # Example Ansible task for SSH hardening
  - name: Ensure SSHPermitRootLogin is disabled
    lineinfile:
      path: /etc/ssh/sshd_config
      regexp: '^PermitRootLogin'
      line: 'PermitRootLogin no'
    notify: restart sshd
  ```

### **5.2 Implement Change Control**
- Enforce **GIT branching** for configuration changes.
- Use **GitHub Actions/ArgoCD** for CI/CD of conventions.

### **5.3 Centralized Logging**
- Deploy **Graylog/ELK Stack** to aggregate logs for audit trails.
- Set up alerts for missing logs (`/var/log/auth.log` not updating).

### **5.4 Regular Audits**
- Schedule **quarterly compliance scans** (e.g., via OpenSCAP).
- Archive old logs (`/var/log/` cleanup scripts).

### **5.5 Documentation**
- Maintain a **runbook** for common fixes (e.g., "How to Reset Kerberos Tickets").
- Use **Confluence/Notion** to document exceptions (e.g., "Why VM1 is exempt from SSH key-only").

---

## **6. Next Steps**
1. **Immediate Fix:** Apply the most severe compliance/performance fixes.
2. **Root Cause Analysis (RCA):** Use tools like `strace` or `perf` to trace slow processes.
3. **Scaling:** Replicate fixes across all on-premise servers.
4. **Feedback Loop:** Document findings in a **wiki** for future teams.

By following this guide, you’ll systematically resolve *On-Premise Conventions* issues while reinforcing best practices.