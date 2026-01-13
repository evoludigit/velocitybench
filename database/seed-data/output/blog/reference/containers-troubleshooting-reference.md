# **[Pattern] Containers Troubleshooting – Reference Guide**

---

## **Overview**
Containers (e.g., Docker, Kubernetes) introduce new operational challenges while enabling efficient, portable runtime environments. This guide provides structured troubleshooting techniques to diagnose and resolve common container-related issues—from image builds to runtime failures—using **log analysis, resource constraints, network problems, and orchestration misconfigurations**.

Key areas covered:
- **Basic troubleshooting workflow** (logs, resource usage, health checks).
- **Common failure modes** (e.g., crashes, slow starts, connectivity).
- **Tools and commands** for diagnostics (e.g., `kubectl`, `docker inspect`, `crictl`).
- **Advanced debugging** (probes, resource limits, custom logging).

---

## **1. Schema Reference**
A standardized troubleshooting **state machine** guides workflows. Use the following table to categorize issues and resolve them systematically.

| **Category**               | **Subcategory**               | **Key Indicators**                          | **Tools/Commands**                          | **Resolution Steps**                                                                 |
|---------------------------|--------------------------------|--------------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------|
| **Container Lifecycle**   | Crashes/Exits                  | `docker logs`, `exit code`, crash loops   | `docker ps -a`, `kubectl logs --previous`   | Check logs, adjust resource limits, validate entrypoint/env vars.                  |
|                           | Failed Startup                 | `Error: ImagePullBackOff`, `CrashLoopBackOff` | `kubectl describe pod`, `crictl ps`       | Verify image names, manifests, and init containers.                                  |
| **Resource Constraints**  | OOM/CPU Throttling             | `killed`, `throttled`, high CPU usage       | `kubectl top pod`, `docker stats`          | Adjust `requests/limits` in manifests or reduce workload.                           |
|                           | Disk/Storage Issues            | `FailedMount`, `No space left`              | `df -h`, `kubectl describe pod`            | Cleanup volumes, adjust `storage.requests`, or scale storage.                        |
| **Networking**            | Connectivity Failures          | `ConnectionRefused`, `DNS resolution errors` | `kubectl exec -it <pod> -- sh`, `nc`       | Check network policies, `dnsConfig`, and ingress/egress rules.                       |
|                           | Port Conflicts                 | `Ports in use`, `Binding failed`            | `kubectl get endpoints`, `kubectl port-forward` | Validate `ports` in manifests, inspect conflicting services.                        |
| **Orchestration**         | Pod Not Ready                  | `Pending`, `ImagePullError`, `CrashLoopBackOff` | `kubectl get pods -o wide`, `kubectl describe pod` | Verify node readiness, labels, and node affinity rules.                              |
|                           | Deployment Rollback             | `Unhealthy`, `Failed preStop hooks`        | `kubectl rollout status`, `kubectl get events` | Check health checks, lifecycle hooks, and resource constraints.                    |
| **Image Issues**          | Corrupted/Outdated Images      | `ImagePullError`, `UNKNOWN`                | `docker history`, `kubectl logs`           | Pull fresh images, validate image signatures, or debug build contexts.             |
|                           | Layer Download Failures        | `layer too big`, `timeout`                 | `docker pull --debug`, `kubectl describe pod` | Split large images, adjust `imagePullPolicy`, or optimize build layers.             |
| **Security/Runtime**      | Permission Denied              | `Permission denied`, `SELinux denied`       | `docker inspect <container>`, `kubectl debug` | Adjust SELinux contexts, validate security contexts in manifests.                   |
|                           | Privilege Escalation           | `run as root`, `sudo` usage                 | `docker inspect`, `kubectl describe pod`    | Restrict `securityContext.runAsNonRoot`, use `capabilities.drop`.                   |

---

## **2. Query Examples**
### **2.1 Basic Log Analysis**
**Problem:** Container exits with `exit code 137` (SIGKILL).
**Query:**
```bash
# Check logs for the failed container
docker logs <container_id>

# For Kubernetes pods (including previous logs)
kubectl logs <pod_name> --previous

# Filter for errors in logs
kubectl logs <pod_name> | grep -i "error\|failed"
```

