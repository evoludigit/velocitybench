# **Debugging Containers: A Troubleshooting Guide**

## **Introduction**
Debugging containers can be challenging due to their isolated environments, ephemeral nature, and complex dependencies. Whether you're troubleshooting a failing deployment, performance issues, or misconfigured services, this guide provides a structured approach to diagnosing and resolving problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms align with your issue:

### **Startup Failures**
- Container fails to start (`CRITICAL` logs, `exit code` errors).
- `docker ps -a` shows a stopped container with no logs.
- Crashes immediately after startup (`OOMKilled`, segfaults, or `command not found`).

### **Runtime Errors**
- Application behaves unexpectedly (timeouts, `500` errors, or crashes).
- Network connectivity issues (can’t reach internal APIs or external services).
- High resource usage (CPU/memory swapping, disk I/O bottlenecks).

### **Persistent State Issues**
- Data corruption or missing files in volume-mounted directories.
- Slow performance due to disk I/O (`read/write` latency).
- Misconfigured environment variables or secrets propagation.

### **Dependency Failures**
- Database connection errors (`connection refused`).
- External service unreachable (APIs, queues, or storage backends).
- Missing required files (`/app` not found, `ENTRYPOINT` script errors).

---

## **2. Common Issues & Fixes**

### **A. Container Won’t Start**
#### **Symptom:**
`docker ps -a` shows the container exited with a non-zero status code.

#### **Debugging Steps:**
1. **Check Logs**
   ```sh
   docker logs <container_id_or_name>
   ```
   - Look for errors like:
     - `exec failed: unable to create process`
     - `cannot connect to the Docker daemon`
     - `OOMKilled` (Out of Memory)

2. **Inspect the Container**
   ```sh
   docker inspect <container_id> --format='{{json .State}}'
   ```
   - Check `Error` field for detailed failure reasons.

3. **Run Interactively for Debugging**
   ```sh
   docker run -it --entrypoint sh <image>  # Replace with your image
   ```
   - Manually test the entrypoint or script.

#### **Common Fixes:**
- **Wrong Command in `CMD`/`ENTRYPOINT`**
  ```dockerfile
  # Bad: CMD ["non-existent-command"]
  CMD ["bash", "-c", "your-script.sh"]  # Or specify `/app/run.sh`
  ```
- **Missing Dependencies**
  ```sh
  apt-get update && apt-get install -y required-library  # For Debian-based images
  ```
- **Resource Limits Exceeded**
  ```sh
  docker run --memory=512m --cpus=1 <image>  # Reduce memory/CPU
  ```

---

### **B. Application Crashes During Runtime**
#### **Symptom:**
Container starts but crashes after some time (e.g., `SIGSEGV`, segmentation fault).

#### **Debugging Steps:**
1. **Attach to a Running Container**
   ```sh
   docker exec -it <container_id> bash
   ```
   - Reproduce the issue manually.

2. **Check Core Dumps (if enabled)**
   ```sh
   docker run --ulimit core=unlimited <image>  # Enable core dumps
   ```

3. **Enable Debug Logging**
   - Modify your app to log stack traces (e.g., `error.log` in Go/Python).

#### **Common Fixes:**
- **Memory Leaks**
  ```sh
  docker stats <container_id>  # Monitor memory usage
  ```
  - Increase `--memory` or optimize app code.

- **Missing Environment Variables**
  ```sh
  docker run -e VAR_NAME=value <image>  # Pass required env vars
  ```

---

### **C. Networking Issues**
#### **Symptom:**
Container can’t connect to databases, APIs, or external services.

#### **Debugging Steps:**
1. **Test Connectivity Inside Container**
   ```sh
   docker exec -it <container_id> sh -c "ping google.com || curl -v http://some-api"
   ```

2. **Check DNS Resolution**
   ```sh
   docker exec -it <container_id> nslookup google.com
   ```

3. **Inspect Network Configuration**
   ```sh
   docker inspect <container_id> | grep -i network
   ```

#### **Common Fixes:**
- **Use a Custom DNS**
  ```sh
  docker run --dns 8.8.8.8 --dns 1.1.1.1 <image>
  ```
- **Bind Mount Host Configs**
  ```sh
  docker run -v /etc/resolv.conf:/etc/resolv.conf:ro <image>
  ```
- **Network Isolation**
  ```sh
  docker network create my-bridge  # Use a dedicated network
  ```

---

