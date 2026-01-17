---
# **[Pattern] Kubernetes & Container Orchestration Reference Guide**

---

## **1. Overview**
Kubernetes (K8s) is an open-source **container orchestration platform** designed to automate deployment, scaling, and management of containerized applications across clusters of hosts. This reference guide provides a structured breakdown of Kubernetes concepts, configuration schemas, query examples, and related best practices for efficient container orchestration at scale.

Kubernetes abstracts infrastructure complexity by managing workloads (Pods, Deployments), networking (Services, Ingress), storage (Volumes, PersistentVolumes), and security (RBAC, Secrets). By leveraging declarative configuration (YAML/JSON manifests), teams can define desired state, allowing Kubernetes to self-heal and scale applications dynamically.

### **Core Objectives**:
- Deploy and manage containerized applications.
- Ensure high availability (HA) and resiliency.
- Automate scaling (horizontal/vertical) based on demand.
- Optimize resource allocation (CPU/memory) across clusters.

---

## **2. Schema Reference**
Below is a table of key Kubernetes resource types, their **Purpose**, **Key Fields**, and **Relationships**.

| **Resource Type**       | **Purpose**                                                                                     | **Key Fields**                                                                 | **Relationships (Depends On/Links To)**                     |
|-------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------|
| **Pod**                 | Lightweight, ephemeral unit housing one or more containers.                                      | `metadata.name`, `spec.containers`, `spec.restartPolicy`                    | Deployments, StatefulSets, DaemonSets                       |
| **Deployment**          | Manages Pod replicas and rolling updates for stable deployments.                                  | `spec.replicas`, `spec.strategy`, `spec.template`                           | Pods, Services                                             |
| **StatefulSet**         | Manages stateful applications with stable, unique network IDs and persistent storage.          | `spec.replicas`, `spec.serviceName`, `spec.volumeClaimTemplates`             | Pods, PVCs, Services                                       |
| **DaemonSet**           | Ensures one Pod per node (e.g., logging agents, monitoring).                                     | `spec.template`, `spec.updateStrategy`                                       | Pods                                                      |
| **Service**             | Exposes Pods internally/externally (ClusterIP, NodePort, LoadBalancer).                         | `spec.type`, `spec.selector`, `spec.ports`                                  | Pods, Ingress                                              |
| **Ingress**             | Manages external HTTP/HTTPS access to Services (e.g., routing rules, TLS).                       | `spec.rules`, `spec.tls`, `spec.backend`                                     | Services                                                  |
| **ConfigMap**           | Stores non-confidential configuration data.                                                      | `data.{key}`, `binaryData`                                                   | Pods                                                      |
| **Secret**              | Secure storage for credentials (e.g., passwords, API keys).                                      | `type`, `stringData`, `immutable`                                             | Pods, Deployments                                          |
| **Namespace**           | Logical isolation (e.g., dev/stage/prod).                                                      | `metadata.name`, `labels`                                                    | All resources (scoped)                                     |
| **PersistentVolume (PV)** | Abstracts storage resources (e.g., AWS EBS, NFS).                                               | `spec.capacity`, `spec.accessModes`, `spec.persistentVolumeReclaimPolicy`     | PVCs                                                      |
| **PersistentVolumeClaim (PVC)** | Claims storage from PVs (Pod-visible).                                                          | `spec.accessModes`, `spec.resources.requests`, `spec.volumeName`             | Pods, PVs                                                 |
| **HorizontalPodAutoscaler (HPA)** | Auto-scales Pods based on CPU/memory or custom metrics.                                         | `spec.scaleTargetRef`, `spec.minReplicas`, `spec.maxReplicas`, `metrics`      | Deployments, StatefulSets                                  |
| **Job/CronJob**         | Runs batch processing tasks (one-time or scheduled).                                           | `spec.template`, `spec.completions`, `schedule` (CronJob)                    | Pods                                                      |
| **Role/Binding**        | Role-Based Access Control (RBAC) for fine-grained permissions.                                   | `rules`, `subjects` (RoleBinding), `resources` (Role)                       | Users/Groups                                               |
| **ClusterRole/ClusterRoleBinding** | Cluster-wide RBAC policies.                                                                | `rules`, `clusterRoleRef` (Binding)                                           | Users/Groups (cluster-scoped)                              |

---

## **3. Query Examples**
### **3.1. Common `kubectl` Commands**
Use `kubectl` to inspect and manage resources. Below are essential examples:

| **Command**                                                                 | **Purpose**                                                                 |
|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `kubectl get pods -n <namespace>`                                            | List Pods in a namespace.                                                    |
| `kubectl describe pod <pod-name>`                                           | Show Pod details (events, conditions, logs).                                  |
| `kubectl exec -it <pod-name> -- bash`                                       | SSH into a running Pod.                                                      |
| `kubectl apply -f deployment.yaml`                                          | Deploy a resource from a YAML file.                                          |
| `kubectl scale deployment <name> --replicas=5`                               | Scale a Deployment to 5 replicas.                                            |
| `kubectl logs <pod-name>`                                                    | View Pod logs.                                                              |
| `kubectl port-forward svc/<service-name> 8080:80`                           | Forward local port `8080` to Service `80`.                                   |
| `kubectl auth can-i create pods --as=admin`                                  | Check RBAC permissions.                                                      |
| `kubectl top pods`                                                          | Show CPU/memory usage per Pod.                                               |

