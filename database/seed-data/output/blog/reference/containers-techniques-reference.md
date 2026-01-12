# **[Pattern] Containers Techniques Reference Guide**

---

## **Overview**
Containers Techniques standardizes the deployment, orchestration, and management of **scalable, portable, and isolated** application workloads using containerization technologies like **Docker** and **Kubernetes**. This pattern ensures consistency across environments (dev, staging, production) while optimizing resource utilization and reducing operational overhead.

Key focus areas:
- **Isolation** – Applications run in lightweight, self-contained units with minimal dependencies.
- **Portability** – Containers deploy identically across on-premises, cloud, or hybrid environments.
- **Scalability** – Orchestration tools dynamically allocate resources based on demand.
- **Efficiency** – Shared host kernels reduce resource waste compared to VMs.

This guide covers **core concepts, implementation schemas, query patterns, and supporting tools** for adopting containers techniques effectively.

---

## **1. Key Concepts & Implementation Details**

### **1.1 Core Components**
| **Component**          | **Description**                                                                                     | **Tools/Technologies**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Container**          | Lightweight, standalone executable units bundling code, runtime, and dependencies.               | Docker, Podman, rkt                                                                   |
| **Container Runtime**  | Executes container images and manages lifecycle.                                                     | containerd, CRI-O, runc                                                               |
| **Container Orchestration** | Automates deployment, scaling, and load balancing of containerized apps.                      | Kubernetes (K8s), Docker Swarm, Nomad, Apache Mesos                                      |
| **Image Registry**     | Stores and distributes container images securely.                                                     | Docker Hub, Google Container Registry, AWS ECR, Harbor                                     |
| **Networking**         | Enables inter-container communication and exposes services.                                          | Kubernetes Ingress, Linkerd, Traefik, Calico                                              |
| **Storage**            | Manages persistent data for stateful containers.                                                     | Kubernetes PersistentVolumes, Ceph, Rook, Portworx                                        |
| **Security**           | Enforces access controls, image scanning, and runtime protection.                                    | Kube-bench, Aqua Security, Falco, Notary                                                   |

---

### **1.2 Container Lifecycle Workflow**
A typical containerized application follows this **implementable** sequence:

1. **Build** → Compile code into a **Docker image** (or other container runtime).
   - Example: `docker build -t my-app:v1.0 .`
2. **Store** → Push image to a **registry** (private or public).
   - Example: `docker push my-registry/my-app:v1.0`
3. **Deploy** → Pull and run containers using an **orchestrator** (e.g., K8s).
   - Example: `kubectl apply -f deployment.yaml`
4. **Monitor** → Track performance, logs, and health via **Kubernetes Events** or **Prometheus**.
5. **Scale** → Adjust replicas or node resources dynamically (e.g., `kubectl scale --replicas=5`).
6. **Update** → Roll out new image versions with zero downtime (using **rolling updates**).

---

### **1.3 Common Architectural Patterns**
| **Pattern**               | **Use Case**                                      | **Implementation**                                                                 |
|---------------------------|---------------------------------------------------|------------------------------------------------------------------------------------|
| **Microservices**         | Decoupled services with independent scaling.       | Deploy each service as a separate K8s pod with its own service account.             |
| **Sidecar Containers**    | Extend pod functionality (e.g., logging, caching).| Inject sidecar (e.g., Fluentd for logs) into a pod via `initContainers` or `PodTeMPLATE`. |
| **Init Containers**       | Run pre-flight checks or setup (e.g., DB migrations).| Define in `podSpec` with `initContainers` array.                                    |
| **Ambassador Pattern**    | API gateway using containers (e.g., NGINX Ingress).| Deploy Ingress Controller to route external traffic to internal services.          |
| **Serverless Containers** | Event-driven, auto-scaling workloads.              | Use **Knative** or **AWS Fargate** for serverless K8s workloads.                     |

---

## **2. Schema Reference**
### **2.1 Kubernetes Manifests (YAML Schemas)**
Below are **critical YAML schemas** for deploying containers in Kubernetes.

#### **Deployment Schema**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: my-registry/my-app:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
```

#### **Service Schema**
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
  type: ClusterIP  # or LoadBalancer/NodePort
```

#### **PersistentVolume (PV) & PersistentVolumeClaim (PVC) Schema**
```yaml
# PV (Static Provisioning)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data"

# PVC (Dynamic Provisioning)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

---

### **2.2 Dockerfile Schema**
A standard **multi-stage Dockerfile** for minimal image size:

```dockerfile
# Stage 1: Build environment
FROM golang:1.21 as builder
WORKDIR /app
COPY . .
RUN go build -o /app/bin/my-app

