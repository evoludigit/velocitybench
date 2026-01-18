# **Debugging Containers: A Troubleshooting Guide**
*A practical, step-by-step guide for resolving container-related issues efficiently.*

---

## **1. Title: Debugging Containers: A Troubleshooting Guide**
Containers (Docker, Kubernetes, or other runtime environments) provide isolation, portability, and scalability—but they can also introduce subtle issues. This guide covers common symptoms, root causes, fixes, and preventative measures to resolve container-related problems quickly.

---

## **2. Symptom Checklist**
Before diving into debugging, check for these **symptoms** to narrow down the issue:

| **Symptom**                     | **Possible Cause**                          | **Severity** |
|----------------------------------|---------------------------------------------|--------------|
| Container fails to start (`EXIT 1`, `CrashLoopBackOff`) | Invalid image, misconfigured entrypoint, resource constraints | High |
| Container starts but crashes | Missing dependencies, permission errors, app logic failure | High |
| Slow or unresponsive container | High CPU/memory usage, disk I/O bottlenecks | Medium |
| Network connectivity issues | Incorrect network mode, port conflicts, DNS misconfiguration | High |
| Logs show errors but container runs | Log rotation issues, missing log collectors (e.g., Fluentd) | Medium |
| Volume mount failures | Incorrect permissions (`chmod`), SELinux/AppArmor blocking | Medium |
| Health checks failing (`livenessProbe`/`readinessProbe`) | Application not ready, misconfigured probe | Medium |
| Image pull failures (`Error: pull access denied`) | Incorrect registry permissions, corrupted image | High |
| Resource limits enforced (`OOMKilled`) | Too much memory/cpu allocated, or app leaks | High |

---
**Action:**
Run `docker ps -a` or `kubectl get pods --all-namespaces` to identify failing containers.

---

## **3. Common Issues & Fixes**

### **A. Container Won’t Start (Exit Code 1)**
**Symptom:**
`docker run` fails with `Error response from daemon: ContainerCommandInvokationFailed` or `kubectl get pods` shows `CrashLoopBackOff`.

#### **Common Causes & Fixes:**
1. **Invalid Entrypoint/Command**
   - **Cause:** The container’s `ENTRYPOINT` or `CMD` in `Dockerfile` is incorrect.
   - **Fix:**
     - Check the container’s exact command:
       ```bash
       docker inspect <container_id> --format='{{.Config.Entrypoint}} {{.Config.Cmd}}'
       ```
     - Modify the `Dockerfile` to use the correct command:
       ```dockerfile
       ENTRYPOINT ["python3"]
       CMD ["app.py"]
       ```
     - Rebuild and run:
       ```bash
       docker build -t myapp .
       docker run myapp
       ```

2. **Missing Dependencies**
   - **Cause:** The application requires libraries/binaries not installed in the image.
   - **Fix:**
     - Install missing packages (example for Debian/Ubuntu):
       ```dockerfile
       RUN apt-get update && apt-get install -y python3-pip
       ```
     - Use `.dockerignore` to exclude unnecessary files:
       ```
       *.pyc
       __pycache__
       ```

3. **Permission Denied Inside Container**
   - **Cause:** User permissions in the image don’t match the running container.
   - **Fix:**
     - Run as root (temporarily for debugging):
       ```bash
       docker run -u root myapp
       ```
     - Set correct permissions in `Dockerfile`:
       ```dockerfile
       RUN chmod -R 755 /app
       USER 1000  # Switch to non-root user
       ```

4. **Resource Constraints (CPU/Memory)**
   - **Cause:** The container requests more resources than the host can provide.
   - **Fix:**
     - Check resource usage:
       ```bash
       docker stats <container_id>
       ```
     - Limit resources in `docker run` or Kubernetes `limitRange`:
       ```bash
       docker run --memory=512m --cpus=1 myapp
       ```
     - In Kubernetes:
       ```yaml
       resources:
         limits:
           cpu: "500m"
           memory: "512Mi"
       ```

