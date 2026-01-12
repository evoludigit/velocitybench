# **Debugging "Containers Best Practices": A Troubleshooting Guide**

Containers (Docker, Kubernetes, etc.) are widely adopted for their portability, scalability, and consistency. However, misconfigurations, resource constraints, and architectural flaws can lead to unexpected behavior. This guide focuses on **quick resolution** of common container-related issues while adhering to best practices.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically verify the following symptoms:

| **Symptom**                          | **Possible Causes**                          |
|--------------------------------------|---------------------------------------------|
| Containers fail to start             | Missing dependencies, wrong permissions, resource limits |
| Slow application performance        | Insufficient CPU/memory, inefficient image layers |
| Unexpected crashes or OOM (Out-of-Memory) | High memory usage, improper garbage collection |
| Network connectivity issues          | Misconfigured DNS, firewall rules, or incorrect network mode |
| Logs show "Failed to pull image"    | Corrupted image, registry authentication issues |
| Unpredictable pod scheduling issues | Resource requests/limits not set, taints/tolerations misconfigured |
| Persistent data corruption          | Improper volume mounts, incorrect storage class |
| Security vulnerabilities            | Missing `non-root` user, outdated base images |

---

## **2. Common Issues & Fixes**

### **2.1 Containers Fail to Start**
#### **Symptom:**
`docker ps` shows `Exited (137)` (OOM kill) or `docker logs <container>` shows missing dependencies.

#### **Root Cause:**
- Missing environment variables, incorrect entrypoint, or missing runtime dependencies.
- Running as `root` without `USER` directive.

#### **Fix:**
✅ **Set a non-root user in Dockerfile:**
```dockerfile
RUN useradd -m myuser && chown -R myuser /app
USER myuser
```
✅ **Ensure required environment variables:**
```bash
docker run -e DB_HOST=postgres -e DB_USER=admin myapp
```
✅ **Check `ENTRYPOINT`/`CMD` in Dockerfile:**
```dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--config", "/app/config.json"]
```

#### **Debugging Steps:**
1. Run interactively:
   ```bash
   docker run -it --entrypoint /bin/sh myimage
   ```
2. Test entrypoint manually.

---

### **2.2 High Memory Usage (OOM)**
#### **Symptom:**
Container crashes with `OOMKilled` and logs indicate memory spikes.

#### **Root Cause:**
- Improper memory limits (`--memory` in Docker, `resources.limits` in K8s).
- Memory leaks in application code.
- Too many cached layers in Docker.

#### **Fix:**
✅ **Set memory limits in Docker:**
```bash
docker run --memory=512m --memory-swap=1g myapp
```
✅ **In Kubernetes:**
```yaml
resources:
  limits:
    memory: "512Mi"
  requests:
    memory: "256Mi"
```
✅ **Check for memory leaks (Python example):**
```python
import tracemalloc
tracemalloc.start()
# Run app, then check:
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:5]:
    print(stat)
```

#### **Debugging Steps:**
1. Monitor memory usage:
   ```bash
   docker stats <container>
   ```
2. Use `docker events` to track OOM kills:
   ```bash
   docker events --filter 'event=oom' --format '{{.Actor.Attributes.name}}'
   ```
3. Check for large temporary files (`/tmp`, cache directories).

---

### **2.3 Network Connectivity Issues**
#### **Symptom:**
Container cannot reach external services (DB, API endpoints).

#### **Root Cause:**
- Incorrect `network_mode` (host/bridge/overlay).
- Missing `dns` configuration in Docker.
- Firewall blocking ports.

