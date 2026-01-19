# **[Pattern] Scaling Troubleshooting – Reference Guide**

---
## **Overview**
This guide provides systematic troubleshooting methods for resolving performance bottlenecks and scaling issues in distributed systems, microservices, or cloud-native applications. Scaling problems manifest as degraded performance, increased latency, or system failures under load. This reference outlines **key concepts**, **diagnostic schemas**, **troubleshooting queries**, and **related patterns** to identify and mitigate scaling issues efficiently.

The approach follows a **structured flow**:
1. **Define scaling goals** (horizontal/vertical, reactive/proactive).
2. **Monitor and collect metrics** (CPU, memory, network, I/O, concurrency).
3. **Identify bottlenecks** (CPU-bound, memory leaks, network saturation).
4. **Apply fixes** (scaling policies, optimizations, or refactoring).
5. **Validate and iterate** (load testing, scaling thresholds).

---
## **Implementation Details**
### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                                                 |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Throughput**         | Requests per second (RPS) handled by the system.                             | 1,000 RPS at P95 latency of 100ms.                                             |
| **Latency**            | Time taken to process a single request.                                      | P99 latency of 500ms during peak hours.                                       |
| **Concurrency Limits** | Maximum simultaneous active requests or connections.                       | Database connection pool maxed at 1,000.                                     |
| **Resource Saturation**| A resource (CPU, memory, disk) nearing or exceeding its capacity.           | 95% CPU utilization across all nodes.                                         |
| **Caching Layer**      | Temporarily stores frequent queries to reduce backend load.                  | Redis cache for API responses.                                               |
| **Queuing System**     | Decouples producers/consumers (e.g., Kafka, RabbitMQ) to handle spikes.      | Kafka topic backlog grows during traffic surges.                              |
| **Partitioning**       | Distributes data across nodes (sharding, database partitioning).              | User data split across 10 DB shards.                                         |
| **Autoscaling**        | Dynamically adjusts resources (e.g., Kubernetes HPA, AWS Auto Scaling).     | EC2 instances scale from 2 to 10 during rush hour.                          |

---

### **Troubleshooting Schema Reference**
Use this schema to systematically diagnose scaling issues. Prioritize based on **impact** and **detectability**.

| **Category**           | **Metrics to Monitor**               | **Tools/Commands**                          | **Bottleneck Indicators**                          | **Recommended Fixes**                                  |
|------------------------|--------------------------------------|--------------------------------------------|---------------------------------------------------|-------------------------------------------------------|
| **CPU**                | `utilization`, `context switches`    | `top`, `htop`, Prometheus (`rate(cpu_usage{})`) | >80% CPU for >5min, excessive context switching.  | Optimize algorithms, horizontal scaling, upgrade CPU.  |
| **Memory**             | `RSS`, `heap usage`, `GC pauses`     | `free -m`, `jstat`, `valgrind`, Prometheus (`process_resident_memory_bytes`) | OOM errors, GC pauses >200ms, memory growth spikes. | Reduce memory leaks, increase heap size, offload to disk. |
| **Network**            | `bandwidth`, `packet loss`, `latency`| `netstat`, `tcpdump`, `iperf`, Prometheus (`network_received_bytes_total`) | High latency (>500ms), TCP retransmissions, bandwidth saturation. | Optimize serializations (Protobuf/Avro), increase MTU, load balance. |
| **Disk I/O**           | `read/write ops`, `latency`          | `iostat`, `iotop`, `fio`, Prometheus (`filesystem_operations_total`) | Disk queue length >5, read latency >10ms.        | Add SSDs, partition databases, optimize queries.       |
| **Database**           | `query latency`, `connections`, `locks`| `slowlog`, `pg_stat_activity`, `EXPLAIN ANALYZE` | Long-running queries (>1s), connection leaks, deadlocks. | Index optimization, query caching, connection pooling. |
| **Concurrency**        | `active requests`, `queue length`    | `netdata`, `Prometheus (http_requests_in_flight)` | Queue backlog grows, 429 Too Many Requests.      | Rate limiting, async processing, increase workers.   |
| **Dependency Latency** | `external API calls`, `timeout`       | `OpenTelemetry`, `Harness`, `Grafana`     | External API latency >500ms, timeouts.           | Cache responses, retry with jitter, circuit breakers. |

