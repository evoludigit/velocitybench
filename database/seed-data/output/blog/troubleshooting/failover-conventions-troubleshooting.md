# **Debugging Failover Conventions: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **Introduction**
Failover Conventions ensure high availability by automatically rerouting requests to backup services when primary nodes fail. Misconfigurations, network issues, or improper failover logic can disrupt service reliability. This guide provides a structured approach to diagnosing and resolving Failover Conventions-related problems.

---

## **Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Category**       | **Symptoms**                                                                 |
|--------------------|------------------------------------------------------------------------------|
| **Service Unavailability** | Primary nodes return errors (e.g., `503 Service Unavailable`)               |
| **Traffic Misrouting**       | Traffic diverted to secondary nodes despite primary being healthy          |
| **Cascading Failures**        | Secondary nodes also fail due to improper failover logic                     |
| **Performance Degradation**  | Latency spikes during failover transitions                                  |
| **Health Checks Fail**        | Service discovery (e.g., Consul, Eureka) returns unhealthy status           |
| **Logging Errors**            | Failover-related errors in application logs (e.g., `No Healthy Instances`) |

---

## **Common Issues and Fixes**

### **1. Failover Logic Misconfiguration**
**Symptom:**
Primary nodes fail even when healthy, or secondary nodes are overloaded.

**Root Causes:**
- Incorrect health check thresholds (e.g., `heartbeat_timeout` too low).
- Overly aggressive failover triggers (e.g., `max_retries=1`).

**Fixes:**
#### **Code Example: Adjusting Failover Thresholds (Go - Using Health Checks)**
```go
// Modify health check thresholds (e.g., in an HTTP client)
client := &http.Client{
    Timeout: 5 * time.Second,         // Low timeout forces failover faster
    Transport: &roundRobinTransport{
        FailoverThreshold: 2,         // Failover after 2 consecutive failures
        RetryDelay: 100 * time.Millisecond, // Delay before retrying
    },
}
```
#### **Configuration Fix (YAML - Kubernetes Liveness Probe)**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30  # Wait for app to start
  periodSeconds: 10         # Check every 10s
  failureThreshold: 3       # Failover after 3 failures
```

---

### **2. Network Partitioning (Split-Brain Scenario)**
**Symptom:**
Primary and secondary nodes can’t communicate, causing inconsistent states.

**Root Causes:**
- DNS resolution failures.
- Firewall rules blocking inter-service traffic.

**Fixes:**
#### **Diagnose Network Connectivity**
```bash
# Check DNS resolution from the app (replace `primary-service`)
dig primary-service
nslookup primary-service

# Test TCP connectivity
nc -zv primary-service 8080
```
#### **Fix Firewall Rules (AWS Security Groups)**
```bash
# Allow traffic between node groups
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxx \
  --protocol tcp \
  --port 8080 \
  --source-group sg-yyyyyy  # Secondary node’s SG
```

---

### **3. Service Discovery Failures**
**Symptom:**
Secondary nodes aren’t registered in the service registry (e.g., Consul, Eureka).

**Root Causes:**
- Misconfigured `serviceName` or `port` in service discovery.
- Registry server downtime.

**Fixes:**
#### **Verify Service Registration**
```bash
# Check Consul catalog (replace `service-name`)
consul catalog service service-name

# Output should list all healthy instances
```
#### **Fix Service Discovery Config (Spring Boot + Eureka)**
```properties
# application.properties
eureka.client.serviceUrl.defaultZone=http://eureka-server:8761/eureka
eureka.instance.preferIpAddress=true
eureka.instance.instanceId=${spring.application.name}:${spring.application.instance_id:${random.value}}
```

---

### **4. Load Balancer Stuck on Primary**
**Symptom:**
Traffic keeps routing to a dead primary node.

**Root Causes:**
- Stale health check results.
- Load balancer (e.g., NGINX, ALB) misconfiguration.

**Fixes:**
#### **NGINX Upstream Health Checks**
```nginx
upstream primary_service {
    least_conn;
    server primary-node-1:8080 max_fails=3 fail_timeout=30s;
    server primary-node-2:8080 backup;  # Secondary if primary fails
}
```
#### **AWS ALB Health Check Tuning**
```bash
aws elbv2 describe-load-balancers \
  --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef
```
Adjust:
```json
"HealthCheckPath": "/health",
"HealthCheckIntervalSeconds": 30,
"HealthCheckTimeoutSeconds": 5,
"HealthyThresholdCount": 2,
"UnhealthyThresholdCount": 3
```

---

### **5. Database Failover Latency**
**Symptom:**
Read replicas lag, causing stale data during failover.

**Root Causes:**
- Replication lag due to high write load.
- Read queries hitting primary instead of replicas.

**Fixes:**
#### **Optimize Replication (PostgreSQL)**
```sql
-- Check replication lag
SELECT pg_stat_replication;
-- Adjust WAL archiving
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 5;  # Increase replicas
```
#### **Route Queries to Replicas (Spring + Hibernate)**
```java
@Configuration
public class DataSourceConfig {
    @Bean
    @Primary
    public DataSource primaryDataSource() {
        // Primary DB config
    }

