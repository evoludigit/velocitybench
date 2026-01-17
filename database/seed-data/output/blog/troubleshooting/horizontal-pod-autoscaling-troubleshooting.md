# **Debugging Horizontal Pod Autoscaling (HPA): A Troubleshooting Guide**

## **1. Introduction**
Horizontal Pod Autoscaling (HPA) automatically adjusts the number of pod replicas based on observed metrics (CPU, memory, custom metrics like query latency). If HPA is misconfigured, it can lead to:
- **Over-provisioning** (wasting resources during low traffic)
- **Under-provisioning** (slow responses under high load)
- **Throttling or crashes** (due to abrupt scaling decisions)

This guide provides a structured approach to diagnosing and fixing HPA issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue with these questions:

| **Symptom** | **Question** | **Possible Cause** |
|-------------|-------------|-------------------|
| ✅ High query latency | `kubectl top pods` shows high CPU/memory usage, but HPA doesn’t scale up. | HPA metrics not properly configured, scaling limits too low, or custom metrics not updating. |
| ❌ Over-provisioning | HPA scales up unnecessarily (e.g., 50 replicas when 5 are needed). | CPU/memory targets too low, or custom metric thresholds too aggressive. |
| ❌ Pod crashes on scaling | Pods fail health checks after scaling. | Insufficient CPU/Memory requests, or custom metrics causing panic. |
| 🚀 Slow scaling decisions | HPA reacts too slowly to traffic spikes. | Scaling policy (`maxExpandRate`, `maxReplicas`) too conservative. |
| 📊 Custom metrics not triggering scaling | Query latency increases, but HPA does nothing. | Custom metric adapter misconfigured, or Metrics Server not reporting. |

---
## **3. Common Issues & Fixes**

### **Issue 1: HPA Not Scaling Up Under High Load**
**Symptoms:**
- `kubectl get hpa` shows "Current replicas vs desired replicas" stuck.
- `kubectl describe hpa <name>` shows no scaling events.

**Root Cause:**
- **CPU/Memory thresholds too high** (e.g., `targetCPUUtilizationPercentage: 90` when load is 80%).
- **Custom metric not detected** (e.g., Prometheus adapter not configured).
- **Pods failing due to insufficient resources** (requests > limits).

**Fix:**
#### **A. Adjust CPU/Memory Thresholds**
```yaml
# Example: Lower targetCPUUtilizationPercentage (default is 80%)
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
        averageUtilization: 70  # Reduced from 80% → 70%
```
**Verify:**
```sh
kubectl get hpa
watch -n 1 'kubectl top pods --no-headers | awk "{print \$3}"'
```
(Force traffic spike with `kubectl run load-test --image=nghttp2/nghttp2 -it --rm --restart=Never -- sh -c "ab -n 10000 -c 100 http://<service-name>"`)

---