#### **Fix:**
✅ **Set DNS in Docker:**
```bash
docker run --dns 8.8.8.8 --dns 1.1.1.1 myapp
```
✅ **Use a custom network (Docker):**
```bash
docker network create mynet
docker run --network mynet myapp
```
✅ **Kubernetes Service Exposure:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: myapp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
```

#### **Debugging Steps:**
1. Test connectivity from inside the container:
   ```bash
   docker exec -it mycontainer ping google.com
   ```
2. Check `resolv.conf` inside the container:
   ```bash
   docker exec mycontainer cat /etc/resolv.conf
   ```
3. Verify network in Docker:
   ```bash
   docker network inspect mynet
   ```

---

### **2.4 Slow Image Pulls**
#### **Symptom:**
`Failed to pull image: rpc error: code = Unavailable desc = connect: no route to host`.

#### **Root Cause:**
- Private registry authentication failure.
- Large image layers causing timeouts.

#### **Fix:**
✅ **Authenticate with private registry:**
```bash
docker login myregistry.com -u user -p pass
```
✅ **Use `.dockerconfigjson` in Kubernetes:**
```yaml
imagePullSecrets:
- name: regcred
```
✅ **Optimize images:**
- Use `multi-stage builds` to reduce size.
- Example:
  ```dockerfile
  # Build stage
  FROM gcc AS builder
  RUN apt-get install -y gcc && \
      gcc -o myapp myapp.c

  # Final stage
  FROM alpine
  COPY --from=builder /myapp /myapp
  CMD ["/myapp"]
  ```

#### **Debugging Steps:**
1. Test image pull manually:
   ```bash
   docker pull myregistry.com/myimage:latest
   ```
2. Check registry logs for errors.
3. Use `docker history <image>` to identify large layers.

---

### **2.5 Persistent Data Loss**
#### **Symptom:**
Data in `/var/lib/docker/volumes` is not retained after container restart.

#### **Root Cause:**
- Using `docker run -v` incorrectly (bind mounts instead of named volumes).
- Volume not persisted across container restarts.

#### **Fix:**
✅ **Use named volumes (recommended):**
```bash
docker volume create myvolume
docker run -v myvolume:/data myapp
```
✅ **Kubernetes PersistentVolume:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

#### **Debugging Steps:**
1. List volumes:
   ```bash
   docker volume ls
   ```
2. Inspect volume mounts:
   ```bash
   docker inspect <container> | grep Mounts
   ```
3. Check PVC status in Kubernetes:
   ```bash
   kubectl get pvc
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `docker logs`          | View container logs                                                        | `docker logs -f mycontainer`                |
| `kubectl describe pod` | Troubleshoot Kubernetes pod events                                         | `kubectl describe pod my-pod`               |
| `docker stats`         | Monitor resource usage                                                    | `docker stats --no-stream mycontainer`      |
| `strace`               | Debug system calls in running processes                                   | `docker exec -it mycontainer strace -p 1`    |
| `netstat`              | Check network connections inside container                                | `docker exec mycontainer netstat -tuln`     |
| `dive`                 | Analyze Docker image layers (optimization)                                | `dive myimage`                              |
| `skopeo`               | Inspect container images                                                    | `skopeo inspect docker://myimage:latest`     |
| `kubectl exec -it`     | Debug inside a running pod                                                 | `kubectl exec -it my-pod -c my-container -- /bin/sh` |
| `crictl`               | Kubernetes runtime debugging (CRI-compliant)                                | `crictl ps`                                 |

**Pro Tip:**
- Use `docker-compose` for local debugging:
  ```bash
  docker-compose up --build
  ```
- Enable `--log-driver=json-file` in Docker for structured logs.

---

## **4. Prevention Strategies**

### **4.1 Dockerfile Best Practices**
✔ **Multi-stage builds** (reduce image size).
✔ **Use `.dockerignore`** to exclude unnecessary files.
✔ **Pin versions** of base images (`FROM python:3.9-slim`).
✔ **Avoid running as root** (use `USER` directive).

### **4.2 Kubernetes Best Practices**
✔ **Set `requests` and `limits`** for CPU/memory.
✔ **Use Resource Quotas** (`kubectl create quota`).
✔ **Use Readiness/Liveness Probes**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
  ```
✔ **Enable Pod Disruption Budgets (PDB)** for high availability.

### **4.3 Security Hardening**
✔ **Scan images for vulnerabilities** (`docker scan` or Trivy).
✔ **Use `docker scan` for security checks**:
  ```bash
  docker scan myimage
  ```
✔ **Enable read-only root filesystem**:
  ```yaml
  securityContext:
    readOnlyRootFilesystem: true
  ```
✔ **Regularly update base images**.

### **4.4 Logging & Monitoring**
✔ **Centralized logging** (ELK Stack, Loki, or Promtail).
✔ **Set up Prometheus + Grafana** for metrics.
✔ **Use Kubernetes Events** for incident tracking:
  ```bash
  kubectl get events --sort-by='.metadata.creationTimestamp'
  ```

### **4.5 CI/CD Best Practices**
✔ **Test images in CI pipeline** (e.g., Docker BuildKit).
✔ **Use `docker-compose` for integration tests**.
✔ **Automate vulnerability scans** in CI (e.g., `trivy`).

---

## **5. Quick Reference Checklist**
| **Issue**               | **First Check**                     | **Next Steps**                          |
|-------------------------|-------------------------------------|-----------------------------------------|
| Container fails to start | `docker logs`                       | Check `ENTRYPOINT`, dependencies, `USER` |
| High memory usage       | `docker stats`                      | Set memory limits, check for leaks      |
| Network issues          | `ping` from container               | Verify `dns`, firewall, network mode    |
| Slow image pulls        | `docker pull --debug`               | Check auth, registry connection         |
| Data loss               | `docker volume inspect`             | Use named volumes, check PVCs           |

---

## **Final Notes**
- **Start small:** Isolate the issue (one container, then scale).
- **Use `docker events` and `kubectl`** for observability.
- **Automate debugging:** Script common checks (e.g., a `debug.sh` script).
- **Stay updated:** Follow Docker/Kubernetes best practices ([Docker docs](https://docs.docker.com/), [K8s Best Practices](https://kubernetes.io/docs/concepts/overview/#best-practices)).

By following this guide, you should be able to **quickly identify and resolve** 90% of container-related issues while maintaining best practices. 🚀