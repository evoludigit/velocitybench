# **[Pattern] Containers Maintenance Reference Guide**

## **Overview**
The **Containers Maintenance** pattern ensures efficient lifecycle management of containerized applications, including orchestration, scaling, health monitoring, logging, and cleanup. This pattern provides best practices for maintaining container environments in Kubernetes, Docker Swarm, or standalone Docker setups, addressing resource optimization, resilience, and operational efficiency. It covers essential operations like **container restart policies, resource limits, logging, garbage collection, and rollback mechanisms**, helping teams minimize downtime and maximize resource usage.

---

## **Key Concepts & Implementation Details**
### **1. Container Lifecycle Management**
Ensure containers are **deployed, monitored, and terminated** optimally.
- **Restart Policies**:
  - `no` (default): Container runs once and exits.
  - `always` (default in Kubernetes/Pods): Restart if the container crashes.
  - `on-failure` (Kubernetes): Restart only after failures (configurable retries).
  - `unless-stopped`: Always restart unless manually stopped.
- **Health Checks**:
  - Configure `HEALTHCHECK` in Docker or `livenessProbe`/`readinessProbe` in Kubernetes.
  - Example (Dockerfile):
    ```dockerfile
    HEALTHCHECK --interval=30s --timeout=3s \
      CMD curl -f http://localhost:8080/health || exit 1
    ```

### **2. Resource Optimization**
Prevent resource starvation and improve performance.
| **Resource**       | **Description**                                                                 | **Implementation**                                                                 |
|--------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **CPU Limits**     | Max CPU a container can use (in millicores or shares).                          | Kubernetes: `resources.limits.cpu: "500m"`                                         |
| **Memory Limits**  | Max RAM a container can consume (e.g., `1G`).                                  | Kubernetes: `resources.limits.memory: "1Gi"`                                      |
| **Storage Limits** | Disk space allocation (e.g., `10Gi`).                                          | Docker volumes with `--mount` or Kubernetes `volumeClaimTemplates`.               |
| **Graceful Shutdown** | Time (in seconds) to shut down gracefully before hard kill.                    | Kubernetes: `terminationGracePeriodSeconds: 30`                                   |

### **3. Logging & Monitoring**
Collect and analyze logs and metrics for debugging and performance tuning.
- **Log Drivers** (Docker):
  - `json-file` (default): Stores logs locally.
  - `journald`: Integrates with systemd.
  - `syslog`: Forwards logs to a central syslog server.
  - Example:
    ```bash
    docker run --log-driver=json-file --log-opt max-size=10m my-app
    ```
- **Metrics Collection**:
  - Tools: Prometheus, Grafana, Datadog.
  - Example (Kubernetes `HorizontalPodAutoscaler`):
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

### **4. Garbage Collection & Cleanup**
Remove unused containers, images, and networks to reclaim space.
- **Docker Commands**:
  ```bash
  # Remove stopped containers
  docker container prune

  # Remove dangling images (unreferenced)
  docker image prune

  # Remove all unused objects (containers, networks, images)
  docker system prune -a
  ```
- **Kubernetes**:
  Use `kubectl` to delete stale resources:
  ```bash
  # Delete incomplete Pods
  kubectl delete pod --field-selector=status.phase==Pending

  # Clean up unused PersistentVolumes
  kubectl get pv | grep "Released" | awk '{print $1}' | xargs kubectl delete pv
  ```

### **5. Rollback & Recovery**
Revert to a previous stable state if deployments fail.
- **Kubernetes Rollbacks**:
  ```bash
  # Rollback a Deployment to the last known good revision
  kubectl rollout undo deployment/my-app

  # Specify a revision
  kubectl rollout undo deployment/my-app --to-revision=2
  ```
- **Docker Rollbacks**:
  - Use `docker run --name my-app-v2 ...` and monitor before promoting.

### **6. Scaling & Auto-Scaling**
Adjust container instances based on demand.
- **Manual Scaling (Kubernetes)**:
  ```bash
  kubectl scale deployment/my-app --replicas=10
  ```
- **Autoscaling (Kubernetes)**:
  Configure `HorizontalPodAutoscaler` (HPA) based on CPU/memory or custom metrics.

---

## **Schema Reference**
| **Component**               | **Fields**                                                                                     | **Example Value**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Docker Container**        | `name`, `image`, `restart`, `ports`, `volumes`, `healthcheck`                                | `{name: "web", image: "nginx:latest", restart: "always", healthcheck: {...}}`       |
| **Kubernetes Pod**          | `metadata.name`, `spec.containers[*].name`, `resources.limits`, `livenessProbe`             | `{metadata.name: "web-pod", spec.containers: [{name: "nginx", image: "nginx"}]}`  |
| **Docker Network**          | `name`, `driver`, `ipamConfig`                                                               | `{name: "my-net", driver: "bridge", ipamConfig: {subnet: "172.20.0.0/16"}}`     |
| **Kubernetes Deployment**   | `spec.replicas`, `strategy`, `rollbackTo`, `template.spec.containers`                       | `{spec.replicas: 3, strategy: {type: "RollingUpdate"}, template.spec.containers: [...]}` |
| **Docker Volume**           | `name`, `driver`, `mountpoint`, `options`                                                   | `{name: "data-volume", driver: "local", mountpoint: "/var/lib/docker/volumes/data-volume"}}` |
| **Log Driver Config**       | `name`, `options` (e.g., `max-size`, `max-file`)                                            | `{name: "json-file", options: {"max-size": "10m", "max-file": "3"}}`              |

---

## **Query Examples**
### **1. List Running Containers with High CPU Usage (Docker)**
```bash
docker stats --format "{{.Container}}" --no-stream | xargs -I {} docker inspect --format='{{json .State.Paused}} {{.Name}}' {} | grep -Eo '[0-9]+(\.[0-9]+)?'
```

### **2. Find Unused Docker Images**
```bash
docker images --filter "dangling=true" --quiet
```

### **3. Check Kubernetes Pods Not Ready**
```bash
kubectl get pods --field-selector=status.phase!=Running
```

### **4. View Logs for a Failed Container (Kubernetes)**
```bash
kubectl logs my-pod --previous
```

### **5. Scale a Deployment Down (Kubernetes)**
```bash
kubectl scale --replicas=0 deployment/my-app
```

---

## **Related Patterns**
1. **[Microservices Orchestration](link)** – Combines containers with service discovery and load balancing.
2. **[Infrastructure as Code (IaC)](link)** – Uses tools like Terraform or Pulumi to define containerized environments declaratively.
3. **[Canary Deployments](link)** – Gradually roll out updates to minimize risk by testing with a subset of users.
4. **[Service Mesh](link)** – Manages inter-service communication (e.g., Istio, Linkerd) for observability and security.
5. **[Immutable Infrastructure](link)** – Treats containers as ephemeral, ensuring consistency via rebuilding instead of patching.
6. **[Blue-Green Deployments](link)** – Instantly switches traffic between two identical environments to reduce downtime.
7. **[Observability Patterns](link)** – Focuses on logging, metrics, and tracing for containerized apps (e.g., Prometheus + Jaeger).

---
**Note:** For production environments, complement this pattern with **secret management (Vault, Kubernetes Secrets)**, **network policies**, and **disaster recovery plans**. Adjust configurations based on workload type (e.g., stateless vs. stateful).