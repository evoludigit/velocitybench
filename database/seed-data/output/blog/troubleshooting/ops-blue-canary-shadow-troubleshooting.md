# **Debugging Blue Canary Shadow Patterns: A Troubleshooting Guide**

## **Introduction**
Blue/Green or Canary Deployments are widely used to minimize downtime and risk during application updates. However, when shadowing (deploying a new version alongside the current one without traffic routing) is not properly configured, issues like inconsistent behavior, traffic leaks, or unintended failures can arise.

This guide provides a structured approach to diagnosing and resolving problems in **Blue Canary Shadow Patterns**, focusing on real-world symptoms, common pitfalls, and actionable fixes.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your issue aligns with the following symptoms:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|------------------|
| **Inconsistent API Responses** | Some requests return old version data, others new version | Misconfigured routing rules |
| **Traffic Leakage** | Requests go to old service despite shadow traffic being disabled | Incorrect service mesh/load balancer rules |
| **Shadow Traffic Not Working** | New version deployed but no traffic routed to it | Missing annotations/config in Kubernetes/Ingress |
| **5xx Errors in Shadow Mode** | New service fails under load but old one works fine | Unhandled version differences (e.g., schema, dependencies) |
| **Slow Response Times** | Increased latency when shadow traffic is enabled | Resource contention (CPU, memory) between versions |
| **Unintended Side Effects** | Logging/metrics break or behavior changes in shadowed service | Debug logging or analytics misconfigured for new version |
| **Orphaned Shadow Deployments** | Old shadow versions still running after rollback | Improper cleanup of shadow pods/services |

---

## **2. Common Issues & Fixes**

### **Issue 1: Traffic Not Routing to Shadow Service**
**Symptoms:**
- Shadow deployment exists but traffic still goes to the old version.
- Pods are running, but requests don’t hit them.

**Common Causes & Fixes:**
#### **A. Misconfigured Ingress/Service Mesh Rules**
If using **Kubernetes Ingress**, ensure the shadow service is included in the routing rules:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
spec:
  rules:
  - host: myapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: old-service  # Default traffic
            port:
              number: 8080
      - path: /shadow
        pathType: Prefix
        backend:
          service:
            name: new-service  # Shadow traffic
            port:
              number: 8080
```

**Fix:** Add a **separate path** for shadow traffic or use **weighted routing** (Istio, Nginx Ingress).

---
#### **B. Missing Istio VirtualService for Shadow Traffic**
If using **Istio**, ensure `VirtualService` includes the shadow version:
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
  - myapp.com
  http:
  - match:
    - uri:
        prefix: "/v1"
    route:
    - destination:
        host: old-service
        port:
          number: 8080
  - match:
    - uri:
        prefix: "/v2"  # Shadow traffic
    route:
    - destination:
        host: new-service
        port:
          number: 8080
    weight: 10  # 10% traffic to new service
```

**Fix:** Update `VirtualService` to include the shadow version with a **weight** (e.g., `weight: 10`).

---

### **Issue 2: Shadow Service Fails Under Load**
**Symptoms:**
- New version crashes under load, but old version works fine.
- Logs show resource exhaustion (OOM, high CPU).

**Common Causes & Fixes:**
#### **A. Resource Constraints Mismatch**
If the new version has **higher memory/CPU requirements**, the shadow pod may crash.

**Fix:** Adjust resource requests/limits:
```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "1Gi"
```

**Debugging:**
- Check pod logs:
  ```sh
  kubectl logs <shadow-pod-name> --previous
  ```
- Verify resource usage:
  ```sh
  kubectl top pod -n <namespace>
  ```

---

#### **B. Database Schema/Dependency Mismatch**
If the new version expects a different database schema, it may fail silently.

**Fix:**
- **Validate database migrations** before shadowing.
- Use **feature flags** to enable new functionality gradually.

**Example (Feature Flag):**
```python
if feature_flag.enabled("new_feature"):
    # New logic
else:
    # Fallback to old behavior
```

---

### **Issue 3: Traffic Leakage (Shadow Traffic Persists After Disable)**
**Symptoms:**
- Shadow traffic is disabled but requests still reach the old service.

**Common Causes & Fixes:**
#### **A. Incorrect Weighted Routing in Istio/Nginx**
If `weight: 100` was set for the old service, traffic won’t shift to the new one.

