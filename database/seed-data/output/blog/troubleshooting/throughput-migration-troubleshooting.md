# **Debugging Throughput Migration: A Troubleshooting Guide**
*For high-throughput microservices, distributed systems, or legacy-to-modern migrations*

---

## **Introduction**
The **Throughput Migration** pattern involves scaling a system by migrating workloads gradually to new infrastructure while maintaining service availability, minimizing downtime, and ensuring high throughput. This is commonly used in:
- Microservices refactoring
- Cloud migrations (monolith → serverless/k8s)
- Legacy system upgrades
- Auto-scaling adjustments

If throughput degrades, latency spikes, or errors increase post-migration, this guide helps diagnose root causes efficiently.

---

## **1. Symptom Checklist**
Check for these signs of throughput migration issues:

| Symptom | Impacted Metrics |
|---------|------------------|
| ✅ **Increased latency** (e.g., 95th percentile response time > 500ms) | `p99_latency`, `avg_latency` |
| ✅ **Error rates rise** (e.g., 5XX errors > 1%) | `error_rate`, `throttles_rejected` |
| ✅ **Throughput drops** (requests/sec < baseline) | `rps`, `qps` |
| ✅ **Resource contention** (CPU/memory spikes) | `cpu_utilization`, `memory_pressure`, `disk_io` |
| ✅ **Cold starts or slow scaling** (during traffic spikes) | `cold_start_rates`, `scale_delay` |
| ✅ **Database stalls** (timeouts or retries) | `db_query_latency`, `retry_attempts` |
| ✅ **Circuit-breaker trips** (e.g., Hystrix, Resilience4j) | `circuit_open_time`, `fallback_invoked` |
| ✅ **Log spikes** (unexpected errors, GC pauses) | `error_logs`, `GC_latency` |

**Tools to Monitor:**
- Prometheus + Grafana (latency, error rates)
- Datadog/New Relic (distributed tracing)
- Spring Boot Actuator (for Java apps)
- AWS CloudWatch/GCP Stackdriver (cloud metrics)

---

## **2. Common Issues & Fixes**
### **Problem 1: Gradual Migration Causes Load Imbalance**
When migrating traffic from `OldService` → `NewService`, uneven distribution leads to bottlenecks.

#### **Symptoms:**
- `NewService` CPU hits 90%, `OldService` is underutilized.
- Latency spikes when `NewService` is hit with too much traffic.

#### **Fixes:**
**A. Adjust Traffic Routing (Canary Release)**
```yaml
# Example: Istio VirtualService for gradual rollout
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
    - my-service.internal
  http:
    - route:
        - destination:
            host: old-service
            subset: v1
          weight: 90  # 90% to old, 10% to new
        - destination:
            host: new-service
            subset: v2
          weight: 10
```
- **Monitor**: Check `istio_requests_total` per service in Prometheus.

**B. Use a Migration Tool**
- **AWS ALB**: Trailhead’s [Canary Deployment Guide](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/elb-canary-deployments.html)
- **Kubernetes**: Gradual `kubectl set image` + `kubectl apply -f` with `podDisruptionBudget`.

---

### **Problem 2: Database Migrations Introduce Latency**
If migrating data to a new DB (e.g., Aurora → MongoDB), schema changes or sync delays hurt performance.

#### **Symptoms:**
- `SELECT` queries time out.
- Replication lag > 1s.

#### **Fixes:**
**A. Dual-Write Pattern (Temporarily)**
```java
// Example: Spring Data JPA + MongoDB dual-write
@Transactional
public void saveUser(User user) {
    userRepository.save(user); // Primary DB
    mongoTemplate.save(user, "users"); // Secondary DB
}
```
- **Monitor**: Track `replication_lag_seconds` in Prometheus.

**B. Batch Migrations**
```bash
# Example: AWS DMS for schema migration
aws dms start-replication-task \
    --replication-task-arn <arn> \
    --start-replication-task-type start-replicating
```
- **Fix**: Increase `batch_size` or parallelize migrations.

---

### **Problem 3: Auto-Scaling Misconfiguration**
New service scales too slowly/slowly during traffic spikes.

#### **Symptoms:**
- `scale_up_delay` > 30s.
- `request_rejection_rate` increases.

#### **Fixes:**
**A. Adjust Kubernetes HPA (Horizontal Pod Autoscaler)**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: new-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: new-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External
      external:
        metric:
          name: requests_per_second
          selector:
            matchLabels:
              app: new-service
        target:
          type: AverageValue
          averageValue: 1000  # Scale up at 1K rps
```
- **Fix**: Reduce `scale_down_delay_seconds` to 60s.

**B. Pre-Warm Pods (for Serverless)**
```bash
# AWS Lambda: Provisioned Concurrency
aws lambda put-provisioned-concurrency-config \
    --function-name NewService \
    --qualifier $LATEST \
    --provisioned-concurrent-executions 20
