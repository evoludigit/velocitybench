# **[Pattern] Kubernetes Deployment Pattern Reference Guide**

---
## **Overview**
FraiseQL's **Kubernetes Deployment Pattern** ensures reliable, scalable, and secure production deployments of applications on Kubernetes. This pattern automates the creation of well-configured **Deployments** with:
- **Horizontal Pod Autoscaling (HPA)** (3–20 replicas by default, configurable)
- **Pod Security Standards** (enforced via **Baseline** or **Restricted** profiles)
- **Network Policies** (zero-trust default deny with allow rules for pods)
- **Resource Limits** (CPU/memory requests & limits for stability)
- **Health Probes** (liveness & readiness checks for resilience)
- **Image Pull Secrets** (secure access to container registries)

This pattern is ideal for containerized applications requiring automatic scaling, compliance, and resilience in Kubernetes environments.

---

## **Schema Reference**

### **1. Deployment Configuration (`k8s/deployment.yaml`)**
| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Value**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `metadata.name`         | `string`       | Unique name for the Deployment.                                                                                                                                      | `my-app-deployment`                                                               |
| `spec.replicas`         | `integer`      | Number of pod replicas (default: 3, max: 20). Adjustable via `autoscaling.minReplicas` and `autoscaling.maxReplicas`.                                   | `3`                                                                               |
| `spec.selector.matchLabels` | `object`   | Labels to select pods managed by this Deployment.                                                                                                               | `{ app: "my-app", tier: "frontend" }`                                              |
| `spec.template.metadata.labels` | `object` | Labels for pods (must match `selector`).                                                                                                                 | Same as above.                                                                   |
| `spec.template.spec.securityContext` | `object` | Pod security settings (e.g., runAsNonRoot, readOnlyRootFilesystem).                                                                                          | `{ runAsNonRoot: true, runAsUser: 1000 }`                                          |
| `spec.template.spec.containers[].name` | `string`     | Container name in the pod.                                                                                                                                         | `nginx`                                                                             |
| `spec.template.spec.containers[].image` | `string`    | Container image URI (e.g., from ECR, Docker Hub).                                                                                                             | `public.ecr.aws/my-repo/my-app:v1.2.0`                                             |
| `spec.template.spec.containers[].ports` | `array`      | Container ports exposed (used by Services).                                                                                                                   | `[{ containerPort: 80 }]`                                                         |
| `spec.template.spec.containers[].resources` | `object` | CPU/memory limits/requests (prevents resource starvation).                                                                                                       | `{ limits: { cpu: "1", memory: "512Mi" }, requests: { cpu: "500m", memory: "256Mi" } }` |
| `spec.template.spec.livenessProbe` | `object`     | Health check for crashed pods (restarted automatically).                                                                                                          | `{ httpGet: { path: "/health", port: 80 }, initialDelaySeconds: 30, periodSeconds: 10 }` |
| `spec.template.spec.readinessProbe` | `object`    | Health check before traffic routing (pod marked `NotReady` if failing).                                                                                           | Same as `livenessProbe` but with `failureThreshold: 3`.                          |
| `spec.strategy.type`    | `string`       | Deployment update strategy (`RollingUpdate` recommended).                                                                                                         | `"RollingUpdate"`                                                                  |
| `spec.strategy.rollingUpdate.maxSurge` | `integer`    | Max pods allowed during update (default: 1).                                                                                                                   | `1`                                                                                 |
| `spec.strategy.rollingUpdate.maxUnavailable` | `integer` | Max unavailable pods during update (default: 0).                                                                                                             | `0`                                                                                 |

---

### **2. Horizontal Pod Autoscaler (`k8s/hpa.yaml`)**
| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Value**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `metadata.name`         | `string`       | Name of the HPA (typically `<deployment-name>-hpa`).                                                                                                               | `my-app-deployment-hpa`                                                          |
| `spec.scaleTargetRef.name` | `string`      | References the Deployment to scale.                                                                                                                              | `my-app-deployment`                                                              |
| `spec.minReplicas`      | `integer`      | Minimum replicas (default: 3).                                                                                                                                     | `3`                                                                                 |
| `spec.maxReplicas`      | `integer`      | Maximum replicas (default: 20).                                                                                                                                  | `20`                                                                                 |
| `spec.metrics`          | `array`        | Scaling triggers (CPU, memory, or custom metrics).                                                                                                               | `[{ type: "Resource", resource: { name: "cpu", target: { type: "Utilization", averageUtilization: 70 } } }]` |

