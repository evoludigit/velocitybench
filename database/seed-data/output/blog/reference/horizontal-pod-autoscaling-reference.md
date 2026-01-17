# **[Pattern] Horizontal Pod Autoscaling (HPA) Reference Guide**
*Dynamic scaling for FraiseQL deployments based on workload metrics and custom business KPIs.*

---

## **Overview**
FraiseQL’s **Horizontal Pod Autoscaling (HPA)** dynamically adjusts the number of running pods in a Kubernetes deployment based on real-time system metrics (CPU, memory) and **custom business metrics** (e.g., query latency, cache hit rates). This ensures optimal resource allocation while maintaining SLAs, reducing costs during low traffic, and scaling efficiently during spikes.

HPA leverages Kubernetes’ built-in metrics alongside FraiseQL-specific metrics via **Prometheus** and **custom metrics adapters**. Policies control scaling thresholds (e.g., scale up at 70% CPU for 5 minutes) and cooldown periods to avoid thrashing. Advanced features like **predictive scaling** (via ML-driven forecasts) and **pod priority classes** for critical workloads are also supported.

---

## **Key Concepts**
| Term | Definition |
|------|------------|
| **HPA Controller** | Kubernetes component that adjusts replica counts based on predefined rules. |
| **Scaling Target** | A Kubernetes Deployment, StatefulSet, or ReplicaSet where pods are scaled. |
| **Metric Thresholds** | CPU (%), memory (%), or custom metrics (e.g., `query_latency_p99 > 100ms`). |
| **Min/Max Replicas** | Hard limits to prevent under/over-scaling (e.g., `min: 2`, `max: 20`). |
| **Cooldown Period** | Time (seconds) to wait after scaling before evaluating again (default: 5m). |
| **Custom Metrics Adapter** | Bridges FraiseQL metrics (e.g., cache hit ratio) to Kubernetes HPA. |
| **Predictive Scaling** | Uses ML models (e.g., ARIMA) to forecast demand and pre-scale pods. |
| **Pod Priority Classes** | Assigns scaling priority to critical workloads (e.g., `preemption-policy: Always`). |

---

## **Schema Reference**
### **1. HPA Configuration Schema**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fraiseql-hpa
spec:
  scaleTargetRef:  # Target deployment/statefulset
    apiVersion: apps/v1
    kind: Deployment
    name: fraiseql
  minReplicas: 2    # Minimum pods (required)
  maxReplicas: 20   # Maximum pods
  metrics:          # Scaling triggers
    - type: Resource  # Built-in Kubernetes metrics
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70  # Scale up at 70% CPU
    - type: Resource
      resource:
        name: memory
        target:
          type: AverageValue
          averageValue: 500Mi  # Scale up at 500Mi memory usage
    - type: Pods        # Custom metrics (requires adapter)
      pods:
        metric:
          name: fraiseql_query_latency_p99
        target:
          type: AverageValue
          averageValue: 100ms
    - type: External    # External monitoring (e.g., Prometheus)
      external:
        metric:
          name: cache_hit_ratio
          selector:
            matchLabels:
              app: fraiseql-cache
        target:
          type: AverageValue
          averageValue: 0.95  # Scale up if cache hits drop below 95%
  behavior:           # Scaling dynamics
    scaleDown:
      stabilizationWindowSeconds: 300  # Delay scaling down
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 20
          periodSeconds: 60
        - type: Pods
          value: 5
          periodSeconds: 60
      selectPolicy: Max
```

---

### **2. Custom Metrics Adapter Configuration**
For FraiseQL-specific metrics (e.g., latency percentiles), deploy a **custom metrics adapter** with:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fraiseql-metrics-adapter
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: fraiseql-metrics-reader
rules:
  - apiGroups: [""]  # Built-in metrics
    resources: ["pods"]
    verbs: ["get", "list"]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics-adapter
spec:
  replicas: 1
  template:
    spec:
      serviceAccountName: fraiseql-metrics-adapter
      containers:
        - name: adapter
          image: prometheus-community/helm-charts:metrics-server-custom-metrics-adapter
          args:
            - --metric-resources=custom=true
            - --prometheus-url=http://prometheus-server:9090
            - --v=2
```

---

