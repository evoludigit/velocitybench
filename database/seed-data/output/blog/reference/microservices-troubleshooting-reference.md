# **[Pattern] Microservices Troubleshooting – Reference Guide**

---

## **Overview**
Microservices architectures offer scalability and modularity but introduce complexity in observability, latency, and dependency management. This pattern provides a structured approach to diagnosing and resolving issues in distributed systems by breaking troubleshooting into **logical phases**: **Detection → Isolation → Diagnostics → Resolution**. It leverages tools, telemetry data, and systematic workflows to minimize downtime and improve reliability. Key focus areas include **distributed tracing**, **metrics correlation**, **circuit breaking**, and **log aggregation**, ensuring efficient root-cause analysis across service boundaries.

---

## **Schema Reference**

| **Phase**         | **Objective**                                                                 | **Key Artifacts**                                                                 | **Tools/Technologies**                                                                                     |
|-------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Detection**     | Identify anomalies in system behavior.                                       | Alerts, error rates, latency spikes, SLO violations.                               | Prometheus, Grafana, Datadog, ELK Stack, PagerDuty.                                                  |
| **Isolation**     | Narrow down the affected component(s) from the broader system.               | Request flows, service dependencies, correlation IDs, context logs.             | Jaeger, Zipkin, OpenTelemetry, Kubernetes Events, API Gateway logs.                                  |
| **Diagnostics**   | Analyze symptoms to determine root cause.                                    | Logs, traces, metrics, config changes, rollback history.                          | Splunk, New Relic, Chaos Mesh, Postmortem tools (e.g., Blameless).                                   |
| **Resolution**    | Implement fixes and validate remediation.                                    | Deploy patches, adjust thresholds, enable retries, update circuit breakers.      | CI/CD pipelines (GitLab CI, ArgoCD), Feature flags (LaunchDarkly), Canary releases.                     |
| **Postmortem**    | Document lessons learned and prevent recurrence.                             | Root cause analysis (RCA) reports, technical debt log, SLO improvements.         | Confluence, Github Issues, Blameless postmortem templates.                                             |

---

## **Implementation Details**

### **1. Detection: Proactive Monitoring**
Microservices require **multi-dimensional telemetry** (metrics, logs, traces) to detect issues early.

#### **Critical Metrics to Monitor**
| **Metric Type**        | **Examples**                                                                                     | **Tools for Collection**                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Performance**        | Latency (P99, P95, avg), Throughput (RPS), Error rates (5xx), GC pauses.                        | Prometheus (via Kubernetes `metrics-server`), Datadog APM, Lightstep.                  |
| **Resource Usage**     | CPU, Memory, Disk I/O (pod/container level), Network bandwidth.                               | cAdvisor, Kubernetes metrics-server, Datadog Infrastructure Monitoring.                |
| **Dependency Health**  | Inter-service latency, call rate, failure rate (e.g., `payment-service` → `inventory-service`). | OpenTelemetry AutoInstrumentation, Distributed Tracing (Jaeger).                         |
| **Business KPIs**      | Conversion rates, checkout success/failure, payment processing time.                           | Custom dashboards (Grafana), Business Intelligence tools (e.g., Amplitude for events).  |

#### **Alerting Strategies**
- **Threshold-based alerts**: Trigger on `error_rate > 1%` or `latency > 500ms` (adjust per SLO).
- **Anomaly detection**: Use ML-driven tools (e.g., Prometheus Anomaly Detection) to flag unexpected patterns.
- **Multi-channel alerts**: Escalate from Slack → PagerDuty → On-call engineers based on severity.

**Example Alert Rule (Prometheus):**
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "High error rate in {{ $labels.service }}"
    description: "{{ $labels.service }} has 1%+ errors over 5 mins."
