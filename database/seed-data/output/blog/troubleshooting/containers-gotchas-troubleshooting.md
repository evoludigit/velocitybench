# **Debugging Containers Gotchas: A Troubleshooting Guide**

Containers are powerful, but misconfigurations, permissions, networking, and runtime issues can lead to unexpected failures. This guide covers **common container pitfalls**, how to diagnose them, and actionable fixes.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| Symptom | Description |
|---------|-------------|
| **Container crashes or exits immediately** | `docker ps -a` shows `Exited (1)` or `Error`. |
| **Applications fail to start** | Logs show `Command not found`, `Permission denied`, or `Cannot connect to service`. |
| **Networking issues** | Containers can’t communicate (e.g., `Failed to connect to database`). |
| **Resource constraints** | OOM killer kills containers (`docker inspect <container> --format='{{.State.OOMKilled}}'`). |
| **Unexpected behavior in multi-container setups** | Services depend on each other but fail silently. |
| **Volume/mount issues** | Files disappear or are read-only after container restart. |
| **Image build errors** | `docker build` fails with unclear errors (e.g., missing layers, permission issues). |
| **Log corruption or missing logs** | `docker logs` returns empty or truncated output. |

---

## **2. Common Issues and Fixes**

### **A. Container Exits Immediately (Exit Code ≠ 0)**
#### **Symptom**
`docker ps -a` shows a container that ran briefly and exited with non-zero status.

#### **Debugging Steps**
1. **Inspect logs**:
   ```bash
   docker logs <container_id>
   ```
2. **Check exit code**:
   ```bash
   docker inspect <container_id> --format='{{.State.ExitCode}}'
   ```
3. **Run interactively for debugging**:
   ```bash
   docker run -it --entrypoint /bin/sh <image>  # Replace with your CMD/ENTRYPOINT
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **Missing CMD/ENTRYPOINT** | Ensure `Dockerfile` has `CMD ["your-command"]` or override in `docker run`. |
| **App crashes on startup** | Logs may show SQL errors, missing configs, or invalid ports. |
| **Signal termination (SIGKILL, SIGTERM)** | Check OOM killer logs (`dmesg | grep -i "killed process"`) and adjust `--memory` limits. |
| **Healthcheck failure** | Modify `HEALTHCHECK` in `Dockerfile` or `docker compose` to reduce frequency. |

**Example Fix (Missing CMD)**
```dockerfile
# Wrong: No CMD (process exits after init)
FROM alpine
RUN true  # Does nothing

# Correct: Explicit CMD
FROM alpine
CMD ["sh", "-c", "while true; do echo 'Running...'; sleep 5; done"]
```

---

### **B. Permission Denied (Filesystem Issues)**
#### **Symptom**
`Permission denied` when accessing files inside the container.

#### **Debugging Steps**
1. **Check file ownership inside container**:
   ```bash
   docker exec -it <container> ls -la /app
   ```
2. **Verify host mount permissions** (if using volumes):
   ```bash
   ls -ld /path/on/host
   ```
3. **Test write access**:
   ```bash
   touch /tmp/test  # Inside container
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **User mismatch between host and container** | Run as root (`USER root`) or set correct UID in `Dockerfile`. |
| **Volume bind mount lacks permissions** | Use `--user` flag or adjust host file permissions. |
| **Read-only filesystem** | Check `docker inspect <container> --format='{{.Mounts}}'` for `ReadOnly` mounts. |

**Example Fix (User Mismatch)**
```dockerfile
# Wrong: App runs as wrong user
FROM node:18
WORKDIR /app
COPY . .
RUN chown -R node:node /app
USER node  # Explicitly set user

# Correct: Ensure ownership matches
RUN chmod -R 755 /app  # Or use multi-stage builds
```

**Run as root (temporary debug)**:
```bash
docker run -u 0 <image>  # Force root inside container
```

---

### **C. Networking Failures (Can’t Connect Between Containers)**
#### **Symptom**
Services can’t communicate (e.g., `postgres` isn’t reachable from `app`).

#### **Debugging Steps**
1. **Check container IPs**:
   ```bash
   docker inspect <container> --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
   ```
