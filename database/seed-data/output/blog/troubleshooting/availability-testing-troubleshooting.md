# **Debugging Availability Testing: A Troubleshooting Guide**

## **Introduction**
Availability Testing ensures that systems remain operational and responsive under expected and extreme loads. Issues in availability can stem from infrastructure failures, misconfigured scaling policies, unhealthy dependencies, or poorly designed resilience mechanisms. This guide provides a structured approach to diagnosing and resolving availability problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the following symptoms:

### **Primary Symptoms**
- **[ ] Applications frequently crash or restart unexpectedly** (e.g., Kubernetes pods, Docker containers, or server processes).
- **[ ] Latency spikes or high response times** (e.g., API calls taking >1s under normal load).
- **[ ] System resources (CPU, memory, disk, network) are at or near capacity** despite scaling.
- **[ ] Dependency failures** (e.g., database timeouts, third-party API outages).
- **[ ] Users report intermittent unavailability** (e.g., 5xx errors in logs but no obvious downtime).
- **[ ] Auto-scaling fails to deploy new instances** (e.g., failed rollouts in Kubernetes).

### **Secondary Symptoms (Indicators of Underlying Issues)**
- **[ ] Logs show `OutOfMemoryError`, `ConnectionRefused`, or `TimeoutException`**.
- **[ ] Health checks fail but the system is "technically working"** (e.g., `/health` endpoint returns 200 but API calls fail).
- **[ ] Load balancers drop requests** (e.g., 503 Service Unavailable errors).
- **[ ] Monitoring alerts for high error rates or slow queries**.
- **[ ] Gateway or API gateway timeouts**.

---
## **2. Common Issues and Fixes**

### **Issue 1: Unhealthy Pods in Kubernetes (Crashes or Restarts)**
**Symptoms:**
- Pods are in `CrashLoopBackOff` or `Error` state.
- Logs show OOM kills, segfaults, or unhandled exceptions.

**Root Causes:**
- **Memory leaks** (application consumes too much RAM over time).
- **Uncaught exceptions** (crashing threads).
- **Resource limits too low** (CPU/memory constraints).

**Debugging Steps & Fixes:**
1. **Check pod logs:**
   ```sh
   kubectl logs <pod-name> --previous  # Check previous instance's logs
   kubectl describe pod <pod-name>   # Check events and failures
   ```
2. **Verify resource limits:**
   ```yaml
   # Example: Increase memory request/limit in deployment.yaml
   resources:
     requests:
       memory: "2Gi"
       cpu: "1"
     limits:
       memory: "3Gi"
       cpu: "2"
   ```
3. **Enable profiling (if memory issues):**
   - Add `-XX:+HeapDumpOnOutOfMemoryError` to JVM args.
   - Use `pmap` to check memory usage:
     ```sh
     pmap -x <pid> | grep heap
     ```
4. **Check for crashes in logs:**
   - Look for `java.lang.OutOfMemoryError`, `Segmentation Fault`, or `Aborted`.

**Preventive Measure:**
- Use **liveness/readiness probes** to auto-restart unhealthy pods.
- Set **resource limits** based on benchmarking.

---

### **Issue 2: Auto-Scaling Not Responding to Load**
**Symptoms:**
- Cluster CPU/memory usage is high, but no new pods are spawned.
- Horizontal Pod Autoscaler (HPA) shows `CurrentMetric` vs. `DesiredReplicas` mismatch.

**Root Causes:**
- **Missing metrics server** (HPA needs Prometheus/Metrics Server).
- **Slow metric collection** (high latency in scraping).
- **Improper target CPU/memory thresholds** (e.g., too high).
- **Pod disruption budget too restrictive** (prevents scaling).

**Debugging Steps & Fixes:**
1. **Verify HPA metrics:**
   ```sh
   kubectl get hpa
   kubectl describe hpa <hpa-name>
   ```
2. **Check metrics server status:**
   ```sh
   kubectl get --raw "/apis/metrics.k8s.io/v1beta1/pods" | jq .
   ```
3. **Adjust scaling thresholds:**
   ```yaml
   # Example: Scale based on CPU utilization (50% target)
   metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 50
   ```
4. **Enable custom metrics (e.g., requests per second):**
   ```yaml
   metrics:
     - type: Pods
       pods:
         metric:
           name: requests_per_second
         target:
           type: AverageValue
           averageValue: 1000
   ```

**Preventive Measure:**
- **Test scaling manually** with `kubectl scale deployment <name> --replicas=5`.
- **Use Cluster Autoscaler** if scaling to nodes (not just pods).

