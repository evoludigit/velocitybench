# **Debugging Containers Observability: A Troubleshooting Guide**

## **Introduction**
Containers Observability ensures you can monitor, log, and trace containerized applications effectively, providing insights into performance, errors, and dependencies. When issues arise—such as missing logs, slow performance, or failed instrumentation—debugging can be challenging without the right approach.

This guide provides a **structured, actionable** troubleshooting process for diagnosing and resolving common **Containers Observability** problems.

---

## **1. Symptom Checklist**
Before diving into fixes, **categorize the issue** based on these common symptoms:

| **Category**               | **Symptoms**                                                                 | **Likely Cause**                          |
|----------------------------|------------------------------------------------------------------------------|-------------------------------------------|
| **Missing/Incomplete Logs** | Logs not appearing in central log aggregation (ELK, Loki, Cloud Logging)    | Misconfigured log forwarding, permission issues, or agent failures |
| **Slow/Stuck Traces**      | Distributed tracing (e.g., Jaeger, OpenTelemetry) shows delayed or incomplete spans | Instrumentation errors, sampling issues, or network latency |
| **High Resource Usage**    | Containers consuming excessive CPU/memory due to observability overhead      | Misconfigured metrics collection, high sampling rate, or agent inefficiencies |
| **Failed Instrumentation** | Application crashes or fails to emit metrics/logs/traces                    | Incorrect SDK usage, missing tags, or build errors |
| **Alert Fatigue**          | Too many false positives in monitoring alerts                               | Misconfigured thresholds, noisy metrics, or incorrect alert rules |
| **Data Corruption/Inconsistency** | Mismatched logs, metrics, and traces (e.g., missing request IDs)          | Improper correlation IDs, broken sidecars, or broken middleware |

---

## **2. Common Issues & Fixes (with Code Examples)**

### **2.1 Missing/Incomplete Logs**
**Symptoms:**
- No logs in central log storage.
- Logs appear delayed or truncated.
- Docker/Kubernetes logs (`docker logs`, `kubectl logs`) show no output.

**Root Causes & Fixes:**

#### **A. Log Forwarding Agent Issues (Fluentd, Fluent Bit, Loki)**
- **Problem:** Agent fails to ship logs to the destination.
- **Diagnosis:**
  ```sh
  # Check Fluentd/Fluent Bit logs
  docker logs <log-forwarding-container>

  # Verify config file syntax
  fluent-bit test --config /path/to/config.conf
  ```
- **Fix:**
  ```yaml
  # Example Fluent Bit config (correct ownership & permissions)
  [INPUT]
      Name              tail
      Path              /var/log/containers/*.log
      Parser            docker
      Tag               kube.*
      Refresh_Interval  10

  [OUTPUT]
      Name              es
      Host              elasticsearch
      Port              9200
      Index             fluent-bit
      Replace_D Downstream_Failure_On_First_Error  On_First_Error
      Retry_Wait        1
      Retry_Limit       false
  ```
  **Common Errors & Fixes:**
  - **Permission denied?** Ensure the container has access to host logs (`/var/log/containers`).
  - **Syntax error?** Validate config with `fluent-bit test`.
  - **Network issue?** Check if the output host (ES, Loki) is reachable.

#### **B. Application Logs Not Emitted**
- **Problem:** Application logs to `STDOUT`/`STDERR`, but logs are not captured.
- **Diagnosis:**
  ```sh
  # Check if logs are written to stdout
  docker exec -it <container> cat /var/log/app.log  # If app logs to file
  journalctl -u <k8s-service>  # For Kubernetes
  ```
- **Fix:**
  - **For Docker:** Ensure logging driver is set:
    ```sh
    docker run --log-driver=json-file --log-opt max-size=10m my-app
    ```
  - **For Kubernetes:** Use `stdout`/`stderr` logging:
    ```yaml
    containers:
    - name: my-app
      image: my-app
      # Output logs to stdout/stderr automatically
    ```

---

### **2.2 Slow/Stuck Distributed Traces**
**Symptoms:**
- Traces appear incomplete (missing spans).
- High latency in tracing backend (Jaeger, Zipkin).
- OpenTelemetry SDK crashes due to instrumentation errors.

**Root Causes & Fixes:**

#### **A. Sampling Misconfiguration**
- **Problem:** Too few samples lead to incomplete traces.
- **Fix (OpenTelemetry):**
  ```python
  # Set explicit sampling rate (e.g., 10% for prod)
  sampler = SamplingSampler(
      SamplerType.RATE,
      sampling_rate=0.1
  )
  tracer = TracerProvider(sampler=sampler).tracer_provider
  ```
  **Kubernetes Example (Sidecar Injection):**
  ```yaml
  apiVersion: v1
  kind: ConfigMap
  metadata:
    name: opentelemetry-config
  data:
    sampler: "parentbased_always_on"
  ```

#### **B. Instrumentation Errors**
- **Problem:** SDK fails to export traces.
- **Diagnosis:**
  ```sh
  # Check OpenTelemetry logs for export errors
  docker logs <otel-collector>
  ```
