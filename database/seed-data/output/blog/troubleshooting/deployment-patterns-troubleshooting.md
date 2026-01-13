# **Debugging Deployment Patterns: A Troubleshooting Guide**

Deployment patterns ensure scalability, resilience, and maintainability of distributed systems. Common deployment patterns include:
- **Blue-Green Deployment**
- **Canary Releases**
- **Rolling Updates**
- **A/B Testing**
- **Feature Flags**
- **Shadow Deployments**
- **Micro Deployments (Blue/Green + Canary Hybrid)**

This guide focuses on diagnosing and resolving common issues related to these deployment strategies.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the issue by checking:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| **Traffic misrouted**                | Users experience inconsistent behavior (e.g., some see old vs. new features).   |
| **High error rates**                 | `5xx` errors spike post-deployment (e.g., database connection pool exhausted). |
| **Performance degradation**          | Latency increases, timeouts occur, or requests hang during rollout.             |
| **Inconsistent metrics**             | Monitoring shows uneven load distribution (e.g., 90% traffic to old version).    |
| **Rollback failures**                | Failed attempt to revert to a previous stable version.                           |
| **Resource exhaustion**              | High CPU/memory usage in new deployment pods/containers.                        |
| **Configuration drift**              | Environment mismatches (e.g., missing environment variables in canary traffic). |
| **Metric sampling issues**           | Missing or incorrect metrics (e.g., `request_count` not incrementing in canary). |

---

## **2. Common Issues and Fixes**

### **2.1. Traffic Misrouting (Blue-Green or Canary)**
**Symptom:**
Users intermittently see old vs. new versions of an app.

**Root Cause:**
- Incorrect traffic splitting (e.g., Istio/Gloo mismatch, ALB weight misconfiguration).
- DNS or CDN caching serving stale responses.
- Load balancer not respecting canary rules.

#### **Fixes:**
##### **A. Verify Traffic Splitting Logic**
- **Istio/Gloo/Linkerd:** Check `VirtualService` weights:
  ```yaml
  apiVersion: networking.istio.io/v1alpha3
  kind: VirtualService
  metadata:
    name: myapp
  spec:
    hosts:
    - myapp.example.com
    http:
    - route:
      - destination:
          host: myapp
          subset: v1  # 90% traffic
        weight: 90
      - destination:
          host: myapp
          subset: v2  # 10% canary
        weight: 10
  ```
  **Debug:** Use `kubectl describe virtualservice myapp` or Istio telemetry.

##### **B. Check Load Balancer Configuration**
- **AWS ALB/NLB:** Ensure `target-group-arns` are correctly weighted:
  ```bash
  aws elbv2 describe-target-groups --target-group-arns <ARN>
  ```
  **Fix:** Adjust weights via AWS Console or CLI:
  ```bash
  aws elbv2 modify-target-group-attributes --target-group-arn <ARN> --attribute Key=load_balancing.cross-zone.enabled,Value=true
  ```

##### **C. Flush DNS/CDN Caches**
- **Cloudflare:** Purge cache via API:
  ```bash
  curl -X POST "https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/purge_cache" \
    -H "Authorization: Bearer <TOKEN>" \
    -H "Content-Type: application/json" \
    --data '{"purge_everything":true}'
  ```
- **Cloud DNS:** Use `nsupdate` or cloud provider tools.

---

### **2.2. High Error Rates After Deployment**
**Symptom:**
Post-deployment, `5xx` errors spike (e.g., `ConnectionRefused`, `Timeout`).

**Root Cause:**
- Incompatible database schema versions.
- Missing dependencies or misconfigured services.
- Rate limiting or circuit breakers tripping.

#### **Fixes:**
##### **A. Check Database Schema Compatibility**
- **Migrations:** Ensure flyway/liquibase migrations are applied to all replicas:
  ```bash
  # Verify migration status
  psql -U <user> -d <db> -c "SELECT * FROM schema_version;"
  ```
  **Fix:** Roll back or re-run migrations if needed.

