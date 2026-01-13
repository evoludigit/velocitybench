# **Debugging Docker & Container Deployment: A Troubleshooting Guide**

## **Introduction**
Docker and containerization are powerful tools for packaging, deploying, and managing applications efficiently. However, misconfigurations, resource constraints, and networking issues can lead to performance degradation, reliability problems, and debugging nightmares.

This guide provides a **practical, step-by-step approach** to diagnose and resolve common Docker and containerization-related issues.

---

## **Symptom Checklist: Is Your Issue Docker-Related?**
Check if any of these symptoms match your problem:

✅ **Containers fail to start** (crash immediately or hang)
✅ **Performance degrades** under load (CPU, memory, or disk bottlenecks)
✅ **Networking issues** (containers can’t communicate, port conflicts)
✅ **Logs show undefined errors** (e.g., `OOMKilled`, `Permission Denied`, `Failed to pull image`)
✅ **Scaling fails** (horizontal pod scaling keeps failing)
✅ **Storage-related issues** (volumes not mounted, persistence problems)
✅ **Resource limits not respected** (containers consume too much CPU/memory)
✅ **Image build failures** (missing dependencies, syntax errors in Dockerfile)

If any of these apply, proceed with debugging.

---

## **Common Issues & Fixes (With Code Examples)**

### **1. Containers Fail to Start**
#### **Issue:** `docker-compose up` fails with `exit code 1` or crashes immediately.
**Possible Causes:**
- Missing dependencies in the container.
- Incorrect `CMD`/`ENTRYPOINT` in `Dockerfile`.
- Permissions issues inside the container.
- Environment variables not set correctly.

#### **Debugging Steps:**
1. **Check container logs:**
   ```bash
   docker logs <container_name_or_id>
   ```
   - If logs are empty, force-recreate with debugging:
     ```bash
     docker run --rm -it <image> sh
     ```
2. **Verify `Dockerfile` syntax:**
   - Ensure `CMD` and `ENTRYPOINT` are correct (e.g., `CMD ["python", "app.py"]`).
   - Example `Dockerfile` with proper `CMD`:
     ```dockerfile
     FROM python:3.9
     WORKDIR /app
     COPY . .
     RUN pip install -r requirements.txt
     CMD ["python", "app.py"]
     ```

3. **Check for missing files/dependencies:**
   - If the app depends on external files, ensure they are copied into the container:
     ```dockerfile
     COPY requirements.txt .
     RUN pip install -r requirements.txt
     ```

4. **Permissions issue?**
   - Run with `--user` flag to test:
     ```bash
     docker run -u $(id -u):$(id -g) <image>
     ```

---

### **2. Performance Degradation (CPU/Memory Issues)**
#### **Issue:** Containers slow down under load, or the system crashes due to `OOMKilled`.
**Possible Causes:**
- Container has no resource limits (`--cpu-shares` or `--memory` not set).
- Host machine is overloaded (check `htop`/`docker stats`).
- Disk I/O bottlenecks (slow storage or excessive writes).

#### **Debugging Steps:**
1. **Check resource usage:**
   ```bash
   docker stats <container_name>
   ```
   - If CPU is at 100%, increase limits:
     ```bash
     docker run --cpus="2" --memory="1G" <image>
     ```
   - For `docker-compose`:
     ```yaml
     services:
       my_service:
         deploy:
           resources:
             limits:
               cpus: '2'
               memory: 1G
     ```

2. **Check for `OOMKilled` in logs:**
   - If seen, increase memory limits.
   - Example in `Dockerfile` (prevent swap usage if needed):
     ```dockerfile
     CMD ["python", "app.py"] --no-memcheck
     ```

3. **Monitor disk I/O:**
   - Use `iotop` or `dstat` to check for slow disks.

---

### **3. Networking Issues (Containers Can’t Communicate)**
#### **Issue:** Services inside containers can’t reach each other or expose ports.
**Possible Causes:**
- Incorrect `ports` mapping in `docker run` or `docker-compose`.
- Misconfigured `network_mode` (`bridge`, `host`, or custom network).
- Docker daemon not running or firewall blocking ports.

#### **Debugging Steps:**
1. **Check if ports are exposed:**
   ```bash
   docker port <container_name>
   ```
   - If missing, expose ports explicitly:
     ```bash
     docker run -p 8080:80 <image>
     ```

2. **Test connectivity inside containers:**
   ```bash
   docker exec -it <container> ping <another_container_name>
   ```
   - If ping fails, check DNS resolution:
     ```bash
     docker exec -it <container> cat /etc/resolv.conf
     ```

3. **Verify networking mode:**
   - Use a custom Docker network for better isolation:
     ```bash
     docker network create my_network
     docker run --network=my_network <image>
     ```

4. **Check firewall rules:**
   ```bash
   sudo iptables -L
   ```
   - If ports are blocked, allow them:
     ```bash
     sudo ufw allow 8080/tcp
     ```

---

### **4. Storage & Volume Issues (Persistent Data Loss)**
#### **Issue:** Data disappears after container restart or `docker-compose down`.
**Possible Causes:**
- Volumes not mounted correctly.
- Bind mounts pointing to the wrong host path.
- NFS/SMB shares failing silently.

