# **Debugging Containers Integration: A Troubleshooting Guide**
*For Backend Engineers*

Containers (Docker, Kubernetes, etc.) provide isolation, portability, and scalability, but integrating them with applications, databases, and other services can introduce complexity. This guide focuses on quickly diagnosing and resolving **containers integration issues** in microservices, orchestrated environments (K8s), and monolithic applications with containerized dependencies.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down the issue:

| **Symptom**                          | **Possible Causes**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------------|
| Container fails to start (`OOMKilled`, `Exit Code 137`) | Memory limits exceeded, CPU throttling, missing dependencies, or misconfigured health checks. |
| Application crashes on startup       | Missing environment variables, incorrect volume mounts, or broken dependencies.     |
| Slow response times                  | Resource starvation (CPU/memory), network latency, or misconfigured load balancers. |
| `Error: Cannot connect to DB`        | Incorrect service names in connection strings, DNS resolution issues, or network policy misconfig. |
| Logs show `404` or `502 Bad Gateway` | Misconfigured ingress, reverse proxy, or service discovery.                        |
| Container logs show `Permission denied` | Incorrect user permissions or SELinux/AppArmor restrictions.                     |
| `ImagePullBackOff` in Kubernetes    | Private registry auth issues, corrupt image layers, or pod anti-affinity conflicts. |
| **Other**                            | Check `docker logs <container>`, `kubectl describe pod`, and network diagnostics.    |

---

## **2. Common Issues and Fixes**

### **2.1 Container Crashes on Startup**
#### **Symptom:**
Container exits immediately with `Exit Code 137` (OOMKilled) or `Exit Code 143` (post-stop signal).

#### **Root Cause:**
- **Memory/CPU limits exceeded** (common in Kubernetes).
- **Missing critical environment variables** (e.g., `DB_HOST`).
- **Dependency not loaded** (e.g., missing `.env` file in a volume).

#### **Fixes:**
**A. Check Resource Limits (K8s)**
```yaml
# In your Deployment/Pod spec:
resources:
  limits:
    memory: "512Mi"  # Increase if app needs more
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "200m"
```
**Verify with:**
```bash
kubectl describe pod <pod-name> | grep Limits
```

**B. Validate Environment Variables**
- Ensure all required vars are set in:
  - Docker `ENV` directives (`Dockerfile`).
  - K8s `env` or `envFrom` (ConfigMaps/Secrets).
  - CI/CD pipeline (if variables are dynamic).

**Example (K8s ConfigMap):**
```yaml
envFrom:
- configMapRef:
    name: app-config
```

**C. Debug Missing Dependencies**
- If logs show `Cannot find module X`, ensure:
  - The file is mounted as a volume.
  - The Docker image includes the dependency (e.g., `npm install` in a build step).

**Example (Docker Volume Mount):**
```dockerfile
VOLUME /path/to/dependencies
```

---

### **2.2 Connection Issues (DB, API, etc.)**
#### **Symptom:**
Application logs show `Connection refused` or `Timeout` when trying to reach another service.

#### **Root Cause:**
1. **Incorrect service name** (K8s DNS vs. hostnames).
2. **Network policies blocking traffic**.
3. **Service not exposed** (e.g., missing `ports` in K8s Service).
4. **DNS resolution failure** (e.g., `kube-dns` not working).

#### **Fixes:**
**A. Verify Service Discovery (K8s)**
- Use the **service name** (not `localhost` or `127.0.0.1`) in connections.
- Example DB connection string:
  ```plaintext
  jdbc:postgresql://postgres-service:5432/dbname
  ```
- Test connectivity:
  ```bash
  kubectl exec -it <pod> -- curl postgres-service:5432
  ```

**B. Check Network Policies**
```yaml
# Example: Allow traffic from app-service to db-service
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-allow-app
spec:
  podSelector:
    matchLabels:
      app: db
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: app-service
    ports:
    - protocol: TCP
      port: 5432
```