---

### **B. Container Runs but Crashes**
**Symptom:**
Container starts but exits immediately or logs show errors like `Segmentation fault` or `Permission denied`.

#### **Common Causes & Fixes:**
1. **Application-Level Errors**
   - **Cause:** The app crashes due to logic errors (e.g., missing config, DB connection failure).
   - **Fix:**
     - Check logs:
       ```bash
       docker logs <container_id>
       kubectl logs <pod_name> --previous  # For Kubernetes
       ```
     - Example log output:
       ```
       app[1]: ERROR: Database connection failed!
       ```
     - Debug inside the container:
       ```bash
       docker exec -it <container_id> /bin/bash
       ```
     - Verify environment variables:
       ```bash
       printenv
       ```

2. **Missing Environment Variables**
   - **Cause:** The app expects env vars not provided.
   - **Fix:**
     - Pass env vars explicitly:
       ```bash
       docker run -e DB_HOST=postgres myapp
       ```
     - In Kubernetes, use `env` or `ConfigMap`:
       ```yaml
       env:
         - name: DB_HOST
           value: "postgres-service"
       ```

3. **SELinux/AppArmor Blocking Operations**
   - **Cause:** Security policies restrict file/system access.
   - **Fix:**
     - Temporarily disable SELinux (for testing):
       ```bash
       setenforce 0
       ```
     - Adjust container profiles (e.g., in `docker run`):
       ```bash
       docker run --security-opt label=disable myapp
       ```

---

### **C. Network Issues**
**Symptom:**
Container cannot connect to external services (e.g., DB, APIs) or other containers.

#### **Common Causes & Fixes:**
1. **Incorrect Network Mode**
   - **Cause:** Wrong network configuration (e.g., `bridge` vs. `host`).
   - **Fix:**
     - Check network settings:
       ```bash
       docker network inspect <network_name>
       ```
     - Run with the correct network:
       ```bash
       docker run --network=my_network myapp
       ```

2. **Port Conflicts**
   - **Cause:** Port `80` is already in use by another container/host service.
   - **Fix:**
     - Find and kill conflicting processes:
       ```bash
       sudo lsof -i :80
       sudo kill <pid>
       ```
     - Map a different host port:
       ```bash
       docker run -p 8080:80 myapp
       ```

3. **DNS Resolution Failures**
   - **Cause:** Container DNS not configured (e.g., `dns=8.8.8.8` not set).
   - **Fix:**
     - Use a custom DNS resolver:
       ```bash
       docker run --dns 8.8.8.8 --dns 1.1.1.1 myapp
       ```
     - In Kubernetes, ensure `kube-dns` is running:
       ```bash
       kubectl get pods -n kube-system | grep dns
       ```

---

### **D. Volume Mount Failures**
**Symptom:**
Container fails to access mounted volumes with errors like `Permission denied` or `No such file or directory`.

#### **Common Causes & Fixes:**
1. **Incorrect Volume Permissions**
   - **Cause:** Host directory permissions don’t match container user.
   - **Fix:**
     - Adjust host directory permissions:
       ```bash
       chmod -R 777 /host/path/to/volume
       ```
     - Or change the container’s working user:
       ```dockerfile
       USER 1000
       WORKDIR /app
       ```

2. **Volume Not Initialized**
   - **Cause:** Anonymous volume created but not populated.
   - **Fix:**
     - Initialize the volume manually:
       ```bash
       touch /host/path/to/volume/file.txt
       ```

3. **SELinux Blocking Volume Access**
   - **Cause:** SELinux context mismatch.
   - **Fix:**
     - Relabel the volume:
       ```bash
       chcon -Rt svirt_sandbox_file_t /host/path/to/volume
       ```

---

### **E. Image Pull Failures**
**Symptom:**
`Error: pull access denied` or `image not found`.

