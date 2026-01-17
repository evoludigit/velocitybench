# **Debugging Logging and Monitoring: A Troubleshooting Guide**

## **Introduction**
Logging and monitoring are critical components of any backend system. Proper logging helps track application behavior, diagnose errors, and audit activity, while monitoring ensures system health, performance, and alerting when issues arise.

This guide focuses on **debugging common issues** related to logging and monitoring implementations, providing **symptom checks, root cause analysis, fixes, tools, and prevention strategies** for a smooth debugging experience.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which logging/monitoring issue you’re dealing with:

| **Symptom** | **Possible Cause** | **Severity** |
|-------------|-------------------|-------------|
| Logs not appearing in the **log aggregator** (ELK, Splunk, Firebase Logs) | Misconfigured log forwarder (Fluentd, Filebeat, Logstash) | High |
| Logs appear **delayed** or **incomplete** | Buffering issues, high volume, or slow shipment | Medium |
| **Missing critical logs** (e.g., errors, DB queries) | Incorrect log level, log filtering, or dead code | High |
| Monitoring **alerts firing incorrectly** (false positives/negatives) | Poorly defined thresholds, metric sampling issues | Medium |
| **High CPU/memory usage** by log processing tools | Log volume spikes, inefficient log parsing | High |
| **No logs in application output** (stdout/stderr) | Console logging disabled, wrong log level | Medium |
| **Deadlocks in log aggregation pipeline** | Slow consumers, log shipper failures | Critical |
| **Slow log retrieval** from the monitoring dashboard | Poorly indexed logs, query inefficiencies | Medium |

---

## **2. Common Issues and Fixes**

### **2.1 Logs Not Appearing in Log Aggregator**
#### **Symptoms:**
- No logs in Elasticsearch/Kibana, Splunk, or Datadog.
- Log forwarder (e.g., Fluentd) shows no errors but no logs shipped.

#### **Root Causes & Fixes**
| **Root Cause** | **Code/Config Fix** | **Verification Step** |
|---------------|-------------------|----------------------|
| **Log forwarder not running** | Ensure Fluentd/Filebeat is running: `systemctl status fluentd` | Check service status |
| **Incorrect output plugin config** | Verify Fluentd config (`/etc/fluent/fluent.conf`): | `fluent-gem list` to check installed plugins |
```ini
<source>
  @type tail
  path /var/log/app.log
  pos_file /var/log/fluentd.pos
  tag app.logs
</source>

<match app.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
</match>
```
| **Missing log tags** | Ensure logs include structured metadata: | Check if `tag` matches in Fluentd |
```python
# Python (structlog)
import structlog
logger = structlog.get_logger()
logger.info("user_login", user=current_user_id, status="success")
```
| **Permission issues** | Check if log file is readable: `ls -l /var/log/app.log` | Test with `tail -f /var/log/app.log` |
| **Network/firewall blocking** | Test connectivity to Elasticsearch: `telnet elasticsearch 9200` | Check firewall rules (`ufw status`) |

#### **Debugging Steps:**
1. **Check log forwarder logs:**
   ```bash
   journalctl -u fluentd -f  # Systemd
   tail -f /var/log/fluentd/fluentd.log
   ```
2. **Test log shipment manually:**
   ```bash
   fluent-cat app.logs
   ```
3. **Verify Elasticsearch index pattern:**
   ```bash
   curl -XGET 'http://elasticsearch:9200/_cat/indices?v'
   ```

---

### **2.2 Logs Delayed or Incomplete**
#### **Symptoms:**
- Logs appear **minutes/hours later** than they were written.
- Some logs are **missing chunks**.