2. **Test connectivity**:
   ```bash
   docker exec -it <app_container> ping <db_container_ip>
   docker exec -it <app_container> nc -zv db_container_ip 5432  # PostgreSQL default
   ```
3. **Inspect network**:
   ```bash
   docker network inspect <network_name>
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **Incorrect service name resolution** | Use `docker-compose` services (`db`) instead of IPs. |
| **Missing default gateway** | Ensure containers are on the same network. |
| **Firewall blocking ports** | Check host firewall (`ufw`, `iptables`, or cloud security groups). |
| **Port conflicts** | Ensure `EXPOSE` in `Dockerfile` matches `docker run -p`. |

**Example Fix (Netorking in Docker Compose)**
```yaml
# docker-compose.yml
version: "3.8"
services:
  web:
    image: nginx
    ports:
      - "80:80"
    depends_on:
      - db
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: example
```
**Access DB from `web` via `db` (service name), not IP.**

---

### **D. Resource Limits (OOM Killer)**
#### **Symptom**
Container killed by OOM killer (`docker inspect <container> --format='{{.State.OOMKilled}}'` returns `true`).

#### **Debugging Steps**
1. **Check memory usage**:
   ```bash
   docker stats <container>
   ```
2. **Review host logs**:
   ```bash
   dmesg | grep -i "killed process"
   ```
3. **Test with limits**:
   ```bash
   docker run --memory=512m --cpus=1 <image>
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **No memory limits** | Set `--memory` and `--cpus` in `docker run`. |
| **Leaky application** | Profile memory usage (e.g., `valgrind`, `heapdump`). |
| **Too many containers** | Reduce resource contention on the host. |

**Example Fix (Memory Limits)**
```bash
docker run --memory=1g --cpus=2 -d my-app
```
Or in `docker-compose.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "2"
```

---

### **E. Volume/Cache Issues (Data Disappears)**
#### **Symptom**
Files in volumes or `/tmp` disappear after container restart.

#### **Debugging Steps**
1. **Check volume mount type**:
   ```bash
   docker inspect <container> --format='{{.Mounts}}'
   ```
2. **Verify host directory**:
   ```bash
   ls -la /path/to/host/volume
   ```
3. **Test write persistence**:
   ```bash
   docker exec -it <container> touch /tmp/test
   docker exec -it <container> ls /tmp/test  # Should exist
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **Volumes mounted as read-only** | Check `ReadOnly` flag in `docker inspect`. |
| **Host directory permissions** | Ensure host has write access (`chmod -R 777 /path/to/volume`). |
| **Anonymous volumes** | Use named volumes for persistence. |

**Example Fix (Named Volume)**
```bash
docker volume create my_volume
docker run -v my_volume:/app/data my-image
```

---

### **F. Image Build Failures**
#### **Symptom**
`docker build` fails with cryptic errors (e.g., "no such file," "permission denied").

#### **Debugging Steps**
1. **Check layer-by-layer logs**:
   ```bash
   docker build --progress=plain -t my-image .
   ```
2. **Test individual `RUN` commands**:
   ```bash
   docker run --rm -it alpine sh -c "apt-get update && apt-get install -y curl"
   ```
3. **Verify file paths**:
   ```bash
   ls -R .  # Check if files exist locally
   ```

#### **Common Causes & Fixes**
| Issue | Fix |
|-------|-----|
| **Path resolution in `COPY`** | Use absolute paths in `Dockerfile`. |
| **Missing dependencies** | Install build tools (`gcc`, `make`) in first layer. |
| **Permission issues** | Run as root during build (`USER root` in `Dockerfile`). |

**Example Fix (Absolute Paths)**
```dockerfile
# Wrong: Relative path fails if build context changes
COPY ./config /app/config