# Stage 2: Runtime environment
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/bin/my-app .
EXPOSE 8080
ENTRYPOINT ["./my-app"]
```

---

## **3. Query Examples**

### **3.1 Kubernetes CLI Queries**
| **Query**                                                                 | **Use Case**                                      | **Example Command**                                      |
|---------------------------------------------------------------------------|---------------------------------------------------|---------------------------------------------------------|
| List all pods in a namespace.                                              | Monitor running containers.                       | `kubectl get pods -n my-namespace`                      |
| Describe a pod’s logs and events.                                          | Debug failures.                                   | `kubectl describe pod my-pod -n my-namespace`          |
| Scale a deployment to 5 replicas.                                          | Adjust resource allocation.                       | `kubectl scale deployment my-app --replicas=5 -n my-namespace` |
| View resource limits for a pod.                                            | Optimize CPU/memory usage.                        | `kubectl top pod my-pod -n my-namespace`               |
| Check ingress traffic.                                                      | Monitor API gateway.                              | `kubectl get ingress`                                  |
| Execute a shell inside a running pod.                                       | Debug live containers.                            | `kubectl exec -it my-pod -- /bin/sh`                   |
| Port-forward to expose a local service.                                     | Test without Ingress.                             | `kubectl port-forward svc/my-service 8080:80`          |

---

### **3.2 Docker Compose Example**
Deploy a multi-container stack with **Docker Compose**:

```yaml
version: "3.8"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    depends_on:
      - redis
  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data
volumes:
  redis-data:
```
**Deploy:**
```bash
docker-compose up -d
```
**Access logs:**
```bash
docker-compose logs web
```

---

## **4. Related Patterns**
| **Pattern**               | **Connection to Containers**                                                                 | **When to Use**                                                                 |
|---------------------------|--------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **[Service Mesh]**        | Manages inter-container traffic (e.g., Istio, Linkerd).                                     | Highly complex microservices needing observability, security, and traffic control. |
| **[Knative]**            | Serverless containers (auto-scaling to zero).                                              | Event-driven workloads with sporadic traffic.                                |
| **[Canary Deployments]** | Gradually roll out updates to assess stability.                                            | Production environments requiring low-risk updates.                           |
| **[Helm Charts]**        | Package and version K8s manifests for reuse.                                               | Large-scale deployments needing templating and dependency management.         |
| **[GitOps]**             | Sync K8s configs via Git (ArgoCD, Flux).                                                   | CI/CD pipelines requiring declarative, audit-friendly deployments.              |

---

## **5. Best Practices & Anti-Patterns**
### **Best Practices**
✅ **Use multi-stage builds** to reduce image size.
✅ **Set resource limits** to prevent noisy neighbors.
✅ **Leverage secrets management** (e.g., Kubernetes Secrets, Vault) instead of hardcoding credentials.
✅ **Implement health checks** (`livenessProbe`, `readinessProbe`) for resilience.
✅ **Adopt CI/CD pipelines** (GitHub Actions, ArgoCD) for automated deployments.

### **Anti-Patterns**
❌ **Running containers as root** (security risk).
❌ **Ignoring image layers** (bloating builds unnecessarily).
❌ **Overusing initContainers** for long-running tasks (use sidecars instead).
❌ **Hardcoding environment-specific configs** (use ConfigMaps/Secrets).
❌ **No observability** (missing Prometheus/Grafana integration).

---

## **6. Troubleshooting Guide**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|------------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Pod crashes repeatedly.**        | Check `kubectl describe pod <pod>` for errors in logs.                       | Fix application issues or adjust resource requests/limits.                   |
| **Container images pull fails.**   | Verify registry access and image tags.                                       | Ensure `imagePullSecrets` configured or registry credentials are correct.   |
| **Network connectivity issues.**   | Test with `kubectl exec -it <pod> -- curl <service>`.                       | Check Service DNS, Ingress rules, or network policies.                       |
| **Persistent storage not mounting.** | Verify PVC/PV claims and storage class.                                      | Ensure dynamic provisioner is running (e.g., `storageclass` matches).        |
| **Slow performance.**              | Use `kubectl top nodes` to identify bottlenecks.                             | Scale nodes horizontally or adjust resource requests.                       |

---

## **7. Further Reading**
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [CNCF Landmine Patterns](https://landscape.cncf.io/)
- [Istio Service Mesh Docs](https://istio.io/latest/docs/)
- [Helm Charts Guide](https://helm.sh/docs/intro/using_helm/)