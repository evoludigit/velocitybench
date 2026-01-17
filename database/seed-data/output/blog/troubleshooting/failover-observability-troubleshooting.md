# **Debugging Failover Observability: A Troubleshooting Guide**

## **Introduction**
Failover Observability ensures that your system can detect, alert, and diagnose failures when primary services fail over to secondary (or tertiary) nodes. Poor failover observability can lead to:
- Undetected outages
- Slow recovery times
- Incomplete failover state accuracy
- Missing alerts for degraded performance

This guide helps troubleshoot common issues in failover systems, ensuring smooth detection, monitoring, and recovery.

---

## **Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **No failover alerts** | No notifications when primary fails over | Alerting system misconfiguration, health checks failing silently |
| **Incorrect failover state** | System reports wrong node as active | Health checks are unreliable, metrics delayed, or stale |
| **Slow failover detection** | Failover takes minutes instead of seconds | Health checks are too infrequent, monitoring agent lag |
| **Missing failover logs** | No logs indicating failover events | Logging disabled, log rotation truncating critical entries |
| **Partial state recovery** | Some services recover, others don’t | Dependencies not checked, health checks incomplete |
| **False failover triggers** | System incorrectly switches nodes | Health check threshold misconfigured, noise in metrics |
| **No metrics for failover path** | No visibility into secondary node performance | Metrics collection disabled, Prometheus/Grafana misconfigured |

If any of these symptoms persist, proceed with debugging.

---

## **Common Issues & Fixes**

### **1. No Failover Alerts**
**Symptom:** No alerts when a primary node fails over.
**Root Cause:**
- **Misconfigured health checks** (e.g., `livenessProbe` not set in Kubernetes)
- **Alerting system not monitoring failover events**
- **Health check delays** (stale metrics)

#### **Debugging Steps:**
- **Check health checks:**
  ```yaml
  # Example Kubernetes liveness/readiness probe
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10  # Too high → delayed detection
  ```
  - **Fix:** Ensure `periodSeconds` is low enough (e.g., `5-10s`).
  - **Verify:** `kubectl get pods -o wide` → Check `READY` status.

- **Inspect alerting rules (Prometheus/Grafana):**
  ```yaml
  # Example Prometheus alert rule
  - alert: NodeDown
    expr: up{job="app"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Node failed: {{ $labels.instance }}"
  ```
  - **Fix:** Ensure the rule fires on expected metrics.
  - **Verify:** `kubectl logs -n monitoring prometheus` → Check for alert triggers.

- **Check log tail for failover events:**
  ```sh
  journalctl -u app-service --no-pager | grep "failover"
  ```
  - If missing, enable structured logging (e.g., JSON logs with `failover` level).

---

### **2. Incorrect Failover State**
**Symptom:** System shows wrong node as active.
**Root Cause:**
- **Health checks are flaky** (network delays, random failures)
- **Metrics are stale** (Prometheus scrapes too infrequently)
- **State synchronization lag** (e.g., Redis, etcd not updating)

#### **Debugging Steps:**
- **Check health check reliability:**
  ```sh
  # Test HTTP health check manually
  curl -v http://<primary-node>:8080/health
  ```
  - If intermittent failures → **Fix:**
    - Increase timeout (`timeoutSeconds` in probes).
    - Use multiple endpoints (e.g., `/health`, `/metrics`).

- **Verify Prometheus scraping:**
  ```sh
  # Check if Prometheus is scraping correctly
  prometheus --config.file=/etc/prometheus/prometheus.yml --web.enable-lifecycle
  curl http://localhost:9090/api/v1/targets | jq '.data.targets[] | select(.labels.job == "app")'
  ```
  - If missing → **Fix:** Update `scrape_config` in Prometheus:
    ```yaml
    scrape_configs:
      - job_name: 'app'
        static_configs:
          - targets: ['primary-node:8080', 'secondary-node:8080']
    ```

- **Inspect cluster state (e.g., etcd, Consul):**
  ```sh
  # Check etcd cluster health
  ETCDCTL_API=3 etcdctl endpoint health --write-out=table
  ```
  - If stale → **Fix:** Restart unhealthy nodes or adjust leader election timeout.

---

### **3. Slow Failover Detection**
**Symptom:** Failover takes too long (e.g., >60s).
**Root Cause:**
- **Health checks run too infrequently** (`periodSeconds` too high).
- **Monitoring agent lag** (e.g., Prometheus scrape interval too long).
- **Network latency** between nodes.

#### **Debugging Steps:**
- **Reduce health check intervals:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 3
    periodSeconds: 5  # Reduced from 30s → 5s
  ```
  - **Verify:** `kubectl describe pod <pod-name>` → Check probe success rate.

- **Optimize Prometheus scraping:**
  ```yaml
  scrape_interval: 10s  # Default is 15s; reduce if needed
  evaluation_interval: 10s
  ```
  - **Verify:** `curl http://localhost:9090/status/buildinfo` → Check last scrape.

- **Check network latency:**
  ```sh
  # Test latency between nodes
  ping primary-node
  traceroute secondary-node
  ```
  - If high latency → **Fix:** Use regional failover or improve network.

---

