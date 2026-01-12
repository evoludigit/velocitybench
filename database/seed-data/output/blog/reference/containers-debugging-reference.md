# **[Pattern] Containers Debugging: Reference Guide**

---

## **Overview**
Debugging containerized applications requires a structured approach to isolate issues across **runtime, orchestration, networking, storage, and application layers**. This reference guide details the debugging workflow, tools, and best practices for diagnosing failures in containers. Coverage includes:
- **Log inspection** (container, host, and streaming logs).
- **Container process inspection** (PIDs, dependencies, and resource usage).
- **Orchestration debugging** (Kubernetes/YAML, health checks, pod crashes).
- **Networking issues** (connectivity, DNS, port conflicts).
- **Storage and volume debugging** (bind mounts, persistent volumes).
- **Performance bottlenecks** (CPU, memory, disk I/O).

Use this guide to systematically troubleshoot container health, performance, and misconfigurations.

---

## **Schema Reference**

| **Category**               | **Component**               | **Debugging Focus**                                                                 | **Common Tools/Commands**                          | **Key Logs/Metrics**                     |
|----------------------------|-----------------------------|--------------------------------------------------------------------------------------|----------------------------------------------------|-------------------------------------------|
| **Container Runtime**      | Container Processes         | Running processes, PIDs, dependencies, and health.                                   | `docker ps`, `docker exec -it`, `ps`, `top`, `htop` | `/var/log/containers/`, `docker logs`    |
|                            | Container Logs              | Streamed logs, container startup errors, and runtime events.                         | `docker logs`, `kubectl logs`, `journalctl`        | `--follow`, `--tail=100`                 |
|                            | Resource Usage              | CPU, memory, disk, and network bottlenecks.                                          | `docker stats`, `kubectl top`, `dcgm-cli`         | `kubectl describe pod`, `cAdvisor`       |
| **Orchestration Layer**    | Pods/Containers             | Pod lifecycle, restarts, and crashes.                                                | `kubectl describe pod`, `kubectl get events`      | `events` table, `Status` field          |
|                            | Deployments/Replicasets     | Rolling updates, scaling issues, and rollback failures.                              | `kubectl rollout status`, `kubectl rollout undo`   | `History` section, `Conditions`          |
|                            | Services & Ingress          | DNS resolution, routing, and service mesh issues.                                    | `kubectl get svc`, `kubectl get ingress`          | `Endpoint` addresses, `TargetPort`       |
| **Networking**             | Network Policies            | Firewall rules, port conflicts, and inter-pod communication.                         | `kubectl get networkpolicy`, `kubectl describe`   | `Ingress/Egress` rules                  |
|                            | Connectivity Issues         | Latency, packet loss, and firewall drops.                                             | `curl`, `telnet`, `nc`, `kubectl exec -it -- bash` | `ping`, `traceroute` logs               |
|                            | DNS Resolution              | Failed service discovery or misconfigured DNS.                                        | `dig`, `nslookup`, `kubectl get endpoints`        | `DNSConfig` in Pod spec                  |
| **Storage & Volumes**      | Persistent Volumes (PVs)    | Volume binding errors, storage class issues.                                         | `kubectl get pv`, `kubectl describe pv`             | `Phase`, `Status`                        |
|                            | Bind Mounts & ConfigMaps    | Permission errors, missing files, or corrupt mounts.                                  | `kubectl exec -it -- ls`, `kubectl get cm`        | `Mounts` section in Pod spec             |
| **Security**               | Seccomp & Capabilities      | Privilege escalation, container breakout attempts.                                    | `docker inspect`, `kubectl describe pod`          | `SecurityContext` fields                |
|                            | Secrets Management          | Exposed secrets, improper key rotation.                                              | `kubectl get secrets`, `envsubst`                  | `--from-literal`, `kubectl create secret` |

---

## **Query Examples**

### **1. Container Logs & Events**
**Scenario:** Debugging a failing container in Kubernetes.
```bash
# View container logs (last 200 lines)
kubectl logs <pod-name> --previous --tail=200

# Stream logs in real-time
kubectl logs <pod-name> -f

# Get pod events (creation, restarts, crashes)
kubectl get events --sort-by='.metadata.creationTimestamp'

# Filter for `Warning` or `Error` events
kubectl get events --field-selector reason=Error
```

**Key Flags:**
- `--previous`: View logs of a previous incarnation of the container.
- `--tail=<N>`: Show the last N lines.
- `-f`: Follow logs in real-time.

---

