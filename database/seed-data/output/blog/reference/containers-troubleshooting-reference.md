**[Pattern] Containers Troubleshooting Reference Guide**

---

### **Overview**
Troubleshooting containerized applications requires systematic diagnosis of issues across layers—runtime, orchestration, networking, storage, and application logic. This guide provides structured methods, tools, and best practices to identify and resolve common container failures, performance bottlenecks, and misconfigurations. Coverage includes container runtime errors, Kubernetes-specific issues, logging, monitoring, and lifecycle debugging. Use this guide for on-demand troubleshooting or as a checklist for proactive maintenance.

---

### **Key Concepts & Implementation Details**

#### **1. Troubleshooting Layers**
- **Container Runtime Layer**: Debug `docker`, `containerd`, or `cri-o` processes, images, and execution environments.
- **Orchestration Layer**: Investigate Kubernetes (`kubelet`, API server, etcd), Nomad, Swarm, or standalone deployments.
- **Networking Layer**: Check pod connectivity, DNS resolution, service meshes, and ingress/egress rules.
- **Storage Layer**: Validate volume mounts, persistent storage claims, and data consistency.
- **Application Layer**: Analyze logs, metrics, and container health for logic errors or resource starvation.

---

### **Schema Reference**
Below are common schemas used in container troubleshooting (simplified for clarity):

| **Category**               | **Schema**                                                                 | **Example Output**                                                                 |
|----------------------------|---------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Container Runtime Events** | `{ "time": "<ISO8601>", "type": "error", "message": "<text>", "details": { } }` | `{"time": "2024-01-01T12:00:00Z", "type": "warn", "message": "OOM killed pod", "details": {"pod": "nginx-abc123"}}` |
| **Kubernetes Pod Status**   | `{ "pod": "<name>", "status": "<Running/Failed>`, "restarts": <int>, "events": [<log_entry_array>] }` | `{"pod": "webapp-456", "status": "CrashLoopBackOff", "restarts": 5}`               |
| **Network Connectivity**    | `{ "source": "<pod>", "target": "<service>", "protocol": "<TCP/UDP>", "status": "<Success/Fail>", "latency": <ms> }` | `{ "source": "db-pod", "target": "api-gateway", "status": "Fail", "latency": null }` |
| **Resource Usage**          | `{ "container": "<name>", "cpu": { "usage": <int>, "limit": <int> }, "memory": { "usage": <GB>, "limit": <GB> } }` | `{ "container": "app", "cpu": {"usage": 300, "limit": 1000}, "memory": {"usage": 1.2, "limit": 2.0}}` |

---

### **Query Examples**

#### **1. Identify Failing Pods**
Use `kubectl` to list pods in `Failed` or `CrashLoopBackOff` states:
```bash
kubectl get pods --all-namespaces -o jsonpath='{range .items[?(@.status.phase=="Failed")]}{.metadata.namespace}/{.metadata.name} {.metadata.creationTimestamp} {"\n"}{end}'
```
**Output Example**:
```
default/nginx-abc123 2024-01-01T11:00:00Z
kube-system/coredns-123 2024-01-02T09:30:00Z
```

#### **2. Debug Container Logs**
Stream logs for a failing pod:
```bash
kubectl logs <pod-name> --previous  # For the last terminated instance
kubectl logs <pod-name> -c <init-container>  # If multi-container pod
```

#### **3. Check Resource Limits**
Inspect CPU/memory constraints:
```bash
kubectl describe pod <pod-name> | grep -E 'Limits|Requests'
```
**Output Example**:
```
Limits:
  cpu:     500m
  memory:  512Mi
Requests:
  cpu:      200m
  memory:   256Mi
```

#### **4. Network Troubleshooting**
Test connectivity between pods:
```bash
kubectl exec -it <pod-name> -- curl -v http://<service-name>
```
Check DNS resolution for a pod:
```bash
kubectl run -it --rm --image=busybox:1.28 dns-test -- nslookup <service-name>
```

#### **5. Diagnose OOM Kills**
Review kernel logs for out-of-memory events:
```bash
journalctl -u kubelet --no-pager | grep -i "oom"
```

#### **6. Validate Storage**
Check volume mount status:
```bash
kubectl describe pod <pod-name> | grep -A 5 "Volumes:"
```
**Output Example**:
```
Volumes:
  config-volume:
    Type:        ConfigMap (a container volume mounted from a ConfigMap)
    Name:        nginx-config
    Optional:    false
