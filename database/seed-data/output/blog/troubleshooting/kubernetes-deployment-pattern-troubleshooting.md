# **Debugging Kubernetes Production Deployment Pattern: A Troubleshooting Guide**
*A comprehensive troubleshooting guide for Kubernetes deployments with Horizontal Pod Autoscaler (HPA), Pod Security, and Network Policies.*

---

## **1. Overview**
This guide helps diagnose and resolve common issues in a **production-grade Kubernetes deployment** pattern that includes:
- **Horizontal Pod Autoscaler (HPA)** for auto-scaling
- **Pod Security Policies / OPA Gatekeeper or PodSecurityPolicy (deprecated but still in use)**
- **Network Policies** for pod-to-pod and ingress/egress control

Common symptoms include **auto-scaling failures, security misconfigurations, resource starvation, and unnecessary network exposure**.

---

## **2. Symptom Checklist**
Before diving into fixes, verify which symptoms match your environment:

| **Symptom**                          | **Question to Ask**                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------------|
| No autoscaling despite HPA configured | Is HPA scaling up/down? Are custom metrics correctly ingested?                     |
| OOMKills or CPU throttling           | Are resource limits too low? Are pods starving due to contention?                 |
| Security violations (e.g., root pods) | Are PodSecurityPolicies or OPA Gatekeeper enforcing rules?                       |
| Unauthorized pod-to-pod traffic     | Are Network Policies blocking unexpected traffic?                                 |
| Unexpected pod restarts              | Are preStop hooks failing? Are liveness/readiness probes misconfigured?            |
| High latency or timeouts             | Are pods waiting on resources? Are ingress rules too restrictive?                  |

---

## **3. Common Issues & Fixes**

### **A. HPA Not Autoscaling (Symptom: No Scaling)**
#### **Root Causes & Fixes**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix (YAML/Code Example)**                          |
|------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| Missing custom metrics             | Check `kubectl get --raw "/apis/autoscaling/v2beta2/custommetrics.k8s.io"`         | Ensure Metrics Server is installed + custom metrics are scraped. |
| CPU/Memory metrics too low          | `kubectl describe hpa <name>` check "current CPU usage" vs. target            | Adjust `metrics.targets.type` (e.g., `Resource` → `Pods`). |
| ScaleDown delays                   | HPA `behavior.scaleDown.stabilizationWindowSeconds` too long                     | Reduce to `300` (default is `3600`). |
| External dependencies slow        | HPA waits for external metrics (e.g., Prometheus) to update                      | Increase `minReadySeconds` or reduce `metrics.interval`. |
| **Example Fix:** Adjust HPA for custom metrics | ```yaml | kubectl edit hpa my-deployment-hpa ``` | `minReadySeconds: 5` `behavior.scaleDown.policies: - type: Percent - value: 10 - periodSeconds: 60` |

---

### **B. Resource Starvation (Symptom: OOMKills, Throttling)**
#### **Root Causes & Fixes**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix (YAML/Code Example)**                          |
|------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| No resource limits set             | `kubectl describe pod <pod>` → "OutOfMemory" or "CPU overcommit"                  | Set `resources.limits.cpu`/`memory` in Deployment. |
| Limits too low                     | Check `kubectl top pods` → CPU/Memory usage exceeds limits                        | Increase limits (e.g., `1 CPU → 2 CPU`).          |
| No requests for QOS guarantees     | Pods marked as `BestEffort` (no requests)                                          | Set `resources.requests.cpu`/`memory`             |
| **Example Fix:** Adjust Pod Resources | ```yaml | apiVersion: apps/v1 kind: Deployment metadata: name: my-app spec: template: spec: containers: - name: my-container resources: limits: cpu: "2" memory: "2Gi" requests: cpu: "1" memory: "1Gi" ``` |

---

### **C. Security Violations (Symptom: Root Pods, Unrestricted Access)**
#### **Root Causes & Fixes**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix (YAML/Code Example)**                          |
|------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| Pod runs as `root`                 | `kubectl describe pod <pod> | grep "User"` → `root`                              | Enforce `securityContext.runAsNonRoot: true`      |
| No PodSecurityPolicy (PSP) / Gatekeeper | Check if a PSP/Gatekeeper is applied in `ClusterRoleBinding`.                     | Define a PSP (deprecated) or OPA Gatekeeper policy. |
| **Example Fix:** Enforce PSP (Legacy) | ```yaml | apiVersion: policy/v1beta1 kind: PodSecurityPolicy metadata: name: restricted spec: privileged: false runAsUser: rule: MustRunAsNonRoot ``` | Apply via `ClusterRoleBinding`: ```yaml kind: ClusterRoleBinding apiVersion: rbac.authorization.k8s.io/v1 metadata: name: my-app-restricted roles: - name: my-app-restricted subjects: - kind: Group name: my-team ``` |

**Modern Alternative (OPA Gatekeeper):**
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: pod-security.yaml
spec:
  crd:
    spec:
      names:
        kind: PodSecurity
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package kubernetes.admission.podsecurity
        violation[{"message": msg}] {
          input.review.object.kind.kind == "Pod"
          not input.review.object.spec.securityContext.runAsNonRoot
          msg := sprintf("Pods must not run as root", [input.review.object.metadata.name])
        }
