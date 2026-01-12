---

# **Debugging Blue-Green Deployment: A Troubleshooting Guide**
*(Back-end Engineering Focus)*

---

## **1. Introduction**
Blue-Green Deployment is a technique where you maintain two identical production environments:
- **Blue** (current live version)
- **Green** (new version, yet to go live)

At deployment time, traffic is switched from Blue to Green. This minimizes downtime and rollback risk.

### **When to Suspect Blue-Green Issues?**
If your system exhibits:
✅ Unstable performance after traffic switch
✅ Partial failovers or inconsistent behavior between versions
✅ Slow response times or timeouts post-deployment
✅ Records mismatch (e.g., DB conflicts, stale session data)

---

## **2. Symptom Checklist**
| Symptom | Likely Cause | Immediate Action |
|---------|-------------|------------------|
| **5xx errors after switch** | Misconfigured endpoints, version mismatch | Check logs, verify traffic routing |
| **Database connection issues** | DB schemas differ, or connection strings misconfigured | Validate DB migrations, test DB calls |
| **Caching inconsistencies** | CDN/Redis cache not cleared | Purge caches, verify cache invalidation |
| **Session/state issues** | Session storage not version-aware (e.g., Redis) | Use sticky sessions or shared state |
| **Slow response times** | Under-provisioned Green environment | Check scaling, CPU/memory usage |
| **API version mismatches** | Backend API endpoints differ | Verify API versions, use feature flags |
| **Logging/Metrics spikes** | New version logs more aggressively | Filter logs, adjust sampling |

---

## **3. Common Issues & Fixes**

### **3.1 Traffic Switch Gone Wrong (Misrouted Requests)**
**Symptom:** Requests land on the wrong version due to DNS or load balancer misconfiguration.

**Code Example: Verify Traffic Routing (Load Balancer Config)**
```yaml
# Nginx/ALB Config: Ensure traffic is routed to Green (target-group-id)
upstream backend {
    server blue-server:8080;
    server green-server:8080;
}
server {
    location / {
        proxy_pass http://backend; # Should switch to green on command
    }
}
```
**Fix:**
- Check load balancer rules (`weight` or `server_pool`).
- Use **canary releases** before full switch.
- Validate DNS propagation (`dig`, `nslookup`).

---

### **3.2 Database Schema Migrations Not Applied**
**Symptom:** New version crashes on `SchemaVersion` misalignment.

**Debugging Command:**
```sql
SELECT * FROM migrations WHERE applied = FALSE;
```
**Fix:**
- Ensure **zero-downtime DB migrations** (e.g., Flyway, Liquibase).
- Use **transactional outbox pattern** for async DB changes.

**Example: Flyway Migration Check**
```java
// Java (Flyway) - Verify migrations
Flyway flyway = Flyway.configure().dataSource(dbUrl, user, pwd).load();
flyway.migrate(); // Force sync if stuck
```

---

### **3.3 Caching Issues (Stale Data)**
**Symptom:** Old cached responses serve users after switch.

**Fix:**
- **Clear all caches** (Redis, CDN, local cache).
- Use **cache versioning** (e.g., `Cache-Control: version=2`).

**Example: Redis Cache Purge (Python)**
```python
import redis
r = redis.Redis(host='localhost')
r.flushdb()  # Emergency cache reset (avoid in prod!)
```
**Prevention:** Implement **automatic cache invalidation** on deploy.

---

### **3.4 Session/State Inconsistencies**
**Symptom:** Users logged in via Blue see data from Green (or vice versa).

**Fix:**
- **Sticky sessions** (session affinity in load balancer).
- Use **shared session storage** (Redis, database).