```

#### **7. Inspect API Server Errors**
List API server conditions:
```bash
kubectl get --raw="/readyz?verbose" | jq '.conditions'
```

---

### **Step-by-Step Troubleshooting Workflow**
1. **Verify Orchestration Health**:
   - Check cluster API server (`kubectl get nodes`).
   - Validate `kubelet` status (`ps aux | grep kubelet`).
   - Review etcd health (`ETCDCTL_API=3 etcdctl endpoint health`).

2. **Isolate the Container**:
   - Use `kubectl describe pod <name>` to inspect events and conditions.
   - Review logs (`kubectl logs <pod-name> -n <namespace>`).

3. **Check Resource Constraints**:
   - Compare usage vs. limits (`kubectl top pods`).
   - Identify throttling (`kubectl get events --sort-by=.metadata.creationTimestamp`).

4. **Network Validation**:
   - Verify pod IP assignment (`kubectl get pods -o wide`).
   - Test connectivity using `kubectl exec` for DNS or direct endpoints.

5. **Storage Checks**:
   - Ensure volumes are attached (`kubectl describe pod`).
   - Validate PVC claims (`kubectl get pvc`).

6. **Application-Specific Debugging**:
   - Capture container logs (e.g., `kubectl logs -l app=web --tail=100`).
   - Use sidecars for distributed tracing (e.g., OpenTelemetry).

---

### **Tools & Utilities**
| **Tool**               | **Purpose**                                                                 |
|------------------------|----------------------------------------------------------------------------|
| `kubectl`              | Core Kubernetes CLI for pod/cluster inspection.                            |
| `stern`                | Multipod log aggregation (`stern <label> -n <namespace>`).                |
| `crictl`               | Debug container runtime (CRI-compatible containers).                        |
| `fluentd`/`Loki`       | Centralized log aggregation for containerized apps.                        |
| `Prometheus/Grafana`   | Metrics monitoring for resource usage and app health.                      |
| `Netdata`/`Datadog`    | Real-time monitoring for container performance.                            |

---

### **Common Issues & Mitigations**

| **Issue**                          | **Root Cause**                          | **Resolution**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------------|
| **Pod in `ImagePullBackOff`**      | Invalid image tag or registry auth issue| Verify image tag (`kubectl describe pod`) and update `imagePullSecrets`.       |
| **CrashLoopBackOff**                | Application crash loop                  | Check logs (`kubectl logs --previous`) for errors; adjust resource limits.     |
| **Pod Eviction (OOM)**              | Memory exhaustion                       | Scale down non-critical workloads; adjust `requests/limits`.                  |
| **NetworkPartition**                | Misconfigured CNI plugin               | Validate CNI plugin logs (`kubectl logs -n kube-system <cni-pod>`).            |
| **PersistentVolumeClaim Stuck**    | Storage backend issues                  | Check PVC events (`kubectl describe pvc`) and validate storage class availability. |

---

### **Related Patterns**
1. **[Observability Patterns for Containers](https://reference-guides.example.com/observability)**
   - Implement structured logging, metrics, and tracing for containers.
2. **[Container Security Best Practices](https://reference-guides.example.com/security)**
   - Harden images, enforce RBAC, and audit container runtime logs.
3. **[Scaling Containers with Horizontal Pod Autoscaler](https://reference-guides.example.com/scaling)**
   - Automate scaling based on CPU/memory thresholds.
4. **[Multi-Architecture Containers](https://reference-guides.example.com/multi-arch)**
   - Build and deploy containers for hybrid cloud environments.
5. **[Service Mesh Integration](https://reference-guides.example.com/service-mesh)**
   - Use Istio/Linkerd for advanced networking and observability.

---
### **Further Reading**
- [Kubernetes Debugging Guide (Official Docs)](https://kubernetes.io/docs/tasks/debug/)
- [Container Runtime Security](https://www.cisecurity.org/cis-benchmarks/)
- [CNCF Troubleshooting Playbook](https://github.com/cncf/troubleshooting-playbooks)