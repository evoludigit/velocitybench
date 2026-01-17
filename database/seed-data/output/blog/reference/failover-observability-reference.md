# **[Pattern] Failover Observability – Reference Guide**

---

## **Overview**
Failover Observability is a **pattern for continuously monitoring system health and failover state changes** to ensure seamless recovery and minimal downtime during outages. This pattern ensures observability into:
- **Failover triggers** (e.g., health check failures, circuit breakers tripping).
- **Failover progression** (e.g., primary-to-secondary handoff, re-synchronization).
- **Failover outcomes** (e.g., successful recovery, retained data consistency).
- **Impact assessment** (e.g., latency spikes, error rates under failover).

It combines **metrics, logs, and traces** to detect, diagnose, and validate failover events in real time. Observability tools (e.g., Prometheus, Datadog, ELK) and custom telemetry (e.g., OpenTelemetry) feed into centralized dashboards and alerting systems to support proactive incident response.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Definition**                                                                                     | **Example Use Cases**                                                                               |
|---------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Failover Event**        | A critical state transition (e.g., primary node failure, active-active switch)                   | Detecting when a database replica is promoted to primary.                                           |
| **Failover Health**       | Metrics tracking failover latency, success rates, and data consistency after handoff.           | Monitoring *"replication lag"* during failover.                                                    |
| **Failover Impact**       | System-wide effects (e.g., increased errors, degraded throughput) during or after failover.     | Alerting on *"spike in 5xx errors"* post-failover.                                                 |
| **Observability Layer**   | Ingestion/processing layer (e.g., Prometheus scraping, OpenTelemetry collectors) for failover data. | Using Prometheus to scrape failover metrics from Kubernetes pods.                                  |
| **Alerting Policy**       | Rules triggering notifications (e.g., "promote_replica_failed" > 5 mins).                       | Sending Slack alerts when a failover takes longer than 30 seconds.                                  |
| **Post-Failover Validation** | Checks to ensure data integrity and system stability after failover.                          | Verifying *"read consistency"* across replicas post-failover.                                       |

---

### **Schema Reference**
#### **1. Failover Events Schema (Log Format)**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                          |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `event_id`              | String     | Unique identifier for the failover event.                                                          | `"failover_2024-05-20_14:30:00"`           |
| `event_type`            | String     | Type of failover (e.g., `"manual"`, `"automatic"`, `"circuit_break"`)                             | `"automatic"`                              |
| `timestamp`             | ISO8601    | When the failover was initiated.                                                                   | `"2024-05-20T14:30:00Z"`                   |
| `source_system`         | String     | System initiating the failover (e.g., `"k8s-controller"`, `"db_driver"`).                        | `"postgres_replica_manager"`                |
| `target_system`         | String     | System affected by the failover.                                                                  | `"user-service"`                           |
| `primary_node`          | String     | Original primary node before failover.                                                            | `"node-123"`                               |
| `new_primary_node`      | String     | Node promoted to primary.                                                                         | `"node-456"`                               |
| `status`                | String     | Failover outcome (`"success"`, `"partial"`, `"failed"`)                                            | `"success"`                                |
| `duration_ms`           | Integer    | Time taken for failover completion.                                                                | `4500`                                     |
| `data_loss`             | Boolean    | Whether data was lost during failover.                                                            | `false`                                    |
| `downtime_seconds`      | Integer    | Service downtime experienced by users.                                                            | `0`                                        |
| `related_trace_ids`     | Array      | Linked trace IDs for contextual requests during failover.                                         | `["trace_abc123", "trace_def456"]`         |

