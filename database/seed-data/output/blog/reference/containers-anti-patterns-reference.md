# **[Pattern] Containers Anti-Patterns Reference Guide**

---

## **Overview**
Containers—lightweight, portable, and isolated environments—are widely adopted for modern cloud-native and microservices architectures. However, improper use introduces inefficiencies, security risks, and operational headaches. This guide documents **anti-patterns** in container deployment, highlighting common pitfalls, their impact, and mitigation strategies. Mastery of these patterns helps engineers avoid resource waste, scalability bottlenecks, and security vulnerabilities.

---

## **Schema Reference**
| **Anti-Pattern Name**               | **Description**                                                                                     | **Impact**                                                                                                                   | **Mitigation Strategy**                                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Monolithic Container**             | Running a massive, multi-process application in a single container.                                    | High CPU/memory usage, slow startup, difficulty scaling individual components.                                             | Break into microservices; use sidecars or init containers for dependencies.                                    |
| **Unoptimized Image Layers**         | Large, bloated base images (e.g., `FROM ubuntu:latest`) with unnecessary packages.                  | Slow pulls, higher storage costs, longer image builds.                                                                     | Use lightweight bases (e.g., `alpine`, `distroless`), multi-stage builds, and `.dockerignore`.                   |
| **Fixed vs. Dynamic Resource Limits**| Hardcoding CPU/memory limits to extreme values (e.g., `--mem=unlimited`) or too restrictive values.   | Starvation of resources or wasted capacity.                                                                               | Set realistic, dynamic limits (e.g., 80% of node capacity for stateless apps).                                   |
| **Improper Volume Persistence**       | Mounting host directories or using anonymous volumes without backups or snapshots.                | Data loss risk, no versioning, difficult rollbacks.                                                                         | Use named volumes with PersistentVolumeClaims (K8s) or volume snapshots.                                         |
| **Hardcoded Configurations**         | Embedding secrets, credentials, or settings directly in container configs (e.g., `ENV X=123`).    | Security risks, single point of failure, no flexibility.                                                                 | Use ConfigMaps/Secrets (K8s) or environment variables from orchestration systems.                                |
| **Ignoring Liveness/Readiness Probes**| Skipping health checks for container applications.                                                   | Undetected crashes, traffic routed to unhealthy pods, degraded user experience.                                             | Implement `/health` endpoints and configure probes in deployments.                                              |
| **Overuse of `latest` Tags**         | Deploying containers using untagged or `latest` images without version control.                   | Inconsistent behavior, accidental rollbacks, no audit trail.                                                               | Always use versioned tags (e.g., `app:1.2.3`).                                                                     |
| **Chaining Containers**              | Linking containers via `docker run --link` or legacy orchestration tricks.                            | Single point of failure, poor network isolation, tighter coupling.                                                       | Use DNS-based service discovery (e.g., K8s services) or sidecar patterns.                                       |
| **No Resource Monitoring**           | Lack of observability tools (logs, metrics, traces) for containers.                                  | Blind spots in performance tuning, slow incident resolution.                                                                | Integrate Prometheus + Grafana for metrics, ELK for logs, and OpenTelemetry for tracing.                        |
| **Ignoring Security Scanning**       | Deploying containers without vulnerability scans.                                                     | Exploitable CVEs, data breaches.                                                                                           | Scan images with Trivy, Clair, or Snyk; use `Dockerfile.scan()` in pipelines.                                      |
| **Mismatched Container Orchestration**| Overusing Docker Swarm for production or ignoring K8s best practices (e.g., no HPA, no RBAC).     | Poor scaling, security gaps, operational overhead.                                                                            | Adopt cloud-native orchestration (K8s/AWS ECS) with autoscaling policies and RBAC.                                |

---

## **Key Concepts & Implementation Details**

### **1. Monolithic Container**
**Why it’s bad**: A single container running multiple processes violates container isolation principles, making debugging and scaling harder.
**Example**:
```dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y nginx mysql
```
**Fix**:
- Split into separate containers (e.g., `nginx`, `mysql`).
- Use **init containers** for setup tasks:
  ```yaml
  # K8s init container example
  initContainers:
  - name: db-setup
    image: postgres:13
    command: ['sh', '-c', 'until pg_isready -U postgres; do sleep 1; done']
  ```

### **2. Unoptimized Image Layers**
**Why it’s bad**: Every layer in a Dockerfile adds to image size and pull time.
**Example**:
```dockerfile
FROM ubuntu:latest           # 300MB
RUN apt-get update           # 100MB
RUN apt-get install -y nginx # 50MB
```
**Fix**:
- Use **multi-stage builds**:
  ```dockerfile
  # Build stage
  FROM golang:1.21 as builder
  WORKDIR /app
  COPY . .
  RUN CGO_ENABLED=0 go build -o /app/app

  # Runtime stage
  FROM alpine:latest
  COPY --from=builder /app/app /app/app
  ```
- Exclude unnecessary files with `.dockerignore`:
  ```
  node_modules/
  *.log
  ```

### **3. Fixed vs. Dynamic Resource Limits**
**Why it’s bad**: Static limits may leave resources idle or crash under load.
**Example**:
```yaml
# Too restrictive (OOM kills)
resources:
  limits:
    memory: "64Mi"
    cpu: "200m"
```
**Fix**:
- Use **requests/limits** dynamically:
  ```yaml
  resources:
    requests:
      cpu: "100m"
      memory: "256Mi"
    limits:
      cpu: "1"
      memory: "512Mi"
  ```
