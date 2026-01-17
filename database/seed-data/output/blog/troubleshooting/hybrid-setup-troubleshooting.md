# **Debugging Hybrid Setup: A Troubleshooting Guide**
*(For Microservices with On-Premises & Cloud/Kubernetes Hybrid Environments)*

Hybrid setups (e.g., Kubernetes on-prem + cloud providers like AWS GKE/Azure AKS) introduce complexity due to network segmentation, cross-environment communication, and differing infrastructure layers. This guide focuses on **quick root-cause analysis** and fixes for common hybrid deployment issues.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down the problem:

| **Symptom**                          | **Sub-Symptoms**                                                                 | **Likely Cause**                          |
|--------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| **Pod/Service Failure**              | Pods stuck in `CrashLoopBackOff`, `Pending`, or `Error`                          | Resource constraints, network issues      |
| **High Latency**                     | Slow API responses, timeouts, or `ConnectionResetError`                         | Network split-brain, misconfigured routes |
| **Authentication/Authorization Failures** | `403 Forbidden`, `401 Unauthorized`, or `PermissionDenied` errors          | RBAC misconfiguration, misrouted traffic  |
| **Data Consistency Issues**          | Stale reads, `ConflictErrors`, or missing records                             | Eventual consistency delays, misaligned retries |
| **Service Discovery Fails**          | Services cannot resolve DNS names (e.g., `kube-dns` unresolvable)                | Corrupted CoreDNS config, misaligned CNI |
| **Storage Issues**                   | PersistentVolumeClaims stuck in `Pending`, or slow I/O                         | Storage class misconfiguration, network policies blocking storage mounts |
| **Logging/Metrics Missing**          | No logs in ELK/Prometheus, or metrics not appearing in monitoring           | Misrouted sidecar containers, log aggregation misconfig |

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Pods Stuck in `CrashLoopBackOff` (Resource/Network Constraints)**
**Symptoms:**
- Pod logs show `Connection refused`, `Timeout`, or `OOMKilled`.
- `kubectl describe pod <pod-name>` reveals crashes.

**Root Causes:**
- Insufficient resources (CPU/memory) in a node.
- Network policies blocking pod-to-pod communication.
- Storage provisioner delays (e.g., `PersistentVolumeBind` pending).

**Quick Fixes:**
#### **A. Check Node Resources**
```bash
kubectl top nodes
```
- If a node is saturated, **scale up horizontally** or **optimize resource requests**.
  ```yaml
  # Example: Adjust resource requests in Deployment
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  ```

#### **B. Verify Network Policies**
```bash
kubectl get networkpolicies --all-namespaces
```
- If policies are too restrictive, **temporarily disable them** for testing:
  ```bash
  kubectl delete networkpolicy --all --namespace=<namespace>
  ```