---

### **3.2. Helm Chart Deployment Example**
Helm simplifies Kubernetes package management. Deploy a chart (e.g., `nginx`):

```bash
# Add a Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install a chart with values override
helm install my-nginx bitnami/nginx \
  --set replicaCount=3 \
  --namespace webapps
```

**Output**:
```
NAME: my-nginx
LAST DEPLOYED: Tue Oct 10 12:00:00 2023
NAMESPACE: webapps
STATUS: deployed
...
```

---

### **3.3. JSONPatch for Dynamic Updates**
Patch a Deployment’s replicas dynamically:

```json
# Apply a JSON Patch
kubectl patch deployment nginx-deployment --patch='{"spec":{"replicas":4}}' --type=json
```

**Result**:
The Deployment’s replica count updates to `4` without recreating Pods.

---

### **3.4. NetworkPolicy Example**
Restrict Pod communication:

```yaml
# deny-all.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}  # Applies to all Pods
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
```

Apply:
```bash
kubectl apply -f deny-all.yaml
```

---
## **4. Related Patterns**
Kubernetes integrates with complementary patterns to enhance orchestration:

| **Pattern**               | **Description**                                                                                     | **Use Case**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Service Mesh (Istio/Linkerd)** | Manages service-to-service communication (traffic routing, observability, security).          | Microservices with strict SLAs or security requirements.                                           |
| **GitOps (ArgoCD/Flux)**  | Syncs Kubernetes manifests from Git for audit-ready deployments.                                    | CI/CD pipelines with infrastructure-as-code (IaC) requirements.                                   |
| **Multi-Cluster Federation** | Manages workloads across multiple K8s clusters.                                                   | Global deployments (e.g., multi-region HA).                                                     |
| **Serverless (Knative)**  | Runs stateless workloads as scalable, event-driven functions.                                      | Event-driven apps (e.g., async processing, webhooks).                                             |
| **Storage Orchestration** | Dynamically provisions storage (e.g., ReadWriteMany via Rook/Ceph).                              | Stateful apps needing shared storage (e.g., databases).                                            |
| **Security Hardening**     | PodSecurityPolicies, network policies, and image scanning.                                          | Compliance (e.g., PCI, HIPAA) or zero-trust security models.                                     |

---

## **5. Best Practices & Troubleshooting**
### **5.1. Resource Optimization**
- **Right-size requests/limits**: Set `resources.requests` and `resources.limits` in Pod specs to avoid OOM kills or throttling.
- **ResourceQuotas**: Limit namespace-level resource consumption:
  ```yaml
  apiVersion: v1
  kind: ResourceQuota
  metadata:
    name: mem-cpu-quota
  spec:
    hard:
      requests.cpu: "10"
      requests.memory: 20Gi
  ```

### **5.2. High Availability**
- Deploy critical workloads as **StatefulSets** (for stable network IDs) or **Deployments** (for stateless apps).
- Use **Multi-AZ clusters** (e.g., AWS EKS) for resilience.

### **5.3. Observability**
- **Metrics**: Use Prometheus + Grafana for monitoring.
- **Logging**: Centralize logs with Fluentd/EFK stack (Elasticsearch, Fluentd, Kibana).
- **Tracing**: Integrate Jaeger or OpenTelemetry for distributed tracing.

### **5.4. Common Issues & Fixes**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Pod CrashLoopBackOff**           | Check `kubectl logs <pod>` for errors.                                         | Fix application crashes or resource constraints.                                                 |
| **ImagePullBackOff**               | Invalid image registry/auth.                                                   | Verify `imagePullSecrets` or registry credentials.                                                |
| **Service Unreachable**             | Endpoint misconfiguration or misnamed `selector`.                             | Use `kubectl get endpoints <service-name>` to debug.                                              |
| **PersistentVolumeClaim Stuck**    | Insufficient PV capacity or access mode mismatch.                             | Adjust `spec.accessModes` or scale PV storage.                                                    |
| **RBAC Forbidden**                 | User lacks permissions.                                                        | Grant `RoleBinding` or `ClusterRoleBinding` to the user.                                          |

---

## **6. Further Reading**
- [Kubernetes Official Docs](https://kubernetes.io/docs/home/)
- [CNCF Kubernetes Ecosystem](https://landscape.cncf.io/?search=Kubernetes)
- [Helm Documentation](https://helm.sh/docs/)
- [Istio Service Mesh](https://istio.io/latest/docs/home/)
- [GitOps with ArgoCD](https://argo-cd.readthedocs.io/)