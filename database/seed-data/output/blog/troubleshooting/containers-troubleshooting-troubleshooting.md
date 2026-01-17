# **Debugging Containers: A Troubleshooting Guide**

## **Introduction**
Containers (Docker, Kubernetes, or other container runtimes) are a core part of modern cloud-native and microservices architectures. While they improve portability, scalability, and resource efficiency, containerized applications often face issues stemming from misconfigurations, networking problems, storage errors, or runtime failures.

This guide provides a structured approach to diagnosing and resolving common container-related problems efficiently.

---

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms match your issue:

| **Category**               | **Symptom**                                                                 |
|----------------------------|----------------------------------------------------------------------------|
| **Container Failures**     | Container fails to start (`Error: Failed to start container`, `Exited (X)`) |
| **Networking Issues**      | Containers cannot communicate (`Connection refused`, `DNS resolution failures`) |
| **Storage Errors**         | Volumes not mounted (`No such file or directory`), disk space errors      |
| **Resource Constraints**   | CPU/Memory throttling, OOM kills                                         |
| **Image Issues**           | Corrupted layers (`Cannot connect to the Docker daemon`), missing dependencies |
| **Orchestration Failures** | Pods stuck in `Pending/Error`, node issues in Kubernetes                   |
| **Security Problems**      | Permission denied (`Permission denied: "xxx" in user "xxx" context`), SECURITY alerts |

**Action:** Pick the most relevant symptom(s) and move to the corresponding section.

---

---

## **2. Common Issues and Fixes**

### **2.1 Container Won’t Start**
**Symptoms:**
- Container exits immediately (`Exited (0)` or non-zero code).
- Logs show errors like `command not found`, `permission denied`, or missing files.

**Possible Causes & Fixes:**
1. **Incorrect Command in `docker run`**
   - Ensure the command in the Dockerfile or `docker run` is correct.
   - Example fix:
     ```dockerfile
     # Dockerfile - Ensure CMD is properly set
     CMD ["app", "--port=8080"]
     ```
     ```bash
     # Run command (use array syntax for proper argument passing)
     docker run -d my-image ["app", "--port=8080"]
     ```

2. **Missing Dependencies**
   - If the image lacks required libraries (e.g., `libc6` on Alpine-based images), install them:
     ```dockerfile
     RUN apk add --no-cache libc6-compat  # Example for Alpine
     ```

3. **Wrong Working Directory or File Permissions**
   - Ensure files are copied correctly and have the right permissions:
     ```dockerfile
     WORKDIR /app
     COPY ./src ./src
     RUN chmod -R 755 ./src  # Fix permissions
     ```

4. **Healthcheck Failures**
   - If a container starts but fails health checks, adjust them:
     ```dockerfile
     HEALTHCHECK --interval=30s --timeout=3s \
       CMD curl -f http://localhost:8080/health || exit 1
     ```

**Debugging Tip:**
- Use `docker logs <container_id>` to inspect startup errors.
- Check exit codes with `docker inspect <container_id> --format='{{.State.ExitCode}}'`.

---

### **2.2 Networking Issues: Containers Can’t Communicate**
**Symptoms:**
- `curl 127.0.0.1:8080` fails inside a container.
- Services fail to reach each other (`Connection refused`).

**Common Causes & Fixes:**
1. **Incorrect `network_mode` in Docker**
   - Default `bridge` network may isolate containers. Use `host` or a custom network:
     ```bash
     docker network create my-net
     docker run --network my-net my-app
     ```

2. **Missing Exposed Ports**
   - Ensure ports are published and services are bound correctly:
     ```dockerfile
     EXPOSE 8080  # Declared in Dockerfile (optional but recommended)
     ```
     ```bash
     docker run -p 8080:8080 my-app  # Map host:container
     ```

3. **Firewall or Security Group Blocking Traffic**
   - Check host firewalls (`sudo ufw status`) and cloud security groups.

