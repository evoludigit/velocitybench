# **[Pattern] On-Premise Techniques Reference Guide**

---

## **Overview**

The **On-Premise Techniques** pattern defines a structured approach to deploying and managing applications, infrastructure, and data processing in an organization’s private, internal data center or local servers (as opposed to cloud-based solutions). This pattern ensures **control, compliance, performance optimization, and security** while leveraging traditional IT infrastructure. It is ideal for organizations with strict regulatory requirements, legacy systems, or mission-critical workloads requiring low latency and full data ownership.

Key focus areas include:
- **Hardware and OS management** (physical servers, virtualization, OS hardening)
- **Application deployment** (containerization, legacy app migration, load balancing)
- **Data handling** (on-premise databases, backup, and disaster recovery)
- **Networking** (firewalls, VPNs, private subnets)
- **Monitoring and automation** (logging, patch management, DevOps tools)

This guide provides **implementation details, schema references, query examples, and related patterns** to ensure a structured, scalable on-premise deployment.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**               | **Description**                                                                 | **Common Tools/Technologies**                     |
|-----------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------|
| **Infrastructure Layer**    | Physical or virtual machines hosting applications and services.                  | Proxmox, VMware, Hyper-V, KVM, Bare Metal          |
| **Networking**              | Private networks, firewalls, VPNs, and load balancers for secure communication. | Cisco, Fortinet, Keepalived, HAProxy               |
| **OS & Security**           | Hardened operating systems, patch management, and compliance auditing.         | Linux (RHEL, Ubuntu), Windows Server, Ansible, Puppet|
| **Storage & Databases**     | On-premise databases, storage arrays, and backup solutions.                     | PostgreSQL, MySQL, NFS, ZFS, Veeam, Bacula         |
| **Application Hosting**     | Deployment of legacy or custom applications (containers, virtualized, or native).| Docker, Kubernetes (self-hosted), Tomcat, Jenkins  |
| **Monitoring & Logging**    | Real-time monitoring, alerts, and centralized logging.                        | Prometheus, Grafana, ELK Stack, Nagios             |
| **Backup & DR**             | Regular backups, snapshots, and disaster recovery planning.                     | Veeam, ZFS Send, DRBD, AWS Outposts (hybrid)       |

---

### **2. Implementation Steps**

#### **A. Infrastructure Setup**
1. **Server Provisioning**
   - Deploy physical or virtual machines with optimized configurations (CPU, RAM, storage).
   - Use **VM snapshots** for rapid rollback or testing.
   - Example: A 4-core, 16GB RAM VM for a database server.

2. **Network Segmentation**
   - Isolate critical systems (e.g., databases in a private subnet).
   - Configure **firewalls** (e.g., iptables, pfSense) to restrict traffic.
   - Example:
     ```bash
     # Allow only SSH from a specific IP in iptables
     sudo iptables -A INPUT -p tcp --dport 22 -s 192.168.1.5 -j ACCEPT
     ```

3. **OS Hardening**
   - Disable unnecessary services (`sshd`, `httpd` if unused).
   - Apply **SELinux/AppArmor** for mandatory access control.
   - Example (SELinux policy):
     ```bash
     sudo setenforce enforcing
     sudo audit2allow -a
     ```

---

#### **B. Application Deployment**
1. **Legacy Application Migration**
   - Containerize legacy apps using **Docker** or **Podman** for portability.
   - Example `Dockerfile` for a Java app:
     ```dockerfile
     FROM openjdk:17-jre
     COPY target/myapp.jar /app/
     WORKDIR /app
     ENTRYPOINT ["java", "-jar", "myapp.jar"]
     ```

2. **Kubernetes (Self-Hosted)**
   - Deploy Kubernetes clusters (e.g., **k3s** for lightweight setups).
   - Example `deployment.yaml`:
     ```yaml
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: myapp
     spec:
       replicas: 3
       selector:
         matchLabels:
           app: myapp
       template:
         spec:
           containers:
           - name: myapp
             image: myapp:latest
             ports:
             - containerPort: 8080
     ```

3. **Load Balancing**
   - Use **Keepalived** or **HAProxy** for high availability.
   - Example HAProxy config:
     ```conf
     frontend http-in
         bind *:80
         default_backend app_servers

     backend app_servers
         balance roundrobin
         server server1 192.168.1.10:8080 check
         server server2 192.168.1.11:8080 check
     ```

---

#### **C. Data Management**
1. **On-Premise Databases**
   - Deploy **PostgreSQL/MySQL** with replication for high availability.
   - Example PostgreSQL replication:
     ```sql
     -- On primary server
     stream = pg_basebackup -D /data/postgresql -Ft -P -C -R -S standby1
     ```

2. **Backup & Recovery**
   - Schedule **automated backups** (e.g., `rsync` for files, `pg_dump` for DBs).
   - Example `cron` job for MySQL backups:
     ```bash
     0 2 * * * mysqldump -u root -p'password' db_name | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
     ```

3. **Disaster Recovery (DR)**
   - Use **snapshots** (ZFS, LVM) or **replication** (DRBD) for near-instant recovery.
   - Example ZFS send/receive:
     ```bash
     # On source
     zfs send -R tanesha/zfs_dataset | ssh user@backup-host "zfs receive -F tanesha/zfs_dataset_backup"
     ```

