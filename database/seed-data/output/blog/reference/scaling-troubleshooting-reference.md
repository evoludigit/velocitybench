# **[Pattern] Scaling Troubleshooting – Reference Guide**

---
## **Overview**
Scaling issues can disrupt application performance, availability, or cost efficiency. This guide provides a structured approach to diagnosing and resolving scaling bottlenecks, covering **infrastructure, application, and operational layers**. Whether dealing with **vertical scaling (increasing resource capacity per instance)** or **horizontal scaling (adding more instances)**, this pattern helps identify root causes using metrics, logging, and teardown analysis. It includes a **schema-driven methodology** for consistent troubleshooting, **practical query examples** for common monitoring tools, and **related patterns** for holistic system optimization.

---
## **Implementation Details**
### **Key Concepts**
1. **Scaling Types**
   - **Vertical Scaling**: Upgrading CPU, memory, or storage per server.
   - **Horizontal Scaling**: Distributing load across multiple servers.
   - **Elastic Scaling**: Dynamically adjusting resources based on demand.

2. **Common Failure Points**
   - **Resource Contention**: CPU, memory, or I/O bottlenecks.
   - **Database Bottlenecks**: Query latency, connection pool exhaustion.
   - **Network Overhead**: High latency between services.
   - **Cold Starts**: Latency in provisioning new instances (e.g., serverless).
   - **Thundering Herd**: Sudden traffic spikes overwhelming the system.

3. **Troubleshooting Phases**
   - **Observation**: Gather metrics (CPU, latency, errors).
   - **Hypothesis**: Identify likely causes (e.g., database queries, cache misses).
   - **Validation**: Test hypotheses with controlled experiments.
   - **Resolution**: Implement fixes (optimize queries, scale out, or configure auto-scaling).

4. **Tools & Techniques**
   - **Monitoring**: Prometheus, CloudWatch, Datadog.
   - **Tracing**: Jaeger, OpenTelemetry.
   - **Logging**: ELK Stack, Fluentd.
   - **Load Testing**: k6, Locust.

---
## **Schema Reference**
Below is a **structured troubleshooting schema** to guide diagnostics. Use this as a checklist or template for structured analysis.

| **Category**               | **Metric/Component**               | **Expected Behavior**                     | **Alert Thresholds**               | **Diagnostic Actions**                                                                 |
|----------------------------|------------------------------------|-------------------------------------------|------------------------------------|----------------------------------------------------------------------------------------|
| **System Metrics**         | CPU Usage (%)                       | < 70% idle load (varies by workload)      | > 90% for > 5 mins                  | Check for CPU-bound loops; optimize algorithms or scale horizontally.                    |
|                            | Memory Usage (GB)                   | Stable growth, no frequent GC pauses      | > 80% of allocated memory           | Identify memory leaks; increase heap size or scale out.                                 |
|                            | Disk I/O Latency (ms)               | < 100ms average latency                   | > 500ms spikes                      | Review disk-bound operations; add caching or partition data.                           |
| **Network**                | Request Latency (p99, p95)          | < 500ms for inter-service calls           | > 1s for > 1% requests              | Check network saturation; optimize serialization or use CDN.                           |
|                            | Error Rates (5xx)                   | < 0.1% error rate                         | > 1% for > 1 hour                   | Review failed requests; check API timeouts or retries.                                  |
| **Database**               | Query Execution Time (p99)          | < 200ms for read queries                  | > 1s for > 5% queries               | Optimize slow queries with indexes; add read replicas.                                  |
|                            | Connection Pool Utilization         | < 80% pool exhaustion                     | > 90% for > 10 mins                 | Increase connection pool size or add a connection pooler (e.g., PgBouncer).          |
| **Application**            | Cache Hit Ratio                     | > 90% hit ratio                            | < 70% for > 1 hour                  | Review cache invalidation; increase cache size or TTL.                                  |
|                            | Concurrent Requests                 | Stable under load                         | Sudden spikes > 5x baseline         | Check for distributed locks or rate-limiting issues.                                    |
| **Auto-Scaling**           | Instance Provisioning Time          | < 100ms for warm instances               | > 5s for cold starts                 | Enable provisioned concurrency (serverless) or keep warm pools.                       |
|                            | Scaling Events (Up/Down)            | Smooth scaling (no jitter)                | Frequent minor adjustments          | Tune scaling policies (e.g., adjust CPU utilization thresholds).                        |
| **Cost Efficiency**        | Idle Resources (%)                  | < 20% idle capacity                        | > 50% for > 24 hours                | Right-size instances; use spot instances or pause idle workloads.                       |

---
## **Query Examples**
Use these queries to identify scaling issues in common monitoring tools.

### **1. CPU Bottlenecks (Prometheus)**
```promql
# High CPU usage over time
rate(container_cpu_usage_seconds_total{container!="POD", namespace="your-app"}[1m]) by (pod)
/ ignoring(instance) sum(container_spec_cpu_quota{container!="POD", namespace="your-app"})[1m]

# CPU saturation alerts
sum(rate(container_cpu_usage_seconds_total{container!="POD", namespace="your-app"}[5m])) by (pod)
> sum(container_spec_cpu_quota{container!="POD", namespace="your-app"}) * 0.9
```

