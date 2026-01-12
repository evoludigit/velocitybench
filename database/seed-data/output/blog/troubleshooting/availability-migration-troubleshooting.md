# **Debugging Availability Migration: A Troubleshooting Guide**

## **1. Introduction**
The **Availability Migration** pattern ensures that applications can failover gracefully between availability zones or regions, minimizing downtime and improving resilience. This guide focuses on diagnosing and resolving common issues in implementations of this pattern, particularly when using **active-active or active-passive failover** strategies.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these common symptoms of Availability Migration issues:

### **Primary Symptoms**
- **[ ]** Failover triggers unexpectedly (e.g., during routine traffic spikes).
- **[ ]** DNS or load balancer misrouting traffic away from the primary node.
- **[ ]** State synchronization delays (e.g., databases lagging behind).
- **[ ]** Application connections dropping during failover.
- **[ ]** Health checks failing on the primary or secondary node.
- **[ ]** Users experiencing degraded performance or timeouts.
- **[ ]** Logs indicating connection resets (`ECONNRESET`, `Connection refused`).

### **Secondary (Indirect) Symptoms**
- **[ ]** Increased latency in region-to-region communication.
- **[ ]** Unexpected API failures (`5xx` errors) during failover.
- **[ ]** Database replication lag (if using active-active DBs).
- **[ ]** Load balancer (LB) health checks returning `UNHEALTHY` incorrectly.
- **[ ]** Resource contention (e.g., CPU/memory overload on secondary node).

---

## **3. Common Issues & Fixes**
Below are the most frequent problems encountered in Availability Migration implementations, along with practical fixes.

---

### **Issue 1: Failover Triggered Prematurely (False Failover)**
**Symptoms:**
- Failover occurs even when the primary node is healthy.
- Application logs show unexpected disconnects.

**Root Causes:**
- Misconfigured health checks (e.g., too aggressive thresholds).
- Network partitions detected incorrectly.
- Load balancer misrouting traffic due to stale health checks.

**Fixes:**

#### **A. Adjust Health Check Thresholds**
Ensure health checks are not triggering too frequently or aggressively.

**Example (AWS ALB Health Check Adjustment):**
```yaml
# AWS Load Balancer Configuration (ALB)
HealthCheck:
  HealthyThreshold: 3  # Require 3 successful probes before marking healthy
  UnhealthyThreshold: 5 # Require 5 failures before marking unhealthy
  Interval: 30s        # Check every 30 seconds
  Timeout: 5s          # Fail fast if no response
```

#### **B. Disable Unnecessary Connection Draining**
If using **connection draining**, ensure it’s not causing false failovers.

**Example (Nginx Config):**
```nginx
http {
    upstream backend {
        server primary:8080 max_fails=3 fail_timeout=30s;
        server secondary:8080 max_fails=3 fail_timeout=30s;
    }

    server {
        location / {
            proxy_pass http://backend;
            proxy_max_fails 3;
            proxy_fail_timeout 30s;
        }
    }
}
```

#### **C. Debug Network Partition Issues**
If failover is triggered due to network splits, check:
- **MTU/Fragmentation:** Large packets may cause failures.
- **Security Groups/NACLs:** Ensure traffic between zones is allowed.
- **VPN/Transit Gateway Latency:** High latency can trigger timeouts.

**Command to Check MTU:**
```bash
ping -M do -s 1472 <primary-ip>  # ETH_DGRAM (Do not fragment)
```
If packets fragment, reduce payload size.

---

### **Issue 2: State Synchronization Delays (Active-Active DBs)**
**Symptoms:**
- Secondary node is out of sync with the primary.
- Read queries return stale data.

**Root Causes:**
- Replication lag due to high write throughput.
- Network latency between regions.
- DB instance throttling (e.g., Aurora/PostgreSQL).

**Fixes:**

#### **A. Monitor Replication Lag**
Use DB-specific tools to check lag:

**PostgreSQL:**
```sql
SELECT * FROM pg_stat_replication;
```
**MySQL:**
```sql
SHOW SLAVE STATUS;
```

**Fix if Lag is High:**
- Scale read replicas.
- Use **binary logging (binlog) compression** in MySQL:
  ```ini
  [mysqld]
  binlog_rows_query_log_events = 1
  binlog_format = ROW
  ```
- Consider **multi-region DB replication** (e.g., AWS Global Database).

#### **B. Implement Quorum-Based Consistency (For Active-Active)**
If using **Cassandra/RocksDB**, ensure:
- **Read repair** is enabled:
  ```cql
  ALTER TABLE keyspace.table WITH read_repair_chance = 0.1;
  ```
