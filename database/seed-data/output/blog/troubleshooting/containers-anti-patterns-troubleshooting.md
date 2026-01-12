# **Debugging Containers Anti-Patterns: A Troubleshooting Guide**

## **Introduction**
Containers are a powerful abstraction for packaging and deploying applications, but improper implementation can lead to systemic failures, performance bottlenecks, and operational inefficiencies. This guide addresses **common container anti-patterns**—misuse of containerization that can cause instability, resource starvation, security risks, and debugging headaches.

---

## **Symptom Checklist**
Before diving into fixes, verify if your system exhibits these symptoms:

| **Category**            | **Symptoms**                                                                 | **Possible Root Cause**                          |
|-------------------------|------------------------------------------------------------------------------|--------------------------------------------------|
| **Resource Starvation** | Containers frequently crash with `OutOfMemory` or `DiskSpace` errors.        | Poor resource limits, unbounded processes.       |
| **Network Issues**      | `Connection refused`, `Timeout`, or `Permission denied` when communicating between containers. | Incorrect port mappings, misconfigured DNS, or firewall rules. |
| **Performance Degradation** | Slow response times, high CPU/memory usage in containers.                      | Over-provisioned containers, inefficient I/O.    |
| **Unpredictable Behavior** | Containers fail randomly, even with identical configurations.               | Race conditions, hardcoded paths, missing secrets. |
| **Security Vulnerabilities** | Unauthorized access, exposed host ports, or unnecessary privileges.         | Over-privileged containers, misconfigured `docker run -v`. |
| **Orphaned Containers**  | Leftover containers, dangling images, or unused volumes cluttering storage. | Lack of garbage collection, improper cleanup scripts. |
| **Dependency Hell**      | Containers fail to start due to missing dependencies (e.g., libraries, config files). | Incorrect layers in Docker images, missing `.dockerignore`. |
| **Logging & Debugging Nightmares** | Hard time isolating logs, tracing requests, or debugging distributed systems. | Poor logging practices, no structured logging. |

If multiple symptoms exist, cross-reference with **Common Issues and Fixes** below.

---

## **Common Issues & Fixes (With Code Examples)**

### **1. Resource Starvation (CPU/Memory/Disk)**
**Symptoms:**
- `OOMKilled` (Out-of-Memory) errors.
- Containers crash with `disk quota exceeded`.
- High CPU usage with no visible workload.

**Root Causes:**
- No CPU/memory limits (`-c` or `--memory` flags).
- Unbounded processes (e.g., infinite loops, leaking memory).
- Large volumes mounted inside containers (e.g., `/var/log`).

#### **Fixes:**
#### **A. Set Resource Limits in `docker run` or `docker-compose`**
```bash
# Limit CPU to 1 core and memory to 512MB
docker run --cpus=1 --memory=512m my-image

# In docker-compose.yml
services:
  my-service:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

#### **B. Use `--memory-swap` to Prevent Swap Thrashing**
```bash
docker run --memory=512m --memory-swap=1g my-image
```

#### **C. Optimize Disk Usage**
- **Clean up old images & containers:**
  ```bash
  docker system prune -a --volumes
  ```
- **Use read-only filesystems where possible:**
  ```bash
  docker run --read-only my-image
  ```
- **Avoid mounting large directories (e.g., `/var/log`)** – instead, use volume backups.

#### **D. Monitor Resource Usage**
```bash
# Check container stats in real-time
docker stats --no-stream

# Find containers consuming the most memory
docker ps -q --filter "status=running" | xargs -I {} sh -c "docker inspect --format '{{.Name}} {{.HostConfig.Memory}}' {}" | sort -nr
```

---

### **2. Network Misconfigurations**
**Symptoms:**
- `Connection refused` between containers.
- `Permission denied` when accessing ports.
- `DNS resolution fails`.

**Root Causes:**
- Incorrect port mappings (`-p` flag).
- Missing network mode (`--network` flag).
- Firewall blocking internal traffic.
- Hardcoded IPs instead of DNS names.

#### **Fixes:**
#### **A. Use Docker Networks Properly**
```bash
# Create a custom bridge network
docker network create my_network

# Attach containers to the same network
docker run --network my_network --name container1 my-image
docker run --network my_network --name container2 my-image
```
**Avoid:**
```bash
# ❌ Bad: Host network mode (exposes all ports)
docker run --net=host my-image
```

#### **B. Publish Ports Correctly**
```bash
# Publish port 8080 inside container to host port 80
docker run -p 80:8080 my-image