- Enable **Horizontal Pod Autoscaler (HPA)** for stateless apps:
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: app-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: app
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
  ```

### **4. Improper Volume Persistence**
**Why it’s bad**: Anonymous volumes or host mounts lack durability.
**Example**:
```yaml
volumes:
- name: data
  emptyDir: {}  # Ephemeral; lost on pod restart
```
**Fix**:
- Use **PersistentVolumeClaims (PVC)**:
  ```yaml
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: mysql-pvc
  ```
- Enable **volume snapshots** for backups:
  ```bash
  kubectl velero create snapshot --include-namespaces=default
  ```

### **5. Hardcoded Configurations**
**Why it’s bad**: Secrets in configs violate the **12-factor app** principle.
**Example**:
```dockerfile
ENV DB_PASSWORD="s3cr3t"
```
**Fix**:
- Use **ConfigMaps/Secrets** (K8s):
  ```yaml
  envFrom:
  - secretRef:
      name: db-secrets
  ```
- Rotate secrets via **Vault** or **AWS Secrets Manager**:
  ```bash
  kubectl create secret generic db-creds --from-literal=password=$(vault read secret/db/password)
  ```

### **6. Ignoring Liveness/Readiness Probes**
**Why it’s bad**: Pods marked "ready" but unresponsive cause traffic blackholing.
**Example**:
```yaml
# Missing probes
livenessProbe: {}
readinessProbe: {}
```
**Fix**:
- Define probes in deployments:
  ```yaml
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30
    periodSeconds: 10
  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 5
  ```

### **7. Overuse of `latest` Tags**
**Why it’s bad**: Untagged images break CI/CD reproducibility.
**Example**:
```dockerfile
# Bad
FROM python:latest
```
**Fix**:
- Tag images with **semantic versioning**:
  ```bash
  docker build -t myapp:1.2.3 .
  docker push myapp:1.2.3
  ```

### **8. Chaining Containers**
**Why it’s bad**: Explicit networking links create tight coupling.
**Example**:
```bash
# Legacy Docker link
docker run -d --name db mysql
docker run --link db:dbapp myapp
```
**Fix**:
- Use **K8s Services** for DNS-based discovery:
  ```yaml
  apiVersion: v1
  kind: Service
  metadata:
    name: mysql
  spec:
    selector:
      app: mysql
    ports:
    - protocol: TCP
      port: 3306
      targetPort: 3306
  ```

### **9. No Resource Monitoring**
**Why it’s bad**: Lack of observability hides performance issues.
**Example**:
```dockerfile
# No logging/config for monitoring
```
**Fix**:
- Integrate **Prometheus + Grafana** for metrics:
  ```yaml
  # Prometheus scrape config
  - job_name: 'myapp'
    static_configs:
    - targets: ['myapp:8080']
  ```
- Use **Fluentd** for centralized logs:
  ```yaml
  containers:
  - name: fluentd
    image: fluent/fluentd
    volumes:
    - ./fluent.conf:/fluentd/etc/fluent.conf
  ```

### **10. Ignoring Security Scanning**
**Why it’s bad**: Vulnerable images risk exploits.
**Example**:
```bash
# No vulnerability checks
docker build -t myapp .
```
**Fix**:
- Scan images pre-deploy:
  ```bash
  # Use Trivy
  trivy image myapp:latest
  ```
- Automate scans in CI/CD pipelines:
  ```yaml
  # GitHub Actions example
  - name: Run Trivy Scan
    uses: aquasecurity/trivy-action@master
    with:
      image-ref: 'myapp:latest'
  ```

### **11. Mismatched Orchestration**
**Why it’s bad**: Docker Swarm lacks K8s features like HPA or RBAC.
**Example**:
```bash
# Swarm mode without scaling
docker service create --name myapp myapp:latest
```
**Fix**:
- Migrate to **Kubernetes** for production:
  ```bash
  kubectl create deployment myapp --image=myapp:1.2.3
  kubectl expose deployment myapp --port=80
  ```

---

## **Query Examples**
### **1. Finding Containers with No Resource Limits**
```bash
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{"N/A"}{"\t"}{.spec.container[*].resources}{"\n"}{end}' \
  | grep -E '"requests|limits"' | grep -v "limits:\ null"
```

### **2. Detecting Pods with Missing Liveness Probes**
```bash
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].livenessProbe}{"\n"}{end}' \
  | grep -v '"initialDelaySeconds"'
```

### **3. Listing Images with `latest` Tags**
```bash
docker images | grep "latest" | awk '{print $1":"$2}'
```

### **4. Checking for Unused PersistentVolumes**
```bash
kubectl get pv --no-headers | awk '{print $1}' | xargs -I {} kubectl describe pv {} | grep -E "Status|Claims"
```

### **5. Scanning Vulnerabilities in a Container Image**
```bash
trivy image nginx:latest --exit-code 1
```

---

## **Related Patterns**
1. **[Container Best Practices]** – Companion guide for correct container design.
2. **[Microservices Decomposition]** – Strategies for splitting monolithic apps.
3. **[Kubernetes Optimization]** – Scaling, networking, and resource tuning.
4. **[Security Hardening for Containers]** – Secrets management, runtime security.
5. **[CI/CD for Containers]** – Automated builds, scans, and deployments.

---
**References**:
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes/)
- [Twelve-Factor App](https://12factor.net/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)