### **3. Predictive Scaling (Optional)**
Enable ML-driven forecasting by annotating the HPA:
```yaml
spec:
  predictiveScaling:
    enabled: true
    model: arima
    forecastWindow: 300  # 5 minutes ahead
    confidenceInterval: 0.95
```

---

## **Query Examples**
### **1. Inspect Current HPA Status**
```sh
kubectl get hpa fraiseql-hpa -o wide
```
**Output:**
```
NAME            REFERENCE               TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
fraiseql-hpa    Deployment/fraiseql     70%/70%   2         20        5          2h
```

### **2. Describe HPA Rules**
```sh
kubectl describe hpa fraiseql-hpa
```
**Key Fields:**
```
Conditions:
  Type           Status  Reason                   Message
  ----           ------  ------                   -------
  ScaledUp       True    CPUUtilizationScaledUp  cpu utilization (percent) met target
Metrics:
  [{"type":"Resource","name":"cpu","current":{"utilization":72},"target":{"type":"Utilization","averageUtilization":70}}, ...]
```

### **3. Scale Manually (Testing)**
```sh
kubectl rollout restart deployment fraiseql
# Observe scaling behavior via:
kubectl get pods -w
```

### **4. Query Custom Metrics via Prometheus**
```sh
kubectl exec -it $(kubectl get pod -l app=prometheus -o jsonpath="{.items[0].metadata.name}") -c prometheus -- promql
> fraiseql_query_latency_p99{namespace="default"} > 100
```

---

## **Related Patterns**
| Pattern | Description |
|---------|-------------|
| **[Vertical Pod Autoscaling (VPA)](https://example.com/vpa)** | Adjusts CPU/memory per pod instead of replica count. |
| **[Cluster Autoscaler](https://example.com/cluster-autoscaler)** | Scales up/down Kubernetes nodes based on unschedulable pods. |
| **[Pod Disruption Budget (PDB)](https://example.com/pdb)** | Ensures minimum pod availability during voluntary disruptions. |
| **[Resource Quota Limits](https://example.com/quota)** | Prevents over-provisioning (e.g., `limits.cpu: "10"`). |
| **[Multi-Cluster HPA](https://example.com/multi-cluster)** | Syncs HPA rules across Kubernetes clusters for global workloads. |

---

## **Best Practices**
1. **Set Realistic Thresholds**:
   - Default `70% CPU` may be too aggressive; test with `50-60%` first.
   - For latency-sensitive apps, use `p99 > 50ms` as a trigger.

2. **Avoid Cooldown Collisions**:
   - Configure `scaleDown.stabilizationWindow` to match your workload’s volatility (e.g., 5m for batch jobs).

3. **Leverage Horizontal Pod Disruption Budgets (HPDBs)**:
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: fraiseql-pdb
   spec:
     minAvailable: 2  # Ensures 2 pods remain during disruptions
     selector:
       matchLabels:
         app: fraiseql
   ```

4. **Monitor Scaling Events**:
   - Use **Kubernetes Events** or **Loki/Grafana** to track scaling actions:
     ```sh
     kubectl get events --sort-by='.metadata.creationTimestamp'
     ```

5. **Custom Metrics Adapter Tuning**:
   - Ensure Prometheus queries are **low-latency** (e.g., avoid `range_over_time` for real-time HPA).

6. **Predictive Scaling Tradeoffs**:
   - **Pros**: Reduces latency during traffic spikes.
   - **Cons**: Requires ML model training and adds complexity.

---

## **Troubleshooting**
| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| **HPA not scaling** | Check `kubectl describe hpa` for `Conditions: RecommendedTrue` but no action. | Verify metrics adapter is running (`kubectl logs -l app=metrics-adapter`). |
| **Thundering Herd** | Rapid scaling up/down causes instability. | Increase `stabilizationWindowSeconds` or adjust thresholds. |
| **Custom metrics missing** | Prometheus query returns no data. | Validate the `selector` labels in HPA match your Prometheus targets. |
| **Pods stuck at 1 replica** | `maxReplicas` is too low or scaling rules aren’t met. | Increase `maxReplicas` or lower thresholds. |
| **Predictive scaling over/underestimates** | ML model is misconfigured. | Retrain the model with recent traffic patterns. |