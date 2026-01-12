# **Debugging Containers Migration: A Troubleshooting Guide**

---

## **1. Introduction**
The **Containers Migration** pattern involves migrating applications or workloads from traditional virtual machines (VMs), bare-metal servers, or legacy monolithic setups into containerized environments (e.g., Docker, Kubernetes). While this offers scalability, portability, and efficiency, migration can introduce performance bottlenecks, dependency issues, and operational challenges.

This guide provides a structured approach to diagnosing and resolving common problems during container migration.

---

## **2. Symptom Checklist**
Before diving into fixes, identify which symptoms align with your issue:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Slow container startup** | Containers take minutes to initialize | Missing dependencies, large images, I/O bottlenecks |
| **Crashing containers** | Apps fail to start or exit abruptly | Incorrect ports, missing environment variables, resource limits |
| **Network connectivity issues** | Containers can't reach external services | Misconfigured DNS, network policies, or security groups |
| **High resource usage** | Containers consume excessive CPU/memory | Poorly optimized containers, no resource limits |
| **Volume/Storage issues** | Data not persisting or mounts failing | Incorrect volume definitions, permission problems |
| **Log visibility problems** | Logs inaccessible or truncated | Log drivers misconfigured, log rotation issues |
| **Orchestration failures** | Kubernetes pods don’t scale or deploy | RBAC issues, misconfigured deployments |
| **Health checks failing** | Readiness/liveness probes report unhealthy | App bugs, incorrect health check paths |
| **Dependency conflicts** | Containers fail due to missing libraries | Base image mismatches, runtime dependencies |
| **Security vulnerabilities** | Containers exposed to unauthorized access | Misconfigured security contexts, open ports |

---

## **3. Common Issues and Fixes**

### **3.1 Slow Container Startup**
**Symptoms:**
- Containers take **>30s** to initialize.
- Docker logs show `Pulling image...` hanging.

**Possible Causes & Fixes:**

#### **Cause 1: Large or Unoptimized Base Images**
- **Fix:** Use lightweight base images (e.g., `alpine` instead of `ubuntu`).
  ```dockerfile
  FROM python:3.9-alpine  # Smaller than standard Python images
  ```
- **Fix:** Multi-stage builds to reduce final image size.
  ```dockerfile
  # Build stage
  FROM python:3.9-slim as builder
  COPY . /app
  RUN pip install -r requirements.txt

  # Runtime stage
  FROM python:3.9-alpine
  COPY --from=builder /app /app
  CMD ["python", "app.py"]
  ```

#### **Cause 2: Missing Dependencies at Runtime**
- **Fix:** Ensure all dependencies are installed and layered correctly.
  ```dockerfile
  RUN apt-get update && \
      apt-get install -y curl && \
      rm -rf /var/lib/apt/lists/*  # Cleanup
  ```

#### **Cause 3: I/O Bottlenecks (Slow Storage)**
- **Fix:** Use SSDs for Docker storage driver.
  ```bash
  # Check current storage driver
  docker info | grep "Storage Driver"
  # Switch to overlay2 (default in newer Docker)
  echo '{"storage-driver": "overlay2"}' | sudo tee /etc/docker/daemon.json
  sudo systemctl restart docker
  ```

---

### **3.2 Crashing Containers**
**Symptoms:**
- `Exit code 137` (OOM killed) or `Error response from daemon: rpc error: code = Unknown desc =`
- Logs show `Segmentation fault` or `Permission denied`.

**Possible Causes & Fixes:**

#### **Cause 1: Missing Environment Variables**
- **Fix:** Pass required env vars at runtime.
  ```bash
  docker run -e DB_HOST=mysql -e DB_USER=admin my-app
  ```
- **Fix:** Define defaults in `Dockerfile`.
  ```dockerfile
  ENV DB_HOST=default_db DB_USER=default_admin
  ```

#### **Cause 2: Incorrect Port Mappings**
- **Fix:** Ensure ports are exposed and mapped correctly.
  ```dockerfile
  EXPOSE 8080
  ```
  ```bash
  docker run -p 8080:8080 my-app
  ```

#### **Cause 3: Resource Limits Exceeded**
- **Fix:** Set CPU/memory limits in `docker run` or Kubernetes.
  ```bash
  docker run --cpus="0.5" --memory=512m my-app
  ```
  ```yaml
  # Kubernetes resource limits
  resources:
    limits:
      cpu: "500m"
      memory: "512Mi"
  ```

#### **Cause 4: Permission Issues**
- **Fix:** Run as non-root (security best practice).
  ```dockerfile
  USER 1000  # Match host UID
  ```
  ```bash
  docker run --user $(id -u):$(id -g) my-app
  ```

---

### **3.3 Network Connectivity Issues**
**Symptoms:**
- Containers can’t reach databases, APIs, or each other.
- `curl: (7) Failed to connect to host`.

**Possible Causes & Fixes:**

#### **Cause 1: Incorrect DNS Resolution**
- **Fix:** Use `--dns` flag or configure `docker-compose.yml`.
  ```yaml
  # docker-compose.yml
  services:
    web:
      dns: 8.8.8.8  # Google DNS
  ```
  ```bash
  docker run --dns=8.8.8.8 my-app
  ```

