**[Pattern] Advanced Load Balancing – Reference Guide**

---

### **1. Overview**
The **Advanced Load Balancing** pattern enables precise and dynamic traffic distribution across backend services, ensuring optimal performance, scalability, and fault tolerance. Unlike standard round-robin or simple weighted balancing, this pattern integrates real-time metrics (e.g., latency, errors, resource consumption) and contextual rules (e.g., geographic proximity, user priority) to dynamically adjust traffic routing. Suitable for large-scale microservices, global applications, or systems requiring high availability (e.g., e-commerce, financial services), this pattern minimizes downtime, prevents cascading failures, and maximizes throughput while adhering to SLAs.

---

### **2. Key Concepts**

#### **2.1 Core Components**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example Use Case**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Policy Engine**           | Evaluates dynamic rules (latency, pod health, custom annotations) to determine backend selection. Supports chaining policies for layered decision-making.                                                | Route 90% traffic to `us-east` if <100ms latency; else fallback to `eu-west`. |
| **Health Scoring**          | Assigns a numeric score to backends based on metrics (e.g., CPU, memory, request success rate). Backends with scores below a threshold are deprioritized or removed from rotation.                   | Exclude pods with >95% CPU utilization.     |
| **Geographic Route Selection** | Uses client IP or DNS resolution to route traffic to the nearest data center, minimizing latency. Works with anycast or multi-region deployments.                                                          | Serve EU users from `fra1`; US users from `nyc3`. |
| **Circuit Breakers**        | Temporarily halts traffic to failing backends, preventing downstream cascades. Resets thresholds based on recovery metrics (e.g., consecutive healthy probes).                                              | Pause traffic to failing microservice for 5 minutes. |
| **Dynamic Weighting**       | Adjusts backend weights in real-time (e.g., scale up healthy instances, scale down lagging ones). Combines with autoscaling for elastic capacity.                                                        | Increase weight of backends with <50ms p99 latency. |
| **Context-Aware Routing**   | Injected metadata (e.g., user tier, session ID) influences routing decisions. Enables personalized performance (e.g., premium users bypass queues).                                                      | Prioritize Gold-tier users over Silver.     |
| **Locality-Aware Load Balancing** | Routes traffic to backends co-located with the client (e.g., Kubernetes node affinity, cloud provider zones). Reduces network hops in distributed systems.                                            | Route to pods on the same Azure region.     |
| **Canary Releases**         | Gradually shifts a fraction of traffic (e.g., 5%) to new versions for testing before full rollout. Monitors for regressions via error rates or custom KPIs.                                              | Test new API version with 2% of traffic.     |
| **Backup Pools**            | Maintains a "cold standby" pool of backends for zero-downtime failovers. Activates only during outages.                                                                                                     | Failover to secondary database cluster on primary failure. |

---

### **3. Schema Reference**
Below is a schema defining the **AdvancedLoadBalancer** configuration. Fields marked with `*` are required.

#### **3.1 Global Configuration**
| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `name`                  | `string*`      | Unique identifier for the load balancer (e.g., `app-global-lb`).                                                                                                                                                   | `"order-service-lb"`                  |
| `policy_engine`         | `object`       | Rules engine configuration.                                                                                                                                                                                      | See **Policy Engine Schema** below.   |
| `geo_routing`           | `object`       | Geographic routing settings.                                                                                                                                                                                 | See **GeoRouting Schema** below.      |
| `health_check`          | `object*`      | Backend health probe configuration.                                                                                                                                                                          | See **HealthCheck Schema** below.     |
| `circuit_breaker`       | `object`       | Circuit breaker thresholds.                                                                                                                                                                               | See **CircuitBreaker Schema** below.  |
| `autoscale_integration` | `boolean`      | Enable dynamic weight adjustments tied to autoscaler (e.g., Kubernetes HPA).                                                                                                                                     | `true`                                 |
| `backup_pools`          | `array`        | List of secondary backend pools for failover.                                                                                                                                                             | `[{"name": "db-secondary"}]`         |
| `metrics_provider`      | `string*`      | Source for real-time metrics (e.g., `prometheus`, `datadog`, `custom`).                                                                                                                                         | `"prometheus:http://metrics-server"` |

---

