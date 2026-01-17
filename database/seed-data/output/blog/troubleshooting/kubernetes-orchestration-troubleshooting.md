# **Debugging Kubernetes & Container Orchestration: A Troubleshooting Guide**

## **Introduction**
Kubernetes (K8s) is the de facto standard for orchestrating containerized workloads at scale. While it provides powerful automation, misconfigurations, resource constraints, and network issues can lead to performance degradation, reliability problems, and scaling bottlenecks.

This guide helps you **quickly identify, diagnose, and resolve** common Kubernetes-related issues with a structured approach.

---

## **Symptom Checklist**
Before diving into fixes, confirm which symptoms align with your problem:

| **Symptom** | **Details** |
|-------------|------------|
| **Performance Degradation** | Slow pod startup, high CPU/memory usage, throttling |
| **Frequent Failures** | Pods crashing, evictions, or failing to schedule |
| **Lack of Visibility** | Insufficient logging, metrics, or observability |
| **Scaling Issues** | HPA failing, pods stuck in "Pending" state |
| **Networking Problems** | Pod-to-pod communication failures, DNS resolution issues |
| **Storage & Persistence Failures** | Failed volume mounts, slow I/O performance |
| **Security & Compliance Issues** | Unauthorized access, pod security violations |
| **Control Plane Instability** | `kube-apiserver`, `kube-scheduler`, or `kube-controller-manager` crashes |

---

## **Common Issues & Fixes**

### **1. Pods Stuck in "Pending" State**
**Symptoms:**
- Pods remain in `Pending` state for extended periods.
- Events show `Insufficient CPU/memory` or `No nodes available`.

**Root Causes & Fixes:**

#### **A. Resource Constraints**
**Check:**
```bash
kubectl describe pod <pod-name> -n <namespace>
```
Look for errors like:
```
Error from server (InsufficientCPU): pod has unbound PersistentVolumeClaims
```
or
```
Error from server (ResourceQuota): requests exceed quota
```

**Fix:**
- **Increase node resources** (CPU/memory):
  ```bash
  kubectl top nodes  # Check current usage
  kubectl edit node <node-name>  # Add more resources (if using cloud provider)
  ```
- **Adjust resource requests/limits** in the deployment:
  ```yaml
  resources:
    requests:
      cpu: "1"
      memory: "512Mi"
    limits:
      cpu: "2"
      memory: "1Gi"
  ```
- **Check ResourceQuota limits**:
  ```bash
  kubectl get resourcequota -n <namespace>
  ```

#### **B. Node Selector/Taints/Tolerations Mismatch**
**Check:**
```bash
kubectl describe pod <pod-name>
```
Look for:
```
Events:
  FailedScheduling: node(s) had taint {key=role:NoSchedule}, that the pod didn’t tolerate
```

**Fix:**
- **Annotate nodes** to allow scheduling:
  ```bash
  kubectl taint nodes <node-name> node-role.kubernetes.io/worker:NoSchedule-
  ```
- **Add tolerations** in the pod spec:
  ```yaml
  tolerations:
  - key: "node-role.kubernetes.io/worker"
    operator: "Exists"
    effect: "NoSchedule"
  ```

#### **C. PersistentVolumeClaims (PVC) Not Bound**
**Check:**
```bash
kubectl get pvc -n <namespace>
```
Look for `Status: Pending`.

**Fix:**
- **Verify StorageClass exists**:
  ```bash
  kubectl get storageclass
  ```
- **Ensure PVC requests match available storage**:
  ```yaml
  resources:
    requests:
      storage: 10Gi  # Must match available PV
  ```

---

### **2. Pods CrashLoopBackOff**
**Symptoms:**
- Pods restart repeatedly (`CrashLoopBackOff`).
- Logs show application crashes.

**Root Causes & Fixes:**

#### **A. Application-Level Errors**
**Check logs:**
```bash
kubectl logs <pod-name> -n <namespace> --previous
```

**Fix:**
- **Adjust environment variables** (if config is wrong).
- **Update the deployment** with a fixed image:
  ```bash
  kubectl set image deployment/<deployment-name> <container>=<correct-image>
  ```