**Output:**
```
E0720 12:35:00.000000       1 memcache.go:254] Error: failed to create socket: Permission denied
=> Indicates SELinux or `fsGroup` misconfiguration.
```

---

### **2.2 Resource Monitoring**
**Problem:** Pod is throttled due to CPU limits.
**Query:**
```bash
# Check CPU usage per pod (Kubernetes)
kubectl top pod -A

# Check CPU/memory usage for a Docker container
docker stats <container_name>

# Inspect resource limits in a pod
kubectl describe pod <pod_name> | grep -A 5 "Limits:"
```

**Output:**
```
Limits:
  cpu:     1
  memory:  512Mi
Requests:
  cpu:     500m
  memory:  256Mi
=> CPU throttling detected; adjust `requests` or `limits`.
```

---

### **2.3 Network Diagnostics**
**Problem:** Internal service fails to communicate.
**Query:**
```bash
# Test connectivity from inside a pod
kubectl exec -it <pod_name> -- sh -c "nc -zv <target_service> <port>"

# Check network policies
kubectl get networkpolicies --all-namespaces

# Inspect pod IP and endpoints
kubectl get endpoints <service_name>
kubectl describe pod <pod_name> | grep -i "ip\|status"
```

**Output:**
```
nc: connect to 10.244.1.2 port 80 (tcp) failed: Connection refused
=> Firewall or service misconfiguration; verify `networkPolicy` and `service.selector`.
```

---

### **2.4 Image Validation**
**Problem:** Image fails to pull with `invalid reference`.
**Query:**
```bash
# Check image tags and repositories
docker manifest inspect <image_name>:<tag>

# Verify image layers for corruption
docker history <image_name> | grep -i "error"

# Pull with debug logging
docker pull --debug <image_name>
```

**Output:**
```
Error: image library/nginx:latest not found
=> Tag may be outdated; verify with `docker images` or registry API.
```

---

### **2.5 Lifecycle Hook Debugging**
**Problem:** Pod fails during preStop lifecycle hook.
**Query:**
```bash
# Check pod events for lifecycle errors
kubectl get events --sort-by='.lastTimestamp'

# Debug the hook directly
kubectl debug -it <pod_name> --image=busybox -- sh
wget http://<hook_endpoint>  # Example hook test
```

**Output:**
```
Last Seen  Type     Reason                  Source               Message
5m        Warning  FailedPreStopHook       kubelet              PreStop hook failed: ExitCode: 1
=> Hook script may timeout or fail; adjust `terminationGracePeriodSeconds`.
```

---

## **3. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                                                 |
|----------------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Containers: Health Checks]** | Define liveness/readiness probes to auto-restart or replace unhealthy containers. | When containers crash silently or fail to start.                               |
| **[Containers: Scaling]**        | Horizontal/vertical scaling strategies for containers under load.                | When pod memory/CPU exceeds limits; scaling out/in dynamically.                 |
| **[Containers: Secrets]**        | Securely manage credentials and sensitive data in container manifests.         | When exposing secrets via environment variables or volumes.                     |
| **[Containers: Multi-Stage Builds]** | Optimize Dockerfiles to reduce image size.                                   | When images are too large (>500MB) or pull failures occur due to layer size.   |
| **[Observability: Logging]**     | Centralized logging for containers (e.g., Fluentd, Loki).                     | When logs are fragmented across nodes or clusters.                              |
| **[Containers: Persistent Storage]** | Manage volumes and claims for stateful containers.                           | When pods require persistent data (e.g., databases, caches).                   |

---

## **4. Advanced Diagnostics**
### **4.1 Debug Containers**
**Use Case:** Debug a failing pod by attaching a temporary container.
**Command:**
```bash
kubectl debug -it <pod_name> --image=ghcr.io/alpine/latest --target=<container_name> -- sh
```
**Example:**
```bash
# Enter a debugging shell with tools (e.g., `curl`, `strace`)
apk add curl && curl -v http://localhost:8080
```

---