```

---

### **D. Unrestricted Network Traffic (Symptom: Unauthorized Pod Communication)**
#### **Root Causes & Fixes**
| **Issue**                          | **Debugging Steps**                                                                 | **Fix (YAML/Code Example)**                          |
|------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------|
| Default `NetworkPolicy` allows all | Check `kubectl get networkpolicy` → No policies or `allow: all`                  | Define strict `NetworkPolicy` rules.               |
| Ingress from external IPs           | Check `kubectl describe networkpolicy` → No `ingress` rules for external traffic | Restrict ingress to trusted CIDRs (e.g., cloud load balancer). |
| **Example Fix:** Restrict Pod Communication | ```yaml | apiVersion: networking.k8s.io/v1 kind: NetworkPolicy metadata: name: deny-all-except-frontend spec: podSelector: {} policyTypes: - Ingress - Egress ingress: - from: - podSelector: matchLabels: app: frontend ports: - protocol: TCP port: 80 egress: - to: - podSelector: matchLabels: app: backend ports: - protocol: TCP port: 6379 ``` |

**Debugging Network Issues:**
- Use `kubectl get events --field-selector involvedObject.kind=Pod` to check pod-init failures.
- Test connectivity with `kubectl exec -it <pod> -- curl <target-pod>`.

---

## **4. Debugging Tools & Techniques**
### **A. Metrics & Monitoring**
- **kubectl top pods** → Real-time CPU/Memory usage.
- **kubectl describe hpa** → HPA scaling events.
- **Prometheus/Grafana** → Long-term metrics (CPU, memory, latency).
- **kube-state-metrics** → Exposes Kubernetes object metrics (e.g., pod count).

### **B. Logging & Events**
- **kubectl logs <pod>** → Check pod-level logs.
- **kubectl get events --sort-by=.metadata.creationTimestamp** → Cluster-wide events.
- **EFK Stack (Elasticsearch, Fluentd, Kibana)** → Centralized logging.

### **C. Security Auditing**
- **kubectl auth can-i** → Check pod RBAC permissions.
- **kube-bench** → CIS compliance scanner.
- **kubeaudit** → Policy-as-code for Kubernetes configurations.

### **D. Network Troubleshooting**
- **kubectl get networkpolicy** → List active policies.
- **tcpdump in a sidecar** → Inspect pod traffic (requires `net-tools`).
- **kube-router/Calico CLI** → Debug CNI-specific issues.

---

## **5. Prevention Strategies**
### **A. Automate with GitOps**
- Use **ArgoCD/Flux** to sync configurations from Git.
- Enforce **policy-as-code** (e.g., OPA Gatekeeper, Kyverno).
- Example: Block `privileged: true` pods via policy:
  ```yaml
  apiVersion: templates.gatekeeper.sh/v1beta1
  kind: ConstraintTemplate
  metadata:
    name: no-privileged-pods
  spec:
    crd:
      spec:
        names:
          kind: K8sNoPrivilegedPods
    targets:
      - target: admission.k8s.gatekeeper.sh
        rego: |
          package kubernetes.admission
          violation[{"msg": msg}] {
            input.review.object.spec.containers[_].securityContext.privileged
            msg := "Pods must not have privileged security context"
          }
  ```

### **B. Define Resource Quotas**
- Prevent over-provisioning:
  ```yaml
  apiVersion: v1
  kind: ResourceQuota
  metadata:
    name: my-namespace-quota
  spec:
    hard:
      requests.cpu: "10"
      requests.memory: 40Gi
      limits.cpu: "12"
      limits.memory: 50Gi
  ```

### **C. Enforce Network Policies by Default**
- Start with **deny-all** and whitelist only necessary traffic.
- Use **Calico’s `NetworkPolicyController`** for automated policy generation.

### **D. Test HPA Scaling with Chaos Engineering**
- Use **Chaos Mesh** to simulate node failures and verify HPA reacts.
- Example:
  ```yaml
  apiVersion: chaos-mesh.org/v1alpha1
  kind: PodChaos
  metadata:
    name: pod-failure-test
  spec:
    action: pod-failure
    mode: one
    selector:
      namespaces:
        - default
      labelSelectors:
        app: my-app
    duration: "30s"
  ```

---

## **6. Summary Checklist for Quick Resolution**
| **Issue**               | **Quick Fix**                                                                 |
|-------------------------|------------------------------------------------------------------------------|
| HPA not scaling         | Check metrics endpoint, adjust `minReadySeconds`, verify custom metrics.     |
| OOMKills                | Increase `resources.limits` or set `requests` for QOS guarantees.             |
| Unauthorized pods       | Enforce `runAsNonRoot` + OPA Gatekeeper.                                     |
| Network misconfigurations | Use `deny-all` policies, restrict ingress to known IPs.                     |
| Unstable deployments    | Check liveness probes, preStop hooks, and resource contention.              |

---
**Final Tip:** Always test changes in a **staging environment** before applying to production. Use **canary deployments** with HPA to roll out updates safely.

---
**Need deeper dives?** Check these resources:
- [Kubernetes Best Practices (CNCF)](https://github.com/kubernetes/website/blob/master/content/en/docs/concepts/cluster-administration/)
- [HPA Troubleshooting](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/)
- [OPA Gatekeeper Docs](https://open-policy-agent.github.io/gatekeeper/website/docs/)