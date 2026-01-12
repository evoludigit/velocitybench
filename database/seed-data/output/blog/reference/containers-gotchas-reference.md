---
# **[Pattern] Containers Gotchas: Reference Guide**

---

## **Overview**
Containers (e.g., Docker) improve portability and efficiency by packaging applications and dependencies into isolated environments. However, they introduce subtle operational and architectural challenges that can cause failures if unanticipated. This guide documents common "gotchas"—unexpected pitfalls—related to **containerization, networking, storage, security, and orchestration** (e.g., Kubernetes). Understanding these issues helps troubleshoot runtime problems and design resilient containerized systems.

---

## **Schema Reference**
Below is a structured taxonomy of **Containers Gotchas** categorized by critical area.

| **Category**          | **Subcategory**               | **Gotcha**                                                                 | **Root Cause**                                                                 | **Impact**                                                                 | **Mitigation**                                                                 |
|------------------------|-------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Runtime**            | **Dependency Hell**            | Missing base images in `Dockerfile`.                                         | Incorrect `FROM` instruction or private repo access issues.                    | Build failures; app crashes at runtime.                                       | Use official images or pinned versions (`FROM nginx:1.25`). Verify `docker pull`. |
|                         | **Layer Caching**              | Poor `Dockerfile` layer ordering causes inconsistent builds.                | Large dependencies placed before smaller ones (cache invalidation).             | Slow builds; unexpected behavior between environments.                      | Group related commands (e.g., `RUN apt-get update && apt-get install ...`). |
|                         | **User/UID Mismatches**        | Containers run as `root`; files created outside user namespace.             | Default `USER` in `Dockerfile` or host filesystem permissions.                 | Permission errors when mounting host directories.                           | Set explicit `USER` (e.g., `USER 1000`) or use `--user` flag.                |
| **Networking**         | **Port Conflicts**             | Host ports already in use by other containers/services.                     | Overlapping port mappings (`-p 8080:80`).                                      | Container fails to start or exposes wrong port.                              | Check `netstat`/`ss` on host; use unique ports or dynamic allocation.        |
|                         | **DNS Resolution**             | Containers resolve host DNS incorrectly (e.g., `localhost` points to container IP). | Misconfigured `/etc/resolv.conf` or custom DNS in `docker run`.               | Network API calls fail (e.g., to external services).                         | Use `--dns 8.8.8.8` or ensure `extra_hosts` maps `localhost` to host IP.    |
|                         | **Bridge Network Overhead**    | Heavy traffic between containers degrades performance.                      | Default bridge network (`docker0`) lacks QoS guarantees.                       | Latency spikes; connection timeouts.                                         | Use Macvlan/VLAN or service meshes (e.g., Istio).                            |
| **Storage**            | **Volume Permissions**         | Host directories mounted into containers lack proper permissions.           | Default `root` UID/GID in containers vs. host users.                           | `Permission denied` errors when writing to volumes.                         | Use `volumes` with `:uid:gid` or bind mounts.                                |
|                         | **Persistent Data Loss**       | Bind mounts or unnamed volumes not persisted across container restarts.      | Missing `-v` flag or temporary storage.                                        | Data corruption or loss when container restarts.                            | Use named volumes (`-v myvol:/path`) or host-based storage.                   |
|                         | **Device Access**             | GPU/USB devices not shared correctly.                                         | Incorrect `--device` flags or missing kernel modules.                        | GPU/USB failures in containerized apps.                                      | Use `--device=/dev/sgX` (for GPUs) or `--userns=host`.                      |
| **Security**           | **Privileged Mode**            | Containers run with `--privileged` expose host kernel.                       | Overuse of privileged mode for debug/testing.                                  | Security vulnerabilities (e.g., kernel exploits).                           | Minimize privileges; use `--cap-drop`/`--cap-add` selectively.                  |
|                         | **Secrets Management**         | Hardcoded credentials or secrets in images/dockerfiles.                      | Secrets committed to Git or embedded in `Dockerfile`.                         | Unauthorized access or compliance violations.                                | Use Docker Secrets, Kubernetes Secrets, or vaults (e.g., HashiCorp Vault).  |
|                         | **Image Vulnerabilities**      | Outdated base images with known CVEs.                                         | Delayed patching or lack of image scanning.                                    | Exploitable containers in production.                                        | Scan images (`docker scan`) and update regularly.                            |
| **Orchestration**      | **Resource Limits**            | Pods/containers exceed CPU/memory limits.                                     | Misconfigured `resources.requests/limits` in Kubernetes.                      | Node OOM kills or throttled performance.                                     | Set realistic limits and monitor with `kubectl top`.                         |
|                         | **Pod Restart Policies**       | CrashLoopBackOff due to misconfigured restart policies.                     | Incorrect `restartPolicy` (e.g., `Always` without health checks).              | Unstable deployments with cascading failures.                               | Use `livenessProbe` + `readinessProbe`; set `restartPolicy: OnFailure`.      |
|                         | **Network Policies**           | Overly permissive or conflicting network policies.                           | Default-allow policies or misconfigured `NetworkPolicy` rules.               | Unauthorized pod communication; security breaches.                          | Enforce least-privilege policies; test with `kubectl describe networkpolicy`. |
| **Debugging**          | **Logging Isolation**          | Container logs mixed with host logs or other containers.                    | Default logging drives (`/var/lib/docker/containers/`).                       | Difficult troubleshooting.                                                  | Use structured logging (e.g., JSON) or centralized tools (Loki, Fluentd).    |
|                         | **Debugging Tools**            | Missing `docker exec` access or broken tools (e.g., `bash` not installed). | Minimal base images omit debug utilities.                                     | Limited diagnostics.                                                          | Include `bash`, `curl`, or `ps` in `Dockerfile`.                            |
| **Multi-Host**          | **Cluster Networking**         | Pods in different nodes cannot communicate without proper CNI.               | Misconfigured Calico/Flannel/Cilium.                                           | Split-brain scenarios; service unavailability.                               | Verify CNI plugin; test cross-node connectivity.                            |
|                         | **Service Discovery**          | DNS-based service discovery fails across clusters.                           | Misconfigured `kube-dns` or `CoreDNS`.                                         | Services unable to resolve each other.                                       | Use headless services or external DNS (e.g., Cloudflare).                     |