4. **DNS Resolution Failures in Kubernetes**
   - Verify Kubernetes Service definitions:
     ```yaml
     # Correct Service YAML (ClusterIP for internal access)
     apiVersion: v1
     kind: Service
     metadata:
       name: my-service
     spec:
       selector:
         app: my-app
       ports:
         - protocol: TCP
           port: 80
           targetPort: 8080
     ```

**Debugging Tip:**
- Test connectivity manually:
  ```bash
  docker exec -it my-container ping google.com  # Check DNS
  docker exec -it my-container curl localhost:8080 # Test local service
  ```
- For Kubernetes, use `kubectl get events` or `kubectl logs <pod>`.

---

### **2.3 Volume Not Mounted**
**Symptoms:**
- Files disappear after container restarts.
- `ls /mnt/data` returns `No such file or directory`.

**Common Causes & Fixes:**
1. **Incorrect Volume Path**
   - Verify the host path exists and is writable:
     ```bash
     mkdir -p /host/path/to/volume
     chmod 777 /host/path/to/volume  # Temporarily for testing
     ```

2. **Permission Denied**
   - Ensure the container user has access:
     ```dockerfile
     RUN chown -R 1000:1000 /mnt/data  # Matches user in container
     ```

3. **Kubernetes PersistentVolumeClaim (PVC) Issues**
   - Check PVC status:
     ```bash
     kubectl get pvc
     kubectl describe pvc <name>
     ```
   - Ensure the StorageClass is provisioned correctly.

**Debugging Tip:**
- Test manually:
  ```bash
  docker run -v /host/path:/container/path my-image ls /container/path
  ```

---

### **2.4 Resource Constraints (CPU/Memory)**
**Symptoms:**
- Container OOM-killed (`Out of memory: Kill process`).
- Slow performance due to CPU throttling.

**Common Causes & Fixes:**
1. **Missing Resource Limits in Docker**
   - Set CPU/Memory limits:
     ```bash
     docker run --cpus=1 --memory=512m my-image
     ```

2. **Kubernetes Resource Requests/Limits**
   - Define `resources` in a Deployment:
     ```yaml
     resources:
       requests:
         cpu: "500m"
         memory: "512Mi"
       limits:
         cpu: "1"
         memory: "1Gi"
     ```

3. **Monitor with `docker stats` or `kubectl top`**
   - Check usage:
     ```bash
     docker stats --no-stream
     kubectl top pods
     ```

**Debugging Tip:**
- Use `crictl ps` (for Kubernetes) to inspect container resource usage.

---

### **2.5 Image Corruption or Layer Issues**
**Symptoms:**
- `Cannot connect to the Docker daemon`.
- `image not found` after rebuilding.

**Common Causes & Fixes:**
1. **Corrupted Docker Image Layers**
   - Rebuild and push fresh images:
     ```bash
     docker build -t my-image:latest .
     docker push my-image:latest
     ```

2. **Docker Daemon Not Running**
   - Restart Docker:
     ```bash
     sudo systemctl restart docker
     ```

3. **Registry Issues**
   - Check `docker pull` and credentials:
     ```bash
     docker login
     docker pull my-image:latest
     ```

**Debugging Tip:**
- Check disk space (`docker system df`) and clean unused data:
  ```bash
  docker system prune -a
  ```

---

### **2.6 Kubernetes Pods Stuck in `Pending` or `Error`**
**Symptoms:**
- Pods never start (`Pending` forever).
- `Error` state with no clear logs.

**Common Causes & Fixes:**
1. **Insufficient Resources**
   - Check cluster capacity:
     ```bash
     kubectl describe nodes
     ```

2. **Missing Node Selectors or Taints**
   - Ensure pods match node labels:
     ```yaml
     affinity:
       nodeAffinity:
         requiredDuringSchedulingIgnoredDuringExecution:
           nodeSelectorTerms:
           - matchExpressions:
             - key: "kubernetes.io/arch"
               operator: In
               values: ["amd64"]
     ```

