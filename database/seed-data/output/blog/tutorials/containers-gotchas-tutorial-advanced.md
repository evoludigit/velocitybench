```markdown
---
title: "Containers Gotchas: 10 Hidden Pitfalls Every Backend Engineer Should Know"
date: 2023-11-15
tags: ["distributed systems", "containers", "Docker", "Kubernetes", "devops", "backend engineering"]
author: "Alex Carter"
description: "Docker and Kubernetes are powerful, but they introduce subtle gotchas that even experienced engineers overlook. Learn the 10 critical pitfalls and how to handle them."
---

# **Containers Gotchas: 10 Hidden Pitfalls Every Backend Engineer Should Know**

Containers have revolutionized how we build, deploy, and scale applications. Docker and Kubernetes have become cornerstones of modern DevOps, enabling reproducibility, portability, and efficient resource utilization. But while containers solve many problems, they also introduce new challenges—some subtle, some critical—that can derail even well-designed systems.

As a senior backend engineer, you’ve likely worked with containers extensively. You know how to spin up a container, deploy it to Kubernetes, and configure networking and storage. But have you considered the gotchas? The edge cases that bite when your app behaves differently in production than in your dev environment? The performance bottlenecks that emerge only at scale? The debugging nightmares caused by misconfigured secrets or misaligned container lifecycles?

This guide dives deep into **10 critical containers gotchas**—pitfalls that even experienced engineers often overlook. We’ll explore real-world examples, tradeoffs, and actionable solutions to help you build more robust containerized applications.

---

## **The Problem: Why Containers Introduce Gotchas**

Containers abstract away many system-level details, which is great for development but can lead to blind spots. For instance:
- **Environment parity**: A container might run fine locally but fail silently in production due to differences in kernel versions, CPU caching, or networking behavior.
- **Resource constraints**: A container’s memory or CPU limits might prevent it from hitting actual hardware-level performance issues during testing.
- **Statefulness assumptions**: Statelessness is the ideal, but real-world apps often need temporary or persistent storage, leading to surprises when containers restart or scale.
- **Debugging complexity**: Containers run in isolated environments, making logging, profiling, and error tracing harder than monolithic apps.

These gotchas often manifest late in development—after deployment—or when scaling to production. The goal of this post is to **preemptively expose these issues** so you can design for them upfront.

---

## **The Solution: Proactive Strategies for Containers Gotchas**

The best way to handle gotchas is to **anticipate them**. This requires:
1. **Testing in a production-like environment** (e.g., staging clusters with resource limits mirroring production).
2. **Instrumenting containers** for observability (logs, metrics, traces).
3. **Designing for failure** (e.g., graceful shutdowns, retry logic, circuit breakers).
4. **Automating recovery** (e.g., liveness probes, readiness checks).
5. **Documenting assumptions** (e.g., "This container assumes ephemeral storage is `/tmp`").

Below, we’ll explore **10 specific gotchas** and how to tackle them.

---

## **1. The "Works on My Machine" Fallacy**

### **The Problem**
You build a container locally with a specific Dockerfile, and it works perfectly. But when deployed to Kubernetes, the app crashes due to missing dependencies or environment variables. Why? Because your local system and the remote environment differ in:
- Installed system libraries (e.g., `glibc` version).
- Kernel features (e.g., `epoll` support).
- User permissions (e.g., `/tmp` ownership).

### **Solution: Use Multi-Stage Builds and Scanning**
To avoid this, **treat your container as a black box**—don’t assume anything about the host. Here’s how:

#### **Example: Multi-Stage Dockerfile (Python App)**
```dockerfile
# Stage 1: Build
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

