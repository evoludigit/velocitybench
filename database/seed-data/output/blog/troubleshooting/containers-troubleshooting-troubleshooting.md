# **Debugging Containers: A Practical Troubleshooting Guide**

Containers are essential for modern cloud-native applications, providing isolation, portability, and scalability. Despite their advantages, issues like slow performance, crashes, network misconfigurations, or failed deployments can disrupt workflows. This guide provides a structured, actionable approach to diagnosing and resolving common container-related problems.

---

## **Symptom Checklist**
Before diving into debugging, identify which symptoms match your issue:

✅ **Application Crashes or Fails to Start**
   - Container exits immediately (`EXCODE=137`, `EXCODE=1`).
   - Logs show `segfault`, `panic`, or `command not found`.

✅ **Performance Issues (Slow Startup, High CPU/Memory Usage)**
   - Container takes excessively long to start.
   - High memory/CPU usage even under light load.

✅ **Networking Problems**
   - Containers cannot communicate with other services (`Connection refused`, `DNS lookup failure`).
   - External traffic cannot reach the container (`403 Forbidden`, `Connection timed out`).

✅ **Volume/Data Persistence Issues**
   - Data disappears after container restart.
   - Permission errors on mounted volumes.

✅ **Log-Related Issues**
   - No logs visible in `docker logs`.
   - Logs appear but are outdated or incomplete.

✅ **Resource Constraints (OOMKilled, CPU Throttling)**
   - Container gets killed with `OOMKilled` (Out of Memory).
   - CPU usage is capped but application is still slow.

✅ **Dependency/Dependency Hell Issues**
   - Missing runtime dependencies (e.g., missing libraries, incorrect `.dockerignore`).
   - Dockerfile build failures due to wrong commands.

✅ **Orchestration Issues (Kubernetes, Docker Swarm, Nomad)**
   - Pods stuck in `CrashLoopBackOff` or `Pending`.
   - Service discovery fails (`kube-dns` misconfiguration).

---

## **Common Issues & Fixes (With Code Examples)**

### **1. Container Fails to Start (Immediate Exit)**
**Symptoms:** Container exits with an exit code (`docker ps -a` shows `Exited`).
**Common Causes:**
- Missing dependencies in `Dockerfile`.
- Incorrect `CMD`/`ENTRYPOINT`.
- Permission issues inside the container.

#### **Debugging Steps:**
✔ **Check Exit Code & Logs**
```bash
docker logs <container_name>
docker inspect --format='{{.State.ExitCode}}' <container_name>
```
- `Exit Code 137` → OOMKilled (memory limit exceeded).
- `Exit Code 1` → Generic failure (check logs).

✔ **Recreate Container Interactively**
```bash
docker run -it --entrypoint /bin/sh <image>  # Debug shell access
```
- Manually verify commands inside the container.

#### **Fixes:**
✔ **Update `Dockerfile` for Missing Dependencies**
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl wget  # Example: Add missing libs
CMD ["your-command"]  # Ensure correct CMD
```

✔ **Use `docker-compose up --build`** to force rebuild.

---

### **2. Slow Startup Time**
**Symptoms:** Container takes >30s to start (`docker stats` shows high CPU on startup).
**Common Causes:**
- Large base images (e.g., `ubuntu` instead of `debian`).
- Overly complex `Dockerfile` layers.
- Slow initial database connections.

#### **Debugging Steps:**
✔ **Check `docker system df` for Layer Cache Issues**
```bash
docker system df  # Large unused layers may slow startup
```

✔ **Profile Build Time**
```bash
time docker build -t myapp .
```

#### **Fixes:**
✔ **Optimize `Dockerfile` (Multi-stage Builds)**
```dockerfile
# Stage 1: Build dependencies
FROM golang:1.21 as builder
WORKDIR /app
COPY . .
RUN go build -o /app/myapp

# Stage 2: Minimal runtime
FROM alpine:latest
COPY --from=builder /app/myapp /usr/local/bin/
CMD ["myapp"]
```

✔ **Use Smaller Base Images** (e.g., `alpine` instead of `ubuntu`).

---

### **3. Networking Issues (Can’t Connect to Other Services)**
**Symptoms:** `curl` fails, `Connection refused`, `DNS lookup failed`.
**Common Causes:**
- Incorrect `EXPOSE` in `Dockerfile`.
- Misconfigured `docker-compose` network.
- Firewall blocking ports (`--network=host` sometimes helps).

#### **Debugging Steps:**
✔ **Test Connectivity Inside Container**
```bash
docker exec -it <container> sh -c "ping google.com"  # Test DNS
docker exec -it <container> sh -c "curl http://internal-service:8080"
```

✔ **Check Ports**
```bash
docker port <container>  # Verify exposed ports
netstat -tuln | grep 8080  # Check host machine ports
```

#### **Fixes:**
✔ **Explicitly Define Ports in `Dockerfile` & `docker-compose`**
```dockerfile
EXPOSE 8080  # Not mandatory but recommended
```
```yaml
# docker-compose.yml
services:
  app:
    ports:
      - "8080:8080"
    networks:
      - mynet
networks:
  mynet:
