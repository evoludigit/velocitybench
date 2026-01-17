# **Debugging On-Premise Monitoring: A Troubleshooting Guide**
*For Senior Backend Engineers*
*Version: 1.1 | Last Updated: [Date]*

---

## **1. Introduction**
On-Premise Monitoring involves host-based monitoring, log aggregation, and performance metrics collection within an internal data center or private cloud. Unlike cloud-managed solutions, on-premise setups require manual configuration, security hardening, and dependency management (e.g., agents, databases, and network assets).

This guide covers troubleshooting common failures in on-premise monitoring systems, focusing on **speed, efficiency, and practical fixes**.

---

## **2. Symptom Checklist**
Before diving into fixes, systematically verify these symptoms:

| **Category**               | **Symptoms**                                                                                                                                                                                                 |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Agent Issues**           | - Agents crashing or failing to start.                                                                                                                                                                 |
|                            | - High latency in metric collection (e.g., >10s delay).                                                                                                                                                         |
|                            | - Errors in agent logs (`permission denied`, `connection refused`, `timeouts`).                                                                                                                    |
| **Data Collection**        | - Missing or stale metrics in dashboards.                                                                                                                                                                  |
|                            | - Logs not being ingested into the central log collector (e.g., ELK, Splunk).                                                                                                                    |
|                            | - Alerts not firing despite critical conditions.                                                                                                                                                             |
| **Storage & Database**     | - Database queries timing out or failing (e.g., Prometheus, TimescaleDB, or custom DB).                                                                                                                 |
|                            | - Disk space exhaustion (agents/collectors filling up `/var/log` or DB storage).                                                                                                                       |
| **Network & Connectivity** | - Agents unable to reach central collector (e.g., `curl: (7) Failed to connect`).                                                                                                                         |
|                            | - High network latency between agents and collectors.                                                                                                                                                      |
| **Hardware & Resource**    | - CPU/memory overload on collector nodes.                                                                                                                                                               |
|                            | - Monitoring agents consuming excessive resources (e.g., `top` shows high CPU usage).                                                                                                                   |
| **Configuration Issues**   | - Misconfigured YAML/JSON files (e.g., wrong `target`, `interval`, or `auth` settings).                                                                                                                 |
|                            | - Certificates expired or misconfigured (HTTPS/TLS issues).                                                                                                                                                |

---

## **3. Common Issues & Fixes**

### **A. Agent Not Starting or Crashing**
#### **Symptoms**
- `systemctl status agent-service` shows `failed`.
- Agent logs (`/var/log/agent.log`) contain errors like:
  ```
  Failed to connect to Prometheus: dial tcp: lookup prometheus-server: no such host
  ```

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                                                                                                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Network misconfiguration**        | Verify `resolv.conf` has correct DNS entries.                                                                                                                                                            |
|                                     | Test connectivity: `nslookup prometheus-server` or `ping prometheus-server`.                                                                                                                          |
| **Missing permissions**             | Ensure the agent user (`monitoring-agent`) has read access to `/var/log/` and write access to `/var/lib/agent/`.                                                                                  |
|                                     | ```bash
     sudo chown -R monitoring-agent:monitoring-agent /var/log/
     sudo chmod -R 750 /var/lib/agent/
     ```                                                                                                                                                                                           |
| **Broken dependencies**            | Check for missing packages (e.g., `libcurl`, `python3-dev`).                                                                                                                                                  |
|                                     | ```bash
     sudo apt-get install -f  # For Debian/Ubuntu
     ```                                                                                                                                                                                             |
| **Misconfigured config file**      | Verify `agent.conf` has correct `server`, `port`, and `auth_token`.                                                                                                                                       |
|                                     | Example fix:                                                                                                                                                                                       |
|                                     | ```yaml
     # Before (wrong)
     server: localhost:9090
     # After (correct)
     server: prometheus-server:9090
     auth_token: "your-secure-token"
     ```                                                                                                                                                                                             |

---

### **B. Missing or Stale Metrics**
#### **Symptoms**
- Prometheus/Grafana shows no data for past 30+ minutes.
- Agents report `scrape failed` errors.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                                                                                                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Scrape interval too high**        | Default Prometheus scrape interval is `15s`. If agents are slow, reduce it:                                                                                                                             |
|                                     | ```yaml
     # prometheus.yml
     scrape_configs:
       - job_name: 'agent-jobs'
         scrape_interval: 5s  # Reduce if needed
         static_configs:
           - targets: ['agent-host:9100']
     ```                                                                                                                                                                                             |
| **Agent not reporting metrics**    | Check agent logs for `failed to scrape`. Example fix for a Prometheus client:                                                                                                                         |
|                                     | ```go
     // Ensure the collector registers correctly in main()
     func main() {
         prometheus.MustRegister(collector.NewMyCollector())
         http.Handle("/metrics", promhttp.Handler())
         log.Fatal(http.ListenAndServe(":9100", nil))
     }
     ```                                                                                                                                                                                             |
| **Prometheus target down**         | Verify `prometheus-cli` can connect:                                                                                                                                                                     |
|                                     | ```bash
     prometheus-cli --prometheus.url=http://prometheus-server:9090 --target=agent-host:9100 --query='up' --silence-errors
     ```                                                                                                                                                                                               |

---

### **C. Logs Not Being Ingested**
#### **Symptoms**
- ELK/Fluentd/Splunk shows no new logs.
- Agents log `Failed to post to Logstash`.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                                                                                                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Fluentd config error**            | Check `fluent.conf` for typos (e.g., `match` vs `filter`). Example fix:                                                                                                                               |
|                                     | ```conf
     # Before (wrong)
     match /var/log/*.log { type ltsv; }
     # After (correct)
     <match /var/log/*.log>
       type ltsv
     </match>
     ```                                                                                                                                                                                             |
