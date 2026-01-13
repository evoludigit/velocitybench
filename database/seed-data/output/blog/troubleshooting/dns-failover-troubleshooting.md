# **Debugging DNS Failover: A Troubleshooting Guide**

## **Introduction**
DNS Failover is a critical pattern for improving **availability, reliability, and scalability** by routing traffic between primary and secondary DNS servers when the primary fails. Misconfigurations, network issues, or infrastructure faults can break this redundancy, leading to outages or degraded performance.

This guide provides a structured approach to diagnosing and resolving DNS failover failures efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms to confirm DNS failover issues:

| **Symptom**                          | **Check if Present** |
|--------------------------------------|----------------------|
| Primary DNS unresponsive             | ✅/❌                 |
| Secondary DNS not taking over traffic | ✅/❌               |
| High latency or timeouts in DNS queries | ✅/❌           |
| Failed health checks on primary server | ✅/❌               |
| Load balancer or application misrouting | ✅/❌              |
| `dig`/`nslookup` returning different results for primary/secondary | ✅/❌ |
| DNS TTL (Time-to-Live) issues causing stale records | ✅/❌ |

**Next Step:** If symptoms match, proceed to **Common Issues & Fixes**.

---

## **2. Common Issues & Fixes**

### **2.1 Primary DNS Server Not Responding**
**Symptoms:**
- DNS queries to primary fail with timeouts
- Load balancer health checks fail

**Possible Causes & Fixes:**

#### **Cause 1: Network Connectivity Issues**
- Firewall blocking DNS ports (UDP 53, TCP 53)
- VPN or security group misconfiguration

**Fix:**
```bash
# Test connectivity from secondary to primary
telnet primary-dns-server 53
# Should respond with 'Connected' or timeout (if unreachable)
```

**Solution:**
- Ensure firewall rules allow **UDP 53** (DNS) between servers.
- Check security groups (AWS, GCP) or firewall policies.

#### **Cause 2: DNS Server Crash or High Load**
- Primary server overloaded or crashed
- DNS cache poisoning or corrupted zones

**Fix:**
```bash
# Check BIND (Linux) or Windows DNS server logs
journalctl -u named  # For BIND
# OR
Get-Service "DNS" | Restart-Service  # Windows
```

**Solution:**
- Restart the DNS service.
- If the server is unresponsive, failover should trigger automatically (if configured).

#### **Cause 3: Incorrect Health Check Thresholds**
- Load balancer health checks are too strict

**Fix:**
```yaml
# Example (Nginx load balancer config)
health_check:
  uri: /health
  interval: 10s
  timeout: 5s
  unhealthy_threshold: 3
```
**Solution:**
- Adjust thresholds to allow temporary DNS instability.
- Use **DNS SRV records** with lower TTLs for faster failover.

---

### **2.2 Secondary DNS Not Taking Over**
**Symptoms:**
- Traffic still routed to primary even after failure
- `dig @primary` fails, but `dig @secondary` succeeds

**Possible Causes & Fixes:**

#### **Cause 1: DNS Failover Not Configured**
- Secondary not set up as a failover (e.g., AWS Route 53, BIND, Cloudflare)

**Fix (BIND Example):**
```bash
# Edit /etc/bind/named.conf (primary)
zone "example.com" {
    type master;
    file "/var/named/example.zone";
    allow-transfer { secondary-dns-ip; };  # Explicitly allow transfers
};

# Edit /etc/bind/named.conf.local (secondary)
zone "example.com" {
    type slave;
    masters { 10.0.0.1; };  # Primary IP
    file "/var/named/slaves/example.zone";
};
```
**Solution:**
- Ensure **slave (secondary) is correctly configured** to pull zones from primary.
- Test with:
  ```bash
  named-checkzone example.com /var/named/slaves/example.zone
  ```

#### **Cause 2: DNS TTL Too High**
- High TTL causes clients to cache stale records

**Fix:**
```bash
# Lower TTL in BIND zone file
$TTL 300  # 5 minutes (instead of 86400)
example.com. IN A 10.0.0.1
```
**Solution:**
- Reduce TTL for failover zones (e.g., `SRV` records).
- Use **short-lived TTLs** for critical systems.

#### **Cause 3: Load Balancer Not Detecting Failover**
- LB stuck on primary due to misconfigured health checks