#### **Root Causes & Fixes**
| **Root Cause** | **Solution** | **Verification** |
|---------------|-------------|----------------|
| **High log volume overwhelming forwarder** | Increase Fluentd buffer size: | Check Fluentd log for buffer errors |
```ini
<source>
  @type tail
  path /var/log/app.log
  buffer_chunk_limit 4M  # Increase from default (256k)
  buffer_queue_limit 8  # Increase if many logs pending
</source>
```
| **Slow log parser** | Optimize `filter` plugins | Benchmark parsing time |
```ini
<filter app.**>
  @type parser
  key_name log
  reserve_data true
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</filter>
```
| **Elasticsearch indexing slow** | Increase Elasticsearch nodes/ram | Monitor ES indices with `curl http://elasticsearch:9200/_nodes/stats` |
| **Dead letter queue (DLQ) full** | Flush or increase DLQ capacity | Check Fluentd DLQ: `fluent-gem list | grep dead_letter` |

#### **Debugging Steps:**
1. **Check Fluentd buffer stats:**
   ```bash
   fluent-gem list | grep buffer
   ```
2. **Monitor Elasticsearch bulk requests:**
   ```bash
   curl -XGET 'http://elasticsearch:9200/_nodes/stats/indices/_bulk'
   ```
3. **Enable Fluentd debug logs:**
   ```ini
   <system>
     log_level debug
   </system>
   ```

---

### **2.3 Missing Critical Logs (e.g., Errors, DB Queries)**
#### **Symptoms:**
- **Error logs not appearing** in log aggregator.
- **Database queries not logged** despite `DEBUG` level.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example Code** |
|---------------|---------|----------------|
| **Wrong log level** | Set correct log level in config | Python (`logging.config.dictConfig`) |
```python
logging.basicConfig(
    level=logging.DEBUG,  # Ensure DEBUG is enabled
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```
| **Log filtering (e.g., `filter` in Fluentd)** | Remove filters blocking critical logs | Check Fluentd `filter` section |
```ini
<filter app.**>
  @type grep
  <exclude>
    key log_level
    pattern ".*INFO.*"  # Remove if blocking debug
  </exclude>
</filter>
```
| **Logs not going to stdout** | Redirect logs to stderr/stdout | Docker example in `Dockerfile` |
```dockerfile
ENTRYPOINT ["python", "-m", "gunicorn", "--log-level=debug", "app:app"]
```
| **Dead code (e.g., `if DEBUG: logger.debug()`)** | Ensure logging is uncommented | Search for `if DEBUG:` in codebase |

#### **Debugging Steps:**
1. **Check log levels in code:**
   ```bash
   grep -r "logging\.debug\|logger\.debug" .
   ```
2. **Test locally with `stderr` capture:**
   ```bash
   python app.py 2>&1 | grep "ERROR"
   ```
3. **Verify Fluentd `match` rules:**
   ```bash
   fluent-cat app.errors  # Test error logs
   ```

---

### **2.4 Incorrect Alerts (False Positives/Negatives)**
#### **Symptoms:**
- **Too many false alerts** (e.g., `5xx errors` when none exist).
- **Critical errors not alerting** despite happening.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example (Prometheus Alert)** |
|---------------|---------|-------------------------------|
| **Threshold too sensitive** | Adjust `for` and `threshold` values | Prometheus AlertRules |
```yaml
groups:
- name: error-rate-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 10m  # Wait 10m before firing
    labels:
      severity: critical
    annotations:
      summary: "High error rate on {{ $labels.instance }}"
```
| **Metric sampling issues** | Increase sample frequency | Check Prometheus `scrape_interval` |
```yaml
scrape_configs:
- job_name: 'app'
  scrape_interval: 15s  # Default is 15s, reduce if needed
```
| **Missing labels in logs** | Ensure logs include `error`/`status` fields | Structured logging example |
```python
logger.error("Failed request", extra={
    "url": request.url,
    "status": 500,
    "user": current_user.id
})
```
| **Alertmanager misconfiguration** | Check `inhibit_rules` | Test with `prometheus-alertmanager --config.file=alertmanager.yml` |