**C. Expose Services Correctly (K8s)**
```yaml
# Ensure the Service type is LoadBalancer/NodePort if needed
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: app
  type: ClusterIP  # Default (internal only); use LoadBalancer for external access
```

---

### **2.3 Slow Performance**
#### **Symptom:**
High latency, timeouts, or `5xx` errors under load.

#### **Root Cause:**
1. **Resource starvation** (CPU/memory throttling).
2. **Disk I/O bottlenecks** (slow storage or `tmpfs` issues).
3. **Network overhead** (too many pods communicating via API instead of shared storage).

#### **Fixes:**
**A. Monitor Resource Usage**
```bash
kubectl top pods
kubectl describe pod <pod> | grep -i "limits\|requests"
```

**B. Optimize Disk I/O**
- Use **read-only volumes** where possible.
- Avoid writing to `/tmp` (use `emptyDir` with `medium: Memory` for ephemeral data).

**Example (Optimized Disk Mount):**
```yaml
volumes:
- name: app-data
  emptyDir:
    medium: Memory
    sizeLimit: 100Mi
```

**C. Reduce Network Chatter**
- **Co-locate related services** (same node in K8s).
- Use **shared databases** instead of per-pod databases.
- Implement **caching** (Redis) for frequent queries.

---

### **2.4 Permission Denied Errors**
#### **Symptom:**
Logs show `Permission denied` when writing files or accessing ports.

#### **Root Cause:**
1. **Incorrect user in Dockerfile**:
   ```dockerfile
   USER root  # Default; avoid for security.
   USER 1000   # Match host user IDs if needed.
   ```
2. **SELinux/AppArmor blocking access**.
3. **Volume mounts with wrong ownership**.

#### **Fixes:**
**A. Set Correct User in Dockerfile**
```dockerfile
FROM ubuntu:22.04
RUN useradd -m myuser && chown -R myuser /app
USER myuser
WORKDIR /app
```

**B. Disable SELinux (Temporarily for Testing)**
```bash
# Inside container:
setenforce 0  # Disable SELinux (not recommended for production)
```
**Permanent fix:**
Edit `/etc/selinux/config` and set `SELINUX=disabled`.

**C. Fix Volume Permissions**
```bash
# Before running the container:
chmod -R 755 /path/to/mount
```

---

### **2.5 Image Pull Errors (`ImagePullBackOff`)**
#### **Symptom:**
K8s fails to pull images with `ImagePullBackOff`.

#### **Root Cause:**
1. **Private registry auth missing**.
2. **Corrupted image layers**.
3. **Image not found** (incorrect tag/repo).

#### **Fixes:**
**A. Configure ImagePullSecrets (Private Registry)**
```yaml
spec:
  imagePullSecrets:
  - name: regcred
```
Create a secret:
```bash
kubectl create secret docker-registry regcred \
  --docker-server=<registry-url> \
  --docker-username=<user> \
  --docker-password=<password> \
  --docker-email=<email>
```

**B. Verify Image Tag**
- Ensure the `image:tag` in Deployment matches the registry.
- Example:
  ```yaml
  image: myrepo/myapp:v1.2.3  # Must exist in registry
  ```

**C. Check Image Layers**
```bash
docker inspect <image> | grep -i "Layers"
```
If layers are corrupted, rebuild the image.

---

## **3. Debugging Tools and Techniques**

### **3.1 Core Debugging Commands**
| **Tool/Command**               | **Purpose**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|
| `docker logs <container>`       | View container logs (real-time with `-f`).                                  |
| `kubectl describe pod <pod>`    | Check pod events, conditions, and resource limits.                            |
| `kubectl exec -it <pod> -- sh`  | Shell into a running container.                                             |
| `curl http://localhost:port`    | Test connectivity inside a container.                                        |
| `dig <service-name>`            | Test DNS resolution (K8s uses CoreDNS).                                      |
| `kubectl get events --sort-by='.metadata.creationTimestamp'` | Check cluster-wide events.            |
| `kubectl top pods --containers` | Monitor CPU/memory usage.                                                   |

