# **[Pattern] Hybrid Gotchas: Reference Guide**

---

## **Overview**
The **Hybrid Gotchas** pattern describes common pitfalls in **hybrid cloud, multi-cloud, or on-premise architectures** where misconfigurations, misalignments, or unanticipated behavior arise from mixing or interacting **different infrastructure models, APIs, or runtime environments**. These issues often surface when:

- **Legacy systems** (monolithic, on-premise) integrate with **cloud-native services** (microservices, serverless, containers).
- **Policy enforcement diverges** (e.g., IAM in AWS vs. Azure vs. on-premise Active Directory).
- **State management conflicts** (e.g., in-memory caching in one tier vs. persistent databases in another).
- **Networking mismatches** (VPN gateways, service mesh inconsistencies, or regional latency).

Gotchas in hybrid setups often lead to **security gaps, performance bottlenecks, debugging difficulties, or operational blind spots**. This guide maps common failure modes, their root causes, and mitigation strategies.

---

## **Schema Reference**

Below is a structured taxonomy of hybrid gotchas, categorized by **layer** (Infrastructure → Application → Data → Security → Operations).

| **Category**          | **Gotcha**                          | **Root Cause**                                                                 | **Impact**                                                                 | **Key Metrics to Monitor**                     |
|-----------------------|--------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Infrastructure**    | Incompatible CLI/API versions        | CLI/API version skew between on-prem and cloud providers (e.g., Terraform v1.5 vs. v1.6). | Failures in resource provisioning, drift detection errors.                 | `CLI/API version mismatches`, `resource creation failures`. |
|                       | IAM/Identity silos                    | Overlapping or missing user/role mappings (e.g., Active Directory vs. AWS IAM). | Unauthorized access, conflicting permissions, or redundant roles.            | `Permission denials`, `access log conflicts`. |
|                       | Hybrid networking misconfigurations  | Incorrect subnet routing (e.g., VPC peering vs. on-prem VPN).                 | Data leakage, latency spikes, or routing loops.                               | `Traceroute failures`, `packet loss`.        |
| **Application**       | State synchronization failures       | Eventual consistency vs. strong consistency in distributed transactions.       | Inconsistent data across tiers (e.g., Redis in cloud vs. SQL on-prem).      | `Write-after-read inconsistencies`, `ETag mismatches`. |
|                       | Hybrid logging/observability gaps    | Mixed tooling (e.g., Prometheus + on-prem ELK vs. cloud-native OpenTelemetry).  | Blind spots in debugging (e.g., missing metrics for one tier).              | `Log ingestion failures`, `metric sampling gaps`. |
|                       | Dependency version conflicts         | Library versions incompatible across environments (e.g., Python 3.8 on-prem vs. 3.10 in cloud). | Crashes, runtime errors, or CI/CD pipeline breaks.                          | `Dependency resolution failures`, `runtime exceptions`. |
| **Data**              | Schema drift in hybrid databases     | Schema changes unaligned across on-prem SQL and cloud NoSQL.                   | Query failures, type mismatches, or migration errors.                         | `Schema validation errors`, `data type conflicts`. |
|                       | Hybrid data residency compliance     | Data stored in regions violating local laws (e.g., GDPR, CCPA).               | Legal penalties, breach risks, or customer trust erosion.                   | `Cross-border data transfer logs`, `compliance audit failures`. |
| **Security**          | Hybrid encryption key mismanagement   | Shared keys between environments (e.g., AWS KMS vs. on-prem HSM).             | Key leakage, decryption failures, or compliance violations.                 | `Key rotation failures`, `decryption errors`. |
|                       | Hybrid DDoS attack vectors            | Hybrid setups expose multiple attack surfaces (e.g., legacy API + cloud load balancer). | Amplification attacks, resource exhaustion.                                  | `Spike in request volume`, `rate limit violations`. |
| **Operations**        | Hybrid CI/CD pipeline fragmentation    | Separate pipelines for on-prem and cloud with no unified rollback strategy.    | Failed deployments, partial rollouts, or extended outages.                   | `Deployment rollback latency`, `revert failures`. |
|                       | Hybrid incident response delays       | Siloed monitoring tools (e.g., Splunk for on-prem, Datadog for cloud).        | Slow MTTR, misdiagnosis, or escalation bottlenecks.                          | `Alert filtering failures`, `incident escalation time`. |

---

## **Query Examples**
Below are **example queries** to detect hybrid gotchas in common tools:

