# **[Pattern] Containers Strategies Reference Guide**

---

## **Overview**
This guide explains **Containers Strategies**—a pattern for defining deployment, scaling, and orchestration policies for containers in cloud-native architectures. The pattern ensures consistent, repeatable deployment of containerized applications by encapsulating strategy metadata (e.g., scaling rules, resource limits, network policies) alongside the application. It is typically implemented using Kubernetes Custom Resources (CRDs) or frameworks like Helm or Terraform.

Unlike ad-hoc deployments, this pattern centralizes strategy configuration, improving maintainability and portability across environments. It is widely used in microservices, serverless architectures, and hybrid cloud deployments.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|
| **Strategy Definition** | A declarative YAML/JSON manifest specifying policies for container deployment. |
| **Scaling Rules**       | Auto-scaling thresholds (e.g., CPU/memory utilization) or event triggers.      |
| **Resource Constraints**| CPU, memory, and storage limits for containers.                                |
| **Network Policies**    | Traffic rules (e.g., ingress/egress filters) for container communication.       |
| **Reconciliation**      | Continuous adjustment of deployed resources to match the defined strategy.     |

---

## **Schema Reference**
Below is the core schema for a **Containers Strategy** manifest. Fields are categorized for clarity.

### **Core Strategy Definition**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `apiVersion`           | `string`       | Schema version (e.g., `strategy.example.com/v1`).                              | `strategy.example.com/v1`             |
| `kind`                 | `string`       | Resource type (e.g., `ContainerStrategy`).                                     | `ContainerStrategy`                   |
| `metadata`             | `object`       | Standard Kubernetes metadata (name, labels, annotations).                     | `{name: "web-server-scale"}`         |
| `spec`                 | `object`       | Strategy-specific configurations.                                              | `{}`                                  |

---

### **Scaling Configuration**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `spec.scaling`          | `object`       | Auto-scaling rules.                                                              | `{}`                                  |
| `spec.scaling.minReplicas` | `integer`    | Minimum pod replicas.                                                            | `2`                                   |
| `spec.scaling.maxReplicas` | `integer`    | Maximum pod replicas.                                                            | `10`                                  |
| `spec.scaling.targetCPU`   | `float`       | Target CPU utilization for scaling (e.g., `70`).                               | `0.7`                                 |
| `spec.scaling.trigger`     | `string`      | Scaling event type (`cpu`, `memory`, `custom`).                                | `"cpu"`                               |

---

### **Resource Constraints**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `spec.resources`        | `object`       | CPU/memory limits and requests.                                                  | `{}`                                  |
| `spec.resources.limits` | `object`       | Hard limits for containers.                                                      | `{cpu: "1", memory: "512Mi"}`        |
| `spec.resources.requests` | `object`   | Guaranteed resources.                                                           | `{cpu: "500m", memory: "256Mi"}`     |

---

### **Network Policies**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------------------------------|
| `spec.networking`       | `object`       | Pod network rules.                                                              | `{}`                                  |
| `spec.networking.ingress` | `list`       | Allow/deny ingress traffic rules.                                               | `[{ports: [80], from: ["namespace:prod"]}]` |
| `spec.networking.egress`  | `list`       | Allow/deny egress traffic rules.                                                | `[{to: ["http://api.example.com"]}]`   |

---

### **Full Example Manifest**
```yaml
apiVersion: strategy.example.com/v1
kind: ContainerStrategy
metadata:
  name: web-app-scale
spec:
  scaling:
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 0.7
    trigger: "cpu"
  resources:
    limits:
      cpu: "1"
      memory: "512Mi"
    requests:
      cpu: "500m"
      memory: "256Mi"
  networking:
    ingress:
      - ports: [80]
        from:
          - namespace: "prod"
    egress:
      - to: ["http://api.example.com"]
```

---

## **Query Examples**
### **1. List All Strategies**
Retrieve all deployed container strategies in a namespace:
```bash
kubectl get containersstrategies -A
```

### **2. Filter Strategies by Label**
List strategies tagged with `team: frontend`:
```bash
kubectl get containersstrategies --selector "team=frontend" -n default
```

### **3. Describe a Specific Strategy**
Show details for `web-app-scale`:
```bash
kubectl describe containersstrategy web-app-scale
```

### **4. Apply a Strategy**
Deploy a new strategy from a YAML file:
```bash
kubectl apply -f web-app-scale.yaml
```

### **5. Scale a Strategy Manually**
Set replicas to 5 (bypassing auto-scaling):
```bash
kubectl scale containersstrategy web-app-scale --replicas=5
```

### **6. Patch a Strategy**
Update `maxReplicas` to `15`:
```bash
kubectl patch containersstrategy web-app-scale --type=json -p='[{"op": "replace", "path": "/spec/scaling/maxReplicas", "value": 15}]'
```

---

## **Implementation Steps**
### **1. Define the Custom Resource Definition (CRD)**
Create a CRD to register `ContainerStrategy` with the cluster:
```yaml
# containersstrategy-crd.yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: containersstrategies.strategy.example.com
spec:
  group: strategy.example.com
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                scaling:
                  type: object
                resources:
                  type: object
  scope: Namespaced
  names:
    plural: containersstrategies
    singular: containersstrategy
    kind: ContainerStrategy
```
Apply the CRD:
```bash
kubectl apply -f containersstrategy-crd.yaml
```

### **2. Implement a Controller**
Use **Operator SDK**, **Kubebuilder**, or **Kustomize** to create a controller that:
- Validates strategy manifests.
- Reconciles deployed pods against strategy rules.
- Adjusts replicas/scaling based on triggers.

### **3. Integrate with Helm/Terraform**
Embed strategy definitions in Helm charts (e.g., `values.yaml`) or Terraform modules for IaC:
```yaml
# helm/values.yaml
containers:
  strategies:
    web-app:
      scaling:
        minReplicas: 2
        maxReplicas: 10
```

### **4. Monitor and Alert**
Set up Prometheus alerts for scaling events:
```yaml
# prometheus-alert.yml
- alert: HighScalingActivity
  expr: rate(container_strategy_scaling_events[5m]) > 5
  for: 1m
  labels:
    severity: warning
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Use Case**                          |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **[Deploy Containers](https://example.com/pattern/deploy-containers)** | Basics of container deployment (e.g., Docker, Kubernetes Pods).               | Initial containerization.            |
| **[Auto Scaling](https://example.com/pattern/auto-scaling)**       | Reactive scaling based on metrics (e.g., HPA, KEDA).                          | Dynamic workload handling.            |
| **[Service Mesh](https://example.com/pattern/service-mesh)**       | Advanced networking (e.g., Istio, Linkerd) for microservices.                 | Secure, observable service mesh.     |
| **[GitOps](https://example.com/pattern/gitops)**                   | Declarative infrastructure management via Git (e.g., ArgoCD).                 | CI/CD for container strategies.       |
| **[Multi-Region Deployment](https://example.com/pattern/multi-region)** | Deploying containers across regions with sync/async replication.            | Global low-latency applications.      |

---

## **Best Practices**
1. **Modularize Strategies**: Group related strategies (e.g., `database`, `api-gateway`) in separate manifests.
2. **Use Labels/Annotations**: Tag strategies for environment-specific rules (e.g., `env: prod`).
3. **Validate Early**: Enforce strategy validation during CI/CD (e.g., OPA/Gatekeeper policies).
4. **Document Defaults**: Clearly define default scaling/resource values in READMEs.
5. **Monitor Strategy Health**: Track reconciliation errors (e.g., `kubectl logs -l strategy=web-app-scale`).

---
**Last Updated:** `[Insert Date]`
**Version:** `1.0`