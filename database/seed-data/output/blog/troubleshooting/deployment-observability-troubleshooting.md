# **Debugging Deployment Observability: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **1. Introduction**
Deployment Observability ensures you can **monitor, trace, and debug** issues in real-time across environments (dev, staging, prod). Poor observability leads to:
- **Undetected failures** (silent crashes, degraded performance)
- **Slow incident response** (guesswork instead of data-driven debugging)
- **Inconsistent deployments** (unpredictable behavior between environments)

This guide focuses on **quick resolution** of observability-related issues in modern microservices/containerized deployments.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Observability Issue** | **Indicators** | **Tools to Check** |
|--------------------------|----------------|--------------------|
| **Missing Metrics** | No Prometheus/Grafana data | `kubectl logs`, `helm test`, SLO alerts |
| **Corrupted Traces** | Distributed tracing (Jaeger/Zipkin) shows broken spans | Check OpenTelemetry collectors |
| **Log Gaps** | Critical logs missing in Loki/Fluentd | Verify log shipper configuration |
| **Slow Query Performance** | High query latency in databases | `EXPLAIN ANALYZE`, `pg_stat_activity` |
| **Environment Drift** | Staging differs from production | `kubectl diff`, CI/CD pipeline checks |
| **Alert Fatigue** | Too many false positives in Prometheus Alertmanager | Review alert rules (`--rule-files`) |
| **Permission Issues** | 403/401 errors in monitoring dashboards | Check IAM roles, Kubernetes RBAC |

---

## **3. Common Issues & Fixes**
### **A. Metrics Not Showing in Prometheus/Grafana**
**Symptoms:**
- No data in dashboards despite healthy services.
- Prometheus scrape errors (`scrape_config` failures).

**Root Causes & Fixes:**

| **Cause** | **Solution** | **Code Example** |
|-----------|-------------|------------------|
| **Misconfigured ServiceMonitor** (K8s) | Wrong `targets` or labels in Helm values. | ```yaml # Correct: endpoints: - port: http targetPort: 9090 path: /metrics interval: 15s |
| **Prometheus Reload Fails** | Syntax error in config (`prometheus.yml`). | ```yaml # Debug: `prometheus --config.file=/etc/prometheus/prometheus.yml --web.enable-lifecycle` |
| **Port Unreachable** | Service exposed on wrong port. | ```bash # Test: `curl -v http://<service>:<port>/metrics` |
| **Missing Prometheus Operator** | Helm chart not installed (`prometheus-operator`). | ```bash helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring ```

---

### **B. Distributed Traces Missing Spans**
**Symptoms:**
- Jaeger/Zipkin shows incomplete traces (missing spans).
- High latency in OTel collector.

**Root Causes & Fixes:**

| **Cause** | **Solution** | **Code Example** |
|-----------|-------------|------------------|
| **Instrumentation Missing** | App lacks OpenTelemetry SDK. | ```python # Add to app.py import opentelemetry from opentelemetry import trace tracer = trace.get_tracer(__name__) @tracer.start_as_current_span("api_endpoint") def my_endpoint(): ... |
| **Collector Configuration Wrong** | Wrong `service_name` or receivers. | ```yaml # Correct service: service: name: my-service port_number: 4317 receivers: otlp: protocols: grpc: max_receive_message_size_mib: 32 |
| **Network Firewall Blocking** | OTel exporter port (4317/4318) blocked. | ```bash # Test: `telnet <collector-ip> 4317` |

**Debugging Steps:**
1. Check collector logs (`kubectl logs -n observability otel-collector-*`).
2. Verify spans in Jaeger CLI:
   ```bash jaeger query --service=my-service --duration=1h
   ```

---

### **C. Logs Missing in Loki/Fluentd**
**Symptoms:**
- Critical logs not in Grafana/Loki.
- Fluentd restarted without preserving state.

**Root Causes & Fixes:**

| **Cause** | **Solution** | **Code Example** |
|-----------|-------------|------------------|
| **Fluentd Output Plugin Misconfigured** | Wrong `loki_url` or labels. | ```conf # Correct output plugin <match **> type loki loki_url http://loki:3100/loki/api/v1/push stream_identifier ${TAG_kubernetes_pod_name} format json |
| **Disk Space Full** | Loki ring storage overloaded. | ```bash # Check storage: kubectl exec -it loki -- ls -l /var/loki/ |
| **Log Shipper Crash Loop** | Invalid regex in filter. | ```conf # Debug: `--enable-debug-log` in fluentd pod |

