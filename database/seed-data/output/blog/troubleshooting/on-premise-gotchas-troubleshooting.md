# **Debugging "On-Premise Gotchas": A Troubleshooting Guide**

## **1. Introduction**
On-premise deployments introduce unique challenges compared to cloud-based systems. Common pitfalls include network fragmentation, hardware failures, permission mismatches, and misconfigured dependencies. This guide provides a structured approach to diagnosing and resolving "on-premise gotchas" efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue with this checklist:

### **System-Level Symptoms**
- [ ] High latency or intermittent connectivity between services.
- [ ] Application crashes or timeouts, especially under heavy load.
- [ ] Authentication failures (e.g., `Permission denied`, `Invalid credentials`).
- [ ] Logs indicate disk I/O bottlenecks or high CPU/memory usage.
- [ ] Unexpected behavior when scaling horizontally (e.g., database replication lag).
- [ ] Network splits or unreachable endpoints (e.g., `Connection refused`, `DNS resolution failed`).

### **Logical & Configural Symptoms**
- [ ] Configuration drift (e.g., environment variables not matching runtime).
- [ ] Missing or misconfigured dependencies (e.g., missing JVM libraries, corrupted DB schemas).
- [ ] Timeouts during dependency initialization (e.g., DB connection pool exhaustion).
- [ ] Logs show repeated retries for failed external calls (e.g., API gateways, queues).
- [ ] Unexpected behavior in batch processing (e.g., partial failures, deadlocks).

### **Monitoring & Alerts**
- [ ] Unexpected spikes in resource usage (CPU, memory, disk).
- [ ] Alerts for disk space exhaustion or swap-thrashing.
- [ ] Slow response times on specific endpoints (check via `curl`, `Postman`, or APM tools).

---

## **3. Common Issues & Fixes**

### **Issue 1: Network Fragmentation (Split Brain, Latency, DNS Failures)**
**Symptoms:**
- Services unable to communicate despite correct IPs.
- High latency between microservices.
- `Connection refused` or `DNS resolution failed` errors.

**Root Causes:**
- Misconfigured firewalls/ACLs blocking internal traffic.
- DNS caching inconsistencies (e.g., local DNS vs. corporate DNS).
- Overlapping IP ranges causing routing loops.

**Fixes:**
#### **A. Verify Firewall Rules**
Ensure services can communicate on required ports (e.g., `8080`, `3306`).
```bash
# Check active connections (Linux)
sudo ss -tulnp | grep <port>

# Test connectivity from a service to another
curl -v http://<service-ip>:<port>
```

#### **B. Test DNS Resolution**
```bash
# Test DNS resolution from the target machine
nslookup <service-name>

# Check /etc/hosts for overrides
cat /etc/hosts
```

#### **C. Use Static IPs or Service Discovery**
If DNS is unreliable, configure applications to use static IPs or a local service registry (e.g., Consul, Eureka).

---

### **Issue 2: Permission Denied (File, DB, or API Access)**
**Symptoms:**
- `Permission denied` when accessing logs, config files, or databases.
- Application crashes on startup due to missing permissions.

**Root Causes:**
- Incorrect user/group permissions on files/directories.
- Database users lack necessary privileges.
- API keys/tokens expired or misconfigured.

**Fixes:**
#### **A. Check File Permissions**
```bash
# Fix directory permissions
sudo chown -R user:group /path/to/app
sudo chmod -R 755 /path/to/app

# Set sticky bit for shared directories
sudo chmod +t /path/to/shared_dir
```

#### **B. Verify Database Permissions**
```sql
-- Grant required privileges (e.g., for PostgreSQL)
GRANT ALL PRIVILEGES ON DATABASE db_name TO app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
```

#### **C. Rotate API Keys/Secrets**
If using OAuth or API keys:
```bash
# Regenerate keys via CLI/API
aws iam create-access-key  # Example for AWS
```

---

### **Issue 3: Disk I/O Bottlenecks**
**Symptoms:**
- High `wait_io` in `iostat -x 1`.
- Application timeouts due to slow disk operations.
- Logs show `java.io.IOException: Too many open files`.

**Root Causes:**
- Insufficient disk space.
- HDD instead of SSD in high-I/O workloads.
- Too many open file handles (default limits too low).

**Fixes:**
#### **A. Monitor Disk Health**
```bash
# Check disk usage
df -h

# Monitor I/O performance
iostat -x 1
```

#### **B. Increase Open File Limits**
Edit `/etc/security/limits.conf`:
```
* soft nofile 65536
* hard nofile 65536
```
Then restart the application or system.

#### **C. Switch to SSD or Ext4 Filesystem**
```bash
# For new installations, format with SSD
mkfs.ext4 -O ^metadata_csum /dev/sdX
```

---

### **Issue 4: Dependency Initialization Failures**
**Symptoms:**
- Application crashes during startup with `NoClassDefFoundError` or `SQLiteException`.
- External dependencies (e.g., DB, Kafka) unreachable.

