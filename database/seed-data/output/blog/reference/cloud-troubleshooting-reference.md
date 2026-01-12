# **[Pattern] Cloud Troubleshooting Reference Guide**

---
## **1. Overview**
The **Cloud Troubleshooting Pattern** provides a structured methodology for diagnosing, isolating, and resolving issues across cloud infrastructure, services, and applications. This pattern covers best practices for log analysis, dependency mapping, performance diagnostics, and automated alerts—ensuring rapid incident response while minimizing downtime. By systematically applying this framework, teams can reduce mean time to resolution (MTTR) and improve operational reliability.

Key areas addressed:
✔ **Log & Metric Collection** – Centralized monitoring of infrastructure, apps, and services.
✔ **Dependency Mapping** – Visualizing service dependencies to identify bottlenecks.
✔ **Performance Profiling** – Analyzing latency, throughput, and resource utilization.
✔ **Automated Alerting** – Setting up proactive notifications for anomalies.
✔ **Root Cause Analysis (RCA)** – Using structured troubleshooting techniques (e.g., binary search, elimination).

---

## **2. Schema Reference**
| **Component**          | **Description**                                                                 | **Key Attributes**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Monitoring Sources** | Logs, metrics, traces, and events collected from cloud services.               | - Collector type (e.g., Fluentd, Prometheus)                                     |
|                        |                                                                                 | - Retention policy (e.g., 30-day log storage)                                    |
|                        |                                                                                 | - Aggregation frequency (e.g., per-second metrics)                               |
| **Dependency Graph**   | Visual representation of service interactions and dependencies.                  | - Nodes: Services, containers, or VMs                                            |
|                        |                                                                                 | - Edges: Dependencies (e.g., "Database → API")                                  |
|                        |                                                                                 | - Latency/throughput metrics per link                                           |
| **Performance Thresholds** | Baseline metrics defining normal vs. anomalous behavior.               | - CPU/Memory utilization (e.g., >90% for 5 mins)                                |
|                        |                                                                                 | - Error rate (e.g., >1% HTTP 5xx errors)                                        |
|                        |                                                                                 | - Latency (e.g., >500ms P99 response time)                                      |
| **Alert Policies**     | Rules triggering notifications for predefined conditions.                     | - Condition (e.g., `avg(cpu_usage) > 80% for 1h`)                             |
|                        |                                                                                 | - Severity (Critical, Warning)                                                  |
|                        |                                                                                 | - Notification channels (Slack, Email, PagerDuty)                               |
| **Troubleshooting Workflow** | Step-by-step process for diagnosing issues.               | - Phases: Isolate → Diagnose → Resolve → Verify                                  |
|                        |                                                                                 | - Tools: Debug scripts, APM agents, cloud provider consoles                      |

---

## **3. Query Examples**
### **3.1 Log Analysis Queries**
Use cloud-native tools (e.g., **AWS CloudWatch Logs**, **Google Cloud Logging**) to filter logs:
```sql
-- Filter 5xx errors in API Gateway (AWS)
fields @timestamp, @message
| filter @message like /5[0-9][0-9]/i
| stats count(*) as error_count by request_id
| sort error_count desc
```

```sql
-- Azure Application Insights query for slow transactions
requests
| where duration > 500ms
| summarize avg(duration), count() by operation_Name
| order by avg_duration desc
```

---

### **3.2 Metric Aggregations (Prometheus/Grafana)**
```promql
-- Alert on high database CPU usage (Prometheus)
max by(instance) (rate(container_cpu_usage_seconds_total{namespace="db"}[5m]))
> 80
```

```promql
-- Track API latency percentiles
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
```

---

### **3.3 Dependency Graph Queries**
**AWS CloudTrail + ECS Example:**
```bash
# List ECS tasks with failed health checks
aws ecs list-tasks --cluster my-cluster --desired-status STOPPED
aws ecs describe-tasks --cluster my-cluster --tasks $(aws ecs list-tasks ...)
| grep "healthStatus": "UNHEALTHY"
```

**Google Cloud Operations Suite:**
```bash
# Find dependent services impacted by an outage
gcloud operations insights query-explain \
  --project=my-project \
  --query="traces where http.status_code in [500, 503] | limit 100"
```

---

### **3.4 Root Cause Analysis (RCA) Scripts**
**Python (AWS Lambda for automated RCA):**
```python
import boto3
from datetime import datetime, timedelta

def analyze_logs():
    cloudwatch = boto3.client('logs')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)

    response = cloudwatch.filter_log_events(
        logGroupName='/aws/lambda/my-function',
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000),
        filterPattern='ERROR'
    )
    errors = [event['message'] for event in response['events']]
    return errors if errors else "No errors found."
```

---

## **4. Implementation Steps**
### **Step 1: Instrumentation**
- **Logs**: Ship logs to a centralized system (e.g., ELK, Datadog).
- **Metrics**: Instrument applications with APM agents (e.g., OpenTelemetry, Datadog APM).
- **Traces**: Enable distributed tracing for microservices (e.g., Jaeger, AWS X-Ray).

