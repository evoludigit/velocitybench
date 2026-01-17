---
# **Debugging On-Premise Observability: A Troubleshooting Guide**

## **1. Introduction**
On-Premise Observability involves monitoring, logging, and tracing applications deployed within an organization’s private infrastructure (e.g., VMs, bare-metal, Kubernetes clusters). Unlike cloud-native observability, on-premise setups often face unique challenges, including network restrictions, resource constraints, and legacy system integration. This guide provides a structured approach to diagnosing and resolving common observability-related issues.

---

## **2. Symptom Checklist**
Before diving into diagnostics, verify the following symptoms to narrow down the problem scope:

| **Category**               | **Symptoms**                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Data Collection**        | - No logs/traces/metrics appearing in the observability backend (e.g., Prometheus, Grafana, ELK).<br>- High latency in data ingestion.<br>- Missing critical log lines. |
| **Agent/Proxy Issues**     | - Agents (e.g., Fluentd, Promtail, OpenTelemetry Collector) failing to start.<br>- Connection timeouts to observability backends.<br>- High CPU/memory usage on agent nodes. |
| **Network/Proxy Problems** | - Firewall blocking traffic (e.g., HTTP(S), gRPC) between agents and collectors.<br>- DNS resolution failures.<br>- TLS/SSL handshake errors. |
| **Storage/Database Issues** | - Backend (e.g., Loki, Thanos, Elasticsearch) running out of disk space.<br>- Slow queries or timeouts in the observability UI.<br>- Corrupted data in log/metric storage. |
| **Kubernetes-Specific**    | - DaemonSets/CronJobs failing to deploy observability agents.<br>- Resource starvation (CPU/memory) in agent pods.<br>- Network policies blocking sidecar traffic. |
| **User Interface Issues**  | - Grafana dashboards not loading.<br>- Slow UI response times.<br>- Authentication failures (e.g., Prometheus RBAC). |

---

## **3. Common Issues and Fixes**

### **3.1 Data Not Being Collected**
#### **Symptom:**
Logs/traces/metrics are missing or incomplete in the observability backend.

#### **Root Causes & Fixes**
| **Root Cause**                          | **Diagnosis**                                                                 | **Fix**                                                                 |
|-----------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Agent misconfiguration**              | Check agent logs (`/var/log/fluentd/fluentd.log`, `promtail.log`).          | Verify agent config (e.g., `fluent.conf`, `scrape_configs.yaml`). Example fix for Promtail:<br>```yaml<br>scrape_configs:<br>- job_name: varlogs<br>  static_configs:<br>- targets: [localhost]<br>  paths: ["/var/log/containers/*.log"]<br>``` |
| **File permissions**                   | Agent cannot read log files.                                                 | Ensure agent runs with correct permissions (e.g., `chown -R fluentd:fluentd /var/log`). |
| **Network restrictions**               | Firewall blocking agent-to-backend traffic (e.g., port 80/443, 9090).        | Check `iptables`, `ufw`, or cloud security groups. Example rule for Prometheus:<br>`sudo iptables -A INPUT -p tcp --dport 9090 -j ACCEPT` |
| **Backend overload**                   | Loki/Elasticsearch throttling or crashing.                                   | Scale backend pods or optimize retention policies.<br>Example (Prometheus):<br>`--storage.tsdb.retention.time=30d --storage.tsdb.wal-compression=true` |
| **Grafana not fetching data**          | Dashboard queries timing out or returning no data.                           | Test API endpoints directly (e.g., `curl http://prometheus:9090/api/v1/query?query=up`). |

---

### **3.2 Agent Crashes or High Resource Usage**
#### **Symptom:**
Agents (e.g., Fluentd, OpenTelemetry Collector) frequently restart or consume excessive CPU/memory.

