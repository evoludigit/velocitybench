# **[Containers Patterns] Reference Guide**

---

## **Overview**
The **Containers Patterns** group defines standardized ways to organize, deploy, and manage applications using containerization (e.g., Docker, Kubernetes). These patterns ensure consistency, scalability, and portability across environments by abstracting infrastructure concerns into modularized, self-contained units (containers).

Key use cases include:
- **Microservices Deployment:** Isolate services with independent scaling.
- **Portability:** Run applications consistently across dev, staging, and production.
- **Resource Efficiency:** Share host OS kernel resources while maintaining isolation.
- **CI/CD Integration:** Standardized container builds for seamless deployment pipelines.

This guide covers foundational patterns (e.g., *Immutable Containers*, *Sidecars*) and advanced implementations (e.g., *Service Meshes*, *Serverless Containers*).

---

## **Schema Reference**
Below are core patterns with key attributes in tabular format for quick reference.

| **Pattern**               | **Purpose**                                                                 | **Key Components**                          | **Deployment Model**                     | **State Management**       | **Scaling**                     | **Example Use Case**                     |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------|-----------------------------------------|----------------------------|--------------------------------|------------------------------------------|
| **Immutable Containers**  | Prevents runtime modifications; enforces consistency via rebuilt containers. | Docker image, immutable filesystem          | Static (recreate on change)            | Ephemeral                   | Manual/autoscaling (e.g., K8s) | CI/CD pipelines, stateless apps           |
| **Sidecar Pattern**       | Extends container functionality (e.g., logging, monitoring).                | Primary container + sidecar (e.g., Prometheus) | Dynamic (co-located)                   | Persistent (sidecar)        | Horizontal scaling              | Log aggregation, proxy services            |
| **Ambassador Pattern**    | Fronts a service with a reverse proxy (e.g., Nginx, Envoy) for routing.      | Service container + ambassador              | Static (side-by-side)                   | Ephemeral                   | Manual (ambassador)           | API gateways, internal service discovery |
| **Adapter Pattern**       | Connects containers to legacy systems/third-party services.                 | Container + adapter (e.g., Kafka connector)  | Dynamic (orchestrated)                  | Persistent (stateful)       | Manual                      | Data ingestion, legacy integration     |
| **Saga Pattern**          | Manages distributed transactions via choreography or orchestration.        | Multiple containers + event bus (e.g., Kafka)| Dynamic (orchestrated)                  | Persistent (external DB)    | Manual (transaction scope)   | Financial workflows, cross-service TA   |
| **Service Mesh**          | Decouples microservices with service-to-service communication.               | Sidecar proxies (e.g., Istio, Linkerd)      | Dynamic (embedded)                      | Ephemeral                   | Automatic (mesh-aware)       | Secure microservices, observability       |
| **Serverless Containers** | Event-driven containers (e.g., AWS Fargate, Knative) with auto-scaling.     | Function container + trigger (e.g., SQS)    | Event-based                             | Ephemeral                   | Automatic (scales to zero)  | Event processing, sporadic workloads     |

---

## **Implementation Details**
### **1. Immutable Containers**
**Core Principle:** Containers are never modified after deployment; changes require rebuilding an image.
**Key Practices:**
- **Use Multi-Stage Builds:** Reduce image size while preserving build context (e.g., `FROM alpine` for runtime, `FROM gcc` for compilation).
  ```dockerfile
  # Build stage
  FROM gcc AS builder
  RUN apt-get update && apt-get install -y gcc
  COPY . /app
  RUN gcc main.c -o main

  # Runtime stage
  FROM alpine
  COPY --from=builder /app/main /app/
  CMD ["/app/main"]
  ```
- **Layer Caching:** Leverage Docker’s layer caching for faster rebuilds (e.g., `COPY` commands before `apt-get update`).
- **Secrets Management:** Avoid hardcoding secrets; use **Docker secrets** or external vaults (e.g., HashiCorp Vault).

**Tools:**
- **Buildah** (OCI-compliant alternative to Docker).
- **Distroless Images** (Google’s minimal base images with no shell).

---

### **2. Sidecar Pattern**
**Use Case:** Extend a container’s functionality without modifying its core image (e.g., logging, monitoring).
**Implementation:**
- **Co-Location:** Deploy sidecar alongside the primary container (e.g., Prometheus sidecar for metrics).
- **Shared Volume:** Use a `volumesFrom` (K8s) or bind mount to share data:
  ```yaml
  # K8s Deployment example
  containers:
  - name: app
    image: my-app
  - name: sidecar
    image: prometheus-sidecar
    volumeMounts:
    - mountPath: /var/log/app
      name: app-logs
  volumes:
  - name: app-logs
    emptyDir: {}
  ```
- **Event-Driven:** Sidecars can publish metrics/events to a bus (e.g., Kafka).

