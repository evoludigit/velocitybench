**[Pattern] Deployment Troubleshooting: Reference Guide**

---

### **Overview**
This guide provides a structured methodology for diagnosing and resolving common deployment issues in cloud-native, microservices, or monolithic applications. It outlines key concepts, schema references for error categorization, troubleshooting queries, and integrations with related patterns. The goal is to streamline issue resolution by organizing troubleshooting into phases: **pre-deployment checks**, **post-deployment validation**, and **live environment diagnostics**.

---

### **Key Concepts**
1. **Deployment Phases**:
   - **Pre-Deployment**: Validates input artifacts, environment readiness, and configuration.
   - **Post-Deployment**: Checks for artifacts deployed correctly and services initialized.
   - **Live**: Monitors performance, errors, and resource constraints.

2. **Error Taxonomy**:
   - **Syntax Errors**: Invalid configurations or syntax in manifests/deployment scripts.
   - **Dependency Errors**: Missing images, unresolvable services, or missing permissions.
   - **Resource Errors**: Insufficient CPU/memory, network throttling, or quotas.
   - **State Errors**: Rollback failures, stuck deployments, or inconsistent cluster states.
   - **Business Logic Errors**: Post-deployment runtime failures (e.g., API timeouts, DB connection issues).

3. **Troubleshooting Tools**:
   - **Cluster Logs**: `kubectl logs`, `journalctl` (for non-K8s environments).
   - **Metrics**: Prometheus/Grafana for latency, error rates, and resource usage.
   - **Debugging Pods**: `kubectl exec` or remote debugging containers.
   - **Network Tools**: `tcpdump`, `curl -v` for API endpoints.

4. **Rollback Strategy**:
   - Define rollback triggers (e.g., 5xx errors > 5% for 1 minute).
   - Use immutable deployments with versioned artifacts.

---

### **Schema Reference**

| **Category**       | **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Example Values**                                                                                     |
|--------------------|-------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Deployment**     | `phase`                 | Enum           | Current status of the deployment (e.g., `pending`, `failed`, `completed`).                                                                                                                                                     | `"failed"`, `"pending"`                                                                                 |
| **Error Details**  | `type`                  | Enum           | Classifies the error (e.g., `syntax`, `dependency`, `resource`).                                                                                                                                                       | `"dependency"`, `"timeout"`                                                                             |
|                    | `code`                  | String         | Vendor-specific error code (e.g., `K8sError:403`).                                                                                                                                                                               | `"DBConnectionError:500"`                                                                        |
|                    | `message`               | String         | Human-readable error description.                                                                                                                                                                                     | `"Failed to pull image: repository does not exist"`                                                   |
|                    | `timestamp`             | ISO 8601       | When the error occurred.                                                                                                                                                                                           | `"2023-10-15T14:30:00Z"`                                                                               |
| **Context**        | `namespace`             | String         | Kubernetes namespace (if applicable).                                                                                                                                                                                 | `"prod-app"`                                                                                           |
|                    | `resource`              | String         | Affected resource (e.g., `deployment`, `pod`).                                                                                                                                                                           | `"deployment/nginx"`                                                                                   |
|                    | `replicaCount`          | Integer        | Number of replicas impacted (if applicable).                                                                                                                                                                           | `3`                                                                                                     |
| **Resolution**     | `action`                | String         | Suggested fix (e.g., `restart-pod`, `update-image`).                                                                                                                                                                | `"update-image: nginx:1.23.0"`                                                                      |
|                    | `severity`              | Enum           | Criticality level (e.g., `critical`, `warning`).                                                                                                                                                                       | `"critical"`                                                                                          |
| **Metrics**        | `latency`               | Float (ms)     | Average latency during deployment (if applicable).                                                                                                                                                                     | `520.3`                                                                                                |
|                    | `errorRate`             | Float (%)      | Error rate post-deployment.                                                                                                                                                                                         | `0.07` (7%)                                                                                            |

---