### **Step 2: Dependency Mapping**
- Use **cloud provider tools** (AWS Service Map, GCP Network Topology).
- For custom apps: Generate graphs via **static analysis** (e.g., `istioctl tree`).

### **Step 3: Define Thresholds**
| **Metric**               | **Warning Threshold** | **Critical Threshold** |
|--------------------------|-----------------------|-------------------------|
| CPU Usage                | 80%                   | 95%                     |
| Memory Usage             | 70%                   | 90%                     |
| HTTP 5xx Errors          | 1%                    | 5%                      |
| Database Query Latency    | 1s                    | 5s                      |

### **Step 4: Set Up Alerts**
**AWS CloudWatch Example:**
```yaml
# CloudFormation template snippet for an alert
Resources:
  HighErrorRateAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmDescription: "API Gateway error rate > 1%"
      MetricName: "5XXError"
      Namespace: "AWS/ApiGateway"
      Statistic: Sum
      Period: 60
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref SNSTopicArn
```

### **Step 5: Troubleshoot**
1. **Isolate**: Check dependency graphs for affected services.
2. **Diagnose**:
   - Correlate logs + metrics (e.g., spikes in 5xx errors → database timeouts).
   - Use **binary search** (e.g., check if issue exists in staging first).
3. **Resolve**: Apply fixes (e.g., scale out, patch, reconfigure).
4. **Verify**: Confirm resolution via automated checks.

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures by stopping requests to failing services.          | Microservices with external dependencies.        |
| **Retries with Backoff**  | Exponential backoff for transient failures.                                     | Handling API throttling or network partitions.   |
| **Chaos Engineering**     | Proactively test system resilience by injecting faults.                          | Pre-launch reliability testing.                 |
| **Observability Pipeline**| Combines logs, metrics, and traces for holistic monitoring.                     | Large-scale distributed systems.                |
| **Blue/Green Deployment** | Zero-downtime deployments via traffic shifting.                                  | Critical production environments.                |

---
## **6. Best Practices**
1. **Centralize Observability**: Use a single pane of glass (e.g., Datadog, New Relic) for all signals.
2. **Reduce Noise**: Fine-tune alert thresholds to avoid alert fatigue.
3. **Automate RCA**: Use ML-based anomaly detection (e.g., AWS DevOps Guru).
4. **Document Runbooks**: Maintain step-by-step troubleshooting guides for common issues.
5. **Postmortems**: After incidents, analyze root causes and update workflows.

---
## **7. Tools & Integrations**
| **Category**       | **Tools**                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **Log Management** | ELK Stack, Datadog, Splunk, AWS CloudWatch Logs                           |
| **Metrics**        | Prometheus, Grafana, Datadog, AWS CloudWatch Metrics                     |
| **Tracing**        | Jaeger, AWS X-Ray, OpenTelemetry, Datadog APM                            |
| **Dependency Maps**| AWS Service Map, GCP Network Topology, Istio, Linkerd                       |
| **Alerting**       | PagerDuty, Opsgenie, AWS SNS, Slack                                     |
| **Automation**     | Terraform, Ansible, AWS Lambda, Python Scripts                           |

---
## **8. Troubleshooting Checklist**
### **Cloud Provider Issues**
- [ ] Check provider status page (e.g., [AWS Health](https://status.aws.amazon.com/), [GCP Status](https://status.cloud.google.com/)).
- [ ] Verify API quota limits (e.g., AWS Service Quotas).
- [ ] Review network egress/ingress rules.

### **Infrastructure Issues**
- [ ] Check VM/container status (e.g., `kubectl get pods`, `aws ec2 describe-instances`).
- [ ] Monitor disk I/O, memory, and CPU saturation.
- [ ] Verify storage (EBS, EFS, or cloud disks) health.

### **Application Issues**
- [ ] Correlate logs with application traces (e.g., slow DB queries).
- [ ] Test API endpoints (e.g., `curl`, Postman).
- [ ] Check for environment mismatches (dev vs. prod configs).

### **Dependency Issues**
- [ ] Follow dependency graph to identify upstream failures.
- [ ] Simulate failover (e.g., kill a database node).
- [ ] Verify backups and disaster recovery plans.

---
## **9. Conclusion**
The **Cloud Troubleshooting Pattern** ensures a systematic approach to diagnosing and resolving cloud-related issues. By combining **observability**, **dependency awareness**, and **automated alerts**, teams can minimize downtime and improve system resilience. Start with foundational monitoring, iteratively refine your troubleshooting workflows, and leverage automation to scale your operations.

**Next Steps:**
- Instrument your applications with logs/metrics/traces.
- Build a dependency map of critical services.
- Define alerting thresholds and runbooks.
- Conduct regular chaos experiments to test resilience.