**Tools:**
- **Fluentd** (log aggregation sidecar).
- **Envoy Proxy** (traffic management sidecar).

---

### **3. Service Mesh (Istio/Linkerd)**
**Core Benefit:** Abstracts service-to-service communication with features like:
- **mTLS:** Automatic encryption between services.
- **Traffic Routing:** Canary deployments, circuit breakers.
- **Observability:** Integrated metrics, tracing (Jaeger).

**Implementation Steps:**
1. **Inject Sidecars:** Use Istio’s `sidecar.injection` annotation in K8s:
   ```yaml
   metadata:
     annotations:
       sidecar.istio.io/inject: "true"
   ```
2. **Define VirtualServices:** Configure routing rules:
   ```yaml
   apiVersion: networking.istio.io/v1alpha3
   kind: VirtualService
   metadata:
     name: my-service
   spec:
     hosts:
     - my-service
     http:
     - route:
       - destination:
           host: my-service
           subset: v1
         weight: 90
       - destination:
           host: my-service
           subset: v2
         weight: 10
   ```
3. **Enable Observability:** Integrate with Prometheus/Grafana for metrics.

**Tools:**
- **Istio** (CNCF project with multi-cloud support).
- **Linkerd** (simpler, lightweight alternative).

---

### **4. Serverless Containers**
**Model:** Containers scale to zero when idle; triggered by events (e.g., HTTP, Kafka).
**Implementation:**
- **AWS Fargate:** Serverless Kubernetes (EKS) or direct Fargate tasks.
- **Knative (GKE):** Auto-scales containers based on custom metrics.
  ```yaml
  # Knative Service YAML
  apiVersion: serving.knative.dev/v1
  kind: Service
  metadata:
    name: my-service
  spec:
    template:
      spec:
        containers:
        - image: my-app
  ```
**Key Considerations:**
- **Cold Starts:** Mitigate with provisioned concurrency (e.g., AWS Fargate spots).
- **Event Sources:** Integrate with SQS, Pub/Sub, or HTTP triggers.

---

## **Query Examples**
### **1. Find Pods Using a Sidecar**
```bash
# K8s CLI to list pods with sidecar annotations
kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name} {.metadata.annotations.sidecar\.istio\.io/inject}{"\n"}{end}'
```

### **2. Check Container Layers**
```bash
# Inspect Docker image layers
docker history --no-trunc my-image
```

### **3. Istio Traffic Analysis**
```bash
# Query Istio telemetry for a service
kubectl exec -it $(kubectl get pod -l istio=sidecar-injector -o jsonpath='{.items[0].metadata.name}') -c istio-proxy -- curl -s http://localhost:15004/metrics | grep istio_requests_total
```

### **4. Knative Autoscaling Events**
```bash
# Listen to Knative scaling events
kubectl get events -w -l eventSource=knative-scaling-controller
```

---

## **Related Patterns**
| **Pattern**               | **Connection to Containers**                                                                 | **Reference Guide**                          |
|---------------------------|--------------------------------------------------------------------------------------------|-----------------------------------------------|
| **12-Factor App**         | Containers encapsulate 12-Factor principles (e.g., statelessness, config via env vars).  | [12-Factor Apps](https://12factor.net/)      |
| **Circuit Breaker**       | Service Mesh (e.g., Istio) implements circuit breakers for fault tolerance.                 | [Resilience Patterns](https://resilience4j.io/)|
| **Event-Driven Architecture** | Serverless Containers and Kafka integrate with event streams.                          | [EventStorming](https://eventstorming.com/)   |
| **Blue-Green Deployment** | Immutable Containers enable seamless rollouts via K8s `rollingUpdate`.                      | [Deployment Strategies](https://kubernetes.io/)|
| **Chaos Engineering**     | Sidecars (e.g., Chaos Mesh) inject faults for resilience testing.                           | [Chaos Mesh Docs](https://chaos-mesh.org/)    |

---

## **Best Practices**
1. **Image Optimization:**
   - Use `multi-stage builds` to reduce size.
   - Scan for vulnerabilities with **Trivy** or **Clair**.
2. **Security:**
   - Run containers as non-root (`USER 1000` in Dockerfile).
   - Enable **Pod Security Policies (PSP)** or **OPA/Gatekeeper** in K8s.
3. **Observability:**
   - Instrument containers with **OpenTelemetry** for metrics/tracing.
   - Export logs to **Loki** or **ELK Stack**.
4. **Cost Efficiency:**
   - Use **Spot Instances** (K8s `Cluster Autoscaler`) for non-critical workloads.
   - Right-size containers with **Vertical Pod Autoscaler (VPA)**.

---
**Last Updated:** `YYYY-MM-DD`
**Contributors:** `@team-name`