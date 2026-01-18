---
# **[Pattern] Advanced Load Balancing Reference Guide**

---

## **Overview**
The **Advanced Load Balancing** pattern extends traditional load balancing to dynamically optimize traffic distribution across systems based on real-time conditions, application logic, and performance metrics. Unlike basic round-robin or random assignment, this pattern incorporates predictive scaling, multi-layered routing, and adaptive policies to minimize latency, prevent cascading failures, and maximize resource utilization. It’s ideal for microservices architectures, cloud-native environments, and high-availability applications where static configurations are insufficient.

Key use cases include:
- **Auto-scaling** based on demand (e.g., sudden traffic spikes).
- **Geographic routing** to reduce latency for global users.
- **A/B testing** and feature flagging via dynamic routing.
- **Multi-cloud or hybrid environments** with heterogeneous workloads.
- **Failure recovery** with circuit breakers and failover logic.

This guide covers implementation strategies, schema references, query examples, and integration with related patterns.

---

## **Schema Reference**
Below are the core components and their relationships for implementing Advanced Load Balancing.

| **Component**               | **Description**                                                                                     | **Attributes**                                                                                     | **Example Values**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Load Balancer**           | Distributes incoming traffic across backend services.                                               | `name`, `type` (e.g., `Layer4`, `Layer7`, `GlobalServerLoadBalancer`), `healthCheckInterval`    | `name: "web-lb", type: "Layer7", healthCheckInterval: "30s"`                                          |
| **Backend Service**         | Target service (e.g., API, database, cache) to route traffic.                                         | `serviceName`, `endpoint`, `weight`, `priority`, `healthStatus`                                  | `serviceName: "order-service", weight: 3, healthStatus: "healthy"`                                    |
| **Routing Rule**            | Defines conditions for dynamic traffic distribution.                                                 | `ruleName`, `priority`, `matchConditions`, `action` (`RouteTo`, `Redirect`, `Reject`)          | `ruleName: "geo-rule", matchConditions: `{region: "us-west"}`                                          |
| **Health Check**            | Monitors backend service availability.                                                               | `checkType` (e.g., `HTTP`, `TCP`, `Latency`), `path`, `timeout`, `interval`                    | `checkType: "HTTP", path: "/health", timeout: "5s"`                                                   |
| **Policy**                  | Applies business logic (e.g., rate limiting, circuit breaking).                                    | `policyName`, `type` (e.g., `RateLimit`, `CircuitBreaker`, `WeightedRoundRobin`), `thresholds`  | `policyName: "rate-limit", type: "RateLimit", thresholds: {rps: 100}`                                |
| **Monitoring Metric**       | Tracks performance data (e.g., latency, error rates, queue length).                                 | `metricName`, `dimensions` (e.g., `service`, `region`), `unit`                                   | `metricName: "latency", dimensions: {service: "auth-service"}, unit: "ms"`                           |
| **Dynamic Config**          | Enables runtime updates to rules/policies without restarting.                                       | `configName`, `version`, `updateTrigger` (e.g., `manual`, `metric-based`)                      | `configName: "traffic-rules-v2", updateTrigger: "metric-based"`                                      |
| **Integration**             | Links load balancer to orchestration tools (e.g., Kubernetes, Istio, AWS ALB).                    | `orchestrator`, `provider`                                                                       | `orchestrator: "Kubernetes", provider: "IngressController"`                                          |

---

## **Implementation Details**

### **1. Core Components**
#### **Load Balancer Types**
| **Type**                  | **Use Case**                                                                                     | **Example Tools**                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Layer 4 (Transport)**   | Routes based on IP/port (e.g., TCP/UDP).                                                          | HAProxy, AWS Network Load Balancer, Nginx.                                                     |
| **Layer 7 (Application)** | Inspects HTTP headers/content for intelligent routing (e.g., path-based, header-based).        | AWS Application Load Balancer, NGINX Ingress, Envoy.                                          |
| **Global Server LB**      | Routes users to the nearest geographic endpoint.                                                  | Google Cloud Global Load Balancer, Azure Traffic Manager.                                     |
| **Service Mesh**          | Manages microservices traffic with observability and security (e.g., Istio, Linkerd).          | Istio (Envoy proxy), Linkerd.                                                                  |

#### **Dynamic Routing Strategies**
| **Strategy**              | **Description**                                                                                 | **Example Use Case**                                                                           |
|---------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Weighted Round Robin**  | Distributes traffic proportionally based on weights (e.g., new releases get 10% traffic).      | Canary deployments.                                                                             |
| **Least Connections**     | Routes to the least busy backend to optimize performance.                                       | Database queries during peak hours.                                                          |
| **IP Hash**               | Ensures consistent routing for a client’s IP (session affinity).                               | Stateful sessions (e.g., shopping carts).                                                     |
| **Latency-Based**         | Routes to the backend with the lowest response time.                                           | Global applications.                                                                           |
| **Rule-Based**            | Applies custom logic (e.g., `if header: "promo=true" then route to "sale-service"`).          | A/B testing, feature flags.                                                                     |
| **Predictive Scaling**    | Uses ML/metrics to preemptively allocate resources (e.g., AWS ALB Auto Scaling).               | Unpredictable traffic bursts (e.g., Black Friday).                                           |

---

### **2. Health Checks and Failover**
#### **Health Check Types**
| **Type**          | **Description**                                                                                 | **Configuration Example**                                                                       |
|-------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **HTTP/HTTPS**    | Sends HTTP requests to a health endpoint.                                                       | `/health`, status code: `200`.                                                                   |
| **TCP**           | Checks if a port is open (no HTTP inspection).                                                 | Port: `8080`, timeout: `2s`.                                                                     |
| **Latency**       | Measures response time to detect degraded performance.                                         | Threshold: `500ms`.                                                                              |
| **Custom Script** | Executes a shell script or API call for complex checks.                                        | Script: `curl -s http://backend/ping | grep "OK" || exit 1`.                                  |

