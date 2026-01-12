# **Debugging Containers Strategies: A Troubleshooting Guide**

## **Introduction**
The **Containers Strategies** pattern involves deploying applications in lightweight, isolated containers (e.g., Docker, Kubernetes) for scalability, consistency, and efficient resource utilization. While containers simplify deployment, issues can arise due to misconfigurations, network problems, or runtime errors.

This guide provides a **focused, actionable** approach to diagnosing and resolving common container-related issues quickly.

---

## **1. Symptom Checklist**
Before diving into debugging, validate these **common symptoms** to narrow down potential problems:

| **Symptom**                     | **Possible Root Cause**                          |
|---------------------------------|-------------------------------------------------|
| Container fails to start        | Missing dependencies, incorrect config maps, health checks, or resource limits. |
| Container hangs or crashes      | Resource starvation, infinite loops, or misconfigured entrypoints. |
| Slow application performance    | CPU/memory throttling, inefficient containers, or suboptimal scheduling. |
| Network issues (e.g., no connectivity) | Incorrect `NetworkMode`, misconfigured DNS, or missing `NetworkPolicy`. |
| Logs show errors (e.g., `503 Service Unavailable`) | Application crashes, unhealthy pods, or misconfigured load balancers. |
| Persistent data corruption      | Volume mounts misconfigured, incorrect permissions, or corruption in storage. |
| Image pull failures             | Private registry misconfig, network restrictions, or corrupted images. |

---

## **2. Common Issues & Fixes**

### **2.1 Container Fails to Start (CrashLoopBackOff / Exit Code Errors)**
**Symptom:**
`kubectl describe pod <pod-name>` shows **"CrashLoopBackOff"** or indicates an **exit code error**.

**Possible Causes & Fixes:**

#### **A. Missing Dependencies**
- **Diagnosis:**
  The container logs show `errno: 2 (No such file or directory)` or `command not found`.
  - Example:
    ```bash
    $ kubectl logs <pod-name>
    Error: Could not find 'some-external-command'
    ```

- **Fix:**
  Ensure the required tools are pre-installed in the image or added via `ENTRYPOINT`/`CMD`.
  - **Example:** Use a base image with required tools (e.g., `FROM python:3.9-slim` instead of a minimal image).
  - **Quick Fix:** Add a shell command in `kubectl exec` to test dependencies.
    ```bash
    kubectl exec -it <pod-name> -- sh
    apt-get update && apt-get install -y <missing-package>  # (Debian-based)
    ```

#### **B. Incorrect ConfigMaps/Secrets**
- **Diagnosis:**
  Application crashes due to missing environment variables or files.
  - Example:
    ```bash
    $ kubectl describe pod <pod-name> | grep -i error
    EnvVarRef not found: <missing-variable>
    ```

- **Fix:**
  Verify ConfigMaps/Secrets and adjust references.
  ```yaml
  # Example: Fixing a missing ConfigMap
  env:
    - name: DB_URL
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: db.url  # Check if key exists
  ```

#### **C. Health Checks Misconfiguration**
- **Diagnosis:**
  Pod starts but is **not ready** (e.g., `livenessProbe`/`readinessProbe` fails).
  - Example:
    ```bash
    $ kubectl get pods -o wide
    STATUS: CrashLoopBackOff (liveness probe failed)
    ```

- **Fix:**
  Adjust probe parameters (e.g., increase timeout, change path).
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 10  # Wait longer for cold starts
    periodSeconds: 5
  ```

#### **D. Resource Limits Violations**
- **Diagnosis:**
  Pod restarts with **"OOMKilled"** (Out of Memory) or CPU throttling.
  - Example:
    ```bash
    $ kubectl describe pod <pod-name> | grep -i limits
    OOMKilled: true
    ```

- **Fix:**
  Adjust CPU/memory requests/limits:
  ```yaml
  resources:
    requests:
      cpu: "500m"  # 0.5 CPU
      memory: "512Mi"
    limits:
      cpu: "1000m"  # 1 CPU
      memory: "1Gi"
  ```

---

### **2.2 Container Hangs or Doesn’t Respond**
**Symptom:**
Pod is **Running**, but `kubectl logs` shows no output, or `curl` returns a timeout.

**Possible Causes & Fixes:**

#### **A. Infinite Loop or Blocking Operation**
- **Diagnosis:**
  Logs are empty, but CPU usage is high.
  - Example:
    ```bash
    $ kubectl top pod <pod-name>
    CPU(m1): 100%
    ```

- **Fix:**
  Check application logs for stuck processes:
  ```yaml
  # Example: Fixing a busy-wait loop
  readinessProbe:
    exec:
      command: ["pgrep", "-f", "sleep 1000"]  # Check if process is stuck
  ```

#### **B. Misconfigured `ENTRYPOINT`/`CMD`**
- **Diagnosis:**
  Container starts but exits immediately (exit code `0` but no response).
  - Example:
    ```bash
    $ kubectl describe pod <pod-name> | grep -i command
    Command: ["sleep", "infinity"]  # Should be `["python", "app.py"]
    ```

- **Fix:**
  Override or correct the entrypoint:
  ```dockerfile
  # In Dockerfile:
  CMD ["python", "app.py"]
  ```

---

### **2.3 Networking Issues**
**Symptom:**
Containers cannot communicate (e.g., database unreachable).

**Possible Causes & Fixes:**

#### **A. Incorrect `NetworkMode`**
- **Diagnosis:**
  Pod logs show `Connection refused` or `DNS lookup failed`.

- **Fix:**
  Ensure proper DNS resolution (use `ClusterIP` for services):
  ```yaml
  # Example: Fixing DNS resolution
  apiVersion: v1
  kind: Service
  metadata:
    name: backend-service
  spec:
    clusterIP: None  # Headless service for direct pod-to-pod
    ports:
      - port: 8080
    selector:
      app: backend
  ```

#### **B. Missing `NetworkPolicy`**
- **Diagnosis:**
  Pods cannot talk to each other even if services are defined.
  - Example:
    ```bash
    $ kubectl get networkpolicies
    No resources found (policy may be too restrictive)
    ```

- **Fix:**
  Allow traffic between namespaces/services:
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-frontend-backend
  spec:
    podSelector:
      matchLabels:
        app: frontend
    policyTypes:
      - Egress
    egress:
      - to:
        - podSelector:
            matchLabels:
              app: backend
        ports:
          - protocol: TCP
            port: 8080
  ```