#### **Common Causes & Fixes:**
1. **Incorrect Registry Authentication**
   - **Cause:** No credentials for private registry.
   - **Fix:**
     - Log in to the registry:
       ```bash
       docker login registry.example.com
       ```
     - For Kubernetes, use `imagePullSecrets`:
       ```yaml
       imagePullSecrets:
         - name: regcred
       ```

2. **Corrupted Image Layer**
   - **Cause:** Incomplete or damaged image.
   - **Fix:**
     - Re-pull the image:
       ```bash
       docker pull myapp:latest
       ```
     - Clean up old layers:
       ```bash
       docker system prune -a
       ```

---

## **4. Debugging Tools & Techniques**

### **A. Essential Docker/Kubernetes Commands**
| **Tool**               | **Command**                                  | **Purpose**                          |
|------------------------|---------------------------------------------|--------------------------------------|
| `docker inspect`       | `docker inspect <container>`                | View container metadata (config, logs) |
| `docker logs`          | `docker logs -f <container>`                | Tail container logs                  |
| `kubectl describe`     | `kubectl describe pod <pod_name>`           | Debug Kubernetes pod issues          |
| `docker exec`          | `docker exec -it <container> bash`          | Shell into running container         |
| `docker cp`            | `docker cp <container>:/file /host/path`    | Copy files in/out of container       |
| `crictl` (K8s)         | `crictl ps`                                 | Inspect container runtime (CRI)       |
| `kubectl debug`        | `kubectl debug -it <pod>`                   | Debug ephemeral containers           |

---

### **B. Logging and Monitoring**
1. **Tail Logs in Real-Time**
   ```bash
   docker logs -f <container>
   kubectl logs -f <pod> --tail=50
   ```
2. **Use `journalctl` for Systemd-Based Containers**
   ```bash
   journalctl -u docker.service -f
   ```
3. **Integrate with Logging Tools**
   - **ELK Stack (Elasticsearch, Logstash, Kibana)**
   - **Fluentd + Grafana**
   - **Loki (Prometheus monitoring)**

---

### **C. Network Debugging**
1. **Check Connectivity Inside Container**
   ```bash
   docker exec <container> ping google.com
   docker exec <container> curl -v http://example.com
   ```
2. **Trace Network Paths**
   ```bash
   kubectl exec <pod> -- ip route
   kubectl exec <pod> -- traceroute google.com
   ```
3. **Use `nsenter` to Debug Network Namespaces**
   ```bash
   docker exec <container> nsenter -t 1 -n ip addr
   ```

---

### **D. Performance Profiling**
1. **Check CPU/Memory Usage**
   ```bash
   docker stats <container>
   kubectl top pod <pod_name>
   ```
2. **Profile Application with `pprof`**
   - Inject `pprof` into Go/Python apps:
     ```go
     import _ "net/http/pprof"
     go func() { log.Println(http.ListenAndServe("0.0.0.0:6060", nil)) }()
     ```
   - Access:
     ```bash
     curl http://<container_ip>:6060/debug/pprof/
     ```

3. **Use `strace`/`perf` for Deep Debugging**
   ```bash
   docker exec <container> strace -f -p 1  # Follow PID 1
   docker exec <container> perf top
   ```

---

## **5. Prevention Strategies**

### **A. Best Practices for Container Development**
1. **Minimize Image Size**
   - Use multi-stage builds:
     ```dockerfile
     # Build stage
     FROM golang:1.21 as builder
     WORKDIR /app
     COPY . .
     RUN go build -o myapp

     # Runtime stage
     FROM alpine:latest
     COPY --from=builder /app/myapp /usr/local/bin/
     CMD ["myapp"]
     ```
   - Remove unnecessary packages:
     ```dockerfile
     RUN apt-get remove -y unneeded-package && apt-get clean
     ```

2. **Immutable Images**
   - Avoid running as `root` in production.
   - Use non-root users:
     ```dockerfile
     RUN useradd -m myuser
     USER myuser
     ```

