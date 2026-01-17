# **Debugging On-Premise Migration: A Troubleshooting Guide**

On-premise migration involves relocating applications, data, and infrastructure from a cloud or legacy system to an internal server environment. While this offers better control and security, it often introduces complex challenges—network latency, dependency conflicts, data corruption, and misconfiguration errors. This guide provides a structured approach to diagnosing and resolving common issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically verify these symptoms to narrow down root causes:

| **Symptom**                          | **Possible Causes**                          |
|--------------------------------------|---------------------------------------------|
| Application fails to start on-prem   | Missing dependencies, incorrect config, permissions |
| High latency in API/database calls   | Network misconfiguration, DNS mismatches, overly restrictive firewalls |
| Data inconsistency between old/new   | Incomplete migration, schema mismatches, ETL failures |
| Performance degradation              | Underpowered hardware, inefficient queries, disk I/O bottlenecks |
| Authentication/authorization errors | Incorrect RBAC, misconfigured credentials, session timeout issues |
| Logs indicate "Connection refused"   | Database server down, firewall blocking ports, misconfigured hostnames |
| Application crashes with "OutOfMemoryError" | Insufficient JVM heap, memory leaks, improper garbage collection tuning |
| Reverse proxy (e.g., Nginx/Apache) fails to route traffic | Misconfigured server blocks, SSL cert errors, load balancer misconfig |

**Action:**
- **Prioritize symptoms** based on criticality (e.g., app failures > performance degradation).
- **Check logs first** (application, OS, network) before making changes.

---

## **2. Common Issues & Fixes**

### **A. Application Deployment Failures**
#### **Issue:** *"Java app fails to start with `NoClassDefFoundError`"*
**Root Cause:** Missing JAR dependencies, incorrect classpath, or library version conflicts.
**Fix:**
1. **Verify `pom.xml`/`build.gradle`** ensures all dependencies are included.
   ```xml
   <!-- Example Maven dependency conflict resolution -->
   <dependencyManagement>
       <dependencies>
           <dependency>
               <groupId>org.springframework.boot</groupId>
               <artifactId>spring-boot-starter-web</artifactId>
               <version>3.1.0</version>
           </dependency>
       </dependencies>
   </dependencyManagement>
   ```
2. **Check `classpath` in `application.properties`:**
   ```properties
   spring.main.jvm-args="-Djava.library.path=/opt/libs/native"
   ```
3. **Use Maven/Gradle dependency trees** to detect conflicts:
   ```bash
   mvn dependency:tree
   ```

#### **Issue:** *"Docker container crashes with 'Permission denied'"*
**Root Cause:** Volume mounts or user permissions misconfigured.
**Fix:**
- Ensure the container runs with the correct user:
  ```dockerfile
  USER 1001  # Match OS user:ID
  ```
- Verify volume permissions:
  ```bash
  chown -R 1001:1001 /path/to/volume
  ```

---

### **B. Network & Connectivity Problems**
#### **Issue:** *"Database connection timeout"*
**Root Cause:** Firewall blocking ports, incorrect host resolution, or network routes.
**Debugging Steps:**
1. **Ping/database server:**
   ```bash
   ping db-server
   telnet db-server 5432  # For PostgreSQL
   ```
2. **Check `/etc/hosts`** for correct IP-to-hostname mapping:
   ```
   192.168.1.100 db-server internal
   ```
3. **Verify firewall rules (iptables/UFW):**
   ```bash
   sudo ufw allow 5432/tcp
   ```
4. **Enable proxy settings** in `application.yml` if behind a corporate proxy:
   ```yaml
   spring:
     cloud:
       inetutils:
         preferred-networks: 192.168
   ```

---

### **C. Data Migration Corruption**
#### **Issue:** *"Data incomplete/mismatched after migration"*
**Root Cause:** Schema drift, ETL tool failures, or incomplete transaction logs.
**Fix:**
1. **Compare schemas** between source and destination:
   ```bash
   # PostgreSQL example
   pg_dump -U user -h source -d db_source | grep -v "CREATE TABLE" > schema.sql
   psql -U user -h destination -d db_dest -f schema.sql
   ```
