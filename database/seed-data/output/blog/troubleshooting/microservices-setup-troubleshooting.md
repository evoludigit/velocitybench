# **Debugging Microservices Setup: A Troubleshooting Guide**

## **Introduction**
Microservices architectures offer scalability, independent deployability, and fault isolation—but they introduce complexity in networking, service discovery, configuration, and inter-service communication. This guide helps diagnose and resolve common issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm symptoms with these checks:

### **Network & Connectivity Issues**
✅ **Connection Refused (503/Timeout Errors)**
✅ **Inter-service communication failures** (e.g., `gRPC/RPC timeouts`)
✅ **DNS resolution failures** (e.g., `serviceA could not connect to serviceB`)
✅ **Firewall/Network ACL blocking traffic**
✅ **Port conflicts** (e.g., two services exposed on the same port)

### **Configuration & Dependency Problems**
✅ **Missing/Incorrect environment variables**
✅ **Dependency version conflicts** (e.g., `libA v2 incompatible with libB v1`)
✅ **Database connection failures** (e.g., `PostgreSQL refused connection`)
✅ **Missing API endpoints** (e.g., `serviceB API v2 moved but not updated`)

### **Performance & Scalability Issues**
✅ **High latency between services**
✅ **Service crashes under load** (e.g., `OOM errors`)
✅ **Slow response times** (e.g., `300ms → 5s`)
✅ **Circuit breaker trips** (e.g., `Hystrix/Resilience4j flagging failures`)

### **Logging & Observability Gaps**
✅ **No logs for a specific service**
✅ **Inconsistent log levels** (e.g., `DEBUG vs ERROR`)
✅ **Missing distributed tracing** (e.g., no Zipkin/Jaeger traces)
✅ **Metrics missing for critical endpoints**

### **Deployment & Rollout Failures**
✅ **Container crashes on startup** (e.g., `ExitCode 137 = OOMKilled`)
✅ **Configuration drift post-deploy** (e.g., `env vars not updated`)
✅ **Database schema mismatch** (e.g., `migrations failed silently`)
✅ **Kubernetes/Pod crashes** (e.g., `CrashLoopBackOff`)

---

## **2. Common Issues & Fixes**
### **2.1 Networking & Connectivity Failures**
#### **Issue: Service A cannot reach Service B**
- **Symptom:** `Connection refused` or `ECONNREFUSED`
- **Root Causes:**
  - Wrong hostname/IP in `service-discovery` (e.g., `serviceB:8080` vs `serviceB.default.svc.cluster.local:8080`).
  - **Kubernetes:** Pods not in the same `Namespace` or `NetworkPolicy` blocking traffic.
  - **Service Mesh:** Istio/Linkerd misconfigured routing.

- **Fixes:**
  ```bash
  # Verify DNS resolution inside a pod
  kubectl exec -it <pod> -- nslookup serviceB
  ```
  **Solution:** Update `hosts` file or configure `headless service` in K8s.
  ```yaml
  # Example: Kubernetes Headless Service for direct pod IP
  apiVersion: v1
  kind: Service
  metadata:
    name: serviceB
  spec:
    clusterIP: None
    ports:
    - port: 8080
    selector:
      app: serviceB
  ```

#### **Issue: Port conflicts**
- **Symptom:** `Address already in use` (e.g., `9090` used by both `serviceA` and `serviceB`).
- **Fix:**
  ```bash
  # Check which process is using the port
  sudo lsof -i :9090
  ```
  **Solution:** Change port in `docker-compose.yml` or K8s `port` definition.
  ```yaml
  ports:
    - "9091:8080"  # Map host:container
  ```

---

### **2.2 Configuration & Dependency Errors**
#### **Issue: Missing environment variables**
- **Symptom:** `Error: Cannot find 'DB_HOST' in env`
- **Fix:**
  ```bash
  # Check if env var exists in a running container
  kubectl exec <pod> -- env | grep DB_HOST
  ```
  **Solution:** Set in `K8s Deployment` or `docker-compose`:
  ```yaml
  env:
    - name: DB_HOST
      value: "postgres-service"
  ```

#### **Issue: Database connection failures**
- **Symptom:** `Cannot connect to postgres://user:pass@db:5432/db`
- **Root Causes:**
  - Wrong credentials.
  - Database not ready on startup.
  - Network policies blocking `db` traffic.

- **Fix:**
  ```sql
  # Test DB connection from the app pod
  kubectl exec <app-pod> -- psql -h db -U user -d db
  ```
  **Solution:** Use `health checks` in K8s:
  ```yaml
  readinessProbe:
    exec:
      command: ["pg_isready", "-h", "db", "-U", "user"]
  ```

---

### **2.3 Performance & Scalability Bottlenecks**
#### **Issue: High latency between services**
- **Symptom:** `ServiceA → ServiceB latency: 2s (vs expected 100ms)`.
- **Root Causes:**
  - **Serial calls** (e.g., `serviceA → serviceB → serviceC`).
  - **Unoptimized gRPC/HTTP calls** (e.g., no async, large payloads).
  - **Database queries** (e.g., `N+1 problem`).

