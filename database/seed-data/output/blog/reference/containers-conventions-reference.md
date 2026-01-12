# **[Pattern] Containers Conventions Reference Guide**

---

## **Overview**
The **Containers Conventions** pattern defines standardized structures, naming, and metadata conventions for packaging and deploying software components, microservices, APIs, or full applications into **containers**. This pattern ensures consistency, interoperability, and operational efficiency across containerized deployments.

Key use cases include:
- **Development & Testing:** Enforces uniform container construction for CI/CD pipelines.
- **Infrastructure as Code (IaC):** Facilitates reproducible environments via standardized container definitions.
- **Multi-Environment Deployments:** Simplifies scaling across dev/staging/production with predictable configurations.
- **Security & Compliance:** Reduces attack surfaces by defining secure default conventions (e.g., non-root user execution).

By adhering to these conventions, teams avoid fragmented tooling and manual errors, enabling seamless integration with orchestrators like Kubernetes (K8s), Docker, or serverless platforms.

---

## **Schema Reference**
This section outlines the **mandatory** and **recommended** fields for container definitions (primarily applied to `Dockerfile`, `docker-compose.yml`, and K8s manifests). Fields are categorized by purpose:

| **Category**       | **Field**               | **Type**       | **Description**                                                                                     | **Required?** | **Default**                     | **Notes**                                                                                     |
|--------------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------|----------------------------------|-----------------------------------------------------------------------------------------------|
| **Metadata**       | `NAME`                  | String         | Unique identifier for the container (e.g., `app-auth-service`).                                        | ✅             | –                                | Must align with CI/CD naming policies.                                        |
|                    | `VERSION`               | SemVer         | Semantic version of the container image (e.g., `1.2.3`).                                        | ✅             | –                                | Use tags like `:latest` sparingly.                                            |
|                    | `DESCRIPTION`           | String         | High-level purpose of the container (e.g., "Handles user authentication via JWT").                | ❌             | –                                | Critical for tooltips and documentation.                                         |
|                    | `MAINTAINER`            | String/Email   | Author/contacts for the container.                                                                    | ❌             | –                                | Include PGP keys or Slack channels for security updates.                                |
| **Security**       | `RUN_AS_USER`           | Integer/String | Non-root user UID/GID (e.g., `1000`).                                                                  | ✅             | `1000`                            | Hardened by default; exceptions require audit.                                     |
|                    | `ENTRYPOINT_USER`       | String         | User for entrypoint execution (e.g., `appuser`).                                                     | ✅             | Same as `RUN_AS_USER`              | Override via env vars if needed.                                                 |
|                    | `NON_ROOT`              | Boolean        | Flag to enforce non-root execution (deprecated; use `RUN_AS_USER`).                                  | ❌             | `true`                            | Only for legacy systems.                                                          |
| **Dependencies**   | `BASE_IMAGE`            | String         | Official image (e.g., `ubuntu:22.04`, `python:3.10-slim`).                                            | ✅             | –                                | Prefer distro-specific tags (e.g., `alpine` over `ubuntu`).                     |
|                    | `DEPENDENCIES`          | Array[String]  | List of package managers/commands (e.g., `["apt-get update", "pip install -r requirements.txt"]`).| ❌             | –                                | Group into layers (e.g., `apt`, `npm`) for cache efficiency.                     |
| **Ports**          | `EXPOSE`                | Array[Int]     | Network ports (e.g., `[8000, 9090]`).                                                                  | ✅             | –                                | Must match service descriptions.                                                 |
| **Environment**    | `ENV_VARS`              | Key-Value      | Configurable variables (e.g., `{"DB_HOST": "postgres", "DEBUG": "true"}`).                         | ❌             | –                                | Use `.env` files for secrets.                                                      |
|                    | `HEALTHCHECK`           | Object         | Liveness/ready probes (e.g., `{"test": "curl -f http://localhost:8080/health || exit 1"}`).         | ❌             | –                                | Required for orchestrators like K8s.                                                  |
| **Optimizations**  | `CACHE_LAYERS`          | Array[String]  | Commands to cache (e.g., `["RUN apt-get install -y nginx"]`).                                        | ❌             | –                                | Reduces rebuild times.                                                          |
|                    | `MULTI_STAGE`           | Boolean        | Enables multi-stage builds (default: `true`).                                                      | ❌             | `true`                            | Reduces final image size.                                                          |
| **Observability**  | `LOGGING`               | Object         | Format/log drivers (e.g., `{"driver": "json-file", "options": {"max-size": "10m"}}`).              | ❌             | `json-file`                      | Critical for monitoring.                                                          |
| **Secrets**        | `SECRET_MOUNT`          | Array[String]  | Paths for mounted secrets (e.g., `["/path/to/config.yaml"]`).                                        | ❌             | –                                | Use Kubernetes Secrets or HashiCorp Vault.                                         |

---