**Fix (AWS Load Balancer Example):**
```yaml
# Update health check target
HealthCheck:
  Target: "DNS:80"  # Check DNS server health
  HealthyThreshold: 2
  Interval: 30s
```
**Solution:**
- Ensure the LB is **monitoring DNS responsiveness** (not just HTTP).
- Use **DNS-based failover** (e.g., Route 53 Latency-Based Routing).

---

### **2.3 Random Failover or "Flapping" Failover**
**Symptoms:**
- DNS records switch between primary and secondary unpredictably
- Clients experience inconsistent latency

**Possible Causes & Fixes:**

#### **Cause 1: DNS Round-Robin Misconfiguration**
- Multiple DNS servers in **RR (Round Robin) mode** without failover logic

**Fix (BIND Example):**
```bash
# Replace RR with weighted or NOTIFY-based failover
$TTL 60
example.com. IN A 10.0.0.1  # Primary
IN A 10.0.0.2  # Secondary (lower weight)
```
**Solution:**
- Avoid **pure RR** for critical services.
- Use **geographic or latency-based failover** (e.g., AWS Route 53).

#### **Cause 2: DNS Cache Poisoning**
- Malicious or misconfigured DNS responses

**Fix:**
```bash
# Validate zone transfers
dig +trace example.com
# Check for unauthorized responses
dig ANY example.com @secondary
```
**Solution:**
- Enable **DNSSEC** to prevent spoofing.
- Use **RPZ (Response Policy Zones)** to block bad queries.

---

## **3. Debugging Tools & Techniques**

### **3.1 DNS Query Testing**
```bash
# Test DNS resolution from multiple locations
dig @primary example.com
dig @secondary example.com
# Compare TTL, SOA, and response times

# Check DNS propagation
dig NS example.com
```

### **3.2 Network & Connectivity Checks**
```bash
# Test DNS port connectivity
telnet primary-dns-server 53

# Check DNS server logs
journalctl -u named  # Linux
Get-WinEvent -LogName "Application" -FilterHashtable @{LogName='System'}  # Windows

# Use `tcpdump` to inspect DNS traffic
tcpdump -i eth0 -n port 53
```

### **3.3 Load Balancer & Health Check Debugging**
```bash
# Check LB health status
aws elb describe-instance-health  # AWS ELB
kubectl get endpoints  # Kubernetes

# Simulate a failure
kill -9 <primary-dns-pid>  # Crash primary to test failover
```

### **3.4 DNS Failover Simulation Tools**
- **DNSCheck (https://dnscheck.pingdom.com/)** – Monitors DNS globally.
- **DNSPropCheck (https://dnspropcheck.com/)** – Tests propagation speed.
- **Cloudflare DNS Analyzer** – Checks for misconfigurations.

---

## **4. Prevention Strategies**
### **4.1 Best Practices for DNS Failover**
✅ **Use DNS Anycast** (e.g., Cloudflare, Google DNS) for global failover.
✅ **Monitor DNS Health** with tools like Prometheus + Grafana.
✅ **Short TTLs for Critical Records** (e.g., `SRV` records).
✅ **Automate Failover Testing** (e.g., scheduled `kill` of primary).
✅ **Implement DNSSEC** to prevent spoofing.
✅ **Use Load Balancers with DNS Health Checks** (AWS ELB, Nginx).

### **4.2 Automated Monitoring Alerts**
```yaml
# Example Prometheus alert rule
- alert: DNSFailoverFailed
  expr: up{job="dns-check"} == 0
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "DNS failover not working (primary down)"
    value: "{{ $value }}"
```

### **4.3 Disaster Recovery Plan**
- **Backup DNS Zones** (`named-compilezone` for BIND).
- **Test Failover Monthly** (kill primary, verify secondary takes over).
- **Document Failover Procedures** for quick recovery.

---

## **Conclusion**
DNS Failover issues can be frustrating but follow this structured approach:
1. **Check symptoms** (timeout, misrouted traffic, TTL issues).
2. **Test connectivity, logs, and failover configuration**.
3. **Adjust DNS settings, LB health checks, and TTLs**.
4. **Monitor and automate failover testing**.

By following these steps, you can **diagnose and fix DNS failover failures efficiently**, ensuring **high availability** for your applications.

---
**Need Further Help?**
- Check [BIND Documentation](https://www.isc.org/bind/)
- AWS DNS Failover: [Route 53 Failover Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html)
- Cloudflare DNS Failover: [DNS Failover Tutorial](https://developers.cloudflare.com/dns/dns-over-tls/dns-failover/)