---
### **Query Examples**
#### **1. CPU Bottleneck**
**Command:**
```bash
# Check CPU usage per process (Linux)
top -c -n 1 | grep -E 'java|node|nginx'

# Prometheus query (CPU saturation)
rate(container_cpu_usage_seconds_total{container="your-pod"}[5m]) by (instance) > 0.85
```

**Grafana Dashboard Alert:**
```
sum(rate(container_cpu_usage_seconds_total{label="your-app"}[5m]))
by (pod) > 80
```

#### **2. Memory Leak (Java)**
**Command:**
```bash
# Check heap dump (for Java)
jmap -heap <PID>
# Analyze with Eclipse MAT or YourKit
```

**Prometheus Query:**
```
process_resident_memory_bytes{job="your-app"} / process_max_resident_memory_bytes{job="your-app"} > 0.9
```

#### **3. Database Slow Query**
**PostgreSQL:**
```sql
-- Analyze slow queries (log to file if not enabled)
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check locks
SELECT locktype, relation::regclass, mode, pid
FROM pg_locks
WHERE NOT granted;
```

**MySQL:**
```sql
-- Slow query log analysis
ANALYZE TABLE slow_query_log;
-- OR
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY sum_timer_wait DESC
LIMIT 10;
```

#### **4. Network Latency Spikes**
**Command:**
```bash
# Check network connections (Linux)
ss -tulnp | grep -E 'ESTAB|TIME_WAIT'

# Test latency/packet loss to dependent services
mtr google.com
```

**Prometheus Query:**
```
rate(http_request_duration_seconds_bucket{le="5s"}[5m])
/ rate(http_request_duration_seconds_count[5m]) < 0.5
```

#### **5. Autoscaling Event Analysis**
**Kubernetes (HPA):**
```yaml
# Check HPA metrics (kubectl)
kubectl get hpa --watch
kubectl describe hpa <hpa-name>

# Prometheus alert rule for scaling failures
sum(kube_pod_container_status_terminated_total{reason="Failed"}) by (pod) > 0
```

**AWS CloudWatch:**
```json
// CloudWatch Metric Filter for Auto Scaling
{
  "MetricName": "CPUUtilization",
  "Namespace": "AWS/EC2",
  "Statistic": "Average",
  "Period": 60,
  "Unit": "Percent",
  "Dimensions": [{"Name": "AutoScalingGroupName", "Value": "your-asg"}]
}
```

---
### **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Circuit Breaker**       | Temporarily stops calling a failing service to prevent cascading failures.     | External dependencies are unstable or latency spikes.                          |
| **Rate Limiting**         | Controls request volume to prevent overloading APIs.                          | Public APIs or third-party integrations with unknown traffic patterns.         |
| **Retry with Backoff**    | Retries failed requests with exponential backoff to handle temporary failures. | Idempotent operations (e.g., DB writes, HTTP PATCH).                           |
| **Bulkheading**           | Isolates resource-intensive operations to avoid cascading effects.             | Batch jobs or long-running tasks in shared environments.                       |
| **Resilience Testing**    | Simulates failures to validate scaling and fallback mechanisms.              | Pre-deployment or during load testing phases.                                  |
| **Multi-Region Deployment**| Distributes traffic across geographic regions to reduce latency/load.         | Global applications with users in multiple regions.                            |
| **Cold Start Mitigation** | Reduces latency for serverless functions by keeping instances warm.          | Serverless (AWS Lambda, Azure Functions) with unpredictable workloads.          |

---

## **Next Steps**
1. **Profile Under Load**: Use tools like **Grafana**, **Prometheus**, or **Dynatrace** to validate metrics under realistic traffic.
2. **Isolate Bottlenecks**: Start with **high-impact, low-effort fixes** (e.g., caching, connection pooling).
3. **Automate Scaling**: Implement **horizontal pod autoscalers**, **KEDA**, or **AWS Auto Scaling** for reactive scaling.
4. **Chaos Engineering**: Test failure scenarios with **Gremlin** or **Chaos Mesh**.
5. **Document SLIs/SLOs**: Define **Service Level Indicators (SLIs)** and **Service Level Objectives (SLOs)** to measure success.

---
**References:**
- [Google SRE Book: Scaling](https://sre.google/sre-book/scaling/)
- [AWS Well-Architected Scaling Framework](https://aws.amazon.com/architecture/well-architected/)
- [Kubernetes Best Practices for Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)