**Example: Sticky Session (Nginx)**
```nginx
http {
    upstream backend {
        zone backend 64k;
        server blue:8080 max_fails=3 fail_timeout=30s;
        server green:8080 max_fails=3 fail_timeout=30s;
    }
    server {
        location / {
            proxy_pass http://backend;
            proxy_cookie_domain off;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

### **3.5 API Versioning Conflicts**
**Symptom:** Backend API endpoints differ, causing 404s.

**Fix:**
- **Feature flags** to toggle endpoints.
- **Versioned endpoints** (`/v1/users`, `/v2/users`).

**Example: Spring Boot Versioned Endpoints**
```java
@RestController
@RequestMapping("/v2/users")
public class UserV2Controller { ... }
```

---

### **3.6 Resource Starvation (Green Crashes)**
**Symptom:** Green environment runs out of CPU/memory.

**Debugging Commands:**
```bash
# Check memory usage (Linux)
free -h
# Check CPU (10-second average)
top -c
```
**Fix:**
- **Scale Green** (auto-scaling groups, Kubernetes HPA).
- **Profile memory leaks** (Java: VisualVM, Python: `tracemalloc`).

---

## **4. Debugging Tools & Techniques**

| Tool | Purpose | Example Command |
|------|---------|-----------------|
| **Prometheus + Grafana** | Monitor metrics (latency, errors) | `curl http://localhost:9090/api/v1/query?query=up` |
| **ELK Stack (Elasticsearch)** | Aggregate logs | `kibana -server http://localhost:5601` |
| **Chaos Engineering (Gremlin)** | Test failure resilience | `grep -i "error" /var/log/nginx/error.log` |
| **Postman/Newman** | Validate API endpoints | `newman run collection.json` |
| **Database Dump Diff** | Compare DB schemas | `pg_dump -U user db_old > old.sql; pg_dump -U user db_new > new.sql` |

**Key Techniques:**
- **Canary Analysis:** Test a small % of traffic on Green first.
- **Blue-Green Health Checks:** Verify Green before switch.
  ```bash
  # Health check endpoint (HTTP 200 = ready)
  curl -s http://green-server:8080/health | grep -q "OK"
  ```
- **Rollback Script:** Automate reverting traffic to Blue.

---

## **5. Prevention Strategies**

### **5.1 Pre-Deployment Checklist**
1. **Smoke Test Green:** Deploy Green, test endpoints.
2. **Load Test:** Simulate production traffic (Locust, JMeter).
3. **Database Sync:** Verify no schema gaps.
4. **Cache Warm-up:** Pre-populate caches.
5. **Network Check:** Validate LB, DNS, and firewall rules.

### **5.2 Automated Safeguards**
- **Feature Flags:** Toggle critical features post-deploy.
- **Circuit Breakers:** Stop traffic if Green fails (e.g., Resilience4j).
- **Automated Rollback:** Trigger on error thresholds.

**Example: Resilience4j Circuit Breaker (Java)**
```java
@CircuitBreaker(name = "usersService", fallbackMethod = "fallback")
public User getUser(Long id) { ... }

public User fallback(UserRequest request, Exception e) {
    log.error("Service down, returning cached user", e);
    return cachedUser;
}
```

### **5.3 Post-Deployment Monitoring**
- **SLOs (Service Level Objectives):** e.g., "99.9% requests < 500ms".
- **Anomaly Detection:** Alert on spikes (e.g., Datadog, New Relic).
- **A/B Testing:** Compare Blue/Green performance metrics.

---

## **6. Rollback Plan**
If Green fails:
1. **Switch traffic back to Blue** (DNS TTL hack: `dig +short example.com`).
2. **Isolate Green** (stop sending traffic; kill pods in Kubernetes).
3. **Debug Green logs:**
   ```bash
   # Check Kubernetes pods
   kubectl logs -l app=green-service --previous
   # Check container logs
   docker logs green-container
   ```
4. **Fix and redeploy Green** (or rollback to Blue).

---

## **7. Summary of Key Actions**
| Issue | Immediate Action | Long-Term Fix |
|-------|------------------|---------------|
| Traffic misrouted | Check LB rules | Use feature flags |
| DB schema mismatch | Force migrations | Test migrations in staging |
| Caching stale | Purge caches | Automatic cache invalidation |
| Session issues | Sticky sessions | Shared session store |
| API conflicts | Version endpoints | Canary releases |

---
**Final Tip:** Blue-Green deployments are safe if you **validate the Green environment before switching traffic**. Always test in staging first!