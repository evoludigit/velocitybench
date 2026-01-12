**[Pattern] Configuration Drift Detection – Reference Guide**

---

# **1. Overview**
**Configuration Drift Detection** is a **proactive pattern** that monitors infrastructure, applications, and configuration states to identify unintended changes. Drift occurs when declared configurations (e.g., Kubernetes manifests, Terraform state, or cloud resource definitions) diverge from operational states (e.g., actual running clusters, deployed services). By continuously comparing baseline configurations with live system states, this pattern helps detect anomalies before they cause failures, compliance violations, or security risks.

Best suited for:
- **Multi-team environments** where configuration ownership is fragmented.
- **CI/CD pipelines** where drift may occur post-deployment.
- **Hybrid/cloud-native** deployments requiring compliance or security audits.
- **Stateful applications** (e.g., databases, caching layers) or ephemeral workloads (e.g., containerized services).

---

# **2. Key Concepts**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Baseline Configuration** | The intended state (e.g., Git-committed manifests, Terraform code, or as-code definitions). |
| **Operational State**    | The real-time state of infrastructure (e.g., running Kubernetes pods, AWS EC2 instances). |
| **Drift**               | Detectable differences between baseline and operational states.              |
| **Remediation**         | Actions to restore alignment (e.g., rolling updates, patching, or manual fixes). |
| **Baseline Sync**       | Periodically updating baselines to reflect intentional changes (e.g., code merges). |

---

# **3. Schema Reference**
Below are common schemas for implementing drift detection, organized by **infrastructure domain**. Adopt one or combine them as needed.

---

### **3.1 Core Schema: Drift Event**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DriftEvent",
  "type": "object",
  "required": ["baseline", "operational", "resources", "severity", "timestamp"],
  "properties": {
    "baseline": {
      "description": "Reference to the baseline configuration (e.g., commit hash, artifact ID).",
      "type": "string"
    },
    "operational": {
      "description": "State of resources as observed at runtime.",
      "type": ["array", "object"]
    },
    "resources": {
      "description": "List of resources where drift was detected.",
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string" },  // e.g., "Kubernetes/Deployment", "AWS/S3Bucket"
          "name": { "type": "string" },  // e.g., "my-app-deployment"
          "baselineSpec": {
            "description": "Expected attributes (e.g., replicas, labels).",
            "type": "object"
          },
          "operationalSpec": {
            "description": "Actual attributes observed.",
            "type": "object"
          },
          "diff": {
            "description": "Structured difference highlighting changes (e.g., `{"replicas": {"expected": 3, "actual": 5}}`).",
            "type": "object"
          }
        }
      }
    },
    "severity": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "remediation": {
      "description": "Suggested fixes (e.g., Terraform commands, kubectl patches).",
      "type": ["string", "object"]
    },
    "source": {
      "description": "Tool/agent generating the drift event (e.g., "KubeConform", "Terraform Cloud").",
      "type": "string"
    }
  }
}
```

---

### **3.2 Resource-Specific Schemas**
| **Domain**          | **Schema Type**               | **Key Fields**                                                                                     |
|---------------------|-------------------------------|---------------------------------------------------------------------------------------------------|
| **Kubernetes**      | `ClusterResourceDiff`         | `kind`, `metadata.name`, `baseline.spec`, `operational.status`, `violations` (from OPA/Policy)  |
| **Terraform**       | `TFStateDiff`                 | `resource.address`, `expected.attributes`, `actual.state`, `modifications_needed`                |
| **AWS**             | `AWSResourceDiff`             | `resourceType` (e.g., "EC2.Instance"), `expected.tags`, `actual.properties`                     |
| **Configuration**   | `ConfigKeyDiff`               | `filePath`, `baseline.value`, `operational.value`, `lineNumber`                                   |

---

# **4. Implementation Approaches**
Choose tools based on your needs (see [Related Patterns](#5-related-patterns)).

---

## **4.1 Manual Inspection (Low Automation)**
- **Tools**: `kubectl diff` (Kubernetes), `terraform plan -out=tfplan` (Terraform).
- **How**:
  1. Export baseline (e.g., `kubectl get deployments -o yaml > baseline.yaml`).
  2. Compare with live state (`kubectl diff --local baseline.yaml`).
  3. Manually reconcile differences.
- **Pros**: No tooling overhead.
- **Cons**: Prone to human error; not scalable.

---

## **4.2 Automated Agents (Agent-Based)**
Deploy lightweight agents to monitor drift in real time.

| **Agent**               | **Domain**       | **How It Works**                                                                                     |
|-------------------------|------------------|------------------------------------------------------------------------------------------------------|
| **KubeConform**         | Kubernetes       | Validates live resources against YAML/JSON schemas (e.g., Open Policy Agent policies).             |
| **Terragrunt**          | Terraform        | Compares Terraform state (`terraform show`) with plan outputs.                                        |
| **AWS Config Rules**    | AWS              | Evaluates resource compliance against predefined rules (e.g., "EC2 instances must have SSM Agent"). |
| **Custom Scripts**      | Generic          | Use `diff` (Unix), `git diff`, or Python (`deepdiff`) to compare files/states.                     |

**Example (Python with `deepdiff`)**:
```python
import deepdiff
import yaml
from kubernetes import client, config