**Fix:** Adjust weights properly:
```yaml
http:
- route:
  - destination:
      host: old-service
      port:
        number: 8080
    weight: 0  # Disable old traffic
  - destination:
      host: new-service
      port:
        number: 8080
    weight: 100  # Full traffic to new
```

**Debugging:**
- Check Istio `VirtualService` weights:
  ```sh
  kubectl get vs -n istio-system
  ```

---

#### **B. Sticky Sessions Misconfigured**
If `sessionAffinity` is set in the Service, requests may stick to the old pod.

**Fix:** Disable sticky sessions:
```yaml
sessionAffinity: None
```

---

### **Issue 4: Shadow Pods Not Cleaning Up After Rollback**
**Symptoms:**
- Shadow pods remain after rolling back to the old version.

**Common Causes & Fixes:**
#### **A. Missing Finalizers or Lifecycle Hooks**
Pods may not delete due to **finalizers** or **termination delays**.

**Fix:**
- Ensure **no finalizers** are blocking deletion:
  ```sh
  kubectl describe pod <shadow-pod> | grep Finalizers
  ```
- If using **Helm**, check `rollback` behavior:
  ```sh
  helm rollback <release-name> 1
  ```

---

---

## **3. Debugging Tools & Techniques**

### **A. Observability Tools**
| **Tool** | **Use Case** | **Command/Example** |
|----------|------------|---------------------|
| **Prometheus + Grafana** | Monitor resource usage, error rates | `http_requests_in_progress > 1000` |
| **Istio Telemetry** | Check traffic distribution | `kubectl get istiovs` |
| **Kubernetes Events** | Debug pod failures | `kubectl get events --sort-by=.metadata.creationTimestamp` |
| **Jaeger/Tracing** | Identify latency spikes | `curl http://jaeger-query:16686/search` |
| **Kiali (Istio)** | Visualize service mesh traffic | `kubectl port-forward svc/kiali 20001:20001 -n istio-system` |

### **B. Practical Debugging Steps**
1. **Check Shadow Pods:**
   ```sh
   kubectl get pods -n <namespace> | grep shadow
   ```
2. **Inspect Network Traffic:**
   ```sh
   kubectl exec -it <pod-name> -c istio-proxy -- curl -v http://localhost:15090/stats/prompt
   ```
3. **Verify Ingress Rules:**
   ```sh
   kubectl describe ingress <ingress-name>
   ```
4. **Test Shadow Endpoint Directly:**
   ```sh
   curl -H "Host: myapp.com" -H "X-Forwarded-Proto: https" http://<shadow-service-ip>/v2
   ```

---

## **4. Prevention Strategies**

### **A. Best Practices for Shadow Deployments**
✅ **Use Canary Analysis Tools** (e.g., Prometheus Alertmanager, Datadog) to monitor shadow traffic.
✅ **Gradual Rollout** – Start with **5-10% traffic** to the shadow version.
✅ **Database Compatibility Check** – Validate schema changes before deploying.
✅ **Feature Flagging** – Enable new features only for shadow traffic.
✅ **Automated Rollback** – Use **Argo Rollouts** or **Flagger** for canary analysis.
✅ **Resource Guardrails** – Set **PodDisruptionBudgets** and **HPA limits**.

### **B. Example: Canary Deployment with Argo Rollouts**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 10m}
      - setWeight: 30
      analysis:
        metrics:
        - name: "error-rate"
          threshold: 5%
          interval: 1m
        - name: "latency"
          thresholdRange:
            min: 100ms
            max: 500ms
```

### **C. Post-Mortem Checklist**
- Was shadow traffic **proportionally increased**?
- Were **resources** sufficient for the new version?
- Were **dependencies** (DB, 3rd-party APIs) tested?
- Was there a **rollback strategy** in place?

---

## **Conclusion**
Blue/Green Shadow Deployments are powerful but require careful configuration. By following this guide, you can:
✔ **Quickly diagnose** traffic misrouting, failures, or leaks.
✔ **Fix issues** with service mesh, Ingress, or resource constraints.
✔ **Prevent future problems** with canary analysis and feature flags.

**Next Steps:**
- **Automate rollbacks** with monitoring alerts.
- **Test shadow deployments** in a staging environment first.
- **Document** your canary strategy for future teams.

---
**Need more help?**
- [Istio Canary Documentation](https://istio.io/latest/docs/tasks/traffic-management/canary/)
- [Kubernetes Ingress Canary Guide](https://kubernetes.github.io/ingress-nginx/examples/canary/)