3. **ImagePullBackOff**
   - Verify image name and permissions:
     ```yaml
     spec:
       containers:
       - name: my-app
         image: my-registry/my-image:latest  # Check registry access
     ```

**Debugging Tip:**
- Describe the pod for details:
  ```bash
  kubectl describe pod <pod-name>
  kubectl logs <pod-name> --previous  # Check previous logs
  ```

---

### **2.7 Security Issues (Permission Denied)**
**Symptoms:**
- `Permission denied: "permission denied"` in logs.
- `Failed to start service: user not found`.

**Common Causes & Fixes:**
1. **Incorrect User in Dockerfile**
   - Set a non-root user:
     ```dockerfile
     RUN useradd -m myuser
     USER myuser
     ```

2. **Volume Permission Mismatch**
   - Ensure host and container permissions align:
     ```bash
     chown -R 1000:1000 /host/path  # Match user in container
     ```

3. **SELinux/AppArmor Issues**
   - Temporarily disable for testing:
     ```bash
     sudo setenforce 0  # Disable SELinux (use cautiously)
     ```

**Debugging Tip:**
- Check user/group IDs:
  ```bash
  docker run -it my-image id  # Verify user exists
  ```

---

---

## **3. Debugging Tools and Techniques**

### **3.1 Docker-Specific Tools**
| **Tool**               | **Use Case**                                                                 |
|------------------------|------------------------------------------------------------------------------|
| `docker logs`          | View container logs.                                                       |
| `docker inspect`       | Deep inspect container/config (JSON output).                              |
| `docker exec -it`      | Run interactive commands inside a container.                               |
| `docker stats`         | Monitor resource usage in real-time.                                       |
| `docker system df`     | Check disk usage and clean up.                                             |
| `dive` (CLI tool)      | Analyze Docker image layers for bloat.                                      |

**Example:**
```bash
# Inspect a container's network setup
docker inspect --format='{{json .NetworkSettings}}' <container>

# Run a shell in a running container
docker exec -it my-container /bin/bash
```

---

### **3.2 Kubernetes Debugging Tools**
| **Tool**               | **Use Case**                                                                 |
|------------------------|------------------------------------------------------------------------------|
| `kubectl logs`         | View pod logs.                                                             |
| `kubectl describe`     | Debug pod, service, or deployment issues.                                  |
| `kubectl exec`         | Run commands inside a pod.                                                 |
| `kubectl top`          | Check CPU/memory usage.                                                    |
| `stern` (CLI tool)     | Stream logs for multiple pods.                                             |
| `kubectl debug`        | Create a debug pod from an existing container.                             |

**Example:**
```bash
# Stream logs for a pod
stern my-pod

# Debug a failed pod by creating a temporary container
kubectl debug -it <pod> --image=busybox --target=<container>
```

---

### **3.3 Logging and Monitoring**
- **Centralized Logging:**
  - Use **Fluentd + Elasticsearch + Kibana (EFK)** or **Loki + Grafana** for Docker/K8s logs.
- **Distributed Tracing:**
  - **Jaeger** or **Zipkin** for latency analysis in microservices.
- **Metrics:**
  - **Prometheus + Grafana** for monitoring container metrics.

**Example Prometheus Query:**
```promql
# Check container CPU usage
container_cpu_usage_seconds_total
```

---

### **3.4 Network Diagnostics**
| **Command**                     | **Purpose**                                                                 |
|----------------------------------|------------------------------------------------------------------------------|
| `docker network inspect`         | Check network configuration.                                                |
| `kubectl get events`             | View cluster events (K8s).                                                  |
| `nc -zv <ip>:<port>`             | Test TCP connectivity.                                                       |
| `traceroute <hostname>`          | Trace network path.                                                          |
| `kubectl port-forward`           | Forward local ports to a pod.                                               |

**Example:**
```bash
# Forward a pod's port to localhost
kubectl port-forward pod/my-pod 8080:8080
```

---

---