---

## **Query Examples**
### **1. Debugging a Build Failure Due to Layer Caching**
**Symptom**: Changing a small file (e.g., `config.json`) doesn’t trigger a rebuild.
**Solution**:
```bash
# Force rebuild by removing cache:
docker builder prune
# OR rebuild with --no-cache:
docker build --no-cache -t myapp:latest .
```

**Key Takeaway**: Group `RUN` commands to minimize cache bloat.

---

### **2. Resolving "Permission Denied" on Mounted Host Directories**
**Symptom**: Container writes to `/app/data` fail with `EACCES`.
**Solution**:
```bash
# Option 1: Use volumes with UID/GID
docker run -v /host/path:/app/data:rw,uid=1000,gid=1000 myimage

# Option 2: Adjust host directory permissions
chown -R 1000:1000 /host/path
```

**Key Takeaway**: Align container UID/GID with host paths.

---

### **3. Investigating NetworkPolicy Blocking Traffic**
**Symptom**: Pod `app-pod` cannot reach `db-pod`.
**Solution**:
```yaml
# Check existing policies:
kubectl get networkpolicy -A

# Test connectivity (from app-pod):
kubectl exec -it app-pod -- curl db-pod:5432
# Debug policy:
kubectl describe networkpolicy default/my-policy
```

**Key Takeaway**: Use `kubectl exec` and `--dry-run` to validate policies.

---

### **4. Handling CrashLoopBackOff in Kubernetes**
**Symptom**: Pod restarts indefinitely with `Error: failed to start container`.
**Solution**:
```bash
# Inspect logs:
kubectl logs my-pod --previous

# Check events:
kubectl describe pod my-pod

# Common fixes:
- Update `livenessProbe`/`readinessProbe`.
- Verify resource limits (`kubectl top pod`).
- Check container logs for app errors.
```