#### **B. Ensure Custom Metrics Are Reported**
If using **custom metrics (e.g., Prometheus)**:
1. **Deploy the Metrics Adapter:**
   ```sh
   kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/metrics-server/main/deploy/manifests/metrics-adapter.yaml
   ```
   *(For Prometheus, use [Prometheus Adapter](https://github.com/DirectXman12/k8s-prometheus-adapter).)*

2. **Configure HPA with Custom Metrics:**
   ```yaml
   metrics:
   - type: Pods
     pods:
       metric:
         name: cache_hit_ratio
       target:
         type: AverageValue
         averageValue: 90m  # Scale when cache hit ratio < 90%
   ```

**Verify Adapter Health:**
```sh
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq
```

---

### **Issue 2: HPA Scales Too Aggressively (Too Many Replicas)**
**Symptoms:**
- HPA jumps from 2 → 50 replicas unnecessarily.
- Cost spikes due to over-provisioning.

**Root Cause:**
- **High `maxExpandRate`** (default is `4`, meaning max 4 scaling steps per min).
- **Low `minReplicas`** (e.g., `minReplicas: 0` allows zero pods during downtime).

**Fix:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  maxReplicas: 20      # Limit max pods
  minReplicas: 2       # Avoid scaling down to zero
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

**Verify:**
```sh
kubectl get hpa -w
```

---

### **Issue 3: Pods Crash After Scaling Up**
**Symptoms:**
- HPA scales up, but pods fail with `CrashLoopBackOff` or `Error`.
- `kubectl describe pod` shows `OOMKilled` or `FailedScheduling`.

**Root Cause:**
- **Requests > Limits** (e.g., `limits.cpu: "1"` but `requests.cpu: "2"`).
- **Custom metric causes panic** (e.g., `0/100` hit ratio triggers scaling to zero).

**Fix:**
#### **A. Check Resource Requests/Limits**
```yaml
# Ensure requests <= limits
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1"
    memory: "1Gi"
```

#### **B. Debug Custom Metrics**
If using `external.metrics.kubernetes.io`, ensure the adapter is correctly configured:
```sh
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1" | grep "<your-metric>"
```

---

## **4. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|----------------------|
| **`kubectl top pods`** | Check CPU/Memory usage in real-time. | `watch -n 1 kubectl top pods` |
| **`kubectl describe hpa`** | Inspect scaling events. | `kubectl describe hpa my-app-hpa` |
| **Prometheus + Grafana** | Visualize custom metrics (latency, cache hit ratio). | `kubectl port-forward svc/prometheus 9090:9090` |
| **Metrics Server** | Verify metrics collection. | `kubectl get --raw "/api/v1/namespaces/default/pods"` |
| **`kubectl logs -l`** | Check pod crashes. | `kubectl logs -l app=my-app --previous` |
| **`kubectl exec -it <pod> -- sh`** | Debug inside a pod. | `kubectl exec -it my-app-xyz -- sh` |

**Advanced Debugging:**
- **Enable Verbose Logging:**
  ```sh
  kubectl set env deployment/my-app KUBE_LOG_LEVEL=4 -n <namespace>
  ```
- **Check HPA Events:**
  ```sh
  kubectl get events -w --sort-by=.metadata.creationTimestamp
  ```

---

## **5. Prevention Strategies**
To avoid HPA issues in production:

### **A. Right-Threshold Tuning**
- Start with **conservative targets** (e.g., `targetCPUUtilization: 50%`).
- Gradually adjust based on **real-world load testing**.

### **B. Use Custom Metrics Wisely**
- **Avoid unstable metrics** (e.g., `error_rate` can cause chaotic scaling).
- **Use rolling averages** (e.g., `90m` latency instead of `1m`).

### **C. Set Proper Scaling Bounds**
```yaml
minReplicas: 3   # Avoid zero pods
maxReplicas: 20  # Prevent runaway scaling
behavior:
  scaleUp:
    policies:
    - type: Percent
      value: 20       # Max 20% increase per minute
      periodSeconds: 60
```

### **D. Implement Canary Strategies**
- **Test HPA in staging** before applying to production.
- **Use `kubectl scale` manually** to verify scaling behavior.

### **E. Monitor HPA Performance**
- **Set up alerts** for:
  - Too many scaling events (`kube_hpa_scaling_events_total`).
  - Replicas stuck (`kube_hpa_status_desired_replicas != current_replicas`).
- **Example Prometheus Alert:**
  ```yaml
  - alert: HPAScalingTooAggressive
    expr: increase(kube_hpa_status_replicas{condition="ScalingActivity"}[5m]) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "HPA {{ $labels.namespace }}/{{ $labels.hpa }} is scaling too frequently"
  ```

### **F. Use Cluster Autoscaler (Optional)**
If using cloud providers (EKS/GKE), combine HPA with **Cluster Autoscaler** for node-level scaling.

---
## **6. Final Checklist Before Going Live**
| **Check** | **Action** |
|-----------|------------|
| ✅ HPA metrics correctly configured (CPU/memory/custom). | `kubectl get hpa` |
| ✅ Requests/limits set properly. | `kubectl describe deployment` |
| ✅ Min/max replicas adjusted. | `kubectl edit hpa` |
| ✅ Custom metrics adapter running. | `kubectl get --raw "/apis/custom.metrics.k8s.io"` |
| ✅ Scaling behavior tested in staging. | Load-test with `locust` or `k6` |
| ✅ Alerts set for scaling anomalies. | Prometheus + Alertmanager |

---
## **7. Conclusion**
HPA should **reduce manual intervention** while ensuring **efficient resource usage**. If issues persist:
1. **Start with `kubectl describe hpa`** to check scaling events.
2. **Verify metrics** (`kubectl top pods`, Prometheus).
3. **Adjust thresholds incrementally** (never change multiple settings at once).
4. **Test in staging** before production.

By following this guide, you can **diagnose and fix HPA issues efficiently**, avoiding costly over/under-provisioning. 🚀