---
#### **2. Failover Health Metrics (Time-Series)**
| **Metric**               | **Description**                                                                                     | **Unit**       | **Labels**                          |
|--------------------------|---------------------------------------------------------------------------------------------------|----------------|-------------------------------------|
| `failover_latency`       | Time from failover trigger to completion.                                                          | Milliseconds   | `{system="user-service", node="node-456"}` |
| `replication_lag`        | Data replication delay post-failover (e.g., database lag).                                         | Seconds        | `{database="postgres", replica="r1"}` |
| `error_rate_post_failover` | Increased error rate after failover.                                                              | Percentage     | `{service="auth-service"}`          |
| `throughput_drop`        | Reduction in requests/second during failover.                                                     | Requests/sec   | `{endpoint="/api/v1/users"}`         |
| `health_check_failures`  | Failures of health checks after failover.                                                          | Count          | `{check="readiness"}`                |

---
#### **3. Failover Impact Schema (Log Format)**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Value**                          |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `event_id`              | String     | References the failover event (from above).                                                        | `"failover_2024-05-20_14:30:00"`           |
| `metric_name`           | String     | Name of impacted metric (e.g., `"error_rate"`, `"latency_p99"`).                                  | `"error_rate"`                             |
| `baseline_value`        | Float      | Pre-failover metric value.                                                                         | `0.01`                                     |
| `peak_value`            | Float      | Highest value observed post-failover.                                                              | `0.35`                                     |
| `recovery_time`         | Integer    | Time taken to return to baseline.                                                                    | `60`                                      |
| `severity`              | String     | Impact severity (`"critical"`, `"high"`, `"medium"`).                                               | `"high"`                                  |

---

## **Query Examples**
### **1. Detect Failover Events (Log Query)**
**Tool:** ELK (Logstash + Kibana) / Loki
**Query:**
```json
event_type: "automatic"
AND status: "success"
AND duration_ms > 5000
| timeslice(1m)
| count by _timeslice, status
```
**Output:**
Shows count of long-duration failovers per minute.

---
### **2. Alert on Replication Lag (Metrics Query)**
**Tool:** Prometheus
**Query:**
```promql
rate(postgres_replication_lag_bytes[5m]) / rate(postgres_replication_speed_bytes[5m])
> 60 * 1000  # >60 seconds lag
```
**Alert Rule:**
```yaml
- alert: ReplicationLagHigh
  expr: replication_lag_seconds > 60
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Replication lag high in {{ $labels.instance }}"
```

---
### **3. Trace Failover Impact (Distributed Tracing)**
**Tool:** Jaeger / OpenTelemetry
**Query:**
```
service: "user-service"
AND operation: "create_user"
AND timestamp > now()-30m
| filter span.kind = "SERVER"
| aggregate(span.duration, count)
```
**Output:**
Histograms of request latency spiking post-failover.

---
### **4. Post-Failover Data Consistency Check**
**Tool:** SQL / PromQL
**SQL (PostgreSQL):**
```sql
SELECT COUNT(*)
FROM user_table
WHERE created_at > NOW() - INTERVAL '10 minutes'
AND checkpoint_timestamp IS NULL;
-- Check for uncommitted transactions post-failover.
```
**PromQL:**
```promql
up{job="db_primary"} == 0
AND on() duration{job="db_failover"} > 60
```
**Action:** Investigate if the primary node recovered but failed to push updates.

---