**Quick Check:**
- Test log ingestion manually:
  ```bash curl -X POST http://loki:3100/loki/api/v1/push -H "Content-Type: application/json" -d '{"streams": [{"stream": {"job":"test"},"values": [["2024-01-01T00:00:00Z","test log"]]}]}'
  ```

---

### **D. Environment Drift (Staging ≠ Prod)**
**Symptoms:**
- Staging works, but prod fails silently.

**Root Causes & Fixes:**

| **Cause** | **Solution** | **Tool Example** |
|-----------|-------------|------------------|
| **Hardcoded Configs** | Use ConfigMaps/Secrets. | ```yaml # Env diff: kubectl get cm staging-config -o yaml > staging-cm.yaml kubectl get cm prod-config -o yaml > prod-cm.yaml diff staging-cm.yaml prod-cm.yaml |
| **Database Schema Mismatch** | Schema migrations not applied. | ```bash # Check: `kubectl logs -n db-migrator job/<migration-job>` |
| **Missing Sidecar Probes** | Liveness/readiness probes disabled. | ```yaml # Ensure livenessProbe: initialDelaySeconds: 30 periodSeconds: 10 timeoutSeconds: 5 successThreshold: 1 failureThreshold: 3 |

**Prevention:**
- Use **Git Sync** for ConfigMaps:
  ```yaml apiVersion: v1 kind: ConfigMap data: app-config: | {{ include "myapp.config" . }} metadata: name: app-config annotations: config.kubernetes.io/path: "config" ```
- Run **environment validation** in CI:
  ```bash # Example: diff-staging-prod.sh ```

---

### **E. Alert Fatigue (Too Many False Positives)**
**Symptoms:**
- Alertmanager spams Slack/Email.

**Root Causes & Fixes:**

| **Cause** | **Solution** | **Example Rule** |
|-----------|-------------|------------------|
| **Too Broad Alerts** | Tighten thresholds. | ```yaml - alert: HighErrorRate for: 5m if: (rate(http_server_errors_total{job="myapp"}[5m])) * 100 > 5 group_by: instance |
| **Missing Silence Rules** | Schedule downtime. | ```yaml - alert: ProductionMaintenance silence_for: 1h if: matches(label: "severity", "critical") matches(label: "service", "db") |
| **Prometheus Scraping Errors** | Ignore unreachable targets. | ```yaml - alert: ScrapeError for: 1h if: up{job="myapp"} == 0 group_by: job |

**Debugging Alerts:**
```bash # List active alerts: kubectl exec -it alertmanager -- prometheus-alertmanager --web.listen-address=:9093 --config.file=/etc/alertmanager/config.yml --alertmanagers.url="http://localhost:9090" --web.route-prefix="/alerts" --query.list --query.matchers="status=pending"
```

---

## **4. Debugging Tools & Techniques**
| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|----------------------|
| **Prometheus Query Editor** | Debug metric queries. | `http://<prometheus>:9090/graph?g0.expr=rate(http_requests_total{job="api"}[5m])` |
| **K6 (Load Testing)** | Simulate traffic spikes. | ```javascript import http from 'k6/http'; export default function () { http.get('http://myapp/api'); } ``` |
| **Jaeger CLI** | Inspect traces. | `jaeger query --service=api --limit=100` |
| **kubectl debug** | Run ad-hoc debugging pods. | ```bash kubectl debug -it deploy/myapp --image=busybox --target=myapp-pod --command -- /bin/sh ```
| **Loki Logs Explorer** | Filter logs by time/label. | `http://<loki>:3100/loki/api/v1/query?query={job="api"} | json_pretty` |
| **Chaos Mesh** | Inject failures for resilience testing. | ```yaml apiVersion: chaos-mesh.org/v1alpha1 kind: PodChaos podName: myapp-pod chaosType: pod-failure failureMode: crash duration: 1m ```

