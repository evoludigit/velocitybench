# **[Pattern] Docker & Container Deployment Reference Guide**

---

## **1. Overview**
The **Docker & Container Deployment** pattern standardizes the process of packaging applications in lightweight, isolated containers for consistent, scalable, and portable deployment across environments. This pattern leverages Docker and Kubernetes (or other orchestration tools) to streamline CI/CD pipelines, reduce infrastructure complexity, and ensure runtime consistency. Key benefits include **environment parity**, **resource efficiency**, and **rapid scaling**. This guide covers containerization best practices, deployment workflows, optimization techniques, and integration with modern DevOps toolchains.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Core Components**
| **Component**         | **Description**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------|
| **Container**         | Lightweight, standalone runtime environment running a single or multiple applications.              |
| **Docker Engine**     | Client-server architecture to build, run, and manage containers. Includes `dockerd` (daemon) and CLI. |
| **Docker Image**      | Immutable, layered, executable package containing an application and its dependencies.            |
| **Dockerfile**        | Script defining how an image is built (e.g., `FROM`, `RUN`, `COPY`, `CMD`).                         |
| **Docker Compose**    | Tool to define and run multi-container applications (YAML-based).                                   |
| **Kubernetes (K8s)**  | Orchestrates containers at scale (scaling, self-healing, load balancing).                          |
| **Docker Hub/Registry** | Hosting platform for storing and sharing container images.                                          |
| **Volumes**           | Persistent storage detached from containers (e.g., databases, logs).                               |
| **Networks**          | Isolation or inter-container communication (e.g., `bridge`, `overlay`).                           |
| **Health Checks**     | Monitor container readiness/liveness (e.g., `HEALTHCHECK` in Docker).                              |

---

### **2.2 Implementation Workflow**
1. **Containerize the Application**
   - Write a **Dockerfile** to define the environment and dependencies.
   - Example:
     ```dockerfile
     FROM node:18-alpine
     WORKDIR /app
     COPY package*.json ./
     RUN npm install
     COPY . .
     CMD ["npm", "start"]
     ```
   - Build the image:
     ```bash
     docker build -t my-app:1.0 .
     ```

2. **Store and Share Images**
   - Push to a registry (e.g., Docker Hub, AWS ECR, GCR):
     ```bash
     docker tag my-app:1.0 myusername/my-app:1.0
     docker push myusername/my-app:1.0
     ```

3. **Deploy Containers**
   - **Single-container**:
     ```bash
     docker run -d --name my-app -p 3000:3000 myusername/my-app:1.0
     ```
   - **Multi-container (Docker Compose)**:
     ```yaml
     # docker-compose.yml
     version: "3.8"
     services:
       app:
         image: myusername/my-app:1.0
         ports:
           - "3000:3000"
         depends_on:
           - db
       db:
         image: postgres:14
         environment:
           POSTGRES_PASSWORD: example
     ```
     Run with:
     ```bash
     docker-compose up -d
     ```