---

### **Issue 3: Database Connection Leaks (Timeouts Under Load)**
**Symptoms:**
- Application logs show `Connection pool exhausted` or `TimeoutException`.
- Database server logs show too many connections.

**Root Causes:**
- **Connection pooling misconfigured** (too few connections).
- **Unclosed JDBC connections** (memory leaks in app).
- **Database max connections reached**.

**Debugging Steps & Fixes:**
1. **Check connection pool metrics:**
   - For HikariCP:
     ```java
     // Log pool stats
     System.out.println(hikariDataSource.getHikariPoolMXBean().getActiveConnections());
     ```
   - For PgBouncer:
     ```sh
     show pools, clients, transactions;
     ```
2. **Increase connection pool size:**
   - **HikariCP config:**
     ```java
     hikari {
       maximum-pool-size = 50
       connection-timeout = 30000
     }
     ```
   - **PgBouncer config (`pgbouncer.ini`):**
     ```
     [databases]
       mydb = host=db hostaddr=dbhost pool_size=50
     ```
3. **Fix connection leaks (e.g., missed `close()` calls):**
   - Use **Try-with-resources** in Java:
     ```java
     try (Connection conn = dataSource.getConnection()) {
       // Use connection
     } // Auto-closes
     ```
   - Enable **HikariCP leak detection**:
     ```java
     hikari.leak-detection-threshold = 5000
     ```

**Preventive Measure:**
- **Monitor pool usage** (e.g., Prometheus + Grafana).
- **Set reasonable idle timeout** to clean up stale connections.

---

### **Issue 4: Third-Party API Timeouts**
**Symptoms:**
- Logs show `ConnectTimeoutException` or `SocketTimeoutException`.
- External service health checks fail.

**Root Causes:**
- **Slow external service** (high latency).
- **No circuit breaker** (app keeps retrying failed calls).
- **Timeout too short** (default 1-2s is often insufficient).

**Debugging Steps & Fixes:**
1. **Check API latency:**
   ```sh
   # Use curl with timeout
   curl -v -m 5 https://external-api.example.com
   ```
2. **Implement retries with backoff:**
   - **Resilience4j (Java):**
     ```java
     Retry retry = Retry.of("myRetry")
         .maxAttempts(3)
         .waitDuration(Duration.ofSeconds(1))
         .retryExceptions(TimeoutException.class);
     ```
   - **Spring Retry:**
     ```yaml
     spring:
       retry:
         max-attempts: 3
         backoff:
           initial-interval: 1000
           multiplier: 2
           max-interval: 5000
     ```
3. **Set realistic timeouts:**
   - **RestTemplate (Java):**
     ```java
     RestTemplate restTemplate = new RestTemplate();
     restTemplate.setConnectTimeout(5000); // 5s
     restTemplate.setReadTimeout(10000);   // 10s
     ```
4. **Use circuit breakers (Resilience4j):**
   ```java
   CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("externalApi");
   Supplier<Boolean> call = () -> externalApi.isAvailable();
   circuitBreaker.executeCallable(call);
   ```

**Preventive Measure:**
- **Mock external APIs in tests** (e.g., WireMock).
- **Monitor SLA compliance** (e.g., Prometheus alert on >99% success rate).

---

### **Issue 5: Load Balancer Dropping Requests**
**Symptoms:**
- 503/504 errors from NGINX, ALB, or cloud load balancer.
- Logs show `No healthy backends`.

**Root Causes:**
- **Pods not responding to health checks**.
- **Misconfigured load balancer health check path**.
- **Network policies blocking traffic**.

**Debugging Steps & Fixes:**
1. **Check health check endpoint:**
   ```sh
   curl -v http://<pod-ip>:<port>/health
   ```
   - If returning 500, fix the endpoint.
2. **Verify load balancer settings (e.g., ALB):**
   - Ensure `/health` path is monitored.
   - Check `HealthCheckPath` and `HealthyThreshold` in AWS ALB.
3. **Test connectivity from load balancer to pods:**
   ```sh
   # Get internal IP of ALB
   kubectl get svc <service-name> -o wide
   # Test from a pod (e.g., via nettop or curl)
   kubectl exec -it <pod> -- curl http://<alb-private-ip>:<port>/health
   ```
4. **Adjust health check timeout:**
   - Example (NGINX Ingress):
     ```yaml
     healthCheckNodePort: 30000
     timeoutSeconds: 5
     healthyThreshold: 2
     unhealthyThreshold: 3
     ```