### **4. Missing Failover Logs**
**Symptom:** No logs when failover occurs.
**Root Cause:**
- **Logging disabled** in failover logic.
- **Log rotation truncates entries.**
- **Logs not aggregated** (e.g., ELK stack misconfigured).

#### **Debugging Steps:**
- **Enable structured failover logs:**
  ```go
  // Example Go logging for failover
  log.Printf("FAILOVER: Primary %s failed, switching to %s",
    primaryNodeIP, secondaryNodeIP)
  ```
  - **Verify:** `kubectl logs <pod>` → Check for `FAILOVER` entries.

- **Adjust log rotation:**
  ```sh
  # Check logrotate config
  grep "failover" /etc/logrotate.d/*
  ```
  - **Fix:** If truncated → Increase log size limit (e.g., `size 1G`).

- **Check ELK/Grafana logs:**
  ```sh
  # Verify logs in Elasticsearch
  curl -X GET "http://elasticsearch:9200/_search?q=failover"
  ```
  - If missing → **Fix:** Update Fluentd/Logstash to capture failover tags.

---

### **5. False Failover Triggers**
**Symptom:** System incorrectly switches nodes.
**Root Cause:**
- **Health check threshold too low** (e.g., `failureThreshold=1`).
- **Noisy metrics** (spikes in CPU/memory).
- **Misconfigured alerting rules.**

#### **Debugging Steps:**
- **Adjust health check failure threshold:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    failureThreshold: 3  # Increase from default 3
    periodSeconds: 5
  ```
  - **Verify:** `kubectl describe pod` → Check probe failures.

- **Add metric smoothing:**
  ```promql
  # Use PromQL to filter noise
  rate(http_requests_total[1m]) > 1000
  ```
  - **Fix:** Adjust thresholds in alert rules.

- **Check alert rule logic:**
  ```yaml
  # Example: Only alert after 3 consecutive failures
  alert: FalseAlarm
    expr: up{job="app"} == 0 and on() group_left() sum by (pod) (rate(http_errors_total[5m]) > 0.1)
    for: 30s
  ```

---

## **Debugging Tools & Techniques**

| **Tool** | **Purpose** | **Example Command/Usage** |
|----------|------------|--------------------------|
| **kubectl** | Check pod/health status | `kubectl get pods -w` |
| **Prometheus** | Metrics & alert inspection | `curl http://prometheus:9090/api/v1/query?query=up{job="app"}` |
| **cURL** | Test API health checks | `curl -v http://<node>:8080/health` |
| **etcdctl** | Check cluster state | `ETCDCTL_API=3 etcdctl endpoint health` |
| **Journalctl** | View system logs | `journalctl -u app-service --since "1h ago"` |
| **Grafana** | Visualize failover events | Query `failover_alerts` dashboard |
| **tcpdump** | Network-level failures | `tcpdump -i eth0 port 8080` |
| **Promtail** | Log aggregation | `promtail -config.file=/etc/promtail/config.yml` |

---

## **Prevention Strategies**

### **1. Proactive Monitoring**
- **Set up synthetic transactions** (e.g., Locust) to test failover paths.
- **Use multi-dimensional alerts** (e.g., Prometheus `group_left()` for cross-node checks).

### **2. Reliable Health Checks**
- **Combine HTTP + TCP checks** (e.g., `tcpSocket` probe for database failover).
  ```yaml
  livenessProbe:
    tcpSocket:
      port: 5432  # PostgreSQL
    initialDelaySeconds: 10
  ```

### **3. Automated Failover Testing**
- **Chaos Engineering (Gremlin, Chaos Mesh):**
  ```sh
  # Simulate node failure
  chaos mesh inject pod app-pod --kill --duration 30s
  ```
- **Canary Deployments:** Test failover in staging before production.

### **4. Log & Metric Retention**
- **Retain failover logs for 30+ days** (e.g., Elasticsearch indices).
- **Archive metrics** (Prometheus remote write to Thanos).

### **5. Failover Circuit Breakers**
- **Implement retry policies with backoff** (e.g., Resilience4j).
  ```java
  CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("failover-breaker");
  circuitBreaker.executeSupplier(() -> fallbackService());
  ```

### **6. Cross-Team Validation**
- **Shared runbooks** for failover recovery.
- **Postmortems** after failover events to improve detection.

---

## **Conclusion**
Failover observability is critical for resilient systems. By systematically checking:
1. **Alerting & health checks** (are they firing?)
2. **Metrics & logs** (are they accurate?)
3. **Network & state sync** (is failover detected in time?)
you can resolve most failover issues efficiently.

**Key Takeaways:**
✅ **Reduce health check intervals** (`periodSeconds=5-10s`).
✅ **Validate alerting rules** ( Prometheus/Grafana).
✅ **Monitor logs** (`journalctl`, ELK).
✅ **Test failover proactively** (Chaos Engineering).

If issues persist, isolate the problem using `kubectl`, Prometheus, and cluster logs. For complex failures, involve DevOps/SRE teams early.

---
**Next Steps:**
- [ ] Audit current failover tests.
- [ ] Adjust health check thresholds.
- [ ] Set up automated failover alerts.