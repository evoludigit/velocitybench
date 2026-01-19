**[Pattern] Containers Troubleshooting Reference Guide**

---

### **Overview**
Containerized applications (e.g., Docker, Kubernetes) abstract infrastructure complexities but introduce unique challenges when debugging runtime failures. This guide outlines systematic troubleshooting for:
- **Unresponsive containers** (crashes, hangs, timeouts).
- **Resource constraints** (CPU/memory starvation).
- **Networking issues** (failed connections, DNS misconfigurations).
- **Configuration errors** (missing files, permission conflicts).

Troubleshooting follows a structured approach:
1. **Verify fundamentals** (logs, container state).
2. **Inspect resources** (CPU, memory, storage).
3. **Test network connectivity** (ports, endpoints).
4. **Review configuration and dependencies**.

---

### **Schema Reference**
| **Category**               | **Attribute**               | **Description**                                                                 | **Tools/Commands**                          |
|----------------------------|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Container State**        | Status                      | Running/Paused/Crashed/Dead/Exited.                                          | `docker inspect <container> \| grep Status` |
|                            | Exit Code                   | Non-zero indicates failure.                                                   | `docker logs <container>`                   |
|                            | Logs                        | Application/error output.                                                     | `kubectl logs <pod>` (K8s)                 |
| **Resources**              | CPU Usage                   | Percentage of allocated CPU.                                                  | `docker stats`                              |
|                            | Memory Usage                | RSS/Heap usage vs. limits.                                                    | `docker stats --no-stream`                  |
|                            | Disk I/O                    | Latency, read/write errors.                                                   | `docker events` (filter for `disk I/O`)    |
| **Networking**             | Port Mappings               | Host:Container ports.                                                        | `docker port <container>`                   |
|                            | Connectivity Tests          | Ping, `telnet`, or `curl` to endpoints.                                       | `kubectl exec -it <pod> -- ping <host>`    |
|                            | DNS Resolution              | Failed `nslookup` or `dig` queries.                                           | `docker exec <container> nslookup <host>`   |
| **Configuration**          | Environment Variables       | Missing/incorrect values.                                                     | `docker inspect <container> \| grep Env`   |
|                            | Volume Mounts               | Missing files or permission errors.                                           | `docker inspect <container> \| grep Mounts`|
| **Dependencies**           | Linked Containers           | Health or readiness probes.                                                   | `kubectl describe pod <pod>` (K8s)         |

---

### **Troubleshooting Workflow**

#### **1. Verify Container Fundamentals**
**Symptom:** Container fails to start or exits immediately.
**Steps:**
- Check status:
  ```bash
  docker ps -a  # List containers (including stopped)
  ```
- Inspect logs:
  ```bash
  docker logs <container>  # Docker
  kubectl logs <pod>       # Kubernetes
  ```
- Examine exit code:
  ```bash
  docker inspect --format='{{.State.ExitCode}}' <container>
  ```
  - **Exit Code 0:** Successful (unlikely for failures).
  - **Exit > 128:** Signal-based (e.g., `137 = SIGKILL`).
  - **Exit between 129-255:** Signal number + 128.

**Common Causes:**
  - Missing environment variables.
  - Invalid `CMD`/`ENTRYPOINT` arguments.
  - Permission denied on mounted volumes.

---

#### **2. Diagnose Resource Constraints**
**Symptom:** Container throttled or killed (OOM, CPU throttling).
**Steps:**
- **CPU:**
  ```bash
  docker stats --no-stream <container>  # Check %CPU usage
  ```
  - **Action:** Increase limits in `docker run` or Kubernetes `resources.limits.cpu`.
- **Memory:**
  ```bash
  docker top <container>  # Check memory per process
  ```
  - **Action:** Adjust `MEMORY_LIMIT` or check for memory leaks.
- **Disk:**
  ```bash
  docker exec <container> df -h  # Check disk usage
  ```
  - **Action:** Clean logs or resize storage if needed.

**Tools:**
- **cAdvisor** (K8s): Monitor resource usage.
- **Prometheus + Grafana**: Long-term metrics.

---

#### **3. Networking Issues**
**Symptom:** Container fails to communicate with dependencies.
**Steps:**
- **Test connectivity:**
  ```bash
  kubectl exec -it <pod> -- ping <service>  # K8s
  docker exec <container> ping <host>       # Docker
  ```
- **Check ports:**
  ```bash
  docker port <container>  # Verify exposed ports
  netstat -tulnp          # Host-side port checks
  ```
- **DNS Resolution:**
  ```bash
  docker exec <container> cat /etc/resolv.conf
  ```
  - **Fix:** Mount custom `/etc/resolv.conf` or configure DNS in `docker-compose`.

**Common Causes:**
  - Firewall blocking traffic.
  - Misconfigured `network_mode` (e.g., `host` vs. `bridge`).
  - Service mesh misrouting (Istio/Linkerd).

---

#### **4. Configuration Errors**
**Symptom:** Application fails due to missing files or permissions.
**Steps:**
- **Inspect mounts:**
  ```bash
  docker inspect <container> \| grep Mounts
  ```
  - **Action:** Verify file paths and permissions in host volume mounts.
- **Environment vars:**
  ```bash
  docker inspect <container> \| grep Env
  ```
  - **Action:** Set missing vars via `--env` or `environment:` in `docker-compose`.

**Example Fix:**
If a config file `/app/config.yaml` is missing:
```yaml
# docker-compose.yml
volumes:
  - ./config:/app/config:ro  # Ensure host path exists
```

---

### **Query Examples**
#### **Docker**
1. **List all containers (including stopped):**
   ```bash
   docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```
2. **Check logs for a crashed container:**
   ```bash
   docker logs --tail 50 <container> \| grep -i error
   ```
3. **Inspect network connectivity:**
   ```bash
   docker exec <container> curl -v http://localhost:8080
   ```

#### **Kubernetes**
1. **Describe a failing pod:**
   ```bash
   kubectl describe pod <pod> \| grep -i "error\|warning"
   ```
2. **Exec into a pod to debug:**
   ```bash
   kubectl exec -it <pod> -- /bin/bash
   ```
3. **Check pod events:**
   ```bash
   kubectl get events --sort-by=.lastTimestamp
   ```

---

### **Advanced Debugging**
| **Scenario**               | **Tool/Command**                          | **Diagnosis**                          |
|----------------------------|-------------------------------------------|----------------------------------------|
| **Init Container Failure** | `kubectl logs <pod> -c <init-container>`  | Init step crashed (e.g., config load). |
| **Sidecar Proxy Issues**   | `kubectl port-forward <pod> 8080:8080`    | Test if sidecar (e.g., Envoy) is reachable. |
| **Volume Corruption**      | `docker run --rm -v <host-path>:/target alpine ls /target` | Verify host files exist. |

---

### **Related Patterns**
1. **[Container Orchestration]** – Scale debugging to clusters (Kubernetes, Swarm).
2. **[Logging Aggregation]** – Centralize logs with ELK Stack or Loki.
3. **[Observability]** – Instrument containers with OpenTelemetry.
4. **[Network Policies]** – Isolate troubleshooting to specific pods.
5. **[Health Checks]** – Implement liveness/readiness probes for auto-recovery.

---
**References:**
- [Docker Inspect Docs](https://docs.docker.com/engine/reference/commandline/inspect/)
- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)