## **Implementation Details**

### **1. Container Naming Conventions**
- **Format:** `{project}-{service}-{type}` (e.g., `user-service-auth-app`, `db-postgres-db`).
- **Type Suffixes:**
  - `-app`: Application containers.
  - `-db`: Databases.
  - `-mq`: Message queues (e.g., RabbitMQ).
  - `-proxy`: Reverse proxies (e.g., `nginx`).
- **Version Tagging:**
  - Use **Semantic Versioning (SemVer)** for tags (e.g., `v1.0.0`).
  - Avoid `:latest` in production; prefer explicit tags.

### **2. Dockerfile Best Practices**
```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm run build

# Stage 2: Runtime
FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json .
ENV NODE_ENV=production
RUN_AS_USER 1000
ENTRYPOINT ["node", "dist/server.js"]
```
**Key Rules:**
- **Layer Caching:** Group `RUN` commands by dependency type (e.g., `apt-get`, `npm`).
- **Minimal Base Images:** Prefer `alpine` or distro-specific images (e.g., `python:3.10-slim`).
- **Non-Root Execution:** Always set `RUN_AS_USER` and `ENTRYPOINT_USER`.

### **3. Kubernetes Manifests**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: auth-service
        image: myregistry/auth-service:v1.2.3
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        securityContext:
          runAsUser: 1000
          readOnlyRootFilesystem: true
```

**Critical Fields:**
- **`securityContext`:** Enforce `runAsUser: 1000` and `readOnlyRootFilesystem: true`.
- **Probes:** Always define `livenessProbe` and `readinessProbe`.
- **Resource Limits:** Set `requests` and `limits` for CPU/memory.

### **4. Secrets Management**
- **Never hardcode secrets** in images or manifests.
- **Options:**
  - **Kubernetes Secrets:** Base64-encoded in `kubectl create secret`.
  - **Vault:** Dynamic secrets via environment variables.
  - **CI/CD Variables:** Passed at runtime (e.g., GitHub Actions secrets).

Example (K8s):
```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: password
```

### **5. Health Checks**
Define health checks in the container’s entry script or `Dockerfile`:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1
```
- **Liveness Probe:** Restarts unhealthy containers.
- **Readiness Probe:** Blocks traffic until the container is ready.

---

## **Query Examples**
### **1. Finding Containers by Tag**
```bash
# List all containers with a specific tag (e.g., "v1.0.0")
docker search --filter=tag="v1.0.0" myregistry
```
**Output:**
```
NAME                          TAG                    DESCRIPTION
myregistry/auth-service       v1.0.0                 Handles JWT authentication...
```

### **2. Validating a Dockerfile for Conventions**
Use `hadolint` to enforce conventions:
```bash
# Install hadolint
wget https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
chmod +x hadolint-Linux-x86_64

# Run linter
./hadolint-Linux-x86_64 Dockerfile
```
**Example Output:**
```
# DL3008 Consider using "--no-cache" flag for layers that don't need caching
RUN npm install
```

### **3. Querying Kubernetes for Non-Compliant Pods**
```bash
# Find pods without securityContext
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[0].securityContext}{"\n"}{end}'
```
**Output:**
```
default   auth-service   {"runAsUser":1000,"readOnlyRootFilesystem":true}
default   legacy-app     {}  # Non-compliant (no securityContext)
```

### **4. Generating a Container Bill of Materials (BOM)**
Use `cosc` (Container Security Context) to scan images:
```bash
# Install cosc (CLI tool)
brew install cosc

# Generate BOM for an image
cosc scan myregistry/auth-service:v1.0.0
```
**Output Snippet:**
```
VULNERABILITIES:
- CVE-2022-1234 (Critical): openssl@1.1.1
DEPENDENCIES:
- node:18-alpine (120MB)
- python:3.10-slim (350MB)
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Image Scanning](link)**       | Automated vulnerability scanning for container images.                                               | Before deploying to production or CI/CD pipelines.                                                   |
| **[Immutable Infrastructure](link)** | Treating containers as ephemeral and non-persistent.                                              | For stateless services or cloud-native deployments.                                                   |
| **[Configuration as Code](link)** | Managing container configs via tools like Kubernetes ConfigMaps/Secrets.                          | When environments require dynamic configurations (e.g., staging vs. prod).                          |
| **[Service Mesh](link)**         | Managing inter-container traffic, observability, and security (e.g., Istio, Linkerd).               | For microservices with complex networking needs (e.g., gRPC, mTLS).                                   |
| **[GitOps](link)**               | Deploying containers via Git-driven workflows (e.g., ArgoCD, Flux).                                | For declarative, auditable deployments.                                                             |

---

## **Additional Resources**
- [CNCF Container Conventions Guide](https://github.com/cncf/container-conventions)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Kubernetes Security Contexts](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Hadolint (Dockerfile Linter)](https://github.com/hadolint/hadolint)