#### **Root Causes & Fixes**
| **Root Cause**                          | **Diagnosis**                                                                 | **Fix**                                                                 |
|-----------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Buffer overflow**                     | Logs accumulating in agent memory.                                           | Increase buffer settings:<br>```yaml<br>buffer_chain:<br>  flush_thread_count: 4<br>  retry_wait: 1s<br>  queue_limit_length: 8192<br>  chunk_limit_size: 2M<br>``` |
| **Plugin misconfiguration**             | Invalid plugin (e.g., incorrect `output` or `filter` plugin).                | Validate plugin configs with `fluent-cut` or `otelcol --config=config.yml`. |
| **Noisy neighbors**                     | Pods sharing a node cause resource contention.                              | Use resource requests/limits in Kubernetes:<br>```yaml<br>resources:<br>  requests:<br>    cpu: "100m"<br>    memory: "256Mi"<br>  limits:<br>    cpu: "500m"<br>    memory: "512Mi"<br>``` |
| **Slow disk I/O**                      | Agent struggling to write logs to disk.                                      | Monitor disk latency (`iostat -x 1`). Use faster storage (e.g., SSD).   |

---

### **3.3 Network/Proxy Issues**
#### **Symptom:**
Agents fail to connect to the observability backend.

#### **Root Causes & Fixes**
| **Root Cause**                          | **Diagnosis**                                                                 | **Fix**                                                                 |
|-----------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **DNS resolution failure**             | Hostname resolution fails (e.g., `prometheus-server` unreachable).            | Test DNS locally:<br>`nslookup prometheus-server`<br>Add to `/etc/hosts` if needed. |
| **TLS handshake errors**               | Invalid certificates or CACerts in the agent.                                 | Verify certs:<br>`openssl s_client -connect prometheus-server:443 -showcerts`<br>Update agent CA bundle:<br>`--tls.ca-file=/path/to/ca.crt` |
| **Proxy misconfiguration**              | Agent behind a corporate proxy but not configured to use it.                 | Configure proxy in agent:<br>```yaml<br>proxy:<br>  http_proxy: "http://proxy.example.com:8080"<br>  https_proxy: "http://proxy.example.com:8080"<br>``` |
| **Rate limiting**                      | Backend (e.g., Prometheus) rejecting too many requests.                       | Throttle agent scrape interval:<br>`scrape_interval: 30s` (default is often 15s). |

---

### **3.4 Storage/Database Problems**
#### **Symptom:**
Observability backend fails or degrades (e.g., slow queries, crashes).

#### **Root Causes & Fixes**
| **Root Cause**                          | **Diagnosis**                                                                 | **Fix**                                                                 |
|-----------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Disk space exhaustion**               | `/var/lib/prometheus`, `/var/lib/loki` full.                                | Monitor disk usage:<br>`df -h /var/lib`<br>Clean up old data or resize storage. |
| **Elasticsearch cluster issues**        | Node connectivity problems or shard allocation failures.                      | Check cluster health:<br>`curl -X GET 'http://elasticsearch:9200/_cluster/health?pretty'`<br>Rebalance shards if needed. |
| **Thanos compactor failing**           | Retention policies not working.                                              | Check compactor logs:<br>`journalctl -u thanos-compactor --no-pager -n 50` |
| **Slow queries in Loki**               | Too many concurrent queries or inefficient retention.                         | Optimize retention:<br>`--limits-config=/etc/loki/limits-config.yaml` with query-rate-limit. |

---

### **3.5 Kubernetes-Specific Issues**
#### **Symptom:**
Observability components fail to deploy or run in Kubernetes.

#### **Root Causes & Fixes**
| **Root Cause**                          | **Diagnosis**                                                                 | **Fix**                                                                 |
|-----------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **DaemonSet not running**              | Pods stuck in `CrashLoopBackOff`.                                            | Check logs:<br>`kubectl logs daemonset/promtail -n monitoring`          | Review DaemonSet spec for resource constraints or init containers. |
| **NetworkPolicy blocking traffic**     | Sidecars (e.g., Promtail) cannot communicate with application pods.         | Verify NetworkPolicy:<br>`kubectl describe networkpolicy -n monitoring`<br>Allow traffic:<br>`- protocol: TCP`<br>`  ports: ["9090"]` |
| **Pod evictions**                      | OOMKilled due to resource limits.                                            | Adjust limits or add vertical pod autoscaler (VPA).                     |
| **ConfigMaps/Secrets mismatches**      | Wrong config injected into pods.                                             | Verify ConfigMap:<br>`kubectl get cm promtail-config -n monitoring -o yaml`<br>Ensure versions match. |

---

## **4. Debugging Tools and Techniques**

