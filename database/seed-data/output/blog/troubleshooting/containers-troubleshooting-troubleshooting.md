# **Debugging "Containers Troubleshooting": A Practical Guide**

Containers are a core component of modern cloud-native architectures, enabling efficient deployment, scaling, and isolation. However, issues with containerized applications can arise due to misconfigurations, resource constraints, runtime errors, or networking problems. This guide provides a structured approach to diagnosing and resolving common container-related issues quickly.

---

## **1. Symptom Checklist**
Before diving into debugging, identify and verify these symptoms:

| **Symptom**                          | **Possible Root Cause**                          |
|--------------------------------------|--------------------------------------------------|
| Containers fail to start             | Wrong image, invalid `Dockerfile`, permissions  |
| High CPU/memory usage               | Resource constraints, inefficient apps          |
| Slow network performance            | DNS issues, incorrect `network_mode`             |
| Logs show errors but container runs  | Misconfigured health checks, exit codes          |
| Volumes persist but data is missing  | Incorrect volume mounts, permission errors       |
| Secrets not mounting in containers   | Wrong `secret` annotations, SELinux restrictions |
| Orphaned containers between runs     | Improper cleanup, `restart_policy` misconfig      |
| Port conflicts in multi-container setups | Duplicate port bindings, `publish_all` misuse   |

---

## **2. Common Issues and Fixes (With Code)**

### **2.1 Container Won’t Start**
**Symptom:** `docker ps` shows `Exited (137)` or `Error response from daemon: OOM kill`.

**Debugging Steps:**
1. **Check logs:**
   ```bash
   docker logs <container_id>
   ```
   - If logs show `OOMKilled`, the container ran out of memory. Adjust `memory` limits in the deployment.

2. **Verify image:**
   ```bash
   docker inspect <image> | grep "Error"
   ```
   - If the image fails to pull, check registry access (`docker login`).

3. **Permissions issue:**
   ```bash
   runuser -u root -c "docker run --rm --privileged alpine sh"  # Test basic execution
   ```

**Fix:**
- **Dockerfile Issue:**
  ```dockerfile
  # Ensure correct CMD/ENTRYPOINT
  CMD ["python", "app.py"]
  ```
- **Resource Limits (Kubernetes):**
  ```yaml
  resources:
    limits:
      memory: "512Mi"
      cpu: "1"
  ```

---

### **2.2 Container Crashes Due to High CPU/Memory**
**Symptom:** Container exits or gets killed by the orchestrator.

**Debugging Steps:**
1. **Check resource usage:**
   ```bash
   docker stats <container_id>
   ```
   - If CPU is saturated, check for infinite loops in your app.

2. **Kubernetes resource quotas:**
   ```yaml
   # Check for missing requests/limits
   kubectl describe pod <pod_name>
   ```

**Fix:**
- **Set CPU limits:**
  ```bash
  docker run --cpus="0.5" -it my_image
  ```
- **Update app to handle load:**
  ```python
  # Example: Use async I/O to reduce CPU usage
  asyncio.run(app())
  ```

---

### **2.3 Slow Network Performance**
**Symptom:** Containers can’t reach external APIs or internal services.

**Debugging Steps:**
1. **Check connectivity:**
   ```bash
   docker exec -it <container> ping google.com
   ```
   - If `ping` fails, inspect DNS (`resolv.conf` inside container).

2. **Verify network mode:**
   ```bash
   docker inspect <container> | grep "NetworkMode"
   ```
   - Ensure correct bridge/subnet configuration.

**Fix:**
- **Configure DNS in container:**
  ```bash
  docker run --dns=8.8.8.8 my_image
  ```
- **Kubernetes: Assign correct network:**
  ```yaml
  networkMode: bridge
  ```

---

### **2.4 Logs Show Errors but Container Runs**
**Symptom:** App logs `ERROR` but container exits with code `0`.

**Debugging Steps:**
1. **Check exit code:**
   ```bash
   docker inspect <container> --format='{{.State.ExitCode}}'
   ```
   - If `0` but logs show errors, the error might be non-fatal.

2. **Run interactively:**
   ```bash
   docker run -it --entrypoint sh my_image
   ```

**Fix:**
- **Add health checks:**
  ```yaml
  # Kubernetes example
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
  ```

---

### **2.5 Volumes Not Persisting Data**
**Symptom:** Container writes are lost after restart.

**Debugging Steps:**
1. **Verify volume mount:**
   ```bash
   docker volume inspect <volume_name>
   ```
   - Check if the volume exists and is attached correctly.

2. **Check permissions:**
   ```bash
   docker exec -it <container> ls -la /mounted/path
   ```

**Fix:**
- **Ensure volume exists:**
  ```bash
  docker volume create my_volume
  ```
- **Mount with correct permissions:**
  ```yaml
  # Kubernetes PersistentVolumeClaim
  accessModes:
    - ReadWriteMany
  ```

---

### **2.6 Secrets Not Mounting**
**Symptom:** App can’t read secrets (`ConfigMap` or files).

