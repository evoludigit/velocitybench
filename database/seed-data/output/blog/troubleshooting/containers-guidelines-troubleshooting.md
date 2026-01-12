# **Debugging "Containers Guidelines" Pattern: A Troubleshooting Guide**
*(Optimizing Kubernetes/Docker Container Lifecycle & Compliance)*

---

## **1. Introduction**
This guide helps diagnose and resolve common issues related to **Container Guidelines**—best practices for container design, deployment, security, and observability. Misconfigurations here can lead to:
- Failed deployments
- Resource starvation
- Security vulnerabilities
- Debugging nightmares (e.g., ephemeral containers)

We’ll focus on **Kubernetes/Docker** but apply principles to non-K8s containerized apps.

---

## **2. Symptom Checklist**
| **Symptom**                          | **Likely Cause**                          | **Quick Check** |
|--------------------------------------|------------------------------------------|-----------------|
| Containers crash on startup          | Invalid entrypoint, missing dependencies | `kubectl logs <pod>` |
| High CPU/memory usage                | Missing resource limits, inefficient code | `kubectl top pods` |
| Persistent "CrashLoopBackOff"       | LivenessProbe failure, unhandled errors | `kubectl describe pod` |
| Slow container initialization        | Heavy init scripts, slow DNS resolution | `docker stats` |
| Security warnings (e.g., `non-root`)| Root privileges, open ports             | `kubectl auth can-i` |
| Unreachable internal services        | Incorrect `networkPolicy`, misconfigured `service` | `kubectl get endpoints` |
| Logs missing or corrupted            | Log rotation misconfig, lack of `volume` | `kubectl logs --previous` |

*Pro Tip:* Use `kubectl get events --sort-by=.metadata.creationTimestamp` to trace pod lifecycle issues.

---

## **3. Common Issues & Fixes**

### **A. Bootstrapping Failures**
**Symptom:** Containers fail to start, exit immediately, or hang.
**Root Cause:** Misconfigured `ENTRYPOINT`/`CMD`, missing environment variables, or resource constraints.

#### **Fix: Validate Entrypoint & Initialization**
```yaml
# Example: Kubernetes Deployment with proper entrypoint
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1
        command: ["app"]  # Overrides ENTRYPOINT if specified in Dockerfile
        args: ["--port", "8080"]  # Overrides CMD
```
**Debugging Steps:**
1. **Test locally:**
   ```bash
   docker run --rm -it myapp:v1 sh  # Debug shell before deployment
   ```
2. **Check startup logs:**
   ```bash
   kubectl logs --previous <pod>  # Inspect previous crashes
   ```
3. **Add health checks:**
   ```yaml
   livenessProbe:
     httpGet:
       path: /healthz
       port: 8080
     initialDelaySeconds: 5
   ```

---

### **B. Resource Starvation**
**Symptom:** Containers OOM-killed or throttled (`ContainerKilled` event).
**Root Cause:** No `resources.requests/limits` or over-provisioned pods.

#### **Fix: Set Resource Limits**
```yaml
resources:
  requests:
    cpu: "100m"    # 0.1 CPU
    memory: "256Mi"
  limits:
    cpu: "500m"    # 0.5 CPU
    memory: "512Mi"
```
**Debugging Steps:**
1. **Check resource usage:**
   ```bash
   kubectl top pods  # Identify overused containers
   ```
2. **Use vertical pod autoscaler (VPA):**
   ```bash
   kubectl autoscale deployment myapp --cpu-percent=80 --min=1 --max=3
   ```
3. **Profile apps:** Use `pprof` or `turbostat` to find bottlenecks.

---

### **C. Networking Issues**
**Symptom:** Containers can’t communicate with each other or outside.
**Root Cause:** Missing `service` definitions, misconfigured `networkPolicy`, or DNS misconfig.

#### **Fix: Debug Network Connectivity**
```yaml
# Ensure Services expose ports correctly
apiVersion: v1
kind: Service
metadata:
  name: myapp-svc
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```
**Debugging Steps:**
1. **Test connectivity:**
   ```bash
   kubectl exec -it <pod> -- curl http://myapp-svc:80
   ```
2. **Check DNS resolution:**
   ```bash
   kubectl run -it --rm --image=busybox:1.28 dns-test -- nslookup myapp-svc
   ```
3. **Inspect network policies:**
   ```bash
   kubectl get networkpolicy
   ```

---

### **D. Security Compliance**
**Symptom:** Scanners flag `non-root` violations, open ports, or exposed secrets.
**Root Cause:** Missing `securityContext` or improper volume mounts.

#### **Fix: Enforce Scanning**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop: ["ALL"]
    add: ["NET_BIND_SERVICE"]
