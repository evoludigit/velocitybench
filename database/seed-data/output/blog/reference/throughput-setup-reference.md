---
**[Pattern] Throughput Setup – Reference Guide**

---

### **1. Overview**
The **Throughput Setup** pattern optimizes system performance by dynamically adjusting resource allocation (e.g., CPU, memory, or connection limits) based on observed workload. It ensures sustained performance under varying loads while minimizing waste or overload. This guide covers how to implement, configure, and validate throughput settings for distributed systems, APIs, or microservices.

---

### **2. Schema Reference**
Define configuration parameters as key-value pairs in JSON/YAML. Below are critical fields:

| **Parameter**          | **Type**       | **Description**                                                                 | **Example Value**               | **Required?** |
|------------------------|----------------|---------------------------------------------------------------------------------|----------------------------------|----------------|
| `target_latency_ms`    | `number`       | Maximum acceptable response time for 95% of requests.                           | `150`                            | Yes            |
| `capacity_units`       | `array<int>`   | List of possible capacity increments (e.g., worker pool sizes, threads).        | `[5, 10, 20, 50]`                | Yes            |
| `adjustment_subinterval` | `string`       | Time period (e.g., "5m", "1h") for reassessing throughput.                     | `"30s"`                          | Yes            |
| `min_capacity`         | `number`       | Lowest allowed capacity unit to avoid under-provisioning.                      | `3`                              | No (default: 1)|
| `max_capacity`         | `number`       | Upper bound for capacity scaling.                                               | `100`                            | No (dynamic)   |
| `scaling_strategy`     | `enum`         | Algorithm type: `linear`, `exponential`, or `adaptive`.                        | `"adaptive"`                     | Yes            |
| `metrics_source`       | `string`       | Data provider (e.g., Prometheus, custom telemetry).                            | `"prometheus"`                   | Yes            |
| `error_threshold`      | `number`       | % of failed requests triggering a reduction in capacity.                       | `10`                             | No (default: 5)|
| `warmup_duration`      | `string`       | Time (e.g., "10m") to observe baseline performance before scaling.              | `"2m"`                           | No (default: 5m)|

**Example JSON Config:**
```json
{
  "target_latency_ms": 200,
  "capacity_units": [2, 5, 10, 20],
  "adjustment_subinterval": "1m",
  "scaling_strategy": "adaptive",
  "metrics_source": "prometheus",
  "error_threshold": 8
}
```

---

### **3. Implementation Details**

#### **3.1 Key Concepts**
- **Target Latency (`target_latency_ms`):** The 95th percentile response time threshold. If exceeded, capacity increases.
- **Capacity Units:** Discrete levels (e.g., worker threads) scaling in response to load.
- **Scaling Strategies:**
  1. **Linear:** Fixed increments/decrements (e.g., +1 unit per subinterval).
  2. **Exponential:** Doubling/decreasing capacity (e.g., 2→4→8 threads).
  3. **Adaptive:** Dynamic adjustments based on metric trends (default).
- **Feedback Loop:** Continuously monitors metrics (e.g., `request_duration_seconds`) and adjusts capacity.

#### **3.2 Data Flow**
1. **Monitoring:** Collects metrics from `metrics_source` (e.g., Prometheus queries like:
   `histogram_quantile(0.95, sum(rate(http_requests_seconds_bucket[5m])) by (le))`).
2. **Comparison:** Compares observed latency against `target_latency_ms`.
3. **Threshold Check:** If errors exceed `error_threshold`, triggers a capacity decrement.
4. **Adjustment:** Scales capacity based on `scaling_strategy` and `capacity_units`.
5. **Validation:** Confirms performance improvement post-adjustment.

#### **3.3 Validation**
- **Baseline Test:** Deploy with `min_capacity` and measure latency under stable load.
- **Stress Test:** Simulate traffic spikes (e.g., `locust -u 1000 -r 100`) and observe adjustments.
- **Logging:** Validate adjustments via logs (e.g., `{"action": "scale_up", "capacity": 10, "trigger": "high_latency"}`).