##### **B. Verify Service Dependencies**
- **Health probes:** Ensure readiness/liveness probes pass:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 5
    periodSeconds: 10
  ```
  **Debug:** Check pod events:
  ```bash
  kubectl describe pod <pod-name> | grep -i "failed"
  ```

##### **C. Review Circuit Breakers**
- **Resilience4j/Envoy:** Check failure rates:
  ```yaml
  # Envoy example (circuit_break)
  static_resources:
    listeners:
    - name: listener_0
      filter_chains:
      - filters:
        - name: envoy.filters.network.http_connection_manager
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
            route_config:
              virtual_hosts:
              - name: local_service
                routes:
                - match:
                    prefix: "/"
                  route:
                    cluster: my_service
                    timeout: 0.5s
                    max_connections: 1000
  ```
  **Debug:** Use Envoy statsd:
  ```bash
  curl http://localhost:9990/stats | grep circuit
  ```

---

### **2.3. Performance Degradation**
**Symptom:**
Latency increases, timeouts, or requests hang during rollout.

**Root Cause:**
- New version has higher resource usage.
- Network partitioning (e.g., pod affinity/anti-affinity issues).
- Cold starts (serverless/K8s).

#### **Fixes:**
##### **A. Monitor Resource Usage**
- **Kubernetes:** Check pod resource requests/limits:
  ```bash
  kubectl top pods --containers
  ```
  **Fix:** Adjust CPU/memory requests:
  ```yaml
  resources:
    requests:
      cpu: "500m"
      memory: "512Mi"
    limits:
      cpu: "1000m"
      memory: "1Gi"
  ```

##### **B. Optimize Networking**
- **Pod Affinity:** Ensure pods are co-located with dependencies:
  ```yaml
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - mysql
        topologyKey: "kubernetes.io/hostname"
  ```

##### **C. Mitigate Cold Starts**
- **Serverless (AWS Lambda):** Use provisioned concurrency.
- **K8s:** Use horizontal pod autoscaler (HPA) with scaling policies:
  ```yaml
  autoscaling:
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  ```

---

### **2.4. Rollback Failures**
**Symptom:**
Unable to revert to a previous stable version.

**Root Cause:**
- Stale traffic routing (e.g., CDN still serving new version).
- Database inconsistencies (e.g., uncommitted transactions).
- Lock contention (e.g., feature flags not updated).

#### **Fixes:**
##### **A. Force-Traffic Redirection**
- **Istio:** Update `VirtualService` weights to 100% old version:
  ```yaml
  http:
  - route:
    - destination:
        host: myapp
        subset: v1
      weight: 100
  ```
  **Apply:** `kubectl apply -f vs-rollback.yaml`

##### **B. Clean Database State**
- **PostgreSQL:** Run `pg_rewind` to sync replicas:
  ```bash
  pg_rewind --stop-after=master --verbose /path/to/replica /path/to/master
  ```
- **MongoDB:** Use `mongodump/mongorestore` to reset.

##### **C. Reset Feature Flags**
- **LaunchDarkly/Unleash:** Disable flag via API:
  ```bash
  curl -X PUT "https://app.launchdarkly.com/api/v2/flags/<FLAG_ID>/toggle" \
    -H "Authorization: Bearer <TOKEN>" \
    -d '{"variation":0}'
  ```

---

### **2.5. Resource Exhaustion**
**Symptom:**
Pods crash due to OOM or CPU throttling.

**Root Cause:**
- Over-provisioned resources in new deployment.
- Memory leaks or inefficient code paths.

#### **Fixes:**
##### **A. Adjust Resource Limits**
- **K8s:** Increase limits or use `LimitRange`:
  ```yaml
  # LimitRange example
  apiVersion: v1
  kind: LimitRange
  metadata:
    name: mem-limit-range
  spec:
    limits:
    - default:
        memory: 1Gi
      defaultRequest:
        memory: 512Mi
      type: Container
  ```

##### **B. Profile Memory Usage**
- **Java:** Use `jcmd` to print heap:
  ```bash
  jcmd <PID> GC.heap_info
  ```
- **Go:** Use `pprof`:
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/heap
  ```

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command/Integration**                              |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------|
| **Istio Telemetry**    | Verify traffic routing, latency, error rates.                               | `kubectl port-forward svc/istio-ingressgateway 8080:80`       |
| **Prometheus/Grafana** | Monitor custom metrics (e.g., `request_latency`, `error_rate`).            | `curl http://<prometheus>:9090/api/v1/query?query=error_rate` |
| **Kiali**              | Visualize service mesh topology and traffic flow.                          | Access via `http://<kiali-ingress>:20001`                   |
| **AWS CloudWatch**     | Logs and metrics for AWS deployments (e.g., ALB, ECS).                      | `aws logs get-log-events --log-group-name /ecs/myapp`        |
| **JMeter/Gatling**     | Simulate canary traffic to detect issues before full rollout.              | `jmeter -n -t test.jmx -l results.jtl`                       |
| **Chaos Mesh**         | Inject failures (e.g., pod kills) to test resilience.                       | `kubectl apply -f chaos.yaml` (e.g., `podkill` experiment)     |
| **New Relic/Dynatrace**| APM for deep code-level debugging (e.g., slow DB queries).                  | Filter traces by `deployment.version: v2`                     |
| **kubectl debug**      | Debug running pods interactively.                                           | `kubectl debug -it <pod> --image=busybox`                    |
| **Terraform Destroy**  | Roll back infrastructure (last resort).                                     | `terraform destroy -auto-approve`                            |

