# **Debugging Container Orchestration with Docker and Kubernetes: A Troubleshooting Guide**

## **Introduction**
Container orchestration using **Docker** and **Kubernetes (K8s)** automates deployment, scaling, and management of containerized applications. However, issues like failed deployments, scaling bottlenecks, and service discovery problems can arise. This guide provides a **focused, actionable approach** to diagnosing and resolving common Kubernetes and Docker issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue using this checklist:

### **Deployment & Pod Issues**
- [ ] Pods are stuck in `Pending`, `CrashLoopBackOff`, or `ImagePullBackOff` state
- [ ] Containers fail to start (`Init:Error`, `Error`)
- [ ] Logs show `Permission denied`, `NotFound`, or `Connection refused`
- [ ] Deployments rollback unexpectedly

### **Scaling Issues**
- [ ] Horizontal Pod Autoscaler (HPA) fails to scale up/down
- [ ] Resource requests/limits (`cpu/memory`) cause OOM kills
- [ ] Manual scaling via `kubectl scale` fails

### **Service & Networking Issues**
- [ ] Services can’t communicate (`404 NotFound`, `Service Unavailable`)
- [ ] Pods are `CrashLoopBackOff` due to dependency failures
- [ ] DNS resolution failures (`kube-dns` or `CoreDNS` issues)

### **Cluster & Node Issues**
- [ ] Nodes report `NotReady` status
- [ ] Pods evicted due to OOM or disk pressure
- [ ] `etcd` or API server crashes (high latency)
- [ ] Persistent volumes (PVs) fail to mount

---

## **2. Common Issues & Fixes**

### **2.1 Pods Not Starting**
#### **Issue:** Pod stuck in `Pending` or `CrashLoopBackOff`
**Symptoms:**
- `kubectl get pods` shows `0/1 containers created`
- Logs: `Error: ImagePullBackOff` or `Error: Permission denied`

#### **Diagnosis & Fixes**
1. **Check Image Issues**
   - Verify the Docker image exists in the registry:
     ```sh
     docker pull <image-name>:<tag>  # Test locally
     ```
   - If private registry, ensure:
     - A `Secret` is created for authentication:
       ```sh
       kubectl create secret docker-registry regcred \
         --docker-server=<registry-url> \
         --docker-username=<user> \
         --docker-password=<password> \
         --docker-email=<email>
       ```
     - The `imagePullSecrets` field is added to the Pod:
       ```yaml
       spec:
         imagePullSecrets:
           - name: regcred
       ```

2. **Check Resource Limits**
   - If `CrashLoopBackOff`, ensure CPU/memory requests are correct:
     ```sh
     kubectl describe pod <pod-name>
     ```
   - Adjust in the deployment:
     ```yaml
     resources:
       requests:
         cpu: "100m"
         memory: "256Mi"
       limits:
         cpu: "500m"
         memory: "512Mi"
     ```

3. **Check Volume Mounts**
   - If PVC/PV fails, check:
     ```sh
     kubectl describe pvc <pvc-name>
     ```
   - Ensure storage class provisions correctly:
     ```yaml
     apiVersion: v1
     kind: PersistentVolumeClaim
     metadata:
       name: my-pvc
     spec:
       storageClassName: "standard"
       accessModes:
         - ReadWriteOnce
       resources:
         requests:
           storage: 1Gi
     ```

---

### **2.2 Service Discovery Failures**
#### **Issue:** Services can’t communicate (`Connection refused`)
**Symptoms:**
- Pods log: `Failed to connect to <service-name>`
- `kubectl exec` into a pod fails to reach other services

#### **Debugging Steps**
1. **Verify Service Endpoint**
   ```sh
   kubectl get endpoints <service-name>
   ```
   - If no IPs appear, check if pods are labeled correctly:
     ```sh
     kubectl get pods --show-labels
     ```

2. **Check Service Type**
   - Ensure `ClusterIP` is used (not `NodePort`/`LoadBalancer` if internal):
     ```yaml
     apiVersion: v1
     kind: Service
     metadata:
       name: my-service
     spec:
       type: ClusterIP
       selector:
         app: my-app
       ports:
         - protocol: TCP
           port: 80
           targetPort: 8080
     ```

3. **Test DNS Resolution Inside Pod**
   ```sh
   kubectl exec -it <pod-name> -- sh
   nslookup <service-name>
   ```
   - If DNS fails, check `kube-dns`/`CoreDNS` logs:
     ```sh
     kubectl logs -n kube-system -l k8s-app=kube-dns
     ```