---

### **4. Query Examples**
#### **Prometheus Queries**
- **Current 95th Percentile Latency:**
  ```promql
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m])) by (le)
  ```
- **Error Rate:**
  ```promql
  sum(rate(http_requests_total{status=~"5.."}[1m])) by (service) / sum(rate(http_requests_total[1m]))
  ```

#### **Adjustment Logic (Pseudocode)**
```python
def adjust_capacity(current_latency, target_latency):
    if current_latency > target_latency * 1.2:  # 20% threshold
        new_capacity = min(max_capacity, current_capacity * 1.5)  # Exponential
    elif error_rate > error_threshold:
        new_capacity = max(min_capacity, current_capacity * 0.8)
    else:
        new_capacity = current_capacity
    return clamp(new_capacity, min_capacity, max_capacity)
```

---

### **5. Query Examples (CLI/Tooling)**
#### **Kubernetes HPA (Horizontal Pod Autoscaler) Analogue**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: throughput-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: throughput-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_request_duration_seconds
      target:
        type: AverageValue
        averageValue: 50ms  # Custom metric (requires Prometheus Adapter)
```

#### **Terraform Module (For Cloud Providers)**
```hcl
resource "aws_appautoscaling_target" "throughput_target" {
  max_capacity       = 50
  min_capacity       = 2
  resource_id        = aws_lambda_function.throughput.arn
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "latency_policy" {
  name               = "latency-scale"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.throughput_target.id
  scalable_dimension = aws_appautoscaling_target.throughput_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.throughput_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 150.0  # target_latency_ms
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
  }
}
```

---

### **6. Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Integration**                                                                 |
|---------------------------|----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Rate Limiting**         | Prevents overload by capping request volume.                              | Use as a fallback if `Throughput Setup` fails (e.g., abject spikes).          |
| **Circuit Breaker**       | Halts requests during failures to avoid cascading outages.                | Trigger circuit break if `error_threshold` isn’t met post-scaling.            |
| **Bulkheading**           | Isolates high-priority workloads from noisy neighbors.                   | Combine with `Throughput Setup` to allocate capacity per service tier.        |
| **A/B Testing (Canary)**  | Gradual rollouts to test performance under scaled capacity.                | Validate adjustments with canary traffic before full rollout.                  |
| **Chaos Engineering**     | Tests resilience by injecting failures during scaling events.              | Simulate network partitions or latency spikes to validate recovery.            |

---

### **7. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------|------------------------------------------------------------------------------|
| Over-scaling (costs spike)          | `target_latency_ms` set too low.        | Increase `target_latency_ms` or adjust `scaling_strategy` to `linear`.       |
| Under-scaling (latency degradation)| `min_capacity` too low.                 | Set `min_capacity` to baseline load + 20% buffer.                            |
| Oscillations (choppy scaling)      | Noise in metrics (e.g., spiky traffic).| Apply smoothing (e.g., 3-minute trailing average) or increase `warmup_duration`. |
| Ignoring errors                     | `error_threshold` too high.             | Reduce `error_threshold` or add manual overrides (e.g., `max_capacity`).     |

---

### **8. Example Workflow**
1. **Setup:**
   ```bash
   # Deploy with min capacity (3 workers)
   kubectl apply -f throughput-deployment.yaml
   ```
2. **Monitor:**
   ```bash
   # Check current latency
   curl -G "http://monitoring/prometheus/api/v1/query" --data-urlencode "query=histogram_quantile(0.95, sum(rate(http_requests_seconds_bucket[1m])) by (le))"
   ```
3. **Adjust:**
   - Latency > 200ms → Scale up to 5 workers.
   - Error rate > 10% → Scale down to 2 workers.
4. **Validate:**
   ```bash
   # Verify post-scaling
   kubectl logs throughput-pod | grep "capacity_adjusted"
   ```