| **Network filtering**              | Ensure no firewalls block UDP/TCP ports (e.g., `514` for Syslog, `24224` for Fluentd).                                                                                                                  |
|                                     | Test with:                                                                                                                                                                                            |
|                                     | ```bash
     telnet logstash-server 514
     ```                                                                                                                                                                                                |
| **Disk full on collector**         | Check `/var/log/` or Fluentd’s buffer directory (`/var/log/fluentd-buffer/`).                                                                                                                            |
|                                     | ```bash
     df -h /var/log
     ```                                                                                                                                                                                               |

---

### **D. Database Performance Issues**
#### **Symptoms**
- Slow queries (e.g., Prometheus `max scrapes per second` hit).
- Database crashes (`disk full` or `connection pool exhausted`).

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                                                                                                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **High cardinality metrics**       | Use `relabeling` to reduce labels (e.g., aggregate by `instance` instead of `pod`).                                                                                                                     |
|                                     | ```yaml
     # prometheus.yml
     relabel_configs:
       - source_labels: [__address__]
         target_label: instance
         regex: '([^:]+):.+'
         replacement: '$1'
     ```                                                                                                                                                                                             |
| **Prometheus storage full**        | Clean up long-retention data:                                                                                                                                                                        |
|                                     | ```bash
     # For Prometheus
     promtool check config /etc/prometheus/prometheus.yml
     ```                                                                                                                                                                                               |
| **TimescaleDB too slow**           | Add `hyperloglog` compression or adjust `timescale.enable_sparse_segments = on`.                                                                                                                       |
|                                     | ```sql
     ALTER TABLE metrics SET (timescale.enable_sparse_segments = on);
     ```                                                                                                                                                                                              |

---

## **4. Debugging Tools & Techniques**
### **A. Agent-Level Debugging**
| **Tool**               | **Usage**                                                                                                                                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `strace`               | Trace system calls for agents stuck in `S` state:                                                                                                                                                   |
|                        | ```bash
        strace -p $(pgrep -f "agent-service")
        ```                                                                                                                                                                                             |
| `netstat`/`ss`         | Check open ports/TCP connections:                                                                                                                                                                      |
|                        | ```bash
        ss -tulnp | grep agent
        ```                                                                                                                                                                                              |
| `journalctl`           | View systemd logs for agent failures:                                                                                                                                                                   |
|                        | ```bash
        journalctl -u agent-service -xe
        ```                                                                                                                                                                                         |

### **B. Network Diagnostics**
| **Tool**               | **Usage**                                                                                                                                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tcpdump`              | Capture network traffic between agent and collector:                                                                                                                                                 |
|                        | ```bash
        tcpdump -i any port 9100 -w agent_traffic.pcap
        ```                                                                                                                                                                                             |
| `ping`/`mtr`           | Check network latency/path issues:                                                                                                                                                                       |
|                        | ```bash
        mtr prometheus-server
        ```                                                                                                                                                                                               |
| `curl`/`telnet`        | Test HTTP/TLS connections:                                                                                                                                                                          |
|                        | ```bash
        curl -v http://prometheus-server:9090/metrics
        ```                                                                                                                                                                                             |

### **C. Log Aggregator Checks**
| **Tool**               | **Usage**                                                                                                                                                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `awk`/`grep`           | Filter logs for errors:                                                                                                                                                                              |
|                        | ```bash
        grep "ERROR" /var/log/agent.log | tail -10
        ```                                                                                                                                                                                             |
| `logrotate`            | Ensure logs aren’t growing uncontrollably:                                                                                                                                                              |
|                        | ```conf
        /var/log/agent.log {
          rotate 7
          daily
          compress
        }
        ```                                                                                                                                                                                              |

---

## **5. Prevention Strategies**
### **A. Proactive Monitoring**
- **Alert on Agent Health**: Use Prometheus alerts for:
  ```yaml
  - alert: AgentDown
    expr: up{job="agent-jobs"} == 0
    for: 5m
    labels: severity=critical
  ```
- **Log Rotation**: Automate log cleanup (e.g., `logrotate`).
- **Resource Limits**: Set `ulimit` for agents:
  ```bash
  sudo ulimit -n 65536  # Increase file descriptors
  ```

### **B. Configuration Management**
- **Use Infrastructure as Code (IaC)**:
  Example Terraform snippet for agents:
  ```hcl
  resource "linux_user" "monitoring_agent" {
    name         = "monitoring-agent"
    home         = "/home/monitoring-agent"
    shell        = "/bin/bash"
    ssh_authorized_keys = ["pub_key"]
  }
  ```
- **Validate Configs Pre-Deploy**:
  ```bash
  # Test Prometheus config
  promtool check config /etc/prometheus/prometheus.yml
  ```

### **C. Performance Tuning**
- **Agent Scraping Efficiency**:
  - Batch metrics (e.g., reduce `scrape_interval` for high-cardinality jobs).
  - Use `remote_write` to offload to a time-series DB (e.g., TimescaleDB).
- **Collector Scaling**:
  - Shard Prometheus for large environments.
  - Use `cortex` for distributed scraping.

---

## **6. Escalation Path**
If issues persist:
1. **Check vendor docs** (e.g., Prometheus [FAQ](https://prometheus.io/docs/introduction/faq/)).
2. **Reproduce in staging** before applying fixes to prod.
3. **Engage SRE/DevOps** for deep dives (e.g., `valgrind` for memory leaks).

---
**Final Note**: On-premise monitoring requires **daily attention to config drift and hardware health**. Automate checks where possible (e.g., `cron` jobs for log cleanup). Happy debugging!