```

---

### **Problem 4: Cold Starts (Cloud Functions)**
New service (e.g., AWS Lambda) is slow on first request.

#### **Symptoms:**
- `cold_start_latency` > 1s.
- Latency spikes at midnight (lower traffic).

#### **Fixes:**
**A. Enable Provisioned Concurrency**
```python
# AWS Lambda Python Handler (warm-up)
def lambda_handler(event, context):
    # Warm-up code (optional)
    if "warmup" in event.get("queryStringParameters", {}):
        do_warmup_work()
    ...
```
- **Monitor**: `Invocations` vs. `Cold Starts` in CloudWatch.

**B. Use a Lightweight Runtime**
- Switch from Python to **Go** or **Node.js** for faster cold starts.

---

### **Problem 5: Circuit Breaker Trips**
New service fails under load, causing retries that overload the system.

#### **Symptoms:**
- `circuit_open_time` > 30s.
- `fallback_invoked` > 10%.

#### **Fixes:**
**A. Resilience4j (Java Example)**
```java
@Bean
public Resilience4jCircuitBreakerFactory circuitBreakerFactory() {
    return Resilience4jCircuitBreakerFactory.ofDefaults();
}

@CircuitBreaker(name = "paymentService")
public String callPaymentService() {
    // Fallback logic
    return "fallback";
}
```
- **Tune thresholds**:
  ```yaml
  spring:
    resilience4j:
      circuitbreaker:
        instances:
          paymentService:
            failureRateThreshold: 50  # Trip at 50% errors
            waitDurationInOpenState: 30s
  ```

**B. Retry with Backoff**
```java
@Retry(name = "paymentRetry", maxAttempts = 3)
@Backoff(delay = 1000, multiplier = 2)
public String callPaymentService() {
    return RestTemplate.getForObject(...);
}
```

---

## **3. Debugging Tools & Techniques**
| Tool/Technique | Use Case |
|---------------|----------|
| **Distributed Tracing (Jaeger/Zipkin)** | Identify latency bottlenecks in microservices. |
| **Load Testing (Locust/k6)** | Simulate migration traffic before full rollout. |
| **APM (New Relic/Datadog)** | Track end-to-end transactions. |
| **CPU Profiler (pprof)** | Find CPU-hogging methods in Java. |
| **Database Exporter (Prometheus DB Exporter)** | Monitor DB query performance. |
| **Chaos Engineering (Gremlin)** | Test system resilience during migration. |
| **Log Aggregation (ELK Stack)** | Filter errors by `old-service` vs `new-service`. |

**Example Workflow:**
1. **Step 1**: Start load test with `locust` (simulate 10K RPS).
2. **Step 2**: Check `zipkin` traces for slow calls.
3. **Step 3**: Profiles `new-service` with `pprof`:
   ```bash
   go tool pprof http://localhost:8080/debug/pprof/profile
   ```

---

## **4. Prevention Strategies**
1. **Pre-Migration:**
   - Run **load tests** with 120% of expected traffic.
   - **Canary deploy** with 5% traffic first.
   - **Chaos test** (kill random pods to simulate failure).

2. **During Migration:**
   - **Monitor dual-write consistency** (e.g., Kafka events for orders).
   - **Set up alerts** for:
     ```yaml
     # Prometheus Alert Rule
     - alert: ThroughputDrop
       expr: rate(http_requests_total[1m]) < 0.9 * on() rate(http_requests_total[1m]) offset 1h
       for: 5m
       labels:
         severity: critical
     ```

3. **Post-Migration:**
   - **Phased rollback**: Redirect 100% → 90% → 80% if errors rise.
   - **Document thresholds** (e.g., "If `p99 > 1s`, roll back").

---

## **5. Quick Reference Table**
| Issue | Immediate Fix | Long-Term Fix |
|-------|--------------|---------------|
| **Load imbalance** | Adjust Istio weights/K8s HPA | Use service mesh (Linkerd/Envoy) |
| **DB lag** | Dual-write + batch sync | Migrate to managed DB (Aurora) |
| **Auto-scaling slow** | Pre-warm pods | Optimize JVM warmup/GPU scheduling |
| **Cold starts** | Provisioned concurrency | Use lighter runtime (Go) |
| **Circuit breaker trips** | Increase timeout | Implement chaos testing |

---

## **Conclusion**
Throughput migration failures often stem from **uneven traffic distribution**, **database lag**, or **scaling misconfigurations**. Use:
1. **Gradual rollouts** (canary/blue-green).
2. **Real-time monitoring** (Prometheus + APM).
3. **Chaos testing** before full cutover.

**Final Checklist Before Migration:**
✅ Load test with 150% traffic.
✅ Set up alerts for `latency`/`error_rate`.
✅ Document rollback plan.
✅ Pre-warm critical services.

By following this guide, you can resolve throughput migration issues in **<1 hour** for most cases. For persistent issues, deep-dive into:
- **Network latency** (VPC peering, MTU issues).
- **GC pauses** (Java tuning with `-Xmx`).
- **Database schema changes** (indexes, partitioning).