# **[Pattern] Containers Tuning Reference Guide**
*Optimizing resource allocation, performance, and operational efficiency in containerized environments*

---

## **1. Overview**
Containers Tuning is a systematic approach to optimizing containerized workloads for **performance, reliability, and cost efficiency**. Unlike static configurations, tuning adjusts runtime parameters (CPU, memory, storage, networking, security, etc.) based on workload demands, infrastructure constraints, and operational priorities. This guide covers key tuning techniques for **Kubernetes, Docker, and generic container runtimes**, including best practices for:
- **Resource limits and requests** (CPU/memory constraints).
- **Storage and filesystem tuning** (overlay, storage drivers, limits).
- **Networking optimizations** (CNCF networks, QoS policies).
- **Security hardening** (capabilities, SELinux/AppArmor, seccomp).
- **Performance profiling** (metrics, autoscaling, profiling tools).

Tuning ensures containers scale predictably, avoid resource starvation, and align with enterprise-grade SLAs. Use this guide to benchmark, validate, and iterate on container configurations for **development, testing, or production** environments.

---

## **2. Implementation Details**

### **2.1 Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example Values/Use Cases**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Resource Requests**  | Minimum guaranteed resources (CPU/memory) for a container.                                         | `requests.cpu: "100m"` (0.1 vCPU), `requests.memory: "256Mi"`                               |
| **Resource Limits**    | Maximum allowed resources to prevent runaway containers.                                          | `limits.cpu: "500m"`, `limits.memory: "1Gi"`                                               |
| **CPU Throttling**     | Dynamic allocation of CPU shares when resources are scarce.                                        | `cpu.quota: 100000`, `cpu.period: 100000` (burstable mode)                                  |
| **Memory Swapping**    | Whether containers can use disk as memory (avoid OOM kills).                                        | `memory.swappiness: 1` (disables swapping)                                                  |
| **Ephemeral Storage**  | Temporary filesystem storage limits (e.g., `/tmp`, logs).                                          | `limits.ephemeral-storage: "1Gi"`                                                          |
| **Network QoS**        | Priority and bandwidth guarantees for network traffic.                                             | `networkPolicy.egress: {"bandwidth": "100Mbps"}`                                           |
| **SELinux/AppArmor**   | Mandatory Access Control (MAC) policies to restrict container actions.                            | Profile: `docker-default`, `k8s-apparmor`                                                   |
| **Seccomp Profiles**   | Restrict syscalls (e.g., disable `ptrace` for security).                                          | Profile: `runtime/default`, `local:///etc/seccomp.json`                                    |
| **Read-Only RootFS**   | Prevent modifications to the container filesystem (security).                                      | `readOnlyRootFilesystem: true`                                                             |
| **PID Limits**         | Restrict the number of processes a container can spawn.                                           | `pidLimit: 1000`                                                                             |

---

### **2.2 Core Tuning Categories**

#### **A. CPU and Memory Optimization**
| **Parameter**               | **Purpose**                                                                 | **Configuration Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `requests.cpu`              | Guaranteed CPU allocation (millicores).                                    | `cpu("500m")` in Kubernetes YAML.                                                        |
| `limits.cpu`                | Hard limit on CPU usage (prevents throttling).                             | `resources.limits: {"cpu": "2"}`                                                        |
| `memory.requests`           | Minimal memory allocation (avoids eviction).                               | `memory: "512Mi"`                                                                        |
| `memory.limits`             | Max memory before OOM (Out-Of-Memory) kill.                                 | `memory: "1Gi"`                                                                          |
| `memory.swappiness`         | Swap behavior (0=disable, 60=default).                                     | Set via `docker run --memory-swappiness=0`.                                             |
| **CPU Manager (K8s)**       | Policies for CPU allocation (static, dynamic, best-effort).                | `spec.ephemeralContainers` with `resources.cpuManager`.                                 |

**Best Practice:**
- For **stateless services**, set `requests` = `limits` to reserve resources.
- For **stateful workloads** (e.g., databases), allocate **20-30% buffer** above peak usage.

---

