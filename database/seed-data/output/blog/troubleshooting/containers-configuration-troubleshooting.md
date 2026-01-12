# **Debugging Containers Configuration: A Troubleshooting Guide**
*For Senior Backend Engineers*

This guide provides a structured approach to diagnosing and resolving common issues in containerized environments, including misconfigurations, runtime errors, and deployment failures. We’ll focus on Kubernetes, Docker, and container orchestration frameworks.

---

## **Table of Contents**
1. [Symptom Checklist](#symptom-checklist)
2. [Common Issues & Fixes](#common-issues--fixes)
3. [Debugging Tools & Techniques](#debugging-tools--techniques)
4. [Prevention Strategies](#prevention-strategies)

---

## **1. Symptom Checklist**
Before diving into fixes, quickly verify these symptoms to narrow down the problem:

✅ **Deployment Failures**
- Pods stuck in `Pending`, `CrashLoopBackOff`, or `ImagePullBackOff`.
- Containers fail to start with no logs (e.g., `Error: unable to up`).

✅ **Resource Constraints**
- CPU/memory limits exceeded (`OOMKilled` or `Evicted` events).
- Containers slow or unresponsive due to insufficient resources.

✅ **Networking Issues**
- Containers can’t communicate (e.g., `Connection refused`, `DNS lookup failed`).
- Ports not exposed externally.

✅ **Configuration Errors**
- Missing environment variables or config maps.
- Incorrect `usr/local/bin` paths (common in Dockerfiles).

✅ **Volume & Persistence Problems**
- Volumes not mounted (`/mnt/data not found`).
- Persistent storage failing (`IO errors`).

✅ **Image-Related Issues**
- Wrong image tag (e.g., `latest` causing unexpected changes).
- Image pull errors (authentication, registry issues).

---

## **2. Common Issues & Fixes**
### **A. Pods Not Starting**
#### **Issue:** Pod stuck in `CrashLoopBackOff`
**Symptoms:**
- Logs show repeated crashes (e.g., `app crashed with exit code 137`).
- Last exit code often indicates OOM (`137`) or signal kill (`-9`).

**Debugging Steps:**
1. **Check Logs**
   ```sh
   kubectl logs <pod-name> -c <container-name> --previous
   ```
   - Look for errors like `segmentation fault` (common in C++ apps) or `command not found`.

2. **Inspect Events**
   ```sh
   kubectl describe pod <pod-name>
   ```
   - Key fields:
     - `Restart Count` (if high, indicates instability).
     - `Events` (look for OOM, crash, or permission issues).

3. **Common Fixes**
   - **OOM Killer:**
     ```yaml
     # Update resource limits in Deployment manifest
     resources:
       limits:
         memory: "512Mi"
         cpu: "500m"
     ```
   - **Missing Dependencies:**
     ```dockerfile
     # Ensure all dependencies are installed (e.g., Python modules)
     RUN pip install --no-cache-dir -r requirements.txt
     ```
   - **Permission Errors:**
     ```yaml
     # Run as non-root if needed (security best practice)
     securityContext:
       runAsUser: 1000
       runAsGroup: 3000
     ```

---

### **B. Containers Can’t Communicate**
#### **Issue:** Service A calls Service B, but requests time out.
**Symptoms:**
- `Connection refused` or `ECONNREFUSED` errors.
- `kubectl exec -it <pod> curl <service-name>` fails.

**Debugging Steps:**
1. **Verify DNS Resolution**
   ```sh
   kubectl exec -it <pod> -- nslookup <service-name>
   ```
   - Should return the ClusterIP or `<service>.namespace.svc.cluster.local`.

2. **Check Service & Endpoints**
   ```sh
   kubectl get svc <service-name>
   kubectl get endpoints <service-name>
   ```
   - If no endpoints, check if pods are ready:
     ```sh
     kubectl get pods -o wide
     ```

3. **Network Policies Blocking Traffic**
   ```sh
   kubectl get networkpolicy
   ```
   - If a policy denies traffic between namespaces, adjust rules:
     ```yaml
     apiVersion: networking.k8s.io/v1
     kind: NetworkPolicy
     metadata:
       name: allow-frontend-to-backend
     spec:
       podSelector:
         matchLabels:
           app: backend
       ingress:
       - from:
         - podSelector:
             matchLabels:
               app: frontend
     ```

4. **Firewall Rules (Node-Level)**
   - Ensure node firewall (`ufw`, `iptables`) allows traffic on container ports.

---

### **C. Image Pull Failures**
#### **Issue:** `ImagePullBackOff` or `Error response from daemon`
**Symptoms:**
- Pod stuck in `Pending` with event: `Failed to pull image`.
- Registry authentication errors (`unauthorized`).

**Debugging Steps:**
1. **Check Image Tag**
   ```yaml
   # Ensure correct tag (avoid `latest`)
   image: my-repo/nginx:1.23.1
   ```
   - Use immutable tags for stability.

2. **Verify Registry Access**
   ```sh
   kubectl describe pod <pod-name> | grep ImagePull
   ```
   - If using private registry, ensure `imagePullSecrets` is configured:
     ```yaml
     spec:
       imagePullSecrets:
       - name: regcred
     ```
   - Create a `.dockerconfigjson` secret:
     ```sh
     kubectl create secret docker-registry regcred \
       --docker-server=<registry-url> \
       --docker-username=<user> \
       --docker-password=<password> \
       --docker-email=<email>
     ```

3. **Test Image Locally**
   ```sh
   docker pull <image-name>:<tag>
   ```
   - If this fails, the issue is registry-related (network, credentials, or image corruption).

---

### **D. Volume Mount Issues**
#### **Issue:** `/data not found` or permission denied.
**Symptoms:**
- App crashes with `open /data/file.txt: No such file or directory`.
- `Permission denied` on mounted files.

**Debugging Steps:**
1. **Verify Volume Definition**
   ```yaml
   # Check if volume exists and is correctly mounted
   volumes:
     - name: data-volume
       persistentVolumeClaim:
         claimName: my-pvc
   ```
   - Ensure PVC exists:
     ```sh
     kubectl get pvc
     ```

2. **Check Mount Path**
   - If using `emptyDir`, specify a path:
     ```yaml
     volumeMounts:
       - name: temp-data
         mountPath: /tmp/data
     ```

3. **Permissions Fix**
   - Use `fsGroup` or `securityContext`:
     ```yaml
     securityContext:
       fsGroup: 2000
     ```

---

## **3. Debugging Tools & Techniques**
### **A. Essential kubectl Commands**
| Command | Purpose |
|---------|---------|
| `kubectl get pods -w` | Watch pod status in real-time. |
| `kubectl logs <pod> --tail=50` | Tail last 50 lines of logs. |
| `kubectl exec -it <pod> -- /bin/sh` | Debug inside a running container. |
| `kubectl describe pod <pod>` | Deep-dive into pod events. |
| `kubectl port-forward <pod> 8080:80` | Test port access locally. |

### **B. Advanced Tools**
- **`stern`**: Multiline log streaming:
  ```sh
  stern <pod-name> -n <namespace>
  ```
- **`kubectl debug`**: Attach an ephemeral container:
  ```sh
  kubectl debug -it <pod> --image=busybox --target=<container>
  ```
- **`livenessProbe` & `readinessProbe`**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10
  ```

### **C. Network Debugging**
- **`nc` (netcat) Test**:
  ```sh
  kubectl exec -it <pod> -- nc -zv <service> 80
  ```
- **`tcpdump`**:
  ```sh
  kubectl exec -it <pod> -- tcpdump -i eth0 port 80
  ```

---

## **4. Prevention Strategies**
### **A. Best Practices for Containers**
1. **Immutable Images**
   - Never run containers as `root`. Use `USER` in Dockerfile:
     ```dockerfile
     USER nodejs
     ```
2. **Minimal Base Images**
   - Prefer `alpine`-based images to reduce attack surface.
3. **Resource Limits**
   - Always set CPU/memory requests/limits:
     ```yaml
     resources:
       requests:
         cpu: "100m"
         memory: "128Mi"
       limits:
         cpu: "500m"
         memory: "512Mi"
     ```

### **B. Infrastructure as Code (IaC)**
- Use **Helm** or **Kustomize** for consistent deployments.
- Example Helm template snippet:
  ```yaml
  {{- if .Values.resourceLimits.enabled }}
  resources:
    limits:
      cpu: {{ .Values.resourceLimits.cpu }}m
      memory: {{ .Values.resourceLimits.memory }}
  {{- end }}
  ```

### **C. Monitoring & Alerts**
- **Prometheus + Grafana**: Track pod restarts, CPU usage, and latency.
- **Alert on Crashes**:
  ```yaml
  # Example Prometheus alert rule
  - alert: PodCrashLooping
    expr: kube_pod_container_status_waiting{reason="CrashLoopBackOff"} > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Pod {{ $labels.pod }} is crash looping"
  ```

### **D. Rollback Strategy**
- Use `kubectl rollout undo` for quick rollbacks:
  ```sh
  kubectl rollout undo deployment/<deployment-name> --to-revision=2
  ```
- Implement **canary deployments** to reduce blast radius.

---

## **Summary Checklist for Quick Resolution**
1. **Is the pod stuck?** → Describe pod, check logs, adjust resources/limits.
2. **Is networking blocked?** → Test DNS, service endpoints, network policies.
3. **Can’t pull image?** → Verify registry auth, image tag, and network.
4. **Volume missing?** → Check PVC, mount paths, and permissions.
5. **App crashes?** → Debug inside container, check dependencies, and logs.

---
**Final Tip:** Always start with `kubectl describe`—it reveals 90% of issues. For complex problems, attach a debug container and inspect files directly. Automate checks with CI/CD pipelines to catch misconfigurations early.