**Root Causes:**
- Missing JARs, missing DB drivers, or corrupted schemas.
- Timeout during dependency resolution.

**Fixes:**
#### **A. Check Dependency Tree**
```bash
mvn dependency:tree  # For Maven projects
# Or check for missing JARs in runtime logs
```

#### **B. Validate DB Schema**
```sql
-- Compare expected vs. actual schema
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';
```

#### **C. Increase Timeout Settings**
```properties
# Example in application.properties
spring.datasource.hikari.connection-timeout=30000
```

---

### **Issue 5: Horizontal Scaling Issues**
**Symptoms:**
- Replicas fail to sync (e.g., inconsistent DB reads).
- Load balancer drops requests without retries.
- Session affinity broken.

**Root Causes:**
- Database replication lag.
- Misconfigured session storage (e.g., Redis not clustered).
- Load balancer health checks too aggressive.

**Fixes:**
#### **A. Check Replication Lag**
```sql
SHOW SLAVE STATUS;  # For MySQL
# Check for `Seconds_Behind_Master`
```

#### **B. Configure Redis Cluster**
```bash
# Run redis-cluster create <node-ips>
redis-cli --cluster create <node-ips> --cluster-replicas 1
```

#### **C. Adjust Load Balancer Settings**
```yaml
# Example for NGINX
server {
  location / {
    proxy_pass http://upstream;
    proxy_read_timeout 60s;
    proxy_connect_timeout 60s;
  }
}
```

---

## **4. Debugging Tools & Techniques**

### **A. Network Debugging**
| Tool | Purpose |
|------|---------|
| `tcpdump` | Capture network traffic |
| `nc` (netcat) | Test TCP/UDP connectivity |
| `mtr` | Replace `ping` + `traceroute` |
| Wireshark | Deep packet inspection |

**Example:**
```bash
# Test TCP connection
nc -zv <host> <port>

# Capture traffic
tcpdump -i eth0 -w trace.pcap port 8080
```

### **B. Log Analysis**
| Tool | Purpose |
|------|---------|
| `jstack` | Get thread dumps |
| `journalctl` | Check systemd logs |
| Graylog/ELK | Centralized logging |
| `grep`/`awk` | Filter logs for errors |

**Example:**
```bash
# Get thread dump for a stuck JVM
jstack -l <pid> > thread_dump.log
```

### **C. Performance Monitoring**
| Tool | Purpose |
|------|---------|
| `iostat` | Disk I/O stats |
| `vmstat` | System metrics |
| `htop` | Process-level CPU/Memory |
| Prometheus + Grafana | Long-term trends |

**Example:**
```bash
# Monitor disk I/O
iostat -x 1 10
```

### **D. Distributed Tracing**
| Tool | Purpose |
|------|---------|
| Jaeger | Open-source tracing |
| Zipkin | Lightweight tracing |
| Datadog/ New Relic | Enterprise-grade APM |

**Example (Jaeger):**
```bash
# Start Jaeger Agent
docker run -d -p 6831:6831/udp -p 6832:6832/udp jaegertracing/all-in-one:latest
```

---

## **5. Prevention Strategies**

### **A. Infrastructure Checklist**
- [ ] Use **SSDs** for critical workloads (e.g., DB, logs).
- [ ] Configure **proper disk quotas** to prevent exhaustion.
- [ ] Enable **network bandwidth monitoring** (e.g., `nload`, `iftop`).
- [ ] **Document IP ranges** and firewall rules.

### **B. Deployment Best Practices**
- [ ] **Test backups** regularly (e.g., `pg_dump` for PostgreSQL).
- [ ] Use **immutable infrastructure** (e.g., Docker containers).
- [ ] **Monitor logging retention** to avoid disk fill-ups.
- [ ] **Automate permission checks** (e.g., Ansible policies).

### **C. Observability Stack**
- **Logging:** ELK Stack (Elasticsearch, Logstash, Kibana) or Loki.
- **Metrics:** Prometheus + Grafana.
- **Tracing:** Jaeger or OpenTelemetry.
- **Alerts:** PagerDuty or Opsgenie for critical failures.

### **D. Disaster Recovery Plan**
- **RPO (Recovery Point Objective):** Ensure data loss < 15 mins.
- **RTO (Recovery Time Objective):** Restore services < 1 hour.
- **Test failover** quarterly (e.g., database failover).

---

## **6. Conclusion**
On-premise gotchas often stem from **network misconfigurations, permission issues, and resource constraints**. By following this guide:
1. **Systematically check symptoms** before diving into code.
2. **Use the right tools** (`tcpdump`, `jstack`, Prometheus) for efficient debugging.
3. **Prevent future issues** with observability and automation.

For recurring problems, document **runbooks** (e.g., "How to fix DB replication lag") to speed up resolution.

---
**Final Tip:** *"On-premise is like a ship—if you don’t monitor the bilge, you’ll sink."* — Senior Backend Engineer