#### **B. Storage Tuning**
| **Parameter**               | **Purpose**                                                                 | **Configuration Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Storage Driver**          | Backend for container layers (e.g., `overlay2`, `devicemapper`).             | `storage-driver: overlay2` in `docker daemon.json`.                                       |
| `readOnlyRootFS`            | Prevent writes to container filesystem.                                      | `securityContext.readOnlyRootFilesystem: true` in Kubernetes.                            |
| `volumeRequest`             | Persistent volume size limits.                                              | `storage.request: 10Gi` in CSI driver.                                                   |
| **OverlayFS Tuning**        | Performance tweaks for overlay2 (e.g., `upperdir_size`).                    | `kernel.parameters: {"fs.overlay.upper_dir_size": "2G"}` in `kubelet` args.               |
| **Node Affinity**           | Schedule pods on nodes with sufficient storage.                             | `nodeSelector: {"storage-class": "ssd"}`                                                 |

**Best Practice:**
- Use **ssd-backed storage** for `/tmp` and `/var/lib/docker` to reduce latency.
- Monitor `docker stats --no-stream` for storage bloat (e.g., unused layers).

---

#### **C. Networking**
| **Parameter**               | **Purpose**                                                                 | **Configuration Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **CNCF Network Plugin**     | Underlay network (e.g., `calico`, `cilium`, `flannel`).                     | `kube-proxy --conntrack-max=1000000`.                                                  |
| `networkPolicy.egress`      | Block/allow traffic to specific ports/ips.                                  | ```yaml egress: - to: - port: "80" protocol: TCP```                                    |
| **QoS Class**               | Pod priority (Guaranteed, Burstable, BestEffort).                           | `resources.qosClass: "Guaranteed"`                                                      |
| **MTU Tuning**              | Adjust packet size to avoid fragmentation (common with VPNs).                | `networks: {"macvlan": {"mtu": 1500}}`                                                  |
| **TCP Keepalive**           | Prevent stale connections (e.g., `tcp_keepalive_time`).                     | `sysctl: net.ipv4.tcp_keepalive_time=600` in init container.                              |

**Best Practice:**
- Set **MTU=1450** for environments with overlapping networks (e.g., AWS VPC + VPN).
- Use **priority classes** (`k8s.io/preemption-policy: PreemptLowerPriority`) for critical workloads.

---

#### **D. Security Hardening**
| **Parameter**               | **Purpose**                                                                 | **Configuration Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Capabilities Dropping**   | Remove dangerous syscalls (e.g., `NET_RAW`, `SYS_ADMIN`).                   | `securityContext.capabilities.drop: ["ALL"]`                                              |
| **SELinux/AppArmor**        | Enforce manditory access control.                                           | `securityContext.seLinuxOptions.level: "s0:c123,c456"`                                   |
| **Seccomp Profiles**        | Restrict syscalls (e.g., block `execve`).                                   | ```yaml seccompProfile: type: RuntimeDefault```                                         |
| **User/Group Mappings**     | Run containers as non-root users.                                            | `securityContext.runAsUser: 1000`                                                        |
| **Pod Security Admission**  | Enforce runtime security policies (e.g., `PodSecurityPolicy` → `PodSecurity`). | ```yaml admissionReviewVersions: ["v1"]```                                               |

**Best Practice:**
- Start with **`runtime/default` seccomp** and audit logs for blocked syscalls.
- Use **`kube-bench`** to validate compliance with CIS benchmarks.

---

#### **E. Autoscaling and Monitoring**
| **Parameter**               | **Purpose**                                                                 | **Configuration Example**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **HPA (Horizontal Pod Autoscaler)** | Scale based on CPU/memory/metrics.                                       | ```yaml metrics: - type: Resource - resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 }} ``` |
| **Vertical Pod Autoscaler** | Adjust `requests/limits` dynamically.                                      | Enable via `kube-pssp` (Pod and Resource Standards Planner).                             |
| **Prometheus Metrics**      | Track container metrics (e.g., `container_cpu_usage_seconds_total`).      | ```yaml livenessProbe: httpGet: { path: /health, port: 8080 }```                          |
| **cAdvisor Integration**    | Collect runtime performance data.                                          | Deploy `cadvisor` sidecar or use `kubelet --containerized`.                              |

**Best Practice:**
- Use **custom metrics** (e.g., Redis queue length) for non-resource-based scaling.
- Set **stable window** in HPA (e.g., `behavior.scaleDown.stableWindow: "5m"`) to avoid thrashing.

---

## **3. Schema Reference (Kubernetes CRDs)**
Below are key **Custom Resource Definitions (CRDs)** and **ConfigMaps** for tuning:

