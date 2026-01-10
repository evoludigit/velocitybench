# **Debugging "The Evolution of Containerization: From chroot to Docker to OCI" – A Troubleshooting Guide**

Containers have evolved from simple Unix isolation techniques (like `chroot`) to modern OCI-compliant runtimes (e.g., Docker, containerd, CRI-O). While this evolution has improved security, portability, and efficiency, each stage introduces unique challenges. This guide provides a structured approach to debugging issues across **chroot, Docker, and OCI runtime environments**.

---

## **1. Symptom Checklist**
Before diving into fixes, verify if your issue falls under one of these categories:

| **Symptom** | **Possible Root Cause** |
|-------------|------------------------|
| Containers fail to start with permission errors (`EPERM`) | Incorrect namespace isolation, seccomp/firesetup misconfig |
| High CPU/memory usage in containers | Misconfigured resource limits, missing cgroups |
| Network connectivity issues (`Connection refused`, `NetworkUnavailable`) | Overly restrictive network policies, misconfigured CNI plugins |
| Container exits immediately with `SIGKILL` | OOM killer triggered, insufficient resources |
| Missing dependencies inside containers | Incorrect layer caching, Dockerfile layer mismatches |
| OCI-runtime crashes (`failed to start container`) | Invalid config, unsupported runtime hooks |
| `chroot` fails with `No such file or directory` | Broken symlinks, incorrect rootfs path |
| Docker daemon crashes (`exit status 1`) | Corrupted storage driver, misconfigured `daemon.json` |
| Slow container startup (`ImagePullError`, `Timeout`) | Registry auth issues, slow pull policies |
| Containers cannot access host devices (`/dev` access denied) | Missing `--device` flag, incorrect `securityContext` |
| Logging unavailable or incomplete | Misconfigured logging driver (e.g., JSON-file, Fluentd) |

---
## **2. Common Issues & Fixes**

### **A. chroot & Early Container Isolation Issues**
#### **Issue: `chroot` fails with "No such file or directory"**
- **Symptom:** Running `chroot /new/root /bin/bash` results in `chroot: failed: No such file or directory`.
- **Root Cause:** The new root directory is empty, or symlinks in `/etc` are broken.
- **Fix:**
  ```bash
  # Verify the rootfs structure
  ls -la /new/root/
  # If missing, recreate essential files:
  mkdir -p /new/root/{etc,var,dev,proc,sys,home}
  # Restore symlinks (e.g., /etc/resolv.conf)
  ln -s /etc/resolv.conf /new/root/etc/resolv.conf
  ```
- **Debugging Tip:** Use `strace chroot` to trace system calls and identify missing entries.

#### **Issue: Shared libraries missing in `chroot`**
- **Symptom:** `ldd /bin/bash` inside `chroot` shows missing libraries (e.g., `libc.so.6`).
- **Fix:** Copy the host’s shared libraries into the rootfs:
  ```bash
  sudo cp -r /lib /new/root/lib
  sudo cp -r /lib64 /new/root/lib64
  ```
- **OCI Modernization:** Avoid manual `chroot`—use **distroless images** or **minimal base images** instead.

---

### **B. Docker-Specific Debugging**
#### **Issue: `"cannot connect to Docker daemon"`**
- **Symptom:** `docker: Cannot connect to the Docker daemon` on `docker ps`.
- **Root Cause:** Docker socket permissions or service misconfiguration.
- **Fix:**
  ```bash
  # Check if Docker socket exists
  ls -la /var/run/docker.sock
  # Grant permissions to your user
  sudo chmod 666 /var/run/docker.sock
  # Restart Docker daemon (if needed)
  sudo systemctl restart docker
  ```
- **OCI Alternative:** Use `containerd` if Docker is unreliable (e.g., in Kubernetes).

#### **Issue: `OOMKilled` containers**
- **Symptom:** Containers exit with `OOMKilled` after a few minutes.
- **Root Cause:** Insufficient memory limits or high memory usage.
- **Fix:**
  ```yaml
  # In docker-compose.yml or Dockerfile
  memory: 1g       # Set explicit memory limit
  mem_limit: 512m  # Alternative syntax
  ```
- **Debugging:**
  ```bash
  # Check container memory usage
  docker stats --no-stream <container_id>
  # Check systemd OOM logs
  journalctl -u docker --no-pager | grep -i "oom"
  ```

#### **Issue: Docker build fails with `"docker: error while loading shared libraries"`**
- **Symptom:** `docker build` crashes with missing `libcontainerd` or `runc` dependencies.
- **Fix:** Install runtime dependencies:
  ```bash
  sudo apt-get install libcontainerd0 libcgroup1
  ```
- **OCI Best Practice:** Use `containerd` (Docker’s underlying runtime) for better performance.

---

### **C. OCI Runtime & containerd Issues**
#### **Issue: `failed to start container: OCI runtime create failed`**
- **Symptom:** `docker run` fails with OCI runtime errors (e.g., invalid spec).
- **Root Cause:** Corrupted image layers or misconfigured `config.json`.
- **Fix:**
  ```bash
  # Inspect the container spec
  docker inspect --format='{{.Config}}' <image>
  # Rebuild the image with proper layers
  docker build --no-cache -t <image> .
  ```
- **Debugging Tools:**
  ```bash
  # Check containerd logs
  journalctl -u containerd --no-pager
  # Test OCI spec manually
  crictl inspectp <container_id>
  ```