### **4.2 Core Dumps**
**Use Case:** Capture memory dumps for crashes.
**For Docker:**
```bash
# Enable core dumps in `/proc/sys/kernel/core_pattern`
echo "/var/lib/docker/containers/<container_id>/<container_id>-json.log" | sudo tee /proc/sys/kernel/core_pattern

# Trigger a crash (e.g., `kill -SEGV <pid>`)
```
**For Kubernetes:**
```yaml
# Add to pod spec
securityContext:
  allowPrivilegeEscalation: true
  capabilities:
    add: ["SYS_PTRACE"]
  privileged: true
```

---

### **4.3 Distributed Tracing**
**Use Case:** Trace requests across microservices in a cluster.
**Tools:**
- **Jaeger**: Instrument containers with Jaeger clients.
- **OpenTelemetry**: Collect traces/metrics from pods.
**Example (Kubernetes Sidecar):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
      - name: jaeger-agent
        image: jaegertracing/jaeger-agent
        ports:
        - containerPort: 6831
          protocol: UDP
        - containerPort: 6832
          protocol: UDP
```

---

## **5. Best Practices**
1. **Standardize Logging**:
   - Use structured logging (e.g., JSON) for centralized analysis.
   - Example: `logger -s -t <component> -- "Error: %(message)s"` (Go).

2. **Resource Guidelines**:
   - Set `requests` ≤ `limits` to avoid throttling.
   - Monitor with `kubectl top` or Prometheus.

3. **Network Isolation**:
   - Use `NetworkPolicy` to restrict pod communication.
   - Avoid `hostNetwork: true` unless necessary.

4. **Image Optimization**:
   - Multi-stage builds to reduce layer size.
   - Scan images for vulnerabilities (e.g., `trivy`, `clair`).

5. **Automated Rollbacks**:
   - Enable `kubectl rollout undo` for failed deployments.
   - Use `readinessProbe` + `livenessProbe` to auto-recover.

6. **Backup Critical Data**:
   - Use `PersistentVolumeClaims` with snapshots (e.g., Velero).
   - Example:
     ```bash
     velero backup create daily-backup --include-namespaces=default
     ```

---

## **6. Troubleshooting Checklist**
| **Step**               | **Action Items**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **1. Verify Logs**     | Check `docker logs` or `kubectl logs` for error patterns.                      |
| **2. Check Status**    | Run `kubectl get pods` or `docker ps` to identify `CrashLoopBackOff` or `Error`. |
| **3. Inspect Resources** | Use `kubectl top pod` or `docker stats` to detect throttling or OOM kills.      |
| **4. Network Diagnostics** | Test connectivity with `kubectl exec` + `nc` or `curl`.                     |
| **5. Image Validation** | Pull images manually (`docker pull`) or inspect layers (`docker history`).      |
| **6. Security Context** | Review `securityContext` for misconfigured permissions/SELinux.                |
| **7. Lifecycle Hooks**  | Test `preStop`/`postStart` hooks with `kubectl debug`.                          |
| **8. Debug Sidecar**   | Attach a debug container to inspect dependencies (e.g., databases).           |
| **9. Rollback**        | Undo changes with `kubectl rollout undo` if recovery is needed.                 |
| **10. Escalate**       | Open a ticket with logs, manifests, and `kubectl describe pod` output.         |

---

## **7. Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|--------------------------------------------------------------------------------|
| **CrashLoopBackOff**   | Kubernetes restarts a pod repeatedly after it crashes.                        |
| **OOMKilled**          | Container killed due to out-of-memory (OOM) conditions.                        |
| **Readiness Probe**    | Checks if a container is ready to serve traffic (e.g., HTTP 200).              |
| **Liveness Probe**     | Determines if a container is running (e.g., `Exec`, `HTTPGet`).                |
| **Init Container**     | Runs before the main container to perform setup tasks (e.g., DB migrations).   |
| **Pod Disruption Budget** | Ensures a minimum number of pods remain available during disruptions.        |
| **Distroless Images**  | Minimal images with only runtime dependencies (e.g., `gcr.io/distroless/base`).|

---
**End of Guide**
*For further reading, refer to the [CNCF Container Runtime Guide](https://github.com/cncf/cncf-branding/tree/master/logos-and-trademarks)*