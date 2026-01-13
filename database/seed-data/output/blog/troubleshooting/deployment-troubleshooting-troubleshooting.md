# **Debugging Deployment Troubleshooting: A Practical Troubleshooting Guide**

Deployments can fail for countless reasons—from misconfigured environments to race conditions in application logic. This guide provides a **structured, actionable approach** to diagnosing and resolving deployment issues quickly.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue by checking:

✅ **Deployment Status**
- Is the deployment **stuck** (e.g., in `pending` or `failed` state)?
- Does the Kubernetes pod/container **never start**, or does it **crash immediately**?
- Are there **unexpected rollbacks**?

✅ **Error Logs**
- Are there **5xx errors** in deployment logs?
- Are logs missing or corrupted?
- Are there **resource limit violations** (e.g., `OutOfMemoryError`)?

✅ **Dependency & Configuration Issues**
- Are **required databases, APIs, or services** unavailable?
- Are **environment variables** missing or misconfigured?
- Are **secrets/credentials** incorrectly injected?

✅ **Network & Connectivity**
- Are **ports blocked** or **firewalls** restricting access?
- Are **DNS resolution failures** preventing service discovery?
- Is **latency** causing timeouts?

✅ **Infrastructure & Resource Constraints**
- Are **CPU/memory limits** being exceeded?
- Is the **disk space** full?
- Are there **quotas** preventing scaling?

---

## **2. Common Issues & Fixes (With Code)**

### **A. Deployment Stuck in Pending State**
**Symptoms:**
- Pod never starts (`kubectl get pods` shows `ContainerCreating` or `Pending`).
- No logs or events in `kubectl describe pod <name>`.

**Possible Causes & Fixes:**

#### **1. Resource Constraints (CPU/Memory/Disk)**
**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```
Look for:
```
Events:
  Type     Reason                  Message
  ----     ------                  -------
  Warning  FailedScheduling        0/2 nodes are available: 1 insufficient cpu, 1 insufficient memory.
```
**Fix:**
- Check node resources:
  ```bash
  kubectl describe nodes
  ```
- Adjust **resource requests/limits** in deployment YAML:
  ```yaml
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  ```

#### **2. Node Drain/Unavailable Nodes**
**Diagnosis:**
```bash
kubectl get nodes --show-labels
```
**Fix:**
- Ensure nodes are **Ready** (`kubectl get nodes`).
- Check node conditions:
  ```bash
  kubectl describe node <node-name>
  ```

#### **3. Pod Affinity/Anti-Affinity Conflicts**
**Diagnosis:**
```bash
kubectl get events --sort-by='.metadata.creationTimestamp'
```
**Fix:**
- Adjust pod affinity rules or node selectors:
  ```yaml
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values:
            - amd64
  ```

---

### **B. Pod Crashes Immediately (CrashLoopBackOff)**
**Symptoms:**
- Pod restarts repeatedly.
- Logs show an error (e.g., `500 Internal Server Error`).

**Possible Causes & Fixes:**

#### **1. Application-Level Errors**
**Diagnosis:**
```bash
kubectl logs <pod-name> --previous  # Check previous crash
```
**Fix:**
- Check for **missing config**, **invalid dependencies**, or **business logic failures**.
- Example: If a Spring Boot app fails due to a missing property:
  ```log
  Caused by: java.lang.IllegalArgumentException: Invalid config!
  ```
  **Fix:** Ensure correct env vars:
  ```yaml
  env:
  - name: SPRING_DATASOURCE_URL
    value: "jdbc:postgresql://db:5432/mydb"
  ```

#### **2. Missing Secrets or ConfigMaps**
**Diagnosis:**
```bash
kubectl get secrets,configmaps --all-namespaces
```
**Fix:**
- Verify secrets are mounted correctly:
  ```yaml
  volumeMounts:
  - name: app-secrets
    mountPath: /etc/secrets
    readOnly: true
  volumes:
  - name: app-secrets
    secret:
      secretName: my-app-secrets
  ```

#### **3. Permission Denied (Role-Based Access Control)**
**Diagnosis:**
```bash
kubectl describe pod <pod-name> | grep "Error"
```
**Fix:**
- Ensure the pod’s **ServiceAccount** has proper RBAC:
  ```yaml
  serviceAccountName: my-app-account
  ```
- Grant necessary permissions:
  ```yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    name: pod-reader
  rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  ```

---

### **C. Service Unavailable (External Dependencies)**
**Symptoms:**
- App logs indicate **timeouts** or **connection refused**.
- Health checks fail.

**Possible Causes & Fixes:**

#### **1. Database/Service Unreachable**
**Diagnosis:**
```bash
kubectl exec <pod-name> -- curl -v http://db:5432
```
**Fix:**
- Check **service DNS resolution**:
  ```yaml
  # If using DNS, ensure service name matches
  db: "postgres://db:5432/mydb"
  ```
- Verify **service liveness probes**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
  ```