def detect_k8s_drift(baseline_path):
    # Load baseline
    with open(baseline_path) as f:
        baseline = yaml.safe_load(f)

    # Fetch live state
    config.load_kube_config()
    api = client.AppsV1Api()
    live = api.list_deployment_for_all_namespaces().to_dict()["items"]

    # Compare
    diff = deepdiff.compare(baseline, live, exclude_paths=["metadata.uid"])
    return diff
```

---

## **4.3 CI/CD Integration (Pipelines)**
Trigger drift checks in **post-deploy** stages.

### **Example: GitHub Actions Workflow**
```yaml
name: Drift Detection
on:
  push:
    branches: [main]
jobs:
  check-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install KubeConform
        run: |
          curl -sSfL https://raw.githubusercontent.com/yannh/kubeconform/master/install.sh | bash -s -- -b /usr/local/bin
      - name: Validate Kubernetes manifests
        run: |
          kubeconform -summary -schema-location local -schema-directory ./schemas -strict -pretty true ./k8s/
```

---

## **4.4 Event-Driven Alerting**
Use **event-driven architectures** (e.g., Prometheus, Fluentd) to alert on drift.

**Example (Prometheus + Alertmanager)**:
```yaml
# prometheus.yml
- alert: KubernetesConfigDrift
  expr: kube_config_drift_detected == 1
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Config drift detected in namespace {{ $labels.namespace }}"
    description: "Deployment {{ $labels.deployment }} has unreconciled changes."
```

**Metrics to Track**:
- `kube_config_drift_detected {namespace="prod", deployment="my-app"}` (binary: 0/1).
- `aws_resource_tags_misdrift {resourceType="S3Bucket", bucket="data-lake"}`.

---

# **5. Query Examples**
Use these queries to analyze drift patterns in tools like **Prometheus**, **Grafana**, or **Elasticsearch**.

---

### **5.1 PromQL (Prometheus)**
```promql
# Drift events in the last 24 hours
sum by (namespace, resource_type, severity) (
  rate(kube_config_drift_events_total[1d])
) > 0

# Critical drift trends
increase(kube_config_drift_events_total{severity="critical"}[30d])
```

---

### **5.2 Elasticsearch (Kibana)**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "source": "kubeconform" } },
        { "range": { "timestamp": { "gte": "now-1d" } } },
        { "match": { "severity": "high" } }
      ]
    }
  }
}
```

---

### **5.3 Terraform Cloud API**
```bash
# List drift findings for a workspace
curl --header "Authorization: Bearer $TF_API_TOKEN" \
  "https://app.terraform.io/api/v2/workspaces/{workspace-id}/runs/{run-id}/diffs"
```

---

# **6. Best Practices**
| **Practice**                          | **Guidance**                                                                                           |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Baseline Frequency**                | Sync baselines **daily** or post-code merges to avoid false positives.                             |
| **Severity Thresholds**               | Classify drift as `critical` if it breaks security/compliance (e.g., missing IAM policies).          |
| **Remediation Automation**            | Use tools like **Argo Rollouts** (K8s) or **Terraform Apply** to auto-fix non-critical drift.          |
| **Audit Logging**                     | Retain drift logs for **1 year** to trace root causes (e.g., who deployed a misconfigured resource?). |
| **Cross-Team Ownership**              | Assign **SRE teams** to own drift detection for shared infrastructure.                                |
| **False Positive Reduction**          | Whitelist expected changes (e.g., auto-scaling rules) in baseline comparisons.                       |

---

# **7. Common Pitfalls**
| **Pitfall**                          | **Solution**                                                                                          |
|---------------------------------------|------------------------------------------------------------------------------------------------------|
| **Overly Strict Policies**            | Start with `medium` severity; tighten rules as teams mature.                                         |
| **Ignoring Stateful Resources**       | Use tools like **Database Migration Framework (DMF)** for DB drift detection.                        |
| **Tool Overload**                     | Prioritize **one primary agent** (e.g., KubeConform for K8s) and supplement with scripts.           |
| **Drift vs. Intentional Changes**     | Tag baselines with `intended=true` for planned changes (e.g., feature flags).                     |

---

# **8. Related Patterns**
| **Pattern**                          | **Connection to Drift Detection**                                                                                     |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **[Infrastructure as Code (IaC)]**   | IaC (e.g., Terraform, Pulumi) reduces drift by treating infrastructure as code.                                   |
| **[Policy as Code]**                  | Use **Open Policy Agent (OPA)** or **Kyverno** to enforce drifts in real time.                                      |
| **[Chaos Engineering]**               | Simulate drift scenarios (e.g., force-recreate a pod) to test resilience.                                         |
| **[GitOps]**                          | Tools like **Flux** or **ArgoCD** sync live state with Git repositories, reducing drift.                          |
| **[Observability Stack]**             | Correlate drift events with logs/metrics (e.g., `aws-cloudtrail` + `Prometheus` for AWS drift).                  |
| **[Configuration Management]**        | Use **Ansible** or **Chef** to enforce consistent configurations across nodes.                                     |

---

# **9. References**
- [Kubernetes Policy Tools](https://kubernetes.io/docs/concepts/policy/)
- [Terraform Drift Detection](https://developer.hashicorp.com/terraform/tutorials/cloud/detect-drift)
- [AWS Config](https://aws.amazon.com/config/features/)
- [DeepDiff Python Library](https://pypi.org/project/deepdiff/)