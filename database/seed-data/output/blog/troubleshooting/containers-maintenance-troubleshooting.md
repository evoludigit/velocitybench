# **Debugging Containers Maintenance: A Troubleshooting Guide**

## **Introduction**
Containers are now the backbone of modern cloud-native applications. However, improper maintenance of containerized environments—such as misconfigured cleanup policies, resource starvation, or corrupted layers—can lead to performance degradation, inefficient resource usage, and even system failures.

This guide provides a **practical, step-by-step approach** to diagnosing and resolving common container maintenance issues in Docker, Kubernetes, and other container orchestration platforms.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if the issue falls under **containers maintenance-related problems**. Common symptoms include:

| **Symptom**                     | **Possible Cause**                          |
|----------------------------------|---------------------------------------------|
| **High disk usage** (OOM errors, slow builds) | Unbounded container logs, unused images, dangling layers |
| **Resource starvation** (CPU/memory throttling) | Too many containers running, misconfigured limits |
| **Slow image pulls**            | Unoptimized image layers, corrupted cache |
| **Orphaned containers**         | Failed cleanup jobs, improper `docker prune` usage |
| **Kubernetes pod evictions**    | Disk pressure, memory pressure, node taints |
| **Build failures (CONTAINER ERROR)** | Corrupted build cache, misconfigured `.dockerignore` |

---

## **2. Common Issues & Fixes**

### **A. High Disk Usage (Container & Docker Storage Issues)**
#### **Symptom:**
- `docker system df` shows excessive space consumption.
- Slow container operations due to disk full errors.
- Builds failing with `disk space exhausted`.

#### **Debugging Steps:**
1. **Check disk usage breakdown**
   ```bash
   docker system df
   ```
   - Look for **dangling images**, **unused volumes**, and **large layers**.

2. **Identify unnecessary images**
   ```bash
   docker images --filter "dangling=true" --format "{{.Repository}}:{{.Tag}}"
   ```
   - Remove them:
     ```bash
     docker image prune -a
     ```

3. **Clean up unused containers, networks, and build cache**
   ```bash
   docker container prune -a
   docker network prune
   docker builder prune
   ```

4. **Adjust Docker storage driver** (if using `overlay2`):
   - Check current driver:
     ```bash
     docker info | grep "Storage Driver"
     ```
   - If storage is fragmented, consider switching to `devicemapper` (if supported) or increasing disk space.

---

### **B. Resource Starvation (CPU/Memory Throttling)**
#### **Symptom:**
- Containers getting throttled (`cgroup` limits in effect).
- Kubernetes pods crashing due to `OOMKilled` or `CPUThrottled`.
- Slower-than-expected performance.

#### **Debugging Steps:**
1. **Check running container resource usage**
   ```bash
   docker stats
   ```
   - Identify containers exceeding CPU/memory limits.

2. **Adjust resource limits (Docker)**
   ```bash
   docker run --cpus="0.5" --memory="512m" my-image
   ```
   - Or modify a running container (requires restart):
     ```bash
     docker update --cpus=0.5 --memory=512m <container_id>
     ```

3. **In Kubernetes, check pod resource requests/limits**
   ```yaml
   resources:
     requests:
       cpu: "500m"
       memory: "512Mi"
     limits:
       cpu: "1"
       memory: "1Gi"
   ```
   - Verify with:
     ```bash
     kubectl describe pod <pod_name>
     ```

4. **Check for no-limits containers** (`--memory=0` or `--cpus=-1`).
   - Use:
     ```bash
     docker inspect --format='{{json .HostConfig.Memory}}' <container_id>
     ```

---

### **C. Slow Image Pulls & Corrupted Layers**
#### **Symptom:**
- `Pulling image: 0%` hangs indefinitely.
- `Layer already exists` errors.
- `image corrupt` build failures.

#### **Debugging Steps:**
1. **Check layer integrity**
   ```bash
   docker verify-image <image_id>
   ```
   - If corrupt, rebuild the image.

2. **Clear Docker cache**
   ```bash
   docker builder prune
   ```

3. **Optimize Dockerfile layers**
   - Use multi-stage builds to reduce image size.
   - Example:
     ```dockerfile
     # Build stage
     FROM golang:1.21 as builder
     WORKDIR /app
     COPY . .
     RUN go build -o myapp

     # Final stage
     FROM alpine:latest
     COPY --from=builder /app/myapp /myapp
     CMD ["/myapp"]
     ```

4. **Increase Docker daemon memory**
   - Edit `/etc/docker/daemon.json`:
     ```json
     {
       "max-concurrent-downloads": 10,
       "max-concurrent-uploads": 5,
       "iostune": {
         "memsw-limit": "-1"
       }
     }
     ```
   - Restart Docker:
     ```bash
     sudo systemctl restart docker
     ```

---