---

## **4. Prevention Strategies**

### **4.1. Automated Canary Analysis**
- Use **SLOs (Service Level Objectives)** to auto-block deployments if errors exceed thresholds.
  **Example (Prometheus Alert Rule):**
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate in {{ $labels.instance }}"
  ```

### **4.2. Progressive Delivery Pipelines**
- **Argo Rollouts:** Gradually roll out changes with step-by-step canary analysis.
  ```yaml
  apiVersion: argoproj.io/v1alpha1
  kind: Rollout
  metadata:
    name: myapp
  spec:
    strategy:
      canary:
        steps:
        - setWeight: 20
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
        - setWeight: 80
  ```

### **4.3. Feature Flag Best Practices**
- **Avoid hardcoded flags:** Use dynamic configuration (e.g., Spring Cloud Config, Consul).
  ```java
  // Spring Boot example
  @Value("${feature.new_ui.enabled:false}")
  private boolean newUiEnabled;
  ```
- **Rollback via flags:** Disable flags to revert immediately.

### **4.4. Infrastructure as Code (IaC)**
- **Terraform/CloudFormation:** Enforce consistent deployments.
  ```hcl
  resource "aws_ecs_service" "myapp" {
    launch_type = "FARGATE"
    task_definition = aws_ecs_task_definition.myapp.arn
    desired_count  = 2
    network_configuration {
      subnets          = [aws_subnet.app.arn]
      security_groups  = [aws_security_group.app.arn]
    }
  }
  ```

### **4.5. Chaos Engineering**
- **Run failure scenarios** in staging (e.g., network partitions, pod kills).
  ```bash
  # Kill pods randomly (Chaos Mesh)
  kubectl apply -f - <<EOF
  apiVersion: chaos-mesh.org/v1alpha1
  kind: PodChaos
  metadata:
    name: pod-kill
  spec:
    action: pod-kill
    mode: one
    selector:
      namespaces:
        - default
  EOF
  ```

### **4.6. Observability First**
- **Log Correlation:** Use `trace_id` or `request_id` across services.
  ```yaml
  # OpenTelemetry example
  tracing:
    sampler: "parentbased_always_on"
    exporter:
      otlp:
        endpoint: "otel-collector:4317"
  ```
- **Alerting:** Set up alerts for:
  - **Traffic skew** (e.g., `istio_requests_total{destination.version=v2}` < 10%).
  - **Database pressure** (e.g., `postgresql_up` drops below 99%).
  - **Canary health** (e.g., `http_requests_total{version=v2, status=~"5.."}` > 0).

---

## **5. Quick Resolution Cheat Sheet**
| **Issue**               | **Immediate Fix**                          | **Long-Term Fix**                          |
|--------------------------|--------------------------------------------|--------------------------------------------|
| Traffic misrouted        | Update `VirtualService` weights            | Use Istio/Gloo traffic splits + testing   |
| High error rates         | Rollback via `kubectl rollout undo`        | Add circuit breakers + SLOs                |
| Performance degradation  | Scale up pods or optimize queries         | Profile with `pprof` + refine DB queries   |
| Rollback failure         | Force-traffic to old version + DB sync    | Automate rollback via feature flags        |
| Resource exhaustion      | Kill pods + increase limits                | Right-size containers + monitor memory     |
| Inconsistent metrics     | Verify Prometheus scraping                  | Use OpenTelemetry for distributed tracing  |

---

## **Conclusion**
Debugging deployment patterns requires a mix of **observability tools**, **traffic control validation**, and **automated rollback mechanisms**. Focus on:
1. **Traffic routing accuracy** (Istio/VirtualService weights, ALB configurations).
2. **Dependency compatibility** (database schemas, service health).
3. **Resource constraints** (CPU/memory limits, profiling).
4. **Automation** (SLOs, progressive delivery, chaos testing).

By following this guide, you can quickly diagnose and resolve deployment issues while minimizing downtime. For complex issues, **reproduce in staging first** using identical environments.