#### **Debugging Steps:**
1. **Check volume mount status:**
   ```bash
   docker volume ls
   docker volume inspect <volume_name>
   ```
   - If missing, recreate with proper volumes:
     ```bash
     docker run -v /host/path:/container/path <image>
     ```

2. **Verify file permissions:**
   - Ensure the container has read/write access:
     ```bash
     docker run --user $(id -u):$(id -g) -v /host/path:/container/path <image>
     ```

3. **Test with a simple file write:**
   ```bash
   docker exec -it <container> touch /container/path/test_file
   docker exec -it <container> ls /container/path
   ```

---

### **5. Image Build Failures (Dependency or Syntax Errors)**
#### **Issue:** `docker build` fails with `Missing file` or `ERROR: unknown instruction`.
**Possible Causes:**
- Incorrect `COPY`/`ADD` paths in `Dockerfile`.
- Missing build dependencies (e.g., `gcc` for C apps).
- Cache issues (partial builds failing).

#### **Debugging Steps:**
1. **Check `docker build --no-cache`:**
   ```bash
   docker build --no-cache -t my_image .
   ```

2. **Verify `Dockerfile` paths:**
   - Ensure files are in the correct directory:
     ```dockerfile
     COPY ./src /app/src  # Must be in the same directory as Dockerfile
     ```

3. **Install build dependencies (e.g., for Node.js):**
   ```dockerfile
   RUN apt-get update && apt-get install -y nodejs npm
   ```

4. **Check for syntax errors:**
   - Validate syntax before building:
     ```bash
     docker buildx imagetools inspect my_image:latest
     ```

---

## **Debugging Tools & Techniques**

| **Tool**          | **Purpose**                                                                 | **Command/Usage**                                                                 |
|-------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `docker logs`     | View container logs                                                           | `docker logs <container>`                                                        |
| `docker stats`    | Monitor CPU/memory usage                                                     | `docker stats`                                                                   |
| `docker inspect`  | Debug container/network/config details                                         | `docker inspect <container>`                                                    |
| `docker exec`     | Run commands inside a running container                                       | `docker exec -it <container> sh`                                                |
| `docker-compose logs` | Check multi-container logs                                             | `docker-compose logs -f`                                                         |
| `netstat`/`ss`    | Check network connections                                                     | `ss -tulnp` (Linux)                                                             |
| `strace`          | Trace system calls (for deep debugging)                                       | `strace -p <PID>`                                                                |
| `docker debug`    | Attach a shell to a failing container                                         | `docker debug <container>` (if using Docker Desktop)                           |
| `cgroup`          | Check resource limits (Linux)                                                | `cat /sys/fs/cgroup/memory/docker/<container_id>/memory.limit_in_bytes`          |

**Advanced Debugging:**
- **Docker Bench Security:** Scan for security misconfigurations.
  ```bash
  docker run --rm -it docker/docker-bench-security
  ```
- **`docker-compose up --build --force-recreate`:** Force-recreate containers if misconfigured.

---

## **Prevention Strategies**

### **1. Use `docker-compose` for Better Orchestration**
- Define services, networks, and volumes in a structured way.
- Example `docker-compose.yml`:
  ```yaml
  version: '3.8'
  services:
    web:
      image: nginx:latest
      ports:
        - "8080:80"
      volumes:
        - ./html:/usr/share/nginx/html
      restart: unless-stopped
  ```

### **2. Set Resource Limits (CPU/Memory)**
- Prevent containers from starving the host:
  ```yaml
  services:
    app:
      deploy:
        resources:
          limits:
            cpus: '1'
            memory: 512M
  ```

### **3. Use Health Checks**
- Automatically restart containers if they fail:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost"]
    interval: 30s
    timeout: 10s
    retries: 3
  ```

### **4. Implement Logging & Monitoring**
- Use **Prometheus + Grafana** for metrics.
- Forward logs to **ELK Stack** (Elasticsearch, Logstash, Kibana).

### **5. Automate Testing with CI/CD**
- Test containers before deploying:
  ```dockerfile
  RUN ["/app/test.sh"]  # Run tests during build
  ```

### **6. Follow Docker Best Practices**
- **Multi-stage builds** (reduce image size).
- **Non-root users** (security).
- **Use `.dockerignore`** (exclude unnecessary files).

---

## **Conclusion**
Debugging Docker and container issues requires a **structured approach**:
1. **Check logs** (`docker logs`, `docker-compose logs`).
2. **Isolate the problem** (CPU, memory, networking, storage).
3. **Test fixes incrementally** (restart containers, adjust configs).
4. **Monitor & prevent future issues** (resource limits, health checks, CI/CD).

By following this guide, you should be able to **quickly identify and resolve** most Docker-related issues. For persistent problems, consider **Docker’s official support forums** or **community troubleshooting resources**.

---
**Need faster help?**
- Use `docker debug` (if available).
- Check **Docker’s troubleshooting docs**: [https://docs.docker.com/troubleshoot](https://docs.docker.com/troubleshoot)