#### **Failover Logic**
- **Primary-Backup**: Traffic routes to backup if primary fails.
- **Circuit Breaker**: Stops sending traffic to a failing service after `N` failures (e.g., Hystrix pattern).
- **Graceful Degradation**: Routes to a simpler service (e.g., static fallback page) during outages.

---
### **3. Policies and Observability**
#### **Common Policies**
| **Policy**               | **Description**                                                                                 | **Example Implementation**                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Rate Limiting**        | Limits requests per client/IP to prevent abuse.                                                | `rate: 100 rps`, `burst: 200`.                                                               |
| **Circuit Breaker**      | Stops traffic to a failing service after `N` failures in `M` seconds.                          | `threshold: 5 failures`, `timeout: 30s`.                                                    |
| **Weighted Routing**     | Distributes traffic based on weights (e.g., 80% to v1, 20% to v2).                             | `weights: {v1: 0.8, v2: 0.2}`.                                                              |
| **Request Timeouts**     | Drops or redirects requests exceeding a threshold.                                             | `timeout: 1s`, `action: "reject"` or `"route-to-fallback"`.                                  |
| **Header-Based**         | Routes based on request headers (e.g., `X-User-Type`).                                        | `match: {header: "X-User-Type", value: "premium"}`.                                          |

#### **Monitoring Metrics**
| **Metric**               | **Description**                                                                                 | **Tool Integration**                                                                           |
|--------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Active Connections**   | Number of concurrent requests to a backend.                                                     | Prometheus, Datadog.                                                                           |
| **Latency Percentiles**  | P50, P90, P99 response times.                                                                   | AWS CloudWatch, New Relic.                                                                     |
| **Error Rates**          | Percentage of failed requests.                                                                   | Grafana, ELK Stack.                                                                             |
| **Queue Length**         | Backlog of pending requests (indicator of overload).                                            | Istio Telemetry, OpenTelemetry.                                                              |
| **Endpoint Utilization** | CPU/memory usage of backends.                                                                   | Kubernetes Metrics Server, AWS CloudWatch Container Insights.                                  |

---

## **Query Examples**
### **1. Dynamic Routing Rule (JSON Configuration)**
```json
{
  "rules": [
    {
      "name": "user-role-route",
      "priority": 1,
      "match": {
        "header": {
          "name": "X-User-Role",
          "value": ["admin", "premium"]
        }
      },
      "action": {
        "route_to": ["secure-service"]
      }
    },
    {
      "name": "fallback-route",
      "priority": 2,
      "match": {
        "status_code": ["5xx"]
      },
      "action": {
        "redirect": "https://static-fallback.example.com"
      }
    }
  ]
}
```

### **2. Kubernetes Ingress Annotation (YAML)**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: advanced-lb-ingress
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "0.2"
    nginx.ingress.kubernetes.io/health-check-path: "/health"
spec:
  rules:
  - host: "app.example.com"
    http:
      paths:
      - path: "/"
        pathType: Prefix
        backend:
          service:
            name: production-service
            port:
              number: 80
      - path: "/canary"
        pathType: Prefix
        backend:
          service:
            name: canary-service
            port:
              number: 80
```

### **3. AWS ALB Rule (CloudFormation)**
```yaml
Resources:
  ALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Subnets: !Ref SubnetIds
  Listener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ProdTargetGroup
  Rule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref Listener
      Priority: 1
      Conditions:
        - Field: path-pattern
          Values: ["/api/*"]
      Actions:
        - Type: forward
          TargetGroupArn: !Ref ApiTargetGroup
```

### **4. Istio VirtualService (YAML)**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
  - "my-app.example.com"
  http:
  - match:
    - headers:
        end-user:
          exact: premium
    route:
    - destination:
        host: premium-service
        subset: v2
  - match:
    - headers:
        end-user:
          regex: ".*"
    route:
    - destination:
        host: default-service
        subset: v1
```

