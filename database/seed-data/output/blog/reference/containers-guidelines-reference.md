# **[Pattern] Containers Guidelines Reference Guide**

---

## **1. Overview**
The **Containers Guidelines** pattern standardizes best practices for defining, deploying, and managing containerized applications. This ensures consistency, reproducibility, and portability across environments. Key components include:
- **Container Image Standards**: Defining image structure, layering, and optimization.
- **Resource Allocation**: Specifying CPU, memory, and storage limits.
- **Security**: Enforcing minimal base images, non-root users, and vulnerability scanning.
- **Orchestration Compatibility**: Aligning with Kubernetes (K8s), Docker Swarm, or other container runtimes.
- **Observability**: Embedding logging, monitoring, and health checks.

This guide provides implementation details, requirements, and examples for adoption.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Container Image Best Practices**
| **Concept**            | **Description**                                                                 | **Implementation**                                                                 |
|------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Base Image Minimalism** | Use lightweight, secure base images (e.g., `alpine`, `distroless`).            | Avoid `ubuntu`/`centos` in favor of `gcr.io/distroless/base-debian12`.            |
| **Layer Caching**      | Optimize Dockerfiles to reuse cached layers (e.g., multi-stage builds).      | Example: `RUN apt-get update && apt-get install -y <packages> --no-install-recommends`. |
| **Image Size Limits**  | Enforce size thresholds (e.g., <500MB for production).                         | Use `docker-slim` or `distroless` to reduce image size.                          |
| **Vulnerability Scanning** | Scan images for CVEs (e.g., using `docker scan` or Trivy).                   | Automate scans in CI/CD pipelines.                                               |
| **Immutable Tags**     | Use semantic versioning (`v1.0.0`, not `:latest`).                             | Avoid `latest` tags in production deployments.                                   |

### **2.2 Resource Allocation**
Configure resources in Kubernetes manifests (`resources.requests/limits`):
```yaml
resources:
  requests:
    cpu: "500m"   # 0.5 CPU
    memory: "256Mi"
  limits:
    cpu: "1000m"  # 1 CPU
    memory: "512Mi"
```
- **Best Practice**: Start with `requests` equal to `limits` for predictable behavior.

### **2.3 Security Guidelines**
| **Requirement**          | **Implementation**                                                                 |
|--------------------------|----------------------------------------------------------------------------------|
| **Non-Root Execution**   | Run containers as non-root users (e.g., `USER 1000` in Dockerfile).              |
| **Read-Only Filesystems** | Mount critical volumes as `readonly`.                                            |
| **Secrets Management**   | Use Kubernetes Secrets or external secret managers (e.g., HashiCorp Vault).      |
| **Network Policies**     | Restrict pod-to-pod communication unless explicitly allowed.                   |

### **2.4 Orchestration Compatibility**
- **Kubernetes**: Adhere to [Best Practices for Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-resources/).
- **Docker Compose**: Use `deploy.resources` for constraints.
- **Multi-Architecture**: Build images for multiple platforms (e.g., `linux/amd64`, `linux/arm64`).

### **2.5 Observability**
- **Logging**: Use structured logs (e.g., JSON) and standardize formatters.
- **Metrics**: Expose Prometheus endpoints or use OpenTelemetry.
- **Health Checks**: Define `livenessProbe` and `readinessProbe` in Kubernetes.

---

## **3. Schema Reference**
### **3.1 Container Image Schema**
| **Field**               | **Type**       | **Required** | **Description**                                                                 | **Example**                     |
|-------------------------|----------------|--------------|-------------------------------------------------------------------------------|--------------------------------|
| `baseImage`             | String         | Yes          | Official image name (e.g., `gcr.io/distroless/base-debian12`).                  | `alpine:3.18`                  |
| `maintainer`            | String         | No           | Contact for image maintenance.                                                | `team@company.com`              |
| `sizes`                 | Object         | Yes          | Image size constraints (MB).                                                  | `{"production": 450}`          |
| `securityScan`          | Boolean        | Yes          | Whether vulnerability scanning is enabled.                                    | `true`                          |
| `entrypoint`            | Array          | Optional     | Override default entrypoint (e.g., `["sh", "-c", "your-command"]`).           | `["app", "server"]`             |

