# **[Pattern] DNS Failover Reference Guide**

---

## **Overview**
DNS Failover is a **high-availability pattern** that ensures seamless failover between multiple backend services when primary nodes fail. By leveraging DNS records and health checks, clients automatically reroute traffic to healthy alternatives without manual intervention. This pattern is critical for:
- **Cloud-native applications** (microservices, containers)
- **Multi-region deployments** (geographic redundancy)
- **Disaster recovery** (primary data center failures)

Implementation relies on **DNS record types** (A, AAAA, SRV) and **DNS providers** with built-in failover logic (e.g., AWS Route 53, Azure DNS, Cloudflare). A health-check mechanism (e.g., HTTP/HTTPS, TCP) validates service availability, and DNS updates records dynamically.

---

## **Implementation Details**

### **Key Components**
| Component          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Primary/Secondary** | Active and standby servers (e.g., web servers, databases).                                     |
| **DNS Records**     | A/AAAA for IP-to-name resolution; SRV for service discovery.                                   |
| **Health Checks**  | Polling endpoints to verify service health (e.g., `/health`).                                  |
| **DNS Provider**   | Supports failover: AWS Route 53, Azure DNS, Cloudflare, or custom scripts (e.g., BIND).        |
| **Load Balancer**   | Optional: Routes traffic to healthy endpoints (e.g., Nginx, HAProxy).                          |

---

### **Schema Reference**
#### **1. Required DNS Records**
| Record Type | Name          | Value (Example)      | TTL  | Purpose                                                                 |
|-------------|---------------|----------------------|------|-------------------------------------------------------------------------|
| **A/AAAA**  | `app.example.com` | `192.0.2.1` (Primary)| 30s  | Points to primary IP; updated via health checks.                       |
| **A/AAAA**  | `app.example.com` | `203.0.113.1` (Backup)| 30s  | Secondary IP; receives traffic if primary fails.                      |
| **SRV**     | `_http._tcp.app` | `0 5 80 app.example.com` | 30s | Service discovery for non-HTTP protocols (e.g., databases).            |

#### **2. Health Check Endpoint**
| Field          | Example Configuration                                                                 |
|----------------|----------------------------------------------------------------------------------------|
| **Endpoint**   | `/health` (HTTP) or `tcp://192.0.2.1:8080` (TCP)                                   |
| **Interval**   | 30 seconds (adjust based on expected failure detection time)                        |
| **Threshold**  | 3 consecutive failures = failover; 2 successful checks = revert                     |
| **Timeout**    | 5 seconds (prevents prolonged outages)                                                 |

#### **3. Failover Logic (Pseudocode)**
```python
if primary_endpoint.unhealthy:
    update_dns("app.example.com", backup_ip)
    trigger_load_balancer_reconfiguration()
else:
    update_dns("app.example.com", primary_ip)
```

---

### **Query Examples**
#### **1. Failover Triggered (Primary Down)**
1. Health check fails 3 times → DNS provider updates `A` record for `app.example.com` to `203.0.113.1`.
2. Client resolves `app.example.com` → returns `203.0.113.1`.
3. Load balancer (if used) distributes traffic to backup node.

**DNS Query Flow:**
```
Client → DNS Resolver → app.example.com (TTL: 30s) → 203.0.113.1
```

#### **2. Failback (Primary Recovered)**
1. Primary endpoint passes health checks → DNS reverts to primary IP.
2. DNS `TTL` (30s) ensures gradual propagation.

**DNS Update Command (AWS CLI Example):**
```bash
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890 \
    --change-batch '{
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "app.example.com",
                "Type": "A",
                "TTL": 30,
                "ResourceRecords": [{"Value": "192.0.2.1"}]
            }
        }]
    }'
```

---

## **Best Practices**

### **1. DNS TTL Tuning**
- **Short TTL (10–30s):** Ideal for failover but increases DNS query load.
- **Long TTL (1h–24h):** Reduces DNS traffic but delays failover.
- **Recommendation:** Use **short TTLs** during outages; increase after recovery.

### **2. Health Check Design**
- **Endpoints:** Avoid `/` (slow) → use `/health` (fast).
- **Protocols:** Prefer HTTP/HTTPS over TCP for richer checks (e.g., status codes).
- **Multi-Port Checks:** For databases, check both `tcp://3306` (MySQL) and `/health`.

### **3. Fallback Strategies**
- **Multi-Region:** Deploy backups in **AZs or regions** (e.g., `us-east-1a` + `us-west-2b`).
- **Hybrid:** Combine DNS failover with a **global load balancer** (e.g., AWS Global Accelerator).

### **4. Monitoring**
- **Logs:** Track DNS updates and failover events (e.g., AWS CloudWatch for Route 53).
- **Alerts:** Notify teams on failover events (e.g., Slack/PagerDuty).

---

## **Related Patterns**
| Pattern                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Circuit Breaker**    | Temporarily stops requests to a failing service (e.g., Hystrix).             |
| **Active-Active**      | Multiple instances handle traffic simultaneously (vs. DNS failover’s active-passive). |
| **Geographic DNS**     | Routes users to nearest server (e.g., `ny.example.com` vs. `london.example.com`). |
| **DNS Round Robin**    | Distributes traffic across multiple IPs (no failover; use for load balancing). |

---

## **Limitations**
| Limitation                          | Mitigation Strategy                                  |
|-------------------------------------|------------------------------------------------------|
| **DNS Propagation Delay**           | Use short TTLs (e.g., 30s) for critical services.     |
| **Single Point of Failure (DNS)**   | Deploy DNS in multiple regions (e.g., AWS Route 53 + Cloudflare). |
| **Complexity in Custom DNS**        | Use managed providers (AWS/Azure) with built-in failover. |

---
**References:**
- [AWS Route 53 Failover Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)
- [IETF DNS SRV Records](https://datatracker.ietf.org/doc/html/rfc2782)