### **Query Examples**
Use these queries to diagnose issues in logs, metrics, or cluster state.

#### **1. Check Deployment Status**
```bash
# Check current deployment status in Kubernetes
kubectl get deployments -n <namespace> -o wide
```
**Output Example**:
```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
nginx      3/3     3            3           5m
```

#### **2. Inspect Failed Pods**
```bash
# List pods with errors
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
kubectl logs <pod-name> -n <namespace> --previous  # Check previous container logs
```

#### **3. Validate Configuration Drift**
```bash
# Compare expected vs. actual config
kubectl apply -f config.yaml --dry-run=client -o yaml | diff - <(kubectl get deployment <name> -n <namespace> -o yaml)
```

#### **4. Network Connectivity Issues**
```bash
# Test connectivity to a service
kubectl run curl-test --image=curlimages/curl --rm -it -- sh -c 'curl -v http://<service-name>:<port>'
```

#### **5. Metrics-Based Troubleshooting**
```bash
# Query Prometheus for error rates
curl 'http://<prometheus-server>:9090/api/v1/query?query=sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)'
```
**Output Example**:
```
{
  "status": "success",
  "data": {
    "result": [
      {
        "metric": {"service": "api-v1"},
        "value": [1697300600, "0.07"]  // 7% 5xx errors over 5 minutes
      }
    ]
  }
}
```

#### **6. Rollback Analysis**
```bash
# Compare versions before/after rollback
kubectl rollout history deployment/<name> -n <namespace>
kubectl describe deployment/<name> -n <namespace> | grep "Image:"
```

---

### **Diagnostic Checklist**
Follow this step-by-step approach for systematic troubleshooting:

1. **Pre-Deployment**:
   - Validate manifests with `kubectl apply --dry-run=client`.
   - Check image tags: `curl -I <registry>/<image>:<tag>`.
   - Test configurations locally (e.g., `minikube` or `docker-compose`).

2. **Post-Deployment**:
   - Confirm resources are running: `kubectl get pods,svc,deploy`.
   - Check logs for startup errors: `kubectl logs <pod> --tail=50`.
   - Verify endpoints: `kubectl exec <pod> -- curl http://localhost:8080/health`.

3. **Live Environment**:
   - Monitor metrics for anomalies (e.g., CPU spikes).
   - Correlate logs with metrics (e.g., `container_logs` + `prometheus_metrics` in tools like Grafana).
   - Isolate root causes using tracing (e.g., OpenTelemetry).

---

### **Related Patterns**
1. **[Canary Deployments]**
   - Gradually roll out changes to identify issues early.
   - *Integration*: Use deployment error rates to trigger rollback in canary patterns.

2. **[Feature Flags]**
   - Temporarily disable problematic features without redeploying.
   - *Integration*: Combine with troubleshooting to isolate business logic errors.

3. **[Infrastructure as Code (IaC)]**
   - Reproduce environments for consistent diagnostics.
   - *Integration*: Use IaC templates to validate pre-deployment configurations.

4. **[Observability Stack]**
   - Centralize logs, metrics, and traces for holistic analysis.
   - *Integration*: Correlate deployment errors with distributed traces (e.g., Jaeger).

5. **[Chaos Engineering]**
   - Proactively test resilience by simulating failures.
   - *Integration*: Use chaos experiments to validate rollback procedures.

---

### **Best Practices**
- **Automate Validation**: Integrate pre-deployment checks (e.g., Trivy for image scanning).
- **Standardize Error Logging**: Use structured logging (e.g., JSON) for easier querying.
- **Document Rollback Steps**: Include SLOs (e.g., "Rollback if error rate exceeds 10% for 3 minutes").
- **Limit Scopes**: Restrict troubleshooting to specific namespaces/teams during incidents.
- **Post-Mortem**: Capture lessons learned in incident reports.

---
**See also**:
- [Kubernetes Official Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Cloud Native Computing Foundation (CNCF) Observability Patterns](https://www.cncf.io/blog/2021/08/24/observability-patterns/)