### **4.1 Logs**
- **Agent Logs**: `journalctl -u fluentd` (systemd), `/var/log/fluentd/fluentd.log`.
- **Backend Logs**: `kubectl logs -n monitoring prometheus-server-0`.
- **Kubernetes Events**: `kubectl get events --sort-by='.metadata.creationTimestamp'`.

### **4.2 Metrics and Dashboards**
- **Prometheus**: Scrape system metrics (`node_exporter`):
  ```yaml
  scrape_configs:
  - job_name: 'node'
    static_configs:
    - targets: ['localhost:9100']
  ```
- **Grafana**: Test dashboards with direct API calls:
  ```bash
  curl http://grafana:3000/api/dashboards/uid/PROMETHEUS-ALERTMANAGER
  ```

### **4.3 Network Diagnostics**
- **Connectivity Tests**:
  ```bash
  # Test agent-to-backend connectivity
  telnet prometheus-server 9090
  # Check DNS resolution
  dig prometheus-server
  ```
- **Packet Capture**:
  ```bash
  tcpdump -i eth0 port 9090 -w debug.pcap
  ```

### **4.4 Performance Profiling**
- **CPU/Memory**:
  ```bash
  # Inside agent container
  perf top
  ```
- **Disk I/O**:
  ```bash
  iostat -x 1
  ```

### **4.5 Distributed Tracing**
- **OpenTelemetry Collector**: Enable auto-instrumentation:
  ```yaml
  receivers:
    otlp:
      protocols:
        grpc:
        http:
  ```
- **Jaeger/Zipkin**: Check trace sampling:
  ```bash
  curl http://jaeger:16686/api/traces
  ```

---

## **5. Prevention Strategies**
### **5.1 Design for Resilience**
- **Redundancy**: Deploy multiple agent instances (e.g., Fluentd pod anti-affinity rules).
- **Graceful Degradation**: Set resource limits and alerts for OOM/kills.
- **Schema Evolution**: Use schema registry (e.g., Confluent Schema Registry) for logs/metrics.

### **5.2 Monitoring the Observability System Itself**
- **Prometheus Blackbox Exporter**: Monitor agent health.
  ```yaml
  scrape_configs:
  - job_name: 'agent_health'
    metrics_path: '/probe'
    params:
      module: [http_2xx]
    static_configs:
    - targets: ['agent1:8080']
  ```
- **Alert on Agent Failures**:
  ```yaml
  - alert: FluentdDown
    expr: up{job="fluentd"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Fluentd instance {{ $labels.instance }} down"
  ```

### **5.3 Automated Testing**
- **Integration Tests**: Use `kafka-console-consumer` to verify log ingestion.
- **Chaos Engineering**: Simulate failures (e.g., kill agent pods) to test recovery.

### **5.4 Documentation and Runbooks**
- **As-Built Docs**: Document agent configs, backend retention policies, and alert rules.
- **Runbook Examples**:
  ```markdown
  **Agent Crash Runbook**
  1. Check logs: `kubectl logs daemonset/promtail -n monitoring`
  2. If buffer overflow: Increase `queue_limit_length` in config.
  3. If OOM: Scale up node or adjust limits.
  ```

### **5.5 Performance Optimization**
- **Compression**: Enable gzip for logs/metrics (e.g., `prometheus --web.enable-lifecycle`).
- **Retention Policies**: Set reasonable TTLs (e.g., 30 days for logs, 90 days for metrics).
- **Sampling**: Use probabilistic sampling for high-volume traces (e.g., `sampling_rate: 0.1`).

---

## **6. Conclusion**
On-premise observability requires proactive diagnostics and preventive measures. Focus on:
1. **Agent Health**: Logs, resource usage, and network connectivity.
2. **Backend Stability**: Disk, query performance, and retention.
3. **Kubernetes Optimization**: Resource limits, network policies, and DaemonSet health.
4. **Automation**: Alerts, runbooks, and testing to reduce MTTR.

**Key Takeaway**: If a symptom persists after basic checks, isolate the issue by comparing a working node to a failing one (e.g., `kubectl exec -it pod/promtail -- sh`).

---
**Further Reading**:
- [Prometheus Operator Best Practices](https://prometheus-operator.dev/docs/operator/)
- [Fluentd Performance Tuning](https://docs.fluentd.org/v1.0/articles/performance_tuning)
- [OpenTelemetry Collector Docs](https://opentelemetry.io/docs/collector/)