### **D. Persistent Storage Corruption**
#### **Symptom:**
Data in volumes/mounts is missing or corrupted.

#### **Debugging Steps:**
1. **Verify Volume Mounts**
   ```sh
   docker volume inspect <volume_name>
   ```
   - Check if the volume exists and is accessible.

2. **Test Write/Read Operations**
   ```sh
   docker exec -it <container_id> dd if=/dev/zero of=/testfile bs=1M count=1
   ```

#### **Common Fixes:**
- **Use Read-Write Volumes**
  ```sh
  docker run -v /path/on/host:/app/data --restart unless-stopped <image>
  ```
- **Backup & Restore Data**
  ```sh
  docker cp <container_id>:/app/data ./backup/
  ```

---

### **E. Dependency Failures (e.g., Missing Databases)**
#### **Symptom:**
App fails to connect to a required service (e.g., PostgreSQL, Redis).

#### **Debugging Steps:**
1. **Check Service Readiness**
   ```sh
   docker exec -it <db_container> pg_isready -U postgres  # For PostgreSQL
   ```

2. **Verify Network Connectivity**
   ```sh
   docker exec -it <app_container> ping <db_container>  # Should resolve via DNS
   ```

#### **Common Fixes:**
- **Use Docker Compose for Local Dev**
  ```yaml
  services:
    app:
      depends_on:
        - postgres
    postgres:
      image: postgres
  ```
- **Test with `healthcheck`**
  ```dockerfile
  HEALTHCHECK --interval=5s --timeout=3s \
    CMD curl -f http://localhost || exit 1
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Monitoring**
- **Structured Logging**
  Use a library like `structlog` (Python) or `logrus` (Go) for JSON logs.
- **Centralized Logging**
  ```sh
  docker-compose exec app fluentd tail -f /var/log/app.log
  ```

### **B. Debugging Images**
- **Multi-Stage Builds for Debug**
  ```dockerfile
  FROM python:3.9 as builder
  RUN pip install python-debugger
  COPY . /app
  RUN python -m pytest --debug

  FROM python:3.9-slim
  COPY --from=builder /app /app
  CMD ["python", "app.py"]
  ```

- **Interactive Debugging**
  ```sh
  docker run -it --entrypoint sh <image>  # Shell into the image
  ```

### **C. Performance Profiling**
- **CPU Profiling (Go Example)**
  ```sh
  go tool pprof http://localhost:6060/debug/pprof/profile
  ```
- **Memory Profiling**
  ```sh
  docker run --memory-profiler-rate=1 -it <image>  # Enable memory profiling
  ```

### **D. Network Debugging**
- **Traceroute Inside Container**
  ```sh
  docker exec -it <container_id> traceroute google.com
  ```
- **Packet Capture (Netcat/TCPdump)**
  ```sh
  docker run --network=host -it --rm alpine nc -lvp 8080
  ```

---

## **4. Prevention Strategies**

### **A. Image Optimization**
- **Minimize Layers**
  ```dockerfile
  # Avoid RUN apt-get update && apt-get install ...
  RUN apt-get update && \
      apt-get install -y package1 package2 && \
      rm -rf /var/lib/apt/lists/*
  ```

- **Use Distroless Images**
  ```dockerfile
  FROM gcr.io/distroless/python3.9
  ```

### **B. Health Checks**
```dockerfile
HEALTHCHECK --interval=10s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1
```

### **C. Resource Limits**
```sh
docker run --memory=512m --cpus=1 --restart unless-stopped <image>
```

### **D. CI/CD Debugging**
- **Automated Linting**
  ```dockerfile
  # Use hadolint in CI
  RUN curl -sSfL https://raw.githubusercontent.com/hadolint/hadolint/main/hadolint.sh | sh
  ```

- **Pre-Push Tests**
  ```sh
  docker-compose up --abort-on-container-exit
  ```

---

## **Conclusion**
Debugging containers requires a systematic approach:
1. **Check logs & inspect container state.**
2. **Reproduce issues interactively.**
3. **Use tools like `nsenter`, `docker stats`, and profiling.**
4. **Prevent future issues with health checks, resource limits, and optimized images.**

By following this guide, you can resolve container issues efficiently and ensure a stable deployment pipeline.

---
**Next Steps:**
- Use `docker-compose` for complex setups.
- Automate debugging with CI/CD (GitHub Actions, GitLab CI).
- Monitor with Prometheus + Grafana for long-term stability.