#### **Debugging Steps:**
1. **Check Prometheus metrics:**
   ```bash
   curl http://prometheus:9090/api/v1/query?query=http_requests_total{status=~"5.."}
   ```
2. **Test alert rules locally:**
   ```bash
   promtool check rules alert_rules.yaml
   ```
3. **Verify alertmanager logs:**
   ```bash
   journalctl -u alertmanager -f
   ```

---

### **2.5 High CPU/Memory Usage by Log Processing Tools**
#### **Symptoms:**
- **Fluentd/Logstash consuming 100% CPU.**
- **Elasticsearch running out of memory.**

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Monitoring Command** |
|---------------|---------|----------------------|
| **High log volume** | Scale Fluentd workers | `htop` to check CPU usage |
```ini
<source>
  @type tail
  thread_count 4  # Increase for high volume
</source>
```
| **Inefficient log parsing** | Use `kibana` or `grok` optimizations | Test parse speed |
```ini
<filter app.**>
  @type parser
  key_name message
  <parse>
    @type json
    time_format %Y-%m-%dT%H:%M:%S.%NZ
    timezone "UTC"
  </parse>
</filter>
```
| **Elasticsearch heap too small** | Adjust `elasticsearch.yml` | Check JVM stats |
```yaml
# elasticsearch.yml
bootstrap.memory_lock: true
xms: 4g
xmx: 4g  # Set to 50-60% of available RAM
```
| **Buffering issues** | Tune Fluentd buffer settings | Monitor `buffer_full` events |
```ini
<match app.**>
  @type elasticsearch
  buffer_type file
  buffer_chunk_limit 8M
  buffer_queue_limit 8
</match>
```

#### **Debugging Steps:**
1. **Check Fluentd performance:**
   ```bash
   fluent-gem list | grep perf
   ```
2. **Monitor Elasticsearch JVM:**
   ```bash
   curl http://elasticsearch:9200/_nodes/stats/jvm
   ```
3. **Enable Fluentd profiling:**
   ```ini
   <system>
     enable_ruby_api true
   </system>
   ```

---

### **2.6 Deadlocks in Log Aggregation Pipeline**
#### **Symptoms:**
- **Logs stuck in Fluentd queue** for hours.
- **Elasticsearch refusing connections** (`connection refused`).

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Verification** |
|---------------|---------|----------------|
| **Elasticsearch down** | Restart ES or check cluster health | `curl http://elasticsearch:9200/_cluster/health` |
```json
{
  "status": "red",  # Indicates issues
  "timed_out": true
}
```
| **Fluentd buffer full** | Increase `buffer_queue_limit` | Check `buffer_full` in logs |
```ini
<match app.**>
  buffer_queue_limit 16  # Default is 8
</match>
```
| **Network partition** | Check DNS/resolver issues | `dig elasticsearch` |
| **Zookeeper/Kafka dead** | Restart dependent services | For Kafka: `systemctl restart zookeeper` |

#### **Debugging Steps:**
1. **Check Fluentd queue depth:**
   ```bash
   fluent-gem list | grep queue
   ```
2. **Test Elasticsearch connectivity:**
   ```bash
   curl -XGET 'http://elasticsearch:9200/_cluster/health?pretty'
   ```
3. **Enable Fluentd debug mode:**
   ```ini
   <system>
     log_level debug
   </system>
   ```

---

## **3. Debugging Tools and Techniques**
### **3.1 Essential Tools**
| **Tool** | **Purpose** | **Command/Usage** |
|----------|------------|------------------|
| **`fluent-gem list`** | List installed Fluentd plugins | `fluent-gem list \| grep tail` |
| **`tail -f`** | Check real-time logs | `tail -f /var/log/fluentd/fluentd.log` |
| **`curl`** | Test API endpoints | `curl -XGET 'http://elasticsearch:9200/_cat/indices'` |
| **`journalctl`** | Check systemd service logs | `journalctl -u fluentd -f` |
| **Prometheus + Grafana** | Monitor metrics | `http://grafana:3000/d/` |
| **Elasticsearch Dev Tools** | Run queries directly | `curl -XGET 'localhost:9200/_search?q=status:error'` |
| **`strace`** | Debug system calls | `strace -f fluentd` |
| **`perf`** | Profile CPU usage | `perf top -p <PID>` |