#### **Issue: `containerd` fails to pull images**
- **Symptom:** `failed to pull image: rpc error: code = Unknown desc = pull image failed`.
- **Root Cause:** Registry auth issues or misconfigured CRI.
- **Fix:**
  ```bash
  # Check registry config
  sudo cat /etc/containerd/config.toml | grep -A5 "plugins"
  # Ensure auth token is valid
  crictl pull <image>
  ```
- **OCI Best Practice:** Use `containerd` with **remote OCI registry support** (e.g., Docker Hub, GHCR).

#### **Issue: `runc` fails with `"invalid path: invalid character"`**
- **Symptom:** `runc` crashes when starting containers.
- **Root Cause:** Path escaping issues in `config.json`.
- **Fix:** Use proper escaping in the OCI spec:
  ```json
  {
    "Mounts": [
      {
        "Type": "bind",
        "Source": "/host/path",
        "Destination": "/container/path",
        "Options": ["rbind", "ro"]
      }
    ]
  }
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|--------------|---------------------|
| `strace` | Trace system calls in `chroot`/`docker` | `strace -f chroot <path>` |
| `docker inspect` | Debug container config | `docker inspect <container>` |
| `crictl` | Inspect `containerd` runtime | `crictl ps -a` |
| `runc debug` | Debug OCI runtime | `runc debug <container_id>` |
| `journalctl` | Check `containerd`/`docker` logs | `journalctl -u docker` |
| `nsenter` | Enter container namespaces | `nsenter -t <pid> -n ping 8.8.8.8` |
| `lsof` | Check file descriptor leaks | `lsof -p <container_pid>` |
| `perf` | Profile high CPU usage | `perf top -p <container_pid>` |
| `docker events` | Monitor Docker events | `docker events --filter 'event=die'` |

---

## **4. Prevention Strategies**
### **A. For chroot-Based Containers**
- **Use `pivot_root` instead of `chroot`** for better performance.
- **Validate rootfs before `chroot`:**
  ```bash
  # Test chroot without entering it
  chroot --test /new/root
  ```
- **Prevent broken symlinks** by using `unionfs` or `overlayfs` (modern alternative).

### **B. For Docker Containers**
- **Use `.dockerignore`** to avoid bloated layers:
  ```dockerignore
  node_modules/
  *.log
  ```
- **Set explicit resource limits** in `docker-compose.yml`:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
  ```
- **Clean up unused images** regularly:
  ```bash
  docker system prune -a --volumes
  ```

### **C. For OCI Runtime (containerd/runc)**
- **Use `containerd` directly** instead of Docker for Kubernetes (CRI support).
- **Optimize image layers** with multi-stage builds:
  ```dockerfile
  FROM alpine AS builder
  RUN apk add --no-cache build-deps && ...
  FROM scratch
  COPY --from=builder /app /app
  ```
- **Enable content addressability** in `containerd` config:
  ```toml
  [plugins."io.containerd.grpc.v1.cri"]
    disable_port_forwarding = false
    disable_tcp_service = false
  ```
- **Monitor OCI compliance** with:
  ```bash
  go run github.com/opencontainers/runc@latest spec-tools/validate
  ```

---

## **5. Advanced Debugging Workflow**
1. **Isolate the Problem:**
   - Is it **host-level** (e.g., kernel namespaces, cgroups) or **container-level** (e.g., misconfigured runtime)?
   - Use `docker top <container>` to check if the process is running but isolated.

2. **Check Logs:**
   ```bash
   # Docker logs
   docker logs --tail 100 <container>
   # containerd logs
   journalctl -u containerd --since "1h ago"
   ```

3. **Test with Minimal Config:**
   - Recreate the issue in a **scratch image** to rule out dependency issues.
   - Example:
     ```dockerfile
     FROM scratch
     COPY entrypoint.sh /
     CMD ["/entrypoint.sh"]
     ```

4. **Compare Working vs. Broken Configs:**
   - Use `docker diff` to see file changes:
     ```bash
     docker diff <container>
     ```
   - Compare `config.json` between working and broken containers.

5. **Kernel-Level Debugging:**
   - Check for **missing kernel features** (e.g., `overlayfs`, `cgroupv2`):
     ```bash
     grep CONFIG_OVERLAY_FS /boot/config-$(uname -r)
     ```

---

## **6. Migration Path: chroot → Docker → OCI**
| **Step** | **Tool** | **Debugging Focus** |
|----------|----------|---------------------|
| 1. **Replace `chroot` with `docker run --rm -v`** | Docker | Verify volume mounts, `--security-opt` |
| 2. **Switch from Docker to `containerd`** | containerd | Check CRI config, `crictl pull` |
| 3. **Use OCI-compliant runtimes** | runc, Firecracker | Validate `config.json`, hooks |
| 4. **Adopt Kubernetes CRI (if applicable)** | kubelet | Check `cri-tools` debug logs |

---

## **Final Checklist Before Escalation**
✅ **Has the issue reproduced in a minimal test case?**
✅ **Are logs and `strace` outputs captured?**
✅ **Is the problem kernel-level (namespaces, cgroups) or app-level?**
✅ **Have OCI runtime configs been validated (`runc spec --debug`)?**
✅ **Is the issue specific to Docker, containerd, or the host OS?**

---
This guide ensures quick resolution by **focusing on observable symptoms, tool-based diagnostics, and OCI-compliant optimizations**. For further issues, refer to:
- [Docker Debugging Guide](https://docs.docker.com/troubleshoot/)
- [containerd Debugging Docs](https://containerd.io/docs/main/debug/)
- [OCI Runtime Spec](https://github.com/opencontainers/runtime-spec)