#### **Cause 2: Misconfigured Network Policies (Kubernetes)**
- **Fix:** Define `NetworkPolicy` to allow traffic.
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-db-access
  spec:
    podSelector:
      matchLabels:
        app: web
    egress:
    - to:
      - podSelector:
          matchLabels:
            app: database
      ports:
      - protocol: TCP
        port: 5432
  ```

#### **Cause 3: Missing Host Network Access**
- **Fix:** Use `--network=host` (not recommended for production).
  ```bash
  docker run --network=host my-app
  ```

---

### **3.4 High Resource Usage**
**Symptoms:**
- CPU/memory warnings in Kubernetes.
- Containers get OOM-killed frequently.

**Possible Causes & Fixes:**

#### **Cause 1: No Resource Limits**
- **Fix:** Set limits in `docker run` or Kubernetes.
  ```yaml
  # Kubernetes deployment
  resources:
    requests:
      cpu: "100m"
      memory: "256Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
  ```

#### **Cause 2: Long-Running Processes**
- **Fix:** Use process monitoring (e.g., `pmap` inside container).
  ```bash
  docker exec -it my-container pmap -x $(pgrep -f "your_process")
  ```

#### **Cause 3: Unoptimized Code**
- **Fix:** Profile app performance inside container.
  ```bash
  docker run -it my-app bash -c "python -m cProfile -s time app.py"
  ```

---

### **3.5 Volume/Storage Issues**
**Symptoms:**
- Data not persisting after container restart.
- `Permission denied` when accessing volumes.

**Possible Causes & Fixes:**

#### **Cause 1: Incorrect Volume Mounts**
- **Fix:** Use named volumes (`docker volume`) or bind mounts.
  ```bash
  docker run -v my_volume:/data my-app
  ```

#### **Cause 2: Permission Conflicts**
- **Fix:** Ensure host and container UIDs match.
  ```dockerfile
  RUN chown -R 1000:1000 /data
  ```

---

## **4. Debugging Tools and Techniques**

| **Tool/Technique** | **Use Case** | **Example Command/Config** |
|--------------------|-------------|----------------------------|
| **`docker stats`** | Monitor CPU/memory usage | `docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"` |
| **`kubectl describe pod`** | Kubernetes pod debugging | `kubectl describe pod my-pod` |
| **`dive`** | Analyze container images | `diver my-image` (installed via `docker run -it wagnerdano/dive`) |
| **`strace`** | Debug syscalls in container | `docker exec -it my-container strace -p 1` |
| **`tcpdump`** | Network packet inspection | `docker run --rm --network=host -v /lib/modules:/lib/modules alpine tcpdump -i eth0 -w dump.pcap` |
| **`journalctl`** | Check systemd-based container logs | `journalctl -u docker.service` |
| **`crictl`** | Debug Kubernetes runtime | `crictl ps` (requires `crictl` CLI) |
| **Health Checks** | Verify app readiness | Define in `Dockerfile` or Kubernetes `livenessProbe`. |
| **`kubectl logs -f`** | Stream pod logs | `kubectl logs -f my-pod --previous` (for crashed pods) |
| **`docker inspect`** | Inspect container/config | `docker inspect my-container` |

---

## **5. Prevention Strategies**

### **5.1 Pre-Migration Checklist**
✅ **Test Containers Locally** – Ensure apps work in isolated environments.
✅ **Benchmark Performance** – Compare VM vs. container startup times.
✅ **Review Security** – Scan images for vulnerabilities (`trivy`, `snyk`).
✅ **Document Dependencies** – List all external services (databases, APIs).
✅ **Plan Rollback Strategy** – Have a backup migration script.

### **5.2 Best Practices During Migration**
🔹 **Use Immutable Images** – Avoid running `apt-get update` inside containers.
🔹 **Implement Health Checks** – Add readiness/liveness probes.
🔹 **Set Resource Limits** – Prevent noisy neighbors.
🔹 **Monitor Logs Proactively** – Use ELK Stack or Loki for centralized logging.
🔹 **Leverage Orphaned Resource Cleanup** – Delete unused containers/volumes.
🔹 **Test Network Policies Early** – Avoid last-minute connectivity issues.

### **5.3 Post-Migration Optimization**
🔧 **Optimize Images** – Remove unused layers (`docker image prune`).
🔧 **Auto-Scaling Configuration** – Use HPA (Horizontal Pod Autoscaler) for Kubernetes.
🔧 **CI/CD Integration** – Automate testing for new container deployments.
🔧 **Secret Management** – Use Kubernetes Secrets or Vault instead of env vars.

---

## **6. Conclusion**
Migrating to containers improves efficiency but requires careful debugging. By following this guide, you can:
✔ **Quickly identify symptoms** using the checklist.
✔ **Apply fixes** for common issues (startup times, crashes, networking).
✔ **Leverage debugging tools** for deep diving.
✔ **Prevent future problems** with best practices.

For persistent issues, consult Docker’s [Troubleshooting Guide](https://docs.docker.com/troubleshoot/) or Kubernetes’ [Debugging Docs](https://kubernetes.io/docs/tasks/debug-application-cluster/). Happy migrating! 🚀