- **Fixes:**
  - **Optimize gRPC calls:**
    ```protobuf
    // Use streaming instead of blocking
    rpc ProcessOrder (stream Order) returns (stream OrderStatus);
    ```
  - **Cache responses** (Redis):
    ```java
    // Spring Boot with Redis
    @Cacheable(value = "userCache", key = "#userId")
    public User getUserById(Long userId) { ... }
    ```

---

### **2.4 Logging & Observability Missing**
#### **Issue: No logs for a specific service**
- **Symptom:** `kubectl logs <pod> --tail=50` → empty.
- **Fix:**
  ```yaml
  # Ensure logs are configured in K8s
  containers:
    - name: serviceA
      image: serviceA:latest
      volumeMounts:
        - name: logs
          mountPath: /var/log
  volumes:
    - name: logs
      emptyDir: {}
  ```
  **Solution:** Use `EFK Stack` (Elasticsearch-Fluentd-Kibana) or `Loki`.

#### **Issue: No distributed tracing**
- **Symptom:** `ServiceA → ServiceB latency hidden`.
- **Fix:** Deploy **Jaeger** or **Zipkin**:
  ```bash
  # Instrument gRPC calls (Java)
  tracing.startSpan("getUser").spanContext().remove();
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Purpose**                          | **Command/Usage**                          |
|------------------------|--------------------------------------|--------------------------------------------|
| `kubectl logs`         | View container logs                  | `kubectl logs <pod> -f`                    |
| `tcpdump`/`Wireshark` | Inspect network traffic               | `tcpdump -i eth0 port 8080`                |
| `k6`/`Locust`          | Load testing                         | `k6 run script.js --vus 100 --duration 30s` |
| `Prometheus + Grafana` | Metrics & alerts                     | `prometheus --config.file=prometheus.yml`   |
| `curl`/`Postman`       | Test API endpoints                   | `curl -X POST http://serviceB/api/v1/user`  |
| `istioctl analyze`     | Check Istio service mesh health       | `istioctl analyze <namespace>`             |

---

## **4. Prevention Strategies**
1. **Infrastructure as Code (IaC)**
   - Use **Terraform** or **Kustomize** for consistent deployments.
   - Example:
     ```hcl
     resource "kubernetes_deployment" "serviceA" {
       metadata { name = "serviceA" }
       spec {
         template {
           spec {
             container {
               image = "serviceA:latest"
               env {
                 name = "DB_HOST"
                 value = "postgres-service"
               }
             }
           }
         }
       }
     }
     ```

2. **Chaos Engineering**
   - Test failures with **Gremlin** or **Chaos Mesh**.
   - Example:
     ```yaml
     # Simulate pod failure
     apiVersion: chaos-mesh.org/v1alpha1
     kind: PodChaos
     metadata:
       name: kill-pod
     spec:
       action: pod-kill
       mode: one
       selector:
         namespaces:
           - default
         labelSelectors:
           app: serviceA
     ```

3. **Automated Testing**
   - **Contract Testing:** Pact (verify API contracts).
   - ** smoke tests:** Post-deploy API checks.
     ```bash
     # Example: Smoke test with k6
     k6 run 'http://serviceB/api/health' --expect 'status:200'
     ```

4. **Observability First**
   - **Structured Logging:** Use **JSON logs** (e.g., `logstash` parsing).
   - **Metrics:** Expose `Prometheus` endpoints.
   - **Tracing:** Auto-instrument with **OpenTelemetry**.

---

## **5. Checklist for Quick Resolution**
| **Step**                | **Action**                                  |
|-------------------------|--------------------------------------------|
| 1. **Check logs**       | `kubectl logs <pod>`                       |
| 2. **Verify network**   | `nslookup`, `tcpdump`, `kubectl describe pod` |
| 3. **Inspect configs**  | `env`, `configmaps`, `secrets`             |
| 4. **Test dependencies**| `pg_isready`, `curl -v http://db:5432`     |
| 5. **Monitor metrics**  | Prometheus/Grafana dashboards              |
| 6. **Reproduce locally**| `docker-compose up`                        |
| 7. **Rollback**         | `kubectl rollout undo deployment serviceA`  |

---

## **Conclusion**
Microservices debugging requires a structured approach:
1. **Isolate** (network? config? dependency?).
2. **Verify** (logs, metrics, traces).
3. **Fix** (code, configs, or infrastructure).
4. **Prevent** (tests, chaos, observability).

By following this guide, you can resolve **90% of issues in <1 hour**. For complex cases, leverage **distributed tracing** and **automated rollbacks**.

---
**Need deeper debugging?**
- **Network:** `tcpdump`, `kubectl describe pod` (`Events` section).
- **Code:** Check **application logs** (`DEBUG` level).
- **Database:** Run `EXPLAIN ANALYZE` for slow queries.