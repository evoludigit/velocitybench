# **[Pattern] Containers Approaches Reference Guide**

---

## **Overview**
The **Containers Approaches** pattern provides standardized ways to package, deploy, and manage applications and dependencies in portable, isolated environments called **containers**. Unlike traditional virtual machines (VMs), containers share the host OS kernel while encapsulating application code, runtime, libraries, and configuration. This pattern ensures consistency across development, testing, staging, and production environments, reducing conflicts like "works on my machine" issues. Key approaches include **Docker** (runtime), **Kubernetes** (orchestration), and **container registries** (storage/retrieval). This guide covers implementation strategies, schema references, and query examples for integrating containers into architecture.

---

## **Implementation Details**

### **1. Core Concepts**
| **Term**               | **Description**                                                                                     | **Key Considerations**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Container**           | Lightweight, standalone executable with packaged dependencies.                                       | Runs directly on the host OS kernel (no full VM overhead).                           |
| **Image**               | Read-only template with application code, dependencies, and configurations.                        | Created via a **Dockerfile** or pre-built (e.g., from Hub/Docker Registry).          |
| **Container Runtime**   | Software managing container lifecycle (e.g., Docker Engine, containerd).                           | Handles isolation, networking, and storage.                                           |
| **Orchestration**       | Tools managing container deployment, scaling, and networking (e.g., Kubernetes, Docker Swarm).     | Required for multi-container apps, load balancing, and self-healing.                  |
| **Registry**            | Centralized repository for storing/sharing container images (e.g., Docker Hub, AWS ECR).           | Ensures version control and security (authentication, scanning).                   |
| **Volumes**             | Persistent storage for container data (e.g., databases, user uploads).                             | Detached from container lifecycle; critical for stateful apps.                       |
| **Networking**          | Isolated or shared networks for inter-container communication.                                       | Use Docker networks or Kubernetes Services for service discovery.                     |
| **Security Context**    | Mechanisms like user namespace mapping, read-only filesystems, and SELinux/AppArmor policies.      | Mitigates privilege escalation risks.                                                  |

---

### **2. Common Implementation Strategies**
#### **A. Single-Container Approach**
- **Use Case**: Simple apps (e.g., static websites, microservices with no dependencies).
- **Steps**:
  1. Write a **Dockerfile** to define the image.
     ```dockerfile
     FROM nginx:alpine
     COPY . /usr/share/nginx/html
     EXPOSE 80
     ```
  2. Build and run:
     ```sh
     docker build -t my-nginx .
     docker run -p 8080:80 my-nginx
     ```
- **Pros**: Simple, fast startup.
- **Cons**: No built-in scaling or service discovery.

#### **B. Multi-Container Approach**
- **Use Case**: Apps requiring multiple services (e.g., frontend + backend + database).
- **Tools**: Docker Compose, Kubernetes.
- **Example (Docker Compose)**:
  ```yaml
  version: '3'
  services:
    web:
      image: nginx
      ports:
        - "80:80"
    db:
      image: postgres
      environment:
        POSTGRES_PASSWORD: example
  ```
  Run with:
  ```sh
  docker-compose up -d
  ```

#### **C. Orchestrated Approach (Kubernetes)**
- **Use Case**: Scalable, production-grade deployments with auto-healing.
- **Key Components**:
  - **Deployments**: Manage pod replicas.
  - **Services**: Expose pods internally/externally.
  - **Ingress**: HTTP routing (e.g., Nginx Ingress Controller).