### **2. Database Query Latency (CloudWatch)**
```sql
-- Slow queries in RDS (p99 latency)
SELECT percentile(duration, 99)
FROM aws_cloudwatch_metric_logs
WHERE metric_name = 'DatabaseConnections'
  AND namespace = 'AWS/RDS'
  AND dimension_value = 'your-db-instance'
  AND timestamp > ago(1h);
```

### **3. Request Latency (OpenTelemetry)**
```jaeger
# Trace analysis for slow API calls
duration > 1s
| filter(service.name = "your-api")
| stats(count(), avg(duration))
| limit 10
```

### **4. Auto-Scaling Activity (AWS CLI)**
```bash
# Check scaling activity in the last hour
aws application-autoscaling describe-scaling-activities \
  --namespace service \
  --resource-id "service:your-app:desiredCapacity" \
  --resource-type "service" \
  --max-results 100 \
  --query "ScalingActivities[?EndTime > ago(1h)].{Activity: ActivityName, Type: ActivityType}"
```

### **5. Cache Miss Rate (ELK Logs)**
```elasticsearch
# Logs-based cache miss analysis
logs*
| stats count() as cache_misses by bin(5m)
| where cache_misses > 0
| sort -cache_misses
```

---
## **Validation & Resolution**
### **Step-by-Step Workflow**
1. **Isolate the Issue**
   - Use the schema to identify which component is underperforming.
   - Example: High `p99` latency in database queries → focus on SQL tuning.

2. **Hypothesis Testing**
   - **Test 1**: Throttle traffic to rule out external factors.
     ```bash
     # Simulate load with k6
     k6 run --vus 100 --duration 30s script.js
     ```
   - **Test 2**: Compare production vs. staging metrics for similar workloads.

3. **Implement Fixes**
   - **Short-term**: Enable read replicas for DB; increase cache size.
   - **Long-term**: Refactor monolithic queries; adopt microservices.

4. **Verify**
   - Monitor metrics post-fix; roll back if degradation occurs.
   - Example rollback command (Kubernetes):
     ```bash
     kubectl rollout undo deployment/your-app --to-revision=2
     ```

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Circuit Breaker]**     | Prevent cascading failures by stopping requests to failing services.         | High latency or frequent failures in dependent services.                        |
| **[Rate Limiting]**       | Control request volume to prevent resource exhaustion.                        | Sudden traffic spikes or DDoS mitigation.                                       |
| **[Retries & Backoffs]**  | Handle transient failures gracefully with exponential retries.               | Network partitions or database timeouts.                                       |
| **[Microservices]**       | Decouple services to isolate scaling bottlenecks.                            | Monolithic apps showing uneven load distribution.                               |
| **[Caching]**             | Reduce load on databases by storing frequent queries.                        | High read query volumes or slow DB responses.                                   |
| **[Async Processing]**    | Offload long-running tasks to queues (e.g., SQS, Kafka).                    | CPU-intensive or I/O-bound background jobs.                                     |
| **[Chaos Engineering]**   | Proactively test resilience by injecting failures.                           | Pre-launch or during scaling migrations.                                       |

---
## **Best Practices**
1. **Baseline Metrics**
   - Establish normal operational ranges for all key metrics (e.g., 95th percentile latency).

2. **Alerting Policies**
   - Define SLOs (e.g., "99.9% of requests < 500ms") and alert thresholds (e.g., p99 > 1s).

3. **Load Testing**
   - Simulate production loads (e.g., using Locust) before scaling events (e.g., Black Friday).

4. **Gradual Rollouts**
   - Use canary deployments to test scaling changes in a subset of traffic.

5. **Document Patterns**
   - Maintain a **troubleshooting notebook** with past issues, fixes, and root causes.

6. **Cost vs. Performance Tradeoffs**
   - Justify scaling decisions with **cost-metric relationships** (e.g., $/request latency).

---
## **Example Walkthrough: Scaling a Database**
### **Symptoms**
- API response times spike during peak hours (10 AM–2 PM).
- `p99` query latency jumps from 200ms to 2s.

### **Troubleshooting**
| Step | Action                                                                 | Tool/Query                                                                 |
|------|------------------------------------------------------------------------|----------------------------------------------------------------------------|
| 1    | Check DB load metrics.                                                 | CloudWatch: `SELECT * FROM "CPUUtilization" WHERE "Namespace" = 'AWS/RDS'` |
| 2    | Identify slow queries.                                                 | AWS RDS Performance Insights or `EXPLAIN ANALYZE` on slow queries.         |
| 3    | Optimize a top slow query (e.g., missing index on `orders.user_id`).   | Add index: `CREATE INDEX idx_user_id ON orders(user_id);`                   |
| 4    | Enable read replicas for read-heavy workloads.                         | AWS CLI: `aws rds create-db-instance-read-replica`                         |
| 5    | Monitor post-fix.                                                      | PromQL: `rate(rds_cpu_utilization{db="your-db"}[5m])`                     |

### **Root Cause**
- **Missing index** on a frequently joined column → full table scans.
- **Solution**: Added index + read replica → reduced `p99` latency to 300ms.

---
## **Further Reading**
- [Google SRE Book: Reliability Engineering](https://sre.google/sre-book/table-of-contents/)
- [AWS Scaling Best Practices](https://aws.amazon.com/architecture/scaling/)
- [Chaos Engineering Handbook](https://www.chaosengineeringhandbook.com/)