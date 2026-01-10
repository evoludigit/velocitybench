---
# **[Pattern] Container Orchestration with Docker and Kubernetes: Reference Guide**

---

## **1. Overview**
Container orchestration automates the deployment, scaling, and management of containerized applications. This pattern combines **Docker** (for containerization) and **Kubernetes (K8s)** (for orchestration) to deliver scalable, resilient, and maintainable workloads.

- **Docker** provides lightweight, portable environments (containers) via the **Docker Engine** and **Docker Compose** (for local/testing).
- **Kubernetes** orchestrates containers across **clusters**, handling:
  - Multi-container pod deployment
  - Auto-scaling (horizontal/pod-level)
  - Self-healing (restarting/removing failed pods)
  - Service discovery & load balancing
  - Storage orchestration (volumes/PersistentVolumes)
  - Secrets management
  - Rolling updates/deployments

For **development/testing**, **Docker Compose** simplifies multi-container workflows. For **production microservices**, Kubernetes ensures scalability, fault tolerance, and CI/CD integration.

**Key Considerations:**
✔ Use Docker alone for isolated, single-container workloads (e.g., dev environments).
✔ Deploy to Kubernetes for production workloads requiring orchestration, auto-scaling, or multi-cluster management.

---

## **2. Schema Reference**
The following tables define core components, their configurations, and relationships.

### **2.1 Core Components & YAML Schema**
| **Component**          | **Purpose**                                                                 | **YAML/Config Key**                     | **Required?** | **Example Values**                     |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------|----------------|-----------------------------------------|
| **Pod**                | Smallest deployable unit (1+ containers sharing storage/network).          | `apiVersion: v1`, `kind: Pod`           | ✅ Yes         | `spec.containers: [name: nginx]`       |
| **Deployment**         | Manages Pod replicas, rolling updates, and self-healing.                     | `apiVersion: apps/v1`, `kind: Deployment` | ✅ Yes         | `spec.replicas: 3`, `strategy: Rolling`|
| **Service**            | Exposes Pods internally (ClusterIP) or externally (NodePort/LoadBalancer).| `apiVersion: v1`, `kind: Service`       | ⚠ Optional     | `type: ClusterIP`, `ports: 80:80`      |
| **ConfigMap/Secret**   | Stores non-sensitive (ConfigMap) and sensitive (Secret) data.               | `apiVersion: v1`, `kind: ConfigMap`     | ⚠ Optional     | Key pairs: `env: "ENV_VAR=value"`      |
| **PersistentVolume (PV)** | Manages external storage (e.g., NFS, cloud storage).          | `apiVersion: v1`, `kind: PersistentVolume` | ⚠ Optional | `accessModes: ["ReadWriteOnce"]` |
| **PersistentVolumeClaim (PVC)** | Pods request storage via PVCs. | `apiVersion: v1`, `kind: PersistentVolumeClaim` | ✅ (for storage) | `resources.requests.storage: "1Gi"` |
| **Ingress**            | Manages external HTTP/HTTPS traffic routing (e.g., Nginx Ingress).          | `apiVersion: networking.k8s.io/v1`, `kind: Ingress` | ⚠ Optional | `rules: [host: "app.example.com"]` |

---

### **2.2 Kubernetes Manifest Relationships**
| **Parent Resource**   | **Child Resources**                          | **Purpose**                                                                 |
|-----------------------|----------------------------------------------|-----------------------------------------------------------------------------|
| Deployment            | Pods                                         | Controls Pod lifecycle (creation, scaling).                                 |
| Service               | Endpoints (pod IPs)                          | Routes traffic to Pods dynamically.                                         |
| ConfigMap/Secret      | Pod/Deployment environment variables          | Injects configuration/data into containers.                                 |
| PVC                   | Pod volumes                                  | Binds persistent storage to Pods.                                           |
| Ingress               | Backend Services (ClusterIP)                 | Routes external traffic to internal Services.                               |

---

## **3. Query Examples**
Use `kubectl` to interact with Kubernetes resources.

### **3.1 Basic Commands**
| **Command**                                                                 | **Purpose**                              |
|------------------------------------------------------------------------------|------------------------------------------|
| `kubectl get pods -A`                                                        | List all Pods across namespaces.         |
| `kubectl describe deployment nginx-deploy`                                  | Inspect Deployment status/events.        |
| `kubectl logs <pod-name>`                                                    | View container logs.                     |
| `kubectl exec -it <pod-name> -- /bin/bash`                                | Access a running container shell.        |
| `kubectl apply -f nginx-deployment.yaml`                                   | Deploy from YAML file.                  |

---

### **3.2 Common Workflows**
#### **Deploy an App with a Deployment and Service**
```yaml
# nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deploy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
---
# nginx-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```
**Apply:**
```bash
kubectl apply -f nginx-deployment.yaml -f nginx-service.yaml
```

---

#### **Scale a Deployment**
```bash
kubectl scale deployment/nginx-deploy --replicas=5
# Verify:
kubectl get pods -l app=nginx
```

---

#### **Expose a Service via Ingress**
```yaml
# nginx-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-service
            port:
              number: 80
```
**Apply:**
```bash
kubectl apply -f nginx-ingress.yaml
```

---

#### **Use a ConfigMap for Configuration**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "debug"
  API_URL: "https://api.example.com"
---
# deployment-with-config.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        envFrom:
        - configMapRef:
            name: app-config
```
**Apply:**
```bash
kubectl apply -f configmap.yaml -f deployment-with-config.yaml
```

---

## **4. Related Patterns**
| **Pattern**                          | **Description**                                                                 | **When to Use**                                  |
|--------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Docker Compose for Local Development](link)** | Uses `docker-compose.yml` to orchestrate multi-container dev environments. | Local testing, CI/CD pipelines.                   |
| **[Helm for Package Management](link)** | Templating engine for Kubernetes manifest management (charts).              | Reusable, versioned deployments.                 |
| **[Kubernetes Operators](link)**      | Automates complex workloads (e.g., databases, monitoring) via custom controllers. | Stateful applications (e.g., PostgreSQL).       |
| **[Service Mesh (Istio/Linkerd)](link)** | Adds observability, security, and traffic management to microservices.    | Production-grade traffic control, mTLS.         |
| **[GitOps with ArgoCD/Flux](link)**   | Syncs cluster state with Git repository (declarative deployments).          | Infrastructure-as-code (IaC) workflows.          |

---

## **5. Key Considerations**
### **5.1 When to Use Docker Alone**
- **Use Case:** Single-container apps (e.g., dev/test environments, lightweight services).
- **Tools:** Docker Engine, Docker Compose.
- **Limitations:** No auto-scaling, self-healing, or multi-cluster management.

### **5.2 When to Use Kubernetes**
- **Use Case:** Production microservices, auto-scaling, multi-region deployments.
- **Key Features:**
  - **Horizontal Pod Autoscaling (HPA):** Scales Pods based on CPU/memory.
  - **Cluster Autoscaling:** Adds/removes nodes dynamically.
  - **Network Policies:** Restricts Pod-to-Pod communication.
  - **Custom Resource Definitions (CRDs):** Extends Kubernetes API (e.g., for databases).

### **5.3 Hybrid Approach**
- **Dev/Test:** Docker Compose (local) → Minikube/Kind (local Kubernetes).
- **Production:** Kubernetes (EKS/GKE/AKS) + Helm for packaging.

---
**Next Steps:**
- Explore [Kubernetes Official Docs](https://kubernetes.io/docs/home/) for deeper dives.
- Use [kubectl-cheatsheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/) for quick commands.