# In docker-compose.yml
ports:
  - "8080:80"
```

#### **C. Use Environment Variables for Dynamic IPs**
Instead of hardcoding IPs:
```dockerfile
# In your app, read the host service IP via env var
export SERVICE_IP=$(getent hosts my-service | awk '{ print $1 }')
```

#### **D. Debug Network Issues**
```bash
# Check container IP
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' my-container

# Test connectivity from inside a container
docker exec -it my-container ping my-service

# Check routing table
docker exec -it my-container ip route
```

---

### **3. Unpredictable Behavior (Race Conditions, Missing Configs)**
**Symptoms:**
- Containers fail intermittently with no clear pattern.
- Apps behave differently in dev vs. prod.

**Root Causes:**
- Missing environment variables.
- Race conditions in startup scripts.
- Hardcoded paths (e.g., `/app/config` vs. `./config`).
- Dependencies not waiting for other services.

#### **Fixes:**
#### **A. Use Environment Variables for Configs**
```bash
# Avoid hardcoding paths
docker run -e DB_HOST=postgres -e DB_PORT=5432 my-app

# In docker-compose.yml
environment:
  - DB_HOST=postgres
  - DB_PORT=5432
```

#### **B. Health Checks & Startup Protocols**
```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

#### **C. Use Entrypoint Scripts for Orderly Startup**
```dockerfile
# Dockerfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# entrypoint.sh
#!/bin/sh
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done
exec "$@"
```

#### **D. Debug with `docker logs`**
```bash
# Follow logs in real-time
docker logs -f my-container

# Show previous logs (if journalctl is used)
docker inspect --format='{{.LogPath}}' my-container | xargs journalctl -u docker -f
```

---

### **4. Security Vulnerabilities**
**Symptoms:**
- Containers run as `root`.
- Unnecessary host ports exposed.
- Secrets in plaintext in images.

**Root Causes:**
- Running containers with `--privileged`.
- Using `docker:latest` with default configs.
- Mounting `/host/path` into container without restrictions.

#### **Fixes:**
#### **A. Run as Non-Root User**
```dockerfile
# Dockerfile
RUN useradd -m myuser && \
    chown -R myuser /app
USER myuser
```

#### **B. Avoid `--privileged` Mode**
```bash
# ❌ Avoid
docker run --privileged my-image

# ✅ Use capabilities instead
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE my-image
```

#### **C. Use Secrets Management**
```bash
# Pass secrets via Docker secrets (Swarm) or env vars
docker run -e DB_PASSWORD=$DB_PASSWORD my-app

# In docker-compose (use `.env` file)
services:
  app:
    environment:
      DB_PASSWORD: ${DB_PASSWORD}
```

#### **D. Scan Images for Vulnerabilities**
```bash
# Use Docker Scout or Trivy
docker scout scan my-image
# or
docker pull ghcr.io/aquasecurity/trivy:latest
trivy image my-image
```

---

### **5. Orphaned Containers & Storage Bloat**
**Symptoms:**
- `docker ps -a` shows many stopped containers.
- Disk usage grows uncontrollably.

**Root Causes:**
- No cleanup scripts (`docker-compose down` not run).
- Unbounded volumes.
- Leftover intermediate layers.

#### **Fixes:**
#### **A. Automate Cleanup with `docker-compose`**
```yaml
# In docker-compose.yml
services:
  redis:
    image: redis
    volumes:
      - redis_data:/data
volumes:
  redis_data: {}
```
**Then:**
```bash
docker-compose down -v  # Removes volumes
```

#### **B. Use `docker system prune`**
```bash
# Remove stopped containers, networks, and unused images
docker system prune -a --volumes
```

#### **C. Set Up a Garbage Collection Schedule**
```bash
# Run weekly (add to cron)
0 0 * * 0 docker system prune -a --volumes
```

---