---

## **5. Prevention Strategies**
### **A. CI/CD Pipeline Checks**
1. **Observability Gates**:
   - Fail pipeline if Prometheus scrape fails.
     ```yaml jobs: - name: "Check Metrics" run: curl -f http://prometheus:9090/-/healthy || exit 1 ```
2. **Canary Deployments**:
   - Gradually roll out changes with traffic splitting (Istio/Linkerd).
     ```yaml # Istio VirtualService trafficPolicy: loadBalancer: simple: LEAST_CONNECTED ```

### **B. Infrastructure as Code (IaC) Best Practices**
1. **Template Validation**:
   - Use `kubectl apply --dry-run=client` for YAML checks.
   - **Helm Lint**: `helm lint ./chart`.
2. **Environment Parity**:
   - Use **Terraform modules** for consistent setups.
     ```hcl module "observability" { source = "./modules/observability" namespace = "observability" tags = local.common_tags } ```

### **C. SLO-Based Alerting**
- Define **Service Level Objectives (SLOs)** (e.g., "99.9% latency < 500ms").
- Alert only on SLO violations:
  ```yaml - alert: HighLatencyViolatesSLO for: 15m if: (histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)) > 0.5) and (avg_over_time(http_request_duration_seconds_sum[5m])) > 0.5 group_by: service ```

### **D. Centralized Observability Dashboards**
- **Grafana Provisioning**:
  ```yaml apiVersion: v1 data: dashboards.yaml: | ---
    folders: - name: MyApp title: MyApp dashboards: - title: API Latency uid: abc123 type: file path: /var/lib/grafana/dashboards/api-latency.json kind: file
    metadata: name: myapp-dashboards type: grafana-dashboard
  ```
- **Auto-Update Dashboards**:
  - Use **Grafana Explore** to save common queries as dashboards.

---

## **6. Quick Reference Cheat Sheet**
| **Issue** | **Immediate Fix** | **Long-Term Fix** |
|-----------|------------------|------------------|
| **No metrics in Prometheus** | `kubectl logs -n monitoring prometheus-k8s-0` | Add `ServiceMonitor` to Helm values |
| **Missing traces in Jaeger** | Check OTel collector logs (`kubectl logs otel-collector-*`) | Verify `service_name` in app instrumentation |
| **Logs missing in Loki** | Test manual log push (see above) | Add `resource.labels` in Fluentd |
| **Staging vs. Prod mismatch** | Run `kubectl diff` between namespaces | Use GitOps (ArgoCD/Flux) |
| **Alert fatigue** | Disable alerts with `silence` | Refine rules with SLOs |

---

## **7. Conclusion**
Deployment Observability failures often stem from **misconfigurations, missing instrumentation, or environment drift**. Follow this guide’s **structured debugging approach**:
1. **Verify symptoms** (metrics, logs, traces).
2. **Check infrastructure** (Prometheus, OTel, Fluentd).
3. **Compare environments** (staging vs. prod).
4. **Prevent recurrence** (CI/CD gates, IaC, SLOs).

**Final Tip:** Always **test observability changes in staging** before production. Use tools like **Prometheus `alertmanager --query.list`** and **Jaeger CLI** for rapid debugging.

---
**Next Steps:**
- [ ] Implement **SLO-based alerting**.
- [ ] Add **canary deployments** for critical services.
- [ ] Use **Chaos Engineering** to validate observability.