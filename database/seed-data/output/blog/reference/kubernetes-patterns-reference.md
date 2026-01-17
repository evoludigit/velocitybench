# **[Pattern] Kubernetes Deployment Patterns – Reference Guide**

---

## **Overview**
Kubernetes Deployment Patterns outlines best practices, architectural strategies, and implementation details for deploying containerized applications efficiently in Kubernetes clusters. This pattern covers deployment strategies, scaling methods, resilience techniques, and security considerations to ensure high availability, scalability, and fault tolerance. Whether you're migrating from traditional VMs or deploying a greenfield application, this guide provides actionable insights to optimize Kubernetes deployments for performance, cost, and maintainability.

---

## **Key Concepts & Implementation Details**

### **1. Deployment Strategies**
How applications are rolled out to Kubernetes clusters impacts downtime, rollback efficiency, and user experience. Common strategies include:

| Strategy          | Description                                                                 | Best Use Case                                                                 |
|-------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Rolling Update** | Gradually replaces pods with new versions while ensuring minimal downtime. | Slowly iterating applications, zero-downtime deployments.                    |
| **Rolling Restart** | Fully replaces pods in batches (backwards-compatible).                      | Testing new versions with a fallback to previous stable versions.              |
| **Blue-Green**    | Runs two identical environments (Blue: live, Green: new version).           | Critical services requiring zero-downtime switchover.                         |
| **Canary**        | Gradually shifts traffic to a new version (e.g., 5% → 100%).              | Feature testing with minimal risk.                                           |
| **A/B Testing**   | Randomly routes traffic to different versions for comparison.              | Marketing campaigns or experimental feature exposure.                        |
| **Feature Flags** | Enables/disables features dynamically without deploying new code.          | Experimenting with new features without affecting all users.                  |

#### **Implementation Notes:**
- Use `kubectl rollout` for rolling updates:
  ```bash
  kubectl set image deployment/<name> <container>=<image>:<tag> --rollback=true
  ```
- For Blue-Green, deploy both versions side-by-side under different service names (e.g., `myapp-v1` and `myapp-v2`) and update DNS/ingress rules.

---

### **2. Scaling Strategies**
Kubernetes provides built-in tools to scale workloads based on demand.

#### **Horizontal Pod Autoscaling (HPA)**
Dynamically adjusts pod count based on CPU/memory usage or custom metrics.
- **Prerequisite:** Metrics Server (`kubectl top pods` must work).
- **Example YAML:**
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: myapp-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: myapp
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  ```

#### **Cluster Autoscaling**
Automatically adds/removes nodes in the cluster based on pending pods or unused capacity.
- **Requirements:** Cloud provider integration (e.g., AWS EKS, GKE Auto-Provisioning).
- **Enabling:**
  ```bash
  kubectl get clusterautoscaler --all-namespaces
  ```

#### **Manual Scaling**
For predictable workloads (e.g., batch jobs), manually set replicas:
```bash
kubectl scale deployment/<name> --replicas=5
```

---

### **3. Resilience Patterns**
Ensure applications recover from failures gracefully.

| Pattern               | Description                                                                 | Implementation                                                                 |
|-----------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Pod Anti-Affinity** | Distributes pods across nodes to avoid single-point failures.              | Use `podAntiAffinity` in `deployment.yaml` (e.g., `preferredDuringSchedulingIgnoredDuringExecution`). |
| **Readiness/Liveness Probes** | Automatically restarts unhealthy pods or marks them as unavailable.        | Define in `container.livenessProbe`/`readinessProbe` (HTTP, TCP, or exec checks). |
| **ReplicaSets**       | Ensures a stable number of pods (used by Deployments/StatefulSets).         | Deployments control ReplicaSets; use `kubectl get rs`.                          |
| **Service Mesh (Istio/Linkerd)** | Manages traffic, retries, and circuit breaking for microservices.       | Install Istio via `helm install istio-base`.                                     |
| **Chaos Engineering** | Proactively tests failure scenarios (e.g., pod kills, network partitions). | Tools: [Chaos Mesh](https://chaos-mesh.org/), [Gremlin](https://www.gremlin.com/). |

---

### **4. Security Best Practices**
Secure deployments from inception.

| Technique          | Description                                                                 | Example                                                                       |
|--------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Network Policies** | Restricts pod-to-pod communication (e.g., deny all ingress by default).   | ```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-all }
spec: { podSelector: {}, policyTypes: ["Ingress"], ingress: [] }
``` |
| **Role-Based Access Control (RBAC)** | Limits permissions via `Role`/`ClusterRole` bindings.                     | Create a `Role` for a namespace: `kubectl create role pod-reader --verb=get --resource=pods`. |
| **Image Scanning**  | Enforces vulnerability checks for container images.                        | Integrate with [Trivy](https://aquasecurity.github.io/trivy/) or [Clair](https://github.com/quay/clair). |
| **Secrets Management** | Avoid hardcoding secrets; use `Secrets` or external vaults (HashiCorp Vault). | ```bash
kubectl create secret generic db-secret --from-literal=password=xxx
``` |
| **Pod Security Policies (PSP) or OPA/Gatekeeper** | Enforces security contexts (e.g., non-root users, read-only root FS). | Example PSP: `allowPrivilegeEscalation: false`.                             |

---

### **5. Observability & Monitoring**
Track performance, errors, and resource usage.

| Tool               | Purpose                                                                   | Example Commands                                                                 |
|--------------------|---------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Prometheus**     | Time-series metrics for monitoring.                                       | Deploy via Helm: `helm install prometheus prometheus-community/prometheus`.    |
| **Grafana**        | Visualizes metrics (e.g., pod CPU/memory).                               | Access dashboard at `http://<grafana-service>:3000`.                             |
| **Loki**           | Log aggregation for Kubernetes.                                           | Ship logs to Loki: `kubectl logs -l app=myapp --tail=100 > /var/log/myapp.log`. |
| **Custom Metrics** | Track business-specific metrics (e.g., "requests processed").             | Create a custom metric adapter in Prometheus.                                  |