## **4. Prevention Strategies**

### **4.1 Best Practices for Docker/Kubernetes**
1. **Use `.dockerignore`**
   - Exclude unnecessary files to reduce image size:
     ```
     # .dockerignore
     node_modules/
     *.log
     ```

2. **Multi-Stage Builds**
   - Reduce final image size:
     ```dockerfile
     FROM alpine as builder
     RUN apk add --no-cache gcc
     FROM alpine
     COPY --from=builder /app /app
     ```

3. **Health Checks**
   - Implement `HEALTHCHECK` in Dockerfiles and `livenessProbe` in Kubernetes.

4. **Resource Limits**
   - Always set CPU/memory limits in production:
     ```bash
     docker run --cpus=0.5 --memory=256m my-app
     ```

5. **Image Scanning**
   - Scan for vulnerabilities using **Trivy** or **Clair**:
     ```bash
     trivy image my-image:latest
     ```

6. **Infrastructure as Code (IaC)**
   - Use **Docker Compose** or **Kubernetes manifests** (GitOps) for reproducibility.

### **4.2 Monitoring and Alerting**
- **Alert on Container Failures:**
  - Set up alerts for container crashes (`container_failed_to_start_total` in Prometheus).
- **Log Retention Policies:**
  - Use tools like **Loki** to retain logs for a limited time.
- **Automated Rollbacks:**
  - Use Kubernetes **Rollback** or Docker **restart policies**:
    ```yaml
    # Kubernetes Rollback
    kubectl rollout undo deployment/my-app
    ```

### **4.3 Security Hardening**
- **Non-Root Users:**
  - Always run containers as non-root in production.
- **Secrets Management:**
  - Use Kubernetes **Secrets** or **Vault** (not plaintext in Dockerfiles).
- **Network Policies:**
  - Restrict pod-to-pod communication:
    ```yaml
    apiVersion: networking.k8s.io/v1
    kind: NetworkPolicy
    metadata:
      name: deny-all-except-frontend
    spec:
      podSelector: {}
      policyTypes:
      - Ingress
      ingress:
      - from:
        - podSelector:
            matchLabels:
              app: frontend
    ```

### **4.4 Backup and Disaster Recovery**
- **Regular Image Backups:**
  - Tag and archive images in a registry.
- **Volume Snapshots:**
  - Use **Velero** for Kubernetes PersistentVolume backups.
- **Chaos Engineering:**
  - Simulate failures with **Chaos Mesh** or **Gremlin** to test resilience.

---

---

## **5. Quick Reference Cheat Sheet**
| **Issue**                     | **Quick Fix**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|
| Container won’t start         | `docker logs <id>` + check `CMD` in Dockerfile.                            |
| Network connectivity issues   | `docker network inspect` + check `EXPOSE`/`ports`.                          |
| Volume not mounted            | Verify host path exists and permissions match (`chown`).                     |
| OOM killed                    | Set `--memory` limit (`docker run --memory=512m`).                          |
| Image pull error              | Check registry credentials (`docker login`).                                 |
| Kubernetes pod stuck          | `kubectl describe pod` + check resources/events.                            |
| Permission denied             | Use non-root user (`USER` in Dockerfile).                                   |
| Slow performance              | Enable CPU limits (`--cpus=1`).                                              |

---

## **Conclusion**
Containers simplify deployment but introduce complexity. By following this guide, you can:
1. **Quickly diagnose** issues using logs, `inspect`, and `describe`.
2. **Fix common problems** with targeted fixes (networking, permissions, resources).
3. **Prevent future issues** with best practices (multi-stage builds, resource limits, health checks).
4. **Monitor and secure** your environment proactively.

**Final Tip:** Start with the **symptom checklist**, then narrow down using **logs and tooling**. For Kubernetes, always check `kubectl describe` first. For Docker, inspect the container’s config and logs.

---
**Further Reading:**
- [Docker Troubleshooting Guide](https://docs.docker.com/troubleshoot/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)