```

✔ **Use `--network=host` for Quick Testing** (not for production):
```bash
docker run --network=host myapp
```

---

### **4. Volume/Data Persistence Issues**
**Symptoms:** Data lost after container restart, `Permission denied`.
**Common Causes:**
- Incorrect volume mounts (`/data` vs. `./data`).
- Wrong permissions in `Dockerfile`.

#### **Debugging Steps:**
✔ **Check Volume Mounts**
```bash
docker volume ls  # List volumes
docker inspect <container> | grep Mounts
```

✔ **Verify File Ownership Inside Container**
```bash
docker exec -it <container> ls -la /data
```

#### **Fixes:**
✔ **Set Correct Permissions in `Dockerfile`**
```dockerfile
RUN chown -R 1000:1000 /data  # Match host user
VOLUME ["/data"]  # Explicitly declare volume
```

✔ **Use Named Volumes (Persistent Storage)**
```yaml
# docker-compose.yml
volumes:
  app_data:
services:
  app:
    volumes:
      - app_data:/data
```

---

### **5. Logs Not Visible or Outdated**
**Symptoms:** `docker logs` shows nothing, or logs are truncated.
**Common Causes:**
- Log driver misconfiguration (`json-file` vs. `journald`).
- Container exited before logs were written.

#### **Debugging Steps:**
✔ **Check Log Driver**
```bash
docker inspect <container> | grep LogConfig
```

✔ **Enable Debug Logging Temporarily**
```bash
docker run --log-driver json-file --log-opt max-size=10m myapp
```

#### **Fixes:**
✔ **Use `docker-compose` Logging Configuration**
```yaml
# docker-compose.yml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

✔ **Tail Logs in Real-Time**
```bash
docker logs -f <container>
```

---

## **Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                  | **Example Usage**                          |
|------------------------|---------------------------------------------|--------------------------------------------|
| `docker inspect`       | Deep container metadata (network, logs, etc.) | `docker inspect <container>`              |
| `docker stats`         | Real-time resource monitoring               | `docker stats --no-stream`                |
| `docker events`        | Stream events (start/stop/crash)            | `docker events -f "container=<name>"`      |
| `docker exec`          | Run commands inside running containers      | `docker exec -it <container> sh`           |
| `strace` (Linux)       | Trace system calls (useful for crashes)     | `strace -f -p $(pgrep nginx)`              |
| `tcpdump`              | Capture network traffic                     | `docker exec <container> tcpdump -i eth0`  |
| `kubectl describe` (K8s)| Pod/Service debugging                        | `kubectl describe pod <pod-name>`          |
| `crictl` (K8s)         | Debug container runtime (CRI)               | `crictl ps`                                |
| `journalctl` (Logs)    | View systemd logs (if using `journald`)     | `journalctl -u docker.service`             |

---

### **Advanced Techniques:**
✔ **Use `docker debug` (for Kubernetes)**
```bash
kubectl debug -it <pod-name> --image=busybox --target=<container>
```

✔ **Attach Debuggers (e.g., `gdb`, `lldb`)**
```bash
docker exec -it <container> gdb /app/myapp
```

---

## **Prevention Strategies**

### **1. Best Practices for `Dockerfile`**
✔ **Use `.dockerignore` to Exclude Unnecessary Files**
```dockerfile
# .dockerignore
node_modules/
*.log
.DS_Store
```
✔ **Avoid Running as Root**
```dockerfile
RUN useradd -m myuser && \
    chown -R myuser /app && \
    USER=myuser
```
✔ **Use `.dockerignore` to Speed Up Builds**
```dockerfile
# .dockerignore
.git/
node_modules/
*.tmp
```

### **2. Optimize Container Runtime**
✔ **Set Resource Limits**
```bash
docker run --cpus=1 --memory=256m myapp
```
✔ **Use Read-Only Filesystems (Where Possible)**
```bash
docker run --read-only myapp
```

### **3. Monitoring & Alerting**
✔ **Integrate with Prometheus + Grafana**
```yaml
# Example Prometheus scrape config
- job_name: 'docker'
  docker_sd_configs:
    - host: unix:///var/run/docker.sock
  relabel_configs:
    - source_labels: [__meta_docker_container_name]
      target_label: container
```

✔ **Use Docker Events + Alertmanager**
```bash
docker events --filter 'event=die' | while read line; do
  echo "$(date) Container $line died" | mail -s "Docker Alert" admin@example.com
done
```

### **4. CI/CD Pipeline Checks**
✔ **Add Container Tests in CI**
```yaml
# .github/workflows/test.yml
steps:
  - run: docker build -t myapp .
  - run: docker run --rm myapp sh -c "your-test-command"
```

✔ **Use `hadolint` for `Dockerfile` Linting**
```bash
docker run --rm -i hadolint/hadolint < Dockerfile
```

---

## **Final Checklist for Quick Resolution**
| **Issue**               | **Quick Fix**                          | **Long-Term Solution**                  |
|-------------------------|----------------------------------------|-----------------------------------------|
| Container crashes       | Check `docker logs`, rebuild image     | Optimize `Dockerfile`, add health checks |
| Slow startup            | Use multi-stage builds                 | Profile app startup time                |
| Networking fails        | Test with `--network=host`             | Verify `EXPOSE` & firewall rules        |
| Data not persistent     | Use named volumes                      | Set correct permissions in Dockerfile   |
| No logs visible         | Check log driver (`json-file`)         | Configure `docker-compose` logging      |

---

### **Conclusion**
Containers simplify deployment but require careful debugging. By following this guide, you can:
✔ **Quickly identify** why containers fail.
✔ **Fix issues** with minimal downtime.
✔ **Prevent recurrences** with best practices.

For Kubernetes-specific issues, extend debugging with `kubectl describe`, `crictl`, and `journalctl`. Always test changes in a staging environment before production.