- **Hints cache** is configured:
  ```cql
  ALTER KEYSPACE keyspace WITH hints_cache_use_ssd = true;
  ```

---

### **Issue 3: DNS Misrouting During Failover**
**Symptoms:**
- Traffic is not redirected to the secondary node.
- Users still hit the primary even after failover.

**Root Causes:**
- DNS TTL too high (e.g., 300s).
- Load balancer not updating health checks fast enough.
- Stale records in CDN/DNS cache.

**Fixes:**

#### **A. Shorten DNS TTL (Temporary Fix)**
```powershell
# AWS Route 53: Reduce TTL to 30s for testing
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890 \
    --change-batch '{
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "example.com",
                "Type": "A",
                "TTL": 30,
                "SetIdentifier": "failover-test",
                "ResourceRecords": [{"Value": "secondary-ip"}]
            }
        }]
    }'
```

#### **B. Use Weighted Records (AWS Route 53)**
 shifts traffic gradually:
 ```powershell
 aws route53 change-resource-record-sets \
     --hosted-zone-id Z1234567890 \
     --change-batch '{
         "Changes": [{
             "Action": "UPSERT",
             "ResourceRecordSet": {
                 "Name": "example.com",
                 "Type": "A",
                 "TTL": 30,
                 "SetIdentifier": "weighted-failover",
                 "ResourceRecords": [
                     {"Value": "primary-ip", "Weight": 0},
                     {"Value": "secondary-ip", "Weight": 100}
                 ]
             }
         }]
     }'
 ```

#### **C. Flush CDN Cache (Cloudflare/AWS CloudFront)**
```bash
# Cloudflare API to purge cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/<zone-id>/purge_cache" \
     -H "Authorization: Bearer <api-token>" \
     -H "Content-Type: application/json" \
     --data '{"purge_everything":true}'
```

---

### **Issue 4: Application Connection Drops on Failover**
**Symptoms:**
- Users see `Connection refused` or `ETIMEDOUT`.
- Session state is lost.

**Root Causes:**
- **Sticky sessions** not configured properly.
- **TCP keepalive** timeout too short.
- **Application-level session persistence** failing.

**Fixes:**

#### **A. Configure Load Balancer Sticky Sessions**
**AWS ALB:**
```yaml
StickySession:
  Enabled: true
  CookieName: AWSALB
  CookieDurationSeconds: 300  # 5-minute sessions
  ForceSticky: false
```

**Nginx:**
```nginx
http {
    upstream backend {
        zone backend 64k;
        server primary:8080;
        server secondary:8080;
    }

    server {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_ssl_session_reuse on;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

#### **B. Adjust TCP Keepalive**
**Linux Kernel (sysctl):**
```bash
# Increase keepalive time (default: 2h)
sysctl -w net.ipv4.tcp_keepalive_time=900
# Increase keepalive probes before dropping
sysctl -w net.ipv4.tcp_keepalive_probes=9
# Reduce keepalive interval
sysctl -w net.ipv4.tcp_keepalive_intvl=30
```

**Java (Application-Level):**
```java
// Configure TCP keepalive (Netty)
BossEventLoopGroup bossGroup = new NioEventLoopGroup(1);
EventLoopGroup workerGroup = new NioEventLoopGroup();
Bootstrap b = new Bootstrap()
    .group(workerGroup)
    .channel(NioSocketChannel.class)
    .handler(new ChannelInitializer<SocketChannel>() {
        @Override
        protected void initChannel(SocketChannel ch) throws Exception {
            ch.config().setOption(ChannelOption.SO_KEEPALIVE, true);
            ch.config().setOption(ChannelOption.TCP_KEEPIDLE, 900); // 15 minutes
            ch.config().setOption(ChannelOption.TCP_KEEPINTVL, 30); // 30 seconds
        }
    });