---

### **2.3 Node Issues (NotReady, Evictions)**
#### **Issue:** Nodes report `NotReady` or pods evicted
**Symptoms:**
- `kubectl get nodes` shows `NotReady`
- Pods evicted with `Insufficient memory/cpu`

#### **Debugging Steps**
1. **Check Node Conditions**
   ```sh
   kubectl describe node <node-name>
   ```
   - Look for `MemoryPressure`, `DiskPressure`, or `PIDPressure`.

2. **Monitor Resource Usage**
   ```sh
   kubectl top node
   ```
   - If OOM kills occur, increase limits or add more nodes.

3. **Check Kubernetes Components**
   - If `kubelet` fails, check logs:
     ```sh
     journalctl -u kubelet -n 50
     ```

---

## **3. Debugging Tools & Techniques**

### **3.1 Essential Commands**
| Issue Type | Command |
|------------|---------|
| **Check Pod Logs** | `kubectl logs <pod-name> -c <container-name>` |
| **Exec into Pod** | `kubectl exec -it <pod-name> -- sh` |
| **Describe Pod/Service** | `kubectl describe pod/service <name>` |
| **Check Events** | `kubectl get events --sort-by='.metadata.creationTimestamp'` |
| **Check Network** | `kubectl get endpoints,svc` |

### **3.2 Logging & Monitoring**
- **`kubectl logs`**: Inspect container logs.
- **Prometheus + Grafana**: Monitor cluster metrics.
- **`kubectl top`**: Check CPU/memory usage.
- **`fluentd`/`EFK Stack`**: Centralized logging.

### **3.3 Network Debugging**
- **`tcpdump` inside Pod**:
  ```sh
  kubectl exec -it <pod> -- tcpdump -i eth0 -w - | less
  ```
- **Check Firewall Rules**:
  ```sh
  kubectl get netpol  # Check NetworkPolicies
  ```

### **3.4 Debugging etcd/API Server**
- **Check etcd Health**:
  ```sh
  ETCDCTL_API=3 etcdctl endpoint health --write-out=table
  ```
- **API Server Errors**:
  ```sh
  kubectl get --raw="/healthz" | jq
  ```

---

## **4. Prevention Strategies**

### **4.1 Best Practices for Stable Deployments**
✅ **Use Resource Requests/Limits** (Avoid OOM kills).
✅ **Leverage ConfigMaps/Secrets** (Avoid hardcoding credentials).
✅ **Enable Liveness/Readiness Probes**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10
  ```
✅ **Use Helm Charts** for complex deployments.

### **4.2 Scaling & High Availability**
✅ **Configure Horizontal Pod Autoscaler (HPA)**:
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: my-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: my-deployment
    minReplicas: 2
    maxReplicas: 10
    metrics:
      - type: Resource
        resource:
          name: cpu
          target:
            type: Utilization
            averageUtilization: 70
  ```
✅ **Use Node Affinity/Anti-Affinity** to distribute pods.

### **4.3 Security Hardening**
✅ **Run as Non-Root User**:
  ```yaml
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
  ```
✅ **Enable Pod Security Policies (PSP)** or **OPA/Gatekeeper**.
✅ **Use Network Policies** to restrict pod-to-pod communication.

---

## **5. Quick Reference Summary**
| **Symptom** | **Quick Fix** |
|-------------|--------------|
| **Pod stuck in `Pending`** | Check `kubectl describe pod` for resource/PV issues. |
| **ImagePullBackOff** | Verify `imagePullSecrets` and registry credentials. |
| **Service not reachable** | Check `kubectl get endpoints` and DNS resolution. |
| **Node `NotReady`** | Check `kubectl describe node` for `MemoryPressure`. |
| **CrashLoopBackOff** | Increase CPU/memory limits or debug logs. |

---

## **Conclusion**
By following this guide, you can **quickly diagnose and resolve** common Kubernetes/Docker issues. Always:
✔ **Check logs first** (`kubectl logs`, `kubectl describe`).
✔ **Validate configurations** (YAML, resources, networking).
✔ **Monitor proactively** (Prometheus, Grafana, HPA).

For persistent issues, **enable debug logging** and **consult the community** (Stack Overflow, Kubernetes Slack). 🚀