---

## **Schema Reference**
Below are key Kubernetes resource schemas for deployment patterns.

### **Deployment YAML (Core Schema)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <name>
spec:
  replicas: <int>          # Desired pod count
  selector:
    matchLabels:           # Must match pod template labels
      app: <name>
  template:
    metadata:
      labels:
        app: <name>
    spec:
      containers:
      - name: <container>
        image: <image>:<tag>
        ports:
        - containerPort: <port>
        resources:
          requests:
            cpu: "<cpu-request>"
            memory: "<memory-request>"
          limits:
            cpu: "<cpu-limit>"
            memory: "<memory-limit>"
        livenessProbe:      # Optional health checks
          httpGet:
            path: /health
            port: <port>
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:     # Optional readiness checks
          httpGet:
            path: /ready
            port: <port>
          initialDelaySeconds: 2
          periodSeconds: 5
      affinity:             # Optional scheduling rules
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: ["<name>"]
              topologyKey: "kubernetes.io/hostname"
```

### **Service YAML (Expose Pods)**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <service-name>
spec:
  selector:
    app: <name>            # Must match deployment labels
  ports:
  - protocol: TCP
    port: <service-port>   # Cluster-internal port
    targetPort: <container-port>  # Pod port
  type: LoadBalancer|NodePort|ClusterIP  # External access method
```

### **HorizontalPodAutoscaler (HPA) YAML**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <hpa-name>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <deployment-name>
  minReplicas: <min>
  maxReplicas: <max>
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: <percentage>
  - type: External       # Custom metrics (e.g., requests/sec)
    external:
      metric:
        name: requests_per second
        selector:
          matchLabels:
            app: <name>
      target:
        type: AverageValue
        averageValue: "1k"
```

---

## **Query Examples**
### **1. List Deployments with Resource Usage**
```bash
kubectl top deployments --all-namespaces
```
Output:
```
NAMESPACE     NAME          CPU(cores)   MEMORY(bytes)
default       myapp         500m         250Mi
```

### **2. Rolling Update with Image Tag**
```bash
kubectl set image deployment/myapp nginx=nginx:1.23 --record
```
(Records the change in deployment history for rollbacks.)

### **3. Check HPA Status**
```bash
kubectl get hpa myapp-hpa -o wide
```
Output:
```
NAME          REFERENCE                 TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
myapp-hpa     Deployment/myapp/v1       60%/70%   2         10        4          2d
```

### **4. Describe Deployment for Troubleshooting**
```bash
kubectl describe deployment myapp
```
Look for `Events` and `Conditions` sections.

### **5. Scale Deployment Manually**
```bash
kubectl scale deployment myapp --replicas=3 --dry-run=client -o yaml | kubectl apply -f -
```

### **6. Verify Pod Liveness**
```bash
kubectl get pods -o wide --show-labels | grep myapp
```
Check `STATUS` (e.g., `Running` vs. `CrashLoopBackOff`).

### **7. Test Network Policy**
```bash
kubectl exec -it <pod> -- sh -c "curl http://denied-service:8080"
```
(Should fail if policy denies traffic.)

---

## **Related Patterns**
1. **[Kubernetes Ingress Patterns]**
   - Details how to manage external access to services (e.g., HTTP routing, TLS termination).
2. **[Service Mesh Patterns]**
   - Covers traffic management, observability, and security with Istio/Linkerd.
3. **[Stateful Workload Patterns]**
   - Best practices for stateful applications (e.g., databases, Kafka) using `StatefulSets`.
4. **[Multi-Cluster Patterns]**
   - Strategies for deploying across multiple Kubernetes clusters (e.g., federation, hybrid cloud).
5. **[CI/CD Patterns for Kubernetes]**
   - Automated pipelines for deploying to Kubernetes (e.g., ArgoCD, Flux, Tekton).
6. **[Helm Chart Patterns]**
   - Templating and versioning deployments with Helm.
7. **[Security Hardening Patterns]**
   - Advanced security (e.g., network segmentation, zero-trust, secret rotation).

---
**Note:** For deeper dives, refer to the [Kubernetes Official Docs](https://kubernetes.io/docs/concepts/) and cloud provider-specific guides (e.g., AWS EKS, GCP GKE).