#### **2. Network Policies Blocking Traffic**
**Diagnosis:**
```bash
kubectl describe networkpolicy <policy-name>
```
**Fix:**
- Adjust **NetworkPolicy** to allow traffic:
  ```yaml
  spec:
    podSelector:
      matchLabels:
        app: my-app
    policyTypes:
    - Ingress
    ingress:
    - from:
      - podSelector:
          matchLabels:
            app: allowed-service
      ports:
      - protocol: TCP
        port: 8080
  ```

---

### **D. Rollback Due to Failed Readiness Probe**
**Symptoms:**
- Deployment rolls back after a few minutes.
- `kubectl get deployments` shows `progress dead`.

**Possible Causes & Fixes:**

#### **1. Slow Application Startup**
**Diagnosis:**
```bash
kubectl describe pod <pod-name>
```
**Fix:**
- Adjust **readiness probe** timeout:
  ```yaml
  readinessProbe:
    httpGet:
      path: /ready
      port: 8080
    initialDelaySeconds: 10
    periodSeconds: 5
  ```

#### **2. Misconfigured Health Check Endpoint**
**Diagnosis:**
```bash
kubectl logs <pod-name> | grep "Health check failed"
```
**Fix:**
- Ensure the endpoint returns `200 OK`:
  ```java
  // (Example in Spring Boot)
  @GetMapping("/ready")
  public String readinessCheck() {
    return "UP";  // Must return 200
  }
  ```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example Command** |
|--------------------------|---------------------------------------|----------------------|
| **`kubectl describe`**   | Inspect pod/node errors               | `kubectl describe pod <name>` |
| **`kubectl logs`**       | Check application logs                | `kubectl logs -f <pod-name>` |
| **`kubectl exec`**       | Run commands inside a pod            | `kubectl exec -it <pod> -- /bin/bash` |
| **Liveness/Readiness Probes** | Monitor app health | Configure in deployment YAML |
| **Prometheus + Grafana**  | Long-term monitoring & alerts        | Deploy via Helm |
| **Journald (Linux)**     | Check system-level logs               | `journalctl -u kubelet` |
| **Port Forwarding**      | Debug local service access            | `kubectl port-forward svc/my-service 8080:80` |
| **Kubernetes Events**    | Track deployment history              | `kubectl get events --sort-by='.metadata.creationTimestamp'` |

---

## **4. Prevention Strategies**

### **A. Pre-Deployment Checks**
- **Unit & Integration Tests** – Catch logic errors early.
- **Deployment Dry Runs** – Test YAML with `kubectl apply --dry-run=client`.
- **Canary Deployments** – Roll out to a small subset first.
- **Rollback Strategy** – Define a clear rollback plan (e.g., Kubernetes `Rollback` command).

### **B. Infrastructure Best Practices**
- **Resource Quotas** – Prevent overcommitment:
  ```yaml
  apiVersion: v1
  kind: ResourceQuota
  metadata:
    name: my-quota
  spec:
    hard:
      requests.cpu: "2"
      requests.memory: 4Gi
  ```
- **Horizontal Pod Autoscaler (HPA)** – Auto-scale based on CPU/memory.
- **Multi-AZ Deployments** – Ensure high availability.

### **C. Observability & Alerting**
- **Centralized Logging** (ELK, Loki) – Aggregate logs across environments.
- **Metrics Collection** (Prometheus) – Track latency, errors, saturation.
- **Alerting (Alertmanager)** – Notify on critical failures:
  ```yaml
  # Example Prometheus alert
  alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
  ```

### **D. CI/CD Pipeline Improvements**
- **Pre-Stage Testing** – Test deployments in staging-like environments.
- **Automated Rollback** – Trigger if health checks fail.
- **Chaos Engineering** – Simulate failures (e.g., kill pods randomly).

---

## **Final Debugging Workflow Summary**
1. **Check Deployment Status** (`kubectl get pods, deployments`).
2. **Inspect Logs** (`kubectl logs`, `kubectl describe pod`).
3. **Verify Dependencies** (DB, APIs, secrets).
4. **Test Locally** (port-forward, exec into pod).
5. **Adjust Probes & Configs** (liveness, readiness, resources).
6. **Monitor Post-Deploy** (Prometheus, ELK).

By following this structured approach, you can **reduce MTTR (Mean Time to Resolution)** and minimize downtime. Always **start simple, then drill down**—most issues are either **misconfigurations, resource constraints, or dependency failures**.

---
**Need a deeper dive on a specific issue?** Let me know! 🚀