## **Related Patterns**
| **Pattern**                 | **Description**                                                                                     | **Why It Matters**                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Limits cascading failures by stopping requests to failing services.                                | Failover Observability validates **when and why** a circuit breaker tripped.                      |
| **[Chaos Engineering](https://chaos.conf/)**                     | Deliberately introduces failures to test resilience.                                               | Observability data helps **correlate chaos experiments** with failover performance.               |
| **[Distributed Tracing](https://www.datadoghq.com/blog/distributed-tracing/)**          | Tracks requests across services to diagnose latency/issues.                                         | Traces help identify **which services were impacted** during failover.                            |
| **[Canary Releases](https://www.articulate.io/blog/canary-release)**               | Gradually rolls out changes to minimize blast radius.                                             | Observability tracks **failover impact** on canary vs. production traffic.                        |
| **[Multi-Region Failover](https://aws.amazon.com/architecture/)**               | Automates failover across geographic regions.                                                     | Observability ensures **global consistency** post-failover (e.g., DNS propagation delays).       |
| **[SLO-Based Alerting](https://sre.google/sre-book/monitoring-distystems/)**          | Alerts on SLO violations (e.g., "99.9% availability").                                             | Failover Observability **validates SLO recovery** after incidents.                               |

---

## **Best Practices**
1. **Instrument Failover Triggers:**
   - Log failover events with `event_type`, `timestamp`, and `source_system`.
   - Example: `logger.info("Failover initiated: primary=node-123, new_primary=node-456")`.

2. **Monitor Critical Paths:**
   - Track **replication lag**, **health check failures**, and **throughput drops** post-failover.

3. **Validate Data Consistency:**
   - Use **checksum comparisons** or **transaction logs** to verify no data was lost.

4. **Automate Recovery Validation:**
   - Write **Prometheus alert rules** or **OpenTelemetry pipelines** to flag anomalies.

5. **Document Failover Procedures:**
   - Include observability queries in **incident runbooks** for post-mortems.

6. **Simulate Failovers:**
   - Use **chaos tools** (e.g., Chaos Mesh) to test observability under failure scenarios.

---
## **Tools & Integrations**
| **Component**            | **Tools**                                                                                          | **Use Case**                                                                                     |
|--------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Metrics Collection**   | Prometheus, Datadog, New Relic, OpenTelemetry Collector                                           | Scraping `failover_latency`, `replication_lag`.                                                 |
| **Logs**                 | ELK Stack (Logstash, Elasticsearch, Kibana), Loki, Fluentd                                       | Logging failover events with `event_id` and `status`.                                           |
| **Distributed Traces**   | Jaeger, Zipkin, OpenTelemetry                                                    | Tracing user requests during failover to identify bottlenecks.                                  |
| **Alerting**             | PagerDuty, Opsgenie, Alertmanager (Prometheus), Datadog Alerts                                  | Notifying teams of long failover durations or data loss.                                         |
| **Visualization**        | Grafana, Datadog Dashboards, Kibana                                                            | Building dashboards for `failover_events_over_time` and `impact_metrics`.                        |
| **Chaos Testing**        | Gremlin, Chaos Mesh, Chaos Monkey                                                               | Simulating failovers to validate observability coverage.                                        |

---
## **Troubleshooting**
| **Issue**                          | **Observability Query**                                                                          | **Root Cause**                                                                                   |
|-------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Failover took >30 seconds           | `histogram_quantile(0.99, sum(rate(failover_duration_seconds_bucket[5m])) by (le)) > 30`   | Slow replica promotion (check `k8s-pod` scale-up time).                                           |
| Data inconsistency post-failover    | `sum by (replica) (postgres_replication_slots_active{state="lagging}) > 0`                  | Unapplied WAL segments (increase `max_wal_senders` in PostgreSQL).                               |
| Spiking error rates                  | `rate(http_requests_total{status=~"5.."}[5m]) > 3 * rate(http_requests_total[5m])`           | In-flight transactions dropped during failover (increase `connection_pool_size`).                 |
| Slow health checks                   | `up{job="health_checks"} == 0`                                                                 | Slow endpoint health checks (reduce TTL in `readinessProbe`).                                     |

---
## **Example Workflow**
1. **Failover Triggered:**
   - Primary node crashes → Kubernetes `PodDisruptionBudget` promotes replica.
   - **Observability:** Log event `event_id="failover_2024-05-20_14:30:00"`, `status="in_progress"`.

2. **Real-Time Monitoring:**
   - Prometheus alerts on `replication_lag_seconds > 10`.
   - Jaeger traces show `span.duration` spiking for `/api/users`.

3. **Validation:**
   - Run SQL check: `SELECT * FROM user_table WHERE created_at > NOW() - INTERVAL '5 mins'` to confirm no data loss.
   - Grafana dashboard shows `throughput_drop` recovering after 2 minutes.

4. **Post-Mortem:**
   - Query logs for `event_id="failover_2024-05-20_14:30:00"` to document duration and impact.
   - Adjust `replication_lag_threshold` in alerting based on findings.