```

---

### **Issue 5: Database Failover Stuck (PostgreSQL Example)**
**Symptoms:**
- Primary DB fails, but standby does not promote.
- `pg_isready` still shows primary as alive.

**Root Causes:**
- **Hot standby** not configured.
- **Replication slot** not created.
- **Manual intervention required** (e.g., `pg_ctl promote`).

**Fixes:**

#### **A. Check Replication Status**
```sql
SELECT * FROM pg_stat_replication;
-- If no rows, replication is broken.
```

#### **B. Create a Replication Slot (PostgreSQL)**
```sql
SELECT * FROM pg_create_physical_replication_slot('failover_slot');
```

#### **C. Force Promote Standby (If Needed)**
```bash
# On standby server
pg_ctl promote
```

#### **D. Check WAL Archiving**
Ensure `wal_level` is set to `replica`:
```sql
ALTER SYSTEM SET wal_level = 'replica';
```

---

## **4. Debugging Tools & Techniques**
### **A. Network Diagnostics**
| Tool | Command/Use Case |
|------|------------------|
| `ping` | Check ICMP connectivity. |
| `mtr` | Trace route with latency. |
| `tcpdump` | Capture network packets. |
| `netstat` | Check open connections. |
| `ss` | Modern replacement for `netstat`. |
| AWS VPC Flow Logs | Monitor traffic between AZs. |

**Example (TCPdump):**
```bash
sudo tcpdump -i eth0 -w failover.pcap 'port 5432 or port 8080'
```

### **B. Log Analysis**
- **Application Logs:** Check for `Connection refused` or `Timeout`.
- **DB Logs:** Look for replication errors.
- **LB Logs:** Verify health check failures.

**Example (AWS CloudWatch Logs Query):**
```sql
filter @type = "RESPONSE" AND @status = 503 AND @httpCode = "503"
| stats count(*) by @service
```

### **C. Health Check Automation**
- **Synthetic Monitoring:** Use **AWS Synthetics, Datadog, or Pingdom** to simulate failover.
- **Custom Scripts:**
  ```bash
  # Bash script to test failover
  while true; do
      response=$(curl -s -o /dev/null -w "%{http_code}" http://example.com/health)
      if [ "$response" -ne 200 ]; then
          echo "Failover detected at $(date)" >> failover.log
      fi
      sleep 60
  done
  ```

### **D. Chaos Engineering (Optional)**
- **Gremlin** or **Chaos Mesh** to test failover manually.
- Simulate **network partitions** or **node failures**.

---

## **5. Prevention Strategies**
### **A. Design-Time Mitigations**
1. **Multi-AZ Deployment by Default**
   - Never deploy single-AZ if failover is required.
2. **Automated Failover Testing**
   - Schedule **chaos tests** (e.g., kill primary node weekly).
3. **Stateful vs. Stateless Separation**
   - Move **session storage** (Redis, DynamoDB) to a resilient tier.

### **B. Runtime Monitoring**
| Metric | Tool | Threshold |
|--------|------|-----------|
| DB Replication Lag | Prometheus + Alertmanager | > 1s |
| LB Health Check Failures | CloudWatch/Azure Monitor | > 10% |
| TCP Connection Drops | `ss -s` | > 1% drop rate |
| Latency (P99) | Datadog/New Relic | > 500ms |

### **C. Infrastructure-as-Code (IaC) Safeguards**
- **Terraform:** Enforce multi-AZ deployments.
  ```hcl
  resource "aws_instance" "app" {
    availability_zone = data.aws_availability_zones.available.names[1] # Always 2nd AZ
    instance_type     = "t3.medium"
  }
  ```
- **Kubernetes:** Use **PodDisruptionBudget** for graceful scaling.
  ```yaml
  apiVersion: policy/v1
  kind: PodDisruptionBudget
  metadata:
    name: app-pdb
  spec:
    maxUnavailable: 1
    selector:
      matchLabels:
        app: my-app
  ```

### **D. Disaster Recovery (DR) Drills**
- **Quarterly DR Tests**
  - Simulate **region-wide outages**.
  - Verify **backup restores** in 15 minutes.
- **Backup Validation**
  - Use **AWS Backup** or **Velero** to test restores.

---

## **6. Conclusion & Key Takeaways**
| Issue | Root Cause | Quick Fix | Prevention |
|-------|------------|-----------|------------|
| **False Failover** | Aggressive health checks | Adjust thresholds | Use **weighted routing** |
| **DB Sync Lag** | High write load | Scale replicas | **Multi-region DB** |
| **DNS Misrouting** | High TTL | Shorten TTL | **Use ALB + Sticky Sessions** |
| **Connection Drops** | TCP timeouts | Increase keepalive | **Sticky sessions + keepalive** |
| **DB Failover Stuck** | Missing slot | `pg_ctl promote` | **Automated standby promotion** |

**Final Checklist Before Going Live:**
✅ **Test failover manually** (kill primary node).
✅ **Monitor replication lag** in production.
✅ **Validate DNS failover** with `dig`/`nslookup`.
✅ **Check session persistence** (cookies/tokens).
✅ **Set up alerts** for health check failures.

By following this guide, you can **quickly diagnose and resolve** Availability Migration issues while ensuring robustness in production. 🚀