#### **Key Takeaways**
✅ Use **multi-stage builds** to reduce image size and avoid bloating the runtime.
✅ **Scan images** for vulnerabilities using tools like [Trivy](https://aquasecurity.github.io/trivy/) or [Clair](https://github.com/quay/clair).
✅ **Test on CI** with a build stage that mirrors production (e.g., same base image, same OS).

---

## **2. The "OOM Killer" Surprise**

### **The Problem**
Your app runs out of memory, but instead of crashing gracefully, the OS’s **OOM Killer** terminates it abruptly. This happens when:
- You set a **high memory limit** in Kubernetes (`resources.limits.memory`), but the app leaks memory over time.
- The OOM Killer triggers before your app can exit cleanly, leaving dangling connections or orphaned processes.

### **Solution: Configure Proper Limits and Graceful Shutdowns**
#### **Example: Kubernetes Pod with Memory Limits + Liveness Probe**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-app
    image: my-app:latest
    resources:
      limits:
        memory: "512Mi"
        cpu: "500m"
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 5
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 2
```

#### **Code Example: Graceful Shutdown in Node.js**
```javascript
// app.js
const server = require('http').createServer();
const gracefulShutdown = () => {
  server.close(() => process.exit(0));
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

server.listen(3000, () => {
  console.log('Server running');
});
```

#### **Key Takeaways**
✅ **Set `memory` limits lower than your app can leak** to trigger OOM before critical failures.
✅ **Use `livenessProbe` + `readinessProbe`** to detect and recover from crashes.
✅ **Implement graceful shutdowns** (e.g., `SIGTERM` handlers) to avoid abrupt terminations.

---

## **3. The "Disk Space Explosion" Gotcha**

### **The Problem**
Your container writes logs, caches, or temporary files to `/tmp` or a volume. Over time, this fills up the disk, causing:
- **Crashes** when the system runs out of space.
- **Noisy neighbor problems** in shared storage (e.g., EBS volumes in EKS).

### **Solution: Clean Up and Set Limits**
#### **Bash Example: Clean Up `/tmp` on Startup**
```dockerfile
# Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y inotify-tools
COPY entrypoint.sh /
CMD ["/entrypoint.sh"]
```

```bash
#!/bin/sh
# entrypoint.sh
cleanup_tmp() {
  find /tmp -type f -delete
  find /tmp -type d -empty -delete
}
trap cleanup_tmp EXIT

# Start your app
exec "$@"
```

#### **Kubernetes Example: Persistent Volume with Retention Policy**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-logs
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
  volumeMode: Filesystem
```

#### **Key Takeaways**
✅ **Avoid `/tmp` for persistent data**—use dedicated volumes.
✅ **Set retention policies** for logs (e.g., rotate with `logrotate`).
✅ **Use `lifecycleHooks` in Kubernetes** to clean up on pod termination.

---

## **4. The "Networking Black Hole" Gotcha**

### **The Problem**
Your container connects to a database or external API, but requests **time out or fail silently**. Common causes:
- **Network policies** blocking traffic.
- **DNS resolution failures** (e.g., `kube-dns` misconfiguration).
- **Firewall rules** in the cloud provider (e.g., AWS Security Groups).

### **Solution: Debug with Network Policies and Observability**
#### **Kubernetes Example: NetworkPolicy for Security**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db-access
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

#### **Debugging Steps**
1. **Test connectivity inside the container**:
   ```bash
   kubectl exec -it my-pod -- sh
   ping database-service
   nc -zv database-service 5432
   ```
2. **Check logs**:
   ```bash
   kubectl logs my-pod
   ```
3. **Use `kubectl describe` for network issues**:
   ```bash
   kubectl describe pod my-pod | grep Network
   ```

#### **Key Takeaways**
✅ **Default-deny networking** and whitelist only necessary traffic.
✅ **Test DNS resolution** inside containers (e.g., `nslookup`).
✅ **Set up network policies** to isolate traffic.

---

## **5. The "Configuration Drift" Gotcha**

### **The Problem**
Your app relies on environment variables or config maps, but:
- **Secrets are hardcoded** in the Dockerfile.
- **Configs change between dev/staging/prod**, causing inconsistencies.
- **Dynamic configs** (e.g., feature flags) aren’t updated without a redeploy.

### **Solution: Use ConfigMaps and Secrets Properly**
#### **Kubernetes Example: ConfigMap + Secret**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DB_HOST: "database.example.com"
  DEBUG: "true"

# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DB_PASSWORD: BASE64_ENCODED_PASSWORD
```

#### **Docker Example: Mount ConfigMaps as Files**
```dockerfile
FROM alpine:latest
COPY ./app-config.yaml /etc/app-config.yaml
ENV APP_CONFIG=/etc/app-config.yaml
```

#### **Key Takeaways**
✅ **Never bake secrets in images**—use Kubernetes Secrets or Vault.
✅ **Use ConfigMaps for non-sensitive configs** (e.g., feature flags).
✅ **Validate configs at startup** (e.g., schema checks).

---

## **6. The "Sidecar Madness" Gotcha**

### **The Problem**
You add a sidecar container (e.g., for logging, monitoring, or proxying), but:
- **Resource competition** causes performance degradation.
- **Complexity spikes** as you add more sidecars.
- **Debugging becomes harder** with multiple processes.

### **Solution: Consolidate or Replace Sidecars**
#### **Example: Use a Single Sidecar for Logging + Metrics**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
      - name: logging-sidecar
        image: fluentd:latest
        volumeMounts:
        - mountPath: /var/log
          name: app-logs
      volumes:
      - name: app-logs
        emptyDir: {}
```

#### **Alternative: Use Horizontal Pod Autoscaler (HPA) + Prometheus**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### **Key Takeaways**
✅ **Avoid overusing sidecars**—consolidate where possible.
✅ **Use HPA + metrics** instead of sidecars for scaling.
✅ **Consider serverless alternatives** (e.g., Knative) if sidecars are too complex.

---

## **7. The "Stateful App in a Stateless World" Gotcha**

### **The Problem**
Your app needs persistence (e.g., Redis, SQLite), but:
- **Containers are ephemeral**—restarts wipe data.
- **StatefulSets are complex** to manage.
- **Backups are manual** and error-prone.

### **Solution: Use StatefulSets + Persistent Volumes**
#### **Kubernetes Example: StatefulSet with Persistent Volume**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:6
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi
```

#### **Key Takeaways**
✅ **Use StatefulSets for stateful apps** (e.g., databases).
✅ **Automate backups** with tools like Velero.
✅ **Consider managed services** (e.g., AWS RDS) if self-managed storage is too complex.

---

## **8. The "Init Container Delays" Gotcha**

### **The Problem**
You use init containers (e.g., to download dependencies), but:
- **Pods remain pending** if init containers fail.
- **Slow init times** cause high latency in scaling.

### **Solution: Optimize Init Containers**
#### **Kubernetes Example: Parallel Init Containers**
```yaml
spec:
  initContainers:
  - name: download-deps
    image: busybox
    command: ["wget", "-O", "/deps.tar.gz", "https://example.com/deps.tar.gz"]
    volumeMounts:
    - name: deps
      mountPath: /deps
  - name: extract-deps
    image: busybox
    command: ["tar", "-xzf", "/deps/deps.tar.gz", "-C", "/deps"]
    volumeMounts:
    - name: deps
      mountPath: /deps
  containers:
  - name: app
    image: my-app:latest
    volumeMounts:
    - name: deps
      mountPath: /app/deps
  volumes:
  - name: deps
    emptyDir: {}
```

#### **Key Takeaways**
✅ **Run init containers in parallel** where possible.
✅ **Set timeouts** for init containers.
✅ **Avoid lengthy init steps**—pre-pull dependencies.

---

## **9. The "Unbounded Retries" Gotcha**

### **The Problem**
Your app retries failed requests (e.g., database connections) but:
- **Exponential backoff isn’t implemented**, causing thundering herds.
- **Retries never stop**, filling up memory or crashing the app.

### **Solution: Implement Circuit Breakers**
#### **Go Example: Using `circuitbreaker` Package**
```go
package main

import (
	"github.com/jasonjwen/go-circuits"
	"time"
)

func main() {
	cb := circuits.NewCircuit(
		circuits.WithMaxFailures(5),
		circuits.WithFailureDuration(30*time.Second),
		circuits.WithSuccessThreshold(2),
	)

	// Simulate a DB call with retry logic
	err := cb.Execute(func() error {
		// Your DB call here
		return tryDatabaseConnection()
	})

	if err != nil {
		// Handle failure
	}
}
```

#### **Key Takeaways**
✅ **Use circuit breakers** (e.g., Hystrix, Resilience4j in Java; `go-circuits` in Go).
✅ **Set retries with jitter** to avoid synchronized retries.
✅ **Log retry attempts** for debugging.

---

## **10. The "Vendor Lock-in" Gotcha**

### **The Problem**
You use Kubernetes-specific features (e.g., `kubectl` commands, custom controllers) but:
- **Deployment becomes harder** if you need to switch clouds.
- **Costs skyrocket** due to proprietary services.

### **Solution: Design for Portability**
#### **Example: Use Helm Charts for Multi-Cloud Deployments**
```yaml
# Chart.yaml (for Helm)
apiVersion: v2
name: my-app
description: A Helm chart for Kubernetes
version: 0.1.0
appVersion: "1.0"
```

#### **Key Takeaways**
✅ **Avoid tight coupling** to Kubernetes-specific features.
✅ **Use CNCF tools** (e.g., Prometheus, Jaeger) instead of cloud-specific ones.
✅ **Document cloud dependencies** in architectures.

---

## **Common Mistakes to Avoid**

1. **Assuming all containers are identical**:
   - Containers run in different environments (e.g., different kernel versions). Test on the **exact** runtime you’ll use in production.

2. **Ignoring resource limits**:
   - Always set `requests` and `limits` for CPU/memory. Without them, you’ll be at the mercy of the