- **Example YAML (Deployment)**:
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
      spec:
        containers:
        - name: my-app
          image: my-app:latest
          ports:
          - containerPort: 80
  ```

#### **D. Serverless Containers**
- **Use Case**: Event-driven workloads (e.g., AWS Fargate, Google Cloud Run).
- **Key Features**:
  - Auto-scaling based on demand.
  - Pay-per-use pricing.
- **Example (AWS ECS Fargate)**:
  ```yaml
  # Task Definition (truncated)
  cpu: '256'
  memory: '512'
  containers:
    - name: my-container
      image: my-app:latest
      portMappings:
        - containerPort: 80
  ```

#### **E. Hybrid Approach**
- **Use Case**: Mix of containers and traditional VMs (e.g., Kubernetes + VMs for legacy apps).
- **Tools**: Kubernetes `NodeSelector` or `taints/tolerations` to schedule pods on specific nodes.

---

## **Schema Reference**
| **Component**          | **Schema Example**                                                                 | **Purpose**                                                                 |
|-------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Dockerfile**         | `FROM <image>:<tag>`<br>`COPY . /app`<br>`CMD ["app"]`                           | Defines image layers and runtime behavior.                                  |
| **docker-compose.yml** | `version: '3'`<br>`services:`<br>`  `<service>`: `<br>`    `image: ...`       | Declares multi-container apps for local/dev environments.                    |
| **Kubernetes Pod**     | ```yaml`apiVersion: v1`<br>`kind: Pod`<br>`metadata:`<br>`  name: my-pod`<br>`spec:`<br>`  containers:`<br>`  - name: nginx`<br>`    image: nginx```` | Lightweight unit for one or more containers.                                |
| **Kubernetes Deployment** | ```yaml`apiVersion: apps/v1`<br>`kind: Deployment`<br>`spec:`<br>`  replicas: 2`<br>`  selector:`<br>`    matchLabels:`<br>`      app: nginx```` | Manages pod replicas and rolling updates.                                     |
| **Network Policy (K8s)** | ```yaml`apiVersion: networking.k8s.io/v1`<br>`kind: NetworkPolicy`<br>`metadata:`<br>`  name: deny-all`<br>`spec:`<br>`  podSelector:`<br>`    matchLabels:`<br>`      role: backend`<br>`  policyTypes:`<br>`  - Ingress```` | Restricts pod-to-pod communication (zero-trust).                             |

---

## **Query Examples**

### **1. Docker CLI Queries**
| **Command**                          | **Purpose**                                                                 | **Example Output**                          |
|---------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `docker ps`                          | List running containers.                                                    | `CONTAINER ID   IMAGE         COMMAND`       |
| `docker images`                      | List downloaded images.                                                     | `REPOSITORY   TAG     IMAGE ID`            |
| `docker logs <container>`            | View container logs.                                                        | `[app] info: Starting server...`           |
| `docker exec -it <container> bash`   | Run a shell inside a container.                                             | `# / #` (Bash prompt)                      |
| `docker build -t my-app .`           | Build an image from a Dockerfile.                                            | `Successfully built 123abc456`             |
| `docker run -d -p 5000:5000 my-app`  | Run a container in detached mode with port mapping.                          | `abc123def456` (container ID)               |

---

### **2. Kubernetes Queries**
| **Command**                          | **Purpose**                                                                 | **Example Output**                          |
|---------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `kubectl get pods`                   | List all pods in the namespace.                                             | `NAME        READY   STATUS`                |
| `kubectl describe pod <pod-name>`    | Show pod details (events, logs, IP).                                         | `Events:`<br>`  - {0s} Created container`   |
| `kubectl logs <pod-name>`             | View pod logs.                                                              | `[main] info: Request received`            |
| `kubectl exec -it <pod-name> -- bash`| Execute a shell inside a pod.                                               | `# / #` (Bash prompt)                      |
| `kubectl apply -f deployment.yaml`   | Apply a Kubernetes configuration file.                                       | `deployment.apps/my-app configured`        |
| `kubectl port-forward <pod> 8080:80` | Forward local port to pod port.                                              | `Forwarding from 127.0.0.1:8080 -> 80`     |

---

### **3. Registry Queries**
| **Command/Tool**                     | **Purpose**                                                                 | **Example**                                  |
|---------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `docker pull nginx:alpine`           | Download an image from a registry.                                          | `Pulling from library/nginx`                |
| `docker push my-registry/my-app:1.0` | Upload an image to a registry.                                              | `The push refers to repository`             |
| `aws ecr describe-repositories`       | List ECR repositories (AWS).                                                 | `[REPOSITORY]`                              |
| `skopeo inspect docker://nginx`       | Inspect an image without pulling it.                                         | `Name: nginx`<br>`Tag: alpine`<br>`Digest: ...` |

