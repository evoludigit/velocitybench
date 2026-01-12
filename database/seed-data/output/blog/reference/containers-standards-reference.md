# **[Pattern] Containers Standards Reference Guide**

---

## **Overview**
The **Containers Standards** pattern defines a standardized approach to containerization, ensuring portability, interoperability, and consistency across cloud platforms, bare-metal environments, and hybrid architectures. This pattern aligns with **OCI (Open Container Initiative) standards**, including:
- **OCI Image Specification** (for container image formats)
- **OCI Runtime Specification** (for container execution)
- **CRI (Container Runtime Interface)** and **Kubernetes CRI** for container orchestration

By adhering to these standards, organizations avoid vendor lock-in, simplify deployment pipelines, and leverage tools like Docker, containerd, CRI-O, and Kubernetes effectively. This guide covers core concepts, schema definitions, implementation best practices, and integration examples.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Key Standards**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Container Image**    | Immutable, portable package containing an application and its dependencies.                     | OCI Image Spec (v1.1), Docker Image Formats                                       |
| **Container Runtime**  | Software that executes containerized applications (e.g., containerd, CRI-O).                     | OCI Runtime Spec, CRI (k8s-compliant runtimes)                                   |
| **Distributed Image Registry** | Central repository storing and distributing container images. | OCI Distribution Spec, Docker Registry API, Harbor/Artifactory                            |
| **Runtime Hooks**      | Pre/post-execution commands (e.g., health checks, init scripts).                                | OCI Runtime Spec (Lifecycle Hooks)                                               |
| **Multi-Stage Builds** | Optimized build process combining multiple images into a single final image.                     | BuildKit, Dockerfile Multi-Stage Instructions                                     |
| **Security Context**   | Configurations for user/root privileges, capabilities, and security labels.                      | OCI Security Context, Kubernetes Security Contexts                                |
| **Artifact Metadata**  | Additional metadata (e.g., licensing, dependencies) attached to images.                          | OCI Image Index, Docker Manifest V2 Signatures                                   |

---

## **Schema Reference**

### **1. OCI Image Schema (Manifest v2)**
| **Field**               | **Type**          | **Description**                                                                                     | **Example Value**                                                                 |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `schemaVersion`         | `string`          | OCI spec version (e.g., `2.0`).                                                                       | `"2.0"`                                                                           |
| `mediaType`             | `string`          | MIME type of the manifest (e.g., `application/vnd.docker.distribution.manifest.v2+json`).         | `"application/vnd.oci.image.manifest.v1+json"`                                      |
| `config`                | `JSON`            | Image configuration (entrypoint, cmd, environment variables).                                    | `{"Cmd":["/app/server"], "Env":["PATH=/usr/local/sbin:/usr/local/bin"]}`           |
| `layers`                | `array[Layer]`    | List of layers with digests and media types.                                                      | `[{ "digest": "sha256:abc123...", "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip" }]` |
| `annotations`           | `map[string]`     | Metadata (e.g., `org.opencontainers.image.source`).                                              | `{"org.opencontainers.image.revision": "a1b2c3d"}`                                  |

**Layer Schema:**
| **Field**       | **Type**  | **Description**                                                                 |
|-----------------|-----------|-------------------------------------------------------------------------------|
| `digest`        | `string`  | Cryptographic hash of the layer (SHA256).                                     |
| `mediaType`     | `string`  | MIME type of the compressed tar archive (e.g., `application/vnd.oci.image.layer.v1.tar+gzip`). |
| `size`          | `int64`   | Size in bytes of the decompressed layer.                                       |

---

### **2. OCI Runtime Spec (RunConfig)**
| **Field**               | **Type**          | **Description**                                                                                     | **Example**                                                                       |
|-------------------------|-------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `ociVersion`            | `string`          | OCI runtime spec version (e.g., `1.0.2-dev`).                                                       | `"1.0.2-dev"`                                                                     |
| `process`               | `ProcessConfig`   | Configuration for the main container process.                                                      | `{ "args": ["--config", "/etc/app.conf"], "cwd": "/app" }`                         |
| `root`                  | `RootConfig`      | Filesystem hierarchy configuration.                                                              | `{ "path": "/var/lib/containerd/io.containerd.content.v1.content", "diff": "/overlay" }` |
| `mounts`                | `array[Mount]`    | Filesystem mounts (bind mounts, volumes).                                                          | `[ { "destination": "/etc/hosts", "type": "bind", "source": "/host/etc/hosts" } ]` |
| `linux`                 | `LinuxConfig`     | Linux-specific configurations (namespaces, cgroups).                                               | `{ "namespaces": [ { "type": "pid" } ] }`                                         |
| `annotations`           | `map[string]`     | Runtime metadata.                                                                                 | `{"io.containerd.content.v1.content.shared": "true"}`                             |