```
**Debugging Steps:**
1. **Audit with `kube-bench` or `kubesec`:**
   ```bash
   kubesec scan deployment myapp
   ```
2. **Check pod security standards:**
   ```bash
   kubectl describe pod myapp-pod | grep SecurityContext
   ```
3. **Rotate secrets:**
   ```bash
   kubectl create secret generic db-pass --from-literal=password=NewPass123!
   ```

---

### **E. Observability Gaps**
**Symptom:** No logs/metrics, hard to debug.
**Root Cause:** Missing sidecars (`Fluentd`, `Prometheus`), or `volumeMounts` misconfig.

#### **Fix: Add Logging & Monitoring**
```yaml
# Example: Sidecar for logs
containers:
- name: app
  image: myapp:v1
  volumeMounts:
  - name: logs
    mountPath: /var/log/app
- name: logsidecar
  image: fluentd:latest
  volumeMounts:
  - name: logs
    mountPath: /fluentd/logs
volumes:
- name: logs
  emptyDir: {}
```
**Debugging Steps:**
1. **Check log aggregation (ELK/Stackdriver):**
   ```bash
   kubectl logs -l app=myapp --tail=50
   ```
2. **Add Prometheus metrics:**
   ```yaml
   ports:
   - containerPort: 8080
     name: http
   - containerPort: 9090
     name: metrics
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                          | **Example Command**                     |
|------------------------|---------------------------------------|-----------------------------------------|
| `kubectl debug`        | Enter a running/failed pod            | `kubectl debug -it <pod>`              |
| `kubectl explain`      | Docs for YAML fields                  | `kubectl explain deployment.spec`       |
| `crictl`               | Debug container runtime               | `crictl ps`                             |
| `traceroute`           | Network latency issues                 | `kubectl exec -it <pod> -- traceroute db` |
| `strace`               | Kernel-level debugging                | `kubectl debug -it <pod> --image=busybox -- chroot / -- strace /app` |
| **Lens/Octant**        | GUI for K8s troubleshooting           | Install via browser                     |

**Pro Tip:** Use `kubectl port-forward <pod> 8080:80` to test locally.

---

## **5. Prevention Strategies**
### **A. Build-Time Checks**
- **Dockerfile:**
  - Use multi-stage builds to reduce image size.
  - Enforce `USER nonroot` and set `WORKDIR`.
  - Example:
    ```dockerfile
    FROM golang:1.20 as builder
    WORKDIR /app
    COPY . .
    RUN go build -o /app/bin/app

    FROM alpine:latest
    USER 1000
    WORKDIR /app
    COPY --from=builder /app/bin/app .
    CMD ["./app"]
    ```
- **Scan images for vulnerabilities:**
  ```bash
  docker scan myapp:v1
  ```

### **B. Deployment-Time Checks**
- **Use `initContainers` for pre-flight checks:**
  ```yaml
  initContainers:
  - name: check-db
    image: curlimages/curl
    command: ['sh', '-c', 'until curl -f http://db:5432; do sleep 5; done']
  ```
- **Leverage `admission controllers` (e.g., OPA/Gatekeeper) to enforce policies.**

### **C. Runtime Monitoring**
- **Set up alerts for:**
  - `Failed` pods (`kubectl get pods -o jsonpath='{.items[*].status.phase}' | grep Failed`)
  - High CPU/memory usage (`kubectl top nodes --containers`)
- **Use `kubenetes-e2e-test` for regression testing:**
  ```bash
  go test -v -timeout 30m ./test/e2e/container_lifecycle
  ```

### **D. Documentation & Conventions**
- **Adopt a `container-spec.json` template:**
  ```json
  {
    "image": "myapp:v1",
    "entrypoint": ["/app/bin/app"],
    "env": ["DB_URL=postgres://user:pass@db:5432/db"],
    "healthCheck": { "path": "/healthz" },
    "resources": { "limits": { "cpu": "500m", "memory": "512Mi" } }
  }
  ```
- **Update `README` with:**
  - Required environment variables.
  - Port mappings.
  - Debugging commands.

---

## **6. Advanced Debugging**
### **A. Kernel-Level Issues**
If containers fail with `OOMKilled` or `Killed`, check:
```bash
dmesg | grep -i "killed process"
cat /proc/<pid>/status | grep VmRSS
```
**Fix:** Adjust `vm.overcommit_memory` in `/etc/sysctl.conf` (if using hostPath).

### **B. GPU/Accelerator Issues**
For NVIDIA GPU pods:
```yaml
containers:
- name: app
  image: nvcr.io/nvidia/cuda:11.0-base
  resources:
    limits:
      nvidia.com/gpu: 1
```
**Debug:**
```bash
nvidia-smi  # Check GPU usage
```

---

## **7. Summary Checklist**
| **Step**               | **Action**                                  |
|------------------------|--------------------------------------------|
| **Bootstrap Issues**   | Validate `ENTRYPOINT`, `CMD`, and probes.   |
| **Resources**          | Set `requests/limits` and VPA.             |
| **Networking**         | Test `Service` endpoints and `NetworkPolicy`. |
| **Security**           | Use `securityContext` and scan images.     |
| **Observability**      | Add logs/metrics and sidecars.             |
| **Prevention**         | Enforce `Dockerfile` rules and `initContainers`. |

---
**Final Note:** Container debugging is iterative. Start with logs, then scale to network/profiling tools. Automate checks with `pre-commit hooks` or CI gates!