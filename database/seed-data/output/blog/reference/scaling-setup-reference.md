**[Pattern] Scaling Setup – Reference Guide**

---

### **Overview**
The **Scaling Setup** pattern defines a structured approach to configuring, deploying, and optimizing scalable systems in cloud-native architectures. It ensures that applications, databases, and services can handle increased load efficiently by abstracting infrastructure concerns (e.g., auto-scaling, load balancing, and resource allocation) from application logic. This pattern is critical for high-availability, cost-efficient, and resilient systems, particularly in microservices and serverless environments.

Key components include:
- **Scalable Units** (e.g., containers, VMs, or serverless functions).
- **Control Mechanisms** (e.g., auto-scaling policies, load balancers).
- **Observability Tools** (e.g., monitoring, logging, and metrics collection).
- **Traffic Management** (e.g., routing, retry logic, and circuit breakers).

This guide outlines implementation strategies, schema references, query examples, and related patterns to enforce scalability without sacrificing performance or reliability.

---

### **Schema Reference**
Below are key schemas for defining scalable setups in cloud environments. Use these as templates for configuration files (e.g., Terraform, CloudFormation, or Kubernetes YAML).

| **Component**               | **Schema**                                                                 | **Description**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Auto-Scaling Group (ASG)** | ```yaml                                                                     | Defines a group of identical instances with auto-scaling triggers.                                   |
|                             | ```                                |                                                                                                     |
|                             | `name: my-app-asg`                                                      | Name of the auto-scaling group.                                                                   |
|                             | `minCapacity: 2`                                                          | Minimum instances to maintain.                                                                     |
|                             | `maxCapacity: 10`                                                         | Maximum instances allowed.                                                                        |
|                             | `desiredCapacity: 3`                                                     | Target number of instances.                                                                         |
|                             | `scalingPolicy: {`                                                         | Auto-scaling configuration with CPU/memory thresholds.                                             |
|                             |   `targetCPUUtilization: 70`                                              | Scale up if CPU > 70%.                                                                             |
|                             | }                                                                         |                                                                                                     |
|                             | `healthCheck: {`                                                          | Health check configuration.                                                                      |
|                             |   `path: /health`                                                         | Endpoint for health checks.                                                                       |
|                             |   `interval: 30`                                                          | Check interval in seconds.                                                                         |
|                             | }                                                                         |                                                                                                     |
|                             | ```                                                                     |                                                                                                     |
| **Load Balancer (LB)**      | ```yaml                                                                     | Distributes traffic across scaled instances.                                                        |
|                             | ```                                |                                                                                                     |
|                             | `type: application`                                                       | Load balancer type (e.g., `network`, `application`).                                               |
|                             | `targetGroups: [`                                                         | Backend targets for traffic routing.                                                              |
|                             |   {`name: my-app-tg`, `port: 8080`}                                        | Target group name and port.                                                                       |
|                             | ]                                                                       |                                                                                                     |
|                             | `listeners: [`                                                            | Inbound traffic rules.                                                                             |
|                             |   {`port: 80`, `protocol: HTTP`, `defaultAction: {`                     | Listener configuration.                                                                           |
|                             |     `type: forward`, `targetGroupArn: arn:aws:elasticloadbalancing:us-east-1:...` | Target group ARN.                                                                                |
|                             |   }}                                                                     |                                                                                                     |
|                             | ]                                                                       |                                                                                                     |
|                             | ```                                                                     |                                                                                                     |
| **Container Orchestration** | ```yaml (Kubernetes Deployment)                                           | Scales containers based on demand (e.g., HPA or Cluster Autoscaler).                               |
|                             | ```                                |                                                                                                     |
|                             | `apiVersion: apps/v1`                                                     | Kubernetes API version.                                                                             |
|                             | `kind: Deployment`                                                        | Resource type.                                                                                     |
|                             | `metadata: {`                                                              | Metadata (e.g., name, labels).                                                                      |
|                             |   `name: my-app`                                                          | Deployment name.                                                                                   |
|                             | }                                                                         |                                                                                                     |
|                             | `spec: {`                                                                 | Deployment specification.                                                                          |
|                             |   `replicas: 3`                                                            | Initial replica count.                                                                             |
|                             |   `selector: {`                                                            | Pod selection labels.                                                                              |
|                             |     `matchLabels: {`                                                      |                                                                                                     |
|                             |       `app: my-app`                                                       |                                                                                                     |
|                             |     }}                                                                   |                                                                                                     |
|                             |   `template: {`                                                            | Pod template.                                                                                      |
|                             |     `spec: {`                                                              | Pod specification.                                                                                 |
|                             |       `containers: [`                                                       | Container definitions.                                                                           |
|                             |         {`name: my-app`, `image: nginx:latest`, `ports: [{port: 80}]}`   | Container name, image, and exposed ports.                                                          |
|                             |       ]                                                                   |                                                                                                     |
|                             |     }}                                                                   |                                                                                                     |
|                             |   }                                                                       |                                                                                                     |
|                             | `spec: {`                                                                 | Horizontal Pod Autoscaler (HPA) configuration.                                                      |
|                             |   `minReplicas: 2`                                                         | Minimum replicas.                                                                                   |
|                             |   `maxReplicas: 10`                                                        | Maximum replicas.                                                                                   |
|                             |   `metrics: [{`                                                             | Scaling metrics (e.g., CPU, memory).                                                               |
|                             |     `type: Resource`,                                                      |                                                                                                     |
|                             |     `resource: {`                                                          |                                                                                                     |
|                             |       `name: cpu`,                                                          |                                                                                                     |
|                             |       `target: {`                                                          |                                                                                                     |
|                             |         `type: Utilization`,                                               |                                                                                                     |
|                             |         `averageUtilization: 50`                                           | Scale when CPU > 50%.                                                                              |
|                             |       }}                                                                  |                                                                                                     |
|                             |     }                                                                     |                                                                                                     |
|                             |   ]                                                                       |                                                                                                     |
|                             | }                                                                         |                                                                                                     |
|                             | ```                                                                     |                                                                                                     |
| **Serverless Function**     | ```yaml (AWS Lambda)                                                       | Scales to zero or scales with invocations.                                                          |
|                             | ```                                |                                                                                                     |
|                             | `functionName: my-scalable-function`                                       | Function name.                                                                                     |
|                             | `runtime: python3.9`                                                       | Runtime environment.                                                                              |
|                             | `handler: index.handler`                                                   | Entry point for the function.                                                                    |
|                             | `memorySize: 512`                                                          | Memory allocation (MB).                                                                           |
|                             | `timeout: 10`                                                              | Execution timeout (seconds).                                                                       |
|                             | `reservedConcurrency: 0`                                                   | Concurrency limit (0 = scales to max).                                                              |
|                             | `scaling: {`                                                              | Concurrency settings.                                                                              |
|                             |   `reservedConcurrency: 10`                                                | Minimum concurrent executions.                                                                      |
|                             |   `maxConcurrency: 1000`                                                   | Maximum concurrent executions.                                                                     |
|                             | }                                                                         |                                                                                                     |
|                             | ```                                                                     |                                                                                                     |

---

### **Query Examples**
Below are examples of queries and commands to validate scaling configurations and monitor performance.

---

#### **1. AWS CloudWatch Metrics (Auto-Scaling)**
**Query:** Monitor CPU utilization and scaling events.
```sql
SELECT
  metric,
  average
FROM
  metric statistics
WHERE
  metric = 'CPUUtilization' OR metric = 'ScalingActivity'
  AND namespace = 'AWS/ApplicationELB'
  AND dimension.Name = 'LoadBalancerName'
  AND dimension.Value = 'my-app-lb'
  AND startTime = ago(1h)
GROUP BY
  metric, average
ORDER BY
  average DESC;
```

**Command:** Adjust scaling policies dynamically.
```bash
# Update ASG scaling policy via AWS CLI
aws application-autoscaling update-scaling-policy \
  --policy-name 'MyApp-CPU-Policy' \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    'TargetValue=50.0,' \
    'PredefinedMetricSpecification={'PredefinedMetricType':'ASGAverageCPUUtilization'},' \
    'CustomizedMetricSpecification={}' \
  --service-namespace 'application-autoscaling' \
  --resource-id 'service/my-app/desired-replica-count' \
  --scalable-unit 'desired-replica-count'
```

---

#### **2. Kubernetes Horizontal Pod Autoscaler (HPA)**
**Query:** Check HPA scaling recommendations.
```bash
# List HPA status with recommended scaling
kubectl get hpa -n my-namespace my-app-hpa -o yaml
```
**Command:** Scale pods based on custom metrics (e.g., Prometheus).
```bash
# Create a custom metric adapter for HPA
kubectl apply -f hpa-custom-metrics-adapter.yaml
# Then scale based on custom metrics (e.g., QPS)
kubectl autoscale deployment my-app --cpu-percent=50 --min=2 --max=10 \
  --custom-metrics-query='sum(rate(http_requests_total[5m])) by (instance)'
```

---

#### **3. Load Balancer Health Checks**
**Query:** Validate load balancer health.
```bash
# AWS ALB health check status
aws elbv2 describe-target-health \
  --target-group-arn 'arn:aws:elasticloadbalancing:us-east-1:...'
```
**Command:** Rotate unhealthy targets.
```bash
# Register new targets and deregister old ones
aws elbv2 register-targets \
  --target-group-arn 'arn:aws:elasticloadbalancing:us-east-1:...' \
  --targets Id=instance-1234567890abcdef0,Port=8080

aws elbv2 deregister-targets \
  --target-group-arn 'arn:aws:elasticloadbalancing:us-east-1:...' \
  --targets Id=instance-0987654321fedcba0,Port=8080
```

---

#### **4. Serverless Scaling (AWS Lambda)**
**Query:** Monitor invocation and concurrency.
```sql
SELECT
  function_name,
  invocations,
  concurrent_executions,
  errors
FROM
  "AWS/Lambda"
WHERE
  function_name = 'my-scalable-function'
  AND startTime > ago(1h)
ORDER BY
  concurrent_executions DESC;
```
**Command:** Test concurrency limits.
```bash
# Simulate high traffic to test scaling
aws lambda invoke \
  --function-name my-scalable-function \
  --payload '{"key": "value"}' \
  response.json

# Monitor concurrent executions
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=function_name,Value=my-scalable-function \
  --start-time $(date -u -v-1h +%s000) \
  --end-time $(date -u +%s000) \
  --period 60 \
  --statistics Average
```

---

### **Implementation Best Practices**
1. **Define Scaling Boundaries:**
   - Set `minCapacity` and `maxCapacity` to avoid over-provisioning or under-resourcing.
   - Use **reserved concurrency** in serverless to prioritize critical workloads.

2. **Leverage Multi-Dimensional Metrics:**
   - Scale based on **CPU**, **memory**, **custom business metrics** (e.g., request rate), or **external signals** (e.g., SQS queue depth).

3. **Implement Health Checks:**
   - Configure **graceful degradation** (e.g., circuit breakers) to avoid cascading failures.
   - Use **readiness/liveness probes** in Kubernetes to self-heal.

4. **Optimize Cold Starts (Serverless):**
   - Increase **memory allocation** to reduce cold start latency.
   - Use **provisioned concurrency** for predictable workloads.

5. **Monitor and Iterate:**
   - Set up **alerts** for scaling events (e.g., `ScalingActivity` in AWS).
   - Use **distributed tracing** (e.g., AWS X-Ray, Jaeger) to identify bottlenecks.

6. **Cost Management:**
   - Use **spot instances** for fault-tolerant workloads.
   - Right-size resources to avoid paying for unused capacity.

---

### **Related Patterns**
1. **[Stateless Services](https://patterns.dev/stateless-services):**
   - Pair with **Scaling Setup** to ensure statelessness enables horizontal scaling.

2. **[Circuit Breaker](https://patterns.dev/circuit-breaker):**
   - Protects scaled services from cascading failures during high load.

3. **[Retries and Backoff](https://patterns.dev/retries-backoff):**
   - Handles transient failures in distributed systems with retries and exponential backoff.

4. **[Queue-Based Load Leveling](https://patterns.dev/queue-based-load-leveling):**
   - Decouples producers/consumers to smooth out traffic spikes (e.g., SQS, Kafka).

5. **[Canary Deployments](https://patterns.dev/canary-deployments):**
   - Gradually scales new versions to reduce risk during updates.

6. **[Multi-Region Deployment](https://patterns.dev/multi-region-deployment):**
   - Extends **Scaling Setup** across regions for global high availability.

7. **[Serverless Architecture](https://patterns.dev/serverless-architecture):**
   - Embrace **Scaling Setup** for automatic, event-driven scaling.

8. **[Database Scaling](https://patterns.dev/database-scaling):**
   - Complements **Scaling Setup** with read replicas, sharding, or managed databases (e.g., Aurora, Cosmos DB).

---
### **Troubleshooting Common Issues**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                                     |
|-------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| Insufficient scaling               | Thresholds too high                    | Lower target metrics (e.g., `TargetCPUUtilization: 30`).                                        |
| Throttling (e.g., Lambda)          | Concurrency limits hit                 | Increase `reservedConcurrency` or use SQS as a buffer.                                            |
| Unstable scaling                    | Noisy metrics (spikes)                 | Use moving averages or smoothed metrics in scaling policies.                                     |
| High latency during scaling         | Cold starts (serverless)               | Increase memory or use provisioned concurrency.                                                   |
| Over-provisioning costs             | Aggressive scaling policies            | Tune `maxCapacity` and use spot instances for non-critical workloads.                           |
| Sticky sessions breaking            | Load balancer not configured for stickiness | Enable `sticky sessions` or use session affinity in Kubernetes.                                 |
| Data inconsistency (distributed DB)| Improper read replicas                 | Ensure read replicas are kept in sync (e.g., Aurora Global Database).                            |

---
### **Example Workflow**
1. **Design:**
   - Define scaling boundaries (`min=2`, `max=10` replicas) and metrics (`CPU > 50%`).
   - Use a **load balancer** to distribute traffic across instances.

2. **Implement:**
   ```yaml
   # Kubernetes Deployment + HPA
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: my-app
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: my-app
           image: my-app:latest
           ports: [{port: 8080}]
   ---
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: my-app-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: my-app
     minReplicas: 2
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 50
   ```

3. **Monitor:**
   - Set up **Prometheus + Grafana** to visualize scaling events.
   - Configure **AWS CloudWatch Alarms** for `ScalingActivity` or `ErrorRate`.

4. **Optimize:**
   - Adjust thresholds based on real-world load.
   - Use **autoscaling predictor** (e.g., SageMaker) for proactive scaling.

---
### **Final Notes**
- **Start Small:** Begin with conservative scaling policies and iterate.
- **Test Under Load:** Use tools like **Locust** or **k6** to simulate traffic spikes.
- **Document:** Record scaling decisions (e.g., thresholds, metrics) in your architecture runbook.

This pattern ensures your system **scales efficiently** while maintaining **resilience** and **cost-effectiveness**. For further reading, explore cloud provider-specific guides (e.g., [AWS Auto Scaling](https://docs.aws.amazon.com/autoscaling/), [Kubernetes Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)).