**ProcessConfig Schema:**
| **Field**       | **Type**  | **Description**                                                                 |
|-----------------|-----------|-------------------------------------------------------------------------------|
| `user`          | `string`  | User to run as (e.g., `1000`).                                                  |
| `args`          | `[]string`| Command-line arguments.                                                        |
| `env`           | `[]string`| Environment variables (e.g., `PATH=/usr/local/bin`).                           |

---

### **3. Kubernetes CRI (Container Runtime Interface)**
| **Resource**         | **Schema**                                                                                     | **Purpose**                                                                           |
|----------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **RuntimeService**   | Defines CRUD operations for containers, images, and pods.                                      | Bridge between k8s and container runtimes (e.g., containerd).                        |
| **PodSandbox**       | Represents a pod’s isolated environment (namespaces, networks, cgroups).                     | Isolates pod execution from the host.                                                |
| **Container**        | Describes a single container within a pod (e.g., CPU/memory limits, runtime class).         | Managed by the runtime (e.g., `containerd` or `CRI-O`).                              |
| **ImageService**     | Handles image pull/push operations with OCI-compliant registries.                             | Integrates with Docker Hub, Harbor, or private registries.                            |
| **RuntimeClass**     | Defines runtime-specific configurations (e.g., `runc`, `catatonit`).                          | Allows runtime flexibility in k8s clusters.                                          |

**Example CRI Request (`PodSandboxConfig`):**
```json
{
  "metadata": { "name": "pod-123" },
  "runtime_spec": {
    "oci_spec": { "version": "1.0.2-dev", "process": { "args": ["nginx"] } },
    "linux": { "namespaces": [ { "type": "network" } ] }
  }
}
```

---

## **Query Examples**

### **1. Pulling an OCI Image**
Using `skopeo` (OCI-compliant CLI tool):
```bash
# Pull image from Docker Hub (OCI-compliant)
skopeo copy docker://nginx:alpine docker-daemon:nginx-alpine

# Inspect image manifest
skopeo inspect docker://nginx:alpine
```

**Output (Manifest Schema):**
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": { "mediaType": "application/vnd.oci.image.config.v1+json", "size": 1234, "digest": "sha256:..." },
  "layers": [ ... ]
}
```

---

### **2. Running a Container with `runc`**
```bash
# Create a sandbox directory (OCI runtime pre-step)
mkdir -p /var/lib/runc/pods

# Run a container using OCI runtime spec
runc run \
  --root=/var/lib/runc \
  --bundle=/tmp/myapp-bundle \
  myapp \
  --console-socket=/tmp/myapp.sock
```

**OCI Runtime Spec (`config.json`):**
```json
{
  "ociVersion": "1.0.2-dev",
  "process": {
    "terminal": true,
    "user": { "uid": 1000, "gid": 1000 },
    "args": ["python3", "app.py"],
    "env": [ "PATH=/usr/local/bin" ]
  },
  "mounts": [ { "destination": "/app", "type": "bind", "source": "/host/app" } ]
}
```

---

### **3. Kubernetes Deployment with CRI**
```yaml
# Deploy a pod using CRI-compliant runtime (e.g., containerd)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  template:
    spec:
      runtimeClassName: containerd  # Uses containerd via CRI
      containers:
      - name: nginx
        image: nginx:alpine
        resources:
          limits:
            memory: "128Mi"
```

**Verify RuntimeClass:**
```bash
kubectl describe runtimeclass containerd
```
**Output:**
```
Name:           containerd
Handler:        containerd
Configuration:  {"imageEndpoint": "unix:///run/containerd/containerd.sock"}
```

---

### **4. Querying Image Metadata with `ctr` (containerd CLI)**
```bash
# List images
ctr -n=libcontainers image ls

# Inspect image details
ctr -n=libcontainers image inspect <IMAGE_ID>