```

---

### **2. Isolation: Tracing and Dependency Mapping**
Isolate issues using **distributed tracing** and **service dependency graphs**.

#### **Distributed Tracing Workflow**
1. **Inject correlation IDs**: Propagate unique IDs across service calls (e.g., `X-Correlation-ID` header) to link logs/traces.
2. **Capture spans**: Record latency, errors, and sub-operations (e.g., DB queries, external API calls) per trace.
3. **Visualize chains**: Use tools like Jaeger or Zipkin to reconstruct request flows (e.g., `user-service` → `auth-service` → `payment-service`).

**Example Trace (Jaeger UI):**
```
user-service (latency: 200ms) → auth-service (latency: 150ms, error: 401) → payment-service (latency: 800ms)
```

#### **Dependency Mapping**
- **Static graphs**: Use Kubernetes manifests or service registries (e.g., Consul) to map service dependencies.
- **Dynamic graphs**: Tools like **Grafana Mimir** or **Datadog Service Maps** update in real-time.

**Tool Command (Kubernetes `kubectl`):**
```bash
kubectl get endpoints -A  # List service endpoints
```

---

### **3. Diagnostics: Root Cause Analysis**
Correlate data from **logs**, **traces**, and **metrics** to pinpoint issues.

#### **Common Symptoms & Root Causes**
| **Symptom**                          | **Possible Root Causes**                                                                                     | **Diagnostic Steps**                                                                                     |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **High Latency**                     | Slow DB queries, cold starts (serverless), network saturation.                                            | Check trace spans (e.g., `db.query` duration), monitor network metrics (`kubelet` bandwidth).          |
| **5xx Errors**                       | Timeouts (e.g., `payment-service` unreachable), validation failures, race conditions.                     | Review error logs, trace failed requests, audit service configuration (e.g., `timeout` settings).     |
| **Cascading Failures**               | Noisy neighbor problem (e.g., one pod consuming all CPU), circuit breaker thresholds too high.           | Enable retry policies, adjust circuit breaker thresholds (Hystrix, Resilience4j).                      |
| **Resource Starvation**              | Memory leaks, unmanaged containers, or misconfigured Horizontal Pod Autoscaler (HPA).                   | Use `kubectl top pods`, check container logs for `OutOfMemoryError`.                                   |
| **Configuration Drift**              | Misaligned configs between environments (dev/prod), missing secrets.                                    | Compare configs with `kubectl diff`, use GitOps (ArgoCD/Flux) for auditing.                            |

#### **Log Analysis**
- **Structured logging**: Use JSON format with `context_id` and `trace_id` for easier correlation.
  ```json
  {
    "timestamp": "2023-10-01T12:00:00Z",
    "level": "ERROR",
    "service": "payment-service",
    "trace_id": "abc123",
    "error": "Payment gateway timeout",
    "details": { "attempts": 3, "retry_delay": "5s" }
  }
  ```
- **Log aggregation**: Use ELK Stack, Loki, or Datadog for cross-service log search.
  **Example Query (Grafana Loki):**
  ```
  {service="payment-service"} | json | error="timeout"
  ```

---

### **4. Resolution: Fixes and Validation**
Apply fixes based on RCA findings and validate using **canary releases** or **feature flags**.

#### **Common Fixes**
| **Issue**               | **Mitigation Strategy**                                                                                  | **Validation Steps**                                                                                     |
|-------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Timeouts**            | Increase timeout thresholds, implement retries with exponential backoff.                             | Test with chaos engineering (e.g., kill `payment-service` pods for 30s).                              |
| **Database Bottlenecks**| Add read replicas, optimize queries, cache frequent calls (Redis).                                     | Monitor DB metrics (`pg_stat_activity`, Prometheus `postgres_up`).                                      |
| **Circuit Breaker Open**| Lower threshold (e.g., `failure_rate = 30%`), enable fallback responses.                               | Simulate failures in staging (e.g., `Chaos Mesh` pod kill).                                           |
| **Dependency Failures** | Decouple services with async messaging (Kafka, RabbitMQ), implement idempotency.                      | Verify event consumption with Kafka Consumer Lag metrics.                                              |

#### **Post-Fix Validation**
- **Automated tests**: Run integration tests (e.g., Postman/Newman) against the fixed service.
- **Gradual rollout**: Use canary deployments (e.g., Istio traffic shifting) to monitor impact.
  **Example Istio Rule:**
  ```yaml
  apiVersion: networking.istio.io/v1alpha3
  kind: VirtualService
  metadata:
    name: payment-service
  spec:
    hosts:
    - payment-service
    http:
    - route:
      - destination:
          host: payment-service
          subset: v2
        weight: 10
      - destination:
          host: payment-service
          subset: v1
        weight: 90
  ```

---

### **5. Postmortem: Document and Improve**
Standardize postmortem processes to avoid recurrence.

#### **Template for Root Cause Analysis**
1. **Timeline**: When did the issue start? Key events (e.g., "Deployed v2 of `auth-service` at 14:30").
2. **Impact**: Scope (e.g., "Checkout failures for 30 mins").
3. **Detailed Analysis**:
   - Root cause (e.g., "New DB schema migration caused schema mismatch").
   - Symptoms (traces, logs, metrics).
   - Fix applied (e.g., rolled back schema, adjusted retry logic).
4. **Action Items**:
   - Short-term (e.g., add DB schema validation in CI).
   - Long-term (e.g., implement automated canary analysis).
5. **Ownership**: Assign engineers to track fixes.

**Tool**: Use [Blameless postmortem templates](https://blameless.com/postmortems) or Jira tickets to document findings.

---

## **Query Examples**

### **1. Detecting Latency Spikes (PromQL)**
```promql
# Latency > 500ms for past 5 mins
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))
> 0.5
```

### **2. Finding Failed Requests (ELK Query)**
```elasticsearch
# Logs with status 5xx in payment-service
service:payment-service AND status:"5.."
| stats count by status
| sort -count
```

### **3. Tracing a Specific Correlation ID (Jaeger CLI)**
```bash
# Filter traces by correlation ID
jaeger query --service payment-service --tags key="correlation_id,value:<ID>"
```

### **4. Kubernetes Pod Resource Usage**
```bash
# Check CPU/memory usage for a pod
kubectl top pod -l app=payment-service --containers
```

### **5. Dependency Graph (K8s + Grafana)**
```bash
# Export service dependencies as dot graph
kubectl get svc -A -o json | jq -r '... | select(.kind == "Service") | "\(.metadata.namespace)/\(.metadata.name) -> \(.spec.ports[0].port)"' > deps.dot
```

---

## **Related Patterns**
1. **[Resilience Patterns](https://microservices.io/patterns/resilience.html)**
   - Use **circuit breakers**, **retries**, and **bulkheads** to handle failures gracefully.
   - *Tools*: Resilience4j, Hystrix, Spring Retry.

2. **[Observability Patterns](https:// patterns.observability.dev/)**
   - Implement **distributed tracing**, **metrics**, and **logs** for end-to-end visibility.
   - *Tools*: OpenTelemetry, Prometheus, Loki.

3. **[Chaos Engineering](https://chaosengineering.io/)**
   - Proactively test resilience by injecting failures (e.g., network partitions, pod kills).
   - *Tools*: Chaos Mesh, Gremlin, Netflix Simian Army.

4. **[Service Mesh Patterns](https://www.istio.io/latest/docs/concepts/traffic-management/)**
   - Use **Istio** or **Linkerd** for advanced traffic control, observability, and security.
   - *Example*: mTLS for service-to-service encryption.

5. **[Canary Releases](https://martinfowler.com/bliki/CanaryRelease.html)**
   - Gradually roll out changes to detect issues early.
   - *Tools*: Argo Rollouts, Istio, Flagger.

6. **[Event-Driven Architecture](https://microservices.io/patterns/data/event-driven-architectures.html)**
   - Decouple services using events (e.g., Kafka) to isolate failures.
   - *Tools*: Apache Kafka, NATS, RabbitMQ.

---

## **Anti-Patterns to Avoid**
1. **Log Spam**: Avoid noisy logs without structured context (e.g., `DEBUG: User logged in` → use `INFO: User login successful, user_id:123, trace_id:abc`).
2. **Ignoring Distributed Context**: Don’t treat microservices as monoliths—always trace cross-service flows.
3. **Over-Reliance on Alert Fatigue**: Prioritize alerts based on SLOs (e.g., ignore `404` errors if they don’t impact business).
4. **Silos in Teams**: Encourage cross-service ownership (e.g., SREs collaborate with frontend teams for end-to-end SLAs).
5. **No Postmortem Culture**: Failures are learning opportunities—document and share lessons.

---
**Key Takeaway**: Microservices troubleshooting requires **systemic observability** and **collaboration**. By standardizing detection, isolation, diagnostics, and resolution workflows, teams can reduce MTTR (Mean Time to Resolution) and build resilient systems. Start with **traces + metrics + logs**, then iterate based on RCA findings.