**Example JSON:**
```json
{
  "baseImage": "gcr.io/distroless/base-debian12",
  "maintainer": "team@company.com",
  "sizes": {
    "production": 450,
    "development": 200
  },
  "securityScan": true,
  "entrypoint": ["app", "--config", "/etc/config.yaml"]
}
```

### **3.2 Kubernetes Pod Schema**
| **Field**               | **Type**       | **Required** | **Description**                                                                 | **Example**                     |
|-------------------------|----------------|--------------|-------------------------------------------------------------------------------|--------------------------------|
| `containers`            | Array          | Yes          | List of container specs.                                                      | `[{"name": "web", "image": "..."}]` |
| `resourceRequests`      | Object         | Optional     | CPU/memory requests.                                                          | `{"cpu": "500m", "memory": "256Mi"}` |
| `securityContext`       | Object         | Optional     | Security settings (e.g., `runAsNonRoot: true`).                                | `{"runAsNonRoot": true, "user": 1001}` |
| `healthChecks`          | Object         | Optional     | Liveness/readiness probes.                                                    | `{"livenessProbe": {"httpGet": {}}}` |

**Example YAML:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
    - name: my-app
      image: "my-registry/my-app:v1.0.0"
      resources:
        requests:
          cpu: "500m"
          memory: "256Mi"
      securityContext:
        runAsNonRoot: true
        user: 1001
      livenessProbe:
        httpGet:
          path: /health
          port: 8080
```

---

## **4. Query Examples**

### **4.1 Querying Compliance with Security Rules**
**Use Case**: Verify if a container image meets security standards.
**Command**:
```bash
docker scan --file container-spec.json
```
**Output**:
```json
{
  "securityScore": 9.2,
  "vulnerabilities": [
    {"package": "libcurl", "severity": "Medium", "fixedVersion": "7.88.1"}
  ],
  "compliance": {
    "runAsNonRoot": true,
    "readOnlyRootFilesystem": false
  }
}
```

### **4.2 Querying Resource Usage in Kubernetes**
**Use Case**: Check if a pod is under resource constraints.
**Command**:
```bash
kubectl describe pod my-app | grep -E "Requests|Limits|CPU|Memory"
```
**Output**:
```
    cpu:        500m
    memory:     256Mi (requests)
    cpu:        1000m
    memory:     512Mi (limits)
```

### **4.3 Querying Image Size**
**Use Case**: Verify image size meets guidelines.
**Command**:
```bash
docker inspect --format='{{.Size}}' my-image | numfmt --to=iec
```
**Output**:
```
450MiB
```

---

## **5. Related Patterns**
1. **[Infrastructure as Code (IaC)](https://learn.microsoft.com/en-us/azure/architecture/framework/cloud-adoption-models/iac)**
   - Aligns container deployments with IaC tools like Terraform or Pulumi.

2. **[Zero-Trust Security](https://learn.microsoft.com/en-us/security/zero-trust/overview)**
   - Extends container security with principles like least privilege and continuous authentication.

3. **[Microservices Architectures](https://microservices.io/)**
   - Containers are foundational for deploying microservices independently.

4. **[Service Mesh (e.g., Istio)](https://istio.io/latest/docs/concepts/what-is-istio/)**
   - Enhances observability, security, and traffic management for containerized apps.

5. **[GitOps](https://www.gitops.tech/)**
   - Use Git repositories to manage container deployments (e.g., ArgoCD).

---
### **6. References**
- [CNCF Best Practices for Images](https://github.com/hypnoglow/container-best-practices)
- [Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#resource-requests-and-limits)
- [Distroless Images](https://github.com/GoogleContainerTools/distroless)