### **5. Terrafom Config (AWS ALB + Auto Scaling)**
```hcl
resource "aws_lb" "app_lb" {
  name               = "app-lb"
  internal           = false
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_autoscaling_policy" "scale_on_cpu" {
  name                   = "scale-on-cpu"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name
  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

---
## **Related Patterns**
Advanced Load Balancing often integrates with or is complemented by the following patterns:

| **Pattern**                     | **Description**                                                                                     | **Integration Example**                                                                           |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Circuit Breaker]**            | Prevents cascading failures by stopping traffic to a failing service.                               | Combine with **Advanced LB** to route traffic to a backup service when health checks fail.    |
| **[Retry & Backoff]**            | Automatically retries failed requests with exponential backoff.                                     | Use in **Layer 7 LB** to handle transient errors (e.g., 503s) before failover.                  |
| **[Service Mesh]**               | Provides fine-grained traffic control, observability, and security for microservices.              | Deploy **Istio/Linkerd** alongside **Advanced LB** for mTLS and telemetry.                      |
| **[Rate Limiting]**              | Controls request volume to prevent abuse or overload.                                              | Apply **rate limiting policies** in **Layer 7 LB** or via sidecar proxies (e.g., Envoy).     |
| **[Canary Releases]**            | Gradually shifts traffic to a new version to minimize risk.                                        | Use **weighted routing** in **Advanced LB** to route 10% of traffic to the new version.        |
| **[Multi-Region Deployment]**    | Deploys services across regions for high availability.                                             | Configure **Global LB** to route users to the nearest healthy region.                           |
| **[Chaos Engineering]**          | Tests resilience by deliberately introducing failures.                                               | Use **Advanced LB** to observe failover behavior during chaos experiments.                       |
| **[Observability Stack]**        | Centralizes logs, metrics, and traces for debugging.                                               | Pair **Advanced LB** with **Prometheus + Grafana** to monitor latency/errors.                   |
| **[API Gateway]**                | Manages APIs with authentication, throttling, and routing.                                          | Integrate **API Gateway** (e.g., Kong, AWS API Gateway) as the frontend to **Advanced LB**.      |

---
## **Best Practices**
1. **Start Simple**: Begin with **Layer 4 LB** (e.g., HAProxy) before adding complexity.
2. **Monitor Everything**: Track metrics for each routing rule and backend.
3. **Test Failover**: Simulate outages to validate recovery paths.
4. **Use Service Mesh for Microservices**: Istio/Linkerd add observability and security.
5. **Leverage Auto-Scaling**: Tie LB policies to cloud auto-scaling groups.
6. **Implement Circuit Breakers**: Prevent cascading failures with patterns like Hystrix.
7. **Document Rules**: Maintain a clear inventory of routing rules and their purposes.
8. **Canary Deployments**: Use weighted routing for gradual rollouts.
9. **Secure Traffic**: Enforce TLS and validate headers (e.g., `X-Forwarded-Proto`).
10. **Optimize Latency**: Use **geo-routing** and **CDN integration** for global apps.

---
## **Troubleshooting**
| **Issue**                          | **Diagnostic Steps**                                                                             | **Resolution**                                                                                   |
|-------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **5xx Errors Spiking**              | Check backend health checks and metrics (e.g., `5xx Errors` in ALB).                          | Review `health_check_path` and `timeout` settings. Add circuit breaker.                          |
| **High Latency**                    | Profile requests with APM tools (e.g., New Relic, Jaeger).                                      | Optimize backend queries or adjust `least-connections` logic.                                    |
| **Unexpected Failover**             | Review failover rules and health check thresholds.                                               | Adjust `health_check_interval` or `unhealthy_threshold`.                                        |
| **Traffic Not Routing Correctly**   | Validate routing rules (e.g., missing `header` conditions).                                      | Test with `curl -v` or `kubectl proxy` for Kubernetes Ingress.                                  |
| **Rate Limiting Blocking Valid Users** | Check rate limit thresholds and dimensions (e.g., by `user_id`).                         | Adjust `rate` or `burst` settings, or add `ipWhitelist` exceptions.                             |
| **Weighted Routing Not Working**    | Verify weights in load balancer config (e.g., Istio `VirtualService`).                          | Confirm weights are integer values (e.g., `weight: 2` for 50% traffic if total=4).             |

---
## **Further Reading**
- [AWS Advanced Load Balancing Docs](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-lifecycle.html)
- [Istio Traffic Management Guide](https://istio.io/latest/docs/tasks/traffic-management/)
- [Kubernetes Ingress Best Practices](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Chaos Engineering at Netflix](https://netflixtechblog.com/chaos-engineering-at-netflix-90cb3875602d)
- [Grafana Load Balancer Dashboards](https://grafana.com/grafana/dashboards/)

---
**Last Updated:** [Insert Date]
**Version:** 1.2