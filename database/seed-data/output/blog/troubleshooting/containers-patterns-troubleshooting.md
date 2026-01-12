# **Debugging Containers Patterns: A Troubleshooting Guide**
*For backend engineers troubleshooting Docker/Kubernetes-based containerized deployments*

---

## **1. Introduction**
Containers (Docker, Kubernetes, etc.) enable scalable, isolated, and reproducible deployments. However, misconfigurations, runtime issues, and dependency conflicts are common. This guide focuses on **practical debugging techniques** to resolve issues quickly.

---

## **2. Symptom Checklist**
Before diving into fixes, identify which symptoms match your issue:

| **Symptom**               | **Possible Cause**                          | **Impact Area**               |
|---------------------------|--------------------------------------------|-------------------------------|
| Container fails to start  | Incorrect `Dockerfile`, missing dependencies | Deployment, CI/CD             |
| High resource usage       | Container leaks memory/cpu, inefficient app | Performance, scaling          |
| Inter-container failures  | Misconfigured networks, missing env vars    | Communication, app logic       |
| Slow deployments          | Image layers not cached, large base images | DevOps efficiency             |
| Persistent crashes         | Application errors, signal handling issues | Stability                     |

**Quick Check:**
- Is the problem **application-level** (logs show errors) or **infrastructure-level** (e.g., Docker/K8s logs show failures)?
- Are modern tools (e.g., `docker inspect`, `kubectl describe`) being used?

---

## **3. Common Issues & Fixes**

### **A. Container Fails to Start**
#### **Symptom:** `docker build`/`docker run` exits immediately.
#### **Common Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Example Code Snippet**                  |
|-------------------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| Missing base image                  | Verify `FROM` in Dockerfile                                          | `FROM ubuntu:22.04` (not a placeholder)  |
| Incorrect layer dependencies        | Reorder `RUN` commands to ensure dependencies are installed first     | ```dockerfile<br>RUN apt-get update && apt-get install -y curl<br>RUN curl -sL https://example.com > app.sh``` |
| Non-zero exit code in `ENTRYPOINT`  | Check `CMD`/`ENTRYPOINT` arguments and app logs                      | ```dockerfile<br>ENTRYPOINT ["python3"]<br>CMD ["app.py --check"]``` |
| Missing ports/volumes in K8s YAML    | Ensure `ports`/`volumes` are defined in Deployment/StatefulSet          | ```yaml<br>ports:<br>- containerPort: 80<br>volumes:<br>- name: data<br>  mountPath: /app/data``` |

#### **Debugging Steps**
1. **Check logs:**
   ```sh
   docker logs <container_id>
   ```
2. **Inspect image layers:**
   ```sh
   docker history <image_name>
   ```
3. **Run interactively to debug:**
   ```sh
   docker run -it --entrypoint /bin/sh <image_name>
   ```

---

### **B. High Resource Usage**
#### **Symptom:** Containers consume unexpected CPU/memory.
#### **Common Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Example Code Snippet**                  |
|-------------------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| Memory leaks in application         | Use `ulimit` or profile the app (e.g., with `valgrind`)                 | ```dockerfile<br>RUN apt-get install valgrind<br>CMD ["valgrind", "--leak-check=full", "./app"]``` |
| Unbounded loops in code             | Add rate limits or circuit breakers                                      | ```python<br># Example: FastAPI rate limiting<br>from fastapi import FastAPI<br>from fastapi.middleware import Middleware<br>from fastapi.middleware.gzip import GZipMiddleware<br>app = FastAPI(middleware=[Middleware(GZipMiddleware)]<br>``` |
| Docker swarm/K8s resource limits    | Set `resources.limits` in Kubernetes or `docker run --cpus=0.5`         | ```yaml<br>resources:<br>  limits:<br>    cpu: "500m"<br>    memory: "512Mi``` |

#### **Debugging Steps**
1. **Monitor usage:**
   ```sh
   docker stats <container_name>
   ```
   or (for K8s):
   ```sh
   kubectl top pods
   ```