---

## **Related Patterns**
1. **Microservices Architecture**
   - **Relation**: Containers enable isolated, scalable microservices.
   - **Complement**: Use Kubernetes for service discovery and load balancing.

2. **Infrastructure as Code (IaC)**
   - **Relation**: Define container deployments in Terraform, Pulumi, or Ansible.
   - **Complement**: Tools like **Terraform + Kubernetes Provider** automate environment provisioning.

3. **Service Mesh (e.g., Istio, Linkerd)**
   - **Relation**: Adds observability, security (mTLS), and traffic management to containerized apps.
   - **Complement**: Deploy alongside Kubernetes for advanced networking.

4. **CI/CD Pipelines**
   - **Relation**: Containers ensure consistency in build/test/deploy stages.
   - **Complement**: Integrate with Jenkins, GitHub Actions, or ArgoCD for automated workflows.

5. **Database as a Service (DBaaS)**
   - **Relation**: Use managed databases (e.g., AWS RDS, MongoDB Atlas) instead of self-hosted in containers.
   - **Complement**: Connect containers to DBaaS via environment variables or service discovery.

6. **Serverless Containers**
   - **Relation**: Run containers without managing infrastructure (e.g., AWS Fargate, Knative).
   - **Complement**: Ideal for sporadic workloads (e.g., batch processing).

7. **Security Hardening**
   - **Relation**: Apply security best practices (e.g., minimal base images, non-root users).
   - **Complement**: Use tools like **Trivy**, **Anchore**, or **Docker Bench**.

---

## **Best Practices**
1. **Minimize Image Size**
   - Use multi-stage builds to reduce attack surface.
   - Example:
     ```dockerfile
     # Build stage
     FROM golang:1.21 as builder
     WORKDIR /app
     COPY . .
     RUN go build -o myapp

     # Runtime stage
     FROM alpine:latest
     COPY --from=builder /app/myapp /myapp
     CMD ["/myapp"]
     ```

2. **Use Read-Only Filesystems**
   - Mitigate risks from accidental writes:
     ```sh
     docker run --read-only my-app
     ```

3. **Leverage Secrets Management**
   - Avoid hardcoding secrets in images. Use:
     - Kubernetes Secrets or ConfigMaps.
     - Docker secrets (Swarm mode).
     - External vaults (HashiCorp Vault, AWS Secrets Manager).

4. **Monitor Performance**
   - Tools: Prometheus + Grafana, Kubernetes Metrics Server.
   - Metrics to track: CPU/memory usage, latency, pod restart frequency.

5. **Implement Rollback Strategies**
   - Kubernetes: Use `kubectl rollout undo`.
   - Docker: Manage image tags and roll back to previous versions.

6. **Adopt Immutable Infrastructure**
   - Never modify running containers. Instead, rebuild and redeploy.

7. **Plan for Scaling**
   - Use horizontal pod autoscaling (Kubernetes) or Docker Swarm scaling.

---

## **Troubleshooting**
| **Issue**                          | **Diagnostic Commands**                          | **Solution**                                  |
|-------------------------------------|---------------------------------------------------|-----------------------------------------------|
| Container fails to start            | `docker logs <container>`                        | Check for missing dependencies or config errors. |
| Slow performance                    | `kubectl top pods`                               | Optimize resource requests/limits in Deployment. |
| Network connectivity issues          | `kubectl get endpoints`                          | Verify Service DNS resolution and Ingress rules. |
| Image pull errors                   | `docker pull --debug my-image`                   | Check registry permissions or network proxy.   |
| Persistent volume corruption        | `kubectl describe pvc <pvc-name>`                | Restore from backup or recreate PVC.          |

---
**Reference Documentation End**