---

#### **D. Monitoring & Automation**
1. **Logging**
   - Centralize logs with **ELK Stack (Elasticsearch, Logstash, Kibana)** or **Graylog**.
   - Example Logstash config for syslog:
     ```conf
     input {
       syslog {
         port => 514
         type => "syslog_messages"
       }
     }
     filter {
       grok {
         match => { "message" => "%{SYSLOGTIMESTAMP:syslog_timestamp} %{SYSLOGHOST:syslog_hostname} %{DATA:syslog_program}(?:\[%{POSINT:syslog_pid}\])?: %{GREEDYDATA:syslog_message}" }
       }
     }
     output {
       elasticsearch { hosts => ["http://localhost:9200"] }
     }
     ```

2. **Alerting**
   - Set up **Prometheus + Grafana** for metrics and alerts.
   - Example Prometheus alert rule:
     ```yaml
     - alert: HighCPUUsage
       expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "High CPU usage on {{ $labels.instance }}"
     ```

3. **Infrastructure as Code (IaC)**
   - Use **Ansible, Terraform, or Pulumi** to automate deployments.
   - Example Ansible playbook for server hardening:
     ```yaml
     - name: Harden SSH
       hosts: all
       tasks:
         - name: Disable root login
           lineinfile:
             path: /etc/ssh/sshd_config
             regexp: "^PermitRootLogin"
             line: "PermitRootLogin no"
           notify: restart sshd
     ```

---

## **Schema Reference**

| **Category**          | **Schema/Format**                          | **Purpose**                                  |
|-----------------------|--------------------------------------------|---------------------------------------------|
| **VM Template**       | JSON (OpenStack/VMware)                   | Define VM hardware, OS, and networking.      |
| **Database Schema**   | SQL (CREATE TABLE) or YAML (Ansible)      | Database structure for on-premise deployments. |
| **Backup Policy**     | YAML (Bacula) or Script (Bash/Python)     | Define backup frequency, retention, and targets. |
| **Network Rules**     | iptables/JSON (Firewall-as-Code)           | Firewall rules for security segmentation.    |
| **Kubernetes Config** | YAML (Deployment, Service, Ingress)       | Define app deployments and networking.       |
| **Monitoring Dashboard** | JSON (Grafana)          | Visualize metrics (CPU, disk, network).     |

---
**Example: VM Template (OpenStack)**
```json
{
  "name": "db-server",
  "image": "ubuntu-22.04",
  "flavor": "large",
  "networks": [
    { "name": "private", "fixed_ip": "10.0.0.10" }
  ],
  "security_groups": ["db-sg"],
  "user_data": "#!/bin/bash\napt update && apt install -y postgresql"
}
```

---

## **Query Examples**

### **1. SQL Query (Database Metrics)**
```sql
-- Check for slow queries in PostgreSQL
SELECT
    query,
    total_time,
    count(*) as calls,
    avg(total_time) as avg_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### **2. Bash Script (Disk Usage Check)**
```bash
#!/bin/bash
df -h | awk '$5 >= "90%" {print $0}'
```
*Output:*
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        10G   9.2G  400M  96% /
```

### **3. Ansible Ad-Hoc Command (Patch Check)**
```bash
ansible all -m command -a "uname -r" --become
```
*Output:*
```
192.168.1.10 | SUCCESS => {
    "changed": false,
    "stdout": "5.4.0-123-generic"
}
```

### **4. Prometheus Query (High Latency)**
```promql
# Check for API response times > 1s
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 1
```

---

## **Related Patterns**

| **Pattern**                     | **Connection to On-Premise Techniques**                                                                 | **When to Use**                                                                 |
|----------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Hybrid Cloud]**               | Combines on-premise with cloud for scalability (e.g., AWS Outposts).                                    | Organizations needing both control (on-prem) and flexibility (cloud).           |
| **[Legacy Modernization]**       | Refactors legacy apps for on-premise containers or microservices.                                      | Migrating outdated monolithic apps to modern infrastructure.                      |
| **[Zero Trust Networking]**      | Applies strict identity verification for on-premise access.                                            | High-security environments (government, finance).                                |
| **[Disaster Recovery as Code]**  | Automates DR planning with IaC (Terraform, Ansible).                                                    | Ensuring consistent, repeatable disaster recovery.                              |
| **[Observability Stack]**        | Centralizes logs, metrics, and traces for on-premise systems.                                           | Debugging and performance monitoring of distributed on-premise apps.             |

---

## **Best Practices**
1. **Isolate Critical Systems**: Use VLANs and firewalls to segment databases and APIs.
2. **Automate Repetitive Tasks**: Use Ansible/Terraform for consistent deployments.
3. **Regular Backups**: Test restore procedures monthly.
4. **Monitor proactively**: Set alerts for CPU, disk, and network anomalies.
5. **Document Everything**: Maintain runbooks for failover and troubleshooting.

---
**Further Reading**:
- [CNCF’s On-Prem Kubernetes Guide](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/)
- [NIST SP 800-53 for Security Controls](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)