### **1. Detecting IAM Role Conflicts (AWS CLI + CloudTrail)**
```bash
# List IAM roles with inconsistent policies between on-prem and AWS
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue="AssumeRole" \
  --max-results 1000 | jq '.Events[] | select(.responseElements.roleName != "on-prem-sync-role")'
```

### **2. Monitoring Schema Drift (AWS Glue + On-Prem MySQL)**
```sql
-- Compare table schemas between cloud (Glue) and on-prem (MySQL)
SELECT
    "on-prem_table".column_name,
    "on-prem_table".data_type AS on_prem_type,
    "glue_catalog".column_name AS glue_column_name,
    "glue_catalog".data_type AS glue_type,
    CASE WHEN "on-prem_table".data_type != "glue_catalog".data_type
         THEN 'MATCH_FAILURE'
         ELSE 'MATCH' END AS schema_status
FROM
    on_prem_metadata."on-prem_table" CROSS JOIN
    glue_catalog."my_database"."glue_catalog"
WHERE
    "on-prem_table".table_name = "glue_catalog".table_name;
```

### **3. Detecting Hybrid Logging Gaps (Fluentd + Splunk)**
```logstash
filter {
  if [source] =~ /on-prem/ {
    mutate {
      add_field => { "[hybrid_status]" => "on-prem_incomplete" }
    }
  }
  if [source] =~ /cloud/ and !["message"] =~ /critical/ {
    mutate {
      add_field => { "[hybrid_status]" => "cloud_filtered" }
    }
  }
}
```

### **4. Hybrid Dependency Conflicts (Docker Compose)**
```yaml
# Example: Detecting Python version conflicts
version: '3.8'
services:
  on-prem-app:
    image: python:3.8
    command: pip install --upgrade --requirement requirements.txt
  cloud-app:
    image: python:3.10
    command: pip install --upgrade --requirement requirements-cloud.txt
  healthcheck:
    image: alpine/py3:3.8
    command: |
      python3 -c "
      import sys; print('On-prem: 3.8, Cloud: 3.10' if sys.version_info < (3, 9) else 'Conflict detected!')
      "
```

---

## **Related Patterns**
To mitigate hybrid gotchas, consider integrating these patterns:

1. **[Multi-Cloud Abstraction Layer](https://docs.cloudpattern.org/multi-cloud-abstraction)**
   - Standardizes APIs (e.g., Terraform Cloud, Crossplane) to reduce provider-specific quirks.

2. **[Chaos Engineering for Hybrid](https://docs.cloudpattern.org/chaos-hybrid)**
   - Simulates failures (e.g., network partitions, API timeouts) to identify blind spots.

3. **[Hybrid Observability Stack](https://docs.cloudpattern.org/observability-hybrid)**
   - Unifies logging (Fluentd + Loki), metrics (Prometheus + CloudWatch), and tracing (Jaeger + OpenTelemetry).

4. **[Policy-as-Code for Hybrid](https://docs.cloudpattern.org/policy-hybrid)**
   - Enforces consistency with tools like **Open Policy Agent (OPA)** or **Kyverno** for Kubernetes.

5. **[Disaster Recovery Hybrid](https://docs.cloudpattern.org/dr-hybrid)**
   - Designs for **multi-region failover** (e.g., AWS Outposts + Azure Arc) to minimize downtime.

6. **[Hybrid Service Mesh](https://docs.cloudpattern.org/service-mesh-hybrid)**
   - Uses **Istio + Linkerd** to manage traffic, retries, and circuit breaking across tiers.

---

## **Mitigation Checklist**
| **Action**                          | **Tool/Strategy**                          | **Owner**          |
|-------------------------------------|--------------------------------------------|--------------------|
| Align IAM roles across environments | **AWS SSO + Active Directory Federation**  | Security Team      |
| Standardize logging formats         | **OpenTelemetry + Grafana Loki**           | DevOps Team        |
| Enforce version pinning             | **Dependency Lockfiles (Poetry, npm-shrinkwrap)** | Dev Team      |
| Test hybrid transactions            | **Chaos Mesh + Kubernetes**                | QA Team           |
| Monitor cross-tier latency          | **Distributed Tracing (Jaeger, Zipkin)**   | SRE Team          |
| Enforce data residency policies     | **AWS Glue DataBrew + GDPR Scanning**       | Compliance Team    |

---
**Key Takeaway**: Hybrid gotchas are **not inherent to architecture** but emerge from **lack of alignment**. Proactive schema validation, unified observability, and **test-driven hybrid integrations** are critical. For deeper dives, refer to the linked related patterns.