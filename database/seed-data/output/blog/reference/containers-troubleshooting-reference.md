# **[Pattern] Containers Troubleshooting – Reference Guide**

---

## **Overview**

Containers offer portability, efficiency, and isolation, but issues like crashes, resource constraints, network misconfigurations, or dependency failures can disrupt operations. This reference guide provides structured diagnostics for common container problems, covering **log analysis, resource monitoring, network checks, runtime issues, and rollback strategies**. It follows a **systematic troubleshooting workflow**—identify symptoms, isolate the root cause, and apply targeted fixes—while leveraging tools like `kubectl`, `docker stats`, `crictl`, and host-level utilities.

Key scenarios addressed:
- **Container crashes or restarts** (OOM, segmentation faults, exit codes)
- **Performance degradation** (CPU/memory throttling, slow I/O)
- **Network connectivity failures** (DNS, port conflicts, egress restrictions)
- **Image/pull failures** (registry issues, authentication errors)
- **Volume/persistent storage errors** (mount failures, permissions)
- **Init/entrypoint execution failures** (missing dependencies, misconfigurations)

The guide assumes familiarity with basic container orchestration (e.g., Docker, Kubernetes) and terminal commands.

---

## **1. Schema Reference**
Troubleshooting follows a **structured schema** to categorize symptoms, probable causes, and remediation steps. Below is a reference table for common issues.

| **Category**               | **Symptom**                       | **Probable Cause**                          | **Verification Commands**                          | **Remediation Steps**                                          |
|----------------------------|-----------------------------------|---------------------------------------------|----------------------------------------------------|---------------------------------------------------------------|
| **Runtime Environment**    | Container exits with code `137`    | OOM Killer terminated process               | `docker stats --no-stream`, `kubectl describe pod`  | Increase memory limits, debug memory leaks (`valgrind`).       |
|                            | Container crashes with `SIGSEGV`   | Segmentation fault (code `11`)              | `docker logs <container>`, `gdb` (core dumps)      | Check for buffer overflows, update libraries.                  |
| **Resource Constraints**   | High CPU/memory usage              | No resource limits (or insufficient limits) | `docker stats`, `kubectl top pod`                   | Set CPU/memory requests/limits; use resource quotas.          |
|                            | Disk I/O saturation                | Slow storage backend                        | `iostat -x 1`, `kubectl describe pod -n <ns> <pod>` | Upgrade storage class, check for spinning disks.              |
| **Networking**             | Container cannot resolve DNS       | Misconfigured `dnsPolicy` or DNS pod        | `cat /etc/resolv.conf`, `kubectl get events`        | Verify `kube-dns` health; check `dnsConfig` in YAML.           |
|                            | Port conflicts (e.g., `443`)       | Port already in use                         | `netstat -tulnp`, `kubectl get endpoints`          | Change port mapping in `ports` section of deployment.         |
|                            | Egress traffic blocked             | NetworkPolicy or firewall rules              | `kubectl describe networkpolicy`                  | Adjust `NetworkPolicy` rules or host firewall (`iptables`).     |
| **Image/Dependency**       | Pull failure (`500 Internal Error`)| Invalid image or auth failure               | `docker pull --verbose`                            | Check credentials (`docker login`), verify image tag.           |
|                            | Missing dependencies               | Missing `.so` files or missing CLI tools     | `ldd <executable>`, `apt-cache policy <package>`    | Rebuild image with dependencies or use multi-stage builds.     |
| **Volume Storage**         | Volume mount fails (`Permission`) | SELinux/AppArmor or incorrect permissions   | `mount | grep <volume>`, `ls -la /host/mount`               | Adjust `fsGroup` in SecurityContext; chmod/chown volumes.     |
|                            | Persistent volume not found        | Dynamic provisioning failure                | `kubectl get pvc`                                  | Check PVC `status.phase`; verify storage class.               |
| **Init/Entrypoint**        | Init container fails                | Missing or misconfigured entrypoint          | `kubectl logs <pod> -c <init-container>`           | Verify `command` in container spec; test manually.             |
|                            | Entrypoint hangs                   | Infinite loop or blocked I/O                | `ps aux`, `strace -p <PID>`                        | Debug with `strace` or add health checks.                     |
| **Orchestration**          | Pod stuck in `Pending`             | Node resource unavailable                   | `kubectl describe node`, `kubectl get events`      | Scale up nodes; check taints/tolerations.                     |
|                            | CrashLoopBackOff                    | Unhandled exceptions in app                 | `kubectl logs <pod> --tail=50`                    | Fix application logic; adjust restart policy (`livenessProbe`). |

---

## **2. Query Examples**
Below are **command-line snippets** to diagnose container issues across environments.

---

### **A. Basic Container Inspection**
#### **List running containers and their status**
```bash
# Docker
docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# Kubernetes
kubectl get pods --all-namespaces -o wide
```

#### **Check container logs**
```bash
# Docker (last 100 lines)
docker logs --tail=100 <container_name>

# Kubernetes (select pod/container)
kubectl logs <pod_name> -c <container_name> --previous  # If crashed
```

#### **Inspect container metadata**
```bash
# Docker
docker inspect --format='{{json .}}' <container_id> | grep -i "exit"

# Kubernetes
kubectl describe pod <pod_name> | grep -E "Events|State|Containers"
```

