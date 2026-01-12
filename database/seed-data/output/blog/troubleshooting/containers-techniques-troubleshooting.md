# **Debugging Container Techniques: A Troubleshooting Guide**

## **Introduction**
Containers (Docker, Kubernetes, and related tools) are widely used for deploying, scaling, and managing applications in isolated environments. While they provide efficiency and consistency, container-related issues can arise due to misconfigurations, dependency problems, runtime errors, or networking issues. This guide provides a structured approach to diagnosing and resolving common containerization problems.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms match your issue:

### **General Container Issues**
- [ ] Containers fail to start (`docker run` hangs or crashes immediately).
- [ ] Application crashes after startup (logs show errors but container doesn’t exit).
- [ ] High resource usage (CPU, memory) leading to failures.
- [ ] Containers are unable to communicate with each other or external services.
- [ ] Persistent volumes/data is lost or corrupted.
- [ ] Slow image pulls or builds.

### **Kubernetes-Specific Issues**
- [ ] Pods are stuck in `Pending`, `CrashLoopBackOff`, or `Error` states.
- [ ] Services fail to route traffic correctly.
- [ ] Deployments/StatefulSets fail to scale or roll out changes.
- [ ] Horizontal Pod Autoscaler (HPA) does not trigger scaling.
- [ ] Logs indicate `OOMKilled` (Out-of-Memory) errors.

### **Networking & Storage Issues**
- [ ] Containers can’t reach external APIs (DNS resolution fails).
- [ ] Volume mounts fail (permissions, path errors).
- [ ] Sidecar containers (e.g., for logging/monitoring) don’t integrate properly.

---

## **2. Common Issues & Fixes (With Code Examples)**

### **2.1 – Container Fails to Start**
**Symptoms:**
- `docker run` exits immediately with no logs.
- `docker logs [container]` shows no output.

**Possible Causes & Fixes:**

#### **A. Missing Dependencies**
**Issue:** The container lacks required libraries or binaries.
**Debugging Steps:**
1. Run the container interactively:
   ```bash
   docker run -it --rm [image] /bin/sh
   ```
2. Check if the required command exists:
   ```sh
   which nginx  # Example for Nginx
   ```
3. If missing, rebuild the image with dependencies:
   ```dockerfile
   FROM ubuntu:latest
   RUN apt-get update && apt-get install -y nginx  # Fix missing nginx
   ```

#### **B. Incorrect User or Permissions**
**Issue:** The app runs as a non-root user but lacks permissions.
**Fix:**
Modify `USER` in `Dockerfile` or set proper permissions:
```dockerfile
USER root  # Temporarily switch to root
RUN chmod -R 755 /path/to/app
USER 1000   # Switch back to non-root
```

---

### **2.2 – Application Crashes After Startup**
**Symptoms:**
- Container starts, but the app crashes (e.g., `Segmentation Fault`, `500 errors`).
- Logs show stack traces or missing configs.

**Debugging Steps:**
1. **Inspect logs:**
   ```bash
   docker logs [container] --tail 50
   ```
2. **Common Fixes:**
   - **Missing Config Files:** Mount a config file:
     ```bash
     docker run -v /host/config:/app/config [image]
     ```
   - **Environment Variables:** Set them explicitly:
     ```bash
     docker run -e DB_HOST=db -e DB_USER=user [image]
     ```
   - **Test in Development:** Run locally first to verify settings.

---

### **2.3 – High Resource Usage & OOMKills**
**Symptoms:**
- Pods restart due to `OOMKilled` in Kubernetes.
- CPU/memory limits not enforced.

**Debugging & Fixes:**
1. **Check resource limits:**
   ```bash
   # For Docker
   docker stats [container]

   # For Kubernetes
   kubectl describe pod [pod-name] | grep -i limits
   ```
2. **Adjust limits:**
   - **Docker:**
     ```bash
     docker run --memory=1g --cpus=1 [image]
     ```
   - **Kubernetes (YAML):**
     ```yaml
     resources:
       limits:
         memory: "1Gi"
         cpu: "1"
     ```