2. **Validate record counts** in critical tables:
   ```sql
   SELECT COUNT(*) FROM customers;  -- Run on both sides
   ```
3. **Re-run migration with logs** (e.g., AWS DMS, Talend):
   ```bash
   ./migration-tool --log-level=DEBUG --retries=3
   ```

---

### **D. Performance Bottlenecks**
#### **Issue:** *"Slow API responses (>2s)"*
**Root Cause:** N+1 queries, unoptimized DB indexes, or slow disk I/O.
**Fix:**
1. **Enable SQL query logging** (PostgreSQL):
   ```sql
   SET log_statement = 'all';
   ```
2. **Add indexes** for frequently queried fields:
   ```sql
   CREATE INDEX idx_user_email ON users(email);
   ```
3. **Use `EXPLAIN ANALYZE`** to identify slow queries:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
   ```
4. **Scale read replicas** if writes are bottleneck:
   ```yaml
   # Spring Data JPA config
   spring.datasource.url=jdbc:postgresql://read-replica:5432/db
   ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|-----------------------------------------------|---------------------------------------------|
| **Postman/curl**       | Test API endpoints                            | `curl -v http://localhost:8080/api/users`   |
| **tcpdump/Wireshark**  | Inspect network traffic                       | `sudo tcpdump -i eth0 port 8080`             |
| **Netdata**            | Real-time system monitoring                   | Install via: `bash <(curl -Ss https://my-netdata.io/kickstart.sh)` |
| **JProfiler/VisualVM** | JVM memory/thread analysis                    | `jvisualvm`                                  |
| **Grafana + Prometheus** | Metrics dashboards (latency, errors)       | `prometheus node_exporter`                  |
| **Redis CLI**          | Debug cache performance issues                | `redis-cli --stat`                           |

**Advanced Debugging:**
- **Enable debug logs** in `application.properties`:
  ```properties
  logging.level.org.springframework.web=DEBUG
  ```
- **Use `strace`** to trace system calls:
  ```bash
  strace -p <PID> -o debug.log
  ```

---

## **4. Prevention Strategies**
To minimize migration headaches, implement these best practices:

### **Pre-Migration**
1. **Blueprint & Documentation**
   - Document all dependencies (libraries, OS version, DB schema).
   - Use tools like **Terraform** for infrastructure-as-code (IaC).

2. **Test Environment Parity**
   - Replicate on-prem environment to match production (OS, JDK, container runtime).

3. **Blue-Green Deployment**
   - Deploy new version alongside old system; switch traffic gradually.

### **During Migration**
4. **Automated Rollback Plan**
   - Script to revert DB changes or redeploy old version:
     ```bash
     # Example: Trigger rollback on failure
     if [ $? -ne 0 ]; then
       ./rollback-migration.sh
     fi
     ```

5. **Monitor Key Metrics**
   - Set up alerts for:
     - High error rates (`5xx` responses).
     - Spikes in `GC time` (JVM).
     - Database connection pools exhaustion.

### **Post-Migration**
6. **Performance Benchmarking**
   - Compare on-prem vs. old system metrics (latency, throughput) using tools like **JMeter**.

7. **Regular Snapshots**
   - Backup DBs and configurations post-migration for quick recovery.

---

## **5. Quick Reference Cheat Sheet**
| **Scenario**               | **First Steps**                          | **Escalation Path**                     |
|----------------------------|------------------------------------------|-----------------------------------------|
| App crash on start         | Check logs, verify dependencies          | Revert to old version, engage dev team   |
| Slow DB queries            | Run `EXPLAIN`, add indexes               | Upgrade DB server, consider read replicas|
| Firewall blocking traffic  | Test connectivity, adjust rules          | Check with network team                 |
| Data loss                  | Verify ETL logs, compare record counts    | Restore from backup, re-migrate         |

---

## **Final Notes**
- **Isolate variables:** Test one component at a time (e.g., DB → app → network).
- **Leverage observability:** Tools like **Prometheus** and **ELK Stack** help correlate logs/metrics.
- **Communicate:** Align stakeholders on migration milestones and rollback plans.

By following this guide, you can diagnose and resolve on-premise migration issues systematically, minimizing downtime and ensuring a smooth transition.