#### **B. Resource Limits Too Low**
**Fix:**
Update resource limits in the deployment:
```yaml
resources:
  limits:
    cpu: "1"
    memory: "512Mi"
```

#### **C. Volume Mount Issues**
**Check:**
```bash
kubectl describe pod <pod-name>
```
Look for `FailedMount` errors.

**Fix:**
- **Verify volume permissions**:
  ```yaml
  securityContext:
    fsGroup: 1000  # Ensure pod can access volume
  ```
- **Check `emptyDir` vs `hostPath`** (for testing) vs `PersistentVolume`.

---

### **3. Horizontal Pod Autoscaler (HPA) Not Working**
**Symptoms:**
- HPA fails to scale pods despite high load.
- Events show `Failed to get metrics for scaling`.

**Root Causes & Fixes:**

#### **A. Metrics Server Not Running**
**Check:**
```bash
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/pods" | jq
```
(If `jq` not installed: `kubectl top pods` should work.)

**Fix:**
Install `metrics-server`:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

#### **B. Incorrect Metrics Configuration**
**Check HPA status:**
```bash
kubectl describe hpa <hpa-name>
```
Look for `Unable to fetch metrics` or `Current metrics unavailable`.

**Fix:**
- **Ensure custom metrics (if any) are configured** (e.g., Prometheus Adapter).
- **Check CPU/Memory scaling thresholds**:
  ```yaml
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  ```

#### **C. Node Auto-Scaling Issues (Cluster Autoscaler)**
**Fix:**
- **Check Cluster Autoscaler logs**:
  ```bash
  kubectl logs -n kube-system <cluster-autoscaler-pod>
  ```
- **Ensure IAM roles (for cloud providers) allow scaling**.

---

### **4. Networking Issues (DNS, Ingress, CNI)**
**Symptoms:**
- Pods cannot communicate (`Connection refused`).
- DNS resolution fails (`kube-dns` not responding).

**Root Causes & Fixes:**

#### **A. DNS Resolution Failures**
**Check CoreDNS logs:**
```bash
kubectl logs -n kube-system -l k8s-app=kube-dns
```

**Fix:**
- **Verify CoreDNS pods are running**:
  ```bash
  kubectl get pods -n kube-system -l k8s-app=kube-dns
  ```
- **Check `kube-dns` config** (if using custom DNS):
  ```yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: coredns
    namespace: kube-system
  data:
    Corefile: |
      .:53 {
          errors
          health {
              lameduck 5s
          }
          ready
          kubernetes cluster.local in-addr.arpa ip6.arpa {
              pods insecure
              fallthrough in-addr.arpa ip6.arpa
          }
          prometheus :9153
          forward . /etc/resolv.conf
          cache 30
          loop
          reload
          loadbalance
      }
  ```

#### **B. Ingress Controller Not Routing Traffic**
**Check Ingress:**
```bash
kubectl get ingress -n <namespace>
kubectl describe ingress <ingress-name>
```

**Fix:**
- **Verify Ingress Controller deployment**:
  ```bash
  kubectl get pods -n <ingress-namespace> -l app=ingress-nginx
  ```
- **Check Ingress rules** (e.g., Nginx config):
  ```yaml
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
  ```

#### **C. CNI Plugin Issues (Calico, Flannel, etc.)**
**Check CNI logs:**
```bash
kubectl logs -n kube-system <cni-pod>
```

**Fix:**
- **Restart CNI pods**:
  ```bash
  kubectl delete pod -n kube-system -l k8s-app=cni
  ```
- **Update CNI configuration** (e.g., Calico IPPools).

---

### **5. Storage Issues (PVs Not Available)**
**Symptoms:**
- Pods fail to mount volumes.
- `PersistentVolumeClaim` remains `Pending`.

**Root Causes & Fixes:**

#### **A. StorageClass Not Bound to PV**
**Check:**
```bash
kubectl get storageclass
kubectl describe pvc <pvc-name>
```

**Fix:**
- **Ensure `Provisioner` matches PVC demands**:
  ```yaml
  storageClassName: my-storage-class
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  ```