### **3.2 Advanced Debugging**
- **Network Diagnostics**:
  ```bash
  # Check connectivity inside a pod
  kubectl exec -it <pod> -- ping postgres-service
  kubectl exec -it <pod> -- nc -zv db-service 5432
  ```
- **CPU Profiling**:
  ```bash
  kubectl top pods --containers  # Check CPU usage
  kubectl describe pod <pod> | grep -i "cpu"
  ```
- **Disk I/O**:
  ```bash
  kubectl exec -it <pod> -- iostat -x 1
  ```

### **3.3 Logging and Monitoring**
- **Centralized Logging**:
  - Use **Loki**, **ELK Stack**, or **Fluentd** to aggregate logs.
- **Distributed Tracing**:
  - Integrate **Jaeger** or **OpenTelemetry** for latency analysis.
- **Metrics**:
  - **Prometheus + Grafana** for real-time monitoring.
  - Example PromQL query for container restarts:
    ```plaintext
    kube_pod_container_status_restarts_total
    ```

---

## **4. Prevention Strategies**
### **4.1 Best Practices for Containers Integration**
1. **Use Health Checks**
   - Define `livenessProbe` and `readinessProbe` in K8s:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 30
       periodSeconds: 10
     ```
2. **Optimize Image Size**
   - Multi-stage builds reduce attack surface and deployment time.
   ```dockerfile
   # Build stage
   FROM node:18 as builder
   WORKDIR /app
   COPY . .
   RUN npm install && npm run build

   # Runtime stage
   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   ```
3. **Implement Resource Requests/Limits**
   - Prevent noisy neighbors:
     ```yaml
     resources:
       requests:
         cpu: "100m"
         memory: "256Mi"
       limits:
         cpu: "500m"
         memory: "512Mi"
     ```
4. **Use ConfigMaps/Secrets**
   - Avoid hardcoding secrets in images:
     ```yaml
     envFrom:
     - secretRef:
         name: db-secret
     ```
5. **Network Policies**
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

### **4.2 CI/CD Integration Checks**
- **Pre-deployment Testing**:
  - Run **integration tests** in a staging environment mirroring production.
  - Use **Chaos Engineering** (e.g., Gremlin) to test failure scenarios.
- **Rollback Strategies**:
  - Enable **automatic rollback** on failed deployments:
    ```yaml
    strategy:
      type: RollingUpdate
      rollingUpdate:
        maxSurge: 1
        maxUnavailable: 1
    ```

### **4.3 Documentation and Runbooks**
- **Maintain a Containers Playbook**:
  - Document:
    - Image versions and rebuild triggers.
    - Network architecture (e.g., service mesh vs. direct pods).
    - Common failures and fixes.
- **Automate Incident Response**:
  - Use **Slack alerts** or **PagerDuty** for critical failures.
  - Example alert rule (Prometheus):
    ```plaintext
    ALERT HighPodRestartRate
      IF kube_pod_container_status_restarts_total{namespace="my-app"} > 3
      FOR 5m
      LABELS {severity="critical"}
      ANNOTATIONS {
        summary="Pod {{ $labels.pod }} is restarting too often",
        description="Pod {{ $labels.pod }} has restarted {{ $value }} times in the last 5 minutes."
      }
    ```

---

## **5. Summary Checklist for Quick Resolution**
| **Step**                     | **Action**                                                                 |
|------------------------------|----------------------------------------------------------------------------|
| **Container fails to start** | Check logs, resource limits, and environment vars.                        |
| **Connection issues**        | Verify service names, network policies, and DNS.                           |
| **Slow performance**         | Monitor CPU/memory, optimize disk I/O, and reduce network overhead.         |
| **Permission denied**        | Set correct user in Dockerfile, adjust SELinux, or fix volume permissions.|
| **Image pull errors**        | Ensure proper ImagePullSecrets and correct image tags.                     |
| **General debugging**        | Use `kubectl describe`, `docker logs`, and network diagnostic tools.       |

---
**Final Tip**: Start with **logs and metrics**, then narrow down to **network/config issues**. Containers integration is often about **correct configuration**, not complex bugs.