# Correct: Absolute path
COPY /build/context/config /app/config
```

---

## **3. Debugging Tools and Techniques**

| Tool | Usage | Example |
|------|-------|---------|
| **`docker logs`** | View container logs. | `docker logs -f <container>` |
| **`docker exec`** | Run commands inside a running container. | `docker exec -it <container> bash` |
| **`docker inspect`** | Debug container/config details. | `docker inspect <container> --format='{{.NetworkSettings.IPAddress}}'` |
| **`docker stats`** | Monitor resource usage. | `docker stats --no-stream` |
| **`strace`** | Trace system calls (inside container). | `docker exec -it <container> strace -e trace=file -p 1` |
| **`tcpdump`** | Capture network traffic. | `docker run --net=host -it alpine tcpdump -i eth0 -w /tmp/pcap` |
| **`crictl`** | Debug Kubernetes/CRI-O containers. | `crictl ps -a` |
| **`journalctl`** | Check host systemd logs. | `journalctl -u docker` |

**Advanced Debugging:**
- **Remote Debugging**: Attach VS Code debug adapter to container (`VS Code Remote Containers`).
- **Core Dumps**: Enable for crashes (`ulimit -c unlimited` in `ENTRYPOINT`).
- **Network Debugging**: Use `docker network create --internal` for isolated testing.

---

## **4. Prevention Strategies**

### **A. Best Practices for Dockerfiles**
1. **Minimize layers**: Combine `RUN` commands to reduce image size.
   ```dockerfile
   # Bad: 5 layers
   RUN apt-get update && \
       apt-get install -y curl && \
       rm -rf /var/lib/apt/lists/*

   # Good: 1 layer
   RUN apt-get update && \
       apt-get install -y curl && \
       apt-get clean && \
       rm -rf /var/lib/apt/lists/*
   ```
2. **Use `.dockerignore`**: Exclude unnecessary files.
   ```text
   # .dockerignore
   node_modules/
   *.log
   ```
3. **Multi-stage builds**: Reduce final image size.
   ```dockerfile
   # Stage 1: Build
   FROM node:18 as builder
   WORKDIR /app
   COPY . .
   RUN npm install && npm run build

   # Stage 2: Runtime
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   ```

### **B. Runtime Safeguards**
1. **Set resource limits**:
   ```bash
   docker run --memory=512m --cpus=1 my-app
   ```
2. **Use healthchecks**:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=3s \
     CMD curl -f http://localhost:8080/health || exit 1
   ```
3. **Monitor containers**:
   - Use `docker events` for real-time alerts.
   - Integrate with Prometheus/Grafana for metrics.

### **C. Networking Hardening**
1. **Isolate networks**:
   ```yaml
   # docker-compose.yml
   services:
     app:
       networks:
         - internal_net
   networks:
     internal_net:
       internal: true
   ```
2. **Use service discovery** (Docker Compose, Linkerd, Istio).
3. **Restrict host access**: Avoid `--net=host` unless necessary.

### **D. Storage Best Practices**
1. **Prefer named volumes** over bind mounts for persistence.
2. **Chown volumes** to match container user:
   ```bash
   docker run -v /host/path:/container/path:Z my-image
   ```
3. **Test volume lifecycle**:
   - Does data persist after `docker rm -v`?
   - Does it survive host reboot?

---

## **5. Summary Checklist for Quick Resolution**
| **Issue** | **Quick Fix** | **Prevention** |
|-----------|--------------|----------------|
| Container exits | Check `docker logs` + `CMD/ENTRYPOINT` | Ensure `CMD` exists |
| Permission denied | Run as root (`-u 0`) or fix ownership | Use `USER` in `Dockerfile` |
| Networking fails | Ping service names (not IPs) | Use Docker Compose networks |
| OOM killed | Reduce `--memory` or optimize app | Set limits in `docker run` |
| Data lost | Use named volumes (`docker volume`) | Prefer volumes over bind mounts |
| Build fails | Debug layer-by-layer | Use `.dockerignore` |

---

## **Final Notes**
- **Start small**: Isolate issues by testing one container at a time.
- **Reproduce locally**: Avoid "works on my machine" problems.
- **Leverage CI/CD**: Automate testing with `docker-compose up --abort-on-container-exit`.

By following this guide, you can quickly diagnose and resolve **90% of container gotchas**. For persistent issues, refer to:
- [Docker Debugging Cheat Sheet](https://github.com/veggiemonk/bash-snippets/blob/master/docker-debugging-cheat-sheet.md)
- [Container Debugging with `strace`](https://www.brendangregg.com/blog/2017-08-08/debugging-containerized-applications-with-strace.html)