**Debugging Steps:**
1. **Check secret template:**
   ```yaml
   # Verify the secret is correctly referenced
   envFrom:
    - secretRef:
        name: my_secret
   ```

2. **Test secret access:**
   ```bash
   kubectl exec <pod> -- cat /path/to/mounted/secret
   ```

**Fix:**
- **Mount secrets explicitly:**
  ```yaml
  volumeMounts:
    - name: my-secret
      mountPath: /etc/secrets
  volumes:
    - name: my-secret
      secret:
        secretName: my-secret
  ```

---

### **2.7 Orphaned Containers**
**Symptom:** Containers remain after pods are deleted.

**Debugging Steps:**
1. **List stopped containers:**
   ```bash
   docker ps -a --filter "status=exited"
   ```

2. **Check Kubernetes events:**
   ```bash
   kubectl get events --sort-by='.metadata.creationTimestamp'
   ```

**Fix:**
- **Cleanup manually:**
  ```bash
  docker rm <container_id>
  ```
- **Update pod cleanup policy:**
  ```yaml
  lifecycle:
    preStop:
      exec:
        command: ["/bin/sh", "-c", "rm -rf /tmp/cache"]
  ```

---

### **2.8 Port Conflicts**
**Symptom:** Multiple containers binding to the same port.

**Debugging Steps:**
1. **Check port binding:**
   ```bash
   docker ps -a --format "table {{.Names}}\t{{.Ports}}"
   ```

2. **Kubernetes port conflicts:**
   ```yaml
   # Verify port assignments
   ports:
     - containerPort: 8080
       hostPort: 8080
   ```

**Fix:**
- **Use unique ports:**
  ```bash
  docker run -p 8081:8080 my_image
  ```
- **Kubernetes random ports:**
  ```yaml
  ports:
    - containerPort: 8080
      protocol: TCP
  ```

---

## **3. Debugging Tools and Techniques**

### **3.1 `docker inspect`**
- Deep inspection of container metadata:
  ```bash
  docker inspect <container> | grep -i "error"
  ```

### **3.2 `kubectl debug`**
- Interactive debugging for Kubernetes pods:
  ```bash
  kubectl debug -it <pod> --image=busybox
  ```

### **3.3 `crictl`**
- Debug CRI-compatible containers (Kubernetes):
  ```bash
  crictl ps
  crictl inspect <container_id>
  ```

### **3.4 `tracing` (OpenTelemetry)**
- Debug latency issues:
  ```bash
  docker run -p 4317:4317 open-telemetry/opentelemetry-collector
  ```

### **3.5 `strace` for Kernel Debugging**
- Debug system calls inside a container:
  ```bash
  docker run -it --rm --entrypoint strace my_image ls /app
  ```

---

## **4. Prevention Strategies**

### **4.1 Image Optimization**
- **Multi-stage builds:**
  ```dockerfile
  # Stage 1: Build
  FROM node:16 as builder
  WORKDIR /app
  COPY . .
  RUN npm install && npm run build

  # Stage 2: Runtime
  FROM nginx:alpine
  COPY --from=builder /app/dist /usr/share/nginx/html
  ```
- **Use `scratch` for stateless apps.**

### **4.2 Resource Management**
- **Set CPU/memory limits:**
  ```bash
  docker run --cpus="1" --memory="512m" my_image
  ```
- **Kubernetes ResourceQuota:**
  ```yaml
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  ```

### **4.3 Logging & Monitoring**
- **Centralized logging (Loki, Fluentd):**
  ```yaml
  # Kubernetes DaemonSet for logging
  containers:
    - name: fluentd
      image: fluent/fluentd-kubernetes-daemonset
  ```
- **Metrics (Prometheus + Grafana):**
  ```yaml
  # Scrape container metrics
  scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
        - role: pod
  ```

### **4.4 Health Checks & Liveness Probes**
- **Kubernetes Health Checks:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10
  ```

### **4.5 Security Hardening**
- **Non-root containers:**
  ```bash
  docker run --user=1000 my_image
  ```
- **Read-only filesystem:**
  ```yaml
  securityContext:
    readOnlyRootFilesystem: true
  ```

---

## **5. Final Checklist for Debugging Containers**
| **Step** | **Action** |
|----------|------------|
| 1 | Check logs (`docker logs`, `kubectl logs`) |
| 2 | Verify resource limits (CPU/memory) |
| 3 | Inspect network connectivity (`ping`, `curl`) |
| 4 | Validate volume/secret mounts |
| 5 | Test with minimal config (single container) |
| 6 | Use `debug` pods for Kubernetes issues |
| 7 | Monitor with Prometheus/Grafana |

---

### **Conclusion**
Containers simplify deployment but introduce new debugging challenges. By following this structured approach—checking logs, verifying configurations, and using the right tools—you can resolve issues efficiently. **Prevention (proper resource limits, health checks, and monitoring) reduces future troubleshooting time.**

For advanced issues, refer to:
- [Docker Debugging Docs](https://docs.docker.com/debug/)
- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug/)