# **[Pattern] Traffic Shifting Patterns – Reference Guide**

## **Overview**
Traffic Shifting Patterns enable dynamic redistribution of user requests across services, environments, or geographic regions to balance load, mitigate failures, or prioritize performance. This pattern is critical in **scalable microservices architectures**, **multi-cloud deployments**, and **disaster recovery** scenarios. Implementations often involve **weighted routing**, **canary releases**, **A/B testing**, **geographic routing (geoDNS)**, or **failover mechanisms**. By leveraging **API gateways (Kong, AWS ALB), service meshes (Istio, Linkerd), or load balancers (NGINX, HAProxy)**, organizations can shift traffic programmatically based on predefined rules (e.g., health checks, latency thresholds, or business logic). This guide covers common traffic-shifting strategies, their schemas, implementation considerations, and query examples.

---

## **Key Concepts & Implementation Details**
### **1. Core Components**
| Component               | Description                                                                                     | Example Tools                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Traffic Director**    | Routes requests based on policies (e.g., weights, rules, failover).                            | AWS ALB, NGINX, Istio, Traefik, HAProxy                                       |
| **Policy Engine**       | Evaluates conditions (e.g., "shift 20% traffic to staging if latency > 1s").                 | Envoy, Kubernetes Ingress, AWS Route 53                                           |
| **Backend Services**    | Targets (e.g., `prod-v1`, `prod-v2`, `staging`).                                               | Kubernetes Pods, EC2 Instances, Lambda Functions                               |
| **Monitoring**          | Tracks metrics (e.g., latency, error rates) to trigger shifts.                                | Prometheus, Datadog, AWS CloudWatch, OpenTelemetry                             |
| **Configuration Store** | Manages dynamic rules (e.g., weights, failover targets).                                      | AWS Parameter Store, Consul, Kubernetes ConfigMaps, Redis                     |

### **2. Common Traffic-Shifting Strategies**
| Strategy               | Description                                                                                     | Use Case                                                                       |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Weighted Routing**   | Distributes traffic by assigning percentages to backends.                                       | Gradual rollouts (e.g., 80% prod-v1, 20% prod-v2).                           |
| **Canary Releases**    | Routes a small percentage (e.g., 5%) to a new version for testing.                              | Testing new features with minimal risk.                                      |
| **A/B Testing**        | Compares user experience between two versions (e.g., UI vs. new API).                          | Optimizing conversions or performance.                                         |
| **GeoDNS/Locality**    | Routes users to the nearest datacenter or region.                                              | Reducing latency for global audiences.                                        |
| **Failover**           | Redirects traffic to a secondary service if the primary fails.                                  | High availability and disaster recovery.                                      |
| **Latency-Based**      | Shifts traffic to the fastest responding backend.                                               | Auto-optimizing performance.                                                 |
| **Header-Based**       | Routes based on request headers (e.g., `X-User-Segment`).                                     | Personalized routing (e.g., VIP customers to premium tier).                    |
| **Time-Based**         | Shifts traffic at specific times (e.g., 100% to staging during maintenance).                   | Scheduled updates or maintenance windows.                                     |

### **3. Implementation Workflow**
1. **Define Rules**: Specify conditions (e.g., "if error rate > 3% on `prod-v1`, shift to `prod-v2`").
2. **Configure Director**: Set up the traffic director (e.g., Istio `VirtualService` or NGINX `upstream`).
3. **Deploy Backends**: Ensure target services are healthy and monitorable.
4. **Test**: Validate rules with synthetic traffic (e.g., Locust, k6).
5. **Monitor**: Use observability tools to detect shifts and adjust policies.

---

## **Schema Reference**
Below are common schemas for traffic-shifting configurations in **Kubernetes (Istio)**, **NGINX**, and **AWS ALB**.

### **1. Istio `VirtualService` (Weighted Routing)**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - my-service.example.com
  http:
  - route:
    - destination:
        host: prod-v1.my-service
        subset: v1
      weight: 80
    - destination:
        host: prod-v2.my-service
        subset: v2
      weight: 20
status:
  loadBalancer:
    addresses:
    - 10.0.0.1