---

### **B. Resource Analysis**
#### **Check CPU/memory usage**
```bash
# Docker
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Kubernetes
kubectl top pod --sort-by=cpu
```

#### **Identify OOM Killer victims**
```bash
# Check kernel logs for OOM events
dmesg | grep -i "killed process"
```

#### **Profile memory usage**
```bash
# Heap dump (Java)
docker exec <container> jmap -dump:format=b,file=heap.hprof <PID>

# Top processes inside container
docker exec <container> top -c
```

---

### **C. Network Diagnostics**
#### **Test connectivity from within a container**
```bash
# Ping an external host
docker exec <container> ping -c 4 google.com

# Check routes
docker exec <container> ip route
```

#### **Verify port exposure**
```bash
# Check if a port is listening
nc -zv <container_ip> <port>

# Kubernetes port forwarding
kubectl port-forward <pod_name> <local_port>:<pod_port>
```

#### **Inspect network policies**
```bash
kubectl get networkpolicy --all-namespaces
kubectl describe networkpolicy <policy_name>
```

---

### **D. Image/Dependency Checks**
#### **Verify image integrity**
```bash
# Check image layers
docker inspect --format='{{json .RootFS.Layers}}' <image>

# Test image locally
docker run --rm -it <image> sh -c "ls -la /app"
```

#### **Debug missing dependencies**
```bash
# List shared libraries
docker exec <container> ldd /path/to/binary | grep "not found"

# Reproduce in a shell
docker run -it <image> sh
```

---

### **E. Volume/Persistent Storage**
#### **Check volume mounts**
```bash
# Docker
docker volume ls
docker run -it --rm -v <volume_name>:/mnt alpine ls -la /mnt

# Kubernetes
kubectl get pvc
kubectl exec <pod> -- ls /path/to/mount
```

#### **Verify storage class**
```bash
kubectl describe storageclass <class_name>
kubectl get sc
```

---

### **F. Init/Entrypoint Debugging**
#### **Test init containers manually**
```bash
# Kubernetes
kubectl run debug-init --image=busybox --rm -it --restart=Never -- \
  sh -c "exec /path/to/init-script"
```

#### **Check entrypoint execution**
```bash
# Mock the entrypoint
docker run -it <image> sh -c "/entrypoint.sh --debug"
```

---

### **G. Orchestration Issues**
#### **Check pod events**
```bash
kubectl get events --sort-by='.lastTimestamp' | head -20
```

#### **Describe pod for detailed logs**
```bash
kubectl describe pod <pod_name> | grep -A 10 "Events:"
```

#### **Scale nodes for resource exhaustion**
```bash
kubectl get nodes -o wide
kubectl scale node <node_name> --replicas=1
```

---

## **3. Related Patterns**
Troubleshooting containers often intersects with other patterns. Refer to:

1. **[Resource Management](https://docs.example.com/patterns/resource-management)**
   - Configure **CPU/memory limits**, **priority classes**, and **resource quotas**.
   - *Tools*: `kubectl top`, `ResourceQuota`.

2. **[Health Checks](https://docs.example.com/patterns/health-checks)**
   - Implement **liveness/readiness probes** to auto-recover failed containers.
   - *Tools*: `livenessProbe`, `readinessProbe`, `kubectl probe`.

3. **[Logging & Monitoring](https://docs.example.com/patterns/logging-monitoring)**
   - Centralize logs with **EFK (Elasticsearch/Fluentd/Kibana)** or **Loki**.
   - *Tools*: `Fluentd`, `Prometheus`, `Grafana`.

4. **[Security Hardening](https://docs.example.com/patterns/security-hardening)**
   - Apply **non-root users**, **read-only filesystems**, and **SELinux/AppArmor**.
   - *Tools*: `SecurityContext`, `podSecurityPolicy`.

5. **[Image Optimization](https://docs.example.com/patterns/image-optimization)**
   - Reduce image size with **multi-stage builds** and **distroless images**.
   - *Tools*: `docker build --squash`, `distroless`.

6. **[Network Isolation](https://docs.example.com/patterns/network-isolation)**
   - Use **NetworkPolicies** to restrict pod-to-pod communication.
   - *Tools*: `NetworkPolicy`, `Calico`.

---

## **4. Best Practices**
1. **Isolate issues**: Use `--debug` flags (`docker run --debug`) to enable verbose logging.
2. **Reproduce locally**: Test fixes in a minimal container before applying to production.
3. **Automate alerts**: Set up **Prometheus alerts** for crashes or resource spikes.
4. **Update regularly**: Keep base images and runtime tools (e.g., Docker/Kubernetes) patched.
5. **Document fixes**: Maintain a **runbook** for recurring issues (e.g., OOM kills).
6. **Leverage eBPF**: Use tools like **Cilium** or **bpftrace** for deep packet inspection without containers.

---

## **5. Further Reading**
- [Docker Troubleshooting Guide](https://docs.docker.com/troubleshoot/)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [CNCF Container Runtime Benchmark](https://github.com/cncf/crbench)
- [Istio Troubleshooting](https://istio.io/latest/docs/tasks/observability/) (for service mesh issues)