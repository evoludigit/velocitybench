---
# **[Pattern] Containers Best Practices Reference Guide**

---

## **Overview**
This reference provides actionable guidelines for designing, deploying, and maintaining containerized applications in **Kubernetes (K8s), Docker, or other container orchestration platforms**. Adhering to these best practices ensures **scalability, security, performance, and maintainability** of containerized workloads. Topics include **image optimization, resource management, networking, security, logging, and CI/CD integration**.

---

## **Key Concepts & Schema Reference**

### **1. Image Optimization**
Reduce image size and improve security by following these principles:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **Tools/Commands**                          |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------|
| **Base Images**            | Use minimal, official, and well-maintained images | Avoid overprivileged images (e.g., `ubuntu`); prefer `alpine` or `distroless`.         | `docker pull python:3.9-alpine`              |
| **Layer Caching**          | Organize `Dockerfile` for optimal caching        | Group related commands and avoid rebuilding unrelated layers.                          | Multi-stage builds (`FROM` chaining)        |
| **Multi-Stage Builds**     | Separate build dependencies from runtime           | Reduce final image size by discarding build tools after use.                             | Example: `COPY --from=builder /app /app`     |
| **Security Scanning**      | Scan for vulnerabilities before deployment       | Integrate static analysis into CI/CD pipelines.                                         | `trivy`, `docker scan`                     |
| **Tagging Strategy**       | Use semantic versioning (`v1.0.0`, not `latest`) | Avoid `latest` tags in production; use tags like `:prod` or `:dev`.                     | `docker tag myapp:1.0.0 myreg/myapp:prod`   |

---

### **2. Resource Management**
Prevent resource starvation and ensure efficiency:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **YAML/CLI Examples**                     |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|--------------------------------------------|
| **CPU/Memory Requests**    | Define non-zero requests for all containers       | Prevents resource throttling; use `limits` for upper bounds.                            | `resources: requests: cpu: "500m"`          |
| **Vertical Scaling**       | Adjust requests/limits based on profiling          | Use `kubectl top pods` or Prometheus for metric collection.                              | `kubectl set resources pod nginx --cpu=1 --memory=512Mi` |
| **Liveness/Readiness Probes** | Monitor container health dynamically        | Configure probes to restart unhealthy containers or route traffic to healthy ones.      | `livenessProbe: httpGet: path: /health`    |
| **Resource Quotas**        | Limit namespace resource consumption            | Apply quotas to prevent a single workload from consuming all cluster resources.       | `kubectl create quota mem-limit --hard=memory=1Gi` |

---

### **3. Networking & Security**
Isolate and secure container communications:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **YAML/CLI Examples**                     |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|--------------------------------------------|
| **Network Policies**       | Enforce least-privilege access control           | Define policies to restrict pod-to-pod communication (e.g., allow only backend → frontend). | `apiVersion: networking.k8s.io/v1`        |
| **Service Mesh (Optional)**| Use Istio or Linkerd for advanced traffic management | Decouples service communication from infrastructure.                                   | `kubectl apply -f istio-gateway.yaml`      |
| **Secrets Management**     | Never hardcode secrets; use Kubernetes Secrets   | Rotate secrets frequently and encrypt at rest.                                           | `kubectl create secret generic db-pass --from-literal=password=xxx` |
| **Pod Security Standards** | Enforce PodSecurityPolicies (PSP) or OPA/Gatekeeper | Restrict privileged containers, drop root capabilities, and read-only root filesystems. | `runAsNonRoot: true`                       |
| **Image Signing**          | Sign images with Cosmos or Notary                | Verify image integrity to prevent tampering.                                             | `cosign sign --key cosign.key myimage:tag`  |

---

### **4. Logging & Monitoring**
Centralize logs and metrics for observability:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **Tools**                                   |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------|
| **Log Aggregation**        | Ship logs to a centralized system (EFK, Loki)     | Use `fluentd`/`fluent-bit` to forward logs to Elasticsearch, Loki, or Datadog.          | `kubectl logs -l app=myapp > log-stream.sh` |
| **Structured Logging**     | Use JSON format for logs                           | Simplifies parsing and filtering in log analysis tools.                                   | `{"level":"info", "message":"app started"}`   |
| **Metrics Collection**     | Export Prometheus-compatible metrics              | Use client libraries (e.g., `prometheus-client`) to expose metrics.                   | `/metrics` endpoint                         |
| **Alerting**               | Define alert rules for critical metrics           | Set thresholds for CPU, memory, or error rates (e.g., `>95% latency` triggers an alert). | Prometheus Alertmanager                     |