---

### **2.4 Persistent Data Corruption**
**Symptom:**
Data written to a volume is lost or corrupted.

**Possible Causes & Fixes:**

#### **A. Incorrect Volume Mount Permissions**
- **Diagnosis:**
  Application fails with `Permission denied` when writing to a volume.
  - Example:
    ```bash
    $ kubectl exec <pod-name> -- ls -la /data
    drwx------ 1 root root 4096 Oct 10 10:00 data  # App runs as non-root
    ```

- **Fix:**
  Set proper permissions in the container:
  ```yaml
  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: my-pvc
  securityContext:
    runAsUser: 1000  # Match app user
  ```

#### **B. Storage Backend Issues**
- **Diagnosis:**
  Volume mounts appear empty or data is overwritten.
  - Example:
    ```bash
    $ kubectl exec <pod-name> -- df -h /data
    Filesystem     Size  Used Avail Use% Mounted on
    /dev/sda1      10G   10G     0 100% /data
    ```

- **Fix:**
  Check PVC storage class and resize if needed:
  ```yaml
  resources:
    requests:
      storage: 20Gi  # Increase from default
  ```

---

### **2.5 Image Pull Failures**
**Symptom:**
Pod status is `ImagePullBackOff`.

**Possible Causes & Fixes:**

#### **A. Private Registry Misconfiguration**
- **Diagnosis:**
  Logs show `denied: requested access to the resource is denied`.

- **Fix:**
  Ensure `imagePullSecrets` is correctly set:
  ```yaml
  spec:
    imagePullSecrets:
      - name: regcred  # Secret with credentials
    containers:
      - name: my-app
        image: private-registry.example.com/myapp:latest
  ```

#### **B. Corrupted Image or Network Issues**
- **Diagnosis:**
  `kubectl describe pod` shows `ImagePullError`.

- **Fix:**
  Rebuild and push the image, or retag it:
  ```bash
  docker tag myapp:latest private-registry.example.com/myapp:v2
  docker push private-registry.example.com/myapp:v2
  ```

---

## **3. Debugging Tools & Techniques**
### **3.1 Logging & Observability**
- **Tools:**
  - `kubectl logs <pod-name>` (real-time logs)
  - `kubectl describe pod <pod-name>` (events, conditions)
  - Prometheus + Grafana (metrics for performance issues)
  - ELK Stack (centralized logging)

- **Quick Commands:**
  ```bash
  # Stream logs in real-time
  kubectl logs -f <pod-name>

  # Follow logs with timestamps
  kubectl logs -p <pod-name>

  # Exec into a running container
  kubectl exec -it <pod-name> -- sh
  ```

### **3.2 Network Diagnostics**
- **Tools:**
  - `kubectl exec <pod-name> -- curl <service>` (test connectivity)
  - `kubectl get endpoints <service>` (check if pods are registered)
  - `tcpdump` inside a container (for deep packet inspection)

- **Example:**
  ```bash
  # Test connectivity from inside a pod
  kubectl exec -it <pod-name> -- curl -v http://backend-service:8080/health
  ```

### **3.3 Performance Profiling**
- **Tools:**
  - `kubectl top pods` (CPU/memory usage)
  - `kubectl top nodes` (cluster resource usage)
  - `kubectl explain <resource>` (check API differences)

- **Example:**
  ```bash
  # Check if a pod is CPU-bound
  kubectl top pod <pod-name> --containers
  ```

---

## **4. Prevention Strategies**
### **4.1 Best Practices for Containers**
✅ **Use Multi-Stage Builds** – Reduce final image size.
✅ **Set Resource Requests/Limits** – Prevent OOM kills.
✅ **Implement Health Checks** – Ensure liveness/readiness probes.
✅ **Use Read-Only Filesystems** – Minimize security risks.
✅ **Leverage ConfigMaps/Secrets** – Avoid hardcoding sensitive data.

### **4.2 CI/CD & Infrastructure as Code (IaC)**
✅ **Automated Testing** – Test containers in staging before production.
✅ **Infrastructure as Code (Terraform/Helm)** – Standardize deployments.
✅ **Image Scanning** – Detect vulnerabilities early (e.g., Trivy, Snyk).

### **4.3 Monitoring & Alerting**
✅ **Set Up Prometheus Alerts** – Catch issues before users do.
✅ **Log Aggregation (Fluentd, Loki)** – Centralize logs for debugging.
✅ **Chaos Engineering (Gremlin/Chaos Mesh)** – Test resilience.

---

## **5. Conclusion**
Containers simplify deployment but require **proactive debugging** to maintain reliability. Use this guide to:
1. **Quickly identify symptoms** (logs, metrics, network checks).
2. **Apply targeted fixes** (ConfigMaps, resource limits, networking).
3. **Prevent future issues** (health checks, IaC, monitoring).

For persistent problems, **reproduce in a dev environment** and verify fixes before applying to production.

---
**Final Tip:** Always **start with `kubectl describe pod` and logs**—most issues are visible there.

---
Would you like any section expanded (e.g., deeper dive into Kubernetes networking)?