2. **Profile memory:**
   ```sh
   docker exec -it <container_id> python -m cProfile -s cumulative app.py
   ```

---

### **C. Inter-Container Failures**
#### **Symptom:** Services can’t communicate (e.g., DB connection refused).
#### **Common Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Example Code Snippet**                  |
|-------------------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| Incorrect network DNS resolution    | Use `--network=host` or define custom DNS in `docker-compose.yml`       | ```yaml<br>services:<br>  app:<br>    networks:<br>      - backend<br>networks:<br>  backend:<br>    driver: bridge``` |
| Missing environment variables       | Pass via `ENV` in Dockerfile or `--env` in `docker run`                  | ```dockerfile<br>ENV DB_URL=postgres://user:pass@db:5432/db``` |
| Port conflicts                      | Expose ports in `ports:` (Dockerfile) or `nodePort` (K8s Service)      | ```yaml<br>apiVersion: v1<br>kind: Service<br>spec:<br>  type: NodePort<br>  ports:<br>  - port: 80<br>    nodePort: 30008``` |

#### **Debugging Steps**
1. **Test connectivity:**
   ```sh
   docker exec -it <container_id> ping <target_container_name>
   ```
2. **Check network config:**
   ```sh
   docker network inspect <network_name>
   ```
3. **Verify logs:**
   ```sh
   kubectl logs <pod_name> -c <container_name>
   ```

---

### **D. Slow Deployments**
#### **Symptom:** Long build/push times.
#### **Common Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Example Code Snippet**                  |
|-------------------------------------|--------------------------------------------------------------------------|--------------------------------------------|
| Large base images                   | Use multi-stage builds or Alpine Linux                                    | ```dockerfile<br># Stage 1: Build<br>FROM python:3.9 as builder<br>RUN pip install --user -r requirements.txt<br># Stage 2: Runtime<br>FROM python:3.9-alpine<br>COPY --from=builder /root/.local /root/.local<br>ENV PATH=/root/.local/bin:$PATH``` |
| Uncached layers                     | Use `.dockerignore` to exclude unnecessary files                       | ```.dockerignore<br>node_modules/<br>.git/<br>logs/<br>venv/``` |
| Slow registry pushes                | Compress images (`docker buildx`) or use layer caching                   | ```sh<br>docker buildx build --cache-from=registry.example.com/myapp:latest -t myapp:latest .``` |

#### **Debugging Steps**
1. **Measure layer times:**
   ```sh
   time docker build -t myapp:debug .
   ```
2. **Check image size:**
   ```sh
   docker image inspect --format='{{.Size}}' myapp:latest
   ```

---

## **4. Debugging Tools & Techniques**
### **Docker-Specific Tools**
| **Tool**               | **Use Case**                                      | **Example Command**                     |
|------------------------|--------------------------------------------------|-----------------------------------------|
| `docker stats`         | Monitor resource usage                           | `docker stats --no-stream`              |
| `docker inspect`       | Check container/config details                   | `docker inspect <container_id>`         |
| `docker events`        | Real-time event streaming                        | `docker events --filter 'event=die'`    |
| `docker exec`          | Run commands in running containers               | `docker exec -it <id> bash`             |
| `docker cp`            | Copy files between host/container                | `docker cp <id>:/app/config ./config`  |

### **Kubernetes-Specific Tools**
| **Tool**               | **Use Case**                                      | **Example Command**                     |
|------------------------|--------------------------------------------------|-----------------------------------------|
| `kubectl describe`     | Debug Pod/Deployment issues                      | `kubectl describe pod <pod_name>`       |
| `kubectl logs`         | View container logs                               | `kubectl logs -f <pod_name>`            |
| `kubectl exec`         | Run commands in Pods                             | `kubectl exec -it <pod_name> -- sh`    |
| `kubectl top`          | Check resource usage                             | `kubectl top pods`                     |
| `kubectl portal`       | Interactive K8s debugging (via k9s)             | `k9s`                                   |