#### **3.2 Policy Engine Schema**
Configures dynamic routing rules. Supports `OR`/`AND` logic via `policy_groups`.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `policy_groups`         | `array*`       | List of rule groups (e.g., latency-based, health-based).                                                                                                                                                     | `[{ "name": "latency", "type": "latency" }]` |
| `fallback_policy`       | `string`       | Action if all policies fail (e.g., `random`, `least_connections`, `backup_pool`).                                                                                                                                | `"backup_pool"`                       |
| `context_metadata`      | `object`       | Key-value pairs injected into policies (e.g., `user_tier: Gold`).                                                                                                                                                 | `"user_tier": "Gold"`                 |

---
#### **3.3 GeoRouting Schema**
Defines regional routing rules.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `regions`               | `array*`       | List of region-backend mappings.                                                                                                                                                                               | `[{ "region": "us-east", "backends": ["app-us1"] }]` |
| `fallback_region`       | `string`       | Default region if client not matched (e.g., `eu-west`).                                                                                                                                                         | `"eu-west"`                           |
| `detection_method`      | `enum`         | How to detect client region: `ip_geolocation`, `dns`, `cookie`.                                                                                                                                                | `"ip_geolocation"`                    |

---

#### **3.4 HealthCheck Schema**
Configures backend health probes.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `interval`              | `string*`      | Probe frequency (e.g., `10s`, `1m`).                                                                                                                                                                                 | `"30s"`                               |
| `timeout`               | `string*`      | Timeout per probe (e.g., `5s`).                                                                                                                                                                                   | `"5s"`                                |
| `success_threshold`     | `integer*`     | Minimum successful probes to mark backend as healthy.                                                                                                                                                         | `3`                                   |
| `failure_threshold`     | `integer*`     | Consecutive failures to trigger deprioritization.                                                                                                                                                              | `2`                                   |
| `metrics`               | `array`        | Custom metrics to include (e.g., `cpu_usage`, `request_latency`).                                                                                                                                                 | `["cpu_usage", "error_rate"]`         |

---
#### **3.5 CircuitBreaker Schema**
Configures failover behavior.

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `trigger_threshold`     | `integer*`     | Failures per interval to trigger breaker (e.g., `5` failures in `1m`).                                                                                                                                         | `5`                                   |
| `reset_timeout`         | `string*`      | Time to wait before retrying backends (e.g., `5m`).                                                                                                                                                           | `"5m"`                                |
| `half_open_probability` | `number`       | Chance to test a backend after reset (e.g., `0.5` = 50%).                                                                                                                                            | `0.3`                                 |
| `metrics`               | `array`        | Metrics to monitor (e.g., `http_5xx`, `connection_errors`).                                                                                                                                                     | `["http_5xx"]`                        |

---

### **4. Query Examples**
The **AdvancedLoadBalancer** API supports CRUD operations via gRPC or REST. Below are common use cases.

#### **4.1 Create a Load Balancer**
**Request (gRPC):**
```proto
CreateLoadBalancerRequest {
  name: "app-lb",
  policy_engine: {
    policy_groups: [{
      name: "latency",
      type: "latency",
      target: "99th_percentile_ms",
      threshold: 100
    }]
  },
  geo_routing: {
    regions: [{
      region: "us-west",
      backends: ["us-west-1", "us-west-2"]
    }]
  }
}
```

**Response:**
```json
{
  "id": "lb-12345",
  "status": "active",
  "created_at": "2023-10-01T12:00:00Z"
}
```

---

#### **4.2 Update Dynamic Weights**
**Request (REST):**
```http
PATCH /v1/lbs/app-lb/weights
Headers: { "Content-Type": "application/json" }
Body:
{
  "backends": [{
    "name": "us-east-1",
    "weight": 70
  }, {
    "name": "eu-west-1",
    "weight": 30
  }]
}
```

**Response:**
```json
{
  "success": true,
  "updated_weights": {
    "us-east-1": 70,
    "eu-west-1": 30
  }
}
```

---

#### **4.3 Trigger Canary Release**
**Request (gRPC):**
```proto
CanaryReleaseRequest {
  lb_name: "order-service-lb",
  target_version: "v2.1.0",
  percentage: 0.05  // 5%
  metrics: ["http_5xx_rate"]
}
```

**Response:**
```json
{
  "canary_id": "canary-789",
  "status": "pending_approval",
  "start_time": "2023-10-01T13:00:00Z"
}
```

---
#### **4.4 Check Backend Health Stats**
**Request (REST):**
```http
GET /v1/lbs/app-lb/backends/us-west-1/health
Headers: { "Accept": "application/json" }
```