**Preventive Measure:**
- **Use readiness probes** (not just liveness).
- **Test health endpoints in CI** (e.g., Postman collection).

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Purpose**                                                                 | **Example Command/Usage**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **kubectl logs/pods**  | Check pod logs for crashes/errors.                                          | `kubectl logs -l app=myapp --tail=50`             |
| **kube-top**           | Real-time CPU/memory per pod.                                               | `kubectl top pods`                                 |
| **Prometheus + Grafana** | Monitor metrics (latency, errors, scaling).                              | `http://grafana:3000/d/prometheus`                |
| **Netdata**            | Low-latency system monitoring (CPU, disk, network).                       | `curl http://localhost:19999/backend/api/v1/node` |
| **Wireshark/tcpdump**  | Check network issues (timeouts, packet loss).                              | `tcpdump -i eth0 -w capture.pcap`                  |
| **JVM Profiler (Async Profiler)** | Find CPU/memory bottlenecks in Java.                          | `./profiler.sh -d 30 -f flame.graph java -jar app.jar` |
| **Jaeger/Zipkin**      | Trace distributed requests (latency in microservices).                   | `http://jaeger:16686`                              |
| **Postman/Newman**     | Test API endpoints under load.                                             | `newman run test.postman_collection.json --iterations 100` |
| **Locust/Gatling**     | Simulate load to find bottlenecks.                                        | `locust -f load_test.py --host=http://localhost:8080` |

**Advanced Techniques:**
- **Distributed Tracing:** Use Jaeger to identify slow dependencies.
- **Chaos Engineering (Gremlin):** Inject failures to test resilience.
- **GameDay Testing:** Manually trigger scaling events (e.g., kill pods).

---

## **4. Prevention Strategies**

### **Best Practices for Availability**
1. **Infrastructure Resilience:**
   - **Multi-AZ/Region Deployments:** Avoid single points of failure.
   - **Pod Disruption Budgets (PDBs):** Ensure minimum pods running during upgrades.
   - **Database Replication:** Use read replicas for read-heavy workloads.

2. **Application Design:**
   - **Circuit Breakers:** Prevent cascading failures (Resilience4j, Hystrix).
   - **Retry with Jitter:** Avoid thundering herds (e.g., exponential backoff).
   - **Graceful Degradation:** Fail open/closed based on SLOs.

3. **Monitoring & Alerts:**
   - **SLO-Based Alerts:** Alert on error budgets (e.g., >1% error rate).
   - **Synthetic Monitoring:** Simulate user flows (e.g., Pingdom, Synthetic Grafana).
   - **Anomaly Detection:** Use ML (e.g., Prometheus Alertmanager + Cortex).

4. **Testing:**
   - **Load Testing:** Simulate 100-1000x production load (Locust, k6).
   - **Chaos Testing:** Kill random pods/nodes (Gremlin, Chaos Mesh).
   - **Chaos Engineering Postmortems:** Document what went wrong and why.

5. **Automated Recovery:**
   - **Self-Healing:** Use Kubernetes liveness probes + restart loops.
   - **Chaos Mesh:** Automate failover experiments.

---

## **5. Step-by-Step Debugging Workflow**

1. **Reproduce the Issue:**
   - Check logs (`kubectl logs`, application logs).
   - Recreate in staging with `locust` or manual load testing.

2. **Isolate the Component:**
   - Is it **infrastructure** (K8s, networking) or **application** (code, config)?
   - Use `kubectl describe pod` to check events.

3. **Check Metrics:**
   - CPU/memory (kube-top, Prometheus).
   - Latency (APM tools like Datadog, New Relic).
   - Dependency health (DB, external APIs).

4. **Apply Fixes:**
   - Adjust scaling (HPA, Cluster Autoscaler).
   - Fix connection leaks (pool sizing, resource limits).
   - Implement retries/circuit breakers.

5. **Verify & Rollback:**
   - Test locally before production.
   - Use blue-green deployments to minimize risk.

6. **Document & Prevent:**
   - Update runbooks for common failures.
   - Schedule regular chaos tests.

---

## **Conclusion**
Availability issues are often caused by misconfigured scaling, resource leaks, or unresilient dependencies. By following this structured debugging approach—**symptom analysis → root cause → fix → prevention**—you can quickly identify and resolve outages while building long-term resilience.

**Key Takeaways:**
- **Log everything** (application, infra, dependencies).
- **Test scaling manually** before relying on autoscale.
- **Use circuit breakers** to avoid cascading failures.
- **Monitor proactively** (not just reactively).

Happy debugging! 🚀