**Key Takeaway**: Combine `describe` and `logs --previous` for context.

---

### **5. Scanning Base Images for Vulnerabilities**
**Symptom**: Unknown CVEs in base images (e.g., `ubuntu:22.04`).
**Solution**:
```bash
# Install Docker Scan Plugin:
docker plugin install --grant-all-permissions ghcr.io/anapsix/alertmanager-docker-scan:latest

# Scan an image:
docker scan myapp:latest
```
**Output Example**:
```
[banner: bash: /usr/bin/docker-scan: No such file or directory]
# Use explicit CLI:
docker scan --format table myapp:latest
```

**Key Takeaway**: Regularly scan images during CI/CD.

---

## **Related Patterns**
To mitigate Containers Gotchas, leverage these complementary patterns:

1. **Observability for Containers**
   - **Pattern**: *Logging, Metrics, and Tracing*
   - **Use Case**: Centralize logs (ELK, Loki) and metrics (Prometheus/Grafana) to debug network/storage issues.
   - **Gotcha Mitigation**: Structured logging (`json-logfmt`) + distributed tracing (Jaeger).

2. **Secure Container Builds**
   - **Pattern**: *Immutable Infrastructure*
   - **Use Case**: Use multi-stage `Dockerfile`s to reduce image size and attack surface.
   - **Gotcha Mitigation**: Avoid `latest` tags; scan images post-build.

3. **Service Mesh for Networking**
   - **Pattern**: *Service Mesh (Istio/Linkerd)*
   - **Use Case**: Replace ad-hoc `NetworkPolicy` with declarative traffic management.
   - **Gotcha Mitigation**: Centralized mTLS and observability for cross-pod communication.

4. **Portable Storage with CSI**
   - **Pattern**: *Container Storage Interface (CSI)*
   - **Use Case**: Standardize storage drivers (e.g., EBS, Ceph) across Kubernetes clusters.
   - **Gotcha Mitigation**: Avoid bind mounts for production; use CSI volumes.

5. **Canary Deployments**
   - **Pattern**: *Progressive Rollouts*
   - **Use Case**: Gradually roll out container updates to detect runtime issues early.
   - **Gotcha Mitigation**: Use `kubectl rollout` with `livenessProbe` to identify failing containers.

6. **Image Signing**
   - **Pattern**: *Notary or Kosko*
   - **Use Case**: Verify container image authenticity to prevent supply-chain attacks.
   - **Gotcha Mitigation**: Sign images before deployment; reject unsigned pulls.

7. **Namespace Isolation**
   - **Pattern**: *User Namespaces*
   - **Use Case**: Isolate containers from host namespaces (e.g., `mknod`, mounts) for security.
   - **Gotcha Mitigation**: Use `--userns=host` judiciously; prefer `--read-only`.

---

## **Troubleshooting Checklist**
Before seeking advanced support, verify these common issues:

| **Gotcha Area**       | **Quick Checks**                                                                 |
|-----------------------|---------------------------------------------------------------------------------|
| **Build Failures**    | Run `docker history <image>` to identify broken layers.                         |
| **Networking**        | Test `ping` between containers `docker exec -it container ping <target>`.     |
| **Storage**           | Check volume permissions: `stat /path/in/container`.                           |
| **Security**          | Audit `docker inspect <container>` for `--privileged` or `--cap-add`.          |
| **Orchestration**     | Verify `kubectl get pods -o wide` for node assignment issues.                 |
| **Debugging**         | Use `docker exec -it <container> bash` to inspect runtime state.               |

---
## **Further Reading**
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Kubernetes Networking Gotchas](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- [CIS Benchmark for Docker](https://www.cisecurity.org/benchmarks/)
- [Container Security Tooling](https://github.com/aquasecurity/trivy) (for image scanning).