---

### **2.4 – Networking Issues (Containers Can’t Communicate)**
**Symptoms:**
- Containers can’t reach databases or APIs.
- `curl` or `wget` fails inside the container.

**Debugging Steps:**
1. **Test DNS resolution:**
   ```bash
   docker exec -it [container] nslookup google.com
   ```
2. **Check firewall/network policies:**
   ```bash
   # For Kubernetes, verify NetworkPolicy
   kubectl describe networkpolicy default-deny
   ```
3. **Fixes:**
   - **Explicitly set DNS:**
     ```bash
     docker run --dns 8.8.8.8 [image]
     ```
   - **Use Kubernetes Services:**
     ```yaml
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

---

### **2.5 – Persistent Data Loss**
**Symptoms:**
- Volume mounts disappear after container restarts.
- Database data is lost.

**Debugging & Fixes:**
1. **Verify volume mount:**
   ```bash
   docker volume ls
   docker inspect [volume] | grep Mountpoint
   ```
2. **Use named volumes (recommended):**
   ```bash
   docker run -v my-named-volume:/data [image]
   ```
3. **For Kubernetes:**
   ```yaml
   volumes:
   - name: my-persistent-volume
     persistentVolumeClaim:
       claimName: my-pvc
   ```

---

## **3. Debugging Tools & Techniques**
### **3.1 – Logging & Inspection**
- **Docker:**
  ```bash
  docker logs [container]      # View logs
  docker inspect [container]   # Inspect metadata
  docker exec -it [container] bash  # Enter container
  ```
- **Kubernetes:**
  ```bash
  kubectl logs [pod-name]          # Logs
  kubectl describe pod [pod-name]  # Debug details
  kubectl exec -it [pod-name] bash  # Execute commands
  ```

### **3.2 – Network Troubleshooting**
- **Traceroute:**
  ```bash
  docker exec [container] traceroute google.com
  ```
- **Netstat:**
  ```bash
  docker exec [container] netstat -tulnp
  ```
- **Kubernetes Port Forwarding:**
  ```bash
  kubectl port-forward svc/my-service 8080:80
  ```

### **3.3 – Performance Profiling**
- **CPU Profile:**
  ```bash
  docker run --cpu-quota=50000 --cpuset-cpus=0 [image]  # Limit CPU
  ```
- **Memory Profiling:**
  ```bash
  docker stats --no-stream  # Check memory usage
  ```

---

## **4. Prevention Strategies**
### **4.1 – Best Practices for Docker**
- **Use `.dockerignore`** to exclude unnecessary files.
- **Multi-stage builds** to reduce image size.
- **Regularly update base images** (e.g., `nginx:latest` → `nginx:1.25`).

### **4.2 – Best Practices for Kubernetes**
- **Resource Requests/Limits** (avoid OOMKills).
- **Liveness/Readiness Probes** for self-healing.
- **Horizontal Pod Autoscaler (HPA)** for scaling.

### **4.3 – CI/CD Integration**
- **Automated Testing:** Run containers in CI before production.
- **Rolling Updates:** Gradually deploy changes to avoid downtime.

### **4.4 – Monitoring & Alerts**
- **Prometheus + Grafana** for container metrics.
- **Log Aggregation** (ELK Stack, Loki).
- **Alert on Critical Failures** (e.g., `CrashLoopBackOff`).

---

## **Conclusion**
Debugging container issues requires a methodical approach:
1. **Check logs and metadata** (`docker logs`, `kubectl describe`).
2. **Test networking** (`curl`, `nslookup`).
3. **Adjust resource limits** if needed.
4. **Prevent future issues** with proper configs, monitoring, and CI/CD.

By following this guide, you can quickly identify and resolve containerization problems while maintaining a stable deployment pipeline.

---
**Need More Help?**
- [Docker Troubleshooting Guide](https://docs.docker.com/troubleshoot/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)