### **Cross-Platform Techniques**
1. **Log Aggregation:**
   - Use **Loki/ELK** for centralized logs.
   - Example with Docker logs:
     ```sh
     docker logs --tail 50 --since 1h <container_id> > debug.log
     ```
2. **Distributed Tracing:**
   - Tools: **Jaeger**, **OpenTelemetry**.
   - Example with OpenTelemetry:
     ```python
     from opentelemetry import trace
     trace.set_tracer_provider(trace.get_tracer_provider())
     tracer = trace.get_tracer(__name__)
     ```
3. **Syntax Checking:**
   - Validate Dockerfiles with `hadolint`:
     ```sh
     hadolint Dockerfile
     ```
   - Validate YAML with `yq`:
     ```sh
     yq eval . deployments.yaml
     ```

---

## **5. Prevention Strategies**
### **A. Best Practices for Docker**
1. **Optimize `Dockerfile`:**
   - Use `.dockerignore` to exclude unnecessary files.
   - Leverage multi-stage builds to reduce image size.
2. **Secure Images:**
   - Scan for vulnerabilities with `trivy`:
     ```sh
     trivy image myapp:latest
     ```
   - Sign images with `cosign`.
3. **Idempotent Builds:**
   - Avoid `RUN apt-get upgrade` (can change behavior).
   - Use specific versions (e.g., `FROM python:3.9.16`).

### **B. Best Practices for Kubernetes**
1. **Resource Limits:**
   - Always define `resources.requests` and `resources.limits`.
2. **Health Checks:**
   - Use `livenessProbe` and `readinessProbe`:
     ```yaml
     livenessProbe:
       httpGet:
         path: /health
         port: 8080
       initialDelaySeconds: 5
       periodSeconds: 10
     ```
3. **ConfigMaps/Secrets:**
   - Externalize configs to avoid hardcoding:
     ```yaml
     envFrom:
       - configMapRef:
           name: app-config
     ```

### **C. CI/CD Pipeline Defenses**
1. **Build Validation:**
   - Test images in CI with `docker scan` (for security).
   - Example GitHub Actions step:
     ```yaml
     - name: Scan image for vulnerabilities
       uses: aquasecurity/trivy-action@master
       with:
         image-ref: 'myapp:latest'
     ```
2. **Rollback Strategies:**
   - Use K8s `rollout undo` or Docker `docker rollback`.
3. **Chaos Engineering:**
   - Test failure scenarios with **Chaos Mesh** or **Gremlin**.

---

## **6. Checklist for Quick Resolution**
| **Step**                     | **Action**                                                                 |
|------------------------------|----------------------------------------------------------------------------|
| 1. Reproduce locally         | `docker-compose up` or `minikube start`                                   |
| 2. Check logs                | `docker logs` / `kubectl logs`                                            |
| 3. Inspect configs           | `docker inspect` / `kubectl describe`                                     |
| 4. Profile resources         | `docker stats` / `kubectl top`                                            |
| 5. Validate dependencies     | `apt-get -y --dry-run install <pkg>` (in container shell)                 |
| 6. Test network connectivity | `curl` or `nc -zv <host> <port>` inside container                          |
| 7. Compare with known good   | Diff configs against a working version                                     |

---

## **7. When to Escalate**
- **Infrastructure limits:** If the issue is beyond local testing (e.g., registry quotas).
- **Deep app bugs:** If logs show unhandled exceptions requiring code changes.
- **Tooling failures:** If `docker`/`kubectl` is misconfigured (e.g., permission issues).

**Escalation Path:**
1. Check cluster logs (`/var/log/docker/`) for Docker/K8s core issues.
2. Engage with platform teams if the problem is environment-specific (e.g., CNI plugin crashes).

---

## **8. References**
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Trivy Scanning](https://aquasecurity.github.io/trivy/latest/docs/scanning/)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)

---
**Final Tip:** Keep a `debug.sh` script in your repo for quick local debugging:
```sh
#!/bin/bash
docker-compose up -d --build
docker-compose logs -f
docker exec -it app_container bash
```
This ensures reproducible debug sessions. Happy debugging! 🚀