---

### **3. Network Policy (`k8s/network-policy.yaml`)**
| **Field**               | **Type**       | **Description**                                                                                                                                                     | **Example Value**                                                                 |
|-------------------------|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `metadata.name`         | `string`       | Name of the NetworkPolicy.                                                                                                                                          | `allow-frontend-to-backend`                                                       |
| `spec.podSelector`      | `object`       | Selects pods affected by this policy.                                                                                                                               | `{ app: "my-app", tier: "backend" }`                                               |
| `spec.ingress`          | `array`        | Allowed incoming traffic rules.                                                                                                                                    | `[{ from: [{ podSelector: { tier: "frontend" } }], ports: [{ port: 8080, protocol: "TCP" }] }]` |
| `spec.policyTypes`      | `array`        | Policy types (`Ingress`, `Egress`, or `Ingress,Egress`). Default: `Ingress`.                                                                                          | `["Ingress"]`                                                                     |

---

### **4. Pod Security Standards (`k8s/pss.yaml`)**
FraiseQL enforces **Pod Security Standards (PSS)** via **Gatekeeper** (OPA) or **Admission Webhooks**. Configure with:
```yaml
apiVersion: pods.security.k8s.io/v1
kind: PodSecurityStandard
metadata:
  name: restricted
spec:
  seccompProfile:
    type: RuntimeDefault
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  seLinux:
    user: "unconfined"
    role: "unconfined"
    type: "unconfined"
```

---

## **Query Examples**
### **1. Deploy a New Application**
```bash
# Apply the Deployment, HPA, and NetworkPolicy
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/network-policy.yaml
```

### **2. Verify Autoscaling**
```bash
# Check HPA status
kubectl get hpa my-app-deployment-hpa
```
**Output:**
```
NAME                     REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
my-app-deployment-hpa    Deployment/my-app     70%/70%   3         20        5          5m
```

### **3. Check Pod Security**
```bash
# List pods with security context
kubectl describe pod my-app-deployment-xxxx | grep SecurityContext
```
**Output:**
```
Security Context:
  Run As User:        1000
  Run As Group:       2000
  Run As Non-root:    true
  Read-only root filesystem:  true
```

### **4. Test NetworkPolicy**
```bash
# Verify allowed traffic (e.g., from frontend to backend)
kubectl describe networkpolicy allow-frontend-to-backend
```
**Output:**
```
Ingress Policy:    Pods with label "tier=backend" allow TCP:8080 from "tier=frontend"
```

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                                     | **Use Case**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Service Mesh Integration]**        | Deploy Istio or Linkerd alongside Kubernetes Deployments for advanced traffic management, observability, and security.                                               | Microservices requiring mutual TLS, canary deployments, or distributed tracing.                     |
| **[Database Migration Pattern]**     | Manage database schema changes alongside app deployments (e.g., using ArgoCD or Flux).                                                                             | Stateful applications with DB dependencies.                                                     |
| **[Canary Releases]**                 | Gradually roll out updates to a subset of traffic using Istio or NGINX Ingress.                                                                                  | Reducing risk in production deployments.                                                         |
| **[Multi-Region Deployment]**         | Sync Deployments across multiple Kubernetes clusters (e.g., using ArgoCD).                                                                                         | High-availability global applications.                                                          |
| **[Observability Stack]**             | Integrate Prometheus, Grafana, and Kubernetes-native monitoring (e.g., Kube-State-Metrics).                                                                 | Proactive incident detection and performance tuning.                                             |

---
**Notes:**
- **Customization:** Adjust `maxReplicas`, `resources`, and `probes` based on workload requirements.
- **Security:** Always validate Pod Security Standards with `kubectl apply -f pss.yaml` and test Network Policies in staging first.
- **Autoscaling:** For non-CPU/memory metrics, use **Custom Metrics** (e.g., Prometheus Adapter).