- Later, refine policies (e.g., allow internal traffic):
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: allow-internal
  spec:
    podSelector: {}
    policyTypes:
    - Ingress
    ingress:
    - from:
      - podSelector: {}
  ```

#### **C. Check Storage Provisioner**
```bash
kubectl get pvc -A | grep Pending
```
- If stuck, **check storage class** and **node affinity**:
  ```yaml
  # Example: Ensure storage class is dynamically provisioned
  storageClassName: standard
  ```

---

### **Issue 2: High Latency Between On-Prem & Cloud Services**
**Symptoms:**
- API calls between on-prem and cloud take **100ms+** (expected: <50ms).
- `ping` between environments fails or is slow.

**Root Causes:**
- **Unoptimized VPC Peering/Transit Gateway**: Public internet route used instead of private peering.
- **Load Balancer Misconfiguration**: External LB in cloud incorrectly routes traffic.
- **DNS Misalignment**: Services in one environment resolve to the wrong IP.

**Quick Fixes:**
#### **A. Verify Network Routing**
```bash
# Check routing tables on a pod in each environment
kubectl exec -it <pod> -- ip route
```
- Ensure the route for the other environment is **via private peering** (not internet gateway).
- **Example fix (if using AWS Transit Gateway):**
  ```bash
  # Ensure attachments are active
  aws ec2 describe-transit-gateway-attachments --transit-gateway-attachment-id <id>
  ```

#### **B. Test DNS Resolution**
```bash
# From a pod in one environment, check if services in the other resolve
kubectl exec -it <pod> -- nslookup <service-name-in-other-env>
```
- If DNS fails, **create a `ConfigMap` with custom DNS entries**:
  ```yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: custom-dns
    namespace: default
  data:
    nameserver: "10.0.0.2"  # Replace with internal DNS IP
  ```
  - Attach this to pods via `dnsConfig` in the pod spec.

#### **C. Optimize Load Balancer**
```bash
# Check if traffic is hitting the wrong LB
kubectl describe service <service-name>
```
- If using AWS ALB/NLB, **ensure `VPC Peering` is configured** and **security groups allow traffic**.
- **Example ALB rule setup (Terraform):**
  ```hcl
  resource "aws_lb_listener" "internal" {
    load_balancer_arn = aws_lb.internal.arn
    port              = 80
    protocol          = "HTTP"
    default_action {
      type             = "forward"
      target_group_arn = aws_lb_target_group.internal.arn
    }
    depends_on        = [aws_vpc_peering_connection.example]
  }
  ```

---

### **Issue 3: RBAC/Authorization Failures**
**Symptoms:**
- `403 Forbidden` when accessing a cloud API (e.g., AWS EKS worker nodes).
- `PermissionDenied` in logs.

**Root Causes:**
- **ServiceAccount lacks IAM roles** (cloud-specific).
- **Kubernetes RoleBindings misaligned** (on-prem vs cloud).
- **Mutual TLS misconfiguration** (if using cert-manager).

**Quick Fixes:**
#### **A. Check IAM Roles for ServiceAccounts (IRSA)**
```bash
aws eks describe-cluster --name <cluster-name> --query "cluster.identity.oidc.issuer"
```
- Ensure the **OIDC provider is correctly configured** in AWS.
- **Attach IAM policies to the ServiceAccount**:
  ```yaml
  apiVersion: v1
  kind: ServiceAccount
  metadata:
    name: my-sa
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::<ACCOUNT>:role/my-role
  ```

#### **B. Verify Kubernetes RBAC**
```bash
kubectl get roles,rolebindings -A
```
- If a role is missing, **create a `Role` and `RoleBinding`**:
  ```yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    name: pod-reader
  rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
  ---
  apiVersion: rbac.authorization.k8s.io/v1
  kind: RoleBinding
  metadata:
    name: read-pods
  subjects:
  - kind: ServiceAccount
    name: my-sa
    namespace: default
  roleRef:
    kind: Role
    name: pod-reader
    apiGroup: rbac.authorization.k8s.io
  ```

---

### **Issue 4: Data Consistency Problems (Eventual Consistency Delays)**
**Symptoms:**
- Race conditions in distributed transactions.
- `ConflictError` in databases (e.g., PostgreSQL with `REPEATABLE READ` isolation).

**Root Causes:**
- **No transaction coordination** across on-prem and cloud.
- **Retry logic misconfigured** (e.g., exponential backoff too aggressive).
- **Database replication lag** (e.g., AWS RDS with on-prem sync).

**Quick Fixes:**
#### **A. Enable Distributed Transactions (Saga Pattern)**
```java
// Example: Using Spring Cloud Stream for event-driven retries
@Retry(name = "dbRetry", maxAttempts = 3, backoff = @Backoff(delay = 1000))
public void updateOrderStatus(Order order) {
    // Logic to update order in both on-prem and cloud DBs
}
```
- **Use a distributed lock** (e.g., Redis):
  ```bash
  kubectl exec -it <redis-pod> -- redis-cli SET order:123 locked "true" NX EX 30
  ```

#### **B. Check Database Replication**
```sql
-- For PostgreSQL (on-prem -> cloud)
SELECT * FROM pg_stat_replication;  -- Check lag
```
- **Tune WAL shipping**:
  ```ini
  # postgresql.conf (on-prem primary)
  wal_level = replica
  max_wal_senders = 10
  wal_keeper_max = 10
  ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|------------------------------------------------------------------------------|---------------------------------------------|