| **Resource**               | **Schema**                                                                 | **Purpose**                                                                 |
|----------------------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **`LimitRange`**           | ```yaml apiVersion: v1 kind: LimitRange metadata: name: mem-cpu-limits spec: limits: - default: 500m max: 2 maxLimitRequestRatio: 1.0 type: Container``` | Enforce default/max `requests`/`limits` across namespaces.                  |
| **`PodSecurityPolicy`**    | ```yaml apiVersion: policy/v1 kind: PodSecurityPolicy spec: privileged: false seccompProfiles: - type: RuntimeDefault``` | Restrict pod capabilities/seccomp.                                            |
| **`VerticalPodAutoscaler`**| ```yaml apiVersion: autoscaling.k8s.io/v1 kind: VerticalPodAutoscaler spec: resourcePolicy: containerPolicies: - containerName: app-1 mode: Auto minAllowed: {"cpu": "100m", "memory": "256Mi"}``` | Adjust container `requests/limits` dynamically.                               |
| **`DaemonSet` Tuning**     | ```yaml template: spec: containers: - name: dockerd resources: limits: memory: "2Gi" securityContext: capabilities: drop: ["ALL"]``` | Configure DaemonSet pods (e.g., `kube-proxy`).                                 |

---
## **4. Query Examples**

### **A. Kubernetes**
#### **1. Check Current Resource Usage**
```sh
kubectl top pods --all-namespaces
kubectl describe pod <pod> | grep -i limits
```

#### **2. Apply CPU/Memory Limits**
```yaml
# limits.yaml
apiVersion: v1
kind: Pod
metadata:
  name: tuned-pod
spec:
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: "200m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
---
kubectl apply -f limits.yaml
```

#### **3. Enable SELinux**
```sh
kubectl edit deploy <deployment>  # Add under securityContext:
  runAsUser: 1000
  seLinuxOptions:
    level: "s0:c123,c456"
```

#### **4. Scale Pods with HPA**
```sh
# Create HPA for deployment
kubectl autoscale deployment nginx --cpu-percent=50 --min=2 --max=10
```

---

### **B. Docker**
#### **1. Set CPU Shares**
```sh
docker run --cpus=0.5 --cpuset-cpus=0 nginx
```

#### **2. Limit Memory and Swap**
```sh
docker run --memory=512m --memory-swappiness=0 my-image
```

#### **3. Configure Docker Daemon (Tuning)**
```json
# /etc/docker/daemon.json
{
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  },
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
# Restart Docker:
sudo systemctl restart docker
```

#### **4. Profile Container Performance**
```sh
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
# For per-container metrics:
docker stats <container> --no-stream
```

---

## **5. Related Patterns**
Consult these complementary patterns for end-to-end container optimization:

1. **[Multi-Stage Builds](https://docs.docker.com/develop/develop-images/multistage-build/)**
   - *Reduce image size by separating build from runtime dependencies.*

2. **[Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)**
   - *Distribute pods across nodes/racks for high availability.*

3. **[Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)**
   - *Enforce namespace-wide limits (e.g., "No team can exceed 10 pods").*

4. **[Service Mesh (Istio/Linkerd)](https://istio.io/latest/docs/concepts/traffic-management/)**
   - *Fine-tune network policies, mTLS, and observability.*

5. **[Cluster Autoscaling](https://kubernetes.io/docs/tasks/run-application/cluster-autoscaling/)**
   - *Scale nodes based on pod pressure (complements HPA).*

6. **[Observability Stack (Prometheus + Grafana)](https://prometheus.io/docs/introduction/overview/)**
   - *Monitor tuned containers with custom dashboards.*

7. **[Distributed Tracing (Jaeger/Zipkin)](https://www.jaegertracing.io/docs/latest/)**
   - *Trace performance bottlenecks in microservices.*

8. **[GitOps (ArgoCD/Flux)](https://argoproj.github.io/argo-cd/)**
   - *Declaratively manage tuned configurations in Git.*

---
## **6. Validation and Iteration**
After applying tunings:
1. **Benchmark**: Use `kubectl top` or `docker stats` to verify resource usage.
2. **Audit Logs**: Check `kube-apiserver` and container logs for errors.
3. **Chaos Testing**: Simulate failures (e.g., `kubectl delete pod --grace-period=0`).
4. **Rollback**: Use Git history or `kubectl rollout undo` for deployments.

---
**Note**: Tuning is iterative—start conservative and adjust based on **real-world workloads**. Monitor for:
- **CPU Throttling** (`kubectl describe pod | grep "CPU Throttling"`).
- **OOM Kills** (`journalctl -u kubelet | grep -i "oom"`).
- **Network Latency** (`tc qdisc show dev eth0`).