## **Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                                                                 | **Example Command**                                  |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| `docker stats`           | Monitor CPU/memory usage in real-time.                                       | `docker stats --no-stream`                            |
| `docker inspect`         | Check container metadata (network, mounts, logs).                            | `docker inspect my-container`                          |
| `docker events`          | Stream real-time events (creations, deaths, logs).                           | `docker events -f 'event=die'`                        |
| `crictl` (CRI compatibility) | Debug Kubernetes-like container runtime.                                | `crictl ps` (requires `crictl` plugin)                |
| `strace`                 | Trace system calls inside a container.                                       | `docker exec -it my-container strace -p 1`            |
| `netstat` / `ss`         | Check open ports and network connections.                                   | `docker exec -it my-container netstat -tulnp`         |
| `journalctl`             | View Docker daemon logs.                                                    | `journalctl -u docker -f`                             |
| **Distributed Tracing**  | Trace requests across microservices (e.g., Jaeger, OpenTelemetry).          | See [OpenTelemetry documentation](https://opentelemetry.io/) |

### **Example: Debugging a Slow Container**
1. **Check resource usage:**
   ```bash
   docker stats my-container
   ```
2. **Inspect network:**
   ```bash
   docker exec -it my-container netstat -tulnp
   ```
3. **Check logs:**
   ```bash
   docker logs -f my-container --tail 50
   ```
4. **Use `strace` to find blocking calls:**
   ```bash
   docker exec -it my-container strace -p 1 -o /tmp/trace.log
   ```

---

## **Prevention Strategies**
### **1. Follow Docker Best Practices**
- **Use multi-stage builds** to minimize image size:
  ```dockerfile
  # Stage 1: Build dependencies
  FROM golang:1.21 as builder
  WORKDIR /app
  COPY . .
  RUN go build -o myapp

  # Stage 2: Runtime image
  FROM alpine:latest
  COPY --from=builder /app/myapp /
  CMD ["./myapp"]
  ```
- **Minimize layers** (combine `RUN` commands).
- **Use `.dockerignore`** to exclude unnecessary files.

### **2. Implement Infrastructure as Code (IaC)**
- Use **Terraform** or **Pulumi** to define containerized environments.
- Example Terraform snippet:
  ```hcl
  resource "docker_container" "myapp" {
    name  = "myapp"
    image = "my-image:latest"
    ports {
      internal = 8080
      external = 8080
    }
    env = [
      "DB_HOST=postgres",
      "DB_PORT=5432"
    ]
  }
  ```

### **3. Automate Testing & CI/CD**
- **Test containers in CI:**
  ```yaml
  # GitHub Actions example
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: docker-compose up --abort-on-container-exit
  ```
- **Use `healthcheck` in `docker-compose`** to validate startup.

### **4. Monitor & Alert Proactively**
- **Set up Prometheus + Grafana** for container metrics.
- **Use Docker Events API** for alerting:
  ```bash
  docker events --filter 'event=die' | grep -i "error"
  ```
- **Integrate with PagerDuty/Slack** for critical failures.

### **5. Document Anti-Patterns & Fixes**
- Maintain a **runbook** (e.g., Confluence/Notion) with:
  - Common issues (e.g., "Container crashes on startup").
  - Fixes (e.g., "Add `--memory=1g`").
  - Owners (who to ping).

---

## **Final Checklist for Container Health**
| **Action**                          | **Tool/Command**                                  |
|-------------------------------------|---------------------------------------------------|
| Check running containers            | `docker ps`                                       |
| Find stopped containers             | `docker ps -a`                                    |
| Clean up unused resources           | `docker system prune -a --volumes`                |
| Monitor resource usage              | `docker stats --no-stream`                        |
| Inspect container metadata          | `docker inspect my-container`                     |
| Test network connectivity           | `docker exec -it my-container ping 8.8.8.8`       |
| Debug slow performance              | `strace`, `perf`, `docker stats`                  |
| Scan for vulnerabilities           | `docker scout scan my-image`                      |
| Automate cleanup                    | Add `docker-compose down -v` to CI/CD              |

---

## **Conclusion**
Containers are powerful but require discipline to avoid anti-patterns. By following this guide, you can:
✅ **Prevent resource starvation** with proper limits.
✅ **Debug network issues** using Docker networks and `netstat`.
✅ **Avoid security risks** by running as non-root and using secrets.
✅ **Prevent bloat** with automated cleanup and volume management.
✅ **Proactively monitor** with tools like `docker stats` and Prometheus.

**Key Takeaway:** Treat containers like production systems—monitor, test, and automate cleanup. When issues arise, follow the **symptom checklist → root cause → fix → prevent** flow.

---
**Further Reading:**
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Cloud Native Patterns (Anti-Patterns)](https://cloudnative.pub/)
- [Kubernetes Anti-Patterns (relevant for containerized apps)](https://www.oreilly.com/library/view/kubernetes-anti-patterns/9781492045029/)