### **2. Container Process Inspection**
**Scenario:** Diagnosing a hanging process inside a container.
```bash
# Execute a shell in a running container
kubectl exec -it <pod-name> -- /bin/bash

# List running processes (PIDs, CPU, memory usage)
ps aux

# Check for zombie processes
ps -eo pid,ppid,cmd | grep 'Z'

# Monitor CPU/memory usage
top -H -p <PID>
```

**Key Commands:**
- `ps aux`: List all processes with UID, PID, and command.
- `top -H`: Show per-process resource usage.
- `strace`: Trace system calls (useful for blocked processes).
  ```bash
  strace -p <PID> -o /tmp/trace.log
  ```

---

### **3. Orchestration Debugging**
**Scenario:** Debugging a Kubernetes Deployment rollout failure.
```bash
# Check deployment status
kubectl rollout status deployment/<deployment-name>

# View deployment history (revisions, rollback to previous)
kubectl rollout history deployment/<deployment-name>

# Describe a pod to see why it crashed
kubectl describe pod <pod-name>

# Check pod events for errors
kubectl describe pod <pod-name> | grep "Error\|Warning"
```

**Key Fields in `kubectl describe pod`:**
- **`Status`**: `Running`, `CrashLoopBackOff`, `Pending`.
- **`Restart Count`**: Indicates frequent crashes.
- **`Events`**: Timestamps and reasons for failures.

---

### **4. Networking Debugging**
**Scenario:** diagnosing a service connectivity issue.
```bash
# Test connectivity to another pod
kubectl exec -it <pod-name> -- curl -v <service-name>.<namespace>.svc.cluster.local:80

# Check pod IP and service endpoints
kubectl get endpoints <service-name>

# Test DNS resolution inside a pod
kubectl exec -it <pod-name> -- nslookup <service-name>

# Check network policies (ingress/egress rules)
kubectl get networkpolicy
kubectl describe networkpolicy <policy-name>
```

**Key Tools:**
- `curl -v`: Verbose HTTP requests (shows headers, redirects).
- `nc -zv <host> <port>`: Test TCP connectivity.
- `iptables -L -n`: Check firewall rules on the host.

---

### **5. Storage & Volume Debugging**
**Scenario:** Debugging a bind mount permission error.
```bash
# Check volume mount status inside a pod
kubectl exec -it <pod-name> -- ls -la /path/to/mount

# Verify volume claims in Kubernetes
kubectl get pvc
kubectl describe pvc <pvc-name>

# Check host filesystem permissions (if using hostPath)
kubectl describe pod <pod-name> | grep -A 5 "Volumes:"
```

**Key Commands:**
- `ls -la`: Verify file permissions in the mounted directory.
- `df -h`: Check disk space usage.
- `mount | grep <volume-name>`: Verify volume is mounted.

---

### **6. Performance Bottlenecks**
**Scenario:** Diagnosing high CPU usage in a container.
```bash
# Check resource usage for a pod
kubectl top pod

# Check container resource limits
kubectl describe pod <pod-name> | grep -A 10 "Resource Limits"

# Monitor CPU/memory over time (via cAdvisor)
kubectl top node --containers=true --all-namespaces

# Use `kubectl debug` to inspect a failed pod
kubectl debug -it <pod-name> --image=busybox --target=<container-name> -- sh
```

**Key Metrics:**
- **CPU Throttling**: Check `kubectl describe pod | grep "CPU"`.
- **Memory OOMKilled**: Look for `Killed` status in `kubectl top pod`.
- **Disk I/O**: Use `iotop` or `dstat` inside the container.

---

## **Related Patterns**
1. **[Container Health Checks]** – Designing liveness/readiness probes for resilient apps.
2. **[Logging & Monitoring for Containers]** – Centralized log aggregation (ELK, Loki) and metrics (Prometheus, Grafana).
3. **[Image Optimization]** – Reducing image size and layers for faster debugging.
4. **[Network Policies]** – Securing pod-to-pod communication.
5. **[Rollback Strategies]** – Reverting deployments safely after failures.
6. **[Distributed Tracing]** – Using Jaeger or OpenTelemetry to trace requests across services.

---

## **Best Practices**
1. **Start Small**: Isolate the issue to a single pod/container before escalating.
2. **Use `kubectl debug`**: Temporarily attach a shell to a failing container.
3. **Enable Debug Logging**: Adjust container logs to include debug-level details.
4. **Check Host Logs**: `/var/log/docker/containers/` or `journalctl -u kubelet`.
5. **Reproduce Locally**: Test changes in a minimal Docker setup before applying to production.
6. **Automate Debugging**: Use tools like **OpenTelemetry** or **Fluentd** for structured logging.

---
**Note:** Commands may vary slightly based on Kubernetes version or Docker runtime (e.g., containerd). Always verify compatibility with your environment.