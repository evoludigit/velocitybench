# **[Pattern] Containers Setup Reference Guide**

## **Overview**
This guide provides detailed instructions for **setting up containerized environments** using widely adopted frameworks (Docker, Kubernetes, and Kubernetes Operators). It covers prerequisites, schema conventions, implementation workflows, and common query patterns for deploying, managing, and scaling containerized applications. Whether deploying a single service or a multi-service ecosystem, this guide ensures consistency across teams.

---

## **Key Concepts**
### **Core Technologies**
| **Technique**       | **Purpose**                                                                 | **Key Components**                                                                 |
|----------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Docker**           | Package apps and dependencies into portable containers.                     | Images, Containers, Volumes, Networks, Dockerfiles, `docker-compose.yml`          |
| **Kubernetes (K8s)** | Orchestrate containers at scale (scheduling, auto-healing, scaling).         | Pods, Deployments, Services, ConfigMaps, Secrets, Ingress, Namespaces, RBAC      |
| **K8s Operators**    | Extend Kubernetes with custom controllers for complex applications.          | CRDs (Custom Resource Definitions), Operator SDK, Helm Charts, Reconciliation    |

### **Common Patterns**
- **Monolithic Containers** (single-process apps).
- **Microservices** (multi-container pods).
- **Serverless Containers** (event-driven, short-lived tasks).
- **Hybrid Workloads** (mixing stateless and stateful apps).

---

## **Requirements**
### **Prerequisites**
Before setting up containers, ensure the following are installed and configured:

| **Component**               | **Version**       | **Purpose**                                                                       |
|-----------------------------|-------------------|-----------------------------------------------------------------------------------|
| Docker Engine               | ≥ 20.10.0         | Container runtime for local/on-prem development.                                   |
| Kubernetes Cluster          | ≥ 1.24            | Orchestration for production deployments (e.g., `minikube`, `kind`, EKS/GKE).     |
| Helm                        | ≥ 3.10            | Package management for Kubernetes (optional but recommended).                      |
| Kubernetes CLI (`kubectl`)  | ≥ 1.24            | Client for interacting with Kubernetes clusters.                                   |
| Container Registry Access   | (e.g., Docker Hub, AWS ECR) | Hosting container images securely.                                          |

---

## **Schema Reference**
### **1. Docker Compose Schema**
Used to define multi-container apps for local development.

```yaml
version: '3.8'
services:
  app:
    image: nginx:latest  # Required. Must be a valid registry path.
    ports:
      - "8080:80"        # Format: <host>:<container>
    environment:
      - DB_URL=postgres://user:pass@db:5432/db
    volumes:
      - ./data:/app/data  # Format: <host_path>:<container_path>
    depends_on:
      - db               # Ensures DB starts before app.
  db:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - db_data:/var/lib/postgresql/data
volumes:
  db_data:               # Named volume for persistence.
```

**Validation Rules:**
- `image`: Must be a complete registry path (e.g., `ghcr.io/org/repo:tag`).
- `ports`: Host port must not conflict with other services.
- `depends_on`: Only enforces *start order*; does not wait for readiness.

---

### **2. Kubernetes Deployment Schema**
Defines how a containerized app scales and updates.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3               # Desired pod count.
  selector:
    matchLabels:
      app: nginx            # Must match Pod labels.
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.23    # Must include tag (no `:latest`).
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"      # 0.1 CPU cores.
            memory: "128Mi"
          limits:
            cpu: "200m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Validation Rules:**
- `replicas`: Must be ≥ 1.
- `image`: Tag *must* be specified (avoid `:latest`).
- `resources`: Set both `requests` and `limits` for production.
- `probes`: Required for self-healing; adjust `initialDelaySeconds` based on app startup time.

---

### **3. Kubernetes Operator Schema (CRD Example)**
Extends Kubernetes with custom resources for complex apps (e.g., databases).

```yaml
apiVersion: apps.example.com/v1
kind: Database
metadata:
  name: my-db
spec:
  size: 10Gi           # Custom field for operator logic.
  replicaCount: 2      # Operator-managed replicas.
  backup:
    schedule: "0 2 * * *"  # Cron syntax.
    retention: 7         # Days to keep backups.
```

**Validation Rules:**
- `apiVersion`: Must match the Operator’s CRD.
- `spec`: Fields are custom (defined by the Operator SDK).
- `status`: Read-only; populated by the Operator.

---

## **Query Examples**
### **1. Docker Compose**
**Deploy an app with a database:**
```bash
docker-compose up -d
```
**Check logs:**
```bash
docker-compose logs -f app
```
**Scale a service:**
```bash
docker-compose up -d --scale worker=5
```

---

### **2. Kubernetes**
**Deploy a YAML file:**
```bash
kubectl apply -f nginx-deployment.yaml
```
**Check pod status:**
```bash
kubectl get pods -w
```
**Port-forward to a pod:**
```bash
kubectl port-forward pod/nginx-deployment-5c8f6d7c44-xyz 8080:80
```
**Delete a stale deployment:**
```bash
kubectl delete deployment nginx-deployment --force --grace-period=0
```

---

### **3. Kubernetes Operator**
**Create a custom resource:**
```bash
kubectl apply -f db-cr.yaml
```
**List custom resources:**
```bash
kubectl get databases.apps.example.com
```
**Patch a resource:**
```bash
kubectl patch database my-db --type='json' -p='{"spec":{"size":"20Gi"}}'
```

---

## **Common Pitfalls & Mitigations**
| **Issue**                          | **Cause**                          | **Solution**                                                                 |
|------------------------------------|------------------------------------|------------------------------------------------------------------------------|
| **Pod hangs at image pull**        | Invalid registry path or auth.     | Verify `image` tag and registry credentials.                                |
| **Resource starvation**            | No `limits` set.                   | Set CPU/memory `limits` in Deployment.                                       |
| **Operator reconciliation loops**   | CRD schema mismatch.               | Check `kubectl describe` for Operator’s reconciliation errors.                |
| **Docker Compose port conflicts**   | Host port already in use.          | Use dynamic ports (`docker-compose up -p 8080`) or change host ports.        |

---

## **Related Patterns**
1. **Service Discovery**: Use Kubernetes `Services` (ClusterIP, NodePort, LoadBalancer) or Istio for advanced routing.
2. **Secrets Management**: Store secrets in Kubernetes `Secrets` or use external tools like HashiCorp Vault.
3. **CI/CD for Containers**: Integrate with GitHub Actions, ArgoCD, or Jenkins to automate builds/deployments.
4. **Observability**: Deploy Prometheus + Grafana for metrics and Loki + Tempo for logs/traces.
5. **Security Hardening**: Scan images with Trivy or Clair; enforce network policies in Kubernetes.

---
**Next Steps:**
- For local development: [Docker Desktop Guide](https://docs.docker.com/desktop/).
- For production: [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/overview/working-with-and-deploying-applications/).