#### **B. Volume Mount Permissions**
**Fix:**
- **Set `fsGroup` in pod security context**:
  ```yaml
  securityContext:
    fsGroup: 1000
  ```
- **Ensure storage backend (e.g., EBS, Ceph) has proper permissions**.

---

## **Debugging Tools & Techniques**

| **Tool** | **Purpose** | **Usage** |
|----------|------------|-----------|
| **`kubectl`** | Core CLI for K8s operations | `kubectl get pods`, `describe`, `logs` |
| **`stern`** | Multi-pod log tailing | `stern <pod-name> -n <namespace>` |
| **`kubectl top`** | Resource usage (CPU/memory) | `kubectl top pods` |
| **`kubectl debug`** | Debug running pods | `kubectl debug -it <pod> --image=busybox` |
| **Prometheus + Grafana** | Metrics & observability | Query `kube_pod_status_phase` |
| **FlameGraph** | CPU profiling | `kubectl exec -it <pod> -- sh -c "perf record -g -- sleep 5"` |
| **`k9s`** | Terminal-based K8s UI | `k9s` (install via [k9s.io](https://k9scli.io/)) |
| **`velero`** | Backup & restore | `velero backup get` |

---

## **Prevention Strategies**

### **1. Infrastructure & Configuration**
✅ **Use Resource Requests/Limits** – Avoid noisy neighbors.
✅ **Enable Pod Disruption Budgets (PDB)** – Prevent downtime during maintenance.
✅ **Use Readiness & Liveness Probes** – Automatically restart failing pods.
✅ **Leverage Network Policies** – Restrict pod-to-pod traffic.

### **2. Observability & Logging**
✅ **Deploy Prometheus + Grafana** – Monitor CPU, memory, and custom metrics.
✅ **Use Centralized Logging (EFK Stack: Elasticsearch, Fluentd, Kibana)**.
✅ **Enable Pod & Node Logging** – Use `Fluent Bit` to ship logs to a SIEM.

### **3. Security Hardening**
✅ **Enable Pod Security Admission (PSA)** – Restrict privileged pods.
✅ **Use Network Policies** – Isolate namespaces.
✅ **Rotate Secrets & Keys** – Avoid hardcoded credentials.

### **4. GitOps & CI/CD**
✅ **Use ArgoCD/Flux** – Automate deployments from Git.
✅ **Implement Rollback Strategies** – Easy rollback on failures.

### **5. Chaos Engineering**
✅ **Test Failures with Chaos Mesh** – Simulate node failures.
✅ **Run Load Tests (Locust, k6)** – Validate scaling.

---

## **Final Checklist for Quick Resolution**
1. **Check `kubectl get pods -A`** – Identify stuck/failed pods.
2. **Describe the pod (`kubectl describe pod <name>`)** – Find root cause.
3. **Inspect logs (`kubectl logs`)** – Look for errors.
4. **Verify resource constraints (`kubectl top`)** – Adjust if needed.
5. **Check network/DNS (`kubectl exec -it <pod> -- nslookup kubernetes.default`)**.
6. **Validate storage (`kubectl get pvc`)** – Ensure PVCs are bound.
7. **Test scaling (`kubectl scale deployment <name> --replicas=10`)**.
8. **Review metrics (`kubectl top nodes`)** – Identify bottlenecks.

---

## **Conclusion**
Kubernetes debugging can be complex, but **systematically checking logs, resource usage, and network issues** helps narrow down problems quickly. **Prevention (probes, limits, observability) reduces incidents**, while ** Chaos testing** ensures resilience.

For deep dives, refer to:
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)
- [Troubleshooting Cluster Issues](https://github.com/kubernetes/website/blob/main/content/en/docs/tasks/debug-application-cluster/troubleshoot.md)

**Next Steps:**
- Set up **alerts for critical metrics** (CPU, memory, node failures).
- **Automate remediation** (e.g., restart pods via ArgoCD).
- **Conduct post-mortems** for recurring issues.

By following this guide, you should resolve **90% of Kubernetes issues within minutes**.