- **Fix:**
  ```python
  # Explicitly enable batch export
  exporter = BatchSpanExporter(
      endpoint="http://jaeger-collector:4317",
      timeout=5.0
  )
  tracer_provider.add_span_processor(
      SimpleSpanProcessor(exporter)
  )
  ```

#### **C. Network Latency**
- **Problem:** Collector/jaeger-agent overwhelmed.
- **Fix:**
  - **Scale Jaeger:** Increase collector replicas in Kubernetes.
  - **Use gRPC instead of HTTP** for lower overhead:
    ```yaml
    # Jaeger config (use gRPC)
    collector:
      otlp:
        enabled: true
        grpc:
          endpoint: 0.0.0.0:4317
    ```

---

### **2.3 High Resource Usage by Observability**
**Symptoms:**
- Containers OOM-killed due to high memory usage.
- CPU throttling from excessive tracing.

**Root Causes & Fixes:**

#### **A. Unbounded Metrics Collection**
- **Problem:** Prometheus scrapes too many metrics.
- **Fix:**
  - **Use relabeling** to filter metrics:
    ```yaml
    - relabel_configs:
      - source_labels: [__name__]
        regex: 'container_network_transmit_errors'
        action: drop
    ```
  - **Set resource limits** on collectors:
    ```yaml
    resources:
      limits:
        cpu: "500m"
        memory: "512Mi"
    ```

#### **B. Overhead from Sidecar Agents**
- **Problem:** Sidecar (e.g., OpenTelemetry Collector) consumes too many resources.
- **Fix:**
  - **Adjust resource requests/limits in Kubernetes:**
    ```yaml
    containers:
    - name: otel-collector
      resources:
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "500m"
          memory: "512Mi"
    ```

---

## **3. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **Docker/K8s Logs**    | Check raw container logs                                                   | `docker logs <container>` / `kubectl logs <pod>` |
| **Fluent Bit/Test**    | Validate log forwarding config                                             | `fluent-bit test --config /etc/fluent-bit/fluent-bit.conf` |
| **OpenTelemetry Debug**| Inspect trace generation in app                                             | `OTEL_PYTHON_TRACES_ENABLED=true python app.py` |
| **Prometheus Debug**   | Check metrics collection issues                                            | `promtool check config /etc/prometheus/prometheus.yml` |
| **Jaeger/K8s Probe**   | Verify trace ingestion                                                      | `kubectl exec -it jaeger-query -- curl http://localhost:16686` |
| **eBPF (Cilium, Pixie)** | Low-overhead tracing/metrics in-cluster                                  | `pixie trace --app my-app`                   |

**Pro Tip:**
- Use **`kubectl exec -it <pod> -- sh`** to inspect running processes.
- For **Java apps**, enable debug logging:
  ```sh
  java -Dcom.sun.management.jmxremote -jar app.jar
  ```

---

## **4. Prevention Strategies**
### **4.1 Design for Observability**
- **Instrument Early:** Use OpenTelemetry SDKs during dev.
- **Standardize Logging:** Enforce structured logging (JSON).
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info({"event": "user_login", "user_id": 123})
  ```
- **Automate Instrumentation:** Use `opentelemetry-instrumentation-*` auto-instrumentation.

### **4.2 Monitor Agent Health**
- **Set Up Alerts:**
  ```yaml
  # Prometheus Alert for Fluent Bit Failures
  - alert: FluentBitHighErrorRate
    expr: rate(fluentbit_errors_total{job="fluent-bit"}[5m]) > 10
  ```
- **Kubernetes Liveness Probes:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 2020
  ```

### **4.3 Optimize Resource Usage**
- **Right Size Collectors:** Use smaller collectors (e.g., Fluent Bit for logs only).
- **Batch Exports:** Reduce API calls with batch spans/metrics.
  ```python
  # OpenTelemetry batching
  exporter = BatchSpanExporter(...)
  tracer_provider.add_span_processor(
      BatchSpanProcessor(exporter)
  )
  ```

### **4.4 Chaos Engineering for Observability**
- **Test Failover:** Simulate collector failures.
- **Load Test:** Check system behavior under high telemetry load.

---

## **5. Quick Reference Cheatsheet**
| **Issue**               | **Immediate Fix**                          | **Long-Term Fix**                          |
|--------------------------|--------------------------------------------|--------------------------------------------|
| Missing Logs             | Restart log-forwarding container           | Validate permissions & config              |
| Slow Traces              | Increase Jaeger collector replicas         | Optimize sampling & instrumentation        |
| High CPU/Memory          | Lower resource limits                      | Use batch exports & relabeling             |
| Instrumentation Errors   | Check SDK logs & docs                      | Auto-instrumentation & CI validation       |
| Alert Fatigue            | Adjust thresholds                         | Implement SLO-based alerting                |

---

## **Final Debugging Workflow**
1. **Reproduce:** Check if the issue is consistent (always vs. intermittent).
2. **Isolate:** Verify if the problem is in the app, sidecar, or backend.
3. **Validate:** Compare against logs/metrics/alerts.
4. **Fix:** Apply the most likely fix (from Common Issues section).
5. **Prevent:** Implement checks for recurrence.

By following this structured approach, you can **quickly diagnose and resolve** most Containers Observability issues while ensuring scalability and reliability.