### **3.2 Debugging Techniques**
1. **Log Level Adjustment**
   - Temporarily set `log_level debug` in Fluentd to get verbose logs.
   ```ini
   <system>
     log_level debug
   </system>
   ```

2. **Dummy Log Injection**
   - Test log shipment with a dummy log:
   ```bash
   echo '{"message":"test","level":"ERROR"}' > /var/log/test.log
   fluent-cat app.errors  # Should appear in Elasticsearch
   ```

3. **Elasticsearch Index Analysis**
   - Check if logs are indexed correctly:
   ```bash
   curl -XGET 'http://elasticsearch:9200/app_logs/_search?q=*'
   ```

4. **Prometheus Alert Testing**
   - Dry-run alerts:
   ```bash
   promtool check alerts alert_rules.yaml
   ```

5. **Network Tracing**
   - Check TCP connections:
   ```bash
   ss -tulnp \| grep fluentd
   ```

---

## **4. Prevention Strategies**
### **4.1 Logging Best Practices**
✅ **Use Structured Logging** (JSON, StructLog) for easier parsing.
✅ **Set Appropriate Log Levels** (`ERROR`, `WARN`, `INFO`, `DEBUG`).
✅ **Include Metadata** (user ID, request ID, timestamps).
✅ **Log Errors with Context** (e.g., `logger.error("Failed login", user=user_id)`).
✅ **Rotate Logs** to prevent disk issues (`logrotate`).

### **4.2 Monitoring Optimization**
✅ **Set Realistic Thresholds** (avoid alert fatigue).
✅ **Use Sampling for High-Volume Metrics** (e.g., Prometheus `rate()`).
✅ **Monitor Log Shipper Performance** (Fluentd/Logstash metrics).
✅ **Auto-scale Elasticsearch** for high log volumes.
✅ **Use Dead Letter Queues (DLQ)** for failed log shipments.

### **4.3 Infrastructure Considerations**
✅ **Separate Log and App Servers** to avoid contention.
✅ **Use Persistent Storage for Logs** (avoid `tmpfs`).
✅ **Backup Log Aggregator Data** (Elasticsearch snapshots).
✅ **Test Failover Scenarios** (e.g., Fluentd restart, ES node failure).
✅ **Use Log Compression** (e.g., `gzip` for cold logs).

### **4.4 CI/CD Checks**
✅ **Validate Log Config in Tests** (mock Fluentd output).
✅ **Run Alert Rule Checks** in CI (`promtool`).
✅ **Log Level Enforcement** (e.g., `flake8` check for `debug` logs in production).

---

## **5. Conclusion**
Debugging logging and monitoring issues requires a **systematic approach**:
1. **Identify symptoms** (missing logs, false alerts, delays).
2. **Check logs/configs** (Fluentd, Elasticsearch, Prometheus).
3. **Fix root causes** (buffering, thresholds, permissions).
4. **Prevent recurrence** (structured logging, auto-scaling, CI checks).

By following this guide, you can **quickly isolate and resolve** logging/monitoring problems while ensuring **scalable, reliable** systems.

---
**Next Steps:**
- **For Fluentd issues:** Review [Fluentd Debugging Guide](https://docs.fluentd.org/v/1.0/articles/debugging).
- **For Elasticsearch:** Use [Elasticsearch Dev Tool](https://www.elastic.co/guide/en/elasticsearch/reference/current/devtools.html).
- **For Prometheus:** Check [Alertmanager Docs](https://prometheus.io/docs/alerting/latest/alertmanager/).