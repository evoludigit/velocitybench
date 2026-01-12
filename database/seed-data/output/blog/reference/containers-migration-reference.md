**[Pattern] Containers Migration: Reference Guide**

---

### **Overview**
The **Containers Migration** pattern refers to the systematic process of relocating applications, services, or workloads from traditional virtual machines (VMs), bare-metal servers, or cloud VMs into **containerized environments** (e.g., Docker, Kubernetes). This pattern improves resource efficiency, scalability, portability, and CI/CD pipeline integration while reducing operational overhead. Common migration targets include Kubernetes clusters, serverless platforms, or container orchestration systems. Key considerations include dependencies, runtime compatibility, stateful vs. stateless applications, networking, security, and rollback strategies. This guide outlines the core implementation steps, schema references, and best practices for executing a successful container migration.

---

### **Key Concepts & Implementation Details**

#### **1. Why Migrate to Containers?**
- **Resource Efficiency:** Containers share the host OS kernel, reducing overhead (vs. VMs).
- **Portability:** Containers run consistently across on-premises, cloud, and hybrid environments.
- **Scalability:** Easily scale horizontally with orchestration tools (e.g., Kubernetes).
- **CI/CD Integration:** Containers standardize deployment environments (avoiding "works on my machine" issues).
- **Cost Savings:** Lower infrastructure costs by optimizing resource usage.

#### **2. Migration Approaches**
| Approach               | Description                                                                 | Best For                          |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------|
| **Replatforming**      | Lifting and shifting existing apps into containers without architectural changes. | Legacy apps needing minor updates. |
| **Refactoring**        | Redesigning apps to leverage container-native features (e.g., sidecars, init containers). | Microservices, polyglot architectures. |
| **Rehosting**          | Moving VMs to containers (e.g., using tools like **Kitloo** or **Kubevirt**). | Lift-and-shift migrations.        |
| **Rearchitecting**     | Fully redesigning apps for cloud-native paradigms (e.g., serverless, event-driven). | Greenfield projects or major upgrades. |

#### **3. Containers Migration Lifecycle**
1. **Assessment**
   - Inventory existing workloads (dependencies, runtime, networking).
   - Identify stateful vs. stateless components.
   - Profile resource usage (CPU, memory, I/O).

2. **Containerization**
   - Define container images (Dockerfiles, multi-stage builds).
   - Configure environment variables, health checks, and resource limits.
   - Use **distroless** or **Alpine-based** images for security.

3. **Orchestration**
   - Deploy to Kubernetes (or another orchestrator) using:
     - **YAML manifests** (Deployment, StatefulSet, DaemonSet).
     - **Helm charts** for templating.
     - **Kustomize** for environment-specific configurations.
   - Configure:
     - Networking (Services, Ingress, CNI plugins).
     - Persistent storage (PersistentVolumes, Claims).
     - Secrets management (Vault, Kubernetes Secrets).

4. **Validation & Testing**
   - Run integration tests in staging (e.g., using **Kaniko** for CI/CD).
   - Verify:
     - Performance (latency, throughput).
     - Security (vulnerability scans, runtime protections).
     - Rollback plans (revert to VMs if needed).

5. **Deployment & Monitoring**
   - Use **blue-green** or **canary** deployments for zero-downtime transitions.
   - Monitor:
     - Container health (liveness/readiness probes).
     - Logs (EFK Stack: Elasticsearch, Fluentd, Kibana).
     - Metrics (Prometheus + Grafana).

6. **Optimization**
   - Right-size resources (Requests/Limits in Kubernetes).
   - Optimize image layers (multi-stage builds, `.dockerignore`).
   - Adopt **SRE practices** (SLIs/SLOs, autoscaling).

---

### **Schema Reference**
Below are key schema definitions for container migration artifacts.

#### **1. Dockerfile Template**
```dockerfile
# Stage 1: Build environment
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go mod download && CGO_ENABLED=0 GOOS=linux go build -o /app/service

# Stage 2: Runtime image (distroless)
FROM gcr.io/distroless/base-debian12
WORKDIR /
COPY --from=builder /app/service /app/service
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app/service"]
```

#### **2. Kubernetes Deployment Manifest**
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
        image: my-registry/my-app:v1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

#### **3. PersistentVolume (PV) & Claim (PVC)**
```yaml
# PersistentVolume (static provisioning)
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
    path: /mnt/data

# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### **4. Ingress Resource (NGINX Example)**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-service
            port:
              number: 80
```

---

### **Query Examples**
#### **1. Check Container Resource Limits**
```sh
kubectl describe pod my-app-56b7f8c4d8-abc12 --show-original
```
Look for `Limits` and `Requests` under the container spec.

#### **2. Verify Liveness Probe Status**
```sh
kubectl get pods --show-labels
kubectl describe pod my-app-56b7f8c4d8-abc12 | grep "Liveness"
```

#### **3. List PersistentVolumeClaims**
```sh
kubectl get pvc
kubectl describe pvc my-pvc
```

#### **4. Monitor Container Logs**
```sh
kubectl logs my-app-56b7f8c4d8-abc12 --tail=50
kubectl logs -f my-app-56b7f8c4d8-abc12  # Follow logs
```

#### **5. Scale Deployment Replicas**
```sh
kubectl scale deployment my-app --replicas=5
```

#### **6. Port-Forward for Local Testing**
```sh
kubectl port-forward pod/my-app-56b7f8c4d8-abc12 8080:8080
```

---

### **Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| **Stateful app data loss**        | Use `PersistentVolumeClaims` with `ReadWriteMany` (e.g., NFS, Ceph).      |
| **Networking misconfigurations** | Test egress/ingress rules with `kubectl exec` and `curl`.                |
| **Dependency conflicts**          | Pin runtime versions (e.g., `FROM golang:1.21` instead of `latest`).       |
| **Security vulnerabilities**      | Scan images with **Trivy** or **Clair**; use distroless/base images.       |
| **Performance bottlenecks**      | Use `vertical pod autoscaler` (VPA) to adjust CPU/memory dynamically.     |
| **Rollback complexity**           | Maintain VM snapshots or use **immutable tags** (e.g., `v1.0.0`).         |

---

### **Related Patterns**
1. **[Blue-Green Deployment](https://pattern.money/blue-green-deployment)**
   - Minimize downtime during container migrations by running old/new versions in parallel.

2. **[Canary Releases](https://pattern.money/canary-releases)**
   - Gradually Route traffic to new containerized versions to test stability.

3. **[Service Mesh Integration](https://pattern.money/service-mesh)**
   - Use **Istio** or **Linkerd** for advanced traffic management, observability, and security.

4. **[GitOps](https://pattern.money/gitops)**
   - Manage container deployments via Git repositories (e.g., ArgoCD, Flux) for auditability.

5. **[Multi-Cluster Deployments](https://pattern.money/multi-cluster)**
   - Deploy containers across regions/clusters for high availability (e.g., using **Kubernetes Federation**).

6. **[Serverless Containers](https://pattern.money/serverless-containers)**
   - Run containers as serverless functions (e.g., **Knative**, **AWS Fargate**) for event-driven workloads.

---
### **Further Reading**
- [CNCF Kubernetes Best Practices](https://github.com/kubernetes/community/blob/main/contributors/guide/kubernetes-best-practices.md)
- [Docker Best Practices](https://docs.docker.com/engine/userguide/eng-image/optimization/)
- [Resizing Containers in Kubernetes](https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/)