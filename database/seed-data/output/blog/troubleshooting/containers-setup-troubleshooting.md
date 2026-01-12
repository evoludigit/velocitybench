# **Debugging Containers Setup: A Practical Troubleshooting Guide**

Containers (Docker, Kubernetes, etc.) are essential for modern microservices and scalable applications. However, misconfigurations, networking issues, resource constraints, or runtime problems can lead to deployment failures, performance degradation, or crashes. This guide provides a **practical, step-by-step approach** to diagnosing and resolving common container-related issues.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms match your problem:

| **Symptom** | **Description** |
|-------------|----------------|
| ❌ **Container fails to start** | Logs show errors, but container does not run (e.g., `Exit Code 137` for OOM kills). |
| ❌ **Slow performance** | High CPU/memory usage, slow response times, or container restarts. |
| ❌ **Network connectivity issues** | Containers can’t reach databases, APIs, or each other (e.g., `curl: (7) Failed to connect`). |
| ❌ **Volumes not mounting** | Files are missing inside containers, or writes don’t persist. |
| ❌ **Kubernetes pods stuck in CrashLoopBackOff** | Logs indicate crashes, but Kubernetes can’t keep them running. |
| ❌ **Docker daemon crashes** | No containers start; `docker-compose up` fails. |
| ❌ **Security-related failures** | Permission denied errors, SELinux/AppArmor blocking operations. |
| ❌ **Environment variable issues** | App fails because required env vars are missing. |

---
---

## **2. Common Issues and Fixes**
### **A. Container Fails to Start**
#### **Issue 1: Missing Dependencies or Incorrect Image**
- **Symptoms:** `"Command not found"`, `"Could not find module"`, or `Exit Code 127`.
- **Debugging Steps:**
  1. **Check logs:**
     ```bash
     docker logs <container_id_or_name>
     ```
  2. **Verify the image:**
     ```bash
     docker image inspect <image_name> | grep "Cmd"
     ```
     - If the `CMD` is missing or incorrect, rebuild the image.
  3. **Test locally:**
     ```bash
     docker run -it <image_name> /bin/sh  # Enter and manually check dependencies.
     ```

#### **Fix:**
- **Recreate the image** with correct dependencies (e.g., `apt-get install`, `pip install`).
- **Use a base image with pre-installed dependencies** (e.g., `python:3.9-slim-buster`).

#### **Example Dockerfile Fix:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```

---

#### **Issue 2: Out-of-Memory (OOM) Kill**
- **Symptoms:** `"Killed"`, `Exit Code 137`.
- **Debugging Steps:**
  1. Check memory usage:
     ```bash
     docker stats <container_id>
     ```
  2. Adjust memory limits in `docker-compose.yml`:
     ```yaml
     deployment:
       resources:
         limits:
           memory: 1G
     ```

#### **Fix:**
- **Optimize the app** (reduce memory usage).
- **Increase memory allocation** (if possible).
- **Use a smaller base image** (e.g., `alpine`-based).

---

#### **Issue 3: Network Connectivity Failures**
- **Symptoms:** `"Connection refused"`, `"Network is unreachable"`.
- **Debugging Steps:**
  1. **Test inside the container:**
     ```bash
     docker exec -it <container_id> sh
     ping <target_ip>
     curl http://<service_address>  # If using a service, get its IP first.
     ```
  2. **Check container networking:**
     ```bash
     docker network inspect <network_name>
     ```
  3. **For Kubernetes:**
     ```bash
     kubectl describe pod <pod_name> | grep -i "ip:"
     kubectl logs <pod_name>
     ```

#### **Fixes:**
- **Ensure the container has access to the network** (e.g., `--network=host` for direct access).
- **Verify DNS resolution** (if using `nginx`, `kube-dns`, or `CoreDNS`).
- **Check firewall rules** (e.g., `iptables`, `ufw`).
- **For Kubernetes:** Ensure `Service` and `Ingress` are correctly configured.

---

### **B. Volumes Not Mounting**
#### **Issue 1: Missing Volume Definition**
- **Symptoms:** Files not found inside the container, writes disappear after restart.
- **Debugging Steps:**
  1. **Check mounted volumes:**
     ```bash
     docker inspect <container_id> | grep "Mounts"
     ```
  2. **Verify Docker volume exists:**
     ```bash
     docker volume ls
     ```

#### **Fix:**
- **Correct `docker-compose.yml`:**
  ```yaml
  services:
    app:
      volumes:
        - ./data:/app/data  # Binds a host dir
        - volume_name:/app/persistent_data  # Uses a named volume
  volumes:
    volume_name:
  ```

---