    @Bean("replicaDataSource")
    public DataSource replicaDataSource() {
        // Replica DB config
    }

    @Bean
    public DataSourceRoutingDataSource dataSource() {
        DataSourceRoutingDataSource ds = new DataSourceRoutingDataSource();
        ds.setDefaultTargetDataSource(primaryDataSource());
        ds.setTargetDataSources(Map.of("replica", replicaDataSource()));
        return ds;
    }
}
```

---

## **Debugging Tools and Techniques**

### **1. Log Analysis**
- **Key Logs to Check:**
  - Service discovery logs (e.g., `eureka-client`, `consul-agent`).
  - Load balancer logs (e.g., `nginx access.log`).
  - Application failover logs (e.g., `INFO: Failed over to secondary-node`).
- **Tools:**
  - `grep`/`awk`: Filter logs for failover events.
    ```bash
    grep "FAILOVER" /var/log/app.log | tail -20
    ```
  - ELK Stack: Correlate logs across services.

### **2. Distributed Tracing**
- **Tools:**
  - **Jaeger/OpenTelemetry**: Trace requests across primary/secondary nodes.
  - **Example Jaeger Query:**
    ```
    service:my-service AND operation:failover
    ```
- **Debugging Flow:**
  1. Identify a failing request in Jaeger.
  2. Check if it bypassed the health check.

### **3. Health Check Monitoring**
- **Synthetic Checks:**
  - Use **Grafana Synthetic Monitoring** to simulate failover.
    ```bash
    curl -v http://primary-service/health
    ```
- **Alerting:**
  - Set up alerts for:
    - `HealthCheckFailed` > 5 minutes.
    - `FailoverAttempts` > 3 in 1 minute.

### **4. Network Debugging**
- **Tools:**
  - `tcpdump`: Capture traffic between nodes.
    ```bash
    sudo tcpdump -i eth0 port 8080
    ```
  - `mtr`: Check latency to all nodes.
    ```bash
    mtr --report primary-node-1
    ```

### **5. Chaos Engineering**
- **Simulate Failures:**
  - **Chaos Mesh**: Kill pods randomly to test failover.
    ```yaml
    # chaos-mesh.yaml
    apiVersion: chaos-mesh.org/v1alpha1
    kind: PodChaos
    metadata:
      name: pod-failover-test
    spec:
      action: pod-failure
      mode: one
      selector:
        namespaces:
          - default
        labelSelectors:
          app: my-service
      duration: "1m"
    ```

---

## **Prevention Strategies**

### **1. Automated Failover Testing**
- **CI/CD Pipeline:**
  - Add a **failover smoke test** after deployments.
    ```bash
    # Example: Fail a primary node and verify traffic redirects
    kubectl delete pod -l app=my-service --force --grace-period=0
    ```
- **Tools:**
  - **EnvoyProxy**: Canary testing with gradual failover.

### **2. Circuit Breakers**
- **Implement Resilience Patterns:**
  - **Hystrix/Resilience4j**: Prevent cascading failures.
    ```java
    @HystrixCommand(fallbackMethod = "fallback")
    public String getDataFromPrimary() {
        // Call primary node
    }

    public String fallback() {
        return "Secondary node fallback";
    }
    ```

### **3. Blue/Green Deployments**
- **Reduce Downtime:**
  - Deploy to a secondary node first, then switch traffic.
    ```bash
    # AWS ALB: Update target groups
    aws elbv2 update-target-group-attributes \
      --target-group-arn tg-xxxxxx \
      --attributes Key=load_balancing_algorithm_type,Value=round_robin
    ```

### **4. Multi-Region Failover**
- **Geographically Distributed:**
  - Use **DNS failover** (e.g., Route 53 Latency-Based Routing).
    ```bash
    aws route53 change-resource-record-sets \
      --hosted-zone-id ZXXXYYY \
      --change-batch file://dns-failover.json
    ```

### **5. Documentation and Runbooks**
- **Failover Runbook:**
  - Document steps for manual failover (e.g., promote a replica).
    ```markdown
    ## Manual Failover Procedure
    1. Check replica health: `kubectl get pods -l app=my-service`.
    2. Promote replica: `kubectl patch service my-service -p '{"spec":{"selector":{"pod-template-hash":"replica-xyz"}}'`.
    ```
- **Postmortems:**
  - After failovers, analyze:
    - Root cause.
    - Duration.
    - Impact on users.

---

## **Conclusion**
Failover Conventions are critical for high availability, but misconfigurations can lead to outages. This guide covered:
1. **Symptom checklists** to identify issues quickly.
2. **Common fixes** for failover logic, networking, and service discovery.
3. **Debugging tools** (logs, tracing, chaos testing).
4. **Prevention strategies** (circuit breakers, blue/green, documentation).

**Next Steps:**
- Schedule **failover drills** quarterly.
- Monitor **failover metrics** (e.g., `failover_latency`).
- Automate **rollbacks** if failover degrades performance.

By following this guide, you can resolve failover issues efficiently and maintain system resilience.