---

### **5. CI/CD & GitOps**
Automate deployments with reproducibility and rollback safety:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **Tools**                                   |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------|
| **Immutable Infrastructure**| Rebuild containers for every change               | Avoid manually editing running containers.                                             | `docker build --no-cache .`                 |
| **Blue-Green Deployments** | Deploy updates to a separate environment first    | Minimize downtime by routing traffic to new pods before full rollout.                  | `kubectl apply -f new-deployment.yaml`      |
| **Canary Releases**        | Gradually roll out updates to a subset of users   | Reduces risk by monitoring impact before full deployment.                               | Istio traffic splitting                     |
| **Rollback Strategy**      | Automate rollbacks based on health checks         | Use Kubernetes `Rollback` or CI/CD hooks to revert if probes fail.                     | `kubectl rollout undo deployment/myapp`    |
| **GitOps**                 | Use tools like ArgoCD to sync cluster state with Git | Auditable, declarative deployments with version control.                               | `argocd app sync myapp`                     |

---

### **6. Cost Optimization**
Reduce cloud costs without sacrificing performance:

| **Category**               | **Best Practice**                                  | **Implementation Notes**                                                                 | **Tools**                                   |
|----------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------|
| **Spot Instances**         | Use spot nodes for fault-tolerant workloads       | Leverage cheaper spot prices for stateless or batch jobs.                                | `kubectl annotate node <node> spot=true`     |
| **Auto-Scaling**           | Configure Horizontal Pod Autoscaler (HPA)         | Scale pods based on CPU/memory or custom metrics (e.g., QPS).                           | `autoscaling/v2beta2`                       |
| **Resource Right-Sizing**  | Match requests/limits to actual usage             | Use `kubectl top` and profiling tools to avoid over-provisioning.                       | `kubectl describe pod -n <namespace>`       |
| **Ephemeral Storage**      | Minimize use of persistent volumes                | Avoid unnecessary disk I/O for stateless applications.                                  | `--storage-class=fast`                     |
| **Multi-Region Deployments** | Deploy to multiple regions for high availability | Distribute workloads to reduce latency and improve resilience.                          | `kubectl apply -f <region>-manifests.yaml`  |

---

## **Query Examples**
### **1. Check Pod Resource Usage**
```sh
kubectl top pods -A
# Output:
NAMESPACE     NAME                  CPU(cores)   MEMORY(bytes)
default       nginx-5b698c4b6-abc1   10m          32Mi
```

### **2. Inspect Network Policies**
```sh
kubectl get networkpolicies --all-namespaces
# Output:
NAMESPACE   NAME                     POD-SELECTOR   AGE
default     default-deny-ingress     <none>         2d
```

### **3. Scan Docker Image for Vulnerabilities**
```sh
docker scan nginx:latest
# Output:
Vulnerability found: CVE-2021-41773 (Critical)
Fixed in: nginx:1.21.0
```

### **4. Deploy with Resource Limits**
```yaml
# deployment.yaml
spec:
  template:
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        resources:
          requests:
            cpu: "200m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
```
Apply with:
```sh
kubectl apply -f deployment.yaml
```

### **5. Rollback a Deployment**
```sh
kubectl rollout undo deployment/myapp
# Or revert to a specific revision:
kubectl rollout undo deployment/myapp --to-revision=2
```

---

## **Related Patterns**
1. **[Infrastructure as Code (IaC) Reference Guide]**
   - Define containerized environments using Terraform or Pulumi.
2. **[Service Mesh Patterns]**
   - Extend networking with Istio or Linkerd for advanced traffic management.
3. **[Canary Deployments]**
   - Gradually roll out changes to minimize risk.
4. **[Microservices Architecture]**
   - Design containerized apps as loosely coupled services.
5. **[Disaster Recovery for Containers]**
   - Backup and restore Kubernetes clusters or etcd.
6. **[Serverless Containers (Knative)]**
   - Run containers event-driven without manual scaling.

---
## **Further Reading**
- [CNCF Kubernetes Best Practices](https://github.com/kubernetes/community/blob/main/sig-docs/resources/kubernetes_best_practices.md)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Prometheus Monitoring Guidelines](https://prometheus.io/docs/practices/operating/)
- [ArgoCD GitOps Documentation](https://argo-cd.readthedocs.io/)