# Pull and push with OCI spec compliance
ctr -n=libcontainers image import ./myapp.tar.gz myapp:latest
ctr -n=libcontainers image push myapp:latest oci-registry/myapp:latest
```

---

## **Implementation Best Practices**
1. **Standardized Image Formats**
   - Use **OCI Image Spec** for all container images (not just Docker).
   - Leverage **BuildKit** for multi-stage builds and caching:
     ```dockerfile
     #syntax = docker/dockerfile:1.4
     FROM buildpack-deps as builder
     WORKDIR /app
     COPY . .
     RUN make build

     FROM alpine
     COPY --from=builder /app /app
     CMD ["app"]
     ```

2. **Security Hardening**
   - Enforce **non-root users** in runtime specs:
     ```json
     "linux": { "user": { "uid": 1000, "gid": 1000 } }
     ```
   - Use **read-only root filesystems** (`readOnlyRootFilesystem: true` in Kubernetes).
   - Sign images with **OCI Image Signing** (Cosign).

3. **Multi-Runtime Support**
   - Configure Kubernetes to support multiple runtimes via `RuntimeClass`:
     ```yaml
     apiVersion: node.k8s.io/v1
     kind: RuntimeClass
     metadata:
       name: firecracker
     handler: firecracker
     ```
   - Use **CRI-O** for lightweight Kubernetes deployments:
     ```bash
     # Install CRI-O
     curl -fsSL https://get.docker.com/cri-o/install.sh | sh
     ```

4. **Distributed Image Management**
   - Use **Harbor** or **Artifactory** for private OCI registries with:
     - **Vulnerability scanning** (Trivy, Clair).
     - **Retention policies** (auto-purge old images).
   - Example Harbor configuration:
     ```yaml
     # Harbor registry config
     registry:
       http:
         addr: :8000
       storage:
         filesystem:
           maxthreads: 100
           cachedir: /data/registry/cache
     ```

5. **Performance Optimization**
   - **Layer Compression**: Use `gzip` or `zstd` for layer files.
   - **Multi-Architecture Builds**: Build images for `linux/amd64`, `linux/arm64`:
     ```dockerfile
     # buildx support
     FROM --platform linux/amd64,linux/arm64 builder as builder
     ```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **Integration with Containers Standards**                                      |
|---------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **[Immutable Infrastructure]**  | Deploy applications as stateless containers with ephemeral storage.                                | Uses OCI images for consistent deployment.                                      |
| **[Service Mesh]**              | Manage service-to-service communication (e.g., Istio, Linkerd).                                     | Integrates with CRI for sidecar injection.                                      |
| **[GitOps]**                    | Sync Kubernetes manifests from Git repositories (e.g., Argo CD, Flux).                               | Deploys OCI-compliant images via CI/CD pipelines.                                |
| **[Serverless Containers]**     | Run short-lived containers (e.g., Knative, AWS Fargate).                                           | Uses OCI runtime specs for ephemeral execution.                                  |
| **[Hybrid Cloud Portability]**  | Deploy containers across on-prem and cloud (e.g., Kubernetes Federation).                          | Leverages CRI for multi-cloud container runtimes.                                |
| **[Observability]**              | Monitor containers with Prometheus, Grafana, and eBPF.                                              | Uses OCI runtime hooks for metrics collection.                                  |
| **[Security Scanning]**         | Scan container images for vulnerabilities (e.g., Trivy, Aqua Security).                            | Integrates with OCI Image Index for manifest inspection.                         |

---

## **Troubleshooting**
| **Issue**                          | **Cause**                                      | **Solution**                                                                         |
|------------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------|
| **Image Pull Errors**              | Registry auth or network issues.               | Verify `~/.docker/config.json` or Kubernetes secrets.                               |
| **Runtime CrashLoopBackOff**       | Misconfigured `resources.limits` or runtime spec. | Check `kubectl describe pod <pod-name>` for OOM errors.                              |
| **Layer Not Found**                | Corrupt or incomplete image layer.             | Rebuild image with `docker build --no-cache`.                                       |
| **CRI Unavailable**                | Runtime service not running (e.g., containerd). | Restart runtime: `systemctl restart containerd`.                                   |
| **Multi-Stage Build Failures**     | Incorrect `COPY --from` syntax.                 | Use `docker buildx build --platform linux/amd64` for cross-compilation.            |

---

## **Further Reading**
- [OCI Image Specification](https://github.com/opencontainers/image-spec)
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)
- [Kubernetes CRI Docs](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [BuildKit Documentation](https://github.com/moby/buildkit)
- [Harbor OCI Registry Guide](https://goharbor.io/docs/)