**Response:**
```json
{
  "backend": "us-west-1",
  "health_score": 0.87,
  "metrics": {
    "cpu_usage": 0.72,
    "error_rate": 0.01,
    "latency_p99": 120
  },
  "status": "degraded"
}
```

---

### **5. Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                                                                 | **When to Use**                          |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| **[Retries and Backoff]**             | Exponential backoff for transient failures (e.g., network timeouts).                                                                                                                                         | Resilient client-server communication.   |
| **[Circuit Breaker]**                 | Isolate faults in distributed systems by stopping cascades.                                                                                                                                                     | Microservices with interdependent services. |
| **[Rate Limiting]**                   | Control request volume to prevent abuse or overload backends.                                                                                                                                               | Public APIs or high-traffic services.    |
| **[Kubernetes Service Mesh]**        | Abstracts load balancing, observability, and security (e.g., Istio, Linkerd).                                                                                                                                  | Kubernetes-native deployments.           |
| **[Multi-Region Deployment]**         | Deploy identical services across regions for global low-latency.                                                                                                                                             | Global-scale applications.               |
| **[Chaos Engineering]**                | Test resilience by intentionally injecting failures.                                                                                                                                                              | Pre-launch reliability validation.       |
| **[Progressive Delivery]**            | Gradually roll out changes (e.g., A/B testing).                                                                                                                                                                | Safe deployment of new features.         |

---
### **6. Best Practices**
1. **Monitor Metrics Religiously**:
   - Track `health_score`, `latency_p99`, and `error_rate` via Prometheus/Grafana.
   - Set alerts for `health_score < 0.5` or `circuit_breaker_triggered`.

2. **Start Conservative with Canaries**:
   - Begin with **1–5%** traffic for new versions to catch edge cases.

3. **Use Locality for Performance**:
   - Combine `locality-aware` routing with `geo_routing` to reduce hops (e.g., client → edge node → co-located backend).

4. **Combine Policies Carefully**:
   - Example: `(latency < 100ms) OR (health_score > 0.9)` → `least_connections`.

5. **Test Failover Scenarios**:
   - Simulate regional outages to validate `backup_pools` and circuit breakers.

6. **Optimize for Cold Starts**:
   - Pre-warm backup pools or use `warmup_requests` in health checks.

7. **Document Fallbacks**:
   - Clearly state how the system behaves when all primary backends fail (e.g., "fallback to read replicas").

---
### **7. Troubleshooting**
| **Issue**                          | **Diagnostic Steps**                                                                                                                                                                                                 | **Solution**                          |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| Traffic routed to failing backend   | Check `health_check.failure_threshold` and `circuit_breaker` logs.                                                                                                                                            | Increase `success_threshold` or adjust `trigger_threshold`. |
| High latency in a region           | Verify `geo_routing.detection_method` accuracy and `locality-aware` pod distribution.                                                                                                                       | Add more edge nodes or adjust region mappings. |
| Canary errors not detected         | Ensure `metrics_provider` includes the monitored metric (e.g., `http_5xx`).                                                                                                                                     | Add missing metric to `CanaryReleaseRequest`. |
| Weight adjustments ignored          | Confirm `autoscale_integration` is enabled and autoscaler is updating backend metrics.                                                                                                                            | Manually adjust weights via API.      |
| Circuit breaker stuck open          | Check `reset_timeout` duration and ensure backends are recovering.                                                                                                                                             | Reset breaker manually or adjust timeout. |

---
### **8. Example Deployment (Terraform)**
```hcl
resource "aws_lb" "advanced_lb" {
  name               = "app-lb"
  internal           = false
  load_balancer_type = "application"

  policy_engine {
    policy_groups {
      name   = "latency"
      type   = "latency"
      target = "99th_percentile_ms"
      threshold = 150
    }
  }

  geo_routing {
    regions = [
      {
        region   = "us-east-1"
        backends = ["us-east-1-app"]
      },
      {
        region   = "eu-west-1"
        backends = ["eu-west-1-app"]
      }
    ]
  }
}
```

---
**See Also**:
- [Kubernetes Advanced Load Balancer Addon](https://github.com/kubernetes-sigs/aws-load-balancer-controller)
- [Istio Traffic Management Docs](https://istio.io/latest/docs/tasks/traffic-management/)
- [Google Cloud Global Load Balancer](https://cloud.google.com/load-balancing/docs/global)