```

### **2. NGINX `upstream` (Header-Based Routing)**
```nginx
upstream backend {
    server backend-v1:8080 max_fails=3 fail_timeout=10s;
    server backend-v2:8080 max_fails=3 fail_timeout=10s;
}
server {
    listen 80;
    location / {
        proxy_pass http://backend;
        proxy_set_header X-Custom-Segment "$http_x_user_segment";
        if ($http_x_user_segment = "vip") {
            proxy_pass http://backend-v2;
        }
    }
}
```

### **3. AWS ALB (GeoDNS + Failover)**
```json
// AWS Route 53 Latency-Based Routing Policy
{
  "Comment": "Shift traffic to EU if AWS_US_EAST_1 is unhealthy",
  "Type": "Latency",
  "HealthChecks": [
    {
      "ResourcePath": "/health",
      "HealthCheckRegion": "us-east-1"
    }
  ],
  "HealthCheckInterval": 30,
  "HealthCheckTimeout": 5,
  "HealthyThreshold": 3,
  "UnhealthyThreshold": 5
}
```

### **4. Kubernetes `Service` (Weighted Endpoints)**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  ports:
  - name: http
    port: 80
    targetPort: 8080
  selector:
    app: my-service
---
apiVersion: v1
kind: Endpoints
metadata:
  name: my-service
subsets:
- addresses:
  - ip: 10.0.0.1
  ports:
  - name: http
    port: 8080
    weight: 80
- addresses:
  - ip: 10.0.0.2
  ports:
  - name: http
    port: 8080
    weight: 20
```

---

## **Query Examples**
### **1. Checking Current Traffic Distribution (Prometheus)**
```promql
# Istio traffic percentages by destination
sum(rate(istio_requests_total{response_code=~"2.."}[5m]))
  by (destination_host, destination_subset) /
sum(rate(istio_requests_total{response_code=~"2.."}[5m]))
  by (destination_host)
```

### **2. AWS CloudWatch (Failover Metrics)**
```json
// Alarm for failover triggered
{
  "MetricName": "ALBRequestCount",
  "Namespace": "AWS/ApplicationELB",
  "Dimensions": [
    {
      "Name": "LoadBalancer",
      "Value": "my-alb"
    }
  ],
  "Statistic": "Sum",
  "Period": 300,
  "EvaluationPeriods": 1,
  "Threshold": 0,
  "ComparisonOperator": "GreaterThanThreshold",
  "TreatMissingData": "notBreaching"
}
```

### **3. Kubernetes Events (Pod Failures)**
```bash
# Check pod failures triggering failover
kubectl get events --sort-by='.metadata.creationTimestamp' \
  --field-selector reason=Failed \
  --field-selector involvedObject.kind=Pod
```

### **4. Istio Policy Evaluation (Envoy Filters)**
```bash
# Simulate a canary shift via Envoy snippets
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service-canary
spec:
  http:
  - route:
    - destination:
        host: my-service
        subset: v1
      weight: 95
    - destination:
        host: my-service
        subset: v2
      weight: 5
      headers:
        request:
          set:
            x-canary: "true"
EOF
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                       |
|-----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Circuit Breaker**         | Stops forwarding requests to failing services to prevent cascading failures.                | High-availability systems (e.g., Netflix Hystrix).                             |
| **Retry**                   | Automatically retries failed requests with backoff.                                           | Idempotent APIs (e.g., database writes).                                           |
| **Rate Limiting**           | Controls request volume to prevent overload.                                                  | Public APIs or microservices with bursty traffic.                                 |
| **Chaos Engineering**       | Intentionally injects failures to test resilience.                                             | Disaster recovery planning.                                                       |
| **Blue-Green Deployment**   | Instantly switches traffic to a new version with zero downtime.                              | Critical systems requiring fast rollbacks.                                       |
| **Feature Flags**           | Dynamically enables/disables features without redeployment.                                   | Gradual feature rollouts.                                                         |
| **Service Mesh**            | Decouples networking from applications for advanced traffic control.                        | Complex microservices architectures (e.g., Istio, Linkerd).                      |

---

## **Best Practices**
1. **Gradual Rollouts**: Use canary releases to mitigate risks.
2. **Monitor Metrics**: Track latency, error rates, and throughput post-shift.
3. **Fallbacks**: Define clear failover targets (e.g., secondary regions).
4. **Automate Policies**: Use CI/CD pipelines to update traffic rules (e.g., Argo Rollouts).
5. **Document Rules**: Maintain a **traffic-shifting policy book** for stakeholders.
6. **Test Failures**: Simulate outages (e.g., with Chaos Mesh) to validate failover.
7. **Canary Analysis**: Use tools like **Flagsmith** or **LaunchDarkly** to analyze canary metrics.

---
**See Also**:
- [Istio Traffic Management Docs](https://istio.io/latest/docs/tasks/traffic-management/)
- [AWS Traffic Shifting Best Practices](https://aws.amazon.com/blogs/networking-and-content-delivery/traffic-shifting-strategies-for-multi-region-applications/)
- [NGINX Plus Traffic Control](https://www.nginx.com/resources/glossary/traffic-control/)