### **C. Kubernetes-Specific Issues**
#### **Issue 1: Pods in CrashLoopBackOff**
- **Symptoms:** Pod keeps restarting, logs show an error.
- **Debugging Steps:**
  1. **Check logs:**
     ```bash
     kubectl logs <pod_name> --previous  # For previous instance
     ```
  2. **Describe the pod:**
     ```bash
     kubectl describe pod <pod_name>
     ```
  3. **Check events:**
     ```bash
     kubectl get events --sort-by=.metadata.creationTimestamp
     ```

#### **Fixes:**
- **Increase readiness probe timeout:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  ```
- **Fix application errors** (e.g., missing env vars, DB connection issues).

---

## **3. Debugging Tools and Techniques**
| **Tool** | **Purpose** | **Example Usage** |
|----------|------------|------------------|
| **`docker logs`** | View container logs. | `docker logs -f <container_id>` |
| **`kubectl logs`** | View Kubernetes pod logs. | `kubectl logs <pod_name>` |
| **`docker inspect`** | Get container details. | `docker inspect <container_id>` |
| **`kubectl describe`** | Debug Kubernetes resources. | `kubectl describe pod <pod_name>` |
| **`stress`** | Simulate load for testing. | `docker run --rm ubuntu stress --cpu 1` |
| **`netstat` / `ss`** | Check network connections. | `docker exec -it <container_id> netstat -tulnp` |
| **`docker stats`** | Monitor resource usage. | `docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"` |
| **`kubectl top`** | Check pod resource usage. | `kubectl top pod` |
| **`traceroute` / `mtr`** | Debug network latency. | `docker exec -it <container_id> traceroute google.com` |
| **`strace`** | Debug system call issues. | `docker run -it --rm ubuntu strace -e trace=open -p <pid>` |
| **`kubectl debug`** | Attach a shell to a struggling pod. | `kubectl debug -it <pod_name> --image=busybox` |

---

## **4. Prevention Strategies**
### **A. Best Practices for Docker**
1. **Use `.dockerignore`** to exclude unnecessary files.
2. **Optimize images** (multi-stage builds, minimal layers).
   ```dockerfile
   # Multi-stage build example
   FROM golang:1.20 as builder
   WORKDIR /app
   COPY . .
   RUN go build -o /app/app

   FROM alpine:latest
   COPY --from=builder /app/app /app/
   CMD ["/app/app"]
   ```
3. **Set resource limits** (`docker-compose.yml`):
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '0.5'
         memory: 512M
   ```
4. **Use health checks** (Docker) or **liveness probes** (Kubernetes).
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s \
     CMD curl -f http://localhost:8080/health || exit 1
   ```

### **B. Best Practices for Kubernetes**
1. **Use resource requests/limits** in deployments:
   ```yaml
   resources:
     requests:
       cpu: "100m"
       memory: "128Mi"
     limits:
       cpu: "500m"
       memory: "512Mi"
   ```
2. **Enable horizontal pod autoscaling (HPA):**
   ```yaml
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
             averageUtilization: 50
   ```
3. **Use ConfigMaps and Secrets** instead of hardcoding secrets.
   ```yaml
   env:
     - name: DB_PASSWORD
       valueFrom:
         secretKeyRef:
           name: db-secret
           key: password
   ```
4. **Monitor with Prometheus + Grafana** for early issue detection.

### **C. General Prevention**
- **Test locally first** (use `docker-compose` before Kubernetes).
- **Use logging aggregation** (ELK Stack, Loki, Fluentd).
- **Implement CI/CD pipelines** with container scanning (Trivy, Snyk).
- **Document container configurations** (e.g., GitHub wiki, Confluence).

---

## **5. Final Checklist for Quick Resolution**
1. **Check logs** (`docker logs`, `kubectl logs`).
2. **Verify networking** (`ping`, `curl`, `docker network inspect`).
3. **Inspect resources** (`docker stats`, `kubectl top`).
4. **Test with a minimal example** (reduce complexity).
5. **Compare working vs. broken configurations**.
6. **Apply fixes incrementally** (avoid making multiple changes at once).
7. **Reproduce in a staging environment** before production.

---
## **Conclusion**
Containers introduce new layers of complexity, but systematic debugging reduces downtime. **Start with logs, verify networking, check resources, and test changes incrementally.** By following this guide, you should be able to **resolve 90% of container-related issues efficiently**.

For persistent problems, **check documentation, community forums (Stack Overflow, GitHub Issues), and container runtime logs** for deeper insights.

---
**Next Steps:**
- **For Docker:** [`docker-compose` docs](https://docs.docker.com/compose/)
- **For Kubernetes:** [`kubectl` cheat sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- **For Monitoring:** [Prometheus Kubernetes docs](https://prometheus.io/docs/prometheus/latest/getting_started/)