4. **Orchestrate at Scale (Kubernetes)**
   - Define a **Deployment** and **Service** in `deployment.yml`:
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
             image: myusername/my-app:1.0
             ports:
             - containerPort: 3000
     ```
   - Apply with:
     ```bash
     kubectl apply -f deployment.yml
     ```

5. **Optimize Performance**
   - **Reduce Image Size**:
     - Use `alpine`-based images.
     - Leverage multi-stage builds:
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
   - **Limit Resources**:
     ```yaml
     # Kubernetes resource limits
     resources:
       requests:
         cpu: "100m"
         memory: "128Mi"
       limits:
         cpu: "500m"
         memory: "512Mi"
     ```
   - **Use Read-only Filesystems**:
     ```bash
     docker run --read-only ...
     ```

6. **Monitor and Log**
   - Integrate with tools like:
     - **Prometheus** + **Grafana** for metrics.
     - **ELK Stack** (Elasticsearch, Logstash, Kibana) for logs.
     - **Docker Events** or Kubernetes `kubectl logs`.

7. **CI/CD Integration**
   - Automate builds/deployments using GitHub Actions, GitLab CI, or Jenkins:
     ```yaml
     # GitHub Actions workflow
     name: Docker Build and Push
     on: push
     jobs:
       build:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v3
           - run: docker build -t myusername/my-app:${{ github.sha }} .
           - run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
           - run: docker push myusername/my-app:${{ github.sha }}
     ```

---

## **3. Schema Reference**

### **3.1 Dockerfile Fields**
| **Directive** | **Purpose**                          | **Example**                          |
|----------------|---------------------------------------|--------------------------------------|
| `FROM`         | Base image                            | `FROM python:3.9`                    |
| `WORKDIR`      | Working directory                     | `WORKDIR /app`                       |
| `COPY`         | Copy files to container               | `COPY . /app`                        |
| `RUN`          | Execute commands                      | `RUN pip install -r requirements.txt` |
| `CMD`          | Default command                       | `CMD ["python", "app.py"]`           |
| `ENTRYPOINT`   | Override container defaults           | `ENTRYPOINT ["python"]`              |
| `ENV`          | Set environment variables             | `ENV FLASK_APP=app.py`               |
| `HEALTHCHECK`  | Health probe                          | `HEALTHCHECK --interval=30s --cmd ...`|

---

### **3.2 Kubernetes Manifest Fields**
| **Field**               | **Purpose**                          | **Example**                          |
|-------------------------|---------------------------------------|--------------------------------------|
| `apiVersion`            | Kubernetes API version                | `apiVersion: apps/v1`                |
| `kind`                  | Resource type (Deployment, Service)   | `kind: Deployment`                   |
| `metadata.name`         | Resource name                         | `name: my-app`                       |
| `spec.replicas`         | Number of pod instances               | `replicas: 3`                        |
| `spec.template.spec containers` | Container spec          | `- image: myusername/my-app:1.0`     |
| `spec.selector`         | Pod matching labels                   | `matchLabels: { app: my-app }`       |
| `spec.template.spec containers ports` | Container ports | `- containerPort: 3000`             |

---

## **4. Query Examples**

### **4.1 Docker CLI Commands**
| **Task**                          | **Command**                                  |
|-----------------------------------|----------------------------------------------|
| List running containers           | `docker ps`                                  |
| Inspect a container               | `docker inspect <container_id>`             |
| Build an image                     | `docker build -t my-image:tag .`             |
| Push to a registry                 | `docker push myusername/my-image:tag`        |
| Run with volume attachment         | `docker run -v /host/path:/container/path ...`|
| Show container logs                | `docker logs <container_id>`                |

---

### **4.2 Kubernetes CLI Commands**
| **Task**                          | **Command**                                  |
|-----------------------------------|----------------------------------------------|
| List pods                         | `kubectl get pods`                           |
| Describe a pod                     | `kubectl describe pod <pod-name>`           |
| Roll out a deployment              | `kubectl rollout status deployment/my-app`   |
| Scale a deployment                 | `kubectl scale deployment/my-app --replicas=5`|
| Expose a service                   | `kubectl expose deployment/my-app --port=3000 --type=LoadBalancer` |

---

### **4.3 Common Errors & Fixes**
| **Error**                          | **Cause**                                      | **Solution**                              |
|-------------------------------------|------------------------------------------------|-------------------------------------------|
| `ImagePullBackOff`                  | Registry auth issue or missing image           | Check `kubectl describe pod` for errors.   |
| `CrashLoopBackOff`                  | App crashes on startup                        | Review logs: `kubectl logs <pod>`         |
| `OOMKilled`                         | Memory limits exceeded                        | Increase `limits.memory` in YAML.         |
| `Connection refused`                | Port misconfiguration                          | Verify `ports` in Deployment/Service.     |

---

## **5. Related Patterns**
1. **[Microservices Architecture]**
   - Use containers to deploy microservices with clear boundaries and independent scalability.

2. **[Infrastructure as Code (IaC)]**
   - Combine containers with Terraform or Pulumi to provision clusters (e.g., EKS, AKS) programmatically.

3. **[Blue-Green Deployment]**
   - Deploy containers in parallel environments to minimize downtime during updates.

4. **[Canary Releases]**
   - Gradually roll out container updates to a subset of users for testing.

5. **[Serverless Containers]**
   - Use platforms like AWS Fargate or Azure Container Instances for event-driven container scaling.

6. **[Security Hardening]**
   - Apply patterns like **non-root user privileges**, **read-only filesystems**, and **image scanning** (e.g., Trivy, Clair).

7. **[Observability]**
   - Integrate containers with distributed tracing (Jaeger) and metrics (Prometheus) for debugging.

8. **[Hybrid Cloud Deployment]**
   - Run containers on-premises (e.g., OpenShift) or in the cloud (e.g., ECS, GKE) using the same manifests.

---
## **6. Best Practices Checklist**
- [ ] Use **minimal base images** (e.g., `alpine`, `distroless`).
- [ ] **Immutable infrastructure**: Avoid modifying running containers.
- [ ] **Tag images semantically** (e.g., `v1.0.0`, `sha-abc123`).
- [ ] **Leverage secrets management** (e.g., Kubernetes Secrets, Vault).
- [ ] **Test locally** with `docker-compose` before cloud deployment.
- [ ] **Monitor resource usage** and adjust limits dynamically.
- [ ] **Automate security scans** in CI/CD pipelines (e.g., Docker Bench Security).

---
**Next Steps**: Combine this pattern with **Kubernetes Auto-Scaling** or **GitOps** (ArgoCD) for advanced workflows.