3. **Health Checks**
   - Define `HEALTHCHECK` in `Dockerfile`:
     ```dockerfile
     HEALTHCHECK --interval=30s --timeout=3s \
       CMD curl -f http://localhost:8080/health || exit 1
     ```
   - In Kubernetes, use `livenessProbe`/`readinessProbe`:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 5
       periodSeconds: 10
     ```

4. **Secret Management**
   - Never hardcode secrets in images.
   - Use Kubernetes `Secrets` or Docker secrets:
     ```bash
     echo "secret" | docker secret create mysecret -
     ```
   - Or environment variables (rotate frequently).

5. **Resource Limits**
   - Always set CPU/memory limits:
     ```yaml
     resources:
       requests:
         cpu: "100m"
         memory: "128Mi"
       limits:
         cpu: "500m"
         memory: "512Mi"
     ```

---

### **B. CI/CD Pipeline Checks**
1. **Automated Testing**
   - Run integration tests in CI:
     ```yaml
     # GitHub Actions example
     - name: Test container
       run: docker-compose up --abort-on-container-exit
     ```
2. **Image Scanning**
   - Use tools like **Trivy**, **Clair**, or **Snyk** to scan for vulnerabilities:
     ```bash
     trivy image myapp:latest
     ```
3. **Rollback Strategies**
   - Use Kubernetes `RollingUpdate` with pod disruption budgets:
     ```yaml
     strategy:
       type: RollingUpdate
       rollingUpdate:
         maxUnavailable: 1
         maxSurge: 1
     ```

---

### **C. Observability**
1. **Centralized Logging**
   - Ship logs to **Loki**, **Fluentd**, or **ELK**.
2. **Metrics Collection**
   - Use **Prometheus** + **Grafana** for monitoring.
   - Example Prometheus scrape config:
     ```yaml
     scrape_configs:
       - job_name: 'docker'
         docker_sd_configs:
           - host: unix:///var/run/docker.sock
         relabel_configs:
           - source_labels: [__meta_docker_container_name]
             target_label: container
     ```
3. **Distributed Tracing**
   - Integrate **Jaeger** or **OpenTelemetry** for latency analysis.

---

## **6. Escalation Path**
If issues persist:
1. **Check Host System Logs**
   - `journalctl -u docker`
   - `dmesg | grep docker`
2. **Engage Community**
   - [Docker Forums](https://forums.docker.com/)
   - [Kubernetes Slack](https://slack.k8s.io/)
3. **Open Issues**
   - File bugs on [Docker GitHub](https://github.com/moby/moby/issues) or [Kubernetes GitHub](https://github.com/kubernetes/kubernetes/issues).

---

## **7. Summary Checklist for Quick Resolution**
| **Step**               | **Action**                                  |
|------------------------|--------------------------------------------|
| 1. **Identify Symptom** | Check logs (`docker logs`, `kubectl describe`) |
| 2. **Reproduce Locally** | Run a minimal test container               |
| 3. **Check Dependencies** | Verify `ENTRYPOINT`, `CMD`, environment vars |
| 4. **Inspect Resources** | CPU, memory, disk with `docker stats`       |
| 5. **Network Debugging** | Test connectivity inside container          |
| 6. **Permissions**      | Check `chmod`, `chown`, SELinux/AppArmor     |
| 7. **Rollback**         | Use previous image tag if possible          |
| 8. **Prevent Future Issues** | Add health checks, resource limits |

---

## **Final Notes**
- **Start small:** Isolate the issue (e.g., test with a minimal `Dockerfile`).
- **Use existing tools:** Leverage `docker inspect`, `kubectl debug`, and logging systems.
- **Automate prevention:** Integrate scanning, testing, and monitoring into your pipeline.

By following this guide, you should be able to **diagnose and resolve 90% of container issues within minutes**. For complex problems, refer to the official documentation ([Docker](https://docs.docker.com/), [Kubernetes](https://kubernetes.io/docs/home/)) or community resources.