| **kubectl debug**      | Debug running pods interactively.                                           | `kubectl debug -it <pod> --image=busybox`   |
| **crictl**             | Inspect containerd runtime (if `kubectl` fails).                            | `crictl ps`                                  |
| **netstat/ss**         | Check open ports and network connections.                                   | `ss -tulnp`                                  |
| **tcpdump**            | Capture network traffic between pods.                                        | `kubectl exec -it <pod> -- tcpdump -i eth0` |
| **AWS CloudWatch**     | Monitor EKS metrics (CPU, memory, network).                                  | `aws cloudwatch get-metric-statistics`       |
| **Prometheus/Grafana** | Visualize latency and error rates.                                           | `kubectl port-forward svc/prometheus 9090`   |
| **Jaeger/Zipkin**      | Trace distributed transactions.                                              | `kubectl logs <jaeger-pod>`                  |
| **kube-bench**         | Audit Kubernetes security compliance.                                         | `kubectl create -f https://raw.githubusercontent.com/aquasecurity/kube-bench/master/benchmark.sh` |

**Pro Tip:**
- Use **`kubectl get events --sort-by='.lastTimestamp'`** to see recent cluster events.
- For **network debugging**, enable `kubectl debug` with a shell and `curl` to test connectivity.

---

## **4. Prevention Strategies**

### **A. Infrastructure as Code (IaC) Best Practices**
- **Use Terraform/Helm** to replicate environments:
  ```hcl
  # Example: Terraform module for hybrid networking
  module "vpc_peering" {
    source = "./modules/vpc-peering"
    vpc_id_onprem  = "vpc-123456"
    vpc_id_cloud   = aws_vpc.cloud.id
    peer_vpc_id    = aws_vpc.cloud.id
  }
  ```
- **Enforce resource quotas** to prevent over-allocation:
  ```yaml
  apiVersion: v1
  kind: ResourceQuota
  metadata:
    name: pod-quota
  spec:
    hard:
      pods: "20"
      requests.cpu: "10"
      requests.memory: "40Gi"
  ```

### **B. Observability & Alerting**
- **Set up cross-environment monitoring** (e.g., Prometheus + Loki for logs).
- **Alert on anomalies** (e.g., pod restarts > 3 in 5 mins):
  ```yaml
  # Example: Prometheus alert rule
  - alert: HighPodRestarts
    expr: kube_pod_container_status_restarts_total > 3
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Pod {{ $labels.pod }} is restarting too often"
  ```

### **C. Chaos Engineering**
- **Test failure scenarios** (e.g., kill a node, simulate network partitions):
  ```bash
  # Kill a node (non-destructive test)
  kubectl delete node <node-name>
  ```
- **Use tools like Chaos Mesh** to simulate:
  - Node failures.
  - Network latency.
  - Pod evictions.

### **D. Documentation & Runbooks**
- **Document hybrid-specific configurations** (e.g., VPC peering, IAM roles).
- **Create a runbook** for common issues (e.g., "Pods stuck in Pending → Check PVCs").

---

## **5. Summary Checklist for Quick Resolution**
| **Step** | **Action**                                                                 |
|----------|-----------------------------------------------------------------------------|
| 1        | **Isolate the scope**: On-prem? Cloud? Both?                                |
| 2        | **Check logs**: `kubectl logs <pod> --previous`                            |
| 3        | **Verify resources**: `kubectl top nodes`, `kubectl describe pod`          |
| 4        | **Test connectivity**: `kubectl exec -it <pod> -- ping <service>`          |
| 5        | **Review network policies**: `kubectl get networkpolicies`                |
| 6        | **Check RBAC/IAM**: `kubectl auth can-i --list`                           |
| 7        | **Monitor cross-env latency**: Use `dig`/`nslookup` or distributed tracing|
| 8        | **Reproduce in staging**: Use Terraform to spin up a test environment.       |

---
**Final Tip:** Hybrid setups are **inherently complex**. **Start small**—validate changes in a staging environment before rolling out to production. Use **automated rollback** (e.g., Argo Rollouts) to minimize blast radius.

Would you like a deep dive on any specific subtopic (e.g., Istio hybrid mesh, database sync)?