### **D. Orphaned Containers & Failed Cleanups**
#### **Symptom:**
- `docker ps -a` shows many stopped containers.
- Kubernetes jobs/pods not auto-removing after completion.

#### **Debugging Steps:**
1. **List all stopped containers**
   ```bash
   docker ps -a --filter "status=exited"
   ```

2. **Remove them**
   ```bash
   docker container prune
   ```

3. **For Kubernetes, check `Job` finalizers**
   - If pods aren’t cleaning up:
     ```yaml
     spec:
       backoffLimit: 0  # Prevents retries that keep pods alive
     ```
   - Or use `TTLSecondsAfterFinished` in Kubernetes:
     ```yaml
     spec:
       ttlSecondsAfterFinished: 60
     ```

---

### **E. Kubernetes Pod Evictions Due to Disk Pressure**
#### **Symptom:**
- Pods getting killed with `Evicted` reason.
- Logs show `FailedScheduling` due to resource constraints.

#### **Debugging Steps:**
1. **Check disk pressure events**
   ```bash
   kubectl describe node <node_name> | grep -i -A 10 "events"
   ```

2. **Clean up unused volumes**
   - List volumes:
     ```bash
     kubectl get pv --all-namespaces
     ```
   - Delete unused PersistentVolumes (PV) and PersistentVolumeClaims (PVC).

3. **Adjust disk pressure thresholds**
   - In `/etc/kubernetes/manifests/kube-scheduler.yaml` (if using static pod):
     ```yaml
     evictionHard:
       diskPressure: "50%"
     ```

---

## **3. Debugging Tools & Techniques**

| **Tool**                | **Purpose**                                                                 | **Command/Usage**                                  |
|-------------------------|-----------------------------------------------------------------------------|----------------------------------------------------|
| `docker system df`      | Check disk usage breakdown                                                 | `docker system df`                                 |
| `kubectl top pods`      | Monitor pod resource usage in Kubernetes                                   | `kubectl top pods --all-namespaces`               |
| `crictl`                | Debug CRI (Container Runtime Interface) events in Kubernetes              | `crictl ps -a`                                    |
| `docker inspect`        | Deep dive into container metadata                                           | `docker inspect <container_id>`                   |
| `kubectl describe pod`  | Check pod events, resource limits, and conditions                          | `kubectl describe pod <pod_name> -n <namespace>` |
| `traceroute/tcpdump`    | Network debugging (if containers can’t communicate)                       | `tcpdump -i any host <ip>`                        |
| `docker stats`          | Real-time CPU/memory usage monitoring                                       | `docker stats --no-stream`                        |

---

## **4. Prevention Strategies**

### **A. Automate Container Cleanup**
- **Docker:**
  - Use `docker container prune`, `image prune` in CI/CD pipelines.
  - Schedule cleanup with `cron`:
    ```bash
    0 3 * * * docker system prune -a --force
    ```
- **Kubernetes:**
  - Use `Finalizers` and `TTLSecondsAfterFinished` for Jobs.
  - Implement `Garbage Collection` for old deployments.

### **B. Set Resource Limits Proactively**
- **Docker:**
  - Always specify `--memory` and `--cpus` in `docker run`.
- **Kubernetes:**
  - Enforce `resource requests` and `limits` in all Pod specs.

### **C. Optimize Dockerfile & Image Layers**
- **Best Practices:**
  - Use `.dockerignore` to exclude unnecessary files.
  - Leverage multi-stage builds.
  - Use `alpine`-based images where possible.

### **D. Monitor & Alert on Anomalies**
- **Tools:**
  - **Prometheus + Grafana** (for Docker/K8s metrics).
  - **Datadog/New Relic** (APM for container performance).
- **Alert Rules:**
  - Alert on `disk.usage > 80%`
  - Alert on `memory.usage > 90% of limit`

### **E. Use Container Runtime Health Checks**
- **Docker:**
  - Health checks in `Dockerfile`:
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/health || exit 1
    ```
- **Kubernetes:**
  - Define `livenessProbe` and `readinessProbe` in Pod specs.

---

## **5. Conclusion**
Container maintenance isn’t just about cleaning up—it’s about **proactively managing resources, optimizing images, and automating cleanup** to prevent outages. By following this guide, you can:

✅ **Diagnose disk, CPU, and memory issues quickly.**
✅ **Prevent orphaned containers and corrupted layers.**
✅ **Optimize Docker/Kubernetes performance.**
✅ **Set up monitoring to catch problems before they escalate.**

**Next Steps:**
- Audit your Docker/K8s environment with `docker system df` and `kubectl top pods`.
- Implement automated cleanup scripts in CI/CD.
- Set up